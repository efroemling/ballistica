// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_BALLISTICA_H_
#define BALLISTICA_SHARED_BALLISTICA_H_

// Try to ensure they're providing proper config stuff.
#ifndef BA_HAVE_CONFIG
#error ballistica platform config has not been defined!
#endif

#ifdef __cplusplus
#include <string>
#endif

// Minimum functionality we want available everywhere we are included.
#include "ballistica/shared/foundation/exception.h"  // IWYU pragma: keep.
#include "ballistica/shared/foundation/inline.h"     // IWYU pragma: keep.
#include "ballistica/shared/foundation/macros.h"     // IWYU pragma: keep.
#include "ballistica/shared/foundation/types.h"

// There are one or two places where we include this from regular C or
// Objective-C code so want to gracefully handle that case.
#ifdef __cplusplus

namespace ballistica {

extern const int kEngineBuildNumber;
extern const char* kEngineVersion;
extern const int kEngineApiVersion;

const int kDefaultPort = 43210;

const float kTVBorder = 0.075f;
const float kVRBorder = 0.085f;

// Largest UDP packets we attempt to send.
// (is there a definitive answer on what this should be?)
const int kMaxPacketSize = 700;

// Extra bytes added to message packets.
const int kMessagePacketHeaderSize = 6;

// The screen, no matter what size/aspect, will always fit this virtual
// rectangle, so placing UI elements within these coords is always safe.

// Our standard virtual res (16:9 aspect ratio).
const int kBaseVirtualResX = 1280;
const int kBaseVirtualResY = 720;

// Our 'small' res which is used for 'small' ui mode only. This matches
// the 19.5:9 aspect ratio common on modern smartphones (as of 2024).
// const int kBaseVirtualResSmallX = 1300;
// const int kBaseVirtualResSmallY = 600;

// Magic numbers at the start of our file types.
const int kBrpFileID = 83749;
const int kBobFileID = 45623;
const int kCobFileID = 13466;

const float kPi = 3.1415926535897932384626433832795028841971693993751f;
const float kPiDeg = kPi / 180.0f;
const float kDegPi = 180.0f / kPi;

namespace core {
class CoreConfig;
}

// The following is a smattering of convenience functions declared in our
// top level namespace. Functionality can be exposed here if it is used
// often enough that avoiding the extra class includes seems like an overall
// compile-time/convenience win.

#if BA_MONOLITHIC_BUILD
/// Entry point for standard monolithic builds. Handles all initing and
/// running.
auto MonolithicMain(const core::CoreConfig& config) -> int;

/// Special alternate version of MonolithicMain which breaks its work into
/// pieces; used to reduce app-not-responding reports from slow Android
/// devices. Call this repeatedly until it returns true;
auto MonolithicMainIncremental(const core::CoreConfig* config) -> bool;
#endif  // BA_MONOLITHIC_BUILD

// Print a momentary message on the screen.
void ScreenMessage(const std::string& msg);
void ScreenMessage(const std::string& msg, const Vector3f& color);

/// Return a human-readable name for the current thread.
auto CurrentThreadName() -> std::string;

/// Log a fatal error and kill the app. Can be called from any thread at any
/// time. Provided message will be shown to the user if possible. This will
/// attempt to ship all accumulated logs to the master-server so the
/// standard Log() call can be used before this to include extra info not
/// relevant to the end user.
void FatalError(const std::string& message = "");

}  // namespace ballistica

#endif  // __cplusplus

#endif  // BALLISTICA_SHARED_BALLISTICA_H_
