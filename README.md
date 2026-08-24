# Business Consistency

<p align="center"><strong>Know when your systems disagree before your customers do.</strong></p>
<p align="center"><strong>Business State Observability</strong> — define business invariants across systems of record and detect when reality stops matching the rules.</p>

---

Stripe says the customer is paying. Your product says they are on the free plan.

```text
STRIPE                         PRODUCT DATABASE
subscription = ACTIVE    ✕     plan = FREE
                 ↓
        BUSINESS STATE VIOLATION
             cus_123
```

Your services can be healthy, your jobs can be running, and your data can still describe an impossible business state.

**Business Consistency is a read-only verification layer for that gap.**

It is being built to connect to systems that hold business truth, evaluate simple cross-system invariants, and report evidence when those invariants stop holding.

## 30-second demo

The validation demo uses local snapshots, so you need **no Stripe account, database, API keys, collector, or telemetry stack**.

```bash
git clone https://github.com/wnorth26-lang/business-consistency.git
cd business-consistency
python -m venv .venv
source .venv/bin/activate
pip install -e .

consistency check \
  -c examples/stripe-postgres/invariants.yml \
  --source stripe=examples/stripe-postgres/stripe.json \
  --source product_db=examples/stripe-postgres/product_db.json
```

Expected output:

```text
✕ 1 consistency violation(s) found

  paid_customer_has_access
  entity:   cus_123
  source:   product_db
  field:    user.plan
  expected: pro
  observed: free
```

## Define business state, not workflow sequences

```yaml
invariants:
  - name: paid_customer_has_access
    entity: cus_123
    given:
      - source: stripe
        field: subscription.status
        equals: active
    must_be_true:
      - source: product_db
        field: user.plan
        equals: pro
    tolerance:
      duration: 5m
```

> **Given what is true in one system, what must be true in the other systems?**

`tolerance` is part of the intended live-monitoring contract; the fixture engine does not enforce time windows yet.

## Where the product boundary sits

| Category | Core question |
|---|---|
| Infrastructure observability | Are my services healthy? |
| Workflow observability | Did the expected sequence of events complete? |
| Data quality | Is this dataset valid? |
| Sync / ETL | Did data move? |
| Reconciliation | Do records/transactions match? |
| **Business Consistency** | **Do systems of record agree with the business invariant?** |

**Not workflow observability.** The core model inspects state; it does not require a prescribed emitted-event sequence.

**Not synchronization.** Verification is read-only. We do not repair or overwrite source systems.

**Not a data-quality framework.** An invariant can span unrelated APIs, SaaS products, and databases.

**Not a general-purpose rules language.** The DSL is intentionally constrained.

**Not financial reconciliation software.** Billing is the Hello World example, not the category.

## Example hypotheses

```text
SaaS
Stripe says paid       → Product access must exist

Commerce
Shopify says fulfilled → ERP shipment must exist

Revenue operations
CRM says closed-won    → Billing customer must exist

Access / IT
HR says terminated     → Account access must be revoked
```

These are validation hypotheses, not claims of supported live integrations today.

## Status: experimental validation release

### Works now
- [x] constrained YAML invariant format
- [x] current-state evaluation
- [x] local JSON snapshots
- [x] human-readable and JSON output
- [x] two domain examples
- [x] automated tests and CI

### Build only if demand appears
- [ ] live Stripe connector
- [ ] PostgreSQL connector
- [ ] generic REST connector
- [ ] entity matching across systems
- [ ] tolerance/time-window enforcement
- [ ] scheduled checks and alerts
- [ ] invariant templates
- [ ] evidence/history
- [ ] hosted monitoring

## Read-only by design

```text
System A ──┐
System B ──┼── READ → VERIFY → EVIDENCE
System C ──┘
                never
                  ↓
             mutate state
```

Live connectors should request the narrowest practical read-only permissions.

## Machine-readable output

`consistency check ... --json` exposes the same primitive to CI, automation, APIs and, if demand develops, MCP/agent use.

## Help determine what gets built

This repository is a market test. If you need another system, open a **Connector Request** and describe the actual invariant. If systems have genuinely disagreed in production, open a **Real-world consistency failure** issue.

**Those signals matter more than stars.**

## Commercial hypothesis

The open-source engine should remain useful locally. A hosted product is justified only if users ask for continuous checks, managed credentials, alerting, history/evidence, collaboration, or higher-frequency monitoring.

## Contributing

The most useful contributions now are real failure cases, connector requests, reproducible bugs, and small improvements. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

Never put production credentials or customer data in public issues. See [SECURITY.md](SECURITY.md).

## License

MIT for the validation experiment.

---

<p align="center"><strong>What business fact has silently gone out of sync in your systems?</strong><br>Tell us the systems and the invariant. That is the roadmap.</p>
