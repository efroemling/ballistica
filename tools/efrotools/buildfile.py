# Released under the MIT License. See LICENSE for details.
#
"""Generate Jenkins 'build-files': scheduled lists of shell commands.

A build-file is simply a newline-delimited list of shell commands that a
Jenkins stage runs one per line (``readFile(...).split("\\n")`` then a
``sh`` per entry). This module provides the shared machinery for emitting
such files where individual commands run only on an interval (every Nth
day) so expensive or rarely-needed work can be spread out instead of run
every nightly pass.

The key property — borrowed from efrohome's machine-upkeep generator — is
that *every* command is emitted on *every* run: a command that is not due
today is emitted as an ``echo "skipping action ..."`` line instead of
being silently omitted. That keeps each run's log a full inventory of the
configured work, showing at a glance what ran, what was skipped, and how
many days remain until each skipped item is next due.

Selection is purely date-deterministic (days since the Unix epoch modulo
the command's interval); there is no persistent 'last run' state. A
missed nightly run simply means a command waits until its next due day.
"""

from datetime import datetime, date, timezone
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class ScheduledCommand:
    """A single command in a scheduled build-file.

    The command is emitted verbatim on days when it is due (that is, when
    ``days_since_epoch() % interval == phase``) and as a 'skipping' echo
    line on all other days.
    """

    #: The shell line emitted when the command is due. The caller is
    #: responsible for it being a valid standalone shell line (quoting,
    #: wrappers, etc.) exactly as it would appear in the build-file.
    command: str

    #: Run cadence in days. ``1`` (the default) runs every pass; ``7``
    #: runs roughly once a week, etc. Must be >= 1.
    interval: int = 1

    #: Human-readable description used in the 'skipping' echo line. When
    #: empty, ``command`` is used. Useful when ``command`` is a long
    #: wrapped invocation but the skip line should show something terse.
    label: str = ''

    #: Offset within the interval cycle on which the command is due, i.e.
    #: it runs when ``days_since_epoch() % interval == phase``. Defaults
    #: to ``0``. Use distinct phases to spread several same-interval
    #: commands across different days so per-run cost stays bounded (e.g.
    #: ten ``interval=14`` builds with phases 0..9 each run once per
    #: fortnight, never all on the same night). Must satisfy
    #: ``0 <= phase < interval``.
    phase: int = 0


def days_since_epoch() -> int:
    """Return the number of whole days since the Unix epoch (UTC).

    This is the date counter used for interval scheduling. Using
    days-since-epoch (rather than day-of-year) means cadences never
    hiccup at year boundaries.
    """
    return (datetime.now(timezone.utc).date() - date(1970, 1, 1)).days


def schedule_dayindex(interval: int, *, day: int | None = None) -> int:
    """Return the position of ``day`` within a command's interval cycle.

    A result of ``0`` means the command is due; any other value is the
    number of days into the cycle (and ``interval - value`` days remain
    until next due). ``day`` defaults to :func:`days_since_epoch`.
    """
    if interval < 1:
        raise ValueError(f'interval must be >= 1; got {interval}.')
    if day is None:
        day = days_since_epoch()
    return day % interval


def gen_buildfile_lines(
    commands: Sequence[ScheduledCommand], *, day: int | None = None
) -> list[str]:
    """Return build-file lines for ``commands`` for the given day.

    Due commands contribute their ``command`` verbatim; not-due commands
    contribute a ``skipping action`` echo naming their cadence position.
    ``day`` defaults to :func:`days_since_epoch` (computed once so the
    whole file reflects a single day).
    """
    if day is None:
        day = days_since_epoch()

    lines: list[str] = []
    for cmd in commands:
        if not 0 <= cmd.phase < cmd.interval:
            raise ValueError(
                f'phase must satisfy 0 <= phase < interval;'
                f' got phase={cmd.phase}, interval={cmd.interval}.'
            )
        dayindex = schedule_dayindex(cmd.interval, day=day)
        if dayindex != cmd.phase:
            desc = (cmd.label or cmd.command).replace('"', "'")
            lines.append(
                f'echo "skipping action '
                f'(dayindex {dayindex}/{cmd.interval}): {desc}"'
            )
        else:
            lines.append(cmd.command)
    return lines


def write_buildfile(
    path: str,
    commands: Sequence[ScheduledCommand],
    *,
    day: int | None = None,
    empty_message: str = 'No actions for this target. Nothing to see here.',
) -> None:
    """Write a scheduled build-file to ``path``.

    When ``commands`` is empty, a single ``echo`` of ``empty_message`` is
    written instead so the consuming Jenkins stage always has a valid
    line to run rather than an empty (and thus malformed) ``sh`` step.
    """
    lines = gen_buildfile_lines(commands, day=day)
    if not lines:
        lines = [f'echo "{empty_message}"']
    with open(path, 'w', encoding='utf-8') as outfile:
        outfile.write('\n'.join(lines))
