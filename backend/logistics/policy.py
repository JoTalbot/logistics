from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4


class AuthorizationError(PermissionError):
    pass


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    policy_version: str = "v1"


class PolicyEngine:
    def decide(self, action: str, risk_level: str, actor_roles: set[str]) -> PolicyDecision:
        if risk_level == "critical" and "human_operator" not in actor_roles:
            return PolicyDecision(False, "critical action requires human_operator")
        if action.startswith("autonomous.") and "autonomy" not in actor_roles:
            return PolicyDecision(False, "autonomous action requires autonomy role")
        return PolicyDecision(True, "allowed")

    def require(self, action: str, risk_level: str, actor_roles: set[str]) -> PolicyDecision:
        decision = self.decide(action, risk_level, actor_roles)
        if not decision.allowed:
            raise AuthorizationError(decision.reason)
        return decision


@dataclass(frozen=True)
class AuditRecord:
    tenant_id: UUID
    actor_id: UUID
    action: str
    resource_type: str
    resource_id: UUID
    decision: str
    reason: str
    timestamp: datetime
    audit_id: UUID = field(default_factory=uuid4)


class AuditSink(Protocol):
    def append(self, record: AuditRecord) -> None: ...


class InMemoryAuditSink:
    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    def append(self, record: AuditRecord) -> None:
        self.records.append(record)


def audit(tenant_id: UUID, actor_id: UUID, action: str, resource_type: str, resource_id: UUID, decision: PolicyDecision, sink: AuditSink) -> None:
    sink.append(AuditRecord(tenant_id, actor_id, action, resource_type, resource_id, "allow" if decision.allowed else "deny", decision.reason, datetime.now(timezone.utc)))
