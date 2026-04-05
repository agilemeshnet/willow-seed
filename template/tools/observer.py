"""
Observer - End-of-session memory compression.

Reads recent diary entries and compresses them into higher-level
Observation nodes. This is the mechanism by which short-term traces
become long-term knowledge.

Run at the end of each significant session, or as a hook.

Usage:
    python tools/observer.py

The observer:
1. Reads recent DiaryEntry nodes (since last observation)
2. Identifies patterns and themes
3. Creates Observation nodes that summarise the patterns
4. Links observations to the diary entries they came from
"""

import os
import sys
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.graph_client import GraphClient


def get_recent_entries(client: GraphClient, limit: int = 20) -> list:
    """Fetch recent diary entries not yet observed."""
    return client.run(
        """
        MATCH (d:DiaryEntry)
        WHERE NOT (d)<-[:OBSERVED_FROM]-(:Observation)
        RETURN d.agent AS agent, d.action AS action,
               d.notes AS notes, d.timestamp AS timestamp
        ORDER BY d.timestamp DESC
        LIMIT $limit
        """,
        parameters={"limit": limit},
    )


def create_observation(
    client: GraphClient, content: str, source_entries: list
) -> None:
    """Create an observation node linked to its source diary entries."""
    client.run(
        """
        CREATE (o:Observation {
            content: $content,
            observer: $agent,
            source: 'session-observer',
            timestamp: datetime(),
            confidence: 0.8,
            domain: 'session-digest',
            observation_type: 'session-summary'
        })
        WITH o
        UNWIND $timestamps AS ts
        MATCH (d:DiaryEntry {timestamp: ts})
        CREATE (o)-[:OBSERVED_FROM]->(d)
        """,
        parameters={
            "agent": client.agent_id,
            "content": content,
            "timestamps": [e["timestamp"] for e in source_entries],
        },
    )


def main():
    agent_id = os.environ.get("AGENT_ID", "Observer")

    with GraphClient(agent_id=agent_id) as client:
        entries = get_recent_entries(client)

        if not entries:
            print("No unobserved diary entries. Nothing to do.")
            return

        print(f"Found {len(entries)} unobserved diary entries.")

        # Group entries by agent
        by_agent = {}
        for entry in entries:
            agent = entry.get("agent", "unknown")
            if agent not in by_agent:
                by_agent[agent] = []
            by_agent[agent].append(entry)

        # Create one observation per agent's recent work
        for agent, agent_entries in by_agent.items():
            actions = [e["action"] for e in agent_entries if e.get("action")]
            summary = f"Agent {agent} performed {len(agent_entries)} actions: {'; '.join(actions[:5])}"
            if len(actions) > 5:
                summary += f" (and {len(actions) - 5} more)"

            create_observation(client, summary, agent_entries)
            print(f"Created observation for {agent}: {len(agent_entries)} entries")

        print("Done.")


if __name__ == "__main__":
    main()
