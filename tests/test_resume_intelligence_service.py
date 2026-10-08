from backend.services.resume_intelligence_service import (
    ResumeIntelligenceService,
)


def create_service() -> ResumeIntelligenceService:
    return ResumeIntelligenceService()


def sample_resume() -> str:
    return """
    Rahul Kumar
    rahul@example.com
    +91 9876543210

    B.Tech in Artificial Intelligence

    2 years of experience in Machine Learning.

    Skills
    Python
    Machine Learning
    NLP
    SQL
    Pandas

    Projects
    AI Recruitment Assistant
    RAG Document Assistant

    Certifications
    Machine Learning Certification
    Generative AI Certification
    """


def test_extracts_candidate_name():

    service = create_service()

    candidate = service.analyze(
        sample_resume(),
        "C001",
    )

    assert candidate.name == "Rahul Kumar"


def test_extracts_email():

    service = create_service()

    candidate = service.analyze(
        sample_resume(),
        "C001",
    )

    assert candidate.email == "rahul@example.com"


def test_extracts_phone():

    service = create_service()

    candidate = service.analyze(
        sample_resume(),
        "C001",
    )

    assert "9876543210" in candidate.phone.replace(
        " ",
        "",
    )


def test_extracts_skills():

    service = create_service()

    candidate = service.analyze(
        sample_resume(),
        "C001",
    )

    assert "Python" in candidate.skills
    assert "Machine Learning" in candidate.skills
    assert "NLP" in candidate.skills
    assert "SQL" in candidate.skills
    assert "Pandas" in candidate.skills


def test_extracts_experience():

    service = create_service()

    candidate = service.analyze(
        sample_resume(),
        "C001",
    )

    assert candidate.experience_years == 2.0


def test_extracts_education():

    service = create_service()

    candidate = service.analyze(
        sample_resume(),
        "C001",
    )

    assert "b.tech" in candidate.education
    assert "artificial intelligence" in candidate.education


def test_extracts_projects():

    service = create_service()

    candidate = service.analyze(
        sample_resume(),
        "C001",
    )

    assert "AI Recruitment Assistant" in candidate.projects
    assert "RAG Document Assistant" in candidate.projects


def test_extracts_certifications():

    service = create_service()

    candidate = service.analyze(
        sample_resume(),
        "C001",
    )

    assert "Machine Learning Certification" in candidate.certifications
    assert "Generative AI Certification" in candidate.certifications


def test_preserves_original_resume():

    service = create_service()

    resume = sample_resume()

    candidate = service.analyze(
        resume,
        "C001",
    )

    assert candidate.resume_text == resume


def test_candidate_source_is_set():

    service = create_service()

    candidate = service.analyze(
        sample_resume(),
        "C001",
    )

    assert candidate.source == "resume_intelligence"


def test_empty_resume_is_supported():

    service = create_service()

    candidate = service.analyze(
        "",
        "C001",
    )

    assert candidate.name == ""
    assert candidate.email == ""
    assert candidate.phone == ""
    assert candidate.skills == []
    assert candidate.experience_years == 0.0


def test_invalid_resume_type_is_rejected():

    service = create_service()

    try:
        service.analyze(
            None,
            "C001",
        )
        assert False
    except TypeError:
        assert True


def test_empty_candidate_id_is_rejected():

    service = create_service()

    try:
        service.analyze(
            sample_resume(),
            "",
        )
        assert False
    except ValueError:
        assert True