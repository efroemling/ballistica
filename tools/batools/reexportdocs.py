# Released under the MIT License. See LICENSE for details.
#
"""Gather re-export docs info for sphinx.

For every documented module with ``__all__``, finds entries that are
instance re-exports (not classes/functions/modules), traces them to
their canonical home, and extracts the ``#:`` comment block plus
type info. The sphinx generator uses this to inject forward-declare
blocks into filtered consumer ``__init__.py`` files so re-exported
instances get documented at every public package, not only at the
canonical home.

Design rationale: ``docs/design/python-api-packages.md``. Anything
in a package's ``__all__`` is part of that package's public API and
should appear on its docs page.

Hard error if any public instance lacks a ``#:`` comment block at
its canonical home. Forces every public instance to be documented
rather than silently producing a stub.
"""

from __future__ import annotations

import os
import sys
import ast
import json
import inspect
import subprocess
import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efro.terminal import Clr
from efro.error import CleanError

if TYPE_CHECKING:
    from typing import Any


#: Packages we walk for re-export info. Anything not in this list
#: simply doesn't get the autogen treatment — its re-exported
#: instances won't be documented at the re-export site. The
#: ballistica top-level packages plus their lib siblings cover
#: the user-facing API surface; expand here when adding new
#: featuresets.
_PACKAGES: list[str] = [
    'babase',
    'baclassic',
    'baplus',
    'bascenev1',
    'bascenev1lib',
    'batemplatefs',
    'bauiv1',
    'bauiv1lib',
    'baenv',
]


@dataclass
class Injection:
    """One forward-declare to inject into a consumer ``__init__.py``."""

    name: str  # the public name (e.g. 'app')
    type_str: str  # the annotation text (e.g. "'babase.App'")
    comment: str  # the full #: block, including leading #: markers


def gather_reexport_injections(
    projroot: str, filtered_ba_data_dir: str
) -> dict[str, list[Injection]]:
    """Orchestrate: spawn worker, parse JSON, return injections.

    Returns a mapping from absolute filtered-init-file path to a
    list of injections to prepend at that file's top.

    Raises ``CleanError`` if any public instance lacks a ``#:``
    comment at its canonical home.
    """
    print(f'{Clr.BLU}{Clr.BLD}' f'Gathering re-export docs info...{Clr.RST}')

    # Use dummy-modules just like vanilla_completions and the
    # sphinx-build subprocess itself; otherwise C-extension stubs
    # don't resolve.
    subprocess.run(['make', 'dummymodules'], check=True, cwd=projroot)

    outpath = os.path.join(projroot, 'build', 'reexport_docs.json')
    os.makedirs(os.path.dirname(outpath), exist_ok=True)

    assert (
        'PYTHONPATH' not in os.environ
    ), 'Refusing to clobber an existing PYTHONPATH'
    # Source PYTHONPATH — we want imports to land in the real
    # source files so ``inspect.getsourcefile`` and the AST walk
    # see the ``#:`` comments where humans wrote them, not in the
    # filtered copy (which may already have been edited).
    ba_data = os.path.join(projroot, 'src/assets/ba_data/python')
    tools = os.path.join(projroot, 'tools')
    dummies = os.path.join(projroot, 'build/dummymodules')
    environ = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE='1',
        BA_RUNNING_WITH_DUMMY_MODULES='1',
        PYTHONPATH=f'{ba_data}:{tools}:{dummies}',
    )
    subprocess.run(
        [sys.executable, '-m', 'batools.reexportdocs', outpath],
        env=environ,
        check=True,
        cwd=projroot,
    )

    with open(outpath, encoding='utf-8') as infile:
        data = json.load(infile)

    if data.get('missing'):
        lines = [
            f"  {m['module']}.{m['name']}"
            f" (canonical at {m['canonical_module']})"
            for m in data['missing']
        ]
        missing_count = len(data['missing'])
        raise CleanError(
            f'{missing_count} public instance(s) lack a #:'
            f' comment block at their canonical home:\n'
            + '\n'.join(lines)
            + '\n\nAdd a #: block above each canonical assignment.'
            ' See docs/design/python-api-packages.md.'
        )

    # Worker reports by package name; map to filtered __init__.py paths.
    result: dict[str, list[Injection]] = {}
    for pkg, raw_injections in data['injections'].items():
        init_path = _filtered_init_for_package(filtered_ba_data_dir, pkg)
        if init_path is None:
            print(
                f'{Clr.YLW}reexportdocs: skipping {pkg!r} —'
                f' no filtered __init__.py found{Clr.RST}',
                file=sys.stderr,
            )
            continue
        result[init_path] = [Injection(**inj) for inj in raw_injections]
    return result


