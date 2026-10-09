
import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from backend.models.candidate import Candidate


DatabasePath = Union[str, Path]


class SQLiteCandidateRepository:
    """
    Persistent candidate repository backed by SQLite.

    The public operations match CandidateRepository so callers can
    choose in-memory or persistent storage without changing their
    core candidate-handling logic.
    """

    def __init__(
        self,
        database_path: DatabasePath = "data/candidates.sqlite3",
    ) -> None:
        if not isinstance(database_path, (str, Path)):
            raise TypeError("Database path must be a string or Path.")

        path = str(database_path).strip()
        if not path:
            raise ValueError("Database path cannot be empty.")

        if path != ":memory:":
            resolved_path = Path(path)
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            path = str(resolved_path)

        self.database_path = path
        self._connection = sqlite3.connect(path)
        self._connection.row_factory = sqlite3.Row

        try:
            self._create_schema()
        except Exception:
            self._connection.close()
            raise

    def _create_schema(self) -> None:
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS candidates (
                    candidate_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL DEFAULT '',
                    phone TEXT NOT NULL DEFAULT '',
                    skills TEXT NOT NULL DEFAULT '[]',
                    experience_years REAL NOT NULL DEFAULT 0,
                    education TEXT NOT NULL DEFAULT '[]',
                    projects TEXT NOT NULL DEFAULT '[]',
                    certifications TEXT NOT NULL DEFAULT '[]',
                    resume_text TEXT NOT NULL DEFAULT '',
                    source TEXT NOT NULL DEFAULT 'repository'
                )
                """
            )

    @staticmethod
    def _validate_candidate(candidate: Candidate) -> None:
        if not isinstance(candidate, Candidate):
            raise TypeError("candidate must be a Candidate instance.")

        if (
            not isinstance(candidate.candidate_id, str)
            or not candidate.candidate_id.strip()
        ):
            raise ValueError("Candidate ID must be a non-empty string.")

        if not isinstance(candidate.name, str):
            raise ValueError("Candidate name must be a string.")

        for field_name in (
            "skills",
            "education",
            "projects",
            "certifications",
        ):
            value = getattr(candidate, field_name)
            if not isinstance(value, list) or not all(
                isinstance(item, str) for item in value
            ):
                raise ValueError(
                    f"Candidate {field_name} must be a list of strings."
                )

        if isinstance(candidate.experience_years, bool) or not isinstance(
            candidate.experience_years, (int, float)
        ):
            raise ValueError("Experience years must be numeric.")

        if candidate.experience_years < 0:
            raise ValueError("Experience years cannot be negative.")

        for field_name in ("email", "phone", "resume_text", "source"):
            if not isinstance(getattr(candidate, field_name), str):
                raise ValueError(f"Candidate {field_name} must be a string.")

    @staticmethod
    def _candidate_values(candidate: Candidate) -> tuple:
        return (
            candidate.candidate_id.strip(),
            candidate.name,
            candidate.email,
            candidate.phone,
            json.dumps(candidate.skills),
            float(candidate.experience_years),
            json.dumps(candidate.education),
            json.dumps(candidate.projects),
            json.dumps(candidate.certifications),
            candidate.resume_text,
            candidate.source,
        )

    @staticmethod
    def _row_to_candidate(row: sqlite3.Row) -> Candidate:
        return Candidate(
            candidate_id=row["candidate_id"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            skills=json.loads(row["skills"]),
            experience_years=row["experience_years"],
            education=json.loads(row["education"]),
            projects=json.loads(row["projects"]),
            certifications=json.loads(row["certifications"]),
            resume_text=row["resume_text"],
            source=row["source"],
        )

    def add(self, candidate: Candidate) -> Candidate:
        """Persist a candidate; reject duplicate IDs."""

        self._validate_candidate(candidate)
        values = self._candidate_values(candidate)

        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO candidates (
                        candidate_id, name, email, phone, skills,
                        experience_years, education, projects,
                        certifications, resume_text, source
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )
        except sqlite3.IntegrityError as exc:
            if self.get_by_id(candidate.candidate_id.strip()) is not None:
                raise ValueError(
                    f"Candidate already exists: "
                    f"{candidate.candidate_id.strip()}"
                ) from exc
            raise

        return candidate

    def get_by_id(self, candidate_id: str) -> Optional[Candidate]:
        """Retrieve a candidate by exact ID."""

        if not isinstance(candidate_id, str):
            raise TypeError("Candidate ID must be a string.")

        row = self._connection.execute(
            "SELECT * FROM candidates WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()

        return self._row_to_candidate(row) if row is not None else None

    def get_all(self) -> List[Candidate]:
        """Return candidates in insertion order."""

        rows = self._connection.execute(
            "SELECT * FROM candidates ORDER BY rowid"
        ).fetchall()

        return [self._row_to_candidate(row) for row in rows]

    def search_by_skill(self, skill: str) -> List[Candidate]:
        """Find candidates with an exact, case-insensitive skill match."""

        if not isinstance(skill, str):
            raise TypeError("Skill must be a string.")

        normalized_skill = skill.lower()
        return [
            candidate
            for candidate in self.get_all()
            if any(item.lower() == normalized_skill for item in candidate.skills)
        ]

    def search_by_skills(self, skills: List[str]) -> List[Candidate]:
        """Find candidates matching at least one requested skill."""

        if not isinstance(skills, list) or not all(
            isinstance(skill, str) for skill in skills
        ):
            raise TypeError("Skills must be a list of strings.")

        normalized_skills = {skill.lower() for skill in skills}
        return [
            candidate
            for candidate in self.get_all()
            if any(
                skill.lower() in normalized_skills
                for skill in candidate.skills
            )
        ]

    def search_by_experience(
        self,
        minimum_years: float,
    ) -> List[Candidate]:
        """Find candidates meeting the minimum experience threshold."""

        if isinstance(minimum_years, bool) or not isinstance(
            minimum_years, (int, float)
        ):
            raise TypeError("Minimum experience must be numeric.")

        return [
            candidate
            for candidate in self.get_all()
            if candidate.experience_years >= minimum_years
        ]

    def count(self) -> int:
        """Return the number of stored candidates."""

        row = self._connection.execute(
            "SELECT COUNT(*) AS total FROM candidates"
        ).fetchone()
        return int(row["total"])

    def clear(self) -> None:
        """Delete all candidate records from this database."""

        with self._connection:
            self._connection.execute("DELETE FROM candidates")

    def close(self) -> None:
        """Close this repository's database connection."""

        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "SQLiteCandidateRepository":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
