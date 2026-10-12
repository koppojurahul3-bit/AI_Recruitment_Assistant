
"""Interview question generation and explainable answer evaluation."""

import re
from typing import Any, Dict, List, Optional

from backend.models.candidate import Candidate
from backend.repositories.candidate_repository import CandidateRepository


class InterviewService:
    """Generate tailored interviews and evaluate answers transparently."""

    DEFAULT_QUESTION_COUNT = 8
    MAX_QUESTION_COUNT = 20

    # Questions are templates, not claims about a candidate's competence.
    SKILL_QUESTIONS = {
        "python": {
            "category": "Technical",
            "question": (
                "Explain how Python manages mutable and immutable objects. "
                "Give an example where this distinction matters."
            ),
            "concepts": ["mutable", "immutable", "object", "example"],
            "follow_up": "How would you avoid unintended mutation in a function?",
        },
        "machine learning": {
            "category": "Technical",
            "question": (
                "Explain the difference between overfitting and underfitting. "
                "How would you detect and reduce them?"
            ),
            "concepts": ["overfitting", "underfitting", "validation", "regularization"],
            "follow_up": "How would you decide whether a model is ready for production?",
        },
        "deep learning": {
            "category": "Technical",
            "question": (
                "Explain forward propagation, backpropagation, and the role "
                "of a loss function when training a neural network."
            ),
            "concepts": ["forward propagation", "backpropagation", "loss", "gradient"],
            "follow_up": "What can cause gradients to vanish or explode?",
        },
        "sql": {
            "category": "Technical",
            "question": (
                "Explain the difference between INNER JOIN and LEFT JOIN. "
                "Describe a situation where each is useful."
            ),
            "concepts": ["inner join", "left join", "matching", "rows"],
            "follow_up": "How would you investigate a slow SQL query?",
        },
        "nlp": {
            "category": "Technical",
            "question": (
                "Describe an NLP pipeline for text classification, including "
                "preprocessing, representation, training, and evaluation."
            ),
            "concepts": ["preprocessing", "tokenization", "representation", "evaluation"],
            "follow_up": "How would you handle class imbalance in text classification?",
        },
        "llm": {
            "category": "Technical",
            "question": (
                "Explain how a large language model generates responses "
                "and describe one limitation that matters in production."
            ),
            "concepts": ["tokens", "context", "generation", "hallucination"],
            "follow_up": "How would you test the reliability of its answers?",
        },
        "rag": {
            "category": "Technical",
            "question": (
                "Explain a RAG pipeline from document ingestion through "
                "retrieval and grounded answer generation."
            ),
            "concepts": ["chunking", "embeddings", "retrieval", "grounding"],
            "follow_up": "How would you diagnose poor retrieval quality?",
        },
        "docker": {
            "category": "Technical",
            "question": (
                "Explain how Docker containers differ from virtual machines "
                "and how you would package an application for deployment."
            ),
            "concepts": ["container", "image", "dependencies", "deployment"],
            "follow_up": "How would you keep secrets out of a Docker image?",
        },
        "fastapi": {
            "category": "Technical",
            "question": (
                "How would you design and validate a FastAPI endpoint, "
                "including request schemas and error handling?"
            ),
            "concepts": ["endpoint", "validation", "schema", "errors"],
            "follow_up": "How would you protect and test the endpoint?",
        },
        "pytorch": {
            "category": "Technical",
            "question": (
                "Describe a PyTorch training loop and explain the roles "
                "of gradients, the optimizer, and zero_grad."
            ),
            "concepts": ["tensor", "gradient", "optimizer", "zero_grad"],
            "follow_up": "How would you identify a training loop that is not learning?",
        },
        "tensorflow": {
            "category": "Technical",
            "question": (
                "Explain how you would build, compile, train, and evaluate "
                "a neural network using TensorFlow or Keras."
            ),
            "concepts": ["model", "loss", "optimizer", "metrics"],
            "follow_up": "How would you monitor overfitting during training?",
        },
        "pandas": {
            "category": "Technical",
            "question": (
                "How would you clean a dataset with missing values, "
                "duplicates, and inconsistent column types using pandas?"
            ),
            "concepts": ["missing values", "duplicates", "types", "validation"],
            "follow_up": "How would you ensure preprocessing is reproducible?",
        },
        "numpy": {
            "category": "Technical",
            "question": (
                "Explain NumPy broadcasting and vectorization, and how "
                "they can improve numerical computation."
            ),
            "concepts": ["arrays", "broadcasting", "vectorization", "dimensions"],
            "follow_up": "How would you check whether two arrays are compatible?",
        },
        "aws": {
            "category": "Technical",
            "question": (
                "Describe how you would deploy a small application on AWS "
                "while addressing permissions, monitoring, and cost."
            ),
            "concepts": ["deployment", "permissions", "monitoring", "cost"],
            "follow_up": "How would you troubleshoot an unhealthy deployment?",
        },
        "java": {
            "category": "Technical",
            "question": (
                "Explain the relationship between interfaces, inheritance, "
                "and polymorphism in Java with an example."
            ),
            "concepts": ["interface", "inheritance", "polymorphism", "example"],
            "follow_up": "When would composition be preferable to inheritance?",
        },
    }

    GENERAL_QUESTIONS = [
        {
            "category": "Problem solving",
            "question": (
                "Describe a technical problem you solved. Explain the "
                "constraints, alternatives, solution, and how you verified it."
            ),
            "concepts": ["problem", "constraints", "solution", "verification"],
            "follow_up": "What would you change if you solved it again?",
        },
        {
            "category": "System design",
            "question": (
                "How would you design a service that accepts requests, "
                "processes them reliably, and records failures for debugging?"
            ),
            "concepts": ["api", "reliability", "logging", "failures"],
            "follow_up": "How would you handle a sudden increase in traffic?",
        },
        {
            "category": "Testing",
            "question": (
                "Explain how you would test a new feature, including normal "
                "cases, edge cases, failure cases, and regression tests."
            ),
            "concepts": ["unit tests", "edge cases", "failure", "regression"],
            "follow_up": "How would you isolate a flaky test?",
        },
        {
            "category": "Behavioral",
            "question": (
                "Describe a time you received critical feedback or faced "
                "a disagreement while working on a technical task."
            ),
            "concepts": ["situation", "action", "reasoning", "outcome"],
            "follow_up": "What did you learn from the experience?",
        },
    ]

    PROJECT_QUESTION = {
        "category": "Resume / project",
        "question": (
            "Walk through one project you worked on. What problem did it "
            "solve, what was your contribution, and how did you measure "
            "whether it worked?"
        ),
        "concepts": ["problem", "contribution", "implementation", "results"],
        "follow_up": "What was the hardest trade-off or limitation?",
    }

    def __init__(
        self,
        candidate_repository: Optional[CandidateRepository] = None,
    ) -> None:
        self.repository = (
            candidate_repository
            if candidate_repository is not None
            else CandidateRepository()
        )

    @staticmethod
    def _validate_text(value: str, name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string.")
        value = value.strip()
        if not value:
            raise ValueError(f"{name} cannot be empty.")
        return value

    @staticmethod
    def _candidate_text(candidate: Candidate) -> str:
        fields = [
            getattr(candidate, "skills", []),
            getattr(candidate, "projects", []),
            getattr(candidate, "certifications", []),
            getattr(candidate, "education", []),
            getattr(candidate, "resume_text", ""),
        ]

        parts: List[str] = []
        for value in fields:
            if isinstance(value, str):
                if value.strip():
                    parts.append(value.strip())
            elif isinstance(value, (list, tuple, set)):
                parts.extend(
                    str(item).strip()
                    for item in value
                    if item is not None and str(item).strip()
                )

        return " ".join(parts)

    @staticmethod
    def _skill_key(skill: str) -> str:
        return re.sub(r"\s+", " ", skill.strip().lower())

    def _candidate_skills(self, candidate: Candidate) -> List[str]:
        skills = getattr(candidate, "skills", [])
        if not isinstance(skills, (list, tuple, set)):
            return []

        return sorted(
            {
                str(skill).strip()
                for skill in skills
                if isinstance(skill, str) and skill.strip()
            },
            key=str.lower,
        )

    def generate_questions(
        self,
        job_description: str,
        candidate_id: Optional[str] = None,
        question_count: int = DEFAULT_QUESTION_COUNT,
    ) -> Dict[str, Any]:
        """Create a deterministic interview plan tailored to available data."""
        job_description = self._validate_text(
            job_description, "Job description"
        )

        if isinstance(question_count, bool) or not isinstance(question_count, int):
            raise TypeError("question_count must be an integer.")

        if not 1 <= question_count <= self.MAX_QUESTION_COUNT:
            raise ValueError(
                f"question_count must be between 1 and "
                f"{self.MAX_QUESTION_COUNT}."
            )

        candidate = None
        if candidate_id is not None:
            candidate_id = self._validate_text(candidate_id, "Candidate ID")
            candidate = self.repository.get_by_id(candidate_id)
            if candidate is None:
                raise ValueError(f"Candidate '{candidate_id}' was not found.")

        job_lower = job_description.lower()
        candidate_lower = (
            self._candidate_text(candidate).lower()
            if candidate is not None
            else ""
        )

        questions: List[Dict[str, Any]] = []
        seen = set()

        def add_question(
            template: Dict[str, Any],
            source: str,
            related_skill: Optional[str] = None,
        ) -> None:
            key = template["question"].casefold()
            if key in seen or len(questions) >= question_count:
                return
            seen.add(key)
            questions.append({
                "question_id": f"Q{len(questions) + 1:03d}",
                "category": template["category"],
                "question": template["question"],
                "expected_concepts": list(template["concepts"]),
                "follow_up": template["follow_up"],
                "source": source,
                "related_skill": related_skill,
            })

        # Prefer questions tied to skills that are both relevant to the role
        # and evidenced in the candidate's recorded skills/resume.
        candidate_skills = (
            self._candidate_skills(candidate)
            if candidate is not None
            else []
        )
        for skill in candidate_skills:
            skill_key = self._skill_key(skill)
            template = self.SKILL_QUESTIONS.get(skill_key)
            if template and skill_key in job_lower:
                add_question(template, "job_and_candidate_skill", skill)

        # Add questions for skills mentioned in the job description.
        for skill_key, template in self.SKILL_QUESTIONS.items():
            if skill_key in job_lower:
                add_question(template, "job_description", skill_key)

        # If candidate details are available, ask about actual project/resume
        # evidence without inventing specific achievements.
        if candidate is not None:
            candidate_evidence = self._candidate_text(candidate).strip()
            if candidate_evidence:
                add_question(self.PROJECT_QUESTION, "candidate_profile")

        # Complete the interview plan with general role-relevant questions.
        for template in self.GENERAL_QUESTIONS:
            add_question(template, "general_interview")

        if not questions:
            add_question(self.GENERAL_QUESTIONS[0], "general_interview")

        return {
            "candidate_id": (
                getattr(candidate, "candidate_id", None)
                if candidate is not None
                else None
            ),
            "candidate_name": (
                getattr(candidate, "name", None)
                if candidate is not None
                else None
            ),
            "job_description": job_description,
            "question_count": len(questions),
            "questions": questions,
            "generation_mode": "deterministic_templates",
            "note": (
                "Questions are generated from predefined templates and "
                "available profile fields. Review them before the interview."
            ),
        }

    def evaluate_answer(
        self,
        question: Dict[str, Any],
        answer: str,
    ) -> Dict[str, Any]:
        """Score an answer against expected concepts with an explainable rubric."""
        if not isinstance(question, dict):
            raise TypeError("question must be a dictionary.")

        question_text = self._validate_text(
            question.get("question", ""), "Question"
        )
        answer = self._validate_text(answer, "Answer")

        concepts = question.get("expected_concepts", [])
        if not isinstance(concepts, list) or not concepts:
            raise ValueError(
                "Question must contain a non-empty expected_concepts list."
            )

        normalized_answer = re.sub(r"\s+", " ", answer.lower())
        matched_concepts = [
            str(concept).strip()
            for concept in concepts
            if isinstance(concept, str)
            and concept.strip()
            and re.search(
                rf"(?<!\w){re.escape(concept.strip().lower())}(?!\w)",
                normalized_answer,
            )
        ]
        missing_concepts = [
            str(concept).strip()
            for concept in concepts
            if isinstance(concept, str)
            and concept.strip()
            and concept.strip().lower() not in {
                item.lower() for item in matched_concepts
            }
        ]

        coverage = len(matched_concepts) / len(concepts)

        # Simple, transparent heuristic rubric:
        # 60% concept coverage, 20% explanation depth, 20% concrete evidence.
        words = re.findall(r"\b[\w+#.-]+\b", answer)
        depth_score = min(len(words) / 60.0, 1.0)
        evidence_markers = (
            "for example", "for instance", "because", "therefore",
            "measured", "tested", "implemented", "result",
        )
        evidence_score = float(
            any(marker in normalized_answer for marker in evidence_markers)
        )

        score = round(
            100.0 * (
                0.60 * coverage
                + 0.20 * depth_score
                + 0.20 * evidence_score
            ),
            2,
        )

        if score >= 80:
            assessment = "Strong evidence"
        elif score >= 60:
            assessment = "Moderate evidence"
        elif score >= 35:
            assessment = "Limited evidence"
        else:
            assessment = "Insufficient evidence"

        feedback = []
        if missing_concepts:
            feedback.append(
                "Consider addressing: " + ", ".join(missing_concepts) + "."
            )
        if len(words) < 20:
            feedback.append(
                "The answer is brief; add reasoning and a concrete example."
            )
        if not evidence_score:
            feedback.append(
                "Include an example, implementation detail, test, or result."
            )
        if not feedback:
            feedback.append(
                "The answer covers the expected concepts; verify depth with "
                "a relevant follow-up question."
            )

        return {
            "question": question_text,
            "answer": answer,
            "score": score,
            "assessment": assessment,
            "matched_concepts": matched_concepts,
            "missing_concepts": missing_concepts,
            "feedback": feedback,
            "follow_up": question.get("follow_up", ""),
            "rubric": {
                "concept_coverage_weight": 0.60,
                "explanation_depth_weight": 0.20,
                "concrete_evidence_weight": 0.20,
                "concept_coverage": round(coverage, 4),
                "explanation_depth": round(depth_score, 4),
                "concrete_evidence": round(evidence_score, 4),
            },
            "evaluation_mode": "deterministic_heuristic",
            "limitation": (
                "This heuristic measures textual concept coverage and answer "
                "detail, not truth, communication quality, or actual expertise. "
                "A human interviewer must review the answer and score."
            ),
        }

    def evaluate_interview(
        self,
        questions: List[Dict[str, Any]],
        answers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Evaluate submitted answers and return an auditable report."""
        if not isinstance(questions, list):
            raise TypeError("questions must be a list.")
        if not isinstance(answers, dict):
            raise TypeError("answers must be a dictionary.")

        results = []
        unanswered = []

        for question in questions:
            if not isinstance(question, dict):
                raise TypeError("Every question must be a dictionary.")

            question_id = question.get("question_id")
            if not isinstance(question_id, str) or not question_id.strip():
                raise ValueError("Every question must have a question_id.")

            answer = answers.get(question_id)
            if answer is None or (
                isinstance(answer, str) and not answer.strip()
            ):
                unanswered.append(question_id)
                continue

            results.append({
                "question_id": question_id,
                **self.evaluate_answer(question, answer),
            })

        scores = [item["score"] for item in results]
        average_score = round(sum(scores) / len(scores), 2) if scores else None

        if average_score is None:
            overall_assessment = "Not assessed"
        elif average_score >= 80:
            overall_assessment = "Strong evidence across answered questions"
        elif average_score >= 60:
            overall_assessment = "Moderate evidence across answered questions"
        elif average_score >= 35:
            overall_assessment = "Limited evidence across answered questions"
        else:
            overall_assessment = "Insufficient evidence across answered questions"

        all_missing = []
        for item in results:
            all_missing.extend(item["missing_concepts"])

        return {
            "total_questions": len(questions),
            "answered_questions": len(results),
            "unanswered_question_ids": unanswered,
            "average_score": average_score,
            "overall_assessment": overall_assessment,
            "question_results": results,
            "improvement_areas": sorted(set(all_missing), key=str.lower),
            "human_review_required": True,
            "decision_policy": (
                "This report is decision support only. Do not use the heuristic "
                "score as an automatic hiring or rejection decision."
            ),
        }
