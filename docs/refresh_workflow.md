# Safe refresh workflow

The normal model never calls a web scraper. It runs from saved source-backed files, which keeps a valuation reproducible and prevents a blocked website from silently changing output.

## Annual financial data

1. Download an official annual report or exchange filing through an authorised route.
2. Transcribe each reviewed observation to the project source-record schema, including URL, report/page, period, **publication date**, retrieval date, unit, basis and verification status. The publication date must be on or before the valuation information cutoff.
3. Stage it:

```bash
python scripts/stage_annual_refresh.py --company infosys --input /absolute/path/new_report_rows.csv
```

4. Inspect the staged CSV and page references. Only then run the command again with `--approve`.

Staging validates the submitted rows and approval validates the complete combined three-year register. Approval rejects duplicate company/year/field/basis records so prior facts cannot be silently overwritten. A restatement must be retained as a separately documented observation/workflow decision rather than replacing the original number without a trace.

## BSE market data

For a direct close, use an official BSE Equity Bhav Copy downloaded through an authorised route. The dedicated importer validates the registered scrip, date token in the source filename, BSE URL, `CLOSE` field and SHA-256 file fingerprint. It never derives a close or merges a duplicate direct observation.

```bash
python scripts/import_bse_bhavcopy.py --company infosys --date 2026-06-30 --bhavcopy /absolute/path/BSE_EQ_BHAVCOPY_20260630.csv --source-url 'https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx'
```

Use `scripts/import_market_prices.py` only for a pre-mapped historical context CSV that already meets the full market schema. Set `price_method=direct_bse_close` only for a direct BSE closing quote with artifact filename and SHA-256 provenance. The model requires the direct observation date to equal the dated share observation and valuation date. Otherwise, it preserves the price as context but blocks market-cap/upside output.

## New company activation

Use `scripts/create_company_workspace.py` to create a scaffolded workspace. It does not put a company in the active registry. After three complete annual periods, a dated-share observation, publication-date cutoff checks and company-specific assumptions are reviewed, set `assumption_status` to `approved` in `config/assumptions/<company>.json` and run:

```bash
python scripts/activate_company.py --company <company_id>
```

Only then can `scripts/run_model.py --company <company_id>` run a valuation.
