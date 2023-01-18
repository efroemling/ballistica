# Released under the MIT License. See LICENSE for details.
#
"""A soft wrapper around _bainternal.

This allows code to use _bainternal functionality and get warnings
or fallbacks in some cases instead of hard errors. Code that absolutely
relies on the presence of _bainternal can just use that module directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    # noinspection PyUnresolvedReferences
    import _bainternal

    HAVE_INTERNAL = True
except ImportError:
    HAVE_INTERNAL = False

if TYPE_CHECKING:
    from typing import Callable, Any


# Code that will function without _bainternal but which should be updated
# to account for its absence should call this to draw attention to itself.
def _no_bainternal_warning() -> None:
    import logging

    logging.warning('INTERNAL CALL RUN WITHOUT INTERNAL PRESENT.')


# Code that won't work without _bainternal should raise these errors.
def _no_bainternal_error() -> RuntimeError:
    raise RuntimeError('_bainternal is not present')


def get_v2_fleet() -> str:
    """(internal)"""
    if HAVE_INTERNAL:
        return _bainternal.get_v2_fleet()
    raise _no_bainternal_error()


def get_master_server_address(source: int = -1, version: int = 1) -> str:
    """(internal)

    Return the address of the master server.
    """
    if HAVE_INTERNAL:
        return _bainternal.get_master_server_address(
            source=source, version=version
        )
    raise _no_bainternal_error()


def is_blessed() -> bool:
    """(internal)"""
    if HAVE_INTERNAL:
        return _bainternal.is_blessed()

    # Harmless to always just say no here.
    return False


def get_news_show() -> str:
    """(internal)"""
    if HAVE_INTERNAL:
        return _bainternal.get_news_show()
    raise _no_bainternal_error()


def game_service_has_leaderboard(game: str, config: str) -> bool:
    """(internal)

    Given a game and config string, returns whether there is a leaderboard
    for it on the game service.
    """
    if HAVE_INTERNAL:
        return _bainternal.game_service_has_leaderboard(
            game=game, config=config
        )
    # Harmless to always just say no here.
    return False


def report_achievement(achievement: str, pass_to_account: bool = True) -> None:
    """(internal)"""
    if HAVE_INTERNAL:
        _bainternal.report_achievement(
            achievement=achievement, pass_to_account=pass_to_account
        )
        return

    # Need to see if this actually still works as expected.. warning for now.
    _no_bainternal_warning()


# noinspection PyUnresolvedReferences
def submit_score(
    game: str,
    config: str,
    name: Any,
    score: int | None,
    callback: Callable,
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
    if HAVE_INTERNAL:
        _bainternal.submit_score(
            game=game,
            config=config,
            name=name,
            score=score,
            callback=callback,
            order=order,
            tournament_id=tournament_id,
            score_type=score_type,
            campaign=campaign,
            level=level,
        )
        return
    # This technically breaks since callback will never be called/etc.
    raise _no_bainternal_error()


def tournament_query(
    callback: Callable[[dict | None], None], args: dict
) -> None:
    """(internal)"""
    if HAVE_INTERNAL:
        _bainternal.tournament_query(callback=callback, args=args)
        return

    # This technically breaks since callback will never be called/etc.
    raise _no_bainternal_error()


def power_ranking_query(callback: Callable, season: Any = None) -> None:
    """(internal)"""
    if HAVE_INTERNAL:
        _bainternal.power_ranking_query(callback=callback, season=season)
        return

    # This technically breaks since callback will never be called/etc.
    raise _no_bainternal_error()


def restore_purchases() -> None:
    """(internal)"""
    if HAVE_INTERNAL:
        _bainternal.restore_purchases()
        return

    # This shouldn't break anything but should try to avoid calling it.
    _no_bainternal_warning()


def purchase(item: str) -> None:
    """(internal)"""

    if HAVE_INTERNAL:
        _bainternal.purchase(item)
        return

    # This won't break messily but won't function as intended.
    _no_bainternal_warning()


def get_purchases_state() -> int:
    """(internal)"""

    if HAVE_INTERNAL:
        return _bainternal.get_purchases_state()

    # This won't function correctly without internal.
    raise _no_bainternal_error()


def get_purchased(item: str) -> bool:
    """(internal)"""

    if HAVE_INTERNAL:
        return _bainternal.get_purchased(item)

    # Without internal we can just assume no purchases.
    return False


def get_price(item: str) -> str | None:
    """(internal)"""

    if HAVE_INTERNAL:
        return _bainternal.get_price(item)

    # Without internal we can just assume no prices.
    return None


def in_game_purchase(item: str, price: int) -> None:
    """(internal)"""

    if HAVE_INTERNAL:
        _bainternal.in_game_purchase(item=item, price=price)
        return

    # Without internal this doesn't function as expected.
    raise _no_bainternal_error()


# noinspection PyUnresolvedReferences
def add_transaction(
    transaction: dict, callback: Callable | None = None
) -> None:
    """(internal)"""
    if HAVE_INTERNAL:
        _bainternal.add_transaction(transaction=transaction, callback=callback)
        return

    # This won't function correctly without internal (callback never called).
    raise _no_bainternal_error()


def reset_achievements() -> None:
    """(internal)"""
    if HAVE_INTERNAL:
        _bainternal.reset_achievements()
        return

    # Technically doesnt break but won't do anything.
    _no_bainternal_warning()


def get_public_login_id() -> str | None:
    """(internal)"""

    if HAVE_INTERNAL:
        return _bainternal.get_public_login_id()

    # Harmless to return nothing in this case.
    return None


def have_outstanding_transactions() -> bool:
    """(internal)"""

    if HAVE_INTERNAL:
        return _bainternal.have_outstanding_transactions()

    # Harmless to return False here.
    return False


def run_transactions() -> None:
    """(internal)"""
    if HAVE_INTERNAL:
        _bainternal.run_transactions()

    # Harmless no-op in this case.


def get_v1_account_misc_read_val(name: str, default_value: Any) -> Any:
    """(internal)"""
    if HAVE_INTERNAL:
        return _bainternal.get_v1_account_misc_read_val(
            name=name, default_value=default_value
        )
    raise _no_bainternal_error()


def get_v1_account_misc_read_val_2(name: str, default_value: Any) -> Any:
    """(internal)"""
    if HAVE_INTERNAL:
        return _bainternal.get_v1_account_misc_read_val_2(
            name=name, default_value=default_value
        )
    raise _no_bainternal_error()


def get_v1_account_misc_val(name: str, default_value: Any) -> Any:
    """(internal)"""
    if HAVE_INTERNAL:
        return _bainternal.get_v1_account_misc_val(
            name=name, default_value=default_value
        )
    raise _no_bainternal_error()


def get_v1_account_ticket_count() -> int:
    """(internal)

    Returns the number of tickets for the current account.
    """

    if HAVE_INTERNAL:
        return _bainternal.get_v1_account_ticket_count()
    return 0


def get_v1_account_state_num() -> int:
    """(internal)"""
    if HAVE_INTERNAL:
        return _bainternal.get_v1_account_state_num()
    return 0


def get_v1_account_state() -> str:
    """(internal)"""
    if HAVE_INTERNAL:
        return _bainternal.get_v1_account_state()

    # Without internal present just consider ourself always signed out.
    return 'signed_out'


def get_v1_account_display_string(full: bool = True) -> str:
    """(internal)"""
    if HAVE_INTERNAL:
        return _bainternal.get_v1_account_display_string(full=full)
    raise _no_bainternal_error()


def get_v1_account_type() -> str:
    """(internal)"""
    if HAVE_INTERNAL:
        return _bainternal.get_v1_account_type()
    raise _no_bainternal_error()


def get_v1_account_name() -> str:
    """(internal)"""
    if HAVE_INTERNAL:
        return _bainternal.get_v1_account_name()
    raise _no_bainternal_error()


def sign_out_v1(v2_embedded: bool = False) -> None:
    """(internal)

    Category: General Utility Functions
    """
    if HAVE_INTERNAL:
        _bainternal.sign_out_v1(v2_embedded=v2_embedded)
        return
    raise _no_bainternal_error()


def sign_in_v1(account_type: str) -> None:
    """(internal)

    Category: General Utility Functions
    """
    if HAVE_INTERNAL:
        _bainternal.sign_in_v1(account_type=account_type)
        return
    raise _no_bainternal_error()


def mark_config_dirty() -> None:
    """(internal)

    Category: General Utility Functions
    """
    if HAVE_INTERNAL:
        _bainternal.mark_config_dirty()
        return

    # Note to self - need to fix config writing to not rely on
    # internal lib.
    _no_bainternal_warning()
