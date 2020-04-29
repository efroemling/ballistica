To run this, simply cd into this directory and run ./ballisticacore_server
(on mac or linux) or launch_ballisticacore_server.bat (on windows).
You'll need to open a UDP port (43210 by default) so that the world can
communicate with your server.
You can configure your server by creating a config.yaml file
(see config_template.yaml as a starting point)

Platform-Specific Notes:

Mac:
- The server should run on the most recent macOS (and possibly older versions,
  though I have not checked)
- It now requires homebrew Python 3, so you'll need that installed
  (brew install python3).

Linux (x86_64):
- Server binaries are currently compiled against Ubuntu 18 LTS. They depend
  on Python 3.7, so you may need to install that.
  This should just be something like "sudo apt install python3"

Raspberry Pi:
- The server binary was compiled on a Raspberry Pi 4 running Raspbian Buster.

Windows:
- You may need to run dist/Vc_redist.x64.exe to install support libraries if
  the app quits with complaints of missing DLLs

Please give me a holler at support@froemling.net if you run into any problems.

Enjoy!
-Eric
