### 1.7.46 (build 22471, api 9, 2025-08-03)
- Resolves some networking issues from certain internet providers.
- Working towards more consistent toolbar visibility more on small ui mode.

### 1.7.45 (build 22465, api 9, 2025-07-29)
- Ticket counts and purchases are now stored with your V2 account instead of V1.
  This should make things like opening treasure chests faster and smoother since
  only a single server is involved instead of two. It also paves the way for all
  the fun new upcoming store stuff. However be aware that older builds of the
  game will still use your old V1-server inventory, so if you go back to an
  older version of the game you may see different ticket counts or unlocks and
  any inventory changes you make there might not be visible in newer versions.
  So try and stay on newer versions at this point to be safe.
- The `baplus.get_v1_account_ticket_count()` method has been removed. This count
  is now available as `ba*.app.classic.tickets`.
- The `baplus.get_v1_account_product_purchased()` method has been removed.
  Current classic purchases are now available as `ba*.app.classic.purchases`.
- Working with the repo now requires the 'zstd' binary, and will complain if it
  is not found during env checks. This should be pretty widely available through
  `apt install zstd` or whatever. We'll be making pretty widespread use of Zstd
  compression in coming years in both the game and tools, as it gives pretty big
  improvements in both size and speed compared to classic gzip stuff. It is also
  being added to Python 3.14 later this year.

### 1.7.44 (build 22451, api 9, 2025-06-28)
- Added a `-B` / `--dont-write-bytecode` flag to disable writing .pyc files, and
  an associated `dont_write_bytecode` value for the server config file. In most
  cases writing .pyc files is useful as it can speed up relaunches and keep
  things running smoother, but if you are doing something like generating tons
  of config dirs for your servers then having the cache directories under each
  of them fill with .pyc files may be wasteful.
- Renamed the `setup_pycache` arg in `baenv` to `setup_pycache_prefix` and
  switched it to default to `False` instead of `True`. Monolithic builds (pretty
  much everything that matters currently) now explicitly pass `True` for it. The
  only real impact this has is that modular builds now use totally vanilla
  Python caching behavior (`__pycache__` dirs) instead of nagging the user about
  manually setting the 'PYTHONPYCACHEPREFIX' env var to specific values.
- The new pycache dir is now simply `(CACHE_DIR)/pyc` instead of
  `(CACHE_DIR)/pyc/(BUILD_NUMBER)`. Having a single directory slightly
  complicates the logic of pruning outdated caches, but I think I prefer that
  over having to regerate a completely new cache each time a minor update comes
  through.
- Pycache upkeep now waits until a few seconds after the app is started up and
  limits its speed a bit to avoid slowing down app startup and minimize the
  possibility of hitches.
- Holding shift while pressing a dev-console toggle key (~ or F2) now cycles it
  in reverse.
- The dev-console now remembers which tab was selected between runs.
- The dev-console logging tab now remembers which logger you were last viewing
  between app runs. This means if you have one particular logger you flip off
  and on a lot you can generally get at it by just bringing up the small size
  dev-console.
- Cleaned up input handling. Now, if there is a single player using the local
  device, all escape/menu/back buttons will bring up the menu associated with
  that player, allowing leaving the game with just that player instead of fully
  exiting to the menu/etc. This worked in limited situations before the big
  1.7.37 UI revamp, but now is more generalized and consistent.
- Added various debug logging for input devices (set `ba.input` to 'Debug' in
  the dev-console logging tab to see it).
- Software cursor no longer freezes during fades or other input-locked
  situations and now draws over the top of fades instead of being affected by
  them (makes it more consistent with hardware cursors).
- Software cursor in sdl builds now disappears when the cursor leaves the window
  instead of getting stuck at the edge.
- Replaced all uses of Python's built in `urllib.request` with our bundled
  `urllib3`. This should perform better and hopefully won't get stuck at
  shutdown like old urllib was prone to do. Please holler if you run into any
  sort of connectivity issues that weren't there before.
- Turned the `babase.garbage_collect()` function into a full subsystem
  (`ba*.app.gc`). It will now warn if too many objects are resorting to cyclic
  garbage collection due to reference loops, and it offers some tips and
  functionality to help track down and eliminate said loops. Check out the
  `GarbageCollectionSubsystem` documentation for more info.
- Added `DiscordSubsystem` class which wraps the underlying `_babase` 
  implementation of discord sdk
- Added proper support for mouse-cancel events. This fixes an annoying issue
  where using home-bar nav gestures on Android to switch apps could lead to
  unintended button presses (namely on chest slots since that is near the home
  bar).
- Fixed issues on some versions of Android with ads being cut off by system bars
  at screen edges.
- (build 22431) Using Android back gestures to bring up the in-game menu now
  properly shows leave-game options for a single local player (similar fix as
  mentioned above).
- Tweaked the default on-screen controls positions slightly for modern phones.
- The audio-server now inits itself asynchronously, which in my tests can shave
  5-10% off of startup times. Please holler if you experience any odd audio
  behavior in this build.
- Officially deprecated the `# ba_meta export plugin` shortcut - you should
  switch to `# ba_meta export babase.Plugin` if you have not yet. The former
  will still work for now but will emit a warning.
- Interstitial ads now show when playing tournaments. Sorry folks. But now that
  tourneys are free, it doesn't make sense to give them a benefit over other
  single-player play which *does* show ads. Remember you can permanently remove
  ads for your account by buying the cheapest token pack. Either way, thanks for
  helping me buy coffee.
- Android version now pauses GL rendering while ads are showing (since it is not
  visible anyway). Should save a bit of battery and help interactive ads play
  smoother.
- Cleared out several reference cycles using the new ref-loop detection
  garbage-collection stuff. Learned an important lesson: don't create dataclass
  classes within functions, as they seem to always wind up with reference cycles
  and you'll leak memory each time you call that function (until manual gc is
  finally run). I found that tutorial.py was creating 214 reference-cycled
  objects per run due to a bunch of dataclasses defined in a function. Moving
  them to the global scope dropped that to 0. Another cycle culprit was Flag
  classes in a few minigames. I fixed those using weakrefs to break the cycles.
- Didn't realize we've technically been requiring OpenGL 3.2 on desktop; not
  3.0. Updated checks accordingly so any 3.0/3.1 people will get better error
  messages.
- The 'Logging' dev-console-tab has been polished up a bit, and now includes
  descriptions for ballistica's various loggers.
- Added `efro.util.strip_exception_tracebacks()` which can help break reference
  cycles caused by handling exceptions.

### 1.7.43 (build 22406, api 9, 2025-06-09)
- Fixes an issue with tournament scores not submitting properly in 1.7.42.

### 1.7.42 (build 22402, api 9, 2025-06-08)
- Basic Discord social sdk support is now in place, but not yet enabled in by
  default in builds (Thanks Loup-Garou911XD!).
- Added `discord_start`, `discord_richpresence`, `discord_set_party`,
  `discord_add_button`, `discord_join_lobby`, `discord_leave_lobby`,
  `discord_send_lobby_message` funtions to _babase.
- Added the `float_times` arg to `dataclassio.IOAttrs` to allow storing
  `datetime.datetime` or `datetime.timedelta` values as simple floats instead of
  int arrays.
- Windows builds are now 64 bit. The last time I made this switch I heard from
  some folks who still needed 32 bit so I switched it back, but this time there
  are technical reasons: we're adopting the discord social sdk which is 64 bit
  only. Also, Windows 10 will be officially end-of-life this coming October and
  Windows 11 is 64 bit only. If you still need 32 bit builds please holler;
  maybe we can maintain a stripped-down test build or something.
- Mac prefab builds for Intel Macs are now enabled again. I had disabled these
  thinking they were likely unused but was happy to find out I was wrong about
  that.
- Added 'Race' and 'Pro Race' to the Practice co-op section.
- Removed the `ba*.app.env.test`, `ba*.app.env.arcade`, and `ba*.app.env.demo`
  values, which were redundant now that `ba*.app.env.variant` exists.
- Removed the `ba*.app.env.android` value which was redundant now that we have
  `ba*.app.env.platform`.
