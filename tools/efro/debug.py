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
from __future__ import annotations

import gc
import sys
import time
import types
import weakref
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, TextIO

    from logging import Logger

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


def getobjs(
    cls: type | str, contains: str | None = None, expanded: bool = False
) -> list[Any]:
    """Return all garbage-collected objects matching criteria.

    'type' can be an actual type or a string in which case objects
    whose types contain that string will be returned.

    If 'contains' is provided, objects will be filtered to those
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
    """Return an expanded list of all objects.

    See https://utcc.utoronto.ca/~cks/space/blog/python/GetAllObjects
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
    """Return a garbage-collected object by its id.

    Remember that this is VERY inefficient and should only ever be used
    for debugging.
    """
    if not isinstance(objid, int):
        raise TypeError(f'Expected an int for objid; got a {type(objid)}.')

    # Don't wanna return stuff waiting to be garbage-collected.
    gc.collect()

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
            f' FileIO={fileio_s}'
        )


def printrefs(
    obj: Any,
    max_level: int = 2,
    exclude_objs: list[Any] | None = None,
    expand_ids: list[int] | None = None,
    file: TextIO | None = None,
) -> None:
    """Print human readable list of objects referring to an object.

    'max_level' specifies how many levels of recursion are printed.
    'exclude_objs' can be a list of exact objects to skip if found in the
      referrers list. This can be useful to avoid printing the local context
      where the object was passed in from (locals(), etc).
    'expand_ids' can be a list of object ids; if that particular object is
      found, it will always be expanded even if max_level has been reached.
    """
    _printrefs(
        obj,
        level=0,
        max_level=max_level,
        exclude_objs=[] if exclude_objs is None else exclude_objs,
        expand_ids=[] if expand_ids is None else expand_ids,
        file=sys.stderr if file is None else file,
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


def printsizes(
    limit: int = 50, file: TextIO | None = None, expanded: bool = False
) -> None:
    """Print total allocated sizes of different types."""
    assert limit > 0
    objsizes: dict[str, int] = {}
    gc.collect()  # Recommended before get_objects().
    allobjs = _get_all_objects(expanded=expanded)
    totalobjsize = 0

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


def _desctype(obj: Any) -> str:
    cls = type(obj)
    # noinspection PyPep8
    if cls is types.ModuleType:
        return f'{type(obj).__name__} {obj.__name__}'
    # noinspection PyPep8
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
        # If it seems to be the vars() for a type or module,
        # try to identify what.
        for ref in getrefs(obj):
            if hasattr(ref, '__dict__') and vars(ref) is obj:
                extra = f' (vars for {_desctype(ref)} @ {id(ref)})'

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
    return f'{_desctype(obj)} @ {id(obj)}{extra}'


def _printrefs(
    obj: Any,
    *,
    level: int,
    max_level: int,
    exclude_objs: list,
    expand_ids: list[int],
    file: TextIO,
) -> None:
    ind = '  ' * level
    print(ind + _desc(obj), file=file)
    v = vars()
    if level < max_level or (id(obj) in expand_ids and level < ABS_MAX_LEVEL):
        refs = getrefs(obj)
        for ref in refs:
            # It seems we tend to get a transient cell object with contents
            # set to obj. Would be nice to understand why that happens
            # but just ignoring it for now.
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
            # of this obj, so explicitly exclude it from the obj's listing.
            _printrefs(
                ref,
                level=level + 1,
                max_level=max_level,
                exclude_objs=exclude_objs + [refs],
                expand_ids=expand_ids,
                file=file,
            )


class DeadlockDumper:
    """Dumps thread states if still around after timeout seconds.

    This uses low level Python functionality so should still fire
    even in the case of deadlock.
    """

    # faulthandler has a single traceback-dump-later state, so only
    # one of us can control it at a time.
    lock = threading.Lock()
    watch_in_progress = False

    def __init__(self, timeout: float) -> None:
        import faulthandler

        cls = type(self)

        with cls.lock:
            if cls.watch_in_progress:
                print(
                    'Existing DeadlockDumper found; new one will be a no-op.',
                    file=sys.stderr,
                )
                self.active = False
                return

            # Ok; no watch is in progress; we can be the active one.
            cls.watch_in_progress = True
            self.active = True
            faulthandler.dump_traceback_later(timeout=timeout)

    def __del__(self) -> None:
        import faulthandler

        cls = type(self)

        # If we made it to here, call off the dump. But only if we are
        # the active dump.
        if self.active:
            faulthandler.cancel_dump_traceback_later()
            cls.watch_in_progress = False


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
        logger: Logger | None = None,
        logextra: dict | None = None,
    ) -> None:
        from efro.util import caller_source_location

        # pylint: disable=not-context-manager
        cls = type(self)
        if cls.watchers_lock is None or cls.watchers is None:
            print(
                'DeadlockWatcher created without watchers enabled.',
                file=sys.stderr,
            )
            return

        # All we do is record when we were made and how long till we
        # expire.
        self.create_time = time.monotonic()
        self.timeout = timeout
        self.noted_expire = False
        self.logger = logger
        self.logextra = logextra
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

        # Print if we lived past our deadline. This is just an extra
        # data point. The watcher thread should be doing the actual
        # stack dumps/etc.
        if self.logger is None or self.logextra is None:
            return

        duration = time.monotonic() - self.create_time
        if duration > self.timeout:
            self.logger.error(
                'DeadlockWatcher %s at %s in thread %s lived %.2fs,'
                ' past timeout %.2fs. This should have triggered'
                ' a deadlock dump.',
                id(self),
                self.caller_source_loc,
                self.thread_id,
                duration,
                self.timeout,
                extra=self.logextra,
            )

    @classmethod
    def enable_deadlock_watchers(cls) -> None:
        """Spins up deadlock-watcher functionality.

        Must be explicitly called before any DeadlockWatchers are
        created.
        """
        assert cls.watchers_lock is None
        cls.watchers_lock = threading.Lock()
        assert cls.watchers is None
        cls.watchers = []

        threading.Thread(
            target=cls._deadlock_watcher_thread_main, daemon=True
        ).start()

    @classmethod
    def _deadlock_watcher_thread_main(cls) -> None:
        # pylint: disable=not-context-manager
        # pylint: disable=not-an-iterable
        assert cls.watchers_lock is not None and cls.watchers is not None

        # Spin in a loop checking our watchers periodically and dumping
        # state if any have timed out. The trick here is that we don't
        # explicitly dump state, but rather we set up a "dead man's
        # switch" that does so after some amount of time if we don't
        # explicitly cancel it. This way we'll hopefully get state dumps
        # even for things like total GIL deadlocks.
        while True:

            # Set a dead man's switch for this pass.
            dumper = DeadlockDumper(timeout=5.171)

            # Sleep most of the way through it but give ourselves time
            # to turn it off if we're still responsive.
            time.sleep(4.129)
            now = time.monotonic()

            found_fresh_expired = False

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
                        if w.logger is not None:
                            w.logger.error(
                                'DeadlockWatcher %s at %s in thread %s'
                                ' with time %.2f expired;'
                                ' check stderr for stack traces.',
                                id(w),
                                w.caller_source_loc,
                                w.thread_id,
                                w.timeout,
                                extra=w.logextra,
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
            del dumper
