# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines
"""A tool for interacting with ballistica's cloud services.
This facilitates workflows such as creating asset-packages, etc.
"""

import os
import sys
import zlib
import time
import random
import datetime
from pathlib import Path
from dataclasses import dataclass

import requests

from efro.terminal import Clr
from efro.error import CleanError
from efro.dataclassio import (
    dataclass_from_dict,
    dataclass_from_json,
    dataclass_to_dict,
    dataclass_to_json,
    ioprepped,
)
from bacommon.bacloud import (
    RequestData,
    ResponseData,
    StreamFinal,
    StreamOutput,
    BACLOUD_VERSION,
)

TOOL_NAME = 'bacloud'

TIMEOUT_SECONDS = 60 * 5

# Connection-establishment failures (provably pre-send) are retried a
# few times with exponential backoff + full jitter to ride out
# transient blips — Cloud Run cold starts and deploy/traffic-ramp
# windows where the request dies before reaching an app instance and
# thus leaves no server-side log. Full jitter (sleep in [0, backoff])
# deliberately de-syncs herds of concurrent CI jobs that would
# otherwise fail and retry in lockstep.
CONNECT_RETRIES = 5
CONNECT_RETRY_BASE_SECONDS = 0.5
CONNECT_RETRY_MAX_SECONDS = 8.0

VERBOSE = os.environ.get('BACLOUD_VERBOSE') == '1'

# Server selection precedence:
#   1. BACLOUD_SERVER — explicit host override (e.g. a specific basn
#      node). Wins if set; otherwise we derive from BA_FLEET.
#   2. BA_FLEET — matches the env var the client uses. 'prod'
#      (default) routes to regional.ballistica.net directly. 'test'
#      and 'dev' query their fleet's master server for a healthy
#      basn node hostname (since those fleets have no regional.*
#      equivalent).
BACLOUD_SERVER_OVERRIDE = os.getenv('BACLOUD_SERVER')
BA_FLEET = os.getenv('BA_FLEET', 'prod').lower()

_FLEET_MASTER_HOSTS = {
    'prod': 'regional.ballistica.net',
    'test': 'test.ballistica.net',
    'dev': 'dev.ballistica.net',
}


def _caller_build_number() -> int:
    """The engine build number to report to bacloud (0 if unset).

    Master gates asset-package resolves/assembles on this (see
    ``MIN_SUPPORTED_ASSET_BUILD``). Only asset build/assemble commands
    care, and the tooling that drives them (e.g. ``asset_bundle_build``)
    sets ``BA_BUILD_NUMBER`` to the target build; every other bacloud
    caller reports 0, which is irrelevant for non-asset commands. (The
    game's runtime asset resolves don't go through bacloud at all -- they
    ride the basn message protocol -- so there's no engine path here.)
    """
    env = os.environ.get('BA_BUILD_NUMBER')
    if env is not None:
        try:
            return int(env)
        except ValueError:
            pass
    return 0


def _hash_file(path: str) -> tuple[int, str]:
    """Return (size, sha256_hex) for a local file."""
    import hashlib

    size = os.path.getsize(path)
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return size, h.hexdigest()


def _upload_plan_sibling(finalize_command: str, sibling: str) -> str:
    """Derive a sibling command path from a finalize command.

    The prepare/finalize endpoints live as siblings of the finalize
    command's parent. For example, if the finalize command is
    ``admin.archive._archive_publish_finalize``, the resulting
    prepare sibling is ``admin._upload_plan_prepare`` (one level
    above, since the upload infrastructure lives at the admin level).
    """
    parts = finalize_command.split('.')
    # Walk up until we find the 'admin' segment and place the
    # sibling directly under it.
    for i, part in enumerate(parts):
        if part == 'admin':
            return '.'.join(parts[: i + 1] + [sibling])
    raise RuntimeError(
        f'Could not locate admin segment in command path'
        f' {finalize_command!r}.'
    )


@ioprepped
@dataclass
class StateData:
    """Persistent state data stored to disk."""

    login_token: str | None = None


def _resolve_api_key(project_root: Path) -> str | None:
    """Return an API key from env or localconfig.json, or None.

    Precedence:

    1. ``BALLISTICA_API_KEY`` env var.
    2. ``ballistica_api_key`` in the localconfig.json pointed to by
       ``EFRO_LOCALCONFIG_PATH`` (absolute or relative to
       ``project_root``). This matches the override used by
       ``efrotools.project.getlocalconfig`` and is how CI runs on
       build hosts (fromini/etc.) see credentials bound via
       Jenkins ``withCredentials``.
    3. ``ballistica_api_key`` in
       ``<project_root>/pconfig/localconfig.json``.
    """
    import json

    key = os.environ.get('BALLISTICA_API_KEY')
    if key:
        return key

    cfgpaths: list[Path] = []
    override = os.environ.get('EFRO_LOCALCONFIG_PATH')
    if override:
        opath = Path(override)
        cfgpaths.append(opath if opath.is_absolute() else project_root / opath)
    cfgpaths.append(project_root / 'pconfig' / 'localconfig.json')

    for cfgpath in cfgpaths:
        if not cfgpath.exists():
            continue
        try:
            with cfgpath.open(encoding='utf-8') as infile:
                cfg = json.load(infile)
        except Exception:
            continue
        val = cfg.get('ballistica_api_key')
        if isinstance(val, str) and val:
            return val
    return None


def get_tz_offset_seconds() -> float:
    """Return the offset between utc and local time in seconds."""
    tval = time.time()

    # Compare naive current and utc times to get our offset from utc.
    utc_offset = (
        datetime.datetime.fromtimestamp(tval)
        - datetime.datetime.fromtimestamp(tval, datetime.UTC).replace(
            tzinfo=None
        )
    ).total_seconds()

    return utc_offset


