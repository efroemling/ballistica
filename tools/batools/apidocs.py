# Released under the MIT License. See LICENSE for details.
#
"""Finding the modules we flag as not-for-modders.

A documented module is flagged internal by carrying
:data:`INTERNAL_API_WARNING` in its module docstring. The docs build
shows such a module's page with its docstring only (so just the
warning and whatever explanation surrounds it), and the project checks
in ``batools.project._checks_apidocs`` keep the flag consistent. See
``docs/design/python-api-packages.md``.
"""

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

#: The exact block marking a module as internal api. Everything keys
#: off this text, so a reworded copy would silently stop counting.
INTERNAL_API_WARNING = (
    '.. warning::\n'
    '\n'
    '  This is an internal api and subject to change at any time. Do not'
    ' use\n'
    '  it in mod code.\n'
)

# Where the Sphinx docs pull Python from (see batools.docs); the
# dummy-module tree is generated from C++ and has no such docstrings.
_DOC_ROOTS = ('tools', 'src/assets/ba_data/python')


class ApiModule:
    """What we need to know about one documented module."""

    def __init__(self, name: str, path: Path, tree: ast.Module) -> None:
        self.name = name
        self.path = path
        self.tree = tree
        self.docstring = ast.get_docstring(tree, clean=False) or ''
        self.flagged = INTERNAL_API_WARNING in self.docstring
        self.is_package = path.name == '__init__.py'


def gather_documented_modules(projroot: Path) -> dict[str, ApiModule]:
    """Parse every module that gets a docs page, keyed by dotted name."""
    modules: dict[str, ApiModule] = {}
    for rootname in _DOC_ROOTS:
        root = projroot / rootname
        for path in sorted(root.rglob('*.py')):
            rel = path.relative_to(root)
            if not _is_documented(rel):
                continue
            parts = list(rel.with_suffix('').parts)
            if parts[-1] == '__init__':
                parts = parts[:-1]
            if not parts:
                continue
            name = '.'.join(parts)
            tree = ast.parse(path.read_text(encoding='utf-8'))
            modules[name] = ApiModule(name, path, tree)
    return modules


def flagged_packages(modules: dict[str, ApiModule]) -> set[str]:
    """Names of the flagged packages among some gathered modules."""
    return {
        mod.name for mod in modules.values() if mod.flagged and mod.is_package
    }


def flagged_ancestor(modname: str, flagged_pkgs: set[str]) -> str | None:
    """The nearest flagged package containing a module, if any."""
    parts = modname.split('.')
    for i in range(len(parts) - 1, 0, -1):
        pkg = '.'.join(parts[:i])
        if pkg in flagged_pkgs:
            return pkg
    return None


def internal_api_modules(projroot: Path) -> set[str]:
    """Names of all documented modules that are internal api.

    That is, flagged ones plus anything under a flagged package (which
    the project checks require to be flagged as well).
    """
    modules = gather_documented_modules(projroot)
    pkgs = flagged_packages(modules)
    return {
        mod.name
        for mod in modules.values()
        if mod.flagged or flagged_ancestor(mod.name, pkgs) is not None
    }


def _is_documented(rel: Path) -> bool:
    """Whether a module (path relative to a docs root) gets a page.

    Mirrors batools.docs: _single-underscore files and dirs are private
    implementation detail; tools/spinoff is a symlink excluded there.
    """
    if '__pycache__' in rel.parts or rel.parts[0] == 'spinoff':
        return False
    return not any(
        part.startswith('_') and not part.startswith('__') for part in rel.parts
    )
