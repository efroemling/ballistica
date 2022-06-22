# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to transferring files/data."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    from pathlib import Path


@ioprepped
@dataclass
class DirectoryManifestFile:
    """Describes metadata and hashes for a file in a manifest."""
    filehash: Annotated[str, IOAttrs('h')]
    filesize: Annotated[int, IOAttrs('s')]


@ioprepped
@dataclass
class DirectoryManifest:
    """Contains a summary of files in a directory."""
    files: Annotated[dict[str, DirectoryManifestFile], IOAttrs('f')]

    _empty_hash: str | None = None

    @classmethod
    def create_from_disk(cls, path: Path) -> DirectoryManifest:
        """Create a manifest from a directory on disk."""
        import hashlib
        from concurrent.futures import ThreadPoolExecutor

        pathstr = str(path)
        paths: list[str] = []

        if path.is_dir():
            # Build the full list of package-relative paths.
            for basename, _dirnames, filenames in os.walk(path):
                for filename in filenames:
                    fullname = os.path.join(basename, filename)
                    assert fullname.startswith(pathstr)
                    paths.append(fullname[len(pathstr) + 1:])
        elif path.exists():
            # Just return a single file entry if path is not a dir.
            paths.append(pathstr)

        def _get_file_info(filepath: str) -> tuple[str, DirectoryManifestFile]:
            sha = hashlib.sha256()
            fullfilepath = os.path.join(pathstr, filepath)
            if not os.path.isfile(fullfilepath):
                raise Exception(f'File not found: "{fullfilepath}"')
            with open(fullfilepath, 'rb') as infile:
                filebytes = infile.read()
                filesize = len(filebytes)
                sha.update(filebytes)
            return (filepath,
                    DirectoryManifestFile(filehash=sha.hexdigest(),
                                          filesize=filesize))

        # Now use all procs to hash the files efficiently.
        cpus = os.cpu_count()
        if cpus is None:
            cpus = 4
        with ThreadPoolExecutor(max_workers=cpus) as executor:
            return cls(files=dict(executor.map(_get_file_info, paths)))

    @classmethod
    def get_empty_hash(cls) -> str:
        """Return the hash for an empty file."""
        if cls._empty_hash is None:
            import hashlib
            sha = hashlib.sha256()
            cls._empty_hash = sha.hexdigest()
        return cls._empty_hash
