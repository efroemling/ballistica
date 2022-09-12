// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BALLISTICA_H_
#define BALLISTICA_BALLISTICA_H_

// Try to ensure they're providing proper config stuff.
#ifndef BA_HAVE_CONFIG
#error ballistica platform config has not been defined!
#endif

#ifdef __cplusplus
#include <string>
#endif

// Minimum functionality we want available everywhere we are included.
#include "ballistica/core/exception.h"
#include "ballistica/core/inline.h"
#include "ballistica/core/macros.h"
#include "ballistica/core/types.h"

// BA 2.0 UI testing.
#define BA_TOOLBAR_TEST 0

#ifdef __cplusplus

namespace ballistica {

extern const int kAppBuildNumber;
extern const char* kAppVersion;

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
const int kDefaultTelnetPort = 43250;

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

// Sim step size in milliseconds.
const int kGameStepMilliseconds = 8;

// Sim step size in seconds.
const float kGameStepSeconds =
    (static_cast<float>(kGameStepMilliseconds) / 1000.0f);

// Globals.
extern int g_early_log_writes;
extern V1Account* g_v1_account;
extern AppFlavor* g_app_flavor;
extern AppConfig* g_app_config;
extern App* g_app;
extern AppInternal* g_app_internal;
extern Audio* g_audio;
extern AudioServer* g_audio_server;
extern BGDynamics* g_bg_dynamics;
extern BGDynamicsServer* g_bg_dynamics_server;
extern Context* g_context;
extern Graphics* g_graphics;
extern GraphicsServer* g_graphics_server;
extern Input* g_input;
extern Logic* g_logic;
extern Thread* g_main_thread;
extern Assets* g_assets;
extern AssetsServer* g_assets_server;
extern Networking* g_networking;
extern NetworkReader* g_network_reader;
extern NetworkWriter* g_network_writer;
extern Platform* g_platform;
extern Python* g_python;
extern StdioConsole* g_stdio_console;
extern TextGraphics* g_text_graphics;
extern UI* g_ui;
extern Utils* g_utils;

/// Main ballistica entry point.
auto BallisticaMain(int argc, char** argv) -> int;

/// Return a string that should be universally unique to this particular
/// running instance of the app.
auto GetAppInstanceUUID() -> const std::string&;

/// Have our main threads/modules all been inited yet?
auto IsBootstrapped() -> bool;

/// Does it appear that we are a blessed build with no known user-modifications?
auto IsUnmodifiedBlessedBuild() -> bool;

// The following is a smattering of convenience functions declared in our top
// level namespace. Functionality can be exposed here if it is used often
// enough that avoiding the extra class includes seems like an overall
// compile-time/convenience win.

// Print a momentary message on the screen.
auto ScreenMessage(const std::string& msg) -> void;
auto ScreenMessage(const std::string& msg, const Vector3f& color) -> void;

// Check current-threads.
auto InMainThread() -> bool;      // (main and graphics are same currently)
auto InGraphicsThread() -> bool;  // (main and graphics are same currently)
auto InLogicThread() -> bool;
auto InAudioThread() -> bool;
auto InBGDynamicsThread() -> bool;
auto InAssetsThread() -> bool;
auto InNetworkWriteThread() -> bool;

/// Return a human-readable name for the current thread.
auto GetCurrentThreadName() -> std::string;

/// Write a string to the log.
/// This will go to stdout, windows debug log, android log, etc.
/// A trailing newline will be added.
auto Log(const std::string& msg, bool to_stdout = true, bool to_server = true)
    -> void;

/// Log a fatal error and kill the app.
/// Can be called from any thread at any time.
/// Provided message will be shown to the user if possible.
/// This will attempt to ship all accumulated logs to the master-server
/// so the standard Log() call can be used before this to include extra
/// info not relevant to the end user.
auto FatalError(const std::string& message = "") -> void;

/// Are we running in a VR environment?
auto IsVRMode() -> bool;

/// Are we running headless?
inline auto HeadlessMode() -> bool {
  // (currently a build-time value but this could change later)
  return g_buildconfig.headless_build();
}

/// Return a lightly-filtered 'real' time value in milliseconds.
/// The value returned here will never go backwards or skip ahead
/// by significant amounts (even if the app has been sleeping or whatnot).
auto GetRealTime() -> millisecs_t;

/// Return a random float value. Not guaranteed to be deterministic or
/// consistent across platforms.
inline auto RandomFloat() -> float {
  // FIXME: should convert this to something thread-safe.
  return static_cast<float>(
      (static_cast<double>(rand()) / RAND_MAX));  // NOLINT
}

}  // namespace ballistica

#endif  // __cplusplus

#endif  // BALLISTICA_BALLISTICA_H_
