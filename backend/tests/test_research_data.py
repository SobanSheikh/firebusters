import csv
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from app.research_data import BASS_FILE, CHART_FILE, RUN_FILE, bass_outcome, finite, prepare


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ["PSI_159", "PSI_117", "PSI_26"]:
            (self.root / name).mkdir()
        self.runs = self.root / "PSI_159" / RUN_FILE
        with self.runs.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow([
                "Flame Type", "Day", "Fuel", "Test", "Cool flame?", " XO2 before test",
                "XO2  after test", "approx p (bar)", "Xf", "mHC (mg/s)", "TFP", "Tad (K)",
                "Zst", "Hot ignition", "burn time (sec)", "Self-ext or flow term",
                "Peak burner T (C )", "Comments",
            ])
            writer.writerow([
                "Normal", "1", "ethane", "run-1", "", "0.21", "0.20", "1.2", "1",
                "2", "Yes", "2500", "0.1", "Yes", "", "FT", "300", "flow cut",
            ])
        self.series = self.root / "PSI_117" / CHART_FILE
        self.series.write_text(',t/(Do)2 (s/mm2),(D/Do)2\nEXPT,0,1\n,-0.1,0.9\n,,\n')
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "as run matrix"
        sheet.append(["BASS Test Matrix"])
        sheet.append(["Setup"])
        sheet.append([
            "Actual Date  (for SPICE Display Date, add 1 for Leap Year)", "As run test no.",
            "Test no.", "Sample no.", "material", "Fan display", "Air display", "GN2 Pot",
            "GN2 display", "O2 % by volume", "pressure, atm", "CO2, mm Hg",
            "Test Observations and Anomalies (ignited, spread, extinguished, burn time, color, etc.) ",
        ])
        sheet.append([
            "2012-03-30", 3, 18, 19, "PMMA sphere 1 cm", "66 > 47", "10, 3-4",
            "4 > max", "198 to 497", 0.221, 0.97, 2.44,
            "N2 did not extinguish the wake; the flame went out when airflow stopped.",
        ])
        workbook.save(self.root / "PSI_26" / BASS_FILE)

    def test_units_missingness_and_original_citations_survive_sort(self):
        bundle = prepare(self.root)
        experiment = bundle["experiments"][0]
        self.assertIsNone(experiment["burn_time_s"])
        self.assertEqual(experiment["pressure_bar"], 1.2)
        self.assertEqual(experiment["termination_label"], "Flow termination")
        bass = next(item for item in bundle["experiments"] if item["investigation_id"] == "PSI-26")
        self.assertEqual(bass["derived_outcome"], "suppression_failed")
        self.assertTrue(bass["suppression_attempted"])
        chart = bundle["charts"][0]
        self.assertEqual(chart["x_unit"], "s/mm²")
        self.assertEqual(chart["points"][0]["record"], 3)
        citations = {c["id"]: c for c in bundle["citations"]}
        for point in chart["points"]:
            self.assertEqual(citations[point["citation_id"]]["locator"]["record"], point["record"])

    def test_unknown_chart_header_is_rejected(self):
        self.series.write_text("time,diameter\n1,2\n")
        with self.assertRaises(ValueError):
            prepare(self.root)

    def test_partial_chart_pair_is_rejected(self):
        self.series.write_text(',t/(Do)2 (s/mm2),(D/Do)2\nEXPT,0,\n')
        with self.assertRaises(ValueError):
            prepare(self.root)

    def test_nonfinite_measurements_are_rejected(self):
        for value in ["NaN", "inf", "-inf"]:
            with self.assertRaises(ValueError):
                finite(value)

    def test_bass_outcome_is_conservative_and_preserves_failed_suppression(self):
        self.assertEqual(bass_outcome("N2 did not extinguish the flame"),
                         ("suppression_failed", True))
        self.assertEqual(bass_outcome("No ignition after repeated attempts"),
                         ("ignition_failed", False))


if __name__ == "__main__":
    unittest.main()
