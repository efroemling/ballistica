# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to transferring files/data."""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    pass


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
            # Build the full list of relative paths.
            for basename, _dirnames, filenames in os.walk(path):
                for filename in filenames:
                    fullname = os.path.join(basename, filename)
                    assert fullname.startswith(pathstr)
                    # Make sure we end up with forward slashes no matter
                    # what the os.* stuff above here was using.
                    paths.append(Path(fullname[len(pathstr) + 1 :]).as_posix())
        elif path.exists():
            # Just return a single file entry if path is not a dir.
            paths.append(path.as_posix())

        def _get_file_info(filepath: str) -> tuple[str, DirectoryManifestFile]:
            sha = hashlib.sha256()
            fullfilepath = os.path.join(pathstr, filepath)
            if not os.path.isfile(fullfilepath):
                raise RuntimeError(f'File not found: "{fullfilepath}".')
            with open(fullfilepath, 'rb') as infile:
                filebytes = infile.read()
                filesize = len(filebytes)
                sha.update(filebytes)
            return (
                filepath,
                DirectoryManifestFile(
                    filehash=sha.hexdigest(), filesize=filesize
                ),
            )

        # Now use all procs to hash the files efficiently.
        cpus = os.cpu_count()
        if cpus is None:
            cpus = 4
        with ThreadPoolExecutor(max_workers=cpus) as executor:
            return cls(files=dict(executor.map(_get_file_info, paths)))

    def validate(self) -> None:
        """Log any odd data in the manifest; for debugging."""
        import logging

        for fpath, _fentry in self.files.items():
            # We want to be dealing in only forward slashes; make sure
            # that's the case (wondering if we'll ever see backslashes
            # for escape purposes).
            if '\\' in fpath:
                logging.exception(
                    "Found unusual path in manifest: '%s'.", fpath
                )
                break  # 1 error is enough for now.

    @classmethod
    def get_empty_hash(cls) -> str:
        """Return the hash for an empty file."""
        if cls._empty_hash is None:
            import hashlib

            sha = hashlib.sha256()
            cls._empty_hash = sha.hexdigest()
        return cls._empty_hash
