# Released under the MIT License. See LICENSE for details.
#
"""A nice collection of ready-to-use pcommands for this package."""

# Note: import as little as possible here at the module level to
# keep launch times fast for small snippets.
from efrotools import pcommand


def ios_sim_run() -> None:
    """Build an iOS/tvOS scheme for the simulator and run it there.

    Usage: ``tools/pcommand ios_sim_run <project> <scheme> <config>
    <ios|tvos>``. Honors the ``IOS_SIM_DEVICE`` (name/udid; default auto-picks
    the newest available) and ``IOS_LOG_SUBSYSTEM`` env vars. Powers
    ``make ios`` / ``make tvos`` -- the Simulator analogue of ``make mac``.
    """
    from efro.error import CleanError
    from batools import iossim

    args = pcommand.get_args()
    if len(args) != 4:
        raise CleanError('Expected <project> <scheme> <config> <ios|tvos>.')
    iossim.run(
        project=args[0],
        scheme=args[1],
        configuration=args[2],
        platform=args[3],
    )


def ios_sim_log() -> None:
    """Stream engine os_log from the booted iOS/tvOS sim.

    Usage: ``tools/pcommand ios_sim_log [device-udid]`` (default ``booted``).
    Mirrors ``make android-log``.
    """
    import os
    from batools import iossim

    args = pcommand.get_args()
    udid = args[0] if args else 'booted'
    iossim.stream_log(
        udid,
        os.environ.get('IOS_LOG_SUBSYSTEM', iossim.DEFAULT_LOG_SUBSYSTEM),
    )
