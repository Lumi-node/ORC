"""
Task Result Value Object.

Standardized result format for all task/trial executions with conditional
logic support. Used by all DynaBots frameworks.

Example:
    from dynabots_core import TaskResult, TaskOutcome

    # Success with data
    result = TaskResult.success(
        task_id="fetch_data",
        data={"records": [...], "count": 42}
    )

    # No action needed (skip downstream tasks)
    result = TaskResult.no_action_needed(
        task_id="check_updates",
        reason="Already up to date"
    )

    # Failure
    result = TaskResult.failure(
        task_id="send_email",
        error="SMTP connection failed"
    )
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from enum import Enum
from datetime import datetime, timezone


class TaskOutcome(Enum):
    """Task execution outcome."""

    SUCCESS = "success"
    FAILURE = "failure"
    NO_ACTION_NEEDED = "no_action_needed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class TaskResult:
    """
    Standardized task result with conditional execution support.

    This is the core value object that enables smart workflow execution.
    Every task returns a TaskResult, which tells downstream tasks whether
    they should execute or skip.

    Attributes:
        task_id: Unique identifier for the task
        outcome: Execution outcome (success, failure, etc.)
        data: Result data (any type)
        metadata: Additional metadata
        should_continue: Whether downstream tasks should execute
        skip_reason: Reason for skipping (if applicable)
        timestamp: When the result was created
        duration_ms: Execution duration in milliseconds
        error_message: Error message (if failure)

    Example:
        # Task that finds missing items
        missing = analyze_gaps(notes, emails)

        if not missing:
            return TaskResult(
                task_id="analyze",
                outcome=TaskOutcome.NO_ACTION_NEEDED,
                data=None,
                should_continue=False,
                skip_reason="No missing items found"
            )
        else:
            return TaskResult.success(
                task_id="analyze",
                data={"missing_items": missing}
            )
    """

    task_id: str
    outcome: TaskOutcome
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Conditional execution control
    should_continue: bool = True
    skip_reason: Optional[str] = None

    # Audit fields
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None

    @property
    def is_actionable(self) -> bool:
        """
        Does this result require downstream action?

        Returns False if:
        - No action needed
        - Task failed
        - Task was skipped
        """
        return self.outcome not in [
            TaskOutcome.NO_ACTION_NEEDED,
            TaskOutcome.FAILURE,
            TaskOutcome.SKIPPED,
        ]

    @property
    def is_success(self) -> bool:
        """Did the task succeed?"""
        return self.outcome == TaskOutcome.SUCCESS

    @property
    def is_failure(self) -> bool:
        """Did the task fail?"""
        return self.outcome == TaskOutcome.FAILURE

    @property
    def is_skipped(self) -> bool:
        """Was the task skipped?"""
        return self.outcome == TaskOutcome.SKIPPED

    @property
    def is_no_action_needed(self) -> bool:
        """Did the task determine no action was needed?"""
        return self.outcome == TaskOutcome.NO_ACTION_NEEDED

    def get_context_for_downstream(self) -> Dict[str, Any]:
        """
        Extract context needed by downstream tasks.

        Returns:
            Dictionary with task result data formatted for downstream consumption.
        """
        return {
            "task_id": self.task_id,
            "outcome": self.outcome.value,
            "data": self.data,
            "is_actionable": self.is_actionable,
            "should_continue": self.should_continue,
            **self.metadata,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "task_id": self.task_id,
            "outcome": self.outcome.value,
            "data": self.data,
            "metadata": self.metadata,
            "should_continue": self.should_continue,
            "skip_reason": self.skip_reason,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "is_actionable": self.is_actionable,
            "is_success": self.is_success,
        }

    @classmethod
    def success(
        cls,
        task_id: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
    ) -> "TaskResult":
        """Create a successful result."""
        return cls(
            task_id=task_id,
            outcome=TaskOutcome.SUCCESS,
            data=data,
            metadata=metadata or {},
            should_continue=True,
            duration_ms=duration_ms,
        )

    @classmethod
    def no_action_needed(
        cls,
        task_id: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
    ) -> "TaskResult":
        """Create a 'no action needed' result that skips downstream tasks."""
        return cls(
            task_id=task_id,
            outcome=TaskOutcome.NO_ACTION_NEEDED,
            data=None,
            metadata=metadata or {},
            should_continue=False,
            skip_reason=reason,
            duration_ms=duration_ms,
        )

    @classmethod
    def failure(
        cls,
        task_id: str,
        error: str,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
    ) -> "TaskResult":
        """Create a failure result."""
        return cls(
            task_id=task_id,
            outcome=TaskOutcome.FAILURE,
            data=None,
            metadata=metadata or {},
            should_continue=False,
            error_message=error,
            duration_ms=duration_ms,
        )

    @classmethod
    def skipped(
        cls,
        task_id: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "TaskResult":
        """Create a skipped result."""
        return cls(
            task_id=task_id,
            outcome=TaskOutcome.SKIPPED,
            data=None,
            metadata=metadata or {},
            should_continue=False,
            skip_reason=reason,
            duration_ms=0,
        )

    @classmethod
    def partial(
        cls,
        task_id: str,
        data: Any,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
    ) -> "TaskResult":
        """Create a partial success result."""
        return cls(
            task_id=task_id,
            outcome=TaskOutcome.PARTIAL,
            data=data,
            metadata=metadata or {},
            should_continue=True,
            skip_reason=reason,
            duration_ms=duration_ms,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskResult":
        """Create a TaskResult from a dictionary."""
        return cls(
            task_id=data["task_id"],
            outcome=TaskOutcome(data["outcome"]),
            data=data.get("data"),
            metadata=data.get("metadata", {}),
            should_continue=data.get("should_continue", True),
            skip_reason=data.get("skip_reason"),
            duration_ms=data.get("duration_ms"),
            error_message=data.get("error_message"),
        )
