# Released under the MIT License. See LICENSE for details.
#
"""Codegen for type-safe language-string wrapper modules.

Given a :class:`~bacommon.langstr.PackageDef`, emit a Python module whose
``strings`` object gives type-safe, ergonomic access to the package's
strings: a no-arg string reads as a property yielding an
:class:`~bacommon.langstr.Lstr`; a parameterized one is a call that builds
an ``Lstr`` from keyword substitutions. Precise types live in an
``if TYPE_CHECKING`` shadow: a no-arg string is a ``name: Lstr`` annotation,
a parameterized one its own stub method (``def name(self, *, …) -> Lstr``)
-- readable inline and a home for a future per-string docstring. Runtime
resolution is the dynamic :class:`~bacommon.langstr.LangStrDir` (no
per-entry runtime class -- decision #28).

Logical paths split on ``/`` into subdir nesting (``ui/mainmenu/play`` ->
``strings.ui.mainmenu.play``); each path segment must be an identifier.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bacommon.langstr._core import PackageDef, StringDef


def _param_type(kind: str) -> str:
    """Annotation for one substitution keyword by its kind."""
    # 'count' is the plural pivot (an int); anything else is a text sub,
    # which accepts a literal string or a nested language-string.
    return 'int' if kind == 'count' else 'str | Lstr'


#: A nested name tree: a leaf maps a name to its :class:`StringDef`, a
#: subdir maps a name to a nested tree (paths split on ``/``).
type _Tree = dict[str, 'StringDef | _Tree']

#: The runtime form of the tree (no kinds): leaf -> param-keyword tuple.
type _RuntimeTree = dict[str, 'tuple[str, ...] | _RuntimeTree']


def _build_tree(strings: tuple[StringDef, ...]) -> _Tree:
    """Split each ``foo/bar`` logical path into a nested name tree."""
    root: _Tree = {}
    for sdef in strings:
        parts = sdef.path.split('/')
        node = root
        for part in parts[:-1]:
            child = node.get(part)
            if child is None:
                child = {}
                node[part] = child
            if not isinstance(child, dict):
                raise ValueError(
                    f'path {sdef.path!r} collides with a string at {part!r}'
                )
            node = child
        leaf = parts[-1]
        if leaf in node:
            raise ValueError(f'duplicate string path {sdef.path!r}')
        node[leaf] = sdef
    return root


def _pascal_case(segment: str) -> str:
    """``some_thing`` -> ``SomeThing``."""
    return ''.join(part.capitalize() for part in segment.split('_'))


def _dir_class_name(segments: list[str]) -> str:
    """Public class name for a group subtree (mirrors the client wrappers).

    The root is ``StringsLibrary``; a subdir is its path PascalCased +
    ``Group`` (``['ui', 'menu']`` -> ``UiMenuGroup``).
    """
    if not segments:
        return 'StringsLibrary'
    return ''.join(_pascal_case(s) for s in segments) + 'Group'


def _emit_dir_classes(out: list[str], tree: _Tree, segments: list[str]) -> None:
    """Emit the typed class for this dir (children first, so refs resolve).

    A subdir is a typed attribute pointing at its group class; a no-arg
    string is a property-style ``name: Lstr``; a parameterized string is its
    own stub method (readable inline, and a home for a future docstring).
    """
    for name in sorted(tree):
        value = tree[name]
        if isinstance(value, dict):
            _emit_dir_classes(out, value, [*segments, name])
    label = '/'.join(segments) if segments else 'library root'
    out += [
        f'    class {_dir_class_name(segments)}:',
        f'        """Type-safe language-string accessors ({label})."""',
        '',
    ]
    for name in sorted(tree):
        value = tree[name]
        if isinstance(value, dict):
            sub = _dir_class_name([*segments, name])
            out.append(f'        {name}: {sub}')
        elif value.params:
            args = ', '.join(
                f'{k}: {_param_type(kind)}' for k, kind in value.params
            )
            out.append(f'        def {name}(self, *, {args}) -> Lstr: ...')
        else:
            out.append(f'        {name}: Lstr')
    out.append('')


def _runtime_tree(tree: _Tree) -> _RuntimeTree:
    out: _RuntimeTree = {}
    for name, value in tree.items():
        out[name] = (
            _runtime_tree(value)
            if isinstance(value, dict)
            else tuple(k for k, _kind in value.params)
        )
    return out


def generate_wrapper_module(pkgdef: PackageDef) -> str:
    """Return the ``.py`` source for a package's type-safe wrapper.

    The output is valid but not auto-formatted (the long ``_TREE`` literal
    in particular); a caller writing it to the tree should run the
    formatter before committing.
    """
    for sdef in pkgdef.strings:
        for part in sdef.path.split('/'):
            if not part.isidentifier():
                raise ValueError(f'bad path segment {part!r} in {sdef.path!r}')
    tree = _build_tree(pkgdef.strings)

    out: list[str] = [
        '# Released under the MIT License. See LICENSE for details.',
        '#',
        '# AUTO-GENERATED by bacommon.langstr codegen; do not edit by hand.',
        f'"""Type-safe language-string accessors for {pkgdef.apverid}."""',
        '',
        'from typing import TYPE_CHECKING',
        '',
        'from bacommon.langstr import LangStrDir',
        '',
        f"__asset_package__ = '{pkgdef.apverid}'",
        '',
        'if TYPE_CHECKING:',
        '    from bacommon.langstr import Lstr, WrapperTree',
        '',
    ]
    _emit_dir_classes(out, tree, [])
    out += [
        f'    strings: {_dir_class_name([])}',
        '',
        # `_TREE` lives at module level (not in the `if not TYPE_CHECKING`
        # block) so consumers can read it statically -- mirroring the
        # client asset-package wrappers (bauiv1/builtinassets.py). Annotated
        # WrapperTree so consumers get a typed tree (and the literal is
        # checked against the shape).
        f'_TREE: WrapperTree = {_runtime_tree(tree)!r}',
        '',
        'if not TYPE_CHECKING:',
        '    strings = LangStrDir(__asset_package__, _TREE)',
        '',
    ]
    return '\n'.join(out)
