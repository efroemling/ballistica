# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the server manager script."""
from __future__ import annotations

from enum import Enum
from dataclasses import field, dataclass
from typing import TYPE_CHECKING

from efro.dataclassio import prepped

if TYPE_CHECKING:
    from typing import Optional, Tuple, List


@prepped
@dataclass
class ServerConfig:
    """Configuration for the server manager app (<appname>_server)."""

    # Name of our server in the public parties list.
    party_name: str = 'FFA'

    # If True, your party will show up in the global public party list
    # Otherwise it will still be joinable via LAN or connecting by IP address.
    party_is_public: bool = True

    # If True, all connecting clients will be authenticated through the master
    # server to screen for fake account info. Generally this should always
    # be enabled unless you are hosting on a LAN with no internet connection.
    authenticate_clients: bool = True

    # IDs of server admins. Server admins are not kickable through the default
    # kick vote system and they are able to kick players without a vote. To get
    # your account id, enter 'getaccountid' in settings->advanced->enter-code.
    admins: List[str] = field(default_factory=list)

    # Whether the default kick-voting system is enabled.
    enable_default_kick_voting: bool = True

    # UDP port to host on. Change this to work around firewalls or run multiple
    # servers on one machine.
    # 43210 is the default and the only port that will show up in the LAN
    # browser tab.
    port: int = 43210

    # Max devices in the party. Note that this does *NOT* mean max players.
    # Any device in the party can have more than one player on it if they have
    # multiple controllers. Also, this number currently includes the server so
    # generally make it 1 bigger than you need. Max-players is not currently
    # exposed but I'll try to add that soon.
    max_party_size: int = 6

    # Options here are 'ffa' (free-for-all) and 'teams'
    # This value is only used if you do not supply a playlist_code (see below).
    # In that case the default teams or free-for-all playlist gets used.
    session_type: str = 'ffa'

    # To host your own custom playlists, use the 'share' functionality in the
    # playlist editor in the regular version of the game.
    # This will give you a numeric code you can enter here to host that
    # playlist.
    playlist_code: Optional[int] = None

    # Whether to shuffle the playlist or play its games in designated order.
    playlist_shuffle: bool = True

    # If True, keeps team sizes equal by disallowing joining the largest team
    # (teams mode only).
    auto_balance_teams: bool = True

    # Whether to enable telnet access.
    # IMPORTANT: This option is no longer available, as it was being used
    # for exploits. Live access to the running server is still possible through
    # the mgr.cmd() function in the server script. Run your server through
    # tools such as 'screen' or 'tmux' and you can reconnect to it remotely
    # over a secure ssh connection.
    enable_telnet: bool = False

    # Series length in teams mode (7 == 'best-of-7' series; a team must
    # get 4 wins)
    teams_series_length: int = 7

    # Points to win in free-for-all mode (Points are awarded per game based on
    # performance)
    ffa_series_length: int = 24

    # If you provide a custom stats webpage for your server, you can use
    # this to provide a convenient in-game link to it in the server-browser
    # beside the server name.
    # if ${ACCOUNT} is present in the string, it will be replaced by the
    # currently-signed-in account's id. To fetch info about an account,
    # your backend server can use the following url:
    # http://bombsquadgame.com/accountquery?id=ACCOUNT_ID_HERE
    stats_url: Optional[str] = None

    # If present, the server subprocess will attempt to gracefully exit after
    # this amount of time. A graceful exit can occur at the end of a series
    # or other opportune time. Server-managers set to auto-restart (the
    # default) will then spin up a fresh subprocess. This mechanism can be
    # useful to clear out any memory leaks or other accumulated bad state
    # in the server subprocess.
    clean_exit_minutes: Optional[float] = None

    # If present, the server subprocess will shut down immediately after this
    # amount of time. This can be useful as a fallback for clean_exit_time.
    # The server manager will then spin up a fresh server subprocess if
    # auto-restart is enabled (the default).
    unclean_exit_minutes: Optional[float] = None

    # If present, the server subprocess will shut down immediately if this
    # amount of time passes with no activity from any players. The server
    # manager will then spin up a fresh server subprocess if
    # auto-restart is enabled (the default).
    idle_exit_minutes: Optional[float] = None

    # (internal) stress-testing mode.
    stress_test_players: Optional[int] = None


# NOTE: as much as possible, communication from the server-manager to the
# child-process should go through these and not ad-hoc Python string commands
# since this way is type safe.
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
    clients: Optional[List[int]]


@dataclass
class ScreenMessageCommand(ServerCommand):
    """Screen-message from the server."""
    message: str
    color: Optional[Tuple[float, float, float]]
    clients: Optional[List[int]]


@dataclass
class ClientListCommand(ServerCommand):
    """Print a list of clients."""


@dataclass
class KickCommand(ServerCommand):
    """Kick a client."""
    client_id: int
    ban_time: Optional[int]
