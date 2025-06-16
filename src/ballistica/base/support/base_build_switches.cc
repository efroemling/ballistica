// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/support/base_build_switches.h"

#if BA_PLATFORM_ANDROID
#include "ballistica/base/app_adapter/app_adapter_android.h"
#endif
#include "ballistica/base/app_adapter/app_adapter_apple.h"  // IWYU pragma: keep.
#include "ballistica/base/app_adapter/app_adapter_headless.h"  // IWYU pragma: keep.
#include "ballistica/base/app_adapter/app_adapter_sdl.h"
#include "ballistica/base/app_adapter/app_adapter_vr.h"  // IWYU pragma: keep.
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_vr.h"  // IWYU pragma: keep.
#include "ballistica/core/core.h"                  // IWYU pragma: keep.

// ------------------------- PLATFORM SELECTION --------------------------------

// This ugly chunk of macros simply pulls in the correct platform class
// header for each platform and defines the actual class that
// g_base->platform will be.

// Android ---------------------------------------------------------------------

#if BA_PLATFORM_ANDROID
#if BA_VARIANT_GOOGLE_PLAY
#include "ballistica/base/platform/android/google/base_plat_andr_google.h"
#define BA_BASE_PLATFORM_CLASS BasePlatformAndroidGoogle
#elif BA_VARIANT_AMAZON_APPSTORE
#include "ballistica/base/platform/android/amazon/base_plat_andr_amazon.h"
#define BA_BASE_PLATFORM_CLASS BasePlatformAndroidAmazon
#elif BA_VARIANT_CARDBOARD
#include "ballistica/base/platform/android/cardboard/base_pl_an_cardboard.h"
#define BA_BASE_PLATFORM_CLASS BasePlatformAndroidCardboard
#else  // Generic android.
#include "ballistica/base/platform/android/base_platform_android.h"
#define BA_BASE_PLATFORM_CLASS BasePlatformAndroid
#endif  // (Android subplatform)

// Apple -----------------------------------------------------------------------

#elif BA_PLATFORM_MACOS || BA_PLATFORM_IOS_TVOS
#include "ballistica/base/platform/apple/base_platform_apple.h"
#define BA_BASE_PLATFORM_CLASS BasePlatformApple

// Windows ---------------------------------------------------------------------

#elif BA_PLATFORM_WINDOWS
#if BA_RIFT_BUILD
#include "ballistica/base/platform/windows/base_platform_windows_oculus.h"
#define BA_BASE_PLATFORM_CLASS BasePlatformWindowsOculus
#else  // generic windows
#include "ballistica/base/platform/windows/base_platform_windows.h"
#define BA_BASE_PLATFORM_CLASS BasePlatformWindows
#endif  // windows subtype

// Linux -----------------------------------------------------------------------

#elif BA_PLATFORM_LINUX
#include "ballistica/base/platform/linux/base_platform_linux.h"
#define BA_BASE_PLATFORM_CLASS BasePlatformLinux
#else

// Generic ---------------------------------------------------------------------

#define BA_BASE_PLATFORM_CLASS BasePlatform

#endif

// ----------------------- END PLATFORM SELECTION ------------------------------

#ifndef BA_BASE_PLATFORM_CLASS
#error no BA_BASE_PLATFORM_CLASS defined for this platform
#endif

namespace ballistica::base {

auto BaseBuildSwitches::CreatePlatform() -> BasePlatform* {
  auto platform = new BA_BASE_PLATFORM_CLASS();
  platform->PostInit();
  assert(platform->ran_base_post_init());
  return platform;
}

auto BaseBuildSwitches::CreateGraphics() -> Graphics* {
#if BA_VR_BUILD
  return new GraphicsVR();
#else
  return new Graphics();
#endif
}

auto BaseBuildSwitches::CreateAppAdapter() -> AppAdapter* {
  assert(g_core);

  AppAdapter* app_adapter{};

#if BA_HEADLESS_BUILD
  app_adapter = new AppAdapterHeadless();
#elif BA_PLATFORM_ANDROID
  app_adapter = new AppAdapterAndroid();
#elif BA_XCODE_BUILD
  app_adapter = new AppAdapterApple();
#elif BA_RIFT_BUILD
  // Rift build can spin up in either VR or regular mode.
  if (g_core->vr_mode()) {
    app_adapter = new AppAdapterVR();
  } else {
    app_adapter = new AppAdapterSDL();
  }
#elif BA_VARIANT_CARDBOARD
  app_adapter = new AppAdapterVR();
#elif BA_SDL_BUILD
  app_adapter = new AppAdapterSDL();
#else
#error No app adapter defined for this build.
#endif

  assert(app_adapter);
  return app_adapter;
}

}  // namespace ballistica::base
