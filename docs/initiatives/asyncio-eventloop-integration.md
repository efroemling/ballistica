# Initiative: asyncio ⇄ EventLoop integration (logic thread)

**Status:** Phase 1 done + validated; Phase 2 investigated & not pursued
(already subsumed by Phase 1); Phase 3 = the shipped state. Effectively
complete.
**Started:** 2026-05-30
**Owner:** Eric

## Progress log

- **2026-05-30 — Phase 1 landed (pure Python, no C++).** New
  `babase/_baeventloop.py` (`BAEventLoop`, a `BaseEventLoop` subclass) +
  `babase/_asyncio.py` rewired to instantiate it, mark it the running loop
  (`loop._thread_id` + `events._set_running_loop`), and drop the 10/s
  heartbeat entirely. mypy + pylint green. Validated on a `--fleet dev`
  headless boot: clean boot to RUNNING in ~0.95s, no traceback, clean
  shutdown. Runtime coroutine probe measured **avg `run_in_executor` hop =
  0.32ms** (was up to 100ms / ~50ms avg under the pump — ~150× faster),
  `asyncio.sleep(0.25)` accurate to ~1ms, `get_running_loop()` returns the
  `BAEventLoop`. Idle is now fully CV-blocked (no heartbeat). The original
  motivator — warm construct-mode resolve ~430ms, dominated by ~7
  pump-bounded hops — now pays ~0.3ms/hop.

- **2026-05-30 — cleanup + a cache-masked latent bug.** Refreshed the public
  `App.asyncio_loop` docstring (it still described the old pumped/encapsulated
  loop and `get_running_loop()` "not returning this loop from most places");
  removed the dead `App._asyncio_timer` field; reworded the
  `_assetsubsystem.py` warm-resolve comment that justified itself with "the
  loop is only pumped periodically". A `preflight-full` (mypy cache cleared)
  then surfaced a latent bug: `BAEventLoop`'s overrides were missing the
  project-required `@override`, and `_thread_id` isn't in typeshed — both had
  been masked by an incomplete incremental-cache resolution of
  `BaseEventLoop`. Fixed: `@override` on the nine mypy-visible overrides
  (`_timer_handle_cancelled` omits it — typeshed doesn't stub that private
  base method), declared `_thread_id: int | None`. Lesson: the fast loop
  (mypy+pylint) skips cpplint and can mask `explicit-override` on freshly
  added stdlib subclasses; periodic `preflight-full` is the net.

- **2026-05-31 — boot-timing re-measurement (warm + cold, `--fleet dev`).**
  Confirmed the integration's payoff and that construct-mode adds no
  meaningful warm-boot cost. Warm: RUNNING 0.525s → resolve **3–12ms
  (offline)** → handoff 0.538s → **entering server-mode 0.814s**. Cold (fresh
  silo): RUNNING 0.943s → resolve **607–762ms (downloads 6 buckets)** →
  handoff 1.551s → server-mode 1.867s. Takeaways: (1) warm resolve is ~10ms
  vs the ~430ms it would cost under the old pump — the headline win;
  (2) construct-mode adds only the offline resolve + one extra app-mode
  transition (~10ms GC) on warm — **not** substantially slower than the old
  pre-construct path; (3) cold's added cost is the one-time `bastdassets`
  download, which is already well-parallelized (all blobs via one
  `asyncio.gather`, `_assetsubsystem.py:795`) and node/network-bound — the
  real cold lever is the deferred prod rollout (bundle/serve from prod/CDN),
  not code; (4) the handoff→server-mode gap (~280–315ms, both warm and cold)
  is classic's normal server-mode startup, pre-existing and unrelated.

- **2026-05-31 — boot GC-warning investigated, NOT a code issue.** The
  boot-time "too many objects garbage-collected" (~76 objects incl.
  websockets/`ConnectionRefusedError`/`FrameSummary`) is **not** an unstripped
  caught exception. Root cause: v2transport's `websockets.connect` routes
  through the sandbox proxy (`HTTPS_PROXY=localhost:54541`); asyncio tries
  `::1` first (refused → `ConnectionRefusedError`) then `127.0.0.1` (succeeds),
  so the connection **succeeds** and the exception is never caught by us — it
  lives in asyncio's `create_connection` internals for the losing sub-attempt,
  amplified by asyncio **debug mode** (`PYTHONDEVMODE`) capturing
  `_source_traceback` (the `FrameSummary` objects). Both the localhost proxy
  and asyncio debug are dev/sandbox-only, so production release builds don't
  trip it; there's no `except` block for a `strip_exception_tracebacks` to
  attach to. Decision: leave it (the existing strip at `v2transport.py:2008`
  remains correct for genuine connect *failures*).

