// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/foundation/fatal_error_report.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cinttypes>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <string>
#include <thread>
#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/foundation/crash_info.h"
#include "ballistica/shared/generic/json_facade.h"

// This is the one translation unit permitted to include cpp-httplib
// directly. The header is large (~22k lines, roughly +1.5s of compile
// time and +187k of linked binary), so confining it here keeps that
// cost paid exactly once. Same discipline json_facade.cc applies to
// yyjson. If a second consumer ever appears, wrap this in a small
// facade rather than including the header again.
//
// Tell httplib not to throw; this code runs inside a fatal-error
// handler where an escaping exception would cost us the report.
#define CPPHTTPLIB_NO_EXCEPTIONS
#include "external/cpp-httplib/httplib.h"

namespace ballistica {

using core::g_core;

namespace {

// Where fatal reports go.
//
// Hardcoded to PROD regardless of which fleet this build targets, and
// over plaintext http rather than https. Both are deliberate:
//
// - Plaintext because the report is sent from the lowest level we have,
//   with no TLS stack available down here (TLS in this engine lives
//   entirely in Python, via its ssl module and bundled certifi). Adding
//   native TLS would mean pulling OpenSSL into five platform build
//   systems to serve one POST. The tradeoff we are accepting is that
//   this data is unauthenticated and interceptable, so the server side
//   treats it as untrusted -- that is fine for "something died, here is
//   roughly what", which is all this channel is for.
//
// - Prod-always because non-prod fleets are https-only, so a
//   fleet-following reporter would silently go nowhere on dev/test
//   builds. http://regional.ballistica.net is an already-established
//   plaintext route (it is BA_FLEET_PROD_BOOTSTRAP_2 in
//   master_server_config.h), and it resolves to a basn node, which is
//   what serves this endpoint. Reports carry build/variant/dev-build
//   fields so non-prod traffic is filterable on the receiving end.
const char* kReportHost = "http://regional.ballistica.net";
const char* kReportPath = "/fatalerror";

/// Resolve the host to report to.
///
/// In developer builds only, BA_FATAL_REPORT_URL overrides the
/// hardcoded prod host so a report can be aimed at a specific basn
/// node (a dev/test-fleet node, or a local listener). This is what
/// lets the end-to-end test exercise the real path without depending
/// on prod. Mirrors BA_BOOTSTRAP_OVERRIDE in master_server_config.h;
/// like that one it is stripped entirely from shipped builds, so a
/// shipped client can never be redirected by its environment.
auto ReportHost() -> const char* {
  // Fixed in shipped builds; dev builds may override via env.
  return kReportHost;
}

// Keep the payload bounded. These are generous relative to a real
// message or trace but stop a pathological error string from turning
// each report into a large upload.
const size_t kMaxMessageLen = 8000;
const size_t kMaxTraceLen = 16000;

// Note these deliberately sum to more than the spin-wait in
// ReportFatalError. That wait -- not these -- is the user-facing cap on
// how long a dying app is held open; keeping it the binding constraint
// means user-visible delay stays fixed however these are tuned. The
// extra budget is not wasted: platforms that show a blocking fatal
// dialog give the send far more wall-clock than the wait does, so the
// full allowance gets used there. Where the wait wins instead, the
// in-flight report is simply lost at abort -- the same outcome as a
// timeout, so nothing rides on which fires first.
const int kConnectionTimeoutSeconds = 5;
const int kTransferTimeoutSeconds = 5;

auto Clamped(const std::string& value, size_t maxlen) -> std::string {
  if (value.size() <= maxlen) {
    return value;
  }
  return value.substr(0, maxlen) + "\n<clamped>";
}

/// Assemble the report payload.
///
/// Everything here is either passed in or a compile-time constant,
/// except the final block which is added only if g_core survived.
///
/// When `recorded` is non-null this is a crash from a *previous* run
/// being submitted on the next launch: identity and modded-flag values
/// then come from the record rather than from this process, which may
/// be a different build entirely.
auto BuildPayload(const std::string& message, const std::string& stack_trace,
                  const CrashInfo* recorded = nullptr) -> std::string {
  JsonBuilder builder;
  auto root = builder.root_object();

  root.Add("msg", Clamped(message, kMaxMessageLen));
  if (!stack_trace.empty()) {
    root.Add("trace", Clamped(stack_trace, kMaxTraceLen));
  }

  // Build identity: compile-time for a live fatal error, recorded for
  // a past crash.
  if (recorded != nullptr) {
    root.Add("build", static_cast<int64_t>(recorded->build_number));
    root.Add("version", recorded->version);
    root.Add("platform", recorded->platform);
    root.Add("arch", recorded->arch);
    root.Add("variant", recorded->variant);
  } else {
    root.Add("build", kEngineBuildNumber);
    root.Add("version", kEngineVersion);
    root.Add("platform", BA_PLATFORM);
    root.Add("arch", BA_ARCH);
    root.Add("variant", BA_VARIANT);
  }

  // OS version. A live fatal error reads the value recorded at startup
  // rather than asking the platform now: that keeps platform code out of
  // a dying process, and g_crash_info is plain static storage that is
  // always safe to read. Empty means unknown -- the platform couldn't
  // tell, or we died before core came up to ask -- and the field is
  // then omitted rather than sent blank.
  const char* os_version =
      recorded != nullptr ? recorded->os_version : g_crash_info.os_version;
  if (os_version[0] != '\0') {
    root.Add("osver", os_version);
  }
  // The developer-build macro does not exist in public builds, so the
  // preprocessor lines below are strip-marked and public gets the
  // plain false branch. Referencing that macro at all -- as a value,
  // in an #if, even in a comment -- fails the public-repo check.
  const bool devbuild = false;
  root.Add("devbuild", recorded != nullptr ? recorded->devbuild : devbuild);
  root.Add("debugbuild", recorded != nullptr
                             ? recorded->debugbuild
                             : static_cast<bool>(BA_DEBUG_BUILD));

  // Wall-clock seconds. Taken from std::chrono rather than core's
  // helper so this stays usable with no core state. For a recorded
  // crash this is when the crash happened, not when we got around to
  // reporting it -- those can be days apart.
  if (recorded != nullptr) {
    root.Add("t", static_cast<int64_t>(recorded->crash_time));
  } else {
    auto now = std::chrono::system_clock::now().time_since_epoch();
    root.Add(
        "t",
        static_cast<int64_t>(
            std::chrono::duration_cast<std::chrono::seconds>(now).count()));
  }

  // Crash-specific context. Only present for a recorded native crash;
  // a live fatal error has no fault address and its location is
  // already in the message/trace.
  if (recorded != nullptr) {
    root.Add("crash", true);
    root.Add("excode", static_cast<int64_t>(recorded->fault_code));
    root.Add("exaddr", static_cast<int64_t>(recorded->fault_address));
    root.Add("acctype", static_cast<int64_t>(recorded->access_type));
    root.Add("accaddr", static_cast<int64_t>(recorded->access_address));
    if (recorded->faulting_module[0] != '\0') {
      root.Add("module", recorded->faulting_module);
      // The offset is what archived symbols resolve against.
      root.Add("modoffset",
               static_cast<int64_t>(recorded->fault_address
                                    - recorded->faulting_module_base));
    }
    if (recorded->renderer[0] != '\0') {
      root.Add("renderer", recorded->renderer);
    }
    root.Add("appstate", static_cast<int64_t>(recorded->app_state));
    root.Add("frame", static_cast<int64_t>(recorded->frame_number));
    root.Add("uptime", static_cast<int64_t>(recorded->crash_time
                                            - recorded->launch_time));
  }

  // Cheap modded-build signals. These replace the old blessing-hash
  // mechanism, which needed the plus feature-set (often gone by the
  // time we get here) and a server-side build->masterhash lookup that
  // only ever existed on the v1 master-server. These three cost
  // nothing and catch obvious tinkering, which is all we need to keep
  // modded builds from drowning out real signal.
  if (recorded != nullptr) {
    // Mirrored from the crashed process as it ran, so these are its
    // values rather than ours. core_alive answers the same question
    // 'coregone' does, but as of the moment of the fault.
    if (recorded->core_alive) {
      root.Add("modded", recorded->modded);
      root.Add("rancmds", recorded->rancmds);
      root.Add("workspaces", recorded->workspaces);
      root.Add("custompy", recorded->custompy);
    } else {
      root.Add("coregone", true);
    }
  } else if (g_core != nullptr) {
    root.Add("modded", g_core->user_ran_commands || g_core->workspaces_in_use
                           || g_core->using_custom_app_python_dir());
    root.Add("rancmds", g_core->user_ran_commands);
    root.Add("workspaces", g_core->workspaces_in_use);
    root.Add("custompy", g_core->using_custom_app_python_dir());
  } else {
    // Distinguish "we know it is clean" from "we could not tell".
    root.Add("coregone", true);
  }

  return builder.Write();
}

}  // namespace

/// Post an already-assembled payload. Shared by the live fatal path
/// and the next-launch crash submit so both get the same timeouts,
/// error handling and never-throw discipline.
void PostPayload(const std::string& payload, std::atomic<int>* result,
                 const char* what) {
  httplib::Client client{ReportHost()};
  client.set_connection_timeout(kConnectionTimeoutSeconds, 0);
  client.set_read_timeout(kTransferTimeoutSeconds, 0);
  client.set_write_timeout(kTransferTimeoutSeconds, 0);

  auto response = client.Post(kReportPath, payload, "application/json");

  // httplib returns a falsy Result rather than throwing, so a
  // network failure lands here as a plain value.
  bool ok = response && response->status >= 200 && response->status < 300;
  if (result != nullptr) {
    *result = ok ? 1 : -1;
  }
  if (!ok && g_core != nullptr) {
    g_core->platform->EmitPlatformLog(
        "root", LogLevel::kError,
        std::string(what) + " report failed: "
            + (response ? std::to_string(response->status)
                        : httplib::to_string(response.error())));
  }
}

void SendFatalErrorReport(const std::string& message,
                          const std::string& stack_trace,
                          std::atomic<int>* result) {
  std::thread thread([message, stack_trace, result] {
    // Belt-and-braces: httplib is built with exceptions disabled above,
    // but string/json assembly can still throw (bad_alloc), and this
    // thread must never propagate out of a fatal handler.
    try {
      std::string payload = BuildPayload(message, stack_trace);
      PostPayload(payload, result, "Fatal-error");
    } catch (...) {
      if (result != nullptr) {
        *result = -1;
      }
    }
  });
  thread.detach();
}

void SubmitPendingCrashReport() {
  // Only the platforms with a native crash handler leave records; on
  // the rest this is a no-op scan that finds nothing.
  std::string path = g_core != nullptr
                         ? g_core->platform->GetPendingCrashRecordPath()
                         : std::string();
  if (path.empty()) {
    return;
  }

  CrashInfo info{};
  {
    FILE* infile = fopen(path.c_str(), "rb");
    if (infile == nullptr) {
      return;
    }
    size_t got = fread(&info, 1, sizeof(info), infile);
    fclose(infile);
    // Whatever happens below, do not leave the record to be retried
    // forever: a record we cannot use is a record we will never be
    // able to use, and a crash-looping app would otherwise report the
    // same failure every launch.
    remove(path.c_str());
    if (got != sizeof(info) || info.format_version != kCrashInfoFormatVersion) {
      if (g_core != nullptr) {
        g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kWarning,
                             "Discarding unreadable crash record (got "
                                 + std::to_string(got) + " bytes, format "
                                 + std::to_string(info.format_version) + ").");
      }
      return;
    }
  }

