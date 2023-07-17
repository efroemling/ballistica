// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_AUDIO_AL_SYS_H_
#define BALLISTICA_BASE_AUDIO_AL_SYS_H_

#include <string>

#include "ballistica/shared/ballistica.h"

#if BA_ENABLE_AUDIO

#if HAVE_FRAMEWORK_OPENAL
#include <OpenAL/al.h>
#include <OpenAL/alc.h>
#else
#include <AL/al.h>
#include <AL/alc.h>
#endif

#if BA_OSTYPE_ANDROID
#include <AL/alext.h>
#endif

#define CHECK_AL_ERROR _check_al_error(__FILE__, __LINE__)
#if BA_DEBUG_BUILD
#define DEBUG_CHECK_AL_ERROR CHECK_AL_ERROR
#else
#define DEBUG_CHECK_AL_ERROR ((void)0)
#endif

namespace ballistica::base {

const int kAudioStreamBufferSize = 4096 * 8;
const int kAudioStreamBufferCount = 7;

// Some OpenAL Error handling utils.
auto GetALErrorString(ALenum err) -> const char*;

void _check_al_error(const char* file, int line);

}  // namespace ballistica::base

#endif  // BA_ENABLE_AUDIO

#endif  // BALLISTICA_BASE_AUDIO_AL_SYS_H_
