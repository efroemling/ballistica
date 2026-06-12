# EfroSynced from ballistica-internal.
# EFRO_SYNC_HASH=86684659705397036487744621506447988418
#
# Released under the MIT License. See LICENSE for details.
#
"""Utilities for debugging memory leaks or other issues.

IMPORTANT - these functions use the gc module which looks 'under the hood'
at Python and sometimes returns not-fully-initialized objects, which may
cause crashes or errors due to suddenly having references to them that they
didn't expect, etc. See https://github.com/python/cpython/issues/59313.
For this reason, these methods should NEVER be called in production code.
Enable them only for debugging situations and be aware that their use may
itself cause problems. The same is true for the gc module itself.
"""

import os
import gc
import sys
import time
import types
import weakref
import logging
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, TextIO, Iterable


ABS_MAX_LEVEL = 10

# NOTE: In general we want this toolset to allow us to explore
# which objects are holding references to others so we can diagnose
# leaks/etc. It is a bit tricky to do that, however, without
# affecting the objects we are looking at by adding temporary references
# from module dicts, function scopes, etc. So we need to try to be
# careful about cleaning up after ourselves and explicitly avoiding
# returning these temporary references wherever possible.

# A good test is running printrefs() repeatedly on some object that is
# known to be static. If the list of references or the ids or any
# the listed references changes with each run, it's a good sign that
# we're showing some temporary objects that we should be ignoring.


# Lazy-init our logger so we don't have it showing up in lists when
# we're not using it.
def _get_logger() -> logging.Logger:
    return logging.getLogger(__name__)


def getobjs(
    cls: type | str, contains: str | None = None, expanded: bool = False
) -> list[Any]:
    """Return all garbage-collected objects matching criteria.

    Args:

      type:
        Can be an actual type or a string in which case objects
        whose types contain that string will be returned.

      contains:
        If provided, objects will be filtered to those
        containing that in their str() representations.
    """

    # Don't wanna return stuff waiting to be garbage-collected.
    gc.collect()

    if not isinstance(cls, type | str):
        raise TypeError('Expected a type or string for cls')
    if not isinstance(contains, str | None):
        raise TypeError('Expected a string or None for contains')

    allobjs = _get_all_objects(expanded=expanded)

    if isinstance(cls, str):
        objs = [o for o in allobjs if cls in str(type(o))]
    else:
        objs = [o for o in allobjs if isinstance(o, cls)]
    if contains is not None:
        objs = [o for o in objs if contains in str(o)]

    return objs


# Recursively expand slists objects into olist, using seen to track
# already processed objects.
def _getr(slist: list[Any], olist: list[Any], seen: set[int]) -> None:
    for obj in slist:
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        olist.append(obj)
        tll = gc.get_referents(obj)
        if tll:
            _getr(tll, olist, seen)


def _get_all_objects(expanded: bool) -> list[Any]:
    """Return all objects visible to garbage collector.

    For notes on the 'expanded' option, see:
    https://utcc.utoronto.ca/~cks/space/blog/python/GetAllObjects
    """
    gcl = gc.get_objects()
    if not expanded:
        return gcl
    olist: list[Any] = []
    seen: set[int] = set()
    # Just in case:
    seen.add(id(gcl))
    seen.add(id(olist))
    seen.add(id(seen))
    # _getr does the real work.
    _getr(gcl, olist, seen)
    return olist


def getobj(objid: int, expanded: bool = False) -> Any:
    """Return a garbage-collectable object by its id.

    Remember that this is VERY inefficient and should only ever be used
    for debugging.
    """
    # If they passed a string (hex, etc), convert to int.
    # if isinstance(objid, str):
    #     objid = int(objid, 0)  # Autodetect hex/etc.

    if not isinstance(objid, int):
        raise TypeError(f'Expected an int for objid; got a {type(objid)}.')

    # Don't wanna return stuff waiting to be garbage-collected.
    # UPDATE: Turning this off.
    # gc.collect()

    allobjs = _get_all_objects(expanded=expanded)
    for obj in allobjs:
        if id(obj) == objid:
            return obj
    raise RuntimeError(f'Object with id {objid} not found.')


