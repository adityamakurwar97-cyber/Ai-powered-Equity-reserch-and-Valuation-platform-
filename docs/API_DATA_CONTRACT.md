# Application data contract

This is a contract for the future backend and frontend, not an implemented HTTP API.

## Request boundary

The future service should accept a registered `company_id` only. It must reject arbitrary filesystem paths, raw calculation overrides, undocumented share counts, and unversioned data uploads.

```json
{
  "company_id": "infosys"
}
```

It should call `project_runner.run_registered_company(PROJECT_ROOT, company_id)` and return or persist the generated result. Inputs must be pinned to the associated preflight manifest hash.

## Core response shape

`export_research_packet.py` produces the canonical UI/AI payload. Its top-level keys are:

```text
schema_version
purpose
not_investment_advice
company
valuation
readiness
historical_financials_inr_crore
forecast_inr_crore
reconciliations
market_comparison
peer_comparison
sensitivity_value_per_share_inr
source_documents
source_facts
share_observations
real_data_blockers
non_blocking_data_warnings
input_manifest
```

The endpoint must preserve `null`/`unavailable` rather than converting them to zero or an estimated value.

## Important semantics

| Field | Contract |
|---|---|
| `valuation.value_per_share_inr` | Intrinsic value per share, only with the status beside it. It is not a price target. |
| `valuation.valuation_status` | `ready` only when a fully diluted period-end denominator is verified; otherwise `provisional_period_end_net_shares`. |
| `market_comparison.status` | `pass` only with one verified direct BSE close on the dated share/valuation date. |
| `market_comparison.market_cap_inr_crore` | Uses period-end net outstanding shares, the standard market-cap basis. |
| `market_comparison.market_price_implied_equity_value_on_valuation_denominator_inr_crore` | Price × the valuation denominator; separate from market cap so fully diluted comparisons are not confused. |
| `source_facts` | Authoritative input-level evidence. Preserve page numbers, source URL, publication date, and verification status. |
| `real_data_blockers` | User-visible reasons a result is provisional or unavailable. Never silently hide them. |

## Error mapping

| Core outcome | Suggested API response |
|---|---|
| Unknown company | 404 with stable `company_not_registered` code |
| Source/share/assumption/cutoff validation fails | 422 with each validation message |
| Reconciliation fails | 422 with failing check names and no valuation output |
| Market or peer price unavailable | 200; core valuation may still be present, with explicit unavailable status |
| Preflight fails | Block release/job execution; do not serve a new snapshot |

## Persistence model for the future backend

Use immutable versioned records. At minimum persist `company`, `source_document`, `source_fact`, `share_observation`, `market_observation`, `assumption_set`, `run_manifest`, and `valuation_run`. Link every `valuation_run` to the exact input hashes produced by `preflight.py`.

Never use an LLM-generated value as a source fact or market price. Store any AI-generated narrative separately with `model`, `prompt_version`, retrieved source IDs, evaluation status, and human-review status.
