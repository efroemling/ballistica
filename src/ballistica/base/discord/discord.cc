// Released under the MIT License. See LICENSE for details.

#define DISCORDPP_IMPLEMENTATION
#if BA_ENABLE_DISCORD
#include "discord.h"

#include <bits/stdc++.h>

#include <atomic>
#include <csignal>
#include <cstdio>
#include <functional>
#include <iostream>
#include <memory>
#include <thread>

#include "cdiscord.h"
#include "discordpp.h"

namespace ballistica::base {

std::atomic<bool> running = true;

void signalHandler(int signum) { running.store(false); }

std::shared_ptr<discordpp::Client> Discord::init() {
  std::signal(SIGINT, signalHandler);
  std::cout << "🚀 Initializing Discord SDK...\n";
  auto client = std::make_shared<discordpp::Client>();

  client->AddLogCallback(
      [](auto message, auto severity) {
        // std::cout << "[" << EnumToString(severity) << "] " << message
        //           << std::endl;
      },
      discordpp::LoggingSeverity::Info);

  client->SetStatusChangedCallback(
      [this, client](discordpp::Client::Status status,
                     discordpp::Client::Error error, int32_t errorDetail) {
        std::cout << "🔄 Status changed: "
                  << discordpp::Client::StatusToString(status) << std::endl;

        if (status == discordpp::Client::Status::Ready) {
          std::cout << "✅ Client is ready! You can now call SDK functions.\n";
          SetActivity(client, "alpha", "discord social sdk", "globe",
                      "Large Image Text", "party", "smol party", 0, 0);

        } else if (error != discordpp::Client::Error::None) {
          std::cerr << "❌ Connection Error: "
                    << discordpp::Client::ErrorToString(error)
                    << " - Details: " << errorDetail << std::endl;
        }
      });

  authenticate(client);

  std::thread discordThread([&]() {
    while (running) {
      discordpp::RunCallbacks();
      std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
  });
  discordThread.detach();
  return client;
}

void Discord::authenticate(std::shared_ptr<discordpp::Client> client) {
  // Generate OAuth2 code verifier for authentication
  auto codeVerifier = client->CreateAuthorizationCodeVerifier();
  // Set up authentication arguments
  discordpp::AuthorizationArgs args{};
  args.SetClientId(APPLICATION_ID);
  args.SetScopes(discordpp::Client::GetDefaultPresenceScopes());
  args.SetCodeChallenge(codeVerifier.Challenge());

  std::fstream file("discord_auth.txt", std::ios::in);
  std::string accessToken;
  file >> accessToken;
  file.close();

  if (accessToken.empty()) {
    // Begin authentication process
    client->Authorize(args, [this, client, codeVerifier](auto result, auto code,
                                                         auto redirectUri) {
      if (!result.Successful()) {
        std::cerr << "❌ Authentication Error: " << result.Error() << std::endl;
        return;
      } else {
        std::cout << "✅ Authorization successful! Getting access token...\n";

        // Exchange auth code for access token
        client->GetToken(
            APPLICATION_ID, code, codeVerifier.Verifier(), redirectUri,
            [client](discordpp::ClientResult result, std::string accessToken,
                     std::string refreshToken,
                     discordpp::AuthorizationTokenType tokenType,
                     int32_t expiresIn, std::string scope) {
              std::cout
                  << "🔓 Access token received! Establishing connection...\n";
              std::fstream file("discord_auth.txt", std::ios::out);
              file << accessToken << std::endl;
              file.close();
              std::cout << "🔑 Access token found! Using it to connect...\n";
              client->UpdateToken(
                  discordpp::AuthorizationTokenType::Bearer, accessToken,
                  [client](discordpp::ClientResult result) {
                    if (result.Successful()) {
                      std::cout
                          << "🔑 Token updated, connecting to Discord...\n";
                      client->Connect();
                    } else {
                      std::cerr
                          << "❌ Failed to update token: " << result.Error()
                          << std::endl;
                    }
                  });
            });
      }
    });

  } else if (!accessToken.empty()) {
    std::cout << "🔑 Access token found! Using it to connect...\n";
    client->UpdateToken(
        discordpp::AuthorizationTokenType::Bearer, accessToken,
        [client](discordpp::ClientResult result) {
          if (result.Successful()) {
            std::cout << "🔑 Token updated, connecting to Discord...\n";
            client->Connect();
          } else {
            std::cerr << "❌ Failed to update token: " << result.Error()
                      << std::endl;
          }
        });
  }
  return;
};

void Discord::SetActivity(std::shared_ptr<discordpp::Client> client,
                          const char* state, const char* details,
                          const char* largeImageKey, const char* largeImageText,
                          const char* smallImageKey, const char* smallImageText,
                          int64_t startTimestamp, int64_t endTimestamp) {
  if (!client) {
    return;
  }
  std::cout << "Setting activity...\n";
  discordpp::Activity activity{};
  // activity.SetSupportedPlatforms(static_cast<discordpp::ActivityGamePlatforms>(
  //     static_cast<int>(discordpp::ActivityGamePlatforms::Desktop)
  //     | static_cast<int>(discordpp::ActivityGamePlatforms::IOS)
  //     | static_cast<int>(discordpp::ActivityGamePlatforms::Android)
  //     | static_cast<int>(discordpp::ActivityGamePlatforms::Embedded)));
  // Set properties if provided
  activity.SetType(discordpp::ActivityTypes::Playing);
  if (state) activity.SetState(state);
  if (details) activity.SetDetails(details);

  // Set timestamps if provided
  // if (startTimestamp > 0)
  // activity.SetTimestamps(activity.Timestamps(startTimestamp)); if
  // (endTimestamp > 0) activity.GetTimestamps().SetEnd(endTimestamp);

  discordpp::ActivityAssets assets{};
  if (largeImageKey) assets.SetLargeImage(largeImageKey);
  if (largeImageText) assets.SetLargeText(largeImageText);
  if (smallImageKey) assets.SetSmallImage(smallImageKey);
  if (smallImageText) assets.SetSmallText(smallImageText);
  activity.SetAssets(assets);
  client->UpdateRichPresence(activity, [](discordpp::ClientResult result) {
    if (result.Successful()) {
      std::cout << "🎮 Rich Presence updated successfully!\n";
    } else {
      std::cerr << "❌ Rich Presence update failed";
    }
  });
}
}  // namespace ballistica::base

#endif  // BA_ENABLE_DISCORD
