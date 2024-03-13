# Released under the MIT License. See LICENSE for details.
#
"""My nifty ssh/mosh/rsync mishmash."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass

from efro.dataclassio import ioprepped


class LockType(Enum):
    """Types of locks that can be acquired on a host."""

    HOST = 'host'
    WORKSPACE = 'workspace'
    PYCHARM = 'pycharm'
    CLION = 'clion'


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
