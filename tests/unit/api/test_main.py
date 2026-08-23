from unittest import TestCase

from fastapi import FastAPI
from fastapi.testclient import TestClient
from moto import mock_aws

from api.main import app, AccessLogMiddleware, unhandled_exception_handler


@mock_aws
class TestAccessLogMiddleware(TestCase):
    """Integration tests for AccessLogMiddleware and the global exception handler."""

    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_logs_request_completed_with_expected_fields(self):
        with self.assertLogs("api.main", level="INFO") as logs:
            response = self.client.get("/health")
        self.assertEqual(200, response.status_code)
        self.assertTrue(any("Request completed" in line for line in logs.output))

    def test_unhandled_exception_returns_500_and_logs_error(self):
        failing_app = FastAPI()
        failing_app.add_middleware(AccessLogMiddleware)
        failing_app.add_exception_handler(Exception, unhandled_exception_handler)

        @failing_app.get("/boom")
        def boom():
            raise ValueError("kaboom")

        client = TestClient(failing_app, raise_server_exceptions=False)
        with self.assertLogs("api.main", level="ERROR"):
            response = client.get("/boom")
        self.assertEqual(500, response.status_code)
        self.assertEqual({"detail": "Internal server error"}, response.json())
