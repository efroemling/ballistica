# Released under the MIT License. See LICENSE for details.
#
"""Plugins for pylint"""

import os

from functools import lru_cache
from typing import TYPE_CHECKING

import astroid.nodes
from pylint.checkers import BaseChecker

if TYPE_CHECKING:
    from pylint.lint import PyLinter

# Calced once at import; pylint runs with cwd at the project root in
# all of our setups (make pylint, checkenv, etc).
_PROJECT_ROOT = os.path.realpath(os.getcwd()) + os.sep

# Additional first-party roots beyond the project root, for tooling that
# lints code living outside the project tree and wants it treated as our
# own. The bamaster workspace checker is the motivating case: it
# materializes user code into a separate cache dir and sets this so our
# transforms (TYPE_CHECKING wipe, annotation stripping) apply to it just
# like the main codebase. Set via the EFRO_PYLINT_FIRST_PARTY_ROOTS env
# var (os.pathsep-separated paths), read once at import.
_EXTRA_FIRST_PARTY_ROOTS = tuple(
    os.path.realpath(p) + os.sep
    for p in os.environ.get('EFRO_PYLINT_FIRST_PARTY_ROOTS', '').split(
        os.pathsep
    )
    if p
)


def ignore_type_check_filter(
    if_node: astroid.nodes.NodeNG,
) -> astroid.nodes.NodeNG:
    """Ignore stuff under a module-level ``if TYPE_CHECKING:`` block.

    Such blocks run only under static analysis, never at runtime, so we
    want pylint to check our code as if they don't exist.

    Note: we deliberately handle only *module-level* blocks. A nested
    ``if TYPE_CHECKING:`` (inside a function or method) can contain
    control-flow — a common idiom here is ``if TYPE_CHECKING: return
    <type-fiction>`` paired with a real runtime ``return``. Wiping such a
    block to ``pass`` strips the ``return``, and there's no restructuring
    that satisfies both pylint (which sees the wiped tree) and mypy
    (which sees ``TYPE_CHECKING`` as True) without *some* suppression —
    so nested handling just trades one suppression for another with no
    real gain. Module-level blocks can't contain control flow, so
    they're unambiguously safe to wipe.
    """

    # Match both the bare ``TYPE_CHECKING`` name and the
    # ``typing.TYPE_CHECKING`` attribute form, at module top-level only.
    test = if_node.test
    is_type_checking = (
        isinstance(test, astroid.nodes.Name) and test.name == 'TYPE_CHECKING'
    ) or (
        isinstance(test, astroid.nodes.Attribute)
        and test.attrname == 'TYPE_CHECKING'
    )
    if not is_type_checking or not isinstance(
        if_node.parent, astroid.nodes.Module
    ):
        return if_node

    # Only apply this to our own code. Wiping TYPE_CHECKING blocks out
    # of stdlib/third-party modules breaks pylint inference that depends
    # on them; scoping to first-party is what the annotation filters
    # already do, and it makes the old ad-hoc denylist of specific
    # third-party modules (openai, filelock, aiohttp, ...) unnecessary.
    if not _is_first_party_module(if_node):
        return if_node

    # Remove any names defined directly under this block from the module
    # scope, so pylint sees them as nonexistent at runtime. We key off
    # each local's enclosing *statement* (see ``_under_if``) so that
    # assignments are scrubbed too, not just imports/defs — leaving an
    # assignment's target in ``.locals`` while wiping its statement from
    # the tree leads to astroid ``locate_child`` crashes downstream.
    #
    # (We only handle direct children here; a name defined under a
    # further-nested compound statement inside the block won't be
    # scrubbed. That's a rare case and not worth the recursion.)
    module_node = if_node.parent
    for name, locations in list(module_node.locals.items()):
        # Calc which remaining name locations are outside of the if
        # block. Update or delete the list as needed.
        new_locs = [l for l in locations if not _under_if(l, if_node)]
        if len(new_locs) == len(locations):
            continue
        if new_locs:
            module_node.locals[name] = new_locs
            continue
        del module_node.locals[name]

    # Now replace its children with a simple pass statement.
    passnode = astroid.nodes.Pass(
        parent=if_node,
        lineno=if_node.lineno + 1,
        end_lineno=if_node.lineno + 1,
        col_offset=if_node.col_offset + 1,
        end_col_offset=if_node.col_offset + 1,
    )
    if_node.body = [passnode]
    return if_node


