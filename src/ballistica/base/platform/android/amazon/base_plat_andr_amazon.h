// Copyright (c) 2011-2022 Eric Froemling

#ifndef BALLISTICA_BASE_PLATFORM_ANDROID_AMAZON_BASE_PLAT_ANDR_AMAZON_H_
#define BALLISTICA_BASE_PLATFORM_ANDROID_AMAZON_BASE_PLAT_ANDR_AMAZON_H_
#if BA_AMAZON_BUILD

#include <string>

#include "ballistica/base/platform/android/base_platform_android.h"

namespace ballistica::base {

class BasePlatformAndroidAmazon : public BasePlatformAndroid {
 public:
  BasePlatformAndroidAmazon();
};

}  // namespace ballistica::base

#endif  // BA_AMAZON_BUILD
#endif  // BALLISTICA_BASE_PLATFORM_ANDROID_AMAZON_BASE_PLAT_ANDR_AMAZON_H_
