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
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from dataclasses import dataclass

import requests

from efro.terminal import Clr
from efro.error import CleanError
from efro.dataclassio import (
    dataclass_from_json,
    dataclass_to_dict,
    dataclass_to_json,
    ioprepped,
)
from bacommon.bacloud import RequestData, ResponseData, BACLOUD_VERSION

if TYPE_CHECKING:
    from typing import IO

TOOL_NAME = 'bacloud'

TIMEOUT_SECONDS = 60 * 5

VERBOSE = os.environ.get('BACLOUD_VERBOSE') == '1'

# Server we talk to (can override via env var).
BACLOUD_SERVER = os.getenv('BACLOUD_SERVER', 'ballistica.net')


@ioprepped
@dataclass
class StateData:
    """Persistent state data stored to disk."""

    login_token: str | None = None


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
    try:
        App().run()
    except KeyboardInterrupt:
        # Let's do a clean fail on keyboard interrupt. Can make this
        # optional if a backtrace is ever useful.
        sys.exit(1)
    except CleanError as clean_exc:
        clean_exc.pretty_print()
        sys.exit(1)


class App:
    """Context for a run of the tool."""

    def __init__(self) -> None:
        self._state = StateData()
        self._project_root: Path | None = None
        self._end_command_args: dict = {}

    def run(self) -> None:
        """Run the tool."""

        # Make sure we can locate the project bacloud is being run from.
        self._project_root = Path(sys.argv[0]).parents[1]
        # Look for a few things we expect to have in a project.
        if not all(
            Path(self._project_root, name).exists()
            for name in ['config/projectconfig.json', 'tools/batools']
        ):
            raise CleanError('Unable to locate project directory.')

        self._load_state()

        # Simply pass all args to the server and let it do the thing.
        self.run_interactive_command(cwd=os.getcwd(), args=sys.argv[1:])

        self._save_state()

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

    def _servercmd(
        self, cmd: str, payload: dict, files: dict[str, IO] | None = None
    ) -> ResponseData:
        """Issue a command to the server and get a response."""

        response_content: str | None = None

        url = f'https://{BACLOUD_SERVER}/bacloudcmd'
        headers = {'User-Agent': f'bacloud/{BACLOUD_VERSION}'}

        rdata = {
            'v': BACLOUD_VERSION,
            'r': dataclass_to_json(
                RequestData(
                    command=cmd,
                    token=self._state.login_token,
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
                    files=files,
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

        if response.error is not None:
            raise CleanError(response.error)

        if response.delay_seconds > 0.0:
            time.sleep(response.delay_seconds)

        return response

    def _download_file(
        self, filename: str, call: str, args: dict
    ) -> int | None:

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

        # We currently expect a single 'default' entry in
        # downloads_inline for this.
        assert response.downloads_inline is not None
        assert len(response.downloads_inline) == 1
        data_zipped = response.downloads_inline.get('default')
        assert isinstance(data_zipped, bytes)

        data = zlib.decompress(data_zipped)

        # Write to tmp files first and then move into place. This way
        # crashes are less likely to lead to corrupt data.
        fnametmp = f'{filename}.tmp'
        with open(fnametmp, 'wb') as outfile:
            outfile.write(data)
        os.rename(fnametmp, filename)
        return len(data)

    def _upload_file(self, filename: str, call: str, args: dict) -> None:
        import tempfile

        print(f'Uploading {Clr.BLU}{filename}{Clr.RST}', flush=True)
        with tempfile.TemporaryDirectory() as tempdir:
            srcpath = Path(filename)
            gzpath = Path(tempdir, 'file.gz')
            subprocess.run(
                f'gzip --stdout "{srcpath}" > "{gzpath}"',
                shell=True,
                check=True,
            )
            with open(gzpath, 'rb') as infile:
                putfiles: dict = {'file': infile}
                _response = self._servercmd(
                    call,
                    args,
                    files=putfiles,
                )

    def _handle_dir_manifest_response(self, dirmanifest: str) -> None:
        from bacommon.transfer import DirectoryManifest

        self._end_command_args['manifest'] = dataclass_to_dict(
            DirectoryManifest.create_from_disk(Path(dirmanifest))
        )

    def _handle_uploads(self, uploads: tuple[list[str], str, dict]) -> None:
        from concurrent.futures import ThreadPoolExecutor

        assert len(uploads) == 3
        filenames, uploadcmd, uploadargs = uploads
        assert isinstance(filenames, list)
        assert isinstance(uploadcmd, str)
        assert isinstance(uploadargs, dict)

        def _do_filename(filename: str) -> None:
            self._upload_file(filename, uploadcmd, uploadargs)

        # Here we can run uploads concurrently if that goes faster...
        # (should keep an eye on this to make sure its thread safe and
        # behaves itself)
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Convert the generator to a list to surface any exceptions
            # that occurred.
            list(executor.map(_do_filename, filenames))

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

    def _handle_uploads_inline(self, uploads_inline: list[str]) -> None:
        """Handle uploading files inline."""
        import base64

        files: dict[str, str] = {}
        for filepath in uploads_inline:
            if not os.path.exists(filepath):
                raise CleanError(f'File not found: {filepath}')
            with open(filepath, 'rb') as infile:
                data = infile.read()
            data_zipped = zlib.compress(data)
            data_base64 = base64.b64encode(data_zipped).decode()
            files[filepath] = data_base64
        self._end_command_args['uploads_inline'] = files

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
            if response.uploads is not None:
                self._handle_uploads(response.uploads)
            if response.uploads_inline is not None:
                self._handle_uploads_inline(response.uploads_inline)

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
            if response.end_command is not None:
                nextcall = response.end_command
                for key, val in self._end_command_args.items():
                    nextcall[1][key] = val
