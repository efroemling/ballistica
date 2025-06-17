// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_NETWORKING_SOCKADDR_H_
#define BALLISTICA_SHARED_NETWORKING_SOCKADDR_H_

#include <cassert>
#include <cstring>
#include <string>

#include "ballistica/shared/foundation/exception.h"
#include "ballistica/shared/networking/networking_sys.h"

namespace ballistica {

class SockAddr {
 public:
  SockAddr() { memset(&addr_, 0, sizeof(addr_)); }

  // Creates from an ipv4 or ipv6 address string; throws an exception on
  // error.
  SockAddr(const std::string& addr, int port);

  explicit SockAddr(const sockaddr_storage& addr_in) {
    addr_ = addr_in;
    assert(addr_.ss_family == AF_INET || addr_.ss_family == AF_INET6);
  }

  auto AsSockAddr() const -> const sockaddr* {
    return reinterpret_cast<const sockaddr*>(&addr_);
  }

  auto AsSockAddrIn() const -> const sockaddr_in* {
    assert(!IsV6());
    return reinterpret_cast<const sockaddr_in*>(&addr_);
  }

  auto AsSockAddrIn6() const -> const sockaddr_in6* {
    assert(IsV6());
    return reinterpret_cast<const sockaddr_in6*>(&addr_);
  }

  auto AddressString() const -> std::string;

  auto Port() const -> int;

  auto GetSockAddrLen() const -> socklen_t {
    switch (addr_.ss_family) {
      case AF_INET:
        return sizeof(sockaddr_in);
      case AF_INET6:
        return sizeof(sockaddr_in6);
      default:
        throw Exception(PyExcType::kValue);
    }
  }

  auto IsV6() const -> bool {
    switch (addr_.ss_family) {
      case AF_INET:
        return false;
      case AF_INET6:
        return true;
      default:
        throw Exception();
    }
  }

  auto operator==(const SockAddr& other) const -> bool {
    if (addr_.ss_family != other.addr_.ss_family) return false;
    if (addr_.ss_family == AF_INET) {
      auto* a1 = AsSockAddrIn();
      auto* a2 = other.AsSockAddrIn();
      return !memcmp(&(a1->sin_addr), &(a2->sin_addr), sizeof(in_addr))
             && a1->sin_port == a2->sin_port;
    }
    if (addr_.ss_family == AF_INET6) {
      auto* a1 = AsSockAddrIn6();
      auto* a2 = other.AsSockAddrIn6();
      return !memcmp(&(a1->sin6_addr), &(a2->sin6_addr), sizeof(in6_addr))
             && a1->sin6_port == a2->sin6_port;
    }
    throw Exception(PyExcType::kValue);
  }

 private:
  sockaddr_storage addr_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_NETWORKING_SOCKADDR_H_
