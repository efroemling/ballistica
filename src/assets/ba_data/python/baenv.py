# Released under the MIT License. See LICENSE for details.
#
"""Manage ballistica execution environment.

This module is used to set up and/or check the global Python environment
before running a ballistica app. This includes things such as paths,
logging, debug-modes, garbage-collection settings, and signal handling.
Because these things are global in nature, this should be done before
any ballistica modules are imported.

Ballistica can be used without explicitly configuring the environment in
order to integrate it in arbitrary Python environments, but this may
cause some features to be disabled or behave differently than expected.
"""
from __future__ import annotations

import os
import sys
import signal
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efro.log import setup_logging, LogLevel

if TYPE_CHECKING:
    from typing import Any

    from efro.log import LogEntry, LogHandler

# Build number and version of the ballistica binary we expect to be
# using.
TARGET_BALLISTICA_BUILD = 21027
TARGET_BALLISTICA_VERSION = '1.7.20'

_g_env_config: EnvConfig | None = None
_g_babase_imported = False  # pylint: disable=invalid-name
_g_babase_app_started = False  # pylint: disable=invalid-name
_g_paths_set_failed = False  # pylint: disable=invalid-name


@dataclass
class EnvConfig:
    """Final settings put together by the configure call."""

    config_dir: str
    data_dir: str
    user_python_dir: str | None
    app_python_dir: str | None
    site_python_dir: str | None
    log_handler: LogHandler | None


def config_exists() -> bool:
    """Has a config been created?"""
    return _g_env_config is not None


def get_config() -> EnvConfig:
    """Return the active env-config. Creates default if none exists."""
    if _g_env_config is None:
        configure()
        assert _g_env_config is not None
    return _g_env_config


def configure(
    config_dir: str | None = None,
    data_dir: str | None = None,
    user_python_dir: str | None = None,
    app_python_dir: str | None = None,
    site_python_dir: str | None = None,
    contains_python_dist: bool = False,
) -> None:
    """Set up the Python environment for running a ballistica app.

    This includes things such as Python paths and log redirection. For
    that reason, this should be called before any other ballistica
    modules are imported, since it may make changes to sys.path,
    affecting where those modules get loaded from.
    """
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    global _g_env_config  # pylint: disable=global-statement, invalid-name
    if _g_env_config is not None:
        raise RuntimeError('An EnvConfig has already been created.')

    # The very first thing we do is set up our logging system and feed
    # Python's stdout/stderr into it. Then we can at least debug problems
    # on systems where native stdout/stderr is not easily accessible
    # such as Android.
    log_handler = setup_logging(
        log_path=None,
        level=LogLevel.DEBUG,
        suppress_non_root_debug=True,
        log_stdout_stderr=True,
        cache_size_limit=1024 * 1024,
    )

    # Sanity check: we should always be run in UTF-8 mode.
    if sys.flags.utf8_mode != 1:
        logging.warning(
            "Python's UTF-8 mode is not set. Running ballistica without"
            ' it may lead to errors.'
        )

    # Now do paths. We want to set stuff up so that engine modules,
    # mods, etc. are pulled from predictable places.
    cwd_path = Path.cwd()

    # A few paths we can ALWAYS calculate since they don't affect Python
    # imports:

    # Default data_dir assumes this module was imported from its
    # ba_data/python subdir.
    if data_dir is None:
        assert Path(__file__).parts[-3:-1] == ('ba_data', 'python')
        data_dir_path = Path(__file__).parents[2]
        # Prefer tidy relative paths like '.' if possible.
        data_dir = str(
            data_dir_path.relative_to(cwd_path)
            if data_dir_path.is_relative_to(cwd_path)
            else data_dir_path
        )

    # Default config-dir is simply ~/.ballisticakit
    if config_dir is None:
        config_dir = str(Path(Path.home(), '.ballisticakit'))

    # Ok now Python paths.

    # If _babase has already been imported, there's not much we can do
    # at this point aside from complain and inform for next time.
    if _g_babase_imported:
        app_python_dir = user_python_dir = site_python_dir = None

        # We don't actually complain yet here; we simply take note
        # that we weren't able to set paths. Then we complain if/when
        # the app is started. This way, non-app uses of babase won't be
        # filled with unnecessary warnings.
        global _g_paths_set_failed  # pylint: disable=global-statement
        _g_paths_set_failed = True

    else:
        # Ok; _babase hasn't been imported yet so we can muck with
        # Python paths.

        # By default, app-python-dir is simply ba_data/python under
        # data-dir.
        if app_python_dir is None:
            app_python_dir = str(Path(data_dir, 'ba_data', 'python'))

        # Likewise site-python-dir defaults to ba_data/python-site-packages.
        if site_python_dir is None:
            site_python_dir = str(
                Path(data_dir, 'ba_data', 'python-site-packages')
            )

        # By default, user-python-dir is simply 'mods' under config-dir.
        if user_python_dir is None:
            user_python_dir = str(Path(config_dir, 'mods'))

        # Ok, now add these to sys.path.

        # First off, strip out any instances of the path containing this
        # module. We will probably be re-adding the same path in a
        # moment but its technically possible that we won't be (if
        # app_python_dir is overridden to somewhere else, etc.)
        our_parent_path = Path(__file__).parent.resolve()
        paths: list[str] = [
            p for p in sys.path if Path(p).resolve() != our_parent_path
        ]
        # Let's lookup mods first (so users can do whatever they want).
        # and then our bundled scripts last (don't want bundled
        # site-package stuff overwriting system versions)
        paths.insert(0, user_python_dir)
        paths.append(app_python_dir)
        paths.append(site_python_dir)
        sys.path = paths

    # Attempt to create the dirs that we'll write stuff to. Not the end
    # of the world if we fail though.
    create_dirs: list[tuple[str, str | None]] = [
        ('config', config_dir),
        ('user_python', user_python_dir),
    ]
    for cdirname, cdir in create_dirs:
        if cdir is not None:
            try:
                os.makedirs(cdir, exist_ok=True)
            except Exception:
                logging.warning(
                    "Unable to create %s dir at '%s'.", cdirname, cdir
                )

    _g_env_config = EnvConfig(
        config_dir=config_dir,
        data_dir=data_dir,
        user_python_dir=user_python_dir,
        app_python_dir=app_python_dir,
        site_python_dir=site_python_dir,
        log_handler=log_handler,
    )

    # In embedded situations (when we're providing our own Python) let's
    # also provide our own root certs so ssl works. We can consider
    # overriding this in particular embedded cases if we can verify that
    # system certs are working. (We also allow forcing this via an env
    # var if the user desires)
    if (
        contains_python_dist
        or os.environ.get('BA_USE_BUNDLED_ROOT_CERTS') == '1'
    ):
        import certifi

        # Let both OpenSSL and requests (if present) know to use this.
        os.environ['SSL_CERT_FILE'] = os.environ[
            'REQUESTS_CA_BUNDLE'
        ] = certifi.where()


