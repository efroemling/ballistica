// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DISCORD_DISCORD_H_
#define BALLISTICA_BASE_DISCORD_DISCORD_H_

#include <memory>
#if BA_ENABLE_DISCORD
#include "discordpp.h"
#endif  // BA_ENABLE_DISCORD

namespace ballistica::base {
class Discord {
#if BA_ENABLE_DISCORD
 public:
  std::shared_ptr<discordpp::Client> init();
  std::shared_ptr<discordpp::Client> client;
  bool client_is_ready = false;
  void authenticate();

  void SetActivity(const char* state, const char* details,
                   const char* largeImageKey, const char* largeImageText,
                   const char* smallImageKey, const char* smallImageText,
                   int64_t startTimestamp, int64_t endTimestamp);
  static const uint64_t APPLICATION_ID = 1373228222002626610;
#endif  // BA_ENABLE_DISCORD
};
}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DISCORD_DISCORD_H_