// Released under the MIT License. See LICENSE for details.

#include "ballistica/networking/sockaddr.h"

namespace ballistica {

SockAddr::SockAddr(const std::string& addr, int port) {
  memset(&addr_, 0, sizeof(addr_));

  // Try ipv4 and then ipv6.
  {
    struct in_addr addr_out {};
    int result = inet_pton(AF_INET, addr.c_str(), &addr_out);
    if (result == 1) {
      auto* a = reinterpret_cast<sockaddr_in*>(&addr_);
      a->sin_family = AF_INET;
      a->sin_port = htons(port);  // NOLINT
      a->sin_addr = addr_out;
      return;
    } else {
      struct in6_addr addr6Out {};
      result = inet_pton(AF_INET6, addr.c_str(), &addr6Out);
      if (result == 1) {
        auto* a = reinterpret_cast<sockaddr_in6*>(&addr_);
        a->sin6_family = AF_INET6;
        a->sin6_port = htons(port);  // NOLINT
        a->sin6_addr = addr6Out;
        return;
      }
    }
  }
  throw Exception("Invalid address: '" + addr + "'.");
}

}  // namespace ballistica