- The `ba*.app.env.debug` value is now `ba*.app.env.debug_build` to make it more
  clear that this refers to how the app was built; not to a setting that can be
  flipped on or off at runtime (like Python's `__debug__` value).
- Added `ba*.app.env.cache_directory` which is where the app can put downloaded
  assets and other data that it wants to keep but which it can recreate if
  needed. It should always be safe to blow any or all of this data away between
  runs (as the OS itself might do so in some cases).
- You can now pass `--cache-dir` or `-a` on the command line to override the
  app's cache directory. Its default varies per platform but the standard one is
  `(CONFIG-DIR)/cache`.
- The `volatile_data_directory` concept which was used internally has been
  replaced by the new cache directory, so if you see a `vdata` dir in your app
  config dir you can delete it to keep things tidy.
- Backup configs are now named `.config_prev.json` instead of
  `config.json.prev`. This keeps them hidden by default on unix-y OSs for a
  tidier look, and also keeps .json file associations working. Feel free to blow
  away any `config.json.prev` files you have lying around.
- Debug builds will now blow away the occasional random file from the cache-dir
  just before spinning up the engine. This is meant to exercise the app's
  ability to recreate anything the OS itself might purge between runs (we make
  the guarantee that cache-dir files remain intact while the app is running but
  no such guarantees between runs).
- The engine is now set up to generate its own Python bytecode (.pyc) files in
  the cache-dir using the PYTHONPYCACHEPREFIX functionality introduced in Python
  3.8. It will run a background thread to prune or regenerate .pyc files as
  needed so the full cache should always be up to date (outside of the first few
  moments when launching a new app version). Previously the app shipped with
  .pyc files scattered in `__pycache__` dirs throughout the codebase which were
  set to always be used when present, which lead to confusing behavior where
  edits to bundled .py files would be ignored unless the associated .pyc file
  was deleted first. Now things should be much more intuitive: there are only
  .py files in ba_data and edits to them will work as expected; all .pyc
  wrangling is handled automagically in the background. This makes me especially
  happy as it allows me to simplify asset pipelines. Please holler if you run
  into any side-effects of this system such as hitches or slowness on launch
  compared to previous versions.
- Cleaned up threading and shutdown behavior. The app now properly shuts down
  Python on exit which means it will block and wait for all Python threads to
  finish (though it will still force the issue and quit immediately if stuck for
  a while). Also purged all uses of 'daemon=True' in threads which is generally
  considered unsafe due to such threads possibly accessing Python state after
  Python has shut down. So this new setup is safer and more deterministic but we
  need to be careful about making sure all threads properly exit at app
  shutdown. If you run into cases where the app consistently gets stuck when
  trying to exit or you see warnings about unexpected threads still running,
  please holler.
  
### 1.7.41 (build 22382, api 9, 2025-05-25)
- Fixed a few unsafe accesses of cJSON objects that could be exploited to crash
  servers by feeding them bad json data. If you ever come across CXX code
  accessing a cJSON obj like `obj->valuestring` without making sure
  `cJSON_IsString(obj)` is true first, please holler loudly at me.

### 1.7.40 (build 22379, api 9, 2025-05-23)
- Upgraded from Python 3.12 to 3.13. See python.org for what fun new goodies
  this gets us.
- Bumping minimum supported Android from 6.0 to 7.0. I'm reworking app language
  support in this version (see notes below) and setting min-version to 7.0 makes
  this significantly simpler due to Android 7 adding support for BCP 47
  resources. It's been a year and a half since the bump to 6.0 and my stats show
  barely anyone still running 6 so I feel this is reasonable.
- Apple builds (namely Mac for now) are now using a more 'vanilla' version of
  the Python library instead of the custom-built version I've been maintaining
  for years. For one, this means that Python and its various modules and library
  dependencies now exist as separate shared libraries on disk instead of all
  being statically compiled into a single binary. This increases app size and
  complexity a bit but will make it much easier to update Python going forward
  and reduces the chances of things breaking due to nonstandard customizations.
  At some point in the future I may make the same change for the Android
  version, though the custom statically linked build is a bit easier to maintain
  there so its less of a priority.
- Fixed an issue on Android where in some cases viewing an ad to reduce chest
  open time would have no effect. Please holler if you ever watch an ad and
  don't see the resulting time reduction.
- Querying exported classes via the meta subsystem now accepts fully qualified
  path strings such as 'babase.Plugin' instead of type objects. This is because
  I have disabled the class-name prettifying that was happening before
  (`set_canonical_module_names()`), so the *actual* class paths we'd pull from
  passed type objects now could be something ugly/internal like
  `babase._plugin.Plugin` and I'd rather not use private paths in our `# ba_meta
  export` comments. By explicitly providing string paths we can keep using clean
  public aliased paths like `babase.Plugin`.
- Sphinx documentation generation is now set to 'nitpicky' so it will complain
  if anything is referenced in comments that cannot be found (classes, methods,
  etc.) This should help avoid broken or out of date docstrings. Specific
  exceptions to this can be added in `conf.py` if needed.
- Added the `babase.LocaleSubsystem` which can be found at `ba*.app.locale`.
  This is the modern replacement for the `LanguageSubsystem` at `ba*.app.lang`
  which will eventually be removed. This ties in with upcoming goodies such as
  asset-package based translations.
- Split the Spanish translation into two different ones: 'Spanish - Latin
  America' and 'Spanish - Spain'.
- Split the Portuguese translation into two different ones: 'Portuguese -
  Brazil' and 'Portuguese - Portugal'.
- Android should now be smarter about selecting translations - for example, if
  your first choice language is not available but your second choice is, it
  should now show your second choice instead of falling back to English.

### 1.7.39 (build 22353, api 9, 2025-04-08)
- Lots of work on sphinx documentation. Docs are now generated for both runtime
  and tools packages. Removed the old pdoc docs generation option since sphinx
  is working quite well and gives us lots of room to grow, and also since we
  can't really support both (docstrings need to be formatted to play nice with
  one or the other). Big thanks to Dliwk though for the old pdoc setup which got
  us to this point.
- The `babase.App.State` class is now `babase.AppState`.
- Removed `babase.print_exception()`. This has been mostly unused for a long
  time. Anything still using it should use `logging.exception()` instead.
- Removed `babase.print_error()`. This has also largely been unused for a long
  time. Anything still using it should use `logging.error()` instead.
- (build 22346) Hardened against some potential malformed-packet attacks. If you
  find someone is still able to crash your server by sending invalid data,
  please let me know.
- Added highlights to show players when they have unclaimed chests in their
  inbox or chests that can be opened.
  
### 1.7.38 (build 22318, api 9, 2025-03-20)
- Added animations for reducing chest wait times or gaining tickets or tokens
- Made MainWindow auto-recreate smarter. If something such as text input or a
  popup window is suppressing main-window-auto-recreate, it'll now do a single
  recreate once the suppression ends.
- (build 22313) Fixed a possible client crash due to uninitialized memory when
  handling `BA_MESSAGE_HOST_INFO` data.
  
### 1.7.37 (build 22304, api 9, 2025-03-10)
- Bumping api version to 9. As you'll see below, there's some UI changes that
  will require a bit of work for any UI mods to adapt to. If your mods don't
  touch UI stuff at all you can simply bump your api version and call it a day.
  I'm hopeful that api version won't need to be bumped again for a long time (if
  ever).
- I am pleased to announce that after years of hard work from many members of
  the community, PirateSpeak is now complete and available as a language choice.
  This changes everything.
- Heavily reworked and cleaned up the logging system. There is now a 'ba' Python
  logger and various logger categories under it such as 'ba.lifecycle',
  'ba.connectivity' or 'ba.v2transport'. By setting these individual loggers to
  different levels such as 'debug', one can easily observe and debug specific
  parts of app behavior. Over time I will better organize the logger hierarchy
  and wire up more functionality to be logged this way.
- Added a 'Logging' tab to the dev-console. This allows easily setting log
  levels for all existing Python loggers, as well as resetting them all to
  defaults. Levels set here are restored on startup, so it is possible to debug
  app startup behavior by setting log levels and then relaunching the app.
  Previously this sort of thing would generally require setting cryptic
  environment variables which was not feasable on all platforms, but this new
  system should work everywhere.
- Log messages printed to both the command line and the in-app console now
  include timestamps and logger names, and are color coded for severity
  (DEBUG=blue, INFO=default, WARNING=orange/yellow, ERROR=red, CRITICAL=purple).
- `efro.log` is now `efro.logging` which better lines up with other logging
  module names. It was originally named `log` to work around a mypy bug.
- Went ahead and fully removed `efro.call.tpartial` (since we're breaking
  compatibility anyway by bumping api version). If you are using
  `efro.call.tpartial` anywhere, simply replace it with `functools.partial`.
- The newest Pylint update (3.3) added a check for
  'too-many-positional-arguments'. This seems like a good idea, so I updated
  various functions to conform to it and set some others to ignore it. Basically
  if you see a function like `def dothing(a, b, *, c, d)` then everything after
  the `*` needs to be passed as a keyword. So you can't do `dothing(val1, val2,
  val3, val4)`; you need to do `dothing(val1, val2, c=val3, d=val4)`. Requiring
  keywords for complex functions generally leads to more readable code and less
  breakage if arguments are added or removed from the function.
- Playlist customization no longer requires pro.
- Soundtrack customization no longer requires pro.
- Campaign hard mode no longer requires pro.
- Full player profile color customization no longer requires pro.
- Removed nag screens for purchasing pro or bundle offers.
- Removed continue logic. Continues have been disabled server-side for a while
  but now removing the client code to clean things up a bit.
- Switching over to the new 'toolbar mode' UI that has been in the works for
  several years. This includes a number of handy things such as consistent
  buttons and widgets for league status, currencies, inventory, and the store.
  It also adds a fixed back button on phones that should be easier to hit and a
  dock for earned treasure chests at the bottom of the screen (will finally use
  those treasure chest textures!). This is a substantial change so please holler
  if you run into anything that looks broken or doesn't behave as you think it
  should.
- When running in 'small' UI mode (phones) the engine now uses 1300x600 as its
  virtual resolution. This gives a wider 19.5:9 aspect ratio which lines up with
  most modern smartphones, so people with such phones should no longer see
  wasted space on the sides of their screen. The virtual resolution on 'medium'
  and 'large' is now 1280x720. This gives the same 16:9 aspect ratio as the old
  resolution (1207x680) but is a cleaner number. The 16:9 aspect ratio still
  works well for tablets monitors, and TVs. When writing a UI, always be sure to
  test it on 'small', 'medium', and 'large' modes to make sure it fits on screen
  and feels similar in scale to the rest of the UI. Ideally when 'ui_v2' rolls
  around we can make it possible to build UIs that adapt better to screen sizes
  so things like fixed aspect ratios will no longer be necessary.
- Split the main menu UI into two classes: `bauiv1.mainmenu.MainMenuWindow` and
  `bauiv1.ingamemenu.InGameMenuWindow`.
- Removed some bits of `bauiv1` which were never fully implemented and which I
  feel were a flawed/outdated design. This includes `UILocation`,
  `UILocationWindow`, `UIEntry`, and `UIController`. The whole purpose of these
  was to add a higher level layer to the UI to make things like saving/restoring
  UI states easier, but I now plan to use `WindowState` classes to accomplish
  much of that in a more backward-compatible way. More on that below.
- Removed touch-specific button target-area adjustements. If you find any
  buttons that are now hard to hit accurately on a touchscreen, please holler.
- Added a new `bauiv1.Window` subclass called `bauiv1.MainWindow` which handles
  what was previously called the 'main-menu-window' system which was a bit
  ad-hoc and messy. MainMenuWindows have a built-in stack system so things like
  back-button handling are more automatic and windows don't have to hard-code
  where their back button goes to. There are also other benefits such as better
  state saving/restoring. When writing a MainWindow, pretty much all navigation
  should only need to use methods: `main_window_has_control()`,
  `main_window_back()`, and `main_window_replace()`.
- Finally got things updated so language testing works again, and made it a bit
  spiffier while at it. You now simply point the game at your test language and
  it will update dynamically as you make edits; no need to download any files.
  Example: if you are editing PirateSpeak, you should see an id such as
  'PirateSpeak_2248' in the website url. You can then go to the game and run
  `import babase; babase.app.lang.testlanguage('PirateSpeak_2248')` and you
  should instantly see some lovely pirate-speak. Also, any changes you make on
  the website should show up in the game within a few seconds. Enjoy!
- Added `urllib3` to our bundled third party Python modules. The engine will be
  doing more heavy downloading with Asset Packages coming online so its time to
  upgrade to a more modern web client library than Python's basic built in
  urllib stuff.
- Pasting a single line of text followed by newlines to the dev console now
  works. Previously it would complain that multiple lines of text aren't
  supported, but now it just ignores the trailing newlines.
- Added an 'AppModes' tab to the dev console, allowing switching between any
  AppModes defined in the current build for testing. Currently this is just
  SceneV1AppMode and EmptyAppMode. This will become more useful in the future
  when things like SquadsAppMode (Squads mode) or RemoteAppMode (the revamped
  BSRemote app) happen.
- Added a 'UI' tab to the dev console allowing debugging virtual screen bounds
  and testing different UI scales dynamically.
- Renamed `SceneV1AppMode` to `ClassicAppMode` and relocated it from the
  `scene_v1` featureset to the `classic` one. This makes more logical sense
  since `classic` is more about app operation and `scene_v1` is more about
  gameplay, though realistically it doesn't matter since those two featuresets
  are hopelessly entangled. Future parallels such as `squads` and `scene_v2`
  featuresets should be more independent of eachother.
- Removed the warning when calling `ba*.screenmessage` in a game context.
  Hopefully most code has been ported at this point and it has done its job. As
  a final reminder, `ba*.screenmessage()` will only show messages locally now;
  you need to use something like `bascenev1.broadcastmessage()` to show things
  to everyone in a game.
- Removed `efro.util.enum_by_value()` which was a workaround for a Python bug
  that has been fixed for a few versions now. Instaed of
  `enum_by_value(MyEnumType, foo)` you can simply do `MyEnumType(foo)`.
- Removed `bauiv1.is_party_icon_visible()` as it is now always visible.
- 'ui_scale' is no longer available in _babase.env() since it can now change;
  use `babase.get_ui_scale()` to get it now.
- Removed the UIScale control from the devtools window, which was only partially
  wired up (it did not affect native layer bits). For now the official ways to
  test UIScales are by using the UI tab in the dev-console or by setting the
  `BA_UI_SCALE` env var. If we can get UIScale switches to feel seamless enough
  at some point, it may be worth adding to display settings.
- There is now a `ba*.app.classic.save_ui_state()` method that should be called
  right before jumping into a game/replay/etc. This will save a state that will
  automatically be restored the next time the main menu activity is entered.
- (build 22010) Added the concept of 'auxiliary' windows and used them to make
  various window navigation more intuitive. Example: previously, if you were on
  the co-op screen and pressed the trophy toolbar icon to see your league rank
  and then pressed back, you would be taken back to the top level main menu. Now
  it will take you back to the co-op screen.
- (build 22018) Hardened SDL joystick handling code so the app won't crash if
  SDL_JoystickOpen() returns nullptr for whatever reason.
- (build 22028) Fixed a longstanding issue that could cause logic thread
  bg-dynamics message overflows.
- Added a close button to the dev-console as an alternate to using key presses
  to close it.
- (build 22063) Added a 'Copy History' button in the Python tab in the
  dev-console. Note that this will copy all cached log history; not just what is
  displayed in the dev-console. This should be handy for diagnosing problems in
  the future.
- (build 22072) Added a 'Use insecure connections' option in settings ->
  advanced. This may make it possible to play from places such as Iran where ssl
  connections are being blocked. Do not enable this if you don't need to.
- (build 22085) Added protection against an attack consisting of spamming
  invalid game-query packets.
- Using prefab builds on a Mac now requires an Apple Silicon machine (M1 or
  newer). Mac x86 prefab builds were becoming a major bottleneck in pushing out
  updates. Please let me know if you are making substantial use of prefab builds
  on an x86 Mac and I can reconsider. Note that this only concerns the prefab
  build system; regular official game builds still fully support x86 Macs.
- Added the `test-fast` Makefile target which skips some slower tests, and wired
  up `make preflight` to use this to keep things moving a bit faster. If you are
  not familiar with it, the `preflight` target is handy to run before committing
  code to git.
- The app-modes tab in the dev-console now uses the meta tag system to discover
  testable app-modes. Previously this would simply list the `default_app_modes`
  listed in the projectconfig.json. So now it is possible to make and explicitly
  test new app modes via mod scripts on vanilla game builds. Note that the game
  still uses the `default_app_modes` projectconfig.json value when selecting
  app-modes at runtime; to change this you need to either change your
  projectconfig and rebuild or replace `ba*.app.mode_selector` at runtime with
  a custom selector that selects your custom app-mode(s).
- The `ba*.app.threadpool_submit_no_wait()` method has been merged into the
  `threadpool` object, so it now is `ba*.app.threadpool.submit_no_wait()`.
- Clarified project rules for `snake_case` methods in C++ and updated various
  methods accordingly such as `Object::Ref::get()` and `Object::Ref::exists()`.
  See 'Getter/Setter Function Names' in
  https://github.com/efroemling/ballistica/wiki/Coding-Style-Guide for more
  info.
- Removed support for tab key navigation. This has been largely ignored for
  years and behaved in a mostly broken way in all recent UIs. Keyboard users
  should use arrow keys for navigation. To update any old UI code, search for
  and remove any 'claims_tab' arguments to UI calls since that argument no
  longer exists.
- Added a `get_unknown_type_fallback()` method to `dataclassio.IOMultiType`.
  This be defined to allow multi-type data to be loadable even in the presence
  of new types it doesn't recognize.
- Added a `lossy` arg to `dataclassio.dataclass_from_dict()` and
  `dataclassio.dataclass_from_json()`. Enum value fallbacks and the new
  multitype fallbacks are now only applied when `lossy` is True. This also flags
  the returned dataclass to prevent it from being serialized back out. Fallbacks
  are useful for forward compatibility, but they are also dangerous in that they
  can silently modify/destroy data, so this mechanism will hopefully help keep
  them used safely.
- Added a spinner widget (creatable via `bauiv1.spinnerwidget()`). This should
  help things look more alive than the static 'loading...' text I've been using
  in various places.
- Tournament now award chests instead of tickets.
- Tournaments are now free to enter if you are running this build or newer.
- (build 22225) Added `babase.get_virtual_screen_size()` and to get the current
  virtual screen size, `babase.get_virtual_safe_area_size()` to get the size of
  the area where things are guaranteed to be visible no matter how the window is
  resized, and added a `refresh_on_screen_size_changes` arg to the `MainWindow`
  class to automatically recreate the window when the screen is resized. This
  combined functionality can be used to custom fit UI elements to the exact
  screen size, which is especially useful at the small ui-scale with its limited
  screen real-estate. Generally medium and large ui-scale windows don't fill the
  entire screen and can simply stay within the virtual safe area and thus don't
  need to refresh.
- (build 22237) Reverted the change from earlier in this release where small
  ui-scale would have its own distinct widescreen virtual-safe-area. The virtual
  safe area is now always 1280x720 (16:9). I came to realize there were
  significant downsides to having safe-area be inconsistent; for instance
  onscreen elements designed for one safe area might be out of frame for players
  using the other, and things would effectively need to be limited to the
  intersection of the two safe areas to work everywhere. Since it is now
  possible to take advantage of the full screen area using the
  `get_virtual_screen_size()` and whatnot mentioned above, it makes sense to
  return to a single consistent safe area.
- (build 22258) Updated the Windows redist installers to the latest versions. If
  anyone is getting release builds of the game silently failing to launch,
  install the bundled redist libs and try again.
- (build 22258) Removed Windows debug redist libs such as `ucrtbased.dll` and
  `vcruntime140d.dll`. Technically these are not supposed to be bundled with
  software anyway and should instead be installed by installing Visual Studio. I
  was shipping outdated versions which was causing extra problems, so I've
  decided that I should follow the rules here and remove them. This means that
  if you want to run debug builds on Windows you'll need to install Visual
  Studio. Most people should be fine with release builds and don't need to worry
  about this.
- Added `docker-compose.yml` which can now be used with `docker compose` command
- Changed Docker make targets to use `docker compose` instead of `docker build`
- (build 22285) Window auto-recreation due to screen resizing is now disabled
  while onscreen-keyboards are present. This works around an issue where text
  editing on Android could break due to on-screen-keyboards causing screen
  resizes which kill the text-widgets they target.
- (build 22300) There is now a 'Secure V1 Connections' option in account
  settings on ballistica.net which should prevent V1 account spoofing attacks
  when enabled. The downside is that clients older than build 22300 will no
  longer be able to access the account while that setting is enabled.

### 1.7.36 (build 21944, api 8, 2024-07-26)
- Wired up Tokens, BombSquad's new purchasable currency. The first thing these
  can be used for is storage packs on ballistica.net, but this will expand to
  other places in the game soon. For a full explanation on why these were added,
  see https://ballistica.net/whataretokens
- Paid private hosting now uses tokens instead of tickets.
- Wired up initial support for using asset-packages for bundled assets.
- bacloud workspace commands are now a bit smarter; you can now do things like 
  `bacloud workspace put .` or even just `bacloud workspace put` and it will
  work. Previously such cases required explicitly passing the workspace name
  as a second argument. Both `workspace get` and `workspace put` now also have
  an optional `--workspace` arg if you want to sync with a workspace different
  than the local directory name.
- Cleaned up look and feel on horizontal scrollbars, especially when and how
  they fade in and out.
- Fixed an issue where ConfigNumberEdit objects would draw incorrectly with
  textscale set to non-1.0 values.
- Fixed a nasty bug with the new stdin handling from 1.7.35 which could cause
  the stdin thread to spin at 100% cpu usage in some cases (such as when
  launching the Mac build from the Finder and not a terminal).
- Added a `draw_controller_mult` arg to `bauiv1.imagewidget()` to control how
  brightly the image pulses when its controller widget is selected (can prevent
  brightly colored images from blowing out too much).
- The Mac version is now correctly rendering to a sRGB colorspace instead of P3.
  This was causing some bright colors to render extra-eye-destroying bright.
- Fixed an issue with the Repeater() class which could cause key presses in UIs
  to get lost if many were happening in short succession. An easy way to observe
  this (at least on my machine) was to press left and right repeatedly in the
  main menu - some presses would be lost and the selection would 'drift' one
  direction.
- Replaced all `efro.call.tpartial` calls with Python's built in
  `functools.partial`. Mypy's 1.11 update added full type checking for
  `functools.partial` so there's no benefit to maintaining our own special
  version anymore. This also applies to `ba*.Call` which is redundant in the
  same way. Both `efro.call.tpartial` and `ba*.Call` will probably be marked
  deprecated and go away at some point (or more likely simply not included in
  newer apis such as bauiv2).
- Added a `Delete Account` button directly to the account section in-game.
- The app now includes build number when looking for custom sys scripts in the
  mods dir. Previously it would have looked for something like `sys/1.7.36` but
  now it will look for something like `sys/1.7.36_21940`. I was seeing a lot of
  crash reports from people creating sys scripts using early builds of some
  version and then upgrading to later builds of the same version containing
  incompatibilities with the older sys scripts. This should help with that
  problem.
  
### 1.7.35 (build 21889, api 8, 2024-06-20)
- Fixed an issue where the engine would block at exit on some version of Linux
  until Ctrl-D was pressed in the calling terminal.
- V2 accounts have been around for a while now, so the old V1 device login
  button is no longer visible in the account panel. It is currently possible to
  bring it back by checking 'Show Deprecated Login Types' in advanced settings,
  but please consider this a warning to upgrade/migrate your account to V2 if
  you have not done so yet.
- The 'Sign in with a BombSquad account' option is now simply 'Sign In' when
  that is the only option. So nice and tidy! When other options such as Google
  Play or Game Center are available it is now called 'Sign in with an email
  address'.
- The engine now supports signing in or creating email/password accounts in a
  pop-up web dialog to avoid taking users out of the app. This currently works
  on the native (not cmake) Mac build but will probably expand to others in the
  future.
- The `ba*.app.env.version` and `ba*.app.env.build_number` values are now
  `ba*.app.env.engine_version` and `ba*.app.env.engine_build_number`. At this
  point any functionality that cares about versions should be looking at engine
  version anyway. In the future we can add separate `app_version` and
  `app_build_number` values for spinoff apps, but in the case of `BombSquad` the
  app version/build is currently the same as the engine's so we don't need that
  just yet.
- Reworked the 'Enter Code' dialog into a 'Send Info' dialog. The `sendinfo`
  command is 99% of the reason for 'Enter Code' existing, so this simplifies
  things for that use case and hopefully clarifies its purpose so I can spend
  less time responding to app reviewers and more time improving the game.
- The `Network Testing` panel no longer requires being signed in (it just skips
  one test if not signed in).
- Took a pass through the engine and its servers to make things more ipv6
  friendly and prep for an eventual ipv6-only world (though ipv4 won't be going
  anywhere for a long time). The existing half-hearted state of ipv6 support was
  starting to cause problems when testing in certain ipv6-only environments, so
  it was time to clean it up.
- The engine will now establish its persistent v2-transport connections to
  regional servers using ipv6 when that is the fastest option based on ping
  tests.
- Improved the efficiency of the `connectivity` system which determines which
  regional ballistica server to establish a connection to (All V2 server
  communication goes through this connection). It now takes geography into
  account, so if it gets a low ping to a server in South America it won't try
  pinging Warsaw, etc. Set the env var `BA_DEBUG_LOG_CONNECTIVITY=1` if you want
  to watch it do it's thing and holler if you see any bad results.
- Servers can now provide their public ipv4 and ipv6 addresses in their configs.
  Previously, a server's address was always determined automatically based on
  how it connected to the master server, but this would only provide one of the
  two forms. Now it is possible to provide both.
- Spaz classes now have a `default_hitpoints` which makes customizing that
  easier (Thanks rabbitboom!)
- Added `docker-gui-release`, `docker-gui-debug`, `docker-server-release`, `docker-server-debug`, `docker-clean` and `docker-save` targets
  to Makefile.
- Fixed an issue in Assault where being teleported back to base with a sticky
  bomb stuck to you would do some crazy rubber-band-launching thing (Thanks
  vishal332008!)
- The `windows-debug` and `windows-release` Makefile targets should properly run
  the game again (these build the Windows version of the game from a WSL
  environment).
- WSL Windows builds are now more strict about their locations. Currently this
  means they must exist somewhere under /mnt/c/. It is turning out that a
  significant number of behavior workarounds (for file permission quirks, etc.)
  need to happen to keep these builds behaving, so I'd like to enforce as
  limited a set of conditions as possible to give us the best chance at
  succeeding there.
- Added a workaround for WSL Windows builds giving permission errors when staging asset
  files that already exist. Please holler if you are building with WSL and still
  running into any sort of errors, as I would love to make that path as reliable
  as possible.
- Fixed an issue where WSL Windows builds would re-extract everything from
  efrocache when anything in the cache-map changed (which is the case for most
  commits). Please holler if you are still seeing lots more 'Extracting:' lines
  when running builds after pulling small updates from git.
- Added github workflow for making docker image and sphinx docs nightly
- Added github workflow for making build release on tag creation
  
### 1.7.34 (build 21823, api 8, 2024-04-26)
- Bumped Python version from 3.11 to 3.12 for all builds and project tools. One
  of the things this means is that we can use `typing.override` instead of the
  `typing_extensions.override` version so the annoying requirement of installing
  `typing_extensions` first thing when setting up the repo introduced a few
  versions back is finally no longer a thing. I'll try to be careful to avoid
  falling back into that situation in the future.
- The project now maintains its own Python virtual environment in `.venv` where
  it automatically installs whatever Python packages it needs instead of asking
  the user to do so in their own environment. This should greatly simplify
  working with the project and keep tool versions more consistent for people.
  There will likely be some bugs related to this needing to be shaken out, so
  please holler if you run into any. Namely, most all Makefile targets will now
  need to depend on the `prereqs` target which ensures the virtual env is set
  up. A target that does not do so may error if run on a freshly cloned/cleaned
  repo, so holler if you run into such a thing.
- There is now a `config/requirements.txt` file which controls which pip
  packages are made available in the project's internal virtual environment.
  Note that this is only for tooling; the actual engine bundles a different
  minimal set of pip packages.
- Since `config/requirements.txt` now exists and pip stuff is handled
  automatically, stripped out the old manual pip requirement management stuff.
  This includes the `list_pip_reqs` and `get_pip_reqs` pcommands and the
  requirements list in `batools.build`.
- Some executable scripts such as `tools/pcommand` and `tools/bacloud` are now
  generated dynamically so that they always use the shiny new internal Python
  virtual-environment. This generation should happen automagically when you
  build `make` targets, but please holler if you run into a situation where it
  does not and you get errors.
- `_bascenev1.protocol_version()` now properly throws an exception if called
  while scene-v1 is not active.
- The `efro.dataclassio` system now supports `datetime.timedelta` values.
- Usage of `pcommandbatch` is now disabled by default. To enable it, set the env
  var `BA_PCOMMANDBATCH_ENABLE=1`. This is primarily due to rare sporadic
  failures I have observed or have been informed of, possibly involving socket
  exhaustion or other hard-to-debug OS conditions. For now I am still
  considering `pcommandbatch` supported and may continue to use it myself, but
  its speed gains may not be worth its added complexity indefinitely. As core
  counts keep increasing in the future, the time expense of spinning up a new
  Python process per pcommand decreases, making pcommandbatch less of a win.
  Please holler if you have any thoughts on this.
- Renamed the `prereqs` Makefile target to `env`. This is more concise and feels
  more accurate now that the target sets up things such as the Python virtual
  environment and generally gets the project environment ready to use.
- (build 21810) Fixed an issue where AppSubsystems could get inited multiple
  times (due to functools.cached_property no longer being thread-safe in Python
  3.12).
- The server config file is now in `toml` format instead of `yaml`. Python has
  built in support for reading `toml` as of 3.11 which means we don't have to
  bundle extra packages, and `toml` has more of a clean minimal design that
  works well for config files. Also I plan to use it for AssetPackage
  configuration stuff so this keeps things consistent.
- The server config can now be set to a `.json` file as an alternative to the
  default `.toml`. This can be handy when procedurally generating server
  configs. If no `--config` path is explicitly passed, it will look for
  `config.json` and `config.toml` in the same dir as the script in that order.
  
### 1.7.33 (build 21795, api 8, 2024-03-24)
- Stress test input-devices are now a bit smarter; they won't press any buttons
  while UIs are up (this could cause lots of chaos if it happened).
- Added a 'Show Demos When Idle' option in advanced settings. If enabled, the
  game will show gameplay demos (a slightly modified form of the stress test)
  periodically after sitting idle at the main menu for a bit. Like an old arcade
  game. I added this for an upcoming conference appearance but though people
  might like to enable it in other cases.
- Replays now have a play/pause button alongside the speed adjustment buttons
  (Thanks vishal332008!)
- Players now get points for killing bots with their own bombs by catching it
  and throwing it back at them. This is actually old logic but was disabled due
  to a logic flaw, but should be fixed now. (Thanks VinniTR!)
- Updated the 'Settings->Advanced->Enter Code' functionality to talk to the V2
  master server (V1 is still used as a fallback).
- Adopted the `@override` decorator in all Python code and set up Mypy to
  enforce its usage. Currently `override` comes from `typing_extensions` module
  but when we upgrade to Python 3.12 soon it will come from the standard
  `typing` module. This decorator should be familiar to users of other
  languages; I feel it helps keep logic more understandable and should help us
  catch problems where a base class changes or removes a method and child
  classes forget to adapt to the change.
- Added a reset button in the input mapping menu. (Thanks Temp!)
- Respawn icons now have dotted steps showing decimal progress to assist
  players on calculating when they are gonna respawn. (Thanks 3alTemp!)
- Replays now have rewind/fast-forward buttons!! (Thanks Dliwk, vishal332008!)
- Custom spaz "curse_time" values now work properly. (Thanks Temp!)
- Implemented `efro.dataclassio.IOMultiType` which will make my life a lot
  easier.
- Punches no longer physically affect powerup boxes which should make it easier
  to grab the powerup (Thanks VinniTR!).
- The 'Manual' party tab now supports entering IPv6 addresses (Thanks
  brostos!).
- Fixes a bug where Meteor Shower could make the game-end bell sound twice
  (Thanks 3alTemp!).
- Leaving the game or dying while touching your team's flag will no longer
  recover & return it indefinitely in a teams game of Capture the Flag. (Thanks
  3alTemp!)
- Added a server config setting for max players (not max clients) (Thanks
  EraOSBeta!)
- Added a UI for customizing Series Length in Teams and Points-to-Win in FFA
  (Thanks EraOSBeta!)
- Implemented HEX code support to the advanced color picker (Thanks 3alTemp!)
- Players leaving the game after getting hurt will now grant kills. (Thanks
  Temp!)
- Sphinx based Python documentation generation is now wired up (Thanks
  Loup-Garou911XD!)
- Renaming & overwriting existing profiles is no longer possible (Thanks Temp!)
- Cleaned up builds when running under WSL. Things like `make mypy` should now
  work correctly there, and it should now be possible to build and run either
  Linux or Windows builds there.
- Added an `allow_clear_button` arg to bauiv1.textwidget() which can be used to
  disable the 'X' button that clears editable text widgets.

### 1.7.32 (build 21741, api 8, 2023-12-20)
- Fixed a screen message that no one will ever see (Thanks vishal332008?...)
- Plugins window now displays 'No Plugins Installed' when no plugins are present
  (Thanks vishal332008!)
- Old messages are now displayed as soon as you press 'Unmute Chat' (Thanks
  vishal332008!)
- Added an 'Add to Favorites' entry to the party menu (Thanks vishal332008!)
- Now displays 'No Parties Added' in favorites tab if no favorites are present
  (Thanks vishal332008!)
- Now shows character icons in the profiles list window (Thanks vishal332008!)
- Added a Random button for names in the Player Profiles window (Thanks
  vishal332008!)
- Fixed a bug where no server is selected by default in the favorites tab
  (Thanks vishal332008!)
- Fixed a bug where no replay is selected by default in the watch tab (Thanks
  vishal332008!)
- Fixed a bug where no profile is selected by default in the profile tab (Thanks
  vishal332008!)
- Fixed a number of UI screens so that ugly window edges are no longer visible
  in corners on modern ultra wide phone displays.
- Added a `player_rejoin_cooldown` server config option. This defaults to 10
  seconds for servers but 0 for normal gui clients. This mechanism had been
  introduced recently to combat multiplayer fast-rejoin exploits and was set to
  10 seconds everywhere, but it could tend to be annoying for local single
  player play, dev testing, etc. Hopefully this strikes a good balance now.
- Removed the player-rejoin-cooldown mechanism from the C++ layer since it was
  redundant with the Python level one and didn't cover as many cases.
- Restored the behavior from before 1.7.28 where backgrounding the app would
  bring up the main menu and pause the action. Now it is implemented more
  cleanly however (an `on_app_active_changed()` call in the `AppMode` class).
  This means that it also applies to other platforms when the app reaches the
  'inactive' state; for instance when minimizing the window on the SDL build.

### 1.7.31 (build 21727, api 8, 2023-12-17)
- Added `bascenev1.get_connection_to_host_info_2()` which is an improved
  type-safe version of `bascenev1.get_connection_to_host_info()`.
- There is now a link to the official Discord server in the About section
  (thanks EraOSBeta!).
- Native stack traces now work on Android; woohoo! Should be very helpful for
  debugging.
- Added the concept of 'ui-operations' in the native layer to hopefully clear
  out the remaining double-window bugs. Basically, widgets used to schedule
  their payload commands to a future cycle of the event loop, meaning it was
  possible for commands that switched the main window to get scheduled twice
  before the first one ran (due to 2 key presses, etc), which could lead to all
  sorts of weirdness happening such as multiple windows popping up when one was
  intended. Now, however, such commands get scheduled to a current
  'ui-operation' and then run *almost* immediately, which should prevent such
  situations. Please holler if you run into any UI weirdness at this point.

### 1.7.30 (build 21697, api 8, 2023-12-08)
- Continued work on the big 1.7.28 update.
- Got the Android version back up and running. There's been lots of cleanup and
  simplification on the Android layer, cleaning out years of cruft. This should
  put things in a better more maintainable place, but there will probably be
  some bugs to iron out, so please holler if you run into any.
- Minimum supported Android version has been bumped from 5.0 to 6.0. Some
  upcoming tech such as ASTC textures will likely not be well supported on such
  old devices, so I think it is better to leave them running an older version
  that performs decently instead of a newer version that performs poorly. And
  letting go of old Android versions lets us better support new ones.
- Android version now uses the 'Oboe' library as an audio back-end instead of
  OpenSL. This should result in better behaving audio in general. Please holler
  if you experience otherwise.
- Bundled Android Python has been bumped to version 3.11.6.
- Android app suspend behavior has been revamped. The app should stay running
  more often and be quicker to respond when dialogs or other activities
  temporarily pop up in front of it. This also allows it to continue playing
  music over other activities such as Google Play Games
  Achievements/Leaderboards screens. Please holler if you run into strange side
  effects such as the app continuing to play audio when it should not be.
- Modernized the Android fullscreen setup code when running in Android 11 or
  newer. The game should now use the whole screen area, including the area
  around notches or camera cutouts. Please holler if you are seeing any problems
  related to this.
- (build 21626) Fixed a bug where click/tap locations were incorrect on some
  builds when tv-border was on (Thanks for the heads-up Loup(Dliwk's fan)!).
- (build 21631) Fixes an issue where '^^^^^^^^^^^^^' lines in stack traces could
  get chopped into tiny bits each on their own line in the dev console.
- Hopefully finally fixed a longstanding issue where obscure cases such as
  multiple key presses simultaneously could cause multiple main menu windows to
  pop up. Please holler if you still see this problem happening anywhere. Also
  added a few related safety checks and warnings to help ensure UI code is free
  from such problems going forward. To make sure your custom UIs are behaving
  well in this system, do the following two things: 1) any time you call
  `set_main_menu_window()`, pass your existing main menu window root widget as
  `from_window`. 2) In any call that can lead to you switching the main menu
  window, check if your root widget is dead or transitioning out first and abort
  if it is. See any window in `ui_v1_lib` for examples.
- (build 21691) Fixed a bug causing touches to not register in some cases on
  newer Android devices. (Huge thanks to JESWIN A J for helping me track that
  down!).
- Temporarily removed the pause-the-game-when-backgrounded behavior for locally
  hosted games, mainly due to the code being hacky. Will try to restore this
  functionality in a cleaner way soon.

### 1.7.29 (build 21619, api 8, 2023-11-21)

- Simply continued work on the big 1.7.28 update. I was able to finally start
  updating the Mac App Store version of the game again (it had been stuck at
  1.4!), and it turns out that Apple AppStore submissions require the version
  number to increase each time and not just the build number, so we may start
  seeing more minor version number bumps for that reason.
- Windows builds should now die with a clear error when the OpenGL version is
  too old (OpenGL 3.0 or newer is required). Previously they could die with more
  cryptic error messages such as "OpenGL function 'glActiveTexture2D' not
  found".

### 1.7.28 (build 21599, api 8, 2023-11-16)

- Turning off ticket continues on all platforms. I'll be moving the game towards
  a new monetization scheme mostly based on cosmetics and this has always felt a
  bit ugly pay-to-win to me, so it's time for it to go. Note that the
  functionality is still in there if anyone wants to support it in mods.
- Massively cleaned up code related to rendering and window systems (OpenGL,
  SDL, etc). This code had been growing into a nasty tangle for 15 years
  attempting to support various old/hacked versions of SDL, etc. I ripped out
  huge chunks of it and put back still-relevant pieces in a much more cleanly
  designed way. This should put us in a much better place for supporting various
  platforms and making graphical improvements going forward.
  `ballistica/base/app_adapter/app_adapter_sdl.cc` is an example of the now
  nicely implemented system.
- The engine now requires OpenGL 3.0 or newer on desktop and OpenGL ES 3.0 or
  newer on mobile. This means we're cutting off a few percent of old devices on
  Android that only support ES 2, but ES 3 has been out for 10 years now so I
  feel it is time. As mentioned above, this allows massively cleaning up the
  graphics code which means we can start to improve it. Ideally now the GL
  renderer can be abstracted a bit more which will make the process of writing
  other renderers easier.
- Removed gamma controls. These were only active on the old Mac builds anyway
  and are being removed from the upcoming SDL3, so if we want this sort of thing
  we should do it through shading in the renderer now.
- Implemented both vsync and max-fps for the SDL build of the game. This means
  you can finally take advantage of that nice high frame rate monitor on your
  PC. Vsync supports 'Disable', 'Enabled' and 'Auto', which attempts to use
  'adaptive' vsync if available, and no vsync otherwise.
- Spent some time tuning a few frame-timing mechanisms, so motion in the game
  should appear significantly smoother in some cases. Please let me know if it
  ever appears *less* smooth than before or if you see what looks like weird
  speed changes which could be timing problems.
- Debug speed adjustments are now Ctrl-plus or Ctrl-minus instead of just plus
  or minus. This makes these safer in case we want to enable them in regular
  builds at some point.
- Flashing things in the game (powerups about to disappear, etc.) now flash at a
  consistent rate even on high frame rate setups.
- Renamed Console to DevConsole, and added an option under advanced settings to
  always show a 'dev' button onscreen which can be used to toggle it. The
  backtick key still works also for anyone with a keyboard. I plan to add more
  functionality besides just the Python console to the dev-console, and perhaps
  improve the Python console a bit too (add support for on-screen keyboards,
  etc.)
- The in-app Python console text is now sized up on phone and tablet devices,
  and is generally a bit larger everywhere.
- Added an API to define DevConsole tabs via Python. Currently it supports basic
  buttons and text, but should be easy to expand to whatever we need. See
  `babase/_devconsole.py`. It should be easy to define new tabs via plugins/etc.
- Cleaned up onscreen keyboard support and generalized it to make it possible to
  support other things besides widgets and to make it easier to implement on
  other platforms.
- Added onscreen keyboard support to the in-app Python console and added an Exec
  button to allow execing it without a return key on a keyboard. The cloud
  console is probably still a better way to go for most people but this makes at
  least simple things possible without an internet connection for most Android
  users.
- Pressing esc when the DevConsole is in its small form now dismisses it
  instead of toggling it to its large form.
- Added some high level functionality for copying and deleting feature-sets to
  the `spinoff` tool. For example, to create your own `poo` feature-set based on
  the existing `template_fs` one, do `tools/spinoff fset-copy template_fs poo`.
  Then do `make update` and `make cmake` to build and run the app, and from
  within it you should be able to do `import bapoo` to get at your nice shiny
  poo feature-set. When you are done playing around, you can do `tools/spinoff
  fset-delete poo` to blow away any traces of it.
- Public builds now properly reconstruct the CMakeLists.txt file for project
  changes.
- Efrocache now supports a starter-archive when building server builds. This
  means that if you do something like `make clean; make
  prefab-server-release-build` you should see just a few file downloads
  happening instead of the hundreds that would happen before, which should be
  significantly faster & more efficient.
- Updated internal Python builds for Apple & iOS to 3.11.5, and updated a few
  dependent libraries as well (OpenSSL bumped from 3.0.8 to 3.0.10, etc.).
- Cleaned up the `babase.quit()` mechanism. The default for the 'soft' arg is
  now true, so a vanilla `babase.quit()` should now be a good citizen on mobile
  platforms. Also added the `g_base->QuitApp()` call which gives the C++ layer
  a high level equivalent to the Python call.
- (build 21326) Fixed an uninitialized variable that could cause V1 networking
  to fail in some builds/runs (thanks Rikko for the heads-up).
- (build 21327) Fixed an issue that could cause the app to pause for 3 seconds
  at shutdown.
- Worked to improve sanity checking on C++ RenderComponents in debug builds to
  make it easier to use and avoid sending broken commands to the renderer. Some
  specifics follow.
- RenderComponents (C++ layer) no longer need an explicit Submit() at the end;
  if one goes out of scope not in the submitted state it will implicitly run a
  submit. Hopefully this will encourage concise code where RenderComponents are
  defined in tight scopes.
- RenderComponents now have a ScopedTransform() call which can be used to push
  and pop the transform stack based on C++ scoping instead of the old
  PushTransform/PopTransform. This should make it harder to accidentally break
  the transform stack with unbalanced components.
- Fixes an issue related to incorrect die-message handling by hockey pucks (fix
  #617). Thanks EraOSBeta!
- Fixes an issue where clamped player-name would display incorrectly if extra
  spaces are present (fix #618). Thanks vishal332008!
- Fixes an issue where King of the Hill scoreboard did not display immediately
  (fix #614). Thanks heLlow-step-sis!
- Fixes an issue where CTF flag return counters could get stuck (fix #584).
  Thanks SoK05 and Dliwk!
- In cases where there's no browser available, the v2 account sign-in URL can
  now be tapped to copy it (Thanks vishal332008!).
- Removed the bits from `babase.app` that were deprecated in 1.7.27. I know that
  was only one version ago, but this version has been cooking for a while now.
- Visual Studio projects have been updated to target Visual Studio 2022.
- Now that all our compilers support it, updating from the C++17 standard to
  C++20. This will allow a few useful things such as being able to pack 8 bools
  into 1 byte.
- Created a custom icon for BallisticaKit (previously it was just the BombSquad
  icon with an ugly 'C' on it). BombSquad itself will still have the BombSquad
  icon.
- Changed `AppState.NOT_RUNNING` to `AppState.NOT_STARTED` since not-running
  could be confused with a state such as paused.
- Changed the general app-state terms 'pause' and 'resume' to 'suspend' and
  'unsuspend'. (note this has nothing to do with pausing in the game which is
  still called pausing). The suspend state is used by mobile versions when
  backgrounded and basically stops all activity in the app. I may later add
  another state called 'paused' for when the app is still running but there is
  an OS dialog or ad or something in front of it. Though perhaps another term
  would be better to avoid confusion with the act of pausing in the game
  ('inactive' maybe?).
- Fixed an issue that could cause a few seconds delay when shutting down if
  internet access is unavailable.
- Generalized the UI system to accept a delegate object, of which UIV1 is now
  one. In the future this will allow plugging in UIV2 instead or other UI
  systems.
- Headless builds now plug in *no* ui delegate instead of UIV1, so one must
  avoid calling UI code from servers now. This should reduce server resource
  usage a bit. Please holler if this causes non-trivial problems. In general,
  code that brings up UI from gameplay contexts should check the value of
  `ba.app.env.headless` and avoid doing so when that is True.
- Cleaned up quit behavior a bit more. The `babase.quit()` call now takes a
  single `babase.QuitType` enum instead of the multiple bool options it took
  before. It also takes a `confirm` bool arg which allows it to be used to bring
  up a confirm dialog.
- Clicking on a window close button to quit no longer brings up a confirm dialog
  and instead quits immediately (though with a proper graceful shutdown and a
  lovely little fade).
- Camera shake is now supported in network games and replays. Somehow I didn't
  notice that was missing for years. The downside is this requires a server to
  be hosting protocol 35, which cuts off support for 1.4 clients. So for now I
  am keeping the default at 33. Once there a fewer 1.4 clients around we can
  consider changing this (if everything hasn't moved to SceneV2 by then).
- Added a server option to set the hosting protocol for servers who might want
  to allow camera shake (or other minor features/fixes) that don't work in the
  default protocol 33. See `protocol_version` in `config.yaml`. Just remember
  that you will be cutting off support for older clients if you use 35.
- Fixed a bug with screen-messages animating off screen too fast when frame
  rates are high.
- Added a proper graceful shutdown process for the audio server. This should
  result in fewer ugly pops and warning messages when the app is quit.
- Tidied up some keyboard shortcuts to be more platform-appropriate. For
  example, toggling fullscreen on Windows is now Alt+Enter or F11.
- Fancy rebuilt Mac build should now automatically sync its frame rate to the
  display its running on (using CVDisplayLinks, not VSync).
- Mac build is now relying solely on Apple's Game Controller Framework, which
  seems pretty awesome these days. It should support most stuff SDL does and
  with less configuring involved. Please holler if you come across something
  that doesn't work.
- Mac build is also now using the Game Controller Framework to handle keyboard
  events. This should better handle things like modifier keys and also will
  allow us to use that exact same code on the iPad/iPhone version.
- OS key repeat events are no longer passed through the engine. This means that
  any time we want repeating behavior, such as holding an arrow key to move
  through UI elements, we will need to wire it up ourselves. We already do this
  for things like game controllers however, so this is more consistent in a way.
- Dev console no longer claims key events unless the Python tab is showing and
  there is a hardware keyboard attached. This allows showing dev console tabs
  above gameplay without interfering with it.
- Added clipboard paste support to the dev console python terminal.
- Added various text editing functionality to the dev console python terminal
  (cursor movement, deleting chars and words, etc.)
- Internal on-screen-keyboard now has a cancel button (thanks vishal332008!)
- Public servers list now shows 'No servers found' if there are no servers to
  show instead of just remaining mysteriously blank (thanks vishal332008!)
- Players are now prevented from rejoining a session for 10 seconds after they
  leave to prevent game exploits. Note this is different than the existing
  system that prevents joining a *party* for 10 seconds; this covers people
  who never leave the party (Thanks EraOSBeta!).
- Fixes an issue where servers could be crashed by flooding them with join
  requests (Thanks for the heads-up Era!).
- The engine will now ignore empty device config dicts and fall back to
  defaults; these could theoretically happen if device config code fails
  somewhere and it previously would leave the device mysteriously inoperable.
- The game will now show <unset> for controls with no bindings in the in-game
  guide and controller/keyboard config screens.
- Fixed a crash that could occur if SDL couldn't find a name for connected
  joystick.
- Simplified the app's handling of broken config files. Previously it would do
  various complex things such as offering to edit the broken config on desktop
  builds, avoiding overwriting broken configs, and automatically loading
  previous configs. Now, if it finds a broken config, it will simply back it up
  to a .broken file, log an error message, and then start up normally with a
  default config. This way, things are more consistent across platforms, and
  technical users can still fix and restore their old configs. Note that the app
  still also writes .prev configs for extra security, though it no longer uses
  them for anything itself.
- Converted more internal engine time values from milliseconds to microseconds,
  including things like the internal EventLoop timeline. Please holler if you
  notice anything running 1000x too fast or slow. In general my strategy going
  forward is to use microseconds for exact internal time values but to mostly
  expose float seconds to the user, especially on the Python layer. There were
  starting to be a few cases were integer milliseconds was not enough precision
  for internal values. For instance, if we run with unclamped framerates and hit
  several hundred FPS, milliseconds per frame would drop to 0 which caused some
  problems. Note that scenev1 will be remaining on milliseconds internally for
  compatibility reasons. Scenev2 should move to microseconds though.
- The V2 account id for the signed in account is now available at
  `ba*.app.plus.accounts.primary.accountid` (alongside some other existing
  account info).
- (build 21585) Fixed an issue where some navigation key presses were getting
  incorrectly absorbed by text widgets. (Thanks for the heads-up Temp!)
- (build 21585) Fixed an issue where texture quality changes would not take
  effect until next launch.
- Added a 'glow_type' arg to `bauiv1.textwidget()` to adjust the glow used when
  the text is selected. The default is 'gradient' but there is now a 'uniform'
  option which may look better in some circumstances.

### 1.7.27 (build 21282, api 8, 2023-08-30)

- Fixed a rare crash that could occur if the app shuts down while a background
  thread is making a web request. The app will now try to wait for any such
  attempts to complete.
- Fixed a bug where PlayerSpaz used `bs.apptime()` where `bs.time()` should have
  been used (thanks EraOSBeta!).
- Added `babase.app.env` which is a type-friendly object containing various
  environment/runtime values. Values directly under `app` such as
  `babase.app.debug_build` will either be consolidated here or moved to classic
  if they are considered deprecated.
- Started using Python's `warnings` module to announce deprecations, and turned
  on deprecation warnings for the release build (by default in Python they are
  mostly only on for debug builds). This way, when making minor changes, I can
  keep old code paths intact for a few versions and warn modders that they
  should transition to new code paths before the old ones disappear. I'd prefer
  to avoid incrementing api-version again if at all possible since that is such
  a dramatic event, so this alternative will hopefully allow gently evolving
  some things without too much breakage.
- Following up on the above two entries, several attributes under `babase.app`
  have been relocated to `babase.app.env` and the originals have been given
  deprecation warnings and will disappear sometime soon. This includes
  `build_number`, `device_name`, `config_file_path`, `version`, `debug_build`,
  `test_build`, `data_directory`, `python_directory_user`,
  `python_directory_app`, `python_directory_app_site`, `api_version`, `on_tv`,
  `vr_mode`, `toolbar_test`, `arcade_mode`, `headless_mode`, `demo_mode`, and
  `protocol_version`.
- Reverting the Android keyboard changes from 1.7.26, as I've received a few
  reports of bluetooth game controllers now thinking they are keyboards. I'm
  thinking I'll have to bite the bullet and implement something that asks the
  user what the thing is to solve cases like that.
- Added tags allowing easily stripping code out of spinoff projects when a
  specific feature-set is not present. For example, to strip lines out when
  feature-set 'foo' is not present, surround them by lines containing
  `__SPINOFF_REQUIRE_FOO_BEGIN__` and `__SPINOFF_REQUIRE_FOO_END__`.

### 1.7.26 (build 21259, api 8, 2023-08-29)

- Android should now be better at detecting hardware keyboards (you will see
  'Configure Keyboard' and 'Configure Keyboard P2' buttons under
  Settings->Controllers if a hardware keyboard is detected). It can be a bit
  tricky distinguishing between gamepad type devices and keyboards on Android,
  so please holler if you have a gamepad that now suddenly thinks it is a
  keyboard or anything like that.
- Various general improvements to the pcommand (project command) system.
- Modules containing pcommand functions are now named with an 's' - so
  `pcommands.py` instead of `pcommand.py`. `pcommand.py` in efrotools is now
  solely related to the functioning of the pcommand system.
- Implemented the `pcommandbatch` system, which is a way to run pcommands using
  a simple local server/client architecture, and set up key build targets to use
  that by default instead of regular pcommand. In some cases, such as when
  assembling build assets, this can speed things up by 5x or so. Run `make
  pcommandbatch_speed_test` to see what the theoretical biggest speedup is on
  your system. If you run into any problems that seem to be related to this, you
  can disable it by setting env var `BA_PCOMMANDBATCH_DISABLE=1` which will
  cause everything to go use regular old pcommand. See docs in
  `tools/efrotools/pcommandbatch.py` for more info.
- Renamed the various `App` C++ classes to `AppAdapter` which better represents
  their current intended role. They are not a general interface to app
  functionality, but rather adapt the app to a particular paradigm or api (VR,
  Headless, SDL GUI, etc.). Also am trying to move any functionality out of
  those classes that does not fit that definition.
- Started cleaning up the app shutdown process. This will allow the app to
  gracefully run tasks such as syncing account data to the cloud or disk or
  properly closing the audio system when shutting down. It also means there
  should be more consistent use of the 'Quit?' confirm window. Please holler if
  you see any odd behavior when trying to quit the app.
- Unix TERM signal now triggers graceful app shutdown.
- Added `app.add_shutdown_task()` to register coroutines to be run as part of
  shutdown.
- Removed `app.iircade_mode`. RIP iiRcade :(.
- Changed `AppState.INITIAL` to `AppState.NOT_RUNNING`, added a
  `AppState.NATIVE_BOOTSTRAPPING`, and changed `AppState.LAUNCHING` to
  `AppState.INITING`. These better describe what the app is actually doing while
  in those states.

### 1.7.25 (build 21211, api 8, 2023-08-03)

- Fixed an issue where the main thread was holding the Python GIL by default in
  monolithic builds with environment-managed event loops. This theoretically
  could have lead to stuttery performance in the Android or Mac builds.
- Did a bit of cleanup on `baenv.py` in preparation for some additional setup it
  will soon be doing to give users more control over logging.
- `getconfig` and `setconfig` in `efrotools` are now `getprojectconfig` and
  `setprojectconfig` (to reflect the file name changes that happened in 1.7.20).
- The efrocache system (how assets and prebuilt binaries are downloaded during
  builds) now uses a `efrocache_repository_url` value in
  `config/projectconfig.json` instead of being hard-coded to my server. This
  makes it possible to theoretically set up mirror servers. I currently keep the
  cache pruned to the last few months worth of files but theoretically someone
  could set up a server that never gets pruned and contains all history from now
  until forever. Efrocache is basically just a big pile of files organized by
  their hashes (see `tools/efrotools/efrocache.py` for details).
- On a related note, the .efrocachemap file now just contains hashes instead of
  full urls per file (which were based on those hashes anyway).
- The default efrocache file location is now `.cache/efrocache` instead of
  `.efrocache`. Feel free to blow away any `.efrocache` dir if you still have
  one (or move it to the new path to avoid having to download things again).
- It is now possible to set an `EFROCACHE_DIR` env var to tell efrocache to
  store its local files somewhere besides the per-project default of
  `.cache/efrocache`. This can save a lot of download time if you want to share
  it between multiple repos or are doing full cleans/rebuilds a lot (if it is
  outside the project dir it won't get blown away during cleans). Efrocache dirs
  are universal (again its just a big pile of files organized by hash) so there
  should be no issues sharing cache dirs. Another nice side effect of
  maintaining a single local efrocache dir is that anything you've ever built
  will still be buildable; otherwise if your build tries to download very old
  cache files they may no longer be available on my efrocache server.
- Hardened efrocache code a bit so that failures during downloads or
  decompresses are less likely to leave problematic half-made stuff lying
  around. Namely, things are now always downloaded or decompressed into temp
  dirs and only moved into their final locations once that completes
  successfully. Its extra important to be safe now that its possible to share
  local efrocache dirs between projects or otherwise keep them around longer.
- Experimenting a bit with adding support for
  [Pyright](https://github.com/microsoft/pyright) type-checking. This could
  theoretically allow for a really great interactive Python environment in
  Visual Studio Code (and potentially other editors), so am seeing if it is
  worth officially supporting in addition to or as a replacement for Mypy. See
  `tools/pcommand pyright`

### 1.7.24 (build 21199, api 8, 2023-07-27)

- Fixed an issue where respawn icons could disappear in epic mode (Thanks for
  the heads-up Rikko!)
- The `BA_ENABLE_IRONY_BUILD_DB` optional build env-var is now
  `BA_ENABLE_COMPILE_COMMANDS_DB` since this same functionality can be used by
  clangd or other tools. Originally I was using it for Irony for Emacs; hence
  the old name.
- Due to the cleanup done in 1.7.20, it is now possible to build and run
  Ballistica as a 'pure' Python app consisting of binary Python modules loaded
  by a standard Python interpreter. This new build style is referred to as
  'modular'. The traditional form of the app, where we bootstrap Python
  ourselves inside a standalone binary, is called 'monolithic'. To build and run
  Ballistica in modular form, you can do `make cmake-modular` or `make
  cmake-modular-server`. This should make it easier to use certain things like
  Python debuggers with Ballistica. While I expect most builds of the engine to
  remain monolithic, this may become the default for certain situations such as
  server builds or possibly Linux builds if it seems beneficial. We'll see.
  Modular mode should work on Linux and Mac currently; other platforms remain
  monolithic-only for now.
- Changed builds such as `cmake` and `cmake-server` to be more like the new
  `cmake-monolithic-*` builds; there is now a `staged` dir that built binaries
  are symlinked into instead of just dumping a `ba_data` into the cmake build
  dir. This keeps things a bit cleaner with fewer build-related files
  interspersed with the stuff that Ballistica expects to be there at runtime.
  This also allows an elegant `-dist` flag to be used with the staging command
  to copy files instead of symlinking them.
- Changed path wrangling a bit in baenv.py. All ballistica Python paths
  (including python-site-packages) are now placed *before* any other existing
  Python paths. This should provide a more consistent environment and means
  Ballistica will always use its own version of things like yaml or certifi or
  typing_extensions instead of ones the user has installed via pip. Holler if
  you run into any problems because of this and we can make an option to use the
  old behavior where Ballistica's app and site paths get placed at the end.
- It is now possible to manually run the app loop even on monolithic builds;
  just do `PYTHONPATH=ba_data/python ./ballisticakit -c "import baenv;
  baenv.configure(); import babase; babase.app.run()"`. This is basically the
  same thing modular builds are doing except that they use a regular Python
  interpreter instead of the ballisticakit binary.
- Cleaned up the `tools/pcommand stage_assets` command. It now always expects a
  separate `-debug` or `-release` arg. So old commands such as `tools/pcommand
  stage_assets -win-Win32-Debug .` now look like `tools/pcommand stage_assets
  -win-Win32 -debug .`. Please holler if you run into any broken asset-staging
  calls in the Makefile/etc.
- `FeatureSet.has_native_python_module` has been renamed to
  `FeatureSet.has_python_binary_module` to be more consistently with related
  functionality.
- Renamed `stage_assets` to `stage_build` and the module it lives in from
  `assetstaging` to simply `staging`. The staging stuff now covers more things
  than simply asset files so this is a more accurate name.
- Added `babase.fatal_error()`. Mod code should generally never use this, but it
  can be useful for core engine code to directly and clearly point out problems
  that cannot be recovered from (Exceptions in such cases can tend to be
  'handled' which leads to a broken or crashing app).

### 1.7.23 (build 21178, api 8, 2023-07-19)

- Network security improvements. (Thanks Dliwk!)
- You can now double click a chat message to copy it. (Thanks Vishal332008!)
- Android's audio library has been updated to the latest version (and is now
  much easier for me to keep up to date). Please holler if you run into anything
  wonky related to audio.
