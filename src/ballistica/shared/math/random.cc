// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/math/random.h"

#include <cassert>
#include <memory>
#include <vector>

namespace ballistica {

static auto rand_range(float min, float max) -> float {
  return min
         + (static_cast<float>(rand())  // NOLINT
            / static_cast<float>(RAND_MAX))
               * (max - min);
}

class SmoothGen1D {
 public:
  SmoothGen1D() = default;
  ~SmoothGen1D() = default;
  auto GetX(int index) -> float {
    Expand(static_cast<uint32_t>(index));
    return vals_x[index];
  }

 private:
  void Expand(uint32_t index) {
    if (index >= vals_x.size()) {
      if (vals_x.empty()) {
        float initial_x = rand_range(0.0f, 1.0f);
        root = std::make_unique<Node>(0, 1, initial_x);
        vals_x.push_back(initial_x);
      }
      for (auto i = static_cast<uint32_t>(vals_x.size()); i <= index; i++) {
        float x;
        root->GetNewValue(&x);
        vals_x.push_back(x);
      }
    }
  }

  class Node {
   public:
    Node(float min_x_in, float max_x_in, float first_val_x)
        : min_x(min_x_in), max_x(max_x_in) {
      // Store our initial value in the right section.
      assert(first_val_x >= min_x && first_val_x <= max_x);

      float mid_x = min_x + (max_x - min_x) * 0.5f;

      Section q;
      if (first_val_x < mid_x) {
        q = kx;
      } else {
        q = kX;
      }

      initial_x[q] = first_val_x;
      int stored = 0;
      for (int i = 0; i < 2; i++) {
        if (i != q) {
          sections[stored] = (Section)i;
          stored++;
        }
      }
      val_count = 1;
    }
    ~Node() = default;
    void GetNewValue(float* x) {
      if (val_count % 2 == 0) ResetSections();
      Section q = PullRandomSection();
      assert(val_count != 0);

      // We gen the rest of our first 2 values ourself.
      if (val_count < 2) {
        switch (q) {
          case kx:
            (*x) = initial_x[q] =
                rand_range(min_x, min_x + (max_x - min_x) * 0.5f);
            break;
          case kX:
            (*x) = initial_x[q] =
                rand_range(min_x + (max_x - min_x) * 0.5f, max_x);
        }
      } else {
        if (val_count == 2) {
          // Make child nodes and feed them their initial values.
          float mid_x = min_x + (max_x - min_x) * 0.5f;
          children[kx] = std::make_unique<Node>(min_x, mid_x, initial_x[kx]);
          children[kX] = std::make_unique<Node>(mid_x, max_x, initial_x[kX]);
        }

        // After this point we let our children do the work.
        children[q]->GetNewValue(x);
      }
      val_count++;
    }

   private:
    enum Section { kx, kX };

    std::unique_ptr<Node> children[2];

    // Pull a section and remove it from our list.
    auto PullRandomSection() -> Section {
      int remaining_sections = 2 - val_count % 2;
      int q_picked = rand() % remaining_sections;  // NOLINT
      Section q_val = sections[q_picked];
      int pos_new = 0;
      for (int pos_old = 0; pos_old < remaining_sections; pos_old++) {
        if (pos_old != q_picked) {
          sections[pos_new] = sections[pos_old];
          pos_new++;
        }
      }
      return q_val;
    }
    void ResetSections() {
      sections[0] = kx;
      sections[1] = kX;
    }
    Section sections[2]{};
    float initial_x[2]{};
    float min_x, max_x;
    int val_count;
  };
  std::unique_ptr<Node> root;
  std::vector<float> vals_x;
};

class SmoothGen2D {
 public:
  SmoothGen2D() = default;
  ~SmoothGen2D() = default;
  auto GetX(int index) -> float {
    Expand(static_cast<uint32_t>(index));
    return vals_x[index];
  }
  auto GetY(int index) -> float {
    Expand(static_cast<uint32_t>(index));
    return vals_y[index];
  }

 private:
  void Expand(uint32_t index) {
    if (index >= vals_x.size()) {
      if (vals_x.empty()) {
        float initial_x = rand_range(0.0f, 1.0f);
        float initial_y = rand_range(0.0f, 1.0f);
        root = std::make_unique<Node>(0, 0, 1, 1, initial_x, initial_y);
        vals_x.push_back(initial_x);
        vals_y.push_back(initial_y);
      }
      for (auto i = static_cast<uint32_t>(vals_x.size()); i <= index; i++) {
        float x, y;
        root->GetNewValue(&x, &y);
        vals_x.push_back(x);
        vals_y.push_back(y);
      }
    }
  }

