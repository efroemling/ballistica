# Released under the MIT License. See LICENSE for details.
#
"""Account related functionality."""

from __future__ import annotations

import copy
import time
from typing import TYPE_CHECKING

import _ba
from ba import _internal

if TYPE_CHECKING:
    from typing import Any


class AccountV1Subsystem:
    """Subsystem for legacy account handling in the app.

    Category: **App Classes**

    Access the single shared instance of this class at 'ba.app.accounts_v1'.
    """

    def __init__(self) -> None:
        self.account_tournament_list: tuple[int, list[str]] | None = None

        # FIXME: should abstract/structure these.
        self.tournament_info: dict = {}
        self.league_rank_cache: dict = {}
        self.last_post_purchase_message_time: float | None = None

        # If we try to run promo-codes due to launch-args/etc we might
        # not be signed in yet; go ahead and queue them up in that case.
        self.pending_promo_codes: list[str] = []

    def on_app_launch(self) -> None:
        """Called when the app is done bootstrapping."""

        # Auto-sign-in to a local account in a moment if we're set to.
        def do_auto_sign_in() -> None:
            if (
                _ba.app.headless_mode
                or _ba.app.config.get('Auto Account State') == 'Local'
            ):
                _internal.sign_in_v1('Local')

        _ba.pushcall(do_auto_sign_in)

    def on_app_pause(self) -> None:
        """Should be called when app is pausing."""

    def on_app_resume(self) -> None:
        """Should be called when the app is resumed."""

        # Mark our cached tourneys as invalid so anyone using them knows
        # they might be out of date.
        for entry in list(self.tournament_info.values()):
            entry['valid'] = False

    def handle_account_gained_tickets(self, count: int) -> None:
        """Called when the current account has been awarded tickets.

        (internal)
        """
        from ba._language import Lstr

        _ba.screenmessage(
            Lstr(
                resource='getTicketsWindow.receivedTicketsText',
                subs=[('${COUNT}', str(count))],
            ),
            color=(0, 1, 0),
        )
        _ba.playsound(_ba.getsound('cashRegister'))

    def cache_league_rank_data(self, data: Any) -> None:
        """(internal)"""
        self.league_rank_cache['info'] = copy.deepcopy(data)

    def get_cached_league_rank_data(self) -> Any:
        """(internal)"""
        return self.league_rank_cache.get('info', None)

    def get_league_rank_points(
        self, data: dict[str, Any] | None, subset: str | None = None
    ) -> int:
        """(internal)"""
        if data is None:
            return 0

        # If the data contains an achievement total, use that. otherwise calc
        # locally.
        if data['at'] is not None:
            total_ach_value = data['at']
        else:
            total_ach_value = 0
            for ach in _ba.app.ach.achievements:
                if ach.complete:
                    total_ach_value += ach.power_ranking_value

        trophies_total: int = (
            data['t0a'] * data['t0am']
            + data['t0b'] * data['t0bm']
            + data['t1'] * data['t1m']
            + data['t2'] * data['t2m']
            + data['t3'] * data['t3m']
            + data['t4'] * data['t4m']
        )
        if subset == 'trophyCount':
            val: int = (
                data['t0a']
                + data['t0b']
                + data['t1']
                + data['t2']
                + data['t3']
                + data['t4']
            )
            assert isinstance(val, int)
            return val
        if subset == 'trophies':
            assert isinstance(trophies_total, int)
            return trophies_total
        if subset is not None:
            raise ValueError('invalid subset value: ' + str(subset))

        if data['p']:
            pro_mult = (
                1.0
                + float(
                    _internal.get_v1_account_misc_read_val(
                        'proPowerRankingBoost', 0.0
                    )
                )
                * 0.01
            )
        else:
            pro_mult = 1.0

        # For final value, apply our pro mult and activeness-mult.
        return int(
            (total_ach_value + trophies_total)
            * (data['act'] if data['act'] is not None else 1.0)
            * pro_mult
        )

    def cache_tournament_info(self, info: Any) -> None:
        """(internal)"""
        from ba._generated.enums import TimeType, TimeFormat

        for entry in info:
            cache_entry = self.tournament_info[
                entry['tournamentID']
            ] = copy.deepcopy(entry)

            # Also store the time we received this, so we can adjust
            # time-remaining values/etc.
            cache_entry['timeReceived'] = _ba.time(
                TimeType.REAL, TimeFormat.MILLISECONDS
            )
            cache_entry['valid'] = True

    def get_purchased_icons(self) -> list[str]:
        """(internal)"""
        # pylint: disable=cyclic-import
        from ba import _store

        if _internal.get_v1_account_state() != 'signed_in':
            return []
        icons = []
        store_items = _store.get_store_items()
        for item_name, item in list(store_items.items()):
            if item_name.startswith('icons.') and _internal.get_purchased(
                item_name
            ):
                icons.append(item['icon'])
        return icons

    def ensure_have_account_player_profile(self) -> None:
        """
        Ensure the standard account-named player profile exists;
        creating if needed.

        (internal)
        """
        # This only applies when we're signed in.
        if _internal.get_v1_account_state() != 'signed_in':
            return

        # If the short version of our account name currently cant be
        # displayed by the game, cancel.
        if not _ba.have_chars(
            _internal.get_v1_account_display_string(full=False)
        ):
            return

        config = _ba.app.config
        if (
            'Player Profiles' not in config
            or '__account__' not in config['Player Profiles']
        ):

            # Create a spaz with a nice default purply color.
            _internal.add_transaction(
                {
                    'type': 'ADD_PLAYER_PROFILE',
                    'name': '__account__',
                    'profile': {
                        'character': 'Spaz',
                        'color': [0.5, 0.25, 1.0],
                        'highlight': [0.5, 0.25, 1.0],
                    },
                }
            )
            _internal.run_transactions()

    def have_pro(self) -> bool:
        """Return whether pro is currently unlocked."""

        # Check our tickets-based pro upgrade and our two real-IAP based
        # upgrades. Also always unlock this stuff in ballistica-core builds.
        return bool(
            _internal.get_purchased('upgrades.pro')
            or _internal.get_purchased('static.pro')
            or _internal.get_purchased('static.pro_sale')
            or 'ballistica' + 'core' == _ba.appname()
        )

    def have_pro_options(self) -> bool:
        """Return whether pro-options are present.

        This is True for owners of Pro or for old installs
        before Pro was a requirement for these options.
        """

        # We expose pro options if the server tells us to
        # (which is generally just when we own pro),
        # or also if we've been grandfathered in
        # or are using ballistica-core builds.
        return self.have_pro() or bool(
            _internal.get_v1_account_misc_read_val_2(
                'proOptionsUnlocked', False
            )
            or _ba.app.config.get('lc14292', 0) > 1
        )

    def show_post_purchase_message(self) -> None:
        """(internal)"""
        from ba._language import Lstr
        from ba._generated.enums import TimeType

        cur_time = _ba.time(TimeType.REAL)
        if (
            self.last_post_purchase_message_time is None
            or cur_time - self.last_post_purchase_message_time > 3.0
        ):
            self.last_post_purchase_message_time = cur_time
            with _ba.Context('ui'):
                _ba.screenmessage(
                    Lstr(
                        resource='updatingAccountText',
                        fallback_resource='purchasingText',
                    ),
                    color=(0, 1, 0),
                )
                _ba.playsound(_ba.getsound('click01'))

    def on_account_state_changed(self) -> None:
        """(internal)"""
        from ba._language import Lstr

        # Run any pending promo codes we had queued up while not signed in.
        if (
            _internal.get_v1_account_state() == 'signed_in'
            and self.pending_promo_codes
        ):
            for code in self.pending_promo_codes:
                _ba.screenmessage(
                    Lstr(resource='submittingPromoCodeText'), color=(0, 1, 0)
                )
                _internal.add_transaction(
                    {
                        'type': 'PROMO_CODE',
                        'expire_time': time.time() + 5,
                        'code': code,
                    }
                )
            _internal.run_transactions()
            self.pending_promo_codes = []

    def add_pending_promo_code(self, code: str) -> None:
        """(internal)"""
        from ba._language import Lstr
        from ba._generated.enums import TimeType

        # If we're not signed in, queue up the code to run the next time we
        # are and issue a warning if we haven't signed in within the next
        # few seconds.
        if _internal.get_v1_account_state() != 'signed_in':

            def check_pending_codes() -> None:
                """(internal)"""

                # If we're still not signed in and have pending codes,
                # inform the user that they need to sign in to use them.
                if self.pending_promo_codes:
                    _ba.screenmessage(
                        Lstr(resource='signInForPromoCodeText'), color=(1, 0, 0)
                    )
                    _ba.playsound(_ba.getsound('error'))

            self.pending_promo_codes.append(code)
            _ba.timer(6.0, check_pending_codes, timetype=TimeType.REAL)
            return
        _ba.screenmessage(
            Lstr(resource='submittingPromoCodeText'), color=(0, 1, 0)
        )
        _internal.add_transaction(
            {'type': 'PROMO_CODE', 'expire_time': time.time() + 5, 'code': code}
        )
        _internal.run_transactions()
