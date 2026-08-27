// Released under the MIT License. See LICENSE for details.
#if BA_XCODE_BUILD

#include "ballistica/base/app_adapter/app_adapter_apple.h"

#include <algorithm>
#include <functional>
#include <iterator>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/app_platform/apple/from_swift.h"
#include "ballistica/base/app_platform/apple/uikit_pasteboard.h"
#include "ballistica/base/app_platform/support/min_sdl_key_names.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/input/device/joystick_input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/input_types.h"

// clang-format off
// This needs to be below ballistica headers since it relies on
// some types in them but does not include headers itself.
#include <BallisticaKit-Swift.h>
// clang-format on

namespace ballistica::base {

/// RAII-friendly way to mark the thread and calls we're allowed to run graphics
/// stuff in.
class AppAdapterApple::ScopedAllowGraphics_ {
 public:
  explicit ScopedAllowGraphics_(AppAdapterApple* adapter) : adapter_{adapter} {
    // We currently assume only one thread will be doing this at any given
    // time; will need to add a lock if that's not always the case.
    assert(!adapter_->graphics_allowed_);
    // Keep graphics thread updated each time through since it can change.
    adapter->graphics_thread_ = std::this_thread::get_id();
    adapter->graphics_allowed_ = true;
  }
  ~ScopedAllowGraphics_() {
    assert(adapter_->graphics_allowed_);
    adapter_->graphics_allowed_ = false;
  }

 private:
  AppAdapterApple* adapter_;
};

auto AppAdapterApple::ManagesMainThreadEventLoop() const -> bool {
  // Nope; we run under a standard Cocoa/UIKit environment and they call us;
  // we don't call them.
  return false;
}

void AppAdapterApple::DoPushMainThreadRunnable(Runnable* runnable) {
  // Kick this along to swift.
  BallisticaKit::FromCpp::pushRawRunnableToMain(runnable);
}

void AppAdapterApple::OnMainThreadStartApp() {
  AppAdapter::OnMainThreadStartApp();
#if BA_USE_STORE_KIT
  BallisticaKit::StoreKitContext::onAppStart();
#endif
#if BA_USE_GAME_CENTER
  BallisticaKit::GameCenterContext::onAppStart();
#endif
}

void AppAdapterApple::ApplyAppConfig() { assert(g_base->InLogicThread()); }

void AppAdapterApple::ApplyGraphicsSettings(const GraphicsSettings* settings) {
  auto* graphics_server = g_base->graphics_server;

  // We need a full renderer reload if quality values have changed
  // or if we don't have a renderer yet.
  bool need_full_reload = ((graphics_server->texture_quality_requested()
                            != settings->texture_quality)
                           || (graphics_server->graphics_quality_requested()
                               != settings->graphics_quality));

  // We need a full renderer reload if quality values have changed or if we
  // don't yet have a renderer.

  if (need_full_reload) {
    ReloadRenderer_(settings);
  }
}

void AppAdapterApple::ReloadRenderer_(const GraphicsSettings* settings) {
  auto* gs = g_base->graphics_server;

  if (gs->renderer() && gs->renderer_loaded()) {
    gs->UnloadRenderer();
  }
  if (!gs->renderer()) {
    gs->set_renderer(new RendererGL());
  }

  // Update graphics quality based on request.
  gs->set_graphics_quality_requested(settings->graphics_quality);
  gs->set_texture_quality_requested(settings->texture_quality);

  // (Re)load stuff with these latest quality settings.
  gs->LoadRenderer();
}

auto AppAdapterApple::TryRender() -> bool {
  auto allow = ScopedAllowGraphics_(this);

  // Run & release any pending runnables.
  std::vector<Runnable*> calls;
  {
    // Pull calls off the list before running them; this way we only need to
    // grab the list lock for a moment.
    auto lock = std::scoped_lock(graphics_calls_mutex_);
    if (!graphics_calls_.empty()) {
      graphics_calls_.swap(calls);
    }
  }
  for (auto* call : calls) {
    call->RunAndLogErrors();
    delete call;
  }

  // Lastly, render.
  auto result = g_base->graphics_server->TryRender();

  // A little trick to make mac resizing look a lot smoother. Because we
  // render in a background thread, we often don't render at the most up to
  // date window size during a window resize. Normally this makes our image
  // jerk around in an ugly way, but if we just re-render once or twice in
  // those cases we mostly always get the most up to date window size.
  if (result && resize_friendly_frames_ > 0) {
    // Leave this enabled for just a few frames every time it is set.
    // (so just in case it breaks we won't draw each frame serveral times for
    // eternity).
    resize_friendly_frames_ -= 1;

    // Keep on drawing until the drawn window size
    // matches what we have (or until we try for too long or fail at drawing).
    seconds_t start_time = g_core->AppTimeSeconds();
    for (int i = 0; i < 5; ++i) {
      bool size_differs =
          ((std::abs(resize_target_resolution_.x
                     - g_base->graphics_server->screen_pixel_width())
            > 0.01f)
           || (std::abs(resize_target_resolution_.y
                        - g_base->graphics_server->screen_pixel_height())
               > 0.01f));
      if (size_differs && g_core->AppTimeSeconds() - start_time < 0.1
          && result) {
        result = g_base->graphics_server->TryRender();
      }
    }
  }

  return result;
}

void AppAdapterApple::EnableResizeFriendlyMode(int width, int height) {
  resize_friendly_frames_ = 5;
  resize_target_resolution_ = Vector2f(width, height);
}

auto AppAdapterApple::InGraphicsContext() -> bool {
  return std::this_thread::get_id() == graphics_thread_ && graphics_allowed_;
}

void AppAdapterApple::DoPushGraphicsContextRunnable(Runnable* runnable) {
  auto lock = std::scoped_lock(graphics_calls_mutex_);
  if (graphics_calls_.size() > 1000) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError, "graphics_calls_ got too big.");
  }
  graphics_calls_.push_back(runnable);
}