- Updated our C json handling code to the latest version of cJSON. Should fix
  some potential vulnerabilities.

### 1.7.22 (build 21165, api 8, 2023-07-11)

- Fixed a very rare race condition when launching threads or sending synchronous
  cross-thread messages. This was manifesting as one out of several thousand
  server launches hanging.
- Changed health box from a red cross to a green cross (turns out games aren't
  supposed to use red crosses for health for legal reasons).
- Cleaned up how Android sets up its OpenGL context; it should be more flexible
  with the config formats it allows may might fix rare cases of graphics setup
  failing (such as with latest Android emulator for me). Please holler if you
  see any graphics wonkiness with this update.
- Added SoK's explodinary icon to the game's custom text drawing because SoK is
  awesome.
- (build 21165) Fixed an issue on Android that could lead to crashes if device
  events occurred very early at launch (button presses, joystick movement, etc.)

### 1.7.21 (build 21152, api 8, 2023-06-27)

- Fixed an issue where server builds would not always include collision meshes.
- Upgraded Python to 3.11.4 on Android builds.
- Cleaned up the language subsystem and the process for applying app-config
  changes a bit. Please holler if you see weirdness in either.
- QR code textures now have a soft limit of 64 bytes for their addresses.
  Warnings will be given for longer addresses up to 96 bytes at which point qr
  code creation will fail. This should keep the images reasonably readable and
  avoids a crash that could occur when more data was provided than could
  physically fit in the qr code.
