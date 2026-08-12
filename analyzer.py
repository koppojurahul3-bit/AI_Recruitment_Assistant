import PyPDF2
import re

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ------------------------------
# Load Sentence Transformer Model
# ------------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")

# ------------------------------
# Skill Knowledge Base
# ------------------------------

skill_dictionary = {

    # ------------------------------
    # Programming Languages
    # ------------------------------

    "Programming Languages": [
        "python",
        "java",
        "c",
        "c++",
        "c#",
        "javascript",
        "typescript",
        "go",
        "golang",
        "rust",
        "php",
        "ruby",
        "kotlin",
        "swift",
        "scala",
        "r"
    ],

    # ------------------------------
    # Machine Learning
    # ------------------------------

    "Machine Learning": [
        "machine learning",
        "scikit-learn",
        "sklearn",
        "random forest",
        "decision tree",
        "logistic regression",
        "linear regression",
        "support vector machine",
        "svm",
        "knn",
        "k-nearest neighbors",
        "naive bayes",
        "xgboost",
        "adaboost",
        "gradient boosting",
        "lightgbm",
        "catboost"
    ],

    # ------------------------------
    # Deep Learning
    # ------------------------------

    "Deep Learning": [
        "deep learning",
        "tensorflow",
        "keras",
        "pytorch",
        "cnn",
        "convolutional neural network",
        "rnn",
        "recurrent neural network",
        "lstm",
        "gru",
        "transformer",
        "bert",
        "gpt",
        "gan",
        "autoencoder"
    ],

    # ------------------------------
    # Natural Language Processing
    # ------------------------------

    "NLP": [
        "nlp",
        "natural language processing",
        "text classification",
        "sentiment analysis",
        "named entity recognition",
        "ner",
        "tokenization",
        "word embeddings",
        "tf-idf",
        "bag of words",
        "word2vec",
        "glove",
        "spacy",
        "nltk"
    ],

    # ------------------------------
    # Generative AI / LLM
    # ------------------------------

    "Generative AI": [
        "generative ai",
        "genai",
        "large language model",
        "llm",
        "llms",
        "openai",
        "chatgpt",
        "gemini",
        "claude",
        "hugging face",
        "huggingface",
        "langchain",
        "llamaindex",
        "rag",
        "retrieval augmented generation",
        "prompt engineering",
        "fine tuning",
        "fine-tuning"
    ],

    # ------------------------------
    # Data Science
    # ------------------------------

    "Data Science": [
        "data science",
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "scipy",
        "jupyter",
        "jupyter notebook",
        "data visualization",
        "exploratory data analysis",
        "eda",
        "statistics"
    ],

    # ------------------------------
    # Web Development
    # ------------------------------

    "Web Development": [
        "html",
        "html5",
        "css",
        "css3",
        "javascript",
        "typescript",
        "react",
        "reactjs",
        "angular",
        "vue",
        "vuejs",
        "next.js",
        "nextjs",
        "bootstrap",
        "tailwind",
        "tailwind css"
    ],

    # ------------------------------
    # Backend Development
    # ------------------------------

    "Backend Development": [
        "node.js",
        "nodejs",
        "express",
        "express.js",
        "django",
        "flask",
        "fastapi",
        "spring",
        "spring boot",
        "asp.net",
        "rest api",
        "restful api",
        "graphql",
        "microservices"
    ],

    # ------------------------------
    # Databases
    # ------------------------------

    "Databases": [
        "sql",
        "mysql",
        "postgresql",
        "postgres",
        "sqlite",
        "oracle",
        "sql server",
        "microsoft sql server",
        "mongodb",
        "mongo",
        "redis",
        "cassandra",
        "dynamodb",
        "firebase",
        "elasticsearch"
    ],

    # ------------------------------
    # Cloud Computing
    # ------------------------------

    "Cloud Computing": [
        "aws",
        "amazon web services",
        "azure",
        "microsoft azure",
        "google cloud",
        "gcp",
        "google cloud platform",
        "ec2",
        "s3",
        "lambda",
        "azure functions"
    ],

    # ------------------------------
    # DevOps
    # ------------------------------

    "DevOps": [
        "docker",
        "kubernetes",
        "k8s",
        "jenkins",
        "ci/cd",
        "cicd",
        "github actions",
        "gitlab ci",
        "terraform",
        "ansible",
        "helm",
        "prometheus",
        "grafana",
        "nginx"
    ],

    # ------------------------------
    # Big Data
    # ------------------------------

    "Big Data": [
        "hadoop",
        "spark",
        "apache spark",
        "pyspark",
        "hive",
        "kafka",
        "apache kafka",
        "databricks",
        "airflow",
        "apache airflow"
    ],

    # ------------------------------
    # Mobile Development
    # ------------------------------

    "Mobile Development": [
        "android",
        "android studio",
        "ios",
        "flutter",
        "dart",
        "react native",
        "swiftui"
    ],

    # ------------------------------
    # Testing
    # ------------------------------

    "Testing": [
        "unit testing",
        "integration testing",
        "pytest",
        "unittest",
        "junit",
        "selenium",
        "cypress",
        "postman",
        "testng"
    ],

    # ------------------------------
    # Version Control
    # ------------------------------

    "Version Control": [
        "git",
        "github",
        "gitlab",
        "bitbucket",
        "svn"
    ],

    # ------------------------------
    # Tools
    # ------------------------------

    "Tools": [
        "streamlit",
        "jupyter",
        "vs code",
        "visual studio code",
        "pycharm",
        "intellij",
        "linux",
        "unix",
        "bash"
    ]
}

