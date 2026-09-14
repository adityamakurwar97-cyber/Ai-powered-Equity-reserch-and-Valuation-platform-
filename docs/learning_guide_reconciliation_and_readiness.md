# Financial Reconciliation & Valuation Readiness — learning guide

## 1. Why reconcile first?

Financial statements are connected views of one business. A DCF can calculate perfectly and still be unreliable if its inputs come from incompatible or incorrectly transcribed statements. This project compares independent report lines and shows a **pass**, **fail**, or **unavailable** result. It never changes an input to make a residual zero.

The tolerance is ₹1 crore because Infosys reports these statements rounded to whole INR crore. In the saved FY2024–FY2026 data every reconciliation residual is ₹0 crore.

| Check | Formula | What it catches |
|---|---|---|
| Balance sheet | assets − (equity + liabilities) | Missing/mis-signed balance-sheet line |
| Cash-flow subtotal | CFO + CFI + CFF − reported net cash change | Cash-flow signs or transcription errors |
| Cash roll-forward | opening cash + net cash change + FX − closing cash | Missing FX effect or wrong opening/closing balance |
| Cash equivalence | CFS closing cash − balance-sheet cash equivalents | Mixing cash equivalents with another balance |

Restricted cash is separately reported (₹348 crore / ₹424 crore / ₹422 crore for FY24/FY25/FY26) and is excluded from the cash-equivalent check. It is not a zero value and not an excess-cash plug.

## 2. FCFF in this model

`FCFF = operating EBIT × (1 − operating tax rate) + D&A − capex − change in operating NWC`.

- Operating EBIT is derived as PBT **before exceptional items** + finance cost − other income, so other income is not treated as recurring operating profit and the FY26 ₹1,289 crore Labour Codes exceptional item is excluded.
- Operating NWC is trade receivables minus trade payables only. Cash, investments, tax balances and financing liabilities are excluded.
- Capex is the reported cash-flow spend on PPE and intangibles, net of sale proceeds, stored positive so the formula subtracts it.
- The operating tax rate and forecast ratios are assumptions in `config/assumptions.json`; they are not reported historical facts. Their lengths, dates, ranges and terminal-rate relationship are validated before the forecast runs.

## 3. Enterprise value to equity value

The forecast produces operating enterprise value. The bridge deducts FY26 lease liabilities (₹9,176 crore) and non-controlling interests (₹445 crore). Cash and investments remain at zero in the bridge because this model has not established that they are all distributable excess cash. Adding them without that assessment would risk double counting.

## 4. Share count treatment

For the active valuation dated **30 June 2026**, the denominator is **404.9645811 crore period-end net outstanding shares**. It comes from the official Q1 FY27 balance sheet and is published on the information-cutoff date of 23 July 2026. Therefore INR crore / crore shares returns INR/share.

This replaces the prior FY26 diluted weighted-average EPS count of 412.0108168 crore. That count is an annual EPS calculation, not a period-end share count. The Q1 FY27 release discloses a quarterly diluted weighted-average count, but not a total fully diluted period-end option/award count. The result is thus a period-end net-share valuation with a dilution warning, not a fully diluted valuation.

## 5. Market context

`data/market/infosys_market_observations.csv` retains a same-date **derived** context price from official market capitalization and gross shares. It is not labelled a direct BSE close, so the model deliberately does **not** calculate market capitalization or upside/downside. A local official BSE Bhav Copy is required to activate that comparison.
