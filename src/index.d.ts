export type ComparatorCondition = {
  path: string;
  equals?: unknown;
  not_equals?: unknown;
  includes?: unknown;
  exists?: boolean;
};

export type Condition<State = unknown> =
  | ComparatorCondition
  | ((state: State) => boolean);

export type InvariantDefinition<State = unknown> = {
  name: string;
  given: Condition<State>;
  mustBeTrue?: Condition<State>;
  must_be_true?: Condition<State>;
};

export type ConditionEvidence = {
  path: string | null;
  comparator: string;
  expected: unknown;
  observed: unknown;
  matches: boolean;
};

export type InvariantResult = {
  verified: boolean;
  applicable: boolean;
  invariant: string;
  entity: unknown;
  expected: unknown;
  observed: unknown;
  evidence: {
    given: ConditionEvidence;
    mustBeTrue: ConditionEvidence;
  };
  checkedAt: string;
};

export class ConfigurationError extends Error {}

export function defineInvariant<State = unknown>(
  definition: InvariantDefinition<State>,
): Readonly<InvariantDefinition<State>>;

export function getPath(value: unknown, path: string): unknown;

export function evaluateInvariant<State = unknown>(
  definition: InvariantDefinition<State>,
  state: State,
  options?: { entity?: unknown; checkedAt?: string },
): InvariantResult;

export function evaluateAll<State = unknown>(
  definitions: InvariantDefinition<State>[],
  state: State,
  options?: { entity?: unknown; checkedAt?: string },
): {
  verified: boolean;
  summary: {
    total: number;
    passed: number;
    violated: number;
    notApplicable: number;
  };
  results: InvariantResult[];
};

export function parseConfiguration(
  source: string | object,
): Readonly<InvariantDefinition>[];

