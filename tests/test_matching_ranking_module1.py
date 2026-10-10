
import pytest

from backend.models.candidate import Candidate
from backend.services.job_requirement_service import JobRequirements
from backend.services.matching_service import MatchResult, MatchingService
from backend.services.ranking_service import RankingService


def make_result(
    candidate_id,
    score,
    skill=80,
    experience=80,
    recommendation="Good Match",
):
    return MatchResult(
        candidate_id=candidate_id,
        skill_match_score=skill,
        experience_match_score=experience,
        education_match_score=80,
        overall_score=score,
        matched_skills=[],
        missing_skills=[],
        experience_gap=0,
        recommendation=recommendation,
    )


def test_matching_normalizes_and_deduplicates_skills():
    candidate = Candidate(
        candidate_id="C1",
        name="Candidate",
        skills=[" python ", "PYTHON", "SQL"],
        experience_years=2,
    )

    requirements = JobRequirements(
        required_skills=["Python", " python ", "SQL"],
        minimum_experience_years=2,
        education_requirements=[],
    )

    result = MatchingService().match(candidate, requirements)

    assert result.skill_match_score == 100.0
    assert result.matched_skills == ["Python", "SQL"]
    assert result.missing_skills == []


def test_matching_reports_missing_skills_and_experience_gap():
    candidate = Candidate(
        candidate_id="C2",
        name="Candidate",
        skills=["Python"],
        experience_years=1,
        education=["Mechanical Engineering"],
    )

    requirements = JobRequirements(
        required_skills=["Python", "SQL"],
        minimum_experience_years=2,
        education_requirements=["Computer Science"],
    )

    result = MatchingService().match(candidate, requirements)

    assert result.matched_skills == ["Python"]
    assert result.missing_skills == ["SQL"]
    assert result.experience_gap == 1.0
    assert result.education_match_score == 0.0


@pytest.mark.parametrize(
    "experience",
    [-1, float("nan"), float("inf")],
)
def test_matching_rejects_invalid_experience(experience):
    candidate = Candidate(
        candidate_id="C3",
        name="Candidate",
        experience_years=experience,
    )

    with pytest.raises(ValueError):
        MatchingService().match(candidate, JobRequirements())


def test_empty_requirements_return_full_neutral_scores():
    candidate = Candidate(
        candidate_id="C4",
        name="Candidate",
    )

    result = MatchingService().match(candidate, JobRequirements())

    assert result.skill_match_score == 100.0
    assert result.experience_match_score == 100.0
    assert result.education_match_score == 100.0
    assert result.overall_score == 100.0
    assert result.recommendation == "Strong Match"


def test_ranking_is_deterministic_without_mutating_input():
    items = [
        make_result("C10", 80),
        make_result("C11", 80),
    ]
    original = list(items)

    ranked = RankingService().rank(items)

    assert [item.candidate_id for item in ranked] == ["C11", "C10"]
    assert items == original
    assert [item.rank for item in ranked] == [1, 2]


def test_top_n_and_shortlist_threshold():
    service = RankingService()
    items = [
        make_result("C1", 90),
        make_result("C2", 70),
        make_result("C3", 69.99),
    ]

    assert [
        item.candidate_id for item in service.top_n(items, 2)
    ] == ["C1", "C2"]

    assert [
        item.candidate_id for item in service.shortlist(items, 70)
    ] == ["C1", "C2"]

    assert len(service.top_n(items, 100)) == 3


@pytest.mark.parametrize("n", [0, -1])
def test_top_n_rejects_non_positive_n(n):
    with pytest.raises(ValueError):
        RankingService().top_n([], n)


@pytest.mark.parametrize(
    "threshold",
    [-0.1, 100.1, float("nan"), float("inf")],
)
def test_shortlist_rejects_invalid_threshold(threshold):
    with pytest.raises(ValueError):
        RankingService().shortlist([], threshold)


def test_ranking_rejects_out_of_range_score():
    with pytest.raises(ValueError):
        RankingService().rank([make_result("C1", 101)])
