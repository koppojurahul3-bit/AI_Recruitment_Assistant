
"""Shared data layer for the recruitment platform."""

from pathlib import Path
from typing import Optional

from backend.agents.orchestrator import RecruitmentOrchestrator
from backend.repositories.repository_factory import (
    create_candidate_repository,
)
from backend.services.candidate_intake_service import (
    CandidateIntakeService,
)


class RecruitmentDataStore:
    """Share one candidate repository across recruitment services."""

    def __init__(
        self,
        storage_backend: Optional[str] = None,
        database_path: Optional[str | Path] = None,
    ) -> None:
        self.repository = create_candidate_repository(
            storage_backend=storage_backend,
            database_path=database_path,
        )

        try:
            self.intake_service = CandidateIntakeService(
                repository=self.repository,
            )

            self.orchestrator = RecruitmentOrchestrator(
                candidate_repository=self.repository,
            )
        except Exception:
            close = getattr(self.repository, "close", None)
            if callable(close):
                close()
            raise

    def close(self) -> None:
        """Close the shared repository."""
        close = getattr(self.repository, "close", None)
        if callable(close):
            close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
