import argparse, json, sys
from pathlib import Path
import yaml
from .engine import evaluate

def main():
    p = argparse.ArgumentParser(prog="consistency", description="Verify business-state invariants across system snapshots.")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="Evaluate business-state invariants")
    c.add_argument("-c", "--config", required=True)
    c.add_argument("--source", action="append", default=[], help="name=path.json (repeatable)")
    c.add_argument("--json", action="store_true")
    args = p.parse_args()
    try:
        config = yaml.safe_load(Path(args.config).read_text())
        sources = {}
        for spec in args.source:
            name, path = spec.split("=", 1)
            sources[name] = json.loads(Path(path).read_text())
        violations = evaluate(config, sources)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"status":"fail" if violations else "pass", "violations":[v.to_dict() for v in violations]}, indent=2))
    elif violations:
        print(f"✕ {len(violations)} consistency violation(s) found\n")
        for v in violations:
            print(f"  {v.invariant}\n  entity:   {v.entity or '-'}\n  source:   {v.source}\n  field:    {v.field}\n  expected: {v.expected}\n  observed: {v.observed}\n")
    else:
        print("✓ All business invariants hold")
    return 1 if violations else 0

if __name__ == "__main__":
    raise SystemExit(main())
