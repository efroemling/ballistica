# Released under the MIT License. See LICENSE for details.
#
"""Generate a JSON completion index for the vanilla Ballistica API.

Driven by ``make vanilla_completions`` via lazybuild. Output lands at
``build/vanilla_completions.json`` and is consumed by sibling
projects (e.g. bamaster's workspace code editor) that copy it into
their own source trees.

We rely on the same dummy-modules + ``PYTHONPATH`` setup the sphinx
docs generator uses (see ``batools.docs.generate_sphinx_docs``):
import the real runtime Python under
``src/assets/ba_data/python`` with the C-extension stubs from
``build/dummymodules`` available, then walk symbols with
``inspect.getmembers``.
"""

from __future__ import annotations

import os
import sys
import ast
import json
import inspect
import subprocess
import importlib
from typing import TYPE_CHECKING

from efro.terminal import Clr
from efro.error import CleanError

if TYPE_CHECKING:
    from typing import Any


#: Top-level runtime packages we surface in completions. Order does
#: not affect output (sorted at the end) — but mirrors the rough
#: subsystem layout.
_RUNTIME_MODULES = [
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

#: Module attribute names we never expose. ``__all__`` semantics are
#: messy across our tree so we filter by leading underscore and a
#: small ignore-set instead.
_SKIP_ATTRS = frozenset(
    {
        'annotations',  # __future__
        'TYPE_CHECKING',
    }
)


def generate_vanilla_completions(projroot: str) -> None:
    """Top-level entry: ensure dummy-modules and dispatch the worker.

    Runs as the orchestrator side. Keeps the orchestrator's own
    interpreter clean (no imports of babase/etc. here) by shelling
    out to a worker subprocess that does the real introspection
    work.
    """

    print(f'{Clr.BLU}{Clr.BLD}Generating vanilla completions...{Clr.RST}')

    # Dummy-modules must exist for the runtime imports to resolve.
    # ``make dummymodules`` is lazybuild-tracked so this is cheap
    # when fresh.
    subprocess.run(['make', 'dummymodules'], check=True, cwd=projroot)

    outdir = os.path.join(projroot, 'build')
    outpath = os.path.join(outdir, 'vanilla_completions.json')
    os.makedirs(outdir, exist_ok=True)

    # Match the sphinx env setup so dummy-module imports resolve
    # the same way docs generation does.
    assert (
        'PYTHONPATH' not in os.environ
    ), 'Refusing to clobber an existing PYTHONPATH'
    ba_data = os.path.join(projroot, 'src/assets/ba_data/python')
    tools = os.path.join(projroot, 'tools')
    dummies = os.path.join(projroot, 'build/dummymodules')
    environ = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE='1',
        BA_RUNNING_WITH_DUMMY_MODULES='1',
        # NOTE: we deliberately do *not* set
        # ``EFRO_SUPPRESS_SET_CANONICAL_MODULE_NAMES`` here even
        # though the sphinx generator does. Sphinx wants the
        # original-source ``__module__`` to find code links;
        # completion-chasing wants the public-rename names so
        # ``type(babase.app).__module__`` resolves to ``babase``
        # (and the editor can chain into ``babase.App.*`` entries)
        # instead of ``babase._app`` (which we don't emit).
        PYTHONPATH=f'{ba_data}:{tools}:{dummies}',
    )
    subprocess.run(
        [sys.executable, '-m', 'batools.vanillacompletions', outpath],
        env=environ,
        check=True,
        cwd=projroot,
    )

    print(f'{Clr.BLU}Wrote {outpath}.{Clr.RST}')


