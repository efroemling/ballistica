// Copyright (c) 2011-2022 Eric Froemling

#ifndef BALLISTICA_BASE_PLATFORM_ANDROID_BASE_PLATFORM_ANDROID_H_
#define BALLISTICA_BASE_PLATFORM_ANDROID_BASE_PLATFORM_ANDROID_H_
#if BA_OSTYPE_ANDROID

#include "ballistica/base/platform/base_platform.h"

namespace ballistica::base {

class BasePlatformAndroid : public BasePlatform {
 public:
  BasePlatformAndroid();
  void LoginAdapterGetSignInToken(const std::string& login_type,
                                  int attempt_id) override;
  void LoginAdapterBackEndActiveChange(const std::string& login_type,
                                       bool active) override;
  void DoPurchase(const std::string& item) override;
  void PurchaseAck(const std::string& purchase,
                   const std::string& order_id) override;
  void DoOpenURL(const std::string& url) override;
};

}  // namespace ballistica::base

#endif  // BA_OSTYPE_ANDROID

#endif  // BALLISTICA_BASE_PLATFORM_ANDROID_BASE_PLATFORM_ANDROID_H_
