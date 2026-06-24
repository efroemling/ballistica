# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to transferring files/data.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.
"""

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
    """Describes a file in a manifest."""

    hash_sha256: Annotated[str, IOAttrs('h')]
    size: Annotated[int, IOAttrs('s')]


@ioprepped
@dataclass
class DirectoryManifest:
    """Contains a summary of files in a directory."""

    files: Annotated[dict[str, DirectoryManifestFile], IOAttrs('f')]

    # Soft-default added April 2024; can remove eventually once this
    # attr is widespread in client.
    exists: Annotated[bool, IOAttrs('e', soft_default=True)]

    @classmethod
    def create_from_disk(cls, path: Path) -> DirectoryManifest:
        """Create a manifest from a directory on disk."""
        import hashlib
        from concurrent.futures import ThreadPoolExecutor

        pathstr = str(path)

        # Each entry pairs the manifest key (forward-slashed; for a
        # single file the bare path.as_posix() the put-file handler
        # keys on) with the actual on-disk path to hash. Keeping the two
        # separate is what fixes single-file inputs: the dir case joins
        # a relative key back onto pathstr, but doing that to a
        # single-file key (which is the whole path) doubles a relative
        # path up (a/b.png -> a/b.png/a/b.png -> File not found).
        entries: list[tuple[str, str]] = []

        exists = path.exists()

        if path.is_dir():
            # Build the full list of relative paths.
            for basename, _dirnames, filenames in os.walk(path):
                for filename in filenames:
                    fullname = os.path.join(basename, filename)
                    assert fullname.startswith(pathstr)
                    # Make sure we end up with forward slashes no matter
                    # what the os.* stuff above here was using.
                    key = Path(fullname[len(pathstr) + 1 :]).as_posix()
                    entries.append((key, fullname))
        elif exists:
            # Single file: key stays path.as_posix(), but the on-disk
            # path is just the path itself (no join — see above).
            entries.append((path.as_posix(), pathstr))

        def _get_file_info(
            entry: tuple[str, str],
        ) -> tuple[str, DirectoryManifestFile]:
            key, fullfilepath = entry
            sha = hashlib.sha256()
            if not os.path.isfile(fullfilepath):
                raise RuntimeError(f'File not found: "{fullfilepath}".')
            # Stream the file through sha256 to keep peak memory
            # bounded — manifest generation must not load arbitrarily
            # large files into RAM, since the whole point of streaming
            # uploads is to handle files larger than process memory.
            filesize = 0
            with open(fullfilepath, 'rb') as infile:
                for chunk in iter(lambda: infile.read(1024 * 1024), b''):
                    sha.update(chunk)
                    filesize += len(chunk)
            return (
                key,
                DirectoryManifestFile(
                    hash_sha256=sha.hexdigest(),
                    size=filesize,
                ),
            )

        # Now use all procs to hash the files efficiently.
        cpus = os.cpu_count()
        if cpus is None:
            cpus = 4
        with ThreadPoolExecutor(max_workers=cpus) as executor:
            return cls(
                files=dict(executor.map(_get_file_info, entries)),
                exists=exists,
            )

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

    # @classmethod
    # def get_empty_hash(cls) -> str:
    #     """Return the hash for an empty file."""
    #     if cls._empty_hash is None:
    #         import hashlib

    #         sha = hashlib.sha256()
    #         cls._empty_hash = sha.hexdigest()
    #     return cls._empty_hash
