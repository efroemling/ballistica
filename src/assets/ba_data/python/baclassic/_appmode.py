# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines
"""Contains ClassicAppMode."""

from __future__ import annotations

import os
import logging
import hashlib
from functools import partial
from typing import TYPE_CHECKING, override

from efro.error import CommunicationError
import bacommon.clienteffect as clfx
import bacommon.classic
from babase import AppMode
import bauiv1 as bui
from bauiv1lib.connectivity import wait_for_connectivity

import _baclassic

if TYPE_CHECKING:
    from typing import Callable, Any, Literal, Iterable

    from efro.call import CallbackRegistration
    import bacommon.cloud
    from bauiv1lib.chest import ChestWindow


# ba_meta export babase.AppMode
class ClassicAppMode(AppMode):
    """AppMode for the classic BombSquad experience."""

    _ACCOUNT_STATE_CONFIG_KEY = 'ClassicAccountState'
    _ASKED_FOR_REVIEW_CONFIG_KEY = 'AskedForReview'

    def __init__(self) -> None:
        self._on_primary_account_changed_callback: (
            CallbackRegistration | None
        ) = None
        self._on_connectivity_changed_callback: CallbackRegistration | None = (
            None
        )
        self._test_sub: bui.CloudSubscription | None = None
        self._account_data_sub: bui.CloudSubscription | None = None

        self._have_account_values = False
        self._have_connectivity = False
        self._current_account_id: str | None = None

        self._purchase_ui_pause: bui.RootUIUpdatePause | None = None
        self._last_tokens_value = 0

        self._purchases_update_timer: bui.AppTimer | None = None
        self._purchase_request_in_flight = False
        self._target_purchases_state: str | None = None

        # state-hash and purchases we last pushed to the classic subsystem
        self._current_purchases_state: str | None = None
        self._current_purchases: frozenset[str] | None = None

    @override
    @classmethod
    def can_handle_intent(cls, intent: bui.AppIntent) -> bool:
        # We support default and exec intents currently.
        return isinstance(intent, bui.AppIntentExec | bui.AppIntentDefault)

    @override
    def handle_intent(self, intent: bui.AppIntent) -> None:
        if isinstance(intent, bui.AppIntentExec):
            _baclassic.classic_app_mode_handle_app_intent_exec(intent.code)
            return
        assert isinstance(intent, bui.AppIntentDefault)
        _baclassic.classic_app_mode_handle_app_intent_default()

    @override
    def on_activate(self) -> None:

        # Let the native layer do its thing.
        _baclassic.classic_app_mode_activate()

        app = bui.app
        plus = app.plus
        assert plus is not None

        # Wire up the root ui to do what we want.
        ui = app.ui_v1
        ui.root_ui_calls[ui.RootUIElement.ACCOUNT_BUTTON] = (
            self._root_ui_account_press
        )
        ui.root_ui_calls[ui.RootUIElement.MENU_BUTTON] = (
            self._root_ui_menu_press
        )
        ui.root_ui_calls[ui.RootUIElement.SQUAD_BUTTON] = (
            self._root_ui_squad_press
        )
        ui.root_ui_calls[ui.RootUIElement.SETTINGS_BUTTON] = (
            self._root_ui_settings_press
        )
        ui.root_ui_calls[ui.RootUIElement.STORE_BUTTON] = (
            self._root_ui_store_press
        )
        ui.root_ui_calls[ui.RootUIElement.INVENTORY_BUTTON] = (
            self._root_ui_inventory_press
        )
        ui.root_ui_calls[ui.RootUIElement.GET_TOKENS_BUTTON] = (
            self._root_ui_get_tokens_press
        )
        ui.root_ui_calls[ui.RootUIElement.INBOX_BUTTON] = (
            self._root_ui_inbox_press
        )
        ui.root_ui_calls[ui.RootUIElement.TICKETS_METER] = (
            self._root_ui_tickets_meter_press
        )
        ui.root_ui_calls[ui.RootUIElement.TOKENS_METER] = (
            self._root_ui_tokens_meter_press
        )
        ui.root_ui_calls[ui.RootUIElement.TROPHY_METER] = (
            self._root_ui_trophy_meter_press
        )
        ui.root_ui_calls[ui.RootUIElement.LEVEL_METER] = (
            self._root_ui_level_meter_press
        )
        ui.root_ui_calls[ui.RootUIElement.ACHIEVEMENTS_BUTTON] = (
            self._root_ui_achievements_press
        )
        ui.root_ui_calls[ui.RootUIElement.CHEST_SLOT_0] = partial(
            self._root_ui_chest_slot_pressed, 0
        )
        ui.root_ui_calls[ui.RootUIElement.CHEST_SLOT_1] = partial(
            self._root_ui_chest_slot_pressed, 1
        )
        ui.root_ui_calls[ui.RootUIElement.CHEST_SLOT_2] = partial(
            self._root_ui_chest_slot_pressed, 2
        )
        ui.root_ui_calls[ui.RootUIElement.CHEST_SLOT_3] = partial(
            self._root_ui_chest_slot_pressed, 3
        )

        # We want to be informed when connectivity changes.
        self._on_connectivity_changed_callback = (
            plus.cloud.on_connectivity_changed_callbacks.register(
                self._update_for_connectivity_change
            )
        )
        # We want to be informed when primary account changes.
        self._on_primary_account_changed_callback = (
            plus.accounts.on_primary_account_changed_callbacks.register(
                self._update_for_primary_account
            )
        )
        # Establish subscriptions/etc. for any current primary account.
        self._update_for_primary_account(plus.accounts.primary)
        self._have_connectivity = plus.cloud.is_connected()
        self._update_for_connectivity_change(self._have_connectivity)

    @override
    def on_deactivate(self) -> None:

        classic = bui.app.classic

        # Store latest league vis vals for any active account.
        self._save_account_state()

        # Stop being informed of account changes.
        self._on_primary_account_changed_callback = None

        # Cancel any ui-pause we may have had going.
        self._purchase_ui_pause = None

        # Remove anything following any current account.
        self._update_for_primary_account(None)

        # Save where we were in the UI so we return there next time.
        if classic is not None:
            classic.save_ui_state()

        # Let the native layer do its thing.
        _baclassic.classic_app_mode_deactivate()

    @override
    def on_app_active_changed(self) -> None:
        if not bui.app.active:
            # If we're going inactive, ask for the main ui, which should
            # have the side effect of pausing the action if we're in a
            # game.
            bui.request_main_ui()

            # Also store any league vis state for the active account.
            # this may be our last chance to do this on mobile.
            self._save_account_state()

    @override
    def on_purchase_process_begin(
        self, item_id: str, user_initiated: bool
    ) -> None:

        # Do the default thing (announces 'updating account...')
        super().on_purchase_process_begin(
            item_id=item_id, user_initiated=user_initiated
        )

        # Pause the root ui so stuff like token counts don't change
        # automatically, allowing us to animate them. Note that we
        # need to explicitly kill this pause if we are deactivated since
        # we wouldn't get the on_purchase_process_end() call; the next
        # app-mode would.
        self._purchase_ui_pause = bui.RootUIUpdatePause()

        # Also grab our last known token count here to plug into animations.
        # We need to do this here before the purchase gets submitted so that
        # we know we're seeing the old value.
        assert bui.app.classic is not None
        self._last_tokens_value = bui.app.classic.tokens

    @override
    def on_purchase_process_end(
        self, item_id: str, user_initiated: bool, applied: bool
    ) -> None:

        # Let the UI auto-update again after any animations we may apply
        # here.
        self._purchase_ui_pause = None

        # Ignore user_initiated; we want to announce newly applied stuff
        # even if it was from a different launch or client or whatever.
        del user_initiated

        # If the purchase wasn't applied, do nothing. This likely means it
        # was redundant or something else harmless.
        if not applied:
            return

        if item_id.startswith('tokens'):
            if item_id == 'tokens1':
                tokens = bacommon.classic.TOKENS1_COUNT
                tokens_str = str(tokens)
                anim_time = 2.0
            elif item_id == 'tokens2':
                tokens = bacommon.classic.TOKENS2_COUNT
                tokens_str = str(tokens)
                anim_time = 2.5
            elif item_id == 'tokens3':
                tokens = bacommon.classic.TOKENS3_COUNT
                tokens_str = str(tokens)
                anim_time = 3.0
            elif item_id == 'tokens4':
                tokens = bacommon.classic.TOKENS4_COUNT
                tokens_str = str(tokens)
                anim_time = 3.5
            else:
                tokens = 0
                tokens_str = '???'
                anim_time = 2.5
                logging.warning(
                    'Unhandled item_id in on_purchase_process_end: %s', item_id
                )

            assert bui.app.classic is not None
            effects: list[clfx.Effect] = [
                clfx.TokensAnimation(
                    duration=anim_time,
                    startvalue=self._last_tokens_value,
                    endvalue=self._last_tokens_value + tokens,
                ),
                clfx.Delay(anim_time),
                clfx.LegacyScreenMessage(
                    message='You got ${COUNT} tokens!',
                    subs=['${COUNT}', tokens_str],
                    color=(0, 1, 0),
                ),
                clfx.PlaySound(clfx.Sound.CASH_REGISTER),
            ]
            bui.app.classic.run_bs_client_effects(effects)

        elif item_id.startswith('gold_pass'):
            bui.screenmessage(
                bui.Lstr(
                    translate=('serverResponses', 'You got a ${ITEM}!'),
                    subs=[
                        (
                            '${ITEM}',
                            bui.Lstr(resource='goldPass.goldPassText'),
                        )
                    ],
                ),
                color=(0, 1, 0),
            )
            if bui.asset_loads_allowed():
                bui.getsound('cashRegister').play()

        else:

            # Fallback: simply announce item id.
            logging.warning(
                'on_purchase_process_end got unexpected item_id: %s.', item_id
            )
            bui.screenmessage(
                bui.Lstr(
                    translate=('serverResponses', 'You got a ${ITEM}!'),
                    subs=[('${ITEM}', item_id)],
                ),
                color=(0, 1, 0),
            )
            if bui.asset_loads_allowed():
                bui.getsound('cashRegister').play()

    def on_engine_will_reset(self) -> None:
        """Called just before classic resets the engine.

        This happens at various times such as session switches.
        """

        self._save_account_state()

    def on_engine_did_reset(self) -> None:
        """Called just after classic resets the engine.

        This happens at various times such as session switches.
        """

        # Restore any old league vis state we had; this allows the user
        # to see animations for league improvements or other changes
        # that have occurred since the last time we were visible.
        self._restore_account_state()

    def _update_purchases(self) -> None:
        self._possibly_request_purchases()

    def _possibly_request_purchases(self) -> None:
        if self._purchase_request_in_flight:
            return

        self._purchase_request_in_flight = True
        bui.accountlog.debug('Requesting latest purchases state...')

        plus = bui.app.plus
        assert plus is not None
        if plus.accounts.primary is None:
            raise RuntimeError(
                'No account present when requesting classic purchases.'
            )

        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bacommon.classic.GetClassicPurchasesMessage(),
                on_response=bui.WeakCallPartial(
                    self._on_get_classic_purchases_response
                ),
            )

    def _on_get_classic_purchases_response(
        self, response: bacommon.classic.GetClassicPurchasesResponse | Exception
    ) -> None:
        assert self._purchase_request_in_flight
        self._purchase_request_in_flight = False

        if isinstance(response, Exception):
            if isinstance(response, CommunicationError):
                # No biggie; we expect these when offline/etc.
                pass
            else:
                bui.netlog.exception('Error requesting classic purchases.')
            return

        # If we're no longer looking for a state, we can abort early.
        if self._target_purchases_state is None:
            bui.accountlog.debug(
                'No longer looking for new purchases state; aborting fetch.'
            )
            self._purchases_update_timer = None
            return

        state = self._state_from_purchases(response.purchases)

        # If this is NOT the state we're after, ignore and keep going.
        if state != self._target_purchases_state:
            return

        # Ok, this is what we were after. Store a frozen version of it
        # and its hash and push it to the classic subsystem.
        self._current_purchases = frozenset(response.purchases)
        self._current_purchases_state = state

        assert bui.app.classic is not None
        bui.app.classic.purchases = self._current_purchases

        bui.accountlog.debug(
            'Updated purchases state to %s: (%s items)',
            state,
            len(self._current_purchases),
        )
        self._purchases_update_timer = None

    @staticmethod
    def _state_from_purchases(purchases: Iterable[str]) -> str:
        return hashlib.md5(','.join(sorted(purchases)).encode()).hexdigest()

    def _update_for_primary_account(
        self, account: bui.AccountV2Handle | None
    ) -> None:
        """Update subscriptions/etc. for a new primary account state."""
        assert bui.in_logic_thread()
        plus = bui.app.plus

        assert plus is not None

        classic = bui.app.classic
        assert classic is not None

        if account is not None:
            self._current_account_id = account.accountid
            self._restore_account_state()
        else:
            self._save_account_state()
            self._current_account_id = None

        # For testing subscription functionality.
        if os.environ.get('BA_SUBSCRIPTION_TEST') == '1':
            if account is None:
                self._test_sub = None
            else:
                with account:
                    self._test_sub = plus.cloud.subscribe_test(
                        self._on_sub_test_update
                    )
        else:
            self._test_sub = None

        if account is None:
            classic.gold_pass = False
            classic.tokens = 0
            classic.tickets = 0
            classic.purchases = frozenset()
            classic.chest_dock_full = False
            classic.remove_ads = False
            self._target_purchases_state = None
            self._account_data_sub = None
            _baclassic.set_root_ui_account_values(
                tickets=-1,
                tokens=-1,
                league_type='',
                league_number=-1,
                league_rank=-1,
                achievements_percent_text='',
                level_text='',
                xp_text='',
                inbox_count=-1,
                inbox_count_is_max=False,
                inbox_announce_text='',
                gold_pass=False,
                chest_0_appearance='',
                chest_1_appearance='',
                chest_2_appearance='',
                chest_3_appearance='',
                chest_0_create_time=-1.0,
                chest_1_create_time=-1.0,
                chest_2_create_time=-1.0,
                chest_3_create_time=-1.0,
                chest_0_unlock_time=-1.0,
                chest_1_unlock_time=-1.0,
                chest_2_unlock_time=-1.0,
                chest_3_unlock_time=-1.0,
                chest_0_unlock_tokens=-1,
                chest_1_unlock_tokens=-1,
                chest_2_unlock_tokens=-1,
                chest_3_unlock_tokens=-1,
                chest_0_ad_allow_time=-1.0,
                chest_1_ad_allow_time=-1.0,
                chest_2_ad_allow_time=-1.0,
                chest_3_ad_allow_time=-1.0,
                store_style='',
            )
            self._have_account_values = False
            self._update_ui_live_state()

        else:
            # Establish a subscription to inform us whenever basic stuff
            # (token count, chests, etc) changes.
            with account:
                self._account_data_sub = (
                    plus.cloud.subscribe_classic_account_data(
                        self._on_classic_account_data_change
                    )
                )

    def _update_for_connectivity_change(self, connected: bool) -> None:
        """Update when the app's connectivity state changes."""
        self._have_connectivity = connected
        self._update_ui_live_state()

    def _update_ui_live_state(self) -> None:
        # We want to show ui elements faded if we don't have a live
        # connection to the master-server OR if we haven't received a
        # set of account values from them yet. If we just plug in raw
        # connectivity state here we get UI stuff un-fading a moment or
        # two before values appear (since the subscriptions have not
        # sent us any values yet) which looks odd.
        _baclassic.set_have_live_account_values(
            self._have_connectivity and self._have_account_values
        )

    def _on_sub_test_update(self, val: int | None) -> None:
        print(f'GOT SUB TEST UPDATE: {val}')

    def _on_classic_account_data_change(
        self, val: bacommon.classic.ClassicLiveAccountClientData
    ) -> None:
        achp = round(val.achievements / max(val.achievements_total, 1) * 100.0)

        bui.accountlog.debug('Got new classic account data.')

        chest0 = val.chests.get('0')
        chest1 = val.chests.get('1')
        chest2 = val.chests.get('2')
        chest3 = val.chests.get('3')

        # Keep a few handy values on classic updated with the latest
        # data.
        classic = bui.app.classic
        assert classic is not None
        classic.remove_ads = val.remove_ads
        classic.gold_pass = val.gold_pass
        classic.tokens = val.tokens
        classic.tickets = val.tickets

        self._target_purchases_state = val.purchases_state

        # If they want us to ask for a review (and we haven't yet), do
        # so.
        if val.Flag.ASK_FOR_REVIEW in val.flags:
            cfg = bui.app.config
            if (
                not cfg.get(self._ASKED_FOR_REVIEW_CONFIG_KEY, False)
                and bui.native_review_request_supported()
            ):
                cfg[self._ASKED_FOR_REVIEW_CONFIG_KEY] = True
                cfg.commit()
                bui.native_review_request()

        # If someone replaced our purchases in the classic subsystem,
        # fix it.
        if (
            self._current_purchases is not None
            and self._current_purchases is not classic.purchases
        ):
            classic.purchases = self._current_purchases

        # If we need to fetch purchases, set up a timer to do so until
        # successful and possibly kick off an immediate attempt.
        if (
            self._target_purchases_state is not None
            and self._current_purchases_state != self._target_purchases_state
        ):
            bui.accountlog.debug(
                'Account purchases state is %s; we have %s. Will fetch new.',
                self._target_purchases_state,
                self._current_purchases_state,
            )
            if self._purchases_update_timer is not None:
                # Ok there's already a timer going; just let it keep
                # doing its thing.
                pass
            else:
                self._purchases_update_timer = bui.AppTimer(
                    3.456, self._update_purchases, repeat=True
                )
                self._possibly_request_purchases()

        else:
            # Not dirty; don't need a timer.
            self._purchases_update_timer = None

        classic.chest_dock_full = (
            chest0 is not None
            and chest1 is not None
            and chest2 is not None
            and chest3 is not None
        )

        _baclassic.set_root_ui_account_values(
            tickets=val.tickets,
            tokens=val.tokens,
            league_type=(
                '' if val.league_type is None else val.league_type.value
            ),
            league_number=(-1 if val.league_num is None else val.league_num),
            league_rank=(-1 if val.league_rank is None else val.league_rank),
            achievements_percent_text=f'{achp}%',
            level_text=str(val.level),
            xp_text=f'{val.xp}/{val.xpmax}',
            inbox_count=val.inbox_count,
            inbox_count_is_max=val.inbox_count_is_max,
            inbox_announce_text=(
                bui.Lstr(resource='unclaimedPrizesText').evaluate()
                if val.inbox_contains_prize
                else ''
            ),
            gold_pass=val.gold_pass,
            chest_0_appearance=(
                '' if chest0 is None else chest0.appearance.value
            ),
            chest_1_appearance=(
                '' if chest1 is None else chest1.appearance.value
            ),
            chest_2_appearance=(
                '' if chest2 is None else chest2.appearance.value
            ),
            chest_3_appearance=(
                '' if chest3 is None else chest3.appearance.value
            ),
            chest_0_create_time=(
                -1.0 if chest0 is None else chest0.create_time.timestamp()
            ),
            chest_1_create_time=(
                -1.0 if chest1 is None else chest1.create_time.timestamp()
            ),
            chest_2_create_time=(
                -1.0 if chest2 is None else chest2.create_time.timestamp()
            ),
            chest_3_create_time=(
                -1.0 if chest3 is None else chest3.create_time.timestamp()
            ),
            chest_0_unlock_time=(
                -1.0 if chest0 is None else chest0.unlock_time.timestamp()
            ),
            chest_1_unlock_time=(
                -1.0 if chest1 is None else chest1.unlock_time.timestamp()
            ),
            chest_2_unlock_time=(
                -1.0 if chest2 is None else chest2.unlock_time.timestamp()
            ),
            chest_3_unlock_time=(
                -1.0 if chest3 is None else chest3.unlock_time.timestamp()
            ),
            chest_0_unlock_tokens=(
                -1 if chest0 is None else chest0.unlock_tokens
            ),
            chest_1_unlock_tokens=(
                -1 if chest1 is None else chest1.unlock_tokens
            ),
            chest_2_unlock_tokens=(
                -1 if chest2 is None else chest2.unlock_tokens
            ),
            chest_3_unlock_tokens=(
                -1 if chest3 is None else chest3.unlock_tokens
            ),
            chest_0_ad_allow_time=(
                -1.0
                if chest0 is None or chest0.ad_allow_time is None
                else chest0.ad_allow_time.timestamp()
            ),
            chest_1_ad_allow_time=(
                -1.0
                if chest1 is None or chest1.ad_allow_time is None
                else chest1.ad_allow_time.timestamp()
            ),
            chest_2_ad_allow_time=(
                -1.0
                if chest2 is None or chest2.ad_allow_time is None
                else chest2.ad_allow_time.timestamp()
            ),
            chest_3_ad_allow_time=(
                -1.0
                if chest3 is None or chest3.ad_allow_time is None
                else chest3.ad_allow_time.timestamp()
            ),
            store_style=val.store_style.value,
        )

        # Note that we have values and updated faded state accordingly.
        self._have_account_values = True
        self._update_ui_live_state()

    def _root_ui_menu_press(self) -> None:
        from babase import menu_press

        ui = bui.app.ui_v1

        # If *any* main-window is up, kill it and resume play.
        old_window = ui.get_main_window()
        if old_window is not None:

            bui.getsound('swish').play()

            classic = bui.app.classic
            assert classic is not None
            classic.resume()

            ui.clear_main_window()
        else:
            # Otherwise act like a standard menu button.
            menu_press()

    def _root_ui_account_press(self) -> None:
        from bauiv1lib.account.settings import AccountSettingsWindow

        bui.app.ui_v1.auxiliary_window_activate(
            win_type=AccountSettingsWindow,
            win_create_call=lambda: AccountSettingsWindow(
                origin_widget=bui.get_special_widget('account_button')
            ),
        )

    def _root_ui_squad_press(self) -> None:
        btn = bui.get_special_widget('squad_button')
        center = btn.get_screen_space_center()
        if bui.app.classic is not None:
            bui.app.classic.party_icon_activate(center)
        else:
            logging.warning('party_icon_activate: no classic.')

    def _root_ui_settings_press(self) -> None:
        from bauiv1lib.settings.allsettings import AllSettingsWindow

        bui.app.ui_v1.auxiliary_window_activate(
            win_type=AllSettingsWindow,
            win_create_call=lambda: AllSettingsWindow(
                origin_widget=bui.get_special_widget('settings_button')
            ),
        )

    def _root_ui_achievements_press(self) -> None:
        from bauiv1lib.achievements import AchievementsWindow

        btn = bui.get_special_widget('achievements_button')

        if not self._ensure_signed_in(origin_widget=btn):
            return

        wait_for_connectivity(
            on_connected=lambda: bui.app.ui_v1.auxiliary_window_activate(
                win_type=AchievementsWindow,
                win_create_call=lambda: AchievementsWindow(origin_widget=btn),
            )
        )

    def _root_ui_inbox_press(self) -> None:
        from bauiv1lib.inbox import InboxWindow

        btn = bui.get_special_widget('inbox_button')

        if not self._ensure_signed_in(origin_widget=btn):
            return

        wait_for_connectivity(
            on_connected=lambda: bui.app.ui_v1.auxiliary_window_activate(
                win_type=InboxWindow,
                win_create_call=lambda: InboxWindow(origin_widget=btn),
            )
        )

    def _root_ui_store_press(self) -> None:
        import bacommon.docui.v1 as dui1

        from bauiv1lib.docui import DocUIWindow
        from bauiv1lib.store import StoreUIController

        btn = bui.get_special_widget('store_button')

        if not self._ensure_signed_in(origin_widget=btn):
            return

        # Pop up an auxiliary window wherever we are in the nav stack.
        wait_for_connectivity(
            on_connected=lambda: bui.app.ui_v1.auxiliary_window_activate(
                win_type=DocUIWindow,
                win_create_call=bui.CallStrict(
                    StoreUIController().create_window,
                    dui1.Request('/'),
                    origin_widget=btn,
                    uiopenstateid='classicstore',
                ),
                win_extra_type_id=(
                    StoreUIController.get_window_extra_type_id()
                ),
            )
        )

    def _root_ui_tickets_meter_press(self) -> None:
        from bauiv1lib.resourcetypeinfo import ResourceTypeInfoWindow

        ResourceTypeInfoWindow(
            'tickets', origin_widget=bui.get_special_widget('tickets_meter')
        )

    def _root_ui_tokens_meter_press(self) -> None:
        from bauiv1lib.resourcetypeinfo import ResourceTypeInfoWindow

        ResourceTypeInfoWindow(
            'tokens', origin_widget=bui.get_special_widget('tokens_meter')
        )

    def _root_ui_trophy_meter_press(self) -> None:
        from bauiv1lib.league.rankwindow import LeagueRankWindow

        btn = bui.get_special_widget('trophy_meter')

        if not self._ensure_signed_in(origin_widget=btn):
            return

        bui.app.ui_v1.auxiliary_window_activate(
            win_type=LeagueRankWindow,
            win_create_call=lambda: LeagueRankWindow(origin_widget=btn),
        )

    def _root_ui_level_meter_press(self) -> None:
        from bauiv1lib.resourcetypeinfo import ResourceTypeInfoWindow

        btn = bui.get_special_widget('level_meter')

        if not self._ensure_signed_in(origin_widget=btn):
            return

        ResourceTypeInfoWindow('xp', origin_widget=btn)

    def _root_ui_inventory_press(self) -> None:
        import bacommon.docui.v1 as dui1

        from bauiv1lib.docui import DocUIWindow
        from bauiv1lib.inventory import InventoryUIController

        # Pop up an auxiliary window wherever we are in the nav stack.
        bui.app.ui_v1.auxiliary_window_activate(
            win_type=DocUIWindow,
            win_create_call=bui.CallStrict(
                InventoryUIController().create_window,
                dui1.Request('/'),
                origin_widget=bui.get_special_widget('inventory_button'),
                uiopenstateid='classicinventory',
            ),
            win_extra_type_id=InventoryUIController.get_window_extra_type_id(),
        )

    def _ensure_signed_in(self, *, origin_widget: bui.Widget | None) -> bool:
        """Make sure we're signed in (requiring modern v2 accounts)."""
        from bauiv1lib.account.signin import show_sign_in_prompt

        plus = bui.app.plus
        if plus is None:
            bui.screenmessage('This requires plus.', color=(1, 0, 0))
            bui.getsound('error').play()
            return False
        if plus.accounts.primary is None:
            show_sign_in_prompt(origin_widget=origin_widget)
            return False
        return True

    def _root_ui_get_tokens_press(self) -> None:
        from bauiv1lib.gettokens import GetTokensWindow, show_get_tokens_window

        btn = bui.get_special_widget('get_tokens_button')

        if not self._ensure_signed_in(origin_widget=btn):
            return

        if bool(True):
            show_get_tokens_window(origin_widget=btn, toggle=True)
        else:
            bui.app.ui_v1.auxiliary_window_activate(
                win_type=GetTokensWindow,
                win_create_call=lambda: GetTokensWindow(origin_widget=btn),
            )

    def _root_ui_chest_slot_pressed(self, index: int) -> None:
        from bauiv1lib.chest import ChestWindow

        widgetid: Literal[
            'chest_0_button',
            'chest_1_button',
            'chest_2_button',
            'chest_3_button',
        ]
        winclass: type[ChestWindow]
        if index == 0:
            widgetid = 'chest_0_button'
            winclass = ChestWindow
            extratypeid = '0'
        elif index == 1:
            widgetid = 'chest_1_button'
            winclass = ChestWindow
            extratypeid = '1'
        elif index == 2:
            widgetid = 'chest_2_button'
            winclass = ChestWindow
            extratypeid = '2'
        elif index == 3:
            widgetid = 'chest_3_button'
            winclass = ChestWindow
            extratypeid = '3'
        else:
            raise RuntimeError(f'Invalid index {index}')

        wait_for_connectivity(
            on_connected=lambda: bui.app.ui_v1.auxiliary_window_activate(
                win_type=winclass,
                win_create_call=lambda: winclass(
                    index=index,
                    origin_widget=bui.get_special_widget(widgetid),
                ),
                win_extra_type_id=extratypeid,
            )
        )

    def _save_account_state(self) -> None:
        if self._current_account_id is None:
            return

        vals = _baclassic.get_account_state()
        if vals is None:
            return

        # Stuff some vals of our own in the dict and save to config.
        assert 'a' not in vals
        vals['a'] = self._current_account_id

        assert bui.app.classic is not None

        assert 'p' not in vals
        vals['p'] = list(bui.app.classic.purchases)

        cfg = bui.app.config
        cfg[self._ACCOUNT_STATE_CONFIG_KEY] = vals
        cfg.commit()

    def _restore_account_state(self) -> None:
        # If we've got a stored state for the current account, restore
        # it.
        assert bui.app.classic is not None

        if self._current_account_id is None:
            return

        cfg = bui.app.config
        vals = cfg.get(self._ACCOUNT_STATE_CONFIG_KEY)

        if not isinstance(vals, dict):
            return

        # If the state applies to someone else, skip it.
        accountid = vals.get('a')
        if (
            not isinstance(accountid, str)
            or accountid != self._current_account_id
        ):
            return

        purchases = vals.get('p')
        if isinstance(purchases, list):

            if not all(isinstance(p, str) for p in purchases):
                bui.balog.exception('Invalid purchases state on restore.')
            else:
                self._current_purchases = frozenset(purchases)
                self._current_purchases_state = self._state_from_purchases(
                    purchases
                )
                bui.app.classic.purchases = self._current_purchases

        _baclassic.set_account_state(vals)

    @override
    def get_dev_console_ui_tab_buttons(
        self,
    ) -> list[bui.DevConsoleButtonDef]:
        return [
            bui.DevConsoleButtonDef(
                'MainWindow Template',
                bui.WeakCallStrict(self._main_win_template_press),
            ),
            bui.DevConsoleButtonDef(
                'DocUI Test', bui.WeakCallStrict(self._doc_ui_test_press)
            ),
        ]

    def _main_win_template_press(self) -> None:
        from bauiv1lib.template import show_template_main_window

        # This only works if a main ui is up.
        if bui.app.ui_v1.get_main_window() is None:
            bui.screenmessage(
                'This requires a main-window to be present.'
                ' Open a menu or whatnot first.',
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        # Unintuitively, swish sounds come from buttons, not windows.
        # And dev-console buttons don't make sounds. So we need to
        # explicitly do so here.
        bui.getsound('swish').play()

        show_template_main_window()

    def _doc_ui_test_press(self) -> None:
        from bauiv1lib.docuitest import show_test_doc_ui_window

        # This only works if a main ui is up.
        if bui.app.ui_v1.get_main_window() is None:
            bui.screenmessage(
                'This requires a main-window to be present.'
                ' Open a menu or whatnot first.',
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        # Unintuitively, swish sounds come from buttons, not windows.
        # And dev-console buttons don't make sounds. So we need to
        # explicitly do so here.
        bui.getsound('swish').play()

        show_test_doc_ui_window()
