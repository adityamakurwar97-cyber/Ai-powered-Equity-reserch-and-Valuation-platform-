"""Reusable application service for the deterministic valuation core.

Future HTTP/API, UI, task-queue, and AI layers should call this module rather than
shelling out to a script or reimplementing validation logic.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from equity_platform import (
    build_historical,
    latest_financial_period_end,
    load_assumptions,
    reconcile_statements,
    run_fcff_valuation,
    sensitivity,
    validate_assumptions,
    validate_information_cutoff,
    validate_source_records,
    valuation_readiness,
)
from market_data import market_comparison, peer_comparison, select_share_observation, validate_market_observations, validate_share_observations


def get_registered_company(root: Path, company_id: str) -> pd.Series:
    registry = pd.read_csv(root / "config/company_registry.csv", dtype={"bse_scrip": str})
    entry = registry[registry.company_id.astype(str) == str(company_id)]
    if len(entry) != 1:
        raise ValueError(f"Unknown or non-unique registered company '{company_id}'.")
    return entry.iloc[0]


def _read_all_valid_market_observations(root: Path) -> tuple[pd.DataFrame, list[str]]:
    frames: list[pd.DataFrame] = []
    warnings: list[str] = []
    market_dir = root / "data/market"
    if not market_dir.exists():
        return pd.DataFrame(), warnings
    for path in sorted(market_dir.glob("*_market_observations.csv")):
        frame = pd.read_csv(path)
        errors = validate_market_observations(frame)
        if errors:
            warnings.append(f"Ignored {path.relative_to(root)} for peer-price joins: {'; '.join(errors)}")
        else:
            frames.append(frame)
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(), warnings)


def run_registered_company(root: Path, company_id: str) -> dict:
    """Run one registered company entirely from saved source-backed artifacts."""
    entry = get_registered_company(root, company_id)
    records = pd.read_csv(root / entry.source_records_path)
    shares = pd.read_csv(root / entry.share_observations_path)
    assumptions = load_assumptions(root / entry.assumptions_path)
    errors = validate_source_records(records)
    errors += validate_share_observations(shares)
    errors += validate_assumptions(assumptions)
    errors += validate_information_cutoff(records, assumptions.get("information_cutoff", ""))
    if errors:
        raise ValueError("Validation blocks valuation:\n- " + "\n- ".join(errors))
    historical = build_historical(records)
    reconciliations = reconcile_statements(historical)
    readiness = valuation_readiness(
        historical, reconciliations, shares, company_id, assumptions["valuation_date"], assumptions["information_cutoff"],
    )
    if not (reconciliations.status == "pass").all():
        raise ValueError("Valuation blocks: statement reconciliation failed or is unavailable.")
    if (readiness.status == "blocked").any():
        raise ValueError("Valuation blocks: readiness checks are blocked.")
    forecast, summary = run_fcff_valuation(historical, assumptions, shares, company_id)
    market_path = root / "data/market" / f"{company_id}_market_observations.csv"
    market = pd.read_csv(market_path) if market_path.exists() else pd.DataFrame(columns=[])
    share_observation = select_share_observation(shares, company_id, assumptions["valuation_date"], assumptions["information_cutoff"])
    market_result = market_comparison(summary, market, share_observation, company_id, str(entry.bse_scrip).zfill(6))
    peers = pd.read_csv(root / "data/peers/peer_inputs.csv")
    all_market, market_warnings = _read_all_valid_market_observations(root)
    peer_result = peer_comparison(
        peers, company_id, assumptions["valuation_date"], latest_financial_period_end(records), all_market,
        assumptions["information_cutoff"],
    )
    sensitivity_table = sensitivity(historical, assumptions, [0.10, 0.12, 0.14], [0.04, 0.05, 0.06], shares, company_id)
    return {
        "entry": entry.to_dict(), "records": records, "shares": shares, "assumptions": assumptions,
        "historical": historical, "reconciliations": reconciliations, "readiness": readiness,
        "forecast": forecast, "summary": summary, "market_result": market_result,
        "peer_result": peer_result, "sensitivity": sensitivity_table, "market_warnings": market_warnings,
    }