def _filtered_init_for_package(
    filtered_ba_data_dir: str, pkg: str
) -> str | None:
    """Locate the consumer ``__init__.py`` (or single .py) under the
    filtered tree for a given package name."""
    candidate_dir = os.path.join(filtered_ba_data_dir, pkg, '__init__.py')
    if os.path.isfile(candidate_dir):
        return candidate_dir
    candidate_single = os.path.join(filtered_ba_data_dir, f'{pkg}.py')
    if os.path.isfile(candidate_single):
        return candidate_single
    return None


def _worker_main(outpath: str) -> None:
    """Worker side: import packages, gather + emit injection plan.

    Invoked as ``python -m batools.reexportdocs <outpath>``.
    """
    injections: dict[str, list[dict[str, str]]] = {}
    missing: list[dict[str, str]] = []

    for modname in _PACKAGES:
        try:
            mod = importlib.import_module(modname)
        except Exception as exc:
            print(
                f'{Clr.YLW}reexportdocs: skipping {modname!r}'
                f' (import failed: {exc}){Clr.RST}',
                file=sys.stderr,
            )
            continue
        all_names = getattr(mod, '__all__', None)
        if not all_names:
            continue

        for name in all_names:
            try:
                value = getattr(mod, name)
            except AttributeError:
                continue
            # Classes/functions/modules are handled directly by
            # sphinx's autodoc machinery — they carry their own
            # docstrings. Only instances need our help.
            if (
                inspect.isclass(value)
                or inspect.isroutine(value)
                or inspect.ismodule(value)
            ):
                continue

            decl = _find_canonical_decl(modname, name)
            if decl is None:
                # Cannot find an assignment — likely an unusual
                # pattern (descriptor, dynamic attribute, etc.).
                # Skip silently; not a clear documentation gap.
                continue

            canonical_module, comment, type_str = decl

            # Resolve type via runtime if AST didn't get one (e.g.
            # plain ``name = Foo()`` assignment with no annotation).
            if type_str is None:
                type_str = _runtime_type_str(value)

            if comment is None:
                missing.append(
                    {
                        'module': modname,
                        'name': name,
                        'canonical_module': canonical_module,
                    }
                )
                continue

            injections.setdefault(modname, []).append(
                {
                    'name': name,
                    'type_str': type_str,
                    'comment': comment,
                }
            )

    with open(outpath, 'w', encoding='utf-8') as outfile:
        json.dump(
            {'injections': injections, 'missing': missing},
            outfile,
            indent=1,
            sort_keys=True,
        )
        outfile.write('\n')


def _find_canonical_decl(
    start_module: str, name: str
) -> tuple[str, str | None, str | None] | None:
    """Walk import chains to the assignment site for ``name``.

    Returns ``(canonical_module, comment, type_str)`` where:
      - ``canonical_module`` is the module name where the actual
        assignment lives (after following any ``from X import name``
        chains).
      - ``comment`` is the ``#:`` block immediately above the
        assignment (full text, including leading ``#:``), or
        ``None`` if there is no such block.
      - ``type_str`` is the annotation text if the assignment is
        annotated (``name: T = ...``), else ``None``.

    Returns ``None`` if the assignment can't be located at all —
    typically means the name is set dynamically (descriptor,
    setattr, etc.).
    """
    visited: set[str] = set()
    current_module = start_module
    current_name = name

    while True:
        if current_module in visited:
            return None  # cycle, give up
        visited.add(current_module)
        scan = _scan_module_for_name(current_module, current_name)
        if scan is None:
            return None
        if isinstance(scan, _ScanFound):
            return (current_module, scan.comment, scan.type_str)
        current_module = scan.new_module
        current_name = scan.new_name


