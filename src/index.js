import { parse as parseYaml } from "yaml";

const COMPARATORS = {
  equals: (actual, expected) => Object.is(actual, expected),
  not_equals: (actual, expected) => !Object.is(actual, expected),
  includes: (actual, expected) =>
    Array.isArray(actual) || typeof actual === "string"
      ? actual.includes(expected)
      : false,
  exists: (actual, expected = true) =>
    expected ? actual !== undefined && actual !== null : actual == null,
};

export class ConfigurationError extends Error {
  constructor(message) {
    super(message);
    this.name = "ConfigurationError";
  }
}

export function defineInvariant(definition) {
  validateDefinition(definition);
  return Object.freeze({ ...definition });
}

export function getPath(value, path) {
  if (!path) return value;
  return String(path)
    .split(".")
    .reduce((current, key) => current?.[key], value);
}

export function evaluateInvariant(definition, state, options = {}) {
  validateDefinition(definition);

  const givenResult = evaluateCondition(definition.given, state);
  const mustResult = evaluateCondition(
    definition.mustBeTrue ?? definition.must_be_true,
    state,
  );
  const applicable = givenResult.matches;
  const verified = !applicable || mustResult.matches;

  return {
    verified,
    applicable,
    invariant: definition.name,
    entity: options.entity ?? state?.entity ?? null,
    expected: applicable ? mustResult.expected : null,
    observed: applicable ? mustResult.observed : null,
    evidence: {
      given: givenResult,
      mustBeTrue: mustResult,
    },
    checkedAt: options.checkedAt ?? new Date().toISOString(),
  };
}

export function evaluateAll(definitions, state, options = {}) {
  if (!Array.isArray(definitions) || definitions.length === 0) {
    throw new ConfigurationError("At least one invariant is required.");
  }
  const results = definitions.map((definition) =>
    evaluateInvariant(definition, state, options),
  );
  return {
    verified: results.every((result) => result.verified),
    summary: {
      total: results.length,
      passed: results.filter((result) => result.verified).length,
      violated: results.filter((result) => !result.verified).length,
      notApplicable: results.filter((result) => !result.applicable).length,
    },
    results,
  };
}

export function parseConfiguration(source) {
  const parsed = typeof source === "string" ? parseYaml(source) : source;
  const definitions = Array.isArray(parsed?.invariants)
    ? parsed.invariants
    : parsed?.invariant
      ? [parsed.invariant]
      : parsed?.name
        ? [parsed]
        : [];

  if (definitions.length === 0) {
    throw new ConfigurationError(
      "Configuration must contain an invariant or invariants array.",
    );
  }

  return definitions.map(normalizeDefinition).map(defineInvariant);
}

function normalizeDefinition(definition) {
  return {
    ...definition,
    mustBeTrue: definition.mustBeTrue ?? definition.must_be_true,
  };
}

function validateDefinition(definition) {
  if (!definition || typeof definition !== "object") {
    throw new ConfigurationError("An invariant must be an object.");
  }
  if (!definition.name || typeof definition.name !== "string") {
    throw new ConfigurationError("An invariant requires a string name.");
  }
  if (!definition.given) {
    throw new ConfigurationError(`${definition.name}: given is required.`);
  }
  if (!(definition.mustBeTrue ?? definition.must_be_true)) {
    throw new ConfigurationError(
      `${definition.name}: mustBeTrue or must_be_true is required.`,
    );
  }
}

function evaluateCondition(condition, state) {
  if (typeof condition === "function") {
    const observed = Boolean(condition(state));
    return {
      path: null,
      comparator: "function",
      expected: true,
      observed,
      matches: observed,
    };
  }

  if (!condition || typeof condition !== "object" || !condition.path) {
    throw new ConfigurationError(
      "A declarative condition requires a path and comparator.",
    );
  }

  const comparatorName = Object.keys(COMPARATORS).find((key) =>
    Object.hasOwn(condition, key),
  );
  if (!comparatorName) {
    throw new ConfigurationError(
      `${condition.path}: use equals, not_equals, includes, or exists.`,
    );
  }

  const observed = getPath(state, condition.path);
  const expected = condition[comparatorName];
  return {
    path: condition.path,
    comparator: comparatorName,
    expected,
    observed: observed ?? null,
    matches: COMPARATORS[comparatorName](observed, expected),
  };
}

