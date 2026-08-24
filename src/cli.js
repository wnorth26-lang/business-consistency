#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import { basename } from "node:path";
import {
  ConfigurationError,
  evaluateAll,
  parseConfiguration,
} from "./index.js";

const HELP = `business-consistency

Verify business invariants against a JSON state snapshot.

Usage:
  business-consistency --config <file.yaml> --state <state.json> [--json]

Options:
  -c, --config   YAML invariant configuration
  -s, --state    JSON state snapshot
      --json     Emit machine-readable JSON
  -h, --help     Show this help

Exit codes:
  0  all applicable invariants passed
  1  one or more invariants were violated
  2  invalid input or execution error`;

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(HELP);
    return 0;
  }
  if (!args.config || !args.state) {
    throw new ConfigurationError("--config and --state are required.");
  }

  const [configurationText, stateText] = await Promise.all([
    readFile(args.config, "utf8"),
    readFile(args.state, "utf8"),
  ]);
  const definitions = parseConfiguration(configurationText);
  const state = JSON.parse(stateText);
  const report = evaluateAll(definitions, state);

  if (args.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    printHumanReport(report, basename(args.state));
  }
  return report.verified ? 0 : 1;
}

function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--json") result.json = true;
    else if (argument === "--help" || argument === "-h") result.help = true;
    else if (argument === "--config" || argument === "-c") {
      result.config = argv[++index];
    } else if (argument === "--state" || argument === "-s") {
      result.state = argv[++index];
    } else {
      throw new ConfigurationError(`Unknown argument: ${argument}`);
    }
  }
  return result;
}

function printHumanReport(report, stateName) {
  console.log(`Business Consistency — ${stateName}`);
  for (const result of report.results) {
    const status = result.verified ? "PASS" : "VIOLATION";
    console.log(`${status.padEnd(10)} ${result.invariant}`);
    if (!result.verified) {
      console.log(`           entity:   ${result.entity ?? "unknown"}`);
      console.log(`           expected: ${format(result.expected)}`);
      console.log(`           observed: ${format(result.observed)}`);
    }
  }
  console.log(
    `\n${report.summary.passed}/${report.summary.total} passed; ${report.summary.violated} violated`,
  );
}

function format(value) {
  return typeof value === "string" ? value : JSON.stringify(value);
}

main()
  .then((exitCode) => {
    process.exitCode = exitCode;
  })
  .catch((error) => {
    console.error(`business-consistency: ${error.message}`);
    process.exitCode = 2;
  });

