<img src="https://files.ballistica.net/ballistica_media/ballistica_logo_half.png" height="50">

***bal·lis·tic***: physics of an object in motion; behaving like a projectile.

***-ica***: collection of things relating to a specific theme.

![](https://github.com/efroemling/ballistica/workflows/CI/badge.svg)

The Ballistica project is the foundation for the next generation of [BombSquad](http://bombsquadgame.com). It will be debuting with the upcoming 1.5 release of the game and lays the foundation for some of the big changes coming in 2.0.

[Head to the project wiki to get started](https://github.com/efroemling/ballistica/wiki), or learn more about the project below.

### Project Goals
* Cleanup
  * BombSquad's codebase, and especially its scripting layer, have grown a lot over its lifetime, but not always in a 'designed' way. It was overdue for a major refactoring, which should keep it more maintainable for years to come. Examples of this include breaking up the giant 15 thousand line bsUI.py file into a much cleaner individual subpackages and updating all code from Python 2.7 to 3.7.
* Provide modders and tinkerers with the best possible development environment
  * I've spent a lot of time incorporating auto-formatters, type-checkers, linters, and smart IDEs into my development workflow and have found them to be an enormous help. By sharing my setup here I hope to make them easily accessible to everyone.
* Improve transparency
  * I get a lot of "what's in the next update?" or "how is 2.0 coming?" questions. By working here in the open I hope to make many of these questions unnecessary.
* Increase community involvement
  * Provide a single place for tracking issues related to the engine/game
  * Allow people to submit their own bug fixes or improvements, making myself less of a bottleneck
  * Migrate modding documentation to this repo's wiki, allowing other modders to add their own bits of wisdom

### Frequently Asked Questions
* **Q: What's with the new name? Is BombSquad getting renamed?**
* A: No, BombSquad is still BombSquad. 'Ballistica' is simply the new name for the engine/app-framework. This way it can be used for other game/app projects without causing confusion. As a modder, the biggest change is that you will see a lot of 'ba' prefixes in the APIs as opposed to 'bs'. You may also see the word 'BallisticaCore' show up various places, which in actual releases will be replaced by 'BombSquad'.

* **Q: Does this mean BombSquad is open source?**
* A: Yes and no. All code contained in this repo is MIT licensed and free for use anywhere. This includes game scripts, pipeline tools, etc. In the future I hope to expand this to include at least some binary sources. Anything not included here, however, even if automatically downloaded by build scripts, is still copyrighted and cannot be redistributed without explicit consent. This includes assets and game binaries. So in general: create and share mods to your heart's content, but please don't distribute your own complete copy of the game.  Please email support@froemling.net if you have any questions.

* **Q: Will my existing BombSquad 1.4.x mods still work?**
* A: No. All mods will need to be explicitly updated to work with the new ballistica apis in 1.5+. This may or may not be a significant amount of work depending on the mod. I would highly suggest tinkering around with some of the new features in 1.5 such as type-safe Python and dynamic assets before attempting to port any old mods. You may also want to consider simply sticking with 1.4 versions for a while longer since they will still be fully supported, especially for server duties. The new ballistica apis may still be in significant flux for at least a while until the dust settles. This will all be worth it in the end, I promise!
