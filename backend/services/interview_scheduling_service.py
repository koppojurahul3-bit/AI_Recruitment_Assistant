
"""Interview scheduling, status tracking, and communication drafts."""

import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


class InterviewSchedulingService:
    """Manage interview records and draft candidate communications."""

    STATUSES = {
        "proposed",
        "confirmed",
        "rescheduled",
        "cancelled",
        "completed",
    }
    ACTIVE_STATUSES = {"proposed", "confirmed", "rescheduled"}
    COMMUNICATION_TYPES = {
        "invitation",
        "confirmation",
        "rescheduling",
        "cancellation",
    }

    def __init__(self, database_path: str | Path = "data/interviews.sqlite3"):
        self.database_path = str(database_path)

        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(
                parents=True, exist_ok=True
            )

        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS interviews (
                    interview_id TEXT PRIMARY KEY,
                    candidate_id TEXT NOT NULL,
                    candidate_name TEXT NOT NULL,
                    candidate_email TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    interviewer TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    timezone TEXT NOT NULL,
                    interview_round TEXT NOT NULL,
                    meeting_link TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1
                );

                CREATE INDEX IF NOT EXISTS idx_interview_candidate
                    ON interviews(candidate_id);

                CREATE INDEX IF NOT EXISTS idx_interview_start
                    ON interviews(start_time);

                CREATE TABLE IF NOT EXISTS interview_audit (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interview_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(interview_id)
                        REFERENCES interviews(interview_id)
                );

                CREATE TABLE IF NOT EXISTS interview_communications (
                    communication_id TEXT PRIMARY KEY,
                    interview_id TEXT NOT NULL,
                    communication_type TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(interview_id)
                        REFERENCES interviews(interview_id)
                );
                """
            )

    @staticmethod
    def _required_text(value: Any, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string.")
        return value.strip()

    @staticmethod
    def _parse_start(value: str) -> datetime:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("start_time must be an ISO 8601 datetime.")

        try:
            parsed = datetime.fromisoformat(value.strip())
        except ValueError as exc:
            raise ValueError(
                "start_time must be a valid ISO 8601 datetime."
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError(
                "start_time must include a timezone offset, "
                "for example 2027-01-15T10:00:00+05:30."
            )

        return parsed

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat()

    @staticmethod
    def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        return dict(row) if row is not None else None

    def _get_connection_interview(
        self, connection: sqlite3.Connection, interview_id: str
    ) -> Optional[sqlite3.Row]:
        return connection.execute(
            "SELECT * FROM interviews WHERE interview_id = ?",
            (interview_id,),
        ).fetchone()

    def _audit(
        self,
        connection: sqlite3.Connection,
        interview_id: str,
        event_type: str,
        actor: str,
        details: Dict[str, Any],
    ) -> None:
        connection.execute(
            """
            INSERT INTO interview_audit
            (interview_id, event_type, actor, details_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                interview_id,
                event_type,
                actor,
                json.dumps(details, sort_keys=True),
                self._now(),
            ),
        )

    def _check_conflict(
        self,
        connection: sqlite3.Connection,
        start: datetime,
        duration: int,
        interviewer: str,
        candidate_id: str,
        exclude_id: Optional[str] = None,
    ) -> None:
        end = start + timedelta(minutes=duration)

        rows = connection.execute(
            """
            SELECT interview_id, candidate_id, interviewer, start_time,
                   duration_minutes, status, timezone
            FROM interviews
            WHERE status IN ('proposed', 'confirmed', 'rescheduled')
            """
        ).fetchall()

        for row in rows:
            if row["interview_id"] == exclude_id:
                continue

            existing_start = datetime.fromisoformat(row["start_time"])
            existing_end = existing_start + timedelta(
                minutes=row["duration_minutes"]
            )

            # Datetimes with offsets compare by absolute instant.
            overlaps = start < existing_end and existing_start < end
            if not overlaps:
                continue

            if row["interviewer"].casefold() == interviewer.casefold():
                raise ValueError(
                    f"Interviewer has a scheduling conflict with "
                    f"interview {row['interview_id']}."
                )

            if row["candidate_id"] == candidate_id:
                raise ValueError(
                    f"Candidate already has an overlapping interview "
                    f"{row['interview_id']}."
                )

    def schedule_interview(
        self,
        *,
        candidate_id: str,
        candidate_name: str,
        candidate_email: str,
        job_title: str,
        interviewer: str,
        start_time: str,
        duration_minutes: int = 60,
        timezone: str = "Asia/Kolkata",
        interview_round: str = "Technical",
        meeting_link: str = "",
        notes: str = "",
        actor: str = "Recruiter",
        status: str = "proposed",
    ) -> Dict[str, Any]:
        """Create an interview record; does not send messages or book a calendar."""
        fields = {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "candidate_email": candidate_email,
            "job_title": job_title,
            "interviewer": interviewer,
            "timezone": timezone,
            "interview_round": interview_round,
            "actor": actor,
        }
        clean = {
            key: self._required_text(value, key)
            for key, value in fields.items()
        }

        start = self._parse_start(start_time)

        if isinstance(duration_minutes, bool) or not isinstance(
            duration_minutes, int
        ):
            raise TypeError("duration_minutes must be an integer.")
        if not 15 <= duration_minutes <= 480:
            raise ValueError(
                "duration_minutes must be between 15 and 480."
            )

        if status not in {"proposed", "confirmed"}:
            raise ValueError(
                "New interviews must have status 'proposed' or 'confirmed'."
            )

        if not isinstance(meeting_link, str) or not isinstance(notes, str):
            raise TypeError("meeting_link and notes must be strings.")

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", clean["candidate_email"]):
            raise ValueError("candidate_email must be a valid email address.")

        interview_id = str(uuid4())
        now = self._now()
        normalized_start = start.isoformat()

        with self._connect() as connection:
            self._check_conflict(
                connection,
                start,
                duration_minutes,
                clean["interviewer"],
                clean["candidate_id"],
            )

            connection.execute(
                """
                INSERT INTO interviews (
                    interview_id, candidate_id, candidate_name,
                    candidate_email, job_title, interviewer, start_time,
                    duration_minutes, timezone, interview_round,
                    meeting_link, notes, status, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    interview_id,
                    clean["candidate_id"],
                    clean["candidate_name"],
                    clean["candidate_email"],
                    clean["job_title"],
                    clean["interviewer"],
                    normalized_start,
                    duration_minutes,
                    clean["timezone"],
                    clean["interview_round"],
                    meeting_link.strip(),
                    notes.strip(),
                    status,
                    now,
                    now,
                ),
            )

            self._audit(
                connection,
                interview_id,
                "scheduled",
                clean["actor"],
                {
                    "start_time": normalized_start,
                    "duration_minutes": duration_minutes,
                    "status": status,
                },
            )

            return self._row_to_dict(
                self._get_connection_interview(connection, interview_id)
            )

    def get_interview(self, interview_id: str) -> Optional[Dict[str, Any]]:
        interview_id = self._required_text(interview_id, "interview_id")
        with self._connect() as connection:
            return self._row_to_dict(
                self._get_connection_interview(connection, interview_id)
            )

    def list_interviews(
        self,
        candidate_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM interviews WHERE 1=1"
        params: List[Any] = []

        if candidate_id is not None:
            query += " AND candidate_id = ?"
            params.append(self._required_text(candidate_id, "candidate_id"))

        if status is not None:
            if status not in self.STATUSES:
                raise ValueError("Unsupported interview status.")
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY start_time"

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def _transition(
        self,
        interview_id: str,
        new_status: str,
        actor: str,
        event_type: str,
    ) -> Dict[str, Any]:
        interview_id = self._required_text(interview_id, "interview_id")
        actor = self._required_text(actor, "actor")

        with self._connect() as connection:
            row = self._get_connection_interview(connection, interview_id)
            if row is None:
                raise ValueError("Interview was not found.")

            current = row["status"]
            allowed = {
                "proposed": {"confirmed", "cancelled"},
                "confirmed": {"cancelled", "completed"},
                "rescheduled": {"confirmed", "cancelled"},
                "cancelled": set(),
                "completed": set(),
            }

            if new_status not in allowed.get(current, set()):
                raise ValueError(
                    f"Cannot transition interview from {current} "
                    f"to {new_status}."
                )

            now = self._now()
            connection.execute(
                """
                UPDATE interviews
                SET status = ?, updated_at = ?, version = version + 1
                WHERE interview_id = ?
                """,
                (new_status, now, interview_id),
            )

            self._audit(
                connection,
                interview_id,
                event_type,
                actor,
                {"previous_status": current, "new_status": new_status},
            )

            return self._row_to_dict(
                self._get_connection_interview(connection, interview_id)
            )

    def confirm_interview(
        self, interview_id: str, actor: str = "Recruiter"
    ) -> Dict[str, Any]:
        return self._transition(
            interview_id, "confirmed", actor, "confirmed"
        )

    def cancel_interview(
        self, interview_id: str, actor: str = "Recruiter"
    ) -> Dict[str, Any]:
        return self._transition(
            interview_id, "cancelled", actor, "cancelled"
        )

    def complete_interview(
        self, interview_id: str, actor: str = "Recruiter"
    ) -> Dict[str, Any]:
        return self._transition(
            interview_id, "completed", actor, "completed"
        )

    def reschedule_interview(
        self,
        interview_id: str,
        *,
        new_start_time: str,
        new_duration_minutes: Optional[int] = None,
        actor: str = "Recruiter",
    ) -> Dict[str, Any]:
        """Move an active interview after validating conflicts."""
        interview_id = self._required_text(interview_id, "interview_id")
        actor = self._required_text(actor, "actor")
        start = self._parse_start(new_start_time)

        with self._connect() as connection:
            row = self._get_connection_interview(connection, interview_id)
            if row is None:
                raise ValueError("Interview was not found.")

            if row["status"] not in self.ACTIVE_STATUSES:
                raise ValueError("Only active interviews can be rescheduled.")

            duration = (
                row["duration_minutes"]
                if new_duration_minutes is None
                else new_duration_minutes
            )
            if isinstance(duration, bool) or not isinstance(duration, int):
                raise TypeError("new_duration_minutes must be an integer.")
            if not 15 <= duration <= 480:
                raise ValueError(
                    "new_duration_minutes must be between 15 and 480."
                )

            self._check_conflict(
                connection,
                start,
                duration,
                row["interviewer"],
                row["candidate_id"],
                exclude_id=interview_id,
            )

            previous = {
                "start_time": row["start_time"],
                "duration_minutes": row["duration_minutes"],
                "status": row["status"],
            }
            now = self._now()

            connection.execute(
                """
                UPDATE interviews
                SET start_time = ?, duration_minutes = ?, status = 'rescheduled',
                    updated_at = ?, version = version + 1
                WHERE interview_id = ?
                """,
                (start.isoformat(), duration, now, interview_id),
            )

            self._audit(
                connection,
                interview_id,
                "rescheduled",
                actor,
                {
                    "previous": previous,
                    "new_start_time": start.isoformat(),
                    "new_duration_minutes": duration,
                },
            )

            return self._row_to_dict(
                self._get_connection_interview(connection, interview_id)
            )

    def get_audit_history(self, interview_id: str) -> List[Dict[str, Any]]:
        interview_id = self._required_text(interview_id, "interview_id")

        with self._connect() as connection:
            if self._get_connection_interview(connection, interview_id) is None:
                raise ValueError("Interview was not found.")

            rows = connection.execute(
                """
                SELECT * FROM interview_audit
                WHERE interview_id = ?
                ORDER BY audit_id
                """,
                (interview_id,),
            ).fetchall()

            result = []
            for row in rows:
                item = dict(row)
                item["details"] = json.loads(item.pop("details_json"))
                result.append(item)
            return result

    def draft_communication(
        self,
        interview_id: str,
        communication_type: str,
        *,
        sender_name: str = "Recruitment Team",
    ) -> Dict[str, Any]:
        """Store a draft only; this method never sends an email."""
        if communication_type not in self.COMMUNICATION_TYPES:
            raise ValueError("Unsupported communication type.")

        sender_name = self._required_text(sender_name, "sender_name")
        interview = self.get_interview(interview_id)
        if interview is None:
            raise ValueError("Interview was not found.")

        start = datetime.fromisoformat(interview["start_time"])
        readable_time = start.strftime("%A, %d %B %Y at %I:%M %p %Z")
        candidate = interview["candidate_name"]
        role = interview["job_title"]
        interviewer = interview["interviewer"]
        duration = interview["duration_minutes"]
        meeting_link = interview["meeting_link"]

        subjects = {
            "invitation": f"Interview invitation — {role}",
            "confirmation": f"Interview confirmed — {role}",
            "rescheduling": f"Interview schedule update — {role}",
            "cancellation": f"Interview cancellation — {role}",
        }

        if communication_type == "invitation":
            opening = (
                f"We would like to invite you to an interview for {role}."
            )
        elif communication_type == "confirmation":
            opening = f"This message confirms your interview for {role}."
        elif communication_type == "rescheduling":
            opening = f"Your interview for {role} has a schedule update."
        else:
            opening = f"We are writing about the cancellation of your interview for {role}."

        lines = [
            f"Hello {candidate},",
            "",
            opening,
            "",
            f"Date and time: {readable_time}",
            f"Duration: {duration} minutes",
            f"Interviewer: {interviewer}",
            f"Time zone: {interview['timezone']}",
        ]
        if meeting_link:
            lines.append(f"Meeting link: {meeting_link}")
        lines.extend(["", "Please reply to the recruitment team if you have questions.", "", f"Regards,\n{sender_name}"])
        body = "\n".join(lines)

        communication_id = str(uuid4())
        created_at = self._now()

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO interview_communications (
                    communication_id, interview_id, communication_type,
                    recipient, subject, body, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'draft', ?)
                """,
                (
                    communication_id,
                    interview_id,
                    communication_type,
                    interview["candidate_email"],
                    subjects[communication_type],
                    body,
                    created_at,
                ),
            )

            self._audit(
                connection,
                interview_id,
                "communication_drafted",
                sender_name,
                {
                    "communication_id": communication_id,
                    "communication_type": communication_type,
                    "status": "draft",
                },
            )

        return {
            "communication_id": communication_id,
            "interview_id": interview_id,
            "communication_type": communication_type,
            "recipient": interview["candidate_email"],
            "subject": subjects[communication_type],
            "body": body,
            "status": "draft",
            "external_operation_performed": False,
            "created_at": created_at,
        }

    def list_communications(
        self, interview_id: str
    ) -> List[Dict[str, Any]]:
        interview_id = self._required_text(interview_id, "interview_id")

        with self._connect() as connection:
            if self._get_connection_interview(connection, interview_id) is None:
                raise ValueError("Interview was not found.")

            rows = connection.execute(
                """
                SELECT * FROM interview_communications
                WHERE interview_id = ?
                ORDER BY created_at
                """,
                (interview_id,),
            ).fetchall()
            return [dict(row) for row in rows]
