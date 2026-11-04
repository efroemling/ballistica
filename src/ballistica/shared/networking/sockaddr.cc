// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/networking/sockaddr.h"

#include <cstdint>
#include <cstdlib>
#include <string>

#if !BA_PLATFORM_WINDOWS
#include <net/if.h>
#endif

namespace ballistica {

namespace {

/// Interface index for the scope part of 'fe80::1%en0' (a name, or a
/// number as Windows writes them); 0 if unknown.
auto ParseScope(const std::string& scope) -> uint32_t {
  if (scope.empty()) {
    return 0;
  }
  char* end{};
  auto val = strtoul(scope.c_str(), &end, 10);
  if (end != nullptr && *end == 0) {
    return static_cast<uint32_t>(val);
  }
#if BA_PLATFORM_WINDOWS
  return 0;
#else
  return if_nametoindex(scope.c_str());
#endif
}

}  // namespace

SockAddr::SockAddr(const std::string& addr_in, int port) {
  memset(&addr_, 0, sizeof(addr_));

  // Link-local IPv6 addresses only mean something on one interface,
  // which rides along as a scope suffix ('fe80::1%en0').
  std::string addr{addr_in};
  uint32_t scope_id{};
  auto percent = addr.find('%');
  if (percent != std::string::npos) {
    scope_id = ParseScope(addr.substr(percent + 1));
    if (scope_id == 0) {
      throw Exception("Invalid address scope: '" + addr_in + "'.",
                      PyExcType::kValue);
    }
    addr.resize(percent);
  }

  // Try ipv4 and then ipv6.
  {
    struct in_addr addr_out{};
    int result = inet_pton(AF_INET, addr.c_str(), &addr_out);
    if (result == 1 && scope_id == 0) {
      auto* a = reinterpret_cast<sockaddr_in*>(&addr_);
      a->sin_family = AF_INET;
      a->sin_port = htons(port);
      a->sin_addr = addr_out;
      return;
    } else {
      struct in6_addr addr6_out{};
      result = inet_pton(AF_INET6, addr.c_str(), &addr6_out);
      if (result == 1) {
        auto* a = reinterpret_cast<sockaddr_in6*>(&addr_);
        a->sin6_family = AF_INET6;
        a->sin6_port = htons(port);
        a->sin6_addr = addr6_out;
        a->sin6_scope_id = scope_id;
        return;
      }
    }
  }
  throw Exception("Invalid address: '" + addr_in + "'.", PyExcType::kValue);
}

auto SockAddr::AddressString() const -> std::string {
  if (IsV6()) {
    char ip_str[INET6_ADDRSTRLEN];
    if (inet_ntop(AF_INET6, &(AsSockAddrIn6()->sin6_addr), ip_str,
                  INET6_ADDRSTRLEN)
        == nullptr) {
      throw Exception("inet_ntop failed for v6 addr", PyExcType::kValue);
    }
    // Scoped (link-local) addresses get their interface back on, in the
    // same form the parser above and Python's socket module use.
    auto scope_id = AsSockAddrIn6()->sin6_scope_id;
    if (scope_id != 0) {
#if !BA_PLATFORM_WINDOWS
      char ifname[IF_NAMESIZE];
      if (if_indextoname(scope_id, ifname) != nullptr) {
        return std::string(ip_str) + "%" + ifname;
      }
#endif
      return std::string(ip_str) + "%" + std::to_string(scope_id);
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