def _is_retryable_connection_error(exc: BaseException) -> bool:
    """Return whether ``exc`` is a pre-send connection failure.

    Only failures where the request provably never reached the
    application are retryable: connection-refused, DNS-resolution
    failures, connect-timeouts, and load-balancer 5xx codes
    (502/503/504) returned by Cloud Run's front end before a request is
    handed to an app instance (cold-start / no-instance / bad-gateway
    during a deploy window). These are idempotency-neutral, so retrying
    is safe even for mutating commands (publish, etc.).

    Post-send failures are deliberately NOT retried, since the request
    may already have taken effect: a ``ReadTimeout`` (bytes were sent,
    the app just didn't answer in time) and an app-level HTTP 500.
    """
    # requests.ConnectionError covers connection-refused + DNS
    # failures; ConnectTimeout subclasses it, so connect-timeouts are
    # included. ReadTimeout is NOT a ConnectionError subclass, so
    # post-send read timeouts are correctly excluded here.
    if isinstance(exc, requests.exceptions.ConnectionError):
        return True
    if isinstance(exc, requests.exceptions.HTTPError):
        resp = exc.response
        if resp is not None and resp.status_code in (502, 503, 504):
            return True
    return False


class _TransientDownloadError(Exception):
    """A CAS blob download failed in a retryable way.

    Raised for a truncated stream (byte-count or sha256 mismatch) or a
    transient 5xx from the blob store -- conditions a re-download can
    plausibly fix. See :func:`_is_retryable_download_error`.
    """


def _is_retryable_download_error(exc: BaseException) -> bool:
    """Whether a CAS blob-download failure is worth retrying.

    Unlike the mutating-server path
    (:func:`_is_retryable_connection_error`), a blob download is
    content-idempotent: the signed URL targets one specific content hash
    and the streamed result is size- AND sha256-verified before use. So
    *any* transient fetch failure is safe to retry here -- crucially
    including a ``ReadTimeout`` (bytes were mid-stream), which the server
    path must NOT retry for mutating commands. Covers connection drops,
    connect/read timeouts, chunked-encoding interruptions, and
    truncated/transient-5xx streams (surfaced as
    :class:`_TransientDownloadError`).
    """
    if isinstance(exc, _TransientDownloadError):
        return True
    return isinstance(
        exc,
        (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError,
        ),
    )


# Per-workspace-checkout control file (a dotfile, so the workspace sync
# auto-ignores it) recording the snapshot id we last synced to, for the
# put optimistic-concurrency / mid-air-collision check (bacloud v24+).
_BACLOUD_STATE_FILENAME = '.bacloudstate.json'


# argv prefixes for CLI commands that are safe to retry even when a
# failure is *post-send* (the request may have reached the server).
# These are read-only or content-idempotent — re-running can't
# double-apply a mutation. The client stamps RequestData.idempotent
# from this list; basn reads it to decide whether a post-send upstream
# timeout becomes a retryable 503 or a terminal error. Everything not
# listed defaults to non-idempotent (fail-closed) — notably publish,
# workspace put/get, login/logout, and admin/archive mutations.
_IDEMPOTENT_COMMAND_PREFIXES: tuple[tuple[str, ...], ...] = (
    ('assetpackage', '_assemble'),
    ('assetpackage', 'version'),
    ('assetpackage', '_listing'),
    ('assetpackage', 'wrapper'),
    ('account', 'info'),
)


def _command_is_idempotent(args: list[str]) -> bool:
    """Whether a bacloud CLI invocation is safe to retry post-send.

    Conservative: matches a known read-only / content-idempotent argv
    prefix (see :data:`_IDEMPOTENT_COMMAND_PREFIXES`); otherwise False.
    """
    return any(
        tuple(args[: len(prefix)]) == prefix
        for prefix in _IDEMPOTENT_COMMAND_PREFIXES
    )


def run_bacloud_main() -> None:
    """Do the thing."""
    # pylint: disable=try-except-raise, raise-missing-from

    # We return 0 on success, 1 for a no/fail result, and 2+ for errors.
    try:
        raise SystemExit(App().run())
    except CleanError as clean_exc:
        clean_exc.pretty_print()
        raise SystemExit(2)
    except SystemExit:
        # Never handle this here.
        raise
    except KeyboardInterrupt:
        # Print nothing on keyboard interrupts.
        raise SystemExit(2)
    except Exception:
        sys.excepthook(*sys.exc_info())  # standard color traceback
        raise SystemExit(2)


