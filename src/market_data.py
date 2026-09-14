"""Saved market, peer and dated-share controls for the deterministic core.

No price is fetched from the network here.  The functions only validate and join
saved, traceable observations so a future backend has a safe data boundary.
"""
from __future__ import annotations

from urllib.parse import urlparse

import numpy as np
import pandas as pd


MARKET_COLUMNS = {
    "company_id", "bse_scrip", "observation_date", "observation_time_ist", "close_price_inr",
    "currency", "market_cap_inr_crore", "price_method", "source_url", "source_artifact",
    "source_file_sha256", "retrieval_date", "verification_status", "notes",
}
SHARE_COLUMNS = {
    "company_id", "effective_date", "publication_date", "net_outstanding_shares",
    "net_outstanding_crore", "treasury_shares", "treasury_shares_crore",
    "diluted_weighted_average_shares", "fully_diluted_period_end_shares",
    "fully_diluted_period_end_crore", "fully_diluted_period_end_status", "denominator_method",
    "source_url", "dilution_source_url", "report_title", "pdf_page", "retrieval_date",
    "verification_status", "notes",
}
PEER_COLUMNS = {
    "company_id", "peer_company", "peer_bse_scrip", "metric", "metric_value", "currency",
    "financial_period_end", "market_observation_date", "publication_date", "definition",
    "source_url", "verification_status", "notes", "price_method",
}
PEER_FINANCIAL_METRICS = {"revenue_inr_crore", "ebit_inr_crore", "net_income_inr_crore"}
PEER_PRICE_METRIC = "bse_close_price_inr"


def _validate_columns(frame: pd.DataFrame, expected: set[str], label: str) -> list[str]:
    missing = sorted(expected - set(frame.columns))
    return [f"{label} columns missing: {missing}"] if missing else []


def _non_blank(value: object) -> bool:
    return pd.notna(value) and bool(str(value).strip())


def _parse_dates(values: pd.Series, label: str, errors: list[str], allow_blank: bool = False) -> pd.Series:
    blank = values.isna() | values.astype(str).str.strip().eq("")
    parsed = pd.to_datetime(values.where(~blank), errors="coerce")
    invalid = parsed.isna() & ~blank
    if invalid.any() or (blank.any() and not allow_blank):
        errors.append(f"{label} must contain valid dates.")
    return parsed


def _normalised_scrip(values: pd.Series) -> pd.Series:
    return values.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)


def _valid_source_url(values: pd.Series) -> bool:
    return values.map(_non_blank).all() and values.astype(str).str.match(r"^https?://", na=False).all()


def validate_market_observations(frame: pd.DataFrame, expected_company_id: str | None = None, expected_bse_scrip: str | None = None) -> list[str]:
    errors = _validate_columns(frame, MARKET_COLUMNS, "Market observation")
    if errors:
        return errors
    if frame.empty:
        return ["No market observations saved."]
    prices = pd.to_numeric(frame.close_price_inr, errors="coerce")
    if prices.isna().any() or not np.isfinite(prices).all() or (prices <= 0).any():
        errors.append("Close price must be finite and positive.")
    if not frame.currency.astype(str).eq("INR").all():
        errors.append("Market observations must use INR.")
    if frame.company_id.map(_non_blank).eq(False).any():
        errors.append("company_id cannot be blank.")
    scrips = _normalised_scrip(frame.bse_scrip)
    if not scrips.str.fullmatch(r"\d{6}").all():
        errors.append("BSE scrip codes must be six digits.")
    if expected_company_id is not None and set(frame.company_id.astype(str)) != {str(expected_company_id)}:
        errors.append("Market observations do not match the requested company_id.")
    if expected_bse_scrip is not None and not scrips.eq(str(expected_bse_scrip).zfill(6)).all():
        errors.append("Market observations do not match the registered BSE scrip.")
    observation_date = _parse_dates(frame.observation_date, "observation_date", errors)
    retrieval_date = _parse_dates(frame.retrieval_date, "retrieval_date", errors)
    if not observation_date.isna().any() and not retrieval_date.isna().any() and (retrieval_date < observation_date).any():
        errors.append("retrieval_date cannot precede observation_date.")
    if not _valid_source_url(frame.source_url):
        errors.append("source_url must be a non-blank http(s) URL.")
    if frame.duplicated(["company_id", "observation_date", "observation_time_ist", "price_method"]).any():
        errors.append("Duplicate market observations with the same method.")
    direct = frame.price_method.astype(str).eq("direct_bse_close")
    if direct.any():
        direct_rows = frame.loc[direct]
        if not direct_rows.verification_status.astype(str).eq("verified").all():
            errors.append("Direct BSE closes require verification_status=verified.")
        if not direct_rows.observation_time_ist.astype(str).eq("close").all():
            errors.append("Direct BSE closes must use observation_time_ist=close.")
        if not direct_rows.source_artifact.map(_non_blank).all():
            errors.append("Direct BSE closes require a source_artifact filename.")
        if not direct_rows.source_file_sha256.astype(str).str.fullmatch(r"[a-f0-9]{64}", case=False).all():
            errors.append("Direct BSE closes require a SHA-256 source-file fingerprint.")
        hosts = direct_rows.source_url.astype(str).map(lambda url: urlparse(url).hostname or "")
        if not hosts.map(lambda host: host == "bseindia.com" or host.endswith(".bseindia.com")).all():
            errors.append("Direct BSE closes must cite a bseindia.com source URL.")
    return errors


