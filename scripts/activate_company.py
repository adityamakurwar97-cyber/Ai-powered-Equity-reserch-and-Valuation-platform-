"""Activate a fully reviewed company workspace in the valuation registry."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from equity_platform import validate_assumptions, validate_information_cutoff, validate_source_records
from market_data import select_share_observation, validate_share_observations

parser = argparse.ArgumentParser(description="Activate a reviewed BSE company for CLI valuation.")
parser.add_argument("--company", required=True, help="company_id from data/company_universe.csv")
args = parser.parse_args()

universe = pd.read_csv(ROOT / "data/company_universe.csv", dtype={"bse_scrip": str, "isin": str})
entry = universe[universe.company_id.astype(str) == str(args.company)]
if len(entry) != 1:
    raise SystemExit("Activation rejected: company must be a unique row in data/company_universe.csv.")
entry = entry.iloc[0]
registry_path = ROOT / "config/company_registry.csv"
registry = pd.read_csv(registry_path, dtype={"bse_scrip": str})
if (registry.company_id.astype(str) == str(args.company)).any():
    raise SystemExit("Activation rejected: company is already active in the registry.")
raw_path = ROOT / "data/raw" / f"{args.company}_source_records.csv"
share_path = ROOT / "data/shares" / f"{args.company}_share_observations.csv"
assumption_path = ROOT / "config/assumptions" / f"{args.company}.json"
if not raw_path.exists() or not share_path.exists() or not assumption_path.exists():
    raise SystemExit("Activation rejected: source records, dated shares, and company assumptions must all exist.")
records = pd.read_csv(raw_path)
shares = pd.read_csv(share_path)
assumptions = json.loads(assumption_path.read_text())
errors = validate_source_records(records)
errors += validate_share_observations(shares)
errors += validate_assumptions(assumptions)
errors += validate_information_cutoff(records, assumptions.get("information_cutoff", ""))
if assumptions.get("assumption_status") != "approved":
    errors.append("Set assumption_status=approved only after reviewing company-specific forecast and bridge assumptions.")
if not records.company.astype(str).eq(str(entry.company)).all():
    errors.append("Source-record company name does not match the company-universe entry.")
if set(shares.company_id.astype(str)) != {str(args.company)}:
    errors.append("Share observations do not match the company id.")
try:
    select_share_observation(shares, args.company, assumptions.get("valuation_date", ""), assumptions.get("information_cutoff", ""))
except ValueError as exc:
    errors.append(str(exc))
if errors:
    raise SystemExit("Activation rejected:\n- " + "\n- ".join(errors))
with registry_path.open("a", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=registry.columns.tolist())
    writer.writerow({
        "company_id": args.company, "company": entry.company, "bse_scrip": str(entry.bse_scrip).zfill(6),
        "isin": entry.isin, "sector": entry.sector, "source_records_path": raw_path.relative_to(ROOT),
        "share_observations_path": share_path.relative_to(ROOT), "assumptions_path": assumption_path.relative_to(ROOT),
    })
universe.loc[universe.company_id.astype(str) == str(args.company), "coverage_status"] = "valuation_ready"
universe.loc[universe.company_id.astype(str) == str(args.company), "notes"] = "Activated after source, share, cutoff, and company-specific assumption validation."
universe.to_csv(ROOT / "data/company_universe.csv", index=False)
print(f"Activated {args.company}; it can now be run with scripts/run_model.py --company {args.company}.")
