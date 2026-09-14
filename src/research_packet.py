"""Create a citation-preserving, deterministic research packet for future consumers."""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


RESEARCH_PACKET_SCHEMA_VERSION = "1.0"


def _json_value(value: Any) -> Any:
    if value is None or value is pd.NA:
        return None
    if isinstance(value, (float, np.floating)):
        return None if not math.isfinite(float(value)) else float(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.date().isoformat()
    return value


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [{str(key): _json_value(value) for key, value in row.items()} for row in frame.to_dict(orient="records")]


def _source_documents(records: pd.DataFrame) -> list[dict[str, Any]]:
    columns = ["source_url", "report_title", "publication_date", "retrieval_date", "printed_page", "pdf_page"]
    docs = records[columns].drop_duplicates().sort_values(["publication_date", "source_url"])
    return _records(docs)


def build_research_packet(run: dict, manifest: dict | None = None) -> dict[str, Any]:
    """Return facts, calculations, and availability—not generated analyst narrative."""
    summary = {key: _json_value(value) for key, value in run["summary"].items()}
    market = {key: _json_value(value) for key, value in run["market_result"].items()}
    peer_records = _records(run["peer_result"])
    blockers = []
    if summary.get("valuation_status") != "ready":
        blockers.append("A verified fully diluted period-end share denominator is not yet saved.")
    if market.get("status") != "pass":
        blockers.append(str(market.get("reason", "A compatible direct BSE close is unavailable.")))
    if any(row.get("status") != "pass" for row in peer_records):
        blockers.append("One or more peers lack a same-date verified direct BSE close.")
    return {
        "schema_version": RESEARCH_PACKET_SCHEMA_VERSION,
        "purpose": "Deterministic, source-backed research packet. It contains no LLM-generated conclusions.",
        "not_investment_advice": True,
        "company": run["entry"],
        "valuation": summary,
        "readiness": _records(run["readiness"]),
        "historical_financials_inr_crore": _records(run["historical"]),
        "forecast_inr_crore": _records(run["forecast"]),
        "reconciliations": _records(run["reconciliations"]),
        "market_comparison": market,
        "peer_comparison": peer_records,
        "sensitivity_value_per_share_inr": _records(run["sensitivity"].reset_index().rename(columns={"index": "wacc"})),
        "source_documents": _source_documents(run["records"]),
        "source_facts": _records(run["records"]),
        "share_observations": _records(run["shares"]),
        "real_data_blockers": blockers,
        "non_blocking_data_warnings": run["market_warnings"],
        "input_manifest": manifest or {},
    }
