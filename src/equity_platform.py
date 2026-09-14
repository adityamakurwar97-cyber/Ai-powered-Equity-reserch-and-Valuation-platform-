"""Deterministic, source-backed FCFF utilities for the BSE research platform.

This module deliberately contains no network calls, model calls, or UI concerns.  It is
the reproducible financial-data boundary that a future API, RAG layer, or UI can call.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


SOURCE_RECORD_COLUMNS = {
    "company", "fiscal_year", "field", "raw_value", "raw_unit", "conversion_factor",
    "normalized_value_inr_crore", "period_end", "publication_date", "frequency", "basis", "source_url",
    "report_title", "printed_page", "pdf_page", "retrieval_date", "verification_status", "notes",
}
CRITICAL_FIELDS = {
    "revenue", "operating_ebit", "depreciation_amortization", "capex", "trade_receivables",
    "trade_payables", "cash_and_cash_equivalents", "weighted_average_diluted_shares",
}
RECONCILIATION_FIELDS = {
    "total_assets", "total_equity", "total_liabilities", "cash_flow_operating",
    "cash_flow_investing", "cash_flow_financing", "cash_flow_net_change", "cash_fx_effect",
    "cash_opening", "cash_and_cash_equivalents", "cash_flow_closing_cash_equivalents",
}
REQUIRED_HISTORICAL_YEARS = 3
REQUIRED_ASSUMPTIONS = {
    "wacc", "terminal_growth", "operating_tax_rate", "forecast_growth", "forecast_ebit_margin",
    "forecast_da_ratio", "forecast_capex_ratio", "forecast_nwc_ratio", "valuation_date",
    "information_cutoff",
}
FORECAST_ARRAYS = (
    "forecast_growth", "forecast_ebit_margin", "forecast_da_ratio", "forecast_capex_ratio",
    "forecast_nwc_ratio",
)


def _missing_columns(frame: pd.DataFrame, expected: set[str], label: str) -> list[str]:
    missing = sorted(expected - set(frame.columns))
    return [f"{label} columns missing: {missing}"] if missing else []


def _is_non_blank(value: object) -> bool:
    return pd.notna(value) and bool(str(value).strip())


def _valid_iso_dates(values: pd.Series, label: str, errors: list[str]) -> pd.Series:
    parsed = pd.to_datetime(values, errors="coerce")
    if parsed.isna().any():
        errors.append(f"{label} must contain valid dates.")
    return parsed


def validate_source_record_rows(records: pd.DataFrame) -> list[str]:
    """Validate individual source facts without requiring a full three-year history.

    This is intentionally used by staging.  Full-history validation happens only after
    a staged refresh is combined with the saved source register.
    """
    errors = _missing_columns(records, SOURCE_RECORD_COLUMNS, "Source-record")
    if errors:
        return errors
    if records.empty:
        return ["Source register cannot be empty."]
    if records.duplicated(["company", "fiscal_year", "field", "basis"]).any():
        errors.append("Duplicate company/year/field/basis source records.")
    numeric_columns = ("raw_value", "conversion_factor", "normalized_value_inr_crore")
    numeric: dict[str, pd.Series] = {}
    for column in numeric_columns:
        numeric[column] = pd.to_numeric(records[column], errors="coerce")
        if numeric[column].isna().any() or not np.isfinite(numeric[column]).all():
            errors.append(f"{column} must be finite numeric values.")
    if "conversion_factor" in numeric and (numeric["conversion_factor"] <= 0).any():
        errors.append("Conversion factors must be finite and positive.")
    if all(column in numeric for column in numeric_columns):
        expected = numeric["raw_value"] * numeric["conversion_factor"]
        if not np.allclose(expected, numeric["normalized_value_inr_crore"], rtol=0, atol=1e-6, equal_nan=False):
            errors.append("Raw value × conversion factor does not equal normalised value.")
    fiscal_year = pd.to_numeric(records["fiscal_year"], errors="coerce")
    if fiscal_year.isna().any() or (fiscal_year % 1 != 0).any():
        errors.append("fiscal_year must contain integer years.")
    period_end = _valid_iso_dates(records["period_end"], "period_end", errors)
    publication_date = _valid_iso_dates(records["publication_date"], "publication_date", errors)
    retrieval_date = _valid_iso_dates(records["retrieval_date"], "retrieval_date", errors)
    if not fiscal_year.isna().any() and not period_end.isna().any() and not (period_end.dt.year == fiscal_year.astype(int)).all():
        errors.append("Each period_end year must match fiscal_year.")
    if not period_end.isna().any() and not publication_date.isna().any() and (publication_date < period_end).any():
        errors.append("publication_date cannot precede period_end.")
    if not publication_date.isna().any() and not retrieval_date.isna().any() and (retrieval_date < publication_date).any():
        errors.append("retrieval_date cannot precede publication_date.")
    if not records["frequency"].astype(str).eq("annual").all():
        errors.append("Only annual records are accepted by this model.")
    if not records["basis"].astype(str).eq("consolidated").all():
        errors.append("Only consolidated records are accepted by this model.")
    if not records["verification_status"].astype(str).eq("verified").all():
        errors.append("Every source record must have verification_status=verified before valuation.")
    for column in ("company", "field", "raw_unit", "source_url", "report_title", "notes"):
        if not records[column].map(_is_non_blank).all():
            errors.append(f"{column} cannot be blank.")
    urls = records["source_url"].astype(str)
    if not urls.str.match(r"^https?://", na=False).all():
        errors.append("source_url must be an http(s) URL.")
    if not records["field"].astype(str).str.match(r"^[a-z][a-z0-9_]*$", na=False).all():
        errors.append("field must use lowercase snake_case.")
    return errors


def validate_source_records(records: pd.DataFrame, required_years: int = REQUIRED_HISTORICAL_YEARS) -> list[str]:
    """Validate a complete valuation source register and its historical coverage."""
    errors = validate_source_record_rows(records)
    if errors:
        return errors
    if records["company"].nunique() != 1:
        errors.append("A valuation source register must contain exactly one company.")
    years = sorted(pd.to_numeric(records["fiscal_year"]).astype(int).unique().tolist())
    if len(years) < required_years:
        errors.append(f"At least {required_years} annual fiscal years are required; found {len(years)}.")
    if years and years != list(range(years[0], years[-1] + 1)):
        errors.append("Fiscal years must be consecutive; do not silently bridge missing annual reports.")
    for year, group in records.groupby("fiscal_year"):
        absent = CRITICAL_FIELDS - set(group.field)
        if absent:
            errors.append(f"FY{int(year)} missing critical fields: {sorted(absent)}")
        if group["period_end"].nunique() != 1:
            errors.append(f"FY{int(year)} has more than one period_end in the source register.")
    return errors


def latest_financial_period_end(records: pd.DataFrame) -> str:
    """Return the source-backed period end for the latest fiscal year."""
    errors = validate_source_records(records)
    if errors:
        raise ValueError("Cannot determine latest period end: " + "; ".join(errors))
    latest_year = int(pd.to_numeric(records["fiscal_year"]).max())
    return str(records.loc[records.fiscal_year == latest_year, "period_end"].iloc[0])


def validate_information_cutoff(records: pd.DataFrame, information_cutoff: str) -> list[str]:
    """Prevent report facts published after the stated valuation information cutoff."""
    errors = _missing_columns(records, SOURCE_RECORD_COLUMNS, "Source-record")
    if errors:
        return errors
    cutoff = pd.to_datetime(information_cutoff, errors="coerce")
    publication_dates = pd.to_datetime(records["publication_date"], errors="coerce")
    if pd.isna(cutoff):
        return ["information_cutoff must be a valid date."]
    if publication_dates.isna().any():
        return ["publication_date must contain valid dates before cutoff validation."]
    late = records.loc[publication_dates > cutoff, ["fiscal_year", "field", "publication_date"]]
    if late.empty:
        return []
    details = ", ".join(f"FY{int(row.fiscal_year)} {row.field} ({row.publication_date})" for _, row in late.head(5).iterrows())
    extra = "" if len(late) <= 5 else f" and {len(late) - 5} more"
    return [f"Information cutoff {information_cutoff} excludes source facts published later: {details}{extra}."]


def build_historical(records: pd.DataFrame) -> pd.DataFrame:
    errors = validate_source_records(records)
    if errors:
        raise ValueError("Validation blocks valuation:\n- " + "\n- ".join(errors))
    values = records.pivot(index="fiscal_year", columns="field", values="normalized_value_inr_crore").sort_index()
    values["operating_nwc"] = values.trade_receivables - values.trade_payables
    values["change_operating_nwc"] = values.operating_nwc.diff()
    values["ebit_margin"] = values.operating_ebit / values.revenue
    values["capex_ratio"] = values.capex / values.revenue
    values["da_ratio"] = values.depreciation_amortization / values.revenue
    # Source register already normalises shares into crore shares (raw shares / 10,000,000).
    values["shares_crore"] = values.weighted_average_diluted_shares
    return values.reset_index()


def _check(name: str, lhs: float, rhs: float, tolerance: float, reason: str = "") -> dict:
    if not (np.isfinite(lhs) and np.isfinite(rhs)):
        return {
            "check": name, "status": "unavailable", "residual_inr_crore": np.nan,
            "tolerance_inr_crore": tolerance, "reason": reason or "Required source line unavailable.",
        }
    residual = lhs - rhs
    return {
        "check": name, "status": "pass" if abs(residual) <= tolerance else "fail",
        "residual_inr_crore": residual, "tolerance_inr_crore": tolerance,
        "reason": reason or "Rounded INR-crore statement comparison.",
    }


def reconcile_statements(historical: pd.DataFrame, tolerance: float = 1.0) -> pd.DataFrame:
    """Reconcile source-backed statement totals; never use a balancing plug."""
    rows = []
    for _, row in historical.sort_values("fiscal_year").iterrows():
        year = int(row.fiscal_year)
        get = lambda name: float(row[name]) if name in row.index and pd.notna(row[name]) else np.nan
        checks = [
            _check("assets = equity + liabilities", get("total_assets"), get("total_equity") + get("total_liabilities"), tolerance),
            _check("operating + investing + financing = reported net cash change", get("cash_flow_operating") + get("cash_flow_investing") + get("cash_flow_financing"), get("cash_flow_net_change"), tolerance),
            _check("opening cash + net cash change + FX = closing cash", get("cash_opening") + get("cash_flow_net_change") + get("cash_fx_effect"), get("cash_flow_closing_cash_equivalents"), tolerance),
            _check("cash-flow closing cash equivalents = balance-sheet cash equivalents", get("cash_flow_closing_cash_equivalents"), get("cash_and_cash_equivalents"), tolerance, "Restricted cash is separately reported and excluded from both cash-equivalent values."),
        ]
        rows.extend({"fiscal_year": year, **check} for check in checks)
    return pd.DataFrame(rows)


def validate_assumptions(assumptions: dict) -> list[str]:
    """Reject incomplete or internally inconsistent FCFF assumptions before calculation."""
    if not isinstance(assumptions, dict):
        return ["Assumptions must be a JSON object."]
    errors = []
    missing = sorted(REQUIRED_ASSUMPTIONS - set(assumptions))
    if missing:
        return [f"Missing assumption(s): {missing}"]
    scalar_names = ("wacc", "terminal_growth", "operating_tax_rate", "debt", "excess_cash", "lease_liabilities", "non_controlling_interest")
    scalars: dict[str, float] = {}
    for name in scalar_names:
        if name not in assumptions:
            continue
        try:
            scalars[name] = float(assumptions[name])
        except (TypeError, ValueError):
            errors.append(f"{name} must be numeric.")
            continue
        if not np.isfinite(scalars[name]):
            errors.append(f"{name} must be finite.")
    if not errors:
        if not 0 <= scalars["operating_tax_rate"] <= 1:
            errors.append("operating_tax_rate must be between 0 and 1.")
        if not 0 < scalars["wacc"] < 1:
            errors.append("wacc must be between 0 and 1.")
        if not -1 < scalars["terminal_growth"] < scalars["wacc"]:
            errors.append("terminal_growth must be greater than -100% and lower than wacc.")
        for name in ("debt", "lease_liabilities", "non_controlling_interest"):
            if name in scalars and scalars[name] < 0:
                errors.append(f"{name} cannot be negative.")
    lengths = []
    vectors: dict[str, list[float]] = {}
    for name in FORECAST_ARRAYS:
        value = assumptions[name]
        if not isinstance(value, list) or not value:
            errors.append(f"{name} must be a non-empty list.")
            continue
        try:
            vector = [float(item) for item in value]
        except (TypeError, ValueError):
            errors.append(f"{name} must contain numeric values.")
            continue
        if not np.isfinite(vector).all():
            errors.append(f"{name} must contain finite values.")
            continue
        vectors[name] = vector
        lengths.append(len(vector))
    if lengths and len(set(lengths)) != 1:
        errors.append("All forecast arrays must have the same length; silent zip truncation is not allowed.")
    if "forecast_growth" in vectors and any(value <= -1 for value in vectors["forecast_growth"]):
        errors.append("forecast_growth values must be greater than -100%.")
    if "forecast_ebit_margin" in vectors and any(not -1 <= value <= 1 for value in vectors["forecast_ebit_margin"]):
        errors.append("forecast_ebit_margin values must be between -100% and 100%.")
    for name in ("forecast_da_ratio", "forecast_capex_ratio"):
        if name in vectors and any(value < 0 for value in vectors[name]):
            errors.append(f"{name} cannot contain negative values.")
    valuation_date = _valid_iso_dates(pd.Series([assumptions["valuation_date"]]), "valuation_date", errors)
    cutoff = _valid_iso_dates(pd.Series([assumptions["information_cutoff"]]), "information_cutoff", errors)
    if not valuation_date.isna().any() and not cutoff.isna().any() and cutoff.iloc[0] < valuation_date.iloc[0]:
        errors.append("information_cutoff cannot precede valuation_date.")
    return errors


def resolve_valuation_shares(historical: pd.DataFrame, share_observations: pd.DataFrame | None = None, company_id: str | None = None, valuation_date: str | None = None, information_cutoff: str | None = None) -> float:
    if share_observations is not None:
        if not company_id or not valuation_date:
            raise ValueError("Valuation is blocked: company_id and valuation_date are required for dated share observations.")
        from market_data import select_share_observation
        observation = select_share_observation(share_observations, company_id, valuation_date, information_cutoff)
        if str(observation.fully_diluted_period_end_status) == "verified":
            return float(observation.fully_diluted_period_end_crore)
        return float(observation.net_outstanding_crore)
    base = historical.sort_values("fiscal_year").iloc[-1]
    needed = ["period_end_paid_up_shares", "treasury_shares"]
    missing = [name for name in needed if name not in base.index or pd.isna(base[name])]
    if missing:
        raise ValueError("Valuation is blocked: dated period-end share inputs missing: " + ", ".join(missing))
    shares = float(base.period_end_paid_up_shares - base.treasury_shares)
    if not np.isfinite(shares) or shares <= 0:
        raise ValueError("Valuation is blocked: invalid period-end shares net of treasury shares.")
    return shares


def valuation_readiness(historical: pd.DataFrame, reconciliations: pd.DataFrame, share_observations: pd.DataFrame | None = None, company_id: str | None = None, valuation_date: str | None = None, information_cutoff: str | None = None) -> pd.DataFrame:
    rec_status = "pass" if not reconciliations.empty and (reconciliations.status == "pass").all() else "blocked"
    try:
        resolve_valuation_shares(historical, share_observations, company_id, valuation_date, information_cutoff)
        share_status = "pass"
        share_note = "Dated period-end net outstanding shares."
        if share_observations is not None:
            from market_data import select_share_observation
            share = select_share_observation(share_observations, company_id or "", valuation_date or "", information_cutoff)
            if str(share.fully_diluted_period_end_status) != "verified":
                share_status = "warning"
                share_note = "Period-end net shares are verified, but fully diluted period-end awards are unavailable; intrinsic value is provisional."
    except ValueError as exc:
        share_status, share_note = "blocked", str(exc)
    return pd.DataFrame([
        {"area": "financial_data_validation", "status": "pass", "detail": "Source-record validation passed."},
        {"area": "statement_reconciliation", "status": rec_status, "detail": "All required statement checks must pass before valuation."},
        {"area": "share_denominator", "status": share_status, "detail": share_note},
        {"area": "market_comparison", "status": "unavailable", "detail": "A direct BSE close on the valuation/share date is required before market cap or upside/downside is calculated."},
    ])


def run_fcff_valuation(historical: pd.DataFrame, assumptions: dict, share_observations: pd.DataFrame | None = None, company_id: str | None = None) -> tuple[pd.DataFrame, dict]:
    assumption_errors = validate_assumptions(assumptions)
    if assumption_errors:
        raise ValueError("Valuation is blocked: " + "; ".join(assumption_errors))
    wacc, growth = float(assumptions["wacc"]), float(assumptions["terminal_growth"])
    base = historical.sort_values("fiscal_year").iloc[-1]
    reconciliation = reconcile_statements(historical)
    failed = reconciliation[reconciliation.status != "pass"]
    if not failed.empty:
        raise ValueError("Valuation is blocked: statement reconciliation has failed or unavailable checks: " + ", ".join(failed.check.tolist()))
    shares_crore = resolve_valuation_shares(historical, share_observations, company_id, assumptions["valuation_date"], assumptions["information_cutoff"])
    horizon = len(assumptions["forecast_growth"])
    years = list(range(int(base.fiscal_year) + 1, int(base.fiscal_year) + 1 + horizon))
    prev_revenue, prev_nwc, rows = float(base.revenue), float(base.operating_nwc), []
    for period, (year, revenue_growth, margin, da_ratio, capex_ratio, nwc_ratio) in enumerate(zip(years, assumptions["forecast_growth"], assumptions["forecast_ebit_margin"], assumptions["forecast_da_ratio"], assumptions["forecast_capex_ratio"], assumptions["forecast_nwc_ratio"]), 1):
        revenue = prev_revenue * (1 + float(revenue_growth))
        ebit = revenue * float(margin)
        da = revenue * float(da_ratio)
        capex = revenue * float(capex_ratio)
        nwc = revenue * float(nwc_ratio)
        delta_nwc = nwc - prev_nwc
        fcff = ebit * (1 - float(assumptions["operating_tax_rate"])) + da - capex - delta_nwc
        rows.append({
            "fiscal_year": year, "period": period, "revenue": revenue, "operating_ebit": ebit, "da": da,
            "capex": capex, "operating_nwc": nwc, "change_operating_nwc": delta_nwc, "fcff": fcff,
            "discount_factor": 1 / (1 + wacc) ** period, "pv_fcff": fcff / (1 + wacc) ** period,
        })
        prev_revenue, prev_nwc = revenue, nwc
    forecast = pd.DataFrame(rows)
    terminal_fcff = float(forecast.iloc[-1].fcff) * (1 + growth)
    terminal_value = terminal_fcff / (wacc - growth)
    pv_terminal = terminal_value * float(forecast.iloc[-1].discount_factor)
    enterprise_value = float(forecast.pv_fcff.sum()) + pv_terminal
    # Cash and investments are deliberately excluded: excess/distributable cash needs a separate documented decision.
    lease_liabilities = float(assumptions.get("lease_liabilities", base.get("lease_liabilities", 0)))
    non_controlling_interest = float(assumptions.get("non_controlling_interest", base.get("non_controlling_interest", 0)))
    equity_value = enterprise_value - float(assumptions.get("debt", 0)) - lease_liabilities - non_controlling_interest + float(assumptions.get("excess_cash", 0))
    denominator_method = "FY26 period-end paid-up shares less treasury shares"
    dilution_status = "not_applicable_to_legacy_mode"
    if share_observations is not None:
        from market_data import select_share_observation
        share = select_share_observation(share_observations, company_id or "", assumptions["valuation_date"], assumptions["information_cutoff"])
        denominator_method = str(share.denominator_method)
        dilution_status = str(share.fully_diluted_period_end_status)
    valuation_status = "ready" if dilution_status in {"verified", "not_applicable_to_legacy_mode"} else "provisional_period_end_net_shares"
    summary = {
        "valuation_schema_version": "1.0", "valuation_date": assumptions["valuation_date"],
        "information_cutoff": assumptions["information_cutoff"], "valuation_status": valuation_status,
        "pv_forecast_fcff_inr_crore": float(forecast.pv_fcff.sum()), "pv_terminal_value_inr_crore": pv_terminal,
        "enterprise_value_inr_crore": enterprise_value, "equity_value_inr_crore": equity_value,
        "shares_crore": shares_crore, "value_per_share_inr": equity_value / shares_crore,
        "share_denominator_method": denominator_method, "fully_diluted_period_end_status": dilution_status,
    }
    return forecast, summary


def sensitivity(historical: pd.DataFrame, assumptions: dict, wacc_values: list[float], growth_values: list[float], share_observations: pd.DataFrame | None = None, company_id: str | None = None) -> pd.DataFrame:
    assumption_errors = validate_assumptions(assumptions)
    if assumption_errors:
        raise ValueError("Sensitivity is blocked: " + "; ".join(assumption_errors))
    table = pd.DataFrame(index=[f"{value:.1%}" for value in wacc_values], columns=[f"{value:.1%}" for value in growth_values], dtype=float)
    for wacc in wacc_values:
        for growth in growth_values:
            table.loc[f"{wacc:.1%}", f"{growth:.1%}"] = np.nan if wacc <= growth else run_fcff_valuation(historical, {**assumptions, "wacc": wacc, "terminal_growth": growth}, share_observations, company_id)[1]["value_per_share_inr"]
    return table


def load_assumptions(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())
