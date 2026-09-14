"""Run a registered company and write deterministic, source-backed output artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from project_runner import run_registered_company


def markdown_report(run: dict) -> str:
    entry = run["entry"]
    summary = pd.Series(run["summary"]).to_frame("value").to_csv()
    return "\n".join([
        f"# Validation and readiness report — {entry['company']}", "", "## Reconciliation results", "",
        run["reconciliations"].to_csv(index=False), "", "## Readiness", "", run["readiness"].to_csv(index=False),
        "", "## Market comparison", "", pd.DataFrame([run["market_result"]]).to_csv(index=False),
        "", "## Peer comparison", "", run["peer_result"].to_csv(index=False), "", "## Valuation output", "", summary,
    ])


parser = argparse.ArgumentParser(description="Run a registered BSE company from saved, source-backed inputs.")
parser.add_argument("--company", default="infosys", help="company_id from config/company_registry.csv")
parser.add_argument("--output-dir", default=str(ROOT / "data/processed"), help="Directory for generated CSV/JSON artifacts")
parser.add_argument("--write-doc-report", action="store_true", help="Also refresh docs/<company>_validation_report.md")
args = parser.parse_args()

try:
    run = run_registered_company(ROOT, args.company)
except ValueError as exc:
    raise SystemExit(str(exc))
output = Path(args.output_dir).expanduser()
if not output.is_absolute():
    output = ROOT / output
output.mkdir(parents=True, exist_ok=True)
run["historical"].to_csv(output / f"{args.company}_historical_normalized.csv", index=False)
run["reconciliations"].to_csv(output / f"{args.company}_reconciliation_results.csv", index=False)
run["readiness"].to_csv(output / f"{args.company}_readiness.csv", index=False)
run["forecast"].to_csv(output / f"{args.company}_fcff_forecast.csv", index=False)
run["sensitivity"].to_csv(output / f"{args.company}_sensitivity.csv")
pd.DataFrame([run["market_result"]]).to_csv(output / f"{args.company}_market_comparison.csv", index=False)
run["peer_result"].to_csv(output / f"{args.company}_peer_comparison.csv", index=False)
(output / f"{args.company}_valuation_summary.json").write_text(json.dumps(run["summary"], indent=2, allow_nan=False) + "\n")
report = markdown_report(run)
(output / f"{args.company}_validation_report.md").write_text(report)
if args.write_doc_report:
    (ROOT / "docs" / f"{args.company}_validation_report.md").write_text(report)
    if args.company == "infosys":
        (ROOT / "docs/validation_report.md").write_text(report)
print(pd.Series(run["summary"]).to_string())
print(pd.Series(run["market_result"]).to_string())
if run["market_warnings"]:
    print("Market-file warnings:\n- " + "\n- ".join(run["market_warnings"]))
