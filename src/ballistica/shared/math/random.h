// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_MATH_RANDOM_H_
#define BALLISTICA_SHARED_MATH_RANDOM_H_

namespace ballistica {

/// Return a random float value. Not guaranteed to be deterministic or
/// consistent across platforms. Should do something better than this.
inline auto RandomFloat() -> float {
  // FIXME: should convert this to something thread-safe.
  return static_cast<float>(
      (static_cast<double>(rand()) / RAND_MAX));  // NOLINT
}

class Random {
 public:
  static void GenList1D(float* list, int size);
  static void GenList2D(float (*list)[2], int size);
  static void GenList3D(float (*list)[3], int size);
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_MATH_RANDOM_H_
