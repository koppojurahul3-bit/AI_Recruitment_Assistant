import re
from typing import List

from backend.models.candidate import Candidate


class ResumeIntelligenceService:
    """
    Extracts structured candidate information from resume text.
    """

    SKILL_KEYWORDS = {
        "python": "Python",
        "java": "Java",
        "c++": "C++",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "sql": "SQL",
        "machine learning": "Machine Learning",
        "deep learning": "Deep Learning",
        "natural language processing": "NLP",
        "nlp": "NLP",
        "generative ai": "Generative AI",
        "llm": "LLM",
        "langchain": "LangChain",
        "tensorflow": "TensorFlow",
        "pytorch": "PyTorch",
        "scikit-learn": "Scikit-Learn",
        "pandas": "Pandas",
        "numpy": "NumPy",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "GCP",
        "git": "Git",
        "github": "GitHub",
        "fastapi": "FastAPI",
        "flask": "Flask",
        "django": "Django",
        "react": "React",
        "node.js": "Node.js",
        "mongodb": "MongoDB",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "rag": "RAG",
        "faiss": "FAISS",
        "chromadb": "ChromaDB",
    }

    def analyze(
        self,
        resume_text: str,
        candidate_id: str = "UNKNOWN"
    ) -> Candidate:
        """
        Convert raw resume text into a structured Candidate.
        """

        if not isinstance(resume_text, str):
            raise TypeError(
                "Resume text must be a string."
            )

        if not candidate_id:
            raise ValueError(
                "Candidate ID cannot be empty."
            )

        cleaned_text = self._clean_text(resume_text)

        return Candidate(
            candidate_id=candidate_id,
            name=self._extract_name(cleaned_text),
            email=self._extract_email(cleaned_text),
            phone=self._extract_phone(cleaned_text),
            skills=self._extract_skills(cleaned_text),
            experience_years=self._extract_experience(cleaned_text),
            education=self._extract_education(cleaned_text),
            projects=self._extract_projects(cleaned_text),
            certifications=self._extract_certifications(cleaned_text),
            resume_text=resume_text,
            source="resume_intelligence",
        )

    @staticmethod
    def _clean_text(
        text: str
    ) -> str:
        """
        Normalize whitespace while preserving line structure.
        """

        lines = []

        for line in text.splitlines():

            cleaned_line = " ".join(
                line.strip().split()
            )

            if cleaned_line:
                lines.append(cleaned_line)

        return "\n".join(lines)

    @staticmethod
    def _extract_name(
        text: str
    ) -> str:
        """
        Use the first meaningful line as the candidate name.
        """

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        if not lines:
            return ""

        first_line = lines[0]

        if (
            "@" in first_line
            or re.search(r"\d", first_line)
            or first_line.lower().startswith(
                ("resume", "cv", "curriculum vitae")
            )
        ):
            return ""

        return first_line

    @staticmethod
    def _extract_email(
        text: str
    ) -> str:
        """
        Extract the first email address.
        """

        match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            text,
        )

        return match.group(0) if match else ""

    @staticmethod
    def _extract_phone(
        text: str
    ) -> str:
        """
        Extract a likely phone number.
        """

        matches = re.findall(
            r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)",
            text,
        )

        for value in matches:

            digits = re.sub(
                r"\D",
                "",
                value,
            )

            if 10 <= len(digits) <= 15:
                return value.strip()

        return ""

    def _extract_skills(
        self,
        text: str
    ) -> List[str]:
        """
        Extract known technical skills.
        """

        detected = []
        normalized_text = text.lower()

        for keyword, display_name in self.SKILL_KEYWORDS.items():

            if self._keyword_present(
                normalized_text,
                keyword,
            ):
                if display_name not in detected:
                    detected.append(display_name)

        return sorted(detected)

    @staticmethod
    def _extract_experience(
        text: str
    ) -> float:
        """
        Extract the highest explicitly mentioned number
        of years of professional experience.
        """

        normalized_text = text.lower()

        patterns = [
            r"(\d+(?:\.\d+)?)\s*\+\s*years?",
            r"(\d+(?:\.\d+)?)\s*years?\s+(?:of\s+)?experience",
            r"experience\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*years?",
        ]

        values = []

        for pattern in patterns:

            matches = re.findall(
                pattern,
                normalized_text,
            )

            for value in matches:
                values.append(float(value))

        return max(values) if values else 0.0

    @staticmethod
    def _extract_education(
        text: str
    ) -> List[str]:
        """
        Extract common degree and education phrases.
        """

        normalized_text = text.lower()

        education_patterns = [
            r"\bb\.?\s*tech\b",
            r"\bb\.?\s*e\.?\b",
            r"\bbachelor(?:'s)?\b",
            r"\bm\.?\s*tech\b",
            r"\bm\.?\s*e\.?\b",
            r"\bmaster(?:'s)?\b",
            r"\bcomputer science\b",
            r"\bartificial intelligence\b",
            r"\bmachine learning\b",
            r"\bdata science\b",
            r"\binformation technology\b",
        ]

        detected = []

        for pattern in education_patterns:

            if re.search(
                pattern,
                normalized_text,
            ):
                match = re.search(
                    pattern,
                    normalized_text,
                )

                if match:
                    value = match.group(0).strip()

                    if value not in detected:
                        detected.append(value)

        return sorted(detected)

    @staticmethod
    def _extract_projects(
        text: str
    ) -> List[str]:
        """
        Extract project names from common project sections.
        """

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        projects = []
        inside_projects = False

        section_headers = {
            "projects",
            "project",
            "academic projects",
            "personal projects",
            "key projects",
        }

        stop_headers = {
            "experience",
            "work experience",
            "education",
            "skills",
            "certifications",
            "certificates",
            "achievements",
        }

        for line in lines:

            normalized = line.lower().rstrip(":")

            if normalized in section_headers:
                inside_projects = True
                continue

            if normalized in stop_headers:
                inside_projects = False
                continue

            if not inside_projects:
                continue

            if len(line) > 2:
                projects.append(line)

        return projects[:10]

    @staticmethod
    def _extract_certifications(
        text: str
    ) -> List[str]:
        """
        Extract certification entries from common
        certification sections.
        """

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        certifications = []
        inside_certifications = False

        section_headers = {
            "certifications",
            "certification",
            "certificates",
            "certificate",
        }

        stop_headers = {
            "projects",
            "project",
            "experience",
            "work experience",
            "education",
            "skills",
            "achievements",
        }

        for line in lines:

            normalized = line.lower().rstrip(":")

            if normalized in section_headers:
                inside_certifications = True
                continue

            if normalized in stop_headers:
                inside_certifications = False
                continue

            if not inside_certifications:
                continue

            if len(line) > 2:
                certifications.append(line)

        return certifications[:10]

    @staticmethod
    def _keyword_present(
        text: str,
        keyword: str
    ) -> bool:
        """
        Check whether a skill appears as a meaningful term.
        """

        escaped_keyword = re.escape(
            keyword.lower()
        )

        pattern = rf"(?<!\w){escaped_keyword}(?!\w)"

        return re.search(
            pattern,
            text,
        ) is not None