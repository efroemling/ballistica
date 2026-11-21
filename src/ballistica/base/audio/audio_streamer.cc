// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/audio/audio_streamer.h"

#include <string>

#include "ballistica/base/audio/audio_server.h"
#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"

namespace ballistica::base {

#if BA_ENABLE_AUDIO
AudioStreamer::AudioStreamer(const char* file_name, ALuint source_in, bool loop)
    : source_(source_in), file_name_(file_name), loops_(loop) {
  assert(g_base->InAudioThread());
  alGenBuffers(kAudioStreamBufferCount, buffers_);
  CHECK_AL_ERROR;
}

AudioStreamer::~AudioStreamer() {
  assert(!playing_);
  assert(g_base->audio_server);

  alDeleteBuffers(kAudioStreamBufferCount, buffers_);
  CHECK_AL_ERROR;
}

auto AudioStreamer::Play() -> bool {
  CHECK_AL_ERROR;
  assert(!playing_);
  playing_ = true;

  // In case the source is already attached to something.
  DetachBuffers();

  // Fill all our buffers with data.
  for (unsigned int buffer : buffers_) {
    if (!Stream(buffer)) {
      return false;
    }
  }

  alSourceQueueBuffers(source_, kAudioStreamBufferCount, buffers_);
  CHECK_AL_ERROR;

  alSourcePlay(source_);
  CHECK_AL_ERROR;

  // Suppress 'always returns true' lint.
  if (explicit_bool(false)) {
    return false;
  }

  return true;
}

void AudioStreamer::Stop() {
  CHECK_AL_ERROR;
  assert(playing_);
  alSourceStop(source_);
  CHECK_AL_ERROR;
  playing_ = false;
  DetachBuffers();
  DoStop();
}

void AudioStreamer::Update() {
  if (eof_) {
    return;
  }

  CHECK_AL_ERROR;

  assert(playing_);

  ALint queued;
  ALint processed;

  // See how many buffers have been processed.
  alGetSourcei(source_, AL_BUFFERS_QUEUED, &queued);
  CHECK_AL_ERROR;
  alGetSourcei(source_, AL_BUFFERS_PROCESSED, &processed);
  CHECK_AL_ERROR;

  // Remember what we saw on entry and how long it's been since our last
  // look, for the underrun report below.
  ALint queued_on_entry{queued};
  ALint processed_on_entry{processed};
  millisecs_t now = g_core->AppTimeMillisecs();
  millisecs_t update_gap = last_update_time_ < 0 ? -1 : now - last_update_time_;
  int unsuspend_count = g_base->audio_server->unsuspend_count();
  bool resumed_since_last_update =
      unsuspend_count != last_update_unsuspend_count_;
  last_update_time_ = now;
  last_update_unsuspend_count_ = unsuspend_count;

  // A fun anomaly in the linux version; we sometimes get more
  // "processed" buffers than we have queued.
  if (queued < processed) {
    g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                         "Streamer oddness: queued(" + std::to_string(queued)
                             + "); processed(" + std::to_string(processed)
                             + ")");
    processed = queued;
  }

  // Pull the completed ones off, refill them, and queue them back up.
  while (processed--) {
    ALuint buffer;
    alSourceUnqueueBuffers(source_, 1, &buffer);
    CHECK_AL_ERROR;
    Stream(buffer);
    if (!eof_) {
      alSourceQueueBuffers(source_, 1, &buffer);
      CHECK_AL_ERROR;
    }
  }

  // Restart playback if need be.
  ALenum state;
  alGetSourcei(source_, AL_SOURCE_STATE, &state);
  CHECK_AL_ERROR;