strength_dictionary = {

    "Python": "Strong Python Programming",

    "Machine Learning": "Strong Machine Learning Knowledge",

    "Deep Learning": "Strong Deep Learning Experience",

    "SQL": "Good Database Knowledge",

    "Pandas": "Good Data Analysis Skills",

    "NumPy": "Strong Numerical Computing Skills"

}

weakness_dictionary = {

    "Docker": "Containerization Skills",

    "AWS": "Cloud Deployment Skills",

    "Kubernetes": "Container Orchestration Knowledge",

    "Git": "Version Control Skills",

    "CI/CD": "DevOps Automation Skills"

}

suggestion_dictionary = {

    "Containerization Skills":
        "Learn Docker and containerize one Machine Learning project.",

    "Cloud Deployment Skills":
        "Deploy one Machine Learning project on AWS or Azure.",

    "Container Orchestration Knowledge":
        "Learn Kubernetes and deploy a containerized application.",

    "Version Control Skills":
        "Upload your projects to GitHub with proper documentation.",

    "DevOps Automation Skills":
        "Learn GitHub Actions or Jenkins to automate deployments."

}

# ------------------------------
# PDF Text Extraction
# ------------------------------

def extract_text(uploaded_file):

    reader = PyPDF2.PdfReader(uploaded_file)

    text = ""

    for page in reader.pages:

        extracted = page.extract_text()

        if extracted:
            text += extracted

    return text


# ------------------------------
# Smart Skill Detection
# ------------------------------

def detect_skills(text):

    text = text.lower()

    detected_categories = set()

    detected_keywords = set()

    for category, keywords in skill_dictionary.items():

        category_found = False

        for keyword in keywords:

            if keyword in text:

                detected_keywords.add(keyword.title())

                category_found = True

        if category_found:
            detected_categories.add(category)

    return list(detected_categories), sorted(list(detected_keywords))

def extract_job_skills(job_description):

    _, job_keywords = detect_skills(job_description)

    return job_keywords

def generate_strengths(categories):

    strengths = []

    for category in categories:

        if category in strength_dictionary:

            strengths.append(
                strength_dictionary[category]
            )

    return strengths

def generate_weaknesses(missing_skills):

    weaknesses = []

    for skill in missing_skills:

        if skill in weakness_dictionary:

            weaknesses.append(
                weakness_dictionary[skill]
            )

    return weaknesses

def generate_suggestions(weaknesses):

    suggestions = []

    for weakness in weaknesses:

        if weakness in suggestion_dictionary:

            suggestions.append(
                suggestion_dictionary[weakness]
            )

    return suggestions

