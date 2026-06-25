# Released under the MIT License. See LICENSE for details.
"""Zstandard dictionaries for compressing display-mesh (``.bob``) data.

These dictionaries are trained on the corpus of display-mesh blobs and
substantially improve zstd compression of individual meshes (small
files that share a lot of structure). They live in ``bacommon`` so that
both server components (which compress meshes on store) and client
components (which decompress them on load) load identical dictionary
bytes.

Dictionaries are immutable and versioned: never mutate an existing
``.dict`` file -- add a new version instead, so blobs compressed with an
older dictionary remain decompressable. Whatever stores a compressed
blob must record which dictionary version produced it.
"""

from functools import lru_cache


@lru_cache(maxsize=None)
def display_mesh_dict_v1() -> bytes:
    """Return the v1 zstd dictionary for display-mesh (``.bob``) data.

    The dictionary is read from the bundled data file on first call and
    cached for the lifetime of the process.
    """
    from importlib.resources import files

    return files('bacommon').joinpath('bob_v1.zstddict').read_bytes()
