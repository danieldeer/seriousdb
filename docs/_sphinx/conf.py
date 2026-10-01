"""Sphinx configuration for seriousdb's generated API reference.

This build is not published as an HTML site. It exists solely to turn the
NumPy-style docstrings in ``src/seriousdb`` into the Markdown files committed
under ``docs/reference/``, so the reference docs read on GitHub stay in sync
with the code without being hand-edited.

Regenerate with::

    uv run --group docs sphinx-build -b markdown -d docs/_build/doctrees docs/_sphinx docs/reference

See ``docs/development.md`` for details.
"""

from __future__ import annotations

import os
import sys

# Make the package importable without an editable install, and resolvable
# the same way whether this runs locally or in CI.
sys.path.insert(0, os.path.abspath("../../src"))

project = "seriousdb"
copyright = "Daniel Hirsch"
author = "Daniel Hirsch"

extensions = [
	"sphinx.ext.autodoc",
	"sphinx.ext.autosummary",
	"sphinx.ext.napoleon",
	"sphinx_markdown_builder",
]

# -- autodoc / autosummary -------------------------------------------------
# One generated page per module, driven by docs/_sphinx/_templates/autosummary,
# instead of autodoc's single flat dump.
autosummary_generate = True
autosummary_generate_overwrite = True
add_module_names = False

#
# NOTE: "members" is intentionally *not* set here. The autosummary module
# template (_templates/autosummary/module.rst) calls ``automodule`` for the
# module docstring only, then lists each function/class/exception with its
# own ``autofunction``/``autoclass``/``autoexception`` directive. Adding
# "members" here would make ``automodule`` document them a second time.
autodoc_default_options = {
	"undoc-members": False,
	"show-inheritance": True,
	"member-order": "bysource",
}
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# -- napoleon (NumPy-style docstrings) --------------------------------------
napoleon_numpy_docstring = True
napoleon_google_docstring = False
napoleon_use_param = True
napoleon_use_rtype = False
napoleon_use_ivar = True
napoleon_include_init_with_doc = False

templates_path = ["_templates"]
exclude_patterns = ["_build"]

# -- sphinx-markdown-builder -------------------------------------------------
markdown_uri_doc_suffix = ".md"
markdown_flavor = "github"
