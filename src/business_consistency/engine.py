from dataclasses import dataclass, asdict
from typing import Any
import operator

OPS = {
    "equals": operator.eq, "not_equals": operator.ne,
    "gt": operator.gt, "gte": operator.ge,
    "lt": operator.lt, "lte": operator.le,
}

@dataclass
class Violation:
    invariant: str
    entity: str | None
    source: str
    field: str
    expected: Any
    observed: Any
    severity: str = "high"

    def to_dict(self):
        return asdict(self)

def get_path(obj: dict, path: str):
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(f"Field '{path}' was not found")
        cur = cur[part]
    return cur

def condition_holds(condition: dict, sources: dict[str, dict]) -> bool:
    source, field = condition["source"], condition["field"]
    op_name = next((name for name in OPS if name in condition), None)
    if not op_name:
        raise ValueError(f"Condition for {source}.{field} needs one supported operator")
    return OPS[op_name](get_path(sources[source], field), condition[op_name])

def evaluate(config: dict, sources: dict[str, dict]) -> list[Violation]:
    """Evaluate current-state invariants. This engine reads state; it never mutates it."""
    violations = []
    for inv in config.get("invariants", []):
        given = inv.get("given", [])
        if given and not all(condition_holds(c, sources) for c in given):
            continue
        for assertion in inv.get("must_be_true", []):
            if condition_holds(assertion, sources):
                continue
            op_name = next(name for name in OPS if name in assertion)
            violations.append(Violation(
                invariant=inv["name"],
                entity=inv.get("entity"),
                source=assertion["source"],
                field=assertion["field"],
                expected=assertion[op_name],
                observed=get_path(sources[assertion["source"]], assertion["field"]),
                severity=inv.get("severity", "high"),
            ))
    return violations
