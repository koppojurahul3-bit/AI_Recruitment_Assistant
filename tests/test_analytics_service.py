
import pytest

from backend.services.analytics_service import RecruitmentAnalyticsService


def create_state():
    return {
        "recruiter_goal": "Hire a Python developer.",
        "current_step": "completed",
        "candidates": [
            {"candidate_id": "C001", "name": "Rahul"},
            {"candidate_id": "C002", "name": "Arjun"},
            {"candidate_id": "C003", "name": "Kiran"},
        ],
        "evaluations": [
            {
                "candidate_id": "C001",
                "overall_score": 90,
                "recommendation": "Strong Match",
            },
            {
                "candidate_id": "C002",
                "overall_score": 70,
                "recommendation": "Good Match",
            },
            {
                "candidate_id": "C003",
                "overall_score": 50,
                "recommendation": "Potential Match",
            },
        ],
        "rankings": [
            {
                "candidate_id": "C001",
                "rank": 1,
                "overall_score": 90,
                "recommendation": "Strong Match",
            },
            {
                "candidate_id": "C002",
                "rank": 2,
                "overall_score": 70,
                "recommendation": "Good Match",
            },
            {
                "candidate_id": "C003",
                "rank": 3,
                "overall_score": 50,
                "recommendation": "Potential Match",
            },
        ],
        "requested_actions": [
            {"action_id": "A001", "status": "pending"},
            {"action_id": "A002", "status": "approved"},
            {"action_id": "A003", "status": "completed"},
            {"action_id": "A004", "status": "denied"},
        ],
        "approved_actions": [
            {"action_id": "A002", "status": "approved"},
        ],
        "completed_actions": [
            {"action_id": "A003", "status": "completed"},
        ],
        "verification_results": [
            {"action_id": "A003", "verified": True},
            {"action_id": "A004", "verified": False},
        ],
        "errors": [],
    }


def test_report_calculates_candidate_summary():
    report = RecruitmentAnalyticsService().generate_report(create_state())

    assert report["summary"]["total_candidates"] == 3
    assert report["summary"]["evaluated_candidates"] == 3
    assert report["summary"]["ranked_candidates"] == 3
    assert report["summary"]["average_match_score"] == 70
    assert report["summary"]["highest_match_score"] == 90
    assert report["summary"]["lowest_match_score"] == 50


def test_report_counts_recommendations():
    report = RecruitmentAnalyticsService().generate_report(create_state())

    assert report["recommendation_breakdown"] == {
        "Strong Match": 1,
        "Good Match": 1,
        "Potential Match": 1,
    }


def test_report_summarizes_actions():
    report = RecruitmentAnalyticsService().generate_report(create_state())

    assert report["actions"]["requested"] == 4
    assert report["actions"]["approved_records"] == 1
    assert report["actions"]["completed"] == 1
    assert report["actions"]["pending_approval"] == 1
    assert report["actions"]["denied"] == 1


def test_report_summarizes_verification():
    report = RecruitmentAnalyticsService().generate_report(create_state())

    assert report["verification"] == {
        "total_results": 2,
        "verified": 1,
        "failed": 1,
    }


def test_report_summarizes_audit_events():
    report = RecruitmentAnalyticsService().generate_report(
        create_state(),
        audit_events=[
            {
                "event_type": "approval",
                "outcome": "success",
            },
            {
                "event_type": "execution",
                "outcome": "blocked",
            },
            {
                "event_type": "execution",
                "outcome": "success",
            },
        ],
    )

    assert report["audit"]["event_count"] == 3
    assert report["audit"]["outcome_breakdown"] == {
        "success": 2,
        "blocked": 1,
    }
    assert report["audit"]["event_type_breakdown"] == {
        "approval": 1,
        "execution": 2,
    }


def test_empty_state_has_no_average_score():
    report = RecruitmentAnalyticsService().generate_report({})

    assert report["summary"]["total_candidates"] == 0
    assert report["summary"]["average_match_score"] is None
    assert report["recommendation_breakdown"] == {}
    assert report["actions"]["requested"] == 0


def test_invalid_scores_are_excluded_from_average():
    state = create_state()
    state["evaluations"] = [
        {"overall_score": 80},
        {"overall_score": "invalid"},
        {"overall_score": 120},
        {"overall_score": True},
        {"overall_score": 60},
    ]

    report = RecruitmentAnalyticsService().generate_report(state)

    assert report["summary"]["average_match_score"] == 70
    assert report["summary"]["evaluated_candidates"] == 5


def test_top_candidates_are_ordered_by_score():
    service = RecruitmentAnalyticsService()

    results = service.get_top_candidates(create_state(), limit=2)

    assert [item["candidate_id"] for item in results] == [
        "C001",
        "C002",
    ]
    assert results[0]["name"] == "Rahul"


def test_top_candidates_rejects_invalid_limit():
    service = RecruitmentAnalyticsService()

    with pytest.raises(ValueError, match="positive integer"):
        service.get_top_candidates(create_state(), limit=0)


def test_report_does_not_mutate_state():
    state = create_state()
    original_errors = list(state["errors"])
    original_candidates = [item.copy() for item in state["candidates"]]

    RecruitmentAnalyticsService().generate_report(state)

    assert state["errors"] == original_errors
    assert state["candidates"] == original_candidates


def test_report_includes_recruiter_goal_and_errors():
    state = create_state()
    state["errors"] = ["Example processing error."]

    report = RecruitmentAnalyticsService().generate_report(state)

    assert report["recruiter_goal"] == "Hire a Python developer."
    assert report["errors"] == ["Example processing error."]


def test_top_candidates_handles_missing_candidate_profile():
    state = create_state()
    state["candidates"] = []

    results = RecruitmentAnalyticsService().get_top_candidates(
        state,
        limit=1,
    )

    assert len(results) == 1
    assert results[0]["name"] == "Unknown"
    assert results[0]["candidate_id"] == "C001"
