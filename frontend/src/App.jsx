
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity, AlertCircle, ArrowDownToLine, ArrowRight, BarChart3,
  Bot, CalendarDays, CheckCircle2,
  ChevronRight, ClipboardCheck, Clock3, FileSearch, FileText,
  Gauge, LayoutDashboard, LoaderCircle, Menu, Mic,
  RefreshCw, Search, Settings2, ShieldCheck, Sparkles, Target,
  Trash2, Users, Workflow, X, Volume2, WandSparkles,
} from "lucide-react";
import * as pdfjsLib from "pdfjs-dist";
import pdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import "./index.css";

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8765"
).replace(/\/+$/, "");

const NAVIGATION = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "analyze", label: "Resume analysis", icon: FileSearch },
  { id: "candidates", label: "Candidates", icon: Users },
  { id: "interviews", label: "Interview AI", icon: ClipboardCheck },
  { id: "schedule", label: "Schedule", icon: CalendarDays },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "voice", label: "Voice recruiter", icon: Mic },
  { id: "agents", label: "AI agents", icon: Workflow },
  { id: "reports", label: "Reports", icon: FileText },
  { id: "settings", label: "Settings", icon: Settings2 },
];

const PAGE_INFO = {
  overview: {
    title: "Recruitment intelligence",
    description: "Your workspace for resume matching and interview operations.",
  },
  analyze: {
    title: "Resume analysis",
    description: "Compare candidate resumes with the requirements of a job.",
  },
  candidates: {
    title: "Candidates",
    description: "Review actual results returned by resume analysis.",
  },
  interviews: {
    title: "Interview AI",
    description: "Generate role-specific questions and evaluate written answers.",
  },
  schedule: {
    title: "Schedule",
    description: "Create and manage saved interview records.",
  },
  analytics: {
    title: "Analytics",
    description: "Metrics calculated from the current analysis session.",
  },
  voice: {
    title: "Voice recruiter",
    description: "Ask recruitment questions using AI and optional browser speech.",
  },
  agents: {
    title: "AI agents",
    description: "Run a recruitment analysis task against current candidate results.",
  },
  reports: {
    title: "Reports",
    description: "Export current candidate results for review.",
  },
  settings: {
    title: "Settings",
    description: "Inspect FastAPI, Ollama, and model connectivity.",
  },
};

async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const isForm = options.body instanceof FormData;

  if (options.body && !isForm && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new Error(
      `Cannot reach the backend at ${API_BASE_URL}. Start FastAPI and check frontend/.env.`
    );
  }

  const contentType = response.headers.get("content-type") || "";
  let data;

  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const detail =
      data && typeof data === "object"
        ? data.detail || data.message
        : data;

    throw new Error(
      typeof detail === "string"
        ? detail
        : `Request failed with HTTP ${response.status}.`
    );
  }

  return data;
}

function readError(error) {
  return error instanceof Error ? error.message : String(error);
}

