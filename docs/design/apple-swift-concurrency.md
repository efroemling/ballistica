# Apple Swift concurrency

**Description:** Swift-6 strict-concurrency conventions for the Apple platform glue — @MainActor equals the engine main thread, C++-exported symbols can't be isolated, and the sanctioned escape-hatch patterns.

All Apple Swift targets build with `SWIFT_VERSION = 6.0` and
`SWIFT_STRICT_CONCURRENCY = complete` (migrated 2026-06; the full journal
lives in git — see `docs/initiatives/RETIRED.md`, swift6-migration). These
are the conventions that migration established; follow them when touching
the Swift glue in `src/ballistica/base/app_platform/apple/`.

## The core fact: `@MainActor` == Ballistica main thread

`AppAdapterApple::ManagesMainThreadEventLoop()` returns **false** — we run
under a standard Cocoa/UIKit environment and they call us. So the OS main
thread IS Ballistica's "main thread", and `g_core->InMainThread()` is true
exactly on the OS main thread. Swift's `@MainActor` isolation therefore
lines up *exactly* with the engine's main-thread concept and its
`assert(...InMainThread())` checks — it is the truthful, non-hack
annotation for main-thread-confined types.

## The interop constraint: C++-exported Swift can't be `@MainActor`

A Swift func/type called from C++ via the interop header
(`BallisticaKit-Swift.h`) CANNOT be `@MainActor` — the annotation drops the
symbol from the generated header, so C++ callers fail to link. Find the
exported types via `grep 'BallisticaKit::' src --include=*.cc` (e.g.
`FromCpp`, `CocoaFromCpp`, `UIKitFromCpp`, `GameCenterContext`,
`StoreKitContext`, `TextTextureData`). Those stay nonisolated and reach
main-actor APIs via the patterns below; NON-exported types (delegates,
views, singletons like `CocoaSupport`) take a truthful whole-type
`@MainActor`.

**Also crucial:** Swift/C++ interop is *unchecked* — calling a `@MainActor`
Swift function from C++ does NOT trigger actor-isolation enforcement, and
Swift→C++ calls carry no `Sendable` requirements. The compiler will not
catch a wrong-thread C++→Swift call; thread-correctness across the boundary
must be reasoned manually (from base-class thread docs in `app_adapter.h`,
asserts, and caller context).

## Escape-hatch patterns (use the matching one, never blanket)

- **`MainActor.assumeIsolated`** — ONLY for entry points the C++ side
  *guarantees* are on-main (an assert or base-class doc says so). It is a
  hard runtime precondition that crashes off-main; never blanket-apply it
  to entry points whose thread is uncertain.
- **`DispatchQueue.main.async`** — fire-and-forget UI work that might be
  called off-main (e.g. `terminateApp`, `showGameServiceUI`).
- **`onMain` helper** (`Thread.isMainThread ? assumeIsolated :
  DispatchQueue.main.sync`) — synchronous getters that must return a value
  to a logic-thread C++ caller but read `@MainActor` state (e.g. the
  `UIDevice` getters). Never a bare `assumeIsolated` here.
- **`nonisolated(unsafe)`** — genuinely single-thread-confined statics
  (logic-thread-only, single-init), `OpaquePointer` transfers, C resources
  (EGL/CADisplayLink) that the always-nonisolated `deinit` must release,
  and self-captures into off-main GameKit `@Sendable` completion closures.
- **`@unchecked Sendable`** — a C++-exported type that is genuinely
  multi-threaded (sync main-thread entry points + detached `Task`s, e.g.
  `StoreKitContext`). An `actor` would break the synchronous C++ entry
  points, and `@MainActor` is unavailable (exported).
- **`@preconcurrency` conformance** — SDK delegate protocols that aren't
  concurrency-annotated (e.g. `@MainActor class GameCenterDelegate:
  NSObject, @preconcurrency GKGameCenterControllerDelegate`). Note a
  `@MainActor` type's init can't run from a nonisolated init — create such
  delegates lazily inside a `@MainActor` method.

When a cross-thread flag blocks a whole-type `@MainActor`, prefer making
the concern *vanish* by going push-based (Swift pushes value changes into a
C++-side atomic, mirroring `from_swift.OnNetAvailChanged`) over annotating
or locking around it — that's the house style (fullscreen state is the
precedent).

## Don't block the main runloop — GCD main-queue starvation is an input killer

Much of this glue depends on `DispatchQueue.main.async` reaching the main
thread *promptly*: GameController-framework input (GCKeyboard/GCController
handlers fire on their default `handlerQueue` — the main queue) and every
engine main-thread runnable (`FromCpp.pushRawRunnableToMain`). CFRunLoop
only drains the GCD main queue on its idle/wake cycles — so main-thread
work that keeps the runloop perpetually busy (a display-link callback that
blocks in a vsync'd swap being the canonical case) starves the queue, and
queued blocks then only run when a real NSEvent cycles the AppKit loop.

This bit for real on the mac build (June–July 2026): the
CVDisplayLink→CADisplayLink modernization moved render+swap into the
display-link callback on the main runloop, and keyboard input went
ignored/stuck during mouse-less gameplay — each queued key event was
delivered only when a mouse-move NSEvent woke the loop. The fix
(`CocoaGLView.swift`, see its header comment): the CADisplayLink tick just
*signals*; a dedicated render thread does make-current → render → swap.

Rules of thumb:
- Display-link callbacks and anything else recurring on the main runloop
  must return quickly — never block on vsync, drawable availability, locks
  held across frames, or cross-thread waits.
- If a symptom looks like "input/events delayed until the user wiggles the
  mouse or touches the screen", suspect main-queue starvation before
  suspecting the input path itself.
- `UIKitGLViewController` uses the same pacer+render-thread split (ported
  2026-07-23), with one iOS-specific addition: `setRenderingPaused(true)`
  is a *fence* — it drops any queued tick and waits out the in-flight
  frame, since GPU work after backgrounding gets the app killed. Keep that
  property intact when touching the render loop.

## Don't aesthetically restructure sim-unverifiable flows

The `GameCenterContext` façade split (thin nonisolated C++ façade + a fully
`@MainActor` impl) was considered and DECLINED: the `nonisolated(unsafe)`
vouches it would remove are correct-not-bugs, and GameKit sign-in/auth
paths can't be simulator-verified — a pure restructure of a live auth flow
that is only compile-checkable is the worst place for cosmetic refactoring.
The kept escape hatches are runtime-trapped (`assumeIsolated`) or inherent
(nonisolated `deinit`, C pointers, off-main ObjC callbacks).

## Build gotchas

- Build the two Mac targets (TestBuild / AppStore) **one at a time** —
  parallel xcodebuilds trip the build lock / signing and fail with a
  misleading code 65 that looks like a compile error.
- `XCODEBUILDVERBOSE=1` (sandboxed is fine) surfaces the real Swift
  diagnostics the pcommand wrapper otherwise filters out.
- Per-target file subsets (`#if BA_PLATFORM_*`) mean the strict-concurrency
  diagnostic set differs per platform — verify changes on Mac + iOS + tvOS,
  and on Release, not just Debug (see
  `docs/design/ios-tvos-app-platform.md`).
