// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/platform/base_platform.h"

#include <csignal>

#include "ballistica/base/base.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/platform/support/min_sdl_key_names.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_sys.h"

#if BA_VR_BUILD
#include "ballistica/base/app/app_vr.h"
#endif

#if BA_HEADLESS_BUILD
#include "ballistica/base/app/app_headless.h"
#endif

#include "ballistica/base/app/app.h"
#include "ballistica/base/app/sdl_app.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_vr.h"

// ------------------------- PLATFORM SELECTION --------------------------------

// This ugly chunk of macros simply pulls in the correct platform class header
// for each platform and defines the actual class g_base->platform will be.

// Android ---------------------------------------------------------------------

#if BA_OSTYPE_ANDROID
#if BA_GOOGLE_BUILD
#include "ballistica/base/platform/android/google/base_plat_andr_google.h"
#define BA_PLATFORM_CLASS BasePlatformAndroidGoogle
#elif BA_AMAZON_BUILD
#include "ballistica/base/platform/android/amazon/base_plat_andr_amazon.h"
#define BA_PLATFORM_CLASS BasePlatformAndroidAmazon
#elif BA_CARDBOARD_BUILD
#include "ballistica/base/platform/android/cardboard/base_pl_an_cardboard.h"
#define BA_PLATFORM_CLASS BasePlatformAndroidCardboard
#else  // Generic android.
#include "ballistica/base/platform/android/base_platform_android.h"
#define BA_PLATFORM_CLASS BasePlatformAndroid
#endif  // (Android subplatform)

// Apple -----------------------------------------------------------------------

#elif BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS
#include "ballistica/base/platform/apple/base_platform_apple.h"
#define BA_PLATFORM_CLASS BasePlatformApple

// Windows ---------------------------------------------------------------------

#elif BA_OSTYPE_WINDOWS
#if BA_RIFT_BUILD
#include "ballistica/base/platform/windows/base_platform_windows_oculus.h"
#define BA_PLATFORM_CLASS BasePlatformWindowsOculus
#else  // generic windows
#include "ballistica/base/platform/windows/base_platform_windows.h"
#define BA_PLATFORM_CLASS BasePlatformWindows
#endif  // windows subtype

// Linux -----------------------------------------------------------------------

#elif BA_OSTYPE_LINUX
#include "ballistica/base/platform/linux/base_platform_linux.h"
#define BA_PLATFORM_CLASS BasePlatformLinux
#else

// Generic ---------------------------------------------------------------------

#define BA_PLATFORM_CLASS BasePlatform

#endif

// ----------------------- END PLATFORM SELECTION ------------------------------

#ifndef BA_PLATFORM_CLASS
#error no BA_PLATFORM_CLASS defined for this platform
#endif