- `PotentialPlugin` has been renamed to `PluginSpec` and the list of them
  renamed from `babase.app.plugins.potential_plugins` to
  `babase.app.plugins.plugin_specs`.
- Added a simpler warning message when plugins are found that need to be updated
  for the new api version.
- Previously, the app would only check api version on plugins when initially
  registering them. This meant that once a plugin was enabled, the app would
  always try to load it even if api version stopped matching. This has been
  corrected; now if the api version doesn't match it will never be loaded.
- Fixed an error where plugins nested more than one level such as
  `mypackage.myplugin.MyPlugin` would fail to load.
- Removed the `display_name` attr from the `PluginSpec` class, as it was simply
  set to `class_path`. It seems that referring to plugins simply by their
  class-paths is a reasonable system for now.
- Added `enabled`, `loadable`, `attempted_load` and `plugin` attrs to the
  `PluginSpec` class. This should make it easier to interact with the overall
  app plugin situation without having to do hacky raw config wrangling.
- Plugins should now show up more sensibly in the plugins UI in some cases. For
  example, a plugin which was previously loading but no longer is after an
  api-version change will still show up in the list as red instead of not
  showing up at all.

### 1.7.20 (build 21140, api 8, 2023-06-22)

- This seems like a good time for a `refactoring` release in anticipation of
  changes coming in 1.8. Basically this means that a lot of things will be
  getting moved or renamed, though their actual functionality should remain
  mostly the same. This will allow modders to prepare for some of what is coming
  in 1.8 without having to worry about functionality changing also. Hopefully
  this will be easier than dumping everything at once when 1.8.0 drops.
- Bumped api-version from 7 to 8. There will be enough breaking changes here
  that I think it's a good thing to force modders to explicitly check/update
  their stuff.
- Started work on the `ba.app.components` subsystem which will be used by
  different app-modes, plugins, etc. to override various app functionality.
- Removed telnet support. This never worked great, has been disabled in server
  builds for a while now, and cloud console mostly eliminates its use case.
- Added the `baclassic` package. As more modern stuff like app-modes,
  squads-mode, and scene-versions start to come online, code specific to more
  hard-coded classic ways of doing things will get migrated here to keep things
  clean and maintainable. Though there are no plans to remove classic
  functionality from the game anytime soon, this functionality may become
  unavailable in some contexts such as when modding cloud servers.
- Added a `baclassic.ClassicSubsystem` singleton accessible as `ba.app.classic`.
  Various older bits from `ba.app` and elsewhere will start to be migrated
  there. Note that the value for `ba.app.classic` can be None if classic is not
  present, so code should try to handle that case cleanly when possible.
- Moved a number of attributes and methods from `ba.app` to `ba.app.classic`.
  This includes things like `spaz_appearances`, `campaigns`, and `maps`.
- `ba.app.accounts_v1` is now `ba.app.classic.accounts`.
- `ba.app.accounts_v2` is now `ba.app.accounts`. Going forward, most all account
  functionality should go through this native v2 stuff.
- 'Model' and 'CollideModel' are now known as 'Mesh' and 'CollisionMesh'
  respectively. I've been wanting to make this change for a while since that
  more accurately describes what is currently stored in a .bob/.cob file. I
  would like to reserve the term 'Model' for use in the future; probably for
  something that can represent multiple meshes, collision-meshes, shading, etc.
  wrapped up into a single unit. To update your code for this change, just
  search for all variations of 'model', 'Model', 'collide_model', '
  CollideModel', etc. and replace them with the equivalent ' Mesh' or
  'CollisionMesh' forms. There should be no remaining uses of 'model' in
  ballistica currently so you should be able to track everything down this way.
- Added the `bascenev1` package. Scene-versions are a major upcoming feature in
  1.8 which for the first time will allow us to make substantial additions and
  changes to low-level game-related types such as nodes, models, and textures
  without breaking backwards compatibility. (bascenev2, etc.) The first step of
  this process will be to move all existing gameplay types into `bascenev1`. So
  instead of looking like: `import ba; ba.newnode()`, gameplay code might look
  more like `import bascenev1 as bs; bs.newnode()` (Wheeee 'bs' is back!).
- Added the `bauiv1` package. This contains all of the existing user-interface
  functionality. Similar to `bascenev1`, most existing UI code now uses the
  convention `import bauiv1 as bui`. This versioning will allow us to evolve
  nicer UI systems in the future (bauiv2, etc.) while keeping existing UIs
  functional.
- Many common bits from `ba` are now available from `bascenev1` and/or `bauiv1`.
  For instance, `bascenev1.app` and `bauiv1.app` are the same as `ba.app`. The
  goal is that most gameplay related modules should only need to import
  `bascenev1` and most UI related modules only `bauiv1` to keep things as simple
  as possible. The `ba` package is now mainly a common repository of
  functionality for these client-facing packages to pull from and should not
  often need to be used directly.
- There is no longer a 'ui' context. Previously, lots of common functionality
  would differ in behavior when executed under the 'ui' context. For example,
  `ba.screenmessage()` under the 'ui' context would simply print to the local
  device's screen, whereas when called under a game hosting context it would
  result in messages sent to all game clients. Now, however, there are instead
  unique versions for gameplay (`bascenev1.screenmessage()`) and ui
  (`bauiv1.screenmessage()`). These versions may differ in arguments and
  functionality; see docs for details. In general, the `ui` versions no longer
  care what context they are running under; their results will always just apply
  to the local device.
- The `ba.Context` class has been reworked a bit and is now `ba.ContextRef` to
  more accurately describe what it actually is. The default constructor
  (`ba.ContextRef()`) will grab a reference to the current context. To get a
  context-ref pointing to *no* context, do `ba.ContextRef.empty()`. UI stuff
  will now insist on being run with no context set. To get references to
  Activity/Session contexts, use the context() methods they provide.
- The following have been split into `bascenev1` and `bauiv1` versions:
  `screenmessage()`, `gettexture()`, `getsound()`, `getmesh()`,
  `getcollisionmesh()`, `getdata()`.
- The `_bainternal` module (the closed source parts of the app) is now the
  `baplus` package. There were too many things with 'internal' in the name and
  it was starting to get confusing. Also, the goal is for this to be an optional
  thing at some point and I feel 'plus' better fits that role; ' internal'
  sounds like something that is always required.
- Added the general concept of 'feature-sets' to the build system. A feature-set
  consists of a high level subset of the app source that can be included or
  excluded for different builds. The current list of feature-sets is `scene_v1`,
  `ui_v1`, `classic`, and `plus`. Tests are being added to ensure that
  feature-sets remain cleanly independent of eachother and also that the app can
  be built and run without *any* feature-sets present. Stay tuned for more info
  as things evolve, but the general idea is that feature-sets will allow us to
  isolate and test new functionality in an efficient way and also will allow
  'spinoff' projects to strip out parts of the app they don't need or add in new
  custom parts on the top of the base set. Modders interested in ' total
  conversions' may want to keep an eye on this.
