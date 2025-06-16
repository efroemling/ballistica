// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/audio/audio_streamer.h"

#include <cstdio>

#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"

// Need to move away from OpenAL on Apple stuff.
#if __clang__
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"
#endif

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
    printf("AudioServer::Streamer: restarting playback\n");
    fflush(stdout);

    alSourcePlay(source_);
    CHECK_AL_ERROR;
  }
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
