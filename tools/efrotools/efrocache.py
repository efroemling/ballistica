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


def get_target(path: str, batch: bool, clr: type[efro.terminal.ClrBase]) -> str:
    """Fetch a target path from the cache, downloading if need be."""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    import tempfile

    from efro.error import CleanError

    output_lines: list[str] = []

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
            msg = f'Refreshing from cache: {path}'
            if batch:
                output_lines.append(msg)
            else:
                print(msg)
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
            msg = f'Downloading: {clr.BLU}{path}{clr.RST}'
            if batch:
                output_lines.append(msg)
            else:
                print(msg)
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

            # Ok; cache download finished. Lastly move it in place to be
            # as atomic as possible.
            os.makedirs(os.path.dirname(local_cache_path), exist_ok=True)
            subprocess.run(
                ['mv', local_cache_dl_path, local_cache_path], check=True
            )

    # Ok we should have a valid file in our cache dir at this point.
    # Just expand it to the target path.

    msg = f'Extracting: {path}'
    if batch:
        output_lines.append(msg)
    else:
        print(msg)

    # Extract and stage the file in a temp dir before doing a final move
    # to the target location to be as atomic as possible.
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


def update_cache(makefile_dirs: list[str]) -> None:
    """Given a list of directories containing Makefiles, update caches."""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches

    import multiprocessing

    cpus = multiprocessing.cpu_count()

    # Build lists of all cached paths as well as the subsets going into
    # our starter caches.
    fnames_starter_gui: list[str] = []
    fnames_starter_server: list[str] = []
    fnames_all: list[str] = []

    # If a path contains any of these substrings it will always be included
    # in starter caches.
    starter_cache_always_include_paths = {
        'build/assets/ba_data/fonts',
        'build/assets/ba_data/data',
        'build/assets/ba_data/python',
        'build/assets/ba_data/python-site-packages',
        'build/assets/ba_data/meshes',
    }

    # Never add binaries to starter caches since those are specific to
    # one platform/architecture; we should always download those
    # as-needed.
    never_add_to_starter_endings = {
        '.a',
        '.dll',
        '.lib',
        '.exe',
        '.pdb',
        '.so',
        '.pyd',
    }

    # We do include model dirs for server starters but want to filter out
    # display meshes there.
    never_add_to_starter_endings_server = {'.bob'}

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

        for rawpath in rawpaths:
            fullpath = _project_centric_path(os.path.join(path, rawpath))

            # Always add to our full list.
            fnames_all.append(fullpath)

            # Now selectively add to starter cache lists.

            always_include = False

            if any(p in fullpath for p in starter_cache_always_include_paths):
                always_include = True

            # Always keep certain file types out of starter caches.
            if any(
                fullpath.endswith(ending)
                for ending in never_add_to_starter_endings
            ):
                continue

            # Keep big files out of starter caches (unless flagged as
            # always-include). The main benefits of starter-caches is
            # that we can reduce the overhead for downloading individual
            # tiny files by grabbing them all at once, but that
            # advantage diminishes as the files get bigger. And not all
            # platforms will use all files, so it generally more
            # efficient to grab bigger ones as needed.
            if os.path.getsize(fullpath) > 50_000 and not always_include:
                continue

            # Gui starter gets everything that made it this far.
            fnames_starter_gui.append(fullpath)

            # Server starter cuts out everything not explicitly
            # always-included.
            if not always_include:
                continue

            # Server starter also exclude some things from within
            # always-included dirs.
            if any(
                fullpath.endswith(ending)
                for ending in never_add_to_starter_endings_server
            ):
                continue

            # If it made it this far, add it to the server cache.
            fnames_starter_server.append(fullpath)

    # Ok, we've got a big list of filenames we need to cache in the
    # cloud. First, however, let's do a big hash of everything and if
    # everything is exactly the same as last time we can skip this step.
    hashes = _gen_complete_state_hashes(fnames_all)
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
        _update_cloud_cache(
            fnames_starter_gui,
            fnames_starter_server,
            fnames_all,
            hashes,
            hashes_existing,
        )

    print(f'{Clr.SBLU}Efrocache update successful!{Clr.RST}')

    # Write the cache state so we can skip the next run if nothing
    # changes.
    os.makedirs(os.path.dirname(UPLOAD_STATE_CACHE_FILE), exist_ok=True)
    with open(UPLOAD_STATE_CACHE_FILE, 'w', encoding='utf-8') as outfile:
        outfile.write(hashes)


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