def generate_candidate_summary(
    strengths,
    weaknesses,
    recommendation,
    candidate_score
):

    summary = ""

    if len(strengths) > 0:

        summary += (
            "The candidate demonstrates "
            + ", ".join(strengths)
            + ". "
        )

    if len(weaknesses) > 0:

        summary += (
            "Areas for improvement include "
            + ", ".join(weaknesses)
            + ". "
        )

    summary += (
        f"Overall Candidate Score: {round(candidate_score,2)}/100. "
    )

    summary += (
        f"Hiring Recommendation: {recommendation}."
    )

    return summary


# ------------------------------
# ATS Score
# ------------------------------

# ------------------------------
# ATS Score
# ------------------------------

def calculate_ats_score(resume_keywords, job_keywords):

    if len(job_keywords) == 0:
        return 0

    matched_skills = set(resume_keywords) & set(job_keywords)

    score = (
        len(matched_skills) / len(set(job_keywords))
    ) * 100

    return round(score)


# ------------------------------
# Contact Information Extraction
# ------------------------------

def extract_email(text):

    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

    match = re.search(pattern, text)

    if match:
        return match.group()

    return "Not Found"


def extract_phone(text):

    pattern = r"\+?\d[\d\s\-]{8,14}\d"

    match = re.search(pattern, text)

    if match:
        return match.group()

    return "Not Found"


def extract_linkedin(text):

    pattern = r"(https?://)?(www\.)?linkedin\.com/[^\s]+"

    match = re.search(pattern, text)

    if match:
        return match.group()

    return "Not Found"


def extract_github(text):

    pattern = r"(https?://)?(www\.)?github\.com/[^\s]+"

    match = re.search(pattern, text)

    if match:
        return match.group()

    return "Not Found"

# ------------------------------
# Experience Extraction
# ------------------------------

def extract_experience(text):

    text = text.lower()

    # Pattern for years and optional months
    pattern = r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s*(?:of\s+)?(?:professional\s+)?experience"

    matches = re.findall(pattern, text)

    if matches:

        experience_values = []

        for match in matches:
            experience_values.append(float(match))

        return max(experience_values)

    # Pattern for months of experience
    month_pattern = r"(\d+)\s*\+?\s*months?\s*(?:of\s+)?(?:professional\s+)?experience"

    month_matches = re.findall(month_pattern, text)

    if month_matches:

        month_values = []

        for match in month_matches:
            month_values.append(int(match) / 12)

        return round(max(month_values), 1)

    # Fresher detection
    if "fresher" in text or "fresh graduate" in text:
        return 0.0

    return 0.0

# ------------------------------
# Education Extraction
# ------------------------------