  class Node {
   public:
    Node(float min_x_in, float min_y_in, float max_x_in, float max_y_in,
         float first_val_x, float first_val_y)
        : min_x(min_x_in), max_x(max_x_in), min_y(min_y_in), max_y(max_y_in) {
      // Store our initial value in the right section.
      assert(first_val_x >= min_x && first_val_x <= max_x);
      assert(first_val_y >= min_y && first_val_y <= max_y);

      float mid_x = min_x + (max_x - min_x) * 0.5f;
      float mid_y = min_y + (max_y - min_y) * 0.5f;

      Section q;
      if (first_val_x < mid_x) {
        if (first_val_y < mid_y) {
          q = kxy;
        } else {
          q = kxY;
        }
      } else {
        if (first_val_y < mid_y) {
          q = kXy;
        } else {
          q = kXY;
        }
      }
      initial_x[q] = first_val_x;
      initial_y[q] = first_val_y;
      int stored = 0;
      for (int i = 0; i < 4; i++) {
        if (i != q) {
          sections[stored] = (Section)i;
          stored++;
        }
      }
      val_count = 1;
    }
    ~Node() = default;
    void GetNewValue(float* x, float* y) {
      if (val_count % 4 == 0) ResetSections();
      Section q = PullRandomSection();

      assert(val_count != 0);

      // We gen the rest of our first 4 values ourself.
      if (val_count < 4) {
        switch (q) {
          case kxy:
          case kXy:
            (*y) = initial_y[q] =
                rand_range(min_y, min_y + (max_y - min_y) * 0.5f);
            break;
          case kxY:
          case kXY:
            (*y) = initial_y[q] =
                rand_range(min_y + (max_y - min_y) * 0.5f, max_y);
        }
        switch (q) {
          case kxy:
          case kxY:
            (*x) = initial_x[q] =
                rand_range(min_x, min_x + (max_x - min_x) * 0.5f);
            break;
          case kXy:
          case kXY:
            (*x) = initial_x[q] =
                rand_range(min_x + (max_x - min_x) * 0.5f, max_x);
        }
      } else {
        if (val_count == 4) {
          // Make child nodes and feed them their initial values.
          float mid_x = min_x + (max_x - min_x) * 0.5f;
          float mid_y = min_y + (max_y - min_y) * 0.5f;
          children[kxy] = std::make_unique<Node>(
              min_x, min_y, mid_x, mid_y, initial_x[kxy], initial_y[kxy]);
          children[kXy] = std::make_unique<Node>(
              mid_x, min_y, max_x, mid_y, initial_x[kXy], initial_y[kXy]);
          children[kXY] = std::make_unique<Node>(
              mid_x, mid_y, max_x, max_y, initial_x[kXY], initial_y[kXY]);
          children[kxY] = std::make_unique<Node>(
              min_x, mid_y, mid_x, max_y, initial_x[kxY], initial_y[kxY]);
        }

        // After this point we let our children do the work.
        children[q]->GetNewValue(x, y);
      }
      val_count++;
    }

   private:
    enum Section { kxy, kXy, kxY, kXY };

    std::unique_ptr<Node> children[4];

    // Pull a section and remove it from our list.
    auto PullRandomSection() -> Section {
      int remaining_sections = 4 - val_count % 4;
      int q_picked = rand() % remaining_sections;  // NOLINT
      Section q_val = sections[q_picked];
      int pos_new = 0;
      for (int pos_old = 0; pos_old < remaining_sections; pos_old++) {
        if (pos_old != q_picked) {
          sections[pos_new] = sections[pos_old];
          pos_new++;
        }
      }
      return q_val;
    }
    void ResetSections() {
      sections[0] = kxy;
      sections[1] = kXy;
      sections[2] = kXY;
      sections[3] = kxY;
    }
    Section sections[4]{};
    float initial_x[4]{};
    float initial_y[4]{};
    float min_x, min_y, max_x, max_y;
    int val_count;
  };
  std::unique_ptr<Node> root;
  std::vector<float> vals_x;
  std::vector<float> vals_y;
};

class SmoothGen3D {
 public:
  SmoothGen3D() = default;
  ~SmoothGen3D() = default;
  auto GetX(int index) -> float {
    Expand(static_cast<uint32_t>(index));
    return vals_x[index];
  }
  auto GetY(int index) -> float {
    Expand(static_cast<uint32_t>(index));
    return vals_y[index];
  }
  auto GetZ(int index) -> float {
    Expand(static_cast<uint32_t>(index));
    return vals_z[index];
  }

