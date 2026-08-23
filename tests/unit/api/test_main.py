from unittest import TestCase

from fastapi import FastAPI
from fastapi.testclient import TestClient
from moto import mock_aws

from api.main import app, RequestContextMiddleware, unhandled_exception_handler


@mock_aws
class TestRequestContextMiddleware(TestCase):
    """Integration tests for RequestContextMiddleware and the global exception handler."""

    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_generates_request_id_when_absent(self):
        response = self.client.get("/health")
        self.assertIn("X-Request-ID", response.headers)
        self.assertTrue(response.headers["X-Request-ID"])

    def test_echoes_provided_request_id(self):
        response = self.client.get("/health", headers={"X-Request-ID": "my-request-id"})
        self.assertEqual("my-request-id", response.headers["X-Request-ID"])

    def test_logs_request_completed_with_expected_fields(self):
        with self.assertLogs("api.main", level="INFO") as logs:
            response = self.client.get("/health")
        self.assertEqual(200, response.status_code)
        self.assertTrue(any("Request completed" in line for line in logs.output))

    def test_unhandled_exception_returns_500_and_logs_error(self):
        failing_app = FastAPI()
        failing_app.add_middleware(RequestContextMiddleware)
        failing_app.add_exception_handler(Exception, unhandled_exception_handler)

        @failing_app.get("/boom")
        def boom():
            raise ValueError("kaboom")

        client = TestClient(failing_app, raise_server_exceptions=False)
        with self.assertLogs("api.main", level="ERROR"):
            response = client.get("/boom")
        self.assertEqual(500, response.status_code)
        self.assertEqual({"detail": "Internal server error"}, response.json())
