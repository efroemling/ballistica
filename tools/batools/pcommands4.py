# Released under the MIT License. See LICENSE for details.
#
"""A nice collection of ready-to-use pcommands for this package."""

# Note: import as little as possible here at the module level to
# keep launch times fast for small snippets.
from typing import TYPE_CHECKING

from efrotools import pcommand

if TYPE_CHECKING:
    from libcst import BaseExpression


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


def assetworkspace() -> None:
    """Get/put an asset-package source workspace via a fast local cache.

    Maintains a persistent local checkout of a cloud asset-package source
    workspace under ``.cache/asset_package_sources/<NAME>/`` (gitignored;
    bacloud syncs only diffs, so repeat gets are fast) and wraps
    ``bacloud workspace get``/``put`` against it.

    bacloud itself guards against mid-air collisions: a ``get`` stashes
    the workspace's snapshot id in a ``.bacloudstate.json`` and a ``put``
    is rejected if the workspace has changed since (``put --force``
    overrides). So the only discipline is the standard cycle: ``get`` ->
    edit the files under the printed path -> ``put``.

    Subcommands::

      assetworkspace get <NAME> [--fleet <FLEET>]
      assetworkspace put <NAME> [--force] [--fleet <FLEET>]
      assetworkspace path <NAME>

    ``<NAME>`` is the case-sensitive cloud workspace name (e.g.
    ``BaBuiltinAssets``); ``path`` just prints the cache dir (no network).
    ``--fleet`` targets a non-default master fleet (sets ``BA_FLEET``
    for the underlying bacloud call; flag form keeps the command
    signature stable for sandbox permission grants).
    """
    import os
    import subprocess

    from efro.error import CleanError

    args = pcommand.get_args()
    if len(args) < 2:
        raise CleanError(
            'Expected: <subcommand> <workspace-name> [flags].'
            ' Subcommands: get, put, path.'
        )
    subcmd, name = args[0], args[1]
    flags = args[2:]

    fleet: str | None = None
    if '--fleet' in flags:
        findex = flags.index('--fleet')
        if findex + 1 >= len(flags):
            raise CleanError('--fleet requires a value (e.g. dev).')
        fleet = flags[findex + 1]
        flags = flags[:findex] + flags[findex + 2 :]

    ws_dir = os.path.join(
        pcommand.PROJROOT, '.cache', 'asset_package_sources', name
    )
    bacloud = os.path.join(pcommand.PROJROOT, 'tools', 'bacloud')

    if subcmd == 'path':
        print(ws_dir)
        return

    if subcmd not in ('get', 'put'):
        raise CleanError(f'Unknown subcommand {subcmd!r}; use get, put, path.')

    if subcmd == 'get':
        os.makedirs(ws_dir, exist_ok=True)
    elif not os.path.isdir(ws_dir):
        raise CleanError(
            f'No local cache for {name!r} at {ws_dir};'
            f' run `assetworkspace get {name}` first.'
        )

    cmd = [bacloud, 'workspace', subcmd, ws_dir, '--workspace', name]
    if subcmd == 'put' and '--force' in flags:
        cmd.append('--force')
    env = dict(os.environ)
    if fleet is not None:
        env['BA_FLEET'] = fleet
    try:
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as exc:
        raise CleanError(
            f'bacloud workspace {subcmd} failed for {name!r}.'
        ) from exc
    verb = 'synced to' if subcmd == 'get' else 'pushed from'
    print(f'Workspace {name!r} {verb} {ws_dir}')


def cst_test() -> None:
    """Test filtering a Python file using LibCST."""

    from typing import override

    from efro.error import CleanError
    import libcst as cst
    from libcst import CSTTransformer, Name, Index, Subscript

    args = pcommand.get_args()

    if len(args) != 2:
        raise CleanError('Expected an in-path and out-path.')

    filename = args[0]
    filenameout = args[1]

    class RemoveAnnotatedTransformer(CSTTransformer):
        """Replaces `Annotated[FOO, ...]` with just `FOO`"""

        @override
        def leave_Subscript(
            self, original_node: BaseExpression, updated_node: BaseExpression
        ) -> BaseExpression:
            if (
                isinstance(updated_node, Subscript)
                and isinstance(updated_node.value, Name)
                and updated_node.value.value == 'Annotated'
                and isinstance(updated_node.slice[0].slice, Index)
            ):
                return updated_node.slice[0].slice.value
            return updated_node

    with open(filename, 'r', encoding='utf-8') as f:
        source_code: str = f.read()

    tree: cst.Module = cst.parse_module(source_code)
    modified_tree: cst.Module = tree.visit(RemoveAnnotatedTransformer())

    with open(filenameout, 'w', encoding='utf-8') as f:
        f.write(modified_tree.code)

    print('Success!')


def prefab_symbols_fetch() -> None:
    """Fetch debug symbols for the Windows prefab binaries present.

    Looks up symbols by each binary's content hash from the master
    server's recent-build archives and drops the .pdb next to its exe,
    after which native stack traces in fatal-error output come out
    fully symbolicated. Symbols are retained for recent builds only.
    Honors ``BA_FLEET`` for developer setups (default prod).
    """
    from batools.prefabsymbols import fetch_prefab_symbols

    fetch_prefab_symbols()
