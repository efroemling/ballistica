# Client Error Reporting

**Description:** How game clients tell us something went wrong — the live fatal-error reporter, next-launch native crash reports, and triggered-window log reports — which one catches what, and how to read each.

A client has three separate ways to report a problem. They are separate
on purpose: each runs in a different state of the process, and what is
safe to do depends entirely on that state.

| Situation | Channel | Sent | What arrives |
|-----------|---------|------|--------------|
| The engine detects something unrecoverable and can still run code (`FatalError`, a failed startup, an escaped exception at top level) | [Fatal errors](#fatal-errors) | Immediately, by the dying process | Message, native stack trace, build identity, modded signals |
| A hard fault — access violation etc. — where no code can safely run | [Native crashes](#native-crashes) | On the **next** launch | Fault code, module+offset, renderer, uptime, app-state, build identity |
| The process is healthy, but something logged a warning or a watched phrase | [Log reports](#log-reports) | During the run | A window of engine log entries around the trigger |

When something *didn't* show up, check the table first — the usual
answer is that it happened in a state no channel covers (see
[Coverage gaps](#coverage-gaps)).

All three land in Cloud Logging; `cloud_log_query` is the reader for
each. Everything a client sends is **untrusted**: the fatal and crash
channels are unauthenticated by design, and the server treats their
contents as hints about what broke, never as facts about who sent it.

## Fatal errors

`src/ballistica/shared/foundation/fatal_error_report.cc`. When the
engine hits a fatal error it POSTs a small JSON report to
`http://regional.ballistica.net/fatalerror`, holding the dying process
open briefly for the send, then aborts (builds that aren't unmodified
blessed builds — developer and modded ones — `exit(1)` instead, to stay
out of OS crash reporting). A report it can't deliver
is saved and sent on the next launch — see
[Deferred delivery](#deferred-delivery).

It sends only what is immediately to hand — the message, a native stack
trace when one is obtainable, compile-time build identity, the OS
version, and four cheap modded-build signals (commands run,
workspaces in use, custom app-scripts dir, Python present in the mods
dir).

The OS version is read from `g_crash_info`, where it was recorded once
core came up, rather than asked of the platform at fatal time. That
keeps platform code out of a dying process. It is optional end to end:
a fatal error before core is up hasn't recorded it yet, some platforms
can't tell (they report `"unknown"`, stored as empty), and older
clients never send it. Absent means the field is simply left out of the
report and the log line. It deliberately does **not** send logs: at fatal time
we cannot know it is safe to touch that state. Logs are the
[log reports](#log-reports) channel's job.

Decisions, and why:

- **Plaintext http, always to prod.** This runs at the lowest level we
  have, where there is no TLS stack — TLS in the engine lives entirely
  in Python — and native TLS would mean OpenSSL in five platform build
  systems to serve one POST. Non-prod fleets are https-only, so a
  fleet-following reporter would silently go nowhere on dev/test
  builds. The cost accepted is that reports are unauthenticated and
  forgeable, which is fine for "something died, here is roughly what".
  Reports carry build/variant/dev-build fields, so non-prod traffic is
  filterable on the receiving end.
- **Lives in `shared/`, not `plus/`.** Its predecessor was a
  `PlusFeatureSet` method that bailed out entirely when plus was
  absent — so the engine-couldn't-start failures most worth reporting
  were the most likely to be dropped.
- **Logging is the only side effect on receipt.** No datastore write:
  reports are forgeable, so persisting them would let anyone grow the
  storage bill. Cloud Logging already provides retention and search.
- **cpp-httplib, confined to this one translation unit.** It returns
  errors as values rather than throwing, which matters in a fatal
  handler, and it is built with `CPPHTTPLIB_NO_EXCEPTIONS`. The header
  is large (~22k lines, +1.5s compile, +187 KB linked), so no second
  translation unit includes it; a second consumer should get a small
  facade instead.
- **Modded signals replaced the old blessing hash.** That hash needed
  the plus feature-set (often gone at fatal time) and a server-side
  build lookup that only ever existed on the v1 master server. When
  `g_core` itself is gone the report says `coregone=True` rather than
  claiming a clean build.

### Deferred delivery

A live report is sent once, from the dying process. If it hasn't been
confirmed by the end of the handler's wait (failed, or still in
flight), the handler writes the same report — message prefixed
`DEFERRED:` — to `<config dir>/pending_reports/fatal_report_<unix>.json`,
and the next launch sends it as soon as the config dir is known
(`CoreFeatureSet::ApplyBaEnvConfig`). This matters most where a failed
send would otherwise leave *nothing*: non-blessed builds `exit(1)` on a
fatal error instead of aborting, so there is no OS crash report either,
and a fatal error just after resuming from the background (network not
back yet) looked exactly like the app silently vanishing.

- **Config dir, not cache dir**: caches can be purged by the OS, and
  are deliberately chaos-deleted in developer builds.
- **Same lifecycle as crash records**: newest wins, every pending report
  is deleted before sending, and a failed send is not retried.
- **Its location is recorded once into static storage**, so the dying
  process never calls into core or platform code to find it. A fatal
  error before the config dir is known can't be deferred.
- **Visible locally too**: the next launch logs `Previous run ended in a
  fatal error that couldn't be reported at the time; …` with the
  message — at WARNING in developer builds (where it may be the only
  trace), INFO otherwise.
- **No server change**: like `CRASH:`, the marker is a message prefix;
  the payload's `t` still carries when the error actually happened.
- A send that completes after the handler gave up on it produces one
  duplicate report; accepted.

### Reading them

```bash
tools/pcommand cloud_log_query --message 'client fatal' --freshness 1d
# Only the ones delivered a launch late:
tools/pcommand cloud_log_query --message 'DEFERRED' --freshness 1d
```

Lines look like `client fatal: <message> | build=… version=…
platform=…/… os=… variant=… devbuild=… modded=… coregone=… addr=…`,
with the stack trace on following lines. `os=` is omitted when unknown.

**Ignore `modded=True` on Android reports from builds through 23039.**
Every Android build read as modded there: the custom-scripts check
compared the app-python dir against baenv's default path, while Android
serves scripts from the apk. Fixed 2026-10-07 (`core.cc`, where
`using_custom_app_python_dir_` is computed). The same bug made those
builds `exit(1)` on a fatal instead of aborting and tagged their log
reports `baModified=1`.

**A fatal's message is all that reaches us; put the cause in it.** A
logged Python exception stays on the device. When a fatal wraps a
failed Python call, have the call return its cause and append it to the
message, as `Assets::StartLoading` does for the bundled asset-package
load (`Cause: <Type>: <message> (file:line func < ...)`).

**Don't filter with `--service global`.** The master server emits these
from whichever Cloud Run service processes the event (`bg` in
practice); `resource.type=global` is for logs relayed from elsewhere,
so that filter excludes exactly these entries. Omit `--service`.

**`devbuild` doesn't separate us from users.** The public repo strips
the developer-build flag, so public-CI builds report `devbuild=False`
exactly like a player's.

### Testing

`BA_CRASH_TEST=1` fires a fatal before core is imported — the harshest
case (no `g_core`, no Python, no stack trace). `BA_CRASH_TEST_TOKEN`
tags it with a token so a test can find its own report.
`test_game_run --crash-test` / `--crash-test-token` drive these, and
`--fatal-report-url` (developer builds only, via `BA_FATAL_REPORT_URL`)
aims the report at a specific server node or a local listener instead
of prod. A shipped build can never be redirected by its environment.

`tests/test_base/test_fatal_error_report.py` exercises the whole chain
and polls Cloud Logging for its token. It runs **against prod** — that
is the only fleet with both a plaintext route and Cloud Logging — so
each run leaves one self-identifying entry there.

## Native crashes

A hard fault can't report itself the way a fatal error does. The
faulting process is dying and its state is untrusted: the crash handler
may not allocate, format, take locks, or dereference engine objects,
and `g_core` itself may be gone or corrupt. So the work is split across
two processes:

1. **As the app runs**, everything a report will want is mirrored into
   `g_crash_info`, a flat POD struct
   (`src/ballistica/shared/foundation/crash_info.h`). Nothing needs
   serializing, so nothing can be caught half-written — each field is
   an independent scalar store.
2. **In the crash handler**, the only work is filling in the fault
   fields and writing bytes out: a minidump with the struct embedded as
   a user stream (type `0x1000ba11`), plus the same struct raw in a
   sidecar `crash_<timestamp>.crashinfo` beside the dump.
3. **On the next launch**, once core is up, `SubmitPendingCrashReport()`
   takes the newest record, converts it to the fatal-error JSON shape —
   allocation is fine now — and sends it through the fatal-error
   transport on a detached thread, so an unreachable server never
   delays a launch.

It reuses the fatal-error channel end to end rather than adding one:
same endpoint, same server path, same Cloud Logging logger. A crash
report is a fatal-error report carrying an extra `crash` block.

### What gets recorded

| Field | Set | Notes |
|-------|-----|-------|
| Build number, version, platform, arch, variant, debug/dev flags | `CrashInfoInit()`, early in `ballistica.cc` | Compile-time identity of the *crashed* build — which may not be the build that reports it, if the user updated in between |
| OS version | `CrashInfoSetOSVersion()`, right after core imports | Empty until then, or when the platform can't tell; omitted from the report when empty. Driver-level crashes often depend on the OS build as much as on the driver. On Windows it is the true version (`10.0.<build>.<revision>`; a build of 22000+ is Windows 11) |
| Renderer identity | `CrashInfoSetRenderer()`, at GL context setup | The GL renderer and version strings, e.g. ANGLE version, backend, GPU, driver. The field most likely to reveal a GPU-driver crash, and one a field report has no other way to get |
| App-state bits (1 = app-active, 2 = app-suspended), update count | `CrashInfoUpdateRuntime()`, each logic-thread display-time update | Per drawn frame with a GUI, ~10 Hz headless. Answers "was it even in the foreground?" and, with uptime, separates a startup crash from one twenty minutes in |
| Modded signals, `core_alive` | Same | Mirrored as the app runs. `core_alive` answers the fatal channel's `coregone` question as of the fault, not as of sending |
| Fault code, fault address, faulting module + base, access type/address, crash time | The crash handler | Module + offset is the useful half: it survives ASLR and is what archived symbols resolve against |

**Coupling:** `GetOSVersionString()` is also hashed into
`AppPlatform::GetPublicDeviceUUID()`, so any change to that string's
*format* on a platform re-rolls every user's public device UUID there.
(The 2026-09-25 Windows switch to `RtlGetVersion` did exactly this
once.)

### What leaves the machine

Only the record, converted to JSON: about 600 bytes, and bounded at
under 1 KB since every string is a fixed-size field. **The dump is
never uploaded.** It stays beside the executable for the cases where we
can reach the machine.

This is a deliberate trade. Module + offset locates the faulting
instruction without the dump, and that is enough to spot and track a
crash across the field. What it can't give is *why*: the dump has the
full call stack of every thread, register state, and memory around the
fault. Moving 1–2 MB per crash from every affected install would need
an authenticated, size-limited endpoint and a storage story, which one
address per crash doesn't justify.

### Record lifecycle

- **Newest wins.** If several records are pending, the newest is sent
  and older ones are deleted — a crash-looping install reports its most
  recent crash, and records can't pile up.
- **Deleted before sending, whatever happens next.** A record that
  can't be read now never will be, and a crash-looping app would
  otherwise report the same failure on every launch. A failed send is
  lost rather than retried.
- **Format-versioned.** `kCrashInfoFormatVersion` is the struct's first
  field. **Bump it whenever the layout changes.** A reader discards any
  record whose version it doesn't know, so the only cost of a change is
  one lost report per install across the upgrade — whereas reading an
  old layout with a new struct would report garbage. The version
  history lives beside the constant in `crash_info.h`.

### Platform coverage

**Windows only today**, and only for the `generic` and `test_build`
variants — the unhandled-exception filter is installed conditionally in
`PlatformWindows`' constructor. Other platforms return no pending
record, so on them the submit step is a no-op. Adding a platform means
a crash handler that fills the fault fields and writes the record, plus
a `GetPendingCrashRecordPath()` override; the struct, the next-launch
submit, and everything server-side are already platform-neutral.

### Reading them

```bash
tools/pcommand cloud_log_query --message 'CRASH' --freshness 1d
```

They are `client fatal` lines whose message starts `CRASH:`, with the
crash block appended to the first line:

```
client fatal: CRASH: 0xC0000005 in libGLESv2.dll+0x212863 | build=… …
  | fault=0xC0000005 at=libGLESv2.dll+0x212863 acc=0@0x0 appstate=1
    frame=2464 uptime=81s renderer=ANGLE (NVIDIA, …, D3D11-…) | OpenGL ES …
```

`acc=0@0x0` — a read of address zero — is the classic null
dereference. When the fault is outside every module we can name, `at=`
falls back to the absolute address, since an offset would mean nothing.

The renderer string is message text, not a label: it is near-unique
per GPU + driver combination, so it is something you search, not
something you slice by.

### From an address to code

Crash reports carry an address; resolving it is a manual, local step —
nothing does it server-side. [prefab-symbols](prefab-symbols.md)
covers where the symbols live and how to fetch them: our own binaries
are keyed by executable hash, and third-party modules such as ANGLE by
their CodeView key.

- **From a report alone** you get one address, which resolves to the
  function it landed in (and a source line if that PDB has line
  tables). For ANGLE, the renderer string names the ANGLE revision
  whose source the line refers to.
- **From a dump**, `tools/pcommand dump_symbols_fetch <dmp>` stages
  symbols for every module the dump names, in a layout a debugger
  symbol path can point straight at. That turns one address into a full
  call stack.

### Testing

A crash needs two launches, so the record has to survive between them.
On the remote Windows hosts, cloudshell's workspace sync excludes
`crash_*` from its `--delete`, so a record written by one
`test_game_run --platform windows` run is still there for the next.
Any reproducible native crash drives the whole chain; confirm with the
`Submitting crash report from previous run (…)` lifecycle INFO line on
the second launch, the record's disappearance, and the Cloud Logging
line.

## Log reports

For problems that don't kill the process. Clients ship a bounded window
of their engine log to the master server when a trigger fires; reports
land in Cloud Logging tagged `baSrc=client`. Shipped prod 2026-08-11
(build 22971 / 1.8.0a79).

Everything about *which* clients report and *what* they send is
server-controlled through CloudVals, so reporting can be switched on,
narrowed, or made more verbose without a client release. Finer
targeting — more conditions and controls over which clients are asked
to log what — is planned; document it here as it lands.

### Spec + config

- `CloudValsTransient.log_report` carries a
  `bacommon.logreporting.LogReportSpec`: `trigger_level` (`tl`, LogLevel
  int value; WARNING=2) OR `trigger_phrases` (`tp`, substrings —
  deliberately no regex), `max_before_entries` (`mb`),
  `max_after_entries` (`ma`, None = rest of run). One window per run; no
  re-arming.
- CloudVals split: `CloudValsPersistent` (config-cached; applies
  pre-connectivity next run; build-blind-safe values only) vs transient
  (per-run; server can tailor per build).

### Cloud logger control (per-logger levels)

- `CloudValsPersistent.logger_control` carries a
  `bacommon.loggercontrol.LoggerControlConfig` — a diff over the
  client's base logger config, same shape as the user's own
  `'Log Levels'` app-config value. Persistent (not transient) so it
  applies from the very start of the next run: `baenv._set_log_levels`
  reads the stored `CloudVals` blob pre-engine; fresh vals arriving
  mid-run also re-apply immediately.
- The user chooses via the `'Cloud Logger Control'` app-config bool
  (default True; toggle in the dev-console Logging tab). ON: cloud
  config (or base defaults) drives levels and the manual per-logger UI
  is replaced by an explainer. OFF: their own `'Log Levels'` diff, as
  before. `BA_LOG_LEVELS` env var still overrides everything.
- Client-side logic: `babase._cloudloggercontrol` (+ the baenv
  launch path). `cloud_controlled_logging()` is True only when the
  toggle has been ON continuously since launch with no env override —
  toggling OFF even momentarily latches it False for the run.
- That bool rides on every `ClientLogReportMessage` (`cc`) and lands
  as `levels=cloud|user` in the report summary line plus a
  `baCloudControlledLogging` label on every emitted line, so report
  queries can filter for clients showing exactly the levels the
  server configured.

### Integrity signals (blessed / modified)

Successors to the v1 system where clients sent their master-hash
(camouflaged as `newsShow`) + `userRanCommands`/`userModded` and the
legacy server derived `blessed` from a per-build Blessing record.
Now split into two orthogonal client-computed values on every
`ClientLogReportMessage`, sampled at each slice send:

- `blessed` (`bl`, tri-state): pure build integrity — non-debug build
  with an embedded blessing hash whose computed script hash checks
  out (`_baplus.get_blessing_state()`). `None` = the background hash
  calc (game_hash.py, kicked at pyembed init) hadn't finished, or a
  pre-field client. Debug builds are always unblessed.
- `modified` (`md`): user-side taint — commands run, workspaces in
  use, custom app-scripts dir, or Python present in the mods dir
  (`_babase.is_user_modified()`; the same four the
  [fatal-error reporter](#fatal-errors) sends, there as `rancmds`,
  `workspaces`, `custompy`, `userpy`). Inherently latching within a
  run, so False = clean-so-far. Note automation-channel execs latch it
  (by design — they run arbitrary code).

  The mods-dir signal (builds after 23040) is what catches plugins,
  which need no commands run to take effect. It is presence-based,
  like the blessing hash: the startup meta-scan reports whether the
  mods dir holds anything the import system could load, loaded or
  not, and the flag is set when that scan completes — so a report
  from the first moments of boot can still read clean. It and
  `blessed` overlap without matching: the hash sees any `.py`
  anywhere under mods, the scan sees importable modules of any form
  (`.pyc`, zips and extensions included).

Server side: `build=blessed|unblessed|unknown, modded=yes|no|unknown`
in summary lines; `baBlessed`/`baModified` labels on every emitted
line (omitted when unknown). Gold-standard field-data filter:
`baBlessed=1, baModified=0, baCloudControlledLogging=1`.

### Mechanics

- Pre-roll ships immediately on trigger (no arm delay); follow-up slices
  on a 5s poll; cursor advances only on confirmed sends
  (`send_message_future`); bounded 1.5s final flush at shutdown.
- Evicted window entries ship as `entries_lost` → an explicit
  placeholder line at the gap (same pattern in basn `_ship_logs` /
  `LogsAndEventsMessage.entries_lost`).
- Dev builds tag the build token `-dev` (build 22978+; AppInstanceInfo's
  dev-build flag → AppFastClientData) so local testing is filterable
  from field data.
- Pure logic + tests: `bacommon/logreporting.py` /
  `tests/test_bacommon/`.

### Reading reports

- `tools/pcommand cloud_log_query --src client` on prod, or the
  dev-log search on dev. Summary line:
  `client log report from b<build> <tag>: N entries at index I`.
- Query mechanics — including the `--message` tokenization trap that
  silently breaks per-build attribution and the strict post-filter
  recipe for it — live in the `cloud-logs` Claude skill.

### Driving an investigation

Set a phrase trigger + windows on the fleet, have the target clients
run; pair with raising logger verbosity via the fleet's cloud logger
control config (above) — and filter the resulting reports on
`levels=cloud` so user-tweaked clients don't muddy the picture.

## Crashlytics (Google Play Android)

The Google Play Android build also links Firebase Crashlytics. It is a
third-party safety net beside the three channels above, not one of
them: it reports to Firebase rather than to our servers, and exists
only in that one build (`PlatformAndroidGoogle`). What it adds there
is exactly what our own channels lack on Android — hard native
crashes, uncaught Java exceptions, and ANRs, each with a symbolicated
stack, device model and OS version.

What we feed it:

- **Breadcrumbs.** `Platform::LowLevelDebugLog()` forwards to
  Crashlytics' log on this build (and is a no-op everywhere else).
  App suspend/resume/active transitions and audio device pause/resume
  go through it, so a report shows the lifecycle steps leading up to
  the crash.
- **The fatal-error message.** Our own fatal errors end in `abort()`,
  so each one also arrives in Crashlytics as a SIGABRT whose stack ends
  in `HandleFatalError`. Every fatal error therefore lands in the same
  one or two Crashlytics issues regardless of cause; tell them apart by
  the caller frame and by the `FATAL ERROR: ...` breadcrumb, which
  `ReportFatalError` logs in builds after 23040. The same error is also
  reported through the [fatal errors](#fatal-errors) channel — expect
  both, and prefer ours for the message and build identity.
- **Custom keys** via `Platform::SetDebugKey()`.

Two reading traps: the "device" on a report is whatever the device
claims to be (bursts of one model within minutes of an upload are
automated store testing, not players), and 32-bit ARM stacks often
arrive entirely unsymbolicated.

## Coverage gaps

Known states no channel covers:

- **Native crashes off Windows**, and on Windows outside the `generic`
  and `test_build` variants — see [Platform coverage](#platform-coverage).
  The Google Play Android build is the exception, through
  [Crashlytics](#crashlytics-google-play-android).
- **A crash with no next launch.** If the user never relaunches, the
  record is never sent.
- **Android, when the native library never loads** (a wrong-architecture
  install, a device without GLES3). Java-layer logs then go no further
  than logcat. Accepted: not worth a separate pathway for it. Failures
  after the library loads are covered by the fatal-error reporter.
- **Any report sent before the network is reachable — partly closed.**
  An undelivered *fatal* report is now deferred to the next launch
  (see [Deferred delivery](#deferred-delivery)); a deferred report or a
  native crash record whose next-launch send fails is still lost, and
  a fatal error before the config dir is known can't be deferred.
- **A process killed by a signal no engine code sees** (Apple). No
  `.ips`, no live or `DEFERRED:` fatal report. See "When nothing
  reports" below.

### When nothing reports: read the device system log (Apple)

An app that "opens for a split second then vanishes" with no crash
report and no fatal report died of something the engine never saw; the
device's system log names it.

1. Collect (needs root; use the full path, since zsh's builtin `log`
   shadows it): `sudo /usr/bin/log collect --device-udid <UDID> --last
   1h --output <path>.logarchive` (UDIDs: `xcrun devicectl list
   devices`).
2. Read: `/usr/bin/log show --archive <path> --predicate 'eventMessage
   CONTAINS[c] "ballisticakit"' --style compact`, then look for launchd
   `exited due to <SIGNAL>` / SpringBoard `Process exited`.

The archive keeps only persisted levels (engine WARNING+ yes,
INFO/DEBUG no) and rotates within hours on a busy phone, so collect
right away. `.ips` files come separately via `xcrun devicectl device
copy from --domain-type systemCrashLogs`. Precedent: SIGPIPE,
2026-09-28 (bundled Python is init'd isolated, so nothing ignored
SIGPIPE; fixed by `signal(SIGPIPE, SIG_IGN)` in `MonolithicMain`).
