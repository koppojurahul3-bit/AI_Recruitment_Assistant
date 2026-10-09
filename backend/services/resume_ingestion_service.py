
from io import BytesIO
from typing import Optional
from uuid import uuid4

from PyPDF2 import PdfReader

from backend.models.candidate import Candidate
from backend.repositories.candidate_repository import CandidateRepository
from backend.services.resume_intelligence_service import (
    ResumeIntelligenceService,
)


class ResumeIngestionService:
    """
    Validates PDF resume uploads, extracts text, analyzes the resume,
    and stores the resulting candidate in the repository.

    Input is PDF bytes. This service does not save uploaded files
    to disk or perform OCR on image-only/scanned PDFs.
    """

    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

    def __init__(
        self,
        candidate_repository: Optional[CandidateRepository] = None,
        resume_intelligence_service: Optional[
            ResumeIntelligenceService
        ] = None,
    ):
        self.candidate_repository = (
            candidate_repository
            if candidate_repository is not None
            else CandidateRepository()
        )

        self.resume_intelligence_service = (
            resume_intelligence_service
            if resume_intelligence_service is not None
            else ResumeIntelligenceService()
        )

    def ingest_pdf(
        self,
        filename: str,
        file_bytes: bytes,
        candidate_id: Optional[str] = None,
    ) -> Candidate:
        """Process one PDF and return its stored candidate record."""

        self._validate_upload(filename, file_bytes)

        resolved_candidate_id = (
            candidate_id.strip()
            if isinstance(candidate_id, str) and candidate_id.strip()
            else str(uuid4())
        )

        if candidate_id is not None and (
            not isinstance(candidate_id, str)
            or not candidate_id.strip()
        ):
            raise ValueError(
                "Candidate ID must be None or a non-empty string."
            )

        if self.candidate_repository.get_by_id(
            resolved_candidate_id
        ) is not None:
            raise ValueError(
                f"Candidate ID already exists: {resolved_candidate_id}"
            )

        resume_text = self._extract_text(file_bytes)

        candidate = self.resume_intelligence_service.analyze(
            resume_text=resume_text,
            candidate_id=resolved_candidate_id,
        )

        # Keep the uploaded filename as source metadata.
        candidate.source = filename.strip()

        self.candidate_repository.add(candidate)

        return candidate

    def _validate_upload(
        self,
        filename: str,
        file_bytes: bytes,
    ) -> None:
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("A filename is required.")

        if not filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF resumes are supported.")

        if not isinstance(file_bytes, bytes):
            raise TypeError("Uploaded file content must be bytes.")

        if not file_bytes:
            raise ValueError("The uploaded PDF is empty.")

        if len(file_bytes) > self.MAX_FILE_SIZE_BYTES:
            raise ValueError(
                "PDF exceeds the maximum allowed size of 10 MB."
            )

        if not file_bytes.startswith(b"%PDF-"):
            raise ValueError("The uploaded file is not a valid PDF.")

    @staticmethod
    def _extract_text(file_bytes: bytes) -> str:
        try:
            reader = PdfReader(BytesIO(file_bytes), strict=True)

            if reader.is_encrypted:
                raise ValueError(
                    "Encrypted PDFs are not supported."
                )

            if not reader.pages:
                raise ValueError("The PDF contains no pages.")

            extracted_pages = []

            for page in reader.pages:
                extracted = page.extract_text() or ""
                extracted_pages.append(extracted)

            text = "\n".join(extracted_pages).strip()

            if not text:
                raise ValueError(
                    "No readable text was found. "
                    "The PDF may be scanned or image-only."
                )

            return text

        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(
                "Could not read the PDF. The file may be damaged "
                "or use an unsupported PDF structure."
            ) from exc
