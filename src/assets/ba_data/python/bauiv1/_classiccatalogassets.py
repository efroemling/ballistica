# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.baclassiccatalogassets.261009`` (bauiv1).

The catalog of classic content as menus and the store present it: map names and
previews, game names and descriptions, co-op level names, and the currency and
chest icons prizes and prices are drawn with. (Character names and icons live
with the characters, in BaClassicCharacterAssets.) Deliberately small and
slow-changing, because server-rendered pages (the store, profile editor)
reference it and every viewer resolves a referenced package in full
(asset-packages.md decision #40). Bundled with the game too, so menus never wait
on it.
"""

# ba_meta require api 9
# ba_meta require asset-package 500

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

from typing import TYPE_CHECKING

from bacommon.assetpackage import ApverNum

from bauiv1._assetref import AssetGroup

from babase import LangStrDir

# a-0.baclassiccatalogassets.261009
_ASSET_PACKAGE = ApverNum(500)

if TYPE_CHECKING:
    from bauiv1._assetref import MeshHandle, SoundHandle, TextureHandle
    from babase import LangStr

    class AudioGroup:
        """
        ::

            Sounds for presenting classic content: the chest window's open
            sequence (rev-up, cork pop, and the cheering voice lines that greet
            a chest popping open).

            See source for the full asset list.
        """

        aww: SoundHandle
        cork_pop2: SoundHandle
        gasp: SoundHandle
        nice: SoundHandle
        ooh: SoundHandle
        rev_up: SoundHandle
        woo: SoundHandle
        woo2: SoundHandle
        woo3: SoundHandle
        wow: SoundHandle
        yeah: SoundHandle

    class MeshesGroup:
        """
        ::

            The level-select button frame meshes map previews are drawn into.

            See source for the full asset list.
        """

        level_select_button_opaque: MeshHandle
        level_select_button_transparent: MeshHandle

    class StringsCoopGroup:
        """
        ::

            How menus present co-op levels and tournaments (player counts and
            the like).

            See source for the full asset list.
        """

        def player_count_abbreviated(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                Abbreviated player-count badge (number + "p" for players).

                English: "{count}p"
            """

    class StringsCoopLevelsGroup:
        """
        ::

            Names of the single-player and co-op campaign levels, including the
            parameterized difficulty variants.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Name of the Infinite Onslaught co-op level.
        #:
        #:     English: "Infinite Onslaught"
        infinite_onslaught: LangStr

        #: ::
        #:
        #:     Name of the Infinite Runaround co-op level.
        #:
        #:     English: "Infinite Runaround"
        infinite_runaround: LangStr

        #: ::
        #:
        #:     Name of the Onslaught Training co-op level.
        #:
        #:     English: "Onslaught Training"
        onslaught_training: LangStr

        #: ::
        #:
        #:     Name of the Pro Football co-op level.
        #:
        #:     English: "Pro Football"
        pro_football: LangStr

        #: ::
        #:
        #:     Name of the Pro Onslaught co-op level.
        #:
        #:     English: "Pro Onslaught"
        pro_onslaught: LangStr

        #: ::
        #:
        #:     Name of the Pro Runaround co-op level.
        #:
        #:     English: "Pro Runaround"
        pro_runaround: LangStr

        def pro_variant(self, *, game: str | LangStr) -> LangStr:
            """
            ::

                Name of the Pro difficulty variant of a level.

                English: "Pro {game}"
            """

        #: ::
        #:
        #:     Name of the Rookie Football co-op level.
        #:
        #:     English: "Rookie Football"
        rookie_football: LangStr

        #: ::
        #:
        #:     Name of the Rookie Onslaught co-op level.
        #:
        #:     English: "Rookie Onslaught"
        rookie_onslaught: LangStr

        #: ::
        #:
        #:     Name of the The Last Stand co-op level.
        #:
        #:     English: "The Last Stand"
        the_last_stand: LangStr

        #: ::
        #:
        #:     Name of the Uber Football co-op level.
        #:
        #:     English: "Uber Football"
        uber_football: LangStr

        #: ::
        #:
        #:     Name of the Uber Onslaught co-op level.
        #:
        #:     English: "Uber Onslaught"
        uber_onslaught: LangStr

        #: ::
        #:
        #:     Name of the Uber Runaround co-op level.
        #:
        #:     English: "Uber Runaround"
        uber_runaround: LangStr

        def uber_variant(self, *, game: str | LangStr) -> LangStr:
            """
            ::

                Name of the Uber difficulty variant of a level.

                English: "Uber {game}"
            """

    class StringsGameDescriptionsGroup:
        """
        ::

            Minigame objective descriptions shown at match start and on game
            lists. Mods define their own; those show untranslated.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Be the chosen one for a length of time to win. Kill the
        #:     chosen one to become it."
        be_the_chosen_one_for_a: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Bomb as many targets as you can."
        bomb_as_many_targets_as_you: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Carry the flag for a set length of time."
        carry_the_flag_for_a_set: LangStr

        def carry_the_flag_for_seconds(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Carry the flag for {arg1} seconds."
            """

        def carry_the_flag_for_seconds_2(
            self, *, arg1: str | LangStr
        ) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Carry the flag for {arg1} seconds"
            """

        def crush_of_your_enemies(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Crush {arg1} of your enemies."
            """

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Defeat all enemies."
        defeat_all_enemies: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Dodge the falling bombs."
        dodge_the_falling_bombs: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Final glorious epic slow motion battle to the death."
        final_glorious_epic_slow_motion_battle: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Gather eggs!"
        gather_eggs: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Get the flag to the enemy end zone."
        get_the_flag_to_the_enemy: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "How fast can you defeat the ninjas?"
        how_fast_can_you_defeat_the: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Kill a set number of enemies to win."
        kill_a_set_number_of_enemies: LangStr

        def kill_enemies(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Defeat {arg1} enemies"
            """

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Last one standing wins."
        last_one_standing_wins: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "last one standing wins"
        last_one_standing_wins_2: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Last remaining alive wins."
        last_remaining_alive_wins: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Last team standing wins."
        last_team_standing_wins: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "last team standing wins"
        last_team_standing_wins_2: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Prevent enemies from reaching the exit."
        prevent_enemies_from_reaching_the_exit: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Reach the enemy flag to score."
        reach_the_enemy_flag_to_score: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "return 1 flag"
        return_1_flag: LangStr

        def return_flags(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Return {arg1} flags"
            """

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Return the enemy flag to score."
        return_the_enemy_flag_to_score: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Run 1 lap."
        run_1_lap: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "run 1 lap"
        run_1_lap_2: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Run 1 lap. Your entire team has to finish."
        run_1_lap_your_entire_team: LangStr

        def run_laps(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Run {arg1} laps."
            """

        def run_laps_2(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Run {arg1} laps"
            """

        def run_laps_your_entire_team_has(
            self, *, arg1: str | LangStr
        ) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Run {arg1} laps. Your entire team has to finish."
            """

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Run real fast!"
        run_real_fast: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Score a goal."
        score_a_goal: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "score a goal"
        score_a_goal_2: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Score a touchdown."
        score_a_touchdown: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "score a touchdown"
        score_a_touchdown_2: LangStr

        def score_goals(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Score {arg1} goals."
            """

        def score_goals_2(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Score {arg1} goals"
            """

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Score some goals."
        score_some_goals: LangStr

        def score_touchdowns(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Score {arg1} touchdowns."
            """

        def score_touchdowns_2(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "score {arg1} touchdowns"
            """

        def secure_all_flags(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Secure all {arg1} flags."
            """

        def secure_all_flags_2(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Secure all {arg1} flags"
            """

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Secure all flags on the map to win."
        secure_all_flags_on_the_map: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Secure the flag for a set length of time."
        secure_the_flag_for_a_set: LangStr

        def secure_the_flag_for_seconds(
            self, *, arg1: str | LangStr
        ) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Secure the flag for {arg1} seconds."
            """

        def secure_the_flag_for_seconds_2(
            self, *, arg1: str | LangStr
        ) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Secure the flag for {arg1} seconds"
            """

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Steal the enemy flag."
        steal_the_enemy_flag: LangStr

        def steal_the_enemy_flag_times(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Steal the enemy flag {arg1} times."
            """

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "There can be only one."
        there_can_be_only_one: LangStr

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "touch 1 flag"
        touch_1_flag: LangStr

        def touch_flags(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Touch {arg1} flags"
            """

        #: ::
        #:
        #:     Minigame objective description (start-of-match / game lists).
        #:
        #:     English: "Touch the enemy flag."
        touch_the_enemy_flag: LangStr

        def touch_the_enemy_flag_times(self, *, arg1: str | LangStr) -> LangStr:
            """
            ::

                Minigame objective description (start-of-match / game lists).

                English: "Touch the enemy flag {arg1} times."
            """

    class StringsGameNamesGroup:
        """
        ::

            Names of the competitive multiplayer minigames. Mods can add their
            own games; those names are shown untranslated.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Name of the Assault minigame.
        #:
        #:     English: "Assault"
        assault: LangStr

        #: ::
        #:
        #:     Name of the Capture the Flag minigame.
        #:
        #:     English: "Capture the Flag"
        capture_the_flag: LangStr

        #: ::
        #:
        #:     Name of the Chosen One minigame.
        #:
        #:     English: "Chosen One"
        chosen_one: LangStr

        #: ::
        #:
        #:     Name of the Conquest minigame.
        #:
        #:     English: "Conquest"
        conquest: LangStr

        #: ::
        #:
        #:     Name of the Death Match minigame.
        #:
        #:     English: "Death Match"
        death_match: LangStr

        #: ::
        #:
        #:     Name of the Easter Egg Hunt minigame.
        #:
        #:     English: "Easter Egg Hunt"
        easter_egg_hunt: LangStr

        #: ::
        #:
        #:     Name of the Elimination minigame.
        #:
        #:     English: "Elimination"
        elimination: LangStr

        #: ::
        #:
        #:     Name of the Football minigame.
        #:
        #:     English: "Football"
        football: LangStr

        #: ::
        #:
        #:     Name of the Hockey minigame.
        #:
        #:     English: "Hockey"
        hockey: LangStr

        #: ::
        #:
        #:     Name of the Keep Away minigame.
        #:
        #:     English: "Keep Away"
        keep_away: LangStr

        #: ::
        #:
        #:     Name of the King of the Hill minigame.
        #:
        #:     English: "King of the Hill"
        king_of_the_hill: LangStr

        #: ::
        #:
        #:     Name of the Meteor Shower minigame.
        #:
        #:     English: "Meteor Shower"
        meteor_shower: LangStr

        #: ::
        #:
        #:     Name of the Ninja Fight minigame.
        #:
        #:     English: "Ninja Fight"
        ninja_fight: LangStr

        #: ::
        #:
        #:     Name of the Onslaught minigame.
        #:
        #:     English: "Onslaught"
        onslaught: LangStr

        #: ::
        #:
        #:     Name of the Race minigame.
        #:
        #:     English: "Race"
        race: LangStr

        #: ::
        #:
        #:     Name of the Runaround minigame.
        #:
        #:     English: "Runaround"
        runaround: LangStr

        #: ::
        #:
        #:     Name of the Target Practice minigame.
        #:
        #:     English: "Target Practice"
        target_practice: LangStr

        #: ::
        #:
        #:     Name of the The Last Stand minigame.
        #:
        #:     English: "The Last Stand"
        the_last_stand: LangStr

    class StringsMapNamesGroup:
        """
        ::

            Names of the play areas (maps) that matches are held in. Mods can
            add their own maps; those names are shown untranslated.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Name of the Big G play area.
        #:
        #:     English: "Big G"
        big_g: LangStr

        #: ::
        #:
        #:     Name of the Bridgit play area.
        #:
        #:     English: "Bridgit"
        bridgit: LangStr

        #: ::
        #:
        #:     Name of the Courtyard play area.
        #:
        #:     English: "Courtyard"
        courtyard: LangStr

        #: ::
        #:
        #:     Name of the Crag Castle play area.
        #:
        #:     English: "Crag Castle"
        crag_castle: LangStr

        #: ::
        #:
        #:     Name of the Doom Shroom play area.
        #:
        #:     English: "Doom Shroom"
        doom_shroom: LangStr

        #: ::
        #:
        #:     Name of the Football Stadium play area.
        #:
        #:     English: "Football Stadium"
        football_stadium: LangStr

        #: ::
        #:
        #:     Name of the Happy Thoughts play area.
        #:
        #:     English: "Happy Thoughts"
        happy_thoughts: LangStr

        #: ::
        #:
        #:     Name of the Hockey Stadium play area.
        #:
        #:     English: "Hockey Stadium"
        hockey_stadium: LangStr

        #: ::
        #:
        #:     Name of the Lake Frigid play area.
        #:
        #:     English: "Lake Frigid"
        lake_frigid: LangStr

        #: ::
        #:
        #:     Name of the Monkey Face play area.
        #:
        #:     English: "Monkey Face"
        monkey_face: LangStr

        #: ::
        #:
        #:     Name of the Rampage play area.
        #:
        #:     English: "Rampage"
        rampage: LangStr

        #: ::
        #:
        #:     Name of the Roundabout play area.
        #:
        #:     English: "Roundabout"
        roundabout: LangStr

        #: ::
        #:
        #:     Name of the Step Right Up play area.
        #:
        #:     English: "Step Right Up"
        step_right_up: LangStr

        #: ::
        #:
        #:     Name of the The Pad play area.
        #:
        #:     English: "The Pad"
        the_pad: LangStr

        #: ::
        #:
        #:     Name of the Tip Top play area.
        #:
        #:     English: "Tip Top"
        tip_top: LangStr

        #: ::
        #:
        #:     Name of the Tower D play area.
        #:
        #:     English: "Tower D"
        tower_d: LangStr

        #: ::
        #:
        #:     Name of the Zigzag play area.
        #:
        #:     English: "Zigzag"
        zigzag: LangStr

    class StringsGroup:
        """
        ::

            Display names and descriptions for classic content: maps, games, and
            co-op levels. (Character names live with the characters, in
            BaClassicCharacterAssets.)

            See source for the full asset list.
        """

        coop: StringsCoopGroup
        coop_levels: StringsCoopLevelsGroup
        game_descriptions: StringsGameDescriptionsGroup
        game_names: StringsGameNamesGroup
        map_names: StringsMapNamesGroup

    class TexturesGroup:
        """
        ::

            Store-facing presentation art for classic content: every character
            icon and its color mask, the character icon mask, every map preview
            and the map preview mask, and the coin/ticket/chest icons display
            items are drawn with. Also the opened-chest art (icon and tint mask)
            the chest window shows a chest popping open with.

            See source for the full asset list.
        """

        always_land_preview: TextureHandle
        big_g_preview: TextureHandle
        bridgit_preview: TextureHandle
        character_icon_mask: TextureHandle
        chest_icon: TextureHandle
        chest_icon_tint: TextureHandle
        chest_open_icon: TextureHandle
        chest_open_icon_tint: TextureHandle
        coin: TextureHandle
        courtyard_preview: TextureHandle
        crag_castle_preview: TextureHandle
        doom_shroom_preview: TextureHandle
        football_stadium_preview: TextureHandle
        hockey_stadium_preview: TextureHandle
        lake_frigid_preview: TextureHandle
        map_preview_mask: TextureHandle
        monkey_face_preview: TextureHandle
        rampage_preview: TextureHandle
        roundabout_preview: TextureHandle
        step_right_up_preview: TextureHandle
        the_pad_preview: TextureHandle
        tickets: TextureHandle
        tickets_purple: TextureHandle
        tip_top_preview: TextureHandle
        tower_d_preview: TextureHandle
        viewer_mask: TextureHandle
        zigzag_preview: TextureHandle

    #: The ``audio`` group - 11 assets (``aww``, ``cork_pop2``, ``gasp``,
    #: ``nice``, ``ooh``, and 6 more). Full list in source.
    audio: AudioGroup

    #: The ``meshes`` group - 2 assets (``level_select_button_opaque``,
    #: ``level_select_button_transparent``). Full list in source.
    meshes: MeshesGroup

    #: The ``strings`` group - 103 strings (``coop``, ``coop_levels``,
    #: ``game_descriptions``, ``game_names``, ``map_names``, and 98 more). Full
    #: list in source.
    strings: StringsGroup

    #: The ``textures`` group - 27 assets (``always_land_preview``,
    #: ``big_g_preview``, ``bridgit_preview``, ``character_icon_mask``,
    #: ``chest_icon``, and 22 more). Full list in source.
    textures: TexturesGroup

_TREE = {
    'audio': {
        'aww': 's',
        'cork_pop2': 's',
        'gasp': 's',
        'nice': 's',
        'ooh': 's',
        'rev_up': 's',
        'woo': 's',
        'woo2': 's',
        'woo3': 's',
        'wow': 's',
        'yeah': 's',
    },
    'meshes': {
        'level_select_button_opaque': 'm',
        'level_select_button_transparent': 'm',
    },
    'strings': {
        'coop': {'player_count_abbreviated': ('count',)},
        'coop_levels': {
            'infinite_onslaught': (),
            'infinite_runaround': (),
            'onslaught_training': (),
            'pro_football': (),
            'pro_onslaught': (),
            'pro_runaround': (),
            'pro_variant': ('game',),
            'rookie_football': (),
            'rookie_onslaught': (),
            'the_last_stand': (),
            'uber_football': (),
            'uber_onslaught': (),
            'uber_runaround': (),
            'uber_variant': ('game',),
        },
        'game_descriptions': {
            'be_the_chosen_one_for_a': (),
            'bomb_as_many_targets_as_you': (),
            'carry_the_flag_for_a_set': (),
            'carry_the_flag_for_seconds': ('arg1',),
            'carry_the_flag_for_seconds_2': ('arg1',),
            'crush_of_your_enemies': ('arg1',),
            'defeat_all_enemies': (),
            'dodge_the_falling_bombs': (),
            'final_glorious_epic_slow_motion_battle': (),
            'gather_eggs': (),
            'get_the_flag_to_the_enemy': (),
            'how_fast_can_you_defeat_the': (),
            'kill_a_set_number_of_enemies': (),
            'kill_enemies': ('arg1',),
            'last_one_standing_wins': (),
            'last_one_standing_wins_2': (),
            'last_remaining_alive_wins': (),
            'last_team_standing_wins': (),
            'last_team_standing_wins_2': (),
            'prevent_enemies_from_reaching_the_exit': (),
            'reach_the_enemy_flag_to_score': (),
            'return_1_flag': (),
            'return_flags': ('arg1',),
            'return_the_enemy_flag_to_score': (),
            'run_1_lap': (),
            'run_1_lap_2': (),
            'run_1_lap_your_entire_team': (),
            'run_laps': ('arg1',),
            'run_laps_2': ('arg1',),
            'run_laps_your_entire_team_has': ('arg1',),
            'run_real_fast': (),
            'score_a_goal': (),
            'score_a_goal_2': (),
            'score_a_touchdown': (),
            'score_a_touchdown_2': (),
            'score_goals': ('arg1',),
            'score_goals_2': ('arg1',),
            'score_some_goals': (),
            'score_touchdowns': ('arg1',),
            'score_touchdowns_2': ('arg1',),
            'secure_all_flags': ('arg1',),
            'secure_all_flags_2': ('arg1',),
            'secure_all_flags_on_the_map': (),
            'secure_the_flag_for_a_set': (),
            'secure_the_flag_for_seconds': ('arg1',),
            'secure_the_flag_for_seconds_2': ('arg1',),
            'steal_the_enemy_flag': (),
            'steal_the_enemy_flag_times': ('arg1',),
            'there_can_be_only_one': (),
            'touch_1_flag': (),
            'touch_flags': ('arg1',),
            'touch_the_enemy_flag': (),
            'touch_the_enemy_flag_times': ('arg1',),
        },
        'game_names': {
            'assault': (),
            'capture_the_flag': (),
            'chosen_one': (),
            'conquest': (),
            'death_match': (),
            'easter_egg_hunt': (),
            'elimination': (),
            'football': (),
            'hockey': (),
            'keep_away': (),
            'king_of_the_hill': (),
            'meteor_shower': (),
            'ninja_fight': (),
            'onslaught': (),
            'race': (),
            'runaround': (),
            'target_practice': (),
            'the_last_stand': (),
        },
        'map_names': {
            'big_g': (),
            'bridgit': (),
            'courtyard': (),
            'crag_castle': (),
            'doom_shroom': (),
            'football_stadium': (),
            'happy_thoughts': (),
            'hockey_stadium': (),
            'lake_frigid': (),
            'monkey_face': (),
            'rampage': (),
            'roundabout': (),
            'step_right_up': (),
            'the_pad': (),
            'tip_top': (),
            'tower_d': (),
            'zigzag': (),
        },
    },
    'textures': {
        'always_land_preview': 't',
        'big_g_preview': 't',
        'bridgit_preview': 't',
        'character_icon_mask': 't',
        'chest_icon': 't',
        'chest_icon_tint': 't',
        'chest_open_icon': 't',
        'chest_open_icon_tint': 't',
        'coin': 't',
        'courtyard_preview': 't',
        'crag_castle_preview': 't',
        'doom_shroom_preview': 't',
        'football_stadium_preview': 't',
        'hockey_stadium_preview': 't',
        'lake_frigid_preview': 't',
        'map_preview_mask': 't',
        'monkey_face_preview': 't',
        'rampage_preview': 't',
        'roundabout_preview': 't',
        'step_right_up_preview': 't',
        'the_pad_preview': 't',
        'tickets': 't',
        'tickets_purple': 't',
        'tip_top_preview': 't',
        'tower_d_preview': 't',
        'viewer_mask': 't',
        'zigzag_preview': 't',
    },
}


if not TYPE_CHECKING:
    audio = AssetGroup(_ASSET_PACKAGE, _TREE['audio'], 'audio')
    meshes = AssetGroup(_ASSET_PACKAGE, _TREE['meshes'], 'meshes')
    strings = LangStrDir(_ASSET_PACKAGE, _TREE['strings'], 'strings')
    textures = AssetGroup(_ASSET_PACKAGE, _TREE['textures'], 'textures')
