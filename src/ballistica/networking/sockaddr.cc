// Released under the MIT License. See LICENSE for details.

#include "ballistica/networking/sockaddr.h"

namespace ballistica {

SockAddr::SockAddr(const std::string& addr, int port) {
  memset(&addr_, 0, sizeof(addr_));

  // try ipv4...
  {
    // inet_pton is not available on XP :-/
    // hmmm at this point we probably don't care; should test inet_pton.
    // #if BA_OSTYPE_WINDOWS
    //    int addr_size = sizeof(addr_);
    //    std::wstring addr2;
    //    addr2.assign(addr.begin(), addr.end());
    //    struct sockaddr_in* a4 = reinterpret_cast<sockaddr_in*>(&addr_);
    //    struct sockaddr_in6* a6 = reinterpret_cast<sockaddr_in6*>(&addr_);
    //    int result =
    //        WSAStringToAddress(const_cast<wchar_t*>(addr2.c_str()), AF_INET,
    //                           nullptr, (LPSOCKADDR)a4, &addr_size);
    //    if (result == 0) {
    //      if (a4->sin_family == AF_INET) {
    //        a4->sin_port = htons(port);
    //        return;
    //      } else if (a6->sin6_family == AF_INET6) {
    //        a6->sin6_port = htons(port);
    //      }
    //    }
    // #else
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
    // #endif
  }
  throw Exception("Invalid address: '" + addr + "'");
}

}  // namespace ballistica
