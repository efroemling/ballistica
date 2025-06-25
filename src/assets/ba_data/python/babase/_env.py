# Released under the MIT License. See LICENSE for details.
#
"""Environment related functionality."""
from __future__ import annotations

import os
import sys
import time
import signal
import logging
import warnings
import threading
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
    envconfig = baenv.get_env_config()
    if envconfig.log_handler is not None:
        _feed_logs_to_babase(envconfig.log_handler)

        # Also let's name the log-handler thread to help in profiling.
        envconfig.log_handler.call_in_thread(
            lambda: _babase.set_thread_name('ballistica logging')
        )

    pre_env = _babase.pre_env()

    # Give a soft warning if we're being used with a different binary
    # version than we were built for.
    running_build: int = pre_env['build_number']
    assert isinstance(running_build, int)

    if running_build != baenv.TARGET_BALLISTICA_BUILD:
        logging.error(
            'These scripts are meant to be used with'
            ' Ballistica build %d, but you are running build %d.'
            " This is likely to cause problems. Module path: '%s'.",
            baenv.TARGET_BALLISTICA_BUILD,
            running_build,
            __file__,
        )

    debug_build = pre_env['debug_build']

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
    assert baenv.env_config_exists()

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

    # Set up our garbage collection stuff.
    _babase.app.gc.set_initial_mode()

    if os.environ.get('BA_GC_DEBUG_LEAK') == '1':
        print('ENABLING GC DEBUG LEAK CHECKS', file=sys.stderr)
        gc.set_debug(gc.DEBUG_LEAK)

    # pylint: disable=c-extension-no-member
    if not TYPE_CHECKING:
        import __main__

        # Clear out the standard quit/exit messages since they don't
        # work in our embedded situations and we wouldn't want to use them
        # if they did since Note that these don't
        # exist in the first place for our monolithic builds which don't
        # use site.py.
        for attr in ('quit', 'exit'):
            if hasattr(__main__.__builtins__, attr):
                delattr(__main__.__builtins__, attr)

        # Also replace standard interactive help with our simplified
        # non-blocking one which is more friendly to cloud/in-app console
        # situations.
        __main__.__builtins__.help = _CustomHelper()

    # UPDATE: As of May 2025 I'm no longer seeing the below issue, so
    # disabling this workaround for now and will remove it soon if no
    # issues arise.

    # On Windows I'm seeing the following error creating asyncio loops
    # in background threads with the default proactor setup:

    # ValueError: set_wakeup_fd only works in main thread of the main
    # interpreter.

    # So let's explicitly request selector loops. Interestingly this
    # error only started showing up once I moved Python init to the main
    # thread; previously the various asyncio bg thread loops were
    # working fine (maybe something caused them to default to selector
    # in that case?..
    if sys.platform == 'win32' and bool(False):
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Kick off some background cache cleanup operations.
    threading.Thread(target=_pycache_upkeep).start()


def _pycache_upkeep() -> None:
    from babase._logging import cachelog

    try:
        _do_pycache_upkeep()
    except Exception:
        cachelog.exception('Error in pycache upkeep.')


