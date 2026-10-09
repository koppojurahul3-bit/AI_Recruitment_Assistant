
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass(frozen=True)
class AuditEvent:
    """Structured record of a recruitment-system event."""

    event_id: str
    timestamp: str
    event_type: str
    actor: str
    description: str
    candidate_id: Optional[str] = None
    action_id: Optional[str] = None
    outcome: str = "info"
    details: Dict[str, Any] = field(default_factory=dict)


class AuditService:
    """
    Records and queries recruitment audit events in memory.

    This service does not persist events across application restarts.
    Avoid placing resume text, passwords, tokens, or other sensitive
    information in event descriptions or details.
    """

    ALLOWED_OUTCOMES = {
        "info",
        "success",
        "failure",
        "blocked",
    }

    def __init__(self):
        self._events: List[AuditEvent] = []

    def log_event(
        self,
        event_type: str,
        actor: str,
        description: str,
        candidate_id: Optional[str] = None,
        action_id: Optional[str] = None,
        outcome: str = "info",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Validate and append one audit event."""

        for field_name, value in (
            ("event_type", event_type),
            ("actor", actor),
            ("description", description),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{field_name} must be a non-empty string."
                )

        for field_name, value in (
            ("candidate_id", candidate_id),
            ("action_id", action_id),
        ):
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(
                    f"{field_name} must be None or a non-empty string."
                )

        if outcome not in self.ALLOWED_OUTCOMES:
            raise ValueError(f"Unsupported audit outcome: {outcome}")

        if details is not None and not isinstance(details, dict):
            raise TypeError("Audit details must be a dictionary.")

        event = AuditEvent(
            event_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type.strip(),
            actor=actor.strip(),
            description=description.strip(),
            candidate_id=candidate_id.strip() if candidate_id else None,
            action_id=action_id.strip() if action_id else None,
            outcome=outcome,
            details=dict(details) if details is not None else {},
        )

        self._events.append(event)
        return event

    def get_events(
        self,
        event_type: Optional[str] = None,
        candidate_id: Optional[str] = None,
        action_id: Optional[str] = None,
        outcome: Optional[str] = None,
    ) -> List[AuditEvent]:
        """Return events matching every supplied filter."""

        filters = (
            ("event_type", event_type),
            ("candidate_id", candidate_id),
            ("action_id", action_id),
            ("outcome", outcome),
        )

        for field_name, value in filters:
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(
                    f"{field_name} filter must be None or non-empty."
                )

        return [
            event
            for event in self._events
            if (event_type is None or event.event_type == event_type)
            and (
                candidate_id is None
                or event.candidate_id == candidate_id
            )
            and (action_id is None or event.action_id == action_id)
            and (outcome is None or event.outcome == outcome)
        ]

    def get_event_by_id(
        self,
        event_id: str,
    ) -> Optional[AuditEvent]:
        """Find a single event by its unique ID."""

        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("A valid event ID is required.")

        return next(
            (
                event
                for event in self._events
                if event.event_id == event_id
            ),
            None,
        )

    def count(self) -> int:
        """Return the total number of recorded events."""

        return len(self._events)

    def clear(self) -> None:
        """Clear in-memory events; intended for tests and resets."""

        self._events.clear()
