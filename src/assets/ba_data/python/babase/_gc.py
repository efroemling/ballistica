# Released under the MIT License. See LICENSE for details.
#
"""Utility functionality related to the overall operation of the app."""
from __future__ import annotations

import gc
import os
import time
import random
import logging
from enum import Enum
from typing import TYPE_CHECKING, assert_never, override

import bacommon.logging

import _babase
from babase._appsubsystem import AppSubsystem
from babase._logging import gc_log

if TYPE_CHECKING:
    import datetime
    from typing import Any, TextIO, Callable

    import babase


class GarbageCollectionSubsystem(AppSubsystem):
    """Garbage collection functionality for the app.

    Access the single shared instance of this class via the
    :attr:`~babase.App.gc` attr on the :class:`~babase.App` class.

    Design
    ======

    Python objects are deallocated in one of two ways: either they are
    immediately deallocated when the last reference to them disappears,
    or they are later deallocated by the cyclic garbage collector, which
    looks for groups of objects retaining references to each other but
    otherwise unaccessible and deallocates them as a group (see:
    Python's :mod:`gc` module).

    Python's garbage collector runs at arbitrary times and can be
    expensive to run, making it liable to cause visual hitches in game
    situations such as ours. For this reason, Ballistica disables it by
    default and instead runs explicit passes at times when hitches won't
    be noticable; namely during in-game transitions when the screen is
    faded to black.

    Because significant time can pass between these explicit passes, we
    try to minimize the number of objects relying on the garbage
    collector for cleanup; otherwise we risk bloating memory usage if a
    single uninterrupted stretch of gameplay repeatedly generates such
    objects. It is generally desirable to avoid reference cycles anyway
    and keep deallocation of objects deterministic and predictable.

    To aid in minimizing garbage-collector reliance, Ballistica's
    standard behavior is to flip on some Python garbage-collection debug
    flags, examine objects being garbage-collected, and provide the user
    with information and warnings if the number of such objects gets too
    large. Controls are provided here to adjust that behavior (see
    :attr:`mode`).

    Note that the goal is simply to keep garbage collection under
    control; not to eliminate it completely. There seems to be a number
    of situations, even within Python stdlib modules, where reference
    loops are mostly unavoidable, and trying to hunt down every last one
    seems like an exercise in futility. We mostly just aim to keep
    things under our warning thresholds so runaway memory usage never
    becomes a problem.

    Usage
    =====

    To switch garbage-collection modes for debugging, do something like::

      babase.app.gc.mode = babase.app.gc.Mode.LEAK_DEBUG

    The engine will remember modes you set this way, allowing you to set
    a mode and then debug repeated runs of the app. Just remember to
    switch back to :attr:`~Mode.STANDARD` mode when finished.

    You can also set mode using the environment variable
    ``BA_GC_MODE``. Modes set this way take precedence over
    modes set using the above method and only apply for the current run.

    For example, to run in :attr:`~Mode.LEAK_DEBUG` mode:

    .. code-block:: sh

      BA_GC_MODE=leak_debug ./bombsquad
    """

    class Mode(Enum):
        """Garbage-collection modes the app can be in.

        For most of these modes, the engine will assume control of
        Python's garbage collector - disabling automatic collection,
        setting debug flags, and running explicit collections on the
        engine's behalf (You can set :attr:`DISABLED` mode if you need
        to avoid this).
        """

        #: In this mode, when the engine runs an explicit garbage
        #: collection pass, it examine the results and logs basic useful
        #: info such as total number of collected objects by type to the
        #: :attr:`~bacommon.logging.ClientLoggerName.GARBAGE_COLLECTION`
        #: logger. By default these will be :obj:`~logging.INFO` or
        #: :obj:`~logging.DEBUG` log messages (generally not visible by
        #: default), but if ever too many objects are handled in a
        #: single pass, a single :obj:`~logging.WARNING` will be emitted
        #: instead.
        #:
        #: The general idea is that this mode stays out of your way
        #: during normal app operation but warns you if things ever get
        #: messy enough to need attention. You can then use the basic
        #: info provided by its log messages to address the issue or, if
        #: need be, you can flip to :attr:`LEAK_DEBUG` mode to dive in
        #: deeper.
        STANDARD = 'standard'

        #: In this mode, Python's garbage-collector is set to the
        #: :obj:`gc.DEBUG_LEAK` flag, which causes information on all
        #: objects handled by the garbage-collector to be printed and
        #: all collected objects to be stored in :obj:`gc.garbage`. Be
        #: aware that in this mode *NOTHING* is actually deallocated
        #: by the garbage-collector, so only use this for debugging.
        #: This mode is useful for interactively digging into particular
        #: reference cycles; you can use :meth:`efro.debug.getobj()` to
        #: find an object based on the hex id printed for it and then
        #: use :meth:`efro.debug.printrefs()` to look into what is
        #: referencing that object.
        #:
        #: Example::
        #:
        #:   # Output from a garbage collection pass in LEAK_DEBUG mode,
        #:   # listing objects the garbage-collector handled:
        #:   # gc: collectable <tuple 0x105f95860>
        #:   # gc: collectable <type 0x12e059030>
        #:   # gc: collectable <tuple 0x1060f1400>
        #:   # gc: collectable <getset_descriptor 0x106234470>
        #:   # gc: collectable <dict 0x1062342f0>
        #:   # gc: collectable <getset_descriptor 0x1062344d0>
        #:
        #:   # We can then use printrefs() to see what is referencing some
        #:   # object, what is referencing those references, etc.
        #:   from efro.debug import printrefs, getobj
        #:   printrefs(getobj(0x1060f1400))
        #:
        #:   # Output:
        #:   # tuple @ 0x1060f1400 (len 2, contains [type, type])
        #:   #   type @ 0x12e059030
        #:   #     tuple @ 0x1060f1400 (len 2, contains [type, type])
        #:   #     getset_descriptor @ 0x106234470
        #:   #     getset_descriptor @ 0x1062344d0
        LEAK_DEBUG = 'leak_debug'

        #: In this mode, Python's garbage collection is left completely
        #: untouched. Use this if you want to do some sort of manual
        #: debugging/experimenting where our default logic would get in
        #: the way. Note that you should generally restart the app after
        #: switching to this mode, as it will not undo any changes that
        #: have already been made by other modes.
        DISABLED = 'disabled'

    _MODE_CONFIG_KEY = 'Garbage Collection Mode'
    _SCREEN_MSG_COLOR = (1.0, 0.8, 0.4)

    def __init__(self) -> None:

        #: A :func:`time.monotonic()` value updated whenever we do an
        #: actual :func:`gc.collect()`. Note that not all calls to our
        #: :meth:`collect()` method result in an actual
        #: :func:`gc.collect()` happening (if not enough time has
        #: passed, etc.)
        self.last_actual_collect_time: float | None = None

        self._total_num_gc_objects = 0
        self._last_collection_time: float | None = None
        self._showed_standard_mode_warning = False
        self._mode: GarbageCollectionSubsystem.Mode | None = None

    @override
    def on_app_running(self) -> None:
        """:meta private:"""
        # Inform the user if we're set to something besides standard
        # (so they don't forget to switch it back when done).
        if self._mode is not None and self._mode is not self.Mode.STANDARD:
            _babase.screenmessage(
                f'Garbage-gollection mode is {self._mode.name}.',
                color=self._SCREEN_MSG_COLOR,
            )
        # Also log some usage tips (handy to copy/paste).
        if self._mode is self.Mode.LEAK_DEBUG:
            gc_log.warning(
                (
                    'Garbage-gollection mode is %s.\n'
                    'Eliminate ref-loops to minimize'
                    ' garbage-collected objects.\n'
                    'Set %s logger to INFO or DEBUG for more info.\n'
                    'To debug refs for an object, do:'
                    ' `from efro.debug import printrefs, getobj;'
                    ' printrefs(getobj(OBJID))`.'
                ),
                self._mode.name,
                bacommon.logging.ClientLoggerName.GARBAGE_COLLECTION.value,
            )

    @property
    def mode(self) -> Mode:
        """The app's current garbage-collection mode.

        Be aware that changes to this mode persist across runs of the
        app (you will see on-screen warnings at launch if it is set to
        non-default value).
        """
        if self._mode is None:
            raise RuntimeError('Initial mode has not yet been set.')
        return self._mode

    @mode.setter
    def mode(self, mode: Mode) -> None:
        cls = type(mode)

        _babase.screenmessage(
            f'Garbage-gollection mode is now {mode.name}.',
            color=self._SCREEN_MSG_COLOR,
        )
        self._apply_mode(mode)

        # Store to app config.
        cfg = _babase.app.config
        if mode is cls.STANDARD:
            # For default, store nothing.
            cfg.pop(self._MODE_CONFIG_KEY, None)
        else:
            cfg[self._MODE_CONFIG_KEY] = mode.value
        cfg.commit()

    def collect(self, force: bool = False) -> None:
        """Request an explicit garbage collection pass.

        Apps should call this when visual hitches would not be noticed,
        such as when the screen is faded to black during transitions.

        The effect of this call is influenced by the current
        :attr:`mode` and other factors. For instance, if mode is
        :attr:`Mode.DISABLED` or if not enough time has passed since the
        last collect, then this call is a no-op.
        """

        if self._mode is None:
            gc_log.debug(
                'Skipping explicit gc pass (no mode set).',
            )
            return

        if self._mode is self.Mode.DISABLED:
            gc_log.debug(
                'Skipping explicit gc pass (mode is %s).',
                self.Mode.DISABLED.name,
            )
            return

        # If we find automatic gc is somehow enabled, abort.
        if gc.isenabled():
            gc_log.debug(
                'Skipping explicit gc pass'
                ' (automatic collection is enabled).'
            )
            return

        # Even when nothing is collected, a full gc pass is a bit of
        # work, so skip runs if they happen too close together.
        now = time.monotonic()
        if (
            self._last_collection_time is not None
            and now - self._last_collection_time < 20
            and not force
        ):
            gc_log.debug('Skipping explicit gc pass (too little time passed).')
            return

        # Also let's skip occasional runs randomly to shake things up a
        # bit for object cleanup checks. For example, if we're running a
        # check a few seconds after a game ends to make sure all game
        # objects have been deallocated, an explicit GC pass that
        # consistently happens around that same time could hide
        # reference loops that we'd like to know about. If we skip the
        # GC occasionally, those sorts of issues are more likely to come
        # to light.
        if not force and random.random() > 0.8:
            gc_log.debug('Skipping explicit gc pass (random jitter).')
            return

        if self._mode is self.Mode.STANDARD:
            self._collect_standard(now)
        elif self._mode is self.Mode.LEAK_DEBUG:
            self._collect_leak_debug(now)
        else:
            assert_never(self._mode)

        self._last_collection_time = now

    def set_initial_mode(self) -> None:
        """:meta private:"""

        # If an env var is set, that takes priority.
        envval = os.environ.get('BA_GC_MODE')
        if envval:
            try:
                self._mode = self.Mode(envval)
            except ValueError:
                gc_log.warning(
                    'Invalid garbage-collection-mode; valid options are %s.',
                    [m.value for m in self.Mode],
                )
        if self._mode is None:
            self._mode = self._mode_from_config()

        self._apply_mode(self._mode)

    def _collect_standard(self, now: float) -> None:

        assert gc.get_debug() == gc.DEBUG_SAVEALL

        # Make more noise (warning instead of info) if there's a
        # substantial number of collections in a single cycle.
        gc_threshold = 50

        starttime = now
        num_affected_objs = gc.collect()
        now2 = self.last_actual_collect_time = time.monotonic()
        duration = now2 - starttime
        self._total_num_gc_objects += num_affected_objs

        if (
            num_affected_objs >= gc_threshold
            and not self._showed_standard_mode_warning
        ):
            loglevel: int = logging.WARNING
            self._showed_standard_mode_warning = True
        else:
            loglevel = logging.INFO

        log_is_visible = gc_log.isEnabledFor(loglevel)
        obj_summary = ''

        # Since we started with DEBUG_SAVEALL on, any objects we just
        # collected should show up in gc.garbage. So we go through those
        # objects, print stats or warnings as necessary, and then clear
        # the list and run another gc pass without DEBUG_SAVEALL to
        # *actually* kill them.
        if num_affected_objs > 0:

            # Build our summary of collected stuff ONLY if we'll actually
            # be showing it.
            if log_is_visible:
                try:
                    obj_summary = _summarize_garbage(loglevel)
                except Exception:
                    gc_log.exception('Error summarizing garbage.')
                    obj_summary = '(error in summarization)'

            if len(gc.garbage) < num_affected_objs:
                gc_log.debug(
                    (
                        '_collect_standard() collected %d objs but'
                        ' only %d appear in gc.garbage; unexpected.'
                    ),
                    num_affected_objs,
                    len(gc.garbage),
                )

            # *Actually* kill any stuff we found by temporarily turning
            # *off save-all and running another collect.
            if gc.garbage:
                gc.set_debug(0)
                gc.garbage.clear()
                gc.collect()
                gc.set_debug(gc.DEBUG_SAVEALL)

        # We should have no garbage left at this point.
        if gc.garbage:
            gc_log.debug(
                (
                    'Wound up with %d items in gc.garbage'
                    ' after _collect_standard() cleanup; not expected.'
                ),
                len(gc.garbage),
            )

        # Report some general stats on what we just did.
        from_last = (
            ''
            if self._last_collection_time is None
            else f' from last {now - self._last_collection_time:.1f}s'
        )
        gc_log.log(
            loglevel,
            'Explicit gc pass handled %d objects%s in %.3fs (total: %d).%s',
            num_affected_objs,
            from_last,
            duration,
            self._total_num_gc_objects,
            obj_summary,
        )

    def _collect_leak_debug(self, now: float) -> None:
        starttime = now
        num_affected_objs = gc.collect()
        now2 = self.last_actual_collect_time = time.monotonic()
        duration = now2 - starttime
        self._total_num_gc_objects += num_affected_objs

        # Just report some general stats on what we collected. The
        # debugging output from Python itself will be the most useful
        # thing here.
        from_last = (
            ''
            if self._last_collection_time is None
            else f' from last {now - self._last_collection_time:.1f}s'
        )
        gc_log.info(
            'Explicit gc pass handled %d objects%s in %.3fs (total: %d).',
            num_affected_objs,
            from_last,
            duration,
            self._total_num_gc_objects,
        )

    def _apply_mode(self, mode: Mode) -> None:
        cls = type(mode)
        if mode is cls.DISABLED:
            # Do nothing.
            pass
        elif mode is cls.LEAK_DEBUG:
            # For this mode we turn off collect, Enable printing all
            # collected objects to stderr, and keep all collected
            # objects around for introspection.
            gc.disable()
            gc.set_debug(gc.DEBUG_LEAK)
        elif mode is cls.STANDARD:
            # In this mode we turn off collect and keep all collected
            # objects around for introspection. When we do an explicit
            # collect we'll temporarily turn off save-all and *actually*
            # delete collected stuff after examining/reporting it.
            gc.disable()
            gc.set_debug(gc.DEBUG_SAVEALL)
        else:
            assert_never(mode)

    def _mode_from_config(self) -> Mode:
        cfg = _babase.app.config
        configval = cfg.get(self._MODE_CONFIG_KEY)
        if configval is None:
            mode = self.Mode.STANDARD
        else:
            try:
                mode = self.Mode(configval)
            except ValueError:
                if _babase.do_once():
                    gc_log.warning(
                        "Invalid garbage-collection mode '%s'.", configval
                    )
                mode = self.Mode.STANDARD

        return mode


