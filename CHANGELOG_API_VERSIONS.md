This file documents past and future changes associated with api-version bumps.

Although Ballistica strives to maintain backward compatibility when possible,
breaking changes are sometimes necessary. Ballistica's api-version system exists
to allow user code to gracefully adapt to these changes and to prevent older
incompatible code from being loaded and causing problems.

Note: For the next api version bump, the engine will be transitioning to an
overlapped api-version system. This means at some point it will support both api
9 and 10 at once. Mods targeting api 9 will still function but will get warnings
about updating to api 10 and preparing for feature changes associated with the
end of api 9 support. Once enough time has passed to allow the mod ecosystem to
prepare, api 9 support will end and those changes will drop. Later the process
will repeat with api 10 and 11 coexisting for a while before 10 is dropped, etc.

### Upcoming changes when API 9 support ends (and how to prepare for them).
- `ba*.Call()` will change to behave like `ba*.CallStrict()` instead of
  `ba*.CallPartial()`. To prepare
  for this, change all of your existing `Call()` usage to `CallPartial()` to
  retain existing behavior.
- Same as above for `ba*.WeakCall()` (migrate to `WeakCallStrict()` or
  `WeakCallPartial()` for now).
- `bauiv1.uicleanupcheck()` will be removed. To prepare for this, you should be
  using `ba*.app.ui_v1.add_use_cleanup_check()` instead.
- `MainWindow.main_window_replace()` will no longer accept `MainWindow` objects
  directly. To prepare for this, you should be passing callables to generate
  `MainWindow` objects.

