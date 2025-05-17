// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DISCORD_DISCORD_H_
#define BALLISTICA_BASE_DISCORD_DISCORD_H_

#include <memory> // For std::shared_ptr
#include "discordpp.h" // Include the Discord header

namespace ballistica::base {
class DiscordClient {
 public:
  void init();
  std::shared_ptr<discordpp::Client> authenticate(std::shared_ptr<discordpp::Client> client);
  const uint64_t APPLICATION_ID = 1371951592034668635;
};
}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DISCORD_DISCORD_H_