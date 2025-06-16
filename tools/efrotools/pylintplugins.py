# Released under the MIT License. See LICENSE for details.
#
"""Plugins for pylint"""

from __future__ import annotations

from typing import TYPE_CHECKING

import astroid
import astroid.nodes

# from pylint.checkers import BaseChecker

if TYPE_CHECKING:
    from typing import Any

VERBOSE = False


failed_imports: set[str] = set()


def failed_import_hook(modname: str) -> None:
    """Custom failed import callback."""

    # We don't actually do anything here except note in our log that
    # something couldn't be imported (may help sanity-check our
    # filtering).
    if VERBOSE:
        if modname not in failed_imports:
            failed_imports.add(modname)
            print('GOT FAILED IMPORT OF', modname)
    raise astroid.AstroidBuildingError(modname=modname)


def ignore_type_check_filter(
    if_node: astroid.nodes.NodeNG,
) -> astroid.nodes.NodeNG:
    """Ignore stuff under ``if TYPE_CHECKING:`` block at module level."""

    # Look for a non-nested 'if TYPE_CHECKING:'
    if (
        isinstance(if_node.test, astroid.Name)
        and if_node.test.name == 'TYPE_CHECKING'
        and isinstance(if_node.parent, astroid.Module)
    ):
        # Special case: some third party modules are starting to contain
        # code that we don't handle cleanly which results in pylint runs
        # breaking. For now just ignoring them as they pop up. We should
        # try to figure out how to disable this filtering for third
        # party modules altogether or make our filtering more robust.
        if if_node.parent.name in {
            'openai._models',
            'openai._base_client',
            'openai._client',
            'openai._compat',
            'filelock',
            'aiohttp.web_app',
            'aiohttp.web_response',
        }:
            return if_node

        module_node = if_node.parent

        # Remove any locals getting defined under this if statement.
        # (ideally should recurse in case we have nested if
        # statements/etc but keeping it simple for now).
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
        passnode = astroid.Pass(
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
    """Return whether the node is under the if statement.

    (This returns False if it is under an elif/else portion)
    """
    # Quick out:
    if node.parent is not if_node:
        return False
    return node in if_node.body


def ignore_reveal_type_call(node: astroid.nodes.NodeNG) -> astroid.nodes.NodeNG:
    """Make ``reveal_type()`` not trigger an error.

    The 'reveal_type()' fake call is used for type debugging types with
    mypy and it is annoying having pylint errors pop up alongside the mypy
    info.
    """

    # Let's just replace any reveal_type(x) call with print(x)..
    if isinstance(node.func, astroid.Name) and node.func.name == 'reveal_type':
        node.func.name = 'print'
        return node
    return node


def using_future_annotations(
    node: astroid.nodes.NodeNG,
) -> astroid.nodes.NodeNG:
    """Return whether postponed annotation evaluation is enabled (PEP 563)."""

    # Find the module.
    mnode = node
    while mnode.parent is not None:
        mnode = mnode.parent

    # Look for 'from __future__ import annotations' to decide if we
    # should assume all annotations are defer-eval'ed. NOTE: this will
    # become default at some point within a few years..
    annotations_set = mnode.locals.get('annotations')
    if (
        annotations_set
        and isinstance(annotations_set[0], astroid.ImportFrom)
        and annotations_set[0].modname == '__future__'
    ):
        return True
    return False


def func_annotations_filter(node: astroid.nodes.NodeNG) -> astroid.nodes.NodeNG:
    """Filter annotated function args/retvals.

    This accounts for deferred evaluation available in in Python 3.7+
    via 'from __future__ import annotations'. In this case we don't want
    Pylint to complain about missing symbols in annotations when they
    aren't actually needed at runtime. And we strip out stuff under
    TYPE_CHECKING blocks which means they'd often be seen as missing.
    """

    # Only run if deferred annotations are on.
    if not using_future_annotations(node):
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
    if bool(True):
        # If this function has type-params, clear them and remove them
        # from our locals.
        if node.type_params:
            for typevar in node.type_params:
                del node.locals[typevar.name.name]
            node.type_params.clear()
    else:
        if node.type_params:
            # We want to leave the typevars intact since they may be
            # used in code (such as isinstance(foo, T)) but we want to
            # kill the bound value which we don't need/use at runtime.
            for typevar in node.type_params:
                typevar.bound = None

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

    node.args.annotations = [None for _ in node.args.args]
    node.args.varargannotation = None
    node.args.kwargannotation = None
    node.args.kwonlyargs_annotations = [None for _ in node.args.kwonlyargs]
    node.args.posonlyargs_annotations = [None for _ in node.args.kwonlyargs]

    # Wipe out return-value annotation.
    if node.returns is not None:
        node.returns = None

    return node


def class_annotations_filter(
    node: astroid.nodes.NodeNG,
) -> astroid.nodes.NodeNG:
    """Filter annotations in class declarations."""

    # Only do this if deferred annotations are on.
    if not using_future_annotations(node):
        return node

    assert isinstance(node, astroid.ClassDef)

    # UPDATE: Not clearing annotations on parent classes, since in
    # some cases we use them at runtime.
    if bool(False):
        for base in node.bases:
            # If we find something like Parent[S, T] as a base class,
            # replace S and T with a dummy string.
            if isinstance(base, astroid.nodes.Subscript):
                slc = base.slice
                dummyval = astroid.Const(parent=slc, value='dummyval')
                dummyval.col_offset = 0
                slc.elts = [dummyval]

    # Note: In a way it seems cleaner to only clear annotations (bounds)
    # and leave the variable names intact since we might use those (for
    # example in a cast() call). However this currently results in
    # unused-variable warnings from pylint since we tend to filter out
    # things like annotations that use those vars. So it's currently
    # less messy to just clear everything.
    if bool(True):
        # If this class has type-params, clear them and remove them
        # from our locals.
        if node.type_params:
            for typevar in node.type_params:
                del node.locals[typevar.name.name]
            node.type_params.clear()
    else:
        if node.type_params:
            # We want to leave the typevars intact since they may be used
            # in code (such as isinstance(foo, T)) but we want to kill the
            # bound value which we don't need/use at runtime.
            for typevar in node.type_params:
                typevar.bound = None

    return node


def var_annotations_filter(node: astroid.nodes.NodeNG) -> astroid.nodes.NodeNG:
    """Filter annotated function variable assigns.

    This accounts for deferred evaluation.
    """
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-nested-blocks

    if using_future_annotations(node):

        # Future behavior:
        #
        # Annotated assigns under functions are not evaluated. Class and
        # module vars are normally not either. However we *do* evaluate
        # if we come across an 'ioprepped' dataclass decorator. (the
        # 'ioprepped' decorator explicitly evaluates dataclass
        # annotations).

        fnode = node
        willeval = False
        while fnode is not None:
            if isinstance(fnode, astroid.FunctionDef):
                # Assigns within functions never eval.
                break
            if isinstance(fnode, astroid.ClassDef):
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

    else:

        # Legacy behavior: Annotated assigns under functions are not
        # evaluated, but class or module vars are.
        fnode = node
        willeval = True
        while fnode is not None:
            if isinstance(
                fnode, (astroid.FunctionDef, astroid.AsyncFunctionDef)
            ):
                willeval = False
                break
            if isinstance(fnode, astroid.ClassDef):
                willeval = True
                break
            fnode = fnode.parent

    # If this annotation won't be eval'ed, replace its annotation with
    # a dummy value.
    if not willeval:
        dummyval = astroid.Const(parent=node, value='dummyval')
        node.annotation = dummyval

    return node


# Stripping subscripts on some generics seems to cause
# more harm than good, so we leave some intact.
# ALLOWED_GENERICS = {'Sequence'}


# def _is_strippable_subscript(node: astroid.nodes.NodeNG) -> bool:
#     if isinstance(node, astroid.Subscript):
#         # We can strip if its not in our allowed list.
#         if not (
#             isinstance(node.value, astroid.Name)
#             and node.value.name in ALLOWED_GENERICS
#         ):
#             return True
#     return False


# def class_generics_filter(node: astroid.nodes.NodeNG) -> astroid.nodes.NodeNG:
#     """Filter generics subscripts out of class declarations."""

#     # First, quick-out if nothing here should be filtered.
#     found = False
#     for base in node.bases:
#         if _is_strippable_subscript(base):
#             found = True

#     if not found:
#         return node

#     # Now strip subscripts from base classes.
#     new_bases: list[astroid.nodes.NodeNG] = []
#     for base in node.bases:
#         if _is_strippable_subscript(base):
#             new_bases.append(base.value)
#             base.value.parent = node
#         else:
#             new_bases.append(base)
#     node.bases = new_bases

#     return node


# class MySuppressChecker(BaseChecker):
#     """Do some suppression."""

#     name = 'unique-returns'
#     priority = -1
#     msgs = {
#         'W0001': (
#             'Returns a non-unique constant.',
#             'non-unique-returns',
#             'All constants returned in a function should be unique.',
#         ),
#     }
#     options = (
#         (
#             'ignore-ints',
#             {
#                 'default': False,
#                 'type': 'yn',
#                 'metavar': '<y_or_n>',
#                 'help': 'Allow returning non-unique integers',
#             },
#         ),
#     )

#     def leave_typevar(self, node: astroid.nodes.TypeVar) -> None:
#         """Clears any state left in this checker from last module checked."""
#         del node  # Unused.
#         # print(
#         #     'hello from',
#         #     type(node.name.name),
#         #     node.scope().locals,
#         #     node.name.name in node.scope().locals,
#         # )
#         # print(
#         #     'AND',
#         # dir(node.scope().locals[node.name.name][0]),
#         # self.linter.is_message_enabled("unused-variable"),
#         # )
#         # print('HO', node.scope().locals)

#     # name = 'suppress-unused-in-type-params'
#     # priority = -1
#     # msgs = {}
#     # options = ()

#     # def __init__(self, linter=None):
#     #     print('INIT')
#     #     super().__init__(linter)

#     # def visit_return(self, node: astroid.nodes.NodeNG) -> None:
#     #     """Do the thing."""
#     #     print('WHEE')
#     #     # if node.scope().name == '_ignore_unused_scope':
#     #     #     # Fake that the variable is used, so pylint won't complain
#     #     #     for target in node.targets:
#     #     #         target.parent.locals[target.name].used = True


# def register(linter: Any) -> Any:
#     """Do a thing."""
#     print('REG', type(linter))
#     linter.register_checker(MySuppressChecker(linter))


def register(linter: Any) -> None:
    """Unused here - we're modifying the ast, not defining linters."""
    del linter  # Unused.


def register_plugins(manager: astroid.Manager) -> None:
    """Apply our transforms to a given astroid manager object."""

    # Hmm; is this still necessary?
    if VERBOSE:
        manager.register_failed_import_hook(failed_import_hook)

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
    manager.register_transform(astroid.If, ignore_type_check_filter)

    # We use 'reveal_type()' quite often, which tells mypy to print
    # the type of an expression. Let's ignore it in Pylint's eyes so
    # we don't see an ugly error there.
    manager.register_transform(astroid.Call, ignore_reveal_type_call)

    # We make use of 'from __future__ import annotations' which causes
    # Python to receive annotations as strings, and also 'if
    # TYPE_CHECKING:' blocks, which lets us do imports and whatnot that
    # are limited to type-checking. Let's make Pylint understand these.
    manager.register_transform(astroid.AnnAssign, var_annotations_filter)
    manager.register_transform(astroid.FunctionDef, func_annotations_filter)
    manager.register_transform(
        astroid.AsyncFunctionDef, func_annotations_filter
    )
    manager.register_transform(astroid.ClassDef, class_annotations_filter)


register_plugins(astroid.MANAGER)
