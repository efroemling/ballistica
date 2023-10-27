// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_BASE_BUILD_SWITCHES_H_
#define BALLISTICA_BASE_SUPPORT_BASE_BUILD_SWITCHES_H_

#include "ballistica/base/base.h"

namespace ballistica::base {

/// Constructs various app components based on the current build config.
class BaseBuildSwitches {
 public:
  static auto CreateGraphics() -> Graphics*;
  static auto CreatePlatform() -> BasePlatform*;
  static auto CreateAppAdapter() -> AppAdapter*;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_BASE_BUILD_SWITCHES_H_
