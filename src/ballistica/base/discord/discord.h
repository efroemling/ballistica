// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DISCORD_DISCORD_H_
#define BALLISTICA_BASE_DISCORD_DISCORD_H_

#include <memory>  // For std::shared_ptr

#include "discordpp.h"  // Include the Discord header

namespace ballistica::base {
class DiscordClient {
 public:
  void init();
  void authenticate(std::shared_ptr<discordpp::Client> client);

  void SetActivity(std::shared_ptr<discordpp::Client> client, const char* state,
                   const char* details, const char* largeImageKey,
                   const char* largeImageText, const char* smallImageKey,
                   const char* smallImageText, int64_t startTimestamp,
                   int64_t endTimestamp);
  static const uint64_t APPLICATION_ID = 1373228222002626610;
};
}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DISCORD_DISCORD_H_