class App:
    """Context for a run of the tool."""

    def __init__(self) -> None:
        self._state = StateData()
        self._project_root: Path | None = None
        self._end_command_args: dict = {}
        self._return_code = 0
        self._api_key: str | None = None
        self._server: str | None = None
        self._idempotent = False
        # Workspace get/put optimistic-concurrency (v24+): the local dir
        # whose .bacloudstate.json to (re)write, and the snapshot id the
        # server handed back this run.
        self._ws_state_dir: str | None = None
        self._ws_name: str | None = None
        self._ws_snapshotid_received: str | None = None

    def run(self) -> int:
        """Run the tool."""

        # Make sure we can locate the project bacloud is being run from.
        self._project_root = Path(sys.argv[0]).parents[1]
        # Look for a few things we expect to have in a project. The
        # bacommontools check covers every repo that receives this
        # module via efrosync — historically this was tools/batools
        # when bacloud lived exclusively in ballistica-internal.
        if not all(
            Path(self._project_root, name).exists()
            for name in ['pconfig/projectconfig.json', 'tools/bacommontools']
        ):
            raise CleanError('Unable to locate project directory.')

        self._api_key = _resolve_api_key(self._project_root)

        # In API-key mode we're stateless: skip load/save of
        # .cache/bacloud/state. This keeps CI runs from stomping
        # on a developer's cached login token and lets multiple
        # parallel CI jobs coexist without corrupting each other.
        if self._api_key is None:
            self._load_state()

        if self._api_key is not None and VERBOSE:
            # Diagnostics go to stderr so they never pollute captured
            # stdout (callers parse stdout as the command result -- e.g.
            # `assetpins` reads a resolved apverid from it).
            print(
                f'{Clr.BLU}bacloud: authenticating with API key'
                f' ({self._api_key[:8]}\u2026){Clr.RST}',
                file=sys.stderr,
            )

        self._server = self._resolve_server()

        # Classify the whole invocation's retry-safety once (it's a
        # property of the user's CLI command, shared by the kickoff and
        # every chained call). basn uses this to decide whether a
        # post-send upstream timeout is safe to surface as a retryable
        # 503.
        self._idempotent = _command_is_idempotent(sys.argv[1:])

        # For a `workspace get`/`put`, set up optimistic-concurrency
        # handling: a put injects its last-synced snapshot id (from the
        # dir's .bacloudstate.json) so the server can reject a mid-air
        # collision. May mutate args (strip the client-only --force, add
        # --expected-snapshotid).
        cwd = os.getcwd()
        args = self._prep_workspace_command(list(sys.argv[1:]), cwd)

        # Simply pass all args to the server and let it do the thing.
        self.run_interactive_command(cwd=cwd, args=args)

        # On a completed get/put the server hands back the workspace's
        # current snapshot id; stash it for the next put's check.
        self._finish_workspace_command()

        if self._api_key is None:
            self._save_state()

        return self._return_code

    def _prep_workspace_command(self, args: list[str], cwd: str) -> list[str]:
        """Set up optimistic-concurrency for a ``workspace get``/``put``.

        Returns the (possibly modified) args to actually send. For a put,
        strips the client-only ``--force`` flag and -- unless forced --
        adds ``--expected-snapshotid`` from the dir's
        ``.bacloudstate.json`` so the server can reject a mid-air
        collision (the workspace having changed since our last get).
        """
        if (
            len(args) < 2
            or args[0] != 'workspace'
            or args[1] not in ('get', 'put')
        ):
            return args

        # The target dir is the lone positional after the subcommand
        # (default '.'); --workspace takes a value, other --flags don't.
        positionals: list[str] = []
        rest = args[2:]
        i = 0
        while i < len(rest):
            tok = rest[i]
            if tok == '--workspace':
                self._ws_name = rest[i + 1] if i + 1 < len(rest) else None
                i += 2
                continue
            if tok.startswith('--'):
                i += 1
                continue
            positionals.append(tok)
            i += 1
        self._ws_state_dir = os.path.abspath(
            os.path.join(cwd, positionals[0] if positionals else '.')
        )

        if args[1] == 'put':
            force = '--force' in args
            args = [a for a in args if a != '--force']
            if not force:
                snapshotid = self._read_ws_state_snapshotid(self._ws_state_dir)
                if snapshotid is not None:
                    args = args + ['--expected-snapshotid', snapshotid]
        return args

    def _finish_workspace_command(self) -> None:
        """Persist the snapshot id the server returned (get/put), if any."""
        import json

        if self._ws_state_dir is None or self._ws_snapshotid_received is None:
            return
        path = os.path.join(self._ws_state_dir, _BACLOUD_STATE_FILENAME)
        try:
            data: dict[str, str] = {'snapshotid': self._ws_snapshotid_received}
            if self._ws_name is not None:
                data['name'] = self._ws_name
            with open(path, 'w', encoding='utf-8') as outfile:
                json.dump(data, outfile)
        except Exception:
            # Non-fatal: the sync itself succeeded; we just couldn't stash
            # the token (a later put simply skips the check).
            if VERBOSE:
                import traceback

                traceback.print_exc()

    @staticmethod
    def _read_ws_state_snapshotid(ws_dir: str) -> str | None:
        """Read the last-synced snapshot id from a dir's state file."""
        import json

        path = os.path.join(ws_dir, _BACLOUD_STATE_FILENAME)
        if not os.path.exists(path):
            return None
        try:
            with open(path, encoding='utf-8') as infile:
                val = json.load(infile).get('snapshotid')
                return val if isinstance(val, str) else None
        except Exception:
            return None

    @property
    def _state_dir(self) -> Path:
        """The full path to the state dir."""
        assert self._project_root is not None
        return Path(self._project_root, '.cache/bacloud')

    @property
    def _state_data_path(self) -> Path:
        """The full path to the state data file."""
        return Path(self._state_dir, 'state')

    def _load_state(self) -> None:
        if not os.path.exists(self._state_data_path):
            return
        try:
            with open(self._state_data_path, 'r', encoding='utf-8') as infile:
                self._state = dataclass_from_json(StateData, infile.read())
        except Exception:
            print(
                f'{Clr.RED}Error loading {TOOL_NAME} data;'
                f' resetting to defaults.{Clr.RST}',
                file=sys.stderr,
            )

    def _save_state(self) -> None:
        if not self._state_dir.exists():
            self._state_dir.mkdir(parents=True, exist_ok=True)
        with open(self._state_data_path, 'w', encoding='utf-8') as outfile:
            outfile.write(dataclass_to_json(self._state))

    def _resolve_server(self) -> str:
        """Return the bacloud server host to talk to.

        Honors ``BACLOUD_SERVER`` as an explicit override; otherwise
        derives the host from ``BA_FLEET``. For non-prod fleets, asks
        that fleet's master server for a healthy basn node.
        """
        if BACLOUD_SERVER_OVERRIDE:
            return BACLOUD_SERVER_OVERRIDE

        if BA_FLEET not in _FLEET_MASTER_HOSTS:
            raise CleanError(
                f'Invalid BA_FLEET value {BA_FLEET!r};'
                f' expected one of {sorted(_FLEET_MASTER_HOSTS)}.'
            )

        if BA_FLEET == 'prod':
            return _FLEET_MASTER_HOSTS['prod']

        master = _FLEET_MASTER_HOSTS[BA_FLEET]
        try:
            with requests.get(
                f'https://{master}/bacloud_node',
                timeout=TIMEOUT_SECONDS,
            ) as resp:
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            if VERBOSE:
                import traceback

                traceback.print_exc()
            raise CleanError(
                f'Unable to look up a basn node via {master}.'
                f' Set env-var BACLOUD_VERBOSE=1 for details.'
            ) from exc

        err = data.get('error')
        if err is not None:
            raise CleanError(f'bacloud_node ({BA_FLEET}): {err}')
        host = data.get('hostname')
        if not isinstance(host, str) or not host:
            raise CleanError(
                f'bacloud_node ({BA_FLEET}): missing hostname in response.'
            )
        if VERBOSE:
            print(
                f'{Clr.BLU}bacloud: fleet {BA_FLEET!r} -> {host}{Clr.RST}',
                file=sys.stderr,
            )
        return host

    def _servercmd(self, cmd: str, payload: dict, stream: bool) -> ResponseData:
        """Issue a command to the server and get a response."""

        response_content: str | None = None

        assert self._server is not None
        url = f'https://{self._server}/bacloudcmd'
        headers = {'User-Agent': f'bacloud/{BACLOUD_VERSION}'}
        # Single auth path: API key takes precedence; otherwise the
        # login_token from interactive sign-in. Either way, it
        # rides as a standard Authorization Bearer header.
        bearer = self._api_key or self._state.login_token
        if bearer is not None:
            headers['Authorization'] = f'Bearer {bearer}'

        rdata = {
            'v': BACLOUD_VERSION,
            'r': dataclass_to_json(
                RequestData(
                    command=cmd,
                    payload=payload,
                    tzoffset=get_tz_offset_seconds(),
                    isatty=sys.stdout.isatty(),
                    stream=stream,
                    idempotent=self._idempotent,
                    build_number=_caller_build_number(),
                )
            ),
        }

        attempt = 0
        while True:
            try:
                # Trying urllib for comparison (note that this doesn't
                # support files arg so not actually production ready)
                if bool(False):
                    import urllib.request
                    import urllib.parse

                    with urllib.request.urlopen(
                        urllib.request.Request(
                            url,
                            urllib.parse.urlencode(rdata).encode(),
                            headers,
                        )
                    ) as raw_response:
                        if raw_response.getcode() != 200:
                            raise RuntimeError('Error talking to server')
                        response_content = raw_response.read().decode()

                # Using requests module.
                else:
                    with requests.post(
                        url,
                        headers=headers,
                        data=rdata,
                        timeout=TIMEOUT_SECONDS,
                    ) as response_raw:
                        response_raw.raise_for_status()
                        assert isinstance(response_raw.content, bytes)
                        response_content = response_raw.content.decode()
                break

            except Exception as exc:
                # Ride out transient connection-establishment blips
                # (cold starts, deploy/traffic-ramp windows). These are
                # provably pre-send, so retrying is safe even for
                # mutating commands; post-send failures fall straight
                # through and surface immediately.
                if attempt < CONNECT_RETRIES and (
                    _is_retryable_connection_error(exc)
                ):
                    delay = random.uniform(
                        0.0,
                        min(
                            CONNECT_RETRY_MAX_SECONDS,
                            CONNECT_RETRY_BASE_SECONDS * 2**attempt,
                        ),
                    )
                    attempt += 1
                    print(
                        f'{Clr.YLW}Unable to reach bacloud server'
                        f' ({type(exc).__name__}); retrying in'
                        f' {delay:.1f}s ({attempt}/{CONNECT_RETRIES})...'
                        f'{Clr.RST}',
                        file=sys.stderr,
                        flush=True,
                    )
                    time.sleep(delay)
                    continue

                if VERBOSE:
                    import traceback

                    traceback.print_exc()
                raise CleanError(
                    f'Unable to talk to bacloud server:'
                    f' {type(exc).__name__}: {exc}.'
                    f' Set env-var BACLOUD_VERBOSE=1 for the full'
                    f' traceback.'
                ) from exc

        assert response_content is not None
        response = dataclass_from_json(ResponseData, response_content)

        # Handle a few things inline (so this functionality is available
        # even to recursive commands, etc.)
        if response.message is not None:
            print(response.message, end=response.message_end, flush=True)

        if response.message_stderr is not None:
            print(
                response.message_stderr,
                end=response.message_stderr_end,
                flush=True,
                file=sys.stderr,
            )

        if response.error is not None:
            raise CleanError(response.error)

        if response.delay_seconds > 0.0:
            time.sleep(response.delay_seconds)

        return response

    def _download_file(
        self, filename: str, call: str, args: dict
    ) -> int | None:
        import hashlib

        # Fast out - for repeat batch downloads, most of the time these
        # will already exist and we can ignore them.
        if os.path.isfile(filename):
            return None

        # Update: We now assume all dirs have been created before this
        # runs. Creating them as we go here could cause race conditions
        # with multithreaded downloads.
        dirname = os.path.dirname(filename)
        assert os.path.isdir(dirname)

        tmp = f'{filename}.tmp'
        chunk_size = 1024 * 1024

        # CAS blob downloads are content-idempotent -- the signed URL
        # targets one specific content hash and the streamed bytes are
        # size- and sha256-verified below -- so any transient fetch
        # failure is safe to retry. Retry the whole attempt (re-fetching a
        # fresh signed URL each time, in case the prior one expired) with
        # the same backoff + full-jitter the server path uses.
        attempt = 0
        while True:
            try:
                response = self._servercmd(call, args, stream=False)

                # We expect a single sentinel entry in downloads_signed
                # keyed at 'default'. The server-side per-file handler
                # doesn't know the client's destination path, so it hands
                # back one signed URL + hash under that sentinel and we
                # stream it into ``filename`` here.
                assert response.downloads_signed is not None
                assert len(response.downloads_signed) == 1
                entry = response.downloads_signed[0]
                assert entry.path == 'default'

                hasher = hashlib.sha256()
                total = 0
                with requests.get(
                    entry.download_url,
                    stream=True,
                    timeout=TIMEOUT_SECONDS,
                ) as resp:
                    # Transient (5xx) blob-store errors are retryable; any
                    # other non-2xx (e.g. 403/404) is a real problem.
                    if resp.status_code >= 500:
                        raise _TransientDownloadError(
                            f'GCS download of {filename} got transient'
                            f' status={resp.status_code}.'
                        )
                    if not 200 <= resp.status_code < 300:
                        raise CleanError(
                            f'GCS download of {filename} failed:'
                            f' status={resp.status_code}'
                            f' body={resp.text!r}'
                        )
                    with open(tmp, 'wb') as outfile:
                        for chunk in resp.iter_content(chunk_size=chunk_size):
                            if not chunk:
                                continue
                            outfile.write(chunk)
                            hasher.update(chunk)
                            total += len(chunk)

                # A short read or hash mismatch means a truncated/corrupt
                # stream -- retryable (re-download).
                if total != entry.size:
                    raise _TransientDownloadError(
                        f'GCS download of {filename} returned {total} bytes;'
                        f' expected {entry.size} (truncated stream).'
                    )
                digest = hasher.hexdigest()
                if digest != entry.sha256:
                    raise _TransientDownloadError(
                        f'GCS download of {filename} sha256 mismatch: got'
                        f' {digest}, expected {entry.sha256}.'
                    )
                os.rename(tmp, filename)
                return total

            except Exception as exc:
                # Drop any partial tmp before retrying or giving up.
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                if attempt < CONNECT_RETRIES and _is_retryable_download_error(
                    exc
                ):
                    delay = random.uniform(
                        0.0,
                        min(
                            CONNECT_RETRY_MAX_SECONDS,
                            CONNECT_RETRY_BASE_SECONDS * 2**attempt,
                        ),
                    )
                    attempt += 1
                    print(
                        f'{Clr.YLW}Download of'
                        f' {os.path.basename(filename)} failed'
                        f' ({type(exc).__name__}); retrying in {delay:.1f}s'
                        f' ({attempt}/{CONNECT_RETRIES})...{Clr.RST}',
                        file=sys.stderr,
                        flush=True,
                    )
                    time.sleep(delay)
                    continue
                raise

    def _handle_dir_manifest_response(self, dirmanifest: str) -> None:
        from bacommon.transfer import DirectoryManifest

        self._end_command_args['manifest'] = dataclass_to_dict(
            DirectoryManifest.create_from_disk(Path(dirmanifest))
        )

    def _handle_deletes(self, deletes: list[str]) -> None:
        """Handle file deletes."""
        for fname in deletes:
            # Server shouldn't be sending us dir paths here.
            assert not os.path.isdir(fname)
            os.unlink(fname)

    def _handle_downloads_inline(
        self,
        downloads_inline: dict[str, bytes],
    ) -> None:
        """Handle inline file data to be saved to the client."""

        for fname, fdata in downloads_inline.items():
            # If there's a directory where we want our file to go, clear
            # it out first. File deletes should have run before this so
            # everything under it should be empty and thus killable via
            # rmdir.
            if os.path.isdir(fname):
                for basename, dirnames, _fn in os.walk(fname, topdown=False):
                    for dirname in dirnames:
                        os.rmdir(os.path.join(basename, dirname))
                os.rmdir(fname)

            dirname = os.path.dirname(fname)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            data_zipped = fdata
            data = zlib.decompress(data_zipped)

            # Write to tmp files first and then move into place. This
            # way crashes are less likely to lead to corrupt data.
            fnametmp = f'{fname}.tmp'
            with open(fnametmp, 'wb') as outfile:
                outfile.write(data)
            os.rename(fnametmp, fname)

    def _handle_downloads(self, downloads: ResponseData.Downloads) -> None:
        from efro.util import data_size_str
        from concurrent.futures import ThreadPoolExecutor, as_completed

        starttime = time.monotonic()

        # Minor optimization: avoid repeat mkdir calls for the same path
        # (we may have lots of stuff in a single dir).
        prepped_dirs = set[str]()

        def _prep_entry(entry: ResponseData.Downloads.Entry) -> None:
            fullpath = (
                entry.path
                if downloads.basepath is None
                else os.path.join(downloads.basepath, entry.path)
            )
            dirname = os.path.dirname(fullpath)
            if dirname not in prepped_dirs:
                os.makedirs(dirname, exist_ok=True)
                prepped_dirs.add(dirname)

        def _download_entry(entry: ResponseData.Downloads.Entry) -> int | None:
            allargs = downloads.baseargs | entry.args
            fullpath = (
                entry.path
                if downloads.basepath is None
                else os.path.join(downloads.basepath, entry.path)
            )
            return self._download_file(fullpath, downloads.cmd, allargs)

        # Run a single thread pre-pass to create all needed dirs.
        # Creating dirs while downloading can introduce race conditions.
        for entry in downloads.entries:
            _prep_entry(entry)

        total = len(downloads.entries)
        num_dls = 0
        total_bytes = 0
        completed = 0

        # Live progress only helps an interactive terminal; in CI / piped
        # contexts it would just add log noise, so there we keep the
        # single end-of-run summary. Progress rides stderr so it never
        # pollutes stdout (which some callers parse as the result).
        show_progress = sys.stderr.isatty()
        last_draw = 0.0

        def _draw_progress() -> None:
            nonlocal last_draw
            now = time.monotonic()
            # Throttle redraws. No forced final frame is needed — the
            # line is cleared below and replaced by the summary.
            if now - last_draw < 0.25:
                return
            last_draw = now
            # \r returns to col 0; \x1b[K clears to end-of-line so a
            # shorter line never leaves stale characters behind.
            print(
                f'\r{Clr.BLU}Downloading {completed}/{total} files'
                f' ({data_size_str(total_bytes)})\u2026{Clr.RST}\x1b[K',
                end='',
                file=sys.stderr,
                flush=True,
            )

        # Run several downloads simultaneously to hopefully maximize
        # throughput. Drain via as_completed (rather than map) so we can
        # surface incremental progress instead of one blocking barrier.
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(_download_entry, entry)
                for entry in downloads.entries
            ]
            for future in as_completed(futures):
                # .result() re-raises any download error (matching the
                # old list(map(...)) fail-fast behavior).
                result = future.result()
                completed += 1
                if result is not None:
                    num_dls += 1
                    total_bytes += result
                if show_progress:
                    _draw_progress()

        if show_progress:
            # Clear the in-progress line so the summary lands cleanly.
            print('\r\x1b[K', end='', file=sys.stderr, flush=True)

        duration = time.monotonic() - starttime
        if num_dls:
            print(
                f'{Clr.BLU}Downloaded {num_dls} files'
                f' ({data_size_str(total_bytes)}'
                f' total) in {duration:.2f}s.{Clr.RST}'
            )

    def _handle_dir_prune_empty(self, prunedir: str) -> None:
        """Handle pruning empty directories."""
        # Walk the tree bottom-up so we can properly kill recursive
        # empty dirs.
        for basename, dirnames, filenames in os.walk(prunedir, topdown=False):
            # It seems that child dirs we kill during the walk are still
            # listed when the parent dir is visited, so lets make sure
            # to only acknowledge still-existing ones.
            dirnames = [
                d for d in dirnames if os.path.exists(os.path.join(basename, d))
            ]
            if not dirnames and not filenames and basename != prunedir:
                os.rmdir(basename)

    def _handle_uploads_signed(
        self, uploads_signed: list[ResponseData.SignedUploadEntry]
    ) -> None:
        """Handle direct-to-GCS streaming uploads via signed URLs.

        For each entry, stream the local file body straight to the
        signed PUT URL using ``requests`` (which sends a chunked-free
        PUT when ``Content-Length`` is set, so GCS sees the bytes as a
        single body that satisfies the URL's ``Content-MD5``
        signature). Memory use is bounded regardless of file size —
        ``requests`` reads the file object in fixed-size chunks rather
        than slurping it.

        Stashes ``{path: session_id}`` into ``end_command`` args under
        ``uploads_signed`` so the server can finalize each session in
        the next call.
        """
        sessions: dict[str, str] = {}
        for entry in uploads_signed:
            if not os.path.exists(entry.path):
                raise CleanError(f'File not found: {entry.path}')
            file_size = os.path.getsize(entry.path)
            # Setting Content-Length explicitly forces ``requests`` to
            # send a non-chunked PUT, which is required for the signed
            # URL's Content-MD5 binding to validate against a single
            # body on the GCS side.
            put_headers = dict(entry.upload_headers)
            put_headers['Content-Length'] = str(file_size)
            with open(entry.path, 'rb') as infile:
                response = requests.put(
                    entry.upload_url,
                    data=infile,
                    headers=put_headers,
                    timeout=TIMEOUT_SECONDS,
                )
            if not 200 <= response.status_code < 300:
                raise CleanError(
                    f'GCS upload of {entry.path} failed:'
                    f' status={response.status_code}'
                    f' body={response.text!r}'
                )
            sessions[entry.path] = entry.session_id
        self._end_command_args['uploads_signed'] = sessions

    def _handle_upload_plan(  # pylint: disable=too-many-locals
        self, plan: ResponseData.UploadPlan
    ) -> tuple[str, dict, bool]:
        """Execute an upload plan end-to-end.

        Walks ``plan.source_dir``, computes sha256+size for every
        file, asks the server which need uploading (dedup check),
        streams the missing ones direct-to-GCS, finalizes the
        upload sessions, and returns the next call tuple for the
        command's ``finalize_command``.
        """
        from bacommon.bacloud import (
            UploadPlanFileInfo,
            UploadPlanPrepareRequest,
            UploadPlanPrepareResponse,
            UploadPlanFinalizeRequest,
            UploadPlanFinalizeResponse,
            UploadPlanCommit,
        )

        source_dir = plan.source_dir
        if not os.path.isdir(source_dir):
            raise CleanError(f'upload_plan source dir not found: {source_dir}')

        # Phase 1: enumerate files and compute hashes.
        files: list[UploadPlanFileInfo] = []
        local_paths: dict[str, str] = {}  # name -> absolute path
        for basepath, _dirs, filenames in os.walk(source_dir):
            for fn in filenames:
                full = os.path.join(basepath, fn)
                rel = os.path.relpath(full, source_dir)
                size, sha256 = _hash_file(full)
                files.append(
                    UploadPlanFileInfo(name=rel, sha256=sha256, size=size)
                )
                local_paths[rel] = full

        if not files:
            raise CleanError(f'upload_plan source dir {source_dir} is empty.')

        # Phase 2: prepare (dedup + allocate uploads).
        prepare_req = UploadPlanPrepareRequest(
            files=files,
            cloud_file_category=plan.cloud_file_category,
        )
        prepare_cmd = _upload_plan_sibling(
            plan.finalize_command, '_upload_plan_prepare'
        )
        prepare_resp_raw = self._servercmd(
            prepare_cmd, dataclass_to_dict(prepare_req), stream=False
        )
        if prepare_resp_raw.raw_result is None:
            raise CleanError('Prepare response missing raw_result.')
        prepare_resp = dataclass_from_dict(
            UploadPlanPrepareResponse, prepare_resp_raw.raw_result
        )

        # Phase 3: stream any needs-upload files to GCS.
        sessions: dict[str, str] = {}
        resolved: dict[str, str] = {}  # name -> cloud_file_id
        for item in prepare_resp.items:
            if item.cloud_file_id is not None:
                resolved[item.name] = item.cloud_file_id
                continue
            assert item.upload_url is not None
            assert item.session_id is not None
            local = local_paths[item.name]
            file_size = os.path.getsize(local)
            put_headers = dict(item.upload_headers)
            put_headers['Content-Length'] = str(file_size)
            with open(local, 'rb') as infile:
                resp = requests.put(
                    item.upload_url,
                    data=infile,
                    headers=put_headers,
                    timeout=TIMEOUT_SECONDS,
                )
            if not 200 <= resp.status_code < 300:
                raise CleanError(
                    f'GCS upload of {item.name} failed:'
                    f' status={resp.status_code}'
                    f' body={resp.text!r}'
                )
            sessions[item.name] = item.session_id

        # Phase 4: finalize uploaded files (if any).
        if sessions:
            finalize_cmd = _upload_plan_sibling(
                plan.finalize_command, '_upload_plan_finalize'
            )
            finalize_req = UploadPlanFinalizeRequest(sessions=sessions)
            finalize_resp_raw = self._servercmd(
                finalize_cmd, dataclass_to_dict(finalize_req), stream=False
            )
            if finalize_resp_raw.raw_result is None:
                raise CleanError('Finalize response missing raw_result.')
            finalize_resp = dataclass_from_dict(
                UploadPlanFinalizeResponse, finalize_resp_raw.raw_result
            )
            for name, cfid in finalize_resp.cloud_file_ids.items():
                resolved[name] = cfid

        # Phase 5: hand off to the plan's finalize command.
        commit = UploadPlanCommit(files=resolved, state=plan.finalize_state)
        return (plan.finalize_command, dataclass_to_dict(commit), False)

    def _handle_downloads_signed(
        self, downloads_signed: list[ResponseData.SignedDownloadEntry]
    ) -> None:
        """Handle direct-from-GCS streaming downloads via signed URLs.

        For each entry, stream the GCS body straight to ``<path>.tmp``
        while feeding bytes through ``hashlib.sha256``. On a successful
        digest + size match we atomic-rename into place; on mismatch
        we delete the tmp file and raise. Memory use is bounded by the
        stream chunk size regardless of file size, so this bypasses
        the Cloud Run 32 MB response cap entirely.

        Downloads run through a thread pool so large workspaces fan
        out over the network instead of serializing through one TCP
        connection.
        """
        import hashlib
        from concurrent.futures import ThreadPoolExecutor

        # 1 MiB read chunk — large enough to keep per-chunk overhead
        # negligible, small enough that peak memory stays bounded even
        # when running several fetches concurrently.
        chunk_size = 1024 * 1024

        def _fetch(entry: ResponseData.SignedDownloadEntry) -> None:
            # Clear out any existing dir where we want the file to go
            # (mirrors the _handle_downloads_inline contract — file
            # deletes should have run before this, so anything still
            # here should be empty and killable via rmdir).
            if os.path.isdir(entry.path):
                for basename, dirnames, _fn in os.walk(
                    entry.path, topdown=False
                ):
                    for dirname in dirnames:
                        os.rmdir(os.path.join(basename, dirname))
                os.rmdir(entry.path)

            # Ensure the parent dir exists. For the workspace-get path
            # the server supplies absolute paths the client chose, and
            # the intermediate dirs may not exist yet.
            parent = os.path.dirname(entry.path)
            if parent:
                os.makedirs(parent, exist_ok=True)

            tmp = f'{entry.path}.tmp'
            hasher = hashlib.sha256()
            total = 0
            with requests.get(
                entry.download_url,
                stream=True,
                timeout=TIMEOUT_SECONDS,
            ) as resp:
                if not 200 <= resp.status_code < 300:
                    raise CleanError(
                        f'GCS download of {entry.path} failed:'
                        f' status={resp.status_code}'
                        f' body={resp.text!r}'
                    )
                with open(tmp, 'wb') as outfile:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if not chunk:
                            continue
                        outfile.write(chunk)
                        hasher.update(chunk)
                        total += len(chunk)

            if total != entry.size:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise CleanError(
                    f'GCS download of {entry.path} returned'
                    f' {total} bytes; expected {entry.size}.'
                )
            digest = hasher.hexdigest()
            if digest != entry.sha256:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise CleanError(
                    f'GCS download of {entry.path} sha256'
                    f' mismatch: got {digest}, expected {entry.sha256}.'
                )
            os.rename(tmp, entry.path)

        if not downloads_signed:
            return
        # Cap parallelism at 4 to match _handle_downloads — this is
        # enough to saturate a typical client uplink without piling
        # pressure on GCS or running the client out of fds.
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(_fetch, downloads_signed))

    def _handle_open_url(self, url: str) -> None:
        import webbrowser

        print(f'{Clr.CYN}(url: {url}){Clr.RST}', file=sys.stderr)
        webbrowser.open(url)

    def _handle_input_prompt(self, prompt: str, as_password: bool) -> None:
        if as_password:
            from getpass import getpass

            self._end_command_args['input'] = getpass(prompt=prompt)
        else:
            if prompt:
                print(prompt, end='', flush=True)
            self._end_command_args['input'] = input()

    def _consume_via_stream_ws(self, response: ResponseData) -> ResponseData:
        """Drain a streamcall over WebSocket.

        Thin wrapper over :func:`bacommontools.streamws.consume_via_ws`
        that injects this app's bearer token. Raises
        :class:`CleanError` on any WS failure (no HTTP-polling
        fallback).
        """
        # pylint: disable=cyclic-import
        from bacommontools.streamws import consume_via_ws

        assert self._server is not None
        bearer = self._api_key or self._state.login_token
        return consume_via_ws(response, bearer=bearer, host=self._server)

    def _servercmd_chained(
        self, call: tuple[str, dict, bool], retry_window: float
    ) -> ResponseData:
        """Run a chained server command, retrying transient failures.

        ``retry_window`` comes from the previous response's
        ``retry_window_seconds``: when > 0 the server has declared this
        chained step idempotent/safe to repeat, so any failure
        (transport or server-reported) is retried with backoff until
        the window elapses, then surfaced normally. A zero window
        behaves exactly like a direct ``_servercmd`` call.
        """
        deadline = time.monotonic() + retry_window
        while True:
            try:
                return self._servercmd(*call)
            except CleanError:
                remaining = deadline - time.monotonic()
                if remaining <= 0.0:
                    raise
                print(
                    f'{Clr.YLW}Server hiccup; retrying...{Clr.RST}',
                    file=sys.stderr,
                    flush=True,
                )
                time.sleep(min(3.0, remaining))

    def run_interactive_command(self, cwd: str, args: list[str]) -> None:
        """Run a single user command to completion."""
        # pylint: disable=too-many-branches
        assert self._project_root is not None
        nextcall: tuple[str, dict, bool] | None = (
            '_interactive',
            {'c': cwd, 'p': str(self._project_root), 'a': args},
            False,
        )

        # Now talk to the server in a loop until there's nothing left to
        # do.
        retry_window = 0.0
        while nextcall is not None:
            self._end_command_args = {}
            response = self._servercmd_chained(nextcall, retry_window)
            nextcall = None
            retry_window = 0.0

            # Phase 2: if the kickoff response carries ``stream_ws``,
            # drain the stream over WebSocket (basn-hosted). WS
            # failures raise CleanError; there is no HTTP-polling
            # fallback. The kickoff response's HTTP ``end_command``
            # path remains in use only for kickoffs that *don't* get
            # a ``stream_ws`` injected (older basn or direct-bamaster).
            if response.stream_ws is not None:
                response = self._consume_via_stream_ws(response)

            # Stream-mode responses: print incremental output frames in
            # order. If a StreamFinal is encountered, treat its inner
            # response as the response to process for this iteration —
            # it carries the call's terminal message / end_command /
            # error / etc. If no StreamFinal lands in this poll
            # iteration, the outer response's other fields are unused
            # (they are just a polling envelope) and we let the outer
            # ``end_command`` drive the next poll.
            if response.stream_frames is not None:
                terminal: ResponseData | None = None
                for frame in response.stream_frames:
                    if isinstance(frame, StreamOutput):
                        print(frame.text, end='', flush=True)
                    elif isinstance(frame, StreamFinal):
                        terminal = frame.response
                        # Any frames after the terminal would be a
                        # protocol violation; stop here defensively.
                        break
                if terminal is None:
                    # Not done yet — proceed with the polling envelope's
                    # end_command (delay_seconds was already applied
                    # inside _servercmd). Skip the rest of the outer
                    # response's fields (they are unused in polling
                    # envelopes).
                    if response.end_command is not None:
                        nextcall = response.end_command
                        retry_window = response.retry_window_seconds
                        for key, val in self._end_command_args.items():
                            nextcall[1][key] = val
                    continue
                # Terminal frame: replace response with the inner one
                # and apply the inline handling that _servercmd would
                # have done if the inner had been the direct response
                # (message / message_stderr / error). Then fall through
                # to the regular field processing for the rest.
                response = terminal
                if response.message is not None:
                    print(
                        response.message,
                        end=response.message_end,
                        flush=True,
                    )
                if response.message_stderr is not None:
                    print(
                        response.message_stderr,
                        end=response.message_stderr_end,
                        flush=True,
                        file=sys.stderr,
                    )
                if response.error is not None:
                    raise CleanError(response.error)

            if response.login is not None:
                self._state.login_token = response.login
            if response.logout:
                self._state.login_token = None
            if response.dir_manifest is not None:
                self._handle_dir_manifest_response(response.dir_manifest)
            if response.uploads_signed is not None:
                self._handle_uploads_signed(response.uploads_signed)
            if response.upload_plan is not None:
                nextcall = self._handle_upload_plan(response.upload_plan)
                # Upload plan overrides end_command; skip the rest of
                # response processing for this round.
                if response.end_command is not None:
                    raise CleanError(
                        'Response has both upload_plan and end_command;'
                        ' these are mutually exclusive.'
                    )
                continue

            # Note: we handle file deletes *before* downloads. This way
            # our file-download code only has to worry about creating or
            # removing directories and not files, and corner cases such
            # as a file getting replaced with a directory should just
            # work.
            #
            # UPDATE: that actually only applies to commands where the
            # client uploads a manifest first and then the server
            # responds with specific deletes and inline downloads. The
            # newer 'downloads' command is used differently; in that
            # case the server is just pushing a big list of hashes to
            # the client and the client is asking for the stuff it
            # doesn't have. So in that case the client needs to fully
            # handle things like replacing dirs with files.
            if response.deletes:
                self._handle_deletes(response.deletes)
            if response.downloads:
                self._handle_downloads(response.downloads)
            if response.downloads_inline:
                self._handle_downloads_inline(response.downloads_inline)
            if response.downloads_signed:
                self._handle_downloads_signed(response.downloads_signed)
            if response.dir_prune_empty:
                self._handle_dir_prune_empty(response.dir_prune_empty)
            if response.workspace_snapshotid is not None:
                # A get/put completed; remember the workspace's current
                # snapshot id so _finish_workspace_command can stash it.
                self._ws_snapshotid_received = response.workspace_snapshotid

            if response.open_url is not None:
                self._handle_open_url(response.open_url)
            if response.input_prompt is not None:
                self._handle_input_prompt(
                    prompt=response.input_prompt[0],
                    as_password=response.input_prompt[1],
                )
            if response.end_message is not None:
                print(
                    response.end_message,
                    end=response.end_message_end,
                    flush=True,
                )
            if response.end_message_stderr is not None:
                print(
                    response.end_message_stderr,
                    end=response.end_message_stderr_end,
                    flush=True,
                    file=sys.stderr,
                )
            if response.end_command is not None:
                nextcall = response.end_command
                retry_window = response.retry_window_seconds
                for key, val in self._end_command_args.items():
                    nextcall[1][key] = val

            if response.return_code is not None:
                # Should only get these if we're actually gonna exit.
                assert nextcall is None
                self._return_code = response.return_code
