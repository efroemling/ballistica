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
"""Store related functionality for classic mode."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Type, List, Dict, Tuple, Optional, Any
    import ba


def get_store_item(item: str) -> Dict[str, Any]:
    """(internal)"""
    return get_store_items()[item]


def get_store_item_name_translated(item_name: str) -> ba.Lstr:
    """Return a ba.Lstr for a store item name."""
    # pylint: disable=cyclic-import
    from ba import _lang
    from ba import _map
    item_info = get_store_item(item_name)
    if item_name.startswith('characters.'):
        return _lang.Lstr(translate=('characterNames', item_info['character']))
    if item_name in ['upgrades.pro', 'pro']:
        return _lang.Lstr(resource='store.bombSquadProNameText',
                          subs=[('${APP_NAME}',
                                 _lang.Lstr(resource='titleText'))])
    if item_name.startswith('maps.'):
        map_type: Type[ba.Map] = item_info['map_type']
        return _map.get_map_display_string(map_type.name)
    if item_name.startswith('games.'):
        gametype: Type[ba.GameActivity] = item_info['gametype']
        return gametype.get_display_string()
    if item_name.startswith('icons.'):
        return _lang.Lstr(resource='editProfileWindow.iconText')
    raise ValueError('unrecognized item: ' + item_name)


def get_store_item_display_size(item_name: str) -> Tuple[float, float]:
    """(internal)"""
    if item_name.startswith('characters.'):
        return 340 * 0.6, 430 * 0.6
    if item_name in ['pro', 'upgrades.pro']:
        return 650 * 0.9, 500 * 0.85
    if item_name.startswith('maps.'):
        return 510 * 0.6, 450 * 0.6
    if item_name.startswith('icons.'):
        return 265 * 0.6, 250 * 0.6
    return 450 * 0.6, 450 * 0.6


def get_store_items() -> Dict[str, Dict]:
    """Returns info about purchasable items.

    (internal)
    """
    # pylint: disable=cyclic-import
    from ba._enums import SpecialChar
    from bastd import maps
    if _ba.app.store_items is None:
        from bastd.game import ninjafight
        from bastd.game import meteorshower
        from bastd.game import targetpractice
        from bastd.game import easteregghunt

        # IMPORTANT - need to keep this synced with the master server.
        # (doing so manually for now)
        _ba.app.store_items = {
            'characters.kronk': {
                'character': 'Kronk'
            },
            'characters.zoe': {
                'character': 'Zoe'
            },
            'characters.jackmorgan': {
                'character': 'Jack Morgan'
            },
            'characters.mel': {
                'character': 'Mel'
            },
            'characters.snakeshadow': {
                'character': 'Snake Shadow'
            },
            'characters.bones': {
                'character': 'Bones'
            },
            'characters.bernard': {
                'character': 'Bernard',
                'highlight': (0.6, 0.5, 0.8)
            },
            'characters.pixie': {
                'character': 'Pixel'
            },
            'characters.wizard': {
                'character': 'Grumbledorf'
            },
            'characters.frosty': {
                'character': 'Frosty'
            },
            'characters.pascal': {
                'character': 'Pascal'
            },
            'characters.cyborg': {
                'character': 'B-9000'
            },
            'characters.agent': {
                'character': 'Agent Johnson'
            },
            'characters.taobaomascot': {
                'character': 'Taobao Mascot'
            },
            'characters.santa': {
                'character': 'Santa Claus'
            },
            'characters.bunny': {
                'character': 'Easter Bunny'
            },
            'pro': {},
            'maps.lake_frigid': {
                'map_type': maps.LakeFrigid
            },
            'games.ninja_fight': {
                'gametype': ninjafight.NinjaFightGame,
                'previewTex': 'courtyardPreview'
            },
            'games.meteor_shower': {
                'gametype': meteorshower.MeteorShowerGame,
                'previewTex': 'rampagePreview'
            },
            'games.target_practice': {
                'gametype': targetpractice.TargetPracticeGame,
                'previewTex': 'doomShroomPreview'
            },
            'games.easter_egg_hunt': {
                'gametype': easteregghunt.EasterEggHuntGame,
                'previewTex': 'towerDPreview'
            },
            'icons.flag_us': {
                'icon': _ba.charstr(SpecialChar.FLAG_UNITED_STATES)
            },
            'icons.flag_mexico': {
                'icon': _ba.charstr(SpecialChar.FLAG_MEXICO)
            },
            'icons.flag_germany': {
                'icon': _ba.charstr(SpecialChar.FLAG_GERMANY)
            },
            'icons.flag_brazil': {
                'icon': _ba.charstr(SpecialChar.FLAG_BRAZIL)
            },
            'icons.flag_russia': {
                'icon': _ba.charstr(SpecialChar.FLAG_RUSSIA)
            },
            'icons.flag_china': {
                'icon': _ba.charstr(SpecialChar.FLAG_CHINA)
            },
            'icons.flag_uk': {
                'icon': _ba.charstr(SpecialChar.FLAG_UNITED_KINGDOM)
            },
            'icons.flag_canada': {
                'icon': _ba.charstr(SpecialChar.FLAG_CANADA)
            },
            'icons.flag_india': {
                'icon': _ba.charstr(SpecialChar.FLAG_INDIA)
            },
            'icons.flag_japan': {
                'icon': _ba.charstr(SpecialChar.FLAG_JAPAN)
            },
            'icons.flag_france': {
                'icon': _ba.charstr(SpecialChar.FLAG_FRANCE)
            },
            'icons.flag_indonesia': {
                'icon': _ba.charstr(SpecialChar.FLAG_INDONESIA)
            },
            'icons.flag_italy': {
                'icon': _ba.charstr(SpecialChar.FLAG_ITALY)
            },
            'icons.flag_south_korea': {
                'icon': _ba.charstr(SpecialChar.FLAG_SOUTH_KOREA)
            },
            'icons.flag_netherlands': {
                'icon': _ba.charstr(SpecialChar.FLAG_NETHERLANDS)
            },
            'icons.flag_uae': {
                'icon': _ba.charstr(SpecialChar.FLAG_UNITED_ARAB_EMIRATES)
            },
            'icons.flag_qatar': {
                'icon': _ba.charstr(SpecialChar.FLAG_QATAR)
            },
            'icons.flag_egypt': {
                'icon': _ba.charstr(SpecialChar.FLAG_EGYPT)
            },
            'icons.flag_kuwait': {
                'icon': _ba.charstr(SpecialChar.FLAG_KUWAIT)
            },
            'icons.flag_algeria': {
                'icon': _ba.charstr(SpecialChar.FLAG_ALGERIA)
            },
            'icons.flag_saudi_arabia': {
                'icon': _ba.charstr(SpecialChar.FLAG_SAUDI_ARABIA)
            },
            'icons.flag_malaysia': {
                'icon': _ba.charstr(SpecialChar.FLAG_MALAYSIA)
            },
            'icons.flag_czech_republic': {
                'icon': _ba.charstr(SpecialChar.FLAG_CZECH_REPUBLIC)
            },
            'icons.flag_australia': {
                'icon': _ba.charstr(SpecialChar.FLAG_AUSTRALIA)
            },
            'icons.flag_singapore': {
                'icon': _ba.charstr(SpecialChar.FLAG_SINGAPORE)
            },
            'icons.flag_iran': {
                'icon': _ba.charstr(SpecialChar.FLAG_IRAN)
            },
            'icons.flag_poland': {
                'icon': _ba.charstr(SpecialChar.FLAG_POLAND)
            },
            'icons.flag_argentina': {
                'icon': _ba.charstr(SpecialChar.FLAG_ARGENTINA)
            },
            'icons.flag_philippines': {
                'icon': _ba.charstr(SpecialChar.FLAG_PHILIPPINES)
            },
            'icons.flag_chile': {
                'icon': _ba.charstr(SpecialChar.FLAG_CHILE)
            },
            'icons.fedora': {
                'icon': _ba.charstr(SpecialChar.FEDORA)
            },
            'icons.hal': {
                'icon': _ba.charstr(SpecialChar.HAL)
            },
            'icons.crown': {
                'icon': _ba.charstr(SpecialChar.CROWN)
            },
            'icons.yinyang': {
                'icon': _ba.charstr(SpecialChar.YIN_YANG)
            },
            'icons.eyeball': {
                'icon': _ba.charstr(SpecialChar.EYE_BALL)
            },
            'icons.skull': {
                'icon': _ba.charstr(SpecialChar.SKULL)
            },
            'icons.heart': {
                'icon': _ba.charstr(SpecialChar.HEART)
            },
            'icons.dragon': {
                'icon': _ba.charstr(SpecialChar.DRAGON)
            },
            'icons.helmet': {
                'icon': _ba.charstr(SpecialChar.HELMET)
            },
            'icons.mushroom': {
                'icon': _ba.charstr(SpecialChar.MUSHROOM)
            },
            'icons.ninja_star': {
                'icon': _ba.charstr(SpecialChar.NINJA_STAR)
            },
            'icons.viking_helmet': {
                'icon': _ba.charstr(SpecialChar.VIKING_HELMET)
            },
            'icons.moon': {
                'icon': _ba.charstr(SpecialChar.MOON)
            },
            'icons.spider': {
                'icon': _ba.charstr(SpecialChar.SPIDER)
            },
            'icons.fireball': {
                'icon': _ba.charstr(SpecialChar.FIREBALL)
            },
            'icons.mikirog': {
                'icon': _ba.charstr(SpecialChar.MIKIROG)
            },
        }
    store_items = _ba.app.store_items
    assert store_items is not None
    return store_items


def get_store_layout() -> Dict[str, List[Dict[str, Any]]]:
    """Return what's available in the store at a given time.

        Categorized by tab and by section."""
    if _ba.app.store_layout is None:
        _ba.app.store_layout = {
            'characters': [{
                'items': []
            }],
            'extras': [{
                'items': ['pro']
            }],
            'maps': [{
                'items': ['maps.lake_frigid']
            }],
            'minigames': [],
            'icons': [{
                'items': [
                    'icons.mushroom',
                    'icons.heart',
                    'icons.eyeball',
                    'icons.yinyang',
                    'icons.hal',
                    'icons.flag_us',
                    'icons.flag_mexico',
                    'icons.flag_germany',
                    'icons.flag_brazil',
                    'icons.flag_russia',
                    'icons.flag_china',
                    'icons.flag_uk',
                    'icons.flag_canada',
                    'icons.flag_india',
                    'icons.flag_japan',
                    'icons.flag_france',
                    'icons.flag_indonesia',
                    'icons.flag_italy',
                    'icons.flag_south_korea',
                    'icons.flag_netherlands',
                    'icons.flag_uae',
                    'icons.flag_qatar',
                    'icons.flag_egypt',
                    'icons.flag_kuwait',
                    'icons.flag_algeria',
                    'icons.flag_saudi_arabia',
                    'icons.flag_malaysia',
                    'icons.flag_czech_republic',
                    'icons.flag_australia',
                    'icons.flag_singapore',
                    'icons.flag_iran',
                    'icons.flag_poland',
                    'icons.flag_argentina',
                    'icons.flag_philippines',
                    'icons.flag_chile',
                    'icons.moon',
                    'icons.fedora',
                    'icons.spider',
                    'icons.ninja_star',
                    'icons.skull',
                    'icons.dragon',
                    'icons.viking_helmet',
                    'icons.fireball',
                    'icons.helmet',
                    'icons.crown',
                ]
            }]
        }
    store_layout = _ba.app.store_layout
    assert store_layout is not None
    store_layout['characters'] = [{
        'items': [
            'characters.kronk', 'characters.zoe', 'characters.jackmorgan',
            'characters.mel', 'characters.snakeshadow', 'characters.bones',
            'characters.bernard', 'characters.agent', 'characters.frosty',
            'characters.pascal', 'characters.pixie'
        ]
    }]
    store_layout['minigames'] = [{
        'items': [
            'games.ninja_fight', 'games.meteor_shower', 'games.target_practice'
        ]
    }]
    if _ba.get_account_misc_read_val('xmas', False):
        store_layout['characters'][0]['items'].append('characters.santa')
    store_layout['characters'][0]['items'].append('characters.wizard')
    store_layout['characters'][0]['items'].append('characters.cyborg')
    if _ba.get_account_misc_read_val('easter', False):
        store_layout['characters'].append({
            'title': 'store.holidaySpecialText',
            'items': ['characters.bunny']
        })
        store_layout['minigames'].append({
            'title': 'store.holidaySpecialText',
            'items': ['games.easter_egg_hunt']
        })
    return store_layout


def get_clean_price(price_string: str) -> str:
    """(internal)"""

    # I'm not brave enough to try and do any numerical
    # manipulation on formatted price strings, but lets do a
    # few swap-outs to tidy things up a bit.
    psubs = {
        '$2.99': '$3.00',
        '$4.99': '$5.00',
        '$9.99': '$10.00',
        '$19.99': '$20.00',
        '$49.99': '$50.00'
    }
    return psubs.get(price_string, price_string)


def get_available_purchase_count(tab: str = None) -> int:
    """(internal)"""
    try:
        if _ba.get_account_state() != 'signed_in':
            return 0
        count = 0
        our_tickets = _ba.get_account_ticket_count()
        store_data = get_store_layout()
        if tab is not None:
            tabs = [(tab, store_data[tab])]
        else:
            tabs = list(store_data.items())
        for tab_name, tabval in tabs:
            if tab_name == 'icons':
                continue  # too many of these; don't show..
            count = _calc_count_for_tab(tabval, our_tickets, count)
        return count
    except Exception:
        from ba import _error
        _error.print_exception('error calcing available purchases')
        return 0


def _calc_count_for_tab(tabval: List[Dict[str, Any]], our_tickets: int,
                        count: int) -> int:
    for section in tabval:
        for item in section['items']:
            ticket_cost = _ba.get_account_misc_read_val('price.' + item, None)
            if ticket_cost is not None:
                if (our_tickets >= ticket_cost
                        and not _ba.get_purchased(item)):
                    count += 1
    return count


def get_available_sale_time(tab: str) -> Optional[int]:
    """(internal)"""
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-nested-blocks
    # pylint: disable=too-many-locals
    try:
        import datetime
        from ba._account import have_pro
        from ba._enums import TimeType, TimeFormat
        app = _ba.app
        sale_times: List[Optional[int]] = []

        # Calc time for our pro sale (old special case).
        if tab == 'extras':
            config = app.config
            if have_pro():
                return None

            # If we haven't calced/loaded start times yet.
            if app.pro_sale_start_time is None:

                # If we've got a time-remaining in our config, start there.
                if 'PSTR' in config:
                    app.pro_sale_start_time = int(
                        _ba.time(TimeType.REAL, TimeFormat.MILLISECONDS))
                    app.pro_sale_start_val = config['PSTR']
                else:

                    # We start the timer once we get the duration from
                    # the server.
                    start_duration = _ba.get_account_misc_read_val(
                        'proSaleDurationMinutes', None)
                    if start_duration is not None:
                        app.pro_sale_start_time = int(
                            _ba.time(TimeType.REAL, TimeFormat.MILLISECONDS))
                        app.pro_sale_start_val = (60000 * start_duration)

                    # If we haven't heard from the server yet, no sale..
                    else:
                        return None

            assert app.pro_sale_start_val is not None
            val: Optional[int] = max(
                0, app.pro_sale_start_val -
                (_ba.time(TimeType.REAL, TimeFormat.MILLISECONDS) -
                 app.pro_sale_start_time))

            # Keep the value in the config up to date. I suppose we should
            # write the config occasionally but it should happen often enough
            # for other reasons.
            config['PSTR'] = val
            if val == 0:
                val = None
            sale_times.append(val)

        # Now look for sales in this tab.
        sales_raw = _ba.get_account_misc_read_val('sales', {})
        store_layout = get_store_layout()
        for section in store_layout[tab]:
            for item in section['items']:
                if item in sales_raw:
                    if not _ba.get_purchased(item):
                        to_end = ((datetime.datetime.utcfromtimestamp(
                            sales_raw[item]['e']) -
                                   datetime.datetime.utcnow()).total_seconds())
                        if to_end > 0:
                            sale_times.append(int(to_end * 1000))

        # Return the smallest time i guess?
        return min(sale_times) if sale_times else None

    except Exception:
        from ba import _error
        _error.print_exception('error calcing sale time')
        return None