 private:
  void Expand(uint32_t index) {
    if (index >= vals_x.size()) {
      if (vals_x.empty()) {
        float initial_x = rand_range(0.0f, 1.0f);
        float initial_y = rand_range(0.0f, 1.0f);
        float initial_z = rand_range(0.0f, 1.0f);
        root = std::make_unique<Node>(0, 0, 0, 1, 1, 1, initial_x, initial_y,
                                      initial_z);
        vals_x.push_back(initial_x);
        vals_y.push_back(initial_y);
        vals_z.push_back(initial_z);
      }
      for (auto i = static_cast<uint32_t>(vals_x.size()); i <= index; i++) {
        float x, y, z;
        root->GetNewValue(&x, &y, &z);
        vals_x.push_back(x);
        vals_y.push_back(y);
        vals_z.push_back(z);
      }
    }
  }

  class Node {
   public:
    Node(float min_x_in, float min_y_in, float min_z_in, float max_x_in,
         float max_y_in, float max_z_in, float first_val_x, float first_val_y,
         float first_val_z)
        : min_x(min_x_in),
          max_x(max_x_in),
          min_y(min_y_in),
          max_y(max_y_in),
          min_z(min_z_in),
          max_z(max_z_in) {
      // store our initial value in the right section...
      assert(first_val_x >= min_x && first_val_x <= max_x);
      assert(first_val_y >= min_y && first_val_y <= max_y);
      assert(first_val_z >= min_z && first_val_z <= max_z);

      float mid_x = min_x + (max_x - min_x) * 0.5f;
      float mid_y = min_y + (max_y - min_y) * 0.5f;
      float mid_z = min_z + (max_z - min_z) * 0.5f;

      Section q;
      if (first_val_x < mid_x) {
        if (first_val_y < mid_y) {
          if (first_val_z < mid_z) {
            q = kxyz;
          } else {
            q = kxyZ;
          }
        } else {
          if (first_val_z < mid_z) {
            q = kxYz;
          } else {
            q = kxYZ;
          }
        }
      } else {
        if (first_val_y < mid_y) {
          if (first_val_z < mid_z) {
            q = kXyz;
          } else {
            q = kXyZ;
          }
        } else {
          if (first_val_z < mid_z) {
            q = kXYz;
          } else {
            q = kXYZ;
          }
        }
      }

      initial_x[q] = first_val_x;
      initial_y[q] = first_val_y;
      initial_z[q] = first_val_z;
      int stored = 0;
      for (int i = 0; i < 8; i++) {
        if (i != q) {
          sections[stored] = (Section)i;
          stored++;
        }
      }
      val_count = 1;
    }
    ~Node() = default;
    void GetNewValue(float* x, float* y, float* z) {
      if (val_count % 8 == 0) ResetSections();

      Section q = PullRandomSection();

      assert(val_count != 0);

      // We gen the rest of our first 8 values ourself.
      if (val_count < 8) {
        switch (q) {
          case kxyz:
          case kxyZ:
          case kxYz:
          case kxYZ:
            (*x) = initial_x[q] =
                rand_range(min_x, min_x + (max_x - min_x) * 0.5f);
            break;
          case kXyz:
          case kXyZ:
          case kXYz:
          case kXYZ:
            (*x) = initial_x[q] =
                rand_range(min_x + (max_x - min_x) * 0.5f, max_x);
        }
        switch (q) {
          case kxyz:
          case kxyZ:
          case kXyz:
          case kXyZ:
            (*y) = initial_y[q] =
                rand_range(min_y, min_y + (max_y - min_y) * 0.5f);
            break;
          case kxYz:
          case kxYZ:
          case kXYz:
          case kXYZ:
            (*y) = initial_y[q] =
                rand_range(min_y + (max_y - min_y) * 0.5f, max_y);
        }
        switch (q) {
          case kxyz:
          case kXyz:
          case kXYz:
          case kxYz:
            (*z) = initial_z[q] =
                rand_range(min_z, min_z + (max_z - min_z) * 0.5f);
            break;
          case kxyZ:
          case kXyZ:
          case kXYZ:
          case kxYZ:
            (*z) = initial_z[q] =
                rand_range(min_z + (max_z - min_z) * 0.5f, max_z);
        }
      } else {
        if (val_count == 8) {
          // make child nodes and feed them their initial values...
          float mid_x = min_x + (max_x - min_x) * 0.5f;
          float mid_y = min_y + (max_y - min_y) * 0.5f;
          float mid_z = min_z + (max_z - min_z) * 0.5f;
          children[kxyz] = std::make_unique<Node>(
              min_x, min_y, min_z, mid_x, mid_y, mid_z, initial_x[kxyz],
              initial_y[kxyz], initial_z[kxyz]);
          children[kxyZ] = std::make_unique<Node>(
              min_x, min_y, mid_z, mid_x, mid_y, max_z, initial_x[kxyZ],
              initial_y[kxyZ], initial_z[kxyZ]);
          children[kXyz] = std::make_unique<Node>(
              mid_x, min_y, min_z, max_x, mid_y, mid_z, initial_x[kXyz],
              initial_y[kXyz], initial_z[kXyz]);
          children[kXyZ] = std::make_unique<Node>(
              mid_x, min_y, mid_z, max_x, mid_y, max_z, initial_x[kXyZ],
              initial_y[kXyZ], initial_z[kXyZ]);
          children[kXYz] = std::make_unique<Node>(
              mid_x, mid_y, min_z, max_x, max_y, mid_z, initial_x[kXYz],
              initial_y[kXYz], initial_z[kXYz]);
          children[kXYZ] = std::make_unique<Node>(
              mid_x, mid_y, mid_z, max_x, max_y, max_z, initial_x[kXYZ],
              initial_y[kXYZ], initial_z[kXYZ]);
          children[kxYz] = std::make_unique<Node>(
              min_x, mid_y, min_z, mid_x, max_y, mid_z, initial_x[kxYz],
              initial_y[kxYz], initial_z[kxYz]);
          children[kxYZ] = std::make_unique<Node>(
              min_x, mid_y, mid_z, mid_x, max_y, max_z, initial_x[kxYZ],
              initial_y[kxYZ], initial_z[kxYZ]);
        }

        // After this point we let our children do the work.
        children[q]->GetNewValue(x, y, z);
      }
      val_count++;
    }

