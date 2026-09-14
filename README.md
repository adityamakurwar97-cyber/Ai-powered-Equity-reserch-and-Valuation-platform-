# AI-powered equity research platform — deterministic core

This repository is the source-backed, deterministic foundation for an AI-powered equity-research platform. It currently runs an educational FCFF valuation for **Infosys Limited** (BSE 500209; ISIN INE009A01021) using traceable FY2024–FY2026 consolidated annual data in INR crore. It includes balance-sheet/cash-flow reconciliation, publication-date information-cutoff controls, dated-share controls and an auditable data manifest.

## Run on a MacBook M2 / VS Code

1. Install Python **3.10–3.13** and open this folder in VS Code.
2. In the integrated terminal: `python3 -m venv .venv && source .venv/bin/activate`
3. Install: `python -m pip install -r requirements.txt`
4. Verify the saved inputs and write a SHA-256 manifest: `python scripts/preflight.py`
5. Run the model: `python scripts/run_model.py --company infosys`
6. Export the application-ready research packet: `python scripts/export_research_packet.py --company infosys`
7. Run focused checks: `python -m unittest discover -s tests -v`
8. In VS Code, open `notebooks/infosys_bse_reliable_data_valuation.ipynb`, select the `.venv` interpreter as kernel, then **Restart Kernel and Run All**.

The normal run uses saved CSV records and does not scrape websites. For refresh, manually transcribe reviewed official-report facts into `data/raw/infosys_source_records.csv`, including the report **publication date** and every traceability column; then stage, validate and test the change.

This is educational, not investment advice or a fair-value guarantee. Forecast and discount-rate assumptions are explicit in `config/assumptions.json`. See `docs/unresolved_issues.md` before relying on outputs.

## Readiness gates

`scripts/run_model.py` blocks valuation if source-record validation, publication-date information cutoff, any statement reconciliation, forecast assumptions, or the dated share denominator is missing or invalid. It saves results in `data/processed/`. `scripts/preflight.py` validates all active registry companies before a release or future API job.

The saved market context is deliberately separate in `data/market/`. The current record is derived from official market-cap data rather than a direct BSE close, so market capitalization and implied upside/downside remain blocked until a direct BSE Bhav Copy close is imported on the dated-share valuation date.

For the financial logic explained with this project’s actual data, read `docs/learning_guide_reconciliation_and_readiness.md`.

## Market, peers, multi-company and refresh workflow

The model now uses a company registry and `--company` runner option. Current dated Infosys net shares are held separately from annual EPS shares. Direct BSE prices can be imported through a provenance-validating saved-data workflow; peer comparison joins verified, date-compatible INR fundamentals to direct BSE price files by scrip/date. Full instructions: `docs/market_peers_multi_company_guide.md` and `docs/refresh_workflow.md`.

For the next developer, start with [docs/developer_handoff.md](docs/developer_handoff.md). It defines the completed deterministic core, real-data blockers, stable service/data contracts, and the intentionally unimplemented backend, frontend, RAG and AI layers.
