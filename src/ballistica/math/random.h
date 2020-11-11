// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MATH_RANDOM_H_
#define BALLISTICA_MATH_RANDOM_H_

namespace ballistica {

class Random {
 public:
  static void GenList1D(float* list, int size);
  static void GenList2D(float (*list)[2], int size);
  static void GenList3D(float (*list)[3], int size);
};

}  // namespace ballistica

#endif  // BALLISTICA_MATH_RANDOM_H_
