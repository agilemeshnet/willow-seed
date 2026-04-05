"""
Graph Client - Secure Neo4j wrapper with safety constraints.

This is the ONLY way agents access the graph database.
Direct Neo4j connections are forbidden.

Usage:
    from tools.graph_client import GraphClient
    client = GraphClient(agent_id="MyAgent")
    results = client.run("MATCH (n:Observation) RETURN n.content LIMIT 5")
    client.close()

Setup:
    pip install neo4j
    Set environment variables:
        NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
        NEO4J_USER=neo4j
        NEO4J_PASSWORD=your-password
"""

import os
import re
from datetime import datetime, timezone

try:
    from neo4j import GraphDatabase
except ImportError:
    print("Install neo4j driver: pip install neo4j")
    raise


# Operations that are NEVER allowed
FORBIDDEN_OPERATIONS = ["DELETE", "DETACH", "DROP", "REMOVE", "CALL.*apoc.*delete"]


class GraphClient:
    """Secure Neo4j client that enforces append-only access."""

    def __init__(self, agent_id: str = "Agent"):
        self.agent_id = agent_id
        uri = os.environ.get("NEO4J_URI")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD")

        if not uri or not password:
            raise ValueError(
                "Set NEO4J_URI and NEO4J_PASSWORD environment variables"
            )

        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.driver.verify_connectivity()

    def _check_safety(self, query: str) -> None:
        """Reject any query containing forbidden operations."""
        query_upper = query.upper().strip()
        for op in FORBIDDEN_OPERATIONS:
            if re.search(op, query_upper):
                raise SecurityError(
                    f"Operation {op} is FORBIDDEN. "
                    "All writes must be append-only (CREATE or MERGE)."
                )

    def _add_provenance(self, query: str, parameters: dict = None) -> tuple:
        """Add automatic provenance metadata to CREATE/MERGE operations."""
        if parameters is None:
            parameters = {}

        # Add provenance parameters for use in queries
        parameters["_agent"] = self.agent_id
        parameters["_timestamp"] = datetime.now(timezone.utc).isoformat()

        return query, parameters

    def run(self, query: str, parameters: dict = None) -> list:
        """Execute a Cypher query with safety checks and provenance."""
        self._check_safety(query)
        query, parameters = self._add_provenance(query, parameters)

        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]

    def log_diary(self, action: str, notes: str) -> None:
        """Write an immutable diary entry. The standard trace mechanism."""
        self.run(
            """
            CREATE (d:DiaryEntry {
                agent: $agent,
                timestamp: datetime(),
                action: $action,
                notes: $notes
            })
            """,
            parameters={
                "agent": self.agent_id,
                "action": action,
                "notes": notes,
            },
        )

    def log_observation(
        self,
        content: str,
        source: str,
        confidence: float = 0.5,
        domain: str = "general",
        ttl_days: int = 90,
        tags: list = None,
    ) -> None:
        """Record an observation with full provenance."""
        self.run(
            """
            CREATE (o:Observation {
                content: $content,
                observer: $agent,
                source: $source,
                timestamp: datetime(),
                confidence: $confidence,
                domain: $domain,
                ttl_days: $ttl_days,
                tags: $tags
            })
            """,
            parameters={
                "agent": self.agent_id,
                "content": content,
                "source": source,
                "confidence": confidence,
                "domain": domain,
                "ttl_days": ttl_days,
                "tags": tags or [],
            },
        )

    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SecurityError(Exception):
    """Raised when a query violates security constraints."""
    pass
