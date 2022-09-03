// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_INTERNAL_INTERNAL_H_
#define BALLISTICA_INTERNAL_INTERNAL_H_

namespace ballistica {

/// Our high level app interface module.
/// It runs in the main thread and is what platform wrappers
/// should primarily interact with.
class AppInternalBase {
 public:
  virtual ~AppInternalBase() {}
};

}  // namespace ballistica

#endif  // BALLISTICA_INTERNAL_INTERNAL_H_
