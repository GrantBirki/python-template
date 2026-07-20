"""Waitress server entrypoint."""

from __future__ import annotations

import argparse
import logging
import os
from collections.abc import Mapping, Sequence

from waitress import serve

from python_template.app import application

LOGGER = logging.getLogger("python_template.server")
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("port must be an integer") from error
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _log_level(value: str) -> str:
    level = value.upper()
    if level not in LOG_LEVELS:
        raise argparse.ArgumentTypeError(
            f"log level must be one of: {', '.join(LOG_LEVELS)}"
        )
    return level


def build_parser(environ: Mapping[str, str] | None = None) -> argparse.ArgumentParser:
    env = os.environ if environ is None else environ
    parser = argparse.ArgumentParser(
        prog="python-template", description="Run the python-template web service"
    )
    parser.add_argument("--host", default=env.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=_port, default=env.get("PORT", "8000"))
    parser.add_argument(
        "--log-level", type=_log_level, default=env.get("LOG_LEVEL", "INFO")
    )
    return parser


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
        force=True,
    )


def main(
    argv: Sequence[str] | None = None, environ: Mapping[str, str] | None = None
) -> int:
    args = build_parser(environ).parse_args(argv)
    configure_logging(args.log_level)
    LOGGER.info("server_start host=%s port=%d", args.host, args.port)
    serve(application, host=args.host, port=args.port)
    return 0
