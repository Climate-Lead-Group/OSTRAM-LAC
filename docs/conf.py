# -*- coding: utf-8 -*-
"""Configure the Sphinx build of the OSTRAM LAC documentation.

Same stack as the OSTRAM documentation (Furo theme, MyST Markdown). Diagrams
are PNG figures under _static/, each with an English file and a Spanish
<name>.es.png that Sphinx picks for the es build; sphinxcontrib-mermaid stays
loaded for the one Mermaid block left in data-reference.md. Source language
is English; Spanish lives in locale/es/LC_MESSAGES/*.po and is built by a
second ReadTheDocs project.

Authors:
    2026 Climate Lead Group
"""

project = "OSTRAM LAC"
copyright = "2025-2026, Climate Lead Group"
author = "Climate Lead Group"
release = "1.0"
version = "1.0"

# OSTRAM also loads sphinx.ext.autosectionlabel; it is left out here because
# pages repeat headings ("Usage", "What It Does") within the same document,
# which floods the build with duplicate-label warnings, and no page uses
# {ref} to a section label (cross-links use MyST heading anchors).
extensions = [
    "myst_parser",
    "sphinxcontrib.mermaid",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "tasklist",
    "attrs_inline",
]

myst_heading_anchors = 3

# Render plain ```mermaid fences (as GitHub does) through the mermaid directive.
myst_fence_as_directive = ["mermaid"]

# Neutral palette stays readable on both Furo backgrounds.
mermaid_light_theme = "neutral"
mermaid_dark_theme = "neutral"

source_suffix = {".md": "markdown"}

# NOTE: no templates_path on purpose -- the repo .gitignore ignores any path
# containing "temp", so docs/_templates would silently never be committed.
exclude_patterns = [
    "_build", "dev", "superpowers", "locale", "requirements.txt",
    "Thumbs.db", ".DS_Store",
]

html_theme = "furo"
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/Climate-Lead-Group/OSTRAM-LAC/",
    "source_branch": "main",
    "source_directory": "docs/",
}

# Internationalisation (sphinx-intl / gettext)
language = "en"
locale_dirs = ["locale/"]
gettext_compact = False
gettext_uuid = False
