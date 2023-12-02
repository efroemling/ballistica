// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_NETWORKING_NETWORK_READER_H_
#define BALLISTICA_BASE_NETWORKING_NETWORK_READER_H_

#include <condition_variable>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#include "ballistica/base/base.h"

namespace ballistica::base {

// A subsystem that manages the game's main network sockets.
// It handles creating/destroying them as well as listening for incoming
// packets. it is not a normal BA thread so doesn't have the ability to receive
// messages (it generally sits blocked in a select() call). Writing to these
// sockets takes place in other threads; just make sure to lock the mutex and
// ensure the sockets exist before doing the actual write.
class NetworkReader {
 public:
  NetworkReader();
  void SetPort(int port);
  void OnAppSuspend();
  void OnAppUnsuspend();
  auto port4() const { return port4_; }
  auto port6() const { return port6_; }
  auto sd_mutex() -> std::mutex& { return sd_mutex_; }
  auto sd4() const { return sd4_; }
  auto sd6() const { return sd6_; }

 private:
  void DoSelect_(bool* can_read_4, bool* can_read_6);
  void DoPoll_(bool* can_read_4, bool* can_read_6);
  void OpenSockets_();
  void PokeSelf_();
  auto RunThread_() -> int;
  void PushIncomingUDPPacketCall_(const std::vector<uint8_t>& data,
                                  const SockAddr& addr);
  static auto RunThreadStatic_(void* self) -> int {
    return static_cast<NetworkReader*>(self)->RunThread_();
  }

  // This needs to be locked while modifying or writing to either the ipv4
  // or ipv6 socket. The one exception is when the network-reader thread is
  // reading from them, since there is no chance of anyone else reading or
  // modifying them. (that is all handled by the net-reader thread).
  std::mutex sd_mutex_;
  int port4_{-1};
  int port6_{-1};
  int sd4_{-1};
  int sd6_{-1};
  bool paused_{};
  std::thread* thread_{};
  std::mutex paused_mutex_;
  std::condition_variable paused_cv_;
  std::unique_ptr<RemoteAppServer> remote_server_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_NETWORKING_NETWORK_READER_H_
