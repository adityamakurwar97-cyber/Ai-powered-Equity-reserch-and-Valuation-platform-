"""Import a manually downloaded BSE historical-price CSV without network scraping."""
from pathlib import Path
import argparse
import pandas as pd
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from market_data import validate_market_observations

parser = argparse.ArgumentParser(description="Validate and save historical BSE market observations.")
parser.add_argument("--company", required=True)
parser.add_argument("--input", required=True, help="CSV already mapped to the project market-observation schema")
parser.add_argument("--append", action="store_true", help="Append only non-duplicate observations to an existing saved file")
args = parser.parse_args()
registry = pd.read_csv(ROOT / "config/company_registry.csv", dtype={"bse_scrip": str})
entry = registry[registry.company_id.astype(str) == str(args.company)]
if len(entry) == 0:
    universe = pd.read_csv(ROOT / "data/company_universe.csv", dtype={"bse_scrip": str})
    entry = universe[universe.company_id.astype(str) == str(args.company)]
if len(entry) != 1: raise SystemExit("Market import rejected: company must be a unique row in the active registry or company universe.")
incoming = pd.read_csv(args.input)
errors = validate_market_observations(incoming, expected_company_id=args.company, expected_bse_scrip=str(entry.iloc[0].bse_scrip))
if errors: raise SystemExit("Market import rejected:\n- " + "\n- ".join(errors))
target = ROOT / "data/market" / f"{args.company}_market_observations.csv"
if args.append and target.exists():
    saved = pd.read_csv(target)
    combined = pd.concat([saved, incoming], ignore_index=True)
    if combined.duplicated(["company_id", "observation_date", "observation_time_ist", "price_method"]).any():
        raise SystemExit("Market import rejected: duplicate observation; do not overwrite a saved snapshot.")
    errors = validate_market_observations(combined, expected_company_id=args.company, expected_bse_scrip=str(entry.iloc[0].bse_scrip))
    if errors: raise SystemExit("Market import rejected after merge:\n- " + "\n- ".join(errors))
    incoming = combined
target.parent.mkdir(parents=True, exist_ok=True)
incoming.to_csv(target, index=False)
print(f"Saved {len(incoming)} validated market observation(s) to {target}")
