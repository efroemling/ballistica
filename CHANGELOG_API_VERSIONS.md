This file documents past and future changes associated with api-version bumps.

## What is API Version?
Although Ballistica strives to maintain backward compatibility when possible,
breaking changes are sometimes necessary. Ballistica's api-version system exists
to allow user code to gracefully adapt to these changes and to prevent older
incompatible code from being loaded and causing problems.

## Overlapping API Versions
In the past, api-version bumps required *all* mods to immediately make necessary
changes and then update their target versions before they would load again,
which resulted in large amounts of friction in the modding community. To avoid
this problem, the engine will be transitioning to an overlapping api-version
system for the next api-version bump. This means at some point it will support
both api 9 and 10 at once. Mods targeting api 9 will still function but will get
warnings about upgrading to 10 and preparing for changes to occur with the
removal of 9. Once enough time has passed to allow the mod ecosystem to prepare,
api 9 support will end and those changes will occur. Later this process will
repeat with api 10 and 11 coexisting for a while before 10 is dropped, etc.

To maintain a working mod, keep your `# ba_meta require api` lines targeting the
newest api version 'X' and ensure that your code accounts for all upcoming
changes to happen with the removal of 'X-1'. Generally the engine will issue
warnings when you are using deprecated functionality, but it is important to
check the list below to be sure.

Note that once api 'X' becomes available, no more changes will be scheduled for
the 'X-1' removal. This means that if you update your code for 'X' and account
for all listed 'X-1' changes, your code should remain functional for as long as
'X' remains supported.

Also note that the engine makes no guarantees of *forward* compatibility within
api-versions. Changes and additions can happen at any time as long as they are
backwards compatible, and code targeting those changes should only expect to
work on builds newer than what they were built against; not older - even if the
api-version has not changed. In general it is best to always be running newest
available builds.

### Upcoming changes when api 9 support ends (and how to prepare for them)
- `ba*.Lstr` is going away. Migrate all uses of it to the new `ba*.LangStr`
  class.
- Engine calls that return an `Lstr` are growing a `langstr` keyword argument.
  Passing `langstr=True` gets you a `LangStr` (or a plain `str` for things we
  have no translation entry for, such as a name your own mod supplied). To
  prepare, pass `langstr=True` at these call sites and handle the result being
  `str | LangStr`. When api 9 support ends these calls return the new type
  unconditionally and the argument becomes inert; it is removed when api 10
  support ends, so you will then drop it again. Affected so far:
  `bascenev1.GameActivity.get_display_string()`,
  `get_settings_display_string()`, `get_instance_display_string()`,
  `get_instance_scoreboard_display_string()`, `get_team_display_string()`,
  `bascenev1.get_map_display_string()`, and
  `bascenev1.MultiTeamSession.get_next_game_description()`.
- Properties that return an `Lstr` cannot take an argument, so each is gaining
  a `_langstr` twin. Use `bascenev1.Level.displayname_langstr` instead of
  `bascenev1.Level.displayname`. When api 9 support ends, `displayname` itself
  returns a `LangStr`; the `_langstr` twin is then removed when api 10 support
  ends, at which point you switch back to the plain name.
- `bascenev1.SessionTeam.name` and `bascenev1.Team.name` are now
  `str | LangStr` rather than `str | Lstr`. Built-in team names are `LangStr`
  values and player-customized names are plain strings. If you assign an
  `Lstr` it is flattened to a `str`, so team names you set will no longer
  re-translate when the language changes; assign a `LangStr` to keep that.
- `ba*.Call()` will change to behave like `ba*.CallStrict()` instead of
  `ba*.CallPartial()`. To prepare for this, change all of your existing `Call()`
  usage to `CallPartial()` to lock in current behavior. Or use `CallStrict()` if
  you don't need to pass extra args at call-time, as this gives better
  type-checking.
- Same as above for `ba*.WeakCall()` (migrate to `WeakCallPartial()` or
  `WeakCallStrict()`).
- `MainWindow.main_window_replace()` will no longer accept `MainWindow` objects
  directly. Instead it expects a callable that generates a `MainWindow` object.
  To prepare for this, code such as
  `self.main_window_replace(MyNiftyWin(some_arg))` can generally just become
  `self.main_window_replace(lambda: MyNiftyWin(some_arg))`. Look at `bauiv1lib`
  for examples.
- `bauiv1.uicleanupcheck()` will be removed. To prepare for this, use
  `ba*.app.ui_v1.add_use_cleanup_check()` instead.
- The `extra_type_id` arg to `ba*.app.ui_v1.set_main_window()` will no longer
  have a default value. If you are using this method (generally you should not),
  make sure you are passing this. It is mainly for use with DocUI windows; in
  most other cases it can be an empty string.
- `bascenev1.SessionPlayer.get_v1_account_id()` is deprecated; use
  `get_account_id()` instead. The new and old functions are technically
  identical and return V1 ids for protocol < 36 and V2 ids for protocol >= 36;
  the new one just has a more correct name. The old name will be removed when
  api 9 support ends.
- `bascenev1.Map.get_preview_texture_name()` is deprecated; override
  `get_preview_texture()` instead, which returns a loaded `bauiv1.Texture`
  rather than a name for the caller to look up. Normally you return it
  straight off an asset-package wrapper, e.g.
  `return myassets.textures.my_map_preview.get()`. Maps that override only
  the old call keep working (the new one falls back to it), but built-in maps
  no longer implement it, so calling it on one now returns `None`. It is
  removed when api 9 support ends.
- `bascenev1.Level.preview_texture_name` is deprecated, as is passing
  `preview_texture_name` to `bascenev1.Level()`. Use the `preview_texture`
  keyword argument and the matching `preview_texture` property instead, which
  deal in asset-package wrapper references rather than names to look up:
  pass the wrapper's texture entry directly —
  `bs.Level(..., preview_texture=myassets.textures.my_level_preview)`, note
  no `.get()`, since levels are built before asset-packages are resolved —
  and read `level.preview_texture` to get the loaded `bauiv1.Texture`.
  Constructing a level the old way still works (the texture is then looked up
  from the name on first use), but built-in levels no longer carry a name, so
  reading `preview_texture_name` on one now returns `None`. Both go away when
  api 9 support ends.
- The `float_times` argument on `efro.dataclassio.IOAttrs` is deprecated and
  will be removed when api 9 support ends. Replace `IOAttrs(float_times=True)`
  with `IOAttrs(time_format='float')`.

