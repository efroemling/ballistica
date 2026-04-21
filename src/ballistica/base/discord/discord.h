// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DISCORD_DISCORD_H_
#define BALLISTICA_BASE_DISCORD_DISCORD_H_

#include <memory>
#include <string>

#include "ballistica/base/base.h"

// Forward declaration so this header does not need to pull in the Social SDK.
namespace discordpp {
class Client;
}

namespace ballistica::base {

/// Ballistica integration with the Discord Social SDK. Only instantiated
/// when BA_ENABLE_DISCORD is on; see BaseFeatureSet construction.
///
/// This is currently a bare smoke-test: it logs the SDK version and hooks
/// the SDK's log callback into our logging system. No OAuth, presence, or
/// lobby wiring yet.
class Discord {
 public:
  Discord();
  ~Discord();

  /// Pump the Discord SDK's callback queue. Called once per logic-thread
  /// tick from Logic::StepDisplayTime_(); callbacks run synchronously on
  /// the caller, so this is where SDK events become visible to our
  /// Python/C++ code.
  void StepDisplayTime();

  /// Start the OAuth2 sign-in flow. Opens the user's browser to
  /// Discord's authorization page; once the user approves, the SDK
  /// captures the code via the loopback redirect, we exchange it for
  /// an access token, and connect to the SDK gateway for presence.
  /// Progress is logged to ba.discord.
  ///
  /// ``attempt_id`` identifies this attempt in the Python-side pending
  /// map (see ``babase._login.discord_sign_in``). When the flow
  /// completes we report the access token back via the
  /// ``kDiscordSignInTokenResponseCall`` hook keyed on this id. An
  /// empty token signals failure.
  void SignIn(int attempt_id);

  /// Publish a Rich Presence activity to Discord. Shows up on the user's
  /// Discord profile as "Playing BallisticaKit: <state>" with details
  /// underneath. Requires SDK status to be Ready (i.e. the user has
  /// signed in) — otherwise the call is a no-op.
  void UpdatePresence(const std::string& state, const std::string& details);

  /// Reconnect to the Discord SDK using a previously-stored refresh
  /// token (no browser flow). Called on app startup when the current
  /// V2 account has a Discord login attached and we have a refresh
  /// token saved for the same Discord user. On success the new
  /// rotated refresh token is handed back to Python for storage; on
  /// failure we tell Python to clear the stored auth.
  void ReconnectWithRefreshToken(const std::string& refresh_token);

 private:
  /// Forward a new Discord auth pair to the Python account subsystem
  /// for persistent storage. Passing empty strings signals "clear".
  static void ReportDiscordAuth(const std::string& refresh_token,
                                const std::string& user_id);

#if BA_ENABLE_DISCORD
  /// Cached refresh token captured from GetToken, consumed when the
  /// SDK reaches Ready and we can also look up the Discord user id.
  std::string pending_refresh_token_;
  std::unique_ptr<discordpp::Client> client_;
#endif
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DISCORD_DISCORD_H_
