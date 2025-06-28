// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_GENERIC_RUNNABLE_H_
#define BALLISTICA_SHARED_GENERIC_RUNNABLE_H_

#include "ballistica/shared/foundation/object.h"

namespace ballistica {

class Runnable : public Object {
 public:
  virtual void Run() = 0;

  void RunAndLogErrors();

  // These are used on lots of threads; we lock to whichever thread first
  // creates a reference to us.
  auto GetThreadOwnership() const -> ThreadOwnership override;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_GENERIC_RUNNABLE_H_
