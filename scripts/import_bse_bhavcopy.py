"""Import a traceable direct BSE close from an official Equity Bhav Copy CSV/ZIP.

This accepts a locally downloaded BSE file only. It does not attempt to bypass BSE
access controls, derive a close from market capitalisation, or self-certify a quote.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
from urllib.parse import urlparse

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from market_data import validate_market_observations


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


parser = argparse.ArgumentParser(description="Import one verified close from an official BSE Equity Bhav Copy.")
parser.add_argument("--company", required=True, help="company_id in the active registry or company universe")
parser.add_argument("--date", required=True, help="Trading date, YYYY-MM-DD")
parser.add_argument("--bhavcopy", required=True, help="Official BSE CSV or ZIP downloaded by the user")
parser.add_argument("--source-url", required=True, help="Exact bseindia.com download or report URL")
parser.add_argument("--retrieval-date", help="YYYY-MM-DD; defaults to today's local date")
parser.add_argument("--output", help="Optional output CSV path; defaults to data/market/<company>_market_observations.csv")
args = parser.parse_args()

try:
    trading_date = pd.Timestamp(args.date)
except ValueError as exc:
    raise SystemExit(f"Bhav Copy import rejected: invalid --date: {exc}")
source_path = Path(args.bhavcopy).expanduser()
if not source_path.is_file():
    raise SystemExit("Bhav Copy import rejected: --bhavcopy does not point to a readable file.")
host = urlparse(args.source_url).hostname or ""
if not (host == "bseindia.com" or host.endswith(".bseindia.com")):
    raise SystemExit("Bhav Copy import rejected: --source-url must be a bseindia.com URL.")
filename = source_path.name.lower()
valid_date_tokens = {
    trading_date.strftime("%Y%m%d"), trading_date.strftime("%d%m%y"),
    trading_date.strftime("%d%m%Y"), trading_date.strftime("%Y-%m-%d"),
}
if not any(token.lower() in filename for token in valid_date_tokens):
    raise SystemExit("Bhav Copy import rejected: filename does not contain the supplied trading date in a recognised BSE date format.")
try:
    retrieval_date = pd.Timestamp(args.retrieval_date) if args.retrieval_date else pd.Timestamp.today().normalize()
except ValueError as exc:
    raise SystemExit(f"Bhav Copy import rejected: invalid --retrieval-date: {exc}")
if retrieval_date < trading_date:
    raise SystemExit("Bhav Copy import rejected: retrieval date cannot precede trading date.")

registry = pd.read_csv(ROOT / "config/company_registry.csv", dtype={"bse_scrip": str})
entry = registry[registry.company_id.astype(str) == str(args.company)]
if len(entry) == 0:
    universe = pd.read_csv(ROOT / "data/company_universe.csv", dtype={"bse_scrip": str})
    entry = universe[universe.company_id.astype(str) == str(args.company)]
if len(entry) != 1:
    raise SystemExit("Bhav Copy import rejected: company must be a unique row in the active registry or company universe.")
entry = entry.iloc[0]
scrip = str(entry.bse_scrip).replace(".0", "").zfill(6)

try:
    copy = pd.read_csv(source_path, compression="infer")
except Exception as exc:
    raise SystemExit(f"Bhav Copy import rejected: unable to read the supplied CSV/ZIP: {exc}")
copy.columns = [str(column).strip().upper() for column in copy.columns]
code_column = next((name for name in ("SC_CODE", "SCRIPCODE", "SCRIP_CODE") if name in copy.columns), None)
close_column = next((name for name in ("CLOSE", "CLOSE_PRICE", "CLOSEPRICE") if name in copy.columns), None)
name_column = next((name for name in ("SC_NAME", "SCHEME_NAME", "SCRIP_NAME") if name in copy.columns), None)
if not code_column or not close_column:
    raise SystemExit("Bhav Copy import rejected: expected a BSE scrip-code column and CLOSE column.")
codes = copy[code_column].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
match = copy[codes == scrip]
if len(match) != 1:
    raise SystemExit(f"Bhav Copy import rejected: expected one row for registered BSE scrip {scrip}, found {len(match)}.")
try:
    close = float(match.iloc[0][close_column])
except (TypeError, ValueError) as exc:
    raise SystemExit(f"Bhav Copy import rejected: CLOSE is not numeric: {exc}")
scrip_name = str(match.iloc[0][name_column]).strip() if name_column else "not supplied in file"
snapshot = pd.DataFrame([{
    "company_id": args.company, "bse_scrip": scrip, "observation_date": trading_date.date().isoformat(),
    "observation_time_ist": "close", "close_price_inr": close, "currency": "INR", "market_cap_inr_crore": pd.NA,
    "price_method": "direct_bse_close", "source_url": args.source_url, "source_artifact": source_path.name,
    "source_file_sha256": sha256(source_path), "retrieval_date": retrieval_date.date().isoformat(),
    "verification_status": "verified", "notes": f"Direct BSE close mapped from official Equity Bhav Copy; source scrip name: {scrip_name}.",
}])
errors = validate_market_observations(snapshot, expected_company_id=args.company, expected_bse_scrip=scrip)
if errors:
    raise SystemExit("Bhav Copy import rejected:\n- " + "\n- ".join(errors))
target = Path(args.output).expanduser() if args.output else ROOT / "data" / "market" / f"{args.company}_market_observations.csv"
if not target.is_absolute():
    target = ROOT / target
target.parent.mkdir(parents=True, exist_ok=True)
if target.exists():
    existing = pd.read_csv(target)
    combined = pd.concat([existing, snapshot], ignore_index=True)
    if combined.duplicated(["company_id", "observation_date", "observation_time_ist", "price_method"]).any():
        raise SystemExit("Bhav Copy import rejected: a direct BSE close for this company/date already exists; preserve the original snapshot.")
    snapshot = combined
snapshot.to_csv(target, index=False)
print(f"Saved verified direct BSE close for {args.company} on {trading_date.date()} to {target}")
