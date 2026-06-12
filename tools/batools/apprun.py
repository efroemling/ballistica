# Released under the MIT License. See LICENSE for details.
#
"""Utils for wrangling running the app as part of a build.

Manages constructing or downloading it as well as running it.
"""

from typing import TYPE_CHECKING
import os
import platform
import re
import signal
import subprocess
import threading

from efro.terminal import Clr

if TYPE_CHECKING:
    from typing import Mapping


def test_runs_disabled() -> bool:
    """Are test runs disabled on the current platform?"""

    # Currently skipping this on Windows, as we aren't able to assemble
    # complete build there without WSL.
    if platform.system() == 'Windows':
        return True

    return False


def test_runs_disabled_reason() -> str:
    """Why are test runs disabled here?"""
    # Can get more specific later.
    return 'App test runs disabled here.'


def python_command(
    cmd: str,
    purpose: str,
    include_project_tools: bool = False,
    env: Mapping[str, str] | None = None,
) -> None:
    """Run a cmd with a built bin and PYTHONPATH set to its scripts."""

    binpath = acquire_binary(purpose=purpose)
    bindir = os.path.dirname(binpath)

    # We'll set both the app python dir and its site-python-dir. This
    # should let us get at most engine stuff. We could also just use
    # baenv to set up app paths, but that might be overkill and could
    # unintentionally bring in stuff like local mods.
    pydir = f'{bindir}/ba_data/python'
    assert os.path.isdir(pydir)
    pysitedir = f'{bindir}/ba_data/python-site-packages'
    assert os.path.isdir(pysitedir)

    # Make our tools dir available if asked.
    tools_path_extra = ':tools' if include_project_tools else ''

    env_final = {} if env is None else dict(env)
    env_final['PYTHONPATH'] = f'{pydir}:{pysitedir}{tools_path_extra}'

    cmdargs = [binpath, '--command', cmd]
    print(f"apprun: Running with Python command: '{cmdargs}'...", flush=True)
    subprocess.run(cmdargs, env=env_final, check=True)


def acquire_binary(purpose: str, *, gui: bool = False) -> str:
    """Return path to a runnable binary, building/downloading as needed.

    By default this provides a headless-server binary along with the
    full server asset bundle (Python scripts + fonts + data, but no
    audio/textures/meshes). That is enough for the binary to fully boot
    and is the right choice for the vast majority of tool/test
    workflows (dummy-module generation, import tests, transport tests,
    etc.).

    Pass ``gui=True`` when the caller genuinely needs a GUI binary and
    the full (including media) asset bundle — e.g. a test that
    exercises rendering. This only works in environments that have the
    full asset source tree available; environments like ba-check that
    strip audio/textures/meshes will fail the asset build in this mode.

    By default the binary is built locally so the caller's working-tree
    edits are reflected in the run. Set ``BA_APP_RUN_USE_PREFAB=1`` to
    use a prefab binary instead — useful for environments without a
    full compiler toolchain (public-repo CI, casual contributors). In
    repos that publish prefabs via efrocache (spinoff/public) the
    prefab path is a download; in ballistica-internal it falls back to
    a remote cmake build via cloudshell.
    """
    binary_build_command: list[str]
    if os.environ.get('BA_APP_RUN_USE_PREFAB') == '1':
        # Going the prefab route.

        # Prefab build targets on WSL (Linux running on Windows) will
        # give us Windows builds which won't work right here. Ask it
        # for Linux builds instead.
        env = dict(os.environ, BA_WSL_TARGETS_WINDOWS='0')

        kind = 'gui' if gui else 'headless'
        if gui:
            binary_build_command = ['make', 'prefab-gui-release-build']
            prefab_target = 'gui-release'
        else:
            binary_build_command = ['make', 'prefab-server-release-build']
            prefab_target = 'server-release'
        binary_path = (
            subprocess.run(
                ['tools/pcommand', 'prefab_binary_path', prefab_target],
                env=env,
                check=True,
                capture_output=True,
            )
            .stdout.decode()
            .strip()
        )

        # The prefab make rule is annotated with __EFROCACHE_TARGET__
        # so repos that publish prefab artifacts (spinoffs, public)
        # rewrite it to fetch from efrocache; repos without an
        # .efrocachemap (ballistica-internal) build from source
        # instead. Word the message based on which path will run.
        will_fetch = False
        if os.path.exists('.efrocachemap'):
            try:
                import json

                with open('.efrocachemap', encoding='utf-8') as efh:
                    will_fetch = binary_path in json.load(efh)
            except (OSError, ValueError):
                pass

        if will_fetch:
            print(
                f'{Clr.SMAG}Fetching prefab {kind} binary & assets for'
                f' {purpose}...{Clr.RST}',
                flush=True,
            )
        else:
            print(
                f'{Clr.SMAG}Building {kind} binary & assets for'
                f' {purpose} (via prefab path)...{Clr.RST}',
                flush=True,
            )
    else:
        # Going the build-it-ourselves route (the default).

        if gui:
            print(
                f'{Clr.SMAG}Building gui binary & assets for'
                f' {purpose}...{Clr.RST}',
                flush=True,
            )
            binary_build_command = ['make', 'cmake-build']
            binary_path = 'build/cmake/debug/staged/ballisticakit'
        else:
            print(
                f'{Clr.SMAG}Building headless binary & assets for'
                f' {purpose}...{Clr.RST}',
                flush=True,
            )
            binary_build_command = ['make', 'cmake-server-build']
            binary_path = (
                'build/cmake/server-debug/staged/dist/ballisticakit_headless'
            )
        env = None

    subprocess.run(binary_build_command, env=env, check=True)
    if not os.path.exists(binary_path):
        raise RuntimeError(
            f"Binary not found at expected path '{binary_path}'."
        )
    return binary_path


