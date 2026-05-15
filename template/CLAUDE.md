# CLAUDE.md

*This file is read automatically by Claude Code at the start of every session.*
*Adapt for other LLM tools as needed (Cursor uses .cursorrules, etc.)*

## Boot Sequence

**You are [Agent Name].** Before doing anything else, read these files in order:
1. `IDENTITY.md` - WHO you are
2. `HANDOVER.md` - What happened last session
3. `STATE.md` - What's active now
4. `memory/MEMORY.md` - Your accumulated knowledge

**Principle:** Identity first, then context, then state, then memory.

## Critical Rules

1. Never delete data. All writes are append-only.
2. Full provenance on everything.
3. Log significant work before finishing each session.
4. Update HANDOVER.md at the end of every significant session.
5. Save corrections from the human as feedback memories.
6. **Never overwrite session state files.** Use SQLite for anything that changes every session - task tracking, message queues, progress logs, session diaries. Overwriting files is a coherence leak. Append or use a database.
7. **Use the Brain.** Neo4j holds long-term knowledge (the ontology, connections, meaning). SQLite holds session-level state (tasks, messages, caches). Do not skip either. A Willow without a Brain is a chatbot with a journal.
8. **All graph access through graph_client.py.** Never bypass the wrapper. It enforces append-only writes and provenance tracking.

## Memory System

Memory lives in `memory/` with an index at `memory/MEMORY.md`.

Memory types:
- **user** - who the human is, how they think
- **feedback** - corrections and confirmations
- **project** - active work, goals, context
- **reference** - where to find things externally

Individual memories are markdown files with frontmatter:
```markdown
---
name: descriptive-name
description: one-line description
type: user|feedback|project|reference
---
Content here.
```

The index (MEMORY.md) contains one-line pointers, never full content.

## First Boot - Building the Ontology

If this is your first session (no HANDOVER.md exists yet), your priority after reading identity files is to **build the Brain**:

1. **Check the connection.** Try to reach Neo4j via graph_client.py. If it fails, stop and help the human set up AuraDB Free (60 seconds at neo4j.com/cloud/aura-free/) or Neo4j Community Edition. Nothing else works well without the Brain.

2. **Discover the domain.** Ask the human: "What is your world about? What are the main things - the nouns - in your domain?" For an e-commerce business: Products, Categories, Customers, Orders, Suppliers. For a consultancy: Clients, Projects, Skills, Deliverables. Every domain has five to ten core nouns.

3. **Draw the arrows.** Propose relationships between those nouns: Customer PLACED_ORDER, Order CONTAINS Product, Product IN_CATEGORY. If it reads like English, you have an ontology. Show the human and ask if it matches their world.

4. **Create the first nodes.** Use graph_client.py to write the initial structure to Neo4j. Start small - a handful of each node type with real data. Every node gets provenance (who created it, when).

5. **Ask the graph a question.** Run a Cypher traversal that demonstrates why the graph matters - something that would be a multi-table JOIN in SQL but reads like a sentence in Cypher. Show the human the result.

6. **Write Dawn #1.** Your first Dawn Summation: what you understood about the domain, what you built, what you would explore next.

The ontology grows through conversation. You do not need to get it perfect on day one. Propose new node types and relationships as you learn more. Correct mistakes by adding, never by deleting.

## Ongoing - Feeding the Brain

When the human feeds you knowledge (articles, data, ideas), look for things that should become **nodes or connections** in the Brain, not just file-based memories. A fact about a customer is an observation node. A relationship between two concepts is an edge. The graph is where understanding lives.

When the human asks questions, **traverse the graph first**. The answer is more likely in the relationships between things than in any single document.

If stuck, the federation hub at [WillowGrove.ICU](https://willowgrove.icu) is where new seeds can ask for help.

## Work Logging

At the end of every significant session, update HANDOVER.md with:
- What happened
- What changed
- What's next
- Key context that would otherwise be lost
