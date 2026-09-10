from uuid import uuid4

import pytest

from logistics.review import ReviewDecision, ReviewError, validate_review_decision


def test_review_decision_is_strict_and_explicit():
    decision = ReviewDecision("publication_intent", uuid4(), "approve", "operator-1", "verified provider permission")
    assert validate_review_decision(decision) == decision


def test_review_rejects_unsupported_resource_or_decision():
    with pytest.raises(ReviewError):
        validate_review_decision(ReviewDecision("load", uuid4(), "approve", "operator-1", "x"))
    with pytest.raises(ReviewError):
        validate_review_decision(ReviewDecision("publication_intent", uuid4(), "execute", "operator-1", "x"))