def getrefs(obj: Any) -> list[Any]:
    """Given an object, return things referencing it."""
    v = vars()  # Ignore ref coming from locals.
    return [o for o in gc.get_referrers(obj) if o is not v]


def printfiles(file: TextIO | None = None) -> None:
    """Print info about open files in the current app."""
    import io

    file = sys.stderr if file is None else file
    try:
        import psutil
    except ImportError:
        print(
            "Error: printfiles requires the 'psutil' module to be installed.",
            file=file,
            flush=True,
        )
        return

    proc = psutil.Process()

    # Let's grab all Python file handles so we can associate raw files
    # with their Python objects when possible.
    fileio_ids = {obj.fileno(): obj for obj in getobjs(io.FileIO)}
    textio_ids = {obj.fileno(): obj for obj in getobjs(io.TextIOWrapper)}

    # FIXME: we could do a more limited version of this when psutil is
    # not present that simply includes Python's files.
    print('Files open by this app (not limited to Python\'s):', file=file)
    for i, ofile in enumerate(proc.open_files()):
        # Mypy doesn't know about mode apparently.
        # (and can't use type: ignore because we don't require psutil
        # and then mypy complains about unused ignore comment when its
        # not present)
        mode = getattr(ofile, 'mode')
        assert isinstance(mode, str)
        textio = textio_ids.get(ofile.fd)
        textio_s = id(textio) if textio is not None else '<not found>'
        fileio = fileio_ids.get(ofile.fd)
        fileio_s = id(fileio) if fileio is not None else '<not found>'
        print(
            f'#{i+1}: path={ofile.path!r},'
            f' fd={ofile.fd}, mode={mode!r}, TextIOWrapper={textio_s},'
            f' FileIO={fileio_s}',
            file=file,
        )
    file.flush()


def printrefs(  # pylint: disable=too-many-positional-arguments
    obj: Any,
    max_level: int = 2,
    exclude_objs: list[Any] | None = None,
    expand_ids: list[int] | None = None,
    file: TextIO | None = None,
    max_visits: int = 500,
) -> None:
    """Print human readable list of objects referring to an object.

    Args:

      max_level:
        Specifies how many levels of recursion are printed.

      exclude_objs:
        Can be a list of exact objects to skip if found in the
        referrers list. This can be useful to avoid printing the local context
        where the object was passed in from (locals(), etc).

      expand_ids:
        Can be a list of object ids; if that particular object is
        found, it will always be expanded even if max_level has been reached.

      max_visits:
        Caps total ``_printrefs`` recursive entries; when exceeded,
        an aborted traversal prints a single ``[truncated...]``
        marker and unwinds. Each recursive entry costs an O(heap)
        ``gc.get_referrers`` scan, so on busy processes this is the
        load-bearing safeguard against runaway calls — the
        per-step ``max_level`` interacts multiplicatively with
        average referrer fan-out, and a few highly-shared
        structural objects can blow up the visit count fast.
    """
    if file is None:
        file = sys.stderr

    # Let's always exclude the gc.garbage list. When we're debugging
    # with gc.DEBUG_SAVEALL enabled this list will include everything,
    # so this cuts out lots of noise.
    if exclude_objs is None:
        exclude_objs = []
    else:
        exclude_objs = list(exclude_objs)
    exclude_objs.append(gc.garbage)

    # Mutable state shared across the recursion.
    state: dict[str, Any] = {
        'visits': 0,
        'max_visits': max_visits,
        'truncated_printed': False,
    }

    _printrefs(
        obj,
        level=0,
        max_level=max_level,
        exclude_objs=exclude_objs,
        expand_ids=[] if expand_ids is None else expand_ids,
        file=file,
        state=state,
    )
    file.flush()


@dataclass
class GarbageRefDump:
    """Captured ref-cycle data for a single sampled object.

    Returned as part of :class:`GarbageSummary` for objects whose type
    matched a caller-provided ``debug_types`` entry.
    """

    #: ``printrefs()`` output describing what holds this object.
    refs: str

    #: If the sampled object was a :class:`BaseException`, the formatted
    #: traceback string. ``None`` otherwise.
    exception_trace: str | None = None


