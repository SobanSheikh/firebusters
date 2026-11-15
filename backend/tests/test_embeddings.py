import unittest

from app.embeddings import MODEL, validate_vectors
from app.index_documents import page_chunks


class EmbeddingTests(unittest.TestCase):
    def test_model_dimension_and_normalization_are_validated(self):
        valid = [1.0] + [0.0] * 383
        self.assertEqual(validate_vectors({"model": MODEL, "embeddings": [valid]}, 1), [valid])
        for model, vector in [(MODEL, valid[:20]), ("other-model", valid),
                              (MODEL, [0.0] * 384), (MODEL, [float("nan")] * 384)]:
            with self.assertRaises(ValueError):
                validate_vectors({"model": model, "embeddings": [vector]}, 1)

    def test_chunks_preserve_page_citation_and_exact_offsets(self):
        page = {"id": "page-citation", "source_id": "original-pdf", "text": "cool flame " * 200}
        chunks = list(page_chunks(page))
        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks, list(page_chunks(page)))
        for chunk in chunks:
            self.assertEqual(chunk["citation_id"], page["id"])
            self.assertEqual(chunk["source_id"], page["source_id"])
            self.assertEqual(chunk["text"], page["text"][chunk["start_char"]:chunk["end_char"]])
        self.assertEqual(chunks[-1]["end_char"], len(page["text"]))


if __name__ == "__main__":
    unittest.main()
