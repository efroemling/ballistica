# Released under the MIT License. See LICENSE for details.
#
"""Wrangles pcommandbatch; an efficient way to run small pcommands.

The whole purpose of pcommand is to be a lightweight way to run small
snippets of Python to do bits of work in a project. The pcommand script
tries to minimize imports and work done in order to keep runtime as
short as possible. However, even an 'empty' pcommand still takes a
fraction of a second due to the time needed to spin up Python and import
a minimal set of modules. This can add up for large builds where
hundreds or thousands of pcommands are being run.

To help fight that problem, pcommandbatch introduces a way to run
pcommands by submitting requests to temporary local server daemons.
This allows individual pcommand calls to go through a lightweight client
binary that simply forwards the command to a running server. This cuts
minimum pcommand runtimes down greatly. Building and managing the server
and client are handled automatically, and systems which are unable to
compile a client binary can fall back to using vanilla pcommand in those
cases.

A few considerations must be made when using pcommandbatch. By default,
all existing pcommands have been fitted with a disallow_in_batch() call
which triggers an error under batch mode. These calls should be removed
if/when each call is updated to work cleanly in batch mode. Guidelines
for batch-friendly pcommands follow:

- Batch mode runs parallel pcommands in different background threads
  and may process thousands of commands in a single process.
  Batch-friendly pcommands must behave reasonably in such an environment.

- Batch-enabled pcommands must not call os.chdir() or sys.exit() or
  anything else having global effects. This should be self-explanatory
  considering the shared server model in use.

- Batch-enabled pcommands must not use environment-variables to
  influence their behavior. In batch mode this would unintuitively use
  the environment of the server and not of the client.

- Batch-enabled pcommands should not look at sys.argv. They should
  instead use pcommand.get_args(). Be aware that this value does not
  include the first two values from sys.argv (executable path and
  pcommand name) so is generally cleaner to use anyway. Also be aware
  that args are thread-local, so only call get_args() from the thread
  your pcommand was called in.

- Batch-enabled pcommands should not use efro.terminal.Clr for coloring
  terminal output; instead they should use pcommand.clr() which properly
  takes into account whether the *client* is running on a tty/etc.

- Standard print and log calls (as well as those of child processes)
  will wind up in the pcommandbatch server log and will not be seen by
  the user or capturable by the calling process. For batch-friendly
  printing, use pcommand.clientprint(). Note that, in batch mode, all
  output will be printed on the client after the command completes and
  stderr and stdout will be printed separately instead of intermingled.
  If a pcommand is long-running and prints at multiple times while doing
  its thing, it is probably not a good fit for batch-mode.

"""
from __future__ import annotations

import os
import sys
import time
import json
import asyncio
import tempfile
import traceback
import subprocess
from typing import TYPE_CHECKING

import filelock
from efro.error import CleanError
from efro.terminal import Clr

if TYPE_CHECKING:
    pass

# Enable debug-mode, in which server commands are *not* spun off into
# daemons. This means some commands will block waiting for background
# servers they launched to exit, but it can make everything easier to
# debug as a whole since all client and server output will go a single
# terminal.
DEBUG = os.environ.get('BA_PCOMMANDBATCH_DEBUG', 0) == '1'

# Enable extra logging during server runs/etc. Debug mode implicitly
# enables this as well.
VERBOSE = DEBUG or os.environ.get('BA_PCOMMANDBATCH_VERBOSE', 0) == '1'


