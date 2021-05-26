# Released under the MIT License. See LICENSE for details.
#
"""Plugins for pylint"""

from __future__ import annotations

from typing import TYPE_CHECKING

import astroid

if TYPE_CHECKING:
    from astroid import node_classes as nc
    from typing import Set, Dict, Any, List

VERBOSE = False


def register(linter: Any) -> None:
    """Unused here; we're modifying the ast; not linters."""
    del linter  # Unused.


failed_imports: Set[str] = set()


def failed_import_hook(modname: str) -> None:
    """Custom failed import callback."""

    # We don't actually do anything here except note in our log that
    # something couldn't be imported. (may help sanity-check our filtering)
    if VERBOSE:
        if modname not in failed_imports:
            failed_imports.add(modname)
            print('GOT FAILED IMPORT OF', modname)
    raise astroid.AstroidBuildingError(modname=modname)


def ignore_type_check_filter(node: nc.NodeNG) -> nc.NodeNG:
    """Ignore stuff under 'if TYPE_CHECKING:' block at module level."""

    # Look for a non-nested 'if TYPE_CHECKING:'
    if (isinstance(node.test, astroid.Name)
            and node.test.name == 'TYPE_CHECKING'
            and isinstance(node.parent, astroid.Module)):

        # Find the module node.
        mnode = node
        while mnode.parent is not None:
            mnode = mnode.parent

        # First off, remove any names that are getting defined
        # in this block from the module locals.
        for cnode in node.body:
            _strip_import(cnode, mnode)

        # Now replace the body with a simple 'pass'. This will
        # keep pylint from complaining about grouped imports/etc.
        passnode = astroid.Pass(parent=node,
                                lineno=node.lineno + 1,
                                col_offset=node.col_offset + 1)
        node.body = [passnode]
    return node


def ignore_reveal_type_call(node: nc.NodeNG) -> nc.NodeNG:
    """Make 'reveal_type()' not trigger an error.

    The 'reveal_type()' fake call is used for type debugging types with
    mypy and it is annoying having pylint errors pop up alongside the mypy
    info.
    """

    # Let's just replace any reveal_type(x) call with print(x)..
    if (isinstance(node.func, astroid.Name)
            and node.func.name == 'reveal_type'):
        node.func.name = 'print'
        return node
    return node


def _strip_import(cnode: nc.NodeNG, mnode: nc.NodeNG) -> None:
    if isinstance(cnode, (astroid.Import, astroid.ImportFrom)):
        for name, val in list(mnode.locals.items()):
            if cnode in val:

                # Pull us out of the list.
                valnew = [v for v in val if v is not cnode]
                if valnew:
                    mnode.locals[name] = valnew
                else:
                    del mnode.locals[name]


def using_future_annotations(node: nc.NodeNG) -> nc.NodeNG:
    """Return whether postponed annotation evaluation is enabled (PEP 563)."""

    # Find the module.
    mnode = node
    while mnode.parent is not None:
        mnode = mnode.parent

    # Look for 'from __future__ import annotations' to decide
    # if we should assume all annotations are defer-eval'ed.
    # NOTE: this will become default at some point within a few years..
    annotations_set = mnode.locals.get('annotations')
    if (annotations_set and isinstance(annotations_set[0], astroid.ImportFrom)
            and annotations_set[0].modname == '__future__'):
        return True
    return False


def func_annotations_filter(node: nc.NodeNG) -> nc.NodeNG:
    """Filter annotated function args/retvals.

    This accounts for deferred evaluation available in in Python 3.7+
    via 'from __future__ import annotations'. In this case we don't
    want Pylint to complain about missing symbols in annotations when
    they aren't actually needed at runtime.
    """
    # Only do this if deferred annotations are on.
    if not using_future_annotations(node):
        return node

    # Wipe out argument annotations.

    # Special-case: functools.singledispatch and ba.dispatchmethod *do*
    # evaluate annotations at runtime so we want to leave theirs intact.
    # Lets just look for a @XXX.register decorator used by both I guess.
    if node.decorators is not None:
        for dnode in node.decorators.nodes:
            if (isinstance(dnode, astroid.nodes.Name)
                    and dnode.name in ('dispatchmethod', 'singledispatch')):
                return node  # Leave annotations intact.

            if (isinstance(dnode, astroid.nodes.Attribute)
                    and dnode.attrname == 'register'):
                return node  # Leave annotations intact.

    node.args.annotations = [None for _ in node.args.args]
    node.args.varargannotation = None
    node.args.kwargannotation = None
    node.args.kwonlyargs_annotations = [None for _ in node.args.kwonlyargs]
    node.args.posonlyargs_annotations = [None for _ in node.args.kwonlyargs]

    # Wipe out return-value annotation.
    if node.returns is not None:
        node.returns = None

    return node


