# Released under the MIT License. See LICENSE for details.
#
"""Contains ClassicAppMode."""
from __future__ import annotations

import os
import logging
from functools import partial
from typing import TYPE_CHECKING, override

from bacommon.app import AppExperience
import babase
import bauiv1

import _baclassic

if TYPE_CHECKING:
    from typing import Callable, Any

    from efro.call import CallbackRegistration
    import bacommon.cloud


# ba_meta export babase.AppMode
class ClassicAppMode(babase.AppMode):
    """AppMode for the classic BombSquad experience."""

    def __init__(self) -> None:
        self._on_primary_account_changed_callback: (
            CallbackRegistration | None
        ) = None
        self._test_sub: babase.CloudSubscription | None = None
        self._account_data_sub: babase.CloudSubscription | None = None

    @override
    @classmethod
    def get_app_experience(cls) -> AppExperience:
        return AppExperience.MELEE

    @override
    @classmethod
    def _supports_intent(cls, intent: babase.AppIntent) -> bool:
        # We support default and exec intents currently.
        return isinstance(
            intent, babase.AppIntentExec | babase.AppIntentDefault
        )

    @override
    def handle_intent(self, intent: babase.AppIntent) -> None:
        if isinstance(intent, babase.AppIntentExec):
            _baclassic.classic_app_mode_handle_app_intent_exec(intent.code)
            return
        assert isinstance(intent, babase.AppIntentDefault)
        _baclassic.classic_app_mode_handle_app_intent_default()

    @override
    def on_activate(self) -> None:

        # Let the native layer do its thing.
        _baclassic.classic_app_mode_activate()

        app = babase.app
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
        ui.root_ui_calls[ui.RootUIElement.CHEST_SLOT_1] = partial(
            self._root_ui_chest_slot_pressed, 1
        )
        ui.root_ui_calls[ui.RootUIElement.CHEST_SLOT_2] = partial(
            self._root_ui_chest_slot_pressed, 2
        )
        ui.root_ui_calls[ui.RootUIElement.CHEST_SLOT_3] = partial(
            self._root_ui_chest_slot_pressed, 3
        )
        ui.root_ui_calls[ui.RootUIElement.CHEST_SLOT_4] = partial(
            self._root_ui_chest_slot_pressed, 4
        )

        # We want to be informed when primary account changes.
        self._on_primary_account_changed_callback = (
            plus.accounts.on_primary_account_changed_callbacks.register(
                self.update_for_primary_account
            )
        )
        # Establish subscriptions/etc. for any current primary account.
        self.update_for_primary_account(plus.accounts.primary)

    @override
    def on_deactivate(self) -> None:

        classic = babase.app.classic

        # Stop being informed of account changes.
        self._on_primary_account_changed_callback = None

        # Remove anything following any current account.
        self.update_for_primary_account(None)

        # Save where we were in the UI so we return there next time.
        if classic is not None:
            classic.save_ui_state()

        # Let the native layer do its thing.
        _baclassic.classic_app_mode_deactivate()

    @override
    def on_app_active_changed(self) -> None:
        # If we've gone inactive, bring up the main menu, which has the
        # side effect of pausing the action (when possible).
        if not babase.app.active:
            babase.invoke_main_menu()

    def update_for_primary_account(
        self, account: babase.AccountV2Handle | None
    ) -> None:
        """Update subscriptions/etc. for a new primary account state."""
        assert babase.in_logic_thread()
        plus = babase.app.plus

        assert plus is not None

        if account is not None:
            babase.set_ui_account_state(True, account.tag)
        else:
            babase.set_ui_account_state(False)

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
            self._account_data_sub = None
            _baclassic.set_root_ui_values(
                tickets_text='-',
                tokens_text='-',
                league_rank_text='-',
                league_type='',
                achievements_percent_text='-',
                level_text='-',
                xp_text='-',
            )

        else:
            with account:
                self._account_data_sub = (
                    plus.cloud.subscribe_classic_account_data(
                        self._on_classic_account_data_change
                    )
                )

    def _on_sub_test_update(self, val: int | None) -> None:
        print(f'GOT SUB TEST UPDATE: {val}')

    def _on_classic_account_data_change(
        self, val: bacommon.cloud.ClassicAccountLiveData
    ) -> None:
        achp = round(val.achievements / max(val.achievements_total, 1) * 100.0)
        _baclassic.set_root_ui_values(
            tickets_text=str(val.tickets),
            tokens_text=str(val.tokens),
            league_rank_text=(
                '-' if val.league_rank is None else f'#{val.league_rank}'
            ),
            league_type=(
                '' if val.league_type is None else val.league_type.value
            ),
            achievements_percent_text=f'{achp}%',
            level_text=str(val.level),
            xp_text=f'{val.xp}/{val.xpmax}',
        )

    def _root_ui_menu_press(self) -> None:
        from babase import push_back_press

        ui = babase.app.ui_v1

        # If *any* main-window is up, kill it and resume play.
        old_window = ui.get_main_window()
        if old_window is not None:

            classic = babase.app.classic
            assert classic is not None
            classic.resume()

            ui.clear_main_window()
            return

        push_back_press()

    def _root_ui_account_press(self) -> None:
        from bauiv1lib.account.settings import AccountSettingsWindow

        self._auxiliary_window_nav(
            win_type=AccountSettingsWindow,
            win_create_call=lambda: AccountSettingsWindow(
                origin_widget=bauiv1.get_special_widget('account_button')
            ),
        )

    def _root_ui_squad_press(self) -> None:
        btn = bauiv1.get_special_widget('squad_button')
        center = btn.get_screen_space_center()
        if bauiv1.app.classic is not None:
            bauiv1.app.classic.party_icon_activate(center)
        else:
            logging.warning('party_icon_activate: no classic.')

    def _root_ui_settings_press(self) -> None:
        from bauiv1lib.settings.allsettings import AllSettingsWindow

        self._auxiliary_window_nav(
            win_type=AllSettingsWindow,
            win_create_call=lambda: AllSettingsWindow(
                origin_widget=bauiv1.get_special_widget('settings_button')
            ),
        )

    def _auxiliary_window_nav(
        self,
        win_type: type[bauiv1.MainWindow],
        win_create_call: Callable[[], bauiv1.MainWindow],
    ) -> None:
        """Navigate to or away from an Auxiliary window.

        Auxiliary windows can be thought of as 'side quests' in the
        window hierarchy; places such as settings windows or league
        ranking windows that the user might want to visit without losing
        their place in the regular hierarchy.
        """
        # pylint: disable=unidiomatic-typecheck

        ui = babase.app.ui_v1

        current_main_window = ui.get_main_window()

        # Scan our ancestors for auxiliary states matching our type as
        # well as auxiliary states in general.
        aux_matching_state: bauiv1.MainWindowState | None = None
        aux_state: bauiv1.MainWindowState | None = None

        if current_main_window is None:
            raise RuntimeError(
                'Not currently handling no-top-level-window case.'
            )

        state = current_main_window.main_window_back_state
        while state is not None:
            assert state.window_type is not None
            if state.is_auxiliary:
                if state.window_type is win_type:
                    aux_matching_state = state
                else:
                    aux_state = state

            state = state.parent

        # If there's an ancestor auxiliary window-state matching our
        # type, back out past it (example: poking settings, navigating
        # down a level or two, and then poking settings again should
        # back out of settings).
        if aux_matching_state is not None:
            current_main_window.main_window_back_state = (
                aux_matching_state.parent
            )
            current_main_window.main_window_back()
            return

        # If there's an ancestory auxiliary state *not* matching our
        # type, crop the state and swap in our new auxiliary UI
        # (example: poking settings, then poking account, then poking
        # back should end up where things were before the settings
        # poke).
        if aux_state is not None:
            # Blow away the window stack and build a fresh one.
            ui.clear_main_window()
            ui.set_main_window(
                win_create_call(),
                from_window=False,  # Disable from-check.
                back_state=aux_state.parent,
                suppress_warning=True,
                is_auxiliary=True,
            )
            return

        # Ok, no auxiliary states found. Now if current window is
        # auxiliary and the type matches, simply do a back.
        if (
            current_main_window.main_window_is_auxiliary
            and type(current_main_window) is win_type
        ):
            current_main_window.main_window_back()
            return

        # If current window is auxiliary but type doesn't match,
        # swap it out for our new auxiliary UI.
        if current_main_window.main_window_is_auxiliary:
            ui.clear_main_window()
            ui.set_main_window(
                win_create_call(),
                from_window=False,  # Disable from-check.
                back_state=current_main_window.main_window_back_state,
                suppress_warning=True,
                is_auxiliary=True,
            )
            return

        # Ok, no existing auxiliary stuff was found period. Just
        # navigate forward to this UI.
        current_main_window.main_window_replace(
            win_create_call(), is_auxiliary=True
        )

    def _root_ui_achievements_press(self) -> None:
        from bauiv1lib.achievements import AchievementsWindow

        self._auxiliary_window_nav(
            win_type=AchievementsWindow,
            win_create_call=lambda: AchievementsWindow(
                origin_widget=bauiv1.get_special_widget('achievements_button')
            ),
        )

    def _root_ui_inbox_press(self) -> None:
        from bauiv1lib.inbox import InboxWindow

        self._auxiliary_window_nav(
            win_type=InboxWindow,
            win_create_call=lambda: InboxWindow(
                origin_widget=bauiv1.get_special_widget('inbox_button')
            ),
        )

    def _root_ui_store_press(self) -> None:
        from bauiv1lib.store.browser import StoreBrowserWindow

        self._auxiliary_window_nav(
            win_type=StoreBrowserWindow,
            win_create_call=lambda: StoreBrowserWindow(
                origin_widget=bauiv1.get_special_widget('store_button')
            ),
        )

    def _root_ui_tickets_meter_press(self) -> None:
        from bauiv1lib.resourcetypeinfo import ResourceTypeInfoWindow

        ResourceTypeInfoWindow(
            'tickets', origin_widget=bauiv1.get_special_widget('tickets_meter')
        )

    def _root_ui_tokens_meter_press(self) -> None:
        from bauiv1lib.resourcetypeinfo import ResourceTypeInfoWindow

        ResourceTypeInfoWindow(
            'tokens', origin_widget=bauiv1.get_special_widget('tokens_meter')
        )

    def _root_ui_trophy_meter_press(self) -> None:
        from bauiv1lib.account import show_sign_in_prompt
        from bauiv1lib.league.rankwindow import LeagueRankWindow

        plus = bauiv1.app.plus
        assert plus is not None
        if plus.get_v1_account_state() != 'signed_in':
            show_sign_in_prompt()
            return

        self._auxiliary_window_nav(
            win_type=LeagueRankWindow,
            win_create_call=lambda: LeagueRankWindow(
                origin_widget=bauiv1.get_special_widget('trophy_meter')
            ),
        )

    def _root_ui_level_meter_press(self) -> None:
        from bauiv1lib.resourcetypeinfo import ResourceTypeInfoWindow

        ResourceTypeInfoWindow(
            'xp', origin_widget=bauiv1.get_special_widget('level_meter')
        )

    def _root_ui_inventory_press(self) -> None:
        from bauiv1lib.inventory import InventoryWindow

        self._auxiliary_window_nav(
            win_type=InventoryWindow,
            win_create_call=lambda: InventoryWindow(
                origin_widget=bauiv1.get_special_widget('inventory_button')
            ),
        )

    def _root_ui_get_tokens_press(self) -> None:
        from bauiv1lib.gettokens import GetTokensWindow

        self._auxiliary_window_nav(
            win_type=GetTokensWindow,
            win_create_call=lambda: GetTokensWindow(
                origin_widget=bauiv1.get_special_widget('get_tokens_button')
            ),
        )

    def _root_ui_chest_slot_pressed(self, index: int) -> None:
        print(f'CHEST {index} PRESSED')
        babase.screenmessage('UNDER CONSTRUCTION.')
