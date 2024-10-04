# Released under the MIT License. See LICENSE for details.
#
"""Store related functionality for classic mode."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from efro.util import utc_now

import babase
import bascenev1

if TYPE_CHECKING:
    from typing import Any


class StoreSubsystem:
    """Wrangles classic store."""

    def get_store_item(self, item: str) -> dict[str, Any]:
        """(internal)"""
        return self.get_store_items()[item]

    def get_store_item_name_translated(self, item_name: str) -> babase.Lstr:
        """Return a babase.Lstr for a store item name."""
        # pylint: disable=cyclic-import
        item_info = self.get_store_item(item_name)
        if item_name.startswith('characters.'):
            return babase.Lstr(
                translate=('characterNames', item_info['character'])
            )
        if item_name in ['merch']:
            return babase.Lstr(resource='merchText')
        if item_name in ['upgrades.pro', 'pro']:
            return babase.Lstr(
                resource='store.bombSquadProNameText',
                subs=[('${APP_NAME}', babase.Lstr(resource='titleText'))],
            )
        if item_name.startswith('maps.'):
            map_type: type[bascenev1.Map] = item_info['map_type']
            return bascenev1.get_map_display_string(map_type.name)
        if item_name.startswith('games.'):
            gametype: type[bascenev1.GameActivity] = item_info['gametype']
            return gametype.get_display_string()
        if item_name.startswith('icons.'):
            return babase.Lstr(resource='editProfileWindow.iconText')
        raise ValueError('unrecognized item: ' + item_name)

    def get_store_item_display_size(
        self, item_name: str
    ) -> tuple[float, float]:
        """(internal)"""
        if item_name.startswith('characters.'):
            return 340 * 0.6, 430 * 0.6
        if item_name in ['pro', 'upgrades.pro', 'merch']:
            assert babase.app.classic is not None
            return 650 * 0.9, 500 * (
                0.72
                if (
                    babase.app.config.get('Merch Link')
                    and babase.app.ui_v1.uiscale is babase.UIScale.SMALL
                )
                else 0.85
            )
        if item_name.startswith('maps.'):
            return 510 * 0.6, 450 * 0.6
        if item_name.startswith('icons.'):
            return 265 * 0.6, 250 * 0.6
        return 450 * 0.6, 450 * 0.6

    def get_store_items(self) -> dict[str, dict]:
        """Returns info about purchasable items.

        (internal)
        """
        # pylint: disable=cyclic-import
        from bascenev1lib import maps

        assert babase.app.classic is not None

        if babase.app.classic.store_items is None:
            from bascenev1lib.game import ninjafight
            from bascenev1lib.game import meteorshower
            from bascenev1lib.game import targetpractice
            from bascenev1lib.game import easteregghunt

            # IMPORTANT - need to keep this synced with the master server.
            # (doing so manually for now)
            babase.app.classic.store_items = {
                'characters.kronk': {'character': 'Kronk'},
                'characters.zoe': {'character': 'Zoe'},
                'characters.jackmorgan': {'character': 'Jack Morgan'},
                'characters.mel': {'character': 'Mel'},
                'characters.snakeshadow': {'character': 'Snake Shadow'},
                'characters.bones': {'character': 'Bones'},
                'characters.bernard': {
                    'character': 'Bernard',
                    'highlight': (0.6, 0.5, 0.8),
                },
                'characters.pixie': {'character': 'Pixel'},
                'characters.wizard': {'character': 'Grumbledorf'},
                'characters.frosty': {'character': 'Frosty'},
                'characters.pascal': {'character': 'Pascal'},
                'characters.cyborg': {'character': 'B-9000'},
                'characters.agent': {'character': 'Agent Johnson'},
                'characters.taobaomascot': {'character': 'Taobao Mascot'},
                'characters.santa': {'character': 'Santa Claus'},
                'characters.bunny': {'character': 'Easter Bunny'},
                'merch': {},
                'pro': {},
                'maps.lake_frigid': {'map_type': maps.LakeFrigid},
                'games.ninja_fight': {
                    'gametype': ninjafight.NinjaFightGame,
                    'previewTex': 'courtyardPreview',
                },
                'games.meteor_shower': {
                    'gametype': meteorshower.MeteorShowerGame,
                    'previewTex': 'rampagePreview',
                },
                'games.target_practice': {
                    'gametype': targetpractice.TargetPracticeGame,
                    'previewTex': 'doomShroomPreview',
                },
                'games.easter_egg_hunt': {
                    'gametype': easteregghunt.EasterEggHuntGame,
                    'previewTex': 'towerDPreview',
                },
                'icons.flag_us': {
                    'icon': babase.charstr(
                        babase.SpecialChar.FLAG_UNITED_STATES
                    )
                },
                'icons.flag_mexico': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_MEXICO)
                },
                'icons.flag_germany': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_GERMANY)
                },
                'icons.flag_brazil': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_BRAZIL)
                },
                'icons.flag_russia': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_RUSSIA)
                },
                'icons.flag_china': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_CHINA)
                },
                'icons.flag_uk': {
                    'icon': babase.charstr(
                        babase.SpecialChar.FLAG_UNITED_KINGDOM
                    )
                },
                'icons.flag_canada': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_CANADA)
                },
                'icons.flag_india': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_INDIA)
                },
                'icons.flag_japan': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_JAPAN)
                },
                'icons.flag_france': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_FRANCE)
                },
                'icons.flag_indonesia': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_INDONESIA)
                },
                'icons.flag_italy': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_ITALY)
                },
                'icons.flag_south_korea': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_SOUTH_KOREA)
                },
                'icons.flag_netherlands': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_NETHERLANDS)
                },
                'icons.flag_uae': {
                    'icon': babase.charstr(
                        babase.SpecialChar.FLAG_UNITED_ARAB_EMIRATES
                    )
                },
                'icons.flag_qatar': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_QATAR)
                },
                'icons.flag_egypt': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_EGYPT)
                },
                'icons.flag_kuwait': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_KUWAIT)
                },
                'icons.flag_algeria': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_ALGERIA)
                },
                'icons.flag_saudi_arabia': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_SAUDI_ARABIA)
                },
                'icons.flag_malaysia': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_MALAYSIA)
                },
                'icons.flag_czech_republic': {
                    'icon': babase.charstr(
                        babase.SpecialChar.FLAG_CZECH_REPUBLIC
                    )
                },
                'icons.flag_australia': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_AUSTRALIA)
                },
                'icons.flag_singapore': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_SINGAPORE)
                },
                'icons.flag_iran': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_IRAN)
                },
                'icons.flag_poland': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_POLAND)
                },
                'icons.flag_argentina': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_ARGENTINA)
                },
                'icons.flag_philippines': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_PHILIPPINES)
                },
                'icons.flag_chile': {
                    'icon': babase.charstr(babase.SpecialChar.FLAG_CHILE)
                },
                'icons.fedora': {
                    'icon': babase.charstr(babase.SpecialChar.FEDORA)
                },
                'icons.hal': {'icon': babase.charstr(babase.SpecialChar.HAL)},
                'icons.crown': {
                    'icon': babase.charstr(babase.SpecialChar.CROWN)
                },
                'icons.yinyang': {
                    'icon': babase.charstr(babase.SpecialChar.YIN_YANG)
                },
                'icons.eyeball': {
                    'icon': babase.charstr(babase.SpecialChar.EYE_BALL)
                },
                'icons.skull': {
                    'icon': babase.charstr(babase.SpecialChar.SKULL)
                },
                'icons.heart': {
                    'icon': babase.charstr(babase.SpecialChar.HEART)
                },
                'icons.dragon': {
                    'icon': babase.charstr(babase.SpecialChar.DRAGON)
                },
                'icons.helmet': {
                    'icon': babase.charstr(babase.SpecialChar.HELMET)
                },
                'icons.mushroom': {
                    'icon': babase.charstr(babase.SpecialChar.MUSHROOM)
                },
                'icons.ninja_star': {
                    'icon': babase.charstr(babase.SpecialChar.NINJA_STAR)
                },
                'icons.viking_helmet': {
                    'icon': babase.charstr(babase.SpecialChar.VIKING_HELMET)
                },
                'icons.moon': {'icon': babase.charstr(babase.SpecialChar.MOON)},
                'icons.spider': {
                    'icon': babase.charstr(babase.SpecialChar.SPIDER)
                },
                'icons.fireball': {
                    'icon': babase.charstr(babase.SpecialChar.FIREBALL)
                },
                'icons.mikirog': {
                    'icon': babase.charstr(babase.SpecialChar.MIKIROG)
                },
                'icons.explodinary': {
                    'icon': babase.charstr(babase.SpecialChar.EXPLODINARY_LOGO)
                },
            }
        return babase.app.classic.store_items

    def get_store_layout(self) -> dict[str, list[dict[str, Any]]]:
        """Return what's available in the store at a given time.

        Categorized by tab and by section.
        """
        plus = babase.app.plus
        classic = babase.app.classic

        assert classic is not None
        assert plus is not None

        if classic.store_layout is None:
            classic.store_layout = {
                'characters': [{'items': []}],
                'extras': [{'items': ['pro']}],
                'maps': [{'items': ['maps.lake_frigid']}],
                'minigames': [],
                'icons': [
                    {
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
                    }
                ],
            }
        store_layout = classic.store_layout
        store_layout['characters'] = [
            {
                'items': [
                    'characters.kronk',
                    'characters.zoe',
                    'characters.jackmorgan',
                    'characters.mel',
                    'characters.snakeshadow',
                    'characters.bones',
                    'characters.bernard',
                    'characters.agent',
                    'characters.frosty',
                    'characters.pascal',
                    'characters.pixie',
                ]
            }
        ]
        store_layout['minigames'] = [
            {
                'items': [
                    'games.ninja_fight',
                    'games.meteor_shower',
                    'games.target_practice',
                ]
            }
        ]
        if plus.get_v1_account_misc_read_val('xmas', False):
            store_layout['characters'][0]['items'].append('characters.santa')
        store_layout['characters'][0]['items'].append('characters.wizard')
        store_layout['characters'][0]['items'].append('characters.cyborg')
        if plus.get_v1_account_misc_read_val('easter', False):
            store_layout['characters'].append(
                {
                    'title': 'store.holidaySpecialText',
                    'items': ['characters.bunny'],
                }
            )
            store_layout['minigames'].append(
                {
                    'title': 'store.holidaySpecialText',
                    'items': ['games.easter_egg_hunt'],
                }
            )

        # This will cause merch to show only if the master-server has
        # given us a link (which means merch is available in our region).
        store_layout['extras'] = [{'items': ['pro']}]
        if babase.app.config.get('Merch Link'):
            store_layout['extras'][0]['items'].append('merch')
        return store_layout

    def get_clean_price(self, price_string: str) -> str:
        """(internal)"""

        # I'm not brave enough to try and do any numerical
        # manipulation on formatted price strings, but lets do a
        # few swap-outs to tidy things up a bit.
        psubs = {
            '$2.99': '$3.00',
            '$4.99': '$5.00',
            '$9.99': '$10.00',
            '$19.99': '$20.00',
            '$49.99': '$50.00',
        }
        return psubs.get(price_string, price_string)

    def get_available_purchase_count(self, tab: str | None = None) -> int:
        """(internal)"""
        plus = babase.app.plus
        if plus is None:
            return 0
        try:
            if plus.get_v1_account_state() != 'signed_in':
                return 0
            count = 0
            our_tickets = plus.get_v1_account_ticket_count()
            store_data = self.get_store_layout()
            if tab is not None:
                tabs = [(tab, store_data[tab])]
            else:
                tabs = list(store_data.items())
            for tab_name, tabval in tabs:
                if tab_name == 'icons':
                    continue  # too many of these; don't show..
                count = self._calc_count_for_tab(tabval, our_tickets, count)
            return count
        except Exception:
            logging.exception('Error calcing available purchases.')
            return 0

    def _calc_count_for_tab(
        self, tabval: list[dict[str, Any]], our_tickets: int, count: int
    ) -> int:
        plus = babase.app.plus
        assert plus
        for section in tabval:
            for item in section['items']:
                ticket_cost = plus.get_v1_account_misc_read_val(
                    'price.' + item, None
                )
                if ticket_cost is not None:
                    if (
                        our_tickets >= ticket_cost
                        and not plus.get_v1_account_product_purchased(item)
                    ):
                        count += 1
        return count

    def get_available_sale_time(self, tab: str) -> int | None:
        """(internal)"""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-nested-blocks
        plus = babase.app.plus
        assert plus is not None

        try:
            import datetime

            app = babase.app
            assert app.classic is not None
            sale_times: list[int | None] = []

            # Calc time for our pro sale (old special case).
            if tab == 'extras':
                config = app.config
                if app.classic.accounts.have_pro():
                    return None

                # If we haven't calced/loaded start times yet.
                if app.classic.pro_sale_start_time is None:
                    # If we've got a time-remaining in our config, start there.
                    if 'PSTR' in config:
                        app.classic.pro_sale_start_time = int(
                            babase.apptime() * 1000
                        )
                        app.classic.pro_sale_start_val = config['PSTR']
                    else:
                        # We start the timer once we get the duration from
                        # the server.
                        start_duration = plus.get_v1_account_misc_read_val(
                            'proSaleDurationMinutes', None
                        )
                        if start_duration is not None:
                            app.classic.pro_sale_start_time = int(
                                babase.apptime() * 1000
                            )
                            app.classic.pro_sale_start_val = (
                                60000 * start_duration
                            )

                        # If we haven't heard from the server yet, no sale..
                        else:
                            return None

                assert app.classic.pro_sale_start_val is not None
                val: int | None = max(
                    0,
                    app.classic.pro_sale_start_val
                    - (
                        int(babase.apptime() * 1000.0)
                        - app.classic.pro_sale_start_time
                    ),
                )

                # Keep the value in the config up to date. I suppose we should
                # write the config occasionally but it should happen often
                # enough for other reasons.
                config['PSTR'] = val
                if val == 0:
                    val = None
                sale_times.append(val)

            # Now look for sales in this tab.
            sales_raw = plus.get_v1_account_misc_read_val('sales', {})
            store_layout = self.get_store_layout()
            for section in store_layout[tab]:
                for item in section['items']:
                    if item in sales_raw:
                        if not plus.get_v1_account_product_purchased(item):
                            to_end = (
                                datetime.datetime.fromtimestamp(
                                    sales_raw[item]['e'], datetime.UTC
                                )
                                - utc_now()
                            ).total_seconds()
                            if to_end > 0:
                                sale_times.append(int(to_end * 1000))

            # Return the smallest time I guess?
            sale_times_int = [t for t in sale_times if isinstance(t, int)]
            return min(sale_times_int) if sale_times_int else None

        except Exception:
            logging.exception('Error calcing sale time.')
            return None

    def get_unowned_maps(self) -> list[str]:
        """Return the list of local maps not owned by the current account.

        Category: **Asset Functions**
        """
        plus = babase.app.plus
        unowned_maps: set[str] = set()
        if babase.app.env.gui:
            for map_section in self.get_store_layout()['maps']:
                for mapitem in map_section['items']:
                    if (
                        plus is None
                        or not plus.get_v1_account_product_purchased(mapitem)
                    ):
                        m_info = self.get_store_item(mapitem)
                        unowned_maps.add(m_info['map_type'].name)
        return sorted(unowned_maps)

    def get_unowned_game_types(self) -> set[type[bascenev1.GameActivity]]:
        """Return present game types not owned by the current account."""
        try:
            plus = babase.app.plus
            unowned_games: set[type[bascenev1.GameActivity]] = set()
            if babase.app.env.gui:
                for section in self.get_store_layout()['minigames']:
                    for mname in section['items']:
                        if (
                            plus is None
                            or not plus.get_v1_account_product_purchased(mname)
                        ):
                            m_info = self.get_store_item(mname)
                            unowned_games.add(m_info['gametype'])
            return unowned_games
        except Exception:
            logging.exception('Error calcing un-owned games.')
            return set()
