// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/zstd_packet_codec.h"

#include <cassert>
#include <cstring>
#include <string>
#include <vector>

#include "ballistica/shared/foundation/exception.h"
#include "zstd.h"  // NOLINT(build/include_subdir)

namespace ballistica::scene_v1 {

namespace {
// Every zstd frame starts with this (little-endian 0xFD2FB528); we drop it
// on the wire and put it back before decoding.
const uint8_t kZstdMagic[4] = {0x28, 0xB5, 0x2F, 0xFD};
}  // namespace

ZstdPacketCodec::ZstdPacketCodec(const std::vector<uint8_t>& dict) {
  if (dict.empty()) {
    throw Exception("empty zstd packet dictionary");
  }
  cdict_ = ZSTD_createCDict(dict.data(), dict.size(), kCompressionLevel);
  ddict_ = ZSTD_createDDict(dict.data(), dict.size());
  cctx_ = ZSTD_createCCtx();
  dctx_ = ZSTD_createDCtx();
  if (!cdict_ || !ddict_ || !cctx_ || !dctx_) {
    throw Exception("zstd packet codec setup failed");
  }
  // All of the stable API: works against any libzstd 1.4+ (Linux distro
  // builds may link an older one than our vendored header).
  ZSTD_CCtx_refCDict(cctx_, cdict_);
  ZSTD_CCtx_setParameter(cctx_, ZSTD_c_contentSizeFlag, 0);
  ZSTD_CCtx_setParameter(cctx_, ZSTD_c_checksumFlag, 0);
  ZSTD_CCtx_setParameter(cctx_, ZSTD_c_dictIDFlag, 0);
  ZSTD_DCtx_refDDict(dctx_, ddict_);
  scratch_.resize(ZSTD_compressBound(kMaxPacketSize));
}

ZstdPacketCodec::~ZstdPacketCodec() {
  ZSTD_freeCCtx(cctx_);
  ZSTD_freeDCtx(dctx_);
  ZSTD_freeCDict(cdict_);
  ZSTD_freeDDict(ddict_);
}

auto ZstdPacketCodec::compress(const std::vector<uint8_t>& src)
    -> std::vector<uint8_t> {
  if (src.empty() || src.size() > kMaxPacketSize) {
    return src;
  }
  // Raw packets must never look like ours (they start with a packet-type
  // byte, all far below the marker).
  assert(src[0] != kMarker);
  size_t n = ZSTD_compress2(cctx_, scratch_.data(), scratch_.size(), src.data(),
                            src.size());
  if (ZSTD_isError(n) || n < 5 || memcmp(scratch_.data(), kZstdMagic, 4) != 0) {
    return src;  // Shouldn't happen; send raw rather than fail.
  }
  // Marker + frame minus magic; only if that actually beats raw.
  size_t out_size = 1 + (n - 4);
  if (out_size >= src.size()) {
    return src;
  }
  std::vector<uint8_t> out(out_size);
  out[0] = kMarker;
  memcpy(out.data() + 1, scratch_.data() + 4, n - 4);
  return out;
}

auto ZstdPacketCodec::decompress(const std::vector<uint8_t>& src)
    -> std::vector<uint8_t> {
  if (!IsZstdPacket(src)) {
    return src;
  }
  if (src.size() < 2) {
    throw Exception("truncated zstd packet");
  }
  // Rebuild the frame: magic + everything after the marker.
  std::vector<uint8_t> frame(4 + (src.size() - 1));
  memcpy(frame.data(), kZstdMagic, 4);
  memcpy(frame.data() + 4, src.data() + 1, src.size() - 1);
  std::vector<uint8_t> out(kMaxPacketSize);
  size_t n = ZSTD_decompressDCtx(dctx_, out.data(), out.size(), frame.data(),
                                 frame.size());
  if (ZSTD_isError(n)) {
    throw Exception(std::string("zstd packet decode failed: ")
                    + ZSTD_getErrorName(n));
  }
  out.resize(n);
  return out;
}

}  // namespace ballistica::scene_v1
