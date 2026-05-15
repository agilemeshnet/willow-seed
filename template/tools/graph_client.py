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

    def create_node(self, label: str, properties: dict) -> list:
        """Create a domain node with automatic provenance.

        Example - building an e-commerce ontology:
            client.create_node("Product", {"name": "Wireless Keyboard", "sku": "KB-001", "price": 45.99})
            client.create_node("Customer", {"name": "Sarah", "email": "sarah@example.com"})
            client.create_node("Category", {"name": "Peripherals"})
        """
        props = {**properties, "created_by": self.agent_id}
        prop_string = ", ".join(f"{k}: ${k}" for k in props)
        return self.run(
            f"CREATE (n:{label} {{{prop_string}, created_at: datetime()}}) RETURN n",
            parameters=props,
        )

    def create_relationship(self, from_label: str, from_match: dict,
                            rel_type: str, to_label: str, to_match: dict,
                            properties: dict = None) -> list:
        """Connect two existing nodes with a typed relationship.

        Example - wiring the ontology:
            client.create_relationship("Customer", {"name": "Sarah"},
                                       "PLACED_ORDER", "Order", {"id": "ORD-001"})
            client.create_relationship("Order", {"id": "ORD-001"},
                                       "CONTAINS", "Product", {"sku": "KB-001"})
            client.create_relationship("Product", {"sku": "KB-001"},
                                       "IN_CATEGORY", "Category", {"name": "Peripherals"})
        """
        from_props = " AND ".join(f"a.{k} = $from_{k}" for k in from_match)
        to_props = " AND ".join(f"b.{k} = $to_{k}" for k in to_match)
        params = {f"from_{k}": v for k, v in from_match.items()}
        params.update({f"to_{k}": v for k, v in to_match.items()})

        rel_prop_str = ""
        if properties:
            params.update(properties)
            rel_prop_str = " {" + ", ".join(f"{k}: ${k}" for k in properties) + "}"

        return self.run(
            f"MATCH (a:{from_label}), (b:{to_label}) "
            f"WHERE {from_props} AND {to_props} "
            f"CREATE (a)-[r:{rel_type}{rel_prop_str} {{created_by: $_agent, created_at: datetime()}}]->(b) "
            f"RETURN type(r)",
            parameters=params,
        )

    def explore(self, label: str = None, limit: int = 25) -> list:
        """See what is in the Brain. Useful for health checks and orientation."""
        if label:
            return self.run(f"MATCH (n:{label}) RETURN n LIMIT $limit",
                            parameters={"limit": limit})
        return self.run(
            "CALL db.labels() YIELD label "
            "RETURN label, "
            "[(label) WHERE true | label][0] as sample "
            "ORDER BY label",
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
