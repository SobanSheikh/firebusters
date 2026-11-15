import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, Response
from starlette.requests import Request

from app.api.routes import assistant as route
from app.assistant_service import MAX_EVIDENCE, SYSTEM, retrieve


def request(address="203.0.113.7"):
    return Request({
        "type": "http", "method": "POST", "path": "/ask", "query_string": b"",
        "headers": [(b"x-forwarded-for", address.encode())],
        "client": ("127.0.0.1", 1234), "server": ("test", 80), "scheme": "http",
    })


class AssistantLimitTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        route.global_recent.clear()
        route.client_recent.clear()
        route.active = 0

    async def test_per_client_rate_limit_blocks_second_generation(self):
        payload = route.Question(question="cool flame evidence")
        answer_mock = AsyncMock(return_value={"ok": True})
        with (patch.object(route.settings, "assistant_client_requests_per_minute", 1),
              patch.object(route.assistant_service, "answer", new=answer_mock)):
            result = await route.ask(payload, request(), Response())
            self.assertEqual(result, {"ok": True})
            with self.assertRaises(HTTPException) as blocked:
                await route.ask(payload, request(), Response())
        self.assertEqual(blocked.exception.status_code, 429)
        self.assertEqual(answer_mock.await_count, 1)

    async def test_relevant_chart_is_deterministic_and_cited(self):
        chart = {"id": "chart-1", "title": "Droplet history", "x_label": "time", "x_unit": "s",
                 "y_label": "diameter", "y_unit": "ratio", "method": "source rows",
                 "limitations": "descriptive", "points": [
                     {"x": 0.0, "y": 1.0, "record": 1, "citation_id": "c1"},
                     {"x": 1.0, "y": 0.5, "record": 2, "citation_id": "c2"}]}
        calls = AsyncMock(side_effect=[[], [{"payload": chart}], [], [{"id": "c1"}, {"id": "c2"}]])
        with (patch("app.assistant_service.records", new=calls),
              patch("app.assistant_service.semantic_evidence", new=AsyncMock(return_value=[]))):
            result = await retrieve({"question": "show droplet diameter history", "experiment_ids": [], "chart_id": None})
        self.assertEqual(result["usage"]["retrieval_passes"], 1)
        self.assertLessEqual(len(result["evidence"]), MAX_EVIDENCE)
        self.assertEqual(result["visuals"][0]["chart_id"], "chart-1")
        self.assertEqual(set(result["visuals"][0]["citation_ids"]), {"c1", "c2"})

    def test_prompt_contains_required_safety_boundaries(self):
        for phrase in ["partial-gravity", "oxygen concentration", "predictive modeling",
                       "certified safety advice", "experimental or simulated"]:
            self.assertIn(phrase, SYSTEM)


if __name__ == "__main__":
    unittest.main()
