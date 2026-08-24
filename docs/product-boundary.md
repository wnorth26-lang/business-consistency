# Product Boundary

## Core thesis
Business Consistency evaluates **current business state across independent systems of record**.

> Given what is true in one system, what must also be true in the other systems?

## Non-goals
- Workflow/event observability as the core model
- Synchronization or automatic mutation
- A general-purpose rules language
- Dataset-centric data quality
- Finance-only reconciliation

## Live connector constraints
Connectors should be read-only by default, minimally scoped, explicit about freshness, independently testable, and able to return evidence about where/when a value was observed.
