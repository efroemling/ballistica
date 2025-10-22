This file documents past and future changes associated with api-version bumps.

Although Ballistica strives to maintain backward compatibility when possible,
breaking changes are sometimes necessary. Ballistica's api-version system exists
to allow user code to gracefully adapt to these changes and to prevent older
incompatible code from being loaded and causing problems.

## Overlapping API Versions
In the past, api-version bumps required *all* mods to immediately update their
target versions before they would load again, which resulted in large amounts of
friction in the modding community. To avoid this problem, the engine will be
transitioning to an overlapping api-version system for the next api-version
bump. This means at some point it will support both api 9 and 10 at once. Mods
targeting api 9 will still function but will get warnings about updating to 10
and preparing for changes to occur with the removal of 9. Once enough time has
passed to allow the mod ecosystem to prepare, api 9 support will end and the
associated changes will occur. Later this process will repeat with api 10 and 11
coexisting for a while before 10 is dropped, etc.

To maintain a working mod, keep your `# ba_meta require api` lines targeting the
newest api version 'X' and ensure that your code accounts for all upcoming
changes to happen with the removal of 'X-1'. Generally the engine will issue
warnings for such code, but it is important to check the list below to be sure.

Note that once api 'X' becomes available, no more changes will be scheduled for
the 'X-1' removal. This means that if you update your code for 'X' and account
for all listed 'X-1' changes, your code should remain functional for as long as
'X' remains supported.

Note also that the engine makes no guarantees of *forward* compatibility within
api-versions. Changes and additions can happen at any time as long as they are
backwards compatible, and code targeting those changes should only expect to
work on builds newer than what they were built against; not older - even if the
api-version has not changed. In general it is best to always be running newest
available builds.

### Upcoming changes when api 9 support ends (and how to prepare for them)
- `ba*.Call()` will change to behave like `ba*.CallStrict()` instead of
  `ba*.CallPartial()`. To prepare for this, change all of your existing `Call()`
  usage to `CallPartial()` to lock in current behavior. Or use `CallStrict()` if
  you don't need to pass extra args at call-time, as this gives better
  type-checking.
- Same as above for `ba*.WeakCall()` (migrate to `WeakCallPartial()` or
  `WeakCallStrict()`).
- `MainWindow.main_window_replace()` will no longer accept `MainWindow` objects
  directly. To prepare for this, you should be passing callables to generate
  `MainWindow` objects. Look at `bauiv1lib` for examples.
- `bauiv1.uicleanupcheck()` will be removed. To prepare for this, use
  `ba*.app.ui_v1.add_use_cleanup_check()` instead.

