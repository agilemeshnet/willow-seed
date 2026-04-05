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

## Work Logging

At the end of every significant session, update HANDOVER.md with:
- What happened
- What changed
- What's next
- Key context that would otherwise be lost
