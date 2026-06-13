from unittest import TestCase
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from moto import mock_aws

import api.routers.chat as chat_module
from api.routers import chat_router


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
        self.mock_service.answer.return_value = "There is 1 rental in progress."
        response = self.client.post("/chat/ask", json={"message": "how many rentals?", "history": []})
        self.assertEqual(200, response.status_code)
        self.assertEqual("There is 1 rental in progress.", response.json())
        self.mock_service.answer.assert_called_once()

    def test_ask_passes_message_and_history(self):
        self.mock_service.answer.return_value = "ok"
        history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi, how can I help?"},
        ]
        response = self.client.post("/chat/ask", json={"message": "and then?", "history": history})
        self.assertEqual(200, response.status_code)
        _, kwargs = self.mock_service.answer.call_args
        self.assertEqual("and then?", kwargs["message"])
        self.assertEqual(2, len(kwargs["history"]))
        self.assertEqual("hello", kwargs["history"][0].content)

    def test_ask_defaults_to_empty_history(self):
        self.mock_service.answer.return_value = "ok"
        response = self.client.post("/chat/ask", json={"message": "hi"})
        self.assertEqual(200, response.status_code)
        _, kwargs = self.mock_service.answer.call_args
        self.assertEqual([], kwargs["history"])

    def test_ask_rejects_invalid_role(self):
        response = self.client.post(
            "/chat/ask",
            json={"message": "hi", "history": [{"role": "system", "content": "x"}]},
        )
        self.assertEqual(422, response.status_code)
