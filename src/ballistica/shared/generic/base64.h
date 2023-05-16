// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_GENERIC_BASE64_H_
#define BALLISTICA_SHARED_GENERIC_BASE64_H_

#include <string>

namespace ballistica {

auto base64_encode(const unsigned char*, unsigned int len, bool urlsafe = false)
    -> std::string;
auto base64_decode(const std::string& s, bool urlsafe = false) -> std::string;

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_GENERIC_BASE64_H_
