// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/foundation/fatal_error_report.h"

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <string>
#include <thread>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/platform.h"
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
auto BuildPayload(const std::string& message, const std::string& stack_trace)
    -> std::string {
  JsonBuilder builder;
  auto root = builder.root_object();

  root.Add("msg", Clamped(message, kMaxMessageLen));
  if (!stack_trace.empty()) {
    root.Add("trace", Clamped(stack_trace, kMaxTraceLen));
  }

  // Compile-time build identity; always available.
  root.Add("build", kEngineBuildNumber);
  root.Add("version", kEngineVersion);
  root.Add("platform", BA_PLATFORM);
  root.Add("arch", BA_ARCH);
  root.Add("variant", BA_VARIANT);
  // The developer-build macro does not exist in public builds, so the
  // preprocessor lines below are strip-marked and public gets the
  // plain false branch. Referencing that macro at all -- as a value,
  // in an #if, even in a comment -- fails the public-repo check.
  const bool devbuild = false;
  root.Add("devbuild", devbuild);
  root.Add("debugbuild", static_cast<bool>(BA_DEBUG_BUILD));

  // Wall-clock seconds. Taken from std::chrono rather than core's
  // helper so this stays usable with no core state.
  auto now = std::chrono::system_clock::now().time_since_epoch();
  root.Add("t",
           static_cast<int64_t>(
               std::chrono::duration_cast<std::chrono::seconds>(now).count()));

  // Cheap modded-build signals. These replace the old blessing-hash
  // mechanism, which needed the plus feature-set (often gone by the
  // time we get here) and a server-side build->masterhash lookup that
  // only ever existed on the v1 master-server. These three cost
  // nothing and catch obvious tinkering, which is all we need to keep
  // modded builds from drowning out real signal.
  if (g_core != nullptr) {
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

void SendFatalErrorReport(const std::string& message,
                          const std::string& stack_trace,
                          std::atomic<int>* result) {
  std::thread thread([message, stack_trace, result] {
    // Belt-and-braces: httplib is built with exceptions disabled above,
    // but string/json assembly can still throw (bad_alloc), and this
    // thread must never propagate out of a fatal handler.
    try {
      std::string payload = BuildPayload(message, stack_trace);

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
            std::string("Fatal-error report failed: ")
                + (response ? std::to_string(response->status)
                            : httplib::to_string(response.error())));
      }
    } catch (...) {
      if (result != nullptr) {
        *result = -1;
      }
    }
  });
  thread.detach();
}

}  // namespace ballistica
