"""Telegram load-ad collection and deterministic parsing.

This module deliberately does not send collected Telegram content to an LLM.
Telegram's current API/content terms place restrictions on scraping and AI/ML use,
so V1 uses local deterministic extraction only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Iterable

from pydantic import BaseModel, Field


DEFAULT_CHATS = (
    "https://t.me/vantazhni_perevezennya_ua",
    "https://t.me/truck_world",
    "https://t.me/TURKIYA_UZBEKISTON_GRUBA_N1",
    "https://t.me/gruzoperevozki_ua",
)


class TelegramSourceMessage(BaseModel):
    chat: str
    message_id: int
    message_url: str | None = None
    published_at: datetime
    text: str = ""
    has_media: bool = False


class ParsedLoadAd(BaseModel):
    source_chat: str
    source_message_id: int
    source_message_url: str | None = None
    published_at: datetime
    raw_text: str
    origin: str | None = None
    destination: str | None = None
    cargo_type: str | None = None
    vehicle_type: str | None = None
    weight_kg: int | None = Field(default=None, gt=0)
    volume_m3: float | None = Field(default=None, gt=0)
    price: Decimal | None = Field(default=None, gt=0)
    currency: str | None = None
    loading_date_text: str | None = None
    phone_numbers: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)
    parser_version: str = "telegram-regex-v1"


@dataclass(frozen=True)
class TelegramChatConfig:
    source: str
    enabled: bool = True


_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)")
_WEIGHT_RE = re.compile(r"(?<!\d)(\d{1,3}(?:[.,]\d{1,3})?)\s*(?:т|тонн?\b|tons?\b)", re.I)
_VOLUME_RE = re.compile(r"(?<!\d)(\d{1,4}(?:[.,]\d{1,2})?)\s*(?:м3|м³|куб(?:\.|ов)?\b)", re.I)
_PRICE_WITH_CURRENCY_RE = re.compile(r"(?<!\d)(\d{2,7}(?:[.,]\d{1,2})?)\s*(€|EUR|грн|UAH|USD|\$|долл(?:\.|ар(?:ов|а)?)?)\b", re.I)
_PRICE_LABEL_RE = re.compile(r"(?:ставка|цена|оплата|rate|price)\s*[:=-]?\s*(\d{2,7}(?:[.,]\d{1,2})?)\s*(€|EUR|грн|UAH|USD|\$|долл(?:\.|ар(?:ов|а)?)?)?\b", re.I)


def _clean(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip(" \t\n,;:-")
    return value or None


def _parse_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value.replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1) if match else None


def _parse_route(text: str) -> tuple[str | None, str | None]:
    patterns = (
        r"(?:^|\n)\s*(?:из|з|from)\s*[:\-]?\s*([^\n→➡➜\-]+?)\s*(?:→|➡|➜|->|-)\s*([^\n]+)",
        r"([^\n,;]+?)\s*(?:→|➡|➜|->)\s*([^\n,;]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return _clean(match.group(1)), _clean(match.group(2))
    return None, None


def _currency(token: str | None) -> str | None:
    if not token:
        return None
    token = token.lower()
    if token in {"€", "eur"}:
        return "EUR"
    if token in {"$", "usd", "долл.", "долларов", "доллара"}:
        return "USD"
    return "UAH"


def _parse_price(text: str) -> tuple[Decimal | None, str | None]:
    match = _PRICE_LABEL_RE.search(text) or _PRICE_WITH_CURRENCY_RE.search(text)
    if not match:
        return None, None
    return _parse_decimal(match.group(1)), _currency(match.group(2))


def parse_load_ad(message: TelegramSourceMessage) -> ParsedLoadAd:
    text = message.text or ""
    origin, destination = _parse_route(text)
    weight_raw = _first_match(_WEIGHT_RE, text)
    volume_raw = _first_match(_VOLUME_RE, text)
    price, currency = _parse_price(text)

    fields_found = sum(value is not None for value in (origin, destination, weight_raw, volume_raw, price))
    confidence = min(1.0, 0.2 * fields_found + (0.2 if message.text else 0.0))

    return ParsedLoadAd(
        source_chat=message.chat,
        source_message_id=message.message_id,
        source_message_url=message.message_url,
        published_at=message.published_at,
        raw_text=text,
        origin=origin,
        destination=destination,
        weight_kg=round(float(_parse_decimal(weight_raw) or 0) * 1000) if weight_raw else None,
        volume_m3=float(_parse_decimal(volume_raw)) if volume_raw else None,
        price=price,
        currency=currency,
        phone_numbers=[re.sub(r"\s+", " ", p).strip() for p in _PHONE_RE.findall(text)],
        confidence=confidence,
    )


def parse_messages(messages: Iterable[TelegramSourceMessage]) -> list[ParsedLoadAd]:
    return [parse_load_ad(message) for message in messages]


async def collect_messages(
    client,
    chats: Iterable[str] = DEFAULT_CHATS,
    *,
    limit: int = 100,
    min_id_by_chat: dict[str, int] | None = None,
):
    """Yield recent messages from configured chats using an authenticated Telethon client."""
    min_id_by_chat = min_id_by_chat or {}
    for chat in chats:
        min_id = min_id_by_chat.get(chat, 0)
        async for message in client.iter_messages(chat, limit=limit, min_id=min_id, reverse=True):
            text = message.message or ""
            yield TelegramSourceMessage(
                chat=chat,
                message_id=message.id,
                message_url=f"{chat}/{message.id}" if str(chat).startswith("https://t.me/") else None,
                published_at=message.date,
                text=text,
                has_media=bool(message.media),
            )
