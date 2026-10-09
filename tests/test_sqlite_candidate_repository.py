
import pytest

from backend.models.candidate import Candidate
from backend.repositories.sqlite_candidate_repository import (
    SQLiteCandidateRepository,
)


@pytest.fixture
def repository(tmp_path):
    repo = SQLiteCandidateRepository(tmp_path / "candidates.sqlite3")
    yield repo
    repo.close()


def make_candidate(candidate_id="candidate-1", **overrides):
    values = {
        "candidate_id": candidate_id,
        "name": "Asha Rao",
        "email": "asha@example.com",
        "phone": "1234567890",
        "skills": ["Python", "SQL"],
        "experience_years": 3.5,
        "education": ["B.Tech"],
        "projects": ["Recruitment platform"],
        "certifications": ["Python Certificate"],
        "resume_text": "Experienced Python developer",
        "source": "resume.pdf",
    }
    values.update(overrides)
    return Candidate(**values)


def test_add_and_retrieve_candidate(repository):
    candidate = make_candidate()
    assert repository.add(candidate) is candidate
    assert repository.get_by_id("candidate-1") == candidate


def test_candidate_persists_across_repository_instances(tmp_path):
    database = tmp_path / "persistent.sqlite3"

    with SQLiteCandidateRepository(database) as first:
        first.add(make_candidate())

    with SQLiteCandidateRepository(database) as second:
        assert second.get_by_id("candidate-1") == make_candidate()
        assert second.count() == 1


def test_duplicate_candidate_id_is_rejected(repository):
    repository.add(make_candidate())

    with pytest.raises(ValueError, match="already exists"):
        repository.add(make_candidate(name="Different Person"))

    assert repository.count() == 1


def test_missing_candidate_returns_none(repository):
    assert repository.get_by_id("missing") is None


def test_get_all_returns_candidates_in_insertion_order(repository):
    first = make_candidate("first")
    second = make_candidate("second")

    repository.add(first)
    repository.add(second)

    assert repository.get_all() == [first, second]


def test_list_fields_round_trip_through_database(repository):
    candidate = make_candidate(
        skills=["Python", "ML"],
        education=["B.Tech", "M.Tech"],
        projects=["Project A", "Project B"],
        certifications=["Certificate A"],
    )

    repository.add(candidate)
    stored = repository.get_by_id(candidate.candidate_id)

    assert stored is not None
    assert stored.skills == candidate.skills
    assert stored.education == candidate.education
    assert stored.projects == candidate.projects
    assert stored.certifications == candidate.certifications


def test_search_by_skill_is_case_insensitive(repository):
    repository.add(make_candidate())

    assert repository.search_by_skill("python") == [
        make_candidate()
    ]


def test_search_by_skill_requires_exact_match(repository):
    repository.add(make_candidate())

    assert repository.search_by_skill("py") == []


def test_search_by_multiple_skills_matches_any_requested_skill(repository):
    first = make_candidate("first", skills=["Python"])
    second = make_candidate("second", skills=["Java"])
    third = make_candidate("third", skills=["Design"])

    for candidate in (first, second, third):
        repository.add(candidate)

    assert repository.search_by_skills(["python", "JAVA"]) == [
        first,
        second,
    ]


def test_search_by_experience_uses_minimum_threshold(repository):
    junior = make_candidate("junior", experience_years=1)
    senior = make_candidate("senior", experience_years=5)

    repository.add(junior)
    repository.add(senior)

    assert repository.search_by_experience(5) == [senior]


def test_count_tracks_insertions(repository):
    assert repository.count() == 0

    repository.add(make_candidate("one"))
    repository.add(make_candidate("two"))

    assert repository.count() == 2


def test_clear_removes_all_records(repository):
    repository.add(make_candidate())
    repository.clear()

    assert repository.get_all() == []
    assert repository.count() == 0


def test_invalid_candidate_type_is_rejected(repository):
    with pytest.raises(TypeError, match="Candidate instance"):
        repository.add({"candidate_id": "one"})


def test_blank_candidate_id_is_rejected(repository):
    with pytest.raises(ValueError, match="non-empty"):
        repository.add(make_candidate("   "))

    assert repository.count() == 0


def test_invalid_list_fields_are_rejected(repository):
    candidate = make_candidate(skills="Python")

    with pytest.raises(ValueError, match="list of strings"):
        repository.add(candidate)

    assert repository.count() == 0


def test_negative_experience_is_rejected(repository):
    candidate = make_candidate(experience_years=-1)

    with pytest.raises(ValueError, match="cannot be negative"):
        repository.add(candidate)

    assert repository.count() == 0


def test_invalid_search_arguments_are_rejected(repository):
    with pytest.raises(TypeError, match="Skill must be a string"):
        repository.search_by_skill(123)

    with pytest.raises(TypeError, match="list of strings"):
        repository.search_by_skills("Python")

    with pytest.raises(TypeError, match="must be numeric"):
        repository.search_by_experience("three")


def test_empty_database_can_be_reopened(tmp_path):
    database = tmp_path / "empty.sqlite3"

    with SQLiteCandidateRepository(database) as first:
        assert first.count() == 0

    with SQLiteCandidateRepository(database) as second:
        assert second.get_all() == []