def _under_if(
    node: astroid.nodes.NodeNG, if_node: astroid.nodes.NodeNG
) -> bool:
    """Return whether the node is defined directly in the if's body.

    Returns False if it lives under an elif/else portion, or nested
    deeper than the body's top level.

    We compare the node's enclosing *statement* against the if-body
    rather than the node itself: a locals entry can be the defining
    statement directly (imports, def/class) or a name buried inside one
    (an ``AssignName`` whose parent is its ``Assign``). Keying off the
    statement handles all of these uniformly — important, because a
    leftover assignment target whose statement we wiped will crash
    astroid inference later (``locate_child`` can't find it).
    """
    try:
        stmt = node.statement()
    except astroid.exceptions.StatementMissing:
        return False
    return stmt in if_node.body


def ignore_reveal_type_call(node: astroid.nodes.NodeNG) -> astroid.nodes.NodeNG:
    """Make ``reveal_type()`` not trigger an error.

    The 'reveal_type()' fake call is used for type debugging types with
    mypy and it is annoying having pylint errors pop up alongside the mypy
    info.
    """

    # Let's just replace any reveal_type(x) call with print(x)..
    if (
        isinstance(node.func, astroid.nodes.Name)
        and node.func.name == 'reveal_type'
    ):
        node.func.name = 'print'
        return node
    return node


@lru_cache(maxsize=None)
def _path_is_first_party(fpath: str | None) -> bool:
    """Return whether a module file path is part of our own code.

    Memoized: this is consulted for every function, class, and
    annotated-assign node across every module pylint builds (including
    third-party deps it infers through), and ``os.path.realpath`` is a
    syscall — but the answer depends only on the path.
    """
    if not isinstance(fpath, str):
        return False
    if 'site-packages' in fpath:
        return False
    # First-party means living under the project we're being run on
    # (pylint runs from the project root in all our setups) or under an
    # explicitly-configured extra root (see _EXTRA_FIRST_PARTY_ROOTS).
    # Checking against the prefix the interpreter lives under is
    # unreliable here (symlinked installs like Homebrew report stdlib
    # paths that don't match sys.base_prefix).
    return os.path.realpath(fpath).startswith(
        (_PROJECT_ROOT, *_EXTRA_FIRST_PARTY_ROOTS)
    )


def _is_first_party_module(node: astroid.nodes.NodeNG) -> bool:
    """Return whether a node hails from our own code.

    Our annotation filters should only apply to first-party code;
    wiping annotations in stdlib/third-party modules breaks pylint
    inference that depends on them (e.g. ``typing.assert_never``'s
    ``Never`` return informing inconsistent-return-statements).
    Previously this scoping happened implicitly because filters keyed
    off the presence of ``from __future__ import annotations``, which
    stdlib/most-third-party code never used.
    """
    return _path_is_first_party(getattr(node.root(), 'file', None))


