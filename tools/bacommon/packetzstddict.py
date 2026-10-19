# Released under the MIT License. See LICENSE for details.
"""Zstandard dictionaries for compressing scene game packets.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.

The game compresses each outgoing scene packet on its own (they average
under a hundred bytes), which zstd only does well with a dictionary
trained on what packets look like. The dictionary here is trained on
captures of hosted games (``test_game_run --packet-dump`` on a host and
a client across several maps, mini-games and player counts; recipe in
``docs/design/packet-compression.md``) and is handed to the C++ layer
at app start.

Both ends of a connection must hold the identical dictionary, so
dictionaries are immutable and versioned: never mutate an existing
``.zstddict`` file -- add a new version instead -- and bump the scene
protocol version when the game switches to it (the protocol version is
what tells a peer which dictionary is in play).
"""

from functools import lru_cache


@lru_cache(maxsize=None)
def packets_dict_v1() -> bytes:
    """Return the v1 zstd dictionary for scene game packets.

    The dictionary is read from the bundled data file on first call and
    cached for the lifetime of the process.
    """
    from importlib.resources import files

    return files('bacommon').joinpath('packets_v1.zstddict').read_bytes()
