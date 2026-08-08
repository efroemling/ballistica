# Network Availability Signal

**Description:** The OS-backed "definitely offline" signal that gates connectivity/transport network retries — platform plumbing, per-OS implementations, and key design decisions.

An OS-backed "is the network path available right now?" signal that
the engine and Python latch onto, so persistent network activity
(connectivity pings, transport agent retries, etc.) short-circuits
when the device is clearly offline.

Primary motivation: avoid burning CPU / battery / data on doomed
network attempts. Secondary: a foundation for any future "show
offline state in UI" work, though that's not the immediate driver.

## Non-goals

- **Not** a replacement for actual reachability / health probes. The
  signal is a strict "definitely offline; don't try" gate, not an
  "internet really works" guarantee. Existing probes still run when
  the path is available.
- **Not** a UX surface (yet). Internal request-gating only.

## Architecture

### C++ Platform abstraction — `src/ballistica/core/platform/platform.{h,cc}`

- `Platform::AddNetworkAvailabilityCallback(cb)` — public, non-virtual.
  Manages the callback list, change-dedup, and DEBUG-level logging on
  `ba.networking`. Fires `cb` synchronously with the current value
  (only when the value is non-default `true`), then again on every
  change.
- `Platform::DoStartNetworkAvailabilityMonitoring()` — protected
  virtual hook, called once on first registration. Default impl
  immediately reports `true` so platforms without a native
  implementation aren't stuck offline forever. Per-OS subclasses
  override to subscribe to the OS API and report state changes via
  `SetNetworkAvailability`.
- `Platform::SetNetworkAvailability(bool)` — protected, called by
  subclasses (and the debug toggler) when the OS reports a change.
  Thread-safe; can be invoked from any thread.
