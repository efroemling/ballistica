// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_CLASSIC_SOFT_H_
#define BALLISTICA_BASE_SUPPORT_CLASSIC_SOFT_H_

namespace ballistica::base {

/// 'Soft' interface to the classic feature-set.
/// Feature-sets listing classic as a soft requirement must limit their use of
/// it to these methods and should be prepared to handle the not-present
/// case.
class ClassicSoftInterface {
 public:
  virtual auto GetControllerValue(base::InputDevice* device,
                                  const std::string& value_name) -> int = 0;
  virtual auto GetControllerFloatValue(base::InputDevice* device,
                                       const std::string& value_name)
      -> float = 0;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_CLASSIC_SOFT_H_
