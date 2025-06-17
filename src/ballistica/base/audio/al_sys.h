// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_AUDIO_AL_SYS_H_
#define BALLISTICA_BASE_AUDIO_AL_SYS_H_

#if BA_ENABLE_AUDIO

#if BA_HAVE_FRAMEWORK_OPENAL
#include <OpenAL/al.h>   // IWYU pragma: export
#include <OpenAL/alc.h>  // IWYU pragma: export
#else
#include <al.h>   // IWYU pragma: export
#include <alc.h>  // IWYU pragma: export
#endif

#if BA_OPENAL_IS_SOFT
#define AL_ALEXT_PROTOTYPES
#include <alext.h>
// Has not been formalized into an extension yet (from alc/inprogext.h"
// typedef void(ALC_APIENTRY* LPALSOFTLOGCALLBACK)(void* userptr, char level,
//                                                 const char* message,
//                                                 int length) noexcept;
// typedef void(ALC_APIENTRY* LPALSOFTSETLOGCALLBACK)(LPALSOFTLOGCALLBACK
// callback,
//                                                    void* userptr) noexcept;
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