def _worker_main(outpath: str) -> None:
    """Worker side: import the runtime tree, dump completion JSON.

    Invoked as ``python -m batools.vanillacompletions <outpath>``
    from ``generate_vanilla_completions`` with the appropriate env
    in place.
    """
    entries: list[dict[str, Any]] = []
    # Maps a class's *real* source qualified name (where it lives
    # in our tree, e.g. ``babase._app.App``) to the *public*
    # qualified name we emit (``babase.App``). Built as we walk
    # classes; used to resolve variable types so chained completion
    # in the editor lands on entries we actually emit.
    aliases: dict[str, str] = {}

    for modname in _RUNTIME_MODULES:
        try:
            mod = importlib.import_module(modname)
        except Exception as exc:
            # Don't blow up the whole generator if one package fails
            # to import — surface the failure and continue. Cleaner
            # signal than a stack trace for partial coverage.
            print(
                f'{Clr.YLW}vanilla_completions: skipping {modname!r}'
                f' (import failed: {exc}){Clr.RST}',
                file=sys.stderr,
            )
            continue
        _emit_module(modname, mod, entries, aliases)

    # Resolve variable type_quals now that all classes have been
    # seen. type_qual can come in three forms at this point:
    #   1. A source-canonical qualname from ``type(value)``
    #      introspection (e.g. ``babase._app.App``) — resolve via
    #      ``aliases``.
    #   2. A public qualname that already matches an emitted entry
    #      (e.g. ``babase.App``) — leave as-is.
    #   3. A raw annotation string from ``__init__`` parsing
    #      (e.g. ``AppConfig``, ``babase.Env``, ``int | None``) —
    #      resolve via shortname lookup if it's a bare class name,
    #      otherwise drop ``type_qual`` (keep the annotation in
    #      ``detail`` for display).
    emitted_labels = {e['label'] for e in entries}
    shortnames: dict[str, list[str]] = {}
    for e in entries:
        if e['kind'] == 'class':
            short = e['label'].rsplit('.', 1)[-1]
            shortnames.setdefault(short, []).append(e['label'])

    for entry in entries:
        raw = entry.get('type_qual')
        if raw is None:
            continue
        resolved = _resolve_type_qual(raw, aliases, emitted_labels, shortnames)
        if resolved is not None:
            entry['type_qual'] = resolved
        else:
            # Complex annotation (subscript, multi-arg union, etc.)
            # or unknown class — drop type_qual so the editor
            # doesn't chain into a dead pointer. ``detail`` still
            # shows the annotation.
            del entry['type_qual']

    # Stable order so JSON diffs are reviewable when this is checked
    # into bamaster.
    entries.sort(key=lambda e: e['label'])

    with open(outpath, 'w', encoding='utf-8') as outfile:
        json.dump(entries, outfile, indent=1, sort_keys=True)
        outfile.write('\n')


def _resolve_type_qual(
    raw: str,
    aliases: dict[str, str],
    emitted_labels: set[str],
    shortnames: dict[str, list[str]],
) -> str | None:
    """Try to resolve a raw annotation string to an emitted qualname.

    Tries the annotation as-is first, then peels off ``Optional[X]``
    / ``X | None`` / ``None | X`` and retries. Returns ``None`` if
    no resolution is possible.
    """
    for candidate in (raw, _strip_optional(raw)):
        if candidate is None:
            continue
        if candidate in aliases:
            return aliases[candidate]
        if candidate in emitted_labels:
            return candidate
        if candidate.isidentifier():
            matches = shortnames.get(candidate, [])
            if len(matches) == 1:
                return matches[0]
    return None


def _strip_optional(s: str) -> str | None:
    """Return the inner type of ``Optional[X]`` / ``X | None``.

    Returns ``None`` if the input isn't recognizably one of those
    forms, signalling "no further resolution to try."
    """
    s = s.strip()
    if s.startswith('Optional[') and s.endswith(']'):
        return s[len('Optional[') : -1].strip()
    if '|' in s:
        parts = [p.strip() for p in s.split('|')]
        non_none = [p for p in parts if p != 'None']
        if len(non_none) == 1 and len(parts) > 1:
            return non_none[0]
    return None