def func_annotations_filter(node: astroid.nodes.NodeNG) -> astroid.nodes.NodeNG:
    """Filter annotated function args/retvals.

    Annotations are deferred-eval'ed (PEP 649/749, the Python 3.14+
    language default), so we don't want Pylint to complain about
    missing symbols in annotations when they aren't actually needed
    at runtime. And we strip out stuff under TYPE_CHECKING blocks
    which means they'd often be seen as missing.
    """
    if not _is_first_party_module(node):
        return node

    assert isinstance(
        node, astroid.nodes.FunctionDef | astroid.nodes.AsyncFunctionDef
    )

    # Note: In a way it seems cleaner to only clear annotations (bounds)
    # and leave the variable names intact since we might use those (for
    # example in a cast() call). However this currently results in
    # unused-variable warnings from pylint since we tend to filter out
    # things like annotations that use those vars. So it's currently
    # less messy to just clear everything.
    # If this function has type-params, clear them and remove them from
    # our locals. (We could instead leave the typevar names intact and
    # only clear their bounds, since names may be used in code such as
    # isinstance(foo, T), but per the note above clearing everything is
    # currently less messy.)
    if node.type_params:
        for typevar in node.type_params:
            del node.locals[typevar.name.name]
        node.type_params.clear()

    # Wipe out argument annotations.

    # Special-case: certain function decorators *do* evaluate
    # annotations at runtime so we want to leave theirs intact. This
    # includes functools.singledispatch, babase.dispatchmethod, and
    # efro.MessageReceiver.
    #
    # Lets just look for a @XXX.register or @XXX.handler decorators for
    # now; can get more specific if we get false positives.
    if node.decorators is not None:
        for dnode in node.decorators.nodes:
            if isinstance(dnode, astroid.nodes.Name) and dnode.name in {
                'dispatchmethod',
                'singledispatch',
            }:
                return node  # Leave annotations intact.

            if isinstance(
                dnode, astroid.nodes.Attribute
            ) and dnode.attrname in {'register', 'handler'}:
                return node  # Leave annotations intact.

    # Some function nodes (certain builtin/extension shims) model an
    # unknown signature as args=None; nothing to filter there.
    if node.args.args is None:
        return node

    node.args.annotations = [None for _ in node.args.args]
    node.args.varargannotation = None
    node.args.kwargannotation = None
    node.args.kwonlyargs_annotations = [None for _ in node.args.kwonlyargs]
    node.args.posonlyargs_annotations = [None for _ in node.args.posonlyargs]

    # Wipe out return-value annotation.
    if node.returns is not None:
        node.returns = None

    return node


def class_annotations_filter(
    node: astroid.nodes.NodeNG,
) -> astroid.nodes.NodeNG:
    """Filter annotations in class declarations."""
    if not _is_first_party_module(node):
        return node

    assert isinstance(node, astroid.nodes.ClassDef)

    # Note: We intentionally do *not* clear annotations on parent
    # classes (e.g. the S, T in a 'Parent[S, T]' base), since in some
    # cases those are used at runtime.

    # Note: In a way it seems cleaner to only clear annotations (bounds)
    # and leave the variable names intact since we might use those (for
    # example in a cast() call). However this currently results in
    # unused-variable warnings from pylint since we tend to filter out
    # things like annotations that use those vars. So it's currently
    # less messy to just clear everything.
    #
    # If this class has type-params, clear them and remove them from our
    # locals.
    if node.type_params:
        for typevar in node.type_params:
            del node.locals[typevar.name.name]
        node.type_params.clear()

    return node


def var_annotations_filter(node: astroid.nodes.NodeNG) -> astroid.nodes.NodeNG:
    """Filter annotated function variable assigns.

    This accounts for deferred annotation evaluation (PEP 649/749,
    the Python 3.14+ language default).

    Annotated assigns under functions are not evaluated. Class and
    module vars are normally not either. However we *do* evaluate
    if we come across an 'ioprepped' dataclass decorator. (the
    'ioprepped' decorator explicitly evaluates dataclass
    annotations).
    """
    if not _is_first_party_module(node):
        return node

    fnode = node
    willeval = False
    while fnode is not None:
        if isinstance(fnode, astroid.nodes.FunctionDef):
            # Assigns within functions never eval.
            break
        if isinstance(fnode, astroid.nodes.ClassDef):
            # Ok; the assign seems to be at the class level. See if
            # its an ioprepped dataclass.
            if fnode.decorators is not None:
                found_ioprepped = False
                for dec in fnode.decorators.nodes:
                    # Look for dataclassio.ioprepped.
                    if (
                        isinstance(dec, astroid.nodes.Attribute)
                        and dec.attrname in {'ioprepped', 'will_ioprep'}
                        and isinstance(dec.expr, astroid.nodes.Name)
                        and dec.expr.name == 'dataclassio'
                    ):
                        found_ioprepped = True
                        break

                    # Look for simply 'ioprepped'.
                    if isinstance(dec, astroid.nodes.Name) and dec.name in {
                        'ioprepped',
                        'will_ioprep',
                    }:
                        found_ioprepped = True
                        break

                if found_ioprepped:
                    willeval = True
                    break

        fnode = fnode.parent

    # If this annotation won't be eval'ed, replace its annotation with
    # a dummy value.
    if not willeval:
        dummyval = astroid.nodes.Const(parent=node, value='dummyval')
        node.annotation = dummyval

    return node


