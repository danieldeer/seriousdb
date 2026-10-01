"""Generate or check the generated documentation in docs/reference.

Used by both .github/workflows/docs.yml and the "docs-reference" hook in
.pre-commit-config.yaml.

Run directly with:

    uv run --group docs python scripts/docs-reference.py

Use --check flag to verify that docs/reference is up to date without modifying it:

    uv run --group docs python scripts/docs-reference.py --check
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPHINX_SRC = ROOT / "docs" / "_sphinx"
REFERENCE = ROOT / "docs" / "reference"

FIX_COMMAND = "uv run --group docs python scripts/docs-reference.py"


def _diff(dcmp: filecmp.dircmp, rel: Path = Path()) -> list[str]:
	"""Collect every path that differs or is missing on one side, recursively.

	Parameters
	----------
	dcmp : filecmp.dircmp
	    Comparison to walk.
	rel : pathlib.Path, optional
	    Path prefix to report, used when recursing into subdirectories.

	Returns
	-------
	list of str
	    One entry per differing or missing file, relative to the compared
	    directories' roots.
	"""
	mismatches = [
		str(rel / name)
		for name in (
			*dcmp.diff_files,
			*dcmp.left_only,
			*dcmp.right_only,
		)
	]
	for name, sub_dcmp in dcmp.subdirs.items():
		mismatches += _diff(sub_dcmp, rel / name)
	return mismatches


def _build(output: Path, doctrees: Path) -> int:
	"""Build the reference documentation into output."""
	result = subprocess.run(
		[
			"sphinx-build",
			"-b",
			"markdown",
			"-W",
			"-d",
			str(doctrees),
			str(SPHINX_SRC),
			str(output),
		],
		check=False,
	)
	return result.returncode


def generate() -> int:
	"""Generate docs/reference from the Sphinx documentation source."""
	with tempfile.TemporaryDirectory() as scratch:
		built = Path(scratch) / "reference"
		doctrees = Path(scratch) / "doctrees"

		result = _build(built, doctrees)
		if result != 0:
			return result

		if REFERENCE.exists():
			shutil.rmtree(REFERENCE)

		REFERENCE.parent.mkdir(parents=True, exist_ok=True)
		shutil.copytree(built, REFERENCE)

	print("Generated docs/reference")
	return 0


def check() -> int:
	"""Check whether docs/reference matches the generated documentation."""
	with tempfile.TemporaryDirectory() as scratch:
		built = Path(scratch) / "reference"
		doctrees = Path(scratch) / "doctrees"

		result = _build(built, doctrees)
		if result != 0:
			return result

		mismatches = sorted(_diff(filecmp.dircmp(built, REFERENCE)))

	if mismatches:
		print(
			"\ndocs/reference is out of date with docstrings in "
			"src/seriousdb.\n"
			"Differing or missing files:\n"
			+ "\n".join(f"  - {path}" for path in mismatches)
			+ f"\n\nRegenerate it with:\n\n {FIX_COMMAND}\n",
			file=sys.stderr,
		)
		return 1

	print("docs/reference is up to date.")
	return 0


def main() -> int:
	"""Generate the reference documentation or check it with --check.

	Returns
	-------
	int
	    Process exit code: 0 if docs/reference is up to date, non-zero
	    otherwise (a Sphinx build failure or a content mismatch).
	"""
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--check",
		action="store_true",
		help="check whether docs/reference is up to date",
	)
	args = parser.parse_args()

	if args.check:
		return check()

	return generate()


if __name__ == "__main__":
	sys.exit(main())
