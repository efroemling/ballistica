# Released under the MIT License. See LICENSE for details.
#
"""Android APK payload-manifest generation for staged builds.

Android pulls its assets out of the apk at runtime; the staged
``payload_info`` manifest tells the game which files to extract and
their hashes. Split out of :mod:`batools.staging` to keep that module
under the line limit.
"""

import os
import hashlib
from functools import partial


def write_payload_file(assets_root: str, full: bool) -> None:
    """Write the ``payload_info`` manifest for a staged android tree."""
    if not assets_root.endswith('/'):
        assets_root = f'{assets_root}/'

    # Now construct a payload file if we have any files.
    file_list = []
    payload_str = ''
    for root, _subdirs, fnames in os.walk(assets_root):
        for fname in fnames:
            if fname.startswith('.'):
                continue
            if fname == 'payload_info':
                continue
            fpath = os.path.join(root, fname)
            fpathshort = fpath.replace(assets_root, '')
            if ' ' in fpathshort:
                raise RuntimeError(
                    f"Invalid filename (contains spaces): '{fpathshort}'"
                )
            payload_str += f'{fpathshort} {_filehash(fpath)}\n'
            file_list.append(fpathshort)

    payload_path = f'{assets_root}/payload_info'
    if file_list:
        # Write the file count, whether this is a 'full' payload, and
        # finally the file list.
        fullstr = '1' if full else '0'
        payload_str = f'{len(file_list)}\n{fullstr}\n{payload_str}'
        with open(payload_path, 'w', encoding='utf-8') as outfile:
            outfile.write(payload_str)
    else:
        # Remove the payload file; this will cause the game to
        # completely skip the payload processing step.
        if os.path.exists(payload_path):
            os.unlink(payload_path)


def _filehash(filename: str) -> str:
    """Generate a hash for a file."""
    md5 = hashlib.md5()
    with open(filename, mode='rb') as infile:
        for buf in iter(partial(infile.read, 1024), b''):
            md5.update(buf)
    return md5.hexdigest()
