# Game Packet Compression

**Description:** How scene game packets are compressed on the wire — zstd with a shipped, versioned dictionary, legacy huffman for older peers — and how to retrain the dictionary or re-vendor zstd.

## Why a dictionary

A hosted game sends each client a stream of small packets (about 80
bytes each on an 8-player game since the compact stream framing of
protocol 44). General-purpose compression does nothing useful at that
size: zstd without a dictionary loses to the old huffman (frame
overhead), and retraining the huffman's byte table buys nothing (it is
a per-byte code; the order-0 entropy bound on real packets is ~0.81).
A zstd dictionary trained on real packet captures changes that:

| scheme | ratio on an 8-bot stress test |
|---|---|
| huffman (shipped table) | 0.89 |
| zstd, 64 KB dictionary, level 5 | 0.70-0.72 (chronologically held-out games) |

at about a microsecond per packet either way, so a fifth to a quarter
less payload for the same CPU. The measurements and the sweeps behind
these numbers are in `docs/initiatives/bandwidth.md`.

## Wire format and negotiation

`ZstdPacketCodec` (`scene_v1/support/zstd_packet_codec.{h,cc}`):

- A compressed packet is the marker byte `0x7F` followed by a zstd
  frame with its 4-byte magic number stripped (every frame's magic is
  identical) and the content-size, checksum and dictionary-id fields
  disabled. Only the stable zstd API is used, so any libzstd 1.4+
  decodes it. A packet that would not shrink is sent raw.
- Three kinds of game packet can arrive at a `Connection`, and the
  first byte says which: raw packets start with a packet-type byte (all
  far below `0x7F`), huffman packets have the top bit set, zstd packets
  start with `0x7F`. `Connection::HandleGamePacketCompressed` dispatches
  on that, per packet, with no state.
- Sending picks per peer: `Connection::PeerSupportsZstdPackets()` is
  true once the handshake has established that the peer is at
  `kProtocolVersionZstdPackets` or newer (the host: after the client's
  handshake response claimed a matching version; the client: after the
  host's handshake announced its version). Until then, and forever for
  older peers, packets go huffman. The handshake packets themselves are
  therefore always huffman, and because receiving is stateless the
  moment each side switches does not need to line up.
- Both ends must hold byte-identical dictionaries, so a dictionary is
  pinned to a protocol version: a new dictionary is a new
  `packets_vN.zstddict` and a protocol bump. Older streams are
  unaffected (replays are message-level and never see packet
  compression).

## The dictionary

`tools/bacommon/packets_v1.zstddict` (64 KB), accessor
`bacommon.packetzstddict.packets_dict_v1()`, handed to C++ once at app
start by `SceneV1AppSubsystem.__init__` via
`_bascenev1.set_packet_compression_dict`. Same rules as the mesh
dictionary in `bacommon.meshzstddict`: immutable, versioned, never
edited in place once a protocol that uses it has shipped. (bacommon is
efrosync'd, so the two files exist in every sibling repo even though
only the game reads them.) The one exception is *before* that
protocol ships: protocol 44 was unshipped through all of this work, so
`packets_v1.zstddict` was replaced in place on 2026-09-08 after the
stream changed shape (compact and unreliable corrections, folded and
packed commands, wide acks, 1200-byte packets); both ends always update
together in that window. After 44 ships, a retrain is `packets_v2`
plus a protocol bump, no exceptions.

Retrain whenever the stream layout changes materially: a dictionary
trained on a previous layout still works but leaves compression on the
table (the 2026-09-07 dictionary scored 0.817 on 2026-09-08 packets;
the retrain 0.767 on the same held-out set). The dictionary also
memorises whatever was common in its corpus, so removing a chatty
pattern from the stream frees space only at the next retrain.

Training recipe (2026-09-08; `build/tmp/dict_retrain.py OUT DUMPS...`
does the whole thing and prints shipped-vs-new held-out ratios):
capture raw outgoing packets with
`test_game_run --packet-dump` on stress-test hosts at a few player
counts (`--stress-test 8` for ~8 minutes cycles through maps and
mini-games; also a `--stress-test 4` run) and on a connected client
(`--packet-dump` there too, for the client→host direction), gather the
`packet_dump_*.bin` files from the silos, and train with the 3.14
stdlib: `compression.zstd.train_dict(packets, 65536)`.
Always score on packets the dictionary did not see (the script holds
out the last 30% of every capture, which is later mini-games): the
dictionary generalises to unseen games at a few points worse than its
training set, and a dictionary trained only on 8-player games scored
0.81 on a 4-player run, so cover the player counts you care about. Level 5
and 64 KB are the sweet spot: bigger dictionaries mostly memorise, and
higher levels cost microseconds for a point or two.

Runtime check on any platform:
`test_game_run [--platform ...] --exec "import _bascenev1;
print(_bascenev1.packet_compression_selftest())"` should print
`'codec': 'zstd'`; `--stream-stats` on a host shows the live wire/raw
ratio per client.

## Linking zstd per platform

We use the libzstd our embedded/system Python already links wherever
that is possible, and vendored public headers (`src/external/zstd/
include/zstd.h` + `zstd_errors.h`, 1.5.7, the version the embedded
pythons were built with) on every platform:

- **Apple** (xcode builds): `libpython_merged.a` in the Python
  xcframework carries zstd 1.5.7 for `_zstd` (see
  `apple-python-build.md`), so there is nothing extra to link; the
  vendored header is on `HEADER_SEARCH_PATHS`.
- **Android**: `src/external/python-android/lib/<abi>/libzstd.a`
  (built by `python_build_android.py`) is already an imported CMake
  target (`pyzstd`) linked into the app; the vendored header is on the
  include path.
- **mac / Linux cmake** (dev builds, headless servers, prefabs):
  `pkg_check_modules(ZSTD REQUIRED IMPORTED_TARGET libzstd)` — Homebrew
  `zstd` on mac (what Homebrew python links), `libzstd-dev` on Linux
  (installed on linbeast, larmbeast and rpi5 on 2026-09-07; jammy's is
  1.4.8, fine for the stable API; static prefab builds pick up its
  `libzstd.a`). A missing dev package fails the configure loudly.
- **Windows**: CPython's Windows `_zstd` links zstd privately, so we
  vendor the official binaries from the facebook/zstd GitHub release:
  `src/external/windows/lib/{x64,Win32}/libzstd.lib` (the release's
  MinGW-built import library, `libzstd.dll.a`, renamed; MSVC links it)
  plus `src/assets/windows/{x64,Win32}/libzstd.dll` shipped beside the
  exe like the ANGLE/OpenAL dlls, pulled in by
  `#pragma comment(lib, "libzstd.lib")` in `platform_windows.cc`.
  **Upgrade:** `tools/pcommand zstd_windows_install [VERSION]` downloads
  the release zips and source tarball, verifies pinned sha256s (an
  unpinned version prints its hashes to add), and installs the headers,
  import libs and dlls. The Windows cloudshell sync carries
  `src/external/zstd` explicitly (`cloudshell.py` filters) and
  `staging.py` ships the dll for gui and server builds alike. Its docstring is the runbook. Keep the version
  in step with the Apple/Android python builds' zstd.
