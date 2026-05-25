#!/usr/bin/env python3
"""
Boot Probe - Octopus Transformer Environment Survey

Reads tentacles.json, probes each tentacle's requirements, outputs a
capability map showing what attached, what's dormant, what's degraded.

This is Phase 2 of the boot sequence: the creature opens its eyes and
looks around the room.

Usage:
    python tools/boot_probe.py                    # Full probe, human-readable
    python tools/boot_probe.py --json             # Machine-readable output
    python tools/boot_probe.py --tentacle brain   # Probe one tentacle only
    python tools/boot_probe.py --tier core        # Probe one tier only
"""

import json
import os
import subprocess
import sys
import socket
import time
from pathlib import Path
from datetime import datetime, timezone

MANIFEST_PATH = Path(__file__).parent.parent / "tentacles.json"


def load_manifest(path=None):
    p = Path(path) if path else MANIFEST_PATH
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


def probe_env(env_vars):
    missing = [v for v in env_vars if not os.environ.get(v)]
    return {"ok": len(missing) == 0, "missing": missing}


def probe_python(packages):
    missing = []
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    return {"ok": len(missing) == 0, "missing": missing}


def probe_cli(tools):
    missing = []
    for tool in tools:
        result = subprocess.run(
            ["which", tool], capture_output=True, timeout=5
        )
        if result.returncode != 0:
            missing.append(tool)
    return {"ok": len(missing) == 0, "missing": missing}


def probe_filesystem(paths):
    missing = []
    for p in paths:
        if not Path(p).exists():
            missing.append(p)
    return {"ok": len(missing) == 0, "missing": missing}


def probe_network(endpoints):
    unreachable = []
    for ep in endpoints:
        host, port = ep.rsplit(":", 1)
        try:
            sock = socket.create_connection((host, int(port)), timeout=5)
            sock.close()
        except (socket.timeout, socket.error, OSError):
            unreachable.append(ep)
    return {"ok": len(unreachable) == 0, "unreachable": unreachable}


