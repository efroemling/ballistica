// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_GENERIC_BUFFER_H_
#define BALLISTICA_SHARED_GENERIC_BUFFER_H_

#include <cstdlib>

#include "ballistica/shared/generic/utils.h"

namespace ballistica {

// Simple data-holding buffer class.
// (FIXME: should kill this and just use std::vector for this purpose)
template <typename T>
class Buffer {
 public:
  Buffer(const Buffer& b) : data_(nullptr), size_(0) {
    Resize(b.size());
    if (b.size() > 0) {
      memcpy(data_, b.data_, b.size() * sizeof(T));
    }
  }

  ~Buffer() {
    if (data_) {
      free(data_);
    }
  }

  auto operator=(const Buffer& src) -> Buffer& {
    assert(this != &src);  // Shouldn't be self-assigning.
    Resize(src.size());
    if (size_ > 0) {
      memcpy(data_, src.data_, size_ * sizeof(T));
    }
    return *this;
  }

  explicit Buffer(size_t size_in = 0) : data_(nullptr), size_(size_in) {
    if (size_ > 0) {
      Resize(size_);
    }
  }

  Buffer(const T* data_in, size_t length) : data_(nullptr), size_(0) {
    if (length > 0) {
      Resize(length);
      memcpy(data_, data_in, length * sizeof(T));
    }
  }

  /// Get the amount of space needed to embed this buffer
  auto GetFlattenedSize() -> size_t { return 4 + size_ * sizeof(T); }

  /// Embed this buffer into a flat memory buffer.
  void embed(char** b) {
    // Embed our size (in items not bytes).
    Utils::EmbedInt32NBO(b, static_cast<int32_t>(size_));
    memcpy(*b, data_, size_ * sizeof(T));
    *b += size_ * sizeof(T);
  }

  /// Extract this buffer for a flat memory buffer.
  void Extract(const char** b) {
    Resize(static_cast_check_fit<size_t>(Utils::ExtractInt32NBO(b)));
    memcpy(data_, *b, size_ * sizeof(T));
    *b += size_ * sizeof(T);
  }

  void Resize(size_t new_size) {
    if (data_) {
      free(data_);
    }
    if (new_size > 0) {
      data_ = static_cast<T*>(malloc(new_size * sizeof(T)));
      BA_PRECONDITION(data_);
    } else {
      data_ = nullptr;
    }
    size_ = new_size;
  }

  // gets the length in the buffer's units (not bytes)
  auto size() const -> size_t { return size_; }

  auto data() const -> T* { return data_; }

 private:
  T* data_;
  size_t size_;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_GENERIC_BUFFER_H_