def build_pcommandbatch(inpaths: list[str], outpath: str) -> None:
    """Create the binary or link regular pcommand."""

    # Make an quiet attempt to build a batch binary, but just symlink
    # the plain old pcommand if anything goes wrong. That should work in
    # all cases; it'll just be slower.

    # Options to show build output or to fail if the build fails.
    verbose = os.environ.get('BA_PCOMMANDBATCH_BUILD_VERBOSE') == '1'
    require = os.environ.get('BA_PCOMMANDBATCH_BUILD_REQUIRE') == '1'

    try:
        if os.path.islink(outpath):
            os.unlink(outpath)

        os.makedirs(os.path.dirname(outpath), exist_ok=True)

        # Let compile output show if they want verbose OR if they're
        # requiring batch to succeed.
        subprocess.run(
            ['cc'] + inpaths + ['-o', outpath],
            check=True,
            capture_output=not (verbose or require),
        )
    except Exception as exc:
        if require:
            raise CleanError('pcommandbatch build failed.') from exc

        # No biggie; we'll just use regular pcommand.
        print(
            f'{Clr.YLW}Warning: Unable to build pcommandbatch executable;'
            f' falling back to regular pcommand. Build with env var'
            f' BA_PCOMMANDBATCH_BUILD_VERBOSE=1 to see what went wrong.'
            f'{Clr.RST}',
            file=sys.stderr,
        )
        subprocess.run(
            ['ln', '-sf', '../../tools/pcommand', outpath], check=True
        )


def batchserver(
    idle_timeout_secs: int, project_dir: str, instance: str
) -> None:
    """Run a server for handling batches of pcommands.

    If a matching instance is already running, is a no-op.
    """
    import daemon

    # Be aware that when running without daemons, various build commands
    # will block waiting for the server processes that they spawned to
    # exit. It can be worth it to debug things with everything spitting
    # output to the same terminal though.
    use_daemon = not DEBUG

    # Our stdout/stderr should already be directed to a file so we can
    # just keep the existing ones.
    server = Server(
        idle_timeout_secs=idle_timeout_secs,
        project_dir=project_dir,
        instance=instance,
        daemon=use_daemon,
    )

    if use_daemon:
        with daemon.DaemonContext(
            working_directory=os.getcwd(), stdout=sys.stdout, stderr=sys.stderr
        ):
            server.run()
    else:
        server.run()


class IdleError(RuntimeError):
    """Error we raise to quit peacefully."""


