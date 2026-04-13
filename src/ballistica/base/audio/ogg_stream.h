// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_AUDIO_OGG_STREAM_H_
#define BALLISTICA_BASE_AUDIO_OGG_STREAM_H_

#include "ballistica/base/audio/audio_streamer.h"

#if BA_ENABLE_AUDIO
#if BA_PLATFORM_IOS_TVOS || BA_PLATFORM_ANDROID
#include "ivorbisfile.h"  // NOLINT
#else
#include <vorbis/vorbisfile.h>
#endif  // BA_PLATFORM_IOS_TVOS
#endif  // BA_ENABLE_AUDIO

#include <string>

namespace ballistica::base {

#if BA_ENABLE_AUDIO

// Handles streaming ogg audio.
class OggStream : public AudioStreamer {
 public:
  OggStream(const char* file_name, ALuint source, bool loop);
  ~OggStream() override;

 protected:
  void DoStop() override;
  void DoStream(char* pcm, int* size, unsigned int* rate) override;

 private:
  auto GetErrorString(int code) -> std::string;
  OggVorbis_File ogg_file_{};
  bool have_ogg_file_;
  vorbis_info* vorbis_info_;
};

#endif  // BA_ENABLE_AUDIO

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_AUDIO_OGG_STREAM_H_
