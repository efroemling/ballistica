# Released under the MIT License. See LICENSE for details.
#
"""A tool for interacting with ballistica's cloud services.
This facilitates workflows such as creating asset-packages, etc.
"""

from __future__ import annotations

import os
import sys
import zlib
import time
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
from bacommon.bacloud import RequestData, ResponseData, BACLOUD_VERSION

TOOL_NAME = 'bacloud'

TIMEOUT_SECONDS = 60 * 5

VERBOSE = os.environ.get('BACLOUD_VERBOSE') == '1'

# Server we talk to (can override via env var).
BACLOUD_SERVER = os.getenv('BACLOUD_SERVER', 'ballistica.net')


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
       ``<project_root>/config/localconfig.json``.
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
    cfgpaths.append(project_root / 'config' / 'localconfig.json')

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
            for name in ['config/projectconfig.json', 'tools/bacommontools']
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
            print(
                f'{Clr.BLU}bacloud: authenticating with API key'
                f' ({self._api_key[:8]}\u2026){Clr.RST}'
            )

        # Simply pass all args to the server and let it do the thing.
        self.run_interactive_command(cwd=os.getcwd(), args=sys.argv[1:])

        if self._api_key is None:
            self._save_state()

        return self._return_code

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
                f' resetting to defaults.{Clr.RST}'
            )

    def _save_state(self) -> None:
        if not self._state_dir.exists():
            self._state_dir.mkdir(parents=True, exist_ok=True)
        with open(self._state_data_path, 'w', encoding='utf-8') as outfile:
            outfile.write(dataclass_to_json(self._state))

    def _servercmd(self, cmd: str, payload: dict) -> ResponseData:
        """Issue a command to the server and get a response."""

        response_content: str | None = None

        url = f'https://{BACLOUD_SERVER}/bacloudcmd'
        headers = {'User-Agent': f'bacloud/{BACLOUD_VERSION}'}
        if self._api_key is not None:
            headers['Authorization'] = f'Bearer {self._api_key}'

        rdata = {
            'v': BACLOUD_VERSION,
            'r': dataclass_to_json(
                RequestData(
                    command=cmd,
                    # In API-key mode we explicitly send no
                    # session token; auth travels via the header.
                    token=(
                        None
                        if self._api_key is not None
                        else self._state.login_token
                    ),
                    payload=payload,
                    tzoffset=get_tz_offset_seconds(),
                    isatty=sys.stdout.isatty(),
                )
            ),
        }

        try:
            # Trying urllib for comparison (note that this doesn't
            # support files arg so not actually production ready)
            if bool(False):
                import urllib.request
                import urllib.parse

                with urllib.request.urlopen(
                    urllib.request.Request(
                        url, urllib.parse.urlencode(rdata).encode(), headers
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

        except Exception as exc:
            if VERBOSE:
                import traceback

                traceback.print_exc()
            raise CleanError(
                'Unable to talk to bacloud server.'
                ' Set env-var BACLOUD_VERBOSE=1 for details.'
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

        response = self._servercmd(call, args)

        # We expect a single sentinel entry in downloads_signed keyed
        # at 'default'. The server-side per-file handler doesn't know
        # the client's destination path, so it hands back one signed
        # URL + hash under that sentinel and we stream it into
        # ``filename`` here.
        assert response.downloads_signed is not None
        assert len(response.downloads_signed) == 1
        entry = response.downloads_signed[0]
        assert entry.path == 'default'

        tmp = f'{filename}.tmp'
        chunk_size = 1024 * 1024
        hasher = hashlib.sha256()
        total = 0
        with requests.get(
            entry.download_url,
            stream=True,
            timeout=TIMEOUT_SECONDS,
        ) as resp:
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

        if total != entry.size:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise CleanError(
                f'GCS download of {filename} returned'
                f' {total} bytes; expected {entry.size}.'
            )
        digest = hasher.hexdigest()
        if digest != entry.sha256:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise CleanError(
                f'GCS download of {filename} sha256 mismatch:'
                f' got {digest}, expected {entry.sha256}.'
            )
        os.rename(tmp, filename)
        return total

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
        from concurrent.futures import ThreadPoolExecutor

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

        # Run several downloads simultaneously to hopefully maximize
        # throughput.
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Convert the generator to a list to trigger any exceptions
            # that occurred.
            results = list(executor.map(_download_entry, downloads.entries))

        num_dls = sum(1 for x in results if x is not None)
        total_bytes = sum(x for x in results if x is not None)
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
    ) -> tuple[str, dict]:
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
            prepare_cmd, dataclass_to_dict(prepare_req)
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
                finalize_cmd, dataclass_to_dict(finalize_req)
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
        return (plan.finalize_command, dataclass_to_dict(commit))

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

        print(f'{Clr.CYN}(url: {url}){Clr.RST}')
        webbrowser.open(url)

    def _handle_input_prompt(self, prompt: str, as_password: bool) -> None:
        if as_password:
            from getpass import getpass

            self._end_command_args['input'] = getpass(prompt=prompt)
        else:
            if prompt:
                print(prompt, end='', flush=True)
            self._end_command_args['input'] = input()

    def run_interactive_command(self, cwd: str, args: list[str]) -> None:
        """Run a single user command to completion."""
        # pylint: disable=too-many-branches
        assert self._project_root is not None
        nextcall: tuple[str, dict] | None = (
            '_interactive',
            {'c': cwd, 'p': str(self._project_root), 'a': args},
        )

        # Now talk to the server in a loop until there's nothing left to
        # do.
        while nextcall is not None:
            self._end_command_args = {}
            response = self._servercmd(*nextcall)
            nextcall = None

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
                for key, val in self._end_command_args.items():
                    nextcall[1][key] = val

            if response.return_code is not None:
                # Should only get these if we're actually gonna exit.
                assert nextcall is None
                self._return_code = response.return_code
