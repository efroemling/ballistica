# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Account related functionality."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Any, Optional, Dict, List


def handle_account_gained_tickets(count: int) -> None:
    """Called when the current account has been awarded tickets.

    (internal)
    """
    from ba._lang import Lstr
    _ba.screenmessage(Lstr(resource='getTicketsWindow.receivedTicketsText',
                           subs=[('${COUNT}', str(count))]),
                      color=(0, 1, 0))
    _ba.playsound(_ba.getsound('cashRegister'))


def cache_league_rank_data(data: Any) -> None:
    """(internal)"""
    _ba.app.league_rank_cache['info'] = copy.deepcopy(data)


def get_cached_league_rank_data() -> Any:
    """(internal)"""
    return _ba.app.league_rank_cache.get('info', None)


def get_league_rank_points(data: Optional[Dict[str, Any]],
                           subset: str = None) -> int:
    """(internal)"""
    if data is None:
        return 0

    # If the data contains an achievement total, use that. otherwise calc
    # locally.
    if data['at'] is not None:
        total_ach_value = data['at']
    else:
        total_ach_value = 0
        for ach in _ba.app.achievements:
            if ach.complete:
                total_ach_value += ach.power_ranking_value

    trophies_total: int = (data['t0a'] * data['t0am'] +
                           data['t0b'] * data['t0bm'] +
                           data['t1'] * data['t1m'] +
                           data['t2'] * data['t2m'] +
                           data['t3'] * data['t3m'] + data['t4'] * data['t4m'])
    if subset == 'trophyCount':
        val: int = (data['t0a'] + data['t0b'] + data['t1'] + data['t2'] +
                    data['t3'] + data['t4'])
        assert isinstance(val, int)
        return val
    if subset == 'trophies':
        assert isinstance(trophies_total, int)
        return trophies_total
    if subset is not None:
        raise ValueError('invalid subset value: ' + str(subset))

    if data['p']:
        pro_mult = 1.0 + float(
            _ba.get_account_misc_read_val('proPowerRankingBoost', 0.0)) * 0.01
    else:
        pro_mult = 1.0

    # For final value, apply our pro mult and activeness-mult.
    return int((total_ach_value + trophies_total) *
               (data['act'] if data['act'] is not None else 1.0) * pro_mult)


def cache_tournament_info(info: Any) -> None:
    """(internal)"""
    from ba._enums import TimeType, TimeFormat
    for entry in info:
        cache_entry = _ba.app.tournament_info[entry['tournamentID']] = (
            copy.deepcopy(entry))

        # Also store the time we received this, so we can adjust
        # time-remaining values/etc.
        cache_entry['timeReceived'] = _ba.time(TimeType.REAL,
                                               TimeFormat.MILLISECONDS)
        cache_entry['valid'] = True


def get_purchased_icons() -> List[str]:
    """(internal)"""
    # pylint: disable=cyclic-import
    from ba import _store
    if _ba.get_account_state() != 'signed_in':
        return []
    icons = []
    store_items = _store.get_store_items()
    for item_name, item in list(store_items.items()):
        if item_name.startswith('icons.') and _ba.get_purchased(item_name):
            icons.append(item['icon'])
    return icons


def ensure_have_account_player_profile() -> None:
    """
    Ensure the standard account-named player profile exists;
    creating if needed.
    """
    # This only applies when we're signed in.
    if _ba.get_account_state() != 'signed_in':
        return

    # If the short version of our account name currently cant be
    # displayed by the game, cancel.
    if not _ba.have_chars(_ba.get_account_display_string(full=False)):
        return

    config = _ba.app.config
    if ('Player Profiles' not in config
            or '__account__' not in config['Player Profiles']):

        # Create a spaz with a nice default purply color.
        _ba.add_transaction({
            'type': 'ADD_PLAYER_PROFILE',
            'name': '__account__',
            'profile': {
                'character': 'Spaz',
                'color': [0.5, 0.25, 1.0],
                'highlight': [0.5, 0.25, 1.0]
            }
        })
        _ba.run_transactions()


def have_pro() -> bool:
    """Return whether pro is currently unlocked."""

    # Check our tickets-based pro upgrade and our two real-IAP based upgrades.
    # Also unlock this stuff in ballistica-core builds.
    return bool(
        _ba.get_purchased('upgrades.pro') or _ba.get_purchased('static.pro')
        or _ba.get_purchased('static.pro_sale')
        or 'ballistica' + 'core' == _ba.appname())


def have_pro_options() -> bool:
    """Return whether pro-options are present.

    This is True for owners of Pro or old installs
    before Pro was a requirement for these.
    """

    # We expose pro options if the server tells us to
    # (which is generally just when we own pro),
    # or also if we've been grandfathered in or are using ballistica-core
    # builds.
    return have_pro() or bool(
        _ba.get_account_misc_read_val_2('proOptionsUnlocked', False)
        or _ba.app.config.get('lc14292', 0) > 1)


def show_post_purchase_message() -> None:
    """(internal)"""
    from ba._lang import Lstr
    from ba._enums import TimeType
    app = _ba.app
    cur_time = _ba.time(TimeType.REAL)
    if (app.last_post_purchase_message_time is None
            or cur_time - app.last_post_purchase_message_time > 3.0):
        app.last_post_purchase_message_time = cur_time
        with _ba.Context('ui'):
            _ba.screenmessage(Lstr(resource='updatingAccountText',
                                   fallback_resource='purchasingText'),
                              color=(0, 1, 0))
            _ba.playsound(_ba.getsound('click01'))


def on_account_state_changed() -> None:
    """(internal)"""
    import time
    from ba import _lang
    app = _ba.app

    # Run any pending promo codes we had queued up while not signed in.
    if _ba.get_account_state() == 'signed_in' and app.pending_promo_codes:
        for code in app.pending_promo_codes:
            _ba.screenmessage(_lang.Lstr(resource='submittingPromoCodeText'),
                              color=(0, 1, 0))
            _ba.add_transaction({
                'type': 'PROMO_CODE',
                'expire_time': time.time() + 5,
                'code': code
            })
        _ba.run_transactions()
        app.pending_promo_codes = []
