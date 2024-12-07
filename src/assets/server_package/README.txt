To run this, simply cd into this directory and run ./ballisticakit_server
(on mac or linux) or launch_ballisticakit_server.bat (on windows).
You'll need to open a UDP port (43210 by default) so that the world can
communicate with your server.
You can configure your server by editing the config.toml file.
(if you only see config_template.toml, you can copy/rename that to config.toml)

Platform-Specific Notes:

Mac:
- The server should run on the most recent macOS (and possibly older versions,
  though I have not checked)
- It now requires homebrew Python 3, so you'll need that installed
  (brew install python3).

Linux (x86_64):
- Server binaries are currently compiled against Ubuntu 22 LTS. 

Raspberry Pi:
- The server binary was compiled on a Raspberry Pi 4 running Raspbian Buster.

Windows:
- You may need to run dist/Vc_redist.x64.exe to install support libraries if
  the app quits with complaints of missing DLLs

Please give me a holler at support@froemling.net or check out
ballistica.net/wiki if you run into any problems.

Enjoy!
-Eric