## Goal

Make the logic thread's C++ `EventLoop` *also* serve as the thread's
asyncio event loop, so that work posted from other threads —
`run_in_executor` completions in particular — wakes the logic thread
**immediately** (CV notify) instead of waiting for the next pump of the
heartbeat-driven asyncio loop.

Today (`babase/_asyncio.py`) we run a stock `SelectorEventLoop` and pump
it via a 10/s `AppTimer` (`run_cycle` = `call_soon(stop)` + `run_forever`).
That heartbeat interval is the per-hop latency floor for async ops on the
logic thread (a warm construct-mode resolve sits at ~430ms, dominated by
pump latency, not work). This initiative removes that floor.

## The key insight — asyncio's primitives already map 1:1 onto EventLoop

The whole integration is essentially an *adapter*. asyncio drives
everything through three scheduling primitives plus a clock, and each
already has an exact counterpart that the `Run_` loop drains every cycle:

| asyncio loop method     | EventLoop / babase primitive                       |
|-------------------------|----------------------------------------------------|
| `call_soon(cb)`         | `PushRunnable` / `_babase.pushcall(cb, raw=True)`  |
| `call_soon_threadsafe`  | same `PushCall` — already locks + notifies the CV  |
| `call_later/at`         | `NewTimer(..., repeat=false)` / `babase.AppTimer`  |
| `time()`                | `g_core->AppTimeMicrosecs()` / `_babase.apptime()` |
| `run_in_executor`       | the existing `app.threadpool` (already the default)|

And crucially we **do not reimplement `Task`/`Future`/coroutine driving** —
those are pure-Python in CPython and only ever call back into
`loop.call_soon` / `call_later` / `create_future`. We reuse them wholesale
(this is exactly how uvloop layers a custom loop under stock asyncio).

`Run_` (src/ballistica/shared/foundation/event_loop.cc:253):

```
while (true):
  CheckInterrupts_()                       // logic thread only
  WaitForNextEvent_()                      // CV wait; releases GIL
  <process thread_messages: kRunnable -> runnables_, shutdown/suspend/...>
  if (!suspended):
    timers_.Run(now)                       // <- asyncio call_later fires here
    RunPendingRunnables_()                 // <- asyncio call_soon fires here
```

So asyncio Handles run inside the exact phases that already exist. No
separate ready-queue, no `_run_once` reimplementation, no selector.

## GIL analysis (the question that motivated this)

The current loop has `acquires_python_gil_=true`: it **holds the GIL
continuously across its whole work phase** and releases it only inside
`WaitForNextEvent_` (`ReleaseGIL_()` → CV wait → `AcquireGIL_()`). So:

- It's **one release/acquire per loop iteration**; iteration count = wakeup
  count (timer fires + PushCalls). Even the pure-C++ game sim runs under
  the held GIL today — which is exactly why worker threads only make
  progress during the frame waits, and why the earlier prompt-wake
  experiment couldn't get the executor serviced between pumps.

Therefore **folding asyncio into this loop does not increase GIL
acquisition frequency at all** — the Handles run inside the work phase that
already holds the GIL, so the cadence stays "once per wakeup." The only
proviso: keep the loop *machinery* (queues, timer heap, the wait) in C++ so
we don't add Python work per cycle. That's why we extend our loop rather
than re-home onto a vanilla `SelectorEventLoop` (whose `_run_once` would put
Python bookkeeping in the frame hot path and hold the GIL longer per
iteration — directionally the concern that prompted this, though it's
hold-*duration* not acquisition-*frequency*).

## Phasing

### Phase 1 — pure-Python prototype (NO C++)

