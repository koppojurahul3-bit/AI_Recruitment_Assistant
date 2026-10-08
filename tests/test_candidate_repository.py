from backend.models.candidate import Candidate
from backend.repositories.candidate_repository import CandidateRepository


def create_repository() -> CandidateRepository:
    repository = CandidateRepository()

    repository.add(
        Candidate(
            candidate_id="C001",
            name="Rahul Kumar",
            email="rahul@example.com",
            skills=[
                "Python",
                "Machine Learning",
                "SQL"
            ],
            experience_years=2.0,
            education=["B.Tech AI/ML"],
            projects=["AI Recruitment Assistant"],
            certifications=["Machine Learning"]
        )
    )

    repository.add(
        Candidate(
            candidate_id="C002",
            name="Ananya Sharma",
            email="ananya@example.com",
            skills=[
                "Python",
                "Deep Learning",
                "NLP"
            ],
            experience_years=3.0,
            education=["B.Tech CSE"],
            projects=["NLP Classification System"],
            certifications=[]
        )
    )

    repository.add(
        Candidate(
            candidate_id="C003",
            name="Vikram Reddy",
            email="vikram@example.com",
            skills=[
                "Java",
                "SQL",
                "Spring"
            ],
            experience_years=4.0,
            education=["B.Tech CSE"],
            projects=["Enterprise Backend Platform"],
            certifications=[]
        )
    )

    return repository


def test_candidate_can_be_added():
    repository = CandidateRepository()

    candidate = Candidate(
        candidate_id="C001",
        name="Rahul Kumar"
    )

    repository.add(candidate)

    assert repository.count() == 1
    assert repository.get_by_id("C001") == candidate


def test_duplicate_candidate_id_is_rejected():
    repository = CandidateRepository()

    candidate = Candidate(
        candidate_id="C001",
        name="Rahul Kumar"
    )

    repository.add(candidate)

    try:
        repository.add(candidate)
        assert False
    except ValueError:
        assert True


def test_get_all_candidates():
    repository = create_repository()

    candidates = repository.get_all()

    assert len(candidates) == 3


def test_search_by_skill():
    repository = create_repository()

    candidates = repository.search_by_skill("Python")

    assert len(candidates) == 2
    assert candidates[0].candidate_id == "C001"
    assert candidates[1].candidate_id == "C002"


def test_search_by_skills():
    repository = create_repository()

    candidates = repository.search_by_skills(
        ["NLP", "Deep Learning"]
    )

    assert len(candidates) == 1
    assert candidates[0].candidate_id == "C002"


def test_search_by_experience():
    repository = create_repository()

    candidates = repository.search_by_experience(3.0)

    assert len(candidates) == 2


def test_unknown_candidate_returns_none():
    repository = create_repository()

    candidate = repository.get_by_id("UNKNOWN")

    assert candidate is None


def test_repository_can_be_cleared():
    repository = create_repository()

    assert repository.count() == 3

    repository.clear()

    assert repository.count() == 0