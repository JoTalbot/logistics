from __future__ import annotations

import json
from uuid import UUID

from .recommendations import OpportunityRecommendation


def persist_recommendation(conn, *, tenant_id: UUID, opportunity_id: UUID, recommendation: OpportunityRecommendation) -> None:
    """Persist the latest explainable recommendation for one tenant-scoped opportunity."""
    conn.execute(
        """
        UPDATE opportunities
        SET score=%s,
            recommended_price=%s,
            market_median_price=%s,
            recommendation_reasons=%s::jsonb,
            recommendation_updated_at=now()
        WHERE tenant_id=%s AND id=%s
        """,
        (
            recommendation.score,
            recommendation.recommended_price,
            recommendation.market_median,
            json.dumps(list(recommendation.reasons)),
            tenant_id,
            opportunity_id,
        ),
    )
