// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_GENERIC_UTILS_H_
#define BALLISTICA_SHARED_GENERIC_UTILS_H_

#include <algorithm>
#include <list>
#include <memory>
#include <string>
#include <vector>

// Need platform-specific headers here so we can inline calls to htonl/etc.
// (perhaps should move those functions to their own file?)
#if BA_PLATFORM_WINDOWS
#include <winsock2.h>
#else
#include <netinet/in.h>
#endif
#include <cstring>

#include "ballistica/shared/ballistica.h"

namespace ballistica {

// FIXME: Currently this lives in shared for easy access to static bits
//  but the singleton of it lives under base. Should perhaps split into
//  two classes.

const int kPrecalcRandsCount = 128;

/// A holding tank for miscellaneous functionality not extensive enough to
/// warrant its own class. When possible, things should be moved out of here
/// into more organized locations.
class Utils {
 public:
  Utils();
  ~Utils();

  static auto BaseName(const std::string& val) -> std::string;

  static auto PtrToString(const void* val) -> std::string;

  // This should probably live elsewhere...
  static auto GetRandomNameList() -> const std::list<std::string>&;
  static void SetRandomNameList(const std::list<std::string>& names);

  /// Strip non-ascii chars from a utf-8 string (the full chars; not just
  /// control characters).
  static auto StripNonAsciiFromUTF8(const std::string& s) -> std::string;

  static auto UnicodeFromUTF8(const std::string& s, const char* loc)
      -> std::vector<uint32_t>;
  static auto UTF8FromUnicode(std::vector<uint32_t> unichars) -> std::string;
  static auto UTF8FromUnicodeChar(uint32_t c) -> std::string;
  static auto UTF8StringLength(const char* val) -> int;

  /// Replace a single occurrence of key with replacement in the target string.
  /// Returns whether a replacement occurred.
  static auto StringReplaceOne(std::string* target, const std::string& key,
                               const std::string& replacement) -> bool;

  static void StringReplaceAll(std::string* target, const std::string& key,
                               const std::string& replacement);

  /// Strip out or corrects invalid utf8.
  /// This is run under the hood for all the above calls but in some cases
  /// (such as the calls below) you may want to run it by hand.
  /// Loc is included in debug log output if invalid utf8 is passed in.
  static auto GetValidUTF8(const char* str, const char* loc) -> std::string;

  /// Use this for debugging (not optimized for speed).
  /// Currently just runs GetValidUTF8 and compares
  /// results to original to see if anything got changed.
  static auto IsValidUTF8(const std::string& val) -> bool;

  // Escape a string so it can be embedded as part of a flattened json string.
  static auto GetJSONString(const char* s) -> std::string;

  // IMPORTANT - These run on 'trusted' utf8 - make sure you've run
  // GetValidUTF8 on any data you pass to these
  static auto GetUTF8Value(const char* s) -> uint32_t;
  static void AdvanceUTF8(const char** s);

  /* The following code uses bitwise operators to determine
   if an unsigned integer, x, is a power of two.  If x is a power of two,
   x is represented in binary with only a single bit; therefore, subtraction
   by one removes that bit and flips all the lower-order bits.  The bitwise
   and <http://www.cprogramming.com/tutorial/bitwise.html>

   then effectively checks to see if any bit is the
   same.  If not, then it's a power of two.*/
  static inline auto IsPowerOfTwo(unsigned int x) -> int {
    return !((x - 1) & x);
  }

  // Yes this stuff should technically be using unsigned values for the
  // bitwise stuff but I'm not brave enough to convert it at the moment.
  // Made a quick attempt and everything blew up.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "bugprone-narrowing-conversions"

  static inline auto FloatToHalfI(uint32_t i) -> uint16_t {
    int s = (i >> 16) & 0x00008000;                 // NOLINT
    int e = ((i >> 23) & 0x000000ff) - (127 - 15);  // NOLINT
    int m = i & 0x007fffff;                         // NOLINT

    if (e <= 0) {
      if (e < -10) {
        return 0;
      }
      m = (m | 0x00800000) >> (1 - e);

      return static_cast<uint16_t>(s | (m >> 13));
    } else if (e == 0xff - (127 - 15)) {
      if (m == 0) {
        // Inf
        return static_cast<uint16_t>(s | 0x7c00);
      } else {
        // NAN
        m >>= 13;
        return static_cast<uint16_t>(s | 0x7c00 | m | (m == 0));
      }
    } else {
      if (e > 30) {
        // Overflow
        return static_cast<uint16_t>(s | 0x7c00);
      }

      return static_cast<uint16_t>(s | (e << 10) | (m >> 13));
    }
  }

