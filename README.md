# 🤖 AI Recruitment Assistant

An AI-powered recruitment platform that analyzes resumes, evaluates candidates against job descriptions, ranks applicants, and provides intelligent hiring recommendations through an interactive Streamlit dashboard.

## 🚀 Live Demo

🔗 https://ai-recruitment-assistant-rahul.streamlit.app

## 📌 Overview

AI Recruitment Assistant is a resume screening and candidate evaluation system designed to help recruiters reduce manual screening effort.

The application accepts multiple PDF resumes and a Job Description, extracts relevant candidate information, evaluates technical skills, calculates ATS compatibility, measures resume-to-job matching, ranks candidates, and generates hiring recommendations.

## ✨ Features

- 📄 Multiple PDF resume upload
- 💼 Job Description analysis
- 🧠 AI-powered skill extraction
- 🎯 ATS score calculation
- 📊 Resume-to-job matching
- 🏆 Candidate ranking
- 👤 Individual candidate profiles
- 📧 Contact information extraction
- 🎓 Education extraction
- 💼 Experience extraction
- 🚀 Project extraction
- 🏅 Certification detection
- 🧠 Soft-skill detection
- 💪 Candidate strengths analysis
- ⚠️ Areas for improvement
- 💡 AI-generated suggestions
- 🤖 Hiring recommendations
- 📝 AI candidate summaries
- 📄 PDF candidate reports
- 📊 CSV recruitment reports
- 📈 Recruitment analytics dashboard
- 🔎 Candidate search and filtering
- ⚙️ Recruitment settings
- 🌐 Streamlit Cloud deployment

## 🏗️ Application Architecture

```text
                 ┌─────────────────────┐
                 │     Recruiter       │
                 └──────────┬──────────┘
                            │
                            ▼
                ┌──────────────────────┐
                │   Streamlit UI       │
                └──────────┬───────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      Resume PDF(s)                Job Description
             │                           │
             ▼                           ▼
      Text Extraction             Skill Extraction
             │                           │
             └─────────────┬─────────────┘
                           ▼
                 ┌─────────────────────┐
                 │ Candidate Analysis  │
                 └──────────┬──────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
      ATS Score       Resume Match      Skill Analysis
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                 Candidate Score & Ranking
                            │
                            ▼
                  Hiring Recommendation
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
        PDF Report                  CSV Report



🛠️ Tech Stack
Programming : Python

Frontend : StreamlitHTML/CSS styling

Data Processing : Pandas , PyPDF2

NLP / AI :
Sentence Transformers 
Semantic embeddings
Resume skill extraction
Job description analysis

Reporting :
ReportLab
CSV generation

Deployment :
GitHub
Streamlit Community Cloud

📂 Project Structure :

AI_Recruitment_Assistant/
│
├── analyzer.py
├── streamlit_app.py
├── requirements.txt
├── sample_resume.pdf
├── .gitignore
└── README.md

⚙️ Installation

Clone the repository:

git clone https://github.com/koppojurahul3-bit/AI_Recruitment_Assistant.git

Move into the project directory:

cd AI_Recruitment_Assistant

Create a virtual environment:

python -m venv .venv

Activate the environment on Windows:

.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Run the application:

streamlit run streamlit_app.py

The application will open in your browser.



📊 Candidate Evaluation

The platform evaluates candidates using multiple signals including:

ATS compatibility
Resume-to-job similarity
Required technical skills
Missing skills
Projects
Certifications
Experience
Education
Soft skills

These signals are combined to produce an overall candidate score and hiring recommendation.



📄 Reports

Recruiters can generate:

Candidate PDF reports
Recruitment CSV reports

The reports contain candidate scores, ranking information, extracted details, skills, recommendations, and analysis.



🎯 Use Cases

This platform can be used for:

Resume screening
Campus recruitment
Technical hiring
Candidate shortlisting
Recruitment analytics
Automated candidate evaluation
HR screening workflows


🔮 Future Improvements
Multi-agent recruitment architecture
Interview question generation
AI voice interviews
Automated interview evaluation
Email automation
Calendar scheduling
Recruiter authentication
Database-backed candidate storage
Advanced RAG-based candidate search
LLM-powered recruitment assistant

👨‍💻 Author

Rahul

AI / ML Developer

GitHub: https://github.com/koppojurahul3-bit


⭐ Project

If you find this project useful, consider giving the repository a ⭐.


### After pasting

Click **Commit changes**.

That's your GitHub documentation done. ✅

---

# 2. Add it to LinkedIn

For LinkedIn, I recommend putting it in **Projects** and also **Featured**.

LinkedIn currently lets you add a Projects section through **Add profile section → Recommended → Projects**. For a newly added project, LinkedIn says the old Project URL field may not appear; instead use **Add media → Add a link**. :contentReference[oaicite:1]{index=1}

### Go to your profile

:contentReference[oaicite:2]{index=2}

Then:

**Me → View Profile → Add profile section → Recommended → Projects**

Create:

### Project Name

```text
AI Recruitment Assistant
Description

Copy this:

Built an AI-powered recruitment platform using Python and Streamlit to automate resume screening and candidate evaluation.

The system accepts multiple PDF resumes and a Job Description, extracts candidate information, calculates ATS scores, performs semantic resume-to-job matching, analyzes skills, ranks candidates, and generates AI-powered hiring recommendations.

Key features include candidate profiles, ATS scoring, resume matching, skill-gap analysis, candidate ranking, PDF/CSV reporting, recruitment analytics, and an interactive recruiter dashboard.

Tech Stack:
Python, Streamlit, Pandas, PyPDF2, Sentence Transformers, ReportLab, NLP, GitHub, Streamlit Cloud.

Live Demo:
https://ai-recruitment-assistant-rahul.streamlit.app
Dates

Since you just completed it, use the month/year when you started and finished the project.

If LinkedIn asks whether it's ongoing, don't mark it ongoing if you're treating this version as completed.

3. Add the links

For the project, use Add media → Add a link and add:

Live Demo
https://ai-recruitment-assistant-rahul.streamlit.app

Title:

Live Demo — AI Recruitment Assistant

Then add another link:

https://github.com/koppojurahul3-bit/AI_Recruitment_Assistant

Title:

GitHub — AI Recruitment Assistant

LinkedIn specifically recommends using Add media → Add a link for project links when the Project URL field isn't available.

4. Put it in Featured too 🔥

This is important because recruiters will see it much earlier on your profile.

Go to:

Profile → Featured → + → Add a link

Add your deployed application:

https://ai-recruitment-assistant-rahul.streamlit.app

Title:

AI Recruitment Assistant — Live Demo

You can also add the GitHub repository as another Featured item.

LinkedIn's Featured section is designed specifically to highlight important work and can feature Projects and other profile content.
