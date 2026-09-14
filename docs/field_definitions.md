# Field definitions

All money values are INR crore. `1 crore = 10,000,000`; therefore INR crore / crore shares = INR per share.

| Field | Definition / treatment |
|---|---|
| operating_ebit | PBT **before exceptional items** + finance cost − other income. It excludes other income and the FY26 ₹1,289 crore Labour Codes exceptional item. |
| capex | Cash-flow expenditure on PPE and intangibles, net of sale proceeds; acquisitions are excluded. Stored positive for FCFF subtraction. |
| operating_nwc | Trade receivables less trade payables only. Cash, investments, tax balances and other financial assets/liabilities are excluded. |
| cash_taxes_paid | Reported total tax cash paid. It is not used as forecast operating cash tax. |
| shares_crore | Historical diluted weighted-average shares divided by 10,000,000; retained for EPS analysis and explicitly not used as the period-end valuation denominator. |
| period_end_paid_up_shares | FY26 date-specific paid-up shares, converted into crore shares. |
| treasury_shares | FY26 treasury shares, converted into crore shares and subtracted from paid-up shares for the valuation denominator. |
| cash_flow_* | Reported consolidated cash-flow statement lines. Inflows are positive, outflows negative; `cash_flow_net_change` is before the separate FX effect. |
| restricted_cash | Reported separately from cash and cash equivalents; excluded from the cash-equivalent reconciliation and equity bridge. |
| publication_date | Date the cited source was publicly available. It is the date tested against `information_cutoff`; `retrieval_date` records local collection and may be later. |
| fully_diluted_period_end_* | Used only when an official period-end employee-award/convertible count is available and status is `verified`; otherwise the dated net-share denominator is used with a provisional warning. |

The source-record CSV is also the source register: it records original values/units, conversion, period, basis, URL, report/page locations, retrieval date, status and ambiguity notes. Derived figures are coded in `src/equity_platform.py`.
