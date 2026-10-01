"""Run local benchmarks with compact output and saved revision history."""

import sys

import pytest


def main() -> int:
	"""Run benchmarks with stable display settings and save the raw samples."""
	return pytest.main(
		[
			"benchmarks",
			"--benchmark-only",
			"--benchmark-autosave",
			"--benchmark-save-data",
			"-q",
			"--benchmark-columns=median,min,max,rounds",
			"--benchmark-time-unit=ms",
			*sys.argv[1:],
		]
	)


if __name__ == "__main__":
	raise SystemExit(main())