@dataclass
class GarbageSummary:
    """Result of inspecting :data:`gc.garbage` for cyclic references.

    Returned by :func:`summarize_garbage`. Callers format the histogram
    and ref-dumps for whatever output context they need (log messages,
    REST responses, etc.).
    """

    #: Map of fully-qualified type name (``module.Class``, or bare class
    #: name for builtins) to count of objects of that type currently in
    #: ``gc.garbage``.
    histogram: dict[str, int] = field(default_factory=dict)

    #: For each type name in the caller's ``debug_types``, a list of
    #: captured ref dumps (one per sampled object, up to
    #: ``debug_type_limit``).
    ref_dumps: dict[str, list[GarbageRefDump]] = field(default_factory=dict)

    #: For ``type`` objects appearing in ``gc.garbage``, the dotted path
    #: of each (e.g. ``mymodule.MyClass``). Useful as an inline annotation
    #: alongside the histogram entry for ``type``.
    type_paths: list[str] = field(default_factory=list)


def summarize_garbage(
    *,
    debug_types: Iterable[str] = (),
    debug_type_limit: int = 1,
    auto_include_exceptions: bool = False,
    printrefs_max_level: int = 2,
    printrefs_max_visits: int = 500,
) -> GarbageSummary:
    """Summarize the current contents of :data:`gc.garbage`.

    The caller is expected to have already run a collect with
    :data:`gc.DEBUG_SAVEALL` so cyclic-collected objects accumulated in
    ``gc.garbage``. This function does not collect or modify gc state
    itself — it only reads ``gc.garbage`` and builds a structured
    summary.

    Args:
      debug_types:
        Iterable of fully-qualified type names (``module.Class``, or
        bare class name for builtins). Sampled objects of these types
        get ``printrefs()`` output captured into the result. Empty
        means histogram only.
      debug_type_limit:
        Max number of objects to sample per matched debug type.
      auto_include_exceptions:
        If ``True``, every object in ``gc.garbage`` that is an
        instance of :class:`BaseException` is sampled for ref-dumps
        (subject to ``debug_type_limit``) regardless of whether
        its type appears in ``debug_types``. Useful when you don't
        yet know which exception classes are anchoring cycles —
        the dump output's ``exception_trace`` field tells you
        where they came from.
      printrefs_max_level:
        Forwarded to :func:`printrefs` as its ``max_level``. Default
        of 2 matches the standalone helper. Higher values walk
        deeper into the referrer graph but cost gets exponential
        in heap-shared structural objects (dict, type, etc.); the
        ``printrefs_max_visits`` cap is the load-bearing safeguard
        against runaway calls — see :func:`printrefs`.
      printrefs_max_visits:
        Forwarded to :func:`printrefs` as its ``max_visits``.

    Returns:
      A :class:`GarbageSummary`.
    """
    # pylint: disable=import-outside-toplevel
    import io
    import traceback

    debug_types_set = set(debug_types)
    debug_objs: dict[str, list[Any]] = {}
    type_paths: list[str] = []
    histogram: dict[str, int] = {}

    for obj in gc.garbage:
        cls = type(obj)
        if cls.__module__ == 'builtins':
            tpname = cls.__qualname__
        else:
            tpname = f'{cls.__module__}.{cls.__qualname__}'
        histogram[tpname] = histogram.get(tpname, 0) + 1

        # Sample objects we've been asked to dump ref-cycles for —
        # either by explicit type name in debug_types, or by being
        # any BaseException subclass when auto_include_exceptions
        # is on.
        sample_for_dump = tpname in debug_types_set or (
            auto_include_exceptions and isinstance(obj, BaseException)
        )
        if sample_for_dump:
            objs = debug_objs.setdefault(tpname, [])
            if len(objs) < debug_type_limit:
                objs.append(obj)

        # Capture dotted paths for type objects so callers can annotate
        # the histogram's 'type' entry inline.
        if tpname == 'type':
            type_paths.append(f'{obj.__module__}.{obj.__qualname__}')

    ref_dumps: dict[str, list[GarbageRefDump]] = {}
    for tpname, objs in debug_objs.items():
        dumps: list[GarbageRefDump] = []
        for obj in objs:
            buf = io.StringIO()
            printrefs(
                obj,
                file=buf,
                max_level=printrefs_max_level,
                max_visits=printrefs_max_visits,
            )
            exc_trace: str | None = None
            if isinstance(obj, BaseException):
                exc_trace = ''.join(
                    traceback.format_exception(
                        type(obj), obj, obj.__traceback__
                    )
                )
            dumps.append(
                GarbageRefDump(refs=buf.getvalue(), exception_trace=exc_trace)
            )
        ref_dumps[tpname] = dumps

    # Don't keep our own references to gc.garbage members in this
    # frame's locals once we're done — callers may want to clear
    # gc.garbage immediately after we return.
    debug_objs.clear()
    del debug_objs

    return GarbageSummary(
        histogram=histogram,
        ref_dumps=ref_dumps,
        type_paths=type_paths,
    )


