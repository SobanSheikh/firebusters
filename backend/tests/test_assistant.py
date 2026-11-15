import unittest
from unittest.mock import AsyncMock, patch

from app.assistant_service import graph, search_terms, validate_claims


class AssistantTests(unittest.IsolatedAsyncioTestCase):
    async def test_graph_returns_no_evidence_without_calling_model(self):
        with (patch("app.assistant_service.records", new=AsyncMock(return_value=[])),
              patch("app.assistant_service.semantic_evidence", new=AsyncMock(return_value=[]))):
            result = await graph.ainvoke({"question": "How do lunar rocks form?", "experiment_ids": [], "chart_id": None})
        self.assertEqual(result["mode"], "no_evidence")
        self.assertEqual(result["claims"], [])

    def test_search_input_is_bounded_and_has_no_query_operators(self):
        terms = search_terms("ethane; DROP TABLE -- '" + " test" * 100)
        self.assertNotIn(";", terms)
        self.assertNotIn("'", terms)
        self.assertLessEqual(len(terms.split(" | ")), 24)

    def test_unknown_citation_is_rejected(self):
        result = validate_claims({"evidence": [{"citation_id": "known", "data": {"value": 12}}],
                                 "claims": [{"text": "Value 12", "citation_ids": ["invented"]}]})
        self.assertEqual(result["claims"], [])

    def test_invalid_claim_does_not_hide_valid_claim(self):
        evidence = [{"citation_id": "known", "data": {"topic": "cool flames"}}]
        result = validate_claims({
            "evidence": evidence,
            "claims": [
                {"text": "This statement is supported.", "citation_ids": ["known"]},
                {"text": "This statement is not supported.", "citation_ids": ["invented"]},
            ],
        })
        self.assertEqual(len(result["claims"]), 1)
        self.assertIn("omitted", result["message"])

    def test_rounded_number_requires_approximation_cue(self):
        evidence = [{"citation_id": "a", "label": "PSI-117", "data": {"value": 0.966}}]
        accepted = validate_claims({"evidence": evidence, "claims": [
            {"text": "The value is near 0.97 in PSI-117.", "citation_ids": ["a"]}], "mode": "ai"})
        self.assertEqual(accepted, {})
        adjusted = validate_claims({"evidence": evidence, "claims": [
            {"text": "The value is 0.97.", "citation_ids": ["a"]}], "mode": "ai"})
        self.assertTrue(adjusted["claims"][0]["text"].startswith("Approximately,"))

    def test_unicode_minus_is_validated_as_negative(self):
        evidence = [{"citation_id": "a", "data": {"value": -0.2008}}]
        self.assertEqual(validate_claims({"evidence": evidence, "claims": [
            {"text": "The value is –0.2008.", "citation_ids": ["a"]}], "mode": "ai"}), {})

    def test_numeric_claim_must_match_cited_record_not_other_record(self):
        evidence = [{"citation_id": "a", "data": {"pressure_bar": 1.2}},
                    {"citation_id": "b", "data": {"pressure_bar": 8.0}}]
        self.assertEqual(validate_claims({"evidence": evidence, "claims": [
            {"text": "Pressure is 8 bar.", "citation_ids": ["a"]}]} )["claims"], [])
        self.assertEqual(validate_claims({"evidence": evidence, "claims": [
            {"text": "Pressure is 1.2 bar.", "citation_ids": ["a"]}], "mode": "ai"}), {})

    def test_invalid_model_number_uses_cited_chart_fallback(self):
        common = {
            "kind": "chart_point",
            "data": {
                "x_label": "Time",
                "x_unit": "s",
                "y_label": "Normalized diameter squared",
                "y_unit": "dimensionless",
                "limitations": "Reviewed CSV points only; no causal interpretation.",
            },
        }
        evidence = [
            {
                **common,
                "citation_id": "point-a",
                "data": {**common["data"], "x": -0.2, "y": 0.96},
            },
            {
                **common,
                "citation_id": "point-b",
                "data": {**common["data"], "x": 1.8, "y": 0.3},
            },
        ]
        result = validate_claims(
            {
                "evidence": evidence,
                "claims": [{"text": "The value is 999.", "citation_ids": ["point-a"]}],
                "mode": "ai",
            }
        )
        self.assertEqual(result["mode"], "curated_fallback")
        self.assertEqual(len(result["claims"]), 2)
        self.assertEqual(result["claims"][0]["citation_ids"], ["point-a", "point-b"])


if __name__ == "__main__":
    unittest.main()
