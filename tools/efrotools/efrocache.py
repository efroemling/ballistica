# Released under the MIT License. See LICENSE for details.
#
"""A simple cloud caching system for making built binaries & assets.

The basic idea here is the ballistica-internal project can flag file
targets in its Makefiles as 'cached', and the public version of those
Makefiles will be filtered to contain cache downloads in place of the
original build commands. Cached files are gathered and uploaded as part
of the pubsync process.

This module is the *consumer* half -- fetching cached targets and
warming the local cache -- which is what public and spinoff repos run.
The gather-and-upload half lives in :mod:`efrotools.efrocachepublish`
and runs only in ballistica-internal.
"""

import os
import json
import time
import zlib
import subprocess
from typing import TYPE_CHECKING, Annotated
from dataclasses import dataclass
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor

from efro.dataclassio import (
    ioprepped,
    IOAttrs,
    dataclass_to_json,
    dataclass_from_json,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    import efro.terminal


TARGET_TAG = '# __EFROCACHE_TARGET__'

CACHE_MAP_NAME = '.efrocachemap'

UPLOAD_STATE_CACHE_FILE = '.cache/efrocache_upload_state'

# Cache file consists of these header bytes, single metadata length byte,
# metadata utf8 bytes, compressed data bytes.
CACHE_HEADER = b'efca'


@ioprepped
@dataclass
class CacheMetadata:
    """Metadata stored with a cache file."""

    executable: Annotated[bool, IOAttrs('e')]


_g_cache_prefix_noexec: bytes | None = None
_g_cache_prefix_exec: bytes | None = None

# Have we already mentioned the wsl-exec-bit oddity this run? (see
# _cache_prefix_for_file). We only want to say it once; otherwise it
# gets repeated for every single file we touch.
_g_noted_wsl_exec_bits = False

# Rough guidance for the curl exit codes we're most likely to see, so a
# failed download can point at a probable cause instead of just asking
# whether the internet is working.
CURL_ERROR_HINTS: dict[int, str] = {
    5: 'Could not resolve the proxy set in the environment.',
    6: 'Could not resolve the server name (dns problem?).',
    7: 'Could not connect to the server (blocked by a firewall/proxy?).',
    28: 'The transfer timed out.',
    35: 'Ssl/tls handshake failed (tls-intercepting proxy?).',
    56: 'The connection dropped part way through the transfer.',
    60: 'Could not verify the server cert (stale ca-certificates?).',
}

# Curl exit codes we'll take another swing at. These are all
# connection-level gripes (dns, connect, timeout, dropped transfer)
# which are commonly just a momentary hiccup.
CURL_RETRY_CODES: set[int] = {5, 6, 7, 18, 28, 35, 52, 55, 56}

# Http codes we'll take another swing at. Anything else the server says
# (404s and friends) won't be fixed by asking again.
HTTP_RETRY_CODES: set[int] = {408, 425, 429, 500, 502, 503, 504}

# How many times we'll try a single download, and how long we wait
# before the second try (doubling for each try after that).
DOWNLOAD_ATTEMPTS = 4
DOWNLOAD_RETRY_DELAY = 2.0


def get_local_cache_dir() -> str:
    """Where we store local efrocache files we've downloaded.

    Rebuilds will be able to access the local cache instead of re-downloading.
    By default each project has its own cache dir but this can be shared
    between projects by setting the EFROCACHE_DIR environment variable.
    """
    envval = os.environ.get('EFROCACHE_DIR')
    if not isinstance(envval, str):
        envval = '.cache/efrocache'
    if not envval:
        raise RuntimeError('efrocache-local-dir cannot be an empty string.')
    if envval.endswith('/') or envval.endswith('\\'):
        raise RuntimeError('efrocache-local-dir must not end with a slash.')
    return envval


def get_repository_base_url() -> str:
    """Return the base repository url (assumes cwd is project root)."""
    from efrotools.project import getprojectconfig

    pconfig = getprojectconfig('.')
    name = 'efrocache_repository_url'
    val = pconfig.get(name)
    if not isinstance(val, str):
        raise RuntimeError(f"'{name}' was not found in projectconfig.")
    if val.endswith('/'):
        raise RuntimeError('Repository string should not end in a slash.')
    return val


def get_existing_file_hash(path: str) -> str:
    """Return the hash used for caching."""
    import hashlib

    prefix = _cache_prefix_for_file(path)
    md5 = hashlib.md5()
    with open(path, 'rb') as infile:
        md5.update(prefix + infile.read())
    return md5.hexdigest()


def _project_centric_path(path: str) -> str:
    """Convert something like foo/../bar to simply bar."""

    # NOTE: we want this to function under raw Windows Python so lets
    # keep everything using forward slashes which is what our cache maps
    # use.
    projpath = f'{os.getcwd()}/'.replace('\\', '/')
    abspath = os.path.abspath(path).replace('\\', '/')
    if not abspath.startswith(projpath):
        raise RuntimeError(
            f'Path "{abspath}" is not under project root "{projpath}"'
        )
    return abspath[len(projpath) :]


@dataclass
class _DownloadFailure:
    """The state of a download that never panned out."""

    url: str
    returncode: int
    http_code: int | None
    proxy_code: int | None
    stderr: bytes | None
    attempts: int

    @property
    def status_code(self) -> int | None:
        """The most meaningful http code we got, if any."""
        return self.http_code if self.http_code is not None else self.proxy_code

    def summary(self) -> str:
        """Return a short single-line reason (for retry messages)."""
        if self.status_code is not None:
            via = '' if self.http_code is not None else ' from proxy'
            return f'http {self.status_code}{via}'
        return f'curl error {self.returncode}'

    def describe(self) -> str:
        """Return indented lines saying everything we know.

        Downloads are the most common failure point for folks building
        the public repo, so we want to say exactly what went wrong
        instead of leaving them staring at a generic message.
        """
        lines = [f'url: {self.url}']
        if self.http_code is not None:
            lines.append(f'server returned: http {self.http_code}')
        elif self.proxy_code is not None:
            # We never reached the server; a proxy answered our connect.
            lines.append(f'proxy returned: http {self.proxy_code}')
        lines.append(f'curl exit code: {self.returncode}')
        curlmsg = (
            ''
            if self.stderr is None
            else self.stderr.decode(errors='replace').strip()
        )
        if curlmsg:
            # Curl error output is generally a single 'curl: (N) blah'
            # line, but be tidy if it ever spans more.
            lines += [f'curl says: {line}' for line in curlmsg.splitlines()]
        hint = CURL_ERROR_HINTS.get(self.returncode)
        if hint is not None:
            lines.append(f'likely cause: {hint}')
        if self.attempts > 1:
            lines.append(f'gave up after {self.attempts} attempts')
        return '\n'.join(f'  {line}' for line in lines)


def _parse_http_codes(rawout: bytes) -> tuple[int | None, int | None]:
    """Pull the (response, proxy-connect) codes out of curl write-out.

    Curl gives us zeros for codes it never got; those become None, as
    does a 200 connect (a healthy tunnel isn't worth mentioning).
    """
    codes: list[int | None] = [None, None]
    vals = rawout.decode(errors='replace').split()
    for i in range(min(len(vals), 2)):
        code = int(vals[i]) if vals[i].isdigit() else 0
        codes[i] = code if code and not (i == 1 and code == 200) else None
    return codes[0], codes[1]


def _download(
    url: str,
    outpath: str,
    *,
    what: str,
    quiet: bool,
    log: Callable[[str], None],
) -> _DownloadFailure | None:
    """Curl a url to a path, retrying transient failures.

    Returns None on success or a _DownloadFailure describing the last
    attempt if we ran out of them. With quiet False we leave curl's
    progress meter visible, which means its stderr can't be captured
    for error output.
    """
    failure: _DownloadFailure | None = None
    delay = DOWNLOAD_RETRY_DELAY

    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        cmd = ['curl', '--fail', '--show-error']
        if quiet:
            cmd.append('--silent')
        # Ask for the http codes so we can tell 'this file is gone' from
        # 'the server is having a moment' (--fail collapses both into
        # exit code 22). http_connect is what a proxy said to our
        # connect request; it's the only code we get when a proxy
        # refuses to tunnel us through.
        wout = '%{http_code} %{http_connect}'
        cmd += ['--write-out', wout, url, '--output', outpath]
        result = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if quiet else None,
        )
        if result.returncode == 0:
            return None

        codes = _parse_http_codes(result.stdout)
        failure = _DownloadFailure(
            url=url,
            returncode=result.returncode,
            http_code=codes[0],
            proxy_code=codes[1],
            stderr=result.stderr,
            attempts=attempt,
        )

        status = failure.status_code
        retryable = result.returncode in CURL_RETRY_CODES or (
            status is not None and status in HTTP_RETRY_CODES
        )
        if not retryable or attempt == DOWNLOAD_ATTEMPTS:
            break

        log(
            f'Download of {what} failed ({failure.summary()});'
            f' retrying in {delay:.0f}s'
            f' (attempt {attempt + 1} of {DOWNLOAD_ATTEMPTS})...'
        )
        time.sleep(delay)
        delay *= 2.0

    assert failure is not None
    return failure


