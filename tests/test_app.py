import json
import logging
import unittest
from typing import Any
from unittest import mock

from python_template import app


class ApplicationTest(unittest.TestCase):
    def call_app(
        self,
        path: str = "/",
        *,
        method: str = "GET",
        query: str = "",
        request_id: str | None = None,
    ) -> dict[str, Any]:
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query,
        }
        if request_id is not None:
            environ["HTTP_X_REQUEST_ID"] = request_id
        response: dict[str, Any] = {}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = status
            response["headers"] = dict(headers)

        response["body"] = b"".join(app.application(environ, start_response))
        response["json"] = json.loads(response["body"])
        return response

    @mock.patch("python_template.app.time.perf_counter", side_effect=[10.0, 10.002])
    @mock.patch("python_template.app.uuid.uuid4", return_value="generated-request-id")
    def test_health_generates_request_id_and_logs(
        self, _uuid4: mock.MagicMock, _perf_counter: mock.MagicMock
    ) -> None:
        with self.assertLogs("python_template.requests", logging.INFO) as logs:
            response = self.call_app("/health")

        self.assertEqual("200 OK", response["status"])
        self.assertEqual({"status": "ok"}, response["json"])
        self.assertEqual("application/json", response["headers"]["Content-Type"])
        self.assertEqual(
            str(len(response["body"])), response["headers"]["Content-Length"]
        )
        self.assertEqual("generated-request-id", response["headers"]["X-Request-ID"])
        self.assertIn(
            "method=GET path=/health status=200 request_id=generated-request-id duration_ms=2.000",
            logs.output[0],
        )

    def test_hello_uses_default_name(self) -> None:
        response = self.call_app("/hello", request_id="default-name")

        self.assertEqual("200 OK", response["status"])
        self.assertEqual({"message": "Hello, World!"}, response["json"])

    def test_hello_uses_first_custom_name_without_logging_query(self) -> None:
        with self.assertLogs("python_template.requests", logging.INFO) as logs:
            response = self.call_app(
                "/hello", query="name=Grant&name=Other", request_id="custom-name"
            )

        self.assertEqual({"message": "Hello, Grant!"}, response["json"])
        self.assertEqual("custom-name", response["headers"]["X-Request-ID"])
        self.assertIn("path=/hello", logs.output[0])
        self.assertNotIn("Grant", logs.output[0])
        self.assertNotIn("QUERY_STRING", logs.output[0])

    def test_hello_treats_blank_name_as_default(self) -> None:
        response = self.call_app("/hello", query="name=", request_id="blank-name")

        self.assertEqual({"message": "Hello, World!"}, response["json"])

    def test_unknown_path_returns_json_404(self) -> None:
        response = self.call_app("/missing", request_id="missing-route")

        self.assertEqual("404 Not Found", response["status"])
        self.assertEqual({"error": "not found"}, response["json"])

    def test_known_path_rejects_unsupported_method(self) -> None:
        response = self.call_app("/health", method="POST", request_id="wrong-method")

        self.assertEqual("405 Method Not Allowed", response["status"])
        self.assertEqual({"error": "method not allowed"}, response["json"])
        self.assertEqual("GET", response["headers"]["Allow"])

    @mock.patch("python_template.app.uuid.uuid4", return_value="replacement-id")
    def test_invalid_request_id_is_replaced(self, _uuid4: mock.MagicMock) -> None:
        response = self.call_app("/health", request_id="invalid request id")

        self.assertEqual("replacement-id", response["headers"]["X-Request-ID"])

    def test_request_id_is_trimmed_before_validation(self) -> None:
        response = self.call_app("/health", request_id="  valid-id  ")

        self.assertEqual("valid-id", response["headers"]["X-Request-ID"])


if __name__ == "__main__":
    unittest.main()