auto AppAdapterApple::ShouldUseCursor() -> bool {
  // On Mac of course we want our nice custom hardware cursor.
  if (g_buildconfig.platform_macos()) {
    return true;
  }

  // Anywhere else (iOS, tvOS, etc.) just say no cursor for now. The OS may
  // draw one in some cases (trackpad connected to iPad, etc.) but we don't
  // interfere and just let the OS draw its normal cursor in that case. Can
  // revisit this later if that becomes a more common scenario.
  return false;
}

auto AppAdapterApple::HasHardwareCursor() -> bool {
  // Only the Mac build uses a hardware (OS) cursor; iOS/tvOS/etc. have
  // none (DrawCursor() calls this unconditionally to pick the hardware-
  // vs software-cursor path, so we must answer for all Apple builds).
  return g_buildconfig.platform_macos();
}

void AppAdapterApple::SetHardwareCursorVisible(bool visible) {
  // (mac should be only build getting called here)
  assert(g_buildconfig.platform_macos());
  assert(g_core->InMainThread());

#if BA_PLATFORM_MACOS
  BallisticaKit::CocoaFromCpp::setCursorVisible(visible);
#endif
}

void AppAdapterApple::TerminateApp() {
#if BA_PLATFORM_MACOS
  BallisticaKit::CocoaFromCpp::terminateApp();
#else
  AppAdapter::TerminateApp();
#endif
}

auto AppAdapterApple::FullscreenControlAvailable() const -> bool {
  // Currently Mac only. Any window-management stuff elsewhere such as
  // iPadOS is out of our hands.
  if (g_buildconfig.platform_macos()) {
    return true;
  }
  return false;
}

auto AppAdapterApple::FullscreenControlGet() const -> bool {
#if BA_PLATFORM_MACOS
  // Read the value Swift pushes to us via OnFullscreenChanged (mirrors the
  // net-availability push model). This avoids a cross-thread Swift call from
  // the logic thread, where this getter runs.
  return fullscreen_control_value_.load();
#else
  return false;
#endif
}

std::atomic<bool> AppAdapterApple::fullscreen_control_value_{false};

void AppAdapterApple::OnFullscreenChanged(bool fullscreen) {
  // Pushed from Swift's NSWindow fullscreen delegate callbacks (main thread);
  // read on the logic thread via FullscreenControlGet. An atomic bool is all
  // the synchronization a single published flag needs. Static (no g_base
  // access) because window state restoration can fire this during launch
  // before the engine exists.
  fullscreen_control_value_.store(fullscreen);
}