namespace ballistica::base {

auto BasePlatform::CreatePlatform() -> BasePlatform* {
  auto platform = new BA_PLATFORM_CLASS();
  platform->PostInit();
  assert(platform->ran_base_post_init_);
  return platform;
}

BasePlatform::BasePlatform() = default;

void BasePlatform::PostInit() {
  // Make sure any overrides remember to call us.
  ran_base_post_init_ = true;
}

BasePlatform::~BasePlatform() = default;

auto BasePlatform::CreateApp() -> App* {
  assert(g_core);
  // assert(InMainThread());
  // assert(g_main_thread);

// TEMP - need to init sdl on our legacy mac build even though its not
// technically an SDL app. Kill this once the old mac build is gone.
#if BA_LEGACY_MACOS_BUILD
  SDLApp::InitSDL();
#endif

  App* app{};

#if BA_HEADLESS_BUILD
  app = new AppHeadless(g_core->main_event_loop());
#elif BA_RIFT_BUILD
  // Rift build can spin up in either VR or regular mode.
  if (g_core->vr_mode) {
    app = new AppVR(g_core->main_event_loop());
  } else {
    app = new SDLApp(g_core->main_event_loop());
  }
#elif BA_CARDBOARD_BUILD
  app = new AppVR(g_core->main_event_loop());
#elif BA_SDL_BUILD
  app = new SDLApp(g_core->main_event_loop());
#else
  app = new App(g_core->main_event_loop());
#endif

  assert(app);
  app->PostInit();
  return app;
}

auto BasePlatform::CreateGraphics() -> Graphics* {
#if BA_VR_BUILD
  return new GraphicsVR();
#else
  return new Graphics();
#endif
}

auto BasePlatform::GetKeyName(int keycode) -> std::string {
  // On our actual SDL platforms we're trying to be *pure* sdl so
  // call their function for this. Otherwise we call our own version
  // of it which is basically the same thing (at least for now).
#if BA_SDL_BUILD && !BA_MINSDL_BUILD
  return SDL_GetKeyName(static_cast<SDL_Keycode>(keycode));
#elif BA_MINSDL_BUILD
  return MinSDL_GetKeyName(keycode);
#else
  Log(LogLevel::kWarn, "CorePlatform::GetKeyName not implemented here.");
  return "?";
#endif
}

void BasePlatform::LoginAdapterGetSignInToken(const std::string& login_type,
                                              int attempt_id) {
  // Default implementation simply calls completion callback immediately.
  g_base->logic->event_loop()->PushCall([login_type, attempt_id] {
    PythonRef args(Py_BuildValue("(sss)", login_type.c_str(),
                                 std::to_string(attempt_id).c_str(), ""),
                   PythonRef::kSteal);
    g_base->python->objs()
        .Get(BasePython::ObjID::kLoginAdapterGetSignInTokenResponseCall)
        .Call(args);
  });
}

void BasePlatform::LoginAdapterBackEndActiveChange(
    const std::string& login_type, bool active) {
  // Default is no-op.
}

auto BasePlatform::GetPublicDeviceUUID() -> std::string {
  assert(g_core);

  if (public_device_uuid_.empty()) {
    std::list<std::string> inputs{g_core->platform->GetDeviceUUIDInputs()};

    // This UUID is supposed to change periodically, so let's plug in
    // some stuff to enforce that.
    inputs.emplace_back(g_core->platform->GetOSVersionString());

    // This part gets shuffled periodically by my version-increment tools.
    // We used to plug version in directly here, but that caused uuids to
    // shuffle too rapidly during periods of rapid development. This
    // keeps it more constant.
    // __last_rand_uuid_component_shuffle_date__ 2023 6 15
    auto rand_uuid_component{"JVRWZ82D4WMBO110OA0IFJV7JKMQV8W3"};

    inputs.emplace_back(rand_uuid_component);
    auto gil{Python::ScopedInterpreterLock()};
    auto pylist{Python::StringList(inputs)};
    auto args{Python::SingleMemberTuple(pylist)};
    auto result = g_base->python->objs()
                      .Get(base::BasePython::ObjID::kHashStringsCall)
                      .Call(args);
    assert(result.UnicodeCheck());
    public_device_uuid_ = result.Str();
  }
  return public_device_uuid_;
}

void BasePlatform::Purchase(const std::string& item) {
  // We use alternate _c ids for consumables in some cases where
  // we originally used entitlements. We are all consumables now though
  // so we can purchase for different accounts.
  std::string item_filtered{item};
  if (g_buildconfig.amazon_build()) {
    if (item == "bundle_bones" || item == "bundle_bernard"
        || item == "bundle_frosty" || item == "bundle_santa" || item == "pro"
        || item == "pro_sale") {
      item_filtered = item + "_c";
    }
  }
  DoPurchase(item_filtered);
}

void BasePlatform::DoPurchase(const std::string& item) {
  // Just print 'unavailable' by default.
  g_base->python->objs().PushCall(
      base::BasePython::ObjID::kUnavailableMessageCall);
}

void BasePlatform::RestorePurchases() {
  Log(LogLevel::kError, "RestorePurchases() unimplemented");
}

void BasePlatform::PurchaseAck(const std::string& purchase,
                               const std::string& order_id) {
  Log(LogLevel::kError, "PurchaseAck() unimplemented");
}

void BasePlatform::OpenURL(const std::string& url) {
  // Can't open URLs in VR - just tell the Python layer to show the url in the
  // gui.
  if (g_core->IsVRMode()) {
    g_base->ui->ShowURL(url);
    return;
  }

  // Otherwise fall back to our platform-specific handler.
  g_base->platform->DoOpenURL(url);
}

void BasePlatform::DoOpenURL(const std::string& url) {
  // Kick this over to logic thread so we're safe to call from anywhere.
  g_base->logic->event_loop()->PushCall(
      [url] { g_base->python->OpenURLWithWebBrowserModule(url); });
}

#if !BA_OSTYPE_WINDOWS
static void HandleSIGINT(int s) {
  if (g_base->logic) {
    g_base->logic->event_loop()->PushCall(
        [] { g_base->logic->HandleInterruptSignal(); });
  } else {
    Log(LogLevel::kError, "SigInt handler called before g_logic exists.");
  }
}
#endif

void BasePlatform::SetupInterruptHandling() {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  struct sigaction handler {};
  handler.sa_handler = HandleSIGINT;
  sigemptyset(&handler.sa_mask);
  handler.sa_flags = 0;
  sigaction(SIGINT, &handler, nullptr);
#endif
}

void BasePlatform::GetCursorPosition(float* x, float* y) {
  assert(x && y);

  // By default, just use our latest event-delivered cursor position;
  // this should work everywhere though perhaps might not be most optimal.
  if (g_base->input == nullptr) {
    *x = 0.0f;
    *y = 0.0f;
    return;
  }
  *x = g_base->input->cursor_pos_x();
  *y = g_base->input->cursor_pos_y();
}

}  // namespace ballistica::base
