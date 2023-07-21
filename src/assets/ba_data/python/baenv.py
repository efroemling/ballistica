# Released under the MIT License. See LICENSE for details.
#
"""Manage ballistica execution environment.

This module is used to set up and/or check the global Python environment
before running a ballistica app. This includes things such as paths,
logging, and app-dirs. Because these things are global in nature, this
should be done before any ballistica modules are imported.

This module can also be exec'ed directly to set up a default environment
and then run the app.

Ballistica can be used without explicitly configuring the environment in
order to integrate it in arbitrary Python environments, but this may
cause some features to be disabled or behave differently than expected.
"""
from __future__ import annotations

import os
import sys
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import TYPE_CHECKING
import __main__

from efro.log import setup_logging, LogLevel

if TYPE_CHECKING:
    from efro.log import LogHandler

# IMPORTANT - It is likely (and in some cases expected) that this
# module's code will be exec'ed multiple times. This is because it is
# the job of this module to set up paths for an engine run, and that may
# involve modifying sys.path in such a way that this module resolves to
# a different path afterwards (for example from
# /abs/path/to/ba_data/scripts/babase.py to ba_data/scripts/babase.py).
# This can result in the next import of baenv loading us from our 'new'
# location, which may or may not actually be the same file on disk as
# the old. Either way, however, multiple execs will happen in some form.
#
# So we need to do a few things to handle that situation gracefully.
#
# - First, we need to store any mutable global state in the __main__
#   module; not in ourself. This way, alternate versions of ourself will
#   still know if we already ran configure/etc.
#
# - Second, we should avoid the use of isinstance and similar calls for
#   our types. An EnvConfig we create would technically be a different
#   type than that created by an alternate baenv.

# Build number and version of the ballistica binary we expect to be
# using.
TARGET_BALLISTICA_BUILD = 21183
TARGET_BALLISTICA_VERSION = '1.7.24'


@dataclass
class EnvConfig:
    """Environment put together by the configure call."""

    config_dir: str
    data_dir: str
    user_python_dir: str | None
    app_python_dir: str | None
    standard_app_python_dir: str
    site_python_dir: str | None
    log_handler: LogHandler | None


@dataclass
class EnvGlobals:
    """Our globals we store in the main module."""

    config: EnvConfig | None = None
    config_called: bool = False
    paths_set_failed: bool = False
    user_system_scripts_dir: str | None = None

    @classmethod
    def get(cls) -> EnvGlobals:
        """Create/return our singleton."""
        name = '_baenv_globals'
        envglobals: EnvGlobals | None = getattr(__main__, name, None)
        if envglobals is None:
            envglobals = EnvGlobals()
            setattr(__main__, name, envglobals)
        return envglobals


def config_exists() -> bool:
    """Has a config been created?"""

    return EnvGlobals.get().config is not None


def did_paths_set_fail() -> bool:
    """Did we try to set paths and failed?"""
    return EnvGlobals.get().paths_set_failed


def get_user_system_scripts_dir() -> str | None:
    """If there's a custom user system scripts dir in play, return it."""
    return EnvGlobals.get().user_system_scripts_dir


def get_config() -> EnvConfig:
    """Return the active config, creating a default if none exists."""
    envglobals = EnvGlobals.get()

    if not envglobals.config_called:
        configure()

    config = envglobals.config
    if config is None:
        raise RuntimeError(
            'baenv.configure() has been called but no config exists;'
            ' perhaps it errored?'
        )
    return config


def configure(
    config_dir: str | None = None,
    data_dir: str | None = None,
    user_python_dir: str | None = None,
    app_python_dir: str | None = None,
    site_python_dir: str | None = None,
    contains_python_dist: bool = False,
) -> None:
    """Set up the Python environment for running a ballistica app.

    This includes things such as Python path wrangling and app directory
    creation. This should be called before any other ballistica modules
    are imported since it may make changes to sys.path which can affect
    where those modules get loaded from.
    """

    envglobals = EnvGlobals.get()

    if envglobals.config_called:
        raise RuntimeError(
            'baenv.configure() has already been called;'
            ' it can only be called once.'
        )
    envglobals.config_called = True

    # The very first thing we do is set up our logging system and pipe
    # Python's stdout/stderr into it. Then we can at least debug
    # problems on systems where native stdout/stderr is not easily
    # accessible such as Android.
    log_handler = _setup_logging()

    # We want to always be run in UTF-8 mode; complain if we're not.
    if sys.flags.utf8_mode != 1:
        logging.warning(
            "Python's UTF-8 mode is not set. Running ballistica without"
            ' it may lead to errors.'
        )

    # Attempt to set up Python paths and our own data paths so that
    # engine modules, mods, etc. are pulled from predictable places.
    (
        user_python_dir,
        app_python_dir,
        site_python_dir,
        data_dir,
        config_dir,
        standard_app_python_dir,
    ) = _setup_paths(
        user_python_dir,
        app_python_dir,
        site_python_dir,
        data_dir,
        config_dir,
    )

    # Attempt to create dirs that we'll write stuff to.
    _setup_dirs(config_dir, user_python_dir)

    # Get ssl working if needed so we can use https and all that.
    _setup_certs(contains_python_dist)

    # This is now the active config.
    envglobals.config = EnvConfig(
        config_dir=config_dir,
        data_dir=data_dir,
        user_python_dir=user_python_dir,
        app_python_dir=app_python_dir,
        standard_app_python_dir=standard_app_python_dir,
        site_python_dir=site_python_dir,
        log_handler=log_handler,
    )


