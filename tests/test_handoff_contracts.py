import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equity_platform import validate_source_records
from market_data import select_share_observation, validate_market_observations
from project_runner import run_registered_company
from research_packet import build_research_packet


class HandoffContractTests(unittest.TestCase):
    def test_source_register_requires_three_consecutive_years(self):
        records = pd.read_csv(ROOT / "data/raw/infosys_source_records.csv")
        two_years = records[records.fiscal_year >= 2025]
        errors = validate_source_records(two_years)
        self.assertTrue(any("At least 3" in error for error in errors))

    def test_share_publication_cannot_breach_information_cutoff(self):
        shares = pd.read_csv(ROOT / "data/shares/infosys_share_observations.csv")
        with self.assertRaises(ValueError):
            select_share_observation(shares, "infosys", "2026-06-30", "2026-07-22")

    def test_direct_bse_close_requires_provenance_fingerprint(self):
        market = pd.read_csv(ROOT / "data/market/infosys_market_observations.csv")
        market.loc[:, "price_method"] = "direct_bse_close"
        market.loc[:, "observation_time_ist"] = "close"
        market.loc[:, "source_url"] = "https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx"
        self.assertTrue(any("SHA-256" in error for error in validate_market_observations(market)))

    def test_registered_run_is_exportable_as_json_research_packet(self):
        run = run_registered_company(ROOT, "infosys")
        packet = build_research_packet(run)
        serialized = json.dumps(packet, allow_nan=False)
        self.assertIn('"schema_version": "1.0"', serialized)
        self.assertEqual(packet["company"]["company_id"], "infosys")
        self.assertTrue(packet["source_documents"])
        self.assertTrue(packet["real_data_blockers"])

    def test_peer_bhavcopy_import_uses_company_universe_and_records_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            bhavcopy = directory / "BSE_EQ_BHAVCOPY_20260630.csv"
            bhavcopy.write_text("SC_CODE,SC_NAME,CLOSE\n532540,TCS,3000.50\n")
            output = directory / "tcs_market_observations.csv"
            completed = subprocess.run(
                [
                    sys.executable, str(ROOT / "scripts/import_bse_bhavcopy.py"), "--company", "tcs",
                    "--date", "2026-06-30", "--bhavcopy", str(bhavcopy),
                    "--source-url", "https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx",
                    "--retrieval-date", "2026-07-01", "--output", str(output),
                ],
                cwd=ROOT, text=True, capture_output=True, check=True,
            )
            imported = pd.read_csv(output)
            self.assertIn("Saved verified direct BSE close", completed.stdout)
            self.assertEqual(imported.loc[0, "bse_scrip"], 532540)
            self.assertEqual(imported.loc[0, "close_price_inr"], 3000.50)
            self.assertRegex(imported.loc[0, "source_file_sha256"], r"^[a-f0-9]{64}$")


if __name__ == "__main__":
    unittest.main()
