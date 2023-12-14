// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/networking/sockaddr.h"

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
      a->sin_port = htons(port);
      a->sin_addr = addr_out;
      return;
    } else {
      struct in6_addr addr6_out {};
      result = inet_pton(AF_INET6, addr.c_str(), &addr6_out);
      if (result == 1) {
        auto* a = reinterpret_cast<sockaddr_in6*>(&addr_);
        a->sin6_family = AF_INET6;
        a->sin6_port = htons(port);
        a->sin6_addr = addr6_out;
        return;
      }
    }
  }
  throw Exception("Invalid address: '" + addr + "'.", PyExcType::kValue);
}

auto SockAddr::AddressString() const -> std::string {
  if (IsV6()) {
    char ip_str[INET6_ADDRSTRLEN];
    if (inet_ntop(AF_INET6, &(AsSockAddrIn6()->sin6_addr), ip_str,
                  INET6_ADDRSTRLEN)
        == nullptr) {
      throw Exception("inet_ntop failed for v6 addr", PyExcType::kValue);
    }
    return ip_str;
  }
  char ip_str[INET_ADDRSTRLEN];
  if (inet_ntop(AF_INET, &(AsSockAddrIn()->sin_addr), ip_str, INET_ADDRSTRLEN)
      == nullptr) {
    throw Exception("inet_ntop failed for v4 addr", PyExcType::kValue);
  }
  return ip_str;
}

auto SockAddr::Port() const -> int {
  if (IsV6()) {
    return ntohs(AsSockAddrIn6()->sin6_port);
  } else {
    return ntohs(AsSockAddrIn()->sin_port);
  }
}

}  // namespace ballistica