class Server:
    """A server that handles requests from pcommandbatch clients."""

    def __init__(
        self,
        idle_timeout_secs: int,
        project_dir: str,
        instance: str,
        daemon: bool,
    ) -> None:
        self._daemon = daemon
        self._project_dir = project_dir
        self._state_dir = f'{project_dir}/.cache/pcommandbatch'
        self._idle_timeout_secs = idle_timeout_secs
        self._worker_state_file_path = (
            f'{self._state_dir}/worker_state_{instance}'
        )
        self._worker_log_file_path = f'{self._state_dir}/worker_log_{instance}'
        self._client_count_since_last_check = 0
        self._running_client_count = 0
        self._port: int | None = None
        self._pid = os.getpid()
        self._next_request_id = 0
        self._instance = instance
        self._spinup_lock_path = f'{self._state_dir}/lock'
        self._spinup_lock = filelock.FileLock(self._spinup_lock_path)
        self._server_error: str | None = None

    def run(self) -> None:
        """Do the thing."""

        try:
            self._spinup_lock.acquire(timeout=10)
            if VERBOSE:
                print(
                    f'pcommandbatch server {self._instance}'
                    f' (pid {os.getpid()}) acquired spinup-lock'
                    f' at time {time.time():.3f}.',
                    file=sys.stderr,
                )

        except filelock.Timeout:
            # Attempt to error and inform clients if we weren't able to
            # acquire the file-lock. Unfortunately I can't really test this
            # case because file-lock releases itself in its destructor.
            if VERBOSE:
                print(
                    f'pcommandbatch server {self._instance}'
                    f' (pid {os.getpid()}) timed out acquiring spinup-lock'
                    f' at time {time.time():.3f}; this should not happen.',
                    file=sys.stderr,
                )

            self._server_error = (
                f'Error: pcommandbatch unable to acquire file-lock at'
                f' {self._spinup_lock_path}. Something is probably broken.'
            )

        # In daemon mode we get multiple processes dumping to the same
        # instance log file. We want to try and clear the log whenever a
        # new batch run starts so it doesn't grow infinitely. So let's
        # have any holder of the spinup lock (including aborted spinups)
        # truncate it if it appears to have been idle long enough to
        # have shut down.
        if self._daemon:
            try:
                existing_log_age = int(
                    time.time() - os.path.getmtime(self._worker_log_file_path)
                )
                if existing_log_age > self._idle_timeout_secs:
                    sys.stderr.truncate(0)
            except FileNotFoundError:
                pass

        # If there's an existing file younger than idle-seconds,
        # consider it still valid and abort our creation.
        try:
            existing_age = int(
                time.time() - os.path.getmtime(self._worker_state_file_path)
            )
            if existing_age <= self._idle_timeout_secs:
                if VERBOSE:
                    print(
                        f'pcommandbatch server {self._instance}'
                        f' (pid {os.getpid()}) found existing batch'
                        f' server (age {existing_age})'
                        f' at time {time.time():.3f};'
                        f' aborting run...',
                        file=sys.stderr,
                    )
                return
        except FileNotFoundError:
            # No state; no problem. Keep spinning up ours.
            if VERBOSE:
                print(
                    f'pcommandbatch server {self._instance}'
                    f' (pid {os.getpid()})'
                    f' found no existing batch server at time'
                    f' {time.time():.3f};'
                    f' proceeding with run...',
                    file=sys.stderr,
                )

        asyncio.run(self._run())

    async def _run(self) -> None:
        """Do the thing."""
        import efrotools.pcommand

        # Tell the running pcommand that we're the captain now.
        efrotools.pcommand.enter_batch_server_mode()

        server = await asyncio.start_server(self._handle_client, '127.0.0.1', 0)

        self._port = server.sockets[0].getsockname()[1]
        print(
            f'pcommandbatch server {self._instance} (pid {self._pid})'
            f' running on port {self._port} at time {time.time():.3f}...',
            file=sys.stderr,
        )

        # Write our first state and then unlock the spinup lock. New
        # spinup attempts will now see that we're here and back off.
        self._update_worker_state_file(-1)
        if self._spinup_lock.is_locked:
            self._spinup_lock.release()

        # Now run until our upkeep task kills us.
        try:
            await asyncio.gather(
                asyncio.create_task(
                    self._upkeep_task(), name='pcommandbatch upkeep'
                ),
                server.serve_forever(),
            )
        except IdleError:
            pass

        print(
            f'pcommandbatch server {self._instance} (pid {self._pid})'
            f' exiting at time {time.time():.3f}.',
            file=sys.stderr,
        )

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle a client."""
        import efro.terminal
        from efrotools.pcommand import run_client_pcommand

        request_id = self._next_request_id
        self._next_request_id += 1
        self._client_count_since_last_check += 1
        self._running_client_count += 1
        try:
            logpath = self._worker_log_file_path.removeprefix(
                f'{self._project_dir}/'
            )
            reqdata: dict = json.loads((await reader.read()).decode())
            assert isinstance(reqdata, dict)
            argv: list[str] = reqdata['a']
            assert isinstance(argv, list)
            assert all(isinstance(i, str) for i in argv)
            color_enabled: bool = reqdata['c']
            assert isinstance(color_enabled, bool)

            print(
                f'pcommandbatch server {self._instance} (pid {self._pid})'
                f' handling request {request_id} at time {time.time():.3f}:'
                f' {argv}.',
                file=sys.stderr,
            )

            # Note: currently just using the 'isatty' value from the
            # client. ideally should expand the client-side logic to
            # exactly match what efro.terminal.Clr does locally.
            clr: type[efro.terminal.ClrBase] = (
                efro.terminal.ClrAlways
                if color_enabled
                else efro.terminal.ClrNever
            )

            try:
                if self._server_error is not None:
                    resultcode = 1
                    stdout_output = ''
                    stderr_output = self._server_error
                else:
                    (
                        resultcode,
                        stdout_output,
                        stderr_output,
                    ) = await asyncio.get_running_loop().run_in_executor(
                        None,
                        lambda: run_client_pcommand(argv, clr, logpath),
                    )
                    if VERBOSE:
                        print(
                            f'pcommandbatch server {self._instance}'
                            f' (pid {self._pid})'
                            f' request {request_id} finished with code'
                            f' {resultcode}.',
                            file=sys.stderr,
                        )
            except Exception:
                print(
                    f'pcommandbatch server {self._instance}'
                    f' (pid {self._pid}):'
                    f' error on request {request_id}:',
                    file=sys.stderr,
                )
                traceback.print_exc()
                stdout_output = ''
                stderr_output = (
                    f"internal pcommandbatch error; see log at '{logpath}'."
                )
                resultcode = 1

            writer.write(
                json.dumps(
                    {'r': resultcode, 'o': stdout_output, 'e': stderr_output}
                ).encode()
            )
            writer.close()
            await writer.wait_closed()

        finally:
            self._running_client_count -= 1
            assert self._running_client_count >= 0

    async def _upkeep_task(self) -> None:
        """Handle timeouts, updating port file timestamp, etc."""

        start_time = time.monotonic()

        idle_secs = 0
        idle_buffer = 5

        while True:
            await asyncio.sleep(1.0)
            now = time.monotonic()
            since_start = now - start_time

            # Whenever we've run client(s) within the last second, we
            # reset our idle time and freshen our state file so clients
            # know they can still use us.

            # Consider ourself idle if there are no currently running
            # jobs AND nothing has been run since our last check. This
            # covers both long running jobs and super short ones that
            # would otherwise slip between our discrete checks.
            if (
                self._client_count_since_last_check
                or self._running_client_count
            ):
                idle_secs = 0
                self._update_worker_state_file(idle_secs)
            else:
                idle_secs += 1
                if VERBOSE:
                    print(
                        f'pcommandbatch server {self._instance}'
                        f' (pid {self._pid})'
                        f' idle {idle_secs}/'
                        f'{self._idle_timeout_secs + idle_buffer} seconds at'
                        f' time {int(time.time())}.',
                        file=sys.stderr,
                    )

            self._client_count_since_last_check = 0

            # Clients should stop trying to contact us when our state
            # file hits idle_timeout_secs in age, but we actually stay
            # alive for a few extra seconds extra just to make sure we
            # don't spin down right as someone is trying to use us.
            if idle_secs >= self._idle_timeout_secs + idle_buffer:
                # This insta-kills our server so it should never be
                # happening while something is running.
                if self._running_client_count:
                    raise CleanError(
                        f'pcommandbatch server {self._instance}'
                        f' (pid {self._pid}):'
                        f' idle-exiting but have running_client_count'
                        f' {self._running_client_count}; something'
                        f' is probably broken.'
                    )
                raise IdleError()

            # No longer limiting command duration; seems like that's not
            # gonna do anything helpful at this point aside from break legit
            # long commands.
            abs_timeout_secs = 60 * 5
            if since_start > abs_timeout_secs and bool(False):
                raise CleanError(
                    f'pcommandbatch server {self._instance}'
                    f' (pid {self._pid}): max'
                    f' run-time of {abs_timeout_secs}s reached.'
                    ' Something is probably broken.'
                )

    def _update_worker_state_file(self, idle_secs: int) -> None:
        assert self._port is not None
        # Dump our port to a temp file and move it into place.
        # Hopefully this will be nice and atomic.
        if VERBOSE:
            print(
                f'pcommandbatch server {self._instance} (pid {self._pid})'
                f' refreshing state file {self._worker_state_file_path}'
                f' with port {self._port} and idle-secs {idle_secs}'
                f' at time {time.time():.3f}.',
                file=sys.stderr,
            )

        with tempfile.TemporaryDirectory() as tempdir:
            outpath = os.path.join(tempdir, 'f')
            with open(outpath, 'w', encoding='utf-8') as outfile:
                outfile.write(json.dumps({'p': self._port}))
            subprocess.run(
                ['mv', outpath, self._worker_state_file_path], check=True
            )