def on_babase_import() -> None:
    """Should be called just after _babase is imported.

    Sets up logging and issue warnings if anything in the running
    _babase environment seems wonky. Many significant environment
    modifications such as interrupt handling do not happen until
    on_babase_start_app(). This allows bits of _babase to be used under
    existing environments without messing things up too badly.
    """
    import _babase

    global _g_babase_imported  # pylint: disable=global-statement

    assert not _g_babase_imported
    _g_babase_imported = True

    # If we have a log_handler set up, wire it up to feed _babase its output.
    envconfig = get_config()
    if envconfig.log_handler is not None:
        _feed_logs_to_babase(envconfig.log_handler)

    env = _babase.pre_env()

    # Give a soft warning if we're being used with a different binary
    # version than we were built for.
    running_build: int = env['build_number']
    if running_build != TARGET_BALLISTICA_BUILD:
        logging.warning(
            'These scripts are meant to be used with'
            ' Ballistica build %d, but you are running build %d.'
            " This might cause problems. Module path: '%s'.",
            TARGET_BALLISTICA_BUILD,
            running_build,
            __file__,
        )

    debug_build = env['debug_build']

    # We expect dev_mode on in debug builds and off otherwise;
    # make noise if that's not the case.
    if debug_build != sys.flags.dev_mode:
        logging.warning(
            'Mismatch in ballistica debug_build %s'
            ' and sys.flags.dev_mode %s; this may cause problems.',
            debug_build,
            sys.flags.dev_mode,
        )


def on_babase_start_app() -> None:
    """Called when ballistica's babase module is spinning up an app."""
    import gc
    import _babase

    global _g_babase_app_started  # pylint: disable=global-statement

    _g_babase_app_started = True

    assert _g_babase_imported
    assert config_exists()

    # If we were unable to set paths earlier, complain now.
    if _g_paths_set_failed:
        logging.warning(
            'Ballistica Python paths have not been set. This may cause'
            ' problems. To ensure paths are set, run baenv.configure()'
            ' before importing any ballistica modules.'
        )

    # Set up interrupt-signal handling.

    # Note: I've found we need to set up our C signal handling AFTER
    # we've told Python to disable its own; otherwise (on Mac at least)
    # it wipes out our existing C handler.
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # Do default handling.
    _babase.setup_sigint()

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


class _CustomHelper:
    """Replacement 'help' that behaves better for our setup."""

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


def _feed_logs_to_babase(log_handler: LogHandler) -> None:
    """Route log/print output to internal ballistica console/etc."""
    import _babase

    def _on_log(entry: LogEntry) -> None:
        # Forward this along to the engine to display in the in-app
        # console, in the Android log, etc.
        _babase.display_log(
            name=entry.name,
            level=entry.level.name,
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

    # FIXME: while this works for now, the downside is that these
    #  callbacks fire in a bg thread so certain things like android
    #  logging will be delayed compared to code that uses native logging
    #  calls directly. Perhaps we should add some sort of 'immediate'
    #  callback option to better handle such cases (similar to the
    #  immediate echofile stderr print that already occurs).
    log_handler.add_callback(_on_log, feed_existing_logs=True)