function formatPercent(value) {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number)}%` : "—";
}

function listValue(value) {
  if (Array.isArray(value)) return value;
  if (typeof value === "string" && value.trim()) return [value];
  return [];
}

function downloadBlob(content, filename, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function extractPdfText(file) {
  const buffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: buffer }).promise;
  const pages = [];

  for (let index = 1; index <= pdf.numPages; index += 1) {
    const page = await pdf.getPage(index);
    const content = await page.getTextContent();
    pages.push(content.items.map((item) => item.str || "").join(" "));
  }

  return pages.join("\n").trim();
}

function Button({
  children,
  secondary = false,
  danger = false,
  disabled = false,
  type = "button",
  onClick,
}) {
  const className = [
    "button",
    secondary ? "button-secondary" : "button-primary",
    danger ? "button-danger" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      className={className}
      type={type}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function Notice({ children, error = false, success = false }) {
  if (!children) return null;

  return (
    <div
      className={[
        "notice",
        error ? "notice-error" : "",
        success ? "notice-success" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role={error ? "alert" : "status"}
    >
      {error && <AlertCircle size={16} />}
      {success && <CheckCircle2 size={16} />}
      <span>{children}</span>
    </div>
  );
}

function PageHeading({ eyebrow = "TALENTIQ WORKSPACE", title, description, action }) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">
          <span className="eyebrow-dot" />
          {eyebrow}
        </div>
        <h1 className="page-title">{title}</h1>
        <p className="page-description">{description}</p>
      </div>
      {action && <div className="heading-action">{action}</div>}
    </div>
  );
}

function Metric({ icon: Icon, label, value, note }) {
  return (
    <article className="metric-card">
      <div className="metric-top">
        <span>{label}</span>
        <span className="metric-icon"><Icon size={17} /></span>
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-footnote">{note}</div>
    </article>
  );
}

function Empty({ icon: Icon = FileSearch, title, text }) {
  return (
    <div className="empty-state">
      <span className="empty-icon"><Icon size={25} /></span>
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

function Loading({ label = "Loading..." }) {
  return (
    <div className="loading-state">
      <LoaderCircle size={20} className="spin" />
      <span>{label}</span>
    </div>
  );
}

function ScoreBar({ label, value }) {
  const score = Math.max(0, Math.min(100, Number(value) || 0));

  return (
    <div className="bar-row">
      <div className="bar-label">
        <span>{label}</span>
        <strong>{Math.round(score)}%</strong>
      </div>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

function OverviewPage({ results, navigate, apiStatus }) {
  const average = results.length
    ? results.reduce((sum, candidate) => sum + Number(candidate.match_percentage || 0), 0) /
      results.length
    : 0;

  const topCandidate = results[0];

  return (
    <>
      <PageHeading
        title={<>Recruitment <span className="accent">intelligence.</span></>}
        description="Analyze resumes, compare job-related skills, and prepare interviews from one workspace."
        action={
          <Button onClick={() => navigate("analyze")}>
            <FileSearch size={16} /> Analyze resumes
          </Button>
        }
      />

      <section className="hero-panel">
        <div className="hero-content">
          <div className="hero-copy-block">
            <div className="section-kicker">
              <Sparkles size={15} /> AI-ASSISTED RECRUITMENT
            </div>
            <h2 className="hero-heading">
              Find relevant skills.
              <br />
              <span className="accent">Make better-informed decisions.</span>
            </h2>
            <p className="hero-copy">
              Upload PDF resumes and a job description to calculate matching
              scores, identify skill gaps, and prepare structured interviews.
              Final hiring decisions remain with a human reviewer.
            </p>
            <div className="hero-actions">
              <Button onClick={() => navigate("analyze")}>
                Start resume analysis <ArrowRight size={16} />
              </Button>
              <Button secondary onClick={() => navigate("interviews")}>
                <ClipboardCheck size={16} /> Prepare interview
              </Button>
            </div>
          </div>
          <div className="orbit-stage" aria-hidden="true">
            <div className="orbit-ring" />
            <div className="orbit-core"><Bot size={36} /></div>
            <span className="orbit-node one" />
            <span className="orbit-node two" />
            <span className="orbit-node three" />
          </div>
        </div>
      </section>

      <div className="metrics-grid">
        <Metric
          icon={Users}
          label="Candidates analyzed"
          value={results.length}
          note="Current browser session"
        />
        <Metric
          icon={Gauge}
          label="Average match"
          value={results.length ? formatPercent(average) : "—"}
          note="Across current results"
        />
        <Metric
          icon={CheckCircle2}
          label="Backend"
          value={apiStatus.api ? "Online" : "Offline"}
          note={apiStatus.api ? "FastAPI is reachable" : "Check backend status"}
        />
      </div>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Candidate snapshot</h2>
            <p className="section-subtitle">
              This summary uses real results from your current session.
            </p>
          </div>
          <Button secondary onClick={() => navigate("candidates")}>
            View candidates <ChevronRight size={16} />
          </Button>
        </div>

        {!results.length ? (
          <Empty
            icon={Users}
            title="No candidate results yet"
            text="Run resume analysis to see ranked candidates and matching scores here."
          />
        ) : (
          <div className="candidate-list">
            {results.slice(0, 5).map((candidate, index) => (
              <div className="candidate-row" key={`${candidate.filename}-${index}`}>
                <div className="candidate-rank">{candidate.rank || index + 1}</div>
                <div className="candidate-main">
                  <strong>{candidate.filename || `Candidate ${index + 1}`}</strong>
                  <span>{candidate.role || "Role not identified"}</span>
                </div>
                <div className="candidate-score">
                  <strong>{formatPercent(candidate.match_percentage)}</strong>
                  <span>match</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {topCandidate && (
          <div className="notice notice-success">
            <CheckCircle2 size={16} />
            <span>
              Highest match in this session: <strong>{topCandidate.filename}</strong>{" "}
              ({formatPercent(topCandidate.match_percentage)}). Review the resume
              and job requirements before making a decision.
            </span>
          </div>
        )}
      </section>
    </>
  );
}

function AnalyzePage({ results, setResults, navigate, jobDescription, setJobDescription }) {
  const [resumes, setResumes] = useState([]);
  const [jdFile, setJdFile] = useState(null);
  const [extracting, setExtracting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadJobPdf(file) {
    if (!file) return;

    setJdFile(file);
    setError("");
    setSuccess("");
    setExtracting(true);

    try {
      const text = await extractPdfText(file);

      if (text.length < 20) {
        throw new Error(
          "The job-description PDF has little or no selectable text. Paste the text manually or use a text-based PDF."
        );
      }

      setJobDescription(text);
      setSuccess(`Extracted ${text.length.toLocaleString()} characters from ${file.name}.`);
    } catch (e) {
      setError(readError(e));
    } finally {
      setExtracting(false);
    }
  }

  async function submitAnalysis(event) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!resumes.length) {
      setError("Select at least one PDF resume.");
      return;
    }

    if (jobDescription.trim().length < 20) {
      setError("Upload a job-description PDF or paste at least 20 characters of job-description text.");
      return;
    }

    setLoading(true);

    try {
      const body = new FormData();
      resumes.forEach((resume) => body.append("resumes", resume));
      body.append("job_description", jobDescription.trim());

      const data = await apiRequest("/api/recruitment/analyze", {
        method: "POST",
        body,
      });

      const nextResults = Array.isArray(data.results) ? data.results : [];
      setResults(nextResults);

      try {
        sessionStorage.setItem("talentiq_results", JSON.stringify(nextResults));
        sessionStorage.setItem("talentiq_jd", jobDescription.trim());
      } catch {
        // Current in-memory results remain usable if browser storage is unavailable.
      }

      setSuccess(`Successfully analyzed ${nextResults.length} candidate(s).`);
    } catch (e) {
      setError(readError(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeading
        title={<>Resume <span className="accent">analysis.</span></>}
        description="Upload resumes and a job description to calculate matching scores and skill gaps."
      />

      <section className="panel">
        <form onSubmit={submitAnalysis}>
          <h2 className="section-title">1. Upload candidate resumes</h2>
          <label className="upload-zone">
            <span className="upload-icon"><FileText size={25} /></span>
            <strong>Choose PDF resumes</strong>
            <span>Multiple files are supported.</span>
            <span className="browse-label">Browse files</span>
            <input
              type="file"
              accept=".pdf,application/pdf"
              multiple
              onChange={(event) => setResumes(Array.from(event.target.files || []))}
            />
          </label>

          {resumes.length > 0 && (
            <div className="file-list">
              {resumes.map((file) => (
                <div className="file-row" key={`${file.name}-${file.size}`}>
                  <FileText size={17} />
                  <div><strong>{file.name}</strong><span>{(file.size / 1024).toFixed(0)} KB</span></div>
                  <button
                    className="icon-button"
                    type="button"
                    aria-label={`Remove ${file.name}`}
                    onClick={() => setResumes((current) => current.filter((item) => item !== file))}
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}

          <h2 className="section-title form-section-title">2. Job description</h2>
          <label className="jd-upload">
            <FileSearch size={22} />
            <span>
              <strong>{jdFile ? jdFile.name : "Upload job-description PDF"}</strong>
              <small>{extracting ? "Extracting PDF text..." : "Text will be extracted locally in your browser."}</small>
            </span>
            {extracting && <LoaderCircle size={18} className="spin" />}
            <input
              type="file"
              accept=".pdf,application/pdf"
              onChange={(event) => void loadJobPdf(event.target.files?.[0])}
            />
          </label>

          <label className="field-label" htmlFor="job-description">
            Or paste / edit job-description text
          </label>
          <textarea
            id="job-description"
            className="field-control job-description-input"
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            placeholder="Paste the role, responsibilities, required skills, and qualifications..."
            rows={8}
          />
          <div className="field-hint">
            {jobDescription.length.toLocaleString()} characters
          </div>

          <Notice error={error} />
          <Notice success={success} />

          <div className="form-actions">
            <Button type="submit" disabled={loading || extracting}>
              {loading ? <><LoaderCircle size={16} className="spin" /> Analyzing...</> : <><WandSparkles size={16} /> Analyze resumes</>}
            </Button>
            {results.length > 0 && (
              <Button secondary onClick={() => navigate("candidates")}>
                View results <ArrowRight size={16} />
              </Button>
            )}
          </div>
        </form>
      </section>

      {loading && <Loading label="Analyzing resumes. Large PDFs may take a moment..." />}

      {results.length > 0 && (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Latest analysis results</h2>
              <p className="section-subtitle">{results.length} candidate(s) returned by the backend.</p>
            </div>
            <Button secondary onClick={() => navigate("candidates")}>
              Open ranking <ArrowRight size={15} />
            </Button>
          </div>
          <CandidateTable results={results} onSelect={() => navigate("candidates")} />
        </section>
      )}
    </>
  );
}

function CandidateTable({ results, onSelect, onProfile }) {
  if (!results.length) {
    return (
      <Empty
        icon={Users}
        title="No analyzed candidates"
        text="Analyze resumes first. Candidate records shown here are not fabricated."
      />
    );
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Rank</th><th>Candidate</th><th>Suggested role</th>
            <th>Job match</th><th>ATS score</th><th>Recommendation</th><th>Action</th>
          </tr>
        </thead>
        <tbody>
          {results.map((candidate, index) => (
            <tr key={`${candidate.filename}-${index}`}>
              <td>#{candidate.rank || index + 1}</td>
              <td>
                <strong className="table-candidate-name">{candidate.filename || `Candidate ${index + 1}`}</strong>
                <span className="table-secondary">{candidate.email || "Email not detected"}</span>
              </td>
              <td>{candidate.role || "—"}</td>
              <td><strong>{formatPercent(candidate.match_percentage)}</strong></td>
              <td>{formatPercent(candidate.ats_score ?? candidate.score)}</td>
              <td>{candidate.recommendation || "Review required"}</td>
              <td>
                <button
                  className="text-button"
                  onClick={() => onProfile ? onProfile(candidate) : onSelect?.(candidate)}
                >
                  View profile <ChevronRight size={14} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CandidateProfile({ candidate, onClose }) {
  if (!candidate) return null;

  const detailLists = [
    ["Detected skills", candidate.keywords],
    ["Strengths", candidate.strengths],
    ["Missing skills", candidate.missing_skills],
    ["Areas to improve", candidate.weaknesses],
    ["Suggestions", candidate.suggestions],
    ["Projects", candidate.projects],
    ["Certifications", candidate.certifications],
    ["Soft skills", candidate.soft_skills],
    ["Education", candidate.education],
    ["Experience", candidate.experience],
  ];

  return (
    <div className="modal-backdrop" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <section className="profile-modal" role="dialog" aria-modal="true" aria-labelledby="profile-title">
        <div className="modal-heading">
          <div>
            <div className="section-kicker">CANDIDATE PROFILE</div>
            <h2 id="profile-title">{candidate.filename || "Candidate profile"}</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close profile"><X size={19} /></button>
        </div>

        <div className="profile-metrics">
          <Metric icon={Target} label="Job match" value={formatPercent(candidate.match_percentage)} note="Resume/JD similarity" />
          <Metric icon={Gauge} label="ATS score" value={formatPercent(candidate.ats_score ?? candidate.score)} note="Skill coverage" />
          <Metric icon={CheckCircle2} label="Candidate score" value={formatPercent(candidate.candidate_score)} note="Combined score" />
        </div>

        <p className="profile-summary">{candidate.summary || "No summary was returned for this candidate."}</p>

        <div className="detail-grid">
          <div className="detail-card"><strong>Email</strong><p>{candidate.email || "Not found"}</p></div>
          <div className="detail-card"><strong>Phone</strong><p>{candidate.phone || "Not found"}</p></div>
          <div className="detail-card"><strong>LinkedIn</strong><p>{candidate.linkedin || "Not found"}</p></div>
          <div className="detail-card"><strong>GitHub</strong><p>{candidate.github || "Not found"}</p></div>
          <div className="detail-card"><strong>Suggested role</strong><p>{candidate.role || "Not identified"}</p></div>
          <div className="detail-card"><strong>Recommendation</strong><p>{candidate.recommendation || "Human review required"}</p></div>
        </div>

        {detailLists.map(([label, value]) => {
          const values = listValue(value);
          if (!values.length) return null;

          return (
            <section className="profile-detail-section" key={label}>
              <h3>{label}</h3>
              <ul>{values.map((item, index) => <li key={`${label}-${index}`}>{String(item)}</li>)}</ul>
            </section>
          );
        })}

        <p className="small-note">
          Scores and recommendations are decision-support signals, not a final hiring decision.
        </p>
        <Button onClick={onClose}>Close profile</Button>
      </section>
    </div>
  );
}

function CandidatesPage({ results, setSelectedCandidate }) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return results;

    return results.filter((candidate) =>
      [
        candidate.filename, candidate.email, candidate.role,
        candidate.recommendation, ...listValue(candidate.keywords),
      ].some((value) => String(value || "").toLowerCase().includes(query))
    );
  }, [results, search]);

  return (
    <>
      <PageHeading
        title={<>Candidate <span className="accent">ranking.</span></>}
        description="Search and inspect candidates returned by your latest resume analysis."
      />
      <section className="panel">
        <div className="panel-heading">
          <div><h2>Analyzed candidates</h2><p className="section-subtitle">{filtered.length} of {results.length} candidates</p></div>
          <label className="search-control">
            <Search size={16} />
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search candidates..." />
          </label>
        </div>
        <CandidateTable results={filtered} onProfile={setSelectedCandidate} />
      </section>
    </>
  );
}

function InterviewsPage({ jobDescription, results }) {
  const [jd, setJd] = useState(jobDescription);
  const [questionCount, setQuestionCount] = useState("8");
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [evaluation, setEvaluation] = useState(null);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function generateQuestions(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setEvaluation(null);

    if (jd.trim().length < 20) {
      setError("Enter a job description of at least 20 characters.");
      return;
    }

    setLoadingQuestions(true);

    try {
      const data = await apiRequest("/api/interviews/questions", {
        method: "POST",
        body: JSON.stringify({
          job_description: jd.trim(),
          question_count: Number(questionCount),
        }),
      });

      setQuestions(Array.isArray(data.questions) ? data.questions : []);
      setAnswers({});
      setMessage(`Generated ${(data.questions || []).length} interview questions.`);
    } catch (e) {
      setError(readError(e));
    } finally {
      setLoadingQuestions(false);
    }
  }

  async function evaluateAnswers() {
    setError("");
    setMessage("");
    setEvaluating(true);

    try {
      const data = await apiRequest("/api/interviews/evaluate", {
        method: "POST",
        body: JSON.stringify({ questions, answers }),
      });

      setEvaluation(data.evaluation);
      setMessage("Evaluation completed.");
    } catch (e) {
      setError(readError(e));
    } finally {
      setEvaluating(false);
    }
  }

  return (
    <>
      <PageHeading
        title={<>Interview <span className="accent">AI.</span></>}
        description="Generate job-specific interview questions and evaluate the candidate's written responses."
      />

      <section className="panel">
        <form onSubmit={generateQuestions}>
          <label className="field-label" htmlFor="interview-jd">Job description</label>
          <textarea
            id="interview-jd"
            className="field-control"
            rows={6}
            value={jd}
            onChange={(event) => setJd(event.target.value)}
            placeholder="Paste the role requirements and responsibilities..."
          />
          <div className="inline-fields">
            <div>
              <label className="field-label" htmlFor="question-count">Number of questions</label>
              <select id="question-count" className="field-control" value={questionCount} onChange={(event) => setQuestionCount(event.target.value)}>
                {[5, 8, 10, 12, 15, 20].map((count) => <option value={count} key={count}>{count} questions</option>)}
              </select>
            </div>
            <div className="inline-field-note">
              {results.length
                ? `${results.length} candidate result(s) are available in this session.`
                : "Analyze resumes first to populate candidate results."}
            </div>
          </div>
          <Notice error>{error}</Notice>
          <Notice success>{message}</Notice>
          <Button type="submit" disabled={loadingQuestions}>
            {loadingQuestions ? <><LoaderCircle size={16} className="spin" /> Generating...</> : <><Sparkles size={16} /> Generate questions</>}
          </Button>
        </form>
      </section>

      {questions.length > 0 && (
        <section className="panel">
          <div className="panel-heading"><div><h2>Interview questions</h2><p className="section-subtitle">Enter the candidate's answers below each question.</p></div><span className="soft-badge">{questions.length} questions</span></div>
          <div className="question-list">
            {questions.map((item, index) => (
              <article className="question-card" key={`${item.question}-${index}`}>
                <div className="question-number">{index + 1}</div>
                <div className="question-content">
                  <span className="section-kicker">{item.category || "GENERAL"}</span>
                  <h3>{item.question}</h3>
                  {listValue(item.expected_points).length > 0 && (
                    <p className="question-hint">Areas to consider: {listValue(item.expected_points).join(", ")}</p>
                  )}
                  <label className="field-label" htmlFor={`answer-${index}`}>Candidate answer</label>
                  <textarea
                    id={`answer-${index}`}
                    className="field-control"
                    rows={4}
                    value={answers[String(index)] || ""}
                    onChange={(event) => setAnswers((current) => ({ ...current, [String(index)]: event.target.value }))}
                    placeholder="Enter the candidate's response..."
                  />
                </div>
              </article>
            ))}
          </div>
          <Button onClick={() => void evaluateAnswers()} disabled={evaluating}>
            {evaluating ? <><LoaderCircle size={16} className="spin" /> Evaluating...</> : <><ClipboardCheck size={16} /> Evaluate answers</>}
          </Button>
        </section>
      )}

      {evaluation !== null && (
        <section className="panel">
          <h2>Evaluation results</h2>
          {typeof evaluation === "string" ? (
            <pre className="response-pre">{evaluation}</pre>
          ) : (
            <div className="evaluation-content">
              <p>{evaluation?.overall_feedback || "Review the detailed evaluation below."}</p>
              {["strengths", "improvements", "per_question"].map((key) => {
                const value = evaluation?.[key];
                if (!value) return null;
                return (
                  <div className="evaluation-section" key={key}>
                    <h3>{key.replaceAll("_", " ")}</h3>
                    <pre className="response-pre">{JSON.stringify(value, null, 2)}</pre>
                  </div>
                );
              })}
              {!evaluation?.overall_feedback && !evaluation?.strengths && !evaluation?.improvements && !evaluation?.per_question && (
                <pre className="response-pre">{JSON.stringify(evaluation, null, 2)}</pre>
              )}
            </div>
          )}
        </section>
      )}
    </>
  );
}

function SchedulePage() {
  const [items, setItems] = useState([]);
  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [role, setRole] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [duration, setDuration] = useState("30");
  const [interviewType, setInterviewType] = useState("Technical");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadSchedule = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest("/api/schedule");
      setItems(Array.isArray(data.items) ? data.items : []);
    } catch (e) {
      setError(readError(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      void loadSchedule();
    }, 0);

    return () => clearTimeout(timeoutId);
  }, [loadSchedule]);

  async function saveInterview(event) {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!candidateName.trim() || !role.trim() || !date || !time) {
      setError("Enter the candidate name, role, date, and time.");
      return;
    }

    setSaving(true);

    try {
      const data = await apiRequest("/api/schedule", {
        method: "POST",
        body: JSON.stringify({
          candidate_name: candidateName.trim(),
          candidate_email: candidateEmail.trim(),
          role: role.trim(),
          date,
          time,
          duration_minutes: Number(duration),
          interview_type: interviewType,
          notes: notes.trim(),
        }),
      });

      setMessage(data.message || "Interview saved.");
      setCandidateName("");
      setCandidateEmail("");
      setRole("");
      setDate("");
      setTime("");
      setDuration("30");
      setInterviewType("Technical");
      setNotes("");
      await loadSchedule();
    } catch (e) {
      setError(readError(e));
    } finally {
      setSaving(false);
    }
  }

  async function removeInterview(id) {
    if (!window.confirm("Delete this saved interview?")) return;

    setError("");
    setMessage("");

    try {
      const data = await apiRequest(`/api/schedule/${encodeURIComponent(id)}`, {
        method: "DELETE",
      });
      setMessage(data.message || "Interview deleted.");
      await loadSchedule();
    } catch (e) {
      setError(readError(e));
    }
  }

  return (
    <>
      <PageHeading
        title={<>Interview <span className="accent">schedule.</span></>}
        description="Create, save, review, and remove interview schedule records."
      />

      <section className="panel">
        <h2 className="section-title">Schedule an interview</h2>
        <form onSubmit={saveInterview}>
          <div className="form-grid">
            <div>
              <label className="field-label" htmlFor="schedule-name">Candidate name</label>
              <input id="schedule-name" className="field-control" value={candidateName} onChange={(event) => setCandidateName(event.target.value)} maxLength={200} required placeholder="Candidate name" />
            </div>
            <div>
              <label className="field-label" htmlFor="schedule-email">Candidate email (optional)</label>
              <input id="schedule-email" type="email" className="field-control" value={candidateEmail} onChange={(event) => setCandidateEmail(event.target.value)} placeholder="candidate@example.com" />
            </div>
            <div>
              <label className="field-label" htmlFor="schedule-role">Job role</label>
              <input id="schedule-role" className="field-control" value={role} onChange={(event) => setRole(event.target.value)} maxLength={200} required placeholder="AI/ML Engineer" />
            </div>
            <div>
              <label className="field-label" htmlFor="schedule-date">Interview date</label>
              <input id="schedule-date" type="date" className="field-control" value={date} onChange={(event) => setDate(event.target.value)} min={new Date().toLocaleDateString("en-CA")} required />
            </div>
            <div>
              <label className="field-label" htmlFor="schedule-time">Interview time</label>
              <input id="schedule-time" type="time" className="field-control" value={time} onChange={(event) => setTime(event.target.value)} required />
            </div>
            <div>
              <label className="field-label" htmlFor="schedule-duration">Duration</label>
              <select id="schedule-duration" className="field-control" value={duration} onChange={(event) => setDuration(event.target.value)}>
                {[15, 30, 45, 60, 90, 120].map((minutes) => <option value={minutes} key={minutes}>{minutes} minutes</option>)}
              </select>
            </div>
            <div>
              <label className="field-label" htmlFor="schedule-type">Interview type</label>
              <select id="schedule-type" className="field-control" value={interviewType} onChange={(event) => setInterviewType(event.target.value)}>
                {["Technical", "HR", "Behavioural", "Managerial", "Final round"].map((type) => <option key={type}>{type}</option>)}
              </select>
            </div>
          </div>

          <label className="field-label" htmlFor="schedule-notes">Notes (optional)</label>
          <textarea id="schedule-notes" className="field-control" rows={3} value={notes} onChange={(event) => setNotes(event.target.value)} maxLength={3000} placeholder="Topics to cover or instructions..." />
          <Notice error>{error}</Notice>
          <Notice success={Boolean(message)}>{message}</Notice>
          <Button type="submit" disabled={saving}>
            {saving ? <><LoaderCircle size={16} className="spin" /> Saving...</> : <><CalendarDays size={16} /> Save interview</>}
          </Button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div><h2>Saved interviews</h2><p className="section-subtitle">Saved locally by the backend.</p></div>
          <Button secondary disabled={loading} onClick={() => void loadSchedule()}><RefreshCw size={15} /> Refresh</Button>
        </div>

        {loading ? <Loading label="Loading saved interviews..." /> : items.length === 0 ? (
          <Empty icon={CalendarDays} title="No saved interviews yet" text="Create your first interview using the form above." />
        ) : (
          <div className="schedule-list">
            {items.map((item) => (
              <article className="schedule-card" key={item.id}>
                <div className="schedule-card-top">
                  <div><h3>{item.candidate_name}</h3><p>{item.role}</p></div>
                  <span className="soft-badge">{item.status || "scheduled"}</span>
                </div>
                <div className="schedule-details">
                  <span><CalendarDays size={15} /> {item.date}</span>
                  <span><Clock3 size={15} /> {item.time}</span>
                  <span><Activity size={15} /> {item.duration_minutes} min</span>
                  <span><ClipboardCheck size={15} /> {item.interview_type}</span>
                </div>
                {item.candidate_email && <p className="schedule-note">{item.candidate_email}</p>}
                {item.notes && <p className="schedule-note">{item.notes}</p>}
                <Button secondary danger onClick={() => void removeInterview(item.id)}><Trash2 size={15} /> Delete</Button>
              </article>
            ))}
          </div>
        )}

        <p className="small-note">
          Records persist in the local JSON file. This does not send calendar invitations or emails.
        </p>
      </section>
    </>
  );
}

function AnalyticsPage({ results }) {
  const average = results.length
    ? results.reduce((sum, item) => sum + Number(item.match_percentage || 0), 0) / results.length
    : 0;
  const highMatches = results.filter((item) => Number(item.match_percentage || 0) >= 70).length;

  return (
    <>
      <PageHeading
        title={<>Recruitment <span className="accent">analytics.</span></>}
        description="Metrics calculated from actual resume-analysis results in this browser session."
      />
      <div className="metrics-grid">
        <Metric icon={Users} label="Analyzed candidates" value={results.length} note="Current session" />
        <Metric icon={Gauge} label="Average match" value={results.length ? formatPercent(average) : "—"} note="Across current results" />
        <Metric icon={CheckCircle2} label="Matches at 70%+" value={highMatches} note="Screening indicator only" />
      </div>
      <section className="panel">
        <h2>Candidate match scores</h2>
        {!results.length ? (
          <Empty icon={BarChart3} title="No analytics yet" text="Analyze resumes to calculate metrics from real results." />
        ) : results.map((candidate, index) => (
          <ScoreBar key={`${candidate.filename}-${index}`} label={candidate.filename || `Candidate ${index + 1}`} value={candidate.match_percentage} />
        ))}
      </section>
    </>
  );
}

function VoicePage({ results, jobDescription }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState("");
  const [recognition, setRecognition] = useState(null);

  useEffect(() => () => {
    if (recognition) recognition.stop();
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  }, [recognition]);

  async function askRecruiter(event) {
    event.preventDefault();
    setError("");
    setAnswer("");

    if (!question.trim()) {
      setError("Enter a question or use voice input first.");
      return;
    }

    setLoading(true);

    try {
      const data = await apiRequest("/api/voice/answer", {
        method: "POST",
        body: JSON.stringify({
          question: question.trim(),
          candidates: results,
          job_description: jobDescription,
        }),
      });
      setAnswer(data.answer || "The backend returned no answer.");
    } catch (e) {
      setError(readError(e));
    } finally {
      setLoading(false);
    }
  }

  function startVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError("Speech recognition is not supported in this browser. Type your question instead.");
      return;
    }

    setError("");
    const instance = new SpeechRecognition();
    instance.lang = "en-IN";
    instance.interimResults = false;
    instance.maxAlternatives = 1;

    instance.onstart = () => setListening(true);
    instance.onend = () => setListening(false);
    instance.onerror = (event) => {
      setListening(false);
      setError(`Voice input failed: ${event.error || "unknown error"}. You can type your question instead.`);
    };
    instance.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || "";
      setQuestion((current) => `${current}${current ? " " : ""}${transcript}`.trim());
    };

    setRecognition(instance);
    instance.start();
  }

  function speakAnswer() {
    if (!answer) {
      setError("Ask a question and receive an answer before using speech output.");
      return;
    }
    if (!("speechSynthesis" in window)) {
      setError("Speech output is not supported in this browser.");
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(answer);
    utterance.lang = "en-IN";
    window.speechSynthesis.speak(utterance);
  }

  return (
    <>
      <PageHeading
        title={<>Voice <span className="accent">recruiter.</span></>}
        description="Ask questions about current candidate matches, missing skills, and interview preparation."
      />

      <section className="hero-panel voice-hero">
        <div className="hero-content">
          <div className="hero-copy-block">
            <div className="section-kicker"><Mic size={15} /> VOICE INTERFACE</div>
            <h2 className="hero-heading">Ask TalentIQ.<br /><span className="accent">Get a grounded answer.</span></h2>
            <p className="hero-copy">
              The browser handles speech input and output. The backend uses your
              configured local Ollama model to generate the response.
            </p>
            <div className="hero-actions">
              <Button onClick={startVoiceInput} disabled={listening}>
                <Mic size={16} /> {listening ? "Listening..." : "Start voice capture"}
              </Button>
              <Button secondary onClick={speakAnswer}><Volume2 size={16} /> Read answer aloud</Button>
            </div>
          </div>
          <div className="orbit-stage"><div className="orbit-ring" /><div className="orbit-core"><Mic size={34} /></div></div>
        </div>
      </section>

      <section className="panel">
        <h2><Bot size={19} /> Ask TalentIQ</h2>
        <p className="section-subtitle">
          {results.length
            ? `${results.length} candidate result(s) will be provided as context.`
            : "No candidate results are available yet. The assistant will say when it lacks candidate data."}
        </p>
        <form onSubmit={askRecruiter}>
          <label className="field-label" htmlFor="voice-question">Your question</label>
          <textarea
            id="voice-question"
            className="field-control"
            rows={5}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Which candidate has the strongest match?"
          />
          <Notice error>{error}</Notice>
          <div className="form-actions">
            <Button type="submit" disabled={loading}>
              {loading ? <><LoaderCircle size={16} className="spin" /> Asking AI...</> : <><Sparkles size={16} /> Ask AI recruiter</>}
            </Button>
          </div>
        </form>
        <div className="response-section">
          <h3>AI response</h3>
          {loading ? <Loading label="Waiting for the local model..." /> : answer ? (
            <div className="response-card"><p>{answer}</p></div>
          ) : (
            <Empty icon={Bot} title="No response yet" text="Submit a question to receive an answer from the backend." />
          )}
        </div>
      </section>
    </>
  );
}

function AgentsPage({ results, jobDescription }) {
  const [task, setTask] = useState(
    "Analyze the candidate results, identify the strongest job-related matches, highlight skill gaps, and recommend next recruitment steps."
  );
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function runTask(event) {
    event.preventDefault();
    setError("");
    setResult("");

    if (!task.trim()) {
      setError("Enter instructions for the recruitment agent.");
      return;
    }

    setLoading(true);

    try {
      const data = await apiRequest("/api/agents/run", {
        method: "POST",
        body: JSON.stringify({
          task: task.trim(),
          candidates: results,
          job_description: jobDescription,
        }),
      });
      setResult(data.result || "The backend returned no task result.");
    } catch (e) {
      setError(readError(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeading
        title={<>AI <span className="accent">agents.</span></>}
        description="Run a local AI recruitment analysis task grounded in the current session's candidate results."
      />
      <section className="panel">
        <div className="agent-heading">
          <span className="large-icon"><Workflow size={25} /></span>
          <div><h2>Recruitment analysis agent</h2><p className="section-subtitle">This agent reports findings and next steps. It does not claim to send emails or modify records.</p></div>
        </div>
        <form onSubmit={runTask}>
          <label className="field-label" htmlFor="agent-task">Task instructions</label>
          <textarea id="agent-task" className="field-control" rows={5} value={task} onChange={(event) => setTask(event.target.value)} />
          <Notice error>{error}</Notice>
          <Button type="submit" disabled={loading}>
            {loading ? <><LoaderCircle size={16} className="spin" /> Running task...</> : <><Workflow size={16} /> Run AI task</>}
          </Button>
        </form>
        <div className="response-section">
          <h3>Agent result</h3>
          {loading ? <Loading label="The local model is analyzing your task..." /> : result ? (
            <div className="response-card"><p>{result}</p></div>
          ) : (
            <Empty icon={Workflow} title="No agent result yet" text="Submit task instructions to run the recruitment analysis agent." />
          )}
        </div>
      </section>
    </>
  );
}

function ReportsPage({ results }) {
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  function exportJson() {
    downloadBlob(JSON.stringify(results, null, 2), "talentiq-candidates.json", "application/json");
    setMessage("JSON export created.");
    setError("");
  }

  async function exportCsv() {
    setError("");
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/reports/candidates.csv`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ results }),
      });

      if (!response.ok) {
        let detail = `CSV export failed with HTTP ${response.status}.`;
        try {
          const data = await response.json();
          detail = data.detail || detail;
        } catch {
          // Keep fallback error.
        }
        throw new Error(detail);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "talentiq_candidates.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setMessage("CSV export created.");
    } catch (e) {
      setError(readError(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeading
        title={<>Recruitment <span className="accent">reports.</span></>}
        description="Download candidate results from the current browser session."
      />
      <section className="panel">
        <h2>Candidate exports</h2>
        <p className="section-subtitle">Exports contain current analysis data only; they do not imply a persistent candidate database.</p>
        <div className="report-options">
          <article className="report-option">
            <span className="large-icon"><FileText size={22} /></span>
            <div><h3>CSV report</h3><p>Spreadsheet-friendly candidate results and scores.</p></div>
            <Button onClick={() => void exportCsv()} disabled={loading}><ArrowDownToLine size={15} /> {loading ? "Exporting..." : "Export CSV"}</Button>
          </article>
          <article className="report-option">
            <span className="large-icon"><FileSearch size={22} /></span>
            <div><h3>JSON report</h3><p>Full structured results for development or review.</p></div>
            <Button secondary onClick={exportJson}><ArrowDownToLine size={15} /> Export JSON</Button>
          </article>
        </div>
        <Notice error>{error}</Notice>
        <Notice success={Boolean(message)}>{message}</Notice>
        <div className="section-header"><div><h3 className="section-title">Report preview</h3><p className="section-subtitle">{results.length} candidate record(s)</p></div></div>
        <CandidateTable results={results} onSelect={() => {}} />
      </section>
    </>
  );
}

function SettingsPage({ apiStatus, refreshStatus, checking }) {
  return (
    <>
      <PageHeading
        title={<>Workspace <span className="accent">settings.</span></>}
        description="Inspect backend and local model connectivity."
        action={<Button secondary onClick={refreshStatus} disabled={checking}><RefreshCw size={16} className={checking ? "spin" : ""} /> Refresh status</Button>}
      />
      <section className="panel">
        <div className="setting-row">
          <div><strong>FastAPI backend</strong><p>{API_BASE_URL}</p></div>
          <span className={`status-badge ${apiStatus.api ? "good" : "bad"}`}>{apiStatus.api ? "Connected" : "Unavailable"}</span>
        </div>
        <div className="setting-row">
          <div><strong>Ollama</strong><p>{apiStatus.ollama_url || "http://127.0.0.1:11434"}</p></div>
          <span className={`status-badge ${apiStatus.ollama === "connected" ? "good" : "bad"}`}>{apiStatus.ollama || "Not verified"}</span>
        </div>
        <div className="setting-row">
          <div><strong>Model</strong><p>{apiStatus.model || "Not reported"}</p></div>
          <span className={`status-badge ${apiStatus.model_available ? "good" : "bad"}`}>{apiStatus.model_available ? "Available" : "Not verified"}</span>
        </div>
        {apiStatus.error && <Notice error>{apiStatus.error}</Notice>}
        <div className="notice">
          <ShieldCheck size={16} />
          <span>AI-assisted hiring requires human review. The backend does not send calendar invitations or emails from this interface.</span>
        </div>
        <p className="small-note">
          To change the API URL, set VITE_API_BASE_URL in frontend/.env and restart Vite.
        </p>
      </section>
    </>
  );
}

export default function App() {
  const [activePage, setActivePage] = useState("overview");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [results, setResults] = useState(() => {
    try {
      const saved = sessionStorage.getItem("talentiq_results");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [jobDescription, setJobDescription] = useState(() => {
    try {
      return sessionStorage.getItem("talentiq_jd") || "";
    } catch {
      return "";
    }
  });
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [apiStatus, setApiStatus] = useState({
    api: false,
    ollama: "unknown",
    model: "",
    model_available: false,
    error: "",
  });
  const [checkingStatus, setCheckingStatus] = useState(false);

  const navigate = useCallback((page) => {
    setActivePage(page);
    setMobileMenuOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const refreshStatus = useCallback(async () => {
    setCheckingStatus(true);

    try {
      const data = await apiRequest("/api/system/status");
      setApiStatus({ ...data, api: true });
    } catch (error) {
      setApiStatus({
        api: false,
        ollama: "disconnected",
        model: "",
        model_available: false,
        error: readError(error),
      });
    } finally {
      setCheckingStatus(false);
    }
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      void refreshStatus();
    }, 0);

    return () => clearTimeout(timeoutId);
  }, [refreshStatus]);

  useEffect(() => {
    try {
      sessionStorage.setItem("talentiq_results", JSON.stringify(results));
      sessionStorage.setItem("talentiq_jd", jobDescription);
    } catch {
      // The application remains usable in memory if session storage is blocked.
    }
  }, [results, jobDescription]);

  useEffect(() => {
    function handleNavigate(event) {
      const page = event.detail;
      if (NAVIGATION.some((item) => item.id === page)) navigate(page);
    }

    window.addEventListener("recruitment:navigate", handleNavigate);
    return () => window.removeEventListener("recruitment:navigate", handleNavigate);
  }, [navigate]);

  const currentPage = PAGE_INFO[activePage] || PAGE_INFO.overview;
  const ActiveIcon = NAVIGATION.find((item) => item.id === activePage)?.icon || LayoutDashboard;

  function renderPage() {
    switch (activePage) {
      case "analyze":
        return <AnalyzePage results={results} setResults={setResults} navigate={navigate} jobDescription={jobDescription} setJobDescription={setJobDescription} />;
      case "candidates":
        return <CandidatesPage results={results} setSelectedCandidate={setSelectedCandidate} />;
      case "interviews":
        return <InterviewsPage jobDescription={jobDescription} results={results} />;
      case "schedule":
        return <SchedulePage />;
      case "analytics":
        return <AnalyticsPage results={results} />;
      case "voice":
        return <VoicePage results={results} jobDescription={jobDescription} />;
      case "agents":
        return <AgentsPage results={results} jobDescription={jobDescription} />;
      case "reports":
        return <ReportsPage results={results} />;
      case "settings":
        return <SettingsPage apiStatus={apiStatus} refreshStatus={refreshStatus} checking={checkingStatus} />;
      default:
        return <OverviewPage results={results} navigate={navigate} apiStatus={apiStatus} />;
    }
  }

  return (
    <div className="app-shell">
      <button
        className="mobile-menu-button"
        onClick={() => setMobileMenuOpen((value) => !value)}
        aria-label="Toggle navigation"
      >
        {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {mobileMenuOpen && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setMobileMenuOpen(false)} />}

      <div className="layout">
        <aside className={`sidebar ${mobileMenuOpen ? "sidebar-open" : ""}`}>
          <button className="brand" onClick={() => navigate("overview")}>
            <span className="brand-mark"><Bot size={23} /></span>
            <span className="brand-text"><strong>TalentIQ</strong><small>AI RECRUITMENT ASSISTANT</small></span>
          </button>

          <div className="nav-label">WORKSPACE</div>
          <nav className="nav-list" aria-label="Main navigation">
            {NAVIGATION.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  className={`nav-item ${activePage === item.id ? "active" : ""}`}
                  onClick={() => navigate(item.id)}
                >
                  <Icon size={19} />
                  <span>{item.label}</span>
                  {activePage === item.id && <ArrowRight className="nav-arrow" size={16} />}
                </button>
              );
            })}
          </nav>

          <button className="sidebar-status" onClick={() => navigate("settings")}>
            <span className={`status-dot ${apiStatus.api ? "online" : "offline"}`} />
            <span><strong>{apiStatus.api ? "API connected" : "API not verified"}</strong><small>{apiStatus.api ? "Backend reachable" : "Check backend status"}</small></span>
          </button>

          <div className="sidebar-footer">
            <div className="footer-brand"><span className="brand-mark small"><Bot size={17} /></span><strong>Recruiter workspace</strong></div>
            <p>AI-assisted hiring requires human review.</p>
          </div>
        </aside>

        <main className="main-area">
          <header className="topbar">
            <div className="topbar-title">
              <span className="topbar-eyebrow">RECRUITMENT INTELLIGENCE</span>
              <h2><ActiveIcon size={18} /> {currentPage.title}</h2>
            </div>
            <div className="topbar-actions">
              <button className="connection-button" onClick={refreshStatus} disabled={checkingStatus}>
                <span className={`status-dot ${apiStatus.api ? "online" : "offline"}`} />
                {checkingStatus ? "CHECKING..." : apiStatus.api ? "CONNECTED" : "CHECK CONNECTION"}
              </button>
              <Button onClick={() => navigate("analyze")}><FileSearch size={16} /> Analyze resumes</Button>
            </div>
          </header>

          <div className="main-content">
            {renderPage()}
            <footer className="footer-line">
              <span>TalentIQ · AI Recruitment Assistant</span>
              <span><ShieldCheck size={14} /> AI-assisted hiring requires human review.</span>
            </footer>
          </div>
        </main>
      </div>

      {selectedCandidate && <CandidateProfile candidate={selectedCandidate} onClose={() => setSelectedCandidate(null)} />}
    </div>
  );
}
