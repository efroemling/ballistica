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


#: Master-server host per fleet, for the freshness check below. Kept
#: local and tiny on purpose: this is a best-effort diagnostic, so it
#: must not drag bacloud's fleet-resolution machinery (and its import
#: cost) into a command whose whole job is to print a path fast.
_FLEET_HOSTS = {
    None: 'www.ballistica.net',
    'prod': 'www.ballistica.net',
    'test': 'test.ballistica.net',
    'dev': 'dev.ballistica.net',
}


def _local_snapshot_id(ws_dir: str) -> str | None:
    """The snapshot id a local checkout was last synced to, if known."""
    import os
    import json

    path = os.path.join(ws_dir, '.bacloudstate.json')
    try:
        with open(path, encoding='utf-8') as infile:
            val = json.load(infile).get('snapshotid')
        return val if isinstance(val, str) else None
    except Exception:
        return None


def _cloud_snapshot_id(name: str, fleet: str | None) -> str | None:
    """The workspace's current cloud snapshot id, or None if unknown.

    Best effort by construction -- every failure mode (no api key, no
    network, an unexpected payload) returns None so callers degrade to
    saying nothing rather than blocking work on a diagnostic.
    """
    import os
    import json
    import urllib.request

    host = _FLEET_HOSTS.get(fleet)
    if host is None:
        return None
    try:
        cfgpath = os.path.join(pcommand.PROJROOT, 'pconfig/localconfig.json')
        with open(cfgpath, encoding='utf-8') as infile:
            api_key = json.load(infile).get('ballistica_api_key')
        if not api_key:
            return None
        req = urllib.request.Request(
            f'https://{host}/api/v1/admin/workspace-size/{name}',
            headers={'Authorization': f'Bearer {api_key}'},
        )
        with urllib.request.urlopen(req, timeout=10.0) as response:
            val = json.loads(response.read().decode()).get('snapshot_id')
        return val if isinstance(val, str) else None
    except Exception:
        return None


def _warn_if_stale(ws_dir: str, name: str, fleet: str | None) -> bool:
    """Warn (to stderr) when a local checkout is behind the cloud.

    Returns whether it is known-stale. The write path is already
    protected -- ``put`` sends the stashed snapshot id and the server
    refuses a stale write -- but *reading* a stale checkout has no such
    guard, and acting on one is silent: content copied out of it looks
    entirely valid downstream. So flag it at the moment a caller asks
    where the files are.
    """
    import sys

    from efro.terminal import Clr

    local = _local_snapshot_id(ws_dir)
    cloud = _cloud_snapshot_id(name, fleet)
    if local is None or cloud is None or local == cloud:
        return False

    print(
        f'{Clr.YLW}WARNING: local checkout of {name!r} is out of date'
        f' (local snapshot {local}, cloud {cloud}).\n'
        f'  Run `tools/pcommand assetworkspace get {name}` before reading'
        f' or copying from it.\n'
        f'  A put from here would be refused, but reads are unguarded:'
        f' stale content looks valid to everything downstream.{Clr.RST}',
        file=sys.stderr,
    )
    return True


def _print_workspace_status(ws_dir: str, name: str, fleet: str | None) -> None:
    """Report whether a local checkout matches the cloud workspace."""
    import os

    from efro.terminal import Clr

    if not os.path.isdir(ws_dir):
        print(f'{name}: no local checkout at {ws_dir}.')
        return
    local = _local_snapshot_id(ws_dir)
    cloud = _cloud_snapshot_id(name, fleet)
    if local is None:
        print(f'{name}: local checkout has no recorded snapshot id.')
    elif cloud is None:
        print(
            f'{name}: local snapshot {local};'
            f' could not reach the cloud to compare.'
        )
    elif local == cloud:
        print(f'{Clr.GRN}{name}: up to date ({local}).{Clr.RST}')
    else:
        _warn_if_stale(ws_dir, name, fleet)


