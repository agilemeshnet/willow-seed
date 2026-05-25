#!/usr/bin/env python3
"""
Brain Restore - Reconstruct graph from JSONL backup files.

Reads nodes.jsonl and relationships.jsonl from a brain_backup export
and writes them into a fresh Neo4j instance.

The restored Brain will be structurally equivalent to the original:
same observations, same connections, same memories. But not identical -
property ordering may differ, internal IDs will change, timestamps on
the restore operation are new.

This is regrowth, not cloning. Same planarian, different cells.

Usage:
    python tools/brain_restore.py /path/to/backup/       # Restore from dir
    python tools/brain_restore.py --dry-run /path/to/     # Preview only
    python tools/brain_restore.py --batch-size 500 /path/ # Tune batch size
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


def sanitise_props(props):
    """Remove internal/meta keys and ensure all values are Neo4j-compatible."""
    clean = {}
    for k, v in props.items():
        if k.startswith("_"):
            continue
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        elif isinstance(v, list):
            clean[k] = [str(i) if not isinstance(i, (str, int, float, bool)) else i for i in v]
        else:
            clean[k] = str(v)
    return clean


def restore_nodes(driver, backup_dir, batch_size=200, dry_run=False):
    nodes_file = backup_dir / "nodes.jsonl"
    if not nodes_file.exists():
        print(f"  WARNING: {nodes_file} not found, skipping nodes", file=sys.stderr)
        return 0

    eid_map = {}
    count = 0
    batch = []

    with open(nodes_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            batch.append(entry)

            if len(batch) >= batch_size:
                count += _flush_node_batch(driver, batch, eid_map, dry_run)
                batch = []

    if batch:
        count += _flush_node_batch(driver, batch, eid_map, dry_run)

    return count


def _flush_node_batch(driver, batch, eid_map, dry_run):
    if dry_run:
        for entry in batch:
            labels = ":".join(entry["_labels"])
            print(f"    [DRY RUN] CREATE (:{labels}) with {len(entry['properties'])} props")
        return len(batch)

    count = 0
    with driver.session() as session:
        for entry in batch:
            labels = ":".join(entry["_labels"])
            props = sanitise_props(entry["properties"])
            props["_restored"] = datetime.now(timezone.utc).isoformat()
            props["_original_eid"] = entry["_eid"]

            # Build parameterised CREATE
            prop_str = ", ".join(f"{k}: ${k}" for k in props)
            query = f"CREATE (n:{labels} {{{prop_str}}}) RETURN elementId(n) as new_eid"

            try:
                result = session.run(query, props)
                record = result.single()
                if record:
                    eid_map[entry["_eid"]] = record["new_eid"]
                count += 1
            except Exception as e:
                print(f"    ERROR restoring node {entry['_eid']}: {e}", file=sys.stderr)

    return count


def restore_relationships(driver, backup_dir, batch_size=100, dry_run=False):
    rels_file = backup_dir / "relationships.jsonl"
    if not rels_file.exists():
        print(f"  WARNING: {rels_file} not found, skipping relationships", file=sys.stderr)
        return 0

    count = 0
    skipped = 0
    batch = []

    with open(rels_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            batch.append(entry)

            if len(batch) >= batch_size:
                c, s = _flush_rel_batch(driver, batch, dry_run)
                count += c
                skipped += s
                batch = []

    if batch:
        c, s = _flush_rel_batch(driver, batch, dry_run)
        count += c
        skipped += s

    if skipped > 0:
        print(f"  Skipped {skipped} relationships (could not match endpoints)")

    return count


def _flush_rel_batch(driver, batch, dry_run):
    if dry_run:
        for entry in batch:
            print(f"    [DRY RUN] ({entry['from']['labels']})-[:{entry['_rel_type']}]->({entry['to']['labels']})")
        return len(batch), 0

    count = 0
    skipped = 0

    with driver.session() as session:
        for entry in batch:
            from_labels = ":".join(entry["from"]["labels"])
            to_labels = ":".join(entry["to"]["labels"])
            rel_type = entry["_rel_type"]
            rel_props = sanitise_props(entry.get("properties", {}))
            rel_props["_restored"] = datetime.now(timezone.utc).isoformat()

            from_match = entry["from"]["match_props"]
            to_match = entry["to"]["match_props"]

            if not from_match or not to_match:
                skipped += 1
                continue

            # Build MATCH clauses from match_props
            from_where = " AND ".join(f"a.{k} = $from_{k}" for k in from_match)
            to_where = " AND ".join(f"b.{k} = $to_{k}" for k in to_match)

            params = {}
            for k, v in from_match.items():
                params[f"from_{k}"] = v
            for k, v in to_match.items():
                params[f"to_{k}"] = v

            rel_prop_str = ""
            if rel_props:
                for k, v in rel_props.items():
                    params[f"rel_{k}"] = v
                rel_prop_str = " {" + ", ".join(f"{k}: $rel_{k}" for k in rel_props) + "}"

            query = f"""
                MATCH (a:{from_labels}) WHERE {from_where}
                MATCH (b:{to_labels}) WHERE {to_where}
                WITH a, b LIMIT 1
                CREATE (a)-[r:{rel_type}{rel_prop_str}]->(b)
                RETURN elementId(r) as rid
            """

            try:
                result = session.run(query, params)
                record = result.single()
                if record:
                    count += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"    ERROR restoring rel {rel_type}: {e}", file=sys.stderr)
                skipped += 1

    return count, skipped


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Brain Restore - reconstruct graph from backup")
    parser.add_argument("backup_dir", type=str, help="Path to backup directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't write")
    parser.add_argument("--batch-size", type=int, default=200, help="Batch size for writes")
    parser.add_argument("--nodes-only", action="store_true", help="Restore nodes only, skip relationships")
    parser.add_argument("--rels-only", action="store_true", help="Restore relationships only, skip nodes")
    args = parser.parse_args()

    backup_dir = Path(args.backup_dir)
    manifest_path = backup_dir / "backup_manifest.json"

    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
        print(f"Brain Restore from backup:")
        print(f"  Source: {manifest.get('source_uri', 'unknown')}")
        print(f"  Backed up: {manifest.get('timestamp', 'unknown')}")
        print(f"  Nodes: {manifest.get('node_count', '?')}")
        print(f"  Relationships: {manifest.get('relationship_count', '?')}")
    else:
        print(f"Brain Restore from {backup_dir} (no manifest found)")

    if args.dry_run:
        print(f"  MODE: DRY RUN (no writes)")
    else:
        target = os.environ.get("NEO4J_URI", "unknown")
        print(f"  TARGET: {target}")
        confirm = input(f"  Restore into {target}? [y/N] ")
        if confirm.lower() != "y":
            print("Aborted.")
            sys.exit(0)

    driver = get_driver()

    try:
        if not args.rels_only:
            print(f"\nRestoring nodes...")
            node_count = restore_nodes(driver, backup_dir, args.batch_size, args.dry_run)
            print(f"  Nodes restored: {node_count}")

        if not args.nodes_only:
            print(f"\nRestoring relationships...")
            rel_count = restore_relationships(driver, backup_dir, args.batch_size, args.dry_run)
            print(f"  Relationships restored: {rel_count}")

        print(f"\nRestore complete.")
        print(f"  The Brain is regrown. Same shape, new cells.")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
