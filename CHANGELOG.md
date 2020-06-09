### 1.5.2 (20063)
- Fixes an issue with controls not working correctly in net-play between 1.4.x and 1.5.x.
- Tidied up onslaught code a bit.
- Fixes various other minor bugs.

### 1.5.1 (20062)
- Windows server now properly displays color when run by double clicking the .bat file.
- Misc bug fixes.

### 1.5.0 (20001)
- This build contains about 2 years worth of MAJOR internal refactoring to prepare for the future of BombSquad. As a player this should not (yet) look different from 1.4, but for modders there is a lot new. See the rest of these change entries or visit ballistica.net for more info.
- Ported the entire scripting layer from Python 2 to to Python 3 (currently at 3.7, and I intend to keep this updated to the latest widely-available release). There's some significant changes going from python 2 to 3 (new print statement, string behavior, etc), but these are well documented online, so please read up as needed.  This should provide us some nice benefits and future-proofs everything. (my janky 2.7 custom Python builds were getting a little long in the tooth).
- Refactored all script code to be PEP8 compliant (Python coding standards).  Basically, this means that stuff that was camel-case (fooBar) is now a single word or underscores (foobar / foo_bar).  There are a few minor exceptions such as existing resource and media filenames, but in general old code can be ported by taking a pass through and killing the camel-case.  I know this is a bit of a pain in the ass, but it'll let us use things like Pylint and just be more consistent with the rest of the Python world.
- On a related note, I'm now using 'yapf' to keep my Python code formatted nicely (using pep8 style); I'd recommend checking it out if you're doing a lot of scripting as its a great time-saver.
- On another related note, I'm trying to confirm to Google's recommendations for Python code (search 'Google Python Style Guide'). There are some good bits of wisdom in there so I recommend at least skimming through it.
- And as one last related note, I'm now running Pylint on all my own Python code. Highly recommended if you are doing serious scripting, as it can make Python almost feel as type-safe as C++.
- The minimum required android version will now be 5.0 (a requirement of the Python 3 builds I'm using)
- Minimum required macOS version is now 10.13 (for similar reasons)
- 'bsInternal' module is now '_ba' (better lines up with standard Python practices)
- bs.writeConfig() and bs.applySettings() are no more. There is now ba.app.config which is basically a fancy dict class with some methods added such as commit() and apply()
- bs.getEnvironment() is no more; the values there are now available through ba.app (see notes down further)
- Fixed the mac build so command line input works again when launched from a terminal
- Renamed 'exceptionOnNone' arg to 'doraise' in various calls.
- bs.emitBGDynamics() is now ba.emitfx()
- bs.shakeCamera() is now ba.camerashake()
- Various other minor name changes (bs.getUIBounds() -> ba.app.uibounds, etc).  I'm keeping old and new Python API docs around for now so you can compare as needed.
- Renamed bot classes based on their actions instead of their appearances (ie: PirateBot -> ExplodeyBot)
- bs.getSharedObject() is now ba.stdobj()
- Removed bs.uni(), bs.utf8(), bs.uni_to_ints(), and bs.uni_from_ints() which are no longer needed due to Python 3's better string handling.
- Removed bs.SecureInt since it didn't do much to slow down hackers and hurts code readability.
- Renamed 'finalize' to 'expire' for actors and activities. 'Finalize' sounds too much like a destructor, which is not really what that is.
- bs.getMapsSupportingPlayType() is now simply ba.getmaps(). I might want to add more filter options to it besides just play-type, hence the rename.
- Changed the concept of 'game', 'net', and 'real' times to 'sim', 'base', and 'real'. See time function docs for specifics.  Also cleared up a few ambiguities over what can be used where.
- I'm converting all scripting functions to operate on floating-point seconds by default instead of integer milliseconds. This will let us support more accurate simulations later and is just cleaner I feel. To keep existing calls working you should be able to add timeformat='ms' and you'll get the old behavior (or multiply your time values by 0.001). Specific notes listed below.
- ba.Timer now takes its 'time' arg as seconds instead of milliseconds. To port old calls, add: timeformat='ms' to each call (or multiply your input by 0.001)
- ba.animate() now takes times in seconds and its 'driver' arg is now 'timetype' for consistency with other time functions. To port existing code you can pass timeformat='ms' to keep the old milliseconds based behavior.
- ditto for ba.animate_array()
- ba.Activity.end() now takes seconds instead of milliseconds as its delay arg.
- TNTSpawner now also takes seconds instead of milliseconds for respawn_time.
- There is a new ba.timer() function which is used for all one-off timer creation. It has the same args as the ba.Timer() class constructor.
- bs.gameTimer() is no more. Pass timeformat='ms' to ba.timer() if you need to recreate its behavior.
- bs.netTimer() is no more. Pass timetype='base' and timeformat='ms' to ba.timer() if you need to recreate its behavior.
- bs.realTimer() is no more. Pass timetype='real' and timeformat='ms' to ba.timer() if you need to recreate its behavior.
- There is a new ba.time() function for getting time values; it has consistent args with the new ba.timer() and ba.Timer() calls.
- bs.getGameTime() is no more. Pass timeformat='ms' to ba.time() if you need to recreate its behavior.
- bs.getNetTime() is no more. Pass timetype='base' and timeformat='ms' to ba.time() if you need to recreate its behavior.
- bs.getRealTime() is no more. Pass timetype='real' and timeformat='ms' to ba.time() if you need to recreate its behavior.
- bs.getTimeString() is now just ba.timestring(), and accepts seconds by default (pass timeformat='ms' to keep old calls working).
- bs.callInGameThread() has been replaced by an optional 'from_other_thread' arg for ba.pushcall()
- There is now a special ba.UNHANDLED value that handlemessage() calls should return any time they don't handle a passed message.  This will allow fallback message types and other nice things in the future.
- Wired the boolean operator up to ba.Actor's exists() method, so now a simple "if mynode" will do the right thing for both Actors and None values instead of having to explicitly check for both.
- Ditto for ba.Node; you can now just do 'if mynode' which will do the right thing for both a dead Node or None.
- Ditto for ba.InputDevice, ba.Widget, ba.Player
- Added a bs.App class accessible via ba.app; will be migrating global app values there instead of littering python modules with globals. The only remaining module globals should be all-caps public 'constants'
- 'Internal' methods and classes living in _ba and elsewhere no longer start with underscores.  They are now simply marked with '(internal)' in their docstrings.  'Internal' bits are likely to have janky interfaces and can change without warning, so be wary of using them.  If you find yourself depending on some internal thing often, please let me know and I can try to clean it up and make it 'public'.
- bs.getLanguage() is no more; that value is now accessible via ba.app.language
- bs.Actor now accepts an optional 'node' arg which it will store as self.node if passed.  Its default DieMessage() and exists() handlers will use self.node if it exists.  This removes the need for a separate NodeActor() for simple cases.
- bs.NodeActor is no more (it can simply be replaced with ba.Actor())
- bs.playMusic() is now ba.setmusic() which better fits its functionality (it sometimes just continues playing or stops playing).
- The bs.Vector class is no more; in its place is a shiny new ba.Vec3 which is implemented internally in C++ so its nice and speedy.  Will probably update certain things like vector node attrs to support this class in the future since it makes vector math nice and convenient.
- Ok you get the point.. see ballistica.net for more info on these changes.

### 1.4.155 (14377)
- Added protection against a repeated-input attack in lobbies.

### 1.4.151 (14371)
- Added Chinese-Traditional language and improved translations for others.

### 1.4.150 (14369)
- Telnet port can now be specified in the config
- Telnet socket no longer opens on headless build when telnet access is off (reduces DoS attack potential)
- Added a filter_chat_message() call which can be used by servers to intercept/modify/block all chat messages.
- bsInternal._disconnectClient() now takes an optional banTime arg (in seconds, defaults to old value of 300).

### 1.4.148 (14365)
- Added a password option for telnet access on server builds

### 1.4.147 (14364)
- Fixes an issue where a client rejoining a server after being kicked could get stuck in limbo
- Language updates
- Increased security on games that list themselves as public. All joining players must now be validated by the master server or they will be kicked. This will let me globally ban accounts or ip addresses from joining games to avoid things like ad spam bots (which has been a problem this week).
- Added a max chat message length of 100
- Clients sending abnormal amounts of data to the server will now be auto-kicked

### 1.4.145 (14351)
- Mostly a maintenance release (real work is happening in the 1.5/2.0 branch) - minor bug fixes and a few language updates.
- Google deprecated some older SDKs, so the minimum Android supported by this build is now 4.4

### 1.4.144 (14350)
- Added Greek translation

### 1.4.143 (14347)
- Fixed an issue where server names starting and ending with curly brackets would display incorrectly
- Fixed an issue where an android back-button press very soon after launch could lead to a crash
- Fixed a potential crash if a remove-player call is made for a player that has already left

### 1.4.142 (14346)
- Fixed an issue in my rigid body simulation code which could lead to crashes when large numbers of bodies are present

### 1.4.141 (14344)
- Fixed a longstanding bug in my huffman compression code that could cause an extra byte of unallocated memory to be read, leading to occasional crashes

### 1.4.140 (14343)
- Fixed a few minor outstanding bugs from the 1.4.139 update

### 1.4.139 (14340)
- Added an option to the server builds to point to a server-stats webpage that will show up as an extra link in the server browser (in client 1.4.139+)
- Removed the language column from the server browser.  This was more relevant back when all clients saw the game in the server's language, and is nowadays largely just hijacked for silly purposes.  Holler if you miss it.
- Server list now re-pings servers less often and averages ping results to reduce the amount of jumping around in the list.  Please holler if this feels off.
- Added some slick new client-verification tech.  Going forward it should be pretty much impossible to fool a server into thinking you are using a different account than you really are.
- Added a 'get_account_id()' method to the bs.Player class.  This will return a player's signed-in account-id (when it can be verified for certain)

### 1.4.138 (14336)
- Removed SDL library from the server builds, so that's one less dependency that needs to be installed when setting up a linux server

### 1.4.137 (14331)
- Lots of internal code cleanup and reorganization before I dig into networking rework (hopefully didn't break too much)
- Slowly cleaning up Python files (hoping to move closer to to PEP 8 standards and eventually Python 3)
- Added Hindi language
- Cleared out some old build types (farewell OUYA; thanks for the memories)
- Added support for meshes with > 65535 verts (though turns out OpenGL ES2 doesn't support this so moot at the moment)

### 1.4.136 (14327)
- Updated 'kiosk mode' functionality (used for simple demo versions of the game)
- Lots of work getting VR builds up to date
- Fixed an issue where 'report this player' window would show up behind the window that spawned it

### 1.4.135 (14324)
- Updated various SDKs for the android build (now building against api 27, removed inmobi ads, etc)

### 1.4.134 (14322)
- Fixed an issue where the internal keyboard would sometimes show up behind game windows
- Fixed an issue where UI widget selection would sometimes loop incorrectly at window edges
- Fixed an issue where overlay windows such as the quit dialog would allow clicks to pass through to regular windows under them
- Work on 2.0 UI (not yet enabled)

### 1.4.133 (14318)
- Pro upgrade now unlocks custom team names and colors in teams mode
- Added a 'Mute Chat' option for completely ignoring incoming chat messages
- Fixed a longstanding issue where player-selectors could get 'stuck'
- Pro upgrade now unlocks a new exact color picker option for character colors/highlights/etc.
- Added new flag icons to the store: Iran, Poland, Argentina, Philippines, and Chile
- Added an option for translators to be notified by the game whenever there are new phrases to translate (under settings->advanced)
- Increased quality on some models, textures and audio
- Assault no longer counts dead bodies hitting the flag as scores
- Replay speed can now be controlled with -/= keys (on devices with keyboards)
- Added Serbian language
- Remote app connections are now disabled by default on server builds
- Server wrapper script now supports python 3 in addition to python 2. (Python 3 support in the actual game will still be a while)
- Added better crash reporting on Android so I can hopefully fix bugs quicker
- bs.Lstr() can now take a 'fallbackResource' or 'fallbackValue' argument; the old 'fallback' argument is deprecated
- Removed the long-since-deprecated bs.translate() and bs.getResource() calls (bs.Lstr() should be used for all that stuff now)
- Removed some deprecated functions from GameActivity: getInstanceScoreBoardNameLocalized(), getInstanceNameLocalized(), getConfigDescriptionLocalized()

### 1.4.132 (14316)
- Fixed an issue where the game could get stuck in a black screen after resuming on Android

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
- Added support for desktop-like environments such as Samsung DeX and Chromebooks on Android
- Optimized game UI for wide-screen layouts such as the Galaxy Note 8

### 1.4.121 (14302)
- Added support for account unlinking

### 1.4.118 (14298)
- Added 64 bit arm binary to Android builds

### 1.4.111 (14286)
- BallisticaCore Pro now unlocks 2 additional characters
- multi-line chat messages are now clamped down to 1 line; should prevent annoying multi-line fullscreen message spam

### 1.4.106 (14280)
- the game will now only print 'game full' player-rejection messages to the client attempting to join; should reduce annoying message spam.

### 1.4.101 (14268)
- the game will now attempt to load connecting players' profiles and info from my master-server instead of trusting the player; should reduce cheating

### 1.4.100 (14264)
- added a 'playlistCode' option in the server config which corresponds with playlist codes added in Ballisticacore 1.4.100 (used for sharing playlists with friends). Now you can create a custom playlist, grab a code for it, and easily use it in a dedicated server.

### 1.4.99 (14252)
- there is now a forced 10 second delay between a player leaving the game and another player from that same client joining the game.  This should fix the exploit where players were leaving and re-joining to avoid spawn times.
- most in-game text is now set as bs.Lstr() values so that they show up in the client's own language instead of the server's  There are currently a few exceptions such as time values which I need to address.

### 1.4.98 (14248)
- added kick-votes that can be started by any client.  currently a client must type '0' or '1' in chat to vote, but i'll add buttons for them soon.
- modified text nodes so they can display in each client's own language.  (most text nodes don't do this yet but the capability is there).  However this means older clients can't connect to 1.4.98 servers, so you may want to stick with an older server for a bit until the userbase gets more updated.

### 1.4.97 (14247)
- back to displaying long names in more places; mainly just the in-game ones are clamped..  trying to find a good balance..

### 1.4.97 (14246)
- public party names will now show up for clients as the title of their party windows instead of "My Party" and also during connect/disconnect (requires client 14246+)
- server now ignores 'locked' states on maps/game-types, so meteor-shower, target-practice, etc. should work now

### 1.4.97 (14244)
- kicked players are now unable to rejoin for a several minutes

### 1.4.96 (14242)
- chat messages and the party window now show player names instead of account names when possible
- server now clamps in-game names to 8 characters so there's some hope of reading them in-game. Can loosen this or add controls for how clamping happens if need be.

### 1.4.96 (14241)
- added an automatic chat-block to combat chat spammers. Blocks start at 10 seconds and double in duration for each repeat offense

### 1.4.95 (14240)
- fixed an issue where a single account could not be used to host multiple parties at once

### 1.4.95 (14236)
- added a port option to the config so its now possible to host multiple parties on one machine (note that ballisticacore 1.4.95+ is required to connect ports aside from 43210)

### 1.4.95 (14234)
- fixed a bug that could cause the windows version to freeze randomly after a while

### 1.4.95 (14233)
- ballisticacore (both bs_headless and regular) now reads commands from standard input, making it easier to run commands via scripts or the terminal
- server now runs using a 'server' account-type instead of the local 'device' account. (avoids daily-ticket-reward messages and other stuff that's not relevant to servers)
- the server script now passes args to the game as a json file instead of individual args; this should keep things cleaner and more expandable
- the ballisticacore_server script also now reads commands from stdin, allowing reconfiguring server settings on the fly
- added more options such as the ability to set game series lengths and to host a non-public party

### 1.4.94
- now have mac, windows, and both 32 and 64 bit linux server builds
- added an optional config.py file that can be used instead of modifying the server script itself
- added an autoBalanceTeams option for teams games
- people joining and leaving the party are no longer announced (too much noise)

### 1.4.93
- should now properly allow clients to use their unlocked characters
- added an option to enable telnet access
