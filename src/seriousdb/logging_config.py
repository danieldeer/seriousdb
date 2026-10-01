"""Centralized logging configuration for the application."""

import logging
import sys

from .config import LOG_LEVEL


def configure_logging() -> None:
	"""Configure the application's centralized logging.

	Sets the root logger's level and output format using the configured
	``LOG_LEVEL``. Logs are written to standard output.
	"""
	logging.basicConfig(
		level=LOG_LEVEL.upper(),
		format="%(asctime)s %(levelname)s %(name)s %(message)s",
		stream=sys.stdout,
		force=True,
	)
