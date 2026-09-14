# Developer handoff — deterministic research core

## What is complete

The repository now provides a reproducible, no-network financial-data and FCFF core for Infosys. It has one clearly defined responsibility: validate saved, official-source facts and produce traceable valuation artifacts. It does not contain a web app, API server, authentication, database, RAG pipeline, fine-tuned model, or LLM call.

The handoff acceptance command is:

```bash
python scripts/preflight.py
python -m unittest discover -s tests -v
python scripts/run_model.py --company infosys
python scripts/export_research_packet.py --company infosys
```

All four commands use local saved files only. `preflight.py` writes a SHA-256 input manifest to `data/processed/project_preflight.json` and will fail if an active company breaks the source, date, share, reconciliation, or assumption controls.

## Current architecture boundary

```text
official report / official BSE Bhav Copy
             │ (reviewed local import)
             ▼
data/raw + data/shares + data/market + data/peers
             │ (strict schemas and cutoff controls)
             ▼
src/equity_platform.py + src/market_data.py
             │
             ▼
src/project_runner.py
             │
             ├── CLI artifacts in data/processed/
             └── source-backed JSON research packet

Future backend / UI / RAG / AI layers must call the project runner or consume its
versioned artifacts; they must not recompute or overwrite source facts.
```

## Stable handoff interfaces

| Interface | Purpose | Future consumer |
|---|---|---|
| `project_runner.run_registered_company(root, company_id)` | One validated in-memory valuation run | API/service layer |
| `scripts/run_model.py` | Writes normalized historicals, forecast, sensitivity, readiness, market and peer outputs | Batch job / scheduler |
| `scripts/export_research_packet.py` | Writes page/source-preserving JSON facts and calculations, with no generated narrative | RAG ingestion / UI |
| `scripts/preflight.py` | Verifies every active company and fingerprints inputs | CI / release gate |
| `scripts/import_bse_bhavcopy.py` | Imports only a local official BSE Bhav Copy with file SHA-256 provenance | Data operations |
| `scripts/stage_annual_refresh.py` | Stages reviewable annual facts before merge | Data operations |

The detailed response and input contracts are in [API_DATA_CONTRACT.md](API_DATA_CONTRACT.md). The future AI/RAG guardrails are in [RAG_AI_READINESS.md](RAG_AI_READINESS.md).

## Data lifecycle rules

1. Only `config/company_registry.csv` companies are active for valuation.
2. `data/company_universe.csv` may list scaffolded or peer-only companies; that does not make them valuation-ready.
3. New companies are created with `scripts/create_company_workspace.py`. They stay inactive until `scripts/activate_company.py` validates their full three-year history, shares, cutoff, and approved company-specific assumptions.
4. `publication_date`, not local retrieval date, enforces the stated information cutoff. Retrieval after the cutoff is allowed if the source was publicly available by the cutoff.
5. The direct-close importer accepts only a BSE-hosted source URL, matching file-date token, registered scrip, exact `CLOSE`, and SHA-256 fingerprint. A derived or secondary quote remains context only.
6. The generated packet is facts plus citations; it is not analyst prose and must not be treated as investment advice.

## Remaining real-data blockers

- Official direct BSE closes matching 30 June 2026 for Infosys and peers. Until then market cap/upside/downside and peer-price status are intentionally unavailable.
- An official Infosys period-end count of unvested/convertible employee awards. Until then per-share value is correctly labelled `provisional_period_end_net_shares`.
- Full three-year, reconciled source registers plus company-specific assumptions for TCS, HCLTech, and Wipro. Their FY26 peer fundamentals are loaded, but they are not activated as standalone valuation companies.

## Work intentionally left for the next owner

1. Backend/API: wrap `run_registered_company` in an authenticated service; do not put calculations in route handlers.
2. Database/job layer: persist immutable source versions, manifests, imports and output snapshots; use a background job for refresh/export.
3. Frontend: render the JSON/CSV artifacts, source citations, warnings and unavailable states exactly as supplied.
4. RAG: ingest only approved, page-aware source documents and packets; see the RAG document before implementation.
5. AI/fine-tuning: add only after an evaluation set, citation validator and prompt-injection controls exist. Fine-tuning must never replace numerical calculations or source-of-truth values.

## Release gate before any UI/API demo

- `python scripts/preflight.py` exits 0.
- Unit tests pass.
- Every displayed monetary value carries the INR crore / INR per-share unit defined by its artifact.
- UI/API displays `valuation_status`, `readiness`, source URLs, publication dates, and every unavailable reason without suppression.
- No secret, raw web scrape, or unverified third-party quote is committed to the repository.