def extract_education(text):

    education_patterns = {
        "PhD": [
            r"\bph\.?d\b",
            r"\bdoctorate\b"
        ],

        "M.Tech": [
            r"\bm\.?\s*tech\b",
            r"\bmaster of technology\b"
        ],

        "M.E": [
            r"\bm\.?\s*e\b",
            r"\bmaster of engineering\b"
        ],

        "M.S": [
            r"\bm\.?\s*s\b",
            r"\bmaster of science\b"
        ],

        "MCA": [
            r"\bmca\b",
            r"\bmaster of computer applications\b"
        ],

        "MBA": [
            r"\bmba\b",
            r"\bmaster of business administration\b"
        ],

        "M.Sc": [
            r"\bm\.?\s*sc\b",
            r"\bmaster of science\b"
        ],

        "B.Tech": [
            r"\bb\.?\s*tech\b",
            r"\bbachelor of technology\b"
        ],

        "B.E": [
            r"\bb\.?\s*e\b",
            r"\bbachelor of engineering\b"
        ],

        "B.S": [
            r"\bb\.?\s*s\b",
            r"\bbachelor of science\b"
        ],

        "BCA": [
            r"\bbca\b",
            r"\bbachelor of computer applications\b"
        ],

        "BBA": [
            r"\bbba\b",
            r"\bbachelor of business administration\b"
        ],

        "B.Sc": [
            r"\bb\.?\s*sc\b",
            r"\bbachelor of science\b"
        ],

        "Bachelor's": [
            r"\bbachelor'?s degree\b",
            r"\bbachelor degree\b"
        ],

        "Master's": [
            r"\bmaster'?s degree\b",
            r"\bmaster degree\b"
        ]
    }

    # --------------------------------
    # Find Education Section
    # --------------------------------

    education_section_pattern = (
        r"(?:education|academic background|academic qualifications)"
        r"(.*?)(?:experience|professional experience|projects|"
        r"technical skills|skills|certifications|certificates|"
        r"achievements|interests|$)"
    )

    section_match = re.search(
        education_section_pattern,
        text,
        re.IGNORECASE | re.DOTALL
    )

    if section_match:

        education_text = section_match.group(1)

    else:

        education_text = text

    # --------------------------------
    # Detect Degrees
    # --------------------------------

    detected_degrees = []

    for degree, patterns in education_patterns.items():

        for pattern in patterns:

            if re.search(pattern, education_text, re.IGNORECASE):

                detected_degrees.append(degree)

                break

    # --------------------------------
    # Extract Education Details
    # --------------------------------

    education_details = []

    lines = [
        line.strip()
        for line in education_text.splitlines()
        if line.strip()
    ]

    for index, line in enumerate(lines):

        degree_found = None

        for degree, patterns in education_patterns.items():

            for pattern in patterns:

                if re.search(pattern, line, re.IGNORECASE):

                    degree_found = degree
                    break

            if degree_found:
                break

        if degree_found:

            field = "Not Found"
            institution = "Not Found"
            year = "Not Found"

            # --------------------------------
            # Extract Year
            # --------------------------------

            year_match = re.search(
                r"\b(19|20)\d{2}\b",
                line
            )

            if year_match:

                year = year_match.group()

            elif index + 1 < len(lines):

                next_year_match = re.search(
                    r"\b(19|20)\d{2}\b",
                    lines[index + 1]
                )

                if next_year_match:

                    year = next_year_match.group()

            # --------------------------------
            # Extract Field
            # --------------------------------

            field_match = re.search(
                r"\b(?:in|major in|specialization in)"
                r"\s+([A-Za-z][A-Za-z &/\-]+)",
                line,
                re.IGNORECASE
            )

            if field_match:

                field = field_match.group(1).strip()

            # --------------------------------
            # Extract Institution
            # --------------------------------

            if index + 1 < len(lines):

                candidate_line = lines[index + 1]

                if not re.search(
                    r"\b(19|20)\d{2}\b",
                    candidate_line
                ):

                    if not any(
                        re.search(
                            pattern,
                            candidate_line,
                            re.IGNORECASE
                        )
                        for patterns in education_patterns.values()
                        for pattern in patterns
                    ):

                        institution = candidate_line

            education_details.append({
                "degree": degree_found,
                "field": field,
                "institution": institution,
                "year": year
            })

    return education_details

# ------------------------------
# Project Extraction
# ------------------------------

def extract_projects(text):

    # --------------------------------
    # Normalize PDF text
    # --------------------------------

    text = text.replace("\r", "\n")

    # Sometimes PDF extraction places a bullet
    # directly after a project title.
    # Example:
    #
    # Enterprise RAG Knowledge Assistant● Developed...
    #
    # We force the bullet onto a new line.

    text = re.sub(
        r"(?<!\n)[●•▪◦]\s*",
        "\n• ",
        text
    )

    # --------------------------------
    # Locate Projects Section
    # --------------------------------

    project_section_pattern = (
        r"(?:projects?|project experience|"
        r"academic projects|personal projects)"
        r"\s*:?\s*"
        r"(.*?)"
        r"(?=\n\s*(?:certifications?|education|"
        r"experience|professional experience|"
        r"technical skills|skills|achievements|"
        r"soft skills|interests|references)\b|$)"
    )

    section_match = re.search(
        project_section_pattern,
        text,
        re.IGNORECASE | re.DOTALL
    )

    if not section_match:

        return []

    project_text = section_match.group(1)

    # --------------------------------
    # Clean Lines
    # --------------------------------

    lines = []

    for line in project_text.splitlines():

        line = line.strip()

        if line:

            lines.append(line)

    # --------------------------------
    # Detect Project Titles
    # --------------------------------

    projects = []

    current_project = None

    for line in lines:

        # Remove common bullet symbols
        clean_line = re.sub(
            r"^[•●▪◦\-]\s*",
            "",
            line
        ).strip()

        # Ignore empty lines
        if not clean_line:

            continue

        # --------------------------------
        # Bullet / Description Line
        # --------------------------------

        if re.match(
            r"^[•●▪◦\-]\s*",
            line
        ):

            if current_project:

                current_project["description"].append(
                    clean_line
                )

            continue

        # --------------------------------
        # Project Title
        # --------------------------------

        # A non-bullet line inside the Projects
        # section is treated as a project title.

        if current_project:

            projects.append(current_project)

        current_project = {
            "name": clean_line,
            "description": []
        }

    # Add final project
    if current_project:

        projects.append(current_project)

    # --------------------------------
    # Build Final Project Records
    # --------------------------------

    final_projects = []

    for project in projects:

        description = project["description"]

        project_text_for_skills = (
            project["name"]
            + " "
            + " ".join(description)
        )

        _, technologies = detect_skills(
            project_text_for_skills
        )

        final_projects.append({
            "name": project["name"],
            "description": description,
            "technologies": technologies
        })

    return final_projects