def _emit_module(
    qualname: str,
    mod: object,
    out: list[dict[str, Any]],
    aliases: dict[str, str],
    visited: set[str] | None = None,
) -> None:
    """Emit one ``module`` entry plus an entry per public attribute.

    Honors ``__all__`` as the package author's "this is part of my
    public surface" signal — see ``docs/design/python-api-packages.md``
    for the design rationale. Names listed in ``__all__`` bypass the
    ``__module__``-based owner check so re-exports (e.g. ``bauiv1.app``
    forwarding to ``babase.app``) are emitted under their importing
    package, not only at the canonical home.

    For packages (modules with ``__path__``), walks public submodules
    via ``pkgutil.iter_modules()`` and recurses. This is what makes
    completion work for libraries like ``bascenev1lib`` whose
    ``__init__.py`` doesn't pre-import its submodules — without the
    explicit walk those submodules are invisible to introspection.
    """
    if visited is None:
        visited = set()
    if qualname in visited:
        return
    visited.add(qualname)

    if _is_meta_private(mod):
        return
    out.append(
        {
            'label': qualname,
            'kind': 'module',
            'detail': _format_detail_module(qualname),
            'info': _short_doc(mod),
        }
    )

    all_names: set[str] = set(getattr(mod, '__all__', None) or ())

    # Recurse into public submodules discovered via package layout.
    # Skipped when the package declares ``__all__`` — there the
    # author's curated surface is the source of truth and we don't
    # want to surface submodules they didn't opt to re-export.
    if not all_names:
        _emit_package_submodules(qualname, mod, out, aliases, visited)

    for name, value in inspect.getmembers(mod):
        if _should_skip(name):
            continue
        if _is_meta_private(value):
            continue
        # Re-exports listed in ``__all__`` are public by design and
        # bypass the owner check. Everything else must originate
        # here (or in our paired private module) to avoid surfacing
        # incidental imports like ``babase.strict_partial``.
        is_canonical = True
        if name not in all_names:
            owner = getattr(value, '__module__', None)
            if owner is not None and not _owns(qualname, owner):
                continue
        else:
            owner = getattr(value, '__module__', None)
            if owner is not None and not _owns(qualname, owner):
                # In __all__, but the canonical home is elsewhere —
                # this is a re-export. Emit it, but don't claim
                # alias-ownership; the canonical-home walk does that
                # so chain resolution prefers the original namespace.
                is_canonical = False
        sub_qualname = f'{qualname}.{name}'
        entry = _build_entry(sub_qualname, value)
        if entry is None:
            continue
        out.append(entry)
        # When the attribute is a class, walk its members too AND
        # (canonical home only) record an alias from its source-
        # canonical name to the public name we're emitting under.
        # Canonical names are deliberately disabled in babase, so
        # without this map the editor would chain ``babase.app`` →
        # ``babase._app.App`` and miss our emitted ``babase.App.*``
        # entries. Re-exports skip the alias-write so chains land
        # on the canonical-home members (e.g. ``babase.App.*``
        # rather than ``bauiv1.App.*``).
        if inspect.isclass(value):
            if is_canonical:
                real_mod = getattr(value, '__module__', None) or ''
                real_qual = (
                    getattr(value, '__qualname__', None) or value.__name__
                )
                if real_mod:
                    aliases[f'{real_mod}.{real_qual}'] = sub_qualname
            _emit_class_members(sub_qualname, value, out)
            _emit_class_instance_attrs(sub_qualname, value, out)


def _emit_package_submodules(
    pkg_qualname: str,
    pkg: object,
    out: list[dict[str, Any]],
    aliases: dict[str, str],
    visited: set[str],
) -> None:
    """Discover and emit public submodules of a package.

    Some packages (notably ``bascenev1lib``, ``bauiv1lib``) don't
    pre-import their submodules in ``__init__.py``, so
    ``inspect.getmembers`` doesn't see them. Use ``pkgutil``
    to enumerate the filesystem-level submodules and recurse.

    Skips private (underscore-prefixed) submodules to match our
    general rule that anything ``_``-prefixed is implementation
    detail.
    """
    import pkgutil

    pkg_path = getattr(pkg, '__path__', None)
    if pkg_path is None:
        return  # not a package, nothing to enumerate

    for info in pkgutil.iter_modules(pkg_path):
        if _should_skip(info.name):
            continue
        sub_qualname = f'{pkg_qualname}.{info.name}'
        try:
            submod = importlib.import_module(sub_qualname)
        except Exception as exc:
            # Surface but don't blow up — some submodules might
            # fail to import under dummy-modules (e.g. ones that
            # need a real C-extension init).
            print(
                f'{Clr.YLW}vanilla_completions:'
                f' skipping {sub_qualname!r}'
                f' (import failed: {exc}){Clr.RST}',
                file=sys.stderr,
            )
            continue
        _emit_module(sub_qualname, submod, out, aliases, visited)