def validate_share_observations(frame: pd.DataFrame) -> list[str]:
    errors = _validate_columns(frame, SHARE_COLUMNS, "Share observation")
    if errors:
        return errors
    if frame.empty:
        return ["No dated share observations saved."]
    net_shares = pd.to_numeric(frame.net_outstanding_shares, errors="coerce")
    net_crore = pd.to_numeric(frame.net_outstanding_crore, errors="coerce")
    treasury_shares = pd.to_numeric(frame.treasury_shares, errors="coerce")
    treasury_crore = pd.to_numeric(frame.treasury_shares_crore, errors="coerce")
    if net_shares.isna().any() or net_crore.isna().any() or not np.allclose(net_shares / 10_000_000, net_crore, rtol=0, atol=1e-6):
        errors.append("Net share-unit conversion is inconsistent.")
    if treasury_shares.isna().any() or treasury_crore.isna().any() or not np.allclose(treasury_shares / 10_000_000, treasury_crore, rtol=0, atol=1e-6):
        errors.append("Treasury-share unit conversion is inconsistent.")
    if net_crore.isna().any() or not np.isfinite(net_crore).all() or (net_crore <= 0).any():
        errors.append("Net outstanding shares must be finite and positive.")
    if treasury_crore.isna().any() or not np.isfinite(treasury_crore).all() or (treasury_crore < 0).any():
        errors.append("Treasury shares must be finite and non-negative.")
    if frame.company_id.map(_non_blank).eq(False).any():
        errors.append("company_id cannot be blank.")
    effective_date = _parse_dates(frame.effective_date, "effective_date", errors)
    publication_date = _parse_dates(frame.publication_date, "publication_date", errors)
    retrieval_date = _parse_dates(frame.retrieval_date, "retrieval_date", errors)
    if not effective_date.isna().any() and not publication_date.isna().any() and (publication_date < effective_date).any():
        errors.append("publication_date cannot precede effective_date.")
    if not publication_date.isna().any() and not retrieval_date.isna().any() and (retrieval_date < publication_date).any():
        errors.append("retrieval_date cannot precede publication_date.")
    if not _valid_source_url(frame.source_url):
        errors.append("source_url must be a non-blank http(s) URL.")
    if frame.duplicated(["company_id", "effective_date"]).any():
        errors.append("Duplicate dated share observations.")
    if not frame.verification_status.astype(str).eq("verified").all():
        errors.append("Share observations must have verification_status=verified.")
    verified = frame.fully_diluted_period_end_status.astype(str).eq("verified")
    unavailable = frame.fully_diluted_period_end_status.astype(str).eq("unavailable")
    if (~(verified | unavailable)).any():
        errors.append("fully_diluted_period_end_status must be verified or unavailable.")
    if verified.any():
        values = pd.to_numeric(frame.loc[verified, "fully_diluted_period_end_shares"], errors="coerce")
        crores = pd.to_numeric(frame.loc[verified, "fully_diluted_period_end_crore"], errors="coerce")
        if values.isna().any() or crores.isna().any() or (values <= 0).any():
            errors.append("Verified fully diluted period-end observations need positive share counts.")
        elif not np.allclose(values / 10_000_000, crores, rtol=0, atol=1e-6):
            errors.append("Fully diluted share-unit conversion is inconsistent.")
        elif (crores.to_numpy() < net_crore.loc[verified].to_numpy()).any():
            errors.append("Fully diluted period-end shares cannot be below net outstanding shares.")
        if not _valid_source_url(frame.loc[verified, "dilution_source_url"]):
            errors.append("Verified fully diluted period-end shares require a dilution_source_url.")
    if unavailable.any() and (frame.loc[unavailable, "fully_diluted_period_end_shares"].notna().any() or frame.loc[unavailable, "fully_diluted_period_end_crore"].notna().any()):
        errors.append("Unavailable fully diluted observations cannot contain a denominator.")
    return errors


