# Ballistica Discord Integration

Design notes for integrating the [Discord Social SDK](https://discord.com/developers/social-sdk) into Ballistica. Phase 1 (sign-in) is in progress; phase 2 (provisional accounts) is planned.

## Goals

Two user-facing capabilities, to be delivered in order:

1. **Sign in with Discord** as a first-class V2 login type, alongside Google Play Game Services, Game Center, V2 email, etc. A V2 account may have a Discord login attached just like any other provider.
2. **Discord features (voice chat, lobby chat, friends) for every player**, regardless of whether they have a Discord account:
   - If the signed-in V2 account has a Discord login attached **and** Discord is locally authenticated → real Discord user experience.
   - Otherwise → a Discord **provisional account** wrapped around the V2 account, using a JWT the master server signs on the client's behalf. This includes the case where a V2 account *has* a Discord login attached but the local device isn't currently authenticated with Discord (e.g. signed in via email, or the refresh token expired). Provisional accounts can later be merged into a full Discord account if the user signs in to Discord.

## SDK availability and public/internal split

The Discord Social SDK is not redistributable, so we treat the build tooling as two layers:

- **Source is public.** The `option(DISCORD ...)` and `if(DISCORD)` block in `ballisticakit-cmake/CMakeLists.txt`, the `BA_ENABLE_DISCORD` buildconfig define, the C++ `Discord` class (guarded by `#if BA_ENABLE_DISCORD`, so it's a no-op by default), and any Python integration all ship in the public repo. A public contributor can read how it all fits together and, with a bit of manual work, compile with Discord enabled.
- **Automation is internal-only.** The `make discord-social-sdk` Makefile target (which fetches our internal archive) and the `cmake-ex` target family (which uses it) are wrapped in `__PUBSYNC_STRIP_BEGIN__` / `__PUBSYNC_STRIP_END__` markers and do not appear in the public repo.

**Public build instructions (for someone wanting Discord support):**

1. Download the Discord Social SDK from https://discord.com/developers/social-sdk.
2. Unpack it to `build/discord_social_sdk/` so that `build/discord_social_sdk/include/discordpp.h` exists.
3. Configure cmake with `-DDISCORD=ON`, e.g. into a dedicated build dir to keep it separate from the vanilla build.

**Internal build:** `make cmake-ex` (or `make cmake-build-ex`) does the fetch + configure + build automatically. Build artifacts go to `build/cmake/<type>-ex/`.

**Sensitive bits later:** Discord app IDs, any server-side JWT signing keys, and other Ballistica-specific values go under `plus/` (closed-source feature set) when they arrive. The basic SDK wiring does not need this yet.

## Design principles to preserve provisional support

Phase (1) is in progress. Three design seams keep (2) a clean addition rather than a refactor:

### 1. `LoginType.DISCORD` means "a real linked Discord account," not "Discord features are active"

Provisional use is not a login type. It is a *session mode* that applies when we want to use the Social SDK but don't have an active local Discord authentication — either because the account has no Discord login attached, or because it does but the local device isn't currently authenticated with Discord. Keeping these concepts separate avoids contorted UI logic.

### 2. Adapter state vs. feature availability are distinct

The `DiscordLoginAdapter` reports whether Discord OAuth tokens exist locally — nothing else. A separate notion, e.g. `discord_features_available`, drives whether the Social SDK is engaged. Today that reduces to "DISCORD in `accounts.primary.logins`"; later it can also include "provisional mode was successfully established." UI code reads the abstract flag.

### 3. Credentials-check response carries a session-mode field from day one

When the master server returns credentials-check info to the client, include a `discord_session_mode` field (or similar) even if its only values today are `"linked"` and `"none"`. Adding a new `"provisional"` variant later is a pure extension; restructuring an existing field is worse.

Exposed on `AccountV2Handle` as a sibling to the existing `logins` dict, not overloaded onto it.

## Architecture sketch

### Client

- New `LoginType.DISCORD` in `tools/bacommon/login.py`.
- New `DiscordLoginAdapter` in `babase/_login.py`, mirroring the GPGS/Game Center adapters. Reports implicit state based on whether a Discord refresh token is present in secure local storage.
- New C++ subsystem that wraps the Discord Social SDK. Lifecycle is explicitly configurable: `configure(mode=RealUser(token=...) | Provisional(jwt=...) | Disabled)`. The mode is driven by account subsystem state, not adapter state directly — a signed-in V2 account with no local Discord auth still gets `Provisional` mode, not `Disabled`. Transitions between `RealUser` and `Provisional` should be seamless (no feature gap).
- Secure refresh-token storage (Keychain on macOS/iOS, Credential Manager on Windows, etc.). **Not** a plaintext file.
- Handle Discord's token-rotation: on each refresh the old refresh token is invalidated and a new one is issued. Persist the new one before the next launch, or the session is locked out.

### Master server

- New endpoint to attach/detach a Discord login on a V2 account. Verifies the supplied Discord token by calling `GET /users/@me` against Discord's API.
- Token-verification logic implemented as a reusable helper, not inline in the attach handler. Provisional minting will reuse the same "is this a valid Discord interaction?" pattern in reverse.
- (Deferred) JWT-signing for provisional accounts. Decide whether to use a dedicated signing key or reuse an existing V2 key — lean toward **dedicated** for blast-radius containment and easier rotation. Register the public key with Discord as a trusted external issuer.

### UI

- **"Sign In With Discord" button** in the account-settings window. This is a dual-purpose button:
  - **Account has no Discord login attached:** initiates the Discord OAuth flow and then offers to *link* the resulting Discord identity to the current V2 account. This is much simpler for the user than the alternative of creating a separate Discord-based account and then merging.
  - **Account has a Discord login attached but Discord is not locally authenticated:** authenticates locally with Discord, upgrading the session from provisional to the real linked Discord identity.
- **Provisional fallback nudge:** when a user's V2 account has a Discord login attached but the client falls back to a provisional session (token expired, signed in via another method, etc.), show a transient screen message like "Sign in with Discord to use your full Discord identity." This keeps users aware without blocking anything.
- **"Don't remind me" checkbox** below the "Sign In With Discord" button in the account page. Suppresses the provisional-fallback nudge for users who can't or don't want to sign into Discord on this device (shared machines, preference, etc.). Stored per-device, not per-account.

## Provisional fallback behavior

The goal is **no gap in Discord service.** Every signed-in user gets Discord features (voice chat, lobby chat, friends) immediately, whether via a real Discord identity or a provisional one.

### Session mode transitions

| Account state | Local Discord auth | Session mode |
|---|---|---|
| No Discord login attached | N/A | Provisional |
| Discord login attached | Authenticated | Real (linked) |
| Discord login attached | Not authenticated (token expired, signed in via other method) | Provisional + nudge |

When a real Discord session drops to provisional (e.g. refresh token expires mid-session), the transition should be silent from a features standpoint — voice chat continues, just under a provisional identity. The nudge message informs the user but doesn't interrupt.

### Two-device scenario

If the same V2 account is signed in on device A (real Discord) and device B (provisional), the user appears in Discord as two separate identities. This is by design — provisional accounts are distinct Discord identities. The nudge on device B tells the user they can sign in with Discord to unify. No server-side deduplication needed.

## Security notes

- Discord refresh tokens are bearer credentials. Encrypt at rest; never log; exclude from crash reports. Revoke via `/oauth2/token/revoke` on explicit sign-out.
- Do not sync refresh tokens between devices via the V2 account. Each device does its own first-time OAuth; this keeps the blast radius small if V2 account data is ever compromised.
- Provisional account JWTs should have short lifetimes (minutes) and be minted on demand rather than cached.

## What to avoid

- Do **not** wrap the Discord Social SDK in an abstraction layer "in case we need to swap the backend." The seams that matter are at the account/identity boundary, not the SDK boundary.
- Do **not** pre-add empty `TODO(provisional)` stubs throughout the codebase. The discipline is "design leaves room for it," not "code gestures at it." Stubs rot.
- Do **not** persist "which login type was used last launch" client-side. The existing V2 pattern re-derives this every session from server response + live adapter state, and the same approach works for Discord.

## Prior implementation (reference only)

An earlier contribution scaffolded Rich Presence and lobby bindings for the Social SDK but never got the build flag wired through, stored tokens in plaintext, and the `SetParty` implementation ignored its arguments in favor of hardcoded values. The approach did not match the design above, so all of it has been stripped.

If useful as reference, the code is preserved in git history at commit **`9edc28ff4eb530dc33a13bc49a92c67dee849463`** (the commit immediately before removal). To inspect, e.g.:

```
git show 9edc28ff4:src/ballistica/base/discord/discord.cc
git show 9edc28ff4:src/ballistica/base/discord/discord.h
git show 9edc28ff4:src/assets/ba_data/python/babase/_discord.py
git show 9edc28ff4 -- 'src/ballistica/base/discord/*' \
    'src/assets/ba_data/python/babase/_discord.py' \
    'src/ballistica/base/python/methods/python_methods_base_1.cc'
```

What was kept from the prior work:
- The SDK-fetch Makefile target (`make discord-social-sdk`) — written separately and independently useful.
- The `discordLogo` / `discordServer` textures — referenced by the unrelated pre-existing "Join our Discord server" UI.
- The "Join our Discord server" UI (`bauiv1lib/discord.py`) — predates the SDK work and is unrelated to account/Social-SDK integration.