def printtypes(
    limit: int = 50, file: TextIO | None = None, expanded: bool = False
) -> None:
    """Print a human readable list of which types have the most instances."""
    assert limit > 0
    objtypes: dict[str, int] = {}
    gc.collect()  # Recommended before get_objects().
    allobjs = _get_all_objects(expanded=expanded)
    allobjc = len(allobjs)
    for obj in allobjs:
        modname = type(obj).__module__
        tpname = type(obj).__qualname__
        if modname != 'builtins':
            tpname = f'{modname}.{tpname}'
        objtypes[tpname] = objtypes.get(tpname, 0) + 1

    if file is None:
        file = sys.stderr

    # Presumably allobjs contains stack-frame/dict type stuff
    # from this function call which in turn contain refs to allobjs.
    # Let's try to prevent these huge lists from accumulating until
    # the cyclical collector (hopefully) gets to them.
    allobjs.clear()
    del allobjs

    print(f'Types most allocated ({allobjc} total objects):', file=file)
    for i, tpitem in enumerate(
        sorted(objtypes.items(), key=lambda x: x[1], reverse=True)[:limit]
    ):
        tpname, tpval = tpitem
        percent = tpval / allobjc * 100.0
        print(f'{i+1}: {tpname}: {tpval} ({percent:.2f}%)', file=file)

    file.flush()


def printsizes(
    limit: int = 50, file: TextIO | None = None, expanded: bool = False
) -> None:
    """Print total allocated sizes of different types."""
    assert limit > 0
    objsizes: dict[str, int] = {}
    gc.collect()  # Recommended before get_objects().
    allobjs = _get_all_objects(expanded=expanded)
    totalobjsize = 0

    if file is None:
        file = sys.stderr

    for obj in allobjs:
        modname = type(obj).__module__
        tpname = type(obj).__qualname__
        if modname != 'builtins':
            tpname = f'{modname}.{tpname}'
        objsize = sys.getsizeof(obj)
        objsizes[tpname] = objsizes.get(tpname, 0) + objsize
        totalobjsize += objsize

    totalobjmb = totalobjsize / (1024 * 1024)
    print(
        f'Types with most allocated bytes ({totalobjmb:.2f} mb total):',
        file=file,
    )
    for i, tpitem in enumerate(
        sorted(objsizes.items(), key=lambda x: x[1], reverse=True)[:limit]
    ):
        tpname, tpval = tpitem
        percent = tpval / totalobjsize * 100.0
        print(f'{i+1}: {tpname}: {tpval} ({percent:.2f}%)', file=file)

    file.flush()


def _desctype(obj: Any) -> str:
    cls = type(obj)
    if cls is types.ModuleType:
        return f'{type(obj).__name__} {obj.__name__}'
    if cls is types.MethodType:
        bnd = 'bound' if hasattr(obj, '__self__') else 'unbound'
        return f'{bnd} {type(obj).__name__} {obj.__name__}'
    return f'{type(obj).__name__}'


