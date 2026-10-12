
"""Grounded retrieval-augmented question answering for recruiters."""

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend.repositories.candidate_repository import CandidateRepository


@dataclass(frozen=True)
class Evidence:
    candidate_id: str
    candidate_name: str
    source: str
    text: str
    score: float

    @property
    def citation(self) -> str:
        return f"[{self.candidate_id} — {self.source}]"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "source": self.source,
            "text": self.text,
            "score": round(self.score, 4),
            "citation": self.citation,
        }


class RecruiterRAGService:
    """Retrieve candidate evidence and answer using only retrieved records."""

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    MAX_CHUNK_CHARACTERS = 900
    DEFAULT_TOP_K = 5
    MAX_TOP_K = 20

    def __init__(
        self,
        candidate_repository: Optional[CandidateRepository] = None,
        embedder: Optional[Any] = None,
        use_semantic_search: bool = True,
    ) -> None:
        self.repository = (
            candidate_repository
            if candidate_repository is not None
            else CandidateRepository()
        )
        self.embedder = embedder
        self.use_semantic_search = use_semantic_search
        self._embedding_attempted = embedder is not None
        self._embedding_unavailable = False

    @staticmethod
    def _tokens(text: str) -> List[str]:
        return re.findall(r"[a-zA-Z0-9+#.]+", text.lower())

    @classmethod
    def _split_text(cls, text: str) -> List[str]:
        """Split long resume text into overlapping, bounded chunks."""
        text = " ".join(text.split())
        if not text:
            return []

        if len(text) <= cls.MAX_CHUNK_CHARACTERS:
            return [text]

        chunks: List[str] = []
        start = 0
        overlap = 120

        while start < len(text):
            end = min(start + cls.MAX_CHUNK_CHARACTERS, len(text))

            if end < len(text):
                boundary = text.rfind(" ", start + 500, end)
                if boundary > start:
                    end = boundary

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            start = max(end - overlap, start + 1)

        return chunks

    @classmethod
    def _candidate_documents(cls, candidate: Any) -> List[Dict[str, str]]:
        """Convert structured candidate fields into citable evidence."""
        candidate_id = str(getattr(candidate, "candidate_id", "") or "").strip()
        candidate_name = str(getattr(candidate, "name", "") or "").strip()

        if not candidate_id:
            return []

        documents: List[Dict[str, str]] = []

        def add(source: str, value: Any) -> None:
            if isinstance(value, str):
                text = value.strip()
            elif isinstance(value, (list, tuple, set)):
                text = ", ".join(
                    str(item).strip()
                    for item in value
                    if item is not None and str(item).strip()
                )
            else:
                text = ""

            if text:
                documents.append({
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name or candidate_id,
                    "source": source,
                    "text": text,
                })

        add("skills", getattr(candidate, "skills", []))
        add(
            "experience_years",
            str(getattr(candidate, "experience_years", "")),
        )
        add("education", getattr(candidate, "education", []))
        add("projects", getattr(candidate, "projects", []))
        add("certifications", getattr(candidate, "certifications", []))
        add("resume_text", getattr(candidate, "resume_text", ""))

        chunked: List[Dict[str, str]] = []
        for document in documents:
            for index, chunk in enumerate(
                cls._split_text(document["text"]), start=1
            ):
                chunked.append({
                    **document,
                    "text": chunk,
                    "source": (
                        document["source"]
                        if document["source"] != "resume_text"
                        else f"resume_text, chunk {index}"
                    ),
                })

        return chunked

    def _all_documents(self) -> List[Dict[str, str]]:
        documents: List[Dict[str, str]] = []
        for candidate in self.repository.get_all():
            documents.extend(self._candidate_documents(candidate))
        return documents

    @staticmethod
    def _lexical_score(
        query_tokens: List[str],
        document_text: str,
        document_frequency: Counter,
        document_count: int,
    ) -> float:
        """Score token overlap with inverse-document-frequency weighting."""
        document_tokens = RecruiterRAGService._tokens(document_text)
        if not query_tokens or not document_tokens:
            return 0.0

        counts = Counter(document_tokens)
        unique_query_tokens = set(query_tokens)
        score = 0.0

        for token in unique_query_tokens:
            if token not in counts:
                continue

            idf = math.log(
                1.0 + (document_count + 1) /
                (document_frequency[token] + 1)
            )
            term_frequency = counts[token] / len(document_tokens)
            score += idf * (1.0 + math.log(counts[token])) * term_frequency

        return score / math.sqrt(len(unique_query_tokens))

    def _load_embedder(self) -> Optional[Any]:
        if self.embedder is not None:
            return self.embedder

        if self._embedding_attempted or self._embedding_unavailable:
            return None

        self._embedding_attempted = True

        if not self.use_semantic_search:
            return None

        try:
            from sentence_transformers import SentenceTransformer

            self.embedder = SentenceTransformer(self.MODEL_NAME)
            return self.embedder
        except Exception:
            # A model may be missing or unavailable offline. Keep the
            # assistant usable with lexical retrieval instead.
            self._embedding_unavailable = True
            return None

    def _semantic_scores(
        self,
        question: str,
        documents: List[Dict[str, str]],
    ) -> Optional[List[float]]:
        embedder = self._load_embedder()
        if embedder is None:
            return None

        try:
            texts = [question] + [item["text"] for item in documents]
            vectors = embedder.encode(texts, normalize_embeddings=True)

            query_vector = vectors[0]
            scores: List[float] = []

            for vector in vectors[1:]:
                score = sum(
                    float(left) * float(right)
                    for left, right in zip(query_vector, vector)
                )
                scores.append(score)

            return scores
        except Exception:
            self._embedding_unavailable = True
            self.embedder = None
            return None

    def retrieve(
        self,
        question: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> List[Evidence]:
        """Return the highest-ranked evidence records for a question."""
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string.")

        if isinstance(top_k, bool) or not isinstance(top_k, int):
            raise TypeError("top_k must be an integer.")

        if not 1 <= top_k <= self.MAX_TOP_K:
            raise ValueError(
                f"top_k must be between 1 and {self.MAX_TOP_K}."
            )

        documents = self._all_documents()
        if not documents:
            return []

        query_tokens = self._tokens(question)
        if not query_tokens:
            return []

        tokenized_documents = [
            set(self._tokens(item["text"])) for item in documents
        ]
        document_frequency: Counter = Counter()
        for tokens in tokenized_documents:
            document_frequency.update(tokens)

        semantic_scores = self._semantic_scores(question, documents)

        if semantic_scores is not None:
            scored = [
                (float(score), index)
                for index, score in enumerate(semantic_scores)
            ]
            # Cosine scores below zero are not useful evidence.
            scored = [
                (score, index)
                for score, index in scored
                if score > 0.0
            ]
        else:
            scored = [
                (
                    self._lexical_score(
                        query_tokens,
                        document["text"],
                        document_frequency,
                        len(documents),
                    ),
                    index,
                )
                for index, document in enumerate(documents)
            ]
            scored = [
                (score, index)
                for score, index in scored
                if score > 0.0
            ]

        scored.sort(
            key=lambda item: (
                item[0],
                documents[item[1]]["candidate_id"],
                documents[item[1]]["source"],
            ),
            reverse=True,
        )

        results: List[Evidence] = []
        seen = set()

        for score, index in scored:
            document = documents[index]
            identity = (
                document["candidate_id"],
                document["source"],
                document["text"],
            )
            if identity in seen:
                continue
            seen.add(identity)

            results.append(
                Evidence(
                    candidate_id=document["candidate_id"],
                    candidate_name=document["candidate_name"],
                    source=document["source"],
                    text=document["text"],
                    score=score,
                )
            )

            if len(results) >= top_k:
                break

        return results

    def answer_question(
        self,
        question: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> Dict[str, Any]:
        """Create a concise, evidence-grounded answer with citations."""
        evidence = self.retrieve(question=question, top_k=top_k)

        if not evidence:
            answer = (
                "I couldn't find relevant evidence in the stored candidate "
                "records. Try a question about a candidate's skills, "
                "experience, education, projects, certifications, or resume."
            )
        else:
            lines = ["Based on the retrieved candidate records:"]
            for item in evidence:
                lines.append(
                    f"- {item.candidate_name} "
                    f"(ID: {item.candidate_id}): {item.text} "
                    f"{item.citation}"
                )
            lines.append(
                "These results summarize retrieved evidence; they do not "
                "establish facts that are absent from the cited records."
            )
            answer = "\n".join(lines)

        return {
            "question": question,
            "answer": answer,
            "sources": [item.to_dict() for item in evidence],
            "retrieved_count": len(evidence),
            "answer_mode": (
                "grounded_evidence_summary"
                if evidence
                else "no_relevant_evidence"
            ),
        }
