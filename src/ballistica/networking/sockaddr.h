// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_NETWORKING_SOCKADDR_H_
#define BALLISTICA_NETWORKING_SOCKADDR_H_

#include <cstring>
#include <string>

#include "ballistica/ballistica.h"
#include "ballistica/networking/networking_sys.h"

namespace ballistica {

class SockAddr {
 public:
  SockAddr() { memset(&addr_, 0, sizeof(addr_)); }

  // Creates from an ipv4 or ipv6 address string;
  // throws an exception on error.
  SockAddr(const std::string& addr, int port);
  explicit SockAddr(const sockaddr_storage& addr_in) {
    addr_ = addr_in;
    assert(addr_.ss_family == AF_INET || addr_.ss_family == AF_INET6);
  }
  auto GetSockAddr() const -> const sockaddr* {
    return reinterpret_cast<const sockaddr*>(&addr_);
  }
  auto GetSockAddrLen() const -> socklen_t {
    switch (addr_.ss_family) {
      case AF_INET:
        return sizeof(sockaddr_in);
      case AF_INET6:
        return sizeof(sockaddr_in6);
      default:
        throw Exception();
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

 private:
  sockaddr_storage addr_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_NETWORKING_SOCKADDR_H_
