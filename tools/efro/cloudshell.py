# Released under the MIT License. See LICENSE for details.
#
"""My nifty ssh/mosh/rsync mishmash."""

from enum import Enum
from dataclasses import dataclass

from efro.dataclassio import ioprepped


class LockType(Enum):
    """Types of locks that can be acquired on a host."""

    HOST = 'host'
    WORKSPACE = 'workspace'


@ioprepped
@dataclass
class HostConfig:
    """Config for a cloud machine to run commands on.

    precommand, if set, will be run before the passed commands.
    Note that it is not run in interactive mode (when no command is given).
    """

    address: str | None = None
    user: str = 'ubuntu'
    port: int = 22
    mosh_port: int | None = None
    mosh_port_2: int | None = None
    mosh_server_path: str | None = None
    mosh_shell: str = 'sh'
    workspaces_root: str = '/home/${USER}/cloudshell_workspaces'
    sync_perms: bool = True
    precommand_noninteractive: str | None = None
    precommand_interactive: str | None = None
    managed: bool = False
    region: str | None = None
    idle_minutes: int = 5
    can_sudo_reboot: bool = False
    max_sessions: int = 4
    reboot_wait_seconds: int = 20
    reboot_attempts: int = 1

    def resolved_workspaces_root(self) -> str:
        """Returns workspaces_root with standard substitutions."""
        return self.workspaces_root.replace('${USER}', self.user)


def socks_proxy_ssh_args() -> list[str]:
    """Return ssh ``-oProxyCommand`` args for a SOCKS5 proxy, if one is set.

    When ``ALL_PROXY`` is a ``socks5://`` url -- e.g. under a network
    sandbox that only permits outbound traffic through its proxy -- this
    returns ``['-oProxyCommand=...']`` so ssh can reach allowed hosts via
    it. To use these with rsync, fold them into ``--rsh`` with
    :func:`shlex.join` (``'--rsh=' + shlex.join(['ssh', *args])``) so the
    multi-word proxy command survives rsync's shell re-parse. Returns an
    empty list when no socks5 proxy is set, so it is safe to splice into a
    command unconditionally.
    """
    import os
    import shutil

    from efro.error import CleanError

    proxy = os.environ.get('ALL_PROXY', '')
    if not proxy.startswith(('socks5://', 'socks5h://')):
        return []

    netloc = proxy.split('://', 1)[1].rstrip('/')
    # Peel any 'user:pass@' userinfo off the 'host:port'.
    userinfo, _, host_port = netloc.rpartition('@')
    if userinfo:
        # An authenticating SOCKS5 proxy: macOS's stock nc can't do SOCKS5
        # auth, so route through ncat (nmap), which can. -4 forces IPv4
        # (the proxy listens on 127.0.0.1 but 'localhost' can resolve to
        # ::1 first); --proxy-dns remote is required since local DNS may be
        # unavailable behind the sandbox.
        ncat = shutil.which('ncat')
        if ncat is None:
            raise CleanError(
                'Behind an authenticating SOCKS5 proxy (ALL_PROXY) but ncat'
                " is not installed; install it with 'brew install nmap'."
            )
        proxy_cmd = (
            f'{ncat} -4 --proxy {host_port} --proxy-type socks5'
            f' --proxy-auth {userinfo} --proxy-dns remote %h %p'
        )
    else:
        # No auth required; stock nc handles plain SOCKS5.
        proxy_cmd = f'nc -X 5 -x {host_port} %h %p'
    return [f'-oProxyCommand={proxy_cmd}']
