# Released under the MIT License. See LICENSE for details.
#
"""Environment related functionality."""
from __future__ import annotations

import sys
import signal
import logging
import warnings
from typing import TYPE_CHECKING, override

from efro.logging import LogLevel

if TYPE_CHECKING:
    from typing import Any
    from efro.logging import LogEntry, LogHandler

_g_babase_imported = False  # pylint: disable=invalid-name
_g_babase_app_started = False  # pylint: disable=invalid-name


def on_native_module_import() -> None:
    """Called when _babase is being imported.

    This code should do as little as possible; we want to defer all
    environment modifications until we actually commit to running an
    app.
    """
    import _babase
    import baenv

    global _g_babase_imported  # pylint: disable=global-statement

    assert not _g_babase_imported
    _g_babase_imported = True

    # If we have a log_handler set up, wire it up to feed _babase its
    # output.
    envconfig = baenv.get_config()
    if envconfig.log_handler is not None:
        _feed_logs_to_babase(envconfig.log_handler)

        # Also let's name the log-handler thread to help in profiling.
        envconfig.log_handler.call_in_thread(
            lambda: _babase.set_thread_name('ballistica logging')
        )

    env = _babase.pre_env()

    # Give a soft warning if we're being used with a different binary
    # version than we were built for.
    running_build: int = env['build_number']
    if running_build != baenv.TARGET_BALLISTICA_BUILD:
        logging.warning(
            'These scripts are meant to be used with'
            ' Ballistica build %d, but you are running build %d.'
            " This might cause problems. Module path: '%s'.",
            baenv.TARGET_BALLISTICA_BUILD,
            running_build,
            __file__,
        )

    debug_build = env['debug_build']

    # We expect dev_mode on in debug builds and off otherwise;
    # make noise if that's not the case.
    if debug_build != sys.flags.dev_mode:
        logging.warning(
            'Ballistica was built with debug-mode %s'
            ' but Python is running with dev-mode %s;'
            ' this mismatch may cause problems.'
            ' See https://docs.python.org/3/library/devmode.html',
            debug_build,
            sys.flags.dev_mode,
        )


def on_main_thread_start_app() -> None:
    """Called in the main thread when we're starting an app.

    We use this opportunity to set up the Python runtime environment
    as we like it for running our app stuff. This includes things like
    signal-handling, garbage-collection, and logging.
    """
    import gc
    import baenv
    import _babase

    global _g_babase_app_started  # pylint: disable=global-statement

    _g_babase_app_started = True

    assert _g_babase_imported
    assert baenv.config_exists()

    # If we were unable to set paths earlier, complain now.
    if baenv.did_paths_set_fail():
        logging.warning(
            'Ballistica Python paths have not been set. This may cause'
            ' problems. To ensure paths are set, run baenv.configure()'
            ' BEFORE importing any Ballistica modules.'
        )

    # Set up interrupt-signal handling.

    # Note: I've found we need to set up our C signal handling AFTER
    # we've told Python to disable its own; otherwise (on Mac at least)
    # it wipes out our existing C handler.
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # Do default handling.
    _babase.setup_sigint()

    # Turn on deprecation warnings. By default these are off for release
    # builds except for in __main__. However this is a key way to
    # communicate api changes to modders and most modders are running
    # release builds so its good to have this on everywhere.
    warnings.simplefilter('default', DeprecationWarning)

    # Turn off fancy-pants cyclic garbage-collection. We run it only at
    # explicit times to avoid random hitches and keep things more
    # deterministic. Non-reference-looped objects will still get cleaned
    # up immediately, so we should try to structure things to avoid
    # reference loops (just like Swift, ObjC, etc).

    # FIXME - move this to Python bootstrapping code. or perhaps disable
    #  it completely since we've got more bg stuff happening now?...
    #  (but put safeguards in place to time/minimize gc pauses).
    gc.disable()

    # pylint: disable=c-extension-no-member
    if not TYPE_CHECKING:
        import __main__

        # Clear out the standard quit/exit messages since they don't
        # work in our embedded situation (should revisit this once we're
        # usable from a standard interpreter). Note that these don't
        # exist in the first place for our monolithic builds which don't
        # use site.py.
        for attr in ('quit', 'exit'):
            if hasattr(__main__.__builtins__, attr):
                delattr(__main__.__builtins__, attr)

        # Also replace standard interactive help with our simplified
        # non-blocking one which is more friendly to cloud/in-app console
        # situations.
        __main__.__builtins__.help = _CustomHelper()

    # On Windows I'm seeing the following error creating asyncio loops
    # in background threads with the default proactor setup:

    # ValueError: set_wakeup_fd only works in main thread of the main
    # interpreter.

    # So let's explicitly request selector loops. Interestingly this
    # error only started showing up once I moved Python init to the main
    # thread; previously the various asyncio bg thread loops were
    # working fine (maybe something caused them to default to selector
    # in that case?..
    if sys.platform == 'win32':
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def on_app_state_initing() -> None:
    """Called when the app reaches the initing state."""
    import _babase
    import baenv

    assert _babase.in_logic_thread()

    # Let the user know if the app Python dir is a 'user' one. This is a
    # risky thing to be doing so don't let them forget they're doing it.
    envconfig = baenv.get_config()
    if envconfig.is_user_app_python_dir:
        _babase.screenmessage(
            f"Using user system scripts: '{envconfig.app_python_dir}'",
            color=(0.6, 0.6, 1.0),
        )


