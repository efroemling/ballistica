// Released under the MIT License. See LICENSE for details.

#if BA_PLATFORM_ANDROID

#include "ballistica/base/platform/android/android_message_bus.h"

#include <jni.h>

#include <string>
#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/android/platform_android.h"

namespace ballistica::base {

// Generated trampolines, native-method table, sender bodies, and
// installer. See `src/meta/babasemeta/android_messages.py` for the
// source spec.
#include "ballistica/base/generated/android/android_messages_impl.inc"

}  // namespace ballistica::base

#endif  // BA_PLATFORM_ANDROID
