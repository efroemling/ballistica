# Copyright (c) 2011-2019 Eric Froemling
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
"""A simple cloud caching system for making built binaries/assets available."""

from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Dict

TARGET_TAG = '#__EFROCACHE_TARGET__'
STRIP_BEGIN_TAG = '#__EFROCACHE_STRIP_BEGIN__'
STRIP_END_TAG = '#__EFROCACHE_STRIP_END__'


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
    import json
    from efrotools import run
    with open('.efrocachemap') as infile:
        efrocachemap = json.loads(infile.read())
    if path not in efrocachemap:
        raise RuntimeError(f'Path not found in efrocache: {path}')
    url = efrocachemap[path]
    subpath = '/'.join(url.split('/')[-3:])
    local_cache_path = os.path.join('.efrocache', subpath)
    local_cache_path_dl = local_cache_path + '.download'
    hashval = ''.join(subpath.split('/'))

    # First off: if there's already a file in place, check its hash.
    # If it matches the cache, we can just update its timestamp and
    # call it a day.
    if os.path.isfile(path):
        existing_hash = get_file_hash(path)
        if existing_hash == hashval:
            print('FOUND VALID FILE; TOUCHING')
            run(f'touch {path}')
            return

    # Ok there's not a valid file in place already.
    # Clear out whatever is there to start with.
    if os.path.exists(path):
        os.unlink(path)

    # Now if we don't have this entry in our local cache,
    # download it.
    if not os.path.exists(local_cache_path):
        os.makedirs(os.path.dirname(local_cache_path), exist_ok=True)
        print('Downloading:', path)
        run(f'curl {url} > {local_cache_path_dl}')
        run(f'mv {local_cache_path_dl} {local_cache_path}')

    # Ok we should have a valid .tar.gz file in our cache dir at this point.
    # Just expand it and it get placed wherever it belongs.
    run(f'tar -zxf {local_cache_path}')

    # The file will wind up with the timestamp it was compressed with,
    # so let's update its timestamp or else it will still be considered
    # dirty.
    run(f'touch {path}')
    if not os.path.exists(path):
        raise RuntimeError(f'File {path} did not wind up as expected.')


def filter_makefile(makefile_dir: str, contents: str) -> str:
    """Filter makefile contents to use efrocache lookups."""
    cachemap = '$(PROJ_DIR)/.efrocachemap'
    lines = contents.splitlines()
    snippets = 'tools/snippets'

    # Strip out parts they don't want.
    while STRIP_BEGIN_TAG in lines:
        index = lines.index(TARGET_TAG)
        endindex = index
        while lines[endindex] != STRIP_END_TAG:
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
        pre = 'cd $(PROJ_DIR) && ' if makefile_dir else ''
        lines.insert(index + 1, f'\t{pre}{snippets} efrocache_get {target}')
    return '\n'.join(lines) + '\n'


def update_cache(makefile_dirs: List[str]) -> None:
    """Given a list of directories containing makefiles, update caches."""

    import multiprocessing
    from efrotools import run
    cpus = multiprocessing.cpu_count()
    fnames: List[str] = []
    for path in makefile_dirs:
        # First, update things..
        cdp = f'cd {path} && ' if path else ''
        subprocess.run(f'{cdp}make -j{cpus} efrocache_build',
                       shell=True,
                       check=True)
        # Now get the list of them.
        fnames += [
            os.path.join(path, s) for s in subprocess.run(
                f'{cdp}make efrocache_list',
                shell=True,
                check=True,
                capture_output=True).stdout.decode().split()
        ]
    staging_dir = 'build/efrocache'
    mapping_file = 'build/efrocachemap'
    run(f'rm -rf {staging_dir}')
    run(f'mkdir -p {staging_dir}')

    _write_cache_files(fnames, staging_dir, mapping_file)

    # Push what we just wrote to the staging server
    print('Pushing cache to staging...', flush=True)
    run('rsync --recursive build/efrocache/'
        ' ubuntu@ballistica.net:files.ballistica.net/cache/ba1/')

    print(f'Cache update successful!')


def _write_cache_files(fnames: List[str], staging_dir: str,
                       mapping_file: str) -> None:
    from efrotools import run
    import hashlib
    import json
    mapping: Dict[str, str] = {}
    baseurl = 'https://files.ballistica.net/cache/ba1/'
    for fname in fnames:

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

        # Fancy pipe stuff which will give us deterministic
        # tar.gz files (no embedded timestamps)
        run(f'tar cf - {fname} | gzip -n > {path}')
        mapping[fname] = baseurl + hashpath
    with open(mapping_file, 'w') as outfile:
        outfile.write(json.dumps(mapping, indent=2, sort_keys=True))