def _do_pycache_upkeep() -> None:
    """Take a quick pass at generating pycs for all .py files."""
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    import py_compile
    import importlib.util

    from efro.util import prune_empty_dirs

    import _babase
    from babase._logging import cachelog

    # Skip this all if bytecode writing is disabled.
    if sys.dont_write_bytecode:
        return

    def should_abort() -> bool:
        appstate = _babase.app.state
        appstate_t = type(appstate)
        return (
            appstate is appstate_t.SHUTTING_DOWN
            or appstate is appstate_t.SHUTDOWN_COMPLETE
        )

    # Let's wait until the app has been in the running state for a few
    # seconds before doing our thing; that way we're out of the way of
    # more high priority stuff like meta-scans that happen at first
    # launch.
    time_in_running_state = 0.0
    sleep_inc = 0.1
    while time_in_running_state < 3.0:
        time.sleep(sleep_inc)
        appstate = _babase.app.state
        appstate_t = type(appstate)
        if appstate is appstate_t.RUNNING:
            time_in_running_state += sleep_inc
        if should_abort():
            cachelog.debug('Aborting pycache update early due to app shutdown.')
            return

    cachelog.info('Running pycache upkeep...')

    # Measure time from when we actually start working.
    starttime = time.monotonic()

    env = _babase.app.env

    stdlibpath = os.path.dirname(py_compile.__file__)

    srcdirs: list[str | None] = [
        env.python_directory_app,
        env.python_directory_app_site,
        stdlibpath,
        env.python_directory_user,
    ]

    # Skip over particular dirnames; namely stuff in stdlib we're very
    # unlikely to ever use. This shaves off quite a bit of work.
    skip_dirs = {
        'test',
        'email',
        '__pycache__',
        'idlelib',
        'tkinter',
        'turtledemo',
        'unittest',
        'encodings',
    }

    # We do lots of stuff and if everything spits an error it's gonna
    # get messy, so let's only warn on the first thing that goes wrong
    # (the rest can be debug messages).
    complained = False

    def complain(msg: str) -> None:
        nonlocal complained
        if complained:
            cachelog.debug('(repeat) Error updating pycache dir: %s', msg)
            return
        cachelog.warning('Error updating pycache dir: %s', msg)

    # Build a dict of dst pyc paths mapped to src py paths and
    # src py modtimes.
    entries: dict[str, tuple[str, float]] = {}
    for srcdir in srcdirs:
        if srcdir is None or not os.path.isdir(srcdir):
            continue
        for dpath, dnames, fnames in os.walk(srcdir):
            # Modify dirnames in-place to prevent walk from descending
            # into them.
            dnames[:] = [d for d in dnames if d not in skip_dirs]
            for fname in fnames:
                if not fname.endswith('.py'):
                    continue
                srcpath = os.path.join(dpath, fname)
                dstpath = importlib.util.cache_from_source(srcpath)
                srcmodtime = os.path.getmtime(srcpath)
                entries[dstpath] = (srcpath, srcmodtime)

                if should_abort():
                    cachelog.debug(
                        'Aborting pycache update early due to app shutdown.'
                    )
                    return

    pycdir = os.path.join(env.cache_directory, 'pyc')

    # Sanity test: make sure these pyc paths appear to be under our
    # designated cache dir.
    for entry in entries:
        if not entry.startswith(pycdir):
            complain(
                f'pyc target {entry}'
                f' does not start with expected prefix {pycdir}.'
            )

        # Just check the first.
        break

    def _has_py_source(path: str) -> bool:
        """Does this .pyc path have an associated existing .py file?"""
        if not path.endswith('.pyc'):
            return False
        try:
            srcpath = importlib.util.source_from_cache(fullpath)
        except Exception as exc:
            # Have gotten reports of failures here on a file named
            # hook-mitmproxy.addons.onboardingapp.cpython-313.pyc'
            # (found in site-packages on a linux install).
            if 'expected only 2 or 3 dots' in str(exc):
                pass
            else:
                complain(f'Error looking for py src for "{path}": {exc}')

            # If anything goes wrong, just assume it *does* have a source;
            # let's only kill stuff when we're sure it doesn't.
            return True

        return os.path.exists(srcpath)

    def _is_older_than_a_few_seconds(path: str) -> bool:
        try:
            return os.path.getmtime(path) < time.time() - 10
        except FileNotFoundError:
            # Transient files such as in-progress pycache temp files are
            # likely to disappear under us. Just consider that as 'not
            # old'.
            return False

    # Now kill all files in our dst pyc dir that *don't* appear in our
    # dict of dst paths.
    for dpath, dnames, fnames in os.walk(pycdir):
        for fname in fnames:
            fullpath = os.path.join(dpath, fname)
            # We excluded skip_dirs when we generated entries, but its
            # still possible that stuff from those dirs has been cached
            # on-demand. So to be extra sure we can delete something we
            # make sure it isn't a .pyc file with an existing src .py
            # file. Technically we could check *everything* this way but
            # it should be lots faster to fast-out with the entries dict
            # lookup first.
            #
            # We also now check to make sure files are older than a few
            # seconds before deleting them; this keeps us out of the way
            # of in-progress .pyc temp files.

            if (
                fullpath not in entries
                and _is_older_than_a_few_seconds(fullpath)
                and not _has_py_source(fullpath)
            ):
                try:
                    cachelog.debug(
                        'pycache-upkeep: pruning file \'%s\'.', fullpath
                    )
                    os.unlink(fullpath)
                except Exception as exc:
                    complain(f'Failed to delete file "{fullpath}": {exc}')

    # Ok, we've killed all files that aren't valid cache files. Now
    # prune all empty dirs.
    try:
        prune_empty_dirs(pycdir)
    except Exception as exc:
        complain(str(exc))

    # Lastly, go through all src paths and compile all dst paths that
    # don't exist or are outdated.
    for dstpath, (srcpath, srcmtime) in entries.items():
        if not os.path.exists(dstpath) or srcmtime > os.path.getmtime(dstpath):
            try:
                cachelog.debug('pycache-upkeep: precompiling \'%s\'.', srcpath)
                py_compile.compile(srcpath, doraise=True)

                # Sleep a bit to limit speed to roughly 100/second max.
                # Hopefully that will reduce any stuttering effects from
                # this and it should still take only a few seconds on
                # fast hardware.
                time.sleep(0.01)

            except Exception as exc:
                # The first time a compile fails, let's pause and see if
                # it actually wound up updated first. There's a chance
                # we could hit the odd sporadic issue trying to update a
                # file that Python is already updating.
                if not complained:
                    time.sleep(0.2)
                    still_out_of_date = not os.path.exists(
                        dstpath
                    ) or srcmtime > os.path.getmtime(dstpath)
                    if still_out_of_date:
                        complain(f'Error precompiling {fullpath}: {exc}')
                        assert complained

            if should_abort():
                cachelog.debug(
                    'Aborting pycache update early due to app shutdown.'
                )
                return

    duration = time.monotonic() - starttime
    cachelog.info('Pycache upkeep completed in %.3fs.', duration)