Prove the prompt-wake with zero engine changes by subclassing
`asyncio.base_events.BaseEventLoop` and routing the scheduling primitives
through existing natives. We inherit the valuable helpers
(`create_task`, `create_future`, `run_in_executor`, `set_default_executor`,
exception handling, `get_debug`) and override only scheduling + lifecycle.
We never call `run_forever`/`_run_once`, so `BaseEventLoop`'s selector path
(`_ready`, `_scheduled`, `_selector`) is never touched.

Skeleton (`babase/_baeventloop.py`, new):

```python
import asyncio, threading, _babase, babase

class BAEventLoop(asyncio.base_events.BaseEventLoop):
    """asyncio loop backed by the logic thread's C++ EventLoop."""

    def time(self) -> float:
        return _babase.apptime()

    def is_running(self) -> bool:
        return True            # the C++ Run_ loop is always running

    def is_closed(self) -> bool:
        return False

    def call_soon(self, callback, *args, context=None):
        handle = asyncio.Handle(callback, args, self, context)
        # raw=True: no thread-check, no context save (Handle._run owns the
        # contextvars.Context); PushCall is thread-safe + notifies the CV.
        _babase.pushcall(handle._run, raw=True)
        return handle

    # call_soon_threadsafe: identical body — pushcall(raw=True) already
    # works cross-thread and wakes the CV. This is the whole fix.
    call_soon_threadsafe = call_soon

    def call_at(self, when, callback, *args, context=None):
        handle = asyncio.TimerHandle(when, callback, args, self, context)
        delay = max(0.0, when - self.time())
        # Keep the AppTimer alive on the handle; drop it on cancel (Phase-1
        # acceptable fallback: let it fire and no-op via Handle._run).
        handle._ba_timer = babase.AppTimer(delay, handle._run, repeat=False)
        return handle

    def call_later(self, delay, callback, *args, context=None):
        return self.call_at(self.time() + delay, callback, *args,
                            context=context)

    # Driven by the engine; explicit run is unsupported here.
    def run_forever(self): raise RuntimeError('loop is engine-driven')
    def run_until_complete(self, f): raise RuntimeError('engine-driven')
    def close(self): pass
```

Wire-up in `setup_asyncio()` (replace `asyncio.new_event_loop()`):

```python
loop = BAEventLoop()
loop.set_default_executor(babase.app.threadpool)
loop.set_exception_handler(_exception_handler)
loop._thread_id = threading.get_ident()       # so is_running()/checks pass
asyncio.events._set_running_loop(loop)         # so get_running_loop() works
asyncio.set_event_loop(loop)                   # so get_event_loop() works
# DELETE the run_cycle()/AppTimer heartbeat entirely.
return loop
```

Expected result: `run_in_executor` completion on a worker →
`call_soon_threadsafe(set_result)` → `pushcall(raw)` → `PushCall` notifies
the CV → `WaitForNextEvent_` wakes → set_result → wakeup → coro steps. Sub-ms
instead of up-to-100ms. The construct-mode warm resolve should drop back to
roughly its work cost (~75ms range we saw with the 1/120 pump) without any
pump at all.

**Phase-1 caveats — re-examined 2026-05-30 (both already handled):**
- ~~Same-thread `call_soon` pays the cross-thread thread-message lock.~~
  **Wrong.** `pushcall(raw)` → `PushCall` → `PushRunnable`, and
  `PushRunnable` (event_loop.cc:685) routes by thread: on the logic thread
  it does a **lock-free** `PushLocalRunnable_` (no mutex, no notify), serviced
  next cycle because `WaitForNextEvent_` returns early while runnables are
  pending (event_loop.cc:207). The lock+notify path is taken *only* from
  worker threads — exactly where `call_soon_threadsafe` needs it.
- ~~A cancelled `call_later` still fires its `AppTimer`.~~ **Handled in
  Phase 1.** `_timer_handle_cancelled` drops `_BATimerHandle._ba_timer`,
  whose dealloc calls `DeleteAppTimer` — real cancellation, no wasted fire.
- N sequential `call_soon`s = N `Run_` iterations: confirmed cheap.
  Measured **~9µs/hop** (10k `await asyncio.sleep(0)` in 89ms). The cost is
  dominated by asyncio's own Python Task/Handle machinery, not our glue.

