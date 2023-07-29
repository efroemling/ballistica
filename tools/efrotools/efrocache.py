# Released under the MIT License. See LICENSE for details.
#
"""A simple cloud caching system for making built binaries & assets.

The basic idea here is the ballistica-internal project can flag file
targets in its Makefiles as 'cached', and the public version of those
Makefiles will be filtered to contain cache downloads in place of the
original build commands. Cached files are gathered and uploaded as part
of the pubsync process.
"""

from __future__ import annotations

import os
import json
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
from efro.terminal import Clr

if TYPE_CHECKING:
    pass

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


g_cache_prefix_noexec: bytes | None = None
g_cache_prefix_exec: bytes | None = None


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
    # from efrotools import getprojectconfig
    import efrotools

    pconfig = efrotools.getprojectconfig('.')
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


def get_target(path: str) -> None:
    """Fetch a target path from the cache, downloading if need be."""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    import tempfile

    from efro.error import CleanError

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

    # First off: if there's already a cache file in place, check its
    # hash. If its calced hash matches its path, we can just update its
    # timestamp and call it a day.
    if os.path.isfile(path):
        existing_hash = get_existing_file_hash(path)
        if existing_hash == hashval:
            os.utime(path, None)
            print(f'Refreshing from cache: {path}')
            return

    # Ok we need to download the cache file.
    # Ok there's not a valid file in place already. Clear out whatever
    # is there to start with.
    if os.path.exists(path):
        os.remove(path)

    # Now, if we don't have this entry in our local cache, download it.
    if not os.path.exists(local_cache_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            local_cache_dl_path = os.path.join(tmpdir, 'dl')
            print(f'Downloading: {Clr.BLU}{path}{Clr.RST}')
            result = subprocess.run(
                [
                    'curl',
                    '--fail',
                    '--silent',
                    url,
                    '--output',
                    local_cache_dl_path,
                ],
                check=False,
            )

            # We prune old cache files on the server, so its possible for
            # one to be trying to build something the server can no longer
            # provide. try to explain the situation.
            if result.returncode == 22:
                raise CleanError(
                    'Server gave an error. Old build files may no longer'
                    ' be available on the server; make sure you are using'
                    ' a recent commit.\n'
                    'Note that build files will remain available'
                    ' indefinitely once downloaded, even if deleted by the'
                    f' server. So as long as your {local_cache_dir} directory'
                    ' stays intact you should be able to repeat any builds you'
                    ' have run before.'
                )
            if result.returncode != 0:
                raise CleanError('Download failed; is your internet working?')

            # Ok; cache download finished. Lastly move it in place to be as
            # atomic as possible.
            os.makedirs(os.path.dirname(local_cache_path), exist_ok=True)
            subprocess.run(
                ['mv', local_cache_dl_path, local_cache_path], check=True
            )

    # Ok we should have a valid file in our cache dir at this point.
    # Just expand it to the target path.

    print(f'Extracting: {path}')

    # Extract and stage the file in a temp dir before doing
    # a final move to the target location to be as atomic as possible.
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(local_cache_path, 'rb') as infile:
            data = infile.read()
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
    pcommand = 'tools/pcommand'

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


def update_cache(makefile_dirs: list[str]) -> None:
    """Given a list of directories containing Makefiles, update caches."""

    import multiprocessing

    cpus = multiprocessing.cpu_count()
    fnames1: list[str] = []
    fnames2: list[str] = []
    for path in makefile_dirs:
        cdp = f'cd {path} && ' if path else ''

        # First, make sure all cache files are built.
        mfpath = os.path.join(path, 'Makefile')
        print(f'Building efrocache targets for {Clr.SBLU}{mfpath}{Clr.RST}...')
        subprocess.run(
            f'{cdp}make -j{cpus} efrocache-build', shell=True, check=True
        )

        rawpaths = (
            subprocess.run(
                f'{cdp}make efrocache-list',
                shell=True,
                check=True,
                capture_output=True,
            )
            .stdout.decode()
            .split()
        )

        # Make sure the paths they gave were relative.
        for rawpath in rawpaths:
            if rawpath.startswith('/'):
                raise RuntimeError(
                    f'Invalid path returned for caching '
                    f'(absolute paths not allowed): {rawpath}'
                )

        # Break these into 2 lists, one of which will be included in the
        # starter-cache.
        for rawpath in rawpaths:
            fullpath = _project_centric_path(os.path.join(path, rawpath))

            # The main reason for this cache is to reduce round trips to
            # the staging server for tiny files, so let's include small files
            # only here. For larger stuff its ok to have a request per file..
            if os.path.getsize(fullpath) < 100000:
                fnames1.append(fullpath)
            else:
                fnames2.append(fullpath)

    # Ok, we've got 2 lists of filenames that we need to cache in the cloud.
    # First, however, let's do a big hash of everything and if everything
    # is exactly the same as last time we can skip this step.
    hashes = _gen_complete_state_hashes(fnames1 + fnames2)
    if os.path.isfile(UPLOAD_STATE_CACHE_FILE):
        with open(UPLOAD_STATE_CACHE_FILE, encoding='utf-8') as infile:
            hashes_existing = infile.read()
    else:
        hashes_existing = ''
    if hashes == hashes_existing:
        print(
            f'{Clr.SBLU}Efrocache state unchanged;'
            f' skipping cache push.{Clr.RST}',
            flush=True,
        )
    else:
        _upload_cache(fnames1, fnames2, hashes, hashes_existing)

    print(f'{Clr.SBLU}Efrocache update successful!{Clr.RST}')

    # Write the cache state so we can skip the next run if nothing
    # changes.
    os.makedirs(os.path.dirname(UPLOAD_STATE_CACHE_FILE), exist_ok=True)
    with open(UPLOAD_STATE_CACHE_FILE, 'w', encoding='utf-8') as outfile:
        outfile.write(hashes)


def _upload_cache(
    fnames1: list[str],
    fnames2: list[str],
    hashes_str: str,
    hashes_existing_str: str,
) -> None:
    # First, if we've run before, print the files causing us to re-run:
    if hashes_existing_str != '':
        changed_files: set[str] = set()
        hashes = json.loads(hashes_str)
        hashes_existing = json.loads(hashes_existing_str)
        for fname, ftime in hashes.items():
            if ftime != hashes_existing.get(fname, ''):
                changed_files.add(fname)

        # We've covered modifications and additions; add deletions:
        for fname in hashes_existing:
            if fname not in hashes:
                changed_files.add(fname)
        print(
            f'{Clr.SBLU}Updating efrocache due to'
            f' {len(changed_files)} changes:{Clr.RST}'
        )
        for fname in sorted(changed_files):
            print(f'  {Clr.SBLU}{fname}{Clr.RST}')

    # Now do the thing.
    staging_dir = 'build/efrocache'
    mapping_file = 'build/efrocachemap'
    subprocess.run(['rm', '-rf', staging_dir], check=True)
    subprocess.run(['mkdir', '-p', staging_dir], check=True)

    _write_cache_files(fnames1, fnames2, staging_dir, mapping_file)

    print(
        f'{Clr.SBLU}Starter cache includes {len(fnames1)} items;'
        f' excludes {len(fnames2)}{Clr.RST}'
    )

    # Sync all individual cache files to the staging server.
    print(f'{Clr.SBLU}Pushing cache to staging...{Clr.RST}', flush=True)
    subprocess.run(
        [
            'rsync',
            '--progress',
            '--recursive',
            '--human-readable',
            'build/efrocache/',
            'ubuntu@staging.ballistica.net:files.ballistica.net/cache/ba1/',
        ],
        check=True,
    )

    # Now generate the starter cache on the server..
    subprocess.run(
        [
            'ssh',
            '-oBatchMode=yes',
            '-oStrictHostKeyChecking=yes',
            'ubuntu@staging.ballistica.net',
            'cd files.ballistica.net/cache/ba1 && python3 genstartercache.py',
        ],
        check=True,
    )


def _gen_complete_state_hashes(fnames: list[str]) -> str:
    import hashlib

    def _get_simple_file_hash(fname: str) -> tuple[str, str]:
        md5 = hashlib.md5()
        with open(fname, mode='rb') as infile:
            md5.update(infile.read())
        return fname, md5.hexdigest()

    # Now use all procs to hash the files efficiently.
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        hashes = dict(executor.map(_get_simple_file_hash, fnames))

    return json.dumps(hashes, separators=(',', ':'))


def _write_cache_files(
    fnames1: list[str], fnames2: list[str], staging_dir: str, mapping_file: str
) -> None:
    import functools

    fhashes1: set[str] = set()
    fhashes2: set[str] = set()
    mapping: dict[str, str] = {}
    writecall = functools.partial(_write_cache_file, staging_dir)

    # Do the first set.
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        results = executor.map(writecall, fnames1)
    for result in results:
        # mapping[result[0]] = f'{base_url}/{result[1]}'
        mapping[result[0]] = result[1]
        fhashes1.add(result[2])

    # Now finish up with the second set.
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        results = executor.map(writecall, fnames2)
    for result in results:
        # mapping[result[0]] = f'{base_url}/result[1]'
        mapping[result[0]] = result[1]
        fhashes2.add(result[2])

    # We want the server to have a startercache.tar.xz file which
    # contains the entire first set. It is much more efficient to build
    # that file on the server than it is to build it here and upload the
    # whole thing. ...so let's simply write a script to generate it and
    # upload that.

    # Also let's have the script touch both sets of files so we can use
    # mod-times to prune older files. Otherwise files that never change
    # might have very old mod times.
    script = (
        'import os\n'
        'import pathlib\n'
        'import subprocess\n'
        'fnames = ' + repr(fhashes1) + '\n'
        'fnames2 = ' + repr(fhashes2) + '\n'
        'subprocess.run(["rm", "-rf", "efrocache"], check=True)\n'
        'print("Copying starter cache files...", flush=True)\n'
        'for fname in fnames:\n'
        '    dst = os.path.join("efrocache", fname)\n'
        '    os.makedirs(os.path.dirname(dst), exist_ok=True)\n'
        '    subprocess.run(["cp", fname, dst], check=True)\n'
        'print("Touching full file set...", flush=True)\n'
        'for fname in list(fnames) + list(fnames2):\n'
        '    fpath = pathlib.Path(fname)\n'
        '    assert fpath.exists()\n'
        '    fpath.touch()\n'
        'print("Compressing starter cache archive...", flush=True)\n'
        'subprocess.run(["tar", "-Jcf", "tmp.tar.xz", "efrocache"],'
        ' check=True)\n'
        'subprocess.run(["mv", "tmp.tar.xz", "startercache.tar.xz"],'
        ' check=True)\n'
        'subprocess.run(["rm", "-rf", "efrocache", "genstartercache.py"])\n'
        'print("Starter cache generation complete!", flush=True)\n'
    )

    with open(
        'build/efrocache/genstartercache.py', 'w', encoding='utf-8'
    ) as outfile:
        outfile.write(script)

    with open(mapping_file, 'w', encoding='utf-8') as outfile:
        outfile.write(json.dumps(mapping, indent=2, sort_keys=True))


def _write_cache_file(staging_dir: str, fname: str) -> tuple[str, str, str]:
    import hashlib

    print(f'Caching {fname}')

    prefix = _cache_prefix_for_file(fname)

    with open(fname, 'rb') as infile:
        fdataraw = infile.read()

    # Calc a hash of the prefix plus the raw file contents. We want to
    # hash the *uncompressed* file since we'll need to calc this for
    # lots of existing files when seeing if they need to be updated.

    # Just going with ol' md5 here; we're the only ones creating these
    # so security isn't a concern currently.
    md5 = hashlib.md5()
    md5.update(prefix + fdataraw)
    finalhash = md5.hexdigest()
    hashpath = os.path.join(finalhash[:2], finalhash[2:4], finalhash[4:])
    path = os.path.join(staging_dir, hashpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, 'wb') as outfile:
        outfile.write(prefix + zlib.compress(fdataraw))

    return fname, finalhash, hashpath


def _cache_prefix_for_file(fname: str) -> bytes:
    # pylint: disable=global-statement
    global g_cache_prefix_exec
    global g_cache_prefix_noexec

    # We'll be calling this a lot when checking existing files, so we
    # want it to be efficient. Let's cache the two options there are at
    # the moment.
    executable = os.access(fname, os.X_OK)
    if executable:
        if g_cache_prefix_exec is None:
            metadata = dataclass_to_json(
                CacheMetadata(executable=True)
            ).encode()
            assert len(metadata) < 256
            g_cache_prefix_exec = (
                CACHE_HEADER + len(metadata).to_bytes() + metadata
            )
        return g_cache_prefix_exec

    # Ok; non-executable it is.
    metadata = dataclass_to_json(CacheMetadata(executable=False)).encode()
    assert len(metadata) < 256
    g_cache_prefix_noexec = CACHE_HEADER + len(metadata).to_bytes() + metadata
    return g_cache_prefix_noexec


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


def warm_start_cache() -> None:
    """Run a pre-pass on the efrocache to improve efficiency."""
    import tempfile

    base_url = get_repository_base_url()
    local_cache_dir = get_local_cache_dir()

    # We maintain a starter archive on the staging server, which is simply
    # a set of commonly used recent cache entries compressed into a
    # single archive. If we have no local cache yet we can download and
    # expand this to give us a nice head start and greatly reduce the
    # initial set of individual files we have to fetch. (downloading a
    # single compressed archive is much more efficient than downloading
    # thousands)
    if not os.path.exists(local_cache_dir):
        print('Downloading efrocache starter-archive...', flush=True)

        # Download and decompress the starter-cache into a temp dir
        # and then move it into place as our shiny new cache dir.
        with tempfile.TemporaryDirectory() as tmpdir:
            starter_cache_file_path = os.path.join(
                tmpdir, 'startercache.tar.xz'
            )
            subprocess.run(
                [
                    'curl',
                    '--fail',
                    f'{base_url}/startercache.tar.xz',
                    '--output',
                    starter_cache_file_path,
                ],
                check=True,
            )
            print('Decompressing starter-cache...', flush=True)
            subprocess.run(
                ['tar', '-xf', starter_cache_file_path], cwd=tmpdir, check=True
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
    cachemap: dict[str, str]
    with open(CACHE_MAP_NAME, encoding='utf-8') as infile:
        cachemap = json.loads(infile.read())
    assert isinstance(cachemap, dict)
    cachemap_mtime = os.path.getmtime(CACHE_MAP_NAME)
    entries: list[tuple[str, str]] = []
    for fname, url in cachemap.items():
        # File hasn't been pulled from cache yet = ignore.
        if not os.path.exists(fname):
            continue

        # File is newer than the cache map = ignore.
        if cachemap_mtime < os.path.getmtime(fname):
            continue

        # Don't have the cache source file for this guy = ignore.
        cachefile = local_cache_dir + '/' + '/'.join(url.split('/')[-3:])
        if not os.path.exists(cachefile):
            continue

        # Ok, add it to the list of files we can potentially update
        # timestamps on once we check its hash.
        filehash = ''.join(url.split('/')[-3:])
        entries.append((fname, filehash))

    if entries:
        # Now fire off a multithreaded executor to check hashes and
        # update timestamps.
        _check_warm_start_entries(entries)