def run_headless_capture(
    *,
    purpose: str,
    config_dir: str | None = None,
    exec_code: str | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float = 30.0,
    udp_listener: bool = False,
    stop_pattern: str | re.Pattern[str] | None = None,
    sigterm_grace: float = 5.0,
) -> subprocess.CompletedProcess[bytes]:
    """Boot the headless engine, capture stdout+stderr, and return.

    Designed for capture-style tests that boot the client, observe a
    bit of behavior in the logs, and quit. Like ``python_command``,
    this goes through ``acquire_binary``, so build-vs-prefab is
    controlled by ``BA_APP_RUN_USE_PREFAB=1`` (default: build).

    By default ``BA_NO_UDP_LISTENER=1`` is exported so the binary
    never opens a UDP socket. That sidesteps Claude Code's sandbox
    (which blocks ``0.0.0.0`` binds) and avoids port conflicts on
    shared CI hosts. Pass ``udp_listener=True`` if a test genuinely
    needs the listener.

    If ``stop_pattern`` (str or compiled regex) is given, output is
    streamed and the process is sent SIGTERM as soon as a line
    matches — much faster than waiting for an apptimer to call
    ``_babase.quit``. Without it, the binary runs until it exits on
    its own or ``timeout`` elapses.

    Stdout and stderr are merged. Returns a CompletedProcess with
    bytes ``stdout``; callers decode as needed. Never raises on
    timeout — callers assert on the captured output instead.
    """
    binpath = os.path.abspath(acquire_binary(purpose=purpose))
    bindir = os.path.dirname(binpath)

    env_final = dict(os.environ)
    if env is not None:
        env_final.update(env)
    if not udp_listener:
        env_final.setdefault('BA_NO_UDP_LISTENER', '1')

    cmd = [binpath]
    if config_dir is not None:
        cmd += ['--config-dir', config_dir]
    if exec_code is not None:
        cmd += ['--exec', exec_code]

    pattern: re.Pattern[str] | None
    if isinstance(stop_pattern, str):
        pattern = re.compile(stop_pattern)
    else:
        pattern = stop_pattern

    captured: list[bytes] = []

    with subprocess.Popen(
        cmd,
        cwd=bindir,
        env=env_final,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ) as proc:
        assert proc.stdout is not None
        stream = proc.stdout

        if pattern is None:
            try:
                out_bytes, _ = proc.communicate(timeout=timeout)
                captured.append(out_bytes)
            except subprocess.TimeoutExpired:
                proc.send_signal(signal.SIGTERM)
                try:
                    out_bytes, _ = proc.communicate(timeout=sigterm_grace)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    out_bytes, _ = proc.communicate()
                captured.append(out_bytes)
        else:
            matcher = pattern

            def reader() -> None:
                for raw in iter(stream.readline, b''):
                    captured.append(raw)
                    if matcher.search(raw.decode(errors='replace')):
                        return

            thread = threading.Thread(target=reader, daemon=True)
            thread.start()
            thread.join(timeout=timeout)
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(timeout=sigterm_grace)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            thread.join(timeout=2.0)

        returncode = proc.returncode

    return subprocess.CompletedProcess(
        args=cmd,
        returncode=returncode,
        stdout=b''.join(captured),
        stderr=None,
    )