  static inline auto FloatToHalf(float i) -> uint16_t {
    union {
      float f;
      uint32_t i;
    } v{};
    v.f = i;
    return FloatToHalfI(v.i);
  }

  static inline auto HalfToFloatI(uint16_t y) -> uint32_t {
    int s = (y >> 15) & 0x00000001;
    int e = (y >> 10) & 0x0000001f;
    int m = y & 0x000003ff;
    if (e == 0) {
      if (m == 0) {  // Plus or minus zero
        return static_cast<uint32_t>(s << 31);
      } else {  // Denormalized number -- renormalize it
        while (!(m & 0x00000400)) {
          m <<= 1;
          e -= 1;
        }
        e += 1;
        m &= ~0x00000400;
      }
    } else if (e == 31) {
      if (m == 0) {  // Inf
        return static_cast<uint32_t>((s << 31) | 0x7f800000);
      } else {  // NaN
        return static_cast<uint32_t>((s << 31) | 0x7f800000 | (m << 13));
      }
    }
    e = e + (127 - 15);
    m = m << 13;
    return static_cast<uint32_t>((s << 31) | (e << 23) | m);
  }

  static inline auto HalfToFloat(uint16_t y) -> float {
    union {
      float f;
      uint32_t i;
    } v{};
    v.i = HalfToFloatI(y);
    return v.f;
  }

  // Value embedding/extracting in buffers.
  // Note to self:
  // Whenever its possible to do so cleanly, we should migrate to storing
  // everything in little-endian and kill off the NBO versions of these.
  // I don't anticipate having to run on big-endian hardware anytime soon
  // and it'll save us a few cycles. (plus things are a sloppy mix of
  // network-byte-ordered and native-ordered as it stands now).

  /// Embed a single bool in a buffer.
  static inline void EmbedBool(char** b, bool i) {
    **b = i;  // NOLINT
    (*b)++;
  }

  /// Embed up to 8 bools in a buffer (in a single byte)  use ExtractBools to
  /// pull them out.
  static inline void EmbedBools(char** b, bool i1, bool i2 = false,
                                bool i3 = false, bool i4 = false,
                                bool i5 = false, bool i6 = false,
                                bool i7 = false, bool i8 = false) {
    **b = uint8_t(i1) | (uint8_t(i2) << 1) | (uint8_t(i3) << 2)  // NOLINT
          | (uint8_t(i4) << 3) | (uint8_t(i5) << 4)              // NOLINT
          | (uint8_t(i6) << 5) | (uint8_t(i7) << 6)              // NOLINT
          | (uint8_t(i8) << 7);                                  // NOLINT
    (*b)++;
  }

  static inline void EmbedInt8(char** b, int8_t i) {
    **b = i;
    (*b)++;
  }

  /// Embed a 2 byte int (short) into a buffer in network byte order.
  static inline void EmbedInt16NBO(char** b, int16_t i) {
    i = htons(i);
    memcpy(*b, &i, sizeof(i));
    *b += 2;
  }

  /// Embed a 4 byte int into a buffer in network-byte-order.
  static inline void EmbedInt32NBO(char** b, int32_t i) {
    i = htonl(i);
    memcpy(*b, &i, sizeof(i));
    *b += 4;
  }

  /// Embed a float in 16 bit "half" format (loses some precision) in
  /// network-byte-order.
  static inline void EmbedFloat16NBO(char** b, float f) {
    uint16_t val = htons(FloatToHalf(f));
    memcpy(*b, &val, sizeof(val));
    *b += 2;
  }

  /// Embed 4 byte float into a buffer.
  static inline void EmbedFloat32(char** b, float f) {
    memcpy(*b, &f, 4);
    *b += 4;
  }

  /// Embed a string into a buffer.
  static inline void EmbedString(char** b, const char* s) {
    strcpy(*b, s);  // NOLINT
    *b += strlen(*b) + 1;
  }

  static inline auto EmbeddedStringSize(const char* s) -> int {
    return static_cast<int>(strlen(s) + 1);
  }

  /// Embed a string in a buffer.
  static inline void EmbedString(char** b, const std::string& s) {
    strcpy(*b, s.c_str());  // NOLINT
    *b += s.size() + 1;
  }

  /// Return the number of bytes an embedded string with occupy.
  static inline auto EmbeddedStringSize(const std::string& s) -> int {
    return static_cast<int>(s.size() + 1);
  }

