
from backend.agents.recruiter_assistant import RecruiterAssistantAgent
from backend.models.candidate import Candidate
from backend.repositories.candidate_repository import CandidateRepository
from backend.services.recruiter_rag_service import RecruiterRAGService


def create_repository():
    repository = CandidateRepository()

    repository.add(
        Candidate(
            candidate_id="C001",
            name="Rahul",
            skills=["Python", "Machine Learning", "SQL"],
            experience_years=3.0,
            education=["B.Tech Computer Science"],
            projects=["Built a resume ranking application"],
            certifications=["Machine Learning Certificate"],
            resume_text=(
                "Developed Python applications for machine learning. "
                "Built resume ranking and candidate matching systems."
            ),
        )
    )

    repository.add(
        Candidate(
            candidate_id="C002",
            name="Arjun",
            skills=["Java", "NLP"],
            experience_years=2.0,
            education=["M.Tech"],
            projects=["Created a natural language processing project"],
            resume_text="Worked on NLP and text classification.",
        )
    )

    return repository


def create_service(repository=None):
    return RecruiterRAGService(
        candidate_repository=(
            repository if repository is not None else create_repository()
        ),
        use_semantic_search=False,
    )


def test_retrieval_finds_candidate_by_skill():
    service = create_service()

    results = service.retrieve("Which candidates know Python?")

    assert results
    assert results[0].candidate_id == "C001"
    assert any("Python" in item.text for item in results)


def test_retrieval_finds_project_evidence():
    service = create_service()

    results = service.retrieve("Who built a resume ranking application?")

    assert results
    assert results[0].candidate_id == "C001"
    assert any("resume ranking" in item.text.lower() for item in results)


def test_answer_includes_citations_and_source_records():
    service = create_service()

    result = service.answer_question("Which candidate knows Python?")

    assert result["retrieved_count"] > 0
    assert result["sources"]
    assert "C001" in result["answer"]
    assert "[C001 —" in result["answer"]
    assert result["answer_mode"] == "grounded_evidence_summary"


def test_no_matching_evidence_returns_clear_message():
    service = create_service()

    result = service.answer_question(
        "Who has professional experience with marine biology?"
    )

    assert result["retrieved_count"] == 0
    assert result["sources"] == []
    assert result["answer_mode"] == "no_relevant_evidence"
    assert "couldn't find relevant evidence" in result["answer"]


def test_empty_repository_returns_no_evidence():
    service = create_service(CandidateRepository())

    result = service.answer_question("Who knows Python?")

    assert result["retrieved_count"] == 0
    assert result["sources"] == []


def test_blank_question_is_rejected():
    service = create_service()

    try:
        service.retrieve("   ")
        assert False, "Expected ValueError for a blank question."
    except ValueError as exc:
        assert "non-empty string" in str(exc)


def test_top_k_validation():
    service = create_service()

    for invalid_top_k in (0, 21):
        try:
            service.retrieve("Python", top_k=invalid_top_k)
            assert False, "Expected ValueError for invalid top_k."
        except ValueError as exc:
            assert "top_k" in str(exc)


def test_top_k_type_validation():
    service = create_service()

    try:
        service.retrieve("Python", top_k="5")
        assert False, "Expected TypeError for non-integer top_k."
    except TypeError as exc:
        assert "integer" in str(exc)


def test_agent_returns_answer_and_sources():
    agent = RecruiterAssistantAgent(
        candidate_repository=create_repository()
    )

    result = agent.answer_question("Which candidate knows Python?")

    assert result["question"] == "Which candidate knows Python?"
    assert isinstance(result["answer"], str)
    assert isinstance(result["sources"], list)
    assert result["retrieved_count"] == len(result["sources"])


def test_agent_can_return_evidence_without_answer():
    agent = RecruiterAssistantAgent(
        candidate_repository=create_repository()
    )

    evidence = agent.retrieve_evidence("Python")

    assert evidence
    assert evidence[0]["candidate_id"] == "C001"
    assert evidence[0]["citation"].startswith("[C001 —")


def test_resume_text_is_split_into_bounded_chunks():
    long_text = "Python experience. " * 150
    candidate = Candidate(
        candidate_id="C003",
        name="Kiran",
        resume_text=long_text,
    )

    documents = RecruiterRAGService._candidate_documents(candidate)
    resume_documents = [
        item for item in documents
        if item["source"].startswith("resume_text")
    ]

    assert len(resume_documents) > 1
    assert all(
        len(item["text"]) <= RecruiterRAGService.MAX_CHUNK_CHARACTERS
        for item in resume_documents
    )