def _emit_class_members(
    cls_qualname: str, cls: type, out: list[dict[str, Any]]
) -> None:
    """Emit one entry per public attribute of a class.

    We use ``inspect.getmembers`` which includes inherited members.
    That duplicates entries across subclasses but keeps the editor
    side dumb — looking up ``Subclass.foo`` just works without an
    MRO walk in the browser.

    We also walk ``__annotations__`` for entries that exist only as
    type annotations with no class-level value (common in
    dummy-module C-extension class stubs and Python class-attr
    type-only declarations). Without this, classes like
    ``babase.Env`` would expose zero members.
    """
    seen: set[str] = set()
    for name, value in inspect.getmembers(cls):
        if _should_skip(name):
            continue
        if _is_meta_private(value):
            continue
        seen.add(name)
        sub_qualname = f'{cls_qualname}.{name}'
        entry = _build_entry(sub_qualname, value)
        if entry is not None:
            out.append(entry)

    # Class-level annotations. PEP 563 (``from __future__ import
    # annotations``) is used throughout the tree, so values here
    # are already strings. Skip non-string values defensively.
    annotations = getattr(cls, '__annotations__', None) or {}
    for name, ann in annotations.items():
        if _should_skip(name) or name in seen:
            continue
        if not isinstance(ann, str):
            continue
        seen.add(name)
        out.append(
            {
                'label': f'{cls_qualname}.{name}',
                'kind': 'variable',
                'detail': ann,
                'info': '',
                # Raw annotation; resolved through aliases /
                # shortnames in the worker's post-process.
                'type_qual': ann,
            }
        )


def _emit_class_instance_attrs(
    cls_qualname: str, cls: type, out: list[dict[str, Any]]
) -> None:
    """Emit ``self.X`` assignments from a class's ``__init__``.

    ``inspect.getmembers`` only sees class-level attributes;
    instance attributes assigned in ``__init__`` (e.g. ``self.env:
    babase.Env = ...``) are invisible to it. Pyright/Pylance solve
    this by AST-parsing the source — we do the same.

    Scope:
      - Only ``__init__`` (not arbitrary methods). Adding e.g.
        ``self.foo = ...`` mid-flow elsewhere happens, but
        ``__init__`` covers ~all the cases that matter for
        completion.
      - Annotated form (``self.X: T = ...``) yields ``T`` as the
        detail string and a raw ``type_qual`` we'll resolve later.
      - Plain form (``self.X = ...``) yields an entry with no
        type info — the user still sees ``X`` as a completion.
    """
    try:
        srcfile = inspect.getsourcefile(cls)
    except TypeError:
        return  # builtin/C-extension; nothing to parse
    if not srcfile or not os.path.isfile(srcfile):
        return

    try:
        with open(srcfile, encoding='utf-8') as infile:
            tree = ast.parse(infile.read())
    except (OSError, SyntaxError):
        return

    # Resolve the class node by walking the qualname path. Handles
    # nested classes naturally — e.g. ``Outer.Inner`` finds
    # ``Inner`` inside ``Outer.body``.
    qualparts = (cls.__qualname__ or cls.__name__).split('.')
    class_node = _find_classdef(tree.body, qualparts)
    if class_node is None:
        return

    init_node: ast.FunctionDef | None = None
    for item in class_node.body:
        if isinstance(item, ast.FunctionDef) and item.name == '__init__':
            init_node = item
            break
    if init_node is None:
        return

    # Pull self.X = ... and self.X: T = ... assignments.
    seen: set[str] = set()
    for stmt in init_node.body:
        if isinstance(stmt, ast.AnnAssign) and _is_self_attr(stmt.target):
            assert isinstance(stmt.target, ast.Attribute)
            name = stmt.target.attr
            if _should_skip(name) or name in seen:
                continue
            seen.add(name)
            ann_text = ast.unparse(stmt.annotation)
            entry: dict[str, Any] = {
                'label': f'{cls_qualname}.{name}',
                'kind': 'variable',
                'detail': ann_text,
                'info': '',
            }
            # Raw annotation text; resolved through aliases /
            # shortnames in the worker's post-process.
            entry['type_qual'] = ann_text
            out.append(entry)
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if not _is_self_attr(target):
                    continue
                assert isinstance(target, ast.Attribute)
                name = target.attr
                if _should_skip(name) or name in seen:
                    continue
                seen.add(name)
                out.append(
                    {
                        'label': f'{cls_qualname}.{name}',
                        'kind': 'variable',
                        'detail': '',
                        'info': '',
                    }
                )


def _find_classdef(
    body: list[ast.stmt], parts: list[str]
) -> ast.ClassDef | None:
    if not parts:
        return None
    target = parts[0]
    rest = parts[1:]
    for node in body:
        if isinstance(node, ast.ClassDef) and node.name == target:
            if not rest:
                return node
            return _find_classdef(node.body, rest)
    return None


def _is_self_attr(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == 'self'
    )