#: Top-level packages the doc-ui routes checker applies to: the
#: first-party ballistica packages. Keying on package name (not file
#: location) is what keeps it off of third party code: this plugin also
#: runs on user code in the master-server's workspace checks, where
#: hand-building doc-ui requests is perfectly valid.
_DOCUI_ROUTES_PACKAGES = frozenset(
    {
        'babase',
        'baclassic',
        'baplus',
        'bascenev1',
        'bascenev1lib',
        'bauiv1',
        'bauiv1lib',
        'bamaster',
        'baserver',
        'basn',
    }
)

#: Modules within those allowed to touch the stringly forms: the
#: client/server chokepoints mapping to and from routes.
_DOCUI_ROUTES_EXEMPT = ('bauiv1lib.docui', 'bamaster.docui')

_DOCUI_V2_MODULE = 'bacommon.docui.v2'

#: v2 classes that bind to page state by key name; the typed forms are
#: the row builders on ``bacommon.docui.routes.DocUIState``.
_DOCUI_V2_INPUT_ROWS = frozenset(
    {
        'CheckboxRow',
        'TextInputRow',
        'ChoiceRow',
        'Choice',
        'ColorRow',
        'SliderRow',
        'NumberRow',
    }
)

#: v2 classes taking page state (``sets=`` / ``state=``); the typed
#: forms are ``DocUIState.assign()`` and ``DocUIState.encode()``.
_DOCUI_V2_STATE_CARRIERS = frozenset({'Browse', 'Replace', 'Local', 'Page'})

#: Every v2 name we track ``from bacommon.docui.v2 import X`` aliases for.
_DOCUI_V2_TRACKED_NAMES = frozenset(
    {'Request', 'Response'} | _DOCUI_V2_INPUT_ROWS | _DOCUI_V2_STATE_CARRIERS
)