def _feed_logs_to_babase(log_handler: LogHandler) -> None:
    """Route log/print output to internal ballistica console/etc."""
    import _babase

    def _on_log(entry: LogEntry) -> None:
        # Forward this along to the engine to display in the in-app
        # console, in the Android log, etc.
        _babase.emit_log(
            name=entry.name,
            level=entry.level.name,
            timestamp=entry.time.timestamp(),
            message=entry.message,
        )

        # We also want to feed some logs to the old v1-cloud-log system.
        # Let's go with anything warning or higher as well as the
        # stdout/stderr log messages that babase.app.log_handler creates
        # for us. We should retire or upgrade this system at some point.
        if entry.level.value >= LogLevel.WARNING.value or entry.name in (
            'stdout',
            'stderr',
        ):
            _babase.v1_cloud_log(entry.message)

    # Add our callback and also feed it all entries already in the
    # cache. This will feed the engine any logs that happened between
    # baenv.configure() and now.

    # FIXME: while this setup works for now, the downside is that these
    #  callbacks fire in a bg thread so certain things like android
    #  logging will be delayed relative to code that uses native logging
    #  calls directly. Ideally we should add some sort of 'immediate'
    #  callback option to better handle such cases (analogous to the
    #  immediate echofile stderr print that LogHandler already
    #  supports).
    log_handler.add_callback(_on_log, feed_existing_logs=True)


class _CustomHelper:
    """Replacement 'help' that behaves better for our setup."""

    @override
    def __repr__(self) -> str:
        return 'Type help(object) for help about object.'

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        # We get an ugly error importing pydoc on our embedded platforms
        # due to _sysconfigdata_xxx.py not being present (but then
        # things mostly work). Let's get the ugly error out of the way
        # explicitly.

        # FIXME: we shouldn't be seeing this error anymore. Should
        #  revisit this.
        import sysconfig

        try:
            # This errors once but seems to run cleanly after, so let's
            # get the error out of the way.
            sysconfig.get_path('stdlib')
        except ModuleNotFoundError:
            pass

        import pydoc

        # Disable pager and interactive help since neither works well
        # with our funky multi-threaded setup or in-game/cloud consoles.
        # Let's just do simple text dumps.
        pydoc.pager = pydoc.plainpager
        if not args and not kwds:
            print(
                'Interactive help is not available in this environment.\n'
                'Type help(object) for help about object.'
            )
            return None
        return pydoc.help(*args, **kwds)