  // Build a message in the shape a reader already expects from this
  // channel, then hand it to the same transport.
  std::string message = "CRASH: ";
  char codebuf[32];
  snprintf(codebuf, sizeof(codebuf), "0x%08" PRIX64, info.fault_code);
  message += codebuf;
  std::string location;
  if (info.faulting_module[0] != '\0') {
    // Hex, because that is the form symbol tooling wants pasted in.
    char offbuf[32];
    snprintf(offbuf, sizeof(offbuf), "+0x%" PRIx64,
             info.fault_address - info.faulting_module_base);
    location = std::string(info.faulting_module) + offbuf;
    message += " in " + location;
  }

  if (g_core != nullptr) {
    g_core->logging->Log(
        LogName::kBaLifecycle, LogLevel::kInfo,
        "Submitting crash report from previous run ("
            + (location.empty() ? std::string("no module") : location) + ").");
  }

  CrashInfo captured = info;
  std::thread thread([message, captured] {
    try {
      std::string payload = BuildPayload(message, "", &captured);
      PostPayload(payload, nullptr, "Crash");
    } catch (...) {
      // Never let a report failure disturb a launch.
    }
  });
  thread.detach();
}

// ---------------------------------------------------------------------------
// Deferred fatal-error reports.
//
// A live fatal-error report is sent once, from the dying process; if the
// network isn't reachable right then it is simply lost. On developer
// builds that also means *no trace at all*: those exit(1) rather than
// abort() so they don't pollute crash reporting, so there is no OS crash
// report either. A fatal error right after an iOS app resumes from the
// background -- network not back yet -- looked exactly like the app
// silently vanishing. So an undelivered report is written to disk and
// sent on the next launch, the same way native crash records are.

