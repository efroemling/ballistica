# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# pylint: disable=invalid-name, redefined-builtin
# pylint: disable=missing-module-docstring

import os

from batools.docs import get_sphinx_settings

settings = get_sphinx_settings(projroot=os.environ['BALLISTICA_ROOT'])

# -- Options for HTML output -------------------------------------------------
# For more themes visit https://sphinx-themes.org/
html_theme = 'furo'  # python_docs_theme, groundwork, furo, sphinx_rtd_theme
html_title = f'{settings.project_name} {settings.version} documentation'

# Sets logo on side panel.
html_logo = settings.logo_small

if html_theme == 'furo':
    html_theme_options = {
        # 'announcement': 'This is a placeholder announcement',
        'light_css_variables': {
            'color-brand-primary': '#3cda0b',
            'color-brand-content': '#7C4DFF',
        },
        'dark_css_variables': {
            'color-brand-primary': '#3cda0b',
            'color-brand-content': '#7C4DFF',
        },
        'footer_icons': [
            {
                'name': 'GitHub',
                'url': 'https://github.com/efroemling/ballistica/',
                'html': """
                    <svg stroke='currentColor' fill='currentColor' stroke-width='0' viewBox='0 0 16 16'>
                        <path fill-rule='evenodd' d='M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z'></path>
                    </svg>
                """,
                'class': '',
            },
        ],
        'top_of_page_button': 'edit',
        'navigation_with_keys': True,
    }

# -- Project information -----------------------------------------------------
project = settings.project_name
copyright = settings.copyright
author = settings.project_author

# The full version, including alpha/beta/rc tags.
version = str(settings.version)
release = str(settings.buildnum)

# -- General configuration ---------------------------------------------------

# Prepend to pages.
rst_prolog = f"""
.. image:: {settings.logo_large}
    :target: index.html
    :alt: Ballistica Logo
"""

# Append to pages.
rst_epilog = """
"""

# Gives us links to common Python types.
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

extensions = [
    'sphinx.ext.napoleon',  # Allows google/numpy style docstrings.
    'sphinx.ext.autodoc',  # Parse docstrings.
    'sphinx.ext.viewcode',  # Adds 'source' links.
    'sphinx.ext.intersphinx',  # Allows linking to base Python types.
]

# Reduces ugly wrapping in the sidebar.
toc_object_entries_show_parents = 'hide'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files. This pattern also
# affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
