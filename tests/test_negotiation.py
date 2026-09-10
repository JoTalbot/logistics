from decimal import Decimal
from logistics.negotiation import next_offer


def test_bounded_counteroffer():
    result = next_offer(current=Decimal('1000'), target=Decimal('900'), floor=Decimal('850'), round_count=0)
    assert result.action == 'counter'
    assert result.offer == Decimal('950.00')
    assert not result.requires_human


def test_round_limit_escalates():
    result = next_offer(current=Decimal('1000'), target=Decimal('900'), floor=Decimal('850'), round_count=3)
    assert result.action == 'human'
    assert result.requires_human
