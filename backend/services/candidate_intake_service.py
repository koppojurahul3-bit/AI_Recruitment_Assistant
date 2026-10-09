
"""Integration service for persistent resume intake."""

from pathlib import Path
from typing import Any, Optional

from backend.repositories.repository_factory import (
    create_candidate_repository,
)
from backend.services.resume_ingestion_service import (
    ResumeIngestionService,
)


class CandidateIntakeService:
    """Connect resume PDF ingestion to a configurable candidate repository.

    Storage configuration is delegated to the repository factory.
    Existing repository, ingestion, and V1 application modules remain unchanged.
    """

    def __init__(
        self,
        storage_backend: Optional[str] = None,
        database_path: Optional[str | Path] = None,
        ingestion_service: Optional[Any] = None,
    ) -> None:
        self.repository = create_candidate_repository(
            storage_backend=storage_backend,
            database_path=database_path,
        )

        self.ingestion_service = (
            ingestion_service
            if ingestion_service is not None
            else ResumeIngestionService(repository=self.repository)
        )

    def ingest_pdf(self, *args: Any, **kwargs: Any) -> Any:
        """Delegate PDF ingestion to the existing ingestion pipeline."""
        return self.ingestion_service.ingest_pdf(*args, **kwargs)

    def close(self) -> None:
        """Close the repository when it supports an explicit close operation."""
        close = getattr(self.repository, "close", None)
        if callable(close):
            close()
