import sys
from pathlib import Path
import unittest
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from equity_platform import build_historical, reconcile_statements, resolve_valuation_shares, run_fcff_valuation, validate_assumptions, validate_information_cutoff, validate_source_records
from market_data import market_comparison, peer_comparison, select_share_observation, validate_market_observations, validate_share_observations

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.records = pd.read_csv(ROOT / "data/raw/infosys_source_records.csv")
        self.historical = build_historical(self.records)
        self.shares = pd.read_csv(ROOT / "data/shares/infosys_share_observations.csv")
        self.market = pd.read_csv(ROOT / "data/market/infosys_market_observations.csv")
        self.assumptions = {"operating_tax_rate": .25, "wacc": .12, "terminal_growth": .05, "valuation_date": "2026-03-31", "information_cutoff": "2026-04-23", "forecast_growth": [.05], "forecast_ebit_margin": [.20], "forecast_da_ratio": [.03], "forecast_capex_ratio": [.02], "forecast_nwc_ratio": [.17], "lease_liabilities": 0, "non_controlling_interest": 0}
    def test_share_unit_conversion(self):
        self.assertAlmostEqual(self.historical.iloc[-1].shares_crore, 412.0108168, places=6)
    def test_equity_bridge_and_per_share_units(self):
        _, s = run_fcff_valuation(self.historical, self.assumptions)
        self.assertAlmostEqual(s["value_per_share_inr"], s["equity_value_inr_crore"] / s["shares_crore"])
    def test_missing_critical_data_blocks_valuation(self):
        broken = self.records[self.records.field != "capex"]
        self.assertTrue(any("missing critical" in e for e in validate_source_records(broken)))
    def test_invalid_terminal_combination_blocks_valuation(self):
        bad = {**self.assumptions, "wacc": .05, "terminal_growth": .05}
        with self.assertRaises(ValueError): run_fcff_valuation(self.historical, bad)
    def test_reconciliation_failure_blocks_valuation(self):
        broken = self.historical.copy()
        broken.loc[broken.index[-1], "cash_flow_financing"] += 2
        self.assertIn("fail", set(reconcile_statements(broken).status))
        with self.assertRaises(ValueError): run_fcff_valuation(broken, self.assumptions)
    def test_cash_flow_sign_error_fails_reconciliation(self):
        broken = self.historical.copy()
        broken.loc[broken.index[-1], "cash_flow_investing"] *= -1
        result = reconcile_statements(broken)
        self.assertIn("fail", set(result.status))
    def test_unavailable_reconciliation_blocks_valuation(self):
        incomplete = self.historical.drop(columns=["cash_fx_effect"])
        self.assertIn("unavailable", set(reconcile_statements(incomplete).status))
        with self.assertRaises(ValueError): run_fcff_valuation(incomplete, self.assumptions)
    def test_zero_is_not_missing(self):
        zero = self.records.copy()
        zero.loc[zero.field == "capex", ["raw_value", "normalized_value_inr_crore"]] = 0
        self.assertEqual(validate_source_records(zero), [])
    def test_period_end_net_treasury_denominator(self):
        self.assertAlmostEqual(resolve_valuation_shares(self.historical), 403.8289901, places=6)
    def test_current_dated_share_observation(self):
        self.assertEqual(validate_share_observations(self.shares), [])
        selected = select_share_observation(self.shares, "infosys", "2026-06-30")
        self.assertAlmostEqual(selected.net_outstanding_crore, 404.9645811, places=6)
        self.assertEqual(selected.fully_diluted_period_end_status, "unavailable")

    def test_verified_period_end_dilution_replaces_net_share_denominator(self):
        diluted = self.shares.astype({"dilution_source_url": "object"}).copy()
        diluted.loc[0, "fully_diluted_period_end_status"] = "verified"
        diluted.loc[0, "fully_diluted_period_end_shares"] = 4_060_000_000
        diluted.loc[0, "fully_diluted_period_end_crore"] = 406.0
        diluted.loc[0, "dilution_source_url"] = "https://www.infosys.com/investors/share-plan-note.pdf"
        self.assertEqual(validate_share_observations(diluted), [])
        self.assertAlmostEqual(resolve_valuation_shares(self.historical, diluted, "infosys", "2026-06-30"), 406.0)
    def test_non_direct_market_price_cannot_drive_comparison(self):
        self.assertEqual(validate_market_observations(self.market), [])
        valuation = {"valuation_date": "2026-06-30", "value_per_share_inr": 1100, "shares_crore": 404.9645811}
        result = market_comparison(valuation, self.market, select_share_observation(self.shares, "infosys", "2026-06-30"), "infosys")
        self.assertEqual(result["status"], "unavailable")
    def test_direct_compatible_market_price_allows_comparison(self):
        direct = self.market.assign(
            price_method="direct_bse_close", observation_time_ist="close",
            source_url="https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx",
            source_artifact="BSE_EQ_BHAVCOPY_20260630.csv", source_file_sha256="a" * 64,
        )
        valuation = {"valuation_date": "2026-06-30", "value_per_share_inr": 1100, "shares_crore": 404.9645811}
        result = market_comparison(valuation, direct, select_share_observation(self.shares, "infosys", "2026-06-30"), "infosys")
        self.assertEqual(result["status"], "pass")
        self.assertIn("implied_upside_downside_pct", result)
    def test_empty_peer_data_is_explicitly_unavailable(self):
        peers = pd.read_csv(ROOT / "data/peers/peer_inputs.csv")
        result = peer_comparison(peers, "infosys", "2026-06-30")
        self.assertEqual(set(result.status), {"unavailable"})
        self.assertTrue(result.revenue_inr_crore.notna().all())
        self.assertTrue(result.market_price_inr.isna().all())

    def test_information_cutoff_blocks_later_source_publication(self):
        late = self.records.copy()
        late.loc[late.index[0], "publication_date"] = "2026-07-24"
        self.assertTrue(validate_information_cutoff(late, "2026-07-23"))

    def test_mismatched_forecast_arrays_block_valuation(self):
        invalid = {**self.assumptions, "forecast_ebit_margin": [.20, .20]}
        self.assertTrue(any("same length" in error for error in validate_assumptions(invalid)))
        with self.assertRaises(ValueError):
            run_fcff_valuation(self.historical, invalid)

    def test_direct_close_can_coexist_with_derived_context(self):
        direct = self.market.assign(
            price_method="direct_bse_close", observation_time_ist="close",
            source_url="https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx",
            source_artifact="BSE_EQ_BHAVCOPY_20260630.csv", source_file_sha256="b" * 64,
        )
        combined = pd.concat([self.market, direct], ignore_index=True)
        valuation = {"valuation_date": "2026-06-30", "value_per_share_inr": 1100, "shares_crore": 404.9645811}
        result = market_comparison(valuation, combined, select_share_observation(self.shares, "infosys", "2026-06-30"), "infosys", "500209")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["market_cap_basis"], "period_end_net_outstanding_shares")

    def test_peer_market_import_is_joined_by_scrip_and_date(self):
        market = pd.DataFrame([{
            "company_id": "tcs", "bse_scrip": "532540", "observation_date": "2026-06-30",
            "observation_time_ist": "close", "close_price_inr": 3000, "currency": "INR",
            "market_cap_inr_crore": pd.NA, "price_method": "direct_bse_close",
            "source_url": "https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx",
            "source_artifact": "BSE_EQ_BHAVCOPY_20260630.csv", "source_file_sha256": "c" * 64,
            "retrieval_date": "2026-07-01", "verification_status": "verified", "notes": "test",
        }])
        peers = pd.read_csv(ROOT / "data/peers/peer_inputs.csv")
        result = peer_comparison(peers, "infosys", "2026-06-30", "2026-03-31", market, "2026-07-23")
        tcs = result[result.peer_bse_scrip == "532540"].iloc[0]
        self.assertEqual(tcs.status, "pass")
        self.assertEqual(tcs.market_price_inr, 3000)

if __name__ == "__main__": unittest.main()
