# Released under the MIT License. See LICENSE for details.
#
"""Checks keeping internal apis from leaking into the public docs.

A documented module is flagged internal by carrying the warning block
in :data:`batools.apidocs.INTERNAL_API_WARNING` in its module docstring
(see ``docs/design/python-api-packages.md``). The docs build shows such
a module's page with its docstring only, so these checks make sure the
flag is spelled so tooling can see it, covers everything under a
flagged package, and isn't sidestepped by a public module re-exporting
internal names.
"""

import ast
from typing import TYPE_CHECKING
from pathlib import Path

from efro.error import CleanError

from batools.apidocs import (
    gather_documented_modules,
    flagged_packages,
    flagged_ancestor,
)

if TYPE_CHECKING:
    from batools.apidocs import ApiModule
    from batools.project._updater import ProjectUpdater


def check_internal_api_modules(self: ProjectUpdater) -> None:
    """Check modules flagged as internal api (and what they touch).

    - A docstring mentioning "internal api" must carry the exact
      warning block, or nothing sees the flag.
    - Every documented module under a flagged package must be flagged
      too; each gets its own docs page, which otherwise shows no
      warning.
    - A public (unflagged) documented module must not list a name
      imported from an internal module in its ``__all__``; that puts
      the internal thing in the public docs under a public name.
    """
    projroot = Path(self.projroot)
    modules = gather_documented_modules(projroot)
    pkgs = flagged_packages(modules)
    errors: list[str] = []
    for mod in modules.values():
        rel = mod.path.relative_to(projroot)
        errors += [
            f'{rel}: {err}' for err in _module_errors(mod, modules, pkgs)
        ]
    if errors:
        raise CleanError('Internal-api doc check failed:\n' + '\n'.join(errors))


def _module_errors(
    mod: ApiModule, modules: dict[str, ApiModule], flagged_pkgs: set[str]
) -> list[str]:
    """All problems with one module (see check_internal_api_modules)."""
    if mod.flagged:
        return []
    if 'internal api' in mod.docstring.lower():
        return [
            'docstring mentions an internal api but lacks the exact'
            ' warning block (see batools.apidocs.INTERNAL_API_WARNING).'
        ]
    pkg = flagged_ancestor(mod.name, flagged_pkgs)
    if pkg is not None:
        return [
            f'under internal-api package {pkg} but not flagged itself;'
            ' its docs page shows no warning. Add the warning block (or'
            ' make it an _underscore module).'
        ]

    def _is_internal(modname: str) -> bool:
        other = modules.get(modname)
        if other is not None and other.flagged:
            return True
        return flagged_ancestor(modname, flagged_pkgs) is not None

    exported = _dunder_all(mod.tree)
    errors: list[str] = []
    for node in ast.walk(mod.tree):
        if not isinstance(node, ast.ImportFrom) or node.level != 0:
            continue
        src = node.module
        if src is None:
            continue
        for alias in node.names:
            localname = alias.asname or alias.name
            # (The name may be a submodule rather than a member.)
            if localname in exported and (
                _is_internal(src) or _is_internal(f'{src}.{alias.name}')
            ):
                errors.append(
                    f'public __all__ exports {localname!r} from internal'
                    f' api {src}. Flag this module internal too, or stop'
                    ' exporting it.'
                )
    return errors


def _dunder_all(tree: ast.Module) -> set[str]:
    """Names in a module's literal top-level ``__all__`` (if any)."""
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == '__all__'
                for t in node.targets
            )
            and isinstance(node.value, (ast.List, ast.Tuple))
        ):
            return {
                elt.value
                for elt in node.value.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            }
    return set()