void AppAdapterApple::SetUsingPointingDevice(bool pointing) {
  // Pushed from Swift's touch/pointer handling (main thread). We track the
  // last value here (main-thread-only, so no locking needed) and, on change,
  // hand the flip off to the logic thread where UI::SetTouchMode lives. This
  // mirrors Android's PlatformAndroid::PushUsingPointingDevice_.
  assert(g_core->InMainThread());
  if (pointing != using_pointing_device_) {
    using_pointing_device_ = pointing;
    g_base->logic->event_loop()->PushCall(
        [pointing] { g_base->ui->SetTouchMode(!pointing); });
  }
}

void AppAdapterApple::FullscreenControlSet(bool fullscreen) {
#if BA_PLATFORM_MACOS
  return BallisticaKit::CocoaFromCpp::setMainWindowFullscreen(fullscreen);
#endif
}

auto AppAdapterApple::FullscreenControlKeyShortcut() const
    -> std::optional<std::string> {
  return "fn+F";
}

/// How each feedback type is rendered through Core Haptics.
///
/// Two motor intensities and a duration -- deliberately the same shape
/// as the SDL table, because the hardware underneath turned out to be
/// the same hardware, reached through a different API.
///
/// The road here was not short (see D20-D22 in the initiative doc).
/// Core Haptics presents itself as intensity + *sharpness*, where
/// sharpness means the difference between a deep thump and a crisp tap.
/// Measured, sharpness does nothing at all: six events differing only in
/// sharpness, alternating between the extremes, are indistinguishable on
/// an Xbox controller, a DualShock 4, *and* a DualSense (Eric
/// 2026-08-03). Apple's bridge evidently derives one amplitude envelope
/// and discards the frequency content -- the same operation that costs
/// us kErmStartupMillisecs.
///
/// What does work is addressing the two grips separately. On every
/// controller tested, the left handle reads deep and the right handle
/// crisp -- on the DualSense as much as on the ERM pads. That is the
/// low-frequency/high-frequency motor pair SDL exposes directly, so
/// these values mean exactly what the SDL ones do and started as a port
/// of them.
/// Note this assumes left-handle == low-frequency and right-handle ==
/// high-frequency. That is the XInput convention Microsoft set with the
/// 360 pad and essentially everyone has followed since -- SDL's own API
/// bakes it in, and all three controllers tested here honor it,
/// including a DualSense whose voice coils have no inherent reason to
/// differ (Apple appears to emulate the convention deliberately).
///
/// But it *is* an assumption: GCHapticsLocality is documented as
/// spatial, not tonal, so Apple promises nothing about what lives in
/// which grip. The failure modes are gentle, which is what makes that
/// acceptable for a cosmetic effect -- symmetric actuators turn our
/// tonal split into a merely positional one, and a reversed controller
/// would feel inverted. Neither goes silent.
struct AppleTypeRender_ {
  /// Left handle: the heavy, low-frequency motor. Deep and rounded.
  float low;

  /// Right handle: the light, high-frequency motor. Sharp and buzzy.
  float high;

  /// A zero motor value means don't drive that actuator at all, so it
  /// must survive to the hardware as zero rather than as any floor.
  int duration_millisecs;
};

/// Indexed by FeedbackEvent::Type; see the static_assert below.
///
/// Durations are the wide-band intent; ERM adds kErmStartupMillisecs.
///
/// Note the four middle entries sit in a narrow 100-120ms band, so what
/// distinguishes them is mostly the motor mix rather than length. That
/// is not an accident of tuning -- shorter events kept reading as too
/// subtle to notice, so length ended up carrying less of the load than
/// first assumed and the mix carrying more.
static constexpr AppleTypeRender_ kAppleTypeRender[] = {
    // join -- both motors evenly; substantial and final.
    {0.5f, 0.5f, 140},
    // collect -- light motor alone. The lightest thing we emit, though
    // note that is now expressed through the mix rather than through
    // being brief; tuning found short events too easy to miss.
    {0.0f, 1.0f, 100},
    // grab -- light motor alone, a touch longer than a collect.
    {0.0f, 1.0f, 110},
    // impact-dealt -- leans light; crisp, confirming something you did.
    {0.4f, 0.6f, 100},
    // impact-received -- leans heavy; duller, something happened to you.
    {0.6f, 0.4f, 120},
    // death -- both motors at full, and by far the longest.
    {1.0f, 1.0f, 220},
};