# ------------------------------
# Certification Extraction
# ------------------------------

def extract_certifications(text):

    # --------------------------------
    # Normalize PDF text
    # --------------------------------

    text = text.replace("\r", "\n")

    # --------------------------------
    # Locate Certification Section
    # --------------------------------

    certification_section_pattern = (
        r"(?:certifications?|certificates?|"
        r"professional certifications?)"
        r"\s*:?\s*"
        r"(.*?)"
        r"(?=\n\s*(?:education|academic background|"
        r"experience|professional experience|"
        r"projects?|project experience|"
        r"technical skills|skills|soft skills|"
        r"achievements|interests|references)\b|$)"
    )

    section_match = re.search(
        certification_section_pattern,
        text,
        re.IGNORECASE | re.DOTALL
    )

    if not section_match:

        return []

    certification_text = section_match.group(1)

    # --------------------------------
    # Clean Lines
    # --------------------------------

    certifications = []

    for line in certification_text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Remove common bullet symbols
        line = re.sub(
            r"^[•●▪◦\-]\s*",
            "",
            line
        ).strip()

        if line:
            certifications.append(line)

    # --------------------------------
    # Remove Duplicates
    # --------------------------------

    unique_certifications = []

    for certification in certifications:

        if certification not in unique_certifications:

            unique_certifications.append(
                certification
            )

    return unique_certifications

# ------------------------------
# Soft Skills Extraction
# ------------------------------

def extract_soft_skills(text):

    # --------------------------------
    # Normalize PDF text
    # --------------------------------

    text = text.replace("\r", "\n")

    # --------------------------------
    # Controlled Soft Skill Dictionary
    # --------------------------------

    soft_skill_dictionary = {
        "communication": "Communication",
        "leadership": "Leadership",
        "teamwork": "Teamwork",
        "team work": "Teamwork",
        "problem solving": "Problem Solving",
        "problem-solving": "Problem Solving",
        "analytical thinking": "Analytical Thinking",
        "adaptability": "Adaptability",
        "time management": "Time Management",
        "critical thinking": "Critical Thinking",
        "collaboration": "Collaboration",
        "creativity": "Creativity",
        "decision making": "Decision Making",
        "decision-making": "Decision Making",
        "attention to detail": "Attention to Detail",
        "interpersonal skills": "Interpersonal Skills",
        "conflict resolution": "Conflict Resolution",
        "emotional intelligence": "Emotional Intelligence",
        "presentation skills": "Presentation Skills",
        "negotiation": "Negotiation",
        "mentoring": "Mentoring",
        "team leadership": "Team Leadership"
    }

    # --------------------------------
    # Locate Soft Skills Section
    # --------------------------------

    soft_skill_section_pattern = (
        r"(?:soft skills?|interpersonal skills?|"
        r"core competencies?|professional skills?)"
        r"\s*:?\s*"
        r"(.*?)"
        r"(?=\n\s*(?:education|academic background|"
        r"experience|professional experience|"
        r"projects?|project experience|"
        r"certifications?|certificates?|"
        r"technical skills|skills|achievements|"
        r"interests|references)\b|$)"
    )

    section_match = re.search(
        soft_skill_section_pattern,
        text,
        re.IGNORECASE | re.DOTALL
    )

    # --------------------------------
    # If no dedicated section exists
    # --------------------------------

    if not section_match:

        return []

    soft_skill_text = section_match.group(1)

    # --------------------------------
    # Detect Soft Skills
    # --------------------------------

    detected_skills = []

    normalized_text = soft_skill_text.lower()

    for keyword, display_name in soft_skill_dictionary.items():

        if keyword in normalized_text:

            if display_name not in detected_skills:

                detected_skills.append(
                    display_name
                )

    return detected_skills

