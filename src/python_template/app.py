"""WSGI application implemented with the Python standard library."""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from collections.abc import Callable, Iterable
from typing import Any
from urllib.parse import parse_qs

LOGGER = logging.getLogger("python_template.requests")
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}")

StartResponse = Callable[[str, list[tuple[str, str]]], Any]


def _request_id(environ: dict[str, Any]) -> str:
    candidate = str(environ.get("HTTP_X_REQUEST_ID", "")).strip()
    if REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return str(uuid.uuid4())


def _route(
    environ: dict[str, Any],
) -> tuple[int, dict[str, str], list[tuple[str, str]]]:
    method = str(environ.get("REQUEST_METHOD", "GET")).upper()
    path = str(environ.get("PATH_INFO", "/"))

    if path not in {"/health", "/hello"}:
        return 404, {"error": "not found"}, []
    if method != "GET":
        return 405, {"error": "method not allowed"}, [("Allow", "GET")]
    if path == "/health":
        return 200, {"status": "ok"}, []

    query = parse_qs(str(environ.get("QUERY_STRING", "")), keep_blank_values=True)
    name = query.get("name", ["World"])[0].strip() or "World"
    return 200, {"message": f"Hello, {name}!"}, []


def application(
    environ: dict[str, Any], start_response: StartResponse
) -> Iterable[bytes]:
    """Serve a JSON response and record one request-completion log entry."""
    started = time.perf_counter()
    request_id = _request_id(environ)
    status_code, payload, extra_headers = _route(environ)
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    headers = [
        ("Content-Type", "application/json"),
        ("Content-Length", str(len(body))),
        ("X-Request-ID", request_id),
        *extra_headers,
    ]
    start_response(f"{status_code} {_status_reason(status_code)}", headers)
    duration_ms = (time.perf_counter() - started) * 1000
    LOGGER.info(
        "request_complete method=%s path=%s status=%d request_id=%s duration_ms=%.3f",
        str(environ.get("REQUEST_METHOD", "GET")).upper(),
        str(environ.get("PATH_INFO", "/")),
        status_code,
        request_id,
        duration_ms,
    )
    return [body]


def _status_reason(status_code: int) -> str:
    return {200: "OK", 404: "Not Found", 405: "Method Not Allowed"}[status_code]