def on_app_state_initing() -> None:
    """Called when the app reaches the initing state."""
    import _babase
    import baenv

    assert _babase.in_logic_thread()

    # Let the user know if the app Python dir is a 'user' one. This is a
    # risky thing to be doing so don't let them forget they're doing it.
    envconfig = baenv.get_env_config()
    if envconfig.is_user_app_python_dir:
        _babase.screenmessage(
            f"Using user system scripts: '{envconfig.app_python_dir}'",
            color=(0.6, 0.6, 1.0),
        )


def interpreter_shutdown_sanity_checks() -> None:
    """Run sanity checks just before finalizing after an app run."""
    import baenv
    from babase._logging import applog

    env_config = baenv.get_env_config()
    main_thread = threading.main_thread()

    # Warn about any still-running threads that we don't expect to find.
    warn_threads: list[threading.Thread] = []
    for thread in threading.enumerate():

        if thread is main_thread:
            continue

        # Our log-handler thread gets set up early and will get torn
        # down after us; we expect it to still be around.
        if (
            env_config.log_handler is not None
            and thread
            is env_config.log_handler._thread  # pylint: disable=W0212
        ):
            continue

        # Dummy threads are native threads that happen to have Python
        # stuff called in them. Ideally we should be using all Python
        # threads so should clear these out at some point. Just ignoring
        # them for now though.
        #
        if isinstance(thread, threading._DummyThread):  # pylint: disable=W0212
            continue

        warn_threads.append(thread)

    if warn_threads:
        applog.warning(
            '%s',
            '\n '.join(
                [
                    f'{len(warn_threads)}'
                    f' unexpected thread(s) still running at'
                    f' Python shutdown:'
                ]
                + [str(t) for t in warn_threads]
            )
            + '\nThreads should spin themselves down at app shutdown'
            ' (see App.add_shutdown_task()).',
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
