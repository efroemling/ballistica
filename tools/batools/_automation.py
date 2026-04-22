# Released under the MIT License. See LICENSE for details.
"""Pcommand entry points for the opt-in automation control channel.

.. warning::

   **Unstable, unsupported.** Part of the automation control channel,
   which is an opt-in dev tool with no backward-compatibility
   guarantees. May change or be removed without notice.

Companion to ``src/ballistica/base/automation/`` and
``babase._automation``: this module provides the ``test_game_cmd``
pcommand, which writes a single line of Python to a running game's
``<silo>/cmd.fifo`` for execution on its logic thread.

This is the external (driver) side of the automation channel; the
in-process side lives under ``src/ballistica/base/automation/``. The
subsystem is gated at compile time on ``BA_ENABLE_AUTOMATION`` (set
via CMake ``-DENABLE_AUTOMATION=ON``) and at runtime on
``BA_AUTOMATION_FIFO`` being set. Both sides are intentionally
siloed from the rest of the codebase — if something here needs to
change, the only other file you should need to look at is the C++
``Automation`` class.
"""

from __future__ import annotations

import os
import sys

# Mirrors batools.pcommands3 — silos live under build/test_run/<name>.
_TEST_RUN_ROOT = os.path.join('build', 'test_run')


def test_game_cmd() -> None:
    """Send a Python line to a running test_game_run instance.

    Usage:

        tools/pcommand test_game_cmd [INSTANCE] PYTHON

    Defaults INSTANCE to ``default`` when omitted (only one positional
    arg given). The given Python string is written to that silo's
    ``cmd.fifo``, which the in-process automation reader thread picks
    up and ``exec``'s on the logic thread.

    The game must have been started by ``test_game_run`` (which is
    what creates the silo and points the binary at the FIFO via the
    ``BA_AUTOMATION_FIFO`` env var). Sending to a silo whose game has
    exited will block in the ``open`` call until either someone reads
    the fifo or the writer is killed — this is normal POSIX FIFO
    behavior, not a bug.
    """
    args = sys.argv[2:]
    if len(args) == 1:
        instance = 'default'
        python_line = args[0]
    elif len(args) == 2:
        instance, python_line = args
    else:
        print(test_game_cmd.__doc__, file=sys.stderr)
        sys.exit(2)

    silo = os.path.join(_TEST_RUN_ROOT, instance)
    fifo = os.path.join(silo, 'cmd.fifo')

    if not os.path.exists(silo):
        print(
            f'No silo dir at {silo!r}; '
            f'is the instance running? '
            f'(start it via tools/pcommand test_game_run [--instance NAME])',
            file=sys.stderr,
        )
        sys.exit(1)

    if not os.path.exists(fifo):
        print(
            f'No FIFO at {fifo!r}; '
            f'is the game still booting, or was it built without '
            f'BA_ENABLE_AUTOMATION?',
            file=sys.stderr,
        )
        sys.exit(1)

    # The in-process reader splits on '\n' and treats each line as
    # one Python command — so multi-line scripts need their newlines
    # encoded on the wire. We escape backslashes first (so '\n'
    # literals in the source round-trip correctly) and then literal
    # newlines as \n. The C++ reader does the inverse before exec.
    encoded = python_line.replace('\\', '\\\\').replace('\n', '\\n')

    # Append a single wire-level newline as the command terminator.
    encoded += '\n'

    # Open in append mode rather than write mode to avoid blocking on
    # FIFO open when no one is currently reading. (POSIX: opening a
    # FIFO for write-only blocks until a reader appears.) Append-mode
    # opens the existing fd more permissively across platforms.
    with open(fifo, 'a', encoding='utf-8') as f:
        f.write(encoded)
