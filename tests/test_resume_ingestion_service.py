
from io import BytesIO

import pytest
from reportlab.pdfgen import canvas

from backend.models.candidate import Candidate
from backend.repositories.candidate_repository import CandidateRepository
from backend.services.resume_ingestion_service import ResumeIngestionService


def create_pdf(text: str) -> bytes:
    """Create a small text-based PDF in memory for testing."""

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 750, text)
    pdf.save()

    return buffer.getvalue()


def create_repository() -> CandidateRepository:
    return CandidateRepository()


def test_ingests_pdf_and_stores_candidate():
    repository = create_repository()
    service = ResumeIngestionService(repository)

    pdf_bytes = create_pdf(
        "Rahul Kumar\n"
        "Email: rahul@example.com\n"
        "Python Machine Learning SQL\n"
        "Education: B.Tech\n"
        "Experience: 3 years"
    )

    candidate = service.ingest_pdf(
        filename="rahul_resume.pdf",
        file_bytes=pdf_bytes,
        candidate_id="C001",
    )

    assert candidate.candidate_id == "C001"
    assert candidate.source == "rahul_resume.pdf"
    assert candidate.resume_text
    assert repository.get_by_id("C001") is candidate


def test_generated_candidate_id_is_stored():
    repository = create_repository()
    service = ResumeIngestionService(repository)

    candidate = service.ingest_pdf(
        filename="resume.pdf",
        file_bytes=create_pdf("Python developer with SQL skills."),
    )

    assert candidate.candidate_id
    assert repository.get_by_id(candidate.candidate_id) is candidate


def test_rejects_non_pdf_filename():
    service = ResumeIngestionService(create_repository())

    with pytest.raises(ValueError, match="Only PDF"):
        service.ingest_pdf("resume.docx", b"not a PDF")


def test_rejects_empty_file():
    service = ResumeIngestionService(create_repository())

    with pytest.raises(ValueError, match="empty"):
        service.ingest_pdf("resume.pdf", b"")


def test_rejects_invalid_pdf_header():
    service = ResumeIngestionService(create_repository())

    with pytest.raises(ValueError, match="not a valid PDF"):
        service.ingest_pdf("resume.pdf", b"not-a-pdf")


def test_rejects_non_bytes_content():
    service = ResumeIngestionService(create_repository())

    with pytest.raises(TypeError, match="must be bytes"):
        service.ingest_pdf("resume.pdf", "not bytes")


def test_rejects_missing_filename():
    service = ResumeIngestionService(create_repository())

    with pytest.raises(ValueError, match="filename is required"):
        service.ingest_pdf(" ", create_pdf("Python developer."))


def test_rejects_oversized_pdf():
    service = ResumeIngestionService(create_repository())
    oversized = b"%PDF-" + (
        b"x" * ResumeIngestionService.MAX_FILE_SIZE_BYTES
    )

    with pytest.raises(ValueError, match="10 MB"):
        service.ingest_pdf("resume.pdf", oversized)


def test_rejects_duplicate_candidate_id():
    repository = create_repository()
    repository.add(
        Candidate(
            candidate_id="C001",
            name="Existing Candidate",
        )
    )
    service = ResumeIngestionService(repository)

    with pytest.raises(ValueError, match="already exists"):
        service.ingest_pdf(
            "another_resume.pdf",
            create_pdf("Python developer."),
            candidate_id="C001",
        )



def test_rejects_pdf_without_readable_text():
    service = ResumeIngestionService(create_repository())

    # Create a valid, one-page PDF containing no text.
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.showPage()
    pdf.save()

    with pytest.raises(ValueError, match="No readable text"):
        service.ingest_pdf("blank.pdf", buffer.getvalue())


def test_rejects_blank_candidate_id():
    service = ResumeIngestionService(create_repository())

    with pytest.raises(ValueError, match="Candidate ID"):
        service.ingest_pdf(
            "resume.pdf",
            create_pdf("Python developer."),
            candidate_id=" ",
        )


def test_rejects_corrupted_pdf():
    service = ResumeIngestionService(create_repository())

    with pytest.raises(ValueError, match="Could not read the PDF"):
        service.ingest_pdf(
            "corrupted.pdf",
            b"%PDF-1.4\nthis is not a valid PDF structure",
        )
