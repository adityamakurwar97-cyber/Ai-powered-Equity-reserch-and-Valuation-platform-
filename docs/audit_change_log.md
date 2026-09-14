# Audit and change log

## Original notebook audit

- Selected `codes/aipoweredreserchAndEquity-2.ipynb`: it is the only notebook and contains the most complete existing workflow, but it is NVIDIA/USD specific.
- It mixes an embedded snapshot with optional hard-coded paths, has duplicated exploratory cells, typo-prone manual forecast cells, illustrative cash/debt/share inputs, and fictional demo peers.
- Its FCFF section uses revenue-ratio assumptions rather than traceable financial statements; it treats practice cash/debt/shares as valuation inputs and has no source/period/basis validation.
- The original was executed from a fresh kernel in an isolated working directory: all 67 cells completed with no cell errors. Its observed side effect was creating `NVIDIA_five_year_forecast.csv` in that isolated directory. It remains preserved and NVIDIA/USD-specific; the replacement notebook is the BSE workflow target.

## Corrections

- Added source-backed Infosys FY2024–FY2026 consolidated annual data in INR crore.
- Defined operating EBIT, operating NWC and capex consistently; other income is excluded from operating EBIT.
- Added hard validation that blocks valuation for missing/review-required source facts, duplicate records, non-annual/non-consolidated rows, bad units/factors and invalid WACC/growth.
- Replaced demo peer comparison with an explicitly disabled feature: no peer inputs are imported because currency, market date and fiscal-period matching were not sourced.
- Excluded cash/investments from the bridge until a separate excess-cash assessment is documented; lease liabilities and NCI are explicit bridge deductions.

## Financial Reconciliation & Valuation Readiness milestone

- Cross-checked and added FY2024–FY2026 total assets, equity, liabilities, operating/investing/financing cash flow, net cash change, FX effect, opening/closing cash and restricted cash from official consolidated reports.
- Added four non-plug reconciliation checks per fiscal year, each with a ₹1 crore rounding tolerance. All twelve saved-data checks return pass with ₹0 residual.
- Replaced the valuation denominator of 412.0108168 crore FY26 diluted weighted-average EPS shares with 403.8289901 crore FY26 period-end paid-up shares net of 0.8650911 crore treasury shares. The same equity value therefore changes per-share value from ₹1,083.79 to ₹1,105.74; no operating forecast or bridge amount was changed.
- Added readiness gating: failed/unavailable reconciliation or missing dated share inputs blocks valuation. Market comparison is explicitly unavailable rather than silently calculated.
- The active FY24 series uses comparative amounts presented in the FY25 official report for balance-sheet/P&L data and original FY24 report cash-flow references where already retained. No alternate restated series was identified in this saved evidence set; a refresh must preserve any original-versus-restated difference as separate source records rather than overwrite it.

## Market, share, peer and multi-company extension

- Added `config/company_registry.csv` and a parameterised `scripts/run_model.py --company <id>` runner. New BSE company workspaces are intentionally empty until source data is staged and approved.
- Added FY27 Q1 dated Infosys net outstanding shares (30 June 2026): 404.964581 crore. The report discloses an interim diluted weighted-average share count but not a fully diluted period-end award count; the valuation labels dilution status unavailable.
- Added saved market/share schemas, a validated historical market importer, a no-bypass BSE access diagnostic, and a date/basis guard that blocks market comparison without a direct BSE close.
- Added peer-input validation that requires INR, verified data, fiscal-definition notes and an equal market date. Empty peer input produces an explicit unavailable result rather than fabricated multiples.

## Verified peer and direct-close import extension

- Added source-backed FY26 INR revenue, operating profit/segment-result and net-income inputs for TCS, HCLTech and Wipro. Peer output now displays those fundamentals, but stays unavailable for valuation multiples until a direct BSE close exists for each peer on the valuation date.
- Added `scripts/import_bse_bhavcopy.py`, which maps a user-supplied official BSE Equity Bhav Copy row to `price_method=direct_bse_close`. It preserves any existing snapshot and rejects duplicate dates or non-BSE file layouts.
- Extended the dated-share schema with fully diluted period-end shares and an award-note source. A verified observation is now selected automatically in the per-share valuation; unavailable data continues to produce a clearly labelled net-share provisional result.
- Added an explicit company-universe register: Infosys is valuation-ready; TCS, HCLTech and Wipro are peer-fundamentals-ready only. This avoids treating partial peer data as complete valuation datasets.

## Handoff and integrity hardening

- Normalized the project data directory to lowercase `data/` so Linux, Docker and CI do not rely on macOS case-insensitive filesystem behavior.
- Added `publication_date` to financial source facts, shares and peer inputs. The active run now blocks report facts or dated shares that were not public by `information_cutoff`; local retrieval after the cutoff is logged but does not create look-ahead bias.
- Corrected FY26 operating EBIT from ₹36,089 crore to ₹37,378 crore: the earlier calculation started from PBT after the ₹1,289 crore exceptional Labour Codes charge despite claiming to exclude it. The charge is now separately retained as an audited source fact.
- Strengthened market data: direct BSE closes need a matching registered scrip, file-date token, BSE URL, file SHA-256, close timestamp and verified status. A valid direct close can now coexist with derived context on the same date.
- Connected peer price comparison to saved `data/market/<peer>_market_observations.csv` files by BSE scrip/date; peer fiscal-period matching is no longer hard-coded to FY26.
- Added row-level versus full-history annual refresh validation, safe scaffold/activation workflow for new companies, a reusable `project_runner` service, no-network preflight manifest, source-backed research packet, and developer/API/RAG handoff documentation.
