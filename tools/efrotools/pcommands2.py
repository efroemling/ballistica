# Released under the MIT License. See LICENSE for details.
#
"""Standard snippets that can be pulled into project pcommand scripts.

A snippet is a mini-program that directly takes input from stdin and does
some focused task. This module is a repository of common snippets that can
be imported into projects' pcommand script for easy reuse.
"""

import sys
from typing import TYPE_CHECKING

from efrotools import pcommand

if TYPE_CHECKING:
    pass


def with_build_lock() -> None:
    """Run a shell command wrapped in a build-lock."""
    from efro.error import CleanError
    from efrotools.buildlock import BuildLock

    import subprocess

    args = sys.argv[2:]
    if len(args) < 2:
        raise CleanError(
            'Expected one lock-name arg and at least one command arg'
        )
    with BuildLock(args[0], projroot=str(pcommand.PROJROOT)):
        subprocess.run(' '.join(args[1:]), check=True, shell=True)


def sortlines() -> None:
    """Sort provided lines. For tidying import lists, etc."""
    from efro.error import CleanError

    if len(sys.argv) != 3:
        raise CleanError('Expected 1 arg.')
    val = sys.argv[2]
    lines = val.splitlines()
    print('\n'.join(sorted(lines, key=lambda l: l.lower())))


def openal_android_build() -> None:
    """Build openalsoft for android."""
    from efro.error import CleanError
    from efrotools.openalbuildandroid import build_openal

    args = sys.argv[2:]
    if len(args) != 2:
        raise CleanError(
            'Expected one <ARCH> arg: arm, arm64, x86, x86_64'
            ' and one <MODE> arg: debug, release'
        )

    build_openal(args[0], args[1])


def openal_apple_build() -> None:
    """Build OpenAL Soft xcframework + mac dylib for Apple platforms.

    Re-clones OpenAL Soft at the pinned tag and builds every slice (macOS /
    iOS / tvOS / visionOS, device + simulator) into build/openal-apple/
    artifacts. Follow with 'make openal-apple-gather' to install into the
    source tree.
    """
    import os

    from efrotools import openalbuildapple

    os.chdir(pcommand.PROJROOT)
    openalbuildapple.build(str(pcommand.PROJROOT))


def openal_apple_test_build() -> None:
    """Build the Apple OpenAL Soft artifacts, reusing an existing checkout.

    For CI / exercising the pipeline -- lazily reuses build/openal-apple/
    checkout (incremental). Follow with 'make openal-apple-gather'.
    """
    import os

    from efrotools import openalbuildapple

    os.chdir(pcommand.PROJROOT)
    openalbuildapple.test_build(str(pcommand.PROJROOT))


def openal_apple_gather() -> None:
    """Install assembled Apple OpenAL Soft artifacts into the source tree.

    Copies build/openal-apple/artifacts into src/external/openal-apple (the
    OpenALSoft.xcframework, the bare macOS dylib, and shared headers).
    """
    import os

    from efrotools import openalbuildapple

    os.chdir(pcommand.PROJROOT)
    openalbuildapple.gather(str(pcommand.PROJROOT))


def openal_android_gather() -> None:
    """Gather built opealsoft libs into src."""
    from efro.error import CleanError
    from efrotools.openalbuildandroid import gather

    args = sys.argv[2:]
    if args:
        raise CleanError('No args expected.')

    gather()


def pyright() -> None:
    """Run Pyright checks on project Python code."""
    import subprocess

    from efro.terminal import Clr

    from efro.error import CleanError

    print(f'{Clr.BLU}Running Pyright (experimental)...{Clr.RST}')
    try:
        subprocess.run(
            ['pyright', '--project', '.pyrightconfig.json'], check=True
        )
    except Exception as exc:
        raise CleanError('Pyright failed.') from exc


def build_pcommandbatch() -> None:
    """Build a version of pcommand geared for large batches of commands."""

    from efro.error import CleanError
    from efro.terminal import Clr

    import efrotools.pcommandbatch as pcb

    args = pcommand.get_args()
    if len(args) < 2:
        raise CleanError('Expected at least 2 args.')

    inpaths = args[:-1]
    outpath = args[-1]
    print(f'Creating batch executable: {Clr.BLD}{outpath}{Clr.RST}')
    pcb.build_pcommandbatch(inpaths, outpath)


def batchserver() -> None:
    """Run a server for handling pcommands."""
    from efro.error import CleanError
    from efro.util import extract_arg

    import efrotools.pcommandbatch as pcb

    args = pcommand.get_args()

    idle_timeout_secs = int(extract_arg(args, '--timeout', required=True))
    project_dir = extract_arg(args, '--project-dir', required=True)
    instance = extract_arg(args, '--instance', required=True)

    if args:
        raise CleanError(f'Unexpected args: {args}.')

    pcb.batchserver(
        idle_timeout_secs=idle_timeout_secs,
        project_dir=project_dir,
        instance=instance,
    )


def pcommandbatch_speed_test() -> None:
    """Test batch mode speeds."""

    import time
    import subprocess
    import threading
    from multiprocessing import cpu_count
    from concurrent.futures import ThreadPoolExecutor

    from efro.error import CleanError
    from efro.terminal import Clr

    args = pcommand.get_args()
    if len(args) != 1:
        raise CleanError('Expected one arg.')

    batch_binary_path = args[0]
    thread_count = cpu_count()

    class _Test:
        def __init__(self) -> None:
            self.in_flight = 0
            self.lock = threading.Lock()
            self.total_runs = 0

        def run_standalone(self) -> None:
            """Run an instance of the test in standalone mode."""
            subprocess.run(['tools/pcommand', 'null'], check=True)
            self._finish_run()

        def run_batch(self) -> None:
            """Run an instance of the test in batch mode."""
            subprocess.run([batch_binary_path, 'null'], check=True)
            self._finish_run()

        def _finish_run(self) -> None:
            with self.lock:
                self.in_flight -= 1
                assert self.in_flight >= 0
            self.total_runs += 1

    test_duration = 5.0
    for name, batch in [('regular pcommand', False), ('pcommandbatch', True)]:
        print(f'{Clr.BLU}Testing {name} speed...{Clr.RST}')
        start_time = time.monotonic()
        test = _Test()
        total_runs_at_timeout = 0
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            # Convert the generator to a list to trigger any
            # exceptions that occurred.
            while True:
                # Try to keep all worker threads busy.
                while test.in_flight < thread_count * 2:
                    with test.lock:
                        test.in_flight += 1
                    executor.submit(
                        test.run_batch if batch else test.run_standalone
                    )
                if time.monotonic() - start_time > test_duration:
                    total_runs_at_timeout = test.total_runs
                    break
                time.sleep(0.0001)
        print(
            f'Total runs in {test_duration:.0f} seconds:'
            f' {Clr.SMAG}{Clr.BLD}{total_runs_at_timeout}{Clr.RST}.'
        )


def null() -> None:
    """Do nothing. Useful for speed tests and whatnot."""
