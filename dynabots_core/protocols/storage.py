"""
Storage protocols.

Defines contracts for persistence backends. DynaBots frameworks use
multiple storage concerns, each independently pluggable:

- ExecutionStore: Workflow/trial execution history
- AuditStore: Immutable audit logs
- CacheStore: Pattern cache for O(1) routing

All storage protocols are optional. Frameworks work without any storage,
just without persistence, audit trails, or caching optimizations.

Example:
    from dynabots_core import ExecutionStore

    class PostgresExecutionStore:
        def __init__(self, pool):
            self.pool = pool

        async def save_workflow(self, workflow_data: dict) -> bool:
            await self.pool.execute(
                "INSERT INTO workflows (id, data) VALUES ($1, $2)",
                workflow_data["id"],
                json.dumps(workflow_data)
            )
            return True
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class ExecutionStore(Protocol):
    """
    Protocol for workflow/trial execution history storage.

    Stores completed executions for analytics, debugging, and compliance.
    Used by DynaBots for workflows and Orc!! for trials.

    Example implementation:
        class SQLiteExecutionStore:
            async def save_workflow(self, workflow_data):
                self.db.execute(
                    "INSERT INTO workflows VALUES (?, ?)",
                    (workflow_data["id"], json.dumps(workflow_data))
                )
                return True

            async def get_workflow(self, workflow_id):
                row = self.db.execute(
                    "SELECT data FROM workflows WHERE id = ?",
                    (workflow_id,)
                ).fetchone()
                return json.loads(row[0]) if row else None
    """

    async def save_workflow(self, workflow_data: Dict[str, Any]) -> bool:
        """Save a completed workflow/trial execution."""
        ...

    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a workflow/trial by ID."""
        ...

    async def list_workflows(
        self, limit: int = 50, **filters: Any
    ) -> List[Dict[str, Any]]:
        """
        List workflow executions with optional filters.

        Args:
            limit: Maximum number of results.
            **filters: Optional filters (e.g., user_id, status, date_range).

        Returns:
            List of workflow data dictionaries.
        """
        ...


@runtime_checkable
class AuditStore(Protocol):
    """
    Protocol for immutable audit log storage.

    Provides tamper-evident logging for compliance and forensics.
    Audit logs should be append-only and ideally stored in immutable
    storage (Azure Blob, S3, etc.).

    Example implementation:
        class BlobAuditStore:
            async def log_workflow(self, workflow_id, data):
                blob_name = f"workflows/{workflow_id}/execution.json"
                await self.container.upload_blob(blob_name, json.dumps(data))
                return True

            async def log_task(self, workflow_id, task_id, data):
                blob_name = f"workflows/{workflow_id}/tasks/{task_id}.json"
                await self.container.upload_blob(blob_name, json.dumps(data))
                return True
    """

    async def log_workflow(
        self, workflow_id: str, data: Dict[str, Any]
    ) -> bool:
        """Log a workflow execution event."""
        ...

    async def log_task(
        self, workflow_id: str, task_id: str, data: Dict[str, Any]
    ) -> bool:
        """Log an individual task execution event."""
        ...

    async def log_error(
        self, workflow_id: str, error_type: str, message: str
    ) -> bool:
        """Log an error event."""
        ...


@runtime_checkable
class CacheStore(Protocol):
    """
    Protocol for cache persistence.

    Used for pattern caching (O(1) intent routing), reputation scores,
    and other ephemeral data that benefits from persistence.

    Example implementation:
        class RedisCache:
            async def get(self, key):
                data = await self.redis.get(key)
                return json.loads(data) if data else None

            async def set(self, key, value):
                await self.redis.set(key, json.dumps(value))
                return True

            async def delete(self, key):
                await self.redis.delete(key)
                return True
    """

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a cached value by key."""
        ...

    async def set(self, key: str, value: Dict[str, Any]) -> bool:
        """Set a cached value."""
        ...

    async def delete(self, key: str) -> bool:
        """Delete a cached value."""
        ...


@runtime_checkable
class ReputationStore(Protocol):
    """
    Protocol for storing agent reputation scores (used by Orc!!).

    Tracks agent performance over time for leadership decisions.

    Example implementation:
        class PostgresReputationStore:
            async def get_reputation(self, agent_name, domain):
                row = await self.pool.fetchone(
                    "SELECT score FROM reputation WHERE agent=$1 AND domain=$2",
                    agent_name, domain
                )
                return row["score"] if row else 0.5

            async def update_reputation(self, agent_name, domain, delta):
                await self.pool.execute('''
                    INSERT INTO reputation (agent, domain, score)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (agent, domain)
                    DO UPDATE SET score = reputation.score + $3
                ''', agent_name, domain, delta)
                return True
    """

    async def get_reputation(self, agent_name: str, domain: str) -> float:
        """Get agent's reputation score for a domain (0.0 to 1.0)."""
        ...

    async def update_reputation(
        self, agent_name: str, domain: str, delta: float
    ) -> bool:
        """Update agent's reputation by delta (can be negative)."""
        ...

    async def get_leaderboard(
        self, domain: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top agents for a domain."""
        ...
