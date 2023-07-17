### 1.7.23 (build 21171, api 8, 2023-07-16)

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
- The `ballisticakit_internal` precompiled library has been renamed to
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
  system browser is not available now has a qrcode and a copy button (where
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
  `ballisticakit_windows/build`.
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

- BallisticaKit Pro now unlocks 2 additional characters
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
  parties on one machine (note that ballisticakit 1.4.95+ is required to connect
  ports aside from 43210)

### 1.4.95 (14234)

- fixed a bug that could cause the Windows version to freeze randomly after a
  while

### 1.4.95 (14233)

- ballisticakit (both `bs_headless` and regular) now reads commands from
  standard input, making it easier to run commands via scripts or the terminal
- server now runs using a 'server' account-type instead of the local 'device'
  account. (avoids daily-ticket-reward messages and other stuff that's not
  relevant to servers)
- the server script now passes args to the game as a json file instead of
  individual args; this should keep things cleaner and more expandable
- the `ballisticakit_server` script also now reads commands from stdin, allowing
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
