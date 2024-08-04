# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=missing-function-docstring, missing-class-docstring
"""Setup for handling RPC (Discord)"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

import json
import uuid
import threading
import time

from baplus.pypresence.presence import Presence

if TYPE_CHECKING:
    from typing import Any


class RPCThread(threading.Thread):
    def __init__(self) -> None:
        super().__init__()
        self.rpc: Presence | None = None
        self.start_time: float = 0.0
        self.connected: bool = False
        self.state: str | None = None
        self.details: str | None = None
        self.party_id: str | None = None
        self.party_size: list | None = None
        self.show_start_time: bool = False
        self.party_join: str | None = None
        self.last_accessibility_check: float | None = None
        self.fb_state: str | None = None
        self.fb_details: str | None = None
        self.fb_party_join: str | None = None
        self.activity: Any = None

    @override
    def run(self) -> None:
        import bascenev1 as bs

        if bs.app.env.gui:
            while True:
                activity = self.activity
                if self.connected:
                    secret = self.party_join
                    fb_secret = self.fb_party_join
                    bs.pushcall(self.update_rpc_data, from_other_thread=True)
                    time.sleep(0.1)
                    if (
                        secret != self.party_join
                        or fb_secret != self.fb_party_join
                    ):
                        self.party_id = str(uuid.uuid4())
                    self.update_rpc()
                else:
                    try:
                        self.connect_rpc()
                    except Exception:
                        # FIXME: we actually want to retry here, but retrying
                        #  periodically (every 5 seconds) causes a socket leak
                        #  which breaks the game after 15-20 minutes (that is if
                        #  we stay in the same activity. an activity coming to
                        #  an end flushes the useless sockets for some reason.
                        #  still trying to figure this out)
                        while activity is self.activity:
                            time.sleep(5)

    def update_rpc(self) -> None:
        assert self.rpc is not None

        try:
            import bascenev1 as bs

            bs.pushcall(
                bs.Call(
                    self.handle_rpc_event,
                    self.rpc.update(
                        state=self.state or self.fb_state,  # type: ignore
                        details=self.details or self.fb_details,  # type: ignore
                        start=(
                            self.start_time
                            if self.show_start_time
                            else None  # type: ignore
                        ),
                        large_image='overclockedlogo4',
                        large_text='BombSquad',
                        party_id=self.party_id,  # type: ignore
                        party_size=self.party_size,  # type: ignore
                        join=(
                            self.party_join
                            or self.fb_party_join  # type: ignore
                        ),
                    ),
                ),
                True,
            )
        except Exception:
            self.connected = False

    def handle_rpc_event(self, data: Any) -> None:
        assert self.rpc is not None

        try:
            import bascenev1 as bs

            follow = bs.app.config.get('Allow RPC Joins', 'Invite Only')
            evt = data['evt']
            data = data['data']

            if evt == 'ACTIVITY_JOIN':
                try:
                    secret = data['secret']
                    server = json.loads(secret)
                    bs.connect_to_party(server['address'], server['port'])
                except Exception:
                    bs.screenmessage('Invalid join data.', (1.0, 0.0, 0.0))
            elif evt == 'ACTIVITY_JOIN_REQUEST':
                if follow == 'Invite Only':
                    bs.screenmessage(
                        data['user']['username']
                        + 'wants to join!\nYou can send them an invite in'
                        ' Discord',
                        (0.0, 1.0, 0.0),
                    )
                elif follow == 'Always':
                    self.rpc.send_data(
                        1,
                        {
                            'nonce': f'{time.time():.20f}',
                            'cmd': 'SEND_ACTIVITY_JOIN_INVITE',
                            'args': {'user_id': data['user']['id']},
                        },
                    )
                    bs.screenmessage(
                        data['user']['username']
                        + 'is joining you through Discord!',
                        (0.0, 1.0, 0.0),
                    )
        except Exception:
            logging.warning('Error in RPC thread')

    def update_rpc_data(self) -> None:
        # pylint: disable=too-many-branches
        try:
            import bascenev1 as bs

            assert bs.app.classic is not None

            self.state = None
            self.details = None
            self.party_size = None
            self.show_start_time = False
            self.party_join = None

            follow = bs.app.config.get('Allow RPC Joins', 'Invite Only')

            hi = bs.get_connection_to_host_info_2()
            if hi:
                self.details = 'Playing in a party'
                self.show_start_time = True
                if hi.address and hi.port:
                    self.details = 'Playing on a server'
                    if follow != 'Never':
                        self.party_join = json.dumps(
                            {'address': hi.address, 'port': hi.port}
                        )
                        if follow == 'Always':
                            self.state = hi.name
            elif follow != 'Never' and (
                not self.last_accessibility_check
                or bs.apptime() - self.last_accessibility_check >= 5
            ):
                self.last_accessibility_check = bs.apptime()
                bs.app.classic.master_server_v1_get(
                    'bsAccessCheck',
                    {
                        'port': bs.get_game_port(),
                        'b': bs.app.env.engine_build_number,
                    },
                    callback=bs.WeakCall(self.set_ip),
                )

            session = bs.get_foreground_host_session()
            if session and len(session.sessionplayers) >= 1:
                self.party_size = [
                    len(session.sessionplayers),
                    session.max_players,
                ]
            if isinstance(session, bs.CoopSession):
                self.state = 'Co-op'
            if isinstance(session, bs.DualTeamSession):
                self.state = 'Teams'
            if isinstance(session, bs.FreeForAllSession):
                self.state = 'FFA'
            activity = bs.get_foreground_host_activity()
            if isinstance(activity, bs.GameActivity):
                self.details = activity.get_instance_display_string().evaluate()
                self.show_start_time = True

            if follow == 'Never':
                self.party_join = None
                self.fb_party_join = None
                self.party_id = str(uuid.uuid4())

            if (self.party_join or self.fb_party_join) and not self.party_size:
                self.party_size = [3, 6]
        except Exception:
            pass

    def set_ip(self, data: dict[str, Any] | None) -> None:
        if (
            data
            and 'accessible' in data
            and data['accessible']
            and 'address' in data
            and 'port' in data
        ):
            import bascenev1 as bs

            follow = bs.app.config.get('Allow RPC Joins', 'Invite Only')
            if bs.get_public_party_enabled():
                self.fb_details = 'Hosting a public party'
                if follow == 'Always':
                    self.fb_state = bs.app.config.get('Public Party Name', '')
            self.fb_party_join = json.dumps(
                {'address': data['address'], 'port': data['port']}
            )
        else:
            self.fb_state = None
            self.fb_details = None
            self.fb_party_join = None

    def connect_rpc(self) -> None:
        self.rpc = Presence('1167093983579738112')  # type: ignore
        self.rpc.connect()  # type: ignore
        for event in ['ACTIVITY_JOIN', 'ACTIVITY_JOIN_REQUEST']:
            self.rpc.send_data(
                1,
                {
                    'nonce': f'{time.time():.20f}',
                    'cmd': 'SUBSCRIBE',
                    'evt': event,
                    'args': {},
                },
            )
        self.connected = True
