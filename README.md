<img src="https://files.ballistica.net/ballistica_media/ballistica_logo_half.png" height="50">

***bal·lis·tic***: physics of an object in motion; behaving like a projectile.

***-ica***: collection of things relating to a specific theme.

![](https://github.com/efroemling/ballistica/workflows/CI/badge.svg)

The Ballistica project is the foundation for [BombSquad](https://www.froemling.net/apps/bombsquad) and potentially other future projects.

[Head to the project wiki to get started](https://github.com/efroemling/ballistica/wiki), or learn more about the project below.

### Project Goals

* **Do one thing and do it well**

  Ballistica is not aiming to be a general purpose game engine. Rather, its goal is to support creating one particular type of experience: 'physics based multiplayer action on small diorama-like environments built from real-world objects'. If you've got something you'd like to create that can fit within that box (as BombSquad itself does), give Ballistica a look. Of course, there is nothing preventing you from going and building an FPS out of this stuff, but I wouldn't recommend it.

* **Python tomfoolery**

   Ballistica is built on a C++ core for performance-sensitive code with a Python layer for high level game/app logic. This Python layer is designed to be mucked with. Users can override core game functionality, write their own mini games, or anything else they can dream up, either by directly accessing files on disk or by working through an integrated web-based editor. It can be a fun way to learn Python without the danger of getting actual work done.

* **Physics-y goodness**

   I love playing with physics simulations, and Ballistica was built partly to scratch this itch. Though the game physics in BombSquad have stayed largely unchanged for a while, my future plans for the engine lean heavily on making this more flexible and open-ended, opening up lots of fun multiplayer physics-y potential. Stay tuned...

* **Community**

   BombSquad started as a 'just for fun' project to play with my friends, and I want to keep that spirit alive as the Ballistica project moves forward. Whether this means making it easier to share mods, organize tournaments, join up with friends, teach each other some Python, or whatever else. Life is short; let's play some games. Or make them. Maybe both.
  
### Frequently Asked Questions
* **Q: What's with this name? Is it BombSquad or Ballistica?**
  * A: BombSquad is the game. Ballistica is the engine.

* **Q: Does this mean BombSquad is open source?**
  * A: Yes and no. All code contained in this repo is MIT licensed and free for use anywhere. This includes game scripts, pipeline tools, and most of the binary engine sources. Anything not directly contained in this repository, however, even if automatically downloaded by build scripts, is still proprietary and cannot be redistributed without explicit consent. This includes assets and prebuilt libraries/binaries. So in a nutshell: create and share mods or use any of this code in your own projects, but please don't distribute your own complete copies of BombSquad without permission. Please email support@froemling.net if you have any questions about this.

* **Q: When are you adding more maps/characters/minigames/etc. to BombSquad!?!?**
  * A: Check out the [Ballistica Roadmap](https://github.com/efroemling/ballistica/wiki/Roadmap) to get a sense of what's planned for when. And for the record, the answer to that particular question is basically '1.8'.

* **Q: When will BombSquad be released on iOS / Steam / Switch / XBox / Playstation / My Toaster??**
  * A: The 2.0 update will be the big 'relaunch' release and the plan is to launch on at least iOS and Steam at that time. I'm trying to get there as fast as I can. As far as consoles, I'd love to and hope to at some point but have nothing to announce just yet. See the [Ballistica Roadmap](https://github.com/efroemling/ballistica/wiki/Roadmap) for more details or check the [Ballistica Downloads](https://ballistica.net/downloads) page for early test builds on some platforms.
  
