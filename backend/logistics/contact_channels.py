from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ContactChannel(str, Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    PHONE = "phone"
    WEB_FORM = "web_form"


@dataclass(frozen=True)
class ContactIntent:
    channel: ContactChannel
    target: str
    message: str
    authorized: bool = False
    suppressed: bool = False
    human_approval_required: bool = True

    @property
    def sendable(self) -> bool:
        return self.authorized and not self.suppressed and not self.human_approval_required


class ContactChannelError(ValueError):
    pass


def prepare_contact_intent(
    *,
    channel: ContactChannel,
    target: str,
    message: str,
    authorized: bool,
    suppressed: bool = False,
) -> ContactIntent:
    if not target.strip():
        raise ContactChannelError("contact target is required")
    if not message.strip():
        raise ContactChannelError("contact message is required")
    return ContactIntent(
        channel=channel,
        target=target.strip(),
        message=message.strip(),
        authorized=authorized,
        suppressed=suppressed,
        human_approval_required=True,
    )


def authorize_for_human_review(intent: ContactIntent) -> ContactIntent:
    if intent.suppressed:
        raise ContactChannelError("suppressed contact cannot be authorized")
    if not intent.authorized:
        raise ContactChannelError("contact authorization is required")
    return ContactIntent(
        channel=intent.channel,
        target=intent.target,
        message=intent.message,
        authorized=True,
        suppressed=False,
        human_approval_required=False,
    )
