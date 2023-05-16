// Copyright (c) 2011-2022 Eric Froemling

#if BA_RIFT_BUILD
#include "ballistica/base/platform/windows/base_platform_windows_oculus.h"

#include "ballistica/core/platform/oculus/oculus_utils.h"

namespace ballistica::base {

BasePlatformWindowsOculus::BasePlatformWindowsOculus() {}

void BasePlatformWindowsOculus::DoPurchase(const std::string& item) {
  core::OculusUtils::Purchase(item);
}

void BasePlatformWindowsOculus::PurchaseAck(const std::string& purchase,
                                            const std::string& order_id) {
  core::OculusUtils::ConsumePurchase(purchase);
}

}  // namespace ballistica::base

#endif  // BA_RIFT_BUILD
