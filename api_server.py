
from __future__ import annotations

import csv
import io
import json
import os
import re
import urllib.error
import urllib.request
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import analyzer


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
SCHEDULE_FILE = DATA_DIR / "interviews.json"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

app = FastAPI(
    title="AI Recruitment Assistant API",
    version="2.0.0",
    description="Local API for the AI Recruitment Assistant React frontend.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------

class InterviewQuestionRequest(BaseModel):
    job_description: str = Field(min_length=20, max_length=30000)
    question_count: int = Field(default=8, ge=1, le=30)


class InterviewEvaluationRequest(BaseModel):
    questions: list[dict[str, Any]]
    answers: dict[str, str]


class VoiceRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    job_description: str = ""


class AgentRequest(BaseModel):
    task: str = Field(min_length=1, max_length=10000)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    job_description: str = ""


class CandidateReportRequest(BaseModel):
    results: list[dict[str, Any]] = Field(default_factory=list)


class ScheduleRequest(BaseModel):
    candidate_name: str = Field(min_length=1, max_length=200)
    candidate_email: str = Field(default="", max_length=320)
    role: str = Field(min_length=1, max_length=200)
    date: str
    time: str
    duration_minutes: int = Field(default=30, ge=5, le=480)
    interview_type: str = Field(default="Technical", max_length=100)
    notes: str = Field(default="", max_length=3000)


# ---------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------

def _ollama_request(path: str, payload: dict[str, Any] | None = None,
                    timeout: int = 120) -> dict[str, Any]:
    """Make a JSON request to the local Ollama server."""
    url = f"{OLLAMA_URL}{path}"
    body = None if payload is None else json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="GET" if body is None else "POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Ollama returned HTTP {exc.code}: {detail[:500]}"
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(
            f"Cannot connect to Ollama at {OLLAMA_URL}. "
            "Start Ollama and make sure the configured model is installed."
        ) from exc


def _ollama_chat(
    system_prompt: str,
    user_prompt: str,
    timeout: int = 180,
    format_json: bool = False,
) -> str:
    """Generate a response using the configured local model."""
    response = _ollama_request(
        "/api/chat",
        {
            "model": OLLAMA_MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0.2},
            **({"format": "json"} if format_json else {}),
        },
        timeout=timeout,
    )

    message = response.get("message", {})
    content = message.get("content", "")

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Ollama returned an empty response.")

    return content.strip()


