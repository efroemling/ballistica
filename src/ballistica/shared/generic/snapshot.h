// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_GENERIC_SNAPSHOT_H_
#define BALLISTICA_SHARED_GENERIC_SNAPSHOT_H_

#include "ballistica/shared/foundation/object.h"

namespace ballistica {

/// Wraps a const instance of some type in a logic-thread-owned Object. To
/// use this, allocate some object using new(), fill it out, and pass it to
/// this which will take ownership and expose it as a const.
template <typename T>
class Snapshot : public Object {
 public:
  explicit Snapshot(T* data) : data_{data} { assert(data); }
  ~Snapshot() { delete data_; }
  auto* Get() const { return data_; }

 private:
  const T* data_;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_GENERIC_SNAPSHOT_H_
