# Released under the MIT License. See LICENSE for details.
#
"""Bootstrapping."""
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from efro.log import setup_logging, LogLevel
import _ba

if TYPE_CHECKING:
    from typing import Any
    from efro.log import LogEntry

_g_did_bootstrap = False  # pylint: disable=invalid-name


def bootstrap() -> None:
    """Run bootstrapping logic.

    This is the very first ballistica code that runs (aside from imports).
    It sets up low level environment bits and creates the app instance.
    """

    global _g_did_bootstrap  # pylint: disable=global-statement, invalid-name
    if _g_did_bootstrap:
        raise RuntimeError('Bootstrap has already been called.')
    _g_did_bootstrap = True

    # The first thing we do is set up our logging system and feed
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

    log_handler.add_callback(_on_log)

    env = _ba.env()

    # Give a soft warning if we're being used with a different binary
    # version than we expect.
    expected_build = 20982
    running_build: int = env['build_number']
    if running_build != expected_build:
        print(
            f'WARNING: These script files are meant to be used with'
            f' Ballistica build {expected_build}.\n'
            f' You are running build {running_build}.'
            f' This might cause the app to error or misbehave.',
            file=sys.stderr,
        )

    # In bootstrap_monolithic.py we told Python not to handle SIGINT itself
    # (because that must be done in the main thread). Now we finish the
    # job by adding our own handler to replace it.

    # Note: I've found we need to set up our C signal handling AFTER
    # we've told Python to disable its own; otherwise (on Mac at least) it
    # wipes out our existing C handler.
    _ba.setup_sigint()

    # Sanity check: we should always be run in UTF-8 mode.
    if sys.flags.utf8_mode != 1:
        print(
            'ERROR: Python\'s UTF-8 mode is not set.'
            ' This will likely result in errors.',
            file=sys.stderr,
        )

    debug_build = env['debug_build']

    # We expect dev_mode on in debug builds and off otherwise.
    if debug_build != sys.flags.dev_mode:
        print(
            f'WARNING: Mismatch in debug_build {debug_build}'
            f' and sys.flags.dev_mode {sys.flags.dev_mode}',
            file=sys.stderr,
        )

    # In embedded situations (when we're providing our own Python) let's
    # also provide our own root certs so ssl works. We can consider overriding
    # this in particular embedded cases if we can verify that system certs
    # are working.
    # (We also allow forcing this via an env var if the user desires)
    if (
        _ba.contains_python_dist()
        or os.environ.get('BA_USE_BUNDLED_ROOT_CERTS') == '1'
    ):
        import certifi

        # Let both OpenSSL and requests (if present) know to use this.
        os.environ['SSL_CERT_FILE'] = os.environ[
            'REQUESTS_CA_BUNDLE'
        ] = certifi.where()

    # On Windows I'm seeing the following error creating asyncio loops in
    # background threads with the default proactor setup:
    # ValueError: set_wakeup_fd only works in main thread of the main
    #   interpreter
    # So let's explicitly request selector loops.
    # Interestingly this error only started showing up once I moved
    # Python init to the main thread; previously the various asyncio
    # bg thread loops were working fine (maybe something caused them
    # to default to selector in that case?..
    if sys.platform == 'win32':
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # pylint: disable=c-extension-no-member
    if not TYPE_CHECKING:
        import __main__

        # Clear out the standard quit/exit messages since they don't
        # work in our embedded situation (should revisit this once we're
        # usable from a standard interpreter).
        del __main__.__builtins__.quit
        del __main__.__builtins__.exit

        # Also replace standard interactive help with our simplified
        # one which is more friendly to cloud/in-game console situations.
        __main__.__builtins__.help = _CustomHelper()

    # Now spin up our App instance and store it on both _ba and ba.
    from ba._app import App
    import ba

    _ba.app = ba.app = App()
    _ba.app.log_handler = log_handler


class _CustomHelper:
    """Replacement 'help' that behaves better for our setup."""

    def __repr__(self) -> str:
        return 'Type help(object) for help about object.'

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        # We get an ugly error importing pydoc on our embedded
        # platforms due to _sysconfigdata_xxx.py not being present
        # (but then things mostly work). Let's get the ugly error out
        # of the way explicitly.
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


def _on_log(entry: LogEntry) -> None:

    # Just forward this along to the engine to display in the in-game console,
    # in the Android log, etc.
    _ba.display_log(
        name=entry.name,
        level=entry.level.name,
        message=entry.message,
    )

    # We also want to feed some logs to the old V1-cloud-log system.
    # Let's go with anything warning or higher as well as the stdout/stderr
    # log messages that ba.app.log_handler creates for us.
    if entry.level.value >= LogLevel.WARNING.value or entry.name in (
        'stdout',
        'stderr',
    ):
        _ba.v1_cloud_log(entry.message)
