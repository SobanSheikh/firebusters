import tempfile
import unittest
from pathlib import Path

from app.psi115 import index_preview, parse_diameters, parse_distribution, parse_grid


class NumericalTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "field.dat"

    def test_grid_preserves_order_and_fortran_exponents(self):
        self.path.write_text("2 2 1 1\n1D0 2\n3 4\n")
        self.assertEqual(parse_grid(self.path)["values"], [1, 2, 3, 4])

    def test_grid_rejects_extra_truncated_nonfinite_and_invalid_dimensions(self):
        for content in ["2 2 1 1\n1 2 3 4 5", "2 2 1 1\n1 2 3",
                        "2 2 1 1\n1 2 NaN 4", "2 2 2 1\n1 2 3 4",
                        "0 2 1 1\n", "2 2 1 1\n1 2 inf 4"]:
            with self.subTest(content=content):
                self.path.write_text(content)
                with self.assertRaises(ValueError):
                    parse_grid(self.path)

    def test_distribution_preserves_first_node_and_line_locator(self):
        self.path.write_text("2 1E-5\n3 2E-5\n")
        records = parse_distribution(self.path)["records"]
        self.assertEqual(records[0], {"node": 2, "value": 1e-5, "line": 1})

    def test_distribution_rejects_duplicate_nodes(self):
        self.path.write_text("2 1\n2 3\n")
        with self.assertRaises(ValueError):
            parse_distribution(self.path)

    def test_diameters_require_positive_ordered_values(self):
        self.path.write_text("Diameter (starting from first non-vapor node)\n1e-9\n2e-9\n")
        self.assertEqual(len(parse_diameters(self.path)["values"]), 2)
        self.path.write_text("Diameter (starting from first non-vapor node)\n2\n1\n")
        with self.assertRaises(ValueError):
            parse_diameters(self.path)

    def test_preview_covers_every_value_and_preserves_extremes(self):
        values = [1, 2, -100, 4, 5, 900, 7]
        preview = index_preview(values, bins=3)
        self.assertLessEqual(len(preview), 3)
        self.assertEqual(preview[0]["start_index"], 0)
        self.assertEqual(preview[-1]["end_index_exclusive"], len(values))
        self.assertEqual(min(r["min"] for r in preview), -100)
        self.assertEqual(max(r["max"] for r in preview), 900)


if __name__ == "__main__":
    unittest.main()
