"""Stage—not silently merge—manually extracted annual-report source records."""
from pathlib import Path
import argparse, datetime as dt, sys
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from equity_platform import validate_source_record_rows, validate_source_records

parser = argparse.ArgumentParser(description="Stage a source-backed annual-report data refresh for review.")
parser.add_argument("--company", required=True)
parser.add_argument("--input", required=True, help="CSV in the source-record schema, manually extracted from an official report")
parser.add_argument("--approve", action="store_true", help="Merge stage only after human review; otherwise write a review file")
args = parser.parse_args()
registry = pd.read_csv(ROOT / "config/company_registry.csv")
row = registry[registry.company_id == args.company]
if len(row) != 1: raise SystemExit("Unknown company; add its registry row first.")
incoming = pd.read_csv(args.input)
# A refresh can contain a single annual-report row. Validate row-level provenance now;
# validate three-year completeness only after it is combined with the saved register.
errors = validate_source_record_rows(incoming)
if errors: raise SystemExit("Annual refresh rejected:\n- " + "\n- ".join(errors))
if not (incoming.company == row.iloc[0].company).all(): raise SystemExit("Annual refresh rejected: company name does not match registry.")
stage = ROOT / "data/staging" / f"{args.company}_annual_refresh_{dt.date.today().isoformat()}.csv"
stage.parent.mkdir(parents=True, exist_ok=True)
incoming.to_csv(stage, index=False)
if not args.approve:
    print(f"Staged {len(incoming)} rows for review: {stage}\nNo source record was changed. Re-run with --approve only after reviewing duplicate periods/fields and report pages.")
    raise SystemExit(0)
target = ROOT / row.iloc[0].source_records_path
existing = pd.read_csv(target)
combined = pd.concat([existing, incoming], ignore_index=True)
if combined.duplicated(["company", "fiscal_year", "field", "basis"]).any():
    raise SystemExit("Approval rejected: duplicate company/year/field/basis would overwrite or conflict with a saved fact.")
errors = validate_source_records(combined)
if errors:
    raise SystemExit("Approval rejected: the combined register is not valuation-ready:\n- " + "\n- ".join(errors))
combined.to_csv(target, index=False)
print(f"Approved {len(incoming)} new records into {target}. Staged copy retained at {stage}.")
