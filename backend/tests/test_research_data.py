import csv
import tempfile
import unittest
from pathlib import Path

from app.research_data import CHART_FILE, RUN_FILE, finite, prepare


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ["PSI_159", "PSI_117"]:
            (self.root / name).mkdir()
        self.runs = self.root / "PSI_159" / RUN_FILE
        with self.runs.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Test", "Fuel", "approx p (bar)", "burn time (sec)", "mHC (mg/s)"])
            writer.writerow(["run-1", "ethane", "1.2", "", "2"])
        self.series = self.root / "PSI_117" / CHART_FILE
        self.series.write_text(',t/(Do)2 (s/mm2),(D/Do)2\nEXPT,0,1\n,-0.1,0.9\n,,\n')

    def test_units_missingness_and_original_citations_survive_sort(self):
        bundle = prepare(self.root)
        experiment = bundle["experiments"][0]
        self.assertIsNone(experiment["burn_time_s"])
        self.assertEqual(experiment["pressure_bar"], 1.2)
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


if __name__ == "__main__":
    unittest.main()
