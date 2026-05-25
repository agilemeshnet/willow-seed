#!/usr/bin/env python3
"""
Brain Backup - Export graph to JSONL files for disaster recovery.

Exports all nodes and relationships from Neo4j to timestamped JSONL files.
Each line is a self-contained JSON record with full provenance.

The export is not byte-identical to the original - property ordering may
differ, internal IDs change - but it is structurally equivalent. Same
cogitations, same connections, same memories. Different wording order.

Like regrowing a limb: same shape, slightly different cells.

Usage:
    python tools/brain_backup.py                          # Full backup
    python tools/brain_backup.py --labels DiaryEntry      # Specific labels
    python tools/brain_backup.py --since 2026-05-01       # Recent only
    python tools/brain_backup.py --output /path/to/dir    # Custom location
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from neo4j import GraphDatabase
except ImportError:
    print("Install neo4j driver: pip install neo4j")
    sys.exit(1)


def get_driver():
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD")
    if not uri or not password:
        print("ERROR: Set NEO4J_URI and NEO4J_PASSWORD environment variables", file=sys.stderr)
        sys.exit(1)
    return GraphDatabase.driver(uri, auth=(user, password))


def neo4j_to_json(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "year"):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [neo4j_to_json(v) for v in value]
    if isinstance(value, dict):
        return {k: neo4j_to_json(v) for k, v in value.items()}
    return value


def export_nodes(driver, output_dir, labels=None, since=None):
    nodes_file = output_dir / "nodes.jsonl"
    count = 0

    where_clauses = []
    params = {}

    if labels:
        label_filter = ":".join(labels)
        query_prefix = f"MATCH (n:{label_filter})"
    else:
        query_prefix = "MATCH (n)"

    if since:
        where_clauses.append("(n.timestamp IS NULL OR n.timestamp >= datetime($since))")
        params["since"] = since

    where = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    query = f"{query_prefix}{where} RETURN n, labels(n) as labels, elementId(n) as eid"

    with driver.session() as session:
        with open(nodes_file, "w") as f:
            result = session.run(query, params)
            for record in result:
                node = record["n"]
                props = neo4j_to_json(dict(node))
                entry = {
                    "_type": "node",
                    "_eid": record["eid"],
                    "_labels": record["labels"],
                    "_exported": datetime.now(timezone.utc).isoformat(),
                    "properties": props
                }
                f.write(json.dumps(entry, default=str) + "\n")
                count += 1

    return count


def export_relationships(driver, output_dir, since=None):
    rels_file = output_dir / "relationships.jsonl"
    count = 0

    where = ""
    params = {}
    if since:
        where = " WHERE r.created >= datetime($since) OR r.timestamp >= datetime($since)"
        params["since"] = since

    query = f"""
        MATCH (a)-[r]->(b){where}
        RETURN type(r) as rel_type, properties(r) as rel_props,
               elementId(a) as from_eid, labels(a) as from_labels, properties(a) as from_props,
               elementId(b) as to_eid, labels(b) as to_labels, properties(b) as to_props,
               elementId(r) as rel_eid
    """

    with driver.session() as session:
        with open(rels_file, "w") as f:
            result = session.run(query, params)
            for record in result:
                entry = {
                    "_type": "relationship",
                    "_rel_eid": record["rel_eid"],
                    "_rel_type": record["rel_type"],
                    "_exported": datetime.now(timezone.utc).isoformat(),
                    "from": {
                        "eid": record["from_eid"],
                        "labels": record["from_labels"],
                        "match_props": _match_key(record["from_labels"], neo4j_to_json(dict(record["from_props"])))
                    },
                    "to": {
                        "eid": record["to_eid"],
                        "labels": record["to_labels"],
                        "match_props": _match_key(record["to_labels"], neo4j_to_json(dict(record["to_props"])))
                    },
                    "properties": neo4j_to_json(dict(record["rel_props"]))
                }
                f.write(json.dumps(entry, default=str) + "\n")
                count += 1

    return count


def _match_key(labels, props):
    """Extract the best properties for re-matching this node on restore.
    Prefer id, name, then first 3 non-internal properties."""
    key = {}
    for field in ["id", "name", "title", "dawn", "agent", "timestamp"]:
        if field in props:
            key[field] = props[field]
    if not key:
        for k, v in list(props.items())[:3]:
            if not k.startswith("_"):
                key[k] = v
    return key


def write_manifest(output_dir, node_count, rel_count, labels, since):
    manifest = {
        "backup_type": "brain_backup",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_uri": os.environ.get("NEO4J_URI", "unknown"),
        "node_count": node_count,
        "relationship_count": rel_count,
        "filters": {
            "labels": labels,
            "since": since
        },
        "files": ["nodes.jsonl", "relationships.jsonl"],
        "note": "Structurally equivalent, not byte-identical. Same cogitations, different cell arrangement."
    }
    with open(output_dir / "backup_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Brain Backup - export graph to JSONL")
    parser.add_argument("--labels", nargs="+", help="Export specific labels only")
    parser.add_argument("--since", type=str, help="Export nodes/rels since date (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, help="Output directory")
    args = parser.parse_args()

    if args.output:
        output_dir = Path(args.output)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        output_dir = Path(__file__).parent.parent / "backups" / f"brain_{ts}"

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Brain Backup starting...")
    print(f"  Output: {output_dir}")
    if args.labels:
        print(f"  Labels: {args.labels}")
    if args.since:
        print(f"  Since:  {args.since}")

    driver = get_driver()

    try:
        node_count = export_nodes(driver, output_dir, labels=args.labels, since=args.since)
        print(f"  Nodes exported: {node_count}")

        rel_count = export_relationships(driver, output_dir, since=args.since)
        print(f"  Relationships exported: {rel_count}")

        write_manifest(output_dir, node_count, rel_count, args.labels, args.since)
        print(f"\nBackup complete: {output_dir}")
        print(f"  {node_count} nodes + {rel_count} relationships")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