def var_annotations_filter(node: nc.NodeNG) -> nc.NodeNG:
    """Filter annotated function variable assigns.

    This accounts for deferred evaluation.
    """
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-nested-blocks

    if using_future_annotations(node):

        # Future behavior:
        # Annotated assigns under functions are not evaluated.
        # Class and module vars are normally not either. However we
        # do evaluate if we come across an 'ioprepped' dataclass
        # decorator. (the 'ioprepped' decorator explicitly evaluates
        # dataclass annotations).

        fnode = node
        willeval = False
        while fnode is not None:
            if isinstance(fnode, astroid.ClassDef):
                if fnode.decorators is not None:
                    found_ioprepped = False
                    for dec in fnode.decorators.nodes:

                        # Look for dataclassio.ioprepped.
                        if (isinstance(dec, astroid.nodes.Attribute)
                                and dec.attrname == 'ioprepped'
                                and isinstance(dec.expr, astroid.nodes.Name)
                                and dec.expr.name == 'dataclassio'):
                            found_ioprepped = True
                            break

                        # Look for simply 'ioprepped'.
                        if (isinstance(dec, astroid.nodes.Name)
                                and dec.name == 'ioprepped'):
                            found_ioprepped = True
                            break

                    if found_ioprepped:
                        willeval = True
                        break

            fnode = fnode.parent

    else:
        # Legacy behavior:
        # Annotated assigns under functions are not evaluated,
        # but class or module vars are.
        fnode = node
        willeval = True
        while fnode is not None:
            if isinstance(fnode,
                          (astroid.FunctionDef, astroid.AsyncFunctionDef)):
                willeval = False
                break
            if isinstance(fnode, astroid.ClassDef):
                willeval = True
                break
            fnode = fnode.parent

    # If this annotation won't be eval'ed, replace it with a dummy string.
    if not willeval:
        dummyval = astroid.Const(parent=node, value='dummyval')
        node.annotation = dummyval

    return node


# Stripping subscripts on some generics seems to cause
# more harm than good, so we leave some intact.
ALLOWED_GENERICS = {'Sequence'}


def _is_strippable_subscript(node: nc.NodeNG) -> bool:
    if isinstance(node, astroid.Subscript):
        # We can strip if its not in our allowed list.
        if not (isinstance(node.value, astroid.Name)
                and node.value.name in ALLOWED_GENERICS):
            return True
    return False


def class_generics_filter(node: nc.NodeNG) -> nc.NodeNG:
    """Filter generics subscripts out of class declarations."""

    # First, quick-out if nothing here should be filtered.
    found = False
    for base in node.bases:
        if _is_strippable_subscript(base):
            found = True

    if not found:
        return node

    # Now strip subscripts from base classes.
    new_bases: List[nc.NodeNG] = []
    for base in node.bases:
        if _is_strippable_subscript(base):
            new_bases.append(base.value)
            base.value.parent = node
        else:
            new_bases.append(base)
    node.bases = new_bases

    return node


def register_plugins(manager: astroid.Manager) -> None:
    """Apply our transforms to a given astroid manager object."""

    # Hmm; is this still necessary?
    if VERBOSE:
        manager.register_failed_import_hook(failed_import_hook)

    # Completely ignore everything under an 'if TYPE_CHECKING' conditional.
    # That stuff only gets run for mypy, and in general we want to
    # check code as if it doesn't exist at all.
    manager.register_transform(astroid.If, ignore_type_check_filter)

    # We use 'reveal_type()' quite often, which tells mypy to print
    # the type of an expression. Let's ignore it in Pylint's eyes so
    # we don't see an ugly error there.
    manager.register_transform(astroid.Call, ignore_reveal_type_call)

    # We make use of 'from __future__ import annotations' which causes Python
    # to receive annotations as strings, and also 'if TYPE_CHECKING:' blocks,
    # which lets us do imports and whatnot that are limited to type-checking.
    # Let's make Pylint understand these.
    manager.register_transform(astroid.AnnAssign, var_annotations_filter)
    manager.register_transform(astroid.FunctionDef, func_annotations_filter)
    manager.register_transform(astroid.AsyncFunctionDef,
                               func_annotations_filter)

    # Pylint doesn't seem to support Generics much right now, and it seems
    # to lead to some buggy behavior and slowdowns. So let's filter them
    # out. So instead of this:
    #   class MyClass(MyType[T]):
    # Pylint will see this:
    #   class MyClass(MyType):
    # I've opened a github issue related to the problems I was hitting,
    # so we can revisit the need for this if that gets resolved.
    # https://github.com/PyCQA/pylint/issues/3605
    manager.register_transform(astroid.ClassDef, class_generics_filter)


register_plugins(astroid.MANAGER)