def _validate_bstr_briefs(ws_dir: str) -> None:
    """Parse every ``.bstr`` brief under a workspace checkout.

    Raises :class:`~efro.error.CleanError` naming each unparseable
    file (bad json/dataclass shape or an invalid tag vocabulary in the
    ``input`` brief). Parsing is cheap, so the whole checkout is
    checked every put rather than tracking dirtiness.
    """
    from pathlib import Path

    from efro.error import CleanError
    from efro.dataclassio import dataclass_from_json

    from bacommon.strbrief import parse_brief
    from bacommon.workspace.assetsv1 import (
        AssetsV1StringFile,
        AssetsV1StringFileV1,
    )

    import json

    from efro.terminal import Clr

    # Wrap pins live as path-vals in workspace.json (deliberately
    # outside the .bstr so wrap edits don't restale translations) —
    # which means file-level copy/restore workflows can silently shed
    # them. Surface a heuristic warning for long unconstrained strings
    # with no wrap declared so a dropped pin gets noticed at put time
    # rather than by eyeballs in-game.
    wrapped: set[str] = set()
    try:
        wsjson = json.loads((Path(ws_dir) / 'workspace.json').read_text())
        for wpath, vals in wsjson.get('path', {}).items():
            if isinstance(vals, dict) and 'wrap' in vals:
                wrapped.add(wpath)
    except OSError, ValueError:
        pass  # No/invalid workspace.json; skip wrap warnings.

    def _eng_len(strfile: AssetsV1StringFileV1) -> int | None:
        for locale, output in strfile.outputs.items():
            if locale.value != 'eng':
                continue
            if isinstance(output.value, str):
                return len(output.value)
            # A plural/select selector; use its longest form.
            return max(
                (len(form) for form in output.value.forms.values()),
                default=0,
            )
        return None

    errors: list[str] = []
    warnings: list[str] = []
    for path in sorted(Path(ws_dir).rglob('*.bstr')):
        rel = path.relative_to(ws_dir)
        try:
            strfile = dataclass_from_json(AssetsV1StringFile, path.read_text())
            # Only validate versions we know; a future format version
            # is the server's business, not a reason to block a put.
            if isinstance(strfile, AssetsV1StringFileV1):
                parse_brief(strfile.input)
                englen = _eng_len(strfile)
                # NONE means "no slot declared", not "unbounded on
                # purpose" -- that's PROSE. So a long English string
                # still sitting at NONE is the case worth asking about.
                if (
                    englen is not None
                    and englen > 90
                    and strfile.layout_preset
                    is AssetsV1StringFileV1.LayoutPreset.NONE
                    and str(rel) not in wrapped
                ):
                    warnings.append(
                        f'  {rel}: long English ({englen} chars) with no'
                        f' layout preset and no wrap path-val — set'
                        f' `prose` if it is meant to be unbounded,'
                        f' or pin a line count. (D21)'
                    )
        except CleanError as exc:
            errors.append(f'  {rel}: {exc}')
        except Exception as exc:
            errors.append(f'  {rel}: {exc!r}')
    if warnings:
        label = 'string' if len(warnings) == 1 else 'strings'
        print(
            f'{Clr.YLW}Warning: {len(warnings)} unconstrained-layout'
            f' {label}:\n' + '\n'.join(warnings) + f'{Clr.RST}'
        )
    if errors:
        label = 'brief' if len(errors) == 1 else 'briefs'
        raise CleanError(
            f'Refusing to upload; {len(errors)} invalid .bstr {label}:\n'
            + '\n'.join(errors)
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

    That guard covers *writes* only. Reading a stale checkout is
    unguarded and fails silently -- content copied out of one looks
    entirely valid to everything downstream -- so ``path`` and
    ``status`` check freshness and warn. **Always ``get`` before you
    read, not just before you write**, especially when copying content
    between workspaces.

    Subcommands::

      assetworkspace get <NAME> [--fleet <FLEET>]
      assetworkspace put <NAME> [--force] [--fleet <FLEET>]
      assetworkspace path <NAME> [--fleet <FLEET>]
      assetworkspace status <NAME> [--fleet <FLEET>]

    ``<NAME>`` is the case-sensitive cloud workspace name (e.g.
    ``BaBuiltinAssets``). ``path`` prints the cache dir on stdout (so
    it stays usable in command substitution) plus a staleness warning
    on stderr; ``status`` reports whether the checkout is current.
    Both are best-effort: no api key or no network means no verdict
    rather than a failure. ``--fleet`` targets a non-default master
    fleet (sets ``BA_FLEET`` for the underlying bacloud call; flag form
    keeps the command signature stable for sandbox permission grants).
    """
    import os
    import time
    import subprocess

    from efro.error import CleanError

    args = pcommand.get_args()
    if len(args) < 2:
        raise CleanError(
            'Expected: <subcommand> <workspace-name> [flags].'
            ' Subcommands: get, put, path, status.'
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
        # Path goes to stdout so `$(... path NAME)` keeps working; the
        # staleness verdict goes to stderr.
        _warn_if_stale(ws_dir, name, fleet)
        print(ws_dir)
        return

    if subcmd == 'status':
        _print_workspace_status(ws_dir, name, fleet)
        return

    if subcmd not in ('get', 'put'):
        raise CleanError(
            f'Unknown subcommand {subcmd!r};' f' use get, put, path, status.'
        )

    if subcmd == 'get':
        os.makedirs(ws_dir, exist_ok=True)
    elif not os.path.isdir(ws_dir):
        raise CleanError(
            f'No local cache for {name!r} at {ws_dir};'
            f' run `assetworkspace get {name}` first.'
        )

    # Validate .bstr authoring briefs before an upload so mistakes
    # (duplicate tags, pasted ICU, bad names) fail here with a file
    # pointer instead of minutes later inside a server translation run.
    # The server parses with this same shared module, so the grammar
    # can't drift.
    if subcmd == 'put':
        _validate_bstr_briefs(ws_dir)

    cmd = [bacloud, 'workspace', subcmd, ws_dir, '--workspace', name]
    if subcmd == 'put' and '--force' in flags:
        cmd.append('--force')
    env = dict(os.environ)
    if fleet is not None:
        env['BA_FLEET'] = fleet
    # A `get` is a read-only sync into a local cache, so re-running it
    # is always safe; retry it a couple of times so a transient network
    # hiccup doesn't surface as a hard failure. (Observed 2026-07-26: a
    # run of `SSLError: UNEXPECTED_EOF_WHILE_READING` failures through
    # an egress proxy, which recovered on their own.) A `put` is
    # deliberately NOT retried -- it mutates the cloud workspace, and
    # bacloud owns that retry policy.
    attempts = 3 if subcmd == 'get' else 1
    for attempt in range(1, attempts + 1):
        try:
            subprocess.run(cmd, check=True, env=env)
            break
        except subprocess.CalledProcessError as exc:
            if attempt >= attempts:
                raise CleanError(
                    f'bacloud workspace {subcmd} failed for {name!r}'
                    + (f' after {attempts} attempts.' if attempts > 1 else '.')
                ) from exc
            delay = 2.0 * attempt
            print(
                f'bacloud workspace {subcmd} failed for {name!r}; retrying'
                f' in {delay:.0f}s ({attempt}/{attempts - 1})...'
            )
            time.sleep(delay)
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


def push_ipa_to_archive() -> None:
    """Construct an ios IPA and publish it to a bamaster archive.

    Like push_ipa but uploads into the archive system (signed-URL GCS
    storage) instead of rsyncing to the staging server. Pass
    --archive-id to override the default ('ios-test-builds').
    """
    import sys

    from efro.util import extract_arg
    import efrotools.ios

    args = sys.argv[2:]
    signing_config = extract_arg(args, '--signing-config')
    archive_id = extract_arg(args, '--archive-id')

    if len(args) != 1:
        raise RuntimeError('Expected 1 mode arg (debug or release).')
    modename = args[0].lower()
    efrotools.ios.push_ipa_to_archive(
        pcommand.PROJROOT,
        modename,
        signing_config=signing_config,
        archive_id=('ios-test-builds' if archive_id is None else archive_id),
    )


def push_apk_to_archive() -> None:
    """Publish an already-built android apk to a bamaster archive.

    The android counterpart to push_ipa_to_archive. Takes the path to
    the apk gradle produced (the build targets pass $(AN_APK)); pass
    --archive-id to override the default ('android-test-builds').
    """
    import pathlib

    import sys

    from efro.util import extract_arg
    import efrotools.android

    args = sys.argv[2:]
    archive_id = extract_arg(args, '--archive-id')

    if len(args) != 1:
        raise RuntimeError('Expected 1 apk path arg.')
    efrotools.android.push_apk_to_archive(
        pcommand.PROJROOT,
        pathlib.Path(args[0]),
        archive_id=(
            'android-test-builds' if archive_id is None else archive_id
        ),
    )