/// What an ERM flywheel eats off the front of every event before
/// anything is felt: Apple's bridge extracting an amplitude envelope
/// from the haptic waveform and resampling it into motor commands, plus
/// the weight's own inertia.
///
/// Additive rather than a floor, deliberately. This is a fixed startup
/// cost, so perceived duration is roughly commanded minus this -- which
/// means long events need the same bump as short ones to land at their
/// intended weight, not just the ones that would otherwise fall under
/// the threshold.
///
/// Measured indirectly: isolated on an Xbox controller, 100ms is felt as
/// nothing and 120ms is felt, while SDL's direct motor drive is
/// perceptible on the same hardware at 60-80ms.
constexpr int kErmStartupMillisecs{50};

// Note there is deliberately no ERM *intensity* floor. One was tried
// (0.85, when everything went through a single `.default` engine) but it
// flattens the two-motor mix -- an impact-dealt at 0.4/0.6 becomes
// 0.85/0.85, which is precisely the distinction these values exist to
// draw. If light events prove imperceptible on ERM, the answer is a
// per-motor floor applied only to non-zero components, not a blanket
// one.

// Transients (instantaneous taps, layered over a body) were tried and
// removed. They render on a DualSense and a DualShock 4 but not on an
// Xbox controller -- a lone transient cannot overcome its heavier
// rotor's inertia, reproducible in four buttons of Apple's own
// HapticControllers sample. Unreliable across hardware, and the crispness
// they added is now available honestly through the high-frequency motor.

static_assert(std::size(kAppleTypeRender)
                  == static_cast<size_t>(FeedbackEvent::Type::kLast),
              "Every FeedbackEvent::Type needs an Apple render mapping, in"
              " enum order.");

auto AppAdapterApple::ApplyJoystickFeedback(JoystickInput* device,
                                            const FeedbackEvent& event) -> int {
  // Grab our addressing now, in the logic thread. The Swift layer is the
  // only thing that can turn this back into a GCController, and it must
  // be an id rather than the device pointer since the device can be gone
  // by the time our main-thread call runs.
  auto controller_id = device->platform_controller_id();
  if (controller_id < 0) {
    return 0;
  }

  auto index = static_cast<size_t>(event.type);
  assert(index < std::size(kAppleTypeRender));
  const auto& render = kAppleTypeRender[index];

  // Correct for the hardware, rather than baking the correction into
  // the table above and inflicting it on controllers that don't need it.
  auto duration_millisecs = render.duration_millisecs;
  if (!device->has_wide_band_haptics()) {
    duration_millisecs += kErmStartupMillisecs;
  }

  auto low = render.low;
  auto high = render.high;
  auto duration = static_cast<float>(duration_millisecs) / 1000.0f;
  PushMainThreadCall([controller_id, low, high, duration] {
    BallisticaKit::FromCpp::playControllerHaptic(controller_id, low, high,
                                                 duration);
  });
  return duration_millisecs;
}

void AppAdapterApple::StopJoystickFeedback(JoystickInput* device) {
  auto controller_id = device->platform_controller_id();
  if (controller_id < 0) {
    return;
  }
  PushMainThreadCall([controller_id] {
    BallisticaKit::FromCpp::stopControllerHaptic(controller_id);
  });
}

auto AppAdapterApple::HasDirectKeyboardInput() -> bool {
  // Mac feeds the engine real key and text events (see CocoaGLView), so
  // widgets can be edited inline there. iOS/tvOS deliver no text events
  // at all; editing goes through the platform string-editor dialog
  // instead (see AppPlatformApple::HaveStringEditor). Claiming direct
  // input there would leave widgets in an inline-edit state that no
  // typing can ever reach.
  return g_buildconfig.platform_macos();
};

auto AppAdapterApple::GetKeyRepeatDelay() -> float {
#if BA_PLATFORM_MACOS
  return BallisticaKit::CocoaFromCpp::getKeyRepeatDelay();
#else
  return AppAdapter::GetKeyRepeatDelay();
#endif
}

