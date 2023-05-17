# Ballistica Project Configuration

This directory contains overall configuration files for the project.

Noteworthy files:
- [projectconfig.json](projectconfig.json): Top level settings for the project.
  Various tools look for values here.
- [spinoffconfig.json](spinoffconfig.json): Configures how this project can be
  spun off into other projects and/or what it inherits from a parent project.
- **localconfig.json**: Optional file influencing behavior only at this
  location. This file should not be stored in git/etc.
