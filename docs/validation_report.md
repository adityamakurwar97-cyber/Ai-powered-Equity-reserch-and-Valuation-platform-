# Validation and readiness report — Infosys Limited

## Reconciliation results

fiscal_year,check,status,residual_inr_crore,tolerance_inr_crore,reason
2024,assets = equity + liabilities,pass,0.0,1.0,Rounded INR-crore statement comparison.
2024,operating + investing + financing = reported net cash change,pass,0.0,1.0,Rounded INR-crore statement comparison.
2024,opening cash + net cash change + FX = closing cash,pass,0.0,1.0,Rounded INR-crore statement comparison.
2024,cash-flow closing cash equivalents = balance-sheet cash equivalents,pass,0.0,1.0,Restricted cash is separately reported and excluded from both cash-equivalent values.
2025,assets = equity + liabilities,pass,0.0,1.0,Rounded INR-crore statement comparison.
2025,operating + investing + financing = reported net cash change,pass,0.0,1.0,Rounded INR-crore statement comparison.
2025,opening cash + net cash change + FX = closing cash,pass,0.0,1.0,Rounded INR-crore statement comparison.
2025,cash-flow closing cash equivalents = balance-sheet cash equivalents,pass,0.0,1.0,Restricted cash is separately reported and excluded from both cash-equivalent values.
2026,assets = equity + liabilities,pass,0.0,1.0,Rounded INR-crore statement comparison.
2026,operating + investing + financing = reported net cash change,pass,0.0,1.0,Rounded INR-crore statement comparison.
2026,opening cash + net cash change + FX = closing cash,pass,0.0,1.0,Rounded INR-crore statement comparison.
2026,cash-flow closing cash equivalents = balance-sheet cash equivalents,pass,0.0,1.0,Restricted cash is separately reported and excluded from both cash-equivalent values.


## Readiness

area,status,detail
financial_data_validation,pass,Source-record validation passed.
statement_reconciliation,pass,All required statement checks must pass before valuation.
share_denominator,warning,"Period-end net shares are verified, but fully diluted period-end awards are unavailable; intrinsic value is provisional."
market_comparison,unavailable,A direct BSE close on the valuation/share date is required before market cap or upside/downside is calculated.


## Market comparison

status,reason
unavailable,A direct BSE closing price on the dated share basis is required; derived or secondary observations are context only.


## Peer comparison

peer_company,peer_bse_scrip,financial_period_end,status,reason,revenue_inr_crore,ebit_inr_crore,net_income_inr_crore,ebit_margin_pct,net_margin_pct,market_price_inr,market_observation_date,market_price_source_url
HCL Technologies Limited,532281,2026-03-31,unavailable,Peer fundamentals are verified; a same-date direct BSE closing price is still required.,130144.0,22397.0,17361.0,17.20939881976887,13.339838947627245,,,
Tata Consultancy Services Limited,532540,2026-03-31,unavailable,Peer fundamentals are verified; a same-date direct BSE closing price is still required.,267021.0,66838.0,52820.0,25.030990071941904,19.781215709625837,,,
Wipro Limited,507685,2026-03-31,unavailable,Peer fundamentals are verified; a same-date direct BSE closing price is still required.,92809.3,15125.1,13265.5,16.29696592906099,14.293287418394494,,,


## Valuation output

,value
valuation_schema_version,1.0
valuation_date,2026-06-30
information_cutoff,2026-07-23
valuation_status,provisional_period_end_net_shares
pv_forecast_fcff_inr_crore,122206.07130655278
pv_terminal_value_inr_crore,333946.55109376926
enterprise_value_inr_crore,456152.62240032206
equity_value_inr_crore,446531.62240032206
shares_crore,404.9645811
value_per_share_inr,1102.6436464824012
share_denominator_method,Period-end issued and outstanding shares net of treasury shares
fully_diluted_period_end_status,unavailable