def _calc_data_dir(data_dir: str | None) -> str:
    if data_dir is None:
        # To calc default data_dir, we assume this module was imported
        # from that dir's ba_data/python subdir.
        assert Path(__file__).parts[-3:-1] == ('ba_data', 'python')
        data_dir_path = Path(__file__).parents[2]

        # Prefer tidy relative paths like '.' if possible so that things
        # like stack traces are easier to read.

        # NOTE: Perhaps we should have an option to disable this
        # behavior for cases where the user might be doing chdir stuff.
        cwd_path = Path.cwd()
        data_dir = str(
            data_dir_path.relative_to(cwd_path)
            if data_dir_path.is_relative_to(cwd_path)
            else data_dir_path
        )
    return data_dir


def _setup_logging() -> LogHandler:
    log_handler = setup_logging(
        log_path=None,
        level=LogLevel.DEBUG,
        suppress_non_root_debug=True,
        log_stdout_stderr=True,
        cache_size_limit=1024 * 1024,
    )
    return log_handler


def _setup_certs(contains_python_dist: bool) -> None:
    # In situations where we're bringing our own Python let's also
    # provide our own root certs so ssl works. We can consider
    # overriding this in particular embedded cases if we can verify that
    # system certs are working. We also allow forcing this via an env
    # var if the user desires.
    if (
        contains_python_dist
        or os.environ.get('BA_USE_BUNDLED_ROOT_CERTS') == '1'
    ):
        import certifi

        # Let both OpenSSL and requests (if present) know to use this.
        os.environ['SSL_CERT_FILE'] = os.environ[
            'REQUESTS_CA_BUNDLE'
        ] = certifi.where()


def _setup_paths(
    user_python_dir: str | None,
    app_python_dir: str | None,
    site_python_dir: str | None,
    data_dir: str | None,
    config_dir: str | None,
) -> tuple[str | None, str | None, str | None, str, str, str]:
    # First a few paths we can ALWAYS calculate since they don't affect
    # Python imports:

    envglobals = EnvGlobals.get()

    data_dir = _calc_data_dir(data_dir)

    # Default config-dir is simply ~/.ballisticakit
    if config_dir is None:
        config_dir = str(Path(Path.home(), '.ballisticakit'))

    # Standard app-python-dir is simply ba_data/python under data-dir.
    standard_app_python_dir = str(Path(data_dir, 'ba_data', 'python'))

    # If _babase has already been imported, there's not much we can do
    # at this point aside from complain and inform for next time.
    if '_babase' in sys.modules:
        app_python_dir = user_python_dir = site_python_dir = None

        # We don't actually complain yet here; we simply take note that
        # we weren't able to set paths. Then we complain if/when the app
        # is started. This way, non-app uses of babase won't be filled
        # with unnecessary warnings.
        envglobals.paths_set_failed = True

    else:
        # Ok; _babase hasn't been imported yet so we can muck with
        # Python paths.

        if app_python_dir is None:
            app_python_dir = standard_app_python_dir

        # Likewise site-python-dir defaults to ba_data/python-site-packages.
        if site_python_dir is None:
            site_python_dir = str(
                Path(data_dir, 'ba_data', 'python-site-packages')
            )

        # By default, user-python-dir is simply 'mods' under config-dir.
        if user_python_dir is None:
            user_python_dir = str(Path(config_dir, 'mods'))

        # Wherever our user_python_dir is, if we find a sys/FOO dir
        # under it where FOO matches our version, use that as our
        # app_python_dir. This allows modding built-in stuff on
        # platforms where there is no write access to said built-in
        # stuff.
        check_dir = Path(user_python_dir, 'sys', TARGET_BALLISTICA_VERSION)
        if check_dir.is_dir():
            envglobals.user_system_scripts_dir = app_python_dir = str(check_dir)

        # Ok, now apply these to sys.path.

        # First off, strip out any instances of the path containing this
        # module. We will *probably* be re-adding the same path in a
        # moment so this keeps things cleaner. Though hmm should we
        # leave it in there in cases where we *don't* re-add the same
        # path?...
        our_parent_path = Path(__file__).parent.resolve()
        oldpaths: list[str] = [
            p for p in sys.path if Path(p).resolve() != our_parent_path
        ]

        # Let's place mods first (so users can override whatever they
        # want) followed by our app scripts and lastly our bundled site
        # stuff.

        # One could make the argument that at least our bundled app &
        # site stuff should be placed at the end so actual local site
        # stuff could override it. That could be a good thing or a bad
        # thing. Maybe we could add an option for that, but for now I'm
        # prioritizing our stuff to give as consistent an environment as
        # possible.
        ourpaths = [user_python_dir, app_python_dir, site_python_dir]

        # Special case: our modular builds will have a 'python-dylib'
        # dir alongside the 'python' scripts dir which contains our
        # binary Python modules. If we see that, add it to the path also.
        # Not sure if we'd ever have a need to customize this path.
        dylibdir = f'{app_python_dir}-dylib'
        if os.path.exists(dylibdir):
            ourpaths.append(dylibdir)

        sys.path = ourpaths + oldpaths

    return (
        user_python_dir,
        app_python_dir,
        site_python_dir,
        data_dir,
        config_dir,
        standard_app_python_dir,
    )


def _setup_dirs(config_dir: str | None, user_python_dir: str | None) -> None:
    create_dirs: list[tuple[str, str | None]] = [
        ('config', config_dir),
        ('user_python', user_python_dir),
    ]
    for cdirname, cdir in create_dirs:
        if cdir is not None:
            try:
                os.makedirs(cdir, exist_ok=True)
            except Exception:
                # Not the end of the world if we can't make these dirs.
                logging.warning(
                    "Unable to create %s dir at '%s'.", cdirname, cdir
                )


def _main() -> None:
    # Run a default configure BEFORE importing babase.
    # (may affect where babase comes from).
    configure()

    import babase

    babase.app.run()


# Allow exec'ing this module directly to do a standard app run.
if __name__ == '__main__':
    _main()
