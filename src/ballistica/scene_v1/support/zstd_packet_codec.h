// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_ZSTD_PACKET_CODEC_H_
#define BALLISTICA_SCENE_V1_SUPPORT_ZSTD_PACKET_CODEC_H_

#include <cstdint>
#include <vector>

// Forward-declare the zstd context types so the header stays free of
// zstd.h (only the .cc pulls the real thing in).
struct ZSTD_CCtx_s;
struct ZSTD_DCtx_s;
struct ZSTD_CDict_s;
struct ZSTD_DDict_s;

namespace ballistica::scene_v1 {

/// Game-packet compression with zstd and a trained dictionary
/// (protocol kProtocolVersionZstdPackets and up; docs/design/
/// packet-compression.md). Game packets are tiny (~80 bytes), so this
/// only beats the legacy per-byte huffman with a dictionary that knows
/// what packets look like; with one, ~0.70 vs huffman's ~0.90 on a
/// stress test, at about a microsecond per packet either way.
///
/// Wire form: a compressed packet is the marker byte kMarker followed
/// by a zstd frame with its 4-byte magic number stripped (every frame's
/// magic is the same, so it is pure overhead at this size) and the
/// content-size, checksum and dictionary-id fields disabled. A packet
/// that would not shrink goes out raw. Raw game packets start with a
/// packet-type byte well below kMarker, and huffman-compressed ones
/// have their top bit set, so a receiver can tell all three apart
/// from the first byte alone (which is what lets huffman and zstd
/// coexist on one connection during the handshake).
///
/// Logic thread only (one context each way, shared by every
/// connection).
class ZstdPacketCodec {
 public:
  static constexpr uint8_t kMarker = 0x7F;
  static constexpr int kCompressionLevel = 5;
  /// Largest decompressed packet we'll accept (reliable messages are
  /// split at 480 bytes; unreliable ones stay under the MTU).
  static constexpr size_t kMaxPacketSize = 16384;

  /// Build from a dictionary (the bytes bacommon ships; both ends must
  /// hold the same dictionary, which the protocol version pins).
  explicit ZstdPacketCodec(const std::vector<uint8_t>& dict);
  ~ZstdPacketCodec();

  /// Compress a raw game packet (returns the raw packet itself when
  /// compression wouldn't shrink it).
  auto compress(const std::vector<uint8_t>& src) -> std::vector<uint8_t>;

  /// Inverse of compress. Throws on malformed input.
  auto decompress(const std::vector<uint8_t>& src) -> std::vector<uint8_t>;

  /// Whether a received packet is one of ours (vs raw or huffman).
  static auto IsZstdPacket(const std::vector<uint8_t>& data) -> bool {
    return !data.empty() && data[0] == kMarker;
  }

  ZstdPacketCodec(const ZstdPacketCodec&) = delete;
  auto operator=(const ZstdPacketCodec&) -> ZstdPacketCodec& = delete;

 private:
  ZSTD_CDict_s* cdict_{};
  ZSTD_DDict_s* ddict_{};
  ZSTD_CCtx_s* cctx_{};
  ZSTD_DCtx_s* dctx_{};
  std::vector<uint8_t> scratch_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_ZSTD_PACKET_CODEC_H_
