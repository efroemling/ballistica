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
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efro.log import setup_logging, LogLevel

if TYPE_CHECKING:
    from efro.log import LogHandler

# Build number and version of the ballistica binary we expect to be
# using.
TARGET_BALLISTICA_BUILD = 21091
TARGET_BALLISTICA_VERSION = '1.7.20'

_g_env_config: EnvConfig | None = None
g_paths_set_failed = False  # pylint: disable=invalid-name
g_user_system_scripts_dir: str | None = None


@dataclass
class EnvConfig:
    """Final settings put together by the configure call."""

    config_dir: str
    data_dir: str
    user_python_dir: str | None
    app_python_dir: str | None
    standard_app_python_dir: str
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

    global _g_env_config  # pylint: disable=global-statement
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

    # By default, app-python-dir is simply ba_data/python under
    # data-dir.
    standard_app_python_dir = str(Path(data_dir, 'ba_data', 'python'))

    # If _babase has already been imported, there's not much we can do
    # at this point aside from complain and inform for next time.
    if '_babase' in sys.modules:
        app_python_dir = user_python_dir = site_python_dir = None

        # We don't actually complain yet here; we simply take note
        # that we weren't able to set paths. Then we complain if/when
        # the app is started. This way, non-app uses of babase won't be
        # filled with unnecessary warnings.
        global g_paths_set_failed  # pylint: disable=global-statement
        g_paths_set_failed = True

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
        # app_python_dir.
        check_dir = os.path.join(
            user_python_dir, 'sys', TARGET_BALLISTICA_VERSION
        )
        if os.path.isdir(check_dir):
            global g_user_system_scripts_dir  # pylint: disable=global-statement
            g_user_system_scripts_dir = check_dir
            app_python_dir = check_dir

        # Ok, now apply these to sys.path.

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
        standard_app_python_dir=standard_app_python_dir,
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
