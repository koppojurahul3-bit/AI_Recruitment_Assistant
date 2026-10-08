from backend.services.matching_service import MatchResult
from backend.services.ranking_service import (
    RankingService,
)


def create_service() -> RankingService:
    return RankingService()


def create_results():
    return [
        MatchResult(
            candidate_id="C001",
            skill_match_score=90.0,
            experience_match_score=100.0,
            education_match_score=100.0,
            overall_score=94.0,
            matched_skills=[
                "Python",
                "Machine Learning",
            ],
            missing_skills=[],
            experience_gap=0.0,
            recommendation="Strong Match",
        ),
        MatchResult(
            candidate_id="C002",
            skill_match_score=80.0,
            experience_match_score=100.0,
            education_match_score=100.0,
            overall_score=87.0,
            matched_skills=[
                "Python",
            ],
            missing_skills=[
                "NLP",
            ],
            experience_gap=0.0,
            recommendation="Good Match",
        ),
        MatchResult(
            candidate_id="C003",
            skill_match_score=70.0,
            experience_match_score=80.0,
            education_match_score=100.0,
            overall_score=76.0,
            matched_skills=[
                "Python",
            ],
            missing_skills=[
                "NLP",
            ],
            experience_gap=1.0,
            recommendation="Good Match",
        ),
        MatchResult(
            candidate_id="C004",
            skill_match_score=40.0,
            experience_match_score=50.0,
            education_match_score=0.0,
            overall_score=36.5,
            matched_skills=[
                "Python",
            ],
            missing_skills=[
                "NLP",
                "SQL",
            ],
            experience_gap=2.0,
            recommendation="Low Match",
        ),
    ]


def test_rank_candidates_by_overall_score():

    service = create_service()

    ranked = service.rank(
        create_results()
    )

    assert [candidate.candidate_id for candidate in ranked] == [
        "C001",
        "C002",
        "C003",
        "C004",
    ]

    assert [candidate.rank for candidate in ranked] == [
        1,
        2,
        3,
        4,
    ]


def test_rank_preserves_scores():

    service = create_service()

    ranked = service.rank(
        create_results()
    )

    assert ranked[0].overall_score == 94.0
    assert ranked[1].overall_score == 87.0
    assert ranked[2].overall_score == 76.0


def test_top_n_returns_requested_number():

    service = create_service()

    top_candidates = service.top_n(
        create_results(),
        2,
    )

    assert len(top_candidates) == 2

    assert [
        candidate.candidate_id
        for candidate in top_candidates
    ] == [
        "C001",
        "C002",
    ]


def test_top_n_one_returns_best_candidate():

    service = create_service()

    top_candidate = service.top_n(
        create_results(),
        1,
    )

    assert len(top_candidate) == 1
    assert top_candidate[0].candidate_id == "C001"


def test_top_n_larger_than_results_returns_all():

    service = create_service()

    top_candidates = service.top_n(
        create_results(),
        10,
    )

    assert len(top_candidates) == 4


def test_top_n_rejects_zero():

    service = create_service()

    try:
        service.top_n(
            create_results(),
            0,
        )
        assert False
    except ValueError:
        assert True


def test_top_n_rejects_negative_value():

    service = create_service()

    try:
        service.top_n(
            create_results(),
            -1,
        )
        assert False
    except ValueError:
        assert True


def test_shortlist_uses_score_threshold():

    service = create_service()

    shortlisted = service.shortlist(
        create_results(),
        minimum_score=70.0,
    )

    assert [
        candidate.candidate_id
        for candidate in shortlisted
    ] == [
        "C001",
        "C002",
        "C003",
    ]


def test_shortlist_can_use_custom_threshold():

    service = create_service()

    shortlisted = service.shortlist(
        create_results(),
        minimum_score=85.0,
    )

    assert [
        candidate.candidate_id
        for candidate in shortlisted
    ] == [
        "C001",
        "C002",
    ]


def test_shortlist_rejects_invalid_threshold():

    service = create_service()

    try:
        service.shortlist(
            create_results(),
            minimum_score=101.0,
        )
        assert False
    except ValueError:
        assert True


def test_equal_scores_have_deterministic_order():

    service = create_service()

    results = [
        MatchResult(
            candidate_id="C010",
            skill_match_score=80.0,
            experience_match_score=80.0,
            education_match_score=80.0,
            overall_score=80.0,
            matched_skills=[],
            missing_skills=[],
            experience_gap=0.0,
            recommendation="Good Match",
        ),
        MatchResult(
            candidate_id="C011",
            skill_match_score=80.0,
            experience_match_score=80.0,
            education_match_score=80.0,
            overall_score=80.0,
            matched_skills=[],
            missing_skills=[],
            experience_gap=0.0,
            recommendation="Good Match",
        ),
    ]

    ranked = service.rank(results)

    assert [
        candidate.candidate_id
        for candidate in ranked
    ] == [
        "C011",
        "C010",
    ]


def test_empty_results_return_empty_list():

    service = create_service()

    ranked = service.rank([])

    assert ranked == []


def test_empty_results_can_be_shortlisted():

    service = create_service()

    shortlisted = service.shortlist([])

    assert shortlisted == []