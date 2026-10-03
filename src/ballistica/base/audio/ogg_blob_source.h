// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_AUDIO_OGG_BLOB_SOURCE_H_
#define BALLISTICA_BASE_AUDIO_OGG_BLOB_SOURCE_H_

#include "ballistica/base/base.h"

#if BA_ENABLE_AUDIO
#if BA_USE_TREMOR_VORBIS
#include "ivorbisfile.h"  // NOLINT
#else
#include <vorbis/vorbisfile.h>
#endif

#include "ballistica/base/assets/asset_blob.h"

namespace ballistica::base {

/// Cursor adapting an AssetBlob for vorbisfile's callback interface,
/// letting oggs decode straight out of memory spans (mapped files,
/// archive regions) with no FILE involved. The blob must outlive the
/// decode; the callbacks' close is a no-op (blob lifetime belongs to
/// the caller - typically RAII).
struct OggBlobSource {
  const AssetBlob* blob{};
  size_t pos{};
};

/// ov_callbacks operating on an OggBlobSource passed as the
/// data-source pointer.
auto OggBlobCallbacks() -> const ov_callbacks&;

}  // namespace ballistica::base

#endif  // BA_ENABLE_AUDIO

#endif  // BALLISTICA_BASE_AUDIO_OGG_BLOB_SOURCE_H_
