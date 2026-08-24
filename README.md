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

Your services can be healthy, your jobs can be running, and your data can still describe an impossible business state. **Business Consistency is a deterministic, read-only verification layer for that gap.**

> **Status:** experimental validation release. Local snapshot evaluation and both CLIs work today. Live connectors and hosted monitoring are not included yet.

## Try the Python CLI

The demo uses local snapshots, so you need no Stripe account, database, API keys, collector or telemetry stack.

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

## Try the Node.js and TypeScript package

Until the first npm release is published, install directly from GitHub:

```bash
npm install --save-dev github:wnorth26-lang/business-consistency
```

Node.js 20 or newer is required.

```bash
npx business-consistency \
  --config examples/billing.yaml \
  --state examples/state.json
```

Use `--json` for machine-readable evidence. Exit code `0` means all applicable invariants passed, `1` means at least one violation was found, and `2` means the input or configuration was invalid.

```ts
import { defineInvariant, evaluateInvariant } from "business-consistency";

const invariant = defineInvariant({
  name: "paid_customer_has_access",
  given: (state) => state.stripe.subscription.status === "active",
  mustBeTrue: (state) => state.product.entitlement.plan === "pro",
});

const result = evaluateInvariant(invariant, state);
```

The JavaScript/TypeScript evaluator also accepts YAML conditions using `equals`, `not_equals`, `includes` and `exists`.

## Define business state, not workflow sequences

Python CLI configuration names source snapshots explicitly:

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
```

The Node.js CLI accepts a combined state snapshot:

```yaml
invariants:
  - name: paid_customer_has_access
    given:
      path: stripe.subscription.status
      equals: active
    must_be_true:
      path: product.entitlement.plan
      equals: pro
```

Both answer the same question: **given what is true in one system, what must be true in the other systems?**

## Where the product boundary sits

| Category | Core question |
|---|---|
| Infrastructure observability | Are my services healthy? |
| Workflow observability | Did the expected sequence of events complete? |
| Data quality | Is this dataset valid? |
| Sync / ETL | Did data move? |
| Reconciliation | Do records or transactions match? |
| **Business Consistency** | **Do systems of record agree with the business invariant?** |

- **Not workflow observability.** The core model inspects state; it does not require a prescribed event sequence.
- **Not synchronization.** Verification is read-only; it does not repair or overwrite source systems.
- **Not a data-quality framework.** An invariant can span unrelated APIs, SaaS products and databases.
- **Not financial reconciliation software.** Billing is the first example, not the entire category.

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

## Works now

- [x] constrained YAML invariant formats
- [x] current-state evaluation
- [x] local JSON snapshots
- [x] human-readable and JSON output
- [x] Python CLI
- [x] Node.js CLI and typed JavaScript API
- [x] automated tests and CI
- [x] stateless HTTP API with OpenAPI documentation
- [x] generic, batch and four opinionated business-state checks

## Build only if demand appears

- [ ] live Stripe connector
- [ ] PostgreSQL connector
- [ ] generic REST connector
- [ ] entity matching across systems
- [ ] tolerance and time-window enforcement
- [ ] scheduled checks and alerts
- [ ] evidence history
- [ ] hosted monitoring
- [ ] MCP interface

## Run the HTTP API

The API follows the same versioned route and validation conventions as the existing Agent Evidence Labs catalogue. It accepts state supplied by the caller and does not store credentials or mutate source systems.

```bash
pip install -e ".[api]"
consistency-api
```

Open `http://localhost:8000/docs` for interactive OpenAPI documentation.

| Route | Purpose |
|---|---|
| `POST /v1/verify` | Evaluate one custom invariant |
| `POST /v1/verify-batch` | Evaluate up to 100 custom invariants |
| `POST /v1/check/subscription-access` | Billing status versus product access |
| `POST /v1/check/order-fulfilment` | Commerce status versus shipment state |
| `POST /v1/check/crm-billing` | Closed-won CRM account versus billing customer |
| `POST /v1/check/employee-offboarding` | HR termination versus active account access |

Example:

```bash
curl -X POST http://localhost:8000/v1/check/subscription-access \
  -H "content-type: application/json" \
  -d '{
    "customer_id": "cus_123",
    "billing_status": "active",
    "access_plan": "free"
  }'
```

The result is `consistent`, `violation`, or `not_applicable`, with deterministic evidence and a UTC check time. Marketplace authentication and metering belong at the hosting gateway; validation and internal failures must not be charged.

## Read-only by design

```text
System A ──┐
System B ──┼── READ → VERIFY → EVIDENCE
System C ──┘
                never
                  ↓
             mutate state
```

The open-source engines evaluate state supplied by the caller. They do not store credentials, modify source records or transmit telemetry. Live connectors should request the narrowest practical read-only permissions.

## Help determine what gets built

This repository is a market test. If you need another system, open a **Connector Request** and describe the actual invariant. If systems have genuinely disagreed in production, open a **Real-world consistency failure** issue. Those signals matter more than stars.

The open-source engine should remain useful locally. A hosted product is justified only if users ask for continuous checks, managed credentials, alerting, evidence history, collaboration or higher-frequency monitoring.

## Development

```bash
# Python
pip install -e . pytest
pytest -q

# Node.js
pnpm install
pnpm run check
pnpm test
pnpm run example
```

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Never put production credentials or customer data in public issues; see [SECURITY.md](SECURITY.md).

## License

MIT © Agent Evidence Labs and Business Consistency contributors.

---

<p align="center"><strong>What business fact has silently gone out of sync in your systems?</strong><br>Tell us the systems and the invariant. That is the roadmap.</p>
