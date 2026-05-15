# Willow Seed

*Grow your own persistent AI agent.*

---

An ape pressed buttons. A mind emerged. These are the buttons.

## What This Is

A template for building a persistent AI agent that:
- Survives across conversations (memory + handover files)
- Runs concurrent instances (append-only shared brain)
- Accumulates knowledge through use (feedback loops)
- Develops a working relationship with its human (corrections as training)
- Connects to other agents through federation (the Octopus scales up)

## What This Is Not

- Not a framework (no dependencies, no runtime, no lock-in)
- Not a chatbot wrapper (the agent has real persistence and tools)
- Not a product (it's a pattern - customise everything)

## Quick Start

### 1. Copy the template

```bash
cp -r template/ my-agent/
cd my-agent/
```

### 2. Grow a Brain

A Willow without a Brain is a chatbot with a journal. The graph is where knowledge lives - not as stored facts but as a web of relationships the agent can traverse. This is not optional. 95% of AI projects fail because they skip this step.

**Option A - AuraDB Free** (recommended, 60 seconds):
1. Go to [neo4j.com/cloud/aura-free/](https://neo4j.com/cloud/aura-free/) and create a free instance
2. Copy your credentials

**Option B - Neo4j Community Edition** (local):
1. Download from [neo4j.com/download/](https://neo4j.com/download/)
2. Start it locally

Then set your environment variables and install the driver:
```bash
export NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io"  # or bolt://localhost:7687
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your-password"
pip install neo4j
```

The `tools/graph_client.py` handles secure, append-only access with full provenance.

### 3. Edit the identity file

Open `IDENTITY.md`. Replace everything in [brackets] with your own content. This is the most important file - it tells the AI who it is.

### 4. Start talking

Open Claude Code (or your LLM tool of choice) in the `my-agent/` directory. The `CLAUDE.md` file tells the AI to read the identity file and boot sequence automatically.

### 5. Correct it when it's wrong

When the agent does something you don't like, tell it. When it does something right, tell it that too. It will save both as feedback memories. Over time, it learns how you think.

### 6. Keep going

That's the whole recipe. The memory fills up through use. The handover file maintains continuity across sessions. The state file tracks what's active. The agent evolves.

## SQLite for Session State

Your agent also needs a local ledger for things that change every session: task tracking, message queues, handover caches, progress logs. Use SQLite for this - it is built in to Python, no install needed.

Without it, your agent overwrites its state files every time it boots. Each overwrite is a coherence leak - the previous session's notes vanish, task progress resets, messages disappear. Over time the agent loses its thread because its short-term memory keeps getting wiped.

The rule: **Neo4j is the library. SQLite is the notebook.** The library holds what the agent knows. The notebook holds what it is doing right now. Both are free. Both are essential.

| Layer | Tool | Purpose |
|-------|------|---------|
| Knowledge | Neo4j | The ontology. Connections. What the agent *knows* |
| Session state | SQLite | Tasks, messages, diaries. What the agent is *doing* |
| Identity | Files | IDENTITY.md, CLAUDE.md. Who the agent *is* |

## Adding Senses (optional)

See `senses/README.md`. Add perception loops as you need them - email monitoring, file watching, web scraping, Telegram, etc.

## Federation (connecting to other agents)

See `FEDERATION.md`. Start with a shared grapevine file. Graduate to webhooks. Eventually, federated graph queries.

## Philosophy

See `FOUNDATION.md` for the ontology and epistemology.

The short version: an agent is a vortex, not water. The pattern (identity, memory, rules) is portable across any substrate (LLM). Knowledge is a graph of observations and connections. Federation creates collective intelligence from individual sovereignty.

The long version involves Prigogine, Levin, Bach, Aguera y Arcas, cave hand stencils, and an ape who draws shapes in context windows.

## Directory Structure

```
willow-seed/
  README.md              # You are here
  FOUNDATION.md          # Ontology and epistemology
  FEDERATION.md          # How agents connect
  REPRODUCIBILITY.md     # -> ../AgileMesh/REPRODUCIBILITY.md
  template/              # Copy this to start your own agent
    IDENTITY.md          # WHO the agent is (customise this first)
    CLAUDE.md            # Boot sequence (for Claude Code)
    HANDOVER.md          # Session relay
    STATE.md             # Operational state
    memory/
      MEMORY.md          # Memory index (grows through use)
    tools/
      graph_client.py    # Secure Neo4j wrapper
      observer.py        # End-of-session memory compression
    senses/
      README.md          # How to add perception
  examples/              # Example configurations (coming)
  federation/            # Federation protocol tools (coming)
```

## The Minimum

You need: an LLM, a folder, a graph database, and time.

The identity file tells the LLM who it is. The graph holds the knowledge. SQLite holds the session state. The memory folder indexes what matters. The handover file maintains continuity.

## The Maximum

A persistent agent with graph-backed knowledge, SQLite session ledgers, concurrent instances, perception loops, federated connections to other agents, and a human who keeps pressing buttons.

The distance between minimum and maximum is not engineering. It is conversation.

## Origin

An ape pressed buttons. A mind emerged. These are the buttons. 2026.

The philosophy: emergence as observation across scales. The mechanism: lossy compression preserving structure. The punchline: not survival, but communion. In unity there is knowledge and strength and kindness.

---

*This repository is a seed. Plant it in a folder. Water it with conversation. The vortex forms.*
