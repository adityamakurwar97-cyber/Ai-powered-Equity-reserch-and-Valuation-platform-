# Market, shares, peers and multi-company guide

## Dated market prices

The model accepts only a `direct_bse_close` saved in `data/market/<company_id>_market_observations.csv` for market-cap and upside/downside calculations. The price date must exactly equal the effective date of the dated share observation and the valuation date. If any of those disagree, `market_comparison` returns `unavailable`; intrinsic valuation still runs from saved fundamentals.

The currently saved Infosys 30 June 2026 price is **derived from the company's same-date disclosed market capitalisation and gross share count**, not a direct BSE close. It proves the data schema and is intentionally blocked from comparison output.

### Historical BSE import

Download the official BSE Equity Bhav Copy. The direct importer verifies the registered scrip, a date token in the filename, a BSE URL and the file's SHA-256 fingerprint before saving the `CLOSE` value:

```bash
python scripts/import_bse_bhavcopy.py --company infosys --date 2026-06-30 --bhavcopy /absolute/path/BSE_EQ_BHAVCOPY_20260630.csv --source-url 'https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx'
```

The importer rejects duplicate direct closes, non-INR prices, an unmatched scrip/date, missing BSE provenance and unreviewed snapshots. A derived/secondary context record can coexist on the same date without blocking the verified direct close. `scripts/check_bse_live_access.py --scrip 500209` is a non-bypass diagnostic only: it makes an ordinary public request and records unavailability if BSE denies it. No credentials, special headers or paid feed are used.

## Current shares and dilution

The active Infosys denominator is 404.964581 crore **period-end net outstanding shares on 30 June 2026**. It comes from the official Q1 FY27 IFRS balance sheet: issued/outstanding shares net of treasury shares. The file retains a quarterly diluted weighted-average EPS count for reference, but it is not substituted for period-end fully diluted shares.

`fully_diluted_period_end_status=unavailable` means exactly that: the model can compute a **provisional** period-end net-share intrinsic value, but labels it as not fully diluted. A later official award schedule can be added only with its publication date, award-note URL and a documented period-end incremental-share calculation. When status is `verified`, the valuation automatically switches to its fully diluted denominator; market cap remains clearly labelled on the normal net-outstanding-share basis.

## Peer comparison

`data/peers/peer_inputs.csv` contains verified FY26 INR fundamentals for TCS, HCLTech and Wipro. The peer module requires the same fiscal period as the active company, a source published by the information cutoff, and a verified direct BSE close on the valuation date. It joins price files from `data/market/<peer_company_id>_market_observations.csv` by BSE scrip and date. It otherwise returns `unavailable` instead of computing misleading multiples.

## Add another BSE company

```bash
python scripts/create_company_workspace.py \
  --company-id example --company "Example Limited" --bse-scrip 500000 \
  --isin INE000A01000 --sector "Example sector"
```

This creates empty source/share files, a company-specific assumption template and a `scaffolded` company-universe row. It does **not** add an active registry entry. Add three or more reviewed annual periods, a dated share record, publication-date controls and approved company-specific assumptions. Then activate it:

```bash
python scripts/activate_company.py --company example
python scripts/run_model.py --company example
```

## Annual report refresh

Structured manual import is intentional: annual-report table layouts change and silent OCR/extraction mistakes are costly. Use `scripts/stage_annual_refresh.py --company <id> --input <source-records.csv>` to validate and stage records. It will not alter saved facts without `--approve`, and approval rejects duplicate company/year/field/basis rows.