- `Platform::StopNetworkAvailabilityDispatch()` — public, called
  early in app shutdown. See [Shutdown gating](#shutdown-gating).

The cached value defaults to `false` so consumers must wait for an
affirmative `true` callback before assuming network is up. This
avoids races where code at startup reads the value before the
platform's first OS report has arrived.

### Python binding — `src/ballistica/base/python/methods/python_methods_base_3.cc`

- `_babase.add_network_availability_callback(call)` — wraps the Python
  callable in a GIL-acquiring lambda before passing to `Platform`. No
  deregistration. Safe to call from any Python-running thread (no
  logic-thread precondition).

### Python public surface — `src/assets/ba_data/python/babase/_net.py`

- `NetworkSubsystem` registers an internal handler that updates
  `self._available`.
- `babase.app.net.available -> bool` is the public read-only property.
  Docstring spells out that `True` means "maybe online" — captive
  portals and ISP outages still report `True`, so callers still need
  real reachability probes; the property is really only useful for
  confirming *non-functional* states (airplane mode, ethernet
  unplugged, etc.).

### Connectivity subsystem — `src/codegen/bapluscodegen/pyembed/connectivity.py`

- `ConnectivityManager.network_available: bool` — local mirror,
  self-contained (subscribes via its own callback rather than reading
  `babase.app.net.available`, to avoid subsystem callback-ordering
  races).
- `_kick_event: asyncio.Event` — set on `False → True` transitions to
  wake the cycle out of its 3.85s sleep immediately.
- `_cycle_loop`'s sleep waits on shutdown OR kick OR timeout.
- `_fetch_basn_list` early-returns when `not network_available` —
  preserves the saved bootstrap address (no spurious "all-attempts-
  failed" path) and avoids per-cycle error-log spam.
- `_run_due_pings` and `_ping` also gate via the local field.

### v2transport subsystem — `src/codegen/bapluscodegen/pyembed/v2transport.py`

- `V2Transport.network_available: bool` — local mirror, same pattern.
- `_wake_event: asyncio.Event` — set on `False → True`.
- `_sleep_and_launch_primary_session` waits via
  `asyncio.wait_for(self._wake_event.wait(), timeout=sleep_seconds)`
  instead of plain `asyncio.sleep`. Either path falls through to the
  same "is primary still needed?" check, so the spawn logic stays in
  one place.
- `on_session_finished` only counts `_consecutive_errors += 1` when
  `network_available` is True. Gated failures don't escalate backoff —
  a brief offline window doesn't push us out of tier 0 (~2.4s base
  sleep) and into tier 1+ (5s+).
- `_establish_ws_endpoint` reads `self.parent.network_available`
  instead of `_babase.app.net.available`, for consistency with the
  gate-vs-real-failure logic upstream.

### Shutdown gating

`Platform::StopNetworkAvailabilityDispatch()` is called from the top
of `Logic::OnAppShutdown` before any subsystem teardown begins.
Once called, `SetNetworkAvailability` and the synchronous fire from
`AddNetworkAvailabilityCallback` become no-ops — guarded by the
existing `network_availability_mutex_`.

The OS-level monitors themselves are not torn down. They live on
detached threads (Apple's NWPathMonitor dispatch queue, Windows'
COM RPC thread pool, Android's NetworkCallback handler) until
process exit; the gate just silences their effect on subscribers.
This prevents late callbacks from reaching subscribers (or the
Python GIL) while the shutdown cascade is dismantling them, which
otherwise risks `RuntimeError: Event loop is closed` from the
subsystems' `call_soon_threadsafe` wakes if a callback fires after
the asyncio loop has been closed.

### Debug toggle

`BA_NETWORK_AVAILABILITY_DEBUG_TOGGLE=1` bypasses real platform
monitoring and runs a detached thread that flips state every 5s,
starting in `false`. Used for testing consumers without actually
severing the network. Implemented as a `std::thread(...).detach()`
running an infinite 5s-toggle loop; tiny shutdown-race window
accepted since the feature is opt-in. Comment at the spawn site
documents the joinable-thread upgrade path if we ever want to close
it.

## Per-platform implementations

Each platform overrides
`Platform::DoStartNetworkAvailabilityMonitoring()` to subscribe to
its OS API. Forwarding back into the generic dispatch path goes
through `SetNetworkAvailability(bool)`.

### Apple (macOS / iOS / tvOS)

- Swift `NWPathMonitor` in `src/ballistica/base/app_platform/apple/FromCpp.swift`
  (`startNetAvailabilityMonitoring()`). Started on a private dispatch
  queue.
- Swift→C++ bridge via
  `src/ballistica/base/app_platform/apple/from_swift.{h,cc}` — the
  `pathUpdateHandler` block calls
  `ballistica::base::from_swift::OnNetAvailChanged(bool)` which
  forwards to `PlatformApple::OnNetAvailChanged` →
  `SetNetworkAvailability`.
- `PlatformApple::DoStartNetworkAvailabilityMonitoring()` calls into
  the Swift bridge when `BA_XCODE_BUILD`; falls through to the
  default on cmake builds (mac headless server).
- Path test: `path.status == .satisfied`.
- Available since iOS 12 / macOS 10.14 / tvOS 12 (deployment targets
  well above).

### Android

- Java side: `BallisticaContext.java` registers a
  `ConnectivityManager.NetworkCallback` via
  `registerDefaultNetworkCallback`.
- `onAvailable` / `onLost` translate to JNI
  `nativeOnNetAvailChanged(boolean)` (in `from_java.cc`) →
  `PlatformAndroid::NativeOnNetAvailChanged` →
  `SetNetworkAvailability`.
- `PlatformAndroid::DoStartNetworkAvailabilityMonitoring()` calls
  Java's `fromNativeStartNetworkAvailabilityMonitoring` to register
  the callback.
- Manifest already declares `ACCESS_NETWORK_STATE`.
- Requires API 24+ (`registerDefaultNetworkCallback`); minSdk is 24.

### Windows

- COM event sink (`NetworkEventSink_`) implementing
  `INetworkListManagerEvents` in
  `src/ballistica/core/platform/windows/platform_windows.cc`.
- Worker thread `RunWindowsNetworkMonitor_` does
  `CoInitializeEx(MTA)`, creates `NetworkListManager`, advises the
  sink to `IConnectionPoint` for `INetworkListManagerEvents`,
  queries initial state via `GetConnectivity`, then parks.
- Connection-point events arrive on COM RPC threads automatically
  (no message pump needed in MTA).
- Internet test:
  `(conn & (NLM_CONNECTIVITY_IPV4_INTERNET | NLM_CONNECTIVITY_IPV6_INTERNET)) != 0`.
  Local-only links count as unavailable.
- On COM init or NLM creation failure, falls back to reporting
  `true` (matches default behavior for unsupported platforms).
- Available since Vista (covers all supported Windows versions).

### Linux

No native implementation. Default
`Platform::DoStartNetworkAvailabilityMonitoring()` reports `true`
immediately, so request-gating is effectively a no-op on Linux.

Future work would wire NetworkManager via D-Bus
(`org.freedesktop.NetworkManager`'s `StateChanged` signal,
`NM_STATE_CONNECTED_GLOBAL` for "real internet"). Covers most
desktop distros (Ubuntu, Fedora, Mint, Steam Deck) but not
systemd-networkd-only systems. Punted because (a) the BombSquad
Linux client mostly runs on desktops with reliable network and
(b) the cost of a false positive (one round of "try and fail" vs
fail-fast) is small compared to the implementation work.

## Key design decisions

### 1. Path-only signal, not "validated internet"

Android's `NET_CAPABILITY_VALIDATED` and Windows'
`NLM_CONNECTIVITY_*_INTERNET` flags do real captive-portal probes
(Android hits a Google 204 endpoint). Tempting, but they have real
false negatives: blocked-in-China, corporate egress filters,
Pi-hole/custom DNS, validation-startup-lag.

If we suppressed requests on `validated=false`, a non-trivial slice
of users would see the app silently refuse to talk to our servers
even when it could. Path-only avoids that — it's the strict subset
that's universally true.

Validated is more useful as a **UX signal** ("limited connectivity"
badge) than a request gate. The abstraction can expose it later as
an optional second tier.

### 2. Callback-based, not polling

All target OS APIs are callback-native:

- Apple `NWPathMonitor` — `pathUpdateHandler` block on a dispatch
  queue.
- Android `ConnectivityManager.registerDefaultNetworkCallback` —
  `onAvailable`/`onLost`/`onCapabilitiesChanged` on a Handler.
- Windows `INetworkListManager` — COM connection-point events.
  Uglier plumbing, same shape.
- Linux NetworkManager — D-Bus `StateChanged` signal.

Callbacks are essentially free — the OS already tracks this for the
radio stack. Polling would wake the process unnecessarily.

### 3. Default to "unavailable" until OS reports otherwise

The cached value starts at `false`; consumers must wait for a real
callback (or the default impl's immediate `true`) before treating
the network as up. This avoids races where code at startup reads
the value before the platform's first OS report has arrived.
Platforms without a native implementation still get an immediate
`true` from the default `DoStartNetworkAvailabilityMonitoring()`,
so they aren't stuck offline forever.

### 4. Home in `core/platform`, not `base/app_platform`

`core/Platform` already has the closest sibling shape —
`RequestPermission`/`HavePermission`, `IsRunningOnTV`,
`GetOSVersionString` — pure OS-state queries with per-OS overrides.
Network reachability is the same shape.

`AppPlatform` is heavily app-feature stuff (login adapters,
purchases, web browser overlay) — wrong neighborhood. `core` is
also a strict dep of `base`, so anything in the engine can
subscribe.

### 5. Callback contract: any thread, no deregistration

Callbacks may fire on **any thread**, including synchronously inside
the registration call. Callers handle their own thread routing.

Reasoning: `core` is below `base` and doesn't know about the logic
thread, so binding to logic-thread delivery would be a layering
violation. Per-OS impls also benefit — Apple can hand the
`pathUpdateHandler` block straight to its dispatch queue with no
extra hop.

No deregistration: registrations live for the app's lifetime.

### 6. Base class owns dispatch + logging; subclasses are minimal

`AddNetworkAvailabilityCallback` is non-virtual. Subclasses can't
intercept it; they override `DoStartNetworkAvailabilityMonitoring()`
and call `SetNetworkAvailability(value)` on each OS-reported
change. Every per-OS impl gets the change-log line, dedup, and
dispatch machinery for free.

### 7. Each subsystem mirrors availability locally

ConnectivityManager and v2transport each subscribe to the platform
callback directly and maintain their own `network_available: bool`
field — they don't read `babase.app.net.available`.

Reasoning: avoids cross-subsystem callback-ordering races. If
ConnectivityManager registers later than NetworkSubsystem, reading
the latter's property could see a stale value momentarily after a
callback. With each subsystem owning a local mirror, ordering is
irrelevant — each one's local field reflects whatever C++ delivered
to *its* callback most recently. The bool write/read is GIL-atomic;
the kick scheduling uses `call_soon_threadsafe`. Both are safe from
any thread.

`babase.app.net.available` remains as the convenient public read
for casual consumers (UI badges, etc.) that just want "right now,
is it available?" and don't need to react to changes.

### 8. Push-based wake events, not poll-based reset

When availability flips `False → True`, both subsystems' subscribed
handlers fire `_kick_event.set()` / `_wake_event.set()` to interrupt
their respective sleeps. Event-driven recovery is much faster than
waiting for the next scheduled tick (~14s worst case for connectivity,
up to ~39s for v2transport's tier-4+ backoff).

Implementation pattern (used by both subsystems):

- The "what to do on wake" is in the existing tail of the sleep
  function; the wake just changes how we exit the sleep, not what
  happens after. So the spawn / fetch logic stays in one place.
- `await asyncio.wait_for(self._event.wait(), timeout=N)` — falls
  through naturally on either timeout or event firing. Cleaner than
  cancel-and-respawn.
- Event is cleared after the wake so subsequent sleeps start fresh.

### 9. Don't count gated failures toward backoff

v2transport's `_consecutive_errors += 1` is gated on
`self.network_available`. Without this, a 30-second offline window
where the gate fails ~5 sessions would push us into tier-2 backoff
(~5s base sleep). The wake event would still interrupt that sleep
on recovery, but we'd lose any genuine error-rate signal — every
offline window would look like 5 server failures.

ConnectivityManager doesn't have a comparable `_consecutive_errors`
counter (its retry rate is just the cycle period), so this only
applies to v2transport.

### 10. Saved bootstrap address never cleared

Once a bootstrap address resolves successfully in a process, it
stays put for the lifetime of the process. The cascade entries are
scheme variants of the same hostname; if the saved one fails, the
others almost certainly fail too. Process restart starts fresh.
Stale-after-build-update is handled by the `known_good in
bootaddrs` check.

### 11. Reset disabled (kept-in-place)

`_reset()`'s time-jump and fg-state-change triggers are gated by
`if bool(False):`. Only the initial-cycle reset fires. Reasoning
captured in a block-comment above `_reset()`: the scenarios reset
handles (mid-session continent move, mid-session VPN-exit toggle,
sleep/wake onto a very different network) produce
suboptimal-but-functional latency, not breakage; geo-ignore lock-in
is the one user-visible artifact and process restart fully recovers
it. The cost of keeping reset is real complexity (it has to be
correctly threaded through any future state we add). Implementation
left in place for cheap re-enable; will likely remove fully if
ongoing experience confirms the cost-benefit.

### 12. Shutdown gates dispatch, not the OS monitors themselves

`StopNetworkAvailabilityDispatch` flips a flag rather than tearing
down the OS monitors. Reasoning: tearing down the monitors would
require synchronization with their delivery threads (COM RPC,
NWPathMonitor dispatch queue, Android handler), which is much more
machinery than the simple flag. The detached threads die at process
exit anyway. The flag prevents callbacks from reaching consumers
(Python in particular) once the shutdown cascade starts dismantling
them.

## Anti-scope (resist drift)

- **Don't build a full network state machine** (interface type,
  expensive, constrained, etc.) until a consumer needs it. The gate
  is one bit: "definitely offline" vs. "maybe online."
- **Don't expose validated-internet as the primary signal** even if
  a platform provides it for free. Optional secondary tier only.
- **Don't add a polling fallback "just in case."** Every target
  platform has a callback API; use it. (Linux falls back to default
  `true` rather than polling.)
- **Don't add deregistration unless a consumer that genuinely needs
  it appears.** Keeps the API surface and per-OS-impl machinery
  smaller.
- **Don't read `babase.app.net.available` from internal subsystems
  with reactive needs.** Subscribe + maintain a local mirror.
- **Don't tear down OS monitors at shutdown.** Flag-based dispatch
  gating is sufficient and avoids cross-thread teardown
  synchronization.

## Testing

### test_game_run flags — `tools/batools/pcommands3.py`

- `--reset-connectivity` → sets `BA_CONNECTIVITY_RESET=1`
- `--debug-network-toggle` → sets `BA_NETWORK_AVAILABILITY_DEBUG_TOGGLE=1`

These exist as flags rather than env-var prefixes so the sandbox
permission grant for `test_game_run` persists across invocations.
The general "prefer pcommand flags over `BA_FOO=1` prefixes" pattern
is documented in `~/.claude/CLAUDE.md` and the `/baclient` skill.

### End-to-end test

`tests/test_plus/test_network_availability_gating.py` boots a fresh
headless client with `BA_NETWORK_AVAILABILITY_DEBUG_TOGGLE=1`, then
asserts on the captured log stream:

1. `Network availability changed: true` appears (debug toggle is
   working).
2. `Fetching ping-target-list` appears, after the flip and within
   2s (connectivity gating + kick worked).
3. `Trying WS connection` appears, after the flip and within 2s
   (v2transport gating + wake-event worked).
4. All pre-flip `No transport-sessions remain; will spawn new one
   in N.NNs` log entries have `N <= 3.5s` — i.e., backoff stayed
   in tier 0 across the gated period (gated failures aren't being
   counted toward `_consecutive_errors`).

Test runs in ~7.4s. Skipped under `BA_TEST_FAST_MODE=1` (so plain
`make test` skips it); runs under `make test-ex` and the live-test
paths.

## References

- Sibling abstractions: `RequestPermission`/`HavePermission`,
  `IsRunningOnTV` in `src/ballistica/core/platform/platform.h`.
- Cross-thread Python callback pattern:
  `Python::ScopedInterpreterLock` in
  `src/ballistica/shared/python/python.h`.
- Coordinated subsystem pattern: ConnectivityManager and v2transport
  in `src/codegen/bapluscodegen/pyembed/`.
- End-to-end test:
  `tests/test_plus/test_network_availability_gating.py`.
