
import pytest

from backend.repositories.candidate_repository import CandidateRepository
from backend.repositories.sqlite_candidate_repository import (
    SQLiteCandidateRepository,
)
from backend.repositories.repository_factory import (
    create_candidate_repository,
)


def test_defaults_to_in_memory_repository(monkeypatch):
    monkeypatch.delenv("CANDIDATE_STORAGE", raising=False)

    repository = create_candidate_repository()

    assert type(repository) is CandidateRepository


def test_explicit_memory_backend_overrides_environment(monkeypatch):
    monkeypatch.setenv("CANDIDATE_STORAGE", "sqlite")

    repository = create_candidate_repository(storage_backend="memory")

    assert type(repository) is CandidateRepository


def test_creates_sqlite_repository_at_requested_path(tmp_path):
    database_path = tmp_path / "candidates.sqlite3"

    repository = create_candidate_repository(
        storage_backend="sqlite",
        database_path=database_path,
    )

    try:
        assert isinstance(repository, SQLiteCandidateRepository)
        assert database_path.exists()
        assert repository.count() == 0
    finally:
        repository.close()


def test_reads_backend_from_environment(monkeypatch, tmp_path):
    database_path = tmp_path / "environment.sqlite3"
    monkeypatch.setenv("CANDIDATE_STORAGE", "sqlite")
    monkeypatch.setenv("CANDIDATE_DATABASE_PATH", str(database_path))

    repository = create_candidate_repository()

    try:
        assert isinstance(repository, SQLiteCandidateRepository)
        assert database_path.exists()
    finally:
        repository.close()


def test_explicit_database_path_overrides_environment(
    monkeypatch,
    tmp_path,
):
    environment_path = tmp_path / "environment.sqlite3"
    explicit_path = tmp_path / "explicit.sqlite3"

    monkeypatch.setenv("CANDIDATE_STORAGE", "sqlite")
    monkeypatch.setenv(
        "CANDIDATE_DATABASE_PATH",
        str(environment_path),
    )

    repository = create_candidate_repository(
        database_path=explicit_path,
    )

    try:
        assert explicit_path.exists()
        assert not environment_path.exists()
    finally:
        repository.close()


def test_backend_selection_is_case_insensitive():
    repository = create_candidate_repository(storage_backend=" MEMORY ")

    assert type(repository) is CandidateRepository


def test_unsupported_backend_is_rejected():
    with pytest.raises(ValueError, match="Unsupported"):
        create_candidate_repository(storage_backend="postgres")


def test_non_string_backend_is_rejected():
    with pytest.raises(TypeError, match="must be a string"):
        create_candidate_repository(storage_backend=123)


def test_empty_sqlite_path_is_rejected():
    with pytest.raises(ValueError, match="cannot be empty"):
        create_candidate_repository(
            storage_backend="sqlite",
            database_path="   ",
        )


def test_non_string_sqlite_path_is_rejected():
    with pytest.raises(TypeError, match="Database path"):
        create_candidate_repository(
            storage_backend="sqlite",
            database_path=123,
        )
