"""Canonical V1 logistics domain contracts.

External providers map into these models. Provider payloads never become domain models.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class LoadStatus(StrEnum):
    NEW = "new"
    NORMALIZED = "normalized"
    OPPORTUNITY = "opportunity"
    BOOKED = "booked"
    CANCELLED = "cancelled"


class OpportunityStatus(StrEnum):
    CANDIDATE = "candidate"
    REJECTED = "rejected"
    ACCEPTED = "accepted"


class GeoPoint(BaseModel):
    model_config = ConfigDict(frozen=True)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CanonicalLocation(BaseModel):
    model_config = ConfigDict(frozen=True)
    raw_address: str = Field(min_length=1)
    normalized_address: str = Field(min_length=1)
    point: GeoPoint | None = None
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    confidence: float = Field(default=0.0, ge=0, le=1)
    provenance: str = "deterministic"


class LoadStop(BaseModel):
    model_config = ConfigDict(frozen=True)
    sequence: int = Field(ge=0)
    kind: str = Field(pattern="^(pickup|delivery)$")
    location: CanonicalLocation
    earliest: datetime | None = None
    latest: datetime | None = None


class Party(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    legal_name: str = Field(min_length=1)
    country_code: str = Field(default="UA", min_length=2, max_length=2)


class Vehicle(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    carrier_party_id: UUID
    capacity_kg: int = Field(gt=0)
    available_from: datetime | None = None


class Load(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    external_ref: str | None = None
    shipper_party_id: UUID | None = None
    cargo_type: str = Field(min_length=1)
    weight_kg: int = Field(gt=0)
    offered_price: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(default="UAH", min_length=3, max_length=3)
    stops: list[LoadStop] = Field(min_length=2)
    status: LoadStatus = LoadStatus.NEW
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Opportunity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    load_id: UUID
    score: float = Field(ge=0, le=1)
    estimated_cost: Decimal = Field(ge=0)
    estimated_margin: Decimal
    risk_adjusted_margin: Decimal
    reasons: list[str] = Field(default_factory=list)
    status: OpportunityStatus = OpportunityStatus.CANDIDATE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
