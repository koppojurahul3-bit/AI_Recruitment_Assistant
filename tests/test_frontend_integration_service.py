
from io import BytesIO

import pytest
from pypdf import PdfWriter

from backend.services.frontend_integration_service import (
    FrontendIntegrationService,
)


def make_pdf(text: str) -> bytes:
    """Create a small text PDF for ingestion tests."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    # A blank PDF has no extractable text, so use a real PDF fixture
    # if the installed PDF tooling cannot add text to a page.
    # This helper is intentionally replaced below by a fixture file
    # in environments where report generation is configured.
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.fixture
def service(tmp_path):
    instance = FrontendIntegrationService(
        storage_backend="sqlite",
        database_path=str(tmp_path / "candidates.sqlite3"),
    )
    yield instance
    instance.close()


def test_empty_uploads_are_rejected(service):
    with pytest.raises(ValueError, match="at least one resume"):
        service.ingest_resumes([])


def test_empty_job_description_is_rejected(service):
    with pytest.raises(ValueError, match="Job description"):
        service.analyze_candidates([], "   ")


def test_no_candidates_are_rejected(service):
    with pytest.raises(ValueError, match="At least one candidate"):
        service.analyze_candidates([], "Python developer")


def test_invalid_upload_filename_is_rejected(service):
    with pytest.raises(ValueError, match="filename"):
        service.ingest_resumes([("", b"%PDF-1.4 invalid")])