class DocUIRoutesChecker(BaseChecker):
    """Keeps first-party doc-ui code on type-safe routes and page state.

    Doc-ui (v2) requests, local-actions, and page state are strings and
    dicts on the wire, but first-party code is expected to author and
    handle them via the dataclasses in ``bacommon.docui.routes``. This
    flags code that hand-builds the stringly forms instead:
    constructing ``bacommon.docui.v2.Request`` directly, naming a
    local-action with a string, building an input row (which binds to
    a state key by name) directly, or passing state ``sets=`` /
    ``state=`` as dict literals.

    Purely syntactic (import aliases + call shapes; no inference) and
    inert outside a handful of packages, so as to cost effectively
    nothing. Timing-checked when added (2026-09-20); if this ever grows
    inference or broader scope, re-measure a cold full run.
    """

    name = 'docui-routes'
    msgs = {
        'W9701': (
            'Raw doc-ui v2 Request; use a route from bacommon.docui.routes'
            ' (route.browse(), route.replace(), etc.)',
            'docui-raw-request',
            'First-party doc-ui code should build requests from type-safe'
            ' route dataclasses instead of paths and arg dicts.',
        ),
        'W9702': (
            'Stringly doc-ui local-action; use a local-action class from'
            ' bacommon.docui.routes (action.local(), action.attach())',
            'docui-raw-local-action',
            'First-party doc-ui code should name local-actions via'
            ' type-safe dataclasses instead of strings.',
        ),
        'W9703': (
            'Raw doc-ui input row; build it from the page state type'
            ' (MyState.checkbox_row(lambda s: s.field), text_input_row(),'
            ' choice_row())',
            'docui-raw-input-row',
            'First-party doc-ui code should bind input rows to page state'
            ' via type-checked field lookups instead of key strings.',
        ),
        'W9704': (
            'Dict literal for doc-ui page state; use'
            ' sets=[MyState.assign(lambda s: s.field, value)] or'
            ' state=mystate.encode()',
            'docui-raw-state',
            'First-party doc-ui code should express page state and'
            ' assignments through the page state type instead of raw'
            ' key/value dicts.',
        ),
    }

    def __init__(self, linter: PyLinter) -> None:
        super().__init__(linter)
        # Names the v2 module goes by in the current module, and local
        # names for v2 classes imported directly (local name -> v2 name).
        self._module_aliases: set[str] = set()
        self._name_aliases: dict[str, str] = {}
        self._active = False

    def visit_module(self, node: astroid.nodes.Module) -> None:
        """Reset per-module state; decide if we care about this one."""
        self._module_aliases = set()
        self._name_aliases = {}
        name = node.name
        self._active = name.partition('.')[
            0
        ] in _DOCUI_ROUTES_PACKAGES and not any(
            name == e or name.startswith(e + '.') for e in _DOCUI_ROUTES_EXEMPT
        )

    def visit_import(self, node: astroid.nodes.Import) -> None:
        """Note 'import bacommon.docui.v2 as foo'."""
        if not self._active:
            return
        for modname, alias in node.names:
            # (A bare 'import bacommon.docui.v2' gets used by its full
            # dotted name, which we match separately.)
            if modname == _DOCUI_V2_MODULE and alias is not None:
                self._module_aliases.add(alias)

    def visit_importfrom(self, node: astroid.nodes.ImportFrom) -> None:
        """Note 'from bacommon.docui[.v2] import ...'."""
        if not self._active:
            return
        if node.modname == _DOCUI_V2_MODULE:
            for name, alias in node.names:
                if name in _DOCUI_V2_TRACKED_NAMES:
                    self._name_aliases[alias or name] = name
        elif node.modname == 'bacommon.docui':
            for name, alias in node.names:
                if name == 'v2':
                    self._module_aliases.add(alias or name)

    def _v2_name(self, func: astroid.nodes.NodeNG) -> str | None:
        """The v2 class a called expression names, if any.

        Recognizes ``<v2 module>.X`` (by alias or full dotted name) and
        directly-imported ``X`` (by whatever local name it was given).
        """
        if isinstance(func, astroid.nodes.Name):
            return self._name_aliases.get(func.name)
        if not isinstance(func, astroid.nodes.Attribute):
            return None
        expr = func.expr
        if isinstance(expr, astroid.nodes.Name):
            is_v2 = expr.name in self._module_aliases
        else:
            is_v2 = bool(expr.as_string() == _DOCUI_V2_MODULE)
        return func.attrname if is_v2 else None

    def visit_call(self, node: astroid.nodes.Call) -> None:
        """Look for the stringly forms being hand-built."""
        if not self._active:
            return

        name = self._v2_name(node.func)
        if name is None:
            return

        if name == 'Request':
            self.add_message('docui-raw-request', node=node)
            return

        if name in _DOCUI_V2_INPUT_ROWS:
            self.add_message('docui-raw-input-row', node=node)
            return

        if name in ('Local', 'Response'):
            for keyword in node.keywords:
                if keyword.arg in (
                    'immediate_local_action',
                    'local_action',
                ) and not (
                    isinstance(keyword.value, astroid.nodes.Const)
                    and keyword.value.value is None
                ):
                    self.add_message('docui-raw-local-action', node=keyword)

        if name in _DOCUI_V2_STATE_CARRIERS:
            # Only literals: a variable may well hold an encode() or
            # merge_assigns() result, which is the typed path.
            for keyword in node.keywords:
                if keyword.arg in ('sets', 'state') and isinstance(
                    keyword.value, astroid.nodes.Dict
                ):
                    self.add_message('docui-raw-state', node=keyword)

    def visit_assignattr(self, node: astroid.nodes.AssignAttr) -> None:
        """Look for ``response.local_action = 'foo'``."""
        if not self._active or node.attrname != 'local_action':
            return

        # Only in modules dealing in v2 doc-ui at all.
        if not self._module_aliases and not self._name_aliases:
            return

        parent = node.parent
        if (
            isinstance(parent, astroid.nodes.Assign)
            and isinstance(parent.value, astroid.nodes.Const)
            and isinstance(parent.value.value, str)
        ):
            self.add_message('docui-raw-local-action', node=parent)


