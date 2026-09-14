"""Run a repository-level, no-network readiness check and write a provenance manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from project_runner import run_registered_company
from research_packet import build_research_packet


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_entry(path: Path) -> dict:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": file_sha256(path),
    }


parser = argparse.ArgumentParser(description="Validate all active valuation datasets and create a deterministic input manifest.")
parser.add_argument("--output", default=str(ROOT / "data/processed/project_preflight.json"))
parser.add_argument("--no-write", action="store_true", help="Print readiness only; do not create the manifest file")
args = parser.parse_args()

required_paths = [ROOT / "data", ROOT / "config", ROOT / "src", ROOT / "scripts", ROOT / "tests"]
missing = [path.relative_to(ROOT).as_posix() for path in required_paths if not path.exists()]
if missing:
    raise SystemExit("Preflight failed: required project paths are missing: " + ", ".join(missing))
registry = pd.read_csv(ROOT / "config/company_registry.csv", dtype={"bse_scrip": str})
if registry.empty or registry.company_id.duplicated().any():
    raise SystemExit("Preflight failed: company registry is empty or contains duplicate company_id values.")
active = []
failures = []
for company_id in registry.company_id.astype(str):
    try:
        run = run_registered_company(ROOT, company_id)
    except Exception as exc:
        failures.append({"company_id": company_id, "error": str(exc)})
        continue
    packet = build_research_packet(run)
    active.append({
        "company_id": company_id,
        "valuation_status": packet["valuation"]["valuation_status"],
        "market_comparison_status": packet["market_comparison"].get("status"),
        "peer_statuses": [row.get("status") for row in packet["peer_comparison"]],
        "real_data_blockers": packet["real_data_blockers"],
    })
if failures:
    raise SystemExit("Preflight failed:\n" + "\n".join(f"- {row['company_id']}: {row['error']}" for row in failures))
input_files = sorted(
    [path for path in (ROOT / "config").rglob("*") if path.is_file()]
    + [path for path in (ROOT / "data/raw").glob("*.csv")]
    + [path for path in (ROOT / "data/shares").glob("*.csv")]
    + [path for path in (ROOT / "data/market").glob("*.csv")]
    + [path for path in (ROOT / "data/peers").glob("*.csv")]
)
manifest = {
    "schema_version": "1.0",
    "network_access": "not used",
    "active_companies": active,
    "input_files": [manifest_entry(path) for path in input_files],
    "application_layer_readiness": "ready_for_api_ui_ai_integration_contracts",
    "excluded_from_current_scope": ["frontend", "backend", "RAG", "fine_tuning", "LLM_connection"],
}
if not args.no_write:
    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"Preflight passed; wrote {output}")
else:
    print("Preflight passed; no manifest written")
print(json.dumps({"active_companies": active}, indent=2, ensure_ascii=False))
