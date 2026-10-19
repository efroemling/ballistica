// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/audio/ogg_stream.h"

#include <cstdio>
#include <string>

#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/platform.h"

namespace ballistica::base {

#if BA_ENABLE_AUDIO

OggStream::OggStream(const char* file_name, ALuint source, bool loop)
    : AudioStreamer(file_name, source, loop), have_ogg_file_(false) {
  int result;
  blob_ = AssetBlob::FromFile(file_name);
  if (!blob_.exists()) {
    throw Exception("can't open ogg file: '" + std::string(file_name) + "'");
  }
  blob_source_ = OggBlobSource{&blob_};

  result = ov_open_callbacks(&blob_source_, &ogg_file_, nullptr, 0,
                             OggBlobCallbacks());
  if (result < 0) {
    throw Exception(GetErrorString(result));
  }
  have_ogg_file_ = true;

  vorbis_info_ = ov_info(&ogg_file_, -1);
  if (vorbis_info_->channels == 1) {
    set_format(Format::kMono16);
  } else {
    set_format(Format::kStereo16);
  }
}

OggStream::~OggStream() {
  if (have_ogg_file_) {
    ov_clear(&ogg_file_);
  }
}

void OggStream::DoStop() {
  if (have_ogg_file_) ov_pcm_seek(&ogg_file_, 0);
}

void OggStream::DoStream(char* pcm, int* size, unsigned int* rate) {
  int section;
  int result;
  while ((*size) < kAudioStreamBufferSize) {
    // tremor's ov_read takes fewer args
#if (BA_PLATFORM_IOS_TVOS || BA_PLATFORM_ANDROID)
    result = static_cast<int>(ov_read(
        &ogg_file_, pcm + (*size), kAudioStreamBufferSize - (*size), &section));
#else
    result = static_cast<int>(ov_read(&ogg_file_, pcm + (*size),
                                      kAudioStreamBufferSize - (*size), 0, 2, 1,
                                      &section));
#endif  // BA_PLATFORM_IOS_TVOS

    if (result > 0) {
      (*size) += result;
    } else {
      if (result < 0) {
        static bool reported_error = false;
        if (!reported_error) {
          reported_error = true;
          g_core->logging->Log(
              LogName::kBaAudio, LogLevel::kError,
              "Error streaming ogg file: '" + file_name() + "'.");
        }
        if (loops()) {
          ov_pcm_seek(&ogg_file_, 0);
        } else {
          return;
        }
      } else {
        // we hit the end of the file; either reset and keep reading if we're
        // looping or just return what we got
        if (loops()) {
          ov_pcm_seek(&ogg_file_, 0);
        } else {
          return;
        }
      }
    }
  }
  if ((*size) == 0 && loops()) {
    throw Exception();
  }
  (*rate) = static_cast<unsigned int>(vorbis_info_->rate);
}

auto OggStream::GetErrorString(int code) -> std::string {
  switch (code) {
    case OV_EREAD:
      return std::string("Read from media.");
    case OV_ENOTVORBIS:
      return std::string("Not Vorbis data.");
    case OV_EVERSION:
      return std::string("Vorbis version mismatch.");
    case OV_EBADHEADER:
      return std::string("Invalid Vorbis header.");
    case OV_EFAULT:
      return std::string("Internal logic fault (bug or heap/stack corruption.");
    default:
      return std::string("Unknown Ogg error.");
  }
}

#endif  // BA_ENABLE_AUDIO

}  // namespace ballistica::base
