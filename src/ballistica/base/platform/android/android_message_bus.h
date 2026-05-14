// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PLATFORM_ANDROID_ANDROID_MESSAGE_BUS_H_
#define BALLISTICA_BASE_PLATFORM_ANDROID_ANDROID_MESSAGE_BUS_H_
#if BA_PLATFORM_ANDROID

#include <jni.h>

#include <string>
#include <vector>

namespace ballistica::base {

// Typed Java<->C++ message bus. The body of this header (handler
// abstract base, sender class, install/setter declarations) is
// generated from `src/codegen/babasecodegen/android_messages.py` via
// `tools/pcommand gen_android_message_cpp`.
#include "ballistica/base/generated/android/android_messages_decl.inc"

}  // namespace ballistica::base

#endif  // BA_PLATFORM_ANDROID
#endif  // BALLISTICA_BASE_PLATFORM_ANDROID_ANDROID_MESSAGE_BUS_H_
