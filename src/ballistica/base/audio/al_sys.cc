// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/audio/al_sys.h"

#include <cstdio>
#include <string>

#include "ballistica/base/audio/audio_server.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/shared/generic/utils.h"

// Need to finish moving away from built-in OpenAL on Apple stuff.
#if __clang__
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"
#endif

#if BA_ENABLE_AUDIO

namespace ballistica::base {

void _check_al_error(const char* file, int line) {
  if (g_base->audio_server->paused()) {
    g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                         Utils::BaseName(file) + ":" + std::to_string(line)
                             + ": Checking OpenAL error while paused.");
  }
  ALenum al_err = alGetError();
  if (al_err != AL_NO_ERROR) {
    g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                         Utils::BaseName(file) + ":" + std::to_string(line)
                             + ": OpenAL Error: " + GetALErrorString(al_err)
                             + ";");
  }
}

auto GetALErrorString(ALenum err) -> std::string {
  switch (err) {
    case AL_INVALID_NAME:
      return "AL_INVALID_NAME";
    case AL_ILLEGAL_ENUM:
      return "AL_ILLEGAL_ENUM";
    case AL_INVALID_VALUE:
      return "AL_INVALID_VALUE";
    case AL_ILLEGAL_COMMAND:
      return "AL_ILLEGAL_COMMAND";
    case AL_OUT_OF_MEMORY:
      return "AL_OUT_OF_MEMORY";
    default: {
      static char undef_err_str[128];
      snprintf(undef_err_str, sizeof(undef_err_str),
               "(unrecognized: 0x%X (%d))", err, err);
      return undef_err_str;
    }
  }
}

}  // namespace ballistica::base

#endif  // BA_ENABLE_AUDIO
