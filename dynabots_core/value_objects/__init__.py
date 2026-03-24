"""
Value objects for the DynaBots framework family.

Value objects are immutable data structures that carry meaning
through their values rather than identity.
"""

from dynabots_core.value_objects.task_result import TaskResult, TaskOutcome

__all__ = ["TaskResult", "TaskOutcome"]
