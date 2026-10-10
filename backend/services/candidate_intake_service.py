"""Integration service for persistent resume intake."""

from inspect import getattr_static
from pathlib import Path
from typing import Optional

from backend.models.candidate import Candidate
from backend.repositories.candidate_repository import CandidateRepository
from backend.repositories.repository_factory import create_candidate_repository
from backend.services.resume_ingestion_service import ResumeIngestionService


class CandidateIntakeService:
    """Connect PDF resume ingestion to a configurable candidate repository."""

    def __init__(
        self,
        storage_backend: Optional[str] = None,
        database_path: Optional[str | Path] = None,
        ingestion_service: Optional[ResumeIngestionService] = None,
        candidate_repository: Optional[CandidateRepository] = None,
    ) -> None:
        if candidate_repository is not None:
            if storage_backend is not None or database_path is not None:
                raise ValueError(
                    "Pass either candidate_repository or storage configuration, not both."
                )
            self.repository = candidate_repository
        else:
            self.repository = create_candidate_repository(
                storage_backend=storage_backend,
                database_path=database_path,
            )

        if ingestion_service is not None:
            # getattr_static avoids treating dynamically generated Mock attributes
            # as a real repository when existing tests inject a bare Mock.
            configured_repository = getattr_static(
                ingestion_service, "candidate_repository", None
            )
            ingestion_repository = (
                getattr(ingestion_service, "candidate_repository")
                if configured_repository is not None
                else None
            )
            if (
                ingestion_repository is not None
                and ingestion_repository is not self.repository
            ):
                raise ValueError(
                    "The ingestion service and intake service must use "
                    "the same candidate repository."
                )
            self.ingestion_service = ingestion_service
        else:
            self.ingestion_service = ResumeIngestionService(
                candidate_repository=self.repository
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
