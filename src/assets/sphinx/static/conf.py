# Released under the MIT License. See LICENSE for details.
#
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# pylint: disable=invalid-name, redefined-builtin
# pylint: disable=missing-module-docstring

from __future__ import annotations

import os
import types
import logging
from typing import TYPE_CHECKING, override

from efro.terminal import Clr

from batools.docs import get_sphinx_settings
from sphinx.util.logging import WarningStreamHandler

if TYPE_CHECKING:
    from docutils import nodes
    from typing import Any

    from sphinx.application import Sphinx


settings = get_sphinx_settings(projroot=os.environ['BALLISTICA_ROOT'])

# -- Options for HTML output -------------------------------------------------
# For more themes visit https://sphinx-themes.org/
html_theme = 'furo'  # python_docs_theme, groundwork, furo, sphinx_rtd_theme
html_title = f'{settings.project_name} Developer\'s Guide'

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
# rst_prolog = f"""
# .. image:: {settings.logo_large}
#     :target: index.html
#     :alt: Ballistica Logo
# """
rst_prolog = """
"""

# Append to pages.
rst_epilog = """
"""

# We want to be warned of refs to missing things. We should either fix
# broken refs or add them to the ignore list here.
nitpicky = True
nitpick_ignore = [
    #
    # Stuff that is part of 'private' apis that we've intentionally
    # hidden despite having public naming. See 'skip_prefixes' below.
    ('py:class', 'v1prep.PagePrep'),
    ('py:class', 'bacommon.displayitem.Wrapper'),
    ('py:class', 'bacommon.displayitem.Item'),
    ('py:class', 'bacommon.displayitem.ItemTypeID'),
    #
    # Stuff that seems like we could fix (presumably issues due to not
    # importing things at runtime (only if TYPE_CHECKING), etc.)
    ('py:class', 'Enum'),
    ('py:class', 'Path'),
    ('py:class', 'bui.Widget'),
    ('py:class', 'bui.MainWindow'),
    ('py:class', 'bui.Lstr'),
    ('py:class', 'bs.Session'),
    ('py:class', 'bs.Activity'),
    ('py:class', 'bs.GameActivity'),
    ('py:class', 'bs.GameTip'),
    ('py:class', 'bs.Lstr'),
    ('py:class', 'bs.Texture'),
    ('py:class', 'bs.Mesh'),
    ('py:class', 'bascenev1.Time'),
    ('py:class', 'babase.SimpleSound'),
    ('py:meth', 'spawn_player_spaz'),
    ('py:class', 'Logger'),
    ('py:class', 'PlaylistType'),
    ('py:class', 'ValueDispatcherMethod'),
    #
    # 'Fake' classes declared with typing.NewType() so don't have
    # doctrings.
    ('py:class', 'babase.AppTime'),
    ('py:class', 'babase.DisplayTime'),
    ('py:class', 'bascenev1.BaseTime'),
    #
    # 3rd party stuff we don't gen docs for (could look into intersphinx).
    ('py:class', 'astroid.nodes.node_ng.NodeNG'),
    ('py:class', 'astroid.Manager'),
    #
    # TypeVars have no docs.
    ('py:class', 'T'),
    ('py:class', 'EnumT'),
    ('py:class', 'RetT'),
    ('py:class', 'ValT'),
    ('py:class', 'SelfT'),
    ('py:class', 'ArgT'),
    ('py:class', 'ExistableT'),
    ('py:class', 'PlayerT'),
    ('py:class', 'TeamT'),
    ('py:class', 'P'),
    ('py:class', 'P.args'),
    ('py:class', 'P.kwargs'),
    ('py:obj', 'typing.P'),
    ('py:obj', 'typing.T'),
    #
    # Unexposed internal types (should possibly just make these public?).
    ('py:class', '_MissingType'),
    #
    # Stdlib stuff for whatever reason coming up as having no docs.
    ('py:class', '_thread.lock'),
    ('py:meth', 'asyncio.get_running_loop'),
    ('py:class', 'asyncio.events.AbstractEventLoop'),
    ('py:class', 'asyncio.streams.StreamReader'),
    ('py:class', 'asyncio.streams.StreamWriter'),
    ('py:class', 'concurrent.futures.thread.ThreadPoolExecutor'),
    ('py:class', 'urllib3.response.BaseHTTPResponse'),
    ('py:class', 'socket.AddressFamily'),
    ('py:attr', 'socket.AF_INET'),
    ('py:attr', 'socket.AF_INET6'),
    ('py:class', 'weakref.ReferenceType'),
]

# Gives us links to common Python types.
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