def select_share_observation(frame: pd.DataFrame, company_id: str, valuation_date: str, information_cutoff: str | None = None) -> pd.Series:
    errors = validate_share_observations(frame)
    if errors:
        raise ValueError("Share denominator is blocked: " + "; ".join(errors))
    match = frame[(frame.company_id.astype(str) == str(company_id)) & (frame.effective_date.astype(str) == str(valuation_date))]
    if len(match) != 1:
        raise ValueError(f"Share denominator is blocked: need exactly one dated share observation for {company_id} on {valuation_date}.")
    observation = match.iloc[0]
    if information_cutoff is not None and pd.Timestamp(observation.publication_date) > pd.Timestamp(information_cutoff):
        raise ValueError("Share denominator is blocked: its publication_date is later than the information cutoff.")
    return observation


def market_comparison(valuation: dict, market: pd.DataFrame, share_observation: pd.Series, company_id: str, expected_bse_scrip: str | None = None) -> dict:
    errors = validate_market_observations(market, expected_company_id=company_id, expected_bse_scrip=expected_bse_scrip)
    if errors:
        return {"status": "unavailable", "reason": "; ".join(errors)}
    date = str(share_observation.effective_date)
    if str(valuation.get("valuation_date")) != date:
        return {"status": "unavailable", "reason": "Valuation date and dated share observation differ."}
    matching_date = market[(market.company_id.astype(str) == str(company_id)) & (market.observation_date.astype(str) == date)]
    direct = matching_date[
        matching_date.price_method.astype(str).eq("direct_bse_close")
        & matching_date.verification_status.astype(str).eq("verified")
        & matching_date.observation_time_ist.astype(str).eq("close")
    ]
    if direct.empty:
        return {"status": "unavailable", "reason": "A direct BSE closing price on the dated share basis is required; derived or secondary observations are context only."}
    if len(direct) != 1:
        return {"status": "unavailable", "reason": "More than one verified direct BSE close exists for the valuation date; resolve the duplicate source."}
    row = direct.iloc[0]
    net_market_cap = float(row.close_price_inr) * float(share_observation.net_outstanding_crore)
    valuation_denominator_value = float(row.close_price_inr) * float(valuation["shares_crore"])
    upside = float(valuation["value_per_share_inr"]) / float(row.close_price_inr) - 1
    return {
        "status": "pass", "observation_date": date, "market_price_inr": float(row.close_price_inr),
        "market_cap_inr_crore": net_market_cap, "market_cap_basis": "period_end_net_outstanding_shares",
        "market_price_implied_equity_value_on_valuation_denominator_inr_crore": valuation_denominator_value,
        "intrinsic_value_inr": float(valuation["value_per_share_inr"]),
        "implied_upside_downside_pct": upside * 100, "price_method": str(row.price_method),
        "source_url": str(row.source_url), "source_file_sha256": str(row.source_file_sha256),
    }


def validate_peer_inputs(frame: pd.DataFrame) -> list[str]:
    errors = _validate_columns(frame, PEER_COLUMNS, "Peer input")
    if errors:
        return errors
    if frame.empty:
        return []
    metric_values = pd.to_numeric(frame.metric_value, errors="coerce")
    if metric_values.isna().any() or not np.isfinite(metric_values).all():
        errors.append("Peer metric_value must be finite numeric values.")
    if not frame.company_id.map(_non_blank).all() or not frame.peer_company.map(_non_blank).all():
        errors.append("Peer company identifiers cannot be blank.")
    if not _normalised_scrip(frame.peer_bse_scrip).str.fullmatch(r"\d{6}").all():
        errors.append("Peer BSE scrip codes must be six digits.")
    financial = frame.metric.astype(str).isin(PEER_FINANCIAL_METRICS)
    if financial.any():
        _parse_dates(frame.loc[financial, "financial_period_end"], "Peer financial_period_end", errors)
        _parse_dates(frame.loc[financial, "publication_date"], "Peer publication_date", errors)
        if not frame.loc[financial, "currency"].astype(str).eq("INR").all():
            errors.append("Peer financial metrics must use INR.")
    price = frame.metric.astype(str).eq(PEER_PRICE_METRIC)
    if price.any():
        _parse_dates(frame.loc[price, "market_observation_date"], "Peer market_observation_date", errors)
        if not frame.loc[price, "price_method"].astype(str).eq("direct_bse_close").all():
            errors.append("Peer price metrics must be direct_bse_close.")
    if not frame.verification_status.astype(str).eq("verified").all():
        errors.append("Peer inputs must have verification_status=verified.")
    if not _valid_source_url(frame.source_url):
        errors.append("Peer source_url must be a non-blank http(s) URL.")
    if not frame.definition.map(_non_blank).all() or not frame.notes.map(_non_blank).all():
        errors.append("Peer definition and notes cannot be blank.")
    if frame.duplicated(["company_id", "peer_bse_scrip", "metric", "financial_period_end", "market_observation_date"]).any():
        errors.append("Duplicate peer metrics are not allowed.")
    return errors


