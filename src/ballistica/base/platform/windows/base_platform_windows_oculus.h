// Copyright (c) 2011-2022 Eric Froemling

#ifndef BALLISTICA_BASE_PLATFORM_WINDOWS_BASE_PLATFORM_WINDOWS_OCULUS_H_
#define BALLISTICA_BASE_PLATFORM_WINDOWS_BASE_PLATFORM_WINDOWS_OCULUS_H_
#if BA_RIFT_BUILD

#include "ballistica/base/platform/windows/base_platform_windows.h"

namespace ballistica::base {

class BasePlatformWindowsOculus : public BasePlatformWindows {
 public:
  BasePlatformWindowsOculus();
  void DoPurchase(const std::string& item) override;
  void PurchaseAck(const std::string& purchase,
                   const std::string& order_id) override;
};

}  // namespace ballistica::base

#endif  // BA_RIFT_BUILD
#endif  // BALLISTICA_BASE_PLATFORM_WINDOWS_BASE_PLATFORM_WINDOWS_OCULUS_H_
