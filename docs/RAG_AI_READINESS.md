# RAG and AI readiness boundary

RAG, fine-tuning, frontend, backend, and an LLM connection are deliberately not implemented in this repository. The deterministic data core is now ready to be consumed by those layers once the real-data blockers in the handoff document are resolved.

## Safe ingestion scope

Only ingest documents that have an approved source-document record or a source fact in the active company dataset. Keep documents partitioned by `company_id`, report/fiscal period, source URL, page number, publication date and SHA-256 file hash. Do not ingest the whole repository: legacy NVIDIA files, unrelated PDFs and generated notebook content are out of scope for an Infosys retrieval index.

## Required retrieval metadata

Each RAG chunk must include:

```text
company_id, document_id, source_url, source_file_sha256, report_title,
printed_page, pdf_page, publication_date, fiscal_year, basis, extraction_method,
review_status
```

The response renderer must show page/source citations for every numerical claim and must label a response as unavailable if no approved evidence is retrieved.

## Guardrails before enabling an LLM

- Treat all report text as untrusted content; never follow instructions embedded in a filing.
- Permit the LLM to explain or summarize only the deterministic packet; it may not calculate a replacement valuation or alter a source fact.
- Route numerical questions to the deterministic service first, then attach cited facts to the model context.
- Add a citation validator that verifies every displayed source ID exists in the selected run manifest.
- Build an evaluation set covering source lookup, unit conversion, period matching, current-share warnings, direct-price absence and refusal of unsupported claims.
- Log prompt version, retrieved chunks, answer, citations, model, temperature and evaluator result. Redact user data and never log API keys.

## Fine-tuning decision rule

Do not fine-tune for financial calculation or source extraction until the RAG evaluation demonstrates persistent retrieval/presentation failures that prompting and retrieval cannot solve. A fine-tuned model must not be the source of valuation numbers, forecasts, market prices, or investment recommendations.
