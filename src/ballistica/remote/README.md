# Remote Feature Set

The remote app-mode: a device used as a game controller, and the future
home of the BombSquad Remote app (being built during the 1.9 development
cycle). Currently a placeholder with no UI: `RemoteAppMode` finds a game
with the remote app's broadcast query, connects to the first one that
answers, and sends it random input, reporting progress as screen-messages
and `ba.net` logs. It wants neither classic networking nor the remote-app
server; the client opens its own socket.