@dataclass
class _ScanFound:
    """Returned by ``_scan_module_for_name`` when the assignment is here."""

    comment: str | None
    type_str: str | None


@dataclass
class _ScanRedirect:
    """Returned when the name is re-imported from another module."""

    new_module: str
    new_name: str


def _scan_module_for_name(
    modname: str, name: str
) -> _ScanFound | _ScanRedirect | None:
    """Scan one module's source for ``name``.

    Returns one of:
      - ``_ScanFound`` if ``name`` is assigned here.
      - ``_ScanRedirect`` if ``name`` is re-imported (follow the chain).
      - ``None`` if the name doesn't appear at module-level here.
    """
    try:
        mod = importlib.import_module(modname)
    except Exception:
        return None
    src = inspect.getsourcefile(mod)
    if not src or not os.path.isfile(src):
        return None
    with open(src, encoding='utf-8') as infile:
        source = infile.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    for node in tree.body:
        if isinstance(
            node, (ast.Assign, ast.AnnAssign)
        ) and _assignment_targets_name(node, name):
            comment = _extract_hash_colon_block(source, node.lineno)
            type_str: str | None = None
            if isinstance(node, ast.AnnAssign):
                try:
                    type_str = ast.unparse(node.annotation)
                except Exception:
                    type_str = None
            return _ScanFound(comment=comment, type_str=type_str)
        if isinstance(node, ast.ImportFrom):
            redirect = _import_from_redirect(node, name, modname)
            if redirect is not None:
                return redirect
    return None


def _import_from_redirect(
    node: ast.ImportFrom, name: str, current_module: str
) -> _ScanRedirect | None:
    """If ``node`` brings in ``name``, return where to redirect to."""
    if not node.module:
        return None
    for alias in node.names:
        matched_local = alias.asname if alias.asname else alias.name
        if matched_local != name:
            continue
        target = _resolve_import_module(current_module, node.module, node.level)
        new_name = alias.name if alias.asname else name
        return _ScanRedirect(new_module=target, new_name=new_name)
    return None


def _assignment_targets_name(
    node: ast.Assign | ast.AnnAssign, name: str
) -> bool:
    if isinstance(node, ast.AnnAssign):
        return isinstance(node.target, ast.Name) and node.target.id == name
    # ast.Assign — can have multiple targets, each can be tuple/list.
    for target in node.targets:
        if isinstance(target, ast.Name) and target.id == name:
            return True
        if isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                if isinstance(elt, ast.Name) and elt.id == name:
                    return True
    return False


def _extract_hash_colon_block(source: str, assign_lineno: int) -> str | None:
    """Read the ``#:`` block immediately preceding an assignment.

    Returns the full block text (each line including the leading
    ``#:`` marker, newline-joined) or ``None`` if there's no such
    block.
    """
    lines = source.splitlines()
    # ast lineno is 1-based; convert to 0-based index.
    idx = assign_lineno - 1
    block: list[str] = []
    i = idx - 1
    while i >= 0:
        stripped = lines[i].lstrip()
        if stripped.startswith('#:'):
            block.append(lines[i].strip())
            i -= 1
            continue
        # Allow blank lines to interrupt? No — must be contiguous
        # right above the assignment, per sphinx's convention.
        break
    if not block:
        return None
    block.reverse()
    return '\n'.join(block)