def _build_entry(qualname: str, value: object) -> dict[str, Any] | None:
    """Build a completion entry for a single symbol."""

    if inspect.ismodule(value):
        # Submodules are handled by the top-level walk only — we
        # don't recurse into arbitrary attribute modules here, since
        # that would re-emit stdlib things attached as attributes.
        return None

    type_qual: str | None = None
    if inspect.isclass(value):
        kind = 'class'
        detail = _format_detail_callable(qualname, value)
    elif inspect.isroutine(value):
        kind = 'function'
        detail = _format_detail_callable(qualname, value)
    elif isinstance(value, property):
        # Properties expose as attributes from the user's POV.
        # Pull the return annotation from the getter so chaining
        # works and the detail shows the actual type (rather than
        # the literal string "property").
        kind = 'variable'
        ret_ann = _property_return_annotation(value)
        if ret_ann:
            detail = ret_ann
            type_qual = ret_ann  # raw; resolved in post-process
        else:
            detail = 'property'
    else:
        kind = 'variable'
        t = type(value)
        detail = t.__name__
        type_qual = _ballistica_type_qualname(t)

    entry: dict[str, Any] = {
        'label': qualname,
        'kind': kind,
        'detail': detail,
        'info': _short_doc(value),
    }
    if type_qual is not None:
        # Only present for variables whose type lives in our tree;
        # the editor uses it to chain ``var.member`` completions
        # through to that class's members.
        entry['type_qual'] = type_qual
    return entry


def _property_return_annotation(prop: property) -> str | None:
    """Extract a property's getter return annotation, if any.

    Uses ``__future__`` annotations semantics so values come back
    as strings; nothing to ``eval``.
    """
    fget = prop.fget
    if fget is None:
        return None
    ann = getattr(fget, '__annotations__', None)
    if not ann:
        return None
    ret = ann.get('return')
    if isinstance(ret, str):
        return ret
    return None


def _ballistica_type_qualname(t: type) -> str | None:
    """Return a qualified type name, but only for Ballistica types.

    Skip ``builtins``/stdlib/etc.: those types' members aren't in
    our JSON, so a qualified name there would just be misleading.
    """
    mod = getattr(t, '__module__', None) or ''
    if not any(mod == m or mod.startswith(f'{m}.') for m in _RUNTIME_MODULES):
        return None
    qual = getattr(t, '__qualname__', None) or t.__name__
    return f'{mod}.{qual}'


def _format_detail_module(qualname: str) -> str:
    return f'module {qualname}'


def _format_detail_callable(qualname: str, value: object) -> str:
    try:
        sig = inspect.signature(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return qualname
    return f"{qualname.rsplit('.', 1)[-1]}{sig}"


def _short_doc(value: object) -> str:
    doc = inspect.getdoc(value)
    if not doc:
        return ''
    # First non-empty paragraph; CodeMirror's ``info`` panel handles
    # the rest of the docstring if/when we want it later.
    first = doc.split('\n\n', 1)[0].strip()
    return first


def _is_meta_private(value: object) -> bool:
    """True if the value's docstring marks it as ``:meta private:``.

    Sphinx convention: a ``:meta private:`` field anywhere in the
    docstring hides the item from generated docs. We honor the same
    marker so authors don't have to maintain a parallel hide-list
    for completions.
    """
    doc = inspect.getdoc(value)
    if not doc:
        return False
    # Match whole-line ``:meta private:`` (with optional leading
    # whitespace). Trailing-content variants like ``:meta private:
    # because foo`` would be unusual; if we ever see them we can
    # relax this.
    for line in doc.splitlines():
        if line.strip() == ':meta private:':
            return True
    return False


def _should_skip(name: str) -> bool:
    if name.startswith('_'):
        return True
    if name in _SKIP_ATTRS:
        return True
    return False


def _owns(modname: str, owner: str) -> bool:
    """True if ``owner`` is ``modname`` or a submodule of it.

    Also accepts the corresponding private/C-extension module —
    e.g. ``_babase`` is treated as part of ``babase``'s public
    surface since types like ``babase.Env`` are implemented there
    and re-exposed by convention. Without this, C-extension
    classes (``babase.Env``, ``babase.Vec3``, etc.) would be
    silently dropped from the completion index.
    """
    if owner == modname or owner.startswith(f'{modname}.'):
        return True
    priv = f'_{modname}'
    return owner == priv or owner.startswith(f'{priv}.')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise CleanError('Expected single arg: <outpath>')
    _worker_main(sys.argv[1])