# Show some inline extra bits for specific types (such
# as type names for type objects).
def _inline_extra(tpname: str, type_paths: list[str]) -> str:
    if tpname == 'type':
        return ' (' + ', '.join(sorted(type_paths)) + ')'
    return ''


def _summarize_garbage(loglevel: int) -> str:
    """Print stuff about gc.garbage to aid in breaking ref cycles."""
    # pylint: disable=too-many-locals
    import io
    import traceback
    from efro.debug import printrefs

    debug_types: set[str]
    debug_type_limit: int
    plus = _babase.app.plus
    if plus is None:
        debug_types = set()
        debug_type_limit = 1
    else:
        debug_types = set(plus.cloud.vals.gc_debug_types)
        debug_type_limit = plus.cloud.vals.gc_debug_type_limit

    debug_objs: dict[str, list[Any]] = {}

    type_paths: list[str] = []
    objtypecounts: dict[str, int] = {}

    for obj in gc.garbage:
        cls = type(obj)
        if cls.__module__ == 'builtins':
            tpname = cls.__qualname__
        else:
            tpname = f'{cls.__module__}.{cls.__qualname__}'
        objtypecounts[tpname] = objtypecounts.get(tpname, 0) + 1

        # Store specific objs for anything we're supposed to
        # be debugging.
        if tpname in debug_types and bool(True):
            objs = debug_objs.setdefault(tpname, [])
            if len(objs) < debug_type_limit:
                objs.append(obj)
            del objs

        # Store type-names for types to show inline.
        if tpname == 'type':
            type_paths.append(f'{obj.__module__}.{obj.__qualname__}')

    obj_summary = '\nObjects by type:' + ''.join(
        f'\n  {tpname}:' f' {tpcount}{_inline_extra(tpname, type_paths)}'
        for tpname, tpcount in sorted(
            objtypecounts.items(),
            key=lambda i: (-i[1], i[0]),
        )
    )

    for debug_obj_type, objs in sorted(debug_objs.items()):
        for i, obj in enumerate(objs):
            buffer = io.StringIO()
            printrefs(obj, file=buffer)
            buffer_indented = '\n'.join(
                f'  {line}' for line in buffer.getvalue().splitlines()
            )
            obj_summary += (
                f'\n'
                f'Refs for {debug_obj_type} {i+1} of {len(objs)}:\n'
                f'{buffer_indented}'
            )
            if isinstance(obj, BaseException):
                trace_str = ''.join(
                    traceback.format_exception(
                        type(obj), obj, obj.__traceback__
                    )
                )
                trace_str = '\n'.join(
                    f'  {line}' for line in trace_str.splitlines()
                )
                obj_summary += (
                    f'\n'
                    f'Stack for {debug_obj_type} {i+1} of {len(objs)}:\n'
                    f'{trace_str}'
                )

    # Include overview if this a warning message.
    if loglevel == logging.WARNING:
        obj_summary += (
            '\nToo many objects garbage-collected'
            ' - try to reduce this.\n'
            'See babase.GarbageCollectionSubsystem documentation'
            ' to learn how.'
        )
    return obj_summary
