
import pytest

from backend.agents.interview_agent import InterviewAgent
from backend.models.candidate import Candidate
from backend.repositories.candidate_repository import CandidateRepository
from backend.services.interview_service import InterviewService


def create_repository():
    repository = CandidateRepository()
    repository.add(
        Candidate(
            candidate_id="C001",
            name="Alice",
            skills=["Python", "Machine Learning", "SQL"],
            experience_years=3,
            education=["B.Tech Computer Science"],
            projects=["Built a machine learning prediction API"],
            resume_text="Implemented a Python ML model and evaluated results.",
        )
    )
    return repository


def create_service():
    return InterviewService(candidate_repository=create_repository())


def test_generate_questions_for_job_description():
    result = create_service().generate_questions(
        "We need a Python and Machine Learning engineer.",
        question_count=5,
    )

    assert result["question_count"] == 5
    assert result["generation_mode"] == "deterministic_templates"
    assert any("Python" in item["question"] for item in result["questions"])
    assert all(item["question_id"] for item in result["questions"])


def test_generate_candidate_specific_questions():
    result = create_service().generate_questions(
        "Python and Machine Learning engineer",
        candidate_id="C001",
        question_count=8,
    )

    assert result["candidate_id"] == "C001"
    assert result["candidate_name"] == "Alice"
    assert any(
        item["category"] == "Resume / project"
        for item in result["questions"]
    )


def test_unknown_candidate_is_rejected():
    with pytest.raises(ValueError, match="was not found"):
        create_service().generate_questions(
            "Python engineer",
            candidate_id="UNKNOWN",
        )


@pytest.mark.parametrize("description", ["", "   "])
def test_empty_job_description_is_rejected(description):
    with pytest.raises(ValueError, match="cannot be empty"):
        create_service().generate_questions(description)


@pytest.mark.parametrize("count", [0, 21])
def test_question_count_bounds(count):
    with pytest.raises(ValueError, match="question_count"):
        create_service().generate_questions("Python engineer", question_count=count)


def test_question_count_type_is_validated():
    with pytest.raises(TypeError, match="integer"):
        create_service().generate_questions("Python engineer", question_count=True)


def test_answer_evaluation_returns_explanation():
    service = create_service()
    question = {
        "question_id": "Q001",
        "question": "Explain overfitting.",
        "expected_concepts": [
            "overfitting",
            "validation",
            "regularization",
        ],
        "follow_up": "How would you detect it?",
    }

    result = service.evaluate_answer(
        question,
        (
            "Overfitting occurs when a model memorizes training data. "
            "I would use validation data and regularization. For example, "
            "I would compare training and validation performance."
        ),
    )

    assert 0 <= result["score"] <= 100
    assert "overfitting" in result["matched_concepts"]
    assert result["missing_concepts"] == []
    assert result["rubric"]["concept_coverage_weight"] == 0.60
    assert result["evaluation_mode"] == "deterministic_heuristic"
    assert result["limitation"]


def test_blank_answer_is_rejected():
    question = {
        "question": "Explain Python.",
        "expected_concepts": ["Python"],
    }

    with pytest.raises(ValueError, match="cannot be empty"):
        create_service().evaluate_answer(question, " ")


def test_invalid_question_concepts_are_rejected():
    with pytest.raises(ValueError, match="expected_concepts"):
        create_service().evaluate_answer(
            {"question": "Explain Python.", "expected_concepts": []},
            "Python is a programming language.",
        )


def test_interview_report_tracks_unanswered_questions():
    service = create_service()
    questions = [
        {
            "question_id": "Q001",
            "question": "Explain Python.",
            "expected_concepts": ["Python", "example"],
            "follow_up": "Give an example.",
        },
        {
            "question_id": "Q002",
            "question": "Explain SQL.",
            "expected_concepts": ["SQL", "query"],
            "follow_up": "Explain a join.",
        },
    ]

    report = service.evaluate_interview(
        questions,
        {"Q001": "Python is a language. For example, it automates tasks."},
    )

    assert report["total_questions"] == 2
    assert report["answered_questions"] == 1
    assert report["unanswered_question_ids"] == ["Q002"]
    assert report["average_score"] is not None
    assert report["human_review_required"] is True


def test_all_unanswered_answers_report_not_assessed():
    report = create_service().evaluate_interview(
        [
            {
                "question_id": "Q001",
                "question": "Explain Python.",
                "expected_concepts": ["Python"],
            }
        ],
        {},
    )

    assert report["average_score"] is None
    assert report["overall_assessment"] == "Not assessed"
    assert report["answered_questions"] == 0


def test_agent_exposes_generation_and_evaluation():
    agent = InterviewAgent(candidate_repository=create_repository())

    plan = agent.generate_questions(
        "Python engineer",
        candidate_id="C001",
        question_count=3,
    )
    report = agent.evaluate_interview(plan["questions"], {})

    assert plan["candidate_id"] == "C001"
    assert report["total_questions"] == 3
    assert report["human_review_required"] is True


def test_duplicate_questions_are_removed():
    result = create_service().generate_questions(
        "Python Python Machine Learning",
        question_count=20,
    )

    question_texts = [item["question"] for item in result["questions"]]
    assert len(question_texts) == len(set(question_texts))
