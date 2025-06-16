// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_HUFFMAN_H_
#define BALLISTICA_SCENE_V1_SUPPORT_HUFFMAN_H_

#include <vector>

namespace ballistica::scene_v1 {

class Huffman {
 public:
  Huffman();
  ~Huffman();

#if HUFFMAN_TRAINING_MODE
  void train(const char* buffer, int len);
#endif

  void build();

  // NOTE: this assumes the topmost bit of the first byte is unused (see
  // details in implementation).
  auto compress(const std::vector<uint8_t>& src) -> std::vector<uint8_t>;
  auto decompress(const std::vector<uint8_t>& src) -> std::vector<uint8_t>;
  auto get_built() const -> bool { return built; }

 private:
  bool built;
#if HUFFMAN_TRAINING_MODE
  uint32_t test_bytes = 0;
  uint32_t test_bits_compressed = 0;
  int total_count = 0;
  int total_length = 0;
#endif

  class Node {
   public:
    Node() = default;

    // Left child index in node array (-1 for none).
    int16_t left_child = -1;

    // Right child index in node array (-1 for none).
    int16_t right_child = -1;

    // Parent index in node array (0 for none - add 255 to this to get
    // actual index).
    uint8_t parent = 0;
    uint8_t bits = 0;
    uint16_t val = 0;
    int frequency = 0;
  };

  Node nodes_[511];
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_HUFFMAN_H_