def get_target(path: str, batch: bool, clr: type[efro.terminal.ClrBase]) -> str:
    """Fetch a target path from the cache, downloading if need be."""
    # pylint: disable=too-many-locals
    import tempfile

    from efro.error import CleanError

    output_lines: list[str] = []

    def _log(msg: str) -> None:
        # In batch mode we hand our output back to the client to print;
        # otherwise we print it ourself.
        if batch:
            output_lines.append(msg)
        else:
            print(msg, flush=True)

    local_cache_dir = get_local_cache_dir()

    path = _project_centric_path(path)

    with open(CACHE_MAP_NAME, encoding='utf-8') as infile:
        efrocachemap = json.loads(infile.read())
    if path not in efrocachemap:
        raise RuntimeError(f'Path not found in efrocache: {path}')

    hashval = efrocachemap[path]

    # These used to be url paths but now they're just hashes.
    assert not hashval.startswith('https:')
    assert '/' not in hashval

    # If our hash is 'abcdefghijkl', our subpath is 'ab/cd/efghijkl'.
    subpath = '/'.join([hashval[:2], hashval[2:4], hashval[4:]])

    repo = get_repository_base_url()
    url = f'{repo}/{subpath}'

    local_cache_path = os.path.join(local_cache_dir, subpath)

    # First off: if there's already a file in place, check its hash. If
    # its calced hash matches the hash-map's value for it, we can just
    # update its timestamp and call it a day.
    if os.path.isfile(path):
        existing_hash = get_existing_file_hash(path)
        if existing_hash == hashval:
            os.utime(path, None)
            _log(f'Refreshing from cache: {path}')
            return '\n'.join(output_lines)

    # Ok we need to download the cache file.
    # Ok there's not a valid file in place already. Clear out whatever
    # is there to start with.
    if os.path.exists(path):
        os.remove(path)

    # Now, if we don't have this entry in our local cache, download it.
    if not os.path.exists(local_cache_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            local_cache_dl_path = os.path.join(tmpdir, 'dl')
            _log(f'Downloading: {clr.BLU}{path}{clr.RST}')

            failure = _download(
                url,
                local_cache_dl_path,
                what=f'build file {path}',
                quiet=True,
                log=_log,
            )
            if failure is not None:
                # We prune old cache files on the server, so its
                # possible for one to be trying to build something the
                # server can no longer provide. Try to explain the
                # situation.
                gone = (
                    failure.http_code in {404, 410}
                    if failure.http_code is not None
                    else failure.proxy_code is None and failure.returncode == 22
                )
                if gone:
                    raise CleanError(
                        f'Build file {path} was not found on the server:\n'
                        f'{failure.describe()}\n'
                        'Old build files may no longer be available on the'
                        ' server; make sure you are using a recent commit.\n'
                        'Note that build files will remain available'
                        ' indefinitely once downloaded, even if deleted by'
                        f' the server. So as long as your {local_cache_dir}'
                        ' directory stays intact you should be able to repeat'
                        ' any builds you have run before.'
                    )
                raise CleanError(
                    f'Download failed for build file {path}:\n'
                    f'{failure.describe()}\n'
                    'Check your internet connection (and any'
                    ' proxy/vpn/firewall in the way) and try again.'
                )

            # Ok; cache download finished. Lastly move it in place to be
            # as atomic as possible.
            os.makedirs(os.path.dirname(local_cache_path), exist_ok=True)
            subprocess.run(
                ['mv', local_cache_dl_path, local_cache_path], check=True
            )

    # Ok we should have a valid file in our cache dir at this point.
    # Just expand it to the target path.

    _log(f'Extracting: {path}')

    # Extract and stage the file in a temp dir before doing a final move
    # to the target location to be as atomic as possible.
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(local_cache_path, 'rb') as infileb:
            data = infileb.read()
        header = data[:4]
        if header != CACHE_HEADER:
            raise RuntimeError('Invalid cache header.')
        metalen = data[4]
        metabytes = data[5 : 5 + metalen]
        datac = data[5 + metalen :]
        metajson = metabytes.decode()
        metadata = dataclass_from_json(CacheMetadata, metajson)
        data = zlib.decompress(datac)

        tmppath = os.path.join(tmpdir, 'out')
        with open(tmppath, 'wb') as outfile:
            outfile.write(data)
        if metadata.executable:
            subprocess.run(['chmod', '+x', tmppath], check=True)

        # Ok; we wrote the file. Now move it into its final place.
        os.makedirs(os.path.dirname(path), exist_ok=True)
        subprocess.run(['mv', tmppath, path], check=True)

    if not os.path.exists(path):
        raise RuntimeError(f'File {path} did not wind up as expected.')

    return '\n'.join(output_lines)


def filter_makefile(makefile_dir: str, contents: str) -> str:
    """Filter makefile contents to use efrocache lookups."""

    # '' should give us ''; 'foo/bar' should give us '../..', etc.
    to_proj_root = (
        ''
        if not makefile_dir
        else '/'.join(['..'] * len(makefile_dir.split('/')))
    )

    cachemap = os.path.join(to_proj_root, CACHE_MAP_NAME)
    lines = contents.splitlines()

    if makefile_dir == '':
        # In root Makefile, just use standard pcommandbatch var.
        pcommand = '$(PCOMMANDBATCH)'
    elif makefile_dir == 'src/assets':
        # Currently efrocache_get needs to be run from project-root so
        # we can't just use $(PCOMMANDBATCH); need a special from-root
        # var.
        pcommand = '$(PCOMMANDBATCHFROMROOT)'
    elif makefile_dir == 'src/resources':
        # Not yet enough stuff in resources to justify supporting
        # pcommandbatch there; sticking with regular pcommand for now.
        pcommand = 'tools/pcommand'
    else:
        raise RuntimeError(f"Unsupported makefile_dir: '{makefile_dir}'.")

    # Replace cachable targets with cache lookups.
    while TARGET_TAG in lines:
        index = lines.index(TARGET_TAG)
        endindex = index
        while lines[endindex].strip() != '':
            endindex += 1
        tname = lines[index + 1].split(':')[0]
        del lines[index:endindex]
        lines.insert(index, tname + ': ' + cachemap)
        target = (makefile_dir + '/' + '$@') if makefile_dir else '$@'
        pre = f'cd {to_proj_root} && ' if makefile_dir else ''
        lines.insert(index + 1, f'\t@{pre}{pcommand} efrocache_get {target}')
    return '\n'.join(lines) + '\n'


def _path_from_hash(hashstr: str) -> str:
    return os.path.join(hashstr[:2], hashstr[2:4], hashstr[4:])


def _cache_prefix_for_file(fname: str) -> bytes:
    # pylint: disable=global-statement
    from efrotools.util import is_wsl_windows_build_path

    global _g_cache_prefix_exec
    global _g_cache_prefix_noexec
    global _g_noted_wsl_exec_bits

    # We'll be calling this a lot when checking existing files, so we
    # want it to be efficient. Let's cache the two options there are at
    # the moment.

    executable = os.access(fname, os.X_OK)

    if is_wsl_windows_build_path(os.getcwd()):
        # Currently the filesystem during wsl windows builds tells us
        # everything is executable. Normally this causes us to
        # re-extract most everything which is all non-executable in the
        # cache. So as a band-aid let's just hard-code everything to
        # give a non-executable result here instead so we only have to
        # redundantly extract the few things that ARE executable instead
        # of all the things that aren't.

        # Make ourself aware if this situation ever changes, but say it
        # exactly once; otherwise it repeats for every file we touch and
        # looks like something is badly wrong when nothing is.
        if not executable and not _g_noted_wsl_exec_bits:
            _g_noted_wsl_exec_bits = True
            print(
                'Note: this wsl filesystem reports real executable bits;'
                ' the efrocache exec-bit workaround may no longer be'
                ' needed here. This is harmless; builds are unaffected.'
                ' (silencing further occurrences)'
            )

        executable = False

    if executable:
        if _g_cache_prefix_exec is None:
            metadata = dataclass_to_json(
                CacheMetadata(executable=True)
            ).encode()
            assert len(metadata) < 256
            _g_cache_prefix_exec = (
                CACHE_HEADER + len(metadata).to_bytes() + metadata
            )
        return _g_cache_prefix_exec

    # Ok; non-executable it is.
    metadata = dataclass_to_json(CacheMetadata(executable=False)).encode()
    assert len(metadata) < 256
    _g_cache_prefix_noexec = CACHE_HEADER + len(metadata).to_bytes() + metadata
    return _g_cache_prefix_noexec


def _check_warm_start_entry(entry: tuple[str, str]) -> None:
    # import hashlib

    fname, filehash = entry

    # If the file still matches the hash value we have for it,
    # go ahead and update its timestamp.
    if get_existing_file_hash(fname) == filehash:
        os.utime(fname, None)


def _check_warm_start_entries(entries: list[tuple[str, str]]) -> None:
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        # Converting this to a list pulls results and propagates errors)
        list(executor.map(_check_warm_start_entry, entries))


def warm_start_cache(cachetype: str) -> None:
    """Run a pre-pass on the efrocache to improve efficiency.

    This may fetch an initial cache archive, batch update mod times
    to reflect new cache maps, etc.
    """
    import tempfile

    from efro.error import CleanError

    if cachetype not in {'gui', 'server'}:
        raise ValueError(f"Invalid cachetype '{cachetype}'.")

    base_url = get_repository_base_url()
    local_cache_dir = get_local_cache_dir()

    cachefname = (
        'startercacheserver' if cachetype == 'server' else 'startercache'
    )

    # We maintain starter-cache archives on the staging server, which
    # are simply sets of commonly used recent cache entries compressed
    # into a single archive. If we have no local cache yet we can
    # download and expand this to give us a nice head start and greatly
    # reduce the initial set of individual files we have to fetch
    # (downloading a single compressed archive is much more efficient
    # than downloading thousands).
    if not os.path.exists(local_cache_dir):
        print('Downloading efrocache starter-archive...', flush=True)

        # Download and decompress the starter-cache into a temp dir
        # and then move it into place as our shiny new cache dir.
        with tempfile.TemporaryDirectory() as tmpdir:
            starter_cache_file_path = os.path.join(
                tmpdir, f'{cachefname}.tar.xz'
            )
            # Note: leaving curl's progress meter visible here since
            # this is a big download; that means its error output isn't
            # captured for us, but it lands on the terminal anyway.
            failure = _download(
                f'{base_url}/{cachefname}.tar.xz',
                starter_cache_file_path,
                what='the starter-archive',
                quiet=False,
                log=lambda msg: print(msg, flush=True),
            )
            if failure is not None:
                raise CleanError(
                    'Download of the efrocache starter-archive failed:\n'
                    f'{failure.describe()}\n'
                    'Check your internet connection (and any'
                    ' proxy/vpn/firewall in the way) and try again.'
                )
            print('Decompressing starter-cache...', flush=True)
            subprocess.run(
                ['tar', '--no-same-owner', '-xf', starter_cache_file_path],
                cwd=tmpdir,
                check=True,
            )
            os.makedirs(os.path.dirname(local_cache_dir), exist_ok=True)
            subprocess.run(
                ['mv', os.path.join(tmpdir, 'efrocache'), local_cache_dir],
                check=True,
            )
            print(
                'Starter-cache fetched successfully! (should speed up builds).'
            )

    # In the public project, let's also scan through all project files
    # managed by efrocache and update timestamps on any that we already
    # have the data for to match the latest map. Otherwise those files
    # will update their own timestamps individually the next time they
    # are 'built'. Even though that only takes a fraction of a second
    # per file, it adds up when done for thousands of files each time
    # the cache map changes. It is much more efficient to do it all in
    # one go here.
    #
    # Note to self: it could be nice to put together a lightweight build
    # server system of some sort so we don't have to spin up a full
    # Python process for each and every file we need to touch. In that
    # case, this optimization would probably be unnecessary.
    #
    # UPDATE - We now have that lightweight build system (pcommandbatch)
    # which means individual refreshes are now much less expensive than
    # before, so disabling this for now.
    #
    # UPDATE 2 - I've disabled pcommandbatch by default so flipping this
    # back on for now since it really helps in some cases such as WSL
    # Windows builds which are painfully slow otherwise. Can consider
    # turning the back off again once asset builds have migrated to
    # the cloud asset-package system.
    if bool(True):
        cachemap: dict[str, str]
        with open(CACHE_MAP_NAME, encoding='utf-8') as infile:
            cachemap = json.loads(infile.read())
        assert isinstance(cachemap, dict)
        cachemap_mtime = os.path.getmtime(CACHE_MAP_NAME)
        entries: list[tuple[str, str]] = []
        for fname, filehash in cachemap.items():
            # File hasn't been pulled from cache yet = ignore.
            if not os.path.exists(fname):
                continue

            # File is newer than the cache map = ignore.
            if cachemap_mtime < os.path.getmtime(fname):
                continue

            # Don't have the cache source file for this guy = ignore. This
            # can happen if cache files have been blown away since the last
            # time this was built.
            cachefile = os.path.join(local_cache_dir, _path_from_hash(filehash))
            if not os.path.exists(cachefile):
                continue

            # Ok, add it to the list of files we can potentially update
            # timestamps on once we check its hash.
            entries.append((fname, filehash))

        if entries:
            # Now fire off a multithreaded executor to check hashes and
            # update timestamps.
            _check_warm_start_entries(entries)