extensions = [
    'sphinx.ext.napoleon',  # Allows google/numpy style docstrings.
    'sphinx.ext.autodoc',  # Parse docstrings.
    'sphinx.ext.viewcode',  # Adds 'source' links.
    'sphinx.ext.intersphinx',  # Allows linking to base Python types.
]

# Reduces ugly wrapping in the on-this-page sidebar.
toc_object_entries_show_parents = 'hide'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files. This pattern also
# affects html_static_path and html_extra_path.
exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
]


def _wrangle_logging() -> None:
    """Modify sphinx's warning handler to ignore very specific warnings
    (we don't want to ignore entire categories).
    """
    logger = logging.getLogger('sphinx')
    assert len(logger.handlers) == 3
    warning_handler = logger.handlers[1]
    assert isinstance(warning_handler, WarningStreamHandler)

    class _EfroCustomSphinxFilter(logging.Filter):

        _cross_ref_ignores_noted = set[str]()

        @override
        def filter(self, record: logging.LogRecord) -> bool:

            # Getting lots of warnings such as:
            # /Users/ericf/LocalDocs/ballistica-internal/
            # .cache/sphinxfiltered/ba_data/babase/__init__.py:docstring
            # of babase._error.ActivityNotFoundError:1: WARNING:
            # duplicate object description of
            # babase._error.ActivityNotFoundError, other instance in
            # bascenev1, use :no-index: for one of them
            #
            # These seem harmless and I assume are related to the fact
            # that we're re-exposing various classes through our various
            # high level package classes (babase, bauiv1, bascenev1,
            # etc.). So Just ignoring as long as one of our modules is
            # mentioned.
            if record.msg == (
                'duplicate object description of %s,'
                ' other instance in %s, use :no-index: for one of them'
            ):
                assert isinstance(record.args, tuple) and isinstance(
                    record.args[0], str
                )
                if any(
                    record.args[0].startswith(p)
                    for p in ['babase.', '_babase.']
                ):
                    return False  # Ignore.

            # Am seeing a fair number of 'more than one target found'
            # warnings for annotations with common type names such as
            # 'State'. In some of these cases such as nested dataclasses
            # we can't actually use fully qualified types, and Sphinx
            # seems to be linking to the correct places, so just
            # ignoring these.
            if (
                record.msg
                == 'more than one target found for cross-reference %r: %s'
            ):
                assert isinstance(record.args, tuple)
                classname = record.args[0]
                assert isinstance(classname, str)
                if classname not in self._cross_ref_ignores_noted:
                    print(
                        f'{Clr.BLD}efro-note:{Clr.RST}'
                        f' Ignoring (most-likely-harmless)'
                        f' more-than-one-target warning for'
                        f' "{classname}".'
                    )
                    self._cross_ref_ignores_noted.add(classname)
                return False  # Ignore.

            return True  # Don't ignore.

    # Explicitly insert our filter *before* sphinx's built in ones so we
    # can prevent sphinx from failing on warnings that we want to
    # ignore.
    warning_handler.filters.insert(0, _EfroCustomSphinxFilter())


_wrangle_logging()


# Prevent docs generation for particular packages that we consider
# 'private' despite having public naming. Note that these will still be
# listed under their parent package's page, but the only thing visible
# in them will be their module docstring (which should explain that they
# are private).
skip_prefixes = [
    'bauiv1lib.docui.v1prep.',
    'bacommon.displayitem.',
    'bacommon.net.',
    'bacommon.cloud.',
    'bacommon.transfer.',
    'bacommon.build.',
    'bacommon.bacloud.',
    'bacommon.assets.',
    'bacommon.bs.',
    'bacommon.clouddialog.',
    'bacommon.clienteffect.',
]

# Make sure we don't unintentionally skip 'foo.bar' by adding 'foo.b'
assert all(p.endswith('.') for p in skip_prefixes)


def skip_private_submodules(
    app: Sphinx, what: str, name: str, obj: Any, skip: bool, options: Any
) -> bool | None:
    """Skip submodules we consider private despite looking public."""
    # pylint: disable=too-many-positional-arguments
    del app, options  # Unused.

    # If this member is an actual module object
    if what == 'module' and isinstance(obj, types.ModuleType):
        fqname = obj.__name__
    # For everything else (functions, classes, etc.)
    else:
        modname = getattr(obj, '__module__', None)
        fqname = f'{modname}.{name}' if modname else name

    if any(fqname.startswith(p) for p in skip_prefixes):
        return True

    return skip


def setup(app: Sphinx) -> Any:
    """Do the thing."""
    app.connect('autodoc-skip-member', skip_private_submodules)
    return {
        'version': '1.0',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
