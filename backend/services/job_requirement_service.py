import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class JobRequirements:
    """
    Structured representation of requirements extracted
    from a job description.
    """

    required_skills: List[str] = field(default_factory=list)
    minimum_experience_years: float = 0.0
    education_requirements: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)


class JobRequirementService:
    """
    Extracts structured recruitment requirements from
    a job description.
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
    }

    CATEGORY_KEYWORDS = {
        "Machine Learning": [
            "machine learning",
            "scikit-learn",
            "tensorflow",
            "pytorch",
        ],
        "Deep Learning": [
            "deep learning",
            "tensorflow",
            "pytorch",
        ],
        "NLP": [
            "natural language processing",
            "nlp",
            "text classification",
            "transformers",
        ],
        "Generative AI": [
            "generative ai",
            "llm",
            "large language model",
            "rag",
            "retrieval augmented generation",
        ],
        "Backend Development": [
            "fastapi",
            "flask",
            "django",
            "backend",
            "api development",
        ],
        "Cloud": [
            "aws",
            "azure",
            "gcp",
            "cloud",
        ],
        "DevOps": [
            "docker",
            "kubernetes",
            "ci/cd",
            "devops",
        ],
        "Data Science": [
            "pandas",
            "numpy",
            "data science",
            "data analysis",
        ],
    }

    EDUCATION_KEYWORDS = [
        "b.tech",
        "btech",
        "b.e",
        "be degree",
        "bachelor",
        "bachelors",
        "master",
        "masters",
        "m.tech",
        "mtech",
        "m.s",
        "ms degree",
        "computer science",
        "information technology",
        "artificial intelligence",
        "data science",
    ]

    def extract(
        self,
        job_description: str
    ) -> JobRequirements:
        """
        Extract structured requirements from a job description.
        """

        if not isinstance(job_description, str):
            raise TypeError(
                "Job description must be a string."
            )

        text = job_description.lower()

        return JobRequirements(
            required_skills=self._extract_skills(text),
            minimum_experience_years=self._extract_experience(text),
            education_requirements=self._extract_education(text),
            categories=self._extract_categories(text),
        )

    def _extract_skills(
        self,
        text: str
    ) -> List[str]:
        """
        Extract known technical skills.
        """

        detected = []

        for keyword, display_name in self.SKILL_KEYWORDS.items():

            if self._keyword_present(
                text,
                keyword
            ):
                if display_name not in detected:
                    detected.append(display_name)

        return sorted(detected)

    def _extract_experience(
        self,
        text: str
    ) -> float:
        """
        Extract the minimum years of experience when
        explicitly mentioned.
        """

        patterns = [
            r"(\d+(?:\.\d+)?)\s*\+\s*years?",
            r"minimum\s+(\d+(?:\.\d+)?)\s*years?",
            r"at\s+least\s+(\d+(?:\.\d+)?)\s*years?",
            r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*years?",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text
            )

            if not match:
                continue

            return float(match.group(1))

        return 0.0

    def _extract_education(
        self,
        text: str
    ) -> List[str]:
        """
        Extract known education requirements.
        """

        detected = []

        for keyword in self.EDUCATION_KEYWORDS:

            if self._keyword_present(
                text,
                keyword
            ):
                detected.append(keyword)

        return sorted(set(detected))

    def _extract_categories(
        self,
        text: str
    ) -> List[str]:
        """
        Identify broad job categories.
        """

        categories = []

        for category, keywords in self.CATEGORY_KEYWORDS.items():

            for keyword in keywords:

                if self._keyword_present(
                    text,
                    keyword
                ):
                    categories.append(category)
                    break

        return sorted(set(categories))

    @staticmethod
    def _keyword_present(
        text: str,
        keyword: str
    ) -> bool:
        """
        Check whether a keyword exists as a meaningful
        term in the text.
        """

        escaped_keyword = re.escape(
            keyword.lower()
        )

        pattern = rf"(?<!\w){escaped_keyword}(?!\w)"

        return re.search(
            pattern,
            text
        ) is not None