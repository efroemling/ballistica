// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/discord/discord.h"

#include <Python.h>

#include <string>
#include <utility>

#include "ballistica/base/python/base_python.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/python/python_ref.h"

#if BA_ENABLE_DISCORD
// The Social SDK ships as a single-header C++ wrapper over its C API: exactly
// one translation unit must define DISCORDPP_IMPLEMENTATION before including
// the header so the wrapper function bodies get emitted here.
#define DISCORDPP_IMPLEMENTATION
#include <discordpp.h>
#endif

namespace ballistica::base {

#if BA_ENABLE_DISCORD

// Ballistica's Discord application ID (registered at
// https://discord.com/developers/applications). Shared between dev and
// prod for now; if we ever split those, move this behind a buildconfig
// switch.
constexpr uint64_t kApplicationId{1373228222002626610ULL};

static auto TranslateSeverity(discordpp::LoggingSeverity severity) -> LogLevel {
  switch (severity) {
    case discordpp::LoggingSeverity::Verbose:
      return LogLevel::kDebug;
    case discordpp::LoggingSeverity::Info:
      return LogLevel::kInfo;
    case discordpp::LoggingSeverity::Warning:
      return LogLevel::kWarning;
    case discordpp::LoggingSeverity::Error:
      return LogLevel::kError;
    case discordpp::LoggingSeverity::None:
      return LogLevel::kInfo;
  }
  return LogLevel::kInfo;
}

Discord::Discord() : client_{std::make_unique<discordpp::Client>()} {
  g_core->logging->Log(
      LogName::kBaDiscord, LogLevel::kInfo,
      "Discord SDK initialized (v"
          + std::to_string(discordpp::Client::GetVersionMajor()) + "."
          + std::to_string(discordpp::Client::GetVersionMinor()) + "."
          + std::to_string(discordpp::Client::GetVersionPatch()) + ").");
  client_->AddLogCallback(
      [](std::string message, discordpp::LoggingSeverity severity) {
        // The SDK appends a trailing newline to each message which
        // turns into blank lines in our log output; strip it.
        while (!message.empty()
               && (message.back() == '\n' || message.back() == '\r')) {
          message.pop_back();
        }
        // The SDK's local-IPC manager (rpc_manager.cpp) retries every
        // ~2s when the Discord *desktop app* isn't running and emits
        // Warning-severity each time. That's harmless noise for users
        // who don't have Discord desktop installed, so demote it to
        // Debug — still visible at DEBUG, silent at default WARNING.
        // analytics.cpp fires similarly when the SDK's internal
        // analytics subsystem tries to emit an event before a token
        // is available — routine SDK-side race, not anything we care
        // about (we don't use the SDK's analytics).
        auto level{TranslateSeverity(severity)};
        if (message.find("rpc_manager.cpp") != std::string::npos
            || message.find("analytics.cpp") != std::string::npos) {
          level = LogLevel::kDebug;
        }
        g_core->logging->Log(LogName::kBaDiscord, level, "SDK: " + message);
      },
      discordpp::LoggingSeverity::Info);

  // Watch for the SDK reaching Ready state — that's when GetCurrentUser()
  // becomes valid and we can confirm who we signed in as.
  client_->SetStatusChangedCallback([this](discordpp::Client::Status status,
                                           discordpp::Client::Error error,
                                           int32_t errorDetail) {
    g_core->logging->Log(
        LogName::kBaDiscord, LogLevel::kInfo,
        "SDK status: " + discordpp::Client::StatusToString(status));
    if (error != discordpp::Client::Error::None) {
      g_core->logging->Log(
          LogName::kBaDiscord, LogLevel::kWarning,
          "SDK error: " + discordpp::Client::ErrorToString(error)
              + " (detail=" + std::to_string(errorDetail) + ").");
    }
    if (status == discordpp::Client::Status::Ready) {
      // Publish a basic "Playing <AppName>" activity. Discord renders
      // the app name from the developer-portal registration of our
      // application id, so this shows up as e.g. "Playing BombSquad"
      // without any text coming from our code. Python can call
      // discord_update_presence() later to override with richer state.
      discordpp::Activity default_activity;
      default_activity.SetType(discordpp::ActivityTypes::Playing);
      client_->UpdateRichPresence(
          std::move(default_activity), [](discordpp::ClientResult result) {
            if (!result.Successful()) {
              g_core->logging->Log(LogName::kBaDiscord, LogLevel::kWarning,
                                   "Default Rich Presence update failed: "
                                       + result.Error() + ".");
            }
          });

      auto user{client_->GetCurrentUserV2()};
      if (user.has_value()) {
        auto login_id{std::to_string(user->Id())};
        g_core->logging->Log(LogName::kBaDiscord, LogLevel::kInfo,
                             "Signed in as " + user->DisplayName()
                                 + " (id=" + login_id
                                 + ", username=" + user->Username() + ").");
        // If we captured a refresh token during the auth flow leading
        // up to this Ready event, now's when we have the matching user
        // id to pair it with. Hand them both to Python for persistent
        // storage.
        if (!pending_refresh_token_.empty()) {
          g_core->logging->Log(LogName::kBaDiscord, LogLevel::kDebug,
                               "Delivering refresh token to Python for "
                               "persistent storage (user_id="
                                   + login_id + ").");
          ReportDiscordAuth(pending_refresh_token_, login_id);
          pending_refresh_token_.clear();
        }
      } else {
        g_core->logging->Log(LogName::kBaDiscord, LogLevel::kWarning,
                             "SDK Ready but GetCurrentUserV2 returned "
                             "no user.");
      }
    }
  });
}

void Discord::ReportDiscordAuth(const std::string& refresh_token,
                                const std::string& user_id) {
  assert(g_base->InLogicThread());
  PythonRef args(Py_BuildValue("(ss)", refresh_token.c_str(), user_id.c_str()),
                 PythonRef::kSteal);
  g_base->python->objs()
      .Get(BasePython::ObjID::kDiscordAuthReceivedCall)
      .Call(args);
}

Discord::~Discord() = default;

void Discord::StepDisplayTime() {
  assert(g_base->InLogicThread());
  discordpp::RunCallbacks();
}

// Reports a sign-in result back to the Python-side pending-attempts map
// (see babase._login.discord_sign_in). Empty token signals failure.
static void ReportSignInTokenResult(int attempt_id, const std::string& token) {
  assert(g_base->InLogicThread());
  PythonRef args(
      Py_BuildValue("(ss)", std::to_string(attempt_id).c_str(), token.c_str()),
      PythonRef::kSteal);
  g_base->python->objs()
      .Get(BasePython::ObjID::kDiscordSignInTokenResponseCall)
      .Call(args);
}

void Discord::SignIn(int attempt_id) {
  assert(g_base->InLogicThread());

  // Generate a PKCE code challenge/verifier pair. The challenge is sent
  // with the authorize request; the verifier is held until the token
  // exchange step proves we're the same client.
  auto code{client_->CreateAuthorizationCodeVerifier()};
  auto verifier{code.Verifier()};

  discordpp::AuthorizationArgs args;
  args.SetClientId(kApplicationId);
  // Presence scope set (GA): identify, friends list, rich presence,
  // provisional accounts, activity invites. Bump to Communications scopes
  // later if/when we want lobbies/voice/DMs.
  args.SetScopes(discordpp::Client::GetDefaultPresenceScopes());
  args.SetCodeChallenge(code.Challenge());

  g_core->logging->Log(LogName::kBaDiscord, LogLevel::kInfo,
                       "Starting Discord OAuth flow (scopes="
                           + discordpp::Client::GetDefaultPresenceScopes()
                           + ")...");

  client_->Authorize(args, [this, verifier, attempt_id](
                               discordpp::ClientResult result,
                               std::string code_value,
                               std::string redirect_uri) {
    if (!result.Successful()) {
      g_core->logging->Log(LogName::kBaDiscord, LogLevel::kWarning,
                           "Authorize failed: " + result.Error() + ".");
      ReportSignInTokenResult(attempt_id, "");
      return;
    }
    g_core->logging->Log(LogName::kBaDiscord, LogLevel::kInfo,
                         "Got auth code; exchanging for access token...");

    client_->GetToken(
        kApplicationId, code_value, verifier, redirect_uri,
        [this, attempt_id](discordpp::ClientResult result,
                           std::string access_token, std::string refresh_token,
                           discordpp::AuthorizationTokenType token_type,
                           int32_t expires_in, std::string scopes) {
          if (!result.Successful()) {
            g_core->logging->Log(LogName::kBaDiscord, LogLevel::kWarning,
                                 "GetToken failed: " + result.Error() + ".");
            ReportSignInTokenResult(attempt_id, "");
            return;
          }
          g_core->logging->Log(
              LogName::kBaDiscord, LogLevel::kInfo,
              "Got access token (expires in " + std::to_string(expires_in)
                  + "s, scopes=" + scopes + "); connecting...");

          // Stash the refresh token; when SDK hits Ready we'll pair
          // it with the Discord user id and hand both to Python for
          // persistent storage (so next launch we can reconnect
          // without a browser OAuth flow).
          pending_refresh_token_ = refresh_token;

          // Deliver the token to the Python sign-in flow. The SDK
          // gateway connection below is independent — it just sets
          // up Rich Presence.
          ReportSignInTokenResult(attempt_id, access_token);

          client_->UpdateToken(
              token_type, access_token, [this](discordpp::ClientResult result) {
                if (!result.Successful()) {
                  g_core->logging->Log(
                      LogName::kBaDiscord, LogLevel::kWarning,
                      "UpdateToken failed: " + result.Error() + ".");
                  return;
                }
                client_->Connect();
              });
        });
  });
}

void Discord::ReconnectWithRefreshToken(const std::string& refresh_token) {
  assert(g_base->InLogicThread());
  if (refresh_token.empty()) {
    g_core->logging->Log(LogName::kBaDiscord, LogLevel::kWarning,
                         "ReconnectWithRefreshToken called with empty token; "
                         "ignoring.");
    return;
  }
  g_core->logging->Log(LogName::kBaDiscord, LogLevel::kInfo,
                       "Reconnecting to Discord using stored refresh token...");

  client_->RefreshToken(
      kApplicationId, refresh_token,
      [this](discordpp::ClientResult result, std::string new_access_token,
             std::string new_refresh_token,
             discordpp::AuthorizationTokenType token_type, int32_t expires_in,
             std::string scopes) {
        if (!result.Successful()) {
          g_core->logging->Log(LogName::kBaDiscord, LogLevel::kWarning,
                               "RefreshToken failed: " + result.Error()
                                   + "; clearing stored auth.");
          // Tell Python to drop the stored token — it's no longer
          // valid (rotation race, revocation, or similar).
          ReportDiscordAuth("", "");
          return;
        }
        g_core->logging->Log(LogName::kBaDiscord, LogLevel::kInfo,
                             "Refreshed access token (expires in "
                                 + std::to_string(expires_in)
                                 + "s, scopes=" + scopes + "); connecting...");

        // Stash the new refresh token; when SDK hits Ready we'll
        // pair it with the user id and persist. Storing via the
        // Ready callback (rather than here) ensures the persisted
        // token is always accompanied by a verified user id.
        pending_refresh_token_ = new_refresh_token;

        client_->UpdateToken(token_type, new_access_token,
                             [this](discordpp::ClientResult result) {
                               if (!result.Successful()) {
                                 g_core->logging->Log(
                                     LogName::kBaDiscord, LogLevel::kWarning,
                                     "UpdateToken (after refresh) failed: "
                                         + result.Error() + ".");
                                 return;
                               }
                               client_->Connect();
                             });
      });
}

void Discord::UpdatePresence(const std::string& state,
                             const std::string& details) {
  assert(g_base->InLogicThread());
  if (client_->GetStatus() != discordpp::Client::Status::Ready) {
    g_core->logging->Log(LogName::kBaDiscord, LogLevel::kWarning,
                         "UpdatePresence called but SDK not Ready; "
                         "skipping. (Call discord_sign_in first.)");
    return;
  }
  discordpp::Activity activity;
  activity.SetType(discordpp::ActivityTypes::Playing);
  activity.SetState(state);
  activity.SetDetails(details);
  client_->UpdateRichPresence(
      std::move(activity), [](discordpp::ClientResult result) {
        if (!result.Successful()) {
          g_core->logging->Log(
              LogName::kBaDiscord, LogLevel::kWarning,
              "UpdateRichPresence failed: " + result.Error() + ".");
        } else {
          g_core->logging->Log(LogName::kBaDiscord, LogLevel::kInfo,
                               "Rich Presence updated.");
        }
      });
}

#else  // BA_ENABLE_DISCORD

Discord::Discord() = default;
Discord::~Discord() = default;
void Discord::StepDisplayTime() {}
void Discord::SignIn(int) {}
void Discord::UpdatePresence(const std::string&, const std::string&) {}
void Discord::ReconnectWithRefreshToken(const std::string&) {}
void Discord::ReportDiscordAuth(const std::string&, const std::string&) {}

#endif  // BA_ENABLE_DISCORD

}  // namespace ballistica::base