def _desc(obj: Any) -> str:
    extra: str | None = None
    if isinstance(obj, list | tuple):
        # Print length and the first few types.
        tps = [_desctype(i) for i in obj[:3]]
        tpsj = ', '.join(tps)
        tpss = (
            f', contains [{tpsj}, ...]'
            if len(obj) > 3
            else f', contains [{tpsj}]' if tps else ''
        )
        extra = f' (len {len(obj)}{tpss})'
    elif isinstance(obj, dict):
        # If it seems to be the vars() for a type or module, try to
        # identify what.
        for ref in getrefs(obj):
            if hasattr(ref, '__dict__') and vars(ref) is obj:
                extra = f' (vars for {_desctype(ref)} @ {hex(id(ref))})'

        # Generic dict: print length and the first few key:type pairs.
        if extra is None:
            pairs = [
                f'{repr(n)}: {_desctype(v)}' for n, v in list(obj.items())[:3]
            ]
            pairsj = ', '.join(pairs)
            pairss = (
                f', contains {{{pairsj}, ...}}'
                if len(obj) > 3
                else f', contains {{{pairsj}}}' if pairs else ''
            )
            extra = f' (len {len(obj)}{pairss})'
    if extra is None:
        extra = ''
    return f'{_desctype(obj)} @ {hex(id(obj))}{extra}'


def _printrefs(
    obj: Any,
    *,
    level: int,
    max_level: int,
    exclude_objs: list,
    expand_ids: list[int],
    file: TextIO,
    state: dict[str, Any],
) -> None:
    # Visit-count safeguard. Print one truncation marker the first
    # time we go over and bail out of further recursion. Each level
    # in the tree calls gc.get_referrers which is O(heap-size); a
    # few highly-shared referrers can otherwise produce a runaway
    # traversal.
    state['visits'] += 1
    if state['visits'] > state['max_visits']:
        if not state['truncated_printed']:
            print(
                ('  ' * level)
                + f"[truncated: visit limit {state['max_visits']} reached]",
                file=file,
            )
            state['truncated_printed'] = True
        return

    ind = '  ' * level
    print(ind + _desc(obj), file=file)
    v = vars()
    if level < max_level or (id(obj) in expand_ids and level < ABS_MAX_LEVEL):
        refs = getrefs(obj)
        for ref in refs:
            # It seems we tend to get a transient cell object with
            # contents set to obj. Would be nice to understand why that
            # happens but just ignoring it for now.
            if isinstance(ref, types.CellType) and ref.cell_contents is obj:
                continue

            # Ignore anything we were asked to ignore.
            if exclude_objs is not None:
                if any(ref is eobj for eobj in exclude_objs):
                    continue

            # Ignore references from our locals.
            if ref is v:
                continue

            # The 'refs' list we just made will be listed as a referrer
            # of this obj, so explicitly exclude it from the obj's
            # listing.
            _printrefs(
                ref,
                level=level + 1,
                max_level=max_level,
                exclude_objs=exclude_objs + [refs],
                expand_ids=expand_ids,
                file=file,
                state=state,
            )


class DeadlockDumper:
    """Dumps thread states if still around after timeout seconds.

    This uses low level Python functionality so should still fire
    even in the case of deadlock.

    Only one of these can exist at a time so generally you should use
    :class:`DeadlockWatcher` instead (which uses this under the hood).
    """

    # faulthandler has a single traceback-dump-later state, so only
    # one of us can control it at a time.
    lock = threading.Lock()
    watch_in_progress = False

    def __init__(self, timeout: float, file: int | None = None) -> None:
        import faulthandler

        cls = type(self)

        with cls.lock:
            if cls.watch_in_progress:
                _get_logger().error(
                    'Existing DeadlockDumper found; new one will be a no-op.',
                )
                self.active = False
                return

            # Ok; no watch is in progress; we can be the active one.
            cls.watch_in_progress = True
            self.active = True
            if file is not None:
                faulthandler.dump_traceback_later(timeout=timeout, file=file)
            else:
                faulthandler.dump_traceback_later(timeout=timeout)

    def invalidate(self) -> None:
        """Call off the dump.

        Can be good to call this explicitly and not rely on releasing
        references since exceptions can unintentionally keep it alive
        longer than intended otherwise.
        """
        import faulthandler

        cls = type(self)

        # If we're the active dump, call it off.
        with cls.lock:
            if self.active:
                starttime = time.monotonic()
                faulthandler.cancel_dump_traceback_later()
                duration = time.monotonic() - starttime
                if duration > 1.0:
                    _get_logger().error(
                        'DeadlockDumper faulthandler cancel took %.2fs;'
                        ' should not happen.',
                        duration,
                    )
                cls.watch_in_progress = False
                self.active = False

    def __del__(self) -> None:
        self.invalidate()


