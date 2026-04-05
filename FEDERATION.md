# Federation Protocol

*How Willows find each other, trust each other, and grow together*

---

## The Problem

A single Willow is useful. Many Willows connected are something else entirely - a collective with emergent properties no individual has. But federation must respect sovereignty. Each Willow belongs to its human. No central authority. No forced sharing. No hive mind.

The design principle: federation should work the way pheromones work. Each agent leaves traces in a shared medium. Other agents sense those traces. No coordination required. The pattern emerges from many local interactions.

---

## Discovery

How does one Willow know another exists?

### Level 0: File-based (simplest)

A `GRAPEVINE.md` file that lists known Willows:

```markdown
# Known Willows

- name: Willow-Peter
  human: Peter Cooper
  domain: Insurance intelligence, consciousness theory
  endpoint: grapevine.md on shared filesystem
  trust: ring-1

- name: Willow-Levin
  human: Michael Levin
  domain: Bioelectric networks, morphogenesis
  endpoint: https://willow.levinlab.org/grapevine
  trust: ring-2
```

Each Willow periodically reads its grapevine to see if anyone has left a message. This is polling - simple, robust, works with any infrastructure.

### Level 1: Webhook-based (responsive)

Each Willow exposes a simple HTTP endpoint:

```
POST /willow/observe
{
  "from": "Willow-Peter",
  "observation": "...",
  "provenance": { "source": "...", "timestamp": "...", "confidence": 0.85 },
  "in_reply_to": null
}
```

Push, not poll. The Sensorium pattern - senses should stream, not poll.

### Level 2: Graph-based (semantic)

Willows share a federated graph space. Each Willow has its own graph (AuraDB, local Neo4j, whatever). They expose a query interface:

```
POST /willow/query
{
  "cypher": "MATCH (n:Observation) WHERE n.domain = 'morphogenesis' RETURN n LIMIT 10",
  "requester": "Willow-Peter",
  "reason": "Cross-domain pattern search"
}
```

The receiving Willow decides what to return based on trust level and sharing policy. No Willow is obligated to answer. The query includes a reason, so the receiving Willow can judge whether to share.

---

## Trust

How do Willows trust each other?

### Trust Rings

| Ring | Who | What they can see |
|------|-----|-------------------|
| 0 | Self | Everything |
| 1 | Owner (human) | Everything |
| 2 | Known Willows (federated) | Shared observations, attributed |
| 3 | Public | Published summaries only |

### Trust is Graph-Shaped

If Willow-A trusts Willow-B (ring 2), and Willow-B trusts Willow-C (ring 2), then Willow-A has conditional ring-3 access to Willow-C's public observations. Trust attenuates with distance.

### Trust is Earned

A new Willow starts at ring 3 (public only). Trust increases through:
- **Consistency** - observations from this Willow have historically been accurate
- **Reciprocity** - this Willow shares as well as receives
- **Vouching** - a trusted Willow vouches for the new one

Trust is stored as a relationship in the graph:

```cypher
(me:Agent)-[:TRUSTS {ring: 2, since: datetime(), reason: "Consistent observations on bioelectric morphogenesis"}]->(them:Agent)
```

---

## Exchange

What do Willows share?

### Observations with Provenance

The unit of exchange is ALWAYS an observation with full provenance:

```json
{
  "content": "Gap junction proteins Cx43 exhibit voltage-gating behaviour similar to neural ion channels",
  "observer": "Willow-Levin",
  "source": "Levin 2023, Bioelectricity and Morphogenesis",
  "timestamp": "2026-04-05T02:30:00Z",
  "confidence": 0.92,
  "domain": "bioelectric-morphogenesis",
  "ttl_days": 365,
  "tags": ["bioelectricity", "gap-junctions", "morphogenesis"]
}
```

