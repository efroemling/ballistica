// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_CRASH_INFO_H_
#define BALLISTICA_SHARED_FOUNDATION_CRASH_INFO_H_

#include <cstdint>
#include <string>

namespace ballistica {

/// Context captured for a native crash, readable from a crash handler.
///
/// A crash handler may not allocate, format, take locks, or
/// dereference engine objects -- the process state is untrusted and
/// g_core may be gone or corrupt. So everything a report will want is
/// mirrored into this plain struct as it becomes known, and the
/// handler does nothing but fill in the few fault fields and write the
/// bytes out. Conversion to the report's json happens on the *next*
/// launch, where allocation is fine.
///
/// Deliberately POD and flat. There is no blob to serialize, so there
/// is nothing that can be caught half-written: each field is an
/// independent scalar store and a stale value in one is harmless.
///
/// Values are recorded from the process that *crashed*, which is the
/// point -- a next-launch reporter is a different process and may even
/// be a different build if the user updated in between.
struct CrashInfo {
  /// Bumped when the layout changes, so a newer build's reader can
  /// tell what an older build's record looks like. Must stay first.
  uint32_t format_version;

  uint32_t build_number;
  /// Lifecycle bits at crash time: 1 = app-active, 2 = app-suspended.
  /// Cheap to maintain and answers "was it even in the foreground?",
  /// which changes how a crash should be read.
  uint32_t app_state;
  /// Engine update steps since launch. A rough "how far in" measure --
  /// paired with uptime it distinguishes a startup crash from one that
  /// took twenty minutes of play.
  uint64_t frame_number;
  uint64_t launch_time;  //< Epoch seconds; set at init.
  uint64_t crash_time;   //< Epoch seconds; set by the handler.

  /// Fault details, filled by the handler.
  uint64_t fault_code;
  uint64_t fault_address;
  uint64_t faulting_module_base;
  uint64_t access_address;
  uint32_t access_type;  //< 0 read, 1 write, 8 execute, else unknown.

  bool devbuild;
  bool debugbuild;
  bool modded;
  bool rancmds;
  bool workspaces;
  bool custompy;
  /// Whether g_core was alive at fault time. Distinguishes "we know
  /// these flags are right" from "we could not tell" -- the same
  /// distinction the fatal-error path draws with its 'coregone' field,
  /// but answered at the moment of the fault rather than at send time.
  bool core_alive;

  char version[32];
  char platform[24];
  char arch[24];
  char variant[32];
  /// GL/renderer identity (ANGLE version, backend, gpu, driver). Not
  /// in fatal-error reports today; a field crash report has no access
  /// to our logs, and reconstructing it afterwards is guesswork.
  char renderer[320];
  /// Module the fault address lands in, if the handler can name it.
  char faulting_module[96];
  /// OS version as the platform reports it; empty when it can't tell,
  /// or when the crash came before core was up to ask. Driver-level
  /// crashes often depend on OS build as much as on the driver itself.
  char os_version[64];
};

/// Current layout version of CrashInfo. Bump on ANY layout change: a
/// reader discards records whose version it doesn't know, which costs
/// one report across an upgrade, whereas misreading an old layout
/// would report garbage.
///
/// 2: added os_version.
const uint32_t kCrashInfoFormatVersion = 2;

/// Minidump user-stream type carrying a CrashInfo. Must be above
/// LastReservedStream (0xffff); the value itself is arbitrary.
const uint32_t kCrashInfoUserStreamType = 0x1000ba11;

/// Suffix for the standalone crash record written beside a dump.
const char* const kCrashRecordSuffix = ".crashinfo";
#if BA_PLATFORM_WINDOWS
#define kCrashRecordSuffixW L".crashinfo"
#endif

/// The process-wide instance. Plain storage the handler can always
/// read, valid from static-init onward.
extern CrashInfo g_crash_info;

/// Fill in compile-time identity and launch time. Safe to call early;
/// call before anything that might crash.
void CrashInfoInit();

/// Record the renderer identity string (copied, not referenced -- a
/// std::string's buffer can be freed or moved out from under us).
void CrashInfoSetRenderer(const std::string& val);

/// Record the OS version. Needs the platform, so call once core is up;
/// until then the field is empty and reports simply omit it.
void CrashInfoSetOSVersion(const std::string& val);

/// Refresh the values that change as the app runs, and advance the
/// step counter. Cheap enough to call per frame: a handful of scalar
/// stores and no formatting.
void CrashInfoUpdateRuntime(uint32_t app_state);

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_FOUNDATION_CRASH_INFO_H_
