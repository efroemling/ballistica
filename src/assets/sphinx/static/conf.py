# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
import os
import sys

sphinx_settings = eval(os.getenv('SPHINX_SETTINGS')) # set in tools/batools/docs.py
ballistica_root = os.getenv('BALLISTICA_ROOT') + '/'

assets_dirs: dict = {
    'ba_data': 'src/assets/ba_data/python/',
    'dummy_modules': 'build/dummymodules/',
    'efro_tools': 'tools/',  # for efro and bacommon package
}

sys.path.append(os.path.abspath(ballistica_root + assets_dirs['ba_data']))
sys.path.append(os.path.abspath(ballistica_root + assets_dirs['dummy_modules']))
sys.path.append(os.path.abspath(ballistica_root + assets_dirs['efro_tools']))

# -- Project information -----------------------------------------------------
project = sphinx_settings['project_name']
copyright = sphinx_settings['copyright']
author = sphinx_settings['project_author']
# The full version, including alpha/beta/rc tags
version = str(sphinx_settings['version'])
release = str(sphinx_settings['buildnum'])


# -- Options for HTML output -------------------------------------------------
# for more themes visit https://sphinx-themes.org/
html_theme = 'furo'  # python_docs_theme, groundwork, furo, sphinx_rtd_theme 
html_title = project + ' ' + version + ' documentation'
html_show_sphinx = False

# do not remove, sets the logo on side panel
html_logo = sphinx_settings['ballistica_logo']

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
        'footer_icons': [{
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

# -- General configuration ---------------------------------------------------

# append to pages
rst_epilog = """
"""
# prepend to pages
rst_prolog = f"""
.. image:: {html_logo}
    :target: index.html
    :alt: Ballistica Logo 
"""
# intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}   
autosummary_generate = True
extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    # might want to use this in future
    # for linking with efro and bacommon packages
    'sphinx.ext.intersphinx',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