def _find_direct_peer_price(market_observations: pd.DataFrame | None, peer_scrip: str, valuation_date: str) -> pd.Series | None:
    if market_observations is None or market_observations.empty:
        return None
    if _validate_columns(market_observations, MARKET_COLUMNS, "Market observation"):
        return None
    rows = market_observations[
        _normalised_scrip(market_observations.bse_scrip).eq(str(peer_scrip).zfill(6))
        & market_observations.observation_date.astype(str).eq(str(valuation_date))
        & market_observations.price_method.astype(str).eq("direct_bse_close")
        & market_observations.observation_time_ist.astype(str).eq("close")
        & market_observations.verification_status.astype(str).eq("verified")
    ]
    return rows.iloc[0] if len(rows) == 1 else None


def peer_comparison(peer_inputs: pd.DataFrame, company_id: str, valuation_date: str, financial_period_end: str | None = None, market_observations: pd.DataFrame | None = None, information_cutoff: str | None = None) -> pd.DataFrame:
    errors = validate_peer_inputs(peer_inputs)
    if errors:
        return pd.DataFrame([{ "status": "unavailable", "reason": "; ".join(errors)}])
    rows = peer_inputs[peer_inputs.company_id.astype(str) == str(company_id)].copy()
    if rows.empty:
        return pd.DataFrame([{ "status": "unavailable", "reason": "No verified peer inputs saved; peer comparison is intentionally withheld."}])
    output = []
    for peer, group in rows.groupby(["peer_company", "peer_bse_scrip"], dropna=False):
        values = {str(row.metric): row for _, row in group.iterrows()}
        missing = PEER_FINANCIAL_METRICS - set(values)
        financial_rows = [values[metric] for metric in PEER_FINANCIAL_METRICS if metric in values]
        target_period = financial_period_end or (str(financial_rows[0].financial_period_end) if financial_rows else "")
        financial_ok = not missing and all(
            str(row.currency) == "INR" and str(row.financial_period_end) == target_period and str(row.verification_status) == "verified"
            for row in financial_rows
        )
        cutoff_ok = information_cutoff is None or all(pd.Timestamp(row.publication_date) <= pd.Timestamp(information_cutoff) for row in financial_rows)
        market_price = _find_direct_peer_price(market_observations, str(peer[1]), valuation_date)
        if financial_ok and cutoff_ok and market_price is not None:
            status, reason = "pass", "Matching fiscal-period INR fundamentals and a same-date direct BSE close are verified."
        elif not financial_ok:
            status, reason = "unavailable", "Peer requires verified INR revenue, EBIT and net income for the target fiscal period."
        elif not cutoff_ok:
            status, reason = "unavailable", "Peer fundamental source was published after the information cutoff."
        else:
            status, reason = "unavailable", "Peer fundamentals are verified; a same-date direct BSE closing price is still required."
        revenue = float(values["revenue_inr_crore"].metric_value) if "revenue_inr_crore" in values else np.nan
        ebit = float(values["ebit_inr_crore"].metric_value) if "ebit_inr_crore" in values else np.nan
        net_income = float(values["net_income_inr_crore"].metric_value) if "net_income_inr_crore" in values else np.nan
        output.append({
            "peer_company": peer[0], "peer_bse_scrip": _normalised_scrip(pd.Series([peer[1]])).iloc[0],
            "financial_period_end": target_period, "status": status, "reason": reason,
            "revenue_inr_crore": revenue, "ebit_inr_crore": ebit, "net_income_inr_crore": net_income,
            "ebit_margin_pct": ebit / revenue * 100 if revenue else np.nan,
            "net_margin_pct": net_income / revenue * 100 if revenue else np.nan,
            "market_price_inr": float(market_price.close_price_inr) if market_price is not None else np.nan,
            "market_observation_date": str(market_price.observation_date) if market_price is not None else pd.NA,
            "market_price_source_url": str(market_price.source_url) if market_price is not None else pd.NA,
        })
    return pd.DataFrame(output)
