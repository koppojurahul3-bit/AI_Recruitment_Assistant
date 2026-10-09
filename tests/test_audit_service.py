
import pytest

from backend.services.audit_service import AuditService, AuditEvent


def test_log_event_creates_structured_event():
    service = AuditService()

    event = service.log_event(
        event_type="candidate_evaluated",
        actor="CandidateEvaluationAgent",
        description="Candidate evaluation completed.",
        candidate_id="C001",
        outcome="success",
        details={"score": 87},
    )

    assert isinstance(event, AuditEvent)
    assert event.event_id
    assert event.timestamp.endswith("+00:00")
    assert event.event_type == "candidate_evaluated"
    assert event.actor == "CandidateEvaluationAgent"
    assert event.candidate_id == "C001"
    assert event.outcome == "success"
    assert event.details == {"score": 87}
    assert service.count() == 1


def test_event_ids_are_unique():
    service = AuditService()

    first = service.log_event("search", "Recruiter", "Search started.")
    second = service.log_event("search", "Recruiter", "Search repeated.")

    assert first.event_id != second.event_id


def test_get_events_filters_by_event_type():
    service = AuditService()
    service.log_event("search", "Recruiter", "Search started.")
    service.log_event("approval", "Recruiter", "Action approved.")

    results = service.get_events(event_type="approval")

    assert len(results) == 1
    assert results[0].event_type == "approval"


def test_get_events_filters_by_candidate_and_outcome():
    service = AuditService()
    service.log_event(
        "evaluation",
        "Evaluator",
        "Evaluation completed.",
        candidate_id="C001",
        outcome="success",
    )
    service.log_event(
        "evaluation",
        "Evaluator",
        "Evaluation failed.",
        candidate_id="C002",
        outcome="failure",
    )

    results = service.get_events(
        candidate_id="C001",
        outcome="success",
    )

    assert len(results) == 1
    assert results[0].candidate_id == "C001"


def test_get_events_filters_by_action_id():
    service = AuditService()
    service.log_event(
        "execution",
        "ExecutionAgent",
        "First action.",
        action_id="A001",
    )
    service.log_event(
        "execution",
        "ExecutionAgent",
        "Second action.",
        action_id="A002",
    )

    results = service.get_events(action_id="A002")

    assert len(results) == 1
    assert results[0].action_id == "A002"


def test_get_event_by_id_finds_existing_event():
    service = AuditService()
    event = service.log_event("search", "Recruiter", "Search started.")

    assert service.get_event_by_id(event.event_id) == event


def test_get_event_by_id_returns_none_for_unknown_id():
    service = AuditService()

    assert service.get_event_by_id("unknown-id") is None


def test_invalid_required_fields_are_rejected():
    service = AuditService()

    with pytest.raises(ValueError, match="event_type"):
        service.log_event("", "Recruiter", "Search started.")

    with pytest.raises(ValueError, match="actor"):
        service.log_event("search", " ", "Search started.")

    with pytest.raises(ValueError, match="description"):
        service.log_event("search", "Recruiter", "")


def test_invalid_outcome_is_rejected():
    service = AuditService()

    with pytest.raises(ValueError, match="Unsupported audit outcome"):
        service.log_event(
            "execution",
            "ExecutionAgent",
            "Action attempted.",
            outcome="unknown",
        )


def test_details_must_be_a_dictionary():
    service = AuditService()

    with pytest.raises(TypeError, match="dictionary"):
        service.log_event(
            "search",
            "Recruiter",
            "Search started.",
            details=["not", "a", "dictionary"],
        )


def test_filters_can_be_combined():
    service = AuditService()
    service.log_event(
        "execution",
        "ExecutionAgent",
        "First action succeeded.",
        candidate_id="C001",
        action_id="A001",
        outcome="success",
    )
    service.log_event(
        "execution",
        "ExecutionAgent",
        "Second action was blocked.",
        candidate_id="C001",
        action_id="A002",
        outcome="blocked",
    )

    results = service.get_events(
        event_type="execution",
        candidate_id="C001",
        action_id="A002",
        outcome="blocked",
    )

    assert len(results) == 1
    assert results[0].action_id == "A002"


def test_clear_removes_all_events():
    service = AuditService()
    service.log_event("search", "Recruiter", "Search started.")
    service.log_event("approval", "Recruiter", "Action approved.")

    service.clear()

    assert service.count() == 0
    assert service.get_events() == []


def test_invalid_event_id_is_rejected():
    service = AuditService()

    with pytest.raises(ValueError, match="valid event ID"):
        service.get_event_by_id(" ")
