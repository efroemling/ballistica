// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_AUDIO_AL_SYS_H_
#define BALLISTICA_BASE_AUDIO_AL_SYS_H_

#if BA_ENABLE_AUDIO

#include <string>

// TODO(ericf): Migrate to OpenALSoft on remaining platforms (iOS, etc.) and
// then we can get rid of framework option.
#if BA_USE_FRAMEWORK_OPENAL
#include <OpenAL/al.h>   // IWYU pragma: export
#include <OpenAL/alc.h>  // IWYU pragma: export
#else
#include <al.h>   // IWYU pragma: export
#include <alc.h>  // IWYU pragma: export
#endif

#define CHECK_AL_ERROR _check_al_error(__FILE__, __LINE__)

namespace ballistica::base {

const int kAudioStreamBufferSize = 4096 * 8;
const int kAudioStreamBufferCount = 7;

// Some OpenAL Error handling utils.
auto GetALErrorString(ALenum err) -> std::string;

void _check_al_error(const char* file, int line);

}  // namespace ballistica::base

#endif  // BA_ENABLE_AUDIO

#endif  // BALLISTICA_BASE_AUDIO_AL_SYS_H_
