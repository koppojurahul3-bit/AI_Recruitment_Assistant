from dataclasses import dataclass, field
from typing import List


@dataclass
class Candidate:
    """
    Structured representation of a recruitment candidate.
    """

    candidate_id: str
    name: str
    email: str = ""

    phone: str = ""

    skills: List[str] = field(default_factory=list)
    experience_years: float = 0.0

    education: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)

    resume_text: str = ""

    source: str = "repository"