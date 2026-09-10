from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from logistics.recommendations import OpportunityRecommendation
from logistics.recommendation_store import persist_recommendation


def test_persist_recommendation_is_tenant_scoped_and_explainable():
    conn = MagicMock()
    tenant_id = uuid4()
    opportunity_id = uuid4()
    recommendation = OpportunityRecommendation(
        score=0.81,
        recommended_price=Decimal("2150.00"),
        market_median=Decimal("2000.00"),
        risk_adjusted_profit=Decimal("500.00"),
        reasons=("positive_risk_adjusted_profit", "recent_market_median_available"),
    )
    persist_recommendation(conn, tenant_id=tenant_id, opportunity_id=opportunity_id, recommendation=recommendation)
    args = conn.execute.call_args.args
    assert args[1][0] == 0.81
    assert args[1][1] == Decimal("2150.00")
    assert args[1][2] == Decimal("2000.00")
    assert 'positive_risk_adjusted_profit' in args[1][3]
    assert args[1][4:] == (tenant_id, opportunity_id)
