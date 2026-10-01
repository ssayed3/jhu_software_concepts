import os
import sys

# Add the Module 4 project root to Python's path
sys.path.insert(0, os.path.abspath(".."))


# -- Project information -----------------------------------------------------

project = "Module 4 - Testing and Documentation"
copyright = "2026, Sayed Sayed"
author = "Sayed Sayed"
release = "1.0"


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]

exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]


# -- Options for HTML output -------------------------------------------------

html_theme = "alabaster"

html_static_path = ["_static"]