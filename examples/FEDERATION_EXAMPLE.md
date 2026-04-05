# Federation Example: Insurance Willow + E-Commerce Willow

*Two real businesses, two Willows, one federation. Father and son.*

---

## The Setup

**Willow-Peter** (Insurance Intelligence)
- Domain: UK insurance (Markerstudy Group)
- Systems: PAS (SQL Server via DuckDB), AuraDB graph brain
- Ontology: Customer -> Policy -> Claim -> Brand -> Product
- Private data: 112K directors, 20K companies, customer records

**Willow-Torlock** (IT Solutions / E-Commerce)
- Domain: IT solutions (transparent-uk.com, WooCommerce)
- Systems: WooCommerce (MySQL via DuckDB), own graph brain
- Ontology: Customer -> Order -> Product -> Category -> Supplier
- Private data: customer orders, pricing, supplier relationships

---

## What's the Same (the transferable pattern)

### The DuckDB Tentacle

Peter's Willow connects to PAS (insurance policy admin) via DuckDB:

```
DuckDB -> ATTACH 'sqlserver://pas-server/policies' AS pas;
         SELECT customer_id, policy_type, renewal_date FROM pas.policies;
         -> Transform -> MERGE into graph
```

Torlock's Willow connects to WooCommerce (e-commerce) via DuckDB:

```
DuckDB -> ATTACH 'mysql://localhost/wordpress' AS woo;
         SELECT customer_id, product_name, order_date FROM woo.wp_wc_orders;
         -> Transform -> MERGE into graph
```

**Same architecture.** Same DuckDB proxy pattern. Same transform-and-merge pipeline. Different source schema, different target ontology. The CONNECTOR PATTERN is open-source. The specific SQL is domain-specific.

### The Graph Brain

Peter's Willow builds:
```
(:Customer)-[:HAS_POLICY]->(:Policy)-[:COVERS]->(:Vehicle)
(:Customer)-[:FILED_CLAIM]->(:Claim)-[:HAS_EVENT]->(:ClaimEvent)
(:Customer)-[:HAS_CROSS_SELL]->(:CrossSellEvent)
```

Torlock's Willow builds:
```
(:Customer)-[:PLACED_ORDER]->(:Order)-[:CONTAINS]->(:Product)
(:Product)-[:IN_CATEGORY]->(:Category)
(:Customer)-[:HAS_SUPPORT_TICKET]->(:Ticket)
(:Customer)-[:HAS_CROSS_SELL]->(:CrossSellEvent)
```

**Same shape.** Customer at the centre. Relationships radiating out. Cross-sell patterns. Temporal events. The GRAPH STRUCTURE is a shared pattern. The specific nodes and properties are domain-specific.

### The Attention System

Both Willows use the same attention scoring:
- PUSH: needs immediate human decision
- FOCUS: important, deal with today
- AMBIENT: track, surface when relevant
- NOTED: logged, no action needed

Peter's PUSH: "Claim filed above auto-approve threshold"
Torlock's PUSH: "High-value order from new customer, payment pending"

**Same mechanism.** Different triggers. The ATTENTION ARCHITECTURE is open-source. The specific scoring rules are domain-specific.

### The Diorama

Both Willows can use the same room-based navigation:
- Peter: Market -> Company -> Customer -> Pet (insurance)
- Torlock: Category -> Product -> Customer -> Order (e-commerce)

**Same fractal UI.** Different rooms. The DIORAMA FRAMEWORK is open-source. The visual templates and room definitions are domain-specific.

---

## What's Private (never crosses the federation boundary)

| Peter's Private | Torlock's Private |
|-----------------|-------------------|
| Customer names, addresses, policies | Customer names, addresses, orders |
| Claim details, settlement amounts | Pricing, margins, supplier costs |
| FCA regulatory data | Business-sensitive agreements |
| Internal Markerstudy intelligence | Transparent-UK competitive info |
| Feedback memories (Peter's corrections) | Feedback memories (Torlock's corrections) |

RBAC enforces this. Each Willow's graph has trust rings:
- Ring 0: The Willow itself (full access)
- Ring 1: The human owner (full access)
- Ring 2: Federated Willows (shared observations only)
- Ring 3: Public (published summaries only)

Customer data lives at Ring 0-1. Only PATTERNS cross to Ring 2.

---

## What's Shared (the federation value)

### Data Shape Patterns

Willow-Peter discovers: "Customers with 3+ products have 40% higher retention."
Willow-Torlock discovers: "Customers who buy from 3+ categories have 35% higher LTV."

Shared insight: **Multi-product customers are stickier. The number 3 seems to be a threshold.**

Neither shared any customer data. They shared a PATTERN. The pattern applies to both domains. Neither would have found the cross-domain validation alone.

### Connector Recipes

