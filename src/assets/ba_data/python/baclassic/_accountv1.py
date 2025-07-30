# Released under the MIT License. See LICENSE for details.
#
"""Account related functionality."""

from __future__ import annotations

import copy
import time
from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    from typing import Any


class AccountV1Subsystem:
    """Subsystem for legacy account handling in the app.

    Access the single instance of this class at
    'ba.app.classic.accounts'.
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

    def on_app_loading(self) -> None:
        """Called when the app is done bootstrapping."""

        # Auto-sign-in to a local account in a moment if we're set to.
        def do_auto_sign_in() -> None:
            if babase.app.plus is None:
                return
            if (
                babase.app.env.headless
                or babase.app.config.get('Auto Account State') == 'Local'
            ):
                babase.app.plus.sign_in_v1('Local')

        babase.pushcall(do_auto_sign_in)

    def on_app_suspend(self) -> None:
        """Should be called when app is pausing."""

    def on_app_unsuspend(self) -> None:
        """Should be called when the app is resumed."""

        # Mark our cached tourneys as invalid so anyone using them knows
        # they might be out of date.
        for entry in list(self.tournament_info.values()):
            entry['valid'] = False

    def handle_account_gained_tickets(self, count: int) -> None:
        """Called when the current account has been awarded tickets.

        (internal)
        """
        babase.screenmessage(
            babase.Lstr(
                resource='getTicketsWindow.receivedTicketsText',
                subs=[('${COUNT}', str(count))],
            ),
            color=(0, 1, 0),
        )
        babase.getsimplesound('cashRegister').play()

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
            assert babase.app.classic is not None
            for ach in babase.app.classic.ach.achievements:
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

        # We used to give this bonus for pro, but on recent versions of
        # the game give it for everyone (since we are phasing out Pro).

        # if data['p']:
        if bool(True):
            if babase.app.plus is None:
                pro_mult = 1.0
            else:
                pro_mult = (
                    1.0
                    + float(
                        babase.app.plus.get_v1_account_misc_read_val(
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

        for entry in info:
            cache_entry = self.tournament_info[entry['tournamentID']] = (
                copy.deepcopy(entry)
            )

            # Also store the time we received this, so we can adjust
            # time-remaining values/etc.
            cache_entry['timeReceived'] = babase.apptime()
            cache_entry['valid'] = True

    def get_purchased_icons(self) -> list[str]:
        """(internal)"""
        # pylint: disable=cyclic-import
        plus = babase.app.plus
        classic = babase.app.classic
        if plus is None or classic is None:
            return []
        if plus.accounts.primary is None:
            return []
        icons = []
        store_items: dict[str, Any] = (
            babase.app.classic.store.get_store_items()
            if babase.app.classic is not None
            else {}
        )
        for item_name, item in list(store_items.items()):
            if (
                item_name.startswith('icons.')
                and item_name in classic.purchases
            ):
                icons.append(item['icon'])
        return icons

    def ensure_have_account_player_profile(self) -> None:
        """
        Ensure the standard account-named player profile exists;
        creating if needed.

        (internal)
        """
        plus = babase.app.plus
        if plus is None:
            return
        # This only applies when we're signed in.
        if plus.get_v1_account_state() != 'signed_in':
            return

        # If the short version of our account name currently cant be
        # displayed by the game, cancel.
        if not babase.can_display_chars(
            plus.get_v1_account_display_string(full=False)
        ):
            return

        config = babase.app.config
        if (
            'Player Profiles' not in config
            or '__account__' not in config['Player Profiles']
        ):
            # Create a spaz with a nice default purply color.
            plus.add_v1_account_transaction(
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
            plus.run_v1_account_transactions()

    def have_pro(self) -> bool:
        """Return whether pro is currently unlocked."""

        classic = babase.app.classic
        if classic is None:
            return False
        purchases = classic.purchases

        # Check various server-side purchases that mean we have pro.
        return (
            'gold_pass' in purchases
            or 'upgrades.pro' in purchases
            or 'static.pro' in purchases
            or 'static.pro_sale' in purchases
        )

    def have_pro_options(self) -> bool:
        """Return whether pro-options are present.

        This is True for owners of Pro or for old installs
        before Pro was a requirement for these options.
        """

        plus = babase.app.plus
        if plus is None:
            return False

        # We expose pro options if the server tells us to (which is
        # generally just when we own pro), or also if we've been
        # grandfathered in.
        return self.have_pro() or bool(
            plus.get_v1_account_misc_read_val_2('proOptionsUnlocked', False)
            or babase.app.config.get('lc14292', 0) > 1
        )

    def show_post_purchase_message(self) -> None:
        """(internal)"""
        cur_time = babase.apptime()
        if (
            self.last_post_purchase_message_time is None
            or cur_time - self.last_post_purchase_message_time > 3.0
        ):
            self.last_post_purchase_message_time = cur_time
            babase.screenmessage(
                babase.Lstr(
                    resource='updatingAccountText',
                    fallback_resource='purchasingText',
                ),
                color=(0, 1, 0),
            )
            # Ick; this can get called early in the bootstrapping process
            # before we're allowed to load assets. Guard against that.
            if babase.asset_loads_allowed():
                babase.getsimplesound('click01').play()

    def on_account_state_changed(self) -> None:
        """(internal)"""
        plus = babase.app.plus
        if plus is None:
            return
        # Run any pending promo codes we had queued up while not signed in.
        if (
            plus.get_v1_account_state() == 'signed_in'
            and self.pending_promo_codes
        ):
            for code in self.pending_promo_codes:
                babase.screenmessage(
                    babase.Lstr(resource='submittingPromoCodeText'),
                    color=(0, 1, 0),
                )
                plus.add_v1_account_transaction(
                    {
                        'type': 'PROMO_CODE',
                        'expire_time': time.time() + 5,
                        'code': code,
                    }
                )
            plus.run_v1_account_transactions()
            self.pending_promo_codes = []

    def add_pending_promo_code(self, code: str) -> None:
        """(internal)"""
        plus = babase.app.plus
        if plus is None:
            import logging

            logging.warning(
                'Error adding pending promo code; plus not present.'
            )
            babase.screenmessage(
                babase.Lstr(resource='errorText'), color=(1, 0, 0)
            )
            babase.getsimplesound('error').play()
            return

        # If we're not signed in, queue up the code to run the next time we
        # are and issue a warning if we haven't signed in within the next
        # few seconds.
        if plus.get_v1_account_state() != 'signed_in':

            def check_pending_codes() -> None:
                """(internal)"""

                # If we're still not signed in and have pending codes,
                # inform the user that they need to sign in to use them.
                if self.pending_promo_codes:
                    babase.screenmessage(
                        babase.Lstr(resource='signInForPromoCodeText'),
                        color=(1, 0, 0),
                    )
                    babase.getsimplesound('error').play()

            self.pending_promo_codes.append(code)
            babase.apptimer(6.0, check_pending_codes)
            return
        babase.screenmessage(
            babase.Lstr(resource='submittingPromoCodeText'), color=(0, 1, 0)
        )
        plus.add_v1_account_transaction(
            {'type': 'PROMO_CODE', 'expire_time': time.time() + 5, 'code': code}
        )
        plus.run_v1_account_transactions()
