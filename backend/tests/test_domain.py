import pytest
from pydantic import ValidationError

from app.domain import Category, Priority, Status, TriageResult
from app.domain.state_machine import (
    InvalidTransitionError,
    can_transition,
    validate_transition,
)

ALL_STATUSES = list(Status)

LEGAL_TRANSITIONS = {
    (Status.OPEN, Status.IN_PROGRESS),
    (Status.OPEN, Status.REJECTED),
    (Status.IN_PROGRESS, Status.RESOLVED),
    (Status.IN_PROGRESS, Status.REJECTED),
}


@pytest.mark.parametrize("current,target", sorted(LEGAL_TRANSITIONS, key=str))
def test_legal_transitions_are_allowed(current, target):
    assert can_transition(current, target) is True
    validate_transition(current, target)  # must not raise


@pytest.mark.parametrize(
    "current,target",
    [
        (c, t)
        for c in ALL_STATUSES
        for t in ALL_STATUSES
        if (c, t) not in LEGAL_TRANSITIONS
    ],
)
def test_illegal_transitions_are_rejected(current, target):
    assert can_transition(current, target) is False
    with pytest.raises(InvalidTransitionError):
        validate_transition(current, target)


@pytest.mark.parametrize("status", ALL_STATUSES)
def test_same_state_transition_is_illegal(status):
    assert can_transition(status, status) is False


@pytest.mark.parametrize("terminal", [Status.RESOLVED, Status.REJECTED])
def test_terminal_states_have_no_outgoing_transitions(terminal):
    for target in ALL_STATUSES:
        assert can_transition(terminal, target) is False


def test_invalid_transition_error_names_both_states():
    with pytest.raises(InvalidTransitionError) as exc_info:
        validate_transition(Status.RESOLVED, Status.OPEN)
    message = str(exc_info.value)
    assert "resolved" in message
    assert "open" in message


def _triage_kwargs(**overrides):
    kwargs = dict(
        category=Category.WATER,
        priority=Priority.NORMAL,
        summary="Water leak near main road",
        confidence=0.8,
    )
    kwargs.update(overrides)
    return kwargs


def test_triage_result_accepts_valid_data():
    result = TriageResult(**_triage_kwargs())
    assert result.confidence == 0.8


@pytest.mark.parametrize("confidence", [-0.01, 1.01, -1.0, 2.0])
def test_triage_result_rejects_confidence_outside_unit_range(confidence):
    with pytest.raises(ValidationError):
        TriageResult(**_triage_kwargs(confidence=confidence))


def test_triage_result_rejects_summary_over_140_chars():
    with pytest.raises(ValidationError):
        TriageResult(**_triage_kwargs(summary="x" * 141))


def test_triage_result_accepts_summary_at_140_chars():
    result = TriageResult(**_triage_kwargs(summary="x" * 140))
    assert len(result.summary) == 140