# ------------------------------
# Role Recommendation
# ------------------------------

def recommend_role(categories):

    categories = set(categories)

    if {"Python", "Machine Learning", "Deep Learning"}.issubset(categories):
        return "🤖 AIML Engineer"

    elif {"Python", "Machine Learning"}.issubset(categories):
        return "📊 Data Scientist"

    elif {"Python", "SQL", "Pandas"}.issubset(categories):
        return "📈 Data Analyst"

    elif {"Python"}.issubset(categories):
        return "💻 Software Engineer"

    else:
        return "🎓 General Candidate"


# ------------------------------
# Resume ↔ Job Description Match
# ------------------------------

def calculate_resume_match(resume_text, job_description):

    resume_embedding = model.encode(resume_text)

    job_embedding = model.encode(job_description)

    similarity = cosine_similarity(
        [resume_embedding],
        [job_embedding]
    )[0][0]

    match_percentage = similarity * 100

    return float(f"{match_percentage:.2f}")

# ------------------------------
# Hiring Recommendation
# ------------------------------

def hiring_recommendation(match_percentage, ats_score):

    if match_percentage >= 90 and ats_score >= 85:
        return "⭐ Highly Recommended"

    elif match_percentage >= 75 and ats_score >= 70:
        return "✅ Recommended"

    elif match_percentage >= 60 and ats_score >= 60:
        return "⚠ Consider"

    else:
        return "❌ Not Recommended"
    
def calculate_candidate_score(
    match_percentage,
    ats_score
):

    candidate_score = (
        (match_percentage * 0.6)
        +
        (ats_score * 0.4)
    )

    return round(candidate_score, 2)

    if len(job_keywords) == 0:
        skill_coverage = 0

    else:

        matched = 0

        for skill in detected_keywords:

            if skill in job_keywords:
                matched += 1

        skill_coverage = (
            matched / len(job_keywords)
        ) * 100

    candidate_score = (

        (match_percentage * 0.5)

        +

        (ats_score * 0.3)

        +

        (skill_coverage * 0.2)

    )

    return round(candidate_score, 2)   

