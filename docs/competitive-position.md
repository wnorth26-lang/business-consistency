# Competitive Position

| Category | Primary question | Business Consistency boundary |
|---|---|---|
| Workflow observability | Did the expected workflow/event sequence complete? | Inspect current cross-system state |
| Sync / ETL | Did data move? | Verify only; do not mutate |
| Data quality | Is a dataset valid? | Verify business entities across systems |
| Rules engine | What does this rule evaluate to? | Constrained invariant against systems of record |
| Reconciliation | Do records/transactions match? | Arbitrary business-state conditions |
| **Business Consistency** | **Do systems agree with the declared business invariant?** | **Core** |

The Stripe/product-access example is a Hello World, not the product category.
