// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/audio/ogg_stream.h"

#include <cstdio>
#include <string>

#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/core_platform.h"

namespace ballistica::base {

#if BA_ENABLE_AUDIO

static auto CallbackRead(void* ptr, size_t size, size_t nmemb,
                         void* data_source) -> size_t {
  return fread(ptr, size, nmemb, static_cast<FILE*>(data_source));
}

static auto CallbackSeek(void* data_source, ogg_int64_t offset, int whence)
    -> int {
  return fseek(static_cast<FILE*>(data_source),
               static_cast_check_fit<long>(offset), whence);  // NOLINT
}
static auto CallbackClose(void* data_source) -> int {
  return fclose(static_cast<FILE*>(data_source));
}
static long CallbackTell(void* data_source) {  // NOLINT (ogg wants long)
  return ftell(static_cast<FILE*>(data_source));
}

OggStream::OggStream(const char* file_name, ALuint source, bool loop)
    : AudioStreamer(file_name, source, loop), have_ogg_file_(false) {
  int result;
  FILE* f;
  if (!(f = g_core->platform->FOpen(file_name, "rb"))) {
    throw Exception("can't open ogg file: '" + std::string(file_name) + "'");
  }
  ov_callbacks callbacks;
  callbacks.read_func = CallbackRead;
  callbacks.seek_func = CallbackSeek;
  callbacks.close_func = CallbackClose;
  callbacks.tell_func = CallbackTell;

  // Have to use callbacks here as codewarrior's FILE struct doesn't
  // seem to agree with what vorbis expects... oh well.
  // Ericf note Aug 2019: Wow I have comments here old enough to be referencing
  // codewarrior; that's awesome!
  result = ov_open_callbacks(f, &ogg_file_, nullptr, 0, callbacks);
  if (result < 0) {
    fclose(f);
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
