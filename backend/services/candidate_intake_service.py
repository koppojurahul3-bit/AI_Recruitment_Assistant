
"""Resume intake using a configurable, shareable candidate repository."""

from pathlib import Path
from typing import Any, Optional

from backend.repositories.repository_factory import (
    create_candidate_repository,
)
from backend.services.resume_ingestion_service import (
    ResumeIngestionService,
)


class CandidateIntakeService:
    """Connect PDF ingestion to a configurable candidate repository."""

    def __init__(
        self,
        storage_backend: Optional[str] = None,
        database_path: Optional[str | Path] = None,
        ingestion_service: Optional[Any] = None,
        candidate_repository: Optional[Any] = None,
        repository: Optional[Any] = None,
    ) -> None:
        if (
            candidate_repository is not None
            and repository is not None
            and candidate_repository is not repository
        ):
            raise ValueError(
                "candidate_repository and repository must reference "
                "the same candidate repository."
            )

        supplied_repository = (
            candidate_repository
            if candidate_repository is not None
            else repository
        )

        self._owns_repository = supplied_repository is None

        if supplied_repository is None:
            self.repository = create_candidate_repository(
                storage_backend=storage_backend,
                database_path=database_path,
            )
        else:
            self.repository = supplied_repository

        if ingestion_service is None:
            self.ingestion_service = ResumeIngestionService(
                candidate_repository=self.repository
            )
        else:
            self.ingestion_service = ingestion_service

        # Validate actual repository wiring without rejecting ordinary
        # mocked ingestion services that do not declare a repository.
        service_attributes = getattr(
            self.ingestion_service,
            "__dict__",
            {},
        )

        has_explicit_repository = (
            isinstance(
                self.ingestion_service,
                ResumeIngestionService,
            )
            or "candidate_repository" in service_attributes
        )

        if has_explicit_repository:
            ingestion_repository = getattr(
                self.ingestion_service,
                "candidate_repository",
                None,
            )

            if (
                ingestion_repository is not None
                and ingestion_repository is not self.repository
            ):
                if self._owns_repository:
                    self._close_repository()

                raise ValueError(
                    "The ingestion service and intake service must use "
                    "the same candidate repository."
                )

    def ingest_pdf(
        self,
        filename: str,
        file_bytes: bytes,
        candidate_id: Optional[str] = None,
    ) -> Any:
        """Delegate PDF ingestion and return its candidate record."""
        return self.ingestion_service.ingest_pdf(
            filename=filename,
            file_bytes=file_bytes,
            candidate_id=candidate_id,
        )

    def _close_repository(self) -> None:
        """Close the repository if it supports closing."""
        close = getattr(self.repository, "close", None)

        if callable(close):
            close()

    def close(self) -> None:
        """Close only repositories created and owned by this service."""
        if self._owns_repository:
            self._close_repository()
