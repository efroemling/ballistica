// Copyright (c) 2011-2022 Eric Froemling

#ifndef BALLISTICA_BASE_PLATFORM_ANDROID_GOOGLE_BASE_PLAT_ANDR_GOOGLE_H_
#define BALLISTICA_BASE_PLATFORM_ANDROID_GOOGLE_BASE_PLAT_ANDR_GOOGLE_H_
#if BA_GOOGLE_BUILD

#include <string>
#include <vector>

#include "ballistica/base/platform/android/base_platform_android.h"

namespace ballistica::base {

class BasePlatformAndroidGoogle : public BasePlatformAndroid {
 public:
  BasePlatformAndroidGoogle();
};

}  // namespace ballistica::base

#endif  // BA_GOOGLE_BUILD
#endif  // BALLISTICA_BASE_PLATFORM_ANDROID_GOOGLE_BASE_PLAT_ANDR_GOOGLE_H_