  if (state != AL_PLAYING) {
    // The source ran dry (we didn't refill fast enough) and OpenAL stopped
    // it. We recover here, but each one is an audible hiccup, so keep it
    // visible (this used to be a bare printf, invisible on mobile logs).
    //
    // The details tell apart the likely causes: a big update gap (vs. the
    // headroom our queued buffers hold) means this thread was starved; all
    // buffers processed with a small gap means the device ate audio faster
    // than real time; buffers still unprocessed means something other than
    // running dry stopped the source (a device disconnect/reset, or the
    // OS). 'resumed' notes an audio suspend/unsuspend in between.
    restart_count_++;
    if (now - last_restart_log_time_ > 5000) {
      last_restart_log_time_ = now;
      g_core->logging->Log(LogName::kBaAudio, LogLevel::kWarning, [&] {
        return "Streaming source underran; restarting playback (file '"
               + file_name_ + "', " + std::to_string(restart_count_)
               + " restart(s) so far). "
               + UnderrunDetails_(state, queued_on_entry, processed_on_entry,
                                  update_gap, resumed_since_last_update);
      });
    }

    alSourcePlay(source_);
    CHECK_AL_ERROR;
  }
}

auto AudioStreamer::UnderrunDetails_(ALenum state, ALint queued,
                                     ALint processed, millisecs_t update_gap,
                                     bool resumed) -> std::string {
  const char* state_name;
  switch (state) {
    case AL_INITIAL:
      state_name = "initial";
      break;
    case AL_PAUSED:
      state_name = "paused";
      break;
    case AL_STOPPED:
      state_name = "stopped";
      break;
    default:
      state_name = "other";
      break;
  }

  // How much audio a full queue holds; an update gap beyond this starves
  // the source.
  std::string headroom{"?"};
  if (last_rate_ > 0) {
    int frame_bytes = format_ == Format::kStereo16 ? 4 : 2;
    auto ms = static_cast<int64_t>(kAudioStreamBufferCount)
              * kAudioStreamBufferSize * 1000
              / (static_cast<int64_t>(last_rate_) * frame_bytes);
    headroom = std::to_string(ms) + "ms";
  }

  // A disconnected device stops every source; worth ruling out.
  std::string connected{"?"};
  if (auto* context = alcGetCurrentContext()) {
    if (auto* device = alcGetContextsDevice(context)) {
      // ALC_CONNECTED (ALC_EXT_disconnect); not in our base alc.h.
      const ALCenum kALCConnected{0x313};
      ALCint val{-1};
      alcGetIntegerv(device, kALCConnected, 1, &val);
      connected = std::to_string(val);
    }
  }

  auto since_unsuspend = g_base->audio_server->last_unsuspend_time();
  std::string unsuspend_str =
      since_unsuspend < 0.0
          ? "never"
          : std::to_string(static_cast<int>(
                (g_core->AppTimeSeconds() - since_unsuspend) * 1000.0))
                + "ms ago";

  return "[state=" + std::string(state_name) + " queued="
         + std::to_string(queued) + " processed=" + std::to_string(processed)
         + "/" + std::to_string(kAudioStreamBufferCount) + " update_gap="
         + std::to_string(update_gap) + "ms" + " headroom=" + headroom
         + " resumed_since_last_update=" + (resumed ? "true" : "false")
         + " last_unsuspend=" + unsuspend_str + " connected=" + connected + "]";
}

void AudioStreamer::DetachBuffers() {
#if BA_DEBUG_BUILD
  ALint state;
  alGetSourcei(source_, AL_SOURCE_STATE, &state);
  CHECK_AL_ERROR;
  assert(state == AL_INITIAL || state == AL_STOPPED);
#endif

  // This should clear everything.
  alSourcei(source_, AL_BUFFER, 0);
  CHECK_AL_ERROR;
}

auto AudioStreamer::Stream(ALuint buffer) -> bool {
  char pcm[kAudioStreamBufferSize];
  int size = 0;
  unsigned int rate;
  CHECK_AL_ERROR;
  DoStream(pcm, &size, &rate);
  if (size > 0) {
    last_rate_ = rate;
    alBufferData(buffer, al_format(), pcm, size, static_cast<ALsizei>(rate));
    CHECK_AL_ERROR;
  } else {
    eof_ = true;
  }

  // Suppress 'always returns true' lint.
  if (explicit_bool(false)) {
    return false;
  }

  return true;
}

#endif  // BA_ENABLE_AUDIO

}  // namespace ballistica::base
