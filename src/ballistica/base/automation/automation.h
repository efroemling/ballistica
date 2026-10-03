// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_AUTOMATION_AUTOMATION_H_
#define BALLISTICA_BASE_AUTOMATION_AUTOMATION_H_

// Opt-in automation capability for in-process control of the running
// game from external tooling (test scripts, Claude Code, etc.). The
// whole mechanism is gated on BA_ENABLE_AUTOMATION (CMake
// -DENABLE_AUTOMATION=ON) so it is absent from default builds — no
// native hooks are compiled in, and no external code path can
// re-enable it.
//
// In builds that compile it in, this subsystem is stood up on
// developer builds so the automation_* native hooks (screenshot
// capture etc.) work for any in-process Python — including code
// delivered remotely over the automation channel
// (babase._automation / baplus._automationsession) or the cloud
// console. Commands and results ride the basn transport channel;
// this object holds only the capabilities the channel drives, not
// any transport of its own.
//
// Unstable, unsupported API — no backward-compatibility guarantees.
// Intentionally siloed from the rest of the engine: it owns its own
// directory, instantiation site, and Python-side helper modules. If
// the design needs to change, look here first.

#include "ballistica/shared/buildconfig/buildconfig_common.h"

#if BA_ENABLE_AUTOMATION

#include <mutex>
#include <string>
#include <vector>

namespace ballistica::base {

/// Hosts the automation capabilities (screenshot capture etc.). The
/// automation_* native hooks check for this object's presence; it is
/// created only where automation is both compiled in and permitted
/// (see base.cc).
class Automation {
 public:
  Automation() = default;

  Automation(const Automation&) = delete;
  Automation& operator=(const Automation&) = delete;

  /// Capture the current framebuffer to an image file; the path's
  /// extension picks the format (.jpg/.jpeg = lossy JPEG — the right
  /// default, small enough to move over the wire; anything else =
  /// lossless PNG, for when pixel-perfect data is actually needed).
  /// Queues the request; the actual glReadPixels + encode + write runs
  /// via RunPendingCaptures() at the tail of a frame render (the only
  /// point where the back buffer holds a complete, coherent frame).
  /// Returns immediately and may be called from any thread. On
  /// completion (success or failure) emits a single ``[automation]
  /// <tag> ok|fail <payload>`` line via the standard automation
  /// logging convention. ``path`` should be absolute.
  void CaptureScreenshot(const std::string& path, const std::string& tag);

  /// Service any queued screenshot captures. MUST be called from the
  /// graphics context immediately after a frame is fully drawn and
  /// before it is presented/swapped — that is the only moment the
  /// window framebuffer holds a complete frame (a readback done at an
  /// arbitrary point, e.g. via PushGraphicsContextCall, lands in the
  /// event-poll phase pre-draw when the post-swap back buffer is
  /// undefined, yielding torn/partial captures). Called from
  /// GraphicsServer::TryRender(); a no-op when nothing is queued.
  void RunPendingCaptures();

  /// Report the app's current OS-window size. Only functions where the
  /// app-adapter runs in a desktop window (SDL builds). Queues the query
  /// to the main thread and returns immediately; may be called from any
  /// thread. Emits ``[automation] <tag> ok <W>x<H>`` (logical units) or
  /// a structured fail line.
  void GetWindowSize(const std::string& tag);

  /// Resize the app's OS window. Only functions where the app-adapter
  /// runs in a desktop window (SDL builds) and only in windowed mode.
  /// Queues the resize to the main thread and returns immediately; may
  /// be called from any thread. Emits ``[automation] <tag> ok <W>x<H>``
  /// with the size actually applied (the OS may clamp; e.g. macOS to
  /// display bounds) or a structured fail line.
  void SetWindowSize(int width, int height, const std::string& tag);

 private:
  struct PendingCapture_ {
    std::string path;
    std::string tag;
  };
  std::mutex pending_captures_mutex_;
  std::vector<PendingCapture_> pending_captures_;
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_AUTOMATION

#endif  // BALLISTICA_BASE_AUTOMATION_AUTOMATION_H_