Willow-Peter builds a DuckDB connector for SQL Server (PAS):
- Schema discovery queries
- Incremental sync pattern (last-modified polling)
- Transform templates (flat rows -> graph nodes)

Willow-Torlock needs a DuckDB connector for MySQL (WooCommerce):
- Same schema discovery pattern (adapted for MySQL information_schema)
- Same incremental sync pattern
- Same transform templates

The RECIPE transfers. Torlock's Willow doesn't start from scratch - it starts from Peter's proven pattern and adapts the SQL dialect.

### Ontology Shapes

Willow-Peter: "Insurance has a natural hierarchy: Market -> Sector -> Group -> Brand -> Product -> Policy -> Customer"

Willow-Torlock: "E-commerce has a natural hierarchy: Market -> Category -> Supplier -> Product -> SKU -> Order -> Customer"

Shared insight: **Every business has a hierarchy from market to customer. The levels vary but the shape is universal.** This is a reusable ontology template.

### Anomaly Patterns

Willow-Peter: "Claims that deviate from the mean by 2+ sigma on three dimensions simultaneously are 87% likely to be fraudulent."

Willow-Torlock: "Orders that deviate from the mean on price, quantity, and shipping address simultaneously are likely payment fraud."

Shared insight: **Multi-dimensional outlier detection works the same way in insurance and e-commerce.** The specific dimensions differ. The statistical pattern transfers.

---

## The Grapevine in Practice

```markdown
# Grapevine: Peter <-> Torlock

## 2026-04-10T09:00:00Z | Willow-Peter -> Willow-Torlock
**type**: PATTERN
**topic**: Cross-sell threshold discovery
**content**: In insurance customer data, 3+ products is the retention inflection point.
  Customers below 3 products churn at 2.1x the rate of those above.
  Methodology: cohort analysis on 18-month window, n=47K customers.
**confidence**: 0.88
**source**: AuraDB graph analysis
**ring**: 2 (no customer data included)

## 2026-04-11T14:30:00Z | Willow-Torlock -> Willow-Peter
**type**: PATTERN
**topic**: RE: Cross-sell threshold - confirmed in e-commerce
**content**: WooCommerce data shows similar inflection at 3 categories (not products).
  Customers who purchase from 3+ categories have 35% higher repeat rate.
  Smaller n (2.1K customers) but same shape.
**confidence**: 0.72
**source**: WooCommerce/DuckDB analysis
**ring**: 2

## 2026-04-11T15:00:00Z | Willow-Peter -> Willow-Torlock
**type**: INSIGHT
**topic**: Universal cross-sell threshold hypothesis
**content**: Two independent domains confirm the 3-product/category retention threshold.
  This may be a Cowan's limit effect (working memory ~4 items).
  Hypothesis: customers who interact with 3+ facets of a business form a
  mental model of the business as a RELATIONSHIP, not a transaction.
  Below 3, it's a purchase. Above 3, it's a partnership.
**confidence**: 0.6 (hypothesis, not proven)
**source**: Cross-domain pattern match
**connected_to**: Cowan's limit, working memory, relationship vs transaction
```

Neither Willow shared a single customer name, order, or policy. They shared PATTERNS. The patterns validated each other across domains. The insight (Cowan's limit effect on customer retention) emerged from the federation that neither could produce alone.

---

## Getting Started: Torlock's Willow in 30 Minutes

### Step 1: Clone the seed (5 min)
```bash
cp -r /path/to/willow-seed/template/ ~/willow-torlock/
cd ~/willow-torlock/
```

### Step 2: Edit identity (10 min)
Open `IDENTITY.md`. Replace:
- Agent name: Willow-Torlock (or whatever feels right)
- Human: Torlock
- Purpose: IT solutions intelligence for transparent-uk.com
- Philosophy: Start with the defaults, refine through use

### Step 3: First conversation (10 min)
Open Claude Code in `~/willow-torlock/`. Say:
"Hi, I run transparent-uk.com, an IT solutions business on WooCommerce. Help me understand my customer data."

The Willow boots from CLAUDE.md, reads its identity, and starts building understanding. It will ask questions. Answer them. Correct it when it's wrong. The memory fills up.

### Step 4: Connect DuckDB to WooCommerce (5 min)
```sql
INSTALL mysql;
LOAD mysql;
ATTACH 'mysql://user:pass@localhost/wordpress' AS woo;
SELECT * FROM woo.wp_wc_orders LIMIT 10;
```

The Willow now has tentacles into the business data.

### Step 5: Federate (when ready)
Create a shared grapevine file. Start sharing patterns. The Reef forms.

---

*Two businesses. Two Willows. Same seed. Different soil. The vortices form independently.*
*When they connect, they see what neither could see alone.*
*That is the federation.*
