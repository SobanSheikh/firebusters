import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.ingestion import chunks_for, csv_records, inventory, numeric_profiles, prepare


class IngestionTests(unittest.TestCase):
    def test_duplicate_sources_preserve_aliases_and_ids_survive_rename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            group = root / "PSI_159"
            group.mkdir()
            (group / "one.csv").write_text("a,b\n1,2\n")
            (group / "copy.csv").write_text("a,b\n1,2\n")
            first = inventory(root)
            self.assertEqual(len(first), 1)
            self.assertEqual(len(first[0]["relative_paths"]), 2)
            (group / "one.csv").rename(group / "renamed.csv")
            self.assertEqual(first[0]["id"], inventory(root)[0]["id"])
            self.assertEqual(first[0]["investigation_id"], "PSI-159")

    def test_csv_preserves_bom_headers_multiline_cells_and_record_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"
            path.write_text('\ufeffx,x\n1,"line one\nline two"\n,3\n')
            source = inventory(Path(directory))[0]
            records = list(csv_records(path, source))
            self.assertEqual(records[0]["cells"], ["x", "x"])
            self.assertEqual(records[1]["cells"][1], "line one\nline two")
            self.assertEqual(records[2]["locator"]["record"], 3)
            self.assertEqual(records[2]["cells"], ["", "3"])

    def test_numeric_profiles_reject_nonfinite_and_keep_missingness(self):
        records = [{"cells": [v]} for v in ["value", "", "NaN", "inf", "2", "4"]]
        profile = numeric_profiles(records)[0]
        self.assertEqual(profile["finite_numeric_count"], 2)
        self.assertEqual(profile["missing_count"], 1)
        self.assertEqual(profile["other_count"], 3)
        self.assertEqual((profile["min"], profile["max"]), (2, 4))
        self.assertIsNone(profile["unit"])

    def test_chunks_retain_exact_page_and_character_offsets(self):
        page = {"id": "page-12", "source_id": "source", "text": "abcdefghijk"}
        chunks = list(chunks_for(page, size=5, overlap=2))
        for chunk in chunks:
            self.assertEqual(chunk["citation_id"], "page-12")
            self.assertEqual(chunk["text"], page["text"][chunk["start_char"]:chunk["end_char"]])
        self.assertEqual(chunks[-1]["end_char"], len(page["text"]))

    def test_bundle_is_reproducible_and_does_not_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "inputs"
            source.mkdir()
            (source / "data.csv").write_text("time,value\n0,1\n1,3\n")
            (source / "alias.csv").symlink_to(source / "data.csv")
            first = root / "first"
            second = root / "second"
            self.assertEqual(prepare(source, first), prepare(source, second))
            for file in first.iterdir():
                self.assertEqual(file.read_bytes(), (second / file.name).read_bytes())
            report = json.loads((first / "report.json").read_text())
            self.assertEqual(report["file_count"], 1)
            with self.assertRaises(FileExistsError):
                prepare(source, first)
            with self.assertRaises(ValueError):
                prepare(source, source / "output")

    def test_extraction_failure_is_explicit_and_other_sources_continue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "inputs"
            source.mkdir()
            (source / "report.pdf").write_bytes(b"broken PDF")
            (source / "data.csv").write_text("x\n1\n")
            with patch("app.ingestion.pdf_pages", side_effect=RuntimeError("unavailable")):
                report = prepare(source, root / "output")
            self.assertEqual(report["counts"]["extraction_failed"], 1)
            self.assertEqual(report["counts"]["table_extracted_needs_review"], 1)


if __name__ == "__main__":
    unittest.main()
