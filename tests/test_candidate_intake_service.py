
from unittest.mock import Mock

import pytest

from backend.repositories.candidate_repository import CandidateRepository
from backend.repositories.sqlite_candidate_repository import (
    SQLiteCandidateRepository,
)
from backend.services.candidate_intake_service import CandidateIntakeService


def test_default_storage_uses_memory_repository():
    ingestion = Mock()

    service = CandidateIntakeService(ingestion_service=ingestion)

    assert isinstance(service.repository, CandidateRepository)
    service.close()


def test_sqlite_storage_uses_configured_database(tmp_path):
    database_path = tmp_path / "candidates.sqlite3"
    ingestion = Mock()

    service = CandidateIntakeService(
        storage_backend="sqlite",
        database_path=database_path,
        ingestion_service=ingestion,
    )

    assert isinstance(service.repository, SQLiteCandidateRepository)
    service.close()


def test_ingest_pdf_delegates_to_existing_service():
    ingestion = Mock()
    ingestion.ingest_pdf.return_value = {"status": "processed"}

    service = CandidateIntakeService(ingestion_service=ingestion)

    result = service.ingest_pdf(b"%PDF-test", filename="resume.pdf")

    assert result == {"status": "processed"}
    ingestion.ingest_pdf.assert_called_once_with(
        b"%PDF-test",
        filename="resume.pdf",
    )
    service.close()


def test_sqlite_repository_can_be_reopened(tmp_path):
    database_path = tmp_path / "candidates.sqlite3"

    first = CandidateIntakeService(
        storage_backend="sqlite",
        database_path=database_path,
        ingestion_service=Mock(),
    )
    assert isinstance(first.repository, SQLiteCandidateRepository)
    first.close()

    second = CandidateIntakeService(
        storage_backend="sqlite",
        database_path=database_path,
        ingestion_service=Mock(),
    )
    assert isinstance(second.repository, SQLiteCandidateRepository)
    second.close()
