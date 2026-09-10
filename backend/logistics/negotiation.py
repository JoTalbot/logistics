from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class NegotiationPolicy:
    max_rounds: int = 3
    min_margin: Decimal = Decimal('0')
    critical_requires_human: bool = True


@dataclass(frozen=True)
class NegotiationDecision:
    action: str
    offer: Decimal | None
    requires_human: bool
    reason: str


def next_offer(*, current: Decimal, target: Decimal, floor: Decimal, round_count: int, policy: NegotiationPolicy | None = None) -> NegotiationDecision:
    policy = policy or NegotiationPolicy()
    if round_count >= policy.max_rounds:
        return NegotiationDecision('human', current, True, 'maximum negotiation rounds reached')
    if target < floor:
        return NegotiationDecision('human', current, policy.critical_requires_human, 'target below economic floor')
    midpoint = (current + target) / Decimal('2')
    offer = max(floor, midpoint).quantize(Decimal('0.01'))
    if offer == current:
        return NegotiationDecision('accept', current, False, 'offer converged')
    return NegotiationDecision('counter', offer, False, 'bounded midpoint counteroffer')
