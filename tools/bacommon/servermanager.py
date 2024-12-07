# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the server manager script."""
from __future__ import annotations

from enum import Enum
from dataclasses import field, dataclass
from typing import TYPE_CHECKING, Any

from efro.dataclassio import ioprepped

if TYPE_CHECKING:
    pass


@ioprepped
@dataclass
class ServerConfig:
    """Configuration for the server manager app (<appname>_server)."""

    # Name of our server in the public parties list.
    party_name: str = 'FFA'

    # If True, your party will show up in the global public party list
    # Otherwise it will still be joinable via LAN or connecting by IP
    # address.
    party_is_public: bool = True

    # If True, all connecting clients will be authenticated through the
    # master server to screen for fake account info. Generally this
    # should always be enabled unless you are hosting on a LAN with no
    # internet connection.
    authenticate_clients: bool = True

    # IDs of server admins. Server admins are not kickable through the
    # default kick vote system and they are able to kick players without
    # a vote. To get your account id, enter 'getaccountid' in
    # settings->advanced->enter-code.
    admins: list[str] = field(default_factory=list)

    # Whether the default kick-voting system is enabled.
    enable_default_kick_voting: bool = True

    # To be included in the public server list, your server MUST be
    # accessible via an ipv4 address. By default, the master server will
    # try to use the address your server contacts it from, but this may
    # be an ipv6 address these days so you may need to provide an ipv4
    # address explicitly.
    public_ipv4_address: str | None = None

    # You can optionally provide an ipv6 address for your server for the
    # public server list. Unlike ipv4, a server is not required to have
    # an ipv6 address to appear in the list, but is still good to
    # provide when available since more and more devices are using ipv6
    # these days. Your server's ipv6 address will be autodetected if
    # your server uses ipv6 when communicating with the master server. You
    # can pass an empty string here to explicitly disable the ipv6
    # address.
    public_ipv6_address: str | None = None

    # UDP port to host on. Change this to work around firewalls or run
    # multiple servers on one machine.
    #
    # 43210 is the default and the only port that will show up in the
    # LAN browser tab.
    port: int = 43210

    # Max devices in the party. Note that this does *NOT* mean max
    # players. Any device in the party can have more than one player on
    # it if they have multiple controllers. Also, this number currently
    # includes the server so generally make it 1 bigger than you need.
    max_party_size: int = 6

    # Max players that can join a session. If present this will override
    # the session's preferred max_players. if a value below 0 is given
    # player limit will be removed.
    session_max_players_override: int | None = None

    # Options here are 'ffa' (free-for-all), 'teams' and 'coop'
    # (cooperative) This value is ignored if you supply a playlist_code
    # (see below).
    session_type: str = 'ffa'

    # Playlist-code for teams or free-for-all mode sessions. To host
    # your own custom playlists, use the 'share' functionality in the
    # playlist editor in the regular version of the game. This will give
    # you a numeric code you can enter here to host that playlist.
    playlist_code: int | None = None

    # Alternately, you can embed playlist data here instead of using
    # codes. Make sure to set session_type to the correct type for the
    # data here.
    playlist_inline: list[dict[str, Any]] | None = None

    # Whether to shuffle the playlist or play its games in designated
    # order.
    playlist_shuffle: bool = True

    # If True, keeps team sizes equal by disallowing joining the largest
    # team (teams mode only).
    auto_balance_teams: bool = True

    # The campaign used when in co-op session mode. Do
    # print(ba.app.campaigns) to see available campaign names.
    coop_campaign: str = 'Easy'

    # The level name within the campaign used in co-op session mode. For
    # campaign name FOO, do print(ba.app.campaigns['FOO'].levels) to see
    # available level names.
    coop_level: str = 'Onslaught Training'

    # Whether to enable telnet access.
    #
    # IMPORTANT: This option is no longer available, as it was being
    # used for exploits. Live access to the running server is still
    # possible through the mgr.cmd() function in the server script. Run
    # your server through tools such as 'screen' or 'tmux' and you can
    # reconnect to it remotely over a secure ssh connection.
    enable_telnet: bool = False

    # Series length in teams mode (7 == 'best-of-7' series; a team must
    # get 4 wins)
    teams_series_length: int = 7

    # Points to win in free-for-all mode (Points are awarded per game
    # based on performance)
    ffa_series_length: int = 24

    # If you have a custom stats webpage for your server, you can use
    # this to provide a convenient in-game link to it in the
    # server-browser alongside the server name.
    #
    # if ${ACCOUNT} is present in the string, it will be replaced by the
    # currently-signed-in account's id. To fetch info about an account,
    # your back-end server can use the following url:
    # https://legacy.ballistica.net/accountquery?id=ACCOUNT_ID_HERE
    stats_url: str | None = None

    # If present, the server subprocess will attempt to gracefully exit
    # after this amount of time. A graceful exit can occur at the end of
    # a series or other opportune time. Server-managers set to
    # auto-restart (the default) will then spin up a fresh subprocess.
    # This mechanism can be useful to clear out any memory leaks or
    # other accumulated bad state in the server subprocess.
    clean_exit_minutes: float | None = None

    # If present, the server subprocess will shut down immediately after
    # this amount of time. This can be useful as a fallback for
    # clean_exit_time. The server manager will then spin up a fresh
    # server subprocess if auto-restart is enabled (the default).
    unclean_exit_minutes: float | None = None

    # If present, the server subprocess will shut down immediately if
    # this amount of time passes with no activity from any players. The
    # server manager will then spin up a fresh server subprocess if
    # auto-restart is enabled (the default).
    idle_exit_minutes: float | None = None

    # Should the tutorial be shown at the beginning of games?
    show_tutorial: bool = False

    # Team names (teams mode only).
    team_names: tuple[str, str] | None = None

    # Team colors (teams mode only).
    team_colors: (
        tuple[tuple[float, float, float], tuple[float, float, float]] | None
    ) = None

    # Whether to enable the queue where players can line up before
    # entering your server. Disabling this can be used as a workaround
    # to deal with queue spamming attacks.
    enable_queue: bool = True

    # Protocol version we host with. Currently the default is 33 which
    # still allows older 1.4 game clients to connect. Explicitly setting
    # to 35 no longer allows those clients but adds/fixes a few things
    # such as making camera shake properly work in net games.
    protocol_version: int | None = None

    # (internal) stress-testing mode.
    stress_test_players: int | None = None

    # How many seconds individual players from a given account must wait
    # before rejoining the game. This can help suppress exploits
    # involving leaving and rejoining or switching teams rapidly.
    player_rejoin_cooldown: float = 10.0

    # Log levels for particular loggers, overriding the engine's
    # defaults. Valid values are NOTSET, DEBUG, INFO, WARNING, ERROR, or
    # CRITICAL.
    log_levels: dict[str, str] | None = None


# NOTE: as much as possible, communication from the server-manager to
# the child-process should go through these and not ad-hoc Python string
# commands since this way is type safe.
class ServerCommand:
    """Base class for commands that can be sent to the server."""


@dataclass
class StartServerModeCommand(ServerCommand):
    """Tells the app to switch into 'server' mode."""

    config: ServerConfig


class ShutdownReason(Enum):
    """Reason a server is shutting down."""

    NONE = 'none'
    RESTARTING = 'restarting'


@dataclass
class ShutdownCommand(ServerCommand):
    """Tells the server to shut down."""

    reason: ShutdownReason
    immediate: bool


@dataclass
class ChatMessageCommand(ServerCommand):
    """Chat message from the server."""

    message: str
    clients: list[int] | None


@dataclass
class ScreenMessageCommand(ServerCommand):
    """Screen-message from the server."""

    message: str
    color: tuple[float, float, float] | None
    clients: list[int] | None


@dataclass
class ClientListCommand(ServerCommand):
    """Print a list of clients."""


@dataclass
class KickCommand(ServerCommand):
    """Kick a client."""

    client_id: int
    ban_time: int | None
