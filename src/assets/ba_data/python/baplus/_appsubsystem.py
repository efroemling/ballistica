# Released under the MIT License. See LICENSE for details.
#
"""Provides plus app subsystem."""
from __future__ import annotations

from typing import TYPE_CHECKING, override

from babase import AppSubsystem

import _baplus
from baplus._ads import AdsSubsystem

if TYPE_CHECKING:
    from typing import Callable, Any

    import bacommon.bs
    from babase import AccountV2Subsystem

    from baplus._cloud import CloudSubsystem


class PlusAppSubsystem(AppSubsystem):
    """Subsystem for plus functionality in the app.

    Access the single shared instance of this class via the
    :attr:`~babase.App.plus` attr on the :class:`~babase.App` class.
    Note that it is possible for this to be ``None`` if the plus package
    is not present, so code should handle that case gracefully.
    """

    # pylint: disable=too-many-public-methods

    accounts: AccountV2Subsystem
    cloud: CloudSubsystem

    def __init__(self) -> None:

        #: Ad wrangling functionality.
        self.ads: AdsSubsystem = AdsSubsystem()

    @override
    def on_app_loading(self) -> None:
        """:meta private:"""
        _baplus.on_app_loading()
        self.accounts.on_app_loading()

    @staticmethod
    def add_v1_account_transaction(
        transaction: dict, callback: Callable | None = None
    ) -> None:
        """:meta private:"""
        return _baplus.add_v1_account_transaction(transaction, callback)

    @staticmethod
    def game_service_has_leaderboard(game: str, config: str) -> bool:
        """Given a game and config string, returns whether there is a
        leaderboard for it on the game service.

        :meta private:
        """
        return _baplus.game_service_has_leaderboard(game, config)

    @staticmethod
    def get_master_server_address(source: int = -1, version: int = 1) -> str:
        """Return the address of the master server.

        :meta private:
        """
        return _baplus.get_master_server_address(source, version)

    @staticmethod
    def get_classic_news_show() -> str:
        """:meta private:"""
        return _baplus.get_classic_news_show()

    @staticmethod
    def get_price(item: str) -> str | None:
        """:meta private:"""
        return _baplus.get_price(item)

    @staticmethod
    def get_v1_account_display_string(full: bool = True) -> str:
        """:meta private:"""
        return _baplus.get_v1_account_display_string(full)

    @staticmethod
    def get_v1_account_misc_read_val(name: str, default_value: Any) -> Any:
        """:meta private:"""
        return _baplus.get_v1_account_misc_read_val(name, default_value)

    @staticmethod
    def get_v1_account_misc_read_val_2(name: str, default_value: Any) -> Any:
        """:meta private:"""
        return _baplus.get_v1_account_misc_read_val_2(name, default_value)

    @staticmethod
    def get_v1_account_misc_val(name: str, default_value: Any) -> Any:
        """:meta private:"""
        return _baplus.get_v1_account_misc_val(name, default_value)

    @staticmethod
    def get_v1_account_name() -> str:
        """:meta private:"""
        return _baplus.get_v1_account_name()

    @staticmethod
    def get_v1_account_public_login_id() -> str | None:
        """:meta private:"""
        return _baplus.get_v1_account_public_login_id()

    @staticmethod
    def get_v1_account_state() -> str:
        """:meta private:"""
        return _baplus.get_v1_account_state()

    @staticmethod
    def get_v1_account_state_num() -> int:
        """:meta private:"""
        return _baplus.get_v1_account_state_num()

    # @staticmethod
    # def get_v1_account_ticket_count() -> int:
    #     """Return the number of tickets for the current account.

    #     :meta private:
    #     """
    #     return _baplus.get_v1_account_ticket_count()

    @staticmethod
    def get_v1_account_type() -> str:
        """:meta private:"""
        return _baplus.get_v1_account_type()

    @staticmethod
    def get_v2_fleet() -> str:
        """:meta private:"""
        return _baplus.get_v2_fleet()

    @staticmethod
    def have_outstanding_v1_account_transactions() -> bool:
        """:meta private:"""
        return _baplus.have_outstanding_v1_account_transactions()

    @staticmethod
    def in_game_purchase(item: str, price: int) -> None:
        """:meta private:"""
        return _baplus.in_game_purchase(item, price)

    @staticmethod
    def is_blessed() -> bool:
        """:meta private:"""
        return _baplus.is_blessed()

    @staticmethod
    def mark_config_dirty() -> None:
        """:meta private:"""
        return _baplus.mark_config_dirty()

    @staticmethod
    def power_ranking_query(callback: Callable, season: Any = None) -> None:
        """:meta private:"""
        return _baplus.power_ranking_query(callback, season)

    @staticmethod
    def purchase(item: str) -> None:
        """:meta private:"""
        return _baplus.purchase(item)

    @staticmethod
    def report_achievement(
        achievement: str, pass_to_account: bool = True
    ) -> None:
        """:meta private:"""
        return _baplus.report_achievement(achievement, pass_to_account)

    @staticmethod
    def reset_achievements() -> None:
        """:meta private:"""
        return _baplus.reset_achievements()

    @staticmethod
    def restore_purchases() -> None:
        """:meta private:"""
        return _baplus.restore_purchases()

    @staticmethod
    def run_v1_account_transactions() -> None:
        """:meta private:"""
        return _baplus.run_v1_account_transactions()

    @staticmethod
    def sign_in_v1(account_type: str) -> None:
        """:meta private:"""
        return _baplus.sign_in_v1(account_type)

    @staticmethod
    def sign_out_v1(v2_embedded: bool = False) -> None:
        """:meta private:"""
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
        """Submit a score to the server.

        Callback will be called with the results. As a courtesy, please
        don't send fake scores to the server. I'd prefer to devote my
        time to improving the game instead of trying to make the score
        server more mischief-proof.

        :meta private:
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
        """:meta private:"""
        return _baplus.tournament_query(callback, args)

    @staticmethod
    def supports_purchases() -> bool:
        """Does this platform support in-app-purchases?

        :meta private:
        """
        return _baplus.supports_purchases()

    @staticmethod
    def show_game_service_ui(
        show: str = 'general',
        game: str | None = None,
        game_version: str | None = None,
    ) -> None:
        """Show game-service provided UI.

        :meta private:
        """
        _baplus.show_game_service_ui(show, game, game_version)
