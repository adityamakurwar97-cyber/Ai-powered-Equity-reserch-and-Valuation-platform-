# Data coverage and activation rules

## Live valuation dataset

Infosys is the only company with the complete, three-year reconciled financial statements required for an FCFF valuation. The current INR/share output uses the official June 30, 2026 net period-end shares. It is marked provisional because the reviewed official release does not disclose a total period-end count of all dilutive employee awards.

When a company discloses that count, save it in `fully_diluted_period_end_shares` and `fully_diluted_period_end_crore`, set `fully_diluted_period_end_status` to `verified`, and cite the award-note source in `dilution_source_url`. The valuation engine will then use that denominator automatically. A quarter's diluted weighted-average shares must not be substituted for it.

## Peer fundamentals

`data/peers/peer_inputs.csv` now contains source-backed FY26 INR revenue, EBIT and net income for TCS, HCLTech and Wipro. These are financial-comparison inputs, not price inputs. The peer result remains unavailable until a direct BSE close is saved for each peer on the valuation date; it deliberately does not use any web quote, delayed feed, implied price, or mismatched date.

## Direct BSE closing price

Use the official BSE Equity Bhav Copy for the exact trading date and run:

```bash
python scripts/import_bse_bhavcopy.py --company infosys --date 2026-06-30 --bhavcopy /absolute/path/to/BSE_EQ_BHAVCOPY_20260630.csv --source-url 'https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx'
```

Repeat for TCS (532540), HCLTech (532281), and Wipro (507685) using their company-universe IDs (`tcs`, `hcltech`, `wipro`). The importer uses the active registry **or company universe** scrip and only accepts a `CLOSE` from the supplied official BSE file; it writes `price_method=direct_bse_close` with a SHA-256 provenance fingerprint. That is the only input which can enable market cap, upside/downside, or peer-price comparison.

## Company universe

`data/company_universe.csv` records coverage explicitly. TCS, HCLTech and Wipro have verified peer fundamentals now, but have not been misrepresented as valuation-ready companies: their full, reconciled three-year valuation statements still need to be source-imported before they are added to `config/company_registry.csv`.