  /// Extract a string from a buffer.
  static inline auto ExtractString(const char** b) -> std::string {
    std::string s = *b;
    *b += s.size() + 1;
    return s;
  }

  /// Extract a single bool from a buffer.
  static inline auto ExtractBool(const char** b) -> bool {
    bool i = (**b != 0);
    (*b)++;
    return i;
  }

  /// Extract multiple bools from a buffer.
  static inline void ExtractBools(const char** b, bool* i1, bool* i2 = nullptr,
                                  bool* i3 = nullptr, bool* i4 = nullptr,
                                  bool* i5 = nullptr, bool* i6 = nullptr,
                                  bool* i7 = nullptr, bool* i8 = nullptr) {
    auto i = static_cast<uint8_t>(**b);
    *i1 = static_cast<bool>(i & 0x01);
    if (i2) *i2 = static_cast<bool>((i >> 1) & 0x01);
    if (i3) *i3 = static_cast<bool>((i >> 2) & 0x01);
    if (i4) *i4 = static_cast<bool>((i >> 3) & 0x01);
    if (i5) *i5 = static_cast<bool>((i >> 4) & 0x01);
    if (i6) *i6 = static_cast<bool>((i >> 5) & 0x01);
    if (i7) *i7 = static_cast<bool>((i >> 6) & 0x01);
    if (i8) *i8 = static_cast<bool>((i >> 7) & 0x01);
    (*b)++;
  }
#pragma clang diagnostic pop

  /// Extract a 1 byte int from a buffer.
  static inline auto ExtractInt8(const char** b) -> int8_t {
    int8_t i = **b;
    (*b)++;
    return i;
  }

  ///  Extract a 2 byte int from a network-byte-order buffer.
  static inline auto ExtractInt16NBO(const char** b) -> int16_t {
    int16_t i;
    memcpy(&i, *b, sizeof(i));
    *b += 2;
    return ntohs(i);  // NOLINT
  }

  /// Extract a 4 byte int from a network-byte-order buffer.
  static inline auto ExtractInt32NBO(const char** b) -> int32_t {
    int32_t i;
    memcpy(&i, *b, sizeof(i));
    *b += 4;
    return ntohl(i);  // NOLINT
  }

  /// Extract a 2 byte (half) float from a network-byte-order buffer.
  static inline auto ExtractFloat16NBO(const char** b) -> float {
    uint16_t i;
    memcpy(&i, *b, sizeof(i));
    *b += 2;
    return HalfToFloat(ntohs(i));  // NOLINT
  }

  /// Extract a 4 byte float from a buffer.
  static inline auto ExtractFloat32(const char** b) -> float {
    float i;
    memcpy(&i, *b, 4);
    *b += 4;
    return i;
  }

  /// Return whether a sequence of some type pointer has nullptr members.
  template <typename T>
  static auto HasNullMembers(const T& sequence) -> bool {
    // NOLINTNEXTLINE(readability-use-anyofallof)
    for (auto&& i : sequence) {
      if (i == nullptr) {
        return true;
      }
    }
    return false;
  }

  // Simple lists of pre-calculated random values between 0 and 1
  // (with no particular distribution)
  static float precalc_rand_1(int64_t index) {
    assert(index >= 0);
    assert(index < kPrecalcRandsCount);
    return precalc_rands_1_[index];
  }
  static float precalc_rand_2(int64_t index) {
    assert(index >= 0);
    assert(index < kPrecalcRandsCount);
    return precalc_rands_2_[index];
  }
  static float precalc_rand_3(int64_t index) {
    assert(index >= 0);
    assert(index < kPrecalcRandsCount);
    return precalc_rands_3_[index];
  }
  // auto huffman() -> Huffman* { return huffman_.get(); }

  // FIXME - move to a nice math-y place
  static auto Sphrand(float radius = 1.0f) -> Vector3f;

  // read a file into a string, throwing an Exception on error.
  static auto FileToString(const std::string& file_name) -> std::string;

  // fixme: move this to a 'Math' class?..
  static auto SmoothStep(float edge0, float edge1, float x) -> float {
    float t;
    t = std::min(1.0f, std::max(0.0f, (x - edge0) / (edge1 - edge0)));
    return t * t * (3.0f - 2.0f * t);
  }

 private:
  static float precalc_rands_1_[];
  static float precalc_rands_2_[];
  static float precalc_rands_3_[];
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_GENERIC_UTILS_H_
