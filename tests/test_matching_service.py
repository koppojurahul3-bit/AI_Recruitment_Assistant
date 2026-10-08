from backend.models.candidate import Candidate
from backend.services.job_requirement_service import JobRequirements
from backend.services.matching_service import (
    MatchingService,
)


def create_service() -> MatchingService:
    return MatchingService()


def create_requirements() -> JobRequirements:
    return JobRequirements(
        required_skills=[
            "Python",
            "Machine Learning",
            "NLP",
            "SQL",
        ],
        minimum_experience_years=2.0,
        education_requirements=[
            "computer science",
        ],
        categories=[
            "Machine Learning",
            "NLP",
        ],
    )


def test_full_candidate_match():

    service = create_service()

    candidate = Candidate(
        candidate_id="C001",
        name="Rahul Kumar",
        skills=[
            "Python",
            "Machine Learning",
            "NLP",
            "SQL",
        ],
        experience_years=3.0,
        education=[
            "B.Tech Computer Science",
        ],
    )

    result = service.match(
        candidate,
        create_requirements(),
    )

    assert result.skill_match_score == 100.0
    assert result.experience_match_score == 100.0
    assert result.education_match_score == 100.0
    assert result.overall_score == 100.0

    assert result.matched_skills == [
        "Machine Learning",
        "NLP",
        "Python",
        "SQL",
    ]

    assert result.missing_skills == []
    assert result.experience_gap == 0.0
    assert result.recommendation == "Strong Match"


def test_partial_skill_match():

    service = create_service()

    candidate = Candidate(
        candidate_id="C002",
        name="Ananya",
        skills=[
            "Python",
            "SQL",
        ],
        experience_years=2.0,
        education=[
            "Computer Science",
        ],
    )

    result = service.match(
        candidate,
        create_requirements(),
    )

    assert result.skill_match_score == 50.0

    assert result.matched_skills == [
        "Python",
        "SQL",
    ]

    assert result.missing_skills == [
        "Machine Learning",
        "NLP",
    ]


def test_experience_gap_is_detected():

    service = create_service()

    candidate = Candidate(
        candidate_id="C003",
        name="Vikram",
        skills=[
            "Python",
            "Machine Learning",
            "NLP",
            "SQL",
        ],
        experience_years=1.0,
        education=[
            "Computer Science",
        ],
    )

    result = service.match(
        candidate,
        create_requirements(),
    )

    assert result.experience_match_score == 50.0
    assert result.experience_gap == 1.0


def test_exceeding_experience_gets_full_score():

    service = create_service()

    candidate = Candidate(
        candidate_id="C004",
        name="Priya",
        skills=[
            "Python",
        ],
        experience_years=5.0,
        education=[],
    )

    result = service.match(
        candidate,
        JobRequirements(
            required_skills=[],
            minimum_experience_years=3.0,
            education_requirements=[],
            categories=[],
        ),
    )

    assert result.experience_match_score == 100.0


def test_no_experience_requirement_gets_full_score():

    service = create_service()

    candidate = Candidate(
        candidate_id="C005",
        name="Arjun",
        skills=[
            "Python",
        ],
        experience_years=0.0,
        education=[],
    )

    result = service.match(
        candidate,
        JobRequirements(
            required_skills=["Python"],
            minimum_experience_years=0.0,
            education_requirements=[],
            categories=[],
        ),
    )

    assert result.experience_match_score == 100.0


def test_no_skill_requirement_gets_full_score():

    service = create_service()

    candidate = Candidate(
        candidate_id="C006",
        name="Neha",
        skills=[],
        experience_years=2.0,
        education=[],
    )

    result = service.match(
        candidate,
        JobRequirements(
            required_skills=[],
            minimum_experience_years=0.0,
            education_requirements=[],
            categories=[],
        ),
    )

    assert result.skill_match_score == 100.0
    assert result.overall_score == 100.0


def test_missing_education_reduces_score():

    service = create_service()

    candidate = Candidate(
        candidate_id="C007",
        name="Kiran",
        skills=[
            "Python",
            "Machine Learning",
            "NLP",
            "SQL",
        ],
        experience_years=2.0,
        education=[
            "Mechanical Engineering",
        ],
    )

    result = service.match(
        candidate,
        create_requirements(),
    )

    assert result.education_match_score == 0.0
    assert result.overall_score == 85.0
    assert result.recommendation == "Strong Match"


def test_recommendation_levels():

    service = create_service()

    candidate = Candidate(
        candidate_id="C008",
        name="Test Candidate",
    )

    strong = service.match(
        candidate,
        JobRequirements(
            required_skills=[],
            minimum_experience_years=0,
            education_requirements=[],
            categories=[],
        ),
    )

    assert strong.recommendation == "Strong Match"

    good = service._recommendation(70)

    potential = service._recommendation(50)

    low = service._recommendation(49.99)

    assert good == "Good Match"
    assert potential == "Potential Match"
    assert low == "Low Match"


def test_skill_matching_is_case_insensitive():

    service = create_service()

    candidate = Candidate(
        candidate_id="C009",
        name="Test Candidate",
        skills=[
            "python",
            "MACHINE LEARNING",
        ],
    )

    requirements = JobRequirements(
        required_skills=[
            "Python",
            "Machine Learning",
        ],
        minimum_experience_years=0,
        education_requirements=[],
        categories=[],
    )

    result = service.match(
        candidate,
        requirements,
    )

    assert result.skill_match_score == 100.0
    assert result.missing_skills == []