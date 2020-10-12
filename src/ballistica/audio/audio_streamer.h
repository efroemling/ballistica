// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_AUDIO_AUDIO_STREAMER_H_
#define BALLISTICA_AUDIO_AUDIO_STREAMER_H_

#include <map>
#include <string>

#include "ballistica/audio/al_sys.h"  // FIXME: shouldn't need this here.
#include "ballistica/core/object.h"

namespace ballistica {

#if BA_ENABLE_AUDIO
// Provider for streamed audio data.
class AudioStreamer : public Object {
 public:
  auto GetDefaultOwnerThread() const -> ThreadIdentifier override {
    return ThreadIdentifier::kAudio;
  }
  AudioStreamer(const char* file_name, ALuint source, bool loop);
  ~AudioStreamer() override;
  auto Play() -> bool;
  void Stop();
  void Update();
  enum Format { INVALID_FORMAT, MONO16_FORMAT, STEREO16_FORMAT };
  auto al_format() const -> ALenum {
    switch (format_) {
      case MONO16_FORMAT:
        return AL_FORMAT_MONO16;
      case STEREO16_FORMAT:
        return AL_FORMAT_STEREO16;
      default:
        break;
    }
    return INVALID_FORMAT;
  }
  auto loops() const -> bool { return loops_; }
  auto file_name() const -> const std::string& { return file_name_; }

 protected:
  virtual void DoStop() = 0;
  virtual void DoStream(char* pcm, int* size, unsigned int* rate) = 0;
  auto Stream(ALuint buffer) -> bool;
  void DetachBuffers();
  void set_format(Format format) { format_ = format; }

 private:
  Format format_ = INVALID_FORMAT;
  bool playing_ = false;
  ALuint buffers_[kAudioStreamBufferCount]{};
  ALuint source_ = 0;
  std::string file_name_;
  bool loops_ = false;
  bool eof_ = false;
};

#endif  // BA_ENABLE_AUDIO

}  // namespace ballistica

#endif  // BALLISTICA_AUDIO_AUDIO_STREAMER_H_
