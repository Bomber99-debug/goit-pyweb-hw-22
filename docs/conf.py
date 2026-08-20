import os
import sys


sys.path.insert(
	0,
	os.path.abspath(".."),
)


project = "Contacts REST API"
author = "Bomber99-debug"

extensions = [
	"sphinx.ext.autodoc",
	"sphinx.ext.napoleon",
	"sphinx.ext.viewcode",
]

templates_path = [
	"_templates",
]

exclude_patterns = []

html_theme = "alabaster"