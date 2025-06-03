// Released under the MIT License. See LICENSE for details.

#define DISCORDPP_IMPLEMENTATION
#if BA_ENABLE_DISCORD
#pragma comment( \
    lib,         \
    "../../src/external/discord_social_sdk/lib/debug/discord_partner_sdk.lib")
#include "ballistica/base/discord/discord.h"

#include <atomic>
#include <csignal>
#include <cstdio>
#include <fstream>
#include <functional>
#include <iostream>
#include <memory>
#include <string>
#include <thread>

#include "external/discord_social_sdk/include/discordpp.h"

namespace ballistica::base {

std::atomic<bool> running = true;

void signalHandler(int signum) { running.store(false); }

std::shared_ptr<discordpp::Client> Discord::init() {
  std::cout << "🚀 Initializing Discord SDK...\n";
  client = std::make_shared<discordpp::Client>();
  auto client_ = client;
  client->AddLogCallback(
      [](auto message, auto severity) {
        // std::cout << "[" << EnumToString(severity) << "] " << message
        //           << std::endl;
      },
      discordpp::LoggingSeverity::Info);

  client->SetStatusChangedCallback(
      [this, client_](discordpp::Client::Status status,
                      discordpp::Client::Error error, int32_t errorDetail) {
        std::cout << "🔄 Status changed: "
                  << discordpp::Client::StatusToString(status) << std::endl;

        if (status == discordpp::Client::Status::Ready) {
          client_is_ready = true;
          std::cout << "✅ Client is ready! You can now call SDK functions.\n";
          // SetActivity(client, "alpha", "discord social sdk", "globe",
          //             "Large Image Text", "party", "smol party", 0, 0);

        } else if (error != discordpp::Client::Error::None) {
          client_is_ready = false;
          std::cerr << "❌ Connection Error: "
                    << discordpp::Client::ErrorToString(error)
                    << " - Details: " << errorDetail << std::endl;
        }
      });
  client->SetMessageCreatedCallback([client_, this](uint64_t messageId) {
    // if (!(messageId == oldMessageId_)) { // this doesnt work
    auto message = client_->GetMessageHandle(messageId);
    std::cout << "📨 New message received: " << message->Content() << "\n";
    // }
  });

  authenticate();

  std::thread discordThread([&]() {
    while (running) {
      discordpp::RunCallbacks();
      std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
  });
  discordThread.detach();
  return client;
}

void Discord::authenticate() {
  // Generate OAuth2 code verifier for authentication
  auto codeVerifier = client->CreateAuthorizationCodeVerifier();
  // Set up authentication arguments
  discordpp::AuthorizationArgs args{};
  args.SetClientId(APPLICATION_ID);
  args.SetScopes(discordpp::Client::GetDefaultCommunicationScopes());
  args.SetCodeChallenge(codeVerifier.Challenge());

  std::fstream file("discord_auth.txt", std::ios::in);
  std::string accessToken;
  file >> accessToken;
  file.close();
  auto client = this->client;
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
}

void Discord::SetActivity(const char* state, const char* details,
                          const char* largeImageKey, const char* largeImageText,
                          const char* smallImageKey, const char* smallImageText,
                          int64_t startTimestamp, int64_t endTimestamp) {
  if (!client) {
    return;
  }

  std::cout << "Setting activity...\n";
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
  UpdateRP();
}

void Discord::AddButton(const char* label, const char* url) {
  if (!client) {
    return;
  }
  std::cout << "Adding button...\n";
  discordpp::ActivityButton button;
  button.SetLabel(label);
  button.SetUrl(url);
  activity.AddButton(button);
  std::cout << "Button added!\n";
  UpdateRP();
}

void Discord::SetParty(const char* partyId, int currentPartySize,
                       int maxPartySize) {
  if (!client) {
    return;
  }
  std::cout << "Setting party...\n";
  discordpp::ActivityParty party;
  party.SetId("party1234");
  party.SetCurrentSize(1);
  party.SetMaxSize(5);
  activity.SetParty(party);
  std::cout << "Party set!\n";

  activity.SetSupportedPlatforms(discordpp::ActivityGamePlatforms::Desktop);
  activity.SetSupportedPlatforms(discordpp::ActivityGamePlatforms::Android);
  discordpp::ActivitySecrets secrets;
  secrets.SetJoin("joinsecret1234");  // Example join secret
  activity.SetSecrets(secrets);
  client->RegisterLaunchCommand(
      APPLICATION_ID, "bombsquad://");  // Example deeplink command Create or
                                        // join a lobby from the client
  UpdateRP();
}

void Discord::JoinLobby(const char* lobbySecret) {
  if (!client) {
    return;
  }
  client->CreateOrJoinLobby(
      "my_lobby_secret",
      [this](discordpp::ClientResult result, uint64_t lobbyId) {
        if (result.Successful()) {
          lobbyId_ = lobbyId;
          std::cout << "🎮 Lobby created or joined successfully! Lobby Id: "
                    << lobbyId << std::endl;
        } else {
          std::cerr << "❌ Lobby creation/join failed\n";
        }
      });
}

void Discord::LeaveLobby() {
  if (!client) {
    return;
  }
  auto client_ = client;
  client->LeaveLobby(lobbyId_, [client_](discordpp::ClientResult result) {
    if (result.Successful()) {
      std::cout << "🎮 Left lobby successfully!\n";
    } else {
      std::cerr << "❌ Failed to leave lobby\n";
    }
  });
}

void Discord::SendLobbyMessage(const char* message) {
  if (!client || lobbyId_ == 0) {
    return;
  }
  auto client_ = client;
  client->SendLobbyMessage(
      lobbyId_, message,
      [client_](discordpp::ClientResult result, uint64_t messageId) {
        if (result.Successful()) {
          std::cout << "📨 Message sent successfully! Message ID: " << messageId
                    << "\n";
        } else {
          std::cerr << "❌ Failed to send message\n";
        }
      });
}

void Discord::UpdateRP() {
  if (!client) {
    return;
  }
  client->UpdateRichPresence(activity, [](discordpp::ClientResult result) {
    if (result.Successful()) {
      std::cout << "🎮 Rich Presence updated successfully!\n";
    } else {
      std::cerr << "❌ Rich Presence update failed\n";
    }
  });
}

}  // namespace ballistica::base

#endif  // BA_ENABLE_DISCORD
