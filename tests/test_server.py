import argparse
import logging
import os
import unittest
from unittest import mock

from python_template import server


class ServerTest(unittest.TestCase):
    def test_port_accepts_valid_value(self):
        self.assertEqual(8000, server._port("8000"))

    def test_port_rejects_non_integer(self):
        with self.assertRaisesRegex(argparse.ArgumentTypeError, "integer"):
            server._port("eight")

    def test_port_rejects_values_below_range(self):
        with self.assertRaisesRegex(argparse.ArgumentTypeError, "between"):
            server._port("0")

    def test_port_rejects_values_above_range(self):
        with self.assertRaisesRegex(argparse.ArgumentTypeError, "between"):
            server._port("65536")

    def test_log_level_normalizes_valid_value(self):
        self.assertEqual("WARNING", server._log_level("warning"))

    def test_log_level_rejects_unknown_value(self):
        with self.assertRaisesRegex(argparse.ArgumentTypeError, "DEBUG, INFO"):
            server._log_level("verbose")

    def test_parser_uses_environment_defaults(self):
        args = server.build_parser(
            {"HOST": "0.0.0.0", "PORT": "9000", "LOG_LEVEL": "debug"}
        ).parse_args([])

        self.assertEqual("0.0.0.0", args.host)
        self.assertEqual(9000, args.port)
        self.assertEqual("DEBUG", args.log_level)

    def test_parser_arguments_override_environment(self):
        args = server.build_parser(
            {"HOST": "env", "PORT": "9000", "LOG_LEVEL": "ERROR"}
        ).parse_args(["--host", "cli", "--port", "7000", "--log-level", "info"])

        self.assertEqual("cli", args.host)
        self.assertEqual(7000, args.port)
        self.assertEqual("INFO", args.log_level)

    def test_parser_uses_process_environment_when_not_supplied(self):
        with mock.patch.dict(
            os.environ,
            {"HOST": "process", "PORT": "8100", "LOG_LEVEL": "CRITICAL"},
            clear=True,
        ):
            args = server.build_parser().parse_args([])

        self.assertEqual("process", args.host)
        self.assertEqual(8100, args.port)
        self.assertEqual("CRITICAL", args.log_level)

    def test_parser_rejects_invalid_environment_port(self):
        with self.assertRaises(SystemExit):
            server.build_parser({"PORT": "invalid"}).parse_args([])

    @mock.patch("python_template.server.logging.basicConfig")
    def test_configure_logging(self, basic_config):
        server.configure_logging("INFO")

        basic_config.assert_called_once_with(
            level="INFO",
            format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
            force=True,
        )

    @mock.patch("python_template.server.serve")
    @mock.patch("python_template.server.configure_logging")
    def test_main_configures_and_runs_waitress(self, configure_logging, serve):
        with self.assertLogs("python_template.server", logging.INFO) as logs:
            result = server.main(
                ["--host", "127.0.0.2", "--port", "8123", "--log-level", "error"], {}
            )

        self.assertEqual(0, result)
        configure_logging.assert_called_once_with("ERROR")
        serve.assert_called_once_with(server.application, host="127.0.0.2", port=8123)
        self.assertIn("server_start host=127.0.0.2 port=8123", logs.output[0])


if __name__ == "__main__":
    unittest.main()