namespace {

// Where deferred reports go (the app's config dir; see
// SetPendingFatalReportDir). Fixed-size static storage: a dying process
// must never have to call into core or platform code to find it. Empty
// = not known yet, nothing can be deferred.
char g_pending_fatal_report_dir[1024]{};

const char* kPendingFatalReportPrefix = "fatal_report_";
const char* kPendingFatalReportSuffix = ".json";

// Far above any real payload (message + trace are clamped to 24k), and
// a guard against reading something unexpected into memory.
const uintmax_t kMaxPendingFatalReportBytes = 64 * 1024;

auto IsPendingFatalReportName(const std::string& name) -> bool {
  std::string prefix{kPendingFatalReportPrefix};
  std::string suffix{kPendingFatalReportSuffix};
  return name.size() > prefix.size() + suffix.size()
         && name.compare(0, prefix.size(), prefix) == 0
         && name.compare(name.size() - suffix.size(), suffix.size(), suffix)
                == 0;
}

/// The report's message, for a local log line: the first "msg" value,
/// raw (still JSON-escaped) and shortened. Good enough to see at a
/// glance what died without pulling in a JSON parser here.
auto PeekMessage(const std::string& payload) -> std::string {
  const std::string key = "\"msg\":\"";
  auto start = payload.find(key);
  if (start == std::string::npos) {
    return "<no message>";
  }
  start += key.size();
  size_t end = start;
  while (end < payload.size() && payload[end] != '"') {
    // Skip escaped characters, quotes included.
    end += payload[end] == '\\' ? 2 : 1;
  }
  std::string msg =
      payload.substr(start, std::min(end, payload.size()) - start);
  const size_t max_len = 300;
  if (msg.size() > max_len) {
    msg = msg.substr(0, max_len) + "...";
  }
  return msg;
}

}  // namespace

