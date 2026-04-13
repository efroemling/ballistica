// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/networking/networking.h"

#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/networking/network_reader.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/core/core.h"
#include "ballistica/shared/networking/sockaddr.h"

namespace ballistica::base {

Networking::Networking() = default;

void Networking::ApplyAppConfig() {
  // Be aware this runs in the logic thread; not the main thread like
  // most of our stuff.
  assert(g_base->InLogicThread());

  // Grab network settings from config and kick them over to the main
  // thread to be applied.
  int port = g_base->app_config->Resolve(AppConfig::IntID::kPort);
  g_base->app_adapter->PushMainThreadCall([port] {
    assert(g_core->InMainThread());
    g_base->network_reader->SetPort(port);
  });

  // This is thread-safe so just applying immediately.
  if (!g_core->HeadlessMode()) {
    remote_server_accepting_connections_ =
        g_base->app_config->Resolve(AppConfig::BoolID::kEnableRemoteApp);
  }
}

void Networking::OnAppSuspend() {}

void Networking::OnAppUnsuspend() {}

void Networking::SendTo(const std::vector<uint8_t>& buffer,
                        const SockAddr& addr) {
  assert(g_base->network_reader);
  assert(!buffer.empty());

  // This needs to be locked during any sd changes/writes.
  std::scoped_lock lock(g_base->network_reader->sd_mutex());

  // Only send if the relevant socket is currently up; silently ignore
  // otherwise.
  int sd = addr.IsV6() ? g_base->network_reader->sd6()
                       : g_base->network_reader->sd4();
  if (sd != -1) {
    sendto(sd, (const char*)&buffer[0],
           static_cast_check_fit<socket_send_length_t>(buffer.size()), 0,
           addr.AsSockAddr(), addr.GetSockAddrLen());
  }
}

}  // namespace ballistica::base
