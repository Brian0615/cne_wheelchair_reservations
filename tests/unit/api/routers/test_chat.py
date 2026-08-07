from unittest import TestCase
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from moto import mock_aws

import api.routers.chat as chat_module
from api.routers import chat_router
from common.data_models import ChatResponse


def _make_app():
    app = FastAPI()
    app.include_router(chat_router)
    return app


@mock_aws
class TestChatRouter(TestCase):
    """Integration tests for the /chat router endpoint."""

    def setUp(self):
        self.mock_service = MagicMock()
        self.patcher = patch.object(chat_module, "chat_service", self.mock_service)
        self.patcher.start()
        self.client = TestClient(_make_app())

    def tearDown(self):
        self.patcher.stop()

    def test_ask_returns_answer(self):
        self.mock_service.answer.return_value = ChatResponse(
            answer="There is 1 rental in progress.",
            model="gemini-3.5-flash-lite",
            input_tokens=100,
            output_tokens=23,
            cache_read_tokens=0,
            total_tokens=123,
        )
        response = self.client.post("/chat/ask", json={"message": "how many rentals?", "history": []})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "answer": "There is 1 rental in progress.",
                "model": "gemini-3.5-flash-lite",
                "input_tokens": 100,
                "output_tokens": 23,
                "cache_read_tokens": 0,
                "total_tokens": 123,
            },
        )
        self.mock_service.answer.assert_called_once()

    def test_ask_passes_message_and_history(self):
        self.mock_service.answer.return_value = ChatResponse(
            answer="ok", model="gemini-3.5-flash-lite", input_tokens=1, output_tokens=1, cache_read_tokens=0,
            total_tokens=2,
        )
        history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi, how can I help?"},
        ]
        response = self.client.post("/chat/ask", json={"message": "and then?", "history": history})
        self.assertEqual(response.status_code, 200)
        _, kwargs = self.mock_service.answer.call_args
        self.assertEqual(kwargs["message"], "and then?")
        self.assertEqual(len(kwargs["history"]), 2)
        self.assertEqual(kwargs["history"][0].content, "hello")

    def test_ask_defaults_to_empty_history(self):
        self.mock_service.answer.return_value = ChatResponse(
            answer="ok", model="gemini-3.5-flash-lite", input_tokens=1, output_tokens=1, cache_read_tokens=0,
            total_tokens=2,
        )
        response = self.client.post("/chat/ask", json={"message": "hi"})
        self.assertEqual(response.status_code, 200)
        _, kwargs = self.mock_service.answer.call_args
        self.assertEqual(kwargs["history"], [])

    def test_ask_rejects_invalid_role(self):
        response = self.client.post(
            "/chat/ask",
            json={"message": "hi", "history": [{"role": "system", "content": "x"}]},
        )
        self.assertEqual(response.status_code, 422)