def _resolve_import_module(current_module: str, module: str, level: int) -> str:
    """Resolve a ``from X import ...`` target name into absolute form."""
    if level == 0:
        return module
    parts = current_module.split('.')
    if level > len(parts):
        return module
    base = '.'.join(parts[: len(parts) - level + 1])
    return f'{base}.{module}' if module else base


def _runtime_type_str(value: object) -> str:
    """Best-effort runtime type-name string for ``value``.

    Used when the canonical assignment is bare (``name = Foo()``)
    so we infer the type from the value. Returns a string suitable
    for use as a string annotation (e.g. ``'babase.App'``).
    """
    t = type(value)
    mod = getattr(t, '__module__', None) or ''
    qual = getattr(t, '__qualname__', None) or t.__name__
    if mod and mod != 'builtins':
        return f"'{mod}.{qual}'"
    return f"'{qual}'"


def apply_injections(
    injections: dict[str, list[Injection]],
) -> None:
    """Prepend forward-declare blocks to filtered consumer files.

    Inserts the synthesized block after any ``from __future__``
    statements (so it doesn't disrupt PEP 236 ordering) and before
    everything else. Idempotent in the sense that each ``make
    docs`` rebuilds from a fresh copy of sources, so we never need
    to detect previously-injected content.
    """
    for path, items in injections.items():
        if not items:
            continue
        with open(path, encoding='utf-8') as infile:
            source = infile.read()

        block = _build_injection_block(items)
        new_source = _insert_after_future_imports(source, block)

        with open(path, 'w', encoding='utf-8') as outfile:
            outfile.write(new_source)


def _build_injection_block(items: list[Injection]) -> str:
    """Compose the synthesized declaration block.

    Annotations are emitted as **string literals** so the consumer
    module doesn't need to import every referenced type. sphinx
    handles string annotations correctly via PEP 563 semantics, and
    mypy/pylint/runtime never have to evaluate them.
    """
    pieces = [
        '# === Auto-generated re-export annotations'
        ' (see batools.reexportdocs) ===',
    ]
    for item in items:
        pieces.append('')
        pieces.append(item.comment)
        ann_quoted = _as_string_annotation(item.type_str)
        pieces.append(f'{item.name}: {ann_quoted}')
    pieces.append('# === End auto-generated ===')
    return '\n'.join(pieces) + '\n'


def _as_string_annotation(type_str: str) -> str:
    """Wrap a type expression in a string literal.

    ``type_str`` may already be quoted (the runtime fallback path
    returns ``'babase.App'`` with quotes); in that case return it
    as-is. Otherwise wrap with single quotes, escaping any internal
    single quotes.
    """
    s = type_str.strip()
    if (s.startswith("'") and s.endswith("'")) or (
        s.startswith('"') and s.endswith('"')
    ):
        return s
    # Annotation expressions can legitimately contain single quotes
    # (e.g. ``Literal['foo']``). Double-quote in that case.
    if "'" in s:
        return f'"{s}"'
    return f"'{s}'"


def _insert_after_future_imports(source: str, block: str) -> str:
    """Splice ``block`` after the last ``from __future__`` import.

    Falls back to inserting after the module docstring (if present)
    or at the very top.
    """
    lines = source.splitlines(keepends=True)
    insert_at = 0
    # Skip past a top-of-file docstring expressed as a string
    # literal statement.
    if lines and lines[0].lstrip().startswith(('"""', "'''", '#')):
        # Simplest: just walk forward through comment/string lines.
        pass
    # Walk for the last from __future__ import.
    last_future_idx = -1
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith('from __future__'):
            last_future_idx = i
    if last_future_idx >= 0:
        insert_at = last_future_idx + 1
    else:
        # No __future__ import — insert at top.
        insert_at = 0

    return (
        ''.join(lines[:insert_at])
        + '\n'
        + block
        + '\n'
        + ''.join(lines[insert_at:])
    )


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise CleanError('Expected single arg: <outpath>')
    _worker_main(sys.argv[1])
