# Released under the MIT License. See LICENSE for details.
#
"""Provides plus app subsystem."""
from __future__ import annotations

from typing import TYPE_CHECKING, override

from babase import AppSubsystem

import _baplus

if TYPE_CHECKING:
    from typing import Callable, Any

    import bacommon.bs
    from babase import AccountV2Subsystem

    from baplus._cloud import CloudSubsystem


class PlusAppSubsystem(AppSubsystem):
    """Subsystem for plus functionality in the app.

    The single shared instance of this app can be accessed at
    babase.app.plus. Note that it is possible for this to be None if the
    plus package is not present, and code should handle that case
    gracefully.
    """

    # pylint: disable=too-many-public-methods

    # Note: this is basically just a wrapper around _baplus for
    # type-checking purposes. Maybe there's some smart way we could skip
    # the overhead of this wrapper at runtime.

    accounts: AccountV2Subsystem
    cloud: CloudSubsystem

    @override
    def on_app_loading(self) -> None:
        _baplus.on_app_loading()
        self.accounts.on_app_loading()

    @staticmethod
    def add_v1_account_transaction(
        transaction: dict, callback: Callable | None = None
    ) -> None:
        """(internal)"""
        return _baplus.add_v1_account_transaction(transaction, callback)

    @staticmethod
    def game_service_has_leaderboard(game: str, config: str) -> bool:
        """(internal)

        Given a game and config string, returns whether there is a leaderboard
        for it on the game service.
        """
        return _baplus.game_service_has_leaderboard(game, config)

    @staticmethod
    def get_master_server_address(source: int = -1, version: int = 1) -> str:
        """(internal)

        Return the address of the master server.
        """
        return _baplus.get_master_server_address(source, version)

    @staticmethod
    def get_classic_news_show() -> str:
        """(internal)"""
        return _baplus.get_classic_news_show()

    @staticmethod
    def get_price(item: str) -> str | None:
        """(internal)"""
        return _baplus.get_price(item)

    @staticmethod
    def get_v1_account_product_purchased(item: str) -> bool:
        """(internal)"""
        return _baplus.get_v1_account_product_purchased(item)

    @staticmethod
    def get_v1_account_product_purchases_state() -> int:
        """(internal)"""
        return _baplus.get_v1_account_product_purchases_state()

    @staticmethod
    def get_v1_account_display_string(full: bool = True) -> str:
        """(internal)"""
        return _baplus.get_v1_account_display_string(full)

    @staticmethod
    def get_v1_account_misc_read_val(name: str, default_value: Any) -> Any:
        """(internal)"""
        return _baplus.get_v1_account_misc_read_val(name, default_value)

    @staticmethod
    def get_v1_account_misc_read_val_2(name: str, default_value: Any) -> Any:
        """(internal)"""
        return _baplus.get_v1_account_misc_read_val_2(name, default_value)

    @staticmethod
    def get_v1_account_misc_val(name: str, default_value: Any) -> Any:
        """(internal)"""
        return _baplus.get_v1_account_misc_val(name, default_value)

    @staticmethod
    def get_v1_account_name() -> str:
        """(internal)"""
        return _baplus.get_v1_account_name()

    @staticmethod
    def get_v1_account_public_login_id() -> str | None:
        """(internal)"""
        return _baplus.get_v1_account_public_login_id()

    @staticmethod
    def get_v1_account_state() -> str:
        """(internal)"""
        return _baplus.get_v1_account_state()

    @staticmethod
    def get_v1_account_state_num() -> int:
        """(internal)"""
        return _baplus.get_v1_account_state_num()

    @staticmethod
    def get_v1_account_ticket_count() -> int:
        """(internal)

        Return the number of tickets for the current account.
        """
        return _baplus.get_v1_account_ticket_count()

    @staticmethod
    def get_v1_account_type() -> str:
        """(internal)"""
        return _baplus.get_v1_account_type()

    @staticmethod
    def get_v2_fleet() -> str:
        """(internal)"""
        return _baplus.get_v2_fleet()

    @staticmethod
    def have_outstanding_v1_account_transactions() -> bool:
        """(internal)"""
        return _baplus.have_outstanding_v1_account_transactions()

    @staticmethod
    def in_game_purchase(item: str, price: int) -> None:
        """(internal)"""
        return _baplus.in_game_purchase(item, price)

    @staticmethod
    def is_blessed() -> bool:
        """(internal)"""
        return _baplus.is_blessed()

    @staticmethod
    def mark_config_dirty() -> None:
        """(internal)

        Category: General Utility Functions
        """
        return _baplus.mark_config_dirty()

    @staticmethod
    def power_ranking_query(callback: Callable, season: Any = None) -> None:
        """(internal)"""
        return _baplus.power_ranking_query(callback, season)

    @staticmethod
    def purchase(item: str) -> None:
        """(internal)"""
        return _baplus.purchase(item)

    @staticmethod
    def report_achievement(
        achievement: str, pass_to_account: bool = True
    ) -> None:
        """(internal)"""
        return _baplus.report_achievement(achievement, pass_to_account)

    @staticmethod
    def reset_achievements() -> None:
        """(internal)"""
        return _baplus.reset_achievements()

    @staticmethod
    def restore_purchases() -> None:
        """(internal)"""
        return _baplus.restore_purchases()

    @staticmethod
    def run_v1_account_transactions() -> None:
        """(internal)"""
        return _baplus.run_v1_account_transactions()

    @staticmethod
    def sign_in_v1(account_type: str) -> None:
        """(internal)

        Category: General Utility Functions
        """
        return _baplus.sign_in_v1(account_type)

    @staticmethod
    def sign_out_v1(v2_embedded: bool = False) -> None:
        """(internal)

        Category: General Utility Functions
        """
        return _baplus.sign_out_v1(v2_embedded)

    @staticmethod
    def submit_score(
        game: str,
        config: str,
        name: Any,
        score: int | None,
        callback: Callable,
        *,
        order: str = 'increasing',
        tournament_id: str | None = None,
        score_type: str = 'points',
        campaign: str | None = None,
        level: str | None = None,
    ) -> None:
        """(internal)

        Submit a score to the server; callback will be called with the results.
        As a courtesy, please don't send fake scores to the server. I'd prefer
        to devote my time to improving the game instead of trying to make the
        score server more mischief-proof.
        """
        return _baplus.submit_score(
            game,
            config,
            name,
            score,
            callback,
            order,
            tournament_id,
            score_type,
            campaign,
            level,
        )

    @staticmethod
    def tournament_query(
        callback: Callable[[dict | None], None], args: dict
    ) -> None:
        """(internal)"""
        return _baplus.tournament_query(callback, args)

    @staticmethod
    def supports_purchases() -> bool:
        """Does this platform support in-app-purchases?"""
        return _baplus.supports_purchases()

    @staticmethod
    def have_incentivized_ad() -> bool:
        """Is an incentivized ad available?"""
        return _baplus.have_incentivized_ad()

    @staticmethod
    def has_video_ads() -> bool:
        """Are video ads available?"""
        return _baplus.has_video_ads()

    @staticmethod
    def can_show_ad() -> bool:
        """Can we show an ad?"""
        return _baplus.can_show_ad()

    @staticmethod
    def show_ad(
        purpose: str, on_completion_call: Callable[[], None] | None = None
    ) -> None:
        """Show an ad."""
        _baplus.show_ad(purpose, on_completion_call)

    @staticmethod
    def show_ad_2(
        purpose: str, on_completion_call: Callable[[bool], None] | None = None
    ) -> None:
        """Show an ad."""
        _baplus.show_ad_2(purpose, on_completion_call)

    @staticmethod
    def show_game_service_ui(
        show: str = 'general',
        game: str | None = None,
        game_version: str | None = None,
    ) -> None:
        """Show game-service provided UI."""
        _baplus.show_game_service_ui(show, game, game_version)
