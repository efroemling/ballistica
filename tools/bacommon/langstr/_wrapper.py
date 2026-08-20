# Released under the MIT License. See LICENSE for details.
#
"""Runtime accessor for generated language-string wrapper packages.

A generated wrapper module exposes a ``strings`` object built from a
compact nested param-tree; its precise types live in the module's
``if TYPE_CHECKING`` shadow (decision #28 -- bare annotations, no per-entry
runtime class). This drives the *runtime* side: a no-arg string reads as a
property yielding a :class:`LangStrSpec`; a parameterized one is a
callable that
builds an :class:`LangStrSpec` from keyword substitutions, and a subdir is a
nested :class:`LangStrDir`.
"""

import datetime
from typing import TYPE_CHECKING

from bacommon.langstr._core import LangStrSpecResource, PackageStructure

if TYPE_CHECKING:
    from bacommon.langstr._core import LangStrSpec

#: A wrapper's compact runtime tree: a leaf is its ordered param-keyword
#: tuple (``()`` for a no-arg string); a subdir is a nested tree.
type WrapperTree = dict[str, 'tuple[str, ...] | WrapperTree']


def package_structure(apverid: str, tree: WrapperTree) -> PackageStructure:
    """Build a :class:`PackageStructure` from a wrapper's runtime ``_TREE``.

    Flattens the nested tree into the ``{logical-path: param-keywords}`` map
    the encode/decode contexts need -- so a consumer of a vendored package
    just passes ``module.APVERID, module._TREE`` (both module-level).
    """
    flat: dict[str, tuple[str, ...]] = {}
    _flatten_tree(tree, '', flat)
    return PackageStructure(apverid, flat)


# (Module-level rather than a closure inside package_structure; a
# self-recursive closure creates a reference cycle per call.)
def _flatten_tree(
    node: WrapperTree, prefix: str, flat: dict[str, tuple[str, ...]]
) -> None:
    for name, value in node.items():
        full = f'{prefix}/{name}' if prefix else name
        if isinstance(value, dict):
            _flatten_tree(value, full, flat)
        else:
            flat[full] = value


def time_sub_millis(
    value: 'datetime.datetime | datetime.timedelta',
    now: 'datetime.datetime | None' = None,
) -> int:
    """One time-typed sub value's wire form (signed ms int).

    The single shared arithmetic for wrapper accessors' *useful*
    duration types: a :class:`datetime.timedelta` is already a signed
    length; a :class:`datetime.datetime` is an absolute time,
    converted to signed ``target - now`` per D12 so the string's
    ``dir`` handles past/future. ``now`` defaults to
    :func:`efro.util.utc_now`; batch callers pass one shared value so
    a page of renders can't drift against itself. Datetimes must be
    timezone-aware (naive ones raise from the subtraction, per stdlib
    rules).
    """
    from efro.util import utc_now

    if isinstance(value, datetime.timedelta):
        return int(value.total_seconds() * 1000)
    if now is None:
        now = utc_now()
    return int((value - now).total_seconds() * 1000)


def convert_time_subs(
    subs: dict[
        str,
        'str | int | LangStrSpec | datetime.datetime | datetime.timedelta',
    ],
    now: 'datetime.datetime | None' = None,
) -> dict[str, 'str | int | LangStrSpec']:
    """Convert any time-typed sub values to their wire form.

    The integer-milliseconds wire value is an implementation detail of
    the duration machinery; conversion is driven purely by each
    value's *type* (see :func:`time_sub_millis`), so no per-param kind
    knowledge is needed -- the typed stubs are what hold authors to
    passing time types only for duration params. ``now`` is resolved
    at most once per call.
    """
    from efro.util import utc_now

    out: dict[str, str | int | LangStrSpec] = {}
    for key, val in subs.items():
        if isinstance(val, (datetime.datetime, datetime.timedelta)):
            if now is None and isinstance(val, datetime.datetime):
                now = utc_now()
            out[key] = time_sub_millis(val, now)
        else:
            out[key] = val
    return out


class _LstrMaker:
    """Callable leaf: builds a :class:`LangStrSpec` from keyword subs."""

    __slots__ = ('_apverid', '_name')

    def __init__(self, apverid: str, name: str) -> None:
        self._apverid = apverid
        self._name = name

    def __call__(
        self,
        now: 'datetime.datetime | None' = None,
        **subs: (
            'str | int | LangStrSpec | datetime.datetime'
            ' | datetime.timedelta'
        ),
    ) -> 'LangStrSpec':
        # ``now`` can never shadow a real param: the brief grammar
        # reserves the name for exactly this use.
        return LangStrSpecResource(
            self._apverid, self._name, convert_time_subs(subs, now)
        )


class LangStrDir:
    """Runtime root/subdir accessor for a generated wrapper package."""

    __slots__ = ('_apverid', '_tree', '_prefix')

    def __init__(
        self, apverid: str, tree: WrapperTree, prefix: str = ''
    ) -> None:
        self._apverid = apverid
        self._tree = tree
        self._prefix = prefix

    def __getattr__(self, name: str) -> 'LangStrSpec | _LstrMaker | LangStrDir':
        try:
            child = self._tree[name]
        except KeyError:
            raise AttributeError(name) from None
        full = f'{self._prefix}/{name}' if self._prefix else name
        if isinstance(child, dict):
            return LangStrDir(self._apverid, child, full)
        # A leaf: its param-keyword tuple. Empty -> a no-arg string, read
        # as a property yielding the LangStrSpec directly; otherwise a maker.
        if not child:
            return LangStrSpecResource(self._apverid, full)
        return _LstrMaker(self._apverid, full)
