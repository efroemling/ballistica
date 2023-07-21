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
#include "ballistica/shared/foundation/exception.h"
#include "ballistica/shared/foundation/inline.h"
#include "ballistica/shared/foundation/macros.h"
#include "ballistica/shared/foundation/types.h"

// BA 2.0 UI testing.
#define BA_TOOLBAR_TEST 0

// There are one or two places where we include this from regular C
// or Objective-C code so want to gracefully handle that case.
#ifdef __cplusplus

namespace ballistica {

extern const int kEngineBuildNumber;
extern const char* kEngineVersion;

// Protocol version we host games with and write replays to.
// This should be incremented whenever there are changes made to the
// session-commands layer (new/removed/changed nodes, attrs, data files,
// behavior, etc.)
// Note that the packet/gamepacket/message layer can vary more organically based
// on build-numbers of connected clients/servers since none of that data is
// stored; this just needs to be observed for all the scene stuff that
// goes into replays since a single stream can get played/replayed on different
// builds (as long as they support that protocol version).
const int kProtocolVersion = 33;

// Oldest protocol version we can act as a client to.
// This can generally be left as-is as long as only
// new nodes/attrs/commands are added and existing
// stuff is unchanged.
const int kProtocolVersionMin = 24;

// FIXME: We should separate out connection protocol from scene protocol. We
//  want to be able to watch really old replays if possible but being able to
//  connect to old clients is much less important (and slows progress).

// Protocol additions:
// 25: added a few new achievement graphics and new node attrs for displaying
// stuff in front of the UI
// 26: added penguin
// 27: added templates for LOTS of characters
// 28: added cyborg and enabled fallback sounds and textures
// 29: added bunny and eggs
// 30: added support for resource-strings in text-nodes and screen-messages
// 31: added support for short-form resource-strings, time-display-node, and
// string-to-string attr connections
// 32: added json based player profiles message, added shield
//     alwaysShowHealthBar attr
// 33: handshake/handshake-response now send json dicts instead of
//     just player-specs
// 34: new image_node enums, data assets.

const int kDefaultPort = 43210;

const float kTVBorder = 0.075f;
const float kVRBorder = 0.085f;

// Largest UDP packets we attempt to send.
// (is there a definitive answer on what this should be?)
const int kMaxPacketSize = 700;

// Extra bytes added to message packets.
const int kMessagePacketHeaderSize = 6;

// The screen, no matter what size/aspect, will always
// fit this virtual rectangle, so placing UI elements within
// these coords is always safe.
// (we currently match the screen ratio of an iPhone 5).
const int kBaseVirtualResX = 1207;
const int kBaseVirtualResY = 680;

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

// The following is a smattering of convenience functions declared in our top
// level namespace. Functionality can be exposed here if it is used often
// enough that avoiding the extra class includes seems like an overall
// compile-time/convenience win.

#if BA_MONOLITHIC_BUILD
/// Entry point for standard monolithic builds. Handles all initing and running.
auto MonolithicMain(const core::CoreConfig& config) -> int;
#endif  // BA_MONOLITHIC_BUILD

// Print a momentary message on the screen.
void ScreenMessage(const std::string& msg);
void ScreenMessage(const std::string& msg, const Vector3f& color);

/// Return a human-readable name for the current thread.
auto CurrentThreadName() -> std::string;

/// Convenient access to Logging::Log.
void Log(LogLevel level, const std::string& msg);

/// Log a fatal error and kill the app.
/// Can be called from any thread at any time.
/// Provided message will be shown to the user if possible.
/// This will attempt to ship all accumulated logs to the master-server
/// so the standard Log() call can be used before this to include extra
/// info not relevant to the end user.
void FatalError(const std::string& message = "");

}  // namespace ballistica

#endif  // __cplusplus

#endif  // BALLISTICA_SHARED_BALLISTICA_H_
