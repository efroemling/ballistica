// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_AUDIO_AUDIO_STREAMER_H_
#define BALLISTICA_BASE_AUDIO_AUDIO_STREAMER_H_

#include <map>
#include <string>

#include "ballistica/base/audio/al_sys.h"  // FIXME: shouldn't need this here.
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

#if BA_ENABLE_AUDIO
// Provider for streamed audio data.
class AudioStreamer : public Object {
 public:
  auto GetDefaultOwnerThread() const -> EventLoopID override {
    return EventLoopID::kAudio;
  }
  AudioStreamer(const char* file_name, ALuint source, bool loop);
  ~AudioStreamer() override;
  auto Play() -> bool;
  void Stop();
  void Update();
  enum class Format : uint8_t { kInvalid, kMono16, kStereo16 };
  auto al_format() const -> ALenum {
    switch (format_) {
      case Format::kMono16:
        return AL_FORMAT_MONO16;
      case Format::kStereo16:
        return AL_FORMAT_STEREO16;
      default:
        break;
    }
    FatalError("Invalid AL format.");
    return AL_FORMAT_MONO16;
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
  Format format_{Format::kInvalid};
  bool playing_{};
  bool loops_{};
  bool eof_{};
  ALuint buffers_[kAudioStreamBufferCount]{};
  ALuint source_{};
  std::string file_name_;
};

#endif  // BA_ENABLE_AUDIO

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_AUDIO_AUDIO_STREAMER_H_