void SetPendingFatalReportDir(const std::string& dir) {
  // A truncated path would point somewhere wrong; better to defer
  // nothing than to write reports where no launch will look.
  if (dir.empty() || dir.size() >= sizeof(g_pending_fatal_report_dir)) {
    return;
  }
  snprintf(g_pending_fatal_report_dir, sizeof(g_pending_fatal_report_dir), "%s",
           dir.c_str());
}

void SavePendingFatalReport(const std::string& message,
                            const std::string& stack_trace) {
  if (g_pending_fatal_report_dir[0] == '\0') {
    return;
  }
  try {
    namespace fs = std::filesystem;
    std::error_code ec;
    fs::path dir{g_pending_fatal_report_dir};
    fs::create_directories(dir, ec);
    if (ec) {
      return;
    }
    // Seconds are plenty to order these (and newest wins anyway); the
    // payload itself carries the precise time.
    auto now = std::chrono::system_clock::now().time_since_epoch();
    auto secs = std::chrono::duration_cast<std::chrono::seconds>(now).count();
    fs::path path = dir
                    / (std::string(kPendingFatalReportPrefix)
                       + std::to_string(secs) + kPendingFatalReportSuffix);
    std::string payload = BuildPayload("DEFERRED: " + message, stack_trace);
    FILE* outfile = fopen(path.string().c_str(), "wb");
    if (outfile == nullptr) {
      return;
    }
    fwrite(payload.data(), 1, payload.size(), outfile);
    fclose(outfile);
  } catch (...) {
    // Best-effort; nothing thrown here may escape a fatal handler.
  }
}