   private:
    enum Section { kxyz, kxyZ, kXyz, kXyZ, kxYz, kxYZ, kXYz, kXYZ };

    std::unique_ptr<Node> children[8];

    // Pull a section and remove it from our list.
    auto PullRandomSection() -> Section {
      int remaining_sections = 8 - val_count % 8;
      int q_picked = rand() % remaining_sections;  // NOLINT
      Section q_val = sections[q_picked];
      int pos_new = 0;
      for (int pos_old = 0; pos_old < remaining_sections; pos_old++) {
        if (pos_old != q_picked) {
          sections[pos_new] = sections[pos_old];
          pos_new++;
        }
      }
      return q_val;
    }
    void ResetSections() {
      for (int i = 0; i < 8; i++) sections[i] = (Section)i;
    }
    Section sections[8]{};
    float initial_x[8]{};
    float initial_y[8]{};
    float initial_z[8]{};
    float min_x, min_y, min_z, max_x, max_y, max_z;
    int val_count;
  };
  std::unique_ptr<Node> root;
  std::vector<float> vals_x;
  std::vector<float> vals_y;
  std::vector<float> vals_z;
};

void Random::GenList1D(float* list, int size) {
  SmoothGen1D gen;
  gen.GetX(size - 1);  // Expand it in one fell swoop
  for (int i = 0; i < size; i++) {
    list[i] = gen.GetX(i);
  }
}

void Random::GenList2D(float (*list)[2], int size) {
  SmoothGen2D gen;
  gen.GetX(size - 1);  // Expand it in one fell swoop
  for (int i = 0; i < size; i++) {
    list[i][0] = gen.GetX(i);
    list[i][1] = gen.GetY(i);
  }
}

void Random::GenList3D(float (*list)[3], int size) {
  SmoothGen3D gen;
  gen.GetX(size - 1);  // Expand it in one fell swoop
  for (int i = 0; i < size; i++) {
    list[i][0] = gen.GetX(i);
    list[i][1] = gen.GetY(i);
    list[i][2] = gen.GetZ(i);
  }
}

}  // namespace ballistica
