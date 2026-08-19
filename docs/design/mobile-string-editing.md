# Mobile String Editing

**Description:** How the platform text-edit dialogs on iOS/tvOS/Android are wired to the engine's StringEditAdapter — the apply-vs-submit split, the kind system that gates it, and the constraints that keep the editor from wedging the game.

When an editable text widget is activated on a platform with a native
editor (`AppPlatform::HaveStringEditor()`), the engine hands the edit to
the OS rather than drawing its own on-screen keyboard. This doc covers
the contract between the two halves. The per-platform UI details live in
the code, which is commented heavily; what follows is the part no single
file shows.

## The two halves

```
TextWidget / DevConsole
  -> StringEditAdapter (Python; babase/_stringedit.py)
    -> AppPlatform::InvokeStringEditor  (reads description/initial_text/
                                         max_length/is_password/kind)
      -> DoInvokeStringEditor           (per-platform)
        -> UIKitFromCpp.swift  /  StringEditDialogFragment.java
          -> StringEditorApply(val, submit) | StringEditorCancel()
            -> adapter.apply(text, submit) | adapter.cancel()
              -> _do_apply() [+ _do_submit() when submit]
```

The adapter attribute names are read by name from C++, so renaming them
silently breaks the bridge — there is a comment saying so in
`_stringedit.py`; heed it.

## apply vs submit — the load-bearing distinction

`apply(text, submit)` carries **two** different gestures:

- `submit=False` — "put this value in." The drafting gesture. Produced
  by tapping away from the editor.
- `submit=True` — an enter-equivalent gesture (the keyboard's action
  key, or the editor's commit button). Runs `_do_apply()` **and then**
  `_do_submit()`, which fires the edit target's return-press behavior:
  chat actually sends, the dev console actually runs the line.

**Submit is opt-in per `StringEditKind`, deliberately.** Both platform
editors decide `submit` from the kind, not from the gesture alone, so
that an ordinary text widget keeps the classic behavior of just being
filled in even when you press Done. Adding a kind to the submitting set
changes behavior for every widget using that kind, so it is a decision,
not a detail.

Current kinds (`StringEditKind`): `DEFAULT` (no submit), `CHAT`
(submits — sends), `CODE` (submits — runs; also disables autocorrect,
autocapitalization and smart punctuation, which corrupt code).

## Glyphs follow the platform, not each other

The editor's commit button sits inches from the OS keyboard's action key
doing the identical thing, so it mirrors **that platform's** key rather
than matching the other platform. Users never see both platforms; they
always see the button next to the key.

That is why chat is an up arrow on iOS (which draws `.send` as an up
arrow, as iMessage does) but a paper plane on Android (which is what
Gboard draws for `IME_ACTION_SEND` — verified on an emulator). Neither
platform allows a custom label on the key, so "Exec"-style wording is
not achievable for code; both use the platform's "go".

## Constraints that keep the game usable

- **The input lock must be the permanent flavor.** The editor takes
  `LockAllInput(true, ...)` because our key/controller input arrives via
  GameController app-wide and does not stop for a presented view
  controller. The *temp* flavor carries a 10-second stuck-lock watchdog
  (`Input::StepDisplayTime`), and an edit routinely outlasts that — a
  temp lock would be dropped mid-edit and hand every keypress back to
  the game underneath. It follows that the lock is released only by the
  session's own finish path, which is why every teardown route calls it.
- **Exactly one terminal result per session.** Both editors latch
  (`resultSent` / `mResultSent`) and both report from `viewDidDisappear`
  / `onDismiss` as a safety net. A late result after the C++ side
  released its adapter ref would fail `BA_PRECONDITION` in
  `StringEditorApply` — an exception, not a no-op — which is why a
  displaced session is retired silently rather than left able to report.
- **A session stays "current" until its editor is off screen**, not
  until it reports a result. UIKit silently drops a `present()` aimed at
  a view controller mid-dismissal, so a new edit arriving during the
  dismissal animation must chain onto the old one's teardown.
- **The 5s adapter timeout is a safety valve, not a feature.**
  `StringEditAdapter.can_be_replaced()` lets a new edit displace one
  whose driver vanished without reporting. It exists because the
  one-edit-at-a-time lock is only as reliable as the platform code that
  releases it. Seeing its warning in a log means a driver bug.

## Key repeat

Held-key repeat for UI navigation and dev-console text editing comes
from `AppAdapter::GetKeyRepeatDelay()/Interval()`. The rule is **use the
OS preference where one exists, our tuned constant where none does**:
macOS reads real Cocoa values; iOS/tvOS have no such API and fall back
to the base defaults. Gamepad UI navigation is hardcoded
(`kUINavigationRepeatDelay`/`Interval` in `ui.h`) for the same reason —
there is no OS preference for a held d-pad — not because hardcoding is
preferred.

Honoring the OS values on desktop is an accessibility matter: those
sliders exist substantially for motor accommodation, and a user who set
a slow repeat needs it honored in menus too. Acceleration through long
lists was considered and rejected: discrete selection plus acceleration
overshoots, every step fires a move sound and animation, and it works
against the users most likely to be holding a key down. Long lists are
better served by page-jump / type-to-search, which are O(1).
