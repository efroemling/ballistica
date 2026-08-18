// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_AUTOMATION_AUTOMATION_H_
#define BALLISTICA_BASE_AUTOMATION_AUTOMATION_H_

// Opt-in automation channel for in-process control of the running
// game from external tooling (test scripts, Claude Code, etc.). The
// entire mechanism is gated on BA_ENABLE_AUTOMATION (CMake
// -DENABLE_AUTOMATION=ON) so it is absent from default builds — no
// FIFO is created, no reader thread is spawned, no external code
// path can re-enable it.
//
// In builds that compile it in, the subsystem itself (which is what
// makes the automation_* native hooks live) is stood up on developer
// builds so any in-process Python — including remotely delivered
// code such as cloud-console exec — can drive the UI. On all other
// build flavors (including distributed test builds and server
// bundles) it exists only with the explicit local opt-in of the
// BA_AUTOMATION_FIFO environment variable. The FIFO itself is an
// optional local command entry point either way; see base.cc for
// the construction gate.
//
// Unstable, unsupported API — no backward-compatibility guarantees.
// The FIFO entry point is POSIX-only and interim (it goes away once
// automation rides the transport channel); on Windows only the
// hook-serving mode exists. Intentionally siloed from the rest of
// the engine: it owns its own directory, instantiation site, and
// Python-side helper module (babase/_automation.py). If the design
// needs to change, look here first.

#include "ballistica/shared/buildconfig/buildconfig_common.h"

#if BA_ENABLE_AUTOMATION

#include <atomic>
#include <string>
#include <thread>

namespace ballistica::base {

/// Hosts the automation capabilities (screenshot capture etc.; the
/// automation_* native hooks check for this object's presence) and
/// optionally reads newline-delimited Python commands from a named
/// FIFO, dispatching each onto the logic-thread event loop for
/// execution. The reader thread blocks on read(); destruction closes
/// the fd to unblock and join.
class Automation {
 public:
  /// With a non-empty ``fifo_path``, open the FIFO (creating it as a
  /// 0600 mkfifo if it doesn't exist) and launch the reader thread;
  /// on any FIFO setup failure logs an error and leaves the command
  /// entry point inert (capabilities stay live); never throws. With
  /// an empty path, no FIFO or reader thread exists — the subsystem
  /// serves only the native hooks.
  explicit Automation(std::string fifo_path);
  ~Automation();

  Automation(const Automation&) = delete;
  Automation& operator=(const Automation&) = delete;

  /// Capture the current framebuffer to a PNG file. Pushes the actual
  /// glReadPixels + encode + write onto the graphics thread; returns
  /// immediately. On completion (success or failure) emits a single
  /// ``[automation] <tag> ok|fail <payload>`` line via the standard
  /// automation logging convention. ``path`` should be absolute.
  void CaptureScreenshot(const std::string& path, const std::string& tag);

 private:
  void RunReader();
  void DispatchLine(const std::string& line);
  auto WaitForLogicEventLoop() -> bool;

  std::string fifo_path_;
  int fifo_fd_{-1};
  std::thread reader_thread_;
  std::atomic<bool> shutdown_{false};
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_AUTOMATION

#endif  // BALLISTICA_BASE_AUTOMATION_AUTOMATION_H_