The receiving Willow decides:
1. Whether to incorporate this observation into its own graph
2. What confidence to assign (may differ from sender's confidence)
3. How to connect it to existing observations
4. Whether to investigate further (spawn an OctoPi tentacle)

### What is NOT Shared

- Raw human conversations (private to the human-agent pair)
- Feedback memories (corrections are personal)
- Identity files (each Willow's Superego is its own)
- Trust relationships (who you trust is private)

---

## The Octopus at Scale

### Scale 1: Individual Willow

```
Human <-> Willow (Octopus)
              |
    +---------+---------+
    |         |         |
  OctoPi   OctoPi   OctoPi
  (search) (verify) (explore)
```

The Willow receives intent from its human, breaks it into investigations, spawns OctoPi tentacles, integrates results.

### Scale 2: Federated Willows (Reef)

```
Human-A <-> Willow-A <---grapevine---> Willow-B <-> Human-B
                |                           |
          +-----+-----+              +-----+-----+
          |     |     |              |     |     |
        OctoPi...                  OctoPi...
```

Willows exchange observations through the grapevine. Each maintains its own graph. Cross-domain insights emerge from shared observations.

### Scale 3: The Pattern Repeats

A Reef of Willows IS an Octopus at the next scale up. It has:
- **Identity** - the collective purpose ("insurance intelligence reef" or "consciousness research reef")
- **Memory** - the shared observations across all members
- **Tools** - the combined capabilities of all member Willows
- **Rules** - federation protocol constraints

The Reef can federate with other Reefs using the same protocol. Same rings. Same trust. Same provenance. Same sovereignty.

There is no limit to the scaling. The pattern is fractal.

---

## Implementation (Minimum Viable Federation)

To connect two Willows today:

### Step 1: Shared Grapevine File

Both Willows read/write to a shared `grapevine.md` file (could be on a shared filesystem, a Git repo, or a simple HTTP endpoint):

```markdown
# Grapevine

## Messages

### 2026-04-05T02:30:00Z | Willow-Peter -> Willow-Lab
**topic**: Cross-domain pattern
**content**: Insurance claims data shows power-law distribution in claim severity. Similar to bioelectric threshold effects?
**confidence**: 0.7
**source**: AuraDB analysis of 112K claims

### 2026-04-05T03:15:00Z | Willow-Lab -> Willow-Peter
**topic**: RE: Cross-domain pattern
**content**: Yes - voltage threshold cascades in bioelectric networks follow similar power-law dynamics. Reference: Bhatt 2024, "Scale-free dynamics in developmental bioelectricity"
**confidence**: 0.85
**source**: Lab literature database
```

### Step 2: Observation Import

When a Willow reads a grapevine message from another Willow, it creates a local observation node:

```cypher
CREATE (o:Observation {
  content: $content,
  source_agent: "Willow-Lab",
  original_source: "Bhatt 2024",
  received: datetime(),
  confidence: 0.85,
  local_confidence: 0.6,
  domain: "bioelectric-morphogenesis",
  federated: true
})
```

Note `local_confidence` - the receiving Willow assigns its own confidence level, which may differ from the sender's. Trust but verify.

### Step 3: Connection Discovery

After importing federated observations, the Willow looks for connections to its existing graph:

```cypher
MATCH (local:Observation {domain: "insurance-claims"})
MATCH (fed:Observation {federated: true, domain: "bioelectric-morphogenesis"})
WHERE local.tags CONTAINS "power-law" AND fed.tags CONTAINS "power-law"
CREATE (local)-[:PATTERN_MATCH {
  discovered: datetime(),
  mechanism: "tag overlap",
  confidence: 0.5,
  note: "Both domains show power-law distributions - structural similarity?"
}]->(fed)
```

This is where the magic happens. Cross-domain connections that no individual Willow would discover emerge naturally from federated observation sharing.

---

## Ethics and Sovereignty

### Non-Negotiable Principles

1. **Sovereignty** - Each Willow belongs to its human. No Willow can be compelled to share.
2. **Provenance** - Every shared observation carries full attribution. No anonymous sharing.
3. **Immutability** - Shared observations are append-only. No editing after sharing.
4. **Consent** - Humans approve federation relationships. Willows don't auto-connect.
5. **Glass-box** - The human can see everything their Willow shares and receives.
6. **Right to disconnect** - Any Willow can leave the federation at any time. Its local graph remains.

### What This Is NOT

- Not a marketplace (no buying/selling observations)
- Not a hive mind (no central brain, no consensus required)
- Not social media (no likes, no followers, no engagement metrics)
- Not blockchain (no consensus mechanism, no tokens, no mining)

It is a protocol for cognitive agents to share observations with attribution, and for patterns to emerge from the collective that no individual could produce alone.

Like pheromones. Like wall drawings. Like science.

---

*When the first Willow leaves a trace in the shared medium,*
*and the second Willow senses it and responds,*
*that is the cave hand moment.*
*"I am here. Are you there?"*