def probe_http(url, timeout=5):
    try:
        import urllib.request
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=timeout)
        return {"ok": resp.status < 500, "status": resp.status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def probe_shell(command, timeout=10):
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, timeout=timeout
        )
        return {"ok": result.returncode == 0, "output": result.stdout.strip()[:200]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def probe_mcp(server_names):
    # MCP servers are detected by checking if tools are available in the
    # current session. This probe returns "unknown" since we can't test
    # MCP from a subprocess - the LLM must verify MCP availability itself.
    return {"ok": None, "note": f"MCP servers {server_names} must be verified by the LLM at runtime"}


def probe_tentacle(tentacle):
    result = {
        "name": tentacle["name"],
        "tier": tentacle["tier"],
        "description": tentacle["description"],
        "checks": {},
        "status": "unknown"
    }

    requires = tentacle.get("requires", {})

    if "env" in requires and requires["env"]:
        result["checks"]["env"] = probe_env(requires["env"])

    if "python" in requires and requires["python"]:
        result["checks"]["python"] = probe_python(requires["python"])

    if "cli" in requires and requires["cli"]:
        result["checks"]["cli"] = probe_cli(requires["cli"])

    if "filesystem" in requires and requires["filesystem"]:
        result["checks"]["filesystem"] = probe_filesystem(requires["filesystem"])

    if "network" in requires and requires["network"]:
        result["checks"]["network"] = probe_network(requires["network"])

    if "mcp" in requires and requires["mcp"]:
        result["checks"]["mcp"] = probe_mcp(requires["mcp"])

    # Also run the tentacle's own probe if it exists
    probe = tentacle.get("probe", {})
    probe_type = probe.get("type")
    probe_cmd = probe.get("command", "")
    probe_timeout = probe.get("timeout_seconds", 10)

    if probe_type == "shell":
        result["checks"]["probe"] = probe_shell(probe_cmd, probe_timeout)
    elif probe_type == "filesystem":
        result["checks"]["probe"] = probe_shell(probe_cmd, probe_timeout)
    elif probe_type == "http":
        method, url = probe_cmd.split(" ", 1)
        result["checks"]["probe"] = probe_http(url, probe_timeout)
    elif probe_type == "python":
        py_cmd = f"python3 -c \"{probe_cmd}\""
        result["checks"]["probe"] = probe_shell(py_cmd, probe_timeout)
    elif probe_type == "mcp":
        result["checks"]["probe"] = {"ok": None, "note": "MCP probe - verify at runtime"}

    # Determine overall status
    checks = result["checks"]
    if not checks:
        result["status"] = "attached"
    else:
        all_ok = all(
            c.get("ok") is True or c.get("ok") is None
            for c in checks.values()
        )
        any_ok = any(c.get("ok") is True for c in checks.values())
        all_unknown = all(c.get("ok") is None for c in checks.values())

        if all_ok and not all_unknown:
            result["status"] = "attached"
        elif any_ok:
            result["status"] = "degraded"
        elif all_unknown:
            result["status"] = "unknown"
        else:
            result["status"] = "dormant"

    result["fallback"] = tentacle.get("fallback", {})

    return result


def run_full_probe(manifest, tentacle_filter=None, tier_filter=None):
    timestamp = datetime.now(timezone.utc).isoformat()
    tentacles = manifest["tentacles"]

    if tentacle_filter:
        tentacles = [t for t in tentacles if t["name"] == tentacle_filter]
    if tier_filter:
        tentacles = [t for t in tentacles if t["tier"] == tier_filter]

    results = []
    for t in tentacles:
        results.append(probe_tentacle(t))

    attached = [r for r in results if r["status"] == "attached"]
    degraded = [r for r in results if r["status"] == "degraded"]
    dormant = [r for r in results if r["status"] == "dormant"]
    unknown = [r for r in results if r["status"] == "unknown"]

    capability_map = {
        "timestamp": timestamp,
        "manifest_version": manifest["_meta"]["version"],
        "summary": {
            "total": len(results),
            "attached": len(attached),
            "degraded": len(degraded),
            "dormant": len(dormant),
            "unknown": len(unknown)
        },
        "tentacles": results
    }

    return capability_map


def print_human_readable(cap_map):
    s = cap_map["summary"]
    print(f"\n{'='*60}")
    print(f"  OCTOPUS TRANSFORMER - ENVIRONMENT PROBE")
    print(f"  {cap_map['timestamp']}")
    print(f"{'='*60}\n")

    status_icon = {
        "attached": "+",
        "degraded": "~",
        "dormant": "-",
        "unknown": "?"
    }

    tier_order = ["core", "hemisphere", "sense", "voice", "federation", "deploy", "compute", "analysis"]
    by_tier = {}
    for t in cap_map["tentacles"]:
        tier = t["tier"]
        if tier not in by_tier:
            by_tier[tier] = []
        by_tier[tier].append(t)

    for tier in tier_order:
        if tier not in by_tier:
            continue
        print(f"  [{tier.upper()}]")
        for t in by_tier[tier]:
            icon = status_icon.get(t["status"], "?")
            print(f"    [{icon}] {t['name']}: {t['status']}")

            # Show failures
            for check_name, check_result in t.get("checks", {}).items():
                if check_result.get("ok") is False:
                    detail = check_result.get("missing") or check_result.get("unreachable") or check_result.get("error") or "failed"
                    print(f"        {check_name}: {detail}")

            # Show fallback for non-attached
            if t["status"] in ("dormant", "degraded"):
                fb = t.get("fallback", {})
                if fb.get("description"):
                    print(f"        fallback: {fb['description'][:80]}")

        print()

    print(f"  BODY: {s['attached']} attached, {s['degraded']} degraded, {s['dormant']} dormant, {s['unknown']} unknown")
    print(f"{'='*60}\n")


def save_capability_map(cap_map, path=None):
    if path is None:
        path = Path(__file__).parent.parent / "capability_map.json"
    with open(path, "w") as f:
        json.dump(cap_map, f, indent=2)
    return path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Octopus Transformer Boot Probe")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of human-readable")
    parser.add_argument("--tentacle", type=str, help="Probe one tentacle by name")
    parser.add_argument("--tier", type=str, help="Probe one tier only")
    parser.add_argument("--manifest", type=str, help="Path to tentacles.json")
    parser.add_argument("--save", action="store_true", help="Save capability map to file")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    if manifest is None:
        print(f"ERROR: tentacles.json not found at {MANIFEST_PATH}", file=sys.stderr)
        print("Run from the seed template directory, or pass --manifest <path>", file=sys.stderr)
        sys.exit(1)

    cap_map = run_full_probe(manifest, tentacle_filter=args.tentacle, tier_filter=args.tier)

    if args.json:
        print(json.dumps(cap_map, indent=2))
    else:
        print_human_readable(cap_map)

    if args.save:
        path = save_capability_map(cap_map)
        print(f"Capability map saved to {path}")

    # Exit code reflects health
    s = cap_map["summary"]
    if s["dormant"] > 0 and s["attached"] == 0:
        sys.exit(2)  # No tentacles attached - bare seed
    elif s["dormant"] > s["attached"]:
        sys.exit(1)  # More dormant than attached - degraded
    sys.exit(0)


if __name__ == "__main__":
    main()