### Phase 2 — native fast-paths: NOT PURSUED (measurements don't justify)

Investigated 2026-05-30. The two bits this phase was meant to add are already
delivered by Phase 1:
- A no-lock same-thread `call_soon` — already free via `PushRunnable`'s
  thread routing (see corrected caveat above). A dedicated
  `_babase.call_soon_local` native would only shave the generic `pushcall`
  arg-parse + lambda alloc — ~1–3µs on an already lock-free ~9µs hop, and no
  logic-thread workload does CPU-bound tight-await loops. Not worth the added
  C++ binding surface.
- Cancelable timers — already done in Phase 1 (drop-ref → `DeleteAppTimer`).

The one remaining idea — pushing `Handle` execution into C++ to drop the
`handle._run` closure per callback — is sub-µs and explicitly deferred; revisit
only if a real async-heavy logic-thread workload ever shows up in a profile.

### Phase 3 — networking policy (stub)

The client logic-thread loop does no socket I/O (v2transport is native C++;
HTTP is blocking urllib3 on worker threads). So leave all of
`BaseEventLoop`'s socket/reader/writer surface
(`sock_*`, `create_connection`, `create_server`, `add_reader/writer`,
`getaddrinfo`, SSL, sendfile, …) as the inherited `NotImplementedError`.
Blocking I/O continues to go through `run_in_executor`. This is a deliberate
scope cut — networking-via-asyncio on the logic thread was only ever a
"maybe" in the old `_asyncio.py` docstring.

## Sharp edges / risks

- **"Running" without `run_forever`.** We set `loop._thread_id` +
  `events._set_running_loop(loop)` manually so `get_running_loop()`,
  `is_running()`, and `Task`/`Future` construction work. This is the one bit
  of asyncio-internal coupling; pin the CPython version assumptions and
  re-verify on Python upgrades.
- **`BaseEventLoop` internals we bypass** (`_ready`, `_scheduled`,
  `_selector`, `_run_once`) must never be entered — guaranteed as long as we
  never call `run_forever`/`run_until_complete` and override the public
  schedulers. A stray library call to `loop.run_until_complete` on the logic
  thread would hit our `RuntimeError`; that's intentional and surfaces
  misuse loudly.
- **`contextvars`.** `Handle`/`TimerHandle` capture and run within a copied
  context themselves; `pushcall(raw=True)` deliberately does *no* context
  save/restore, so there's no double-handling. Good.
- **Suspend/resume.** While `suspended_`, `Run_` skips `timers_.Run` +
  `RunPendingRunnables_`, so asyncio work correctly pauses with the app and
  resumes on unsuspend. No special handling needed.
- **Shutdown.** Loop lives for the thread's lifetime; `close()` is a no-op.
  Any executor futures outstanding at shutdown behave as they do today.

## Validation plan

1. Unit-ish: a boot-time `aio_test()` (the existing `if bool(False)` block)
   doing `await asyncio.sleep()` + `await loop.run_in_executor(...)`; confirm
   it completes and `get_running_loop()` is our loop.
2. Latency: re-run the construct-mode warm-boot resolve timing
   (`apprun.run_headless_capture`); expect the ~430ms pump-bound figure to
   collapse toward the ~75ms work cost, with **no** heartbeat timer present.
3. Idle: confirm a warm idle headless app makes no busy-wake (no heartbeat
   means idle should be fully CV-blocked; verify CPU at rest).
4. Throughput sanity: a tight-await coroutine (e.g. 10k `call_soon` hops)
   to characterize per-iteration overhead before deciding on Phase 2.
5. `make cmake-build` + `make cmake-server-build`; `make mypy`/`make pylint`.

## References

- `babase/_asyncio.py` — current pumped-loop setup (to be replaced).
- `event_loop.cc` `Run_` (:253), `RunPendingRunnables_` (:618),
  `WaitForNextEvent_`, `PushLocalRunnable_`/`PushCrossThreadRunnable_` (:660).
- `python_methods_base_1.cc` — `pushcall` (:582, raw mode :529),
  `apptime` (:619), `apptimer` (:662).
- `docs/followups.md` → "Async / Event Loop" entry (root-cause writeup).