void SubmitPendingFatalReports() {
  if (g_pending_fatal_report_dir[0] == '\0') {
    return;
  }
  namespace fs = std::filesystem;
  std::string payload;
  std::string newest;
  size_t pending_count{};
  try {
    std::error_code ec;
    fs::path dir{g_pending_fatal_report_dir};
    if (!fs::is_directory(dir, ec)) {
      return;  // The common case: nothing ever deferred.
    }
    std::vector<fs::path> reports;
    for (const auto& entry : fs::directory_iterator(dir, ec)) {
      if (IsPendingFatalReportName(entry.path().filename().string())) {
        reports.push_back(entry.path());
      }
    }
    if (reports.empty()) {
      return;
    }
    pending_count = reports.size();
    // Names embed a unix timestamp of fixed width for any date we'll
    // see, so lexicographic order is chronological; newest wins.
    std::sort(reports.begin(), reports.end());
    newest = reports.back().string();
    auto size = fs::file_size(reports.back(), ec);
    if (!ec && size > 0 && size <= kMaxPendingFatalReportBytes) {
      FILE* infile = fopen(newest.c_str(), "rb");
      if (infile != nullptr) {
        payload.resize(static_cast<size_t>(size));
        size_t got = fread(payload.data(), 1, payload.size(), infile);
        fclose(infile);
        payload.resize(got);
      }
    }
    // Whatever happens next, none of these get looked at again: a
    // crash-looping app must not report the same failure every launch.
    for (const auto& report : reports) {
      fs::remove(report, ec);
    }
  } catch (...) {
    return;
  }

  if (payload.empty()) {
    if (g_core != nullptr) {
      g_core->logging->Log(
          LogName::kBaLifecycle, LogLevel::kWarning,
          "Discarded unreadable deferred fatal-error report (" + newest + ").");
    }
    return;
  }

  if (g_core != nullptr) {
    // Loud in developer builds: a previous run died and (being a dev
    // build) left no OS crash report, so this may be the only place
    // anyone sees it. Quieter in shipped builds, where the server-side
    // report is what matters and a warning would trip log reports.
    const LogLevel level = LogLevel::kInfo;
    g_core->logging->Log(
        LogName::kBaLifecycle, level,
        "Previous run ended in a fatal error that couldn't be reported at"
        " the time; reporting it now"
            + (pending_count > 1
                   ? " (newest of " + std::to_string(pending_count) + ")"
                   : std::string())
            + ": " + PeekMessage(payload));
  }

  std::thread thread([payload] {
    try {
      PostPayload(payload, nullptr, "Deferred fatal-error");
    } catch (...) {
      // Never let a report failure disturb a launch.
    }
  });
  thread.detach();
}

}  // namespace ballistica
