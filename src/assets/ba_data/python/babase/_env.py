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

    # Turn off cyclic garbage-collection. We run it only at explicit
    # times to avoid random hitches and keep things more deterministic.
    # Non-reference-looped objects will still get cleaned up
    # immediately, so we should try to structure things to avoid and/or
    # break reference loops (just like Swift, ObjC, etc).

    # TODO: Should wire up some sort of callback for things that the
    # cyclic collector kills so we can try to get everything
    # deterministic and then there is no downside to running cyclic
    # collections very rarely. Could also just leave the cyclic
    # collector on in that case, but I wonder if there could be
    # overhead/hitches from it even if nothing gets collected.
    gc.disable()

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


def _pycache_cleanup_old_builds() -> None:
    """Blow away pyc dirs for old builds."""
    # pylint: disable=too-many-locals
    import shutil

    import _babase
    from babase._logging import applog

    # If pyc writing is disabled, doesn't make sense to do this.
    if sys.dont_write_bytecode:
        return

    # This is only really relevant for our builds where we're mucking
    # with pycache_prefix. If that not set, let's skip this (probably
    # wouldn't hurt to run anyway but whatevs).
    if sys.pycache_prefix is None:
        return

    # Per entry: is_us, modtime, path
    entries: list[tuple[bool, float, str]] = []

    env = _babase.app.env

    pycdir = os.path.join(env.cache_directory, 'pyc')
    fnames = os.listdir(pycdir)
    build_number_str = str(env.engine_build_number)
    for fname in fnames:
        fullpath = os.path.join(pycdir, fname)

        # Abort if the app is shutting down.
        appstate = _babase.app.state
        appstate_t = type(appstate)
        if (
            appstate is appstate_t.SHUTTING_DOWN
            or appstate is appstate_t.SHUTDOWN_COMPLETE
        ):
            break

        # If it doesn't look like a build-number dir, kill it immediately.
        if not fname.isdigit() or not os.path.isdir(fullpath):
            try:
                if os.path.isdir(fullpath):
                    shutil.rmtree(fullpath)
                else:
                    os.unlink(fullpath)
            except Exception as exc:
                applog.warning(
                    'Unable to prune unused cache dir "%s": %s',
                    fullpath,
                    exc,
                )
        else:
            entries.append(
                (
                    fname == build_number_str,
                    os.path.getmtime(fullpath),
                    fullpath,
                )
            )

    # Puts our cache at the top followed by newest modtime ones.
    entries.sort()

    # Now prune all but the top 3; that seems reasonable.
    for entry_is_us, _entry_mtime, entry_path in entries[:-1]:
        assert not entry_is_us
        try:
            shutil.rmtree(entry_path)
        except Exception as exc:
            applog.warning(
                'Unable to prune unused cache dir "%s": %s', entry_path, exc
            )


def _pycache_gen_pycs() -> None:
    """Take a quick pass at generating pycs for all .py files."""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    import py_compile
    import importlib.util

    import _babase
    from babase._logging import applog

    env = _babase.app.env

    # If pyc writing is disabled, doesn't make sense to do this.
    if sys.dont_write_bytecode:
        return

    # Also let's not do this if a pycacheprefix is not set; we'd likely
    # be doing a lot of failed writes in that case for read-only stdlib
    # module dirs.
    if sys.pycache_prefix is None:
        return

    # Now let's go through all of our scripts dirs and compile pycs for
    # for sources without one or newer than the existing one.
    #
    # For ordering, let's prioritize app scripts followed by mods and
    # finally stdlib. Stdlib might have the most stuff we don't use so
    # keeping them to the end could be good.
    #
    # We don't do anything fancy here; just create when one doesn't
    # exist. We don't bother with updating when sources change or
    # pruning orphaned pycs since build number bumps will cause us to
    # regen a whole new set which will cover most changes out in the
    # wild.

    # Note: originally I was using os.__file__ but it turns out that
    # module is 'frozen' in some cases and won't have a __file__. So we
    # need to pick something that is always bundled as a .py. Hopefully
    # py_compile fits the bill.
    stdlibpath = os.path.dirname(py_compile.__file__)

    dirpaths: list[str | None] = [
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
    complained = False
    for dirpath in dirpaths:
        if dirpath is None or not os.path.isdir(dirpath):
            continue
        for root, dnames, fnames in os.walk(dirpath):
            # Modify dirnames in-place to prevent walk from descending
            # into them.
            if dnames:
                dnames[:] = [d for d in dnames if d not in skip_dirs]
            for fname in fnames:

                # Abort if the app is shutting down (only check
                # this when we're doing actual writes; probably
                # not worth checking when just scanning modtimes).
                appstate = _babase.app.state
                appstate_t = type(appstate)
                if (
                    appstate is appstate_t.SHUTTING_DOWN
                    or appstate is appstate_t.SHUTDOWN_COMPLETE
                ):
                    return

                if not fname.endswith('.py'):
                    continue
                fullpath = os.path.join(root, fname)
                try:
                    pycpath = importlib.util.cache_from_source(fullpath)
                    if not os.path.exists(pycpath) or os.path.getmtime(
                        fullpath
                    ) > os.path.getmtime(pycpath):
                        py_compile.compile(fullpath, doraise=True)

                except Exception as exc:
                    # Make a bit of noise (once) for any other issues
                    # though.

                    # ..however first let's pause and see if it actually
                    # is updated first. There's a chance we could hit
                    # odd issues with trying to update a file that
                    # Python is already updating.
                    if not complained:
                        time.sleep(0.2)
                        still_out_of_date = not os.path.exists(
                            pycpath
                        ) or os.path.getmtime(fullpath) > os.path.getmtime(
                            pycpath
                        )
                        if still_out_of_date:
                            applog.warning(
                                'Error precompiling %s: %s', fullpath, exc
                            )
                            complained = True


def _pycache_upkeep() -> None:
    from babase._logging import applog

    starttime = time.monotonic()

    try:
        _pycache_cleanup_old_builds()
    except Exception:
        applog.exception('Error cleaning up old build pycaches')

    try:
        _pycache_gen_pycs()
    except Exception:
        applog.exception('Error bg generating pycs')

    duration = time.monotonic() - starttime
    applog.debug('Completed pycache upkeep in %.3fs.', duration)


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