auto AppAdapterApple::GetKeyRepeatInterval() -> float {
#if BA_PLATFORM_MACOS
  return BallisticaKit::CocoaFromCpp::getKeyRepeatInterval();
#else
  return AppAdapter::GetKeyRepeatInterval();
#endif
}

auto AppAdapterApple::DoClipboardIsSupported() -> bool {
#if BA_PLATFORM_MACOS
  return BallisticaKit::CocoaFromCpp::clipboardIsSupported();
#elif BA_PLATFORM_IOS
  return true;
#else
  return AppAdapter::DoClipboardIsSupported();
#endif
}

auto AppAdapterApple::DoClipboardHasText() -> bool {
#if BA_PLATFORM_MACOS
  return BallisticaKit::CocoaFromCpp::clipboardHasText();
#elif BA_PLATFORM_IOS
  return UIKitPasteboardHasText();
#else
  return AppAdapter::DoClipboardHasText();
#endif
}

void AppAdapterApple::DoClipboardSetText(const std::string& text) {
#if BA_PLATFORM_MACOS
  BallisticaKit::CocoaFromCpp::clipboardSetText(text);
#elif BA_PLATFORM_IOS
  UIKitPasteboardSetText(text);
#else
  AppAdapter::DoClipboardSetText(text);
#endif
}

auto AppAdapterApple::DoClipboardGetText() -> std::string {
#if BA_PLATFORM_MACOS
  auto contents = BallisticaKit::CocoaFromCpp::clipboardGetText();
  if (contents) {
    return std::string(contents.get());
  }
  throw Exception("No text on clipboard.");
#elif BA_PLATFORM_IOS
  // Synchronous reads can block on an OS permission prompt here, which
  // would hang the logic thread; we deliberately support only the async
  // path (iOS shipped after the sync call was deprecated, so nothing
  // legitimately relies on this).
  BA_LOG_ONCE(LogName::kBa, LogLevel::kWarning,
              "Synchronous clipboard reads are not supported on this"
              " platform; use clipboard_get_text_async().");
  throw Exception(
      "Synchronous clipboard reads are not supported on this platform;"
      " use clipboard_get_text_async().",
      PyExcType::kRuntime);
#else
  return AppAdapter::DoClipboardGetText();
#endif
}

void AppAdapterApple::DoClipboardGetTextAsync(
    std::function<void(std::optional<std::string>)> completion_call) {
#if BA_PLATFORM_IOS
  assert(g_base->InLogicThread());

  // The completion may hold thread-affine state, so park it here on the
  // logic thread and send a state-free completion down to the ObjC
  // layer; results marshal back to the logic thread and complete FIFO
  // (safe since reads run on a serial queue, preserving order).
  clipboard_get_text_calls_.push_back(std::move(completion_call));
  UIKitPasteboardGetTextAsync([](std::optional<std::string> text) {
    // (Runs on the pasteboard background queue.)
    g_base->logic->event_loop()->PushCall([text = std::move(text)] {
      auto* adapter = AppAdapterApple::Get(g_base);
      assert(!adapter->clipboard_get_text_calls_.empty());
      auto call = std::move(adapter->clipboard_get_text_calls_.front());
      adapter->clipboard_get_text_calls_.pop_front();
      call(std::move(text));
    });
  });
#else
  AppAdapter::DoClipboardGetTextAsync(std::move(completion_call));
#endif
}

auto AppAdapterApple::GetKeyName(int keycode) -> std::string {
  return MinSDL_GetKeyName(keycode);
}

auto AppAdapterApple::NativeReviewRequestSupported() -> bool {
  // StoreKit currently supports this everywhere except tvOS.
  if (g_buildconfig.xcode_build() && g_buildconfig.use_store_kit()
      && !g_buildconfig.platform_tvos()) {
    return true;
  }
  return false;
}

void AppAdapterApple::DoNativeReviewRequest() {
#if BA_XCODE_BUILD && BA_USE_STORE_KIT && !BA_PLATFORM_TVOS
  BallisticaKit::StoreKitContext::requestReview();
#else
  FatalError("This should not be getting called.");
#endif
}

}  // namespace ballistica::base

#endif  // BA_XCODE_BUILD
