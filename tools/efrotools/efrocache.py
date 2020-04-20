# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""A simple cloud caching system for making built binaries/assets available.

The basic idea here is the ballistica-internal project can flag file targets
in its Makefiles as 'cached', and the public version of those Makefiles will
be filtered to contain cache downloads in place of the original build commands.
Cached files are gathered and uploaded as part of the pubsync process.
"""

from __future__ import annotations

import os
import subprocess
import json
from typing import TYPE_CHECKING
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor

if TYPE_CHECKING:
    from typing import List, Dict, Tuple, Set

CLRHDR = '\033[95m'  # Header.
CLRGRN = '\033[92m'  # Green.
CLRBLU = '\033[94m'  # Glue.
CLRRED = '\033[91m'  # Red.
CLREND = '\033[0m'  # End.

BASE_URL = 'https://files.ballistica.net/cache/ba1/'

TARGET_TAG = '#__EFROCACHE_TARGET__'
STRIP_BEGIN_TAG = '#__EFROCACHE_STRIP_BEGIN__'
STRIP_END_TAG = '#__EFROCACHE_STRIP_END__'

CACHE_DIR_NAME = '.efrocache'
CACHE_MAP_NAME = '.efrocachemap'

UPLOAD_STATE_CACHE_FILE = '.cache/efrocache_upload_state'


def get_file_hash(path: str) -> str:
    """Return the hash used for caching.

    This incorporates the file contents as well as its path.
    """
    import hashlib
    md5 = hashlib.md5()
    with open(path, 'rb') as infile:
        md5.update(infile.read())
    md5.update(path.encode())
    return md5.hexdigest()


def get_target(path: str) -> None:
    """Fetch a target path from the cache, downloading if need be."""

    from efrotools import run
    with open(CACHE_MAP_NAME) as infile:
        efrocachemap = json.loads(infile.read())
    if path not in efrocachemap:
        raise RuntimeError(f'Path not found in efrocache: {path}')
    url = efrocachemap[path]
    subpath = '/'.join(url.split('/')[-3:])
    local_cache_path = os.path.join(CACHE_DIR_NAME, subpath)
    local_cache_path_dl = local_cache_path + '.download'
    hashval = ''.join(subpath.split('/'))

    # First off: if there's already a file in place, check its hash.
    # If it matches the cache, we can just update its timestamp and
    # call it a day.
    if os.path.isfile(path):
        existing_hash = get_file_hash(path)
        if existing_hash == hashval:
            os.utime(path, None)
            print(f'Refreshing from cache: {path}')
            return

    # Ok there's not a valid file in place already.
    # Clear out whatever is there to start with.
    if os.path.exists(path):
        os.unlink(path)

    # Now if we don't have this entry in our local cache,
    # download it.
    if not os.path.exists(local_cache_path):
        os.makedirs(os.path.dirname(local_cache_path), exist_ok=True)
        print(f'Downloading: {CLRBLU}{path}{CLREND}')
        run(f'curl --silent {url} > {local_cache_path_dl}')
        run(f'mv {local_cache_path_dl} {local_cache_path}')

    # Ok we should have a valid .tar.gz file in our cache dir at this point.
    # Just expand it and it get placed wherever it belongs.
    print(f'Extracting: {path}')
    run(f'tar -zxf {local_cache_path}')

    # The file will wind up with the timestamp it was compressed with,
    # so let's update its timestamp or else it will still be considered
    # dirty.
    run(f'touch {path}')
    if not os.path.exists(path):
        raise RuntimeError(f'File {path} did not wind up as expected.')


def filter_makefile(makefile_dir: str, contents: str) -> str:
    """Filter makefile contents to use efrocache lookups."""

    if makefile_dir:
        # Assuming just one level deep at the moment; can revisit later.
        assert '/' not in makefile_dir
        to_proj_root = '..'
    else:
        to_proj_root = ''

    cachemap = os.path.join(to_proj_root, CACHE_MAP_NAME)
    lines = contents.splitlines()
    snippets = 'tools/snippets'

    # Strip out parts they don't want.
    while STRIP_BEGIN_TAG in lines:
        index = lines.index(STRIP_BEGIN_TAG)
        endindex = index
        while lines[endindex] != STRIP_END_TAG:
            endindex += 1

        # If the line after us is blank, include it too to keep spacing clean.
        if not lines[endindex + 1].strip():
            endindex += 1

        del lines[index:endindex + 1]

    # Replace cachable targets with cache lookups
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
        lines.insert(index + 1, f'\t@{pre}{snippets} efrocache_get {target}')
    return '\n'.join(lines) + '\n'


def update_cache(makefile_dirs: List[str]) -> None:
    """Given a list of directories containing Makefiles, update caches."""

    import multiprocessing
    cpus = multiprocessing.cpu_count()
    fnames1: List[str] = []
    fnames2: List[str] = []
    for path in makefile_dirs:
        cdp = f'cd {path} && ' if path else ''

        # First, make sure all cache files are built.
        mfpath = os.path.join(path, 'Makefile')
        print(f'Building efrocache targets for {CLRBLU}{mfpath}{CLREND}...')
        subprocess.run(f'{cdp}make -j{cpus} efrocache-build',
                       shell=True,
                       check=True)

        rawpaths = subprocess.run(f'{cdp}make efrocache-list',
                                  shell=True,
                                  check=True,
                                  capture_output=True).stdout.decode().split()

        # Make sure the paths they gave were relative.
        for rawpath in rawpaths:
            if rawpath.startswith('/'):
                raise RuntimeError(f'Invalid path returned for caching '
                                   f'(absolute paths not allowed): {rawpath}')

        # Break these into 2 lists, one of which will be included in the
        # starter-cache.
        for rawpath in rawpaths:
            fullpath = os.path.join(path, rawpath)

            # The main reason for this cache is to reduce round trips to
            # the staging server for tiny files, so let's include small files
            # only here. For larger stuff its ok to have a request per file..
            if os.path.getsize(fullpath) < 100000:
                fnames1.append(fullpath)
            else:
                fnames2.append(fullpath)

    # Ok, we've got 2 lists of filenames that we need to cache in the cloud.
    # First, however, let's look up modtimes for everything and if everything
    # is exactly the same as last time we can skip this step.
    hashes = _gen_hashes(fnames1 + fnames2)
    if os.path.isfile(UPLOAD_STATE_CACHE_FILE):
        with open(UPLOAD_STATE_CACHE_FILE) as infile:
            hashes_existing = infile.read()
    else:
        hashes_existing = ''
    if hashes == hashes_existing:
        print(
            f'{CLRBLU}Efrocache state unchanged;'
            f' skipping cache push.{CLREND}',
            flush=True)
    else:
        _upload_cache(fnames1, fnames2, hashes, hashes_existing)

    print(f'{CLRBLU}Efrocache update successful!{CLREND}')

    # Write the cache state so we can skip the next run if nothing changes.
    os.makedirs(os.path.dirname(UPLOAD_STATE_CACHE_FILE), exist_ok=True)
    with open(UPLOAD_STATE_CACHE_FILE, 'w') as outfile:
        outfile.write(hashes)


def _upload_cache(fnames1: List[str], fnames2: List[str], hashes_str: str,
                  hashes_existing_str: str) -> None:
    from efrotools import run

    # First, if we've run before, print the files causing us to re-run:
    if hashes_existing_str != '':
        changed_files: Set[str] = set()
        hashes = json.loads(hashes_str)
        hashes_existing = json.loads(hashes_existing_str)
        for fname, ftime in hashes.items():
            if ftime != hashes_existing.get(fname, ''):
                changed_files.add(fname)

        # We've covered modifications and additions; add deletions:
        for fname in hashes_existing:
            if fname not in hashes:
                changed_files.add(fname)
        print(f'{CLRBLU}Updating efrocache due to'
              f' {len(changed_files)} changes:{CLREND}')
        for fname in sorted(changed_files):
            print(f'  {CLRBLU}{fname}{CLREND}')

    # Now do the thing.
    staging_dir = 'build/efrocache'
    mapping_file = 'build/efrocachemap'
    run(f'rm -rf {staging_dir}')
    run(f'mkdir -p {staging_dir}')

    _write_cache_files(fnames1, fnames2, staging_dir, mapping_file)

    print(f"{CLRBLU}Starter cache includes {len(fnames1)} items;"
          f" excludes {len(fnames2)}{CLREND}")

    # Sync all individual cache files to the staging server.
    print(f'{CLRBLU}Pushing cache to staging...{CLREND}', flush=True)
    run('rsync --progress --recursive build/efrocache/'
        ' ubuntu@ballistica.net:files.ballistica.net/cache/ba1/')

    # Now generate the starter cache on the server..
    run('ssh -oBatchMode=yes -oStrictHostKeyChecking=yes ubuntu@ballistica.net'
        ' "cd files.ballistica.net/cache/ba1 && python3 genstartercache.py"')


def _gen_hashes(fnames: List[str]) -> str:
    import hashlib

    def _get_file_hash(fname: str) -> Tuple[str, str]:
        md5 = hashlib.md5()
        with open(fname, mode='rb') as infile:
            md5.update(infile.read())
        return fname, md5.hexdigest()

    # Now use all procs to hash the files efficiently.
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        hashes = dict(executor.map(_get_file_hash, fnames))

    return json.dumps(hashes, separators=(',', ':'))


def _write_cache_files(fnames1: List[str], fnames2: List[str],
                       staging_dir: str, mapping_file: str) -> None:
    fhashes1: Set[str] = set()
    import functools
    mapping: Dict[str, str] = {}
    call = functools.partial(_write_cache_file, staging_dir)

    # Do the first set.
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        results = executor.map(call, fnames1)
    for result in results:
        mapping[result[0]] = BASE_URL + result[1]
        fhashes1.add(result[1])

    # We want the server to have a startercache.tar.xz file which contains
    # this entire first set. It is much more efficient to build that file
    # on the server than it is to build it here and upload the whole thing.
    # ...so let's simply write a script to generate it and upload that.

    script = (
        'import os\n'
        'import subprocess\n'
        'fnames = ' + repr(fhashes1) + '\n'
        'subprocess.run(["rm", "-rf", "efrocache"], check=True)\n'
        'print("Copying starter cache files...", flush=True)\n'
        'for fname in fnames:\n'
        '    dst = os.path.join("efrocache", fname)\n'
        '    os.makedirs(os.path.dirname(dst), exist_ok=True)\n'
        '    subprocess.run(["cp", fname, dst], check=True)\n'
        'print("Compressing starter cache archive...", flush=True)\n'
        'subprocess.run(["tar", "-Jcf", "tmp.tar.xz", "efrocache"],'
        ' check=True)\n'
        'subprocess.run(["mv", "tmp.tar.xz", "startercache.tar.xz"],'
        ' check=True)\n'
        'subprocess.run(["rm", "-rf", "efrocache", "genstartercache.py"])\n'
        'print("Starter cache generation complete!", flush=True)\n')

    with open('build/efrocache/genstartercache.py', 'w') as outfile:
        outfile.write(script)

    # Now finish up with the second set.
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        results = executor.map(call, fnames2)
        for result in results:
            mapping[result[0]] = BASE_URL + result[1]

    with open(mapping_file, 'w') as outfile:
        outfile.write(json.dumps(mapping, indent=2, sort_keys=True))


def _write_cache_file(staging_dir: str, fname: str) -> Tuple[str, str]:
    import hashlib
    from efrotools import run
    print(f'Caching {fname}')
    if ' ' in fname:
        raise RuntimeError('Spaces in paths not supported.')

    # Just going with ol' md5 here; we're the only ones creating these so
    # security isn't a concern.
    md5 = hashlib.md5()
    with open(fname, 'rb') as infile:
        md5.update(infile.read())
    md5.update(fname.encode())
    finalhash = md5.hexdigest()
    hashpath = os.path.join(finalhash[:2], finalhash[2:4], finalhash[4:])
    path = os.path.join(staging_dir, hashpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Fancy pipe stuff which will give us deterministic tar.gz files
    # with no embedded timestamps.
    # Note: The 'COPYFILE_DISABLE' prevents mac tar from adding
    # file attributes/resource-forks to the archive as as ._filename.
    run(f'COPYFILE_DISABLE=1 tar cf - {fname} | gzip -n > {path}')
    return fname, hashpath


def _check_warm_start_entry(entry: Tuple[str, str]) -> None:
    import hashlib
    fname, filehash = entry
    md5 = hashlib.md5()
    with open(fname, 'rb') as infile:
        md5.update(infile.read())
    md5.update(fname.encode())
    finalhash = md5.hexdigest()

    # If the file still matches the hash value we have for it,
    # go ahead and update its timestamp.
    if finalhash == filehash:
        os.utime(fname, None)


def _check_warm_start_entries(entries: List[Tuple[str, str]]) -> None:
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        # Converting this to a list pulls results and propagates errors)
        list(executor.map(_check_warm_start_entry, entries))


def warm_start_cache() -> None:
    """Run a pre-pass on the efrocache to improve efficiency."""
    from efrotools import run

    # We maintain a starter-cache on the staging server, which
    # is simply the latest set of cache entries compressed into a single
    # compressed archive. If we have no local cache yet we can download
    # and expand this to give us a nice head start and greatly reduce
    # the initial set of individual files we have to fetch.
    # (downloading a single compressed archive is much more efficient than
    # downloading thousands)
    if not os.path.exists(CACHE_DIR_NAME):
        print('Downloading asset starter-cache...', flush=True)
        run(f'curl {BASE_URL}startercache.tar.xz > startercache.tar.xz')
        print('Decompressing starter-cache...', flush=True)
        run('tar -xf startercache.tar.xz')
        run(f'mv efrocache {CACHE_DIR_NAME}')
        run(f'rm startercache.tar.xz')
        print('Starter-cache fetched successfully!'
              ' (should speed up asset builds)')

    # In the public build, let's scan through all files managed by
    # efrocache and update any with timestamps older than the latest
    # cache-map that we already have the data for.
    # Otherwise those files will update individually the next time
    # they are 'built'. Even though that only takes a fraction of a
    # second per file, it adds up when done for thousands of assets
    # each time the cache map changes. It is much more efficient to do
    # it in one go here.
    cachemap: Dict[str, str]
    with open(CACHE_MAP_NAME) as infile:
        cachemap = json.loads(infile.read())
    assert isinstance(cachemap, dict)
    cachemap_mtime = os.path.getmtime(CACHE_MAP_NAME)
    entries: List[Tuple[str, str]] = []
    for fname, url in cachemap.items():

        # File hasn't been pulled from cache yet = ignore.
        if not os.path.exists(fname):
            continue

        # File is newer than the cache map = ignore.
        if cachemap_mtime < os.path.getmtime(fname):
            continue

        # Don't have the cache source file for this guy = ignore.
        cachefile = CACHE_DIR_NAME + '/' + '/'.join(url.split('/')[-3:])
        if not os.path.exists(cachefile):
            continue

        # Ok, add it to the list of files we can potentially update timestamps
        # on once we check its hash.
        filehash = ''.join(url.split('/')[-3:])
        entries.append((fname, filehash))

    if entries:
        # Now fire off a multithreaded executor to check hashes and update
        # timestamps.
        _check_warm_start_entries(entries)
