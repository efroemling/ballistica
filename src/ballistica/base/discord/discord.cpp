// Released under the MIT License. See LICENSE for details.

#define DISCORDPP_IMPLEMENTATION
#include "discord.h"

#include <atomic>
#include <csignal>
#include <functional>
#include <iostream>
#include <thread>

#include "cdiscord.h"
#include "discordpp.h"

namespace ballistica::base {

void DiscordClient::init() {
  // Replace with your Discord Application ID
  const uint64_t APPLICATION_ID = 1234567890123456789;

  std::cout << "🚀 Initializing Discord SDK...\n";
  auto client = std::make_shared<discordpp::Client>();
  client->AddLogCallback(
      [](auto message, auto severity) {
        printf("[%d] %s", static_cast<int>(severity), message.c_str());
      },
      discordpp::LoggingSeverity::Info);

  client->SetStatusChangedCallback(
      [client](auto status, auto error, auto details) {
        printf("Status has changed to %s\n",
               discordpp::Client::StatusToString(status).c_str());
        if (status == discordpp::Client::Status::Ready) {
          printf(
              "Client is ready, you can now call SDK functions. For "
              "example:\n");
          printf("You have %d friends\n",
                 static_cast<int>(client->GetRelationships().size()));
        } else if (error != discordpp::Client::Error::None) {
          printf("Error connecting: %s %d\n",
                 discordpp::Client::ErrorToString(error).c_str(), details);
        } else {
          printf("Status changed to %s\n",
                 discordpp::Client::StatusToString(status).c_str());
        }
      });
  auto codeVerifier = client->CreateAuthorizationCodeVerifier();
  discordpp::AuthorizationArgs args{};
  args.SetClientId(APPLICATION_ID);
  args.SetScopes(
      discordpp::Client::
          GetDefaultPresenceScopes());  // or
                                        // discordpp::Client::GetDefaultCommunicationScopes()
  args.SetCodeChallenge(codeVerifier.Challenge());

  client->Authorize(
      args, [client, codeVerifier](auto result, auto code, auto redirectUri) {
        if (!result.Successful()) {
          printf("Auth Error: %s\n", result.ToString().c_str());
        } else {
          printf("Received authorization code, exchanging for access token\n");
          client->GetToken(
              APPLICATION_ID, code, codeVerifier.Verifier(), redirectUri,
              [client](auto result, auto accessToken, auto refreshToken, auto,
                       auto, auto) {
                printf("Received access token, connecting to Discord\n");
                client->UpdateToken(
                    discordpp::AuthorizationTokenType::Bearer, accessToken,
                    [client](auto result) { client->Connect(); });
              });
        }
      });
}

};  // namespace ballistica::base