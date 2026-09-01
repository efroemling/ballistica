// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/audio/ogg_blob_source.h"

#include <cstring>

namespace ballistica::base {

#if BA_ENABLE_AUDIO

static auto BlobRead(void* ptr, size_t size, size_t nmemb, void* data_source)
    -> size_t {
  auto* src = static_cast<OggBlobSource*>(data_source);
  if (size == 0) {
    return 0;
  }
  size_t want = size * nmemb;
  size_t avail = src->blob->size() - src->pos;
  size_t got = want < avail ? want : avail;
  memcpy(ptr, src->blob->data() + src->pos, got);
  src->pos += got;
  // fread-style semantics: number of complete items read.
  return got / size;
}

static auto BlobSeek(void* data_source, ogg_int64_t offset, int whence) -> int {
  auto* src = static_cast<OggBlobSource*>(data_source);
  ogg_int64_t base;
  switch (whence) {
    case SEEK_SET:
      base = 0;
      break;
    case SEEK_CUR:
      base = static_cast<ogg_int64_t>(src->pos);
      break;
    case SEEK_END:
      base = static_cast<ogg_int64_t>(src->blob->size());
      break;
    default:
      return -1;
  }
  ogg_int64_t newpos = base + offset;
  if (newpos < 0 || newpos > static_cast<ogg_int64_t>(src->blob->size())) {
    return -1;
  }
  src->pos = static_cast<size_t>(newpos);
  return 0;
}

static auto BlobClose(void* data_source) -> int {
  (void)data_source;  // Blob lifetime belongs to the caller.
  return 0;
}

static long BlobTell(void* data_source) {  // NOLINT (vorbis uses long)
  return static_cast<long>(                // NOLINT
      static_cast<OggBlobSource*>(data_source)->pos);
}

auto OggBlobCallbacks() -> const ov_callbacks& {
  static const ov_callbacks callbacks{BlobRead, BlobSeek, BlobClose, BlobTell};
  return callbacks;
}

#endif  // BA_ENABLE_AUDIO

}  // namespace ballistica::base