def register(linter: PyLinter) -> None:
    """Pylint plugin entry point.

    (Our ast transforms register themselves with astroid at import
    time, below; only actual checkers need to go through here.)
    """
    linter.register_checker(DocUIRoutesChecker(linter))


def register_plugins(manager: astroid.Manager) -> None:
    """Apply our transforms to a given astroid manager object."""

    # Motivation notes:
    #
    # As of April 2025 we can opt to turn all these modifications off
    # and still pass checking with a few minor tweaks, but I'm keeping
    # them on for now. The primary reason is that I want Pylint to see
    # the world as close as possible to how it will be at runtime - with
    # neither 'if TYPE_CHECKING' blocks nor (most) annotations being
    # evaluated. I like to put as much as possible in 'if TYPE_CHECKING'
    # blocks so as to minimize actual imports, and with mypy (and
    # vanilla Pylint) there is no simple way to determine what needs to
    # be imported at runtime vs what can be forward-declared in
    # TYPE_CHECKING blocks. Placing imports under a TYPE_CHECKING block
    # which are actually needed at runtime will lead to errors that are
    # not detected until runtime, which is not good.
    #
    # So the filtering we do here is designed to give us a way to see
    # exactly what needs to be imported for runtime. We basically wipe
    # out TYPE_CHECKING blocks and Annotations in Pylint's eyes, so what
    # is left and what gets checked is strictly runtime imports and
    # usage. Mypy continues to see and check types against the full
    # original code.
    #
    # So, to use this system in practice: All imports can be added
    # normally at the top of a module. Then if Pylint says an import is
    # unused (presumably because it is used in an annotation that is not
    # evaluated at runtime), it can be moved to the TYPE_CHECKING block.
    # Currently nothing tells us if things in a TYPE_CHECKING blocks are
    # unused, but that is not too harmful and we can periodically remove
    # things and see if mypy complains. We could technically run a
    # second pass of Pylint with this filtering disabled for that
    # purpose but that would probably be overkill.

    # Completely ignore everything under an 'if TYPE_CHECKING'
    # conditional. That stuff only gets run for mypy, and in general we
    # want to check code as if it doesn't exist at all.
    manager.register_transform(astroid.nodes.If, ignore_type_check_filter)

    # We use 'reveal_type()' quite often, which tells mypy to print
    # the type of an expression. Let's ignore it in Pylint's eyes so
    # we don't see an ugly error there.
    manager.register_transform(astroid.nodes.Call, ignore_reveal_type_call)

    # Annotations are deferred-eval'ed (PEP 649/749; the language
    # default as of Python 3.14), and we also use 'if TYPE_CHECKING:'
    # blocks, which lets us do imports and whatnot that are limited to
    # type-checking. Let's make Pylint understand these.
    manager.register_transform(astroid.nodes.AnnAssign, var_annotations_filter)
    manager.register_transform(
        astroid.nodes.FunctionDef, func_annotations_filter
    )
    manager.register_transform(
        astroid.nodes.AsyncFunctionDef, func_annotations_filter
    )
    manager.register_transform(astroid.nodes.ClassDef, class_annotations_filter)


register_plugins(astroid.MANAGER)
