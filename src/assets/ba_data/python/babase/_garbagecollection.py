# Released under the MIT License. See LICENSE for details.
#
"""Utility functionality related to the overall operation of the app."""
from __future__ import annotations

import gc
import time
import logging
from typing import TYPE_CHECKING

import _babase
from babase._appsubsystem import AppSubsystem

if TYPE_CHECKING:
    import datetime
    from typing import Any, TextIO, Callable

    import babase


class GarbageCollectionSubsystem(AppSubsystem):
    """Garbage collection functionality for the app.

    Access the single shared instance of this class via the
    :attr:`~babase.App.gc` attr on the :class:`~babase.App` class.
    """

    def __init__(self) -> None:
        self._total_num_gc_objects = 0
        self._last_collection_time = 0.0
        self._showed_elim_tip = False
        self._showed_debug_tip = False
        self._showed_debug_ref_tip = False

    def collect(self, force: bool = False) -> None:
        """Run an explicit pass of cyclic garbage collection.

        By default, ballistica disables Python's cyclic garbage collector to
        avoid unpredictable hitches. However, there still may be objects in
        dependency loops that cannot be freed without it. This call can be
        run at explicit times when hitches won't be a problem (namely when
        the screen is faded to black) to free such objects.

        Another purpose of this call is to convey via logs when too many
        objects are getting collected and support efforts to eliminate
        the dependency loops causing it. For that reason, always call
        this method instead of calling :func:`gc.collect()` directly.
        """
        from babase._logging import garbagecollectionlog

        # If automatic gc is still enabled, skip all this.
        if gc.isenabled():
            garbagecollectionlog.info(
                'Skipping explicit garbage-collection'
                ' (automatic collection is enabled).'
            )
            return

        # Even if nothing is collected, a full gc pass is a bit of work,
        # so skip runs if they happen too close together.
        now = time.monotonic()
        if now - self._last_collection_time < 20 and not force:
            garbagecollectionlog.debug(
                'Skipping explicit garbage-collection'
                ' (too little time passed since last).'
            )
            return
        self._last_collection_time = now

        garbagecollectionlog.info('Running cyclic-garbage-collector.')

        debug_leak_enabled = gc.get_debug() & gc.DEBUG_LEAK == gc.DEBUG_LEAK

        # Normally we don't make noise until there's a substantial amount of
        # gc happening, but if we are explicitly debugging leaks then we
        # make noise for *any* gc.
        gc_threshold = 0 if debug_leak_enabled else 50

        # Do the thing.
        starttime = time.monotonic()
        num_affected_objs = gc.collect()
        duration = time.monotonic() - starttime

        self._total_num_gc_objects += num_affected_objs

        # If we pass our gc threshold, make some noise. Normally just do
        # this once, or do it every time if we're doing leak debugging.
        if num_affected_objs > gc_threshold and (
            _babase.do_once() or debug_leak_enabled
        ):
            loglevel = logging.WARNING

        else:
            loglevel = logging.INFO

        # Bail here if logging is off for this level (so we accurately
        # track whether our one-time messages have been shown)
        if not garbagecollectionlog.isEnabledFor(loglevel):
            return

        if num_affected_objs and not self._showed_elim_tip:
            self._showed_elim_tip = True
            elimtip = (
                '\nEliminate reference loops to get this as close'
                ' to 0 as possible.'
            )
        else:
            elimtip = ''

        # If debugging is off, show how to turn it on, and, if it is on,
        # show how to debug refs.
        if debug_leak_enabled:
            if not self._showed_debug_ref_tip:
                self._showed_debug_ref_tip = True
                tip = (
                    '\nTo debug refs for an object, do'
                    ' `from efro.debug import printrefs, getobj;'
                    ' printrefs(getobj(OBJID))`'
                )
            else:
                tip = ''
        else:
            if not self._showed_debug_tip:
                self._showed_debug_tip = True
                tip = (
                    '\nTo debug this,'
                    ' do `import gc; gc.set_debug(gc.DEBUG_LEAK)`'
                    ' or set env var BA_GC_DEBUG_LEAK=1.'
                )
            else:
                tip = ''

        garbagecollectionlog.log(
            loglevel,
            'Cyclic-garbage-collector handled %d objects in %.3fs'
            ' (total: %d).%s%s',
            num_affected_objs,
            duration,
            self._total_num_gc_objects,
            elimtip,
            tip,
        )