def generate_pdf_report(result, filename):

    styles = getSampleStyleSheet()

    pdf = SimpleDocTemplate(filename)

    content = []

    content.append(
        Paragraph("<b>AI Recruitment Assistant Report</b>", styles["Title"])
    )

    content.append(
        Paragraph(f"<b>Candidate:</b> {result['filename']}", styles["BodyText"])
    )

    content.append(
        Paragraph(f"<b>Email:</b> {result['email']}", styles["BodyText"])
    )

    content.append(
        Paragraph(f"<b>Phone:</b> {result['phone']}", styles["BodyText"])
    )

    content.append(
        Paragraph(f"<b>LinkedIn:</b> {result['linkedin']}", styles["BodyText"])
    )

    content.append(
        Paragraph(f"<b>GitHub:</b> {result['github']}", styles["BodyText"])
    )

    content.append(
        Paragraph("<br/><b>Evaluation</b>", styles["Heading2"])
    )

    content.append(
        Paragraph(f"Recommended Role : {result['role']}", styles["BodyText"])
    )

    content.append(
        Paragraph(f"ATS Score : {result['score']}%", styles["BodyText"])
    )

    content.append(
        Paragraph(f"Resume Match : {result['match_percentage']}%", styles["BodyText"])
    )

    content.append(
        Paragraph(
            f"Candidate Score : {result['candidate_score']}/100",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph("<br/><b>Technologies</b>", styles["Heading2"])
    )

    content.append(
        Paragraph(", ".join(result["keywords"]), styles["BodyText"])
    )

    content.append(
        Paragraph(
            "<br/><b>Professional Experience</b>",
            styles["Heading2"]
        )
    )

    if result["experience"] == 0:

        content.append(
            Paragraph(
                "Fresher / Not Specified",
                styles["BodyText"]
            )
        )

    elif result["experience"] == 1:

        content.append(
            Paragraph(
                "1 year",
                styles["BodyText"]
            )
        ) 

    else:

        content.append(
            Paragraph(
                f"{result['experience']} years",
                styles["BodyText"]
            )
        )

    content.append(
        Paragraph(
            "<br/><b>Education</b>",
            styles["Heading2"]
        )
    )

    if len(result["education"]) == 0:

        content.append(
            Paragraph(
                "Not Found",
                styles["BodyText"]
            )
        )

    else:

        for education in result["education"]:

            content.append(
                Paragraph(
                    f"<b>{education['degree']}</b>",
                    styles["BodyText"]
                )
            )

        content.append(
            Paragraph(
                f"Field: {education['field']}",
                styles["BodyText"]
            )
        )

        content.append(
            Paragraph(
                f"Institution: {education['institution']}",
                styles["BodyText"]
            )
        )

        content.append(
            Paragraph(
                f"Year: {education['year']}",
                styles["BodyText"]
            )
        )

        content.append(
            Spacer(1, 6)
        )
    
    content.append(
        Paragraph(
            "<br/><b>Projects</b>",
            styles["Heading2"]
        )
    )

    if len(result["projects"]) == 0:

        content.append(
            Paragraph(
                "No projects detected.",
                styles["BodyText"]
            )
        )

    else:

        for project in result["projects"]:

            content.append(
                Paragraph(
                    f"<b>{project['name']}</b>",
                    styles["BodyText"]
                )
            )

        for description in project["description"]:

            content.append(
                Paragraph(
                    f"• {description}",
                    styles["BodyText"]
                )
            )

        if len(project["technologies"]) > 0:

            content.append(
                Paragraph(
                    "<b>Technologies:</b> "
                    + ", ".join(
                        project["technologies"]
                    ),
                    styles["BodyText"]
                )
            )

        content.append(
           Spacer(1, 8)
        )

    content.append(
        Paragraph(
            "<br/><b>Certifications</b>",
            styles["Heading2"]
        )
    )

    if len(result["certifications"]) == 0:

        content.append(
            Paragraph(
                "No certifications detected.",
                styles["BodyText"]
            )
        )

    else:

        for certification in result["certifications"]:

            content.append(
                Paragraph(
                    f"• {certification}",
                    styles["BodyText"]
                )
            )

    content.append(
        Spacer(1, 8)
    )

    content.append(
        Paragraph(
            "<br/><b>Soft Skills</b>",
            styles["Heading2"]
        )
    )

    if len(result["soft_skills"]) == 0:

        content.append(
            Paragraph(
                "No soft skills detected.",
                styles["BodyText"]
            )
        )

    else:

        content.append(
            Paragraph(
                ", ".join(result["soft_skills"]),
                styles["BodyText"]
            )
        )

    content.append(
        Spacer(1, 8)
    )
    
    content.append(
        Paragraph("<br/><b>Strengths</b>", styles["Heading2"])
    )

    content.append(
        Paragraph("<br/>".join(result["strengths"]), styles["BodyText"])
    )

    content.append(
        Paragraph("<br/><b>Areas for Improvement</b>", styles["Heading2"])
    )

    if len(result["weaknesses"]) == 0:

        content.append(
            Paragraph("No major weaknesses detected.", styles["BodyText"])
        )

    else:

        content.append(
            Paragraph("<br/>".join(result["weaknesses"]), styles["BodyText"])
        )

    content.append(
        Paragraph("<br/><b>AI Suggestions</b>", styles["Heading2"])
    )

    if len(result["suggestions"]) == 0:

        content.append(
            Paragraph("No suggestions required.", styles["BodyText"])
        )

    else:

        content.append(
            Paragraph("<br/>".join(result["suggestions"]), styles["BodyText"])
        )

    content.append(
        Paragraph("<br/><b>AI Candidate Summary</b>", styles["Heading2"])
    )

    content.append(
        Paragraph(result["summary"], styles["BodyText"])
    )

    content.append(
        Paragraph("<br/><b>Hiring Recommendation</b>", styles["Heading2"])
    )

    content.append(
        Paragraph(result["recommendation"], styles["BodyText"])
    )

    pdf.build(content)