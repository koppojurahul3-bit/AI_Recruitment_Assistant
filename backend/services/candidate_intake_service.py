
"""Integration service for persistent resume intake."""

from pathlib import Path
from typing import Optional

from backend.models.candidate import Candidate
from backend.repositories.repository_factory import (
    create_candidate_repository,
)
from backend.services.resume_ingestion_service import (
    ResumeIngestionService,
)


class CandidateIntakeService:
    """Connect PDF resume ingestion to a configurable candidate repository."""

    def __init__(
        self,
        storage_backend: Optional[str] = None,
        database_path: Optional[str | Path] = None,
        ingestion_service: Optional[ResumeIngestionService] = None,
    ) -> None:
        self.repository = create_candidate_repository(
            storage_backend=storage_backend,
            database_path=database_path,
        )

        self.ingestion_service = (
            ingestion_service
            if ingestion_service is not None
            else ResumeIngestionService(
                candidate_repository=self.repository
            )
        )

    def ingest_pdf(
        self,
        filename: str,
        file_bytes: bytes,
        candidate_id: Optional[str] = None,
    ) -> Candidate:
        """Ingest a PDF and return its stored candidate."""
        return self.ingestion_service.ingest_pdf(
            filename=filename,
            file_bytes=file_bytes,
            candidate_id=candidate_id,
        )

    def close(self) -> None:
        """Close the repository if it supports closing."""
        close = getattr(self.repository, "close", None)
        if callable(close):
            close()