def _update_cloud_cache(
    fnames_starter_gui: list[str],
    fnames_starter_server: list[str],
    fnames_all: list[str],
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

        # We've covered modifications and additions; add deletions.
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

    _gather_cache_files(
        fnames_starter_gui,
        fnames_starter_server,
        fnames_all,
        staging_dir,
        mapping_file,
    )

    print(
        f'{Clr.SBLU}Starter gui cache includes {len(fnames_starter_gui)} items;'
        f' excludes {len(fnames_all) - len(fnames_starter_gui)}{Clr.RST}'
    )
    print(
        f'{Clr.SBLU}Starter server cache includes'
        f' {len(fnames_starter_server)} items;'
        f' excludes {len(fnames_all) - len(fnames_starter_server)}{Clr.RST}'
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

    # Now generate the starter cache on the server.
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


def _gather_cache_files(
    fnames_starter_gui: list[str],
    fnames_starter_server: list[str],
    fnames_all: list[str],
    staging_dir: str,
    mapping_file: str,
) -> None:
    # pylint: disable=too-many-locals
    import functools

    fhashpaths_all: set[str] = set()
    names_to_hashes: dict[str, str] = {}
    names_to_hashpaths: dict[str, str] = {}
    writecall = functools.partial(_write_cache_file, staging_dir)

    # Calc hashes and hash-paths for all cache files.
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        for fname, fhash, fhashpath in executor.map(writecall, fnames_all):
            names_to_hashes[fname] = fhash
            names_to_hashpaths[fname] = fhashpath
            fhashpaths_all.add(fhashpath)

    # Now calc hashpaths for our starter file sets.
    fhashpaths_starter_gui: set[str] = set()
    for fname in fnames_starter_gui:
        fhashpaths_starter_gui.add(names_to_hashpaths[fname])
    fhashpaths_starter_server: set[str] = set()
    for fname in fnames_starter_server:
        fhashpaths_starter_server.add(names_to_hashpaths[fname])

    # We want the server to have a startercache(server).tar.xz files
    # which contain the entire subsets we were passed. It is much more
    # efficient to build those files on the server than it is to build
    # them here and upload the whole thing. ...so let's simply write a
    # script to generate them and upload that.

    # Also let's have the script touch the full set of files we're still
    # using so we can use mod-times to prune unused ones eventually.
    # Otherwise files that we're still using but which never change
    # might have very old mod times.
    script = (
        'import os\n'
        'import pathlib\n'
        'import subprocess\n'
        f'fnames_starter_gui = {repr(fhashpaths_starter_gui)}\n'
        f'fnames_starter_server = {repr(fhashpaths_starter_server)}\n'
        f'fnames_all = {repr(fhashpaths_all)}\n'
        'print("Updating modtimes on all current cache files...", flush=True)\n'
        'for fname in fnames_all:\n'
        '    fpath = pathlib.Path(fname)\n'
        '    assert fpath.exists()\n'
        '    fpath.touch()\n'
        'for scname, scarchivename, fnames_starter in [\n'
        '      ("gui", "startercache", fnames_starter_gui),\n'
        '      ("server", "startercacheserver", fnames_starter_server)]:\n'
        '    print(f"Gathering {scname} starter-cache files...", flush=True)\n'
        '    subprocess.run(["rm", "-rf", "efrocache"], check=True)\n'
        '    for fname in fnames_starter:\n'
        '        dst = os.path.join("efrocache", fname)\n'
        '        os.makedirs(os.path.dirname(dst), exist_ok=True)\n'
        '        subprocess.run(["cp", fname, dst], check=True)\n'
        '    print(f"Compressing {scname} starter-cache archive...",'
        ' flush=True)\n'
        '    subprocess.run(["tar", "-Jcf", "tmp.tar.xz", "efrocache"],'
        ' check=True)\n'
        '    subprocess.run(["mv", "tmp.tar.xz", f"{scarchivename}.tar.xz"],'
        ' check=True)\n'
        '    subprocess.run(["rm", "-rf", "efrocache"], check=True)\n'
        '    print(scname.capitalize() + "starter-cache generation complete!",'
        ' flush=True)\n'
        'subprocess.run(["rm", "-rf", "genstartercache.py"])\n'
    )

    with open(
        'build/efrocache/genstartercache.py', 'w', encoding='utf-8'
    ) as outfile:
        outfile.write(script)

    with open(mapping_file, 'w', encoding='utf-8') as outfile:
        outfile.write(json.dumps(names_to_hashes, indent=2, sort_keys=True))


def _path_from_hash(hashstr: str) -> str:
    return os.path.join(hashstr[:2], hashstr[2:4], hashstr[4:])


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
    hashpath = _path_from_hash(finalhash)
    path = os.path.join(staging_dir, hashpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, 'wb') as outfile:
        outfile.write(prefix + zlib.compress(fdataraw))

    return fname, finalhash, hashpath


def _cache_prefix_for_file(fname: str) -> bytes:
    # pylint: disable=global-statement
    from efrotools.util import is_wsl_windows_build_path

    global g_cache_prefix_exec
    global g_cache_prefix_noexec

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

        # Make ourself aware if this situation ever changes.
        if not executable:
            print('GOT WSL PATH NON-EXECUTABLE; NOT EXPECTED')

        executable = False

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


def warm_start_cache(cachetype: str) -> None:
    """Run a pre-pass on the efrocache to improve efficiency.

    This may fetch an initial cache archive, batch update mod times
    to reflect new cache maps, etc.
    """
    import tempfile

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
            subprocess.run(
                [
                    'curl',
                    '--fail',
                    f'{base_url}/{cachefname}.tar.xz',
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
