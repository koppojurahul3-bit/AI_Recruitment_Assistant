from backend.services.job_requirement_service import (
    JobRequirementService,
)


def create_service() -> JobRequirementService:
    return JobRequirementService()


def test_extracts_required_skills():

    service = create_service()

    requirements = service.extract(
        """
        We are hiring an ML Engineer with strong
        Python, SQL, Machine Learning and NLP skills.
        """
    )

    assert "Python" in requirements.required_skills
    assert "SQL" in requirements.required_skills
    assert "Machine Learning" in requirements.required_skills
    assert "NLP" in requirements.required_skills


def test_extracts_experience_requirement():

    service = create_service()

    requirements = service.extract(
        """
        The candidate must have at least 3 years
        of experience in machine learning.
        """
    )

    assert requirements.minimum_experience_years == 3.0


def test_extracts_plus_experience():

    service = create_service()

    requirements = service.extract(
        """
        Looking for an engineer with 2+ years
        of experience.
        """
    )

    assert requirements.minimum_experience_years == 2.0


def test_extracts_education_requirements():

    service = create_service()

    requirements = service.extract(
        """
        Bachelor's degree in Computer Science,
        Artificial Intelligence or related field.
        """
    )

    assert "bachelor" in requirements.education_requirements
    assert "computer science" in requirements.education_requirements
    assert "artificial intelligence" in requirements.education_requirements


def test_extracts_job_categories():

    service = create_service()

    requirements = service.extract(
        """
        This role focuses on Generative AI,
        LLM applications, RAG and NLP systems.
        """
    )

    assert "Generative AI" in requirements.categories
    assert "NLP" in requirements.categories


def test_does_not_match_partial_words():

    service = create_service()

    requirements = service.extract(
        """
        We need experience with Python.
        """
    )

    assert "Python" in requirements.required_skills

    requirements = service.extract(
        """
        The candidate should understand pythonic
        programming concepts.
        """
    )

    assert "Python" not in requirements.required_skills


def test_empty_job_description():

    service = create_service()

    requirements = service.extract("")

    assert requirements.required_skills == []
    assert requirements.minimum_experience_years == 0.0
    assert requirements.education_requirements == []
    assert requirements.categories == []


def test_invalid_job_description_type():

    service = create_service()

    try:
        service.extract(None)
        assert False
    except TypeError:
        assert True