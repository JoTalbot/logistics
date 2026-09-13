import pytest

from logistics.calibration_operations import bounded_adjustment, evaluate_calibration_gate


def test_gate_requires_drift_sample_and_operator_approval():
    assert not evaluate_calibration_gate(terminal_cases=100, drift_detected=False, operator_approved=True).eligible
    assert not evaluate_calibration_gate(terminal_cases=5, drift_detected=True, minimum_terminal_cases=20, operator_approved=True).eligible
    assert not evaluate_calibration_gate(terminal_cases=20, drift_detected=True, operator_approved=False).eligible
    gate = evaluate_calibration_gate(terminal_cases=20, drift_detected=True, operator_approved=True)
    assert gate.eligible
    assert gate.policy_mutation is False


def test_bounded_adjustment_is_clamped_and_does_not_mutate_state():
    assert bounded_adjustment(current_score=0.5, suggested_delta=0.5, max_abs_delta=0.05) == 0.55
    assert bounded_adjustment(current_score=0.02, suggested_delta=-0.5, max_abs_delta=0.05) == 0.0
    assert bounded_adjustment(current_score=0.98, suggested_delta=0.5, max_abs_delta=0.05) == 1.0
    with pytest.raises(ValueError):
        bounded_adjustment(current_score=1.1, suggested_delta=0.01)