def _parse_json_response(text: str) -> Any:
    """Parse JSON returned by an LLM, including fenced JSON responses."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start_object = cleaned.find("{")
        end_object = cleaned.rfind("}")
        start_array = cleaned.find("[")
        end_array = cleaned.rfind("]")

        if start_array >= 0 and end_array > start_array:
            try:
                return json.loads(cleaned[start_array:end_array + 1])
            except json.JSONDecodeError:
                pass

        if start_object >= 0 and end_object > start_object:
            try:
                return json.loads(cleaned[start_object:end_object + 1])
            except json.JSONDecodeError:
                pass

    raise ValueError("The AI model did not return valid JSON.")


def _load_schedule() -> list[dict[str, Any]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not SCHEDULE_FILE.exists():
        return []

    try:
        content = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        return content if isinstance(content, list) else []
    except (OSError, json.JSONDecodeError):
        raise HTTPException(
            status_code=500,
            detail="The schedule file could not be read. Check data/interviews.json.",
        )


def _save_schedule(items: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary_file = SCHEDULE_FILE.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps(items, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_file.replace(SCHEDULE_FILE)


def _safe_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _candidate_context(
    candidates: list[dict[str, Any]],
    job_description: str,
) -> str:
    """Keep prompt context useful without sending entire extracted resumes."""
    safe_candidates = []

    for index, candidate in enumerate(candidates[:50], start=1):
        safe_candidates.append({
            "rank": candidate.get("rank", index),
            "filename": candidate.get("filename", "Unknown candidate"),
            "role": candidate.get("role", ""),
            "match_percentage": candidate.get("match_percentage"),
            "ats_score": candidate.get("ats_score", candidate.get("score")),
            "candidate_score": candidate.get("candidate_score"),
            "recommendation": candidate.get("recommendation", ""),
            "keywords": candidate.get("keywords", []),
            "missing_skills": candidate.get("missing_skills", []),
            "strengths": candidate.get("strengths", []),
            "weaknesses": candidate.get("weaknesses", []),
            "summary": candidate.get("summary", ""),
        })

    return json.dumps(
        {
            "job_description": job_description[:12000],
            "candidates": safe_candidates,
        },
        ensure_ascii=False,
        default=str,
    )


# ---------------------------------------------------------------------
# Health and system status
# ---------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "AI Recruitment Assistant API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AI Recruitment Assistant API",
        "version": "2.0.0",
    }


@app.get("/api/system/status")
def system_status():
    """The backend stays available even if Ollama is not running."""
    result: dict[str, Any] = {
        "api": True,
        "ollama": "disconnected",
        "ollama_url": OLLAMA_URL,
        "model": OLLAMA_MODEL,
        "model_available": False,
        "error": "",
    }

    try:
        response = _ollama_request("/api/tags", timeout=5)
        models = response.get("models", [])
        model_names = [
            item.get("name", "")
            for item in models
            if isinstance(item, dict)
        ]

        result["ollama"] = "connected"
        result["model_available"] = any(
            name == OLLAMA_MODEL
            or name.split(":")[0] == OLLAMA_MODEL.split(":")[0]
            for name in model_names
        )

        if not result["model_available"]:
            result["error"] = (
                f"Ollama is running, but '{OLLAMA_MODEL}' was not found. "
                f"Available models: {', '.join(model_names) or 'none'}."
            )
    except Exception as exc:
        result["error"] = str(exc)

    return result


# ---------------------------------------------------------------------
# Resume analysis: existing analyzer.py is preserved
# ---------------------------------------------------------------------

@app.post("/api/recruitment/analyze")
async def analyze_resumes(
    resumes: list[UploadFile] = File(...),
    job_description: str = Form(""),
):
    if not resumes:
        raise HTTPException(status_code=400, detail="Upload at least one resume PDF.")

    jd_text = (job_description or "").strip()

    if len(jd_text) < 20:
        raise HTTPException(
            status_code=400,
            detail="Job description must contain at least 20 characters.",
        )

    job_keywords = analyzer.extract_job_skills(jd_text)
    results: list[dict[str, Any]] = []

    for resume in resumes:
        filename = resume.filename or "resume.pdf"

        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"{filename} is not a PDF file.",
            )

        try:
            resume.file.seek(0)
            resume_text = analyzer.extract_text(resume.file)

            if not resume_text.strip():
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"No selectable text was found in {filename}. "
                        "Scanned PDFs require OCR."
                    ),
                )

            categories, keywords = analyzer.detect_skills(resume_text)
            categories = sorted(list(categories))
            keywords = sorted(list(keywords))

            ats_score = float(analyzer.calculate_ats_score(keywords, job_keywords))
            match_percentage = float(
                analyzer.calculate_resume_match(resume_text, jd_text)
            )
            missing_skills = sorted(
                skill for skill in job_keywords if skill not in keywords
            )

            strengths = analyzer.generate_strengths(categories)
            weaknesses = analyzer.generate_weaknesses(missing_skills)
            suggestions = analyzer.generate_suggestions(weaknesses)
            recommendation = analyzer.hiring_recommendation(
                match_percentage, ats_score
            )
            candidate_score = analyzer.calculate_candidate_score(
                match_percentage, ats_score
            )
            summary = analyzer.generate_candidate_summary(
                strengths, weaknesses, recommendation, candidate_score
            )

            results.append({
                "filename": filename,
                "email": analyzer.extract_email(resume_text),
                "phone": analyzer.extract_phone(resume_text),
                "linkedin": analyzer.extract_linkedin(resume_text),
                "github": analyzer.extract_github(resume_text),
                "experience": analyzer.extract_experience(resume_text),
                "education": analyzer.extract_education(resume_text),
                "projects": analyzer.extract_projects(resume_text),
                "certifications": analyzer.extract_certifications(resume_text),
                "soft_skills": analyzer.extract_soft_skills(resume_text),
                "categories": categories,
                "keywords": keywords,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "missing_skills": missing_skills,
                "suggestions": suggestions,
                "summary": summary,
                "score": ats_score,
                "ats_score": ats_score,
                "match_percentage": match_percentage,
                "candidate_score": candidate_score,
                "recommendation": recommendation,
                "role": analyzer.recommend_role(categories),
            })

        except HTTPException:
            raise
        except Exception as exc:
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze {filename}: {exc}",
            ) from exc

    results.sort(
        key=lambda item: float(item.get("match_percentage") or 0),
        reverse=True,
    )

    for rank, result in enumerate(results, start=1):
        result["rank"] = rank

    return {
        "success": True,
        "count": len(results),
        "job_description_characters": len(jd_text),
        "results": results,
    }


# ---------------------------------------------------------------------
# Interview question generation and evaluation
# ---------------------------------------------------------------------

@app.post("/api/interviews/questions")
def generate_interview_questions(request: InterviewQuestionRequest):
    system_prompt = (
        "You are a technical recruitment interviewer. Create fair, job-related "
        "interview questions based only on the provided job description. "
        "Return valid JSON only, with this exact shape: "
        '{"questions":[{"question":"...","category":"...","expected_points":["..."]}]}. '
        "Do not invent candidate experience or qualifications."
    )

    user_prompt = (
        f"Generate exactly {request.question_count} useful interview questions "
        "for this role. Include a balanced mix of technical, practical, and "
        "behavioral questions where relevant.\n\n"
        f"JOB DESCRIPTION:\n{request.job_description}"
    )

    try:
        raw = _ollama_chat(
            system_prompt,
            user_prompt,
            format_json=True,
        )
        parsed = _parse_json_response(raw)

        if isinstance(parsed, dict):
            questions = parsed.get("questions", [])
        elif isinstance(parsed, list):
            questions = parsed
        else:
            questions = []

        valid_questions = []

        for item in questions:
            if isinstance(item, str):
                valid_questions.append({
                    "question": item,
                    "category": "General",
                    "expected_points": [],
                })
            elif isinstance(item, dict) and item.get("question"):
                valid_questions.append({
                    "question": str(item["question"]),
                    "category": str(item.get("category", "General")),
                    "expected_points": item.get("expected_points", []),
                })

        if not valid_questions:
            raise ValueError("The model returned no usable interview questions.")

        return {
            "success": True,
            "model": OLLAMA_MODEL,
            "questions": valid_questions[:request.question_count],
        }

    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/interviews/evaluate")
def evaluate_interview_answers(request: InterviewEvaluationRequest):
    if not request.questions:
        raise HTTPException(
            status_code=400,
            detail="Generate interview questions before evaluating answers.",
        )

    payload = {
        "questions": request.questions[:30],
        "answers": request.answers,
    }

    system_prompt = (
        "You are a structured interview evaluator. Evaluate only the answers "
        "provided. Do not infer protected characteristics or make claims not "
        "supported by the response. Give evidence-based feedback and identify "
        "missing evidence. Return valid JSON only with keys: overall_feedback, "
        "strengths, improvements, per_question. Do not make a final hiring "
        "decision."
    )

    try:
        raw = _ollama_chat(
            system_prompt,
            json.dumps(payload, ensure_ascii=False),
        )

        try:
            evaluation = _parse_json_response(raw)
        except ValueError:
            evaluation = {"overall_feedback": raw}

        return {
            "success": True,
            "model": OLLAMA_MODEL,
            "evaluation": evaluation,
        }

    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ---------------------------------------------------------------------
# Voice recruiter and recruitment agent
# ---------------------------------------------------------------------

@app.post("/api/voice/answer")
def voice_recruiter_answer(request: VoiceRequest):
    context = _candidate_context(
        request.candidates,
        request.job_description,
    )

    system_prompt = (
        "You are TalentIQ, a recruitment assistant. Answer the recruiter's "
        "question clearly and concisely using only the supplied job description "
        "and candidate analysis data. If no candidate data is supplied, say so. "
        "Never invent candidate names, scores, skills, or contact information. "
        "Treat match scores as decision-support signals, not definitive proof "
        "of ability. Do not make a final hiring decision."
    )

    user_prompt = (
        f"RECRUITMENT CONTEXT:\n{context}\n\n"
        f"RECRUITER QUESTION:\n{request.question}"
    )

    try:
        answer = _ollama_chat(system_prompt, user_prompt)
        return {
            "success": True,
            "model": OLLAMA_MODEL,
            "answer": answer,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/agents/run")
def run_recruitment_agent(request: AgentRequest):
    context = _candidate_context(
        request.candidates,
        request.job_description,
    )

    system_prompt = (
        "You are the analysis agent in a local AI Recruitment Assistant. "
        "Perform the recruiter's requested analysis using only the supplied "
        "context. State when evidence is missing. Give findings, supporting "
        "evidence, skill gaps, and practical next steps. Do not claim to have "
        "sent messages, scheduled meetings, modified files, or performed "
        "external actions. Do not make a final hiring decision."
    )

    user_prompt = (
        f"TASK:\n{request.task}\n\n"
        f"AVAILABLE RECRUITMENT CONTEXT:\n{context}"
    )

    try:
        result = _ollama_chat(system_prompt, user_prompt)
        return {
            "success": True,
            "model": OLLAMA_MODEL,
            "result": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ---------------------------------------------------------------------
# Candidate CSV export
# ---------------------------------------------------------------------

@app.post("/api/reports/candidates.csv")
def export_candidates_csv(request: CandidateReportRequest):
    output = io.StringIO()
    columns = [
        "rank",
        "filename",
        "email",
        "phone",
        "role",
        "match_percentage",
        "ats_score",
        "candidate_score",
        "recommendation",
        "keywords",
        "missing_skills",
        "strengths",
        "weaknesses",
        "summary",
    ]

    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()

    for candidate in request.results:
        row = dict(candidate)

        for key in ("keywords", "missing_skills", "strengths", "weaknesses"):
            row[key] = _safe_string(row.get(key))

        writer.writerow({
            key: _safe_string(row.get(key))
            for key in columns
        })

    content = output.getvalue()
    output.close()

    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="talentiq_candidates.csv"'
        },
    )


# ---------------------------------------------------------------------
# Local interview scheduling
# These endpoints persist JSON records; they do not send invitations.
# ---------------------------------------------------------------------

@app.get("/api/schedule")
def list_schedule():
    return {"success": True, "items": _load_schedule()}


@app.post("/api/schedule")
def create_schedule(request: ScheduleRequest):
    try:
        parsed_date = date.fromisoformat(request.date)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Date must use YYYY-MM-DD format.",
        ) from exc

    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", request.time):
        raise HTTPException(
            status_code=400,
            detail="Time must use 24-hour HH:MM format.",
        )

    item = {
        "id": str(uuid.uuid4()),
        "candidate_name": request.candidate_name.strip(),
        "candidate_email": request.candidate_email.strip(),
        "role": request.role.strip(),
        "date": parsed_date.isoformat(),
        "time": request.time,
        "duration_minutes": request.duration_minutes,
        "interview_type": request.interview_type.strip(),
        "notes": request.notes.strip(),
        "status": "scheduled",
    }

    items = _load_schedule()
    items.append(item)
    _save_schedule(items)

    return {
        "success": True,
        "message": "Interview saved locally. No invitation has been sent.",
        "item": item,
    }


@app.delete("/api/schedule/{item_id}")
def delete_schedule(item_id: str):
    items = _load_schedule()
    updated = [item for item in items if str(item.get("id")) != item_id]

    if len(updated) == len(items):
        raise HTTPException(status_code=404, detail="Interview record not found.")

    _save_schedule(updated)
    return {"success": True, "message": "Interview record deleted."}


# ---------------------------------------------------------------------
# Basic analytics endpoint
# ---------------------------------------------------------------------

@app.post("/api/analytics")
def calculate_analytics(request: CandidateReportRequest):
    results = request.results
    scores = [
        float(item.get("match_percentage") or 0)
        for item in results
    ]

    return {
        "success": True,
        "candidate_count": len(results),
        "average_match": round(sum(scores) / len(scores), 2) if scores else 0,
        "matches_at_70_percent": sum(score >= 70 for score in scores),
        "matches_at_80_percent": sum(score >= 80 for score in scores),
    }
