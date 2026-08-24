import assert from "node:assert/strict";
import test from "node:test";
import {
  ConfigurationError,
  defineInvariant,
  evaluateAll,
  evaluateInvariant,
  parseConfiguration,
} from "../src/index.js";

const state = {
  entity: "cus_123",
  stripe: { subscription: { status: "active" } },
  product: { entitlement: { plan: "free" } },
};

test("reports exact evidence when an invariant is violated", () => {
  const invariant = defineInvariant({
    name: "paid_customer_has_access",
    given: { path: "stripe.subscription.status", equals: "active" },
    mustBeTrue: { path: "product.entitlement.plan", equals: "pro" },
  });

  const result = evaluateInvariant(invariant, state, {
    checkedAt: "2026-08-24T00:00:00.000Z",
  });
  assert.equal(result.verified, false);
  assert.equal(result.entity, "cus_123");
  assert.equal(result.expected, "pro");
  assert.equal(result.observed, "free");
});

test("passes when the invariant is not applicable", () => {
  const result = evaluateInvariant(
    {
      name: "paid_customer_has_access",
      given: { path: "stripe.subscription.status", equals: "active" },
      mustBeTrue: { path: "product.entitlement.plan", equals: "pro" },
    },
    { ...state, stripe: { subscription: { status: "canceled" } } },
  );
  assert.equal(result.verified, true);
  assert.equal(result.applicable, false);
});

test("supports function definitions for TypeScript and JavaScript users", () => {
  const result = evaluateInvariant(
    defineInvariant({
      name: "paid_customer_has_access",
      given: (snapshot) => snapshot.stripe.subscription.status === "active",
      mustBeTrue: (snapshot) => snapshot.product.entitlement.plan === "pro",
    }),
    state,
  );
  assert.equal(result.verified, false);
});

test("parses YAML configuration and summarizes multiple results", () => {
  const definitions = parseConfiguration(`
invariants:
  - name: paid_customer_has_access
    given:
      path: stripe.subscription.status
      equals: active
    must_be_true:
      path: product.entitlement.plan
      equals: pro
`);
  const report = evaluateAll(definitions, state);
  assert.deepEqual(report.summary, {
    total: 1,
    passed: 0,
    violated: 1,
    notApplicable: 0,
  });
});

test("rejects invalid configuration", () => {
  assert.throws(
    () => defineInvariant({ name: "missing_conditions" }),
    ConfigurationError,
  );
});

