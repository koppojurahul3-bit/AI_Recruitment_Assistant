
import pytest

from backend.agents.interview_scheduling_agent import InterviewSchedulingAgent
from backend.services.interview_scheduling_service import (
    InterviewSchedulingService,
)


@pytest.fixture
def service(tmp_path):
    return InterviewSchedulingService(tmp_path / "interviews.sqlite3")


def create_interview(service, **overrides):
    data = {
        "candidate_id": "C001",
        "candidate_name": "Alice",
        "candidate_email": "alice@example.com",
        "job_title": "ML Engineer",
        "interviewer": "Interviewer A",
        "start_time": "2027-01-15T10:00:00+05:30",
        "duration_minutes": 60,
        "timezone": "Asia/Kolkata",
        "interview_round": "Technical",
        "actor": "Test Recruiter",
    }
    data.update(overrides)
    return service.schedule_interview(**data)


def test_schedule_and_retrieve_interview(service):
    interview = create_interview(service)

    assert interview["candidate_id"] == "C001"
    assert interview["status"] == "proposed"
    assert interview["version"] == 1
    assert service.get_interview(interview["interview_id"])["job_title"] == "ML Engineer"


def test_records_persist_across_service_instances(tmp_path):
    path = tmp_path / "persistent.sqlite3"
    first = InterviewSchedulingService(path)
    created = create_interview(first)

    second = InterviewSchedulingService(path)
    assert second.get_interview(created["interview_id"]) is not None


def test_timezone_offset_is_required(service):
    with pytest.raises(ValueError, match="timezone offset"):
        create_interview(service, start_time="2027-01-15T10:00:00")


@pytest.mark.parametrize("duration", [0, 10, 481])
def test_invalid_duration_rejected(service, duration):
    with pytest.raises(ValueError, match="duration_minutes"):
        create_interview(service, duration_minutes=duration)


def test_invalid_email_rejected(service):
    with pytest.raises(ValueError, match="valid email"):
        create_interview(service, candidate_email="not-an-email")


def test_interviewer_conflict_is_rejected(service):
    create_interview(service)

    with pytest.raises(ValueError, match="Interviewer has a scheduling conflict"):
        create_interview(
            service,
            candidate_id="C002",
            candidate_email="bob@example.com",
            start_time="2027-01-15T10:30:00+05:30",
        )


def test_candidate_conflict_is_rejected(service):
    create_interview(service)

    with pytest.raises(ValueError, match="Candidate already has"):
        create_interview(
            service,
            interviewer="Interviewer B",
            start_time="2027-01-15T10:30:00+05:30",
        )


def test_non_overlapping_interviews_are_allowed(service):
    create_interview(service)
    second = create_interview(
        service,
        candidate_id="C002",
        candidate_email="bob@example.com",
        start_time="2027-01-15T11:00:00+05:30",
    )
    assert second["status"] == "proposed"


def test_confirm_cancel_and_invalid_transition(service):
    interview = create_interview(service)
    interview_id = interview["interview_id"]

    confirmed = service.confirm_interview(interview_id)
    assert confirmed["status"] == "confirmed"

    cancelled = service.cancel_interview(interview_id)
    assert cancelled["status"] == "cancelled"

    with pytest.raises(ValueError, match="Cannot transition"):
        service.confirm_interview(interview_id)


def test_reschedule_updates_record_and_audit(service):
    interview = create_interview(service)
    interview_id = interview["interview_id"]

    moved = service.reschedule_interview(
        interview_id,
        new_start_time="2027-01-16T10:00:00+05:30",
        actor="Recruiter",
    )

    assert moved["status"] == "rescheduled"
    assert moved["version"] == 2
    assert moved["start_time"].startswith("2027-01-16")

    history = service.get_audit_history(interview_id)
    assert any(item["event_type"] == "rescheduled" for item in history)


def test_reschedule_conflict_is_rejected(service):
    first = create_interview(service)
    create_interview(
        service,
        candidate_id="C002",
        candidate_email="bob@example.com",
        start_time="2027-01-16T10:00:00+05:30",
    )

    with pytest.raises(ValueError, match="conflict"):
        service.reschedule_interview(
            first["interview_id"],
            new_start_time="2027-01-16T10:30:00+05:30",
        )


def test_cancelled_interview_does_not_block_slot(service):
    first = create_interview(service)
    service.cancel_interview(first["interview_id"])

    second = create_interview(
        service,
        candidate_id="C002",
        candidate_email="bob@example.com",
    )
    assert second["status"] == "proposed"


def test_communication_is_a_draft_not_sent(service):
    interview = create_interview(service)

    draft = service.draft_communication(
        interview["interview_id"],
        "invitation",
    )

    assert draft["recipient"] == "alice@example.com"
    assert draft["status"] == "draft"
    assert draft["external_operation_performed"] is False
    assert "ML Engineer" in draft["subject"]
    assert "Alice" in draft["body"]

    communications = service.list_communications(interview["interview_id"])
    assert len(communications) == 1
    assert communications[0]["status"] == "draft"


def test_invalid_communication_type_is_rejected(service):
    interview = create_interview(service)

    with pytest.raises(ValueError, match="Unsupported communication"):
        service.draft_communication(interview["interview_id"], "spam")


def test_listing_can_filter_by_status_and_candidate(service):
    first = create_interview(service)
    create_interview(
        service,
        candidate_id="C002",
        candidate_email="bob@example.com",
        start_time="2027-01-16T10:00:00+05:30",
    )
    service.confirm_interview(first["interview_id"])

    assert len(service.list_interviews(status="confirmed")) == 1
    assert len(service.list_interviews(candidate_id="C002")) == 1


def test_missing_interview_raises_clear_error(service):
    with pytest.raises(ValueError, match="not found"):
        service.cancel_interview("missing-id")


def test_agent_exposes_schedule_and_communication(service):
    agent = InterviewSchedulingAgent(service=service)
    interview = agent.schedule_interview(
        candidate_id="C010",
        candidate_name="Neha",
        candidate_email="neha@example.com",
        job_title="Python Engineer",
        interviewer="Interviewer C",
        start_time="2027-02-01T09:00:00+05:30",
    )

    draft = agent.draft_communication(
        interview["interview_id"],
        "confirmation",
    )
    assert draft["status"] == "draft"
    assert agent.get_interview(interview["interview_id"]) is not None
