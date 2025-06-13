// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DISCORD_DISCORD_H_
#define BALLISTICA_BASE_DISCORD_DISCORD_H_

#include <memory>
#if BA_ENABLE_DISCORD
#include "external/discord_social_sdk/include/discordpp.h"
#endif  // BA_ENABLE_DISCORD

namespace ballistica::base {
class Discord {
#if BA_ENABLE_DISCORD

 public:
  static const uint64_t APPLICATION_ID = 1373228222002626610;
  std::shared_ptr<discordpp::Client> init();
  std::shared_ptr<discordpp::Client> client;
  discordpp::Activity activity;
  uint64_t lobbyId_{0};
  uint64_t oldMessageId_{0};
  bool client_is_ready = false;
  void authenticate();

  void SetActivity(const char* state, const char* details,
                   const char* largeImageKey, const char* largeImageText,
                   const char* smallImageKey, const char* smallImageText,
                   int64_t startTimestamp, int64_t endTimestamp);

  void SetParty(const char* partyId, int currentPartySize, int maxPartySize);
  void AddButton(const char* label, const char* url);
  void JoinLobby(const char* lobbySecret);
  void LeaveLobby(const char* lobbyId);
  void SendLobbyMessage(const char* message);
  void LeaveLobby();
  void UpdateRP();
  void Shutdown() {
    if (client) {
      client->Disconnect();
      client.reset();
    }
  }
#endif  // BA_ENABLE_DISCORD
};
}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DISCORD_DISCORD_H_