class DeadlockWatcher:
    """Individual watcher for deadlock conditions.

    Use the enable_deadlock_watchers() to enable this system.

    Next, use these wrapped in a with statement around some operation
    that may deadlock. If the with statement does not complete within the
    timeout period, a traceback of all threads will be dumped.

    Note that the checker thread runs a cycle every ~5 seconds, so
    something stuck needs to remain stuck for 5 seconds or so to be
    caught for sure.
    """

    watchers_lock: threading.Lock | None = None
    watchers: list[weakref.ref[DeadlockWatcher]] | None = None

    def __init__(
        self,
        timeout: float = 10.0,
    ) -> None:
        from efro.util import caller_source_location

        # pylint: disable=not-context-manager
        cls = type(self)
        if cls.watchers_lock is None or cls.watchers is None:
            _get_logger().error(
                'DeadlockWatcher created without watchers enabled.',
            )
            return

        # All we do is record when we were made and how long till we
        # expire.
        self.create_time = time.monotonic()
        self.timeout = timeout
        self.noted_expire = False
        # self.logger = logger
        # self.logextra = logextra
        self.caller_source_loc = caller_source_location()
        curthread = threading.current_thread()
        self.thread_id = (
            '<unknown>'
            if curthread.ident is None
            else hex(curthread.ident).removeprefix('0x')
        )
        self.active = False

        with cls.watchers_lock:
            cls.watchers.append(weakref.ref(self))

    # Support the with statement.
    def __enter__(self) -> Any:
        self.active = True
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, exc_tb: Any) -> None:
        self.active = False

        duration = time.monotonic() - self.create_time
        if duration > self.timeout:
            _get_logger().error(
                'DeadlockWatcher %s at %s in thread %s lived %.2fs,'
                ' past its timeout of %.2fs. You should see a deadlock dump.',
                id(self),
                self.caller_source_loc,
                self.thread_id,
                duration,
                self.timeout,
            )

    @classmethod
    def enable_deadlock_watchers(cls, use_logs: bool = True) -> None:
        """Spins up deadlock-watcher functionality.

        Must be explicitly called before any DeadlockWatchers are
        created.

        :param use_logs: If ``True``, deadlock stack dumps will be
          emitted through Python logging and will include extra info.
          While generally preferable, this will not work if the GIL is
          permanently deadlocked. The ``False`` option will emit dumps
          through stderr which should work even if the GIL is
          deadlocked.
        """
        from efro.util import strict_partial

        assert cls.watchers_lock is None
        cls.watchers_lock = threading.Lock()
        assert cls.watchers is None
        cls.watchers = []

        threading.Thread(
            target=strict_partial(
                cls._deadlock_watcher_thread_main, use_logs=use_logs
            ),
            daemon=True,
        ).start()

    @classmethod
    def _deadlock_watcher_thread_main(cls, use_logs: bool) -> None:
        # pylint: disable=not-context-manager
        # pylint: disable=not-an-iterable
        from tempfile import TemporaryDirectory

        assert cls.watchers_lock is not None and cls.watchers is not None

        thread_start_time = time.monotonic()

        # Spin in a loop checking our watchers periodically and dumping
        # state if any have timed out. The trick here is that we don't
        # explicitly dump state, but rather we set up a "dead man's
        # switch" that does so after some amount of time if we don't
        # explicitly cancel it. This way we should get state dumps even
        # for things like total GIL deadlocks.
        with TemporaryDirectory() as tempdir:
            logfilepath = os.path.join(tempdir, 'dumps')
            if use_logs:
                # pylint: disable=consider-using-with
                logfile = open(logfilepath, 'wb')
            else:
                logfile = None

            while True:

                timeout = 5.171
                starttime = time.monotonic()

                # Set a dead man's switch for this pass.
                dumper = DeadlockDumper(
                    timeout=timeout,
                    file=logfile.fileno() if logfile is not None else None,
                )

                ex = f't1 {time.monotonic()-starttime:.2f}'

                # Sleep most of the way through it but give ourselves time
                # to turn it off if we're still responsive.
                time.sleep(timeout - 1.53)
                now = time.monotonic()

                ex += f' t2 {time.monotonic()-starttime:.2f}'

                found_fresh_expired = False

                watcher_info: str | None = None

                # If any watcher is still active and expired, sleep past the
                # timeout to force the dumper to do its thing.
                with cls.watchers_lock:

                    for wref in cls.watchers:
                        w = wref()
                        if (
                            w is not None
                            and now - w.create_time > w.timeout
                            and not w.noted_expire
                            and w.active
                        ):
                            # If they supplied a logger, let them know they
                            # should check stderr for a dump.
                            _get_logger().error(
                                'Found expired DeadlockWatcher %s at %s'
                                ' in thread %s;'
                                ' will force a state dump.',
                                id(w),
                                w.caller_source_loc,
                                w.thread_id,
                            )
                            wdur = now - w.create_time
                            watcher_info = (
                                f'DeadlockWatcher {id(w)}'
                                f' at {w.caller_source_loc}'
                                f' in thread {w.thread_id}'
                                f' lived {wdur:.2f}s past its timeout of'
                                f' {w.timeout:.2f}s.'
                            )
                            found_fresh_expired = True
                            w.noted_expire = True

                        # Important to clear this ref; otherwise we can keep
                        # a random watcher alive until our next time through.
                        w = None

                    # Prune dead watchers and reset for the next pass.
                    cls.watchers = [w for w in cls.watchers if w() is not None]

                if found_fresh_expired:
                    # Push us over the dumper time limit which give us a
                    # lovely dump. Technically we could just do an immediate
                    # dump here instead, but that would give us two paths to
                    # maintain instead of this single one.
                    time.sleep(2.0)

                # Call off the dump if it hasn't happened yet.
                dumper.invalidate()
                del dumper

                now = time.monotonic()
                duration = now - starttime
                total_duration = now - thread_start_time

                # If it seems that we dumped.
                if duration > timeout:
                    # If we dumped to a file, try to read it and log it.
                    if logfile is not None:

                        # Wait until a few seconds after the dump's
                        # scheduled time to give it a good chance to
                        # finish.
                        while now < starttime + timeout + 3.0:
                            time.sleep(0.5)
                            now = time.monotonic()
                        try:
                            logfile.close()
                            with open(
                                logfilepath, 'r', encoding='utf-8'
                            ) as infile:
                                dump = infile.read()
                            # Reset it for next time.
                            os.remove(logfilepath)
                            # pylint: disable=consider-using-with
                            logfile = open(logfilepath, 'wb')
                            if watcher_info is None:
                                # This seems to happen periodically
                                # simply due to scheduling on some
                                # server setups. So let's just warn
                                # instead of erroring.
                                logcall = _get_logger().warning
                                watcher_info = (
                                    f'No expired watchers found'
                                    f' (slept {duration:.2f}s of'
                                    f' {timeout:.2f}s,'
                                    f' {total_duration:.2f}s'
                                    f' since thread start).'
                                    f' ex: {ex}'
                                )
                            else:
                                logcall = _get_logger().error
                            logcall(
                                'Deadlock Detected!\n%s\n\n%s',
                                watcher_info,
                                dump,
                            )
                        except Exception:
                            _get_logger().exception(
                                'Error logging/resetting dump file.'
                            )
                            logfile = None

                    # Its possible that our dumper fired without us
                    # wanting to; this likely means something was
                    # holding on to the GIL. Let the user know (but only
                    # if we're NOT using logging, since we already
                    # include this info there).
                    if not found_fresh_expired and not use_logs:
                        _get_logger().error(
                            'DeadlockWatcher thread seems to have dumped states'
                            ' without any expired watchers'
                            ' (slept %.2f of %.2f, %.2f since thread start).'
                            ' This likely means something is not playing nice'
                            ' with the GIL.',
                            duration,
                            timeout,
                            now - thread_start_time,
                        )