- There is no longer a standalone `ba.playsound()` function. Both ui-sounds (
  acquired via `bauiv1.getsound()` and scene-sounds (acquired via
  `bascenev1.getsound()`) now have a play() method on them for this purpose. So
  just search for any instances of 'playsound' in your code and change stuff
  like `ba.playsound(ba.getsound('error'))` to `bs.getsound('error').play()`.
  Playing sounds in timers is now especially nicer looking; instead of
  `ba.timer(1.0, ba.Call(ba.playsound, my_sound))` you can now simply do
  `bs.timer(1.0, my_sound.play)`
- Since time functionality needs to be split between ui and scene versions
  anyway, I'm taking the opportunity to revise ballistica's time concepts. I
  revamped these in 1.5, and, after working with them for a few years, I feel
  that having a single time(), timer(), and Timer() call with a variety of
  arguments influencing behavior is unwieldy, so I'll be splitting things out
  into a few separate and simplified versions. Details follow.
- There is now the concept of 'app-time'. This was previously called '
  real-time'. It is basically time that has elapsed while the app is actively
  running. It never jumps ahead or goes backwards and it stops progressing while
  the app is suspended (which is why I feel the term 'real-time' was a bit
  misleading).
- `ballistica::GetRealTime()` in the C++ layer is now
  `ballistica::GetAppTimeMillisecs()`.
- App-time is now stored internally in microseconds instead of milliseconds, and
  there is a `ballistica::GetAppTimeMicrosecs()` call to retrieve the full
  resolution value.
- A number of calls, including the various time/timer functions listed below,
  now always accept time as float seconds and no longer accept a ba.TimeFormat
  value to do otherwise. TimeFormat was basically a way to transition elegantly
  from milliseconds to seconds everywhere, but it has been long enough now that
  we should simplify things. If you are passing
  timeformat=ba.TimeFormat.MILLISECONDS anywhere, simply divide your value by
  1000 now instead to make it seconds.
- In Python there is now an `apptime()` function to get current app-time in
  seconds, an `apptimer()` function to set a timer based on app-time, and an
  `AppTimer()` class to get an adjustable/cancelable timer. There is also an
  `AppTime` type which is technically just float but which can be used by
  type-checkers to keep these time values from being accidentally mixed with
  others. All of these are available in `ba`, `bauiv1`, and `bascenev1`.
- There is now the concept of `display-time` which is a value that progresses
  *mostly* at the same speed as app-time, but in a way that tries to advance at
  a constant rate per local frame drawn, which is useful for visual purposes
  such as UI animations. Trying to instead use app-time in these situations may
  lead to visual jitters since actual times between frame draws may not always
  be constant. Display-time avoids this problem, trading off technical time
  accuracy for visual smoothness. Be aware that display-time updates may be very
  sparse (like 10 per second) if the app is running in headless mode.
- There is now a `displaytime()` function to get current display-time in
  seconds, a `displaytimer()` function to set a timer based on display-time, and
  a `DisplayTimer()` class for an adjustable timer. `DisplayTime` is the custom
  type for these time values (though again, outside of the type-checker it is
  simply a float).
- Within scenes, there is the concept of 'scene-time' or simply just 'time'.
  This was previously called 'sim-time' and is the default time value that most
  gameplay code should deal with. When speeding up or slowing down or pausing a
  game, it is the rate of scene-time progression that is actually changing.
- The `bascenev1.time()` function now gets the current scene-time in seconds,
  the `bascenev1.timer()` function sets a timer based on scene-time, and
  `bascenev1.Timer()` class gives an adjustable timer. `bascenev1.Time` is the
  custom type for these time values (though again, outside of the type-checker,
  it is simply a float). These names are the same as ballistica's previous
  unified time calls, but they no longer have the options to return values in
  milliseconds or operate on other time types. Just do `int(bs.time() * 1000)`
  if you need milliseconds.
- The 'base-time' concept within scenes remains. Base-time can be thought of as
  a metronome - it progresses constantly for a scene even if the scene is paused
  or sped up or slowed down. Some factors, however, can still cause it to speed
  up or slow down, including changing playback rate in a replay or excess cpu
  load causing it to progress slower than normal.
- There is now a `bascenev1.basetime()` function to get the current base-time in
  seconds, a `bascenev1.basetimer()` call to set a timer using base-time, and a
  `bascenev1.BaseTimer` class for an adjustable timer. `bascenev1.BaseTime` is
  the custom type for these values, though again it is simply a float outside of
  the type checker.
- Reworked frame scheduling to be much more general and no longer assume 60fps (
  basically using the new 'display-time' concept). The engine should now be
  better at maintaining smooth looking animation at other frame-rates. Please
  holler if you see otherwise. Note this doesn't affect the issue where pure SDL
  builds like PC/Linux are locked to 60fps; that's a separate thing.
- You can set env-var `BA_DEBUG_LOG_DISPLAY_TIME=1` to get display-time stat
  logs to make sure things are working smoothly on your setup.
- The engine no longer requires that ba_data and other required files exist in
  the current working dir. This assumption meant the engine would at some point
  `chdir()` to where those files live, which felt dirty and complicated passing
  command line args or using ballistica functionality as part of scripts. There
  is now `ba.app.data_directory` which shows where the app is looking for its
  stuff. It is also now possible to specify this directory on the command-line
  via `--data-dir` or `-d`. Note that some platforms/setups may choose to
  `chdir()` to that dir *before* spinning up the engine (to get clean relative
  paths in stack traces/etc.), but the engine itself no longer forces this.
- The `-cfgdir` command-line arg has been renamed to be either `--config-dir` or
  `-C`.
- The `-exec` command-line arg has been renamed to be either `--exec` or `-e`.
- Added a command arg accessible via `--command` or `-c`. Unlike the exec arg
  which runs as part of the app event loop, this command runs *instead* of the
  normal event loop. It can be thought of as analogous to the `-c` arg for the
  Python interpreter. This provides a clean way to do things like introspect
  ballistica's binary modules without having to worry about data files being
  present or about exiting the app after the command runs. The app simply
  bootstraps its Python interpreter, runs this command, and then exits.
- Moved bootstrapping code from a few different places such as ba._bootstrap to
  a standalone `baenv` module. Calling `baenv.configure()` will set up various
  Python things such as script paths, logging, stdout redirection, and signal
  handling. Default runs of the app will do this as the very first thing, but it
  will also be possible to skip this and use ballistica functionality in a more
  'vanilla' Python environment. Running ballistica in the following way should
  be essentially the same as a 'default' run: `PYTHONPATH=ba_data/python
  ./ballisticakit -c 'import baenv; baenv.configure(); import ba;
  ba.app.run()'`.
- Related to the above, it is now possible for `ba.app.python_directory_app`,
  `ba.app.python_directory_user`, and `ba.app.python_directory_app_site` to be
  None if ballistica is being run in a non-standard environment setup. Just
  something to watch out for.
- The `ba` module is no longer imported by default. Since most modding will go
  through other modules now such as `bascenev` or `bauiv1` it seemed odd to be
  importing only `ba`.
- Starting to move the 'spinoff' system into the public repo (things like
  tools/spinoff and tools/batools/spinoff). This is what will be used to make
  filtered standalone versions of ballistica. More on this soon.
- The `ba` module is now called `babase` and is now just a feature-set like any
  other, which simplifies a lot of project logic. It can even be removed from
  spinoff projects, though in practice it makes little sense to do so.
- Python dummy-modules are now always generated on an as-needed basis (when
  running things like `make mypy`) and live in build/dummymodules instead of
  under assets src.
- Added a help command accessible via '--help' or '-h'. Prints available command
  line args/etc.
- Mods dir can now be overridden via '--mods-dir' or '-m' command line args.
- Ballistica has been updated to use Python 3.11 (with all bundled Python
  versions set to 3.11.3).
- Cleaned up bundled Python builds a bit; they now include a number of
  previously-not-included modules such as the rather tricky to compile 'ctypes'.
  Also some modules that relied on native parts that we are not building have
  been filtered out. If you come across any bundled modules that don't import or
  there are any standard modules that you would like to have which are currently
  excluded, please holler.
- Fixes an issue where holding a key while bringing up the chat window could
  leave the player moving in the same direction.
- The ballistica project config file has been renamed from 'config/config.json'
  to 'config/projectconfig.json'. There's a fair amount of other stuff in the
  config dir these days so this helps keep things clear.
- The resources directory is now 'src/resources' (though this is mostly not
  present in the public repo as of yet, but it should appear at some point).
- Similarly, the assets directory is now 'src/assets' and assets get built to '
  build/assets'. This simplifies a lot of project logic in terms of which files
  get blown away during cleans, which get ignored by syncs, etc. (a single big
  src and build dir is simpler than lots of little ones).
- Shortened some names for meta-generated sources. Something like '
  ballistica/generated/python_embedded/foo.inc' might now look more like '
  ballistica/mgen/pyembed/foo.inc'. Some include paths were starting to get
  ridiculously long so this will save a bit of space, especially as
  meta-generated code is set to become a bigger deal soon.
- Renamed BallisticaCore to BallisticaKit. This is simply the default project
  name and is replaced by an actual project name such as 'BombSquad' in spun-off
  projects. Because there is now a 'core' feature set, this name was feeling a
  bit ambiguous. I also feel 'core' sounds like a small subset of a project and
  'kit' more accurately sounds like the entirety of a project. Also, in the
  future, the default BallisticaKit app may be expanded with editing
  functionality and I feel the name 'Kit' fits better for something used that
  way than 'Core' does.
- The `ballisticacore_internal` precompiled library has been renamed to
  `ballistica_plus`. This name better describes what it actually is (basically
  precompiled native portion of the `plus` feature set). Also by removing the
  'kit' from the end it will no longer be renamed in spinoff projects, meaning
  we should be able to recycle the same built libraries in those cases.
- Moved the `ba*.app.accounts` subsystem to `ba*.app.plus.accounts`. This is a
  little more verbose but is cleaner in a way since that functionality is part
  of plus and is not available when plus is missing. So now there's
  `ba*.app.classic.accounts` for v1 stuff and `ba*.app.plus.accounts` for v2
  stuff.
- For similar reasons, moved the `ba*.app.cloud` subsystem to
  `ba*.app.plus.cloud`.
- The big single ballistica standard library Python package containing all the
  built in games, actors, windows, etc. (bastd) has been split out into parts
  associated with bascenev1 (bascenev1lib) and bauiv1 (bauiv1lib). This way,
  when bascenev2 comes along, it can have its own unique associated library of
  stuff (bascenev2lib). To upgrade existing code, go through and replace
  instances of `bastd.ui` with `bauiv1lib` and all other instances of `bastd`
  with `bascenev1lib`. That should mostly do it. Random tip: check out the
  `tools/pcommand mypy_files` as a handy tool to help get your mods updated.
- (build 21057) Fixed an issue with news items erroring on the main menu (thanks
  for the heads up Rikko)
- (build 21059) Fixed an issue where trying to add a new playlist would error (
  thanks for the heads up SEBASTIAN2059)
- (build 21059) Fixed meta scanning which was coming up empty. Note that games
  must now tag themselves via `ba_meta export bascenev1.GameActivity` instead of
  `ba_meta export game` to be discovered. Warnings will be issued if the old tag
  form is found. This is necessary because there will be totally different
  concepts of game-activities/etc. in future scene versions so we need to use
  exact class names instead of the 'game' shortcut.
- (build 21060) Fixed a bug where epic mode was not in slow motion (but sounds
  still were hehehehe).
- (build 21062) The audio server no longer stops all playing sounds when it is
  reset. This behavior was intended to keep game sounds from 'bleeding' out into
  the main menu, but with app-mode-switches now causing resets just after launch
  it is making some early UI sounds (such as the 'power-down' sound if a plugin
  disappears) sound cut-off and broken. Please holler if you notice any sounds
  that get 'stuck' playing after games/etc.
- (build 21063) Improved error handling when loading plugins. If plugin code
  encountered a ModuleNotFound error while executing, it was being incorrectly
  reported that the plugin itself had disappeared, when actually it was just a
  problem within the plugin's code. This is now correctly handled and reported.
  Which is good because this situation will come up a lot for people upgrading
  old plugins which reference 'ba' and other modules that no longer exist.
- (build 21064) Fixed an issue where the menu button wasn't clickable in-game
  (thanks for the heads up Irvin).
- (build 21067) Fixed timing bugs in MeteorShower and a few other places caused
  by incorrect use of `bs.apptime()` there `bs.time()` should have been used
  (thanks for the heads- up SEBASTIAN2059)
- (build 21070) Fixed an issue where teams series would incorrectly end after 1
  round (thanks for the heads up SEBASTIAN2059)
- (build 21072) Fixed a crash drawing a terrain node with no texture set.
- (build 21073) Stack traces are now implemented under windows so should show up
  for fatal errors and whatnot. Also fatal error logging now mentions when stack
  traces are not available.
- (build 21074) Added `babase.native_stack_trace()` to fetch native stack traces
  as strings.
- (build 21076) Hopefully fixed a 'file in use' error for `_appstate_dump_tb` on
  windows. Please holler if you are still seeing this. This file gets written
  for debugging whenever the logic thread remains unresponsive for several
  seconds.
- (build 21078) Custom system scripts dirs works again (complete copies of app
  system scripts living in your mods directory under `sys/$(YOUR_APP_VERSION)`.
  Tools for creating/destroying these setups are now at `babase.modutils` (they
  had been placed under bauiv1 but that was just silly).
- (build 21080) Fixed an issue where the touch screen controller arrow on
  Android would not show correctly under the player.
- (build 21084) Plugin UI now has a categories dropdown for showing only enabled
  or disabled plugins (Thanks vishal332008!)
- (build 21095) Fixed an issue where certain buttons such as map selection
  buttons
  would draw incorrectly.
- (build 21106) Fixed an issue where in-game ping would always display green no
  matter how bad the ping was.
- (build 21107) Upped internal display-timer resolution from milliseconds to
  microseconds.
- (build 21107) Finished implementing new scheduling system for headless mode.
  This should fix the issue where 1.7.20 servers would have 100ms of lag by
  default. Server performance should now be equal to or better than 1.7.19.
  Please holler if not.
- (build 21111) Fixed a server crash when an individual client player leaves the
  game but doesn't disconnect from the server.
- (build 21113) Linux builds now use the '-rdynamic' flag which means stack
  traces we capture in the engine are more readable; they at least show mangled
  c++ symbols instead of just addresses.
- (build 21114) Fixed a bug where new chat messages would not properly appear in
  the chat window while it is open. (Thanks for the heads-up SatSriyakaal!)
- (build 21117) Now bundling .pdb files with windows test builds. This adds a
  few megs but allows us to log nice full stack traces instead of just
  addresses. Try `print(_babase.native_stack_trace())` if you want to make sure
  its working.
- (build 21118) Fixed an issue where certain messages such as player-left
  weren't being send to clients.
- (build 21118) Renamed `bascenev1.screenmessage()` to
  `bascenev1.broadcastmessage()` to make it more clear that it behaves
  differently (sending messages to all connected clients instead of just the
  local screen). There is still a `bascenev1.screenmessage()` but that is now
  the same local-only version available in babase. Added a temporary warning if
  calling screenmessage() in a situation that in previous versions would have
  done a broadcast.
- (build 21121) The old app `user_agent_string` which was very ugly and
  cluttered and nonstandard has been renamed to `legacy_user_agent_string`. A
  newer simpler one is now available from `babase.user_agent_string()`. It looks
  like `Ballistica/1.7.20`. If OS version or platform or whatever else needs to
  be communicated to a server, it should be passed explicitly as extra data.
- (build 21124) Changed debug-prints for connectivity and v2-transport stuff to
  use log calls instead of prints. The environment vars to enable them are now
  `BA_DEBUG_LOG_CONNECTIVITY` and `BA_DEBUG_LOG_V2_TRANSPORT`. Set either to '1'
  to enable debug logging.
- (build 21125) Fixed a bug where app-modes would not have their
  DoApplyAppConfig callbacks called in C++, which was causing the server-mode
  `idle_exit_minutes` value to be ignored. Servers should now properly exit
  after being idle for this length of time.
- (build 21126) Reworked the efrocache system used by public builds for
  downloading built assets and binaries. It should now be faster and more
  efficient (though I have not tested this). Most importantly, it now supports
  spinoff, which means that spinoff projects created from the public github repo
  should now build and run. So if you run `make spinoff-test-base` and then `cd
  build/spinofftest/base`, you should be able to do `make cmake` from that
  spinoff project and get a running app (though it will be just a blank window).
  But the app at that point *is* 100% open source; woohoo!
- (build 20129) Fixed an issue where server builds would not build font assets
  (though it would install them if any recent gui builds had built them) which
  could lead to obscure crashing.
- (build 21131) Fixed a bug where `is_browser_likely_available()` would
  incorrectly return False on Android, causing certain things such as the v2
  login screen to merely display URLs onscreen and not offer to open them in a
  browser.

### 1.7.19 (build 20997, api 7, 2023-01-19)

- Fixes an issue where repeated curses could use incorrect countdown times (
  Thanks EraOSBeta!).
- Last manual party connect port is now saved. Previously, it always assumed the
  port to be 43210 (Thanks ritiek!).
- Added a plugin-settings window under the plugins UI which allows
  enabling/disabling all plugins and setting whether new plugins are
  auto-enabled (Thanks vishal332008!).
- Missing maps are now cleanly filtered out of playlists instead of causing
  errors/hangs (Thanks imayushsaini!).
- Added in-game-ping option under advanced settings (Thanks imayushsaini!).
- `BA_DEVICE_NAME` environment variable can now be used to change the name the
  local device shows up as. Handy if running multiple servers so you can tell
  them apart in cloud-console/etc. (Thanks imayushsaini!).

### 1.7.18 (build 20989, api 7, 2023-01-16)

- Reworked some low level asynchronous messaging functionality in efro.message
  and efro.rpc. Previously these were a little *too* asynchronous which could
  lead to messages being received in a different order than they were sent,
  which is not desirable.
- Added a way to suppress 'Your build is outdated' messages at launch ( see
  `ba._hooks.show_client_too_old_error()`).

### 1.7.17 (build 20983, api 7, 2023-01-09)

- V2 accounts now show a 'Unlink Legacy (V1) Accounts' button in account
  settings if they have any old V1 links present. This can be used to clear out
  old links to replace them with V2 links which work correctly with V2 accounts.
- `ba.internal.dump_tracebacks()` is now `ba.internal.dump_app_state()` and
  `ba.internal.log_dumped_tracebacks()` is now
  `ba.internal.log_dumped_app_state()`. This reflects the fact that these calls
  may be expanded to include other app state in the future (C++ layer thread
  states, etc.).
- Added `ba.app.health_monitor` which will dump app state if the logic thread
  ever stops responding for 5+ seconds while the app is running (to help
  diagnose deadlock situations).
- Various extra logging and bug fixes related to V2 accounts and master server
  communication (trying to get this stuff working as smoothly as possible now
  that it is feature-complete).

### 1.7.16 (build 20969, api 7, 2022-12-18)

- Fixed a bug where profile names encased in curly brackets could cause harmless
  error messages.
- Android will no longer log errors on ba.open_url() calls if a browser is not
  available (it still just falls back to the in-app dialog in that case).
- The 'Upgrade' button for device accounts now signs you out and closes the
  upgrade window to hopefully make it more clear that you need to sign in with
  your newly created/upgraded BombSquad account.
- Fixed a bug where the remote app could not connect for the first 5 seconds
  after launching the app.
- Added Malay language. Ick; apparently its been sitting done for a while and I
  hadn't realized it wasn't added to the game yet. Apologies!. And thanks to all
  contributors!
- Added 'enable_queue' server config setting. This defaults to True but can be
  turned off as a workaround for server owners targeted by queue spam attacks.
- The public party list no longer sorts servers without queues at the end of the
  list. This sorting was put there long ago to prioritize fancy new
  queue-supporting servers but now it would just make the few that opt out of
  queues hard to find. Doh. So opting out of queues is probably not a great idea
  until this build is widespread.
- Public uuids now only change once every 6 months or so instead of with every
  version bump. This way periods of heavy development won't put added strain on
  server owners trying to keep ban lists up to date and whatnot.
- Added a merch button in the in-game store that goes to the ballistica.net
  merch page (though it only shows up in the few countries where merch is
  available).

### 1.7.15 (build 20960, api 7, 2022-12-04)

- The cancel button on the 'Sign in with a Bombsquad Account' popup no longer
  respond to system cancel buttons (escape key, android back button, etc). Turns
  out some Android people were pressing back repeatedly to come back from a
  browser after signing in and immediately canceling their sign in attempts in
  the game before they completed. Hopefully this will avoid some frustration.
- Fixed an issue where back presses could result in multiple main menu windows
  appearing.

### 1.7.14 (build 20958, api 7, 2022-12-03)

- Android Google Play logins now provide V2 accounts with access to all V2
  features such as a globally-unique account tag, cloud-console, and workspaces.
  They should still retain their V1 data as well.
- V2 accounts now have a 'Manage Account' button in the app account window which
  will sign you into a browser with your current account.
- Removed Google App Invite functionality which has been deprecated for a while
  now. Google Play users can still get tickets by sharing the app via codes (
  same as other platforms).
- Updated Android root-detection library to the latest version. Please holler if
  you are getting new false 'your device is rooted' errors when trying to play
  tournaments or anything like that.
- Removed a few obsolete internal functions: `_ba.is_ouya_build()`,
  `_ba.android_media_scan_file()`.
- Renaming some methods/data to disambiguate 'login' vs 'sign-in', both in the
  app and on ballistica.net. Those two terms are somewhat ambiguous and
  interchangeable in English and can either be a verb or a noun. I'd like to
  keep things clear in Ballistica by always using 'sign-in' for the verb form
  and 'login' for the noun. For example: 'You can now sign in to your account
  using your Google Play login'.
- Fixed the 'your config is broken' dialog that shows on desktop builds if the
  game's config file is corrupt and can't be read. It should let you edit the
  config or replace it with a default.
- `ba.printobjects()` is now `ba.ls_objects()`. It technically logs and doesn't
  print so the former name was a bit misleading.
- Added `ba.ls_input_devices()` to dump debug info about the current set of
  input devices. Can be helpful to diagnose mysterious devices joining games
  unintentionally and things like that.
- Added 'raw' bool arg to `ba.pushcall()`. Passing True for it disables
  context_ref save/restore and thread checks.
- Added `ba.internal.dump_tracebacks()` which can be used to dump the stack
  state of all Python threads after some delay. Useful for debugging deadlock;
  just call right before said deadlock occurs. Results will be logged on the
  next app launch if they cannot be immediately.
- Fixed a low level event-loop issue that in some cases was preventing the
  Android version from properly pausing/resuming the app or managing connections
  while in the background. If you look at the devices section on ballistica.net
  you should now see your device disappear when you background the app and
  reappear when you foreground it. Please holler if not.
- Device accounts are now marked as deprecated, and signing in with one now
  brings up an 'upgrade' UI which allows converting it to a V2 account. It is my
  hope to push the entire client ecosystem to V2 accounts as quickly as possible
  since trying to support both independent V1 accounts and V2 accounts is a
  substantial technical burden.
- Fixed an issue where Log calls made within
  `EventLoopThread::PushThreadMessage()` could result in deadlock.
- Fixed an issue where some Android hardware buttons could theoretically cause
  rogue game controller button presses (due to downcasting int values > 255 into
  a uint8 value).

### 1.7.13 (build 20919, api 7, 2022-11-03)

- Android target-sdk has been updated to 33 (Android 13). Please holler if
  anything seems broken or is behaving differently than before on Android.
- Android back-button handling code had to be reworked a bit for sdk 33 ( see
  https://developer.android.com/guide/navigation/predictive-back-gesture).
  Because of this, back buttons on gamepads or other special cases behave
  slightly differently, but hopefully still in a reasonable way. Please holler
  if you find otherwise.

### 1.7.12 (build 20914, api 7, 2022-10-18)

- Disabled some live-objects warnings as it seems their use of certain gc module
  functionality might be causing some rare errors/crashes. On further
  inspection, it turns out that is technically expected. Basically those calls
  are useful for debugging but can break things. Added a note at the top of
  efro.debug elaborating on the situation. We can reimplement similar warnings
  later in a safe manner.
- Removed `ba._general.print_active_refs()` because the newer stuff in
  efro.debug does the same thing better.
- Bug fixes related to v2 account connections.

### 1.7.11 (build 20909, api 7, 2022-10-15)

- Switched our Python autoformatting from yapf to black. The yapf project seems
  to be mostly dead whereas black seems to be thriving. The final straw was yapf
  not supporting the `match` statement in Python 3.10.
- Added `has_settings_ui()` and `show_settings_ui()` methods to ba.Plugin.
  Plugins can use these to enable a 'Settings' button next to them in the plugin
  manager that brings up a custom UI.
- Fixed workspaces functionality, which I broke rather terribly in 1.7.10 when I
  forgot to test it against all the internal changes there (sorry). Note that
  there is a slight downside to having workspace syncing enabled now in that it
  turns off the fast-v2-relaunch-login optimization from 1.7.10.
- App should now show a message when workspace has been changed and a restart is
  needed for it to take effect.
- Fixed an issue where `ba.open_url()` would fall back to internal url display
  window on some newer Android versions instead of opening a browser. It should
  now correctly open a browser on regular Android. On AndroidTV/iiRcade/VR it
  will now always display the internal pop-up. It was trying to use fancy logic
  before to determine if a browser was available but this seemed to be flaky.
  Holler if this is not working well on your device/situation.
- The internal 'fallback' `ba.open_url()` window which shows a url string when a
  web browser is not available now has a qrcode and a copy button (where
  copy/paste is supported).
- Added a 'force_internal' arg to `ba.open_url()` if you would like to always
  use the internal window instead of attempting to open a browser. Now that we
  show a copy button and qr code there are some cases where this may be
  desirable.

### 1.7.10 (build 20895, api 7, 2022-10-09)

- Added eval support for cloud-console. This means you can type something like '
  1+1' in the console and see '2' printed. This is how Python behaves in the
  stdin console or in-game console or the standard Python interpreter.
- Exceptions in the cloud-console now print to stderr instead of
  logging.exception(). This means they aren't a pretty red color anymore, but
  this will keep cloud-console behaving well with things like servers where
  logging.exception() might trigger alarms or otherwise. This is also consistent
  with standard interactive Python behavior.
- Cloud console now shows the device name at the top instead of simply 'Console'
  while connected.
- Moved the function that actually runs cloud console code to
  `ba._cloud.cloud_console_exec()`.
- Added efro.debug which contains useful functionality for debugging object
  reference issues and memory leaks on live app instances (via cloud shell or
  whatever).
- Lots of reworking/polishing in general on communication between the game and
  v2 regional/master servers in preparation of upgrading Google Play accounts to
  V2. Please holler if anything is not working smoothly with a V2 account.
- When establishing V2 master-server communication, if the closest regional
  server is down or too busy, will now fall back to farther ones instead of
  giving up. You can follow this process by setting env var
  `BA_DEBUG_PRINT_V2_TRANSPORT` to 1 when running the app.
- Network testing now skips the alternate v1 master server addr if the primary
  succeeded. The alternate often fails which makes things look broken even
  though the game is ok as long as primary works.
- The v2-transport system will now properly reestablish account connectivity
  when asked to refresh its connection (the cloud does this periodically so
  regional cloud servers can be restarted as needed). Practically this means
  your app won't stop showing up under the ballistica.net devices section after
  its been running for a while; a problem previous builds had.
- The v2-transport system can now establish more than one connection at a time,
  which allows the app to gracefully transition to a new connection when the old
  is about to expire without any period of no connectivity. To test this
  functionality, set env var `BA_DEBUG_PRINT_V2_TRANSPORT=1` to see transport
  debug messages and `BA_DEBUG_V2_TRANSPORT_SHORT_DURATION=1` to cause the cloud
  to request a connection-refresh every 30 seconds or so.
- V2 accounts now consider themselves instantly signed in if they were signed in
  when the app last ran. They still need to contact the master-server before
  anything important can happen, but this should help keep things feel faster in
  general.
- Due to v2-transport improvements, pressing the 'End Session Now' button in
  ballistica.net account settings should now instantly log you out of all apps
  using that session (ones that are online at least). Previously this would
  often not take effect until something like an app relaunch.
- Fixes an issue where the tournament entry window could remain stuck on top
  when following a 'get more tickets' link. (Thanks itsre3!)
- The main menu now says 'End Test' when in a stress test instead of 'End Game'
  (Thanks vishal332008!)
- Added 'discordLogo' and 'githubLogo' textures for anyone who wants to use
  those for UIs.

### 1.7.9 (build 20880, api 7, 2022-09-24)

- Cleaned up the efro.message system to isolate response types that are used
  purely internally (via a new SysResponse type).
- Fixed bug with 'Disable Camera Shake' option. (GitHub #511) (thanks Dliwk!)
- Fixed an issue where Co-op football would play no music.
- Accept "fairydust" as an emit type in `ba.emitfx()` (thanks ritiek!).
- Added epic mode option to Easter Egg Hunt (thanks itsre3!).
- The game no longer auto-signs-in to a device account when first run since we
  want to start encouraging people to use V2 accounts.
- Removed support for GameCircle in Amazon builds (which has been discontinued
  for years at this point).

### 1.7.8 (build 20871, api 7, 2022-09-21)

- Fixed tournament scores submits which were broken in 1.7.7 (oops).
- Added @clear command to stdin command reader.

### 1.7.7 (build 20868, api 7, 2022-09-20)

- Added `ba.app.meta.load_exported_classes()` for loading classes discovered by
  the meta subsystem cleanly in a background thread.
- Improved logging of missing playlist game types.
- Some ba.Lstr functionality can now be used in background threads.
- Added simple check for incoming packets (should increase security level a
  bit).
- Simplified logic for C++ `Platform::GetDeviceName()` and made it accessible to
  Python via `ba.app.device_name`.
- Default device name now uses gethostname() instead of being hard coded to '
  Untitled Device' (though many platforms override this).
- Added support for the console tool in the new devices section on
  ballistica.net.
- Increased timeouts in net-testing gui and a few other places to be able to
  better diagnose/handle places with very poor connectivity.
- Removed `Platform::SetLastPyCall()` which was just for debugging and which has
  not been useful in a while.
- Moved some app bootstrapping from the C++ layer to the `ba._bootstrap` module.
- The game will now properly return to the stress-test window after a stress
  test finishes (thanks vishal332008!)
- Continue window will now pause the game to avoid running up times in the
  background (thanks vishal332008!)
- Keepaway and KingOfTheHill now have epic options (thanks FAL-Guys!)
- Spaz starting with gloves no longer loses it after picking up an expiring
  gloves powerup (thanks itsre3!)
- Starting to rename the 'game' thread to the 'logic' thread. This is the thread
  where most high level app logic happen, not only game logic.
- `_ba.in_game_thread()` is now `_ba.in_logic_thread()`.
- Misc C++ layer tidying/refactoring.
- Split out the `_ba` binary module into `_ba` and `_bainternal`. This will
  eventually allow running without the closed-source parts (`_bainternal`)
  present at all.
- There is now a `_bainternal.py` dummy-module alongside the existing `_ba.py`
  one. Be sure to exclude it from any script collections used by the game (the
  same as `_ba.py`).
- Added checks to make sure `_ba` or `_bainternal` arent used outside of ba.
  Any 'internal' functionality needed outside of ba should be exposed through
  ba.internal. `_ba` and `_bainternal` are internal implementation details.
- Removed C++ Module class and simplified EventLoopThread class. The Module
  class was an old relic of long ago before C++ had lambdas and its existence
  was pretty pointless and confusing these days.
- Renamed C++ App to AppFlavor and AppGlobals to App.
- Renamed C++ Media to Assets.
- Removed 'scores to beat' list in coop which was only ever functional in
  limited cases on the Mac version. Perhaps that feature can reappear in a
  cross-platform way sometime.
- Simplified C++ bootstrapping to allocate all globals in one place.
- Renamed C++ Game classes to Logic.
- The app now bootstraps Python in the main thread instead of the logic thread.
  This will keep things more consistent later when we are able to run under an
  already-existing Python interpreter.
- As a side-effect of initing Python in the main thread, it seems that Python
  now catches segfaults in our debug builds and prints Python stack traces. (
  see https://docs.python.org/3/library/faulthandler.html). We'll have to
  experiment and see if this is a net positive or something we want to disable
  or make optional.
- Python and `_ba` are now completely initialized in public source code. Now we
  just need to enable the app to survive without `_bainternal` and it'll be
  possible to build a 100% open source app.
- `Logging::Log()` in the C++ layer now takes a LogLevel arg (kDebug, kWarning,
  kError, etc.) and simply calls the equivalent Python logging.XXX call. This
  unifies our C++ and Python logging to go through the same place.
- `ba.log()` is no more. Instead just use standard Python logging functions (
  logging.info(), logging.error(), etc.).
- `_ba.getlog()` is now `_ba.get_v1_cloud_log()`. Note that this functionality
  will go away eventually so you should use `ba.app.log_handler` and/or standard
  Python logging functions to get at app logs.
- Along the same lines, `_ba.get_log_file_path()` is now
  `_ba.get_v1_cloud_log_file_path()`.
- Added `_ba.display_log()` function which ships a log message to the in-game
  terminal and platform-specific places like the Android log. The engine wires
  up standard Python logging output to go through this.
- Added `_ba.v1_cloud_log()` which ships a message to the old v1-cloud-log (the
  log which is gathered and sent to the v1 master server to help me identify
  problems people are seeing). This is presently wired up to a subset of Python
  logging output to approximate how it used to work.
- Note: Previously in the C++ layer some code would mix Python print calls (such
  as `PyErr_PrintEx()`) with ballistica::Log() calls. Previously these all wound
  up going to the same place (Python's sys.stderr) so it worked, but now they no
  longer do and so this sort of mixing should be avoided. So if you see a weird
  combination of colored log output lines with non-colored lines that seem to go
  together, please holler as it means something needs to be fixed.
- Builds for Apple devices now explicitly set a thread stack size of 1MB. The
  default there is 512k and I was seeing some stack overflows for heavy physics
  sims or very recursive Python stuff.
- If you want to grab recent logs, you can now use
  `ba.app.log_handler.get_cached()`. This will give you everything that has gone
  through Python logging, Python stdout/stderr, and the C++ Log() call (up to
  the max cache size that is).
- LogHandler output now ALWAYS goes to stderr. Previously it only would if an
  interactive terminal was detected. This should make the binary easier to debug
  if run from scripts/etc. We can add a `--quiet` option if needed or whatnot.
- (build 20859) Fixed an error setting up asyncio loops under Windows related to
  the fact that Python is now inited in the main thread.
- (build 20864) Fatal-error message/traceback now properly prints to stderr
  again (I think the recent logging rejiggering caused it to stop).
- (build 20864) Fixed an issue where the app could crash when connected to the
  cloud console while in a network game.
- Added a simplified help() command which behaves reasonably under the in-game
  console or cloud-console.

### 1.7.6 (build 20687, api 7, 2022-08-11)

- Cleaned up the MetaSubsystem code.
- It is now possible to tell the meta system about arbitrary classes (ba\_meta
  export foo.bar.Class) instead of just the preset types 'plugin', 'game', etc.
- Newly discovered plugins are now activated immediately instead of requiring a
  restart.

### 1.7.5 (build 20672, api 7, 2022-07-25)

- Android build now uses the ReLinker library to load the native main.so, which
  will (hopefully) avoid some random load failures on older Android versions.
- Android Google Play build now prints a message at launch if the billing
  library isn't available or needs to be updated (explaining why purchases won't
  work in that case).
- Various minor bug fixes (mostly cleaning up unnecessary error logging)
- Updated Android builds to use the new NDK 25 release
- Added a warning when trying to play a tournament with a workspace active
- Added api-version to changelog headers and `pcommand version` command.

### 1.7.4 (20646, 2022-07-12)

- Fixed the trophies list showing an incorrect total (Thanks itsre3!)
- ba.app.meta.metascan is now ba.app.meta.scanresults
- Cleaned up co-op ui code a bit
- Added a utility function to add custom co-op games in the practice section:
  `ba.app.add_coop_practice_level`. Also added new workspace template script
  which uses it to define a new co-op game type.
- Removed some spammy debug timing logging I added for tracking down a recent
  bug (can be reenabled by setting env var `BA_DEBUG_TIMING=1`)
- Updated the 'Show Mods Folder' to properly show the path to the mods folder.
  Before it would unhelpfully show something like `<External Storage>/BombSquad`
  but now it should be something more useful like
  `Android/data/net.froemling.bombsquad/files/mods`.
- Android user scripts dir is now called 'mods' instead of 'BombSquad'. The name
  'BombSquad' made sense when it was located in a truly shared area of storage
  but now that it is in the app-specific area (something like
  Android/data/net.froemling.bombsquad/files) it makes sense to just use 'mods'
  like other platforms.
- Updated the Modding Guide button in advanced settings to point to the new
  ballistica wiki stuff instead of the old out-of-date 1.4 modding docs.
- Added ba.app.net.sslcontext which is a shared SSLContext we can recycle for
  our https requests. It turns out it can take upwards of 1 second on older
  Android devices to create a default SSLContext, so this can provide a nice
  speedup compared to the default behavior of creating a new default one for
  each request.
- Rewrote Google Play version purchasing code using Google's newest libraries (
  Google Play Billing 5.0). This should make everything more reliable, but
  please holler if you try to purchase anything in the game and run into
  problems.
- It is now possible on the Google Play version to purchase things like Pro more
  than once for different accounts.

### 1.7.3 (20634, 2022-07-06)

- Fixed an issue with King of the Hill flag regions not working when players
  entered them (Thanks itsre3!)
- Fixed an issue in Chosen One where the flag resetting on top of a player would
  not cause them to become the chosen one (Thanks Dliwk!)
- Fixed an issue where triple-bomb powerup would not flash before wearing off (
  Thanks Juleskie!).
- Fixed an issue where syncing workspaces containing large files could error.
- Net-testing window now requires you to be signed in instead of giving an error
  result in that case.
- The app now issues a gentle notice if plugins are removed instead of erroring
  and continuing to look for them on subsequent launches. This makes things much
  smoother when switching between workspaces or users.
- Added new translation entries for Workspace/Plugin stuff.
- tools/bacloud workspace get/put commands are now functional (wiki page with
  instructions coming soon).
- `_ba.android_get_external_storage_path` is now
  `_ba.android_get_external_files_dir` which maps to the actual call it makes
  under the hood these days.
- Android logging now breaks up long entries such as stack-traces into multiple
  log entries so they should not get truncated.
- The app now issues a warning if device time varies significantly from actual
  world time. This can lead to things like the app incorrectly treating SSL
  certificates as not yet valid and network functionality failing.
- The app now issues a warning if unable to establish secure connections to
  cloud servers (which can be due to aforementioned issue, but could also stem
  from other network problems).
- The Network Testing utility (Settings->Advanced->Network Testing) now tests
  for more potential issues including ones mentioned above.
- The Android version now stores files such as extracted assets and audio caches
  in the non-backed-up files dir (Android's Context.getNoBackupFilesDir()).
  These files can always be recreated by the app so they don't need backups, and
  this makes it more likely that Android will back up what's left in the regular
  files dir (the app config, etc).
- Fixed an issue causing hitches during background SSL network operations (
  manifesting on the Android version but theoretically possibly anywhere).

### 1.7.2 (20620, 2022-06-25)

- Minor fixes in some minigames (Thanks Droopy!)
- Fixed a bug preventing 'clients' arg from working in `_ba.chatmessage` (Thanks
  imayushsaini!)
- Fixed a bug where ba.Player.getdelegate(doraise=True) could return None
  instead of raising a ba.DelegateNotFoundError (thanks Dliwk!)
- Lots of Romanian language improvements (Thanks Meryu!)
- Workspaces are now functional. They require signing in with a V2 account,
  which currently is limited to explicitly created email/password logins. See
  ballistica.net to create such an account or create/edit a workspace. This is
  bleeding edge stuff so please holler with any bugs you come across or if
  anything seems unintuitive.
- Newly detected Plugins are now enabled by default in all cases; not just
  headless builds. (Though a restart is still required before they run). Some
  builds (headless, iiRcade) can't easily access gui settings so this makes
  Plugins more usable there and keeps things consistent. The user still has the
  opportunity to deactivate newly detected plugins before restarting if they
  don't want to use them.
- Reworked app states for the new workspace system, with a new `loading` stage
  that comes after `launching` and before `running`. The `loading` stage
  consists of an initial account log-in (or lack thereof) and any
  workspace/asset downloading related to that. This allows the app to ensure
  that the latest workspace state is synced for the active account before
  running plugin loads and meta scans, allowing those bits to work as seamlessly
  in workspaces as they do for traditional local manual installs.
- Plugins now have an `on_app_running` call instead of `on_app_launch`, allowing
  them to work seamlessly with workspaces (see previous entry).
- Errors running/loading plugins now show up as screen-messages. This can be
  ugly but hopefully provides a bit of debugging capability for anyone testing
  code on a phone or somewhere with no access to full log output. Once we can
  add logging features to the workspaces web ui we can perhaps scale back on
  this.
- Api version increased from 6 to 7 due to the aforementioned plugin changes
  (`on_app_launch` becoming `on_app_running`, etc.)

### 1.7.1 (20597, 2022-06-04)

- V2 account logic fixes
- Polishing V2 web-based login flow

### 1.7.0 (20591, 2022-06-02)

- V2 accounts are now available (woohoo!). These are called 'BombSquad Accounts'
  in the account section. V2 accounts communicate with a completely new server
  and will be the foundation for lots of new functionality in the future.
  However they also function as a V1 account so existing functionality should
  still work. Note that the new 'workspaces' feature for V2-accounts is not yet
  enabled in this build, but it will be in the next few builds. Also note that
  account types such as GameCenter and Google-Play will be 'upgraded' to V2
  accounts in the future so there is no need to try this out if you use one of
  those. But if you use device-accounts you might want to create yourself a V2
  account, since device-accounts will remain V1-only (though you can link an old
  device-account to a v2-enabled account if you want to keep your progress).
  Getting a V2 account now also gives you a chance to reserve a nice account-tag
  before all the good ones are taken.
- Legacy account subsystem has been renamed from `ba.app.accounts` to
  `ba.app.accounts_v1`
- Added `ba.app.accounts_v2` subsystem for working with V2 accounts.
- `ba.SessionPlayer.get_account_id()` is now
  `ba.SessionPlayer.get_v1_account_id()`
- `ba.InputDevice.get_account_id()` is now `ba.InputDevice.get_v1_account_id()`
- `_ba.sign_in()` is now `_ba.sign_in_v1()`
- `_ba.sign_out()` is now `_ba.sign_out_v1()`
- `_ba.get_account_name()` is now `_ba.get_v1_account_name()`
- `_ba.get_account_type()` is now `_ba.get_v1_account_type()`
- `_ba.get_account_state()` is now `_ba.get_v1_account_state()`
- `_ba.get_account_state_num()` is now `_ba.get_v1_account_state_num()`
- `_ba.get_account_display_string()` is now
  `_ba.get_v1_account_display_string()`
- `_ba.get_account_misc_val()` is now `_ba.get_v1_account_misc_val()`
- `_ba.get_account_misc_read_val()` is now `_ba.get_v1_account_misc_read_val()`
- `_ba.get_account_misc_read_val_2()` is now
  `_ba.get_v1_account_misc_read_val_2()`
- `_ba.get_account_ticket_count()` is now `_ba.get_v1_account_ticket_count()`
- Exposing more sources in the public repo; namely networking stuff. I realize
  this probably opens up some attack vectors for hackers but also opens up
  options for server-owners to add their own defenses without having to wait on
  me. Hopefully this won't prove to be a bad idea.
- V2 master server addr is now simply https://ballistica.net. If you had saved
  links to the previous address, https://tools.ballistica.net, please update
  them, as the old address may stop working at some point.
- Upgraded everything to Python 3.10. The upgrade process is pretty smooth at
  this point so we should be able to upgrade yearly now once each new Python
  version has had some time to mature.

### 1.6.12 (20567, 2022-05-04)

- More internal work on V2 master-server communication

### 1.6.11 (20539, 2022-03-23)

- Documentation is now generated using pdoc <https://pdoc.dev>. Thanks Dliwk!!
  ( I'll get it wired up to auto-update to a webpage soon).
- Players who connect to authenticated servers impersonating someone else are
  now simply kicked; not banned. The old behavior was being intentionally
  exploited to ban people from their own servers/etc. I may revert to bans once
  I can do it in a way that is not exploitable.
- The game now establishes a V2 master-server connection (which will soon be
  used for lots of cool functionality). For this version it is mainly enabled
  for testing purposes; please holler if you see any odd warning messages or
  behavior.

### 1.6.10 (20511, 2022-03-20)

- Added `_ba.get_client_public_device_uuid` function which returns a
  semi-permanent device id for a connected client running 1.6.10 or newer. Can
  be useful to combat spam attacks or other mischief.
- Fixed an issue with `make update` not properly rewriting Visual Studio project
  files to account for new/deleted source files.
- Removed various bits of code associated with the (no-longer-functional) Google
  Play Games multiplayer connections.
- Added lots of foundation code for v2 master-server connections (not yet
  enabled).

### 1.6.9 (20486, 2022-02-22)

- Upgraded Android Python to 3.9.10
- Fixed an issue with SSL in Android builds that was preventing communication
  with the master-server in 1.6.8
- Added a new network-diagnostics tool at 'Settings->Advanced->Network Testing'.
  Can be used to diagnose issues talking to master-servers/etc. (especially
  useful now that SSL can factor in)
- Added clipboard support to Mac test build (thought pasting currently requires
  ctrl-v instead of cmd-v).
- Fixed an issue where non-ascii characters in device names could break network
  communication.

### 1.6.8 (20458, 2022-02-16)

- Added Filipino language (Thanks David!)
- Restored pre-v1.5 jump behaviour.
- All communication with the master-server should now be secure (https) using
  root certificates from the
  [certifi](https://github.com/certifi/python-certifi) project. Please holler if
  you run into any connection issues with this version.

### 1.6.7 (20436)

- Fixed a vulnerability which could expose device-account uuids.
- Now generating Linux Arm64 server and test builds (currently built against
  Ubuntu 20).
- Mac test builds are now Universal binaries (Arm64 & x86-64 versions bundled
  together).
- Mac test builds are now notarized and distributed via a snazzy .dmg instead of
  a zip file, so the OS should no longer try to prevent you from running them.
- Test builds can now be found at <https://ballistica.net/builds> - this page
  shows more info about the builds, including file checksums (stored on a
  separate server from the actual files for increased security).

### 1.6.6 (20394)

- Beginning work on moving to new asset system.
- Added Tamil language (Thanks Ryan!)
- Added methods for changing camera attributes to the `_ba` module.

### 1.6.5 (20394)

- Added co-op support to server builds (thanks Dliwk!)
- Updated everything from Python 3.8 to Python 3.9. The biggest immediate impact
  to our code is that basic types such as list, dict, and tuple can be used in
  annotations, eliminating the need to import typing.Dict, typing.List, etc. See
  python.org for more changes.
- Note: accessing mods on external storage on Android will not work in this
  release. This functionality has not been working in recent versions of Android
  due to increased security features anyway and I am in the process of replacing
  it with a cloud based system for installing mods. More on this soon.
- Python 3.9 no longer supports Windows 7 or earlier (according to
  <https://www.python.org/downloads/windows/>) so if you are running such a
  version of Windows you will need to stick to older builds.

### 1.6.4 (20382)

- Some cleanups in the Favorites tab of the gather window.
- Reorganized prefab target names; some targets such as `prefab-debug` are now
  `prefab-gui-debug` (more consistent with the existing `prefab-server-debug`
  targets).
- Windows builds now go to build/windows instead of
  `ballisticacore_windows/build`.
- Lots of project reorganization to allow things such as documentation or the
  dummy `_ba.py` module to be rebuilt from the public repo.
- Added network flood attack mitigation.

### 1.6.3 (20366)

- Telnet access works again for gui builds without requiring a password (access
  must still be granted via the gui).

### 1.6.2 (20365)

- Declare opponent team as the winner if a player with their final turn leaves
  an elimination game.
- Fix for certain cases when trying to host a private game where no available
  nearby servers could be found.
- Enabling per-architecture apk splitting for smaller download sizes on Android.

### 1.6.1 (20362)

- Some clean-up on Android builds, including simplifying ad-networks. No longer
  should ever show rewarded ads in between game rounds (only when actual rewards
  are involved).

### 1.6.0 (20357)

- Revamped netcode significantly. We still don't have client-prediction, but
  things should (hopefully) feel much lower latency now.
- Added network debug graphs accessible by hitting F8.
- Added private parties functionality (cloud hosted parties with associated
  codes making it easier to play with friends)
- The meta subsystem now enables new plugins by default in headless builds.
- Added option to save party in Manual tab
- Slight tidying on the tourney entry popup
- Env var to override UI scale is now `BA_UI_SCALE` instead of
  `BA_FORCE_UI_SCALE`.
- Fixed an issue where ba.storagename() could prevent objects on the stack from
  getting released cleanly
- Improvements to documentation generation such as link to some external base
  types.
- Added `ba.clipboard_*` functions for copying and pasting text on supported
  platforms.
- Implemented clipboard functionality on SDL based builds (such as prefab).
- Fixed an issue where click locations on scaled text fields could be
  incorrectly calculated.
- Server-wrapper improvements allowing config path and `ba_root` path to be
  passed explicitly.
- Binary -cfgdir option now properly allows any path, not just `./ba_root`.
- Additional server-wrapper options such as disabling auto-restart and automatic
  restarts on config file changes.
- Running a `_ba.connect_to_party` command via the -exec arg should now do the
  right thing.
- Fixed possible crash due to buffer under/overruns in `Utils::precalc_rands_*`.
- Fixed a potential crash-on-exit due to statically allocated colliders/caches
  in `ode_collision_trimesh.cpp` getting torn down while in use
- Better randomization for player free-for-all starting locations
- Plugins can now register to be called for pause, resume, and shutdown events
  in addition to launch
- Added ba.app.state holding the overall state of the app (running, paused,
  etc.)
- renamed the efro.dataclasses module to efro.dataclassio and added significant
  functionality
- command-line input no longer errors on commands longer than 4k bytes.
- added show-tutorial option to the server wrapper config
- added custom-team-names option to the server wrapper config
- added custom-team-colors option to the server wrapper config
- added inline-playlist option to the server wrapper config

### 1.5.29 (20246)

- Exposed ba method/class initing in public C++ layer.
- The 'restart' and 'shutdown' commands in the server script now default to
  immediate=True
- Wired up `clean_exit_minutes`, `unclean_exit_minutes`, and `idle_exit_minutes`
  options in the server config
- Removed remains of the google-real-time-multiplayer stuff from the
  android/java layer.

### 1.5.28 (20239)

- Simplified `ba.enum_by_value()`
- Updated Google Play version to hopefully show friend high scores again on
  score screens (at least for levels that have an associated Google Play
  leaderboard).
- Public-party-list now properly shows an error instead of 'loading...' when not
  signed in.
- Heavily reworked public party list display code to be more efficient and avoid
  hitches even with large numbers of servers.

### 1.5.27 (20238)

- Language functionality has been consolidated into a LanguageSubsystem object
  at ba.app.lang
- `ba.get_valid_languages()` is now an attr: `ba.app.lang.available_languages`
- Achievement functionality has been consolidated into an AchievementSubsystem
  object at ba.app.ach
- Plugin functionality has been consolidated into a PluginSubsystem obj at
  ba.app.plugins
- Ditto with AccountV1Subsystem and ba.app.accounts
- Ditto with MetadataSubsystem and ba.app.meta
- Ditto with AdsSubsystem and ba.app.ads
- Revamped tab-button functionality into a cleaner type-safe class (
  bastd.ui.tabs.TabRow)
- Split Gather-Window tabs out into individual classes for future improvements (
  bastd.ui.gather.\*)
- Added the ability to disable ticket-purchasing UIs for builds
  (`ba.app.allow_ticket_purchases`)
- Reworked the public party gather section to perform better; it should no
  longer have to rebuild the list from scratch each time the UI is visited.
- Added a filter option to the public party list (sorry it has taken so long).

### 1.5.26 (20217)

- Simplified licensing header on python scripts.
- General project refactoring in order to open source most of the C++ layer.

### 1.5.25 (20176)

- Added Venetian language (thanks Federico!)
- Fixed an issue where chosen-one flashes would remain if the player leaves the
  game
- Added android input-device detection log messages for debugging
- Android asset-sync phase (completing install...) now emits log output for
  debugging.

### 1.5.24 (20163)

- Upgraded Python from version 3.7 to 3.8. This is a substantial change (though
  nothing like the previous update from 2.7 to 3.7) so please holler if anything
  is broken. These updates will happen once every year or two now...
- Windows debug builds now use Python debug libraries. This should hopefully
  catch more errors that would otherwise go undetected and potentially cause
  crashes.
- Switched windows builds to use 'fast' mode math instead of 'strict'. This
  should make the game run more efficiently (similar modes are already in use on
  other platforms) but holler if any odd breakage happens such as things falling
  through floors (more often than the occasional random fluke-y case that
  happens now).
- Added `_ba.can_display_full_unicode()` for any code that wants to avoid
  printing things that won't show up locally.
- Now pulling some classes such as Literal and Protocol from typing instead of
  `typing_extensions` (they were officially added to Python in 3.8)
- Double taps/clicks now work properly on widgets nested under a scroll-widget
  on mobile (so, for example, replays can now be double-clicked to view them)

### 1.5.23 (20146)

- Fixed the shebang line in `bombsquad_server` file by using `-S` flag for
  `/usr/bin/env`.
- Fixed a bug with hardware keyboards emitting extra characters in the in-game
  console (~ or F2)
- Added support for 'plugin' mods and user controls to configure them in
  settings-\>advanced-\>plugins.
- Renamed `selection_loop_to_parent` to `selection_loops_to_parent` in widget
  calls.
- Added `selection_loops_to_parent`, `border`, `margin`, `claims_left_right`,
  and `claims_tab` args to ba.columnwidget().
- Column-widget now has a default `border` of 0 (explicitly pass 2 to get the
  old look).
- Column-widget now has a default `margin` of 10 (explicitly pass 0 to get the
  old look).
- Added `selection_loops_to_parent`, `claims_left_right`, and `claims_tab` args
  to ba.scrollwidget.
- Added `selection_loops_to_parent`, `claims_left_right`, and `claims_tab` args
  to ba.rowwidget.
- Added `claims_left_right` and `claims_tab` to ba.hscrollwidget().
- Default widget `show_buffer` is now 20 instead of 0 (causes scrolling to stay
  slightly ahead of widget selection). This can be overridden with the
  ba.widget() call if anything breaks.
- Relocated ba.app.uiscale to ba.app.ui.uiscale.
- Top level settings window now properly saves/restores its state again.
- Added Emojis to the Internal Game Keyboard.
- Added continuous CAPITAL letters typing feature in the Internal Game Keyboard.

### 1.5.22 (20139)

- Button and key names now display correctly again on Android (and are cleaned
  up on other platforms too).

### 1.5.21 (20138)

- Added a UI subsystem at ba.app.ui (containing globals/functionality that was
  previously directly under ba.app). And hopefully added a fix for rare state of
  two main menus appearing on-screen at once.
- Added options in the 'Advanced' section to disable camera shake and camera
  gyroscope motion.

### 1.5.20 (20126)

- The ba.Session.teams and ba.Session.players lists are now
  ba.Session.sessionteams and ba.Session.sessionplayers. This is to help keep it
  clear that a Team/Player and a SessionTeam/SessionPlayer are different things
  now.
- Disconnecting an input-device now immediately removes the player instead of
  doing so in the next cycle; this prevents possible issues where code would try
  to access player.inputdevice before the removal happens which would lead to
  errors.
- Updated mac prefab builds to point at homebrew's python@3.7 package now that
  3.8 has been made the default.
- Fixed an issue where adding/deleting UI widgets within certain callbacks could
  cause a crash.
- Fixed a case where an early fatal error could lead to a hung app and no error
  dialog.
- Added environment variables which can override UI scale for testing. Set
  `BA_FORCE_UI_SCALE` to small, medium or large.
- Added a ba.UIScale enum. The value at ba.app.uiscale replaces the old
  `ba.app.interface_type`, `ba.app.small_ui`, and `ba.app.med_ui` values.
- Emoji no longer display in-game with a washed-out appearance. If there are any
  places in-game where bright-colored emoji become distracting, please holler.
- `_ba.get_game_roster()` now includes `account_id` which is the validated
  account id of all clients (will be None until completes). Also, a few keys are
  renamed: `specString->spec_string` and `displayString->display_string`.

### 1.5.19 (20123)

- Cleaned up some bomb logic to avoid weird corner-cases such as land-mine
  explosions behaving like punches when set off by punches or bombs potentially
  resulting in multiple explosions when triggered by multiple other bombs
  simultaneously. Holler if anything explosion-related seems off now.
- Reactivated and cleaned up fatal-error message dialogs; they should now show
  up more consistently and on more platforms when something catastrophic happens
  instead of getting a silent crash.
- Certain hardware buttons on Android which stopped working in 1.5 should now be
  working again...

### 1.5.18 (20108)

- A bit of project cleanup; tools/snippets is now tools/pcommand, etc.
- More minor bug fixes and crash/bug-logging improvements.

### 1.5.17 (20102)

- More cleanup to logging and crash reporting system.
- Various other minor bug fixes...

### 1.5.16 (20099)

- Hopefully finally fixed that pesky crash bug on score submissions.

### 1.5.14 (20096)

- Fixed Android VR version failing to launch.
- More bug fixing and crash reporting improvements.

### 1.5.13 (20095)

- Hopefully fixed an elusive random crash on android that popped up recently.
- Misc bug fixes.

### 1.5.12 (20087)

- Improved exception handling and crash reporting.
- Misc bug fixes.

### 1.5.11 (20083)

- Fixed a freeze in the local network browser.

### 1.5.10 (20083)

- Streamlined C++ layer bootstrapping process a bit.
- Creating sys scripts via ba.modutils now works properly.
- Custom soundtracks should now work again under Android 10.
- Misc other bug fixes.

### 1.5.9 (20082)

- Reduced some hitches when clicking on certain buttons in the UI
- Fixed an issue where very early keyboard/controller connects/disconnects could
  get lost on android.
- `ba._modutils` is now ba.modutils since it is intended to be publicly
  accessible.
- drop-down console is now properly accessible again via android hardware
  keyboards (\` key)
- Other minor bug fixes..

### 1.5.8 (20079)

- Fixed an issue where touch controls or sound settings values could look like
  0.8999999999. Please holler if you see this anywhere else.
- Fixed a potential crash when tapping the screen before the game is fully
  inited.
- Restored the correct error message in the 'Google Play' connection tab from
  1.4 (I am actively working on a replacement)
- Other minor bug fixes.

### 1.5.7 (20077)

- Fixed an issue where co-op score screen rating could look like '
  3.9999999999999'
- Other minor bug fixes.

### 1.5.6 (20075)

- Lots of internal event-handling cleanup/reorganization in preparation for
  Android 1.5 update.
- Lots of low level input handling cleanup, also related to Android 1.5 version.
  Please holler if keyboard/game-controllers/etc. are behaving odd on any
  platforms.
- Now including Android test builds for the first time since 1.5. These have not
  been thoroughly tested yet so please holler with anything that is obviously
  broken.
- Mouse wheel now works in manual camera mode on more platforms.
- Server scripts now run in opt mode in release builds, so they can use bundled
  .opt-1.pyc files.
- Fixes a potential crash in the local network browser.
- Fixes an issue where Hockey Pucks would not show up in network games.
- More misc bug fixes and tidying.

### 1.5.5 (20069)

- Cleaned up Windows version packaging.
- More misc bug fixes.

### 1.5.4 (20067)

- Should now work properly with non-ascii paths on Windows (for real this time).
- Note that Windows game data is now stored under 'Local' appdata instead of '
  Roaming'; if you have an old installation with data you want to preserve, you
  may want to move it over manually.
- Misc cleanup and minor bug fixes.

### 1.5.3 (20065)

- Improved handling of non-ascii characters in file paths on Windows.

### 1.5.2 (20063)

- Fixes an issue with controls not working correctly in net-play between 1.4.x
  and 1.5.x.
- Tidied up onslaught code a bit.
- Fixes various other minor bugs.

### 1.5.1 (20062)

- Windows server now properly displays color when run by double-clicking the
  .bat file.
- Misc bug fixes.

### 1.5.0 (20001)

- This build contains about 2 years worth of MAJOR internal refactoring to
  prepare for the future of BombSquad. As a player this should not (yet) look
  different from 1.4, but for modders there is a lot new. See the rest of these
  change entries or visit [ballistica.net](https://ballistica.net) for more
  info.
- Ported the entire scripting layer from Python 2 to Python 3 (currently at 3.7,
  and I intend to keep this updated to the latest widely-available release).
  There's some significant changes going from python 2 to 3 (new print
  statement, string behavior, etc.), but these are well documented online, so
  please read up as needed. This should provide us some nice benefits and
  future-proofs everything. (my janky 2.7 custom Python builds were getting a
  little long in the tooth).
- Refactored all script code to be PEP8 compliant (Python coding standards).
  Basically, this means that stuff that was camel-case (fooBar) is now a single
  word or underscores (`foobar` / `foo_bar`). There are a few minor exceptions
  such as existing resource and media filenames, but in general old code can be
  ported by taking a pass through and killing the camel-case. I know this is a
  bit of a pain in the ass, but it'll let us use things like Pylint and just be
  more consistent with the rest of the Python world.
- On a related note, I'm now using 'yapf' to keep my Python code formatted
  nicely (using pep8 style); I'd recommend checking it out if you're doing a lot
  of scripting as it's a great time-saver.
- On another related note, I'm trying to confirm to Google's recommendations for
  Python code (search 'Google Python Style Guide'). There are some good bits of
  wisdom in there, so I recommend at least skimming through it.
- And as one last related note, I'm now running Pylint on all my own Python
  code. Highly recommended if you are doing serious scripting, as it can make
  Python almost feel as type-safe as C++.
- The minimum required android version will now be 5.0 (a requirement of the
  Python 3 builds I'm using)
- Minimum required macOS version is now 10.13 (for similar reasons)
- 'bsInternal' module is now `_ba` (better lines up with standard Python
  practices)
- bs.writeConfig() and bs.applySettings() are no more. There is now
  ba.app.config which is basically a fancy dict class with some methods added
  such as commit() and apply()
- bs.getEnvironment() is no more; the values there are now available through
  ba.app (see notes down further)
- Fixed the mac build so command line input works again when launched from a
  terminal
- Renamed 'exceptionOnNone' arg to 'doraise' in various calls.
- bs.emitBGDynamics() is now ba.emitfx()
- bs.shakeCamera() is now ba.camerashake()
- Various other minor name changes (bs.getUIBounds() -> ba.app.ui_bounds, etc.).
  I'm keeping old and new Python API docs around for now, so you can compare as
  needed.
- Renamed bot classes based on their actions instead of their appearances (ie:
  PirateBot -> ExplodeyBot)
- bs.getSharedObject() is now ba.stdobj()
- Removed bs.uni(), bs.utf8(), `bs.uni_to_ints()`, and `bs.uni_from_ints()`
  which are no longer needed due to Python 3's better string handling.
- Removed bs.SecureInt since it didn't do much to slow down hackers and hurts
  code readability.
- Renamed 'finalize' to 'expire' for actors and activities. 'Finalize' sounds
  too much like a destructor, which is not really what that is.
- bs.getMapsSupportingPlayType() is now simply ba.getmaps(). I might want to add
  more filter options to it besides just play-type, hence the renaming.
- Changed the concept of 'game', 'net', and 'real' times to 'sim', 'base', and '
  real'. See time function docs for specifics. Also cleared up a few ambiguities
  over what can be used where.
- I'm converting all scripting functions to operate on floating-point seconds by
  default instead of integer milliseconds. This will let us support more
  accurate simulations later and is just cleaner I feel. To keep existing calls
  working you should be able to add timeformat='ms' and you'll get the old
  behavior (or multiply your time values by 0.001). Specific notes listed below.
- ba.Timer now takes its 'time' arg as seconds instead of milliseconds. To port
  old calls, add: timeformat='ms' to each call (or multiply your input by 0.001)
- ba.animate() now takes times in seconds and its 'driver' arg is now 'timetype'
  for consistency with other time functions. To port existing code you can pass
  timeformat='ms' to keep the old milliseconds based behavior.
- ditto for `ba.animate_array()`
- ba.Activity.end() now takes seconds instead of milliseconds as its delay arg.
- TNTSpawner now also takes seconds instead of milliseconds for `respawn_time`.
- There is a new ba.timer() function which is used for all one-off timer
  creation. It has the same args as the ba.Timer() class constructor.
- bs.gameTimer() is no more. Pass timeformat='ms' to ba.timer() if you need to
  recreate its behavior.
- bs.netTimer() is no more. Pass timetype='base' and timeformat='ms' to
  ba.timer() if you need to recreate its behavior.
- bs.realTimer() is no more. Pass timetype='real' and timeformat='ms' to
  ba.timer() if you need to recreate its behavior.
- There is a new ba.time() function for getting time values; it has consistent
  args with the new ba.timer() and ba.Timer() calls.
- bs.getGameTime() is no more. Pass timeformat='ms' to ba.time() if you need to
  recreate its behavior.
- bs.getNetTime() is no more. Pass timetype='base' and timeformat='ms' to
  ba.time() if you need to recreate its behavior.
- bs.getRealTime() is no more. Pass timetype='real' and timeformat='ms' to
  ba.time() if you need to recreate its behavior.
- bs.getTimeString() is now just ba.timestring(), and accepts seconds by default
  (pass timeformat='ms' to keep old calls working).
- bs.callInGameThread() has been replaced by an optional `from_other_thread` arg
  for ba.pushcall()
- There is now a special `ba.UNHANDLED` value that handlemessage() calls should
  return any time they don't handle a passed message. This will allow fallback
  message types and other nice things in the future.
- Wired the boolean operator up to ba.Actor's exists() method, so now a simple "
  if mynode" will do the right thing for both Actors and None values instead of
  having to explicitly check for both.
- Ditto for ba.Node; you can now just do 'if mynode' which will do the right
  thing for both a dead Node or None.
- Ditto for ba.InputDevice, ba.Widget, ba.Player
- Added a bs.App class accessible via ba.app; will be migrating global app
  values there instead of littering python modules with globals. The only
  remaining module globals should be all-caps public 'constants'
- 'Internal' methods and classes living in `_ba` and elsewhere no longer start
  with underscores. They are now simply marked with '(internal)' in their
  docstrings.  'Internal' bits are likely to have janky interfaces and can
  change without warning, so be wary of using them. If you find yourself
  depending on some internal thing often, please let me know, and I can try to
  clean it up and make it 'public'.
- bs.getLanguage() is no more; that value is now accessible via ba.app.language
- bs.Actor now accepts an optional 'node' arg which it will store as `self.node`
  if passed. Its default DieMessage() and exists() handlers will use `self.node`
  if it exists. This removes the need for a separate NodeActor() for simple
  cases.
- bs.NodeActor is no more (it can simply be replaced with ba.Actor())
- bs.playMusic() is now ba.setmusic() which better fits its functionality (it
  sometimes just continues playing or stops playing).
- The bs.Vector class is no more; in its place is a shiny new ba.Vec3 which is
  implemented internally in C++ so its nice and speedy. Will probably update
  certain things like vector node attrs to support this class in the future
  since it makes vector math nice and convenient.
- Ok you get the point... see [ballistica.net](https://ballistica.net) for more
  info on these changes.

### 1.4.155 (14377)

- Added protection against a repeated-input attack in lobbies.

### 1.4.151 (14371)

- Added Chinese-Traditional language and improved translations for others.

### 1.4.150 (14369)

- Telnet port can now be specified in the config
- Telnet socket no longer opens on headless build when telnet access is off (
  reduces DoS attack potential)
- Added a `filter_chat_message()` call which can be used by servers to
  intercept/modify/block all chat messages.
- `bsInternal._disconnectClient()` now takes an optional banTime arg (in
  seconds, defaults to old value of 300).

### 1.4.148 (14365)

- Added a password option for telnet access on server builds

### 1.4.147 (14364)

- Fixes an issue where a client rejoining a server after being kicked could get
  stuck in limbo
- Language updates
- Increased security on games that list themselves as public. All joining
  players must now be validated by the master server, or they will be kicked.
  This will let me globally ban accounts or ip addresses from joining games to
  avoid things like ad spam-bots (which has been a problem this week).
- Added a max chat message length of 100
- Clients sending abnormal amounts of data to the server will now be auto-kicked

### 1.4.145 (14351)

- Mostly a maintenance release (real work is happening in the 1.5/2.0 branch) -
  minor bug fixes and a few language updates.
- Google deprecated some older SDKs, so the minimum Android supported by this
  build is now 4.4

### 1.4.144 (14350)

- Added Greek translation

### 1.4.143 (14347)

- Fixed an issue where server names starting and ending with curly brackets
  would display incorrectly
- Fixed an issue where an android back-button press very soon after launch could
  lead to a crash
- Fixed a potential crash if a remove-player call is made for a player that has
  already left

### 1.4.142 (14346)

- Fixed an issue in my rigid body simulation code which could lead to crashes
  when large numbers of bodies are present

### 1.4.141 (14344)

- Fixed a longstanding bug in my huffman compression code that could cause an
  extra byte of unallocated memory to be read, leading to occasional crashes

### 1.4.140 (14343)

- Fixed a few minor outstanding bugs from the 1.4.139 update

### 1.4.139 (14340)

- Added an option to the server builds to point to a server-stats webpage that
  will show up as an extra link in the server browser (in client 1.4.139+)
- Removed the language column from the server browser. This was more relevant
  back when all clients saw the game in the server's language, and is nowadays
  largely just hijacked for silly purposes. Holler if you miss it.
- Server list now re-pings servers less often and averages ping results to
  reduce the amount of jumping around in the list. Please holler if this feels
  off.
- Added some slick new client-verification tech. Going forward it should be
  pretty much impossible to fool a server into thinking you are using a
  different account than you really are.
- Added a `get_account_id()` method to the bs.Player class. This will return a
  player's signed-in account-id (when it can be verified for certain)

### 1.4.138 (14336)

- Removed SDL library from the server builds, so that's one less dependency that
  needs to be installed when setting up a linux server

### 1.4.137 (14331)

- Lots of internal code cleanup and reorganization before I dig into networking
  rework (hopefully didn't break too much)
- Slowly cleaning up Python files (hoping to move closer to PEP 8 standards and
  eventually Python 3)
- Added Hindi language
- Cleared out some old build types (farewell OUYA; thanks for the memories)
- Added support for meshes with > 65535 verts (though turns out OpenGL ES2
  doesn't support this so moot at the moment)

### 1.4.136 (14327)

- Updated 'kiosk mode' functionality (used for simple demo versions of the game)
- Lots of work getting VR builds up to date
- Fixed an issue where 'report this player' window would show up behind the
  window that spawned it

### 1.4.135 (14324)

- Updated various SDKs for the android build (now building against api 27,
  removed inmobi ads, etc.)

### 1.4.134 (14322)

- Fixed an issue where the internal keyboard would sometimes show up behind game
  windows
- Fixed an issue where UI widget selection would sometimes loop incorrectly at
  window edges
- Fixed an issue where overlay windows such as the quit dialog would allow
  clicks to pass through to regular windows under them
- Work on 2.0 UI (not yet enabled)

### 1.4.133 (14318)

- Pro upgrade now unlocks custom team names and colors in teams mode
- Added a 'Mute Chat' option for completely ignoring incoming chat messages
- Fixed a longstanding issue where player-selectors could get 'stuck'
- Pro upgrade now unlocks a new exact color picker option for character
  colors/highlights/etc.
- Added new flag icons to the store: Iran, Poland, Argentina, Philippines, and
  Chile
- Added an option for translators to be notified by the game whenever there are
  new phrases to translate (under settings->advanced)
- Increased quality on some models, textures and audio
- Assault no longer counts dead bodies hitting the flag as scores
- Replay speed can now be controlled with -/= keys (on devices with keyboards)
- Added Serbian language
- Remote app connections are now disabled by default on server builds
- Server wrapper script now supports python 3 in addition to python 2. (Python 3
  support in the actual game will still be awhile)
- Added better crash reporting on Android, so I can hopefully fix bugs more
  quickly.
- bs.Lstr() can now take a 'fallbackResource' or 'fallbackValue' argument; the
  old 'fallback' argument is deprecated
- Removed the long-since-deprecated bs.translate() and bs.getResource() calls (
  bs.Lstr() should be used for all that stuff now)
- Removed some deprecated functions from GameActivity:
  getInstanceScoreBoardNameLocalized(), getInstanceNameLocalized(),
  getConfigDescriptionLocalized()

### 1.4.132 (14316)

- Fixed an issue where the game could get stuck in a black screen after resuming
  on Android

### 1.4.131 (14315)

- Replay playback speed can now be adjusted in the menu
- Fixed an issue with touch controls showing up while in party chat
- Fixed issues with the new anti-turbo logic when hosting

### 1.4.130 (14313)

- New character: Grumbledorf the Wizard
- Improved public party browsing performance
- Added protections against turbo exploits when hosting
- Fixed issues with some Android controllers not being recognized

### 1.4.126 (14307)

- Improved keyboard and mouse support on Android

### 1.4.125 (14306)

- Added support for keyboards on Android
- Added support for desktop-like environments such as Samsung DeX and
  Chromebooks on Android
- Optimized game UI for wide-screen layouts such as the Galaxy Note 8

### 1.4.121 (14302)

- Added support for account unlinking

### 1.4.118 (14298)

- Added 64-bit arm binary to Android builds

### 1.4.111 (14286)

- BombSquad Pro now unlocks 2 additional characters
- multi-line chat messages are now clamped down to 1 line; should prevent
  annoying multi-line fullscreen message spam

### 1.4.106 (14280)

- the game will now only print 'game full' player-rejection messages to the
  client attempting to join; should reduce annoying message spam.

### 1.4.101 (14268)

- the game will now attempt to load connecting players' profiles and info from
  my master-server instead of trusting the player; should reduce cheating

### 1.4.100 (14264)

- added a 'playlistCode' option in the server config which corresponds with
  playlist codes added in BombSquad 1.4.100 (used for sharing playlists with
  friends). Now you can create a custom playlist, grab a code for it, and easily
  use it in a dedicated server.

### 1.4.99 (14252)

- there is now a forced 10-second delay between a player leaving the game and
  another player from that same client joining the game. This should fix the
  exploit where players were leaving and re-joining to avoid spawn times.
- most in-game text is now set as bs.Lstr() values so that they show up in the
  client's own language instead of the server's There are currently a few
  exceptions such as time values which I need to address.

### 1.4.98 (14248)

- added kick-votes that can be started by any client. Currently, a client must
  type '0' or '1' in chat to vote, but I'll add buttons for them soon.
- modified text nodes so that they can display in each client's own language.  (
  most text nodes don't do this yet but the capability is there). However, this
  means older clients can't connect to 1.4.98 servers, so you may want to stick
  with an older server for a bit until the userbase gets more updated.

### 1.4.97 (14247)

- back to displaying long names in more places; mainly just the in-game ones are
  clamped... trying to find a good balance...

### 1.4.97 (14246)

- public party names will now show up for clients as the title of their party
  windows instead of "My Party" and also during connect/disconnect (requires
  client 14246+)
- server now ignores 'locked' states on maps/game-types, so meteor-shower,
  target-practice, etc. should work now

### 1.4.97 (14244)

- kicked players are now unable to rejoin for a several minutes

### 1.4.96 (14242)

- chat messages and the party window now show player names instead of account
  names when possible
- server now clamps in-game names to 8 characters so there's some hope of
  reading them in-game. Can loosen this or add controls for how clamping happens
  if need be.

### 1.4.96 (14241)

- added an automatic chat-block to combat chat spammers. Block durations start
  at 10 seconds and double with each repeat offense

### 1.4.95 (14240)

- fixed an issue where a single account could not be used to host multiple
  parties at once

### 1.4.95 (14236)

- added a port option to the config, so it's now possible to host multiple
  parties on one machine (note that bombsquad 1.4.95+ is required to connect
  ports aside from 43210)

### 1.4.95 (14234)

- fixed a bug that could cause the Windows version to freeze randomly after a
  while

### 1.4.95 (14233)

- bombsquad (both `bs_headless` and regular) now reads commands from
  standard input, making it easier to run commands via scripts or the terminal
- server now runs using a 'server' account-type instead of the local 'device'
  account. (avoids daily-ticket-reward messages and other stuff that's not
  relevant to servers)
- the server script now passes args to the game as a json file instead of
  individual args; this should keep things cleaner and more expandable
- the `bombsquad_server` script also now reads commands from stdin, allowing
  reconfiguring server settings on the fly
- added more options such as the ability to set game series lengths and to host
  a non-public party

### 1.4.94

- now have mac, windows, and both 32 and 64-bit linux server builds
- added an optional config.py file that can be used instead of modifying the
  server script itself
- added an autoBalanceTeams option for teams games
- people joining and leaving the party are no longer announced (too much noise)

### 1.4.93

- should now properly allow clients to use their unlocked characters
- added an option to enable telnet access
