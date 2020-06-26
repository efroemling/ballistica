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
"""Exposed functionality not intended for full public use.

Classes and functions contained here, while technically 'public', may change
or disappear without warning, so should be avoided (or used sparingly and
defensively) in mods.
"""

# pylint: disable=unused-import

from ba._map import (get_unowned_maps, get_map_class, register_map,
                     preload_map_preview_media, get_map_display_string,
                     get_filtered_map_name)
from ba._appconfig import commit_app_config
from ba._input import (get_device_value, get_input_map_hash,
                       get_input_device_config)
from ba._general import getclass, json_prep, get_type_name
from ba._account import (on_account_state_changed,
                         handle_account_gained_tickets, have_pro_options,
                         have_pro, cache_tournament_info,
                         ensure_have_account_player_profile,
                         get_purchased_icons, get_cached_league_rank_data,
                         get_league_rank_points, cache_league_rank_data)
from ba._activitytypes import JoinActivity, ScoreScreenActivity
from ba._achievement import (get_achievement, set_completed_achievements,
                             display_achievement_banner,
                             get_achievements_for_coop_level)
from ba._apputils import (is_browser_likely_available, get_remote_app_name,
                          should_submit_debug_info, show_ad, show_ad_2)
from ba._benchmark import (run_gpu_benchmark, run_cpu_benchmark,
                           run_media_reload_benchmark, run_stress_test)
from ba._campaign import getcampaign
from ba._messages import PlayerProfilesChangedMessage
from ba._meta import get_game_types
from ba._multiteamsession import DEFAULT_TEAM_COLORS, DEFAULT_TEAM_NAMES
from ba._music import do_play_music
from ba._netutils import (master_server_get, master_server_post,
                          get_ip_address_type)
from ba._powerup import get_default_powerup_distribution
from ba._profile import (get_player_profile_colors, get_player_profile_icon,
                         get_player_colors)
from ba._tips import get_next_tip
from ba._playlist import (get_default_free_for_all_playlist,
                          get_default_teams_playlist, filter_playlist)
from ba._store import (get_available_sale_time, get_available_purchase_count,
                       get_store_item_name_translated,
                       get_store_item_display_size, get_store_layout,
                       get_store_item, get_clean_price)
from ba._tournament import get_tournament_prize_strings
from ba._gameutils import get_trophy_string
