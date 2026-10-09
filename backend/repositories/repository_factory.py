
import os
from pathlib import Path
from typing import Optional, Union

from backend.repositories.candidate_repository import CandidateRepository
from backend.repositories.sqlite_candidate_repository import (
    SQLiteCandidateRepository,
)


Repository = Union[CandidateRepository, SQLiteCandidateRepository]


def create_candidate_repository(
    storage_backend: Optional[str] = None,
    database_path: Optional[Union[str, Path]] = None,
) -> Repository:
    """
    Create a candidate repository using explicit settings or environment
    configuration.

    Environment variables:
        CANDIDATE_STORAGE: "memory" or "sqlite". Defaults to "memory".
        CANDIDATE_DATABASE_PATH: SQLite file path. Defaults to
            "data/candidates.sqlite3".

    Explicit function arguments take precedence over environment values.
    """

    selected_backend = (
        storage_backend
        if storage_backend is not None
        else os.getenv("CANDIDATE_STORAGE", "memory")
    )

    if not isinstance(selected_backend, str):
        raise TypeError("Storage backend must be a string.")

    selected_backend = selected_backend.strip().lower()

    if selected_backend == "memory":
        return CandidateRepository()

    if selected_backend == "sqlite":
        selected_path = (
            database_path
            if database_path is not None
            else os.getenv(
                "CANDIDATE_DATABASE_PATH",
                "data/candidates.sqlite3",
            )
        )

        if not isinstance(selected_path, (str, Path)):
            raise TypeError("Database path must be a string or Path.")

        if not str(selected_path).strip():
            raise ValueError("Database path cannot be empty.")

        return SQLiteCandidateRepository(selected_path)

    raise ValueError(
        "Unsupported candidate storage backend. "
        "Choose 'memory' or 'sqlite'."
    )
