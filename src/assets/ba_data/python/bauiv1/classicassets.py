# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.baclassicassets.260808a`` (bauiv1).

All assets for classic bombsquad.
"""

# ba_meta require api 9
# ba_meta require asset-package a-0.baclassicassets.260808a

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

__asset_package__ = 'a-0.baclassicassets.260808a'

from typing import TYPE_CHECKING

from bauiv1._assetref import AssetGroup

from babase import LangStrDir

if TYPE_CHECKING:
    from bauiv1._assetref import (
        MeshVerifiedSpec,
        SoundVerifiedSpec,
        TextureVerifiedSpec,
    )
    from babase import LangStr

    class AudioGroup:
        """
        ::

            All standard game sounds (everything non-bootstrap).

            See source for the full asset list.
        """

        achievement: SoundVerifiedSpec
        action_hero1: SoundVerifiedSpec
        action_hero2: SoundVerifiedSpec
        action_hero3: SoundVerifiedSpec
        action_hero4: SoundVerifiedSpec
        action_hero_death: SoundVerifiedSpec
        action_hero_fall: SoundVerifiedSpec
        action_hero_hit1: SoundVerifiedSpec
        action_hero_hit2: SoundVerifiedSpec
        activate_beep: SoundVerifiedSpec
        agent1: SoundVerifiedSpec
        agent2: SoundVerifiedSpec
        agent3: SoundVerifiedSpec
        agent4: SoundVerifiedSpec
        agent_death: SoundVerifiedSpec
        agent_fall: SoundVerifiedSpec
        agent_hit1: SoundVerifiedSpec
        agent_hit2: SoundVerifiedSpec
        alarm: SoundVerifiedSpec
        ali1: SoundVerifiedSpec
        ali2: SoundVerifiedSpec
        ali3: SoundVerifiedSpec
        ali4: SoundVerifiedSpec
        ali_death: SoundVerifiedSpec
        ali_fall: SoundVerifiedSpec
        ali_hit1: SoundVerifiedSpec
        ali_hit2: SoundVerifiedSpec
        alien1: SoundVerifiedSpec
        alien2: SoundVerifiedSpec
        alien3: SoundVerifiedSpec
        alien4: SoundVerifiedSpec
        alien_death: SoundVerifiedSpec
        alien_fall: SoundVerifiedSpec
        alien_hit1: SoundVerifiedSpec
        alien_hit2: SoundVerifiedSpec
        announce_eight: SoundVerifiedSpec
        announce_five: SoundVerifiedSpec
        announce_four: SoundVerifiedSpec
        announce_nine: SoundVerifiedSpec
        announce_one: SoundVerifiedSpec
        announce_seven: SoundVerifiedSpec
        announce_six: SoundVerifiedSpec
        announce_ten: SoundVerifiedSpec
        announce_three: SoundVerifiedSpec
        announce_two: SoundVerifiedSpec
        assassin1: SoundVerifiedSpec
        assassin2: SoundVerifiedSpec
        assassin3: SoundVerifiedSpec
        assassin4: SoundVerifiedSpec
        assassin_death: SoundVerifiedSpec
        assassin_fall: SoundVerifiedSpec
        assassin_hit1: SoundVerifiedSpec
        assassin_hit2: SoundVerifiedSpec
        aww: SoundVerifiedSpec
        bear1: SoundVerifiedSpec
        bear2: SoundVerifiedSpec
        bear3: SoundVerifiedSpec
        bear4: SoundVerifiedSpec
        bear_death: SoundVerifiedSpec
        bear_fall: SoundVerifiedSpec
        bear_hit1: SoundVerifiedSpec
        bear_hit2: SoundVerifiedSpec
        bell_high: SoundVerifiedSpec
        bell_low: SoundVerifiedSpec
        bell_med: SoundVerifiedSpec
        big_impact: SoundVerifiedSpec
        big_impact2: SoundVerifiedSpec
        block: SoundVerifiedSpec
        bomb_drop01: SoundVerifiedSpec
        bomb_drop02: SoundVerifiedSpec
        bomb_roll01: SoundVerifiedSpec
        bones1: SoundVerifiedSpec
        bones2: SoundVerifiedSpec
        bones3: SoundVerifiedSpec
        bones_death: SoundVerifiedSpec
        bones_fall: SoundVerifiedSpec
        boo: SoundVerifiedSpec
        box_drop: SoundVerifiedSpec
        boxing_bell: SoundVerifiedSpec
        bunny1: SoundVerifiedSpec
        bunny2: SoundVerifiedSpec
        bunny3: SoundVerifiedSpec
        bunny4: SoundVerifiedSpec
        bunny_death: SoundVerifiedSpec
        bunny_fall: SoundVerifiedSpec
        bunny_hit1: SoundVerifiedSpec
        bunny_hit2: SoundVerifiedSpec
        bunny_jump: SoundVerifiedSpec
        cash_register2: SoundVerifiedSpec
        char_select_music: SoundVerifiedSpec
        cheer: SoundVerifiedSpec
        cork_pop2: SoundVerifiedSpec
        cowboy1: SoundVerifiedSpec
        cowboy2: SoundVerifiedSpec
        cowboy3: SoundVerifiedSpec
        cowboy4: SoundVerifiedSpec
        cowboy_death: SoundVerifiedSpec
        cowboy_fall: SoundVerifiedSpec
        cowboy_hit1: SoundVerifiedSpec
        cowboy_hit2: SoundVerifiedSpec
        crowd_chant: SoundVerifiedSpec
        cyborg1: SoundVerifiedSpec
        cyborg2: SoundVerifiedSpec
        cyborg3: SoundVerifiedSpec
        cyborg4: SoundVerifiedSpec
        cyborg_death: SoundVerifiedSpec
        cyborg_fall: SoundVerifiedSpec
        cyborg_hit1: SoundVerifiedSpec
        cyborg_hit2: SoundVerifiedSpec
        cymbal: SoundVerifiedSpec
        debris_fall: SoundVerifiedSpec
        deek2: SoundVerifiedSpec
        ding_small: SoundVerifiedSpec
        ding_small_high: SoundVerifiedSpec
        dripity: SoundVerifiedSpec
        drum_roll: SoundVerifiedSpec
        drum_roll_short: SoundVerifiedSpec
        explosion01: SoundVerifiedSpec
        explosion02: SoundVerifiedSpec
        explosion03: SoundVerifiedSpec
        explosion04: SoundVerifiedSpec
        explosion05: SoundVerifiedSpec
        fanfare: SoundVerifiedSpec
        flag_catcher_music: SoundVerifiedSpec
        flying_music: SoundVerifiedSpec
        foghorn: SoundVerifiedSpec
        foot_impact01: SoundVerifiedSpec
        foot_impact02: SoundVerifiedSpec
        foot_impact03: SoundVerifiedSpec
        forward_march_music: SoundVerifiedSpec
        freeze: SoundVerifiedSpec
        frosty01: SoundVerifiedSpec
        frosty02: SoundVerifiedSpec
        frosty03: SoundVerifiedSpec
        frosty04: SoundVerifiedSpec
        frosty05: SoundVerifiedSpec
        frosty_death: SoundVerifiedSpec
        frosty_fall: SoundVerifiedSpec
        frosty_hit01: SoundVerifiedSpec
        frosty_hit02: SoundVerifiedSpec
        frosty_hit03: SoundVerifiedSpec
        fuse01: SoundVerifiedSpec
        gasp: SoundVerifiedSpec
        gladiator1: SoundVerifiedSpec
        gladiator2: SoundVerifiedSpec
        gladiator3: SoundVerifiedSpec
        gladiator4: SoundVerifiedSpec
        gladiator_death: SoundVerifiedSpec
        gladiator_fall: SoundVerifiedSpec
        gladiator_hit1: SoundVerifiedSpec
        gladiator_hit2: SoundVerifiedSpec
        gong: SoundVerifiedSpec
        grand_romp_music: SoundVerifiedSpec
        gravel_skid: SoundVerifiedSpec
        health_powerup: SoundVerifiedSpec
        hiss: SoundVerifiedSpec
        impact_hard: SoundVerifiedSpec
        impact_hard2: SoundVerifiedSpec
        impact_hard3: SoundVerifiedSpec
        impact_medium: SoundVerifiedSpec
        impact_medium2: SoundVerifiedSpec
        jack01: SoundVerifiedSpec
        jack02: SoundVerifiedSpec
        jack03: SoundVerifiedSpec
        jack04: SoundVerifiedSpec
        jack05: SoundVerifiedSpec
        jack06: SoundVerifiedSpec
        jack_death01: SoundVerifiedSpec
        jack_fall01: SoundVerifiedSpec
        jack_hit01: SoundVerifiedSpec
        jack_hit02: SoundVerifiedSpec
        jack_hit03: SoundVerifiedSpec
        jack_hit04: SoundVerifiedSpec
        jack_hit05: SoundVerifiedSpec
        jack_hit06: SoundVerifiedSpec
        jack_hit07: SoundVerifiedSpec
        jumpsuit1: SoundVerifiedSpec
        jumpsuit2: SoundVerifiedSpec
        jumpsuit3: SoundVerifiedSpec
        jumpsuit4: SoundVerifiedSpec
        jumpsuit_death: SoundVerifiedSpec
        jumpsuit_fall: SoundVerifiedSpec
        jumpsuit_hit1: SoundVerifiedSpec
        jumpsuit_hit2: SoundVerifiedSpec
        kronk1: SoundVerifiedSpec
        kronk10: SoundVerifiedSpec
        kronk2: SoundVerifiedSpec
        kronk3: SoundVerifiedSpec
        kronk4: SoundVerifiedSpec
        kronk5: SoundVerifiedSpec
        kronk6: SoundVerifiedSpec
        kronk7: SoundVerifiedSpec
        kronk8: SoundVerifiedSpec
        kronk9: SoundVerifiedSpec
        kronk_death: SoundVerifiedSpec
        kronk_fall: SoundVerifiedSpec
        laser: SoundVerifiedSpec
        laser_reverse: SoundVerifiedSpec
        mel01: SoundVerifiedSpec
        mel02: SoundVerifiedSpec
        mel03: SoundVerifiedSpec
        mel04: SoundVerifiedSpec
        mel05: SoundVerifiedSpec
        mel06: SoundVerifiedSpec
        mel07: SoundVerifiedSpec
        mel08: SoundVerifiedSpec
        mel09: SoundVerifiedSpec
        mel10: SoundVerifiedSpec
        mel_death01: SoundVerifiedSpec
        mel_fall01: SoundVerifiedSpec
        menu_music: SoundVerifiedSpec
        metal_hit: SoundVerifiedSpec
        metal_skid: SoundVerifiedSpec
        nice: SoundVerifiedSpec
        ninja_attack1: SoundVerifiedSpec
        ninja_attack2: SoundVerifiedSpec
        ninja_attack3: SoundVerifiedSpec
        ninja_attack4: SoundVerifiedSpec
        ninja_attack5: SoundVerifiedSpec
        ninja_attack6: SoundVerifiedSpec
        ninja_attack7: SoundVerifiedSpec
        ninja_death1: SoundVerifiedSpec
        ninja_fall1: SoundVerifiedSpec
        ninja_hit1: SoundVerifiedSpec
        ninja_hit2: SoundVerifiedSpec
        ninja_hit3: SoundVerifiedSpec
        ninja_hit4: SoundVerifiedSpec
        ninja_hit5: SoundVerifiedSpec
        ninja_hit6: SoundVerifiedSpec
        ninja_hit7: SoundVerifiedSpec
        ninja_hit8: SoundVerifiedSpec
        old_lady1: SoundVerifiedSpec
        old_lady2: SoundVerifiedSpec
        old_lady3: SoundVerifiedSpec
        old_lady4: SoundVerifiedSpec
        old_lady_death: SoundVerifiedSpec
        old_lady_fall: SoundVerifiedSpec
        old_lady_hit1: SoundVerifiedSpec
        old_lady_hit2: SoundVerifiedSpec
        ooh: SoundVerifiedSpec
        opera_singer1: SoundVerifiedSpec
        opera_singer2: SoundVerifiedSpec
        opera_singer3: SoundVerifiedSpec
        opera_singer4: SoundVerifiedSpec
        opera_singer_death: SoundVerifiedSpec
        opera_singer_fall: SoundVerifiedSpec
        opera_singer_hit1: SoundVerifiedSpec
        opera_singer_hit2: SoundVerifiedSpec
        orchestra_hit: SoundVerifiedSpec
        orchestra_hit2: SoundVerifiedSpec
        orchestra_hit3: SoundVerifiedSpec
        orchestra_hit4: SoundVerifiedSpec
        orchestra_hit_big1: SoundVerifiedSpec
        orchestra_hit_big2: SoundVerifiedSpec
        penguin1: SoundVerifiedSpec
        penguin2: SoundVerifiedSpec
        penguin3: SoundVerifiedSpec
        penguin4: SoundVerifiedSpec
        penguin_death: SoundVerifiedSpec
        penguin_fall: SoundVerifiedSpec
        penguin_hit1: SoundVerifiedSpec
        penguin_hit2: SoundVerifiedSpec
        pixie1: SoundVerifiedSpec
        pixie2: SoundVerifiedSpec
        pixie3: SoundVerifiedSpec
        pixie4: SoundVerifiedSpec
        pixie_death: SoundVerifiedSpec
        pixie_fall: SoundVerifiedSpec
        pixie_hit1: SoundVerifiedSpec
        pixie_hit2: SoundVerifiedSpec
        player_death: SoundVerifiedSpec
        player_left: SoundVerifiedSpec
        pop01: SoundVerifiedSpec
        powerup01: SoundVerifiedSpec
        punch_strong01: SoundVerifiedSpec
        punch_strong02: SoundVerifiedSpec
        punch_swish: SoundVerifiedSpec
        punch_weak01: SoundVerifiedSpec
        race_beep1: SoundVerifiedSpec
        race_beep2: SoundVerifiedSpec
        ref_whistle: SoundVerifiedSpec
        rev_up: SoundVerifiedSpec
        robot1: SoundVerifiedSpec
        robot2: SoundVerifiedSpec
        robot3: SoundVerifiedSpec
        robot4: SoundVerifiedSpec
        robot_death: SoundVerifiedSpec
        robot_fall: SoundVerifiedSpec
        robot_hit1: SoundVerifiedSpec
        robot_hit2: SoundVerifiedSpec
        run_away_music: SoundVerifiedSpec
        santa01: SoundVerifiedSpec
        santa02: SoundVerifiedSpec
        santa03: SoundVerifiedSpec
        santa04: SoundVerifiedSpec
        santa05: SoundVerifiedSpec
        santa_death: SoundVerifiedSpec
        santa_fall: SoundVerifiedSpec
        santa_hit01: SoundVerifiedSpec
        santa_hit02: SoundVerifiedSpec
        santa_hit03: SoundVerifiedSpec
        santa_hit04: SoundVerifiedSpec
        scamper01: SoundVerifiedSpec
        scary_music: SoundVerifiedSpec
        score: SoundVerifiedSpec
        score_hit01: SoundVerifiedSpec
        score_hit02: SoundVerifiedSpec
        scores_epic_music: SoundVerifiedSpec
        shatter: SoundVerifiedSpec
        shield_down: SoundVerifiedSpec
        shield_hit: SoundVerifiedSpec
        shield_up: SoundVerifiedSpec
        skid01: SoundVerifiedSpec
        slow_epic_music: SoundVerifiedSpec
        spawn: SoundVerifiedSpec
        spaz_attack01: SoundVerifiedSpec
        spaz_attack02: SoundVerifiedSpec
        spaz_attack03: SoundVerifiedSpec
        spaz_attack04: SoundVerifiedSpec
        spaz_death01: SoundVerifiedSpec
        spaz_eff: SoundVerifiedSpec
        spaz_fall01: SoundVerifiedSpec
        spaz_impact01: SoundVerifiedSpec
        spaz_impact02: SoundVerifiedSpec
        spaz_impact03: SoundVerifiedSpec
        spaz_impact04: SoundVerifiedSpec
        spaz_jump01: SoundVerifiedSpec
        spaz_jump02: SoundVerifiedSpec
        spaz_jump03: SoundVerifiedSpec
        spaz_jump04: SoundVerifiedSpec
        spaz_ow: SoundVerifiedSpec
        spaz_pickup01: SoundVerifiedSpec
        spaz_scream01: SoundVerifiedSpec
        splatter: SoundVerifiedSpec
        sports_music: SoundVerifiedSpec
        sticky_impact: SoundVerifiedSpec
        super_punch: SoundVerifiedSpec
        superhero1: SoundVerifiedSpec
        superhero2: SoundVerifiedSpec
        superhero3: SoundVerifiedSpec
        superhero4: SoundVerifiedSpec
        superhero_death: SoundVerifiedSpec
        superhero_fall: SoundVerifiedSpec
        superhero_hit1: SoundVerifiedSpec
        superhero_hit2: SoundVerifiedSpec
        survival_music: SoundVerifiedSpec
        swip: SoundVerifiedSpec
        swip2: SoundVerifiedSpec
        techno_hit01: SoundVerifiedSpec
        tick: SoundVerifiedSpec
        ticking: SoundVerifiedSpec
        to_the_death_music: SoundVerifiedSpec
        trash_rummage: SoundVerifiedSpec
        victory_music: SoundVerifiedSpec
        warn_beep: SoundVerifiedSpec
        warn_beeps: SoundVerifiedSpec
        warrior1: SoundVerifiedSpec
        warrior2: SoundVerifiedSpec
        warrior3: SoundVerifiedSpec
        warrior4: SoundVerifiedSpec
        warrior_death: SoundVerifiedSpec
        warrior_fall: SoundVerifiedSpec
        warrior_hit1: SoundVerifiedSpec
        warrior_hit2: SoundVerifiedSpec
        when_johnny_comes_marching_home_music: SoundVerifiedSpec
        witch1: SoundVerifiedSpec
        witch2: SoundVerifiedSpec
        witch3: SoundVerifiedSpec
        witch4: SoundVerifiedSpec
        witch_death: SoundVerifiedSpec
        witch_fall: SoundVerifiedSpec
        witch_hit1: SoundVerifiedSpec
        witch_hit2: SoundVerifiedSpec
        wizard1: SoundVerifiedSpec
        wizard2: SoundVerifiedSpec
        wizard3: SoundVerifiedSpec
        wizard4: SoundVerifiedSpec
        wizard_death: SoundVerifiedSpec
        wizard_fall: SoundVerifiedSpec
        wizard_hit1: SoundVerifiedSpec
        wizard_hit2: SoundVerifiedSpec
        woo: SoundVerifiedSpec
        woo2: SoundVerifiedSpec
        woo3: SoundVerifiedSpec
        wood_debris_fall: SoundVerifiedSpec
        wow: SoundVerifiedSpec
        wrestler1: SoundVerifiedSpec
        wrestler2: SoundVerifiedSpec
        wrestler3: SoundVerifiedSpec
        wrestler4: SoundVerifiedSpec
        wrestler_death: SoundVerifiedSpec
        wrestler_fall: SoundVerifiedSpec
        wrestler_hit1: SoundVerifiedSpec
        wrestler_hit2: SoundVerifiedSpec
        yeah: SoundVerifiedSpec
        zoe_attack01: SoundVerifiedSpec
        zoe_attack02: SoundVerifiedSpec
        zoe_attack03: SoundVerifiedSpec
        zoe_attack04: SoundVerifiedSpec
        zoe_death01: SoundVerifiedSpec
        zoe_eff: SoundVerifiedSpec
        zoe_fall01: SoundVerifiedSpec
        zoe_impact01: SoundVerifiedSpec
        zoe_impact02: SoundVerifiedSpec
        zoe_impact03: SoundVerifiedSpec
        zoe_impact04: SoundVerifiedSpec
        zoe_jump01: SoundVerifiedSpec
        zoe_jump02: SoundVerifiedSpec
        zoe_jump03: SoundVerifiedSpec
        zoe_ow: SoundVerifiedSpec
        zoe_pickup01: SoundVerifiedSpec
        zoe_scream01: SoundVerifiedSpec

    class MeshesGroup:
        """
        ::

            All standard game meshes (everything non-bootstrap).

            See source for the full asset list.
        """

        achievement_outline: MeshVerifiedSpec
        action_hero_fore_arm: MeshVerifiedSpec
        action_hero_hand: MeshVerifiedSpec
        action_hero_head: MeshVerifiedSpec
        action_hero_lower_leg: MeshVerifiedSpec
        action_hero_pelvis: MeshVerifiedSpec
        action_hero_toes: MeshVerifiedSpec
        action_hero_torso: MeshVerifiedSpec
        action_hero_upper_arm: MeshVerifiedSpec
        action_hero_upper_leg: MeshVerifiedSpec
        agent_fore_arm: MeshVerifiedSpec
        agent_hand: MeshVerifiedSpec
        agent_head: MeshVerifiedSpec
        agent_lower_leg: MeshVerifiedSpec
        agent_pelvis: MeshVerifiedSpec
        agent_toes: MeshVerifiedSpec
        agent_torso: MeshVerifiedSpec
        agent_upper_arm: MeshVerifiedSpec
        agent_upper_leg: MeshVerifiedSpec
        ali_fore_arm: MeshVerifiedSpec
        ali_hand: MeshVerifiedSpec
        ali_head: MeshVerifiedSpec
        ali_lower_leg: MeshVerifiedSpec
        ali_pelvis: MeshVerifiedSpec
        ali_toes: MeshVerifiedSpec
        ali_torso: MeshVerifiedSpec
        ali_upper_arm: MeshVerifiedSpec
        ali_upper_leg: MeshVerifiedSpec
        alien_fore_arm: MeshVerifiedSpec
        alien_hand: MeshVerifiedSpec
        alien_head: MeshVerifiedSpec
        alien_lower_leg: MeshVerifiedSpec
        alien_pelvis: MeshVerifiedSpec
        alien_toes: MeshVerifiedSpec
        alien_torso: MeshVerifiedSpec
        alien_upper_arm: MeshVerifiedSpec
        alien_upper_leg: MeshVerifiedSpec
        always_land_bg: MeshVerifiedSpec
        always_land_level: MeshVerifiedSpec
        always_land_level_bottom: MeshVerifiedSpec
        always_land_vrfill_mound: MeshVerifiedSpec
        angry_computer_transparent: MeshVerifiedSpec
        assassin_fore_arm: MeshVerifiedSpec
        assassin_hand: MeshVerifiedSpec
        assassin_head: MeshVerifiedSpec
        assassin_lower_leg: MeshVerifiedSpec
        assassin_pelvis: MeshVerifiedSpec
        assassin_toes: MeshVerifiedSpec
        assassin_torso: MeshVerifiedSpec
        assassin_upper_arm: MeshVerifiedSpec
        assassin_upper_leg: MeshVerifiedSpec
        bear_fore_arm: MeshVerifiedSpec
        bear_hand: MeshVerifiedSpec
        bear_head: MeshVerifiedSpec
        bear_lower_leg: MeshVerifiedSpec
        bear_pelvis: MeshVerifiedSpec
        bear_toes: MeshVerifiedSpec
        bear_torso: MeshVerifiedSpec
        bear_upper_arm: MeshVerifiedSpec
        bear_upper_leg: MeshVerifiedSpec
        big_g: MeshVerifiedSpec
        big_gbottom: MeshVerifiedSpec
        bomb: MeshVerifiedSpec
        bomb_sticky: MeshVerifiedSpec
        bones_fore_arm: MeshVerifiedSpec
        bones_hand: MeshVerifiedSpec
        bones_head: MeshVerifiedSpec
        bones_lower_leg: MeshVerifiedSpec
        bones_pelvis: MeshVerifiedSpec
        bones_toes: MeshVerifiedSpec
        bones_torso: MeshVerifiedSpec
        bones_upper_arm: MeshVerifiedSpec
        bones_upper_leg: MeshVerifiedSpec
        bridgit_level_bottom: MeshVerifiedSpec
        bridgit_level_top: MeshVerifiedSpec
        bunny_fore_arm: MeshVerifiedSpec
        bunny_hand: MeshVerifiedSpec
        bunny_head: MeshVerifiedSpec
        bunny_lower_leg: MeshVerifiedSpec
        bunny_pelvis: MeshVerifiedSpec
        bunny_toes: MeshVerifiedSpec
        bunny_torso: MeshVerifiedSpec
        bunny_upper_arm: MeshVerifiedSpec
        bunny_upper_leg: MeshVerifiedSpec
        button_null: MeshVerifiedSpec
        courtyard_level: MeshVerifiedSpec
        courtyard_level_bottom: MeshVerifiedSpec
        cowboy_fore_arm: MeshVerifiedSpec
        cowboy_hand: MeshVerifiedSpec
        cowboy_head: MeshVerifiedSpec
        cowboy_lower_leg: MeshVerifiedSpec
        cowboy_pelvis: MeshVerifiedSpec
        cowboy_toes: MeshVerifiedSpec
        cowboy_torso: MeshVerifiedSpec
        cowboy_upper_arm: MeshVerifiedSpec
        cowboy_upper_leg: MeshVerifiedSpec
        crag_castle_level: MeshVerifiedSpec
        crag_castle_level_bottom: MeshVerifiedSpec
        crag_castle_vrfill_mound: MeshVerifiedSpec
        currency_meter: MeshVerifiedSpec
        currency_plus_button: MeshVerifiedSpec
        cyborg_fore_arm: MeshVerifiedSpec
        cyborg_hand: MeshVerifiedSpec
        cyborg_head: MeshVerifiedSpec
        cyborg_lower_leg: MeshVerifiedSpec
        cyborg_pelvis: MeshVerifiedSpec
        cyborg_toes: MeshVerifiedSpec
        cyborg_torso: MeshVerifiedSpec
        cyborg_upper_arm: MeshVerifiedSpec
        cyborg_upper_leg: MeshVerifiedSpec
        doom_shroom_bg: MeshVerifiedSpec
        doom_shroom_level: MeshVerifiedSpec
        doom_shroom_stem: MeshVerifiedSpec
        doom_shroom_vrfill: MeshVerifiedSpec
        egg: MeshVerifiedSpec
        football_stadium: MeshVerifiedSpec
        football_stadium_vrfill: MeshVerifiedSpec
        frame_inset: MeshVerifiedSpec
        frosty_fore_arm: MeshVerifiedSpec
        frosty_hand: MeshVerifiedSpec
        frosty_head: MeshVerifiedSpec
        frosty_lower_leg: MeshVerifiedSpec
        frosty_pelvis: MeshVerifiedSpec
        frosty_toes: MeshVerifiedSpec
        frosty_torso: MeshVerifiedSpec
        frosty_upper_arm: MeshVerifiedSpec
        frosty_upper_leg: MeshVerifiedSpec
        gladiator_fore_arm: MeshVerifiedSpec
        gladiator_hand: MeshVerifiedSpec
        gladiator_head: MeshVerifiedSpec
        gladiator_lower_leg: MeshVerifiedSpec
        gladiator_pelvis: MeshVerifiedSpec
        gladiator_toes: MeshVerifiedSpec
        gladiator_torso: MeshVerifiedSpec
        gladiator_upper_arm: MeshVerifiedSpec
        gladiator_upper_leg: MeshVerifiedSpec
        heart_opaque: MeshVerifiedSpec
        heart_transparent: MeshVerifiedSpec
        hockey_stadium_inner: MeshVerifiedSpec
        hockey_stadium_outer: MeshVerifiedSpec
        hockey_stadium_stands: MeshVerifiedSpec
        image2x1_vertical: MeshVerifiedSpec
        impact_bomb: MeshVerifiedSpec
        jack_fore_arm: MeshVerifiedSpec
        jack_hand: MeshVerifiedSpec
        jack_head: MeshVerifiedSpec
        jack_lower_leg: MeshVerifiedSpec
        jack_toes: MeshVerifiedSpec
        jack_torso: MeshVerifiedSpec
        jack_upper_arm: MeshVerifiedSpec
        jack_upper_leg: MeshVerifiedSpec
        jumpsuit_fore_arm: MeshVerifiedSpec
        jumpsuit_hand: MeshVerifiedSpec
        jumpsuit_head: MeshVerifiedSpec
        jumpsuit_lower_leg: MeshVerifiedSpec
        jumpsuit_pelvis: MeshVerifiedSpec
        jumpsuit_toes: MeshVerifiedSpec
        jumpsuit_torso: MeshVerifiedSpec
        jumpsuit_upper_arm: MeshVerifiedSpec
        jumpsuit_upper_leg: MeshVerifiedSpec
        kronk_fore_arm: MeshVerifiedSpec
        kronk_hand: MeshVerifiedSpec
        kronk_head: MeshVerifiedSpec
        kronk_lower_leg: MeshVerifiedSpec
        kronk_pelvis: MeshVerifiedSpec
        kronk_toes: MeshVerifiedSpec
        kronk_torso: MeshVerifiedSpec
        kronk_upper_arm: MeshVerifiedSpec
        kronk_upper_leg: MeshVerifiedSpec
        lake_frigid: MeshVerifiedSpec
        lake_frigid_reflections: MeshVerifiedSpec
        lake_frigid_top: MeshVerifiedSpec
        lake_frigid_vrfill: MeshVerifiedSpec
        land_mine: MeshVerifiedSpec
        level_select_button_opaque: MeshVerifiedSpec
        level_select_button_transparent: MeshVerifiedSpec
        logo: MeshVerifiedSpec
        logo_transparent: MeshVerifiedSpec
        mel_fore_arm: MeshVerifiedSpec
        mel_hand: MeshVerifiedSpec
        mel_head: MeshVerifiedSpec
        mel_lower_leg: MeshVerifiedSpec
        mel_toes: MeshVerifiedSpec
        mel_torso: MeshVerifiedSpec
        mel_upper_arm: MeshVerifiedSpec
        mel_upper_leg: MeshVerifiedSpec
        meter_transparent: MeshVerifiedSpec
        monkey_face_level: MeshVerifiedSpec
        monkey_face_level_bottom: MeshVerifiedSpec
        nature_background: MeshVerifiedSpec
        nature_background_vrfill: MeshVerifiedSpec
        neo_spaz_fore_arm: MeshVerifiedSpec
        neo_spaz_hand: MeshVerifiedSpec
        neo_spaz_head: MeshVerifiedSpec
        neo_spaz_lower_leg: MeshVerifiedSpec
        neo_spaz_pelvis: MeshVerifiedSpec
        neo_spaz_toes: MeshVerifiedSpec
        neo_spaz_torso: MeshVerifiedSpec
        neo_spaz_upper_arm: MeshVerifiedSpec
        neo_spaz_upper_leg: MeshVerifiedSpec
        ninja_fore_arm: MeshVerifiedSpec
        ninja_hand: MeshVerifiedSpec
        ninja_head: MeshVerifiedSpec
        ninja_lower_leg: MeshVerifiedSpec
        ninja_pelvis: MeshVerifiedSpec
        ninja_toes: MeshVerifiedSpec
        ninja_torso: MeshVerifiedSpec
        ninja_upper_arm: MeshVerifiedSpec
        ninja_upper_leg: MeshVerifiedSpec
        old_lady_fore_arm: MeshVerifiedSpec
        old_lady_hand: MeshVerifiedSpec
        old_lady_head: MeshVerifiedSpec
        old_lady_lower_leg: MeshVerifiedSpec
        old_lady_pelvis: MeshVerifiedSpec
        old_lady_toes: MeshVerifiedSpec
        old_lady_torso: MeshVerifiedSpec
        old_lady_upper_arm: MeshVerifiedSpec
        old_lady_upper_leg: MeshVerifiedSpec
        opera_singer_fore_arm: MeshVerifiedSpec
        opera_singer_hand: MeshVerifiedSpec
        opera_singer_head: MeshVerifiedSpec
        opera_singer_lower_leg: MeshVerifiedSpec
        opera_singer_pelvis: MeshVerifiedSpec
        opera_singer_toes: MeshVerifiedSpec
        opera_singer_torso: MeshVerifiedSpec
        opera_singer_upper_arm: MeshVerifiedSpec
        opera_singer_upper_leg: MeshVerifiedSpec
        penguin_fore_arm: MeshVerifiedSpec
        penguin_hand: MeshVerifiedSpec
        penguin_head: MeshVerifiedSpec
        penguin_lower_leg: MeshVerifiedSpec
        penguin_pelvis: MeshVerifiedSpec
        penguin_toes: MeshVerifiedSpec
        penguin_torso: MeshVerifiedSpec
        penguin_upper_arm: MeshVerifiedSpec
        penguin_upper_leg: MeshVerifiedSpec
        pixie_fore_arm: MeshVerifiedSpec
        pixie_hand: MeshVerifiedSpec
        pixie_head: MeshVerifiedSpec
        pixie_lower_leg: MeshVerifiedSpec
        pixie_pelvis: MeshVerifiedSpec
        pixie_toes: MeshVerifiedSpec
        pixie_torso: MeshVerifiedSpec
        pixie_upper_arm: MeshVerifiedSpec
        pixie_upper_leg: MeshVerifiedSpec
        plastic_eyes_transparent: MeshVerifiedSpec
        player_lineup1_transparent: MeshVerifiedSpec
        player_lineup2_transparent: MeshVerifiedSpec
        player_lineup3_transparent: MeshVerifiedSpec
        player_lineup4_transparent: MeshVerifiedSpec
        powerup: MeshVerifiedSpec
        powerup_simple: MeshVerifiedSpec
        puck: MeshVerifiedSpec
        rampage_bg: MeshVerifiedSpec
        rampage_bg2: MeshVerifiedSpec
        rampage_level: MeshVerifiedSpec
        rampage_level_bottom: MeshVerifiedSpec
        rampage_vrfill: MeshVerifiedSpec
        robot_fore_arm: MeshVerifiedSpec
        robot_hand: MeshVerifiedSpec
        robot_head: MeshVerifiedSpec
        robot_lower_leg: MeshVerifiedSpec
        robot_pelvis: MeshVerifiedSpec
        robot_toes: MeshVerifiedSpec
        robot_torso: MeshVerifiedSpec
        robot_upper_arm: MeshVerifiedSpec
        robot_upper_leg: MeshVerifiedSpec
        roundabout_level: MeshVerifiedSpec
        roundabout_level_bottom: MeshVerifiedSpec
        running_shoes: MeshVerifiedSpec
        santa_fore_arm: MeshVerifiedSpec
        santa_hand: MeshVerifiedSpec
        santa_head: MeshVerifiedSpec
        santa_lower_leg: MeshVerifiedSpec
        santa_toes: MeshVerifiedSpec
        santa_torso: MeshVerifiedSpec
        santa_upper_arm: MeshVerifiedSpec
        santa_upper_leg: MeshVerifiedSpec
        scroll_widget_short: MeshVerifiedSpec
        step_right_up_level: MeshVerifiedSpec
        step_right_up_level_bottom: MeshVerifiedSpec
        step_right_up_vrfill_mound: MeshVerifiedSpec
        superhero_fore_arm: MeshVerifiedSpec
        superhero_hand: MeshVerifiedSpec
        superhero_head: MeshVerifiedSpec
        superhero_lower_leg: MeshVerifiedSpec
        superhero_pelvis: MeshVerifiedSpec
        superhero_toes: MeshVerifiedSpec
        superhero_torso: MeshVerifiedSpec
        superhero_upper_arm: MeshVerifiedSpec
        superhero_upper_leg: MeshVerifiedSpec
        the_pad_bg: MeshVerifiedSpec
        the_pad_bgsmall: MeshVerifiedSpec
        the_pad_level: MeshVerifiedSpec
        the_pad_level_bottom: MeshVerifiedSpec
        the_pad_vrfill_bottom: MeshVerifiedSpec
        the_pad_vrfill_mound: MeshVerifiedSpec
        the_pad_vrfill_top: MeshVerifiedSpec
        tip_top_bg: MeshVerifiedSpec
        tip_top_level: MeshVerifiedSpec
        tip_top_level_bottom: MeshVerifiedSpec
        tnt: MeshVerifiedSpec
        toolbar_backing: MeshVerifiedSpec
        toolbar_backing_bottom: MeshVerifiedSpec
        toolbar_backing_bottom2: MeshVerifiedSpec
        toolbar_backing_opaque: MeshVerifiedSpec
        toolbar_backing_top: MeshVerifiedSpec
        toolbar_backing_top2: MeshVerifiedSpec
        toolbar_backing_transparent: MeshVerifiedSpec
        tower_dlevel: MeshVerifiedSpec
        tower_dlevel_bottom: MeshVerifiedSpec
        trees: MeshVerifiedSpec
        warrior_fore_arm: MeshVerifiedSpec
        warrior_hand: MeshVerifiedSpec
        warrior_head: MeshVerifiedSpec
        warrior_lower_leg: MeshVerifiedSpec
        warrior_pelvis: MeshVerifiedSpec
        warrior_toes: MeshVerifiedSpec
        warrior_torso: MeshVerifiedSpec
        warrior_upper_arm: MeshVerifiedSpec
        warrior_upper_leg: MeshVerifiedSpec
        window_bgblotch: MeshVerifiedSpec
        witch_fore_arm: MeshVerifiedSpec
        witch_hand: MeshVerifiedSpec
        witch_head: MeshVerifiedSpec
        witch_lower_leg: MeshVerifiedSpec
        witch_pelvis: MeshVerifiedSpec
        witch_toes: MeshVerifiedSpec
        witch_torso: MeshVerifiedSpec
        witch_upper_arm: MeshVerifiedSpec
        witch_upper_leg: MeshVerifiedSpec
        wizard_fore_arm: MeshVerifiedSpec
        wizard_hand: MeshVerifiedSpec
        wizard_head: MeshVerifiedSpec
        wizard_lower_leg: MeshVerifiedSpec
        wizard_pelvis: MeshVerifiedSpec
        wizard_toes: MeshVerifiedSpec
        wizard_torso: MeshVerifiedSpec
        wizard_upper_arm: MeshVerifiedSpec
        wizard_upper_leg: MeshVerifiedSpec
        wrestler_fore_arm: MeshVerifiedSpec
        wrestler_hand: MeshVerifiedSpec
        wrestler_head: MeshVerifiedSpec
        wrestler_lower_leg: MeshVerifiedSpec
        wrestler_pelvis: MeshVerifiedSpec
        wrestler_toes: MeshVerifiedSpec
        wrestler_torso: MeshVerifiedSpec
        wrestler_upper_arm: MeshVerifiedSpec
        wrestler_upper_leg: MeshVerifiedSpec
        zig_zag_level: MeshVerifiedSpec
        zig_zag_level_bottom: MeshVerifiedSpec
        zoe_fore_arm: MeshVerifiedSpec
        zoe_hand: MeshVerifiedSpec
        zoe_head: MeshVerifiedSpec
        zoe_lower_leg: MeshVerifiedSpec
        zoe_pelvis: MeshVerifiedSpec
        zoe_toes: MeshVerifiedSpec
        zoe_torso: MeshVerifiedSpec
        zoe_upper_arm: MeshVerifiedSpec
        zoe_upper_leg: MeshVerifiedSpec

    class StringsAccountGroup:
        """
        ::

            Account-management UI: sign-in/out, account creation/linking,
            progress display, and the player-info viewer.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Heading for a list of linked accounts.
        #:
        #:     English: "Accounts"
        accounts: LangStr

        def achievement_progress(
            self, *, complete: str | LangStr, total: str | LangStr
        ) -> LangStr:
            """
            ::

                Display of achievement completion (N out of M).

                English: "Achievements: {complete} of {total}"
            """

        #: ::
        #:
        #:     Button to ban the viewed player (admin/host action).
        #:
        #:     English: "Ban This Player"
        ban_this_player: LangStr

        def campaign_progress(self, *, progress: str | LangStr) -> LangStr:
            """
            ::

                Display of hard-mode campaign completion percentage.

                English: "Campaign (Hard): {progress}"
            """

        #: ::
        #:
        #:     Button to create a new account.
        #:
        #:     English: "Create an Account"
        create_an_account: LangStr

        #: ::
        #:
        #:     Button to delete the account.
        #:
        #:     English: "Delete Account"
        delete_account: LangStr

        #: ::
        #:
        #:     Instructions for switching Google accounts.
        #:
        #:     English: "If you want to use a different Google account, use the
        #:     Google Play Games app to switch."
        google_play_games_account_switch: LangStr

        #: ::
        #:
        #:     Button to manage account settings on the web.
        #:
        #:     English: "Manage Account"
        manage_account: LangStr

        #: ::
        #:
        #:     Error shown when an action requires sign-in.
        #:
        #:     English: "You must sign in to do this."
        not_signed_in: LangStr

        #: ::
        #:
        #:     Title of the player-info viewer popup.
        #:
        #:     English: "Player Info"
        player_info: LangStr

        #: ::
        #:
        #:     Button to report the viewed player.
        #:
        #:     English: "Report This Player"
        report_this_player: LangStr

        #: ::
        #:
        #:     Sign-in button label.
        #:
        #:     English: "Sign In"
        sign_in: LangStr

        #: ::
        #:
        #:     Notice that codes require being signed in.
        #:
        #:     English: "You must sign in to an account for codes to take
        #:     effect."
        sign_in_for_codes: LangStr

        #: ::
        #:
        #:     Blurb explaining the benefits of signing in.
        #:
        #:     English: "Sign in to collect Tickets, compete online, and share
        #:     progress across devices."
        sign_in_info: LangStr

        #: ::
        #:
        #:     Error when sign-in fails, likely due to no internet.
        #:
        #:     English: "Unable to sign in. (no internet connection?)"
        sign_in_no_connection: LangStr

        def sign_in_with(self, *, service: str | LangStr) -> LangStr:
            """
            ::

                Sign-in button label naming a specific service.

                English: "Sign In with {service}"
            """

        #: ::
        #:
        #:     Button to sign in with the automatic device-local account.
        #:
        #:     English: "Sign In with Device Account"
        sign_in_with_device: LangStr

        #: ::
        #:
        #:     Explanation under the device-account sign-in button.
        #:
        #:     English: "(an automatic account only available from this device)"
        sign_in_with_device_info: LangStr

        #: ::
        #:
        #:     Button to sign in via an email address.
        #:
        #:     English: "Sign In with an Email Address"
        sign_in_with_email: LangStr

        #: ::
        #:
        #:     Sign-out button label.
        #:
        #:     English: "Sign Out"
        sign_out: LangStr

        #: ::
        #:
        #:     Status shown while signing in.
        #:
        #:     English: "Signing in..."
        signing_in: LangStr

        #: ::
        #:
        #:     Status shown while signing out.
        #:
        #:     English: "Signing out..."
        signing_out: LangStr

        #: ::
        #:
        #:     Status message while a code is being submitted.
        #:
        #:     English: "Submitting Code..."
        submitting_code: LangStr

        def tickets(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                Display of the ticket balance.

                English: "Tickets: {count}"
            """

        #: ::
        #:
        #:     Title of the account section/window; also labels account buttons.
        #:
        #:     English: "Account"
        title: LangStr

        #: ::
        #:
        #:     Heading for trophies earned this season.
        #:
        #:     English: "Trophies This Season"
        trophies_this_season: LangStr

        #: ::
        #:
        #:     Instruction shown with a web link for creating or signing in to
        #:     an account.
        #:
        #:     English: "Use this link to create an account or sign in."
        v2_link_instructions: LangStr

        #: ::
        #:
        #:     Label above the signed-in account name.
        #:
        #:     English: "You are signed in as:"
        you_are_signed_in_as: LangStr

    class StringsAchievementsBoomGoesTheDynamiteGroup:
        """
        ::

            Strings for the "Boom Goes the Dynamite" achievement: its name and
            its descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Pro Onslaught".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Kill 3 bad guys with TNT"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Killed 3 bad guys with TNT"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete all objectives on {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level}"
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Boom Goes the Dynamite"
        name: LangStr

    class StringsAchievementsBoxerGroup:
        """
        ::

            Strings for the "Boxer" achievement: its name and its descriptions
            (short/full, unearned/earned). It is earned on the campaign level
            "Onslaught Training".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Win without using any bombs"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Won without using any bombs"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete {level} without using any bombs."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level} without using any bombs"
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Boxer"
        name: LangStr

    class StringsAchievementsDualWieldingGroup:
        """
        ::

            Strings for the "Dual Wielding" achievement: its name and its
            descriptions (short/full, unearned/earned).

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Full description of what an achievement requires, naming the
        #:     campaign level it applies to.
        #:
        #:     English: "Connect 2 controllers (hardware or app)"
        description_full: LangStr

        #: ::
        #:
        #:     Full description of an achievement the player has already earned,
        #:     naming the campaign level (past tense).
        #:
        #:     English: "Connected 2 controllers (hardware or app)"
        description_full_complete: LangStr

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Dual Wielding"
        name: LangStr

    class StringsAchievementsFlawlessVictoryGroup:
        """
        ::

            Strings for the "Flawless Victory" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Rookie Onslaught".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Win without getting hit"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Won without getting hit"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Win {level} without getting hit."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Won {level} without getting hit."
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Flawless Victory"
        name: LangStr

    class StringsAchievementsFreeLoaderGroup:
        """
        ::

            Strings for the "Free Loader" achievement: its name and its
            descriptions (short/full, unearned/earned).

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Full description of what an achievement requires, naming the
        #:     campaign level it applies to.
        #:
        #:     English: "Start a Free-For-All game with 2+ players"
        description_full: LangStr

        #: ::
        #:
        #:     Full description of an achievement the player has already earned,
        #:     naming the campaign level (past tense).
        #:
        #:     English: "Started a Free-For-All game with 2+ players"
        description_full_complete: LangStr

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Free Loader"
        name: LangStr

    class StringsAchievementsGoldMinerGroup:
        """
        ::

            Strings for the "Gold Miner" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Uber Onslaught".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Kill 6 bad guys with land-mines"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Killed 6 bad guys with land-mines"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Kill 6 enemies with landmines on {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Killed 6 bad guys with land-mines on {level}"
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Gold Miner"
        name: LangStr

    class StringsAchievementsGotTheMovesGroup:
        """
        ::

            Strings for the "Got the Moves" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Uber Football".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Win without using punches or bombs"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Won without using punches or bombs"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Win {level} without any punches or bombs."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Won {level} without any punches or bombs"
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Got the Moves"
        name: LangStr

    class StringsAchievementsInControlGroup:
        """
        ::

            Strings for the "In Control" achievement: its name and its
            descriptions (short/full, unearned/earned).

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Full description of what an achievement requires, naming the
        #:     campaign level it applies to.
        #:
        #:     English: "Connect a controller (hardware or app)"
        description_full: LangStr

        #: ::
        #:
        #:     Full description of an achievement the player has already earned,
        #:     naming the campaign level (past tense).
        #:
        #:     English: "Connected a controller. (hardware or app)"
        description_full_complete: LangStr

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "In Control"
        name: LangStr

    class StringsAchievementsLastStandGodGroup:
        """
        ::

            Strings for the "Last Stand God" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "The Last Stand".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Score 1000 points"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Scored 1000 points"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete the mission on {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level}."
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} God"
            """

    class StringsAchievementsLastStandMasterGroup:
        """
        ::

            Strings for the "Last Stand Master" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "The Last Stand".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Score 250 points"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Scored 250 points"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete all objectives on {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level}."
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Master"
            """

    class StringsAchievementsLastStandWizardGroup:
        """
        ::

            Strings for the "Last Stand Wizard" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "The Last Stand".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Score 500 points"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Scored 500 points"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete {level} to unlock this achievement."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level}."
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Champion"
            """

    class StringsAchievementsMineGamesGroup:
        """
        ::

            Strings for the "Mine Games" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Rookie Onslaught".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Kill 3 bad guys with land-mines"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Killed 3 bad guys with land-mines"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Kill 3 bad guys with land-mines on {level}"
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed all objectives on {level}."
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Mine Games"
        name: LangStr

    class StringsAchievementsOffYouGoThenGroup:
        """
        ::

            Strings for the "Off You Go Then" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Onslaught Training".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Toss 3 bad guys off the map"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Tossed 3 bad guys off the map"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete all objectives in {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Tossed 3 bad guys off the map in {level}"
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Off You Go Then"
        name: LangStr

    class StringsAchievementsOnslaughtGodGroup:
        """
        ::

            Strings for the "Onslaught God" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Infinite Onslaught".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Score 5000 points"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Scored 5000 points"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete all objectives on {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level}"
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} God"
            """

    class StringsAchievementsOnslaughtMasterGroup:
        """
        ::

            Strings for the "Onslaught Master" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Infinite Onslaught".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Score 500 points"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Scored 500 points"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete all objectives on {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level}"
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Master"
            """

    class StringsAchievementsOnslaughtTrainingVictoryGroup:
        """
        ::

            Strings for the "Onslaught Training Victory" achievement: its name
            and its descriptions (short/full, unearned/earned). It is earned on
            the campaign level "Onslaught Training".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Defeat all waves"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Defeated all waves"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Defeat all waves in {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Defeated all waves in {level}."
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Victory"
            """

    class StringsAchievementsOnslaughtWizardGroup:
        """
        ::

            Strings for the "Onslaught Wizard" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Infinite Onslaught".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Score 1000 points"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Scored 1000 points"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete all objectives in {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level}."
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Master"
            """

    class StringsAchievementsPrecisionBombingGroup:
        """
        ::

            Strings for the "Precision Bombing" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Pro Runaround".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Win without any powerups"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Won without any powerups"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Win {level} without using any power-ups."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Won {level} without any power-ups."
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Precision Bombing"
        name: LangStr

    class StringsAchievementsProBoxerGroup:
        """
        ::

            Strings for the "Pro Boxer" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Pro Onslaught".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Win without using any bombs"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Won without using any bombs"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete {level} without using any bombs."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level} without using any bombs"
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Pro Boxer"
        name: LangStr

    class StringsAchievementsProFootballShutoutGroup:
        """
        ::

            Strings for the "Pro Football Shutout" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Pro Football".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Win without letting the bad guys score"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Won without letting the bad guys score"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete {level} without taking any damage."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level} without letting the opponent score."
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Shutout"
            """

    class StringsAchievementsProFootballVictoryGroup:
        """
        ::

            Strings for the "Pro Football Victory" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Pro Football".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Win the game"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Won the game"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Win the game in {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level}."
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Victory"
            """

    class StringsAchievementsProOnslaughtVictoryGroup:
        """
        ::

            Strings for the "Pro Onslaught Victory" achievement: its name and
            its descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Pro Onslaught".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Defeat all waves"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Defeated all waves"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Defeat all waves of {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Defeated all waves of {level}"
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Victory"
            """

    class StringsAchievementsProRunaroundVictoryGroup:
        """
        ::

            Strings for the "Pro Runaround Victory" achievement: its name and
            its descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Pro Runaround".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Complete all waves"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Completed all waves"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete all waves on {level}"
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed all waves on {level}"
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Victory"
            """

    class StringsAchievementsRookieFootballShutoutGroup:
        """
        ::

            Strings for the "Rookie Football Shutout" achievement: its name and
            its descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Rookie Football".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Win without letting the bad guys score"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Won without letting the bad guys score"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Win {level} without letting the opponent score."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level}."
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Shutout"
            """

    class StringsAchievementsRookieFootballVictoryGroup:
        """
        ::

            Strings for the "Rookie Football Victory" achievement: its name and
            its descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Rookie Football".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Win the game"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Won the game"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Win the game in {level}"
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed the campaign on {level}."
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Victory"
            """

    class StringsAchievementsRookieOnslaughtVictoryGroup:
        """
        ::

            Strings for the "Rookie Onslaught Victory" achievement: its name and
            its descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Rookie Onslaught".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Defeat all waves"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Defeated all waves"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Defeat all waves in {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Defeated all waves in {level}."
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Victory"
            """

    class StringsAchievementsRunaroundGodGroup:
        """
        ::

            Strings for the "Runaround God" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Infinite Runaround".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Score 2000 points"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Scored 2000 points"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete all objectives on {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level}"
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} God"
            """

    class StringsAchievementsRunaroundMasterGroup:
        """
        ::

            Strings for the "Runaround Master" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Infinite Runaround".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Score 500 points"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Scored 500 points"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete all objectives in {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level}"
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Master"
            """

    class StringsAchievementsRunaroundWizardGroup:
        """
        ::

            Strings for the "Runaround Wizard" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Infinite Runaround".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Score 1000 points"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Scored 1000 points"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete the objective on {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Scored 1000 points on {level}"
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "Champion of {level}"
            """

    class StringsAchievementsSharingIsCaringGroup:
        """
        ::

            Strings for the "Sharing is Caring" achievement: its name and its
            descriptions (short/full, unearned/earned).

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Full description of what an achievement requires, naming the
        #:     campaign level it applies to.
        #:
        #:     English: "Successfully share the game with a friend"
        description_full: LangStr

        #: ::
        #:
        #:     Full description of an achievement the player has already earned,
        #:     naming the campaign level (past tense).
        #:
        #:     English: "Successfully shared the game with a friend"
        description_full_complete: LangStr

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Sharing is Caring"
        name: LangStr

    class StringsAchievementsStayinAliveGroup:
        """
        ::

            Strings for the "Stayin' Alive" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Uber Runaround".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Win without dying"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Won without dying"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Win {level} without dying."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Won {level} without dying"
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Stayin' Alive"
        name: LangStr

    class StringsAchievementsSuperMegaPunchGroup:
        """
        ::

            Strings for the "Super Mega Punch" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Pro Football".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Inflict 100% damage with one punch"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Inflicted 100% damage with one punch"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Inflict 100% damage with one punch in {level}"
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level}"
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Super Mega Punch"
        name: LangStr

    class StringsAchievementsSuperPunchGroup:
        """
        ::

            Strings for the "Super Punch" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Rookie Football".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Inflict 50% damage with one punch"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Inflicted 50% damage with one punch"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete {level} without taking any damage."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Inflicted 50% damage with one punch on {level}"
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Super Punch"
        name: LangStr

    class StringsAchievementsTeamPlayerGroup:
        """
        ::

            Strings for the "Team Player" achievement: its name and its
            descriptions (short/full, unearned/earned).

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Full description of what an achievement requires, naming the
        #:     campaign level it applies to.
        #:
        #:     English: "Start a Teams game with 4+ players"
        description_full: LangStr

        #: ::
        #:
        #:     Full description of an achievement the player has already earned,
        #:     naming the campaign level (past tense).
        #:
        #:     English: "Started a Teams game with 4+ players"
        description_full_complete: LangStr

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "Team Player"
        name: LangStr

    class StringsAchievementsTheGreatWallGroup:
        """
        ::

            Strings for the "The Great Wall" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Uber Runaround".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Stop every single bad guy"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Stopped every single bad guy"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete all objectives in {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Stopped every single bad guy on {level}."
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "The Great Wall"
        name: LangStr

    class StringsAchievementsTheWallGroup:
        """
        ::

            Strings for the "The Wall" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Pro Runaround".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Stop every single bad guy"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Stopped every single bad guy"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Stop every single bad guy on {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Stopped every single bad guy on {level}"
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "The Wall"
        name: LangStr

    class StringsAchievementsTntTerrorGroup:
        """
        ::

            Strings for the "TNT Terror" achievement: its name and its
            descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Uber Onslaught".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Kill 6 bad guys with TNT"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Killed 6 bad guys with TNT"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Kill 6 enemies with TNT on {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Killed 6 bad guys with TNT on {level}"
            """

        #: ::
        #:
        #:     Name of an achievement the player can earn.
        #:
        #:     English: "TNT Terror"
        name: LangStr

    class StringsAchievementsUberFootballShutoutGroup:
        """
        ::

            Strings for the "Uber Football Shutout" achievement: its name and
            its descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Uber Football".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Win without letting the bad guys score"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Won without letting the bad guys score"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete {level} without taking any damage."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed {level}."
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Shutout"
            """

    class StringsAchievementsUberFootballVictoryGroup:
        """
        ::

            Strings for the "Uber Football Victory" achievement: its name and
            its descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Uber Football".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Win the game"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Won the game"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Win the game in {level}."
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Won the game in {level}"
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Victory"
            """

    class StringsAchievementsUberOnslaughtVictoryGroup:
        """
        ::

            Strings for the "Uber Onslaught Victory" achievement: its name and
            its descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Uber Onslaught".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Defeat all waves"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Defeated all waves"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Defeat all waves in {level}"
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Defeated all waves in {level}"
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Victory"
            """

    class StringsAchievementsUberRunaroundVictoryGroup:
        """
        ::

            Strings for the "Uber Runaround Victory" achievement: its name and
            its descriptions (short/full, unearned/earned). It is earned on the
            campaign level "Uber Runaround".

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Short description of what an achievement requires, shown before
        #:     it is earned.
        #:
        #:     English: "Complete all waves"
        description: LangStr

        #: ::
        #:
        #:     Short description of an achievement the player has already earned
        #:     (past tense).
        #:
        #:     English: "Completed all waves"
        description_complete: LangStr

        def description_full(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of what an achievement requires, naming the
                campaign level it applies to.

                English: "Complete all waves on {level}"
            """

        def description_full_complete(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Full description of an achievement the player has already
                earned, naming the campaign level (past tense).

                English: "Completed all waves on {level}"
            """

        def name(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Name of an achievement the player can earn.

                English: "{level} Victory"
            """

    class StringsAchievementsGroup:
        """
        ::

            Achievement strings: the name of each co-op campaign achievement
            plus its short and full descriptions, in both unearned and earned
            (past-tense) forms.

            See source for the full asset list.
        """

        boom_goes_the_dynamite: StringsAchievementsBoomGoesTheDynamiteGroup
        boxer: StringsAchievementsBoxerGroup
        dual_wielding: StringsAchievementsDualWieldingGroup
        flawless_victory: StringsAchievementsFlawlessVictoryGroup
        free_loader: StringsAchievementsFreeLoaderGroup
        gold_miner: StringsAchievementsGoldMinerGroup
        got_the_moves: StringsAchievementsGotTheMovesGroup
        in_control: StringsAchievementsInControlGroup
        last_stand_god: StringsAchievementsLastStandGodGroup
        last_stand_master: StringsAchievementsLastStandMasterGroup
        last_stand_wizard: StringsAchievementsLastStandWizardGroup
        mine_games: StringsAchievementsMineGamesGroup
        off_you_go_then: StringsAchievementsOffYouGoThenGroup
        onslaught_god: StringsAchievementsOnslaughtGodGroup
        onslaught_master: StringsAchievementsOnslaughtMasterGroup
        onslaught_training_victory: (
            StringsAchievementsOnslaughtTrainingVictoryGroup
        )
        onslaught_wizard: StringsAchievementsOnslaughtWizardGroup
        precision_bombing: StringsAchievementsPrecisionBombingGroup
        pro_boxer: StringsAchievementsProBoxerGroup
        pro_football_shutout: StringsAchievementsProFootballShutoutGroup
        pro_football_victory: StringsAchievementsProFootballVictoryGroup
        pro_onslaught_victory: StringsAchievementsProOnslaughtVictoryGroup
        pro_runaround_victory: StringsAchievementsProRunaroundVictoryGroup
        rookie_football_shutout: StringsAchievementsRookieFootballShutoutGroup
        rookie_football_victory: StringsAchievementsRookieFootballVictoryGroup
        rookie_onslaught_victory: StringsAchievementsRookieOnslaughtVictoryGroup
        runaround_god: StringsAchievementsRunaroundGodGroup
        runaround_master: StringsAchievementsRunaroundMasterGroup
        runaround_wizard: StringsAchievementsRunaroundWizardGroup
        sharing_is_caring: StringsAchievementsSharingIsCaringGroup
        stayin_alive: StringsAchievementsStayinAliveGroup
        super_mega_punch: StringsAchievementsSuperMegaPunchGroup
        super_punch: StringsAchievementsSuperPunchGroup
        team_player: StringsAchievementsTeamPlayerGroup
        the_great_wall: StringsAchievementsTheGreatWallGroup
        the_wall: StringsAchievementsTheWallGroup
        tnt_terror: StringsAchievementsTntTerrorGroup
        uber_football_shutout: StringsAchievementsUberFootballShutoutGroup
        uber_football_victory: StringsAchievementsUberFootballVictoryGroup
        uber_onslaught_victory: StringsAchievementsUberOnslaughtVictoryGroup
        uber_runaround_victory: StringsAchievementsUberRunaroundVictoryGroup

    class StringsAppInviteGroup:
        """
        ::

            Friend-invite / promo-code sharing flow.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Button to email an invite code.
        #:
        #:     English: "Email It"
        email_it: LangStr

        #: ::
        #:
        #:     Cheerful "Enjoy!" message.
        #:
        #:     English: "ENJOY!"
        enjoy: LangStr

        def friend_has_sent_promo(
            self, *, count: int, app_name: str | LangStr, name: str | LangStr
        ) -> LangStr:
            """
            ::

                Header naming a ticket gift from a friend.

                English: (one) "# {app_name} Ticket from {name}" / (other) "#
                {app_name} Tickets from {name}"
            """

        def friend_promo_award(self, *, count: int) -> LangStr:
            """
            ::

                Explanation of the ticket reward per redemption.

                English: (one) "You will receive # Ticket each time it is used."
                / (other) "You will receive # Tickets each time it is used."
            """

        def friend_promo_expire(self, *, expire_hours: int) -> LangStr:
            """
            ::

                Notice of code expiry for new players only.

                English: (one) "The code will expire in # hour and only works
                for new players." / (other) "The code will expire in # hours and
                only works for new players."
            """

        def friend_promo_instructions(
            self, *, app_name: str | LangStr
        ) -> LangStr:
            """
            ::

                How to redeem the promo code.

                English: "To use it, open {app_name} and go to
                "Settings->Advanced->Send Info". See bombsquadgame.com for
                download links for all supported platforms."
            """

        def friend_promo_redeem_long(
            self, *, count: int, max_uses: str | LangStr
        ) -> LangStr:
            """
            ::

                How many free tickets a promo code grants and to how many
                people.

                English: (one) "It can be redeemed for # free ticket by up to
                {max_uses} people." / (other) "It can be redeemed for # free
                tickets by up to {max_uses} people."
            """

        def friend_promo_redeem_short(self, *, count: int) -> LangStr:
            """
            ::

                Short note of ticket value for a code.

                English: (one) "It can be redeemed for # Ticket in the game." /
                (other) "It can be redeemed for # Tickets in the game."
            """

        #: ::
        #:
        #:     Status while requesting a promo code.
        #:
        #:     English: "Requesting a code..."
        requesting_code: LangStr

        #: ::
        #:
        #:     Instruction to share a promo code.
        #:
        #:     English: "Share this code with friends:"
        share_code: LangStr

        #: ::
        #:
        #:     Parenthetical pointer to where a promo code is entered.
        #:
        #:     English: "(in "Settings->Advanced->Send Info")"
        where_to_enter: LangStr

        def you_have_been_sent_promo(
            self, *, app_name: str | LangStr
        ) -> LangStr:
            """
            ::

                Notice that the player got a promo code.

                English: "You have been sent a {app_name} promo code:"
            """

    class StringsCharactersGroup:
        """
        ::

            Playable character display names. Mods can register their own
            characters; those names are shown untranslated.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Translate the "Agent" title;
        #:     keep/transliterate "Johnson".
        #:
        #:     English: "Agent Johnson"
        agent_johnson: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Robot designation: keep as "B-9000"
        #:     (transliterate letters/digits only where the script requires).
        #:
        #:     English: "B-9000"
        b9000: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Invented proper name: keep verbatim in
        #:     Latin-script locales; transliterate phonetically in non-Latin
        #:     scripts. Established legacy renames in some locales are
        #:     intentional and were seeded.
        #:
        #:     English: "Bernard"
        bernard: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. A warm, familiar granny-ish given name:
        #:     keep/adapt "Betty" or use an equivalent common local name.
        #:
        #:     English: "Betty"
        betty: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Meaningful nickname: playful
        #:     diminutive/pet-name forms for "bones/skeleton" work well.
        #:
        #:     English: "Bones"
        bones: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. playful given name; transliterate
        #:     phonetically in non-Latin scripts, or keep an established
        #:     cowboy-flavored rename.
        #:
        #:     English: "Butch"
        butch: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Use each culture's standard
        #:     Easter-bunny term.
        #:
        #:     English: "Easter Bunny"
        easter_bunny: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Meaningful name: a frosty/snowy
        #:     name-like form (playful beats a generic "snowman" where a natural
        #:     option exists).
        #:
        #:     English: "Frosty"
        frosty: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. invented proper name; transliterate
        #:     phonetically in non-Latin scripts.
        #:
        #:     English: "Gretel"
        gretel: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Invented wizardly pun name: "grumble" +
        #:     a Gandalf/Dumbledore-style suffix. A local grumble-pun in the
        #:     same shape is ideal; otherwise transliterate. Never a generic
        #:     "wizard" word alone, and never an actual name from other fiction.
        #:
        #:     English: "Grumbledorf"
        grumbledorf: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Invented proper name: keep verbatim in
        #:     Latin-script locales; transliterate phonetically in non-Latin
        #:     scripts. Established legacy renames in some locales are
        #:     intentional and were seeded. Use local name order conventions.
        #:
        #:     English: "Jack Morgan"
        jack_morgan: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Invented proper name: keep verbatim in
        #:     Latin-script locales; transliterate phonetically in non-Latin
        #:     scripts. Established legacy renames in some locales are
        #:     intentional and were seeded.
        #:
        #:     English: "Kronk"
        kronk: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. short proper name; transliterate
        #:     phonetically in non-Latin scripts.
        #:
        #:     English: "Lee"
        lee: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Meaningful name ("fortunate"):
        #:     translate the meaning as a name-like form.
        #:
        #:     English: "Lucky"
        lucky: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Invented proper name: keep verbatim in
        #:     Latin-script locales; transliterate phonetically in non-Latin
        #:     scripts. Established legacy renames in some locales are
        #:     intentional and were seeded.
        #:
        #:     English: "Mel"
        mel: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. a compound nickname meaning a neutral
        #:     intermediary; a fitting localized equivalent works well.
        #:
        #:     English: "Middle-Man"
        middle_man: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Invented proper name: keep verbatim in
        #:     Latin-script locales; transliterate phonetically in non-Latin
        #:     scripts. Established legacy renames in some locales are
        #:     intentional and were seeded.
        #:
        #:     English: "Pascal"
        pascal: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. English puns pixel/pixie. Either keep
        #:     "Pixel" (transliterated as needed) or use a fairy/sprite word
        #:     that lands a similar double meaning.
        #:
        #:     English: "Pixel"
        pixel: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Use each culture's traditional
        #:     gift-bringer name.
        #:
        #:     English: "Santa Claus"
        santa_claus: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Descriptive name: translate the meaning
        #:     (snake + shadow, ninja-flavored).
        #:
        #:     English: "Snake Shadow"
        snake_shadow: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. the default character and series
        #:     mascot; transliterate phonetically, or keep an established
        #:     playful rename.
        #:
        #:     English: "Spaz"
        spaz: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Chinese locales use the official mascot
        #:     name 淘公仔; others translate "Taobao Mascot" ("Taobao" stays as the
        #:     brand).
        #:
        #:     English: "Taobao Mascot"
        taobao_mascot: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. invented proper name; transliterate
        #:     phonetically in non-Latin scripts.
        #:
        #:     English: "Todd McBurton"
        todd_mcburton: LangStr

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Invented proper name: keep verbatim in
        #:     Latin-script locales; transliterate phonetically in non-Latin
        #:     scripts. Established legacy renames in some locales are
        #:     intentional and were seeded.
        #:
        #:     English: "Zoe"
        zoe: LangStr

    class StringsChestGroup:
        """
        ::

            Chest window: open/reduce-wait controls, slot descriptions, and
            prize odds.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Button to open a chest.
        #:
        #:     English: "Open"
        open: LangStr

        #: ::
        #:
        #:     Playful prompt on an openable chest.
        #:
        #:     English: "OPEN ME!"
        open_me: LangStr

        #: ::
        #:
        #:     Button to open a chest immediately.
        #:
        #:     English: "Open Now"
        open_now: LangStr

        #: ::
        #:
        #:     Note that the player can open a chest early.
        #:
        #:     English: "You have enough Tokens to open this now - you don't
        #:     need to wait."
        open_now_description: LangStr

        #: ::
        #:
        #:     Heading for the prize-odds view.
        #:
        #:     English: "Prize Odds"
        prize_odds: LangStr

        #: ::
        #:
        #:     Button to reduce the wait time.
        #:
        #:     English: "Reduce Wait"
        reduce_wait: LangStr

        #: ::
        #:
        #:     Explanation of what a chest slot holds.
        #:
        #:     English: "This slot can hold a chest. Earn chests by playing
        #:     campaign levels, placing in tournaments, and completing
        #:     achievements."
        slot_description: LangStr

        def slot_number(self, *, num: str | LangStr) -> LangStr:
            """
            ::

                Label naming a numbered chest slot.

                English: "Chest Slot {num}"
            """

        #: ::
        #:
        #:     Button to stop open-chest reminders.
        #:
        #:     English: "Stop Reminding Me"
        stop_reminding_me: LangStr

        #: ::
        #:
        #:     Label for the time until a chest unlocks.
        #:
        #:     English: "Unlocks In"
        unlocks_in: LangStr

    class StringsControlsGroup:
        """
        ::

            On-screen control guidance shown during play: button hints and
            input-hardware suggestions.

            See source for the full asset list.
        """

        def fire_tv_remote_warning(
            self, *, remote_app_name: str | LangStr
        ) -> LangStr:
            """
            ::

                Suggestion to use a controller or the remote app.

                English: "For a better experience, use a controller or install
                {remote_app_name} on your phone or tablet."
            """

        #: ::
        #:
        #:     Label for the movement control in the controls guide.
        #:
        #:     English: "Move"
        move: LangStr

        def move_directions(
            self,
            *,
            up: str | LangStr,
            left: str | LangStr,
            down: str | LangStr,
            right: str | LangStr,
        ) -> LangStr:
            """
            ::

                On-screen controls guide line listing the four movement
                keys/buttons; the placeholders are key/button names.

                English: "Move: {up}, {left}, {down}, {right}"
            """

        #: ::
        #:
        #:     Label for the run control in the controls guide.
        #:
        #:     English: "Run"
        run: LangStr

        #: ::
        #:
        #:     On-screen controls guide line telling controller players how to
        #:     run.
        #:
        #:     English: "Run: <hold any button>"
        run_hold_any_button: LangStr

        #: ::
        #:
        #:     On-screen controls guide line telling keyboard players how to
        #:     run.
        #:
        #:     English: "Run: <hold any key>"
        run_hold_any_key: LangStr

    class StringsCoopGroup:
        """
        ::

            Co-op play UI: campaign/custom/tournament tabs, difficulty markers,
            tournament info/status, and level-lock notices.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Heading label shown before an achievement name.
        #:
        #:     English: "Achievement:"
        achievement_label: LangStr

        #: ::
        #:
        #:     Heading over the list of achievements left to earn.
        #:
        #:     English: "Achievements Remaining:"
        achievements_remaining: LangStr

        #: ::
        #:
        #:     Label for the campaign tab/section.
        #:
        #:     English: "Campaign"
        campaign: LangStr

        #: ::
        #:
        #:     Warning that all chest slots are full so earned chests will be
        #:     lost.
        #:
        #:     English: "WARNING: All your chest slots are full. Any chests you
        #:     earn this game will be lost."
        chest_slots_full_warning: LangStr

        #: ::
        #:
        #:     Label for the player's best score.
        #:
        #:     English: "Current Best"
        current_best: LangStr

        #: ::
        #:
        #:     Label for the custom-games tab.
        #:
        #:     English: "Custom"
        custom: LangStr

        #: ::
        #:
        #:     Marker that a level is available only in hard mode.
        #:
        #:     English: "Hard Mode Only"
        difficulty_hard_only: LangStr

        #: ::
        #:
        #:     Confirmation prompt that a level unlocks only in hard mode.
        #:
        #:     English: "This level can only be unlocked in hard mode. Do you
        #:     think you have what it takes!?!?!"
        difficulty_hard_unlock_only: LangStr

        #: ::
        #:
        #:     Label for a tournament entry fee.
        #:
        #:     English: "Entry"
        entry_fee: LangStr

        def level_is_locked(self, *, level: str | LangStr) -> LangStr:
            """
            ::

                Notice that a named level is locked.

                English: "{level} is locked."
            """

        def level_must_be_completed_first(
            self, *, level: str | LangStr
        ) -> LangStr:
            """
            ::

                Notice that a named level must be completed first.

                English: "{level} must be completed first."
            """

        #: ::
        #:
        #:     Celebration heading on the co-op score screen when the next level
        #:     was just unlocked.
        #:
        #:     English: "Level Unlocked!"
        level_unlocked: LangStr

        #: ::
        #:
        #:     Heading on the co-op score screen labeling the upcoming level.
        #:
        #:     English: "Next Level"
        next_level: LangStr

        #: ::
        #:
        #:     Placeholder when no achievements remain.
        #:
        #:     English: "- none"
        no_achievements_remaining: LangStr

        #: ::
        #:
        #:     Warning that tournament scores are ignored on test builds.
        #:
        #:     English: "WARNING: Tournament scores from this test build will be
        #:     ignored."
        no_tournaments_in_test_build: LangStr

        def of_total(self, *, total: str | LangStr) -> LangStr:
            """
            ::

                Suffix showing a value out of a total time.

                English: "of {total}"
            """

        def player_count_abbreviated(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                Abbreviated player-count badge (number + "p" for players).

                English: "{count}p"
            """

        def power_ranking_points(self, *, number: str | LangStr) -> LangStr:
            """
            ::

                Compact points label for power-ranking scores.

                English: "{number} pts"
            """

        #: ::
        #:
        #:     Label for tournament prizes.
        #:
        #:     English: "Prizes"
        prizes: LangStr

        #: ::
        #:
        #:     Label for tournament time remaining.
        #:
        #:     English: "Time Remaining"
        time_remaining: LangStr

        #: ::
        #:
        #:     Singular "Tournament" label.
        #:
        #:     English: "Tournament"
        tournament: LangStr

        #: ::
        #:
        #:     Status while loading tournament state.
        #:
        #:     English: "Checking tournament state; please wait..."
        tournament_checking_state: LangStr

        #: ::
        #:
        #:     Notice that the current tournament has ended.
        #:
        #:     English: "This tournament has ended. A new one will start soon."
        tournament_ended: LangStr

        #: ::
        #:
        #:     Explanation of how tournaments work.
        #:
        #:     English: "Compete for high scores with other players in your
        #:     league. Prizes are awarded to the top scoring players when
        #:     tournament time expires."
        tournament_info: LangStr

        #: ::
        #:
        #:     Plural "Tournaments" tab label.
        #:
        #:     English: "Tournaments"
        tournaments: LangStr

        #: ::
        #:
        #:     Notice that tournaments are off while a workspace is active.
        #:
        #:     English: "Tournaments are disabled when Workspaces are active. To
        #:     re-enable tournaments, disable your Workspace and restart."
        tournaments_disabled_workspace: LangStr

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

    class StringsCoopScoreGroup:
        """
        ::

            Co-op score/results screen: unavailable-scores notices, the
            best-scores/best-times section headings, and level/tournament
            proceed messages.

            See source for the full asset list.
        """

        def best_rating(self, *, rating: str | LangStr) -> LangStr:
            """
            ::

                The player's best rating on this co-op level.

                English: "Your best rating is {rating}"
            """

        #: ::
        #:
        #:     Notice that the level must be completed to proceed.
        #:
        #:     English: "You must complete this level to proceed!"
        complete_level_to_proceed: LangStr

        def current_standing(self, *, rank: str | LangStr) -> LangStr:
            """
            ::

                The player's current rank on this co-op level.

                English: "Your current standing is #{rank}"
            """

        #: ::
        #:
        #:     Label for the finishing time on the co-op results screen.
        #:
        #:     English: "Final Time"
        final_time: LangStr

        #: ::
        #:
        #:     Notice that friend scores could not be loaded.
        #:
        #:     English: "Friend scores unavailable."
        friend_scores_unavailable: LangStr

        def last_games(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                Note that a rating covers only recent games.

                English: "(last {count} games)"
            """

        #: ::
        #:
        #:     Announcement that a new co-op level became available.
        #:
        #:     English: "Level Unlocked!"
        level_unlocked: LangStr

        def multi_player_count(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                Player count for a multi-player co-op score entry.

                English: "{count} players"
            """

        #: ::
        #:
        #:     Celebration for beating your own previous best.
        #:
        #:     English: "New personal best!"
        new_personal_best: LangStr

        #: ::
        #:
        #:     Label for the level that follows this one.
        #:
        #:     English: "Next Level"
        next_level: LangStr

        #: ::
        #:
        #:     Notice that too few players remain to continue.
        #:
        #:     English: "Not enough players remaining; exit and start a new
        #:     game."
        not_enough_players_remaining: LangStr

        def out_of(self, *, rank: str | LangStr, all: str | LangStr) -> LangStr:
            """
            ::

                The player's rank among all ranked players.

                English: "(#{rank} out of {all})"
            """

        #: ::
        #:
        #:     Label for the score rating on the co-op results screen.
        #:
        #:     English: "Rating"
        rating: LangStr

        #: ::
        #:
        #:     Notice that the score list could not be loaded.
        #:
        #:     English: "Score list unavailable."
        score_list_unavailable: LangStr

        def score_was(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                The previous best score, shown when it is beaten.

                English: "(was {count})"
            """

        #: ::
        #:
        #:     Player count for a single-player co-op score entry.
        #:
        #:     English: "1 player"
        single_player_count: LangStr

        #: ::
        #:
        #:     Heading/button label for the tournament standings.
        #:
        #:     English: "Tournament Standings"
        tournament_standings: LangStr

        #: ::
        #:
        #:     Notice that world scores could not be loaded.
        #:
        #:     English: "World scores unavailable."
        world_scores_unavailable: LangStr

        #: ::
        #:
        #:     Heading for the world-best scores list.
        #:
        #:     English: "World's Best Scores"
        worlds_best_scores: LangStr

        #: ::
        #:
        #:     Heading for the world-best times list.
        #:
        #:     English: "World's Best Times"
        worlds_best_times: LangStr

        #: ::
        #:
        #:     Heading for the player's own best scores.
        #:
        #:     English: "Your Best Scores"
        your_best_scores: LangStr

        #: ::
        #:
        #:     Heading for the player's own best times.
        #:
        #:     English: "Your Best Times"
        your_best_times: LangStr

    class StringsCreditsGroup:
        """
        ::

            Credits-window text: section headings and contributor credit lines.

            See source for the full asset list.
        """

        def additional_audio_art_ideas(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Credit line for additional contributors.

                English: "Additional Audio, Early Artwork, and Ideas by {name}"
            """

        def additional_music_from(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Credit line for additional music.

                English: "Additional music from {name}"
            """

        #: ::
        #:
        #:     Credit line thanking friends and family playtesters.
        #:
        #:     English: "All of my friends and family who helped play test"
        all_my_family: LangStr

        def coding_graphics_audio(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Credit line for the main developer.

                English: "Coding, Graphics, and Audio by {name}"
            """

        #: ::
        #:
        #:     Section heading for translation credits.
        #:
        #:     English: "Language Translations:"
        language_translations: LangStr

        #: ::
        #:
        #:     Section heading for legal text.
        #:
        #:     English: "Legal:"
        legal: LangStr

        def public_domain_music_via(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Credit line for public-domain music.

                English: "Public-domain music via {name}"
            """

        def software_based_on(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Credit line for third-party software.

                English: "This software is based in part on the work of {name}."
            """

        def song_credit(
            self,
            *,
            title: str | LangStr,
            performer: str | LangStr,
            composer: str | LangStr,
            arranger: str | LangStr,
            publisher: str | LangStr,
            source: str | LangStr,
        ) -> LangStr:
            """
            ::

                Credit line for the menu music, naming its title, performer,
                composer, arranger, publisher and source. Every placeholder is
                filled with a proper name that stays in English; only the
                connecting words are translated. The two line breaks are part of
                the layout and must be preserved.

                English: "{title} Performed by {performer} Composed by
                {composer}, Arranged by {arranger}, Published by {publisher},
                Courtesy of {source}"
            """

        #: ::
        #:
        #:     Section heading for sound/music credits.
        #:
        #:     English: "Sound & Music:"
        sound_and_music: LangStr

        def sounds_source(self, *, source: str | LangStr) -> LangStr:
            """
            ::

                Credit heading naming a sound source.

                English: "Sounds ({source}):"
            """

        #: ::
        #:
        #:     Section heading for special thanks.
        #:
        #:     English: "Special Thanks:"
        special_thanks: LangStr

        def thanks_especially_to(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Special-thanks credit line.

                English: "Special thanks to {name}"
            """

        def title(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Title of the credits window.

                English: "{app_name} Credits"
            """

        #: ::
        #:
        #:     Humorous credit line thanking coffee.
        #:
        #:     English: "Whoever invented coffee"
        whoever_invented_coffee: LangStr

    class StringsEconomyGroup:
        """
        ::

            Screen-messages about currency: grants and related notices.

            See source for the full asset list.
        """

        def received_tickets(self, *, count: int) -> LangStr:
            """
            ::

                Confirmation of how many tickets were received.

                English: (one) "Received # Ticket!" / (other) "Received #
                Tickets!"
            """

        def you_got_tokens(self, *, tokens: int) -> LangStr:
            """
            ::

                Confirmation effect sent to game clients when tokens are
                credited (store purchases, promo codes, and other grant flows).

                English: (one) "You got # Token!" / (other) "You got # Tokens!"
            """

    class StringsFileSelectorGroup:
        """
        ::

            File/folder selector window titles and buttons.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Title when selecting a file.
        #:
        #:     English: "Select a File"
        select_file: LangStr

        #: ::
        #:
        #:     Title when selecting a file or folder.
        #:
        #:     English: "Select a File or Folder"
        select_file_or_folder: LangStr

        #: ::
        #:
        #:     Title when selecting a folder.
        #:
        #:     English: "Select a Folder"
        select_folder: LangStr

        #: ::
        #:
        #:     Button to confirm the current folder.
        #:
        #:     English: "Use This Folder"
        use_this_folder: LangStr

    class StringsGameGroup:
        """
        ::

            Generic in-game scoreboard and result vocabulary shared across the
            various gameplay activities (scores, victory/draw banners, wave
            progress, bonus labels).

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Label for a level-completion score bonus.
        #:
        #:     English: "Completion Bonus"
        completion_bonus: LangStr

        def disqualified_player_left(
            self, *, team: str | LangStr, player: str | LangStr
        ) -> LangStr:
            """
            ::

                Notice that a team was disqualified when a player left.

                English: "Team {team} has been disqualified because {player}
                left the game."
            """

        #: ::
        #:
        #:     Celebratory banner for two kills in quick succession.
        #:
        #:     English: "DOUBLE KILL!"
        double_kill: LangStr

        #: ::
        #:
        #:     Banner shown when a game ends in a tie.
        #:
        #:     English: "Draw"
        draw: LangStr

        def epic_description_filter(
            self, *, description: str | LangStr
        ) -> LangStr:
            """
            ::

                Epic-mode wrapper appended to a game description.

                English: "{description} In epic slow motion."
            """

        def epic_name_filter(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Name of the slow-motion variant of a minigame.

                English: "Epic {name}"
            """

        #: ::
        #:
        #:     Banner shown when the player fails a level.
        #:
        #:     English: "Fail"
        fail: LangStr

        #: ::
        #:
        #:     Heading over the final score table.
        #:
        #:     English: "Final Scores"
        final_scores: LangStr

        #: ::
        #:
        #:     Celebratory banner for five kills in quick succession.
        #:
        #:     English: "FIVE KILL!!!"
        five_kill: LangStr

        #: ::
        #:
        #:     Celebratory banner for clearing a wave flawlessly.
        #:
        #:     English: "Flawless Wave!"
        flawless_wave: LangStr

        def game_on_map(
            self, *, name: str | LangStr, mapname: str | LangStr
        ) -> LangStr:
            """
            ::

                Pure-formatting template pairing a game with its map;
                substitution-only.

                English: "{name} @ {mapname}"
            """

        def killing_track_skipper(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Notice that a racer is killed for cutting the course.

                English: "Killing {name} for skipping part of the track!"
            """

        def lap_number(
            self, *, current: str | LangStr, total: str | LangStr
        ) -> LangStr:
            """
            ::

                Progress label for the current lap of a race.

                English: "Lap {current}/{total}"
            """

        #: ::
        #:
        #:     Label for the remaining-lives bonus in a co-op score tally.
        #:
        #:     English: "Lives Bonus"
        lives_bonus: LangStr

        def multi_kill(self, *, count: int) -> LangStr:
            """
            ::

                Celebratory banner for a kill streak of a given count (six or
                more).

                English: (one) "#-KILL!!!" / (other) "#-KILLS!!!"
            """

        def name_betrayed(
            self, *, name: str | LangStr, victim: str | LangStr
        ) -> LangStr:
            """
            ::

                Death announcement: a player killed a teammate.

                English: "{name} betrayed {victim}."
            """

        def name_died(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Death announcement: a player died.

                English: "{name} died."
            """

        def name_killed(
            self, *, name: str | LangStr, victim: str | LangStr
        ) -> LangStr:
            """
            ::

                Death announcement: a player killed an opponent.

                English: "{name} killed {victim}."
            """

        def name_scores(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Announcement that a named player scores.

                English: "{name} Scores!"
            """

        def name_suicide(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Death announcement: a player killed themselves.

                English: "{name} committed suicide."
            """

        #: ::
        #:
        #:     Error message when no valid maps exist for a game type.
        #:
        #:     English: "No valid maps found for this game type."
        no_valid_maps_error: LangStr

        def onslaught_respawn(
            self, *, player: str | LangStr, wave: str | LangStr
        ) -> LangStr:
            """
            ::

                In-game notice that a fallen co-op player will rejoin at a given
                enemy wave; placeholders are the player name and wave number.

                English: "{player} will respawn in wave {wave}"
            """

        #: ::
        #:
        #:     Warning that your own flag must be at your base to score.
        #:
        #:     English: "Your own flag must be at your base to score!"
        own_flag_at_base_warning: LangStr

        #: ::
        #:
        #:     Notice that the host has paused the game.
        #:
        #:     English: "(paused by host)"
        paused_by_host: LangStr

        #: ::
        #:
        #:     Celebration shown for completing a wave without damage.
        #:
        #:     English: "Perfect Wave!"
        perfect_wave: LangStr

        def points_gained(self, *, points: str | LangStr) -> LangStr:
            """
            ::

                Pure-formatting popup showing points just gained;
                substitution-only.

                English: "+{points}"
            """

        def points_gained_titled(
            self, *, points: str | LangStr, title: str | LangStr
        ) -> LangStr:
            """
            ::

                Pure-formatting popup pairing gained points with an award title;
                substitution-only.

                English: "+{points} {title}"
            """

        #: ::
        #:
        #:     Prompt to press any button to continue.
        #:
        #:     English: "Press any button to continue..."
        press_any_button_continue: LangStr

        #: ::
        #:
        #:     Prompt to press a button to play again.
        #:
        #:     English: "Press any button to play again..."
        press_any_button_play_again: LangStr

        #: ::
        #:
        #:     Prompt to press any key or button to continue.
        #:
        #:     English: "Press any key/button to continue..."
        press_any_key_button_continue: LangStr

        #: ::
        #:
        #:     Prompt to press a key or button to play again.
        #:
        #:     English: "Press any key/button to play again..."
        press_any_key_button_play_again: LangStr

        #: ::
        #:
        #:     Flying-map tip: press jump repeatedly to fly.
        #:
        #:     English: "** Press jump repeatedly to fly **"
        press_jump_to_fly: LangStr

        #: ::
        #:
        #:     Celebratory banner for four kills in quick succession.
        #:
        #:     English: "QUAD KILL!!!"
        quad_kill: LangStr

        #: ::
        #:
        #:     Notice that you must reach wave 2 to rank.
        #:
        #:     English: "Reach wave 2 to rank."
        reach_wave_2: LangStr

        #: ::
        #:
        #:     Label for a score value on the in-game scoreboard.
        #:
        #:     English: "Score"
        score: LangStr

        def solo_name_filter(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Name of the solo variant of a minigame.

                English: "Solo {name}"
            """

        #: ::
        #:
        #:     Label for the time-based bonus in a co-op score tally.
        #:
        #:     English: "Time Bonus"
        time_bonus: LangStr

        def time_bonus_amount(self, *, amount: str | LangStr) -> LangStr:
            """
            ::

                Time-bonus label with its current amount, shown on the co-op
                HUD.

                English: "Time Bonus: {amount}"
            """

        #: ::
        #:
        #:     Banner shown when the game time limit runs out.
        #:
        #:     English: "Time Expired"
        time_expired: LangStr

        #: ::
        #:
        #:     Heading label shown before a gameplay tip.
        #:
        #:     English: "Tip:"
        tip_title: LangStr

        #: ::
        #:
        #:     Banner shown when the tournament time limit runs out.
        #:
        #:     English: "Tournament Time Expired"
        tournament_time_expired: LangStr

        #: ::
        #:
        #:     Celebratory banner for three kills in quick succession.
        #:
        #:     English: "TRIPLE KILL!!"
        triple_kill: LangStr

        def turbo_warning(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Warning that button-spamming will knock a player out.

                English: "Warning {name}: Button-spamming (turbo) will knock you
                out!"
            """

        #: ::
        #:
        #:     Celebratory banner shown when a game is won.
        #:
        #:     English: "Victory!"
        victory: LangStr

        #: ::
        #:
        #:     Small "versus" label shown between two opponents.
        #:
        #:     English: "vs."
        vs: LangStr

        def waiting_for_host(self, *, host: str | LangStr) -> LangStr:
            """
            ::

                Notice that the host must continue the game.

                English: "(Waiting for {host} to continue)"
            """

        #: ::
        #:
        #:     Label for the current wave number in wave-based games.
        #:
        #:     English: "Wave"
        wave: LangStr

        def wave_number(self, *, number: str | LangStr) -> LangStr:
            """
            ::

                Label for the current wave with its number, shown on the co-op
                HUD.

                English: "Wave {number}"
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

    class StringsGameSettingsGroup:
        """
        ::

            Names of game settings and their preset choices, shown in the
            playlist editor. Short label-style noun phrases, not prose; several
            double as the value shown for a setting, so each must read correctly
            standing alone.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Name of a game setting permitting scores below zero.
        #:
        #:     English: "Allow Negative Scores"
        allow_negative_scores: LangStr

        #: ::
        #:
        #:     Name of a game setting that evens out the total lives given to
        #:     each team.
        #:
        #:     English: "Balance Total Lives"
        balance_total_lives: LangStr

        #: ::
        #:
        #:     Name of a game setting for how often bombs appear.
        #:
        #:     English: "Bomb Spawning"
        bomb_spawning: LangStr

        #: ::
        #:
        #:     Name of a game setting granting the boxing-gloves power-up to the
        #:     chosen one.
        #:
        #:     English: "Chosen One Gets Gloves"
        chosen_one_gets_gloves: LangStr

        #: ::
        #:
        #:     Name of a game setting granting an energy shield to the chosen
        #:     one.
        #:
        #:     English: "Chosen One Gets Shield"
        chosen_one_gets_shield: LangStr

        #: ::
        #:
        #:     Name of a game setting for how long a player must stay the chosen
        #:     one to win.
        #:
        #:     English: "Chosen One Time"
        chosen_one_time: LangStr

        #: ::
        #:
        #:     Menu option for a duration of eight seconds, shown as one of the
        #:     values a game setting can take in the playlist editor.
        #:
        #:     English: "8 Seconds"
        eight_seconds: LangStr

        #: ::
        #:
        #:     Name of a game setting that allows the impact-bomb power-up to
        #:     appear.
        #:
        #:     English: "Enable Impact Bombs"
        enable_impact_bombs: LangStr

        #: ::
        #:
        #:     Name of a game setting that allows the triple-bomb power-up to
        #:     appear.
        #:
        #:     English: "Enable Triple Bombs"
        enable_triple_bombs: LangStr

        #: ::
        #:
        #:     Name of a game setting requiring every team member to finish, not
        #:     just one.
        #:
        #:     English: "Entire Team Must Finish"
        entire_team_must_finish: LangStr

        #: ::
        #:
        #:     Name of a game setting that plays the match in dramatic slow
        #:     motion.
        #:
        #:     English: "Epic Mode"
        epic_mode: LangStr

        #: ::
        #:
        #:     Menu option for a duration of five minutes, shown as one of the
        #:     values a game setting can take in the playlist editor.
        #:
        #:     English: "5 Minutes"
        five_minutes: LangStr

        #: ::
        #:
        #:     Name of a game setting for how long a dropped flag waits before
        #:     returning to its base.
        #:
        #:     English: "Flag Idle Return Time"
        flag_idle_return_time: LangStr

        #: ::
        #:
        #:     Name of a game setting for how long touching a flag takes to send
        #:     it back to its base.
        #:
        #:     English: "Flag Touch Return Time"
        flag_touch_return_time: LangStr

        #: ::
        #:
        #:     Menu option for a duration of four seconds, shown as one of the
        #:     values a game setting can take in the playlist editor.
        #:
        #:     English: "4 Seconds"
        four_seconds: LangStr

        #: ::
        #:
        #:     Name of a game setting for how long something must be held to
        #:     count.
        #:
        #:     English: "Hold Time"
        hold_time: LangStr

        #: ::
        #:
        #:     Name of a game setting for how many kills each player needs for
        #:     the team to win.
        #:
        #:     English: "Kills to Win Per Player"
        kills_to_win_per_player: LangStr

        #: ::
        #:
        #:     Name of a game setting for how many laps a race runs.
        #:
        #:     English: "Laps"
        laps: LangStr

        #: ::
        #:
        #:     Name of a game setting for how many lives each player starts
        #:     with.
        #:
        #:     English: "Lives Per Player"
        lives_per_player: LangStr

        #: ::
        #:
        #:     Menu option for a longer than normal duration, shown as one of
        #:     the values a game setting can take in the playlist editor.
        #:
        #:     English: "Long"
        long: LangStr

        #: ::
        #:
        #:     Menu option for a much longer than normal duration, shown as one
        #:     of the values a game setting can take in the playlist editor.
        #:
        #:     English: "Longer"
        longer: LangStr

        #: ::
        #:
        #:     Name of a game setting for how often land-mines appear.
        #:
        #:     English: "Mine Spawning"
        mine_spawning: LangStr

        #: ::
        #:
        #:     Menu option for that land-mines never appear, shown as one of the
        #:     values a game setting can take in the playlist editor.
        #:
        #:     English: "No Mines"
        no_mines: LangStr

        #: ::
        #:
        #:     The choice "None", meaning the option is switched off.
        #:
        #:     English: "None"
        none: LangStr

        #: ::
        #:
        #:     Menu option for the normal duration, shown as one of the values a
        #:     game setting can take in the playlist editor.
        #:
        #:     English: "Normal"
        normal: LangStr

        #: ::
        #:
        #:     Menu option for a duration of one minute, shown as one of the
        #:     values a game setting can take in the playlist editor.
        #:
        #:     English: "1 Minute"
        one_minute: LangStr

        #: ::
        #:
        #:     Menu option for a duration of one second, shown as one of the
        #:     values a game setting can take in the playlist editor.
        #:
        #:     English: "1 Second"
        one_second: LangStr

        #: ::
        #:
        #:     Name of a game setting for a harder variant of the game.
        #:
        #:     English: "Pro Mode"
        pro_mode: LangStr

        #: ::
        #:
        #:     Name of a game setting for how long players wait before returning
        #:     after dying.
        #:
        #:     English: "Respawn Times"
        respawn_times: LangStr

        #: ::
        #:
        #:     Name of a game setting for the score needed to win.
        #:
        #:     English: "Score to Win"
        score_to_win: LangStr

        #: ::
        #:
        #:     Menu option for a shorter than normal duration, shown as one of
        #:     the values a game setting can take in the playlist editor.
        #:
        #:     English: "Short"
        short: LangStr

        #: ::
        #:
        #:     Menu option for a much shorter than normal duration, shown as one
        #:     of the values a game setting can take in the playlist editor.
        #:
        #:     English: "Shorter"
        shorter: LangStr

        #: ::
        #:
        #:     Name of a game setting where players take turns alone rather than
        #:     as a team.
        #:
        #:     English: "Solo Mode"
        solo_mode: LangStr

        #: ::
        #:
        #:     Name of a game setting for how many targets appear.
        #:
        #:     English: "Target Count"
        target_count: LangStr

        #: ::
        #:
        #:     Menu option for a duration of ten minutes, shown as one of the
        #:     values a game setting can take in the playlist editor.
        #:
        #:     English: "10 Minutes"
        ten_minutes: LangStr

        #: ::
        #:
        #:     Name of a game setting capping how long a match runs.
        #:
        #:     English: "Time Limit"
        time_limit: LangStr

        #: ::
        #:
        #:     Menu option for a duration of twenty minutes, shown as one of the
        #:     values a game setting can take in the playlist editor.
        #:
        #:     English: "20 Minutes"
        twenty_minutes: LangStr

        #: ::
        #:
        #:     Menu option for a duration of two minutes, shown as one of the
        #:     values a game setting can take in the playlist editor.
        #:
        #:     English: "2 Minutes"
        two_minutes: LangStr

        #: ::
        #:
        #:     Menu option for a duration of two seconds, shown as one of the
        #:     values a game setting can take in the playlist editor.
        #:
        #:     English: "2 Seconds"
        two_seconds: LangStr

    class StringsGatherGroup:
        """
        ::

            Party/gather UI strings: hosting-form labels, pre-join prompts, and
            related networking-flow messages.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Label for the About tab of the gather window.
        #:
        #:     English: "About"
        about: LangStr

        def about_description(
            self, *, party: str | LangStr, button: str | LangStr
        ) -> LangStr:
            """
            ::

                Intro text on the gather window About tab explaining parties;
                {party} is the party icon glyph and {button} the
                top-controller-button glyph (both single characters).

                English: "Use these tabs to assemble a party. Parties let you
                play games and tournaments with your friends across different
                devices. Use the {party} button at the top right to chat and
                interact with your party. (on a controller, press {button} while
                in a menu)"
            """

        #: ::
        #:
        #:     Addendum on the gather About tab noting one device can host
        #:     several players.
        #:
        #:     English: "Remember: any device in a party can have more than one
        #:     player if you have enough controllers."
        about_local_multiplayer_extra: LangStr

        def added_to_favorites(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Confirmation after saving a favorite party.

                English: "Added '{name}' to Favorites."
            """

        #: ::
        #:
        #:     Placeholder shown when addresses cannot be fetched.
        #:
        #:     English: "<error fetching addresses>"
        address_fetch_error: LangStr

        #: ::
        #:
        #:     Status shown while checking something.
        #:
        #:     English: "checking..."
        checking: LangStr

        #: ::
        #:
        #:     Button to connect to a party.
        #:
        #:     English: "Connect"
        connect: LangStr

        #: ::
        #:
        #:     Button to copy the party code.
        #:
        #:     English: "Copy Code"
        copy_code: LangStr

        #: ::
        #:
        #:     Confirmation after copying a party code.
        #:
        #:     English: "Code copied to clipboard."
        copy_code_confirm: LangStr

        #: ::
        #:
        #:     Tip about setting up a dedicated server.
        #:
        #:     English: "For best results, set up a dedicated server. See
        #:     bombsquadgame.com/server to learn how."
        dedicated_server_info: LangStr

        def delete_confirm_list(self, *, list: str | LangStr) -> LangStr:
            """
            ::

                Confirmation before deleting a named list.

                English: "Delete "{list}"?"
            """

        #: ::
        #:
        #:     Short hint pointing to the gather window.
        #:
        #:     English: "Use the gather window to assemble a party."
        description_short: LangStr

        def disconnect_clients(self, *, count: int) -> LangStr:
            """
            ::

                Confirmation before an action disconnects party players.

                English: (one) "This will disconnect the # player in your party.
                Are you sure?" / (other) "This will disconnect the # players in
                your party. Are you sure?"
            """

        #: ::
        #:
        #:     Blurb inviting players to the Discord.
        #:
        #:     English: "Want to look for new people to play with? Join our
        #:     Discord and find new friends!"
        discord_friends: LangStr

        #: ::
        #:
        #:     Button to open the Discord invite.
        #:
        #:     English: "Join the Discord"
        discord_join: LangStr

        #: ::
        #:
        #:     Label for the favorites list of saved parties.
        #:
        #:     English: "Favorites"
        favorites: LangStr

        #: ::
        #:
        #:     Button to save a party as a favorite.
        #:
        #:     English: "Save As Favorite"
        favorites_save: LangStr

        #: ::
        #:
        #:     Notice that a free cloud server is available.
        #:
        #:     English: "FREE CLOUD SERVER AVAILABLE!"
        free_cloud_server_available: LangStr

        def free_cloud_server_available_minutes(
            self, *, minutes: str | LangStr
        ) -> LangStr:
            """
            ::

                Countdown to the next free cloud server.

                English: "Next free cloud server available in {minutes}
                minutes."
            """

        #: ::
        #:
        #:     Notice that no free cloud servers are free right now.
        #:
        #:     English: "No free cloud servers available."
        free_cloud_server_not_available: LangStr

        #: ::
        #:
        #:     Button to get a friend invite code.
        #:
        #:     English: "Get Friend Invite Code"
        get_friend_invite_code: LangStr

        #: ::
        #:
        #:     Heading for the host-public-party view.
        #:
        #:     English: "Host a Public Party"
        host_public_party: LangStr

        #: ::
        #:
        #:     Notice that hosting is unavailable.
        #:
        #:     English: "Hosting Unavailable"
        hosting_unavailable: LangStr

        #: ::
        #:
        #:     Error for an invalid server address.
        #:
        #:     English: "Error: invalid address."
        invalid_address_error: LangStr

        #: ::
        #:
        #:     Error screen-message when a friend/party invite code the player
        #:     entered is not valid.
        #:
        #:     English: "Invalid code."
        invalid_code_error: LangStr

        #: ::
        #:
        #:     Error for an invalid party name.
        #:
        #:     English: "Error: invalid name."
        invalid_name_error: LangStr

        #: ::
        #:
        #:     Error for an invalid server port.
        #:
        #:     English: "Error: invalid port."
        invalid_port_error: LangStr

        def invite_a_friend(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                Blurb about inviting friends for a ticket reward.

                English: "Friends don't have the game? Invite them to try it and
                they'll receive {count} free Tickets."
            """

        #: ::
        #:
        #:     Button to invite friends.
        #:
        #:     English: "Invite Friends"
        invite_friends: LangStr

        #: ::
        #:
        #:     Heading for the join-public-party view.
        #:
        #:     English: "Join a Public Party"
        join_public_party: LangStr

        #: ::
        #:
        #:     Question label about internet joinability.
        #:
        #:     English: "Are you joinable from the internet?:"
        joinable_from_internet: LangStr

        #: ::
        #:
        #:     Negative joinability status with a caveat marker.
        #:
        #:     English: "NO*"
        joinable_no: LangStr

        #: ::
        #:
        #:     Affirmative joinability status.
        #:
        #:     English: "YES"
        joinable_yes: LangStr

        #: ::
        #:
        #:     Subtitle for the nearby-party tab.
        #:
        #:     English: "Join a Nearby Party (LAN, Bluetooth, etc.)"
        local_network_description: LangStr

        #: ::
        #:
        #:     Button to make the party private.
        #:
        #:     English: "Make My Party Private"
        make_party_private: LangStr

        #: ::
        #:
        #:     Button to make the party public.
        #:
        #:     English: "Make My Party Public"
        make_party_public: LangStr

        #: ::
        #:
        #:     Label for the Manual (join-by-address) tab.
        #:
        #:     English: "Manual"
        manual: LangStr

        #: ::
        #:
        #:     Label for the server address input field.
        #:
        #:     English: "Address"
        manual_address: LangStr

        #: ::
        #:
        #:     Subtitle for the manual-connect tab.
        #:
        #:     English: "Join a party by address:"
        manual_description: LangStr

        #: ::
        #:
        #:     Heading for the join-by-address section.
        #:
        #:     English: "Join By Address"
        manual_join_section: LangStr

        #: ::
        #:
        #:     Label for the max-connections setting.
        #:
        #:     English: "Max Connections"
        max_connections: LangStr

        #: ::
        #:
        #:     Label for the max-party-size setting.
        #:
        #:     English: "Max Party Size"
        max_party_size: LangStr

        #: ::
        #:
        #:     Label for the Nearby (local network) tab.
        #:
        #:     English: "Nearby"
        nearby: LangStr

        #: ::
        #:
        #:     Placeholder shown when there is no connection.
        #:
        #:     English: "<no connection>"
        no_connection: LangStr

        #: ::
        #:
        #:     Placeholder when no favorite parties are saved.
        #:
        #:     English: "No Parties Added"
        no_parties_added: LangStr

        #: ::
        #:
        #:     Placeholder when no public servers are found.
        #:
        #:     English: "No servers found."
        no_servers_found: LangStr

        #: ::
        #:
        #:     Label for the party join code.
        #:
        #:     English: "Party Code"
        party_code: LangStr

        #: ::
        #:
        #:     Label for the party name field.
        #:
        #:     English: "Party Name"
        party_name: LangStr

        #: ::
        #:
        #:     Description line in the pre-join password prompt dialog, shown
        #:     above the password entry field when joining a password-protected
        #:     party.
        #:
        #:     English: "This party requires a password."
        party_requires_password: LangStr

        #: ::
        #:
        #:     Status that the party server is running.
        #:
        #:     English: "Your party server is running."
        party_server_running: LangStr

        #: ::
        #:
        #:     Lowercase column label for party size.
        #:
        #:     English: "party size"
        party_size: LangStr

        #: ::
        #:
        #:     Status shown while checking party status.
        #:
        #:     English: "checking status..."
        party_status_checking: LangStr

        #: ::
        #:
        #:     Status that the party is joinable.
        #:
        #:     English: "your party is now joinable from the internet"
        party_status_joinable: LangStr

        #: ::
        #:
        #:     Status that the server is unreachable.
        #:
        #:     English: "unable to connect to server"
        party_status_no_connection: LangStr

        #: ::
        #:
        #:     Status that the hosted party is not public.
        #:
        #:     English: "your party is not public"
        party_status_not_public: LangStr

        #: ::
        #:
        #:     Label for the optional party-password entry field in the gather
        #:     window's public-hosting form.
        #:
        #:     English: "Password (optional)"
        password_optional: LangStr

        #: ::
        #:
        #:     Lowercase column label for network ping.
        #:
        #:     English: "ping"
        ping: LangStr

        #: ::
        #:
        #:     Label for the server port input field.
        #:
        #:     English: "Port"
        port: LangStr

        #: ::
        #:
        #:     Label for the Private (cloud) party tab.
        #:
        #:     English: "Private"
        private: LangStr

        #: ::
        #:
        #:     Explanation of private cloud parties.
        #:
        #:     English: "Private parties run on dedicated cloud servers; no
        #:     router configuration required."
        private_party_cloud_description: LangStr

        #: ::
        #:
        #:     Button to host a private party.
        #:
        #:     English: "Host a Private Party"
        private_party_host: LangStr

        #: ::
        #:
        #:     Button to join a private party.
        #:
        #:     English: "Join a Private Party"
        private_party_join: LangStr

        #: ::
        #:
        #:     Label for the Public party tab.
        #:
        #:     English: "Public"
        public: LangStr

        #: ::
        #:
        #:     Warning about router config for public hosting.
        #:
        #:     English: "This may require configuring port-forwarding on your
        #:     router. For an easier option, host a private party."
        public_host_router_config: LangStr

        def router_forwarding(self, *, port: str | LangStr) -> LangStr:
            """
            ::

                Tip to forward a UDP port on the router.

                English: "*To fix this, forward UDP port {port} to your local
                address on your router."
            """

        #: ::
        #:
        #:     Button to show the local machine address.
        #:
        #:     English: "Show My Address"
        show_my_address: LangStr

        #: ::
        #:
        #:     Button to start hosting.
        #:
        #:     English: "Host"
        start_hosting: LangStr

        def start_hosting_paid(self, *, cost: str | LangStr) -> LangStr:
            """
            ::

                Button to start paid hosting for a cost.

                English: "Host Now For {cost}"
            """

        def start_stop_hosting_minutes(self, *, minutes: int) -> LangStr:
            """
            ::

                Notice of the free start/stop-hosting window in minutes.

                English: (one) "You can start and stop hosting for free for the
                next # minute." / (other) "You can start and stop hosting for
                free for the next # minutes."
            """

        #: ::
        #:
        #:     Button to stop hosting.
        #:
        #:     English: "Stop Hosting"
        stop_hosting: LangStr

        #: ::
        #:
        #:     Title of the Gather section, where players meet up and play with
        #:     others; also labels the main-menu button leading there and
        #:     gather-related join-screen hints.
        #:
        #:     English: "Gather"
        title: LangStr

        #: ::
        #:
        #:     Error when the host address cannot resolve.
        #:
        #:     English: "Error: unable to resolve host."
        unable_to_resolve_host: LangStr

        #: ::
        #:
        #:     Notice that a V2 account is required.
        #:
        #:     English: "This requires a V2 account. Upgrade your account and
        #:     try again."
        v2_account_required: LangStr

        #: ::
        #:
        #:     Label for the internet-facing address.
        #:
        #:     English: "Your address from the internet:"
        your_address_from_internet: LangStr

        #: ::
        #:
        #:     Label for the local network address.
        #:
        #:     English: "Your local address:"
        your_local_address: LangStr

    class StringsGetRemoteGroup:
        """
        ::

            Get-remote-app window: controller/remote-app info blurb.

            See source for the full asset list.
        """

        def info_short(
            self, *, app_name: str | LangStr, remote_app_name: str | LangStr
        ) -> LangStr:
            """
            ::

                Blurb about using controllers or the remote app.

                English: "{app_name} is most fun when played with family &
                friends. Connect one or more hardware controllers or install the
                {remote_app_name} app on phones or tablets to use them as
                controllers."
            """

    class StringsGetTokensGroup:
        """
        ::

            Get-tokens / Gold Pass store window strings.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Excited price label for a no-cost option.
        #:
        #:     English: "FREE!"
        free: LangStr

        #: ::
        #:
        #:     The "Gold Pass" product name.
        #:
        #:     English: "Gold Pass"
        gold_pass: LangStr

        #: ::
        #:
        #:     Gold Pass benefit: infinite tokens.
        #:
        #:     English: "Infinite Tokens."
        gold_pass_desc1: LangStr

        #: ::
        #:
        #:     Gold Pass benefit: no ads.
        #:
        #:     English: "No ads."
        gold_pass_desc2: LangStr

        #: ::
        #:
        #:     Gold Pass benefit: forever.
        #:
        #:     English: "Forever."
        gold_pass_desc3: LangStr

        #: ::
        #:
        #:     Error when the player lacks enough tokens.
        #:
        #:     English: "Not enough tokens!"
        not_enough_tokens: LangStr

        def num_tokens(self, *, count: int) -> LangStr:
            """
            ::

                A number of tokens.

                English: (one) "# Token" / (other) "# Tokens"
            """

        #: ::
        #:
        #:     Notice that purchases are unavailable here.
        #:
        #:     English: "Sorry, purchases are not available on this build. Try
        #:     signing into your account on another platform and making
        #:     purchases from there."
        purchase_never_available: LangStr

        #: ::
        #:
        #:     Notice that a purchase is unavailable.
        #:
        #:     English: "This purchase is not available."
        purchase_not_available: LangStr

        #: ::
        #:
        #:     Limited-time offer to remove ads via a token pack.
        #:
        #:     English: "LIMITED TIME OFFER: PURCHASE ANY TOKEN PACK TO REMOVE
        #:     IN-GAME ADS."
        remove_ads_offer: LangStr

        #: ::
        #:
        #:     Tagline describing tokens as the new currency.
        #:
        #:     English: "BombSquad's shiny new currency."
        shiny_new_currency: LangStr

        #: ::
        #:
        #:     Notice that the player owns a Gold Pass.
        #:
        #:     English: "You have a Gold Pass. All token purchases are free.
        #:     Enjoy!"
        you_have_gold_pass: LangStr

    class StringsHelpGroup:
        """
        ::

            Help window: section headings and how-to-play text for controls,
            controllers, devices, friends, and powerups.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     How-to text for the Bomb action.
        #:
        #:     English: "- Bomb - Stronger than punches, but can result in grave
        #:     self-injury. For best results, throw towards enemy before fuse
        #:     runs out."
        bomb_info: LangStr

        def can_help(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Reassurance that the app can help.

                English: "{app_name} can help."
            """

        #: ::
        #:
        #:     Heading for the controllers section.
        #:
        #:     English: "Controllers"
        controllers: LangStr

        def controllers_info(
            self, *, app_name: str | LangStr, remote_app_name: str | LangStr
        ) -> LangStr:
            """
            ::

                Body text for the controllers section.

                English: "You can play {app_name} with friends over a network,
                or play together on the same device if you have enough
                controllers. It supports a variety of controllers, and you can
                even use phones as controllers via the free '{remote_app_name}'
                app. See Settings > Controllers for more info."
            """

        #: ::
        #:
        #:     Heading for the controls section.
        #:
        #:     English: "Controls"
        controls: LangStr

        def controls_subtitle(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Subtitle introducing the basic actions.

                English: "Your friendly {app_name} character has a few basic
                actions:"
            """

        #: ::
        #:
        #:     Heading for the devices section.
        #:
        #:     English: "Devices"
        devices: LangStr

        def devices_info(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Body text for the devices section.

                English: "The VR version of {app_name} can be played over the
                network with the regular version, so whip out your extra phones,
                tablets, and computers and get your game on. It can even be
                useful to connect a regular version of the game to the VR
                version just to allow people outside to watch the action."
            """

        #: ::
        #:
        #:     Heading for the friends section.
        #:
        #:     English: "Friends"
        friends: LangStr

        def friends_good(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Two-line message about playing with friends.

                English: "These are good to have. {app_name} is most fun with
                several players and can support up to 8 at a time, which leads
                us to:"
            """

        #: ::
        #:
        #:     How-to text for the Jump action.
        #:
        #:     English: "- Jump - Jump to cross small gaps, to throw things
        #:     higher, and to express feelings of joy."
        jump_info: LangStr

        #: ::
        #:
        #:     Continued humorous line about punching.
        #:
        #:     English: "Or punching something, throwing it off a cliff, and
        #:     blowing it up on the way down with a sticky bomb."
        or_punching_something: LangStr

        #: ::
        #:
        #:     How-to text for the Pick Up action.
        #:
        #:     English: "- Pick Up - Grab flags, enemies, or anything else not
        #:     bolted to the ground. Press again to throw."
        pick_up_info: LangStr

        #: ::
        #:
        #:     Playful one-or-two-sentence description of the curse power-up,
        #:     shown under its name in the help screen. The tone is deliberately
        #:     light -- keep the joke rather than translating literally.
        #:
        #:     English: "You probably want to avoid these. ...or do you?"
        powerup_curse_description: LangStr

        #: ::
        #:
        #:     Name of the curse power-up, labelling its icon in the help
        #:     screen's power-up list.
        #:
        #:     English: "Curse"
        powerup_curse_name: LangStr

        #: ::
        #:
        #:     Playful one-or-two-sentence description of the med-pack power-up,
        #:     shown under its name in the help screen. The tone is deliberately
        #:     light -- keep the joke rather than translating literally.
        #:
        #:     English: "Restores you to full health. You'd never have guessed."
        powerup_health_description: LangStr

        #: ::
        #:
        #:     Name of the med-pack power-up, labelling its icon in the help
        #:     screen's power-up list.
        #:
        #:     English: "Med-Pack"
        powerup_health_name: LangStr

        #: ::
        #:
        #:     Playful one-or-two-sentence description of the ice-bombs
        #:     power-up, shown under its name in the help screen. The tone is
        #:     deliberately light -- keep the joke rather than translating
        #:     literally.
        #:
        #:     English: "Weaker than normal bombs, but they'll leave your
        #:     enemies frozen and extra brittle."
        powerup_ice_bombs_description: LangStr

        #: ::
        #:
        #:     Name of the ice-bombs power-up, labelling its icon in the help
        #:     screen's power-up list.
        #:
        #:     English: "Ice-Bombs"
        powerup_ice_bombs_name: LangStr

        #: ::
        #:
        #:     Playful one-or-two-sentence description of the trigger-bombs
        #:     power-up, shown under its name in the help screen. The tone is
        #:     deliberately light -- keep the joke rather than translating
        #:     literally.
        #:
        #:     English: "Slightly weaker than regular bombs, but they explode on
        #:     impact."
        powerup_impact_bombs_description: LangStr

        #: ::
        #:
        #:     Name of the trigger-bombs power-up, labelling its icon in the
        #:     help screen's power-up list.
        #:
        #:     English: "Trigger-Bombs"
        powerup_impact_bombs_name: LangStr

        #: ::
        #:
        #:     Playful one-or-two-sentence description of the land-mines
        #:     power-up, shown under its name in the help screen. The tone is
        #:     deliberately light -- keep the joke rather than translating
        #:     literally.
        #:
        #:     English: "These come in packs of 3 — perfect for base defense or
        #:     stopping speedy enemies!"
        powerup_land_mines_description: LangStr

        #: ::
        #:
        #:     Name of the land-mines power-up, labelling its icon in the help
        #:     screen's power-up list.
        #:
        #:     English: "Land-Mines"
        powerup_land_mines_name: LangStr

        #: ::
        #:
        #:     Playful one-or-two-sentence description of the boxing-gloves
        #:     power-up, shown under its name in the help screen. The tone is
        #:     deliberately light -- keep the joke rather than translating
        #:     literally.
        #:
        #:     English: "Makes your punches harder, faster, better, stronger."
        powerup_punch_description: LangStr

        #: ::
        #:
        #:     Name of the boxing-gloves power-up, labelling its icon in the
        #:     help screen's power-up list.
        #:
        #:     English: "Boxing-Gloves"
        powerup_punch_name: LangStr

        #: ::
        #:
        #:     Playful one-or-two-sentence description of the energy-shield
        #:     power-up, shown under its name in the help screen. The tone is
        #:     deliberately light -- keep the joke rather than translating
        #:     literally.
        #:
        #:     English: "Absorbs a bit of damage so you don't have to."
        powerup_shield_description: LangStr

        #: ::
        #:
        #:     Name of the energy-shield power-up, labelling its icon in the
        #:     help screen's power-up list.
        #:
        #:     English: "Energy-Shield"
        powerup_shield_name: LangStr

        #: ::
        #:
        #:     Playful one-or-two-sentence description of the sticky-bombs
        #:     power-up, shown under its name in the help screen. The tone is
        #:     deliberately light -- keep the joke rather than translating
        #:     literally.
        #:
        #:     English: "Stick to anything they hit. Hilarity ensues."
        powerup_sticky_bombs_description: LangStr

        #: ::
        #:
        #:     Name of the sticky-bombs power-up, labelling its icon in the help
        #:     screen's power-up list.
        #:
        #:     English: "Sticky-Bombs"
        powerup_sticky_bombs_name: LangStr

        #: ::
        #:
        #:     Playful one-or-two-sentence description of the triple-bombs
        #:     power-up, shown under its name in the help screen. The tone is
        #:     deliberately light -- keep the joke rather than translating
        #:     literally.
        #:
        #:     English: "Lets you whip out three bombs in a row instead of just
        #:     one."
        powerup_triple_bombs_description: LangStr

        #: ::
        #:
        #:     Name of the triple-bombs power-up, labelling its icon in the help
        #:     screen's power-up list.
        #:
        #:     English: "Triple-Bombs"
        powerup_triple_bombs_name: LangStr

        #: ::
        #:
        #:     Heading for the powerups section.
        #:
        #:     English: "Powerups"
        powerups: LangStr

        #: ::
        #:
        #:     Subtitle introducing powerups.
        #:
        #:     English: "Of course, no game is complete without powerups:"
        powerups_subtitle: LangStr

        #: ::
        #:
        #:     How-to text for the Punch action.
        #:
        #:     English: "- Punch - Punches do more damage the faster your fists
        #:     are moving, so run and spin like a madman."
        punch_info: LangStr

        #: ::
        #:
        #:     How-to text for the Run action.
        #:
        #:     English: "- Run - Hold ANY button to run. Triggers or shoulder
        #:     buttons work well if you have them. Running gets you places
        #:     faster but makes it hard to turn, so watch out for cliffs."
        run_info: LangStr

        #: ::
        #:
        #:     Opening humorous line in the help window.
        #:
        #:     English: "Some days you just feel like punching something. Or
        #:     blowing something up."
        some_days: LangStr

        def title(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Title of the help window.

                English: "{app_name} Help"
            """

        #: ::
        #:
        #:     Lead-in before the list of what you need.
        #:
        #:     English: "To get the most out of this game, you'll need:"
        to_get_the_most: LangStr

        def welcome(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Welcome heading in the help window.

                English: "Welcome to {app_name}!"
            """

    class StringsInGameMenuGroup:
        """
        ::

            In-game pause-menu strings: resume/end/leave buttons and their
            confirmation prompts.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Label for the in-game pause menu button that ends the current
        #:     game and returns to the menu.
        #:
        #:     English: "End Game"
        end_game: LangStr

        #: ::
        #:
        #:     Label for the in-game pause menu button that stops the replay
        #:     currently being viewed.
        #:
        #:     English: "End Replay"
        end_replay: LangStr

        #: ::
        #:
        #:     Label for the in-game pause menu button that ends the current
        #:     benchmark/test run (shown in place of the end-game button).
        #:
        #:     English: "End Test"
        end_test: LangStr

        #: ::
        #:
        #:     Confirmation question shown before ending the current game and
        #:     returning to the main menu.
        #:
        #:     English: "Exit to menu?"
        exit_to_menu_confirm: LangStr

        def just_player(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Small annotation under the leave-game button clarifying which
                player would leave (their name substituted in).

                English: "(Just {name})"
            """

        #: ::
        #:
        #:     Label for the in-game pause menu button that removes the pressing
        #:     player's character from the game (in local multiplayer with
        #:     several players).
        #:
        #:     English: "Leave Game"
        leave_game: LangStr

        #: ::
        #:
        #:     Label for the in-game pause menu button that disconnects from the
        #:     party (shown when connected to someone else's game).
        #:
        #:     English: "Leave Party"
        leave_party: LangStr

        #: ::
        #:
        #:     Confirmation question shown before disconnecting from a party via
        #:     the in-game menu.
        #:
        #:     English: "Really leave the party?"
        leave_party_confirm: LangStr

        #: ::
        #:
        #:     Label for the in-game pause menu button that closes the menu and
        #:     resumes playing.
        #:
        #:     English: "Resume"
        resume: LangStr

    class StringsInboxGroup:
        """
        ::

            Message-inbox window: messages, prizes, expiry labels.

            See source for the full asset list.
        """

        def expired_ago(self, *, t: str | LangStr) -> LangStr:
            """
            ::

                Label showing how long ago something expired.

                English: "Expired {t} ago"
            """

        def expires_in(self, *, t: str | LangStr) -> LangStr:
            """
            ::

                Label showing time until a message expires.

                English: "Expires in {t}"
            """

        #: ::
        #:
        #:     Heading for final tournament standings.
        #:
        #:     English: "Final Standings"
        final_standings: LangStr

        #: ::
        #:
        #:     Notice that the app must be updated to view content.
        #:
        #:     English: "You must update the app to view this."
        must_update: LangStr

        #: ::
        #:
        #:     Placeholder when the inbox is empty.
        #:
        #:     English: "No messages."
        no_messages: LangStr

        #: ::
        #:
        #:     Attention label on the root-UI inbox button when unopened prize
        #:     messages await.
        #:
        #:     English: "You have unclaimed prizes!"
        unclaimed_prizes: LangStr

        #: ::
        #:
        #:     Label above a prize the player won.
        #:
        #:     English: "Your prize:"
        your_prize: LangStr

    class StringsInventoryGroup:
        """
        ::

            Client-side inventory window bits: offline/signed-out placeholder
            variants (the online inventory content itself is server-composed).

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Inventory placeholder message.
        #:
        #:     English: "Full inventory is only available when online."
        only_available_online: LangStr

        #: ::
        #:
        #:     Inventory placeholder message.
        #:
        #:     English: "Full inventory is only available when signed in."
        only_available_signed_in: LangStr

        #: ::
        #:
        #:     Window title (client-side offline/profiles-only variants; the
        #:     online inventory title comes from the server).
        #:
        #:     English: "Inventory"
        title: LangStr

    class StringsKeyboardGroup:
        """
        ::

            Labels and instructions for the on-screen keyboard used for text
            entry on touch and controller devices.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Instructions for switching on-screen keyboards.
        #:
        #:     English: "Double press space to change keyboards."
        change_instructions: LangStr

        def configuring(self, *, device: str | LangStr) -> LangStr:
            """
            ::

                Title while remapping keys for a given keyboard device; the
                placeholder is the device name.

                English: "Configuring {device}"
            """

        #: ::
        #:
        #:     Notice that no other on-screen keyboards exist.
        #:
        #:     English: "No other keyboards available."
        no_others_available: LangStr

        #: ::
        #:
        #:     Label on the on-screen keyboard space bar.
        #:
        #:     English: "space"
        space_key: LangStr

        def switched(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Confirmation that the on-screen keyboard changed.

                English: "Keyboard switched to {name}"
            """

    class StringsKioskGroup:
        """
        ::

            Kiosk/demo-mode menu strings.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Title of the demo/kiosk menu.
        #:
        #:     English: "Demo Menu"
        demo_menu: LangStr

        #: ::
        #:
        #:     Button to open the full menu (kiosk).
        #:
        #:     English: "Full Menu"
        full_menu: LangStr

        #: ::
        #:
        #:     Kiosk section: single-player / co-op examples.
        #:
        #:     English: "Single Player / Co-op Examples"
        single_player_examples: LangStr

        #: ::
        #:
        #:     Kiosk section: versus examples.
        #:
        #:     English: "Versus Examples"
        versus_examples: LangStr

    class StringsLeagueGroup:
        """
        ::

            League/season UI: ranking labels, season timing notices, bonuses,
            and the league-president title.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Notice that achievement details are unavailable for past seasons.
        #:
        #:     English: "Sorry, achievement specifics are not available for old
        #:     seasons."
        achievements_unavailable_old_seasons: LangStr

        #: ::
        #:
        #:     Note that the activeness multiplier does not affect all-time
        #:     rankings. Shown from the league-rank window.
        #:
        #:     English: "This does not apply to all-time rankings."
        activeness_all_time_info: LangStr

        #: ::
        #:
        #:     Explains how the activeness multiplier rises and falls with daily
        #:     play. Shown from the league-rank window.
        #:
        #:     English: "This multiplier rises on days when you play and drops
        #:     on days when you do not."
        activeness_info: LangStr

        #: ::
        #:
        #:     Label for all-time (non-seasonal) stats.
        #:
        #:     English: "All Time"
        all_time: LangStr

        #: ::
        #:
        #:     Name of the Bronze league tier.
        #:
        #:     English: "Bronze"
        bronze: LangStr

        def current_season(self, *, number: str | LangStr) -> LangStr:
            """
            ::

                Label for the current season, with its number.

                English: "Current Season ({number})"
            """

        #: ::
        #:
        #:     Name of the Diamond league tier.
        #:
        #:     English: "Diamond"
        diamond: LangStr

        #: ::
        #:
        #:     Name of the Gold league tier.
        #:
        #:     English: "Gold"
        gold: LangStr

        #: ::
        #:
        #:     The "League" label/heading.
        #:
        #:     English: "League"
        league: LangStr

        #: ::
        #:
        #:     Title for the top-ranked player in a league.
        #:
        #:     English: "League President"
        league_president: LangStr

        #: ::
        #:
        #:     Label for the player's league rank.
        #:
        #:     English: "League Rank"
        league_rank: LangStr

        #: ::
        #:
        #:     Label for score multipliers.
        #:
        #:     English: "Multipliers"
        multipliers: LangStr

        def number_badge(self, *, number: str | LangStr) -> LangStr:
            """
            ::

                Rank-number badge (hash + number); substitution-only.

                English: "#{number}"
            """

        #: ::
        #:
        #:     Label for the power-ranking metric.
        #:
        #:     English: "Power Ranking"
        power_ranking: LangStr

        def power_ranking_points_equals(
            self, *, number: str | LangStr
        ) -> LangStr:
            """
            ::

                Badge showing a points equivalence in power ranking.

                English: "= {number} pts"
            """

        def power_ranking_points_mult(
            self, *, number: str | LangStr
        ) -> LangStr:
            """
            ::

                Badge showing a points multiplier in power ranking.

                English: "(x{number} pts)"
            """

        def rank_in_league(
            self,
            *,
            rank: str | LangStr,
            name: str | LangStr,
            suffix: str | LangStr,
        ) -> LangStr:
            """
            ::

                Compact line showing a player's numeric rank within a named
                league tier (account viewer / league standings). {rank} is the
                numeric rank, {name} the tier name (e.g. Bronze, Gold), {suffix}
                an optional trailing marker that is usually empty (layout code
                probes whether it lands at the end).

                English: "#{rank}, {name} League{suffix}"
            """

        def season(self, *, number: str | LangStr) -> LangStr:
            """
            ::

                Label naming a season by number.

                English: "Season {number}"
            """

        def season_ended_days_ago(self, *, days: int) -> LangStr:
            """
            ::

                Notice that a season ended a number of days ago.

                English: (one) "Season ended # day ago." / (other) "Season ended
                # days ago."
            """

        def season_ends_days(self, *, days: int) -> LangStr:
            """
            ::

                Notice that the season ends in a number of days.

                English: (one) "Season ends in # day." / (other) "Season ends in
                # days."
            """

        def season_ends_hours(self, *, hours: int) -> LangStr:
            """
            ::

                Notice that the season ends in a number of hours.

                English: (one) "Season ends in # hour." / (other) "Season ends
                in # hours."
            """

        def season_ends_minutes(self, *, minutes: int) -> LangStr:
            """
            ::

                Notice that the season ends in a number of minutes.

                English: (one) "Season ends in # minute." / (other) "Season ends
                in # minutes."
            """

        #: ::
        #:
        #:     Name of the Silver league tier.
        #:
        #:     English: "Silver"
        silver: LangStr

        #: ::
        #:
        #:     Label for points needed to become ranked.
        #:
        #:     English: "To Ranked"
        to_ranked: LangStr

        def tournament_required(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Notice that a higher league is required to enter.

                English: "You must reach the {name} league to enter this
                tournament."
            """

        #: ::
        #:
        #:     Notice that trophy counts reset each season.
        #:
        #:     English: "Trophy counts will reset next season."
        trophy_counts_reset: LangStr

        #: ::
        #:
        #:     Label for the up-to-date-version score bonus.
        #:
        #:     English: "Up-To-Date Bonus"
        up_to_date_bonus: LangStr

        def up_to_date_bonus_description(
            self, *, percent: str | LangStr
        ) -> LangStr:
            """
            ::

                Explanation of the up-to-date bonus, with the percentage.

                English: "Players running a recent version of the game receive a
                {percent}% bonus here."
            """

        #: ::
        #:
        #:     Label above the player's own power ranking.
        #:
        #:     English: "Your Power Ranking:"
        your_power_ranking: LangStr

    class StringsLobbyGroup:
        """
        ::

            Join-screen (lobby) prompts and labels shown while players are
            joining, picking profiles, and readying up.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     The bomb action word, shown emphasized in join prompts.
        #:
        #:     English: "BOMB"
        bomb: LangStr

        #: ::
        #:
        #:     Placeholder name while a player is still joining.
        #:
        #:     English: "<choosing player>"
        choosing_player: LangStr

        #: ::
        #:
        #:     Lobby profile-list entry for creating or editing a profile.
        #:
        #:     English: "<Create/Edit Player>"
        create_edit_player: LangStr

        #: ::
        #:
        #:     Prompt inviting anyone to join by pressing a button.
        #:
        #:     English: "press any button to join..."
        press_any_button_to_join: LangStr

        #: ::
        #:
        #:     Prompt to join by pressing the punch button.
        #:
        #:     English: "press PUNCH to join..."
        press_punch_to_join: LangStr

        def press_to_override_character(
            self, *, buttons: str | LangStr
        ) -> LangStr:
            """
            ::

                Prompt for overriding the profile character in the lobby.

                English: "press {buttons} to override your character"
            """

        def press_to_select_profile(self, *, buttons: str | LangStr) -> LangStr:
            """
            ::

                Prompt for selecting a player profile in the lobby.

                English: "press {buttons} to select a player"
            """

        def press_to_select_team(self, *, buttons: str | LangStr) -> LangStr:
            """
            ::

                Prompt for choosing a team in the lobby.

                English: "press {buttons} to select a team"
            """

        #: ::
        #:
        #:     Status note that a joining player is ready.
        #:
        #:     English: "ready"
        ready: LangStr

    class StringsMainMenuGroup:
        """
        ::

            Main-menu strings: menu buttons, build watermarks, and menu-scene
            status text.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Label for the main-menu button showing the game's credits.
        #:
        #:     English: "Credits"
        credits: LangStr

        #: ::
        #:
        #:     Label for the main-menu button that exits the app (general
        #:     wording; the Mac variant uses the 'Quit' string).
        #:
        #:     English: "Exit Game"
        exit_game: LangStr

        def host_navigating_menus(self, *, host: str | LangStr) -> LangStr:
            """
            ::

                Shown to connected clients while the party host is navigating
                menus (so they know why they are looking at an idle screen).

                English: "- {host} is navigating menus like a boss -"
            """

        #: ::
        #:
        #:     Label for the main-menu button opening the
        #:     how-to-play/instructions section.
        #:
        #:     English: "How to Play"
        how_to_play: LangStr

        #: ::
        #:
        #:     Label for the main-menu button switching the game into Arcade
        #:     mode (a simplified mode designed for stand-up arcade cabinets).
        #:
        #:     English: "Arcade Mode"
        mode_arcade: LangStr

        #: ::
        #:
        #:     Label for the main-menu button switching the game into Demo mode
        #:     (a simple mode providing a few gameplay examples instead of the
        #:     full experience).
        #:
        #:     English: "Demo Mode"
        mode_demo: LangStr

        #: ::
        #:
        #:     Heading shown in the main-menu ticker above the player's next
        #:     unearned achievements.
        #:
        #:     English: "Next Achievements:"
        next_achievements: LangStr

        #: ::
        #:
        #:     Label for the main-menu button that exits the app (wording used
        #:     on Mac, where apps are 'quit'; other platforms use the 'Exit
        #:     Game' string).
        #:
        #:     English: "Quit"
        quit: LangStr

        #: ::
        #:
        #:     Watermark label shown in the main menu on special test builds of
        #:     the game.
        #:
        #:     English: "Test Build"
        test_build: LangStr

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

    class StringsMultiTeamGroup:
        """
        ::

            Multi-team series victory and score screens: player-award headings
            (most valuable/violent/destroyed), the "SERIES!" banner, and the
            score-table column labels.

            See source for the full asset list.
        """

        def best_of_final(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                Title for a best-of-N final series.

                English: "Best-of-{count} Final"
            """

        def best_of_series(self, *, count: int) -> LangStr:
            """
            ::

                Title for a best-of-N series.

                English: (one) "Best Of # Series:" / (other) "Best Of # Series:"
            """

        #: ::
        #:
        #:     Column label for the death count in the score table.
        #:
        #:     English: "Deaths"
        deaths: LangStr

        def deaths_tally(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                A player's death count in the end-of-series tally.

                English: "{count} deaths"
            """

        def first_to_final(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                Title for a first-to-N-wins final series.

                English: "First-to-{count} Final"
            """

        def first_to_series(self, *, count: int) -> LangStr:
            """
            ::

                Title for a first-to-N-wins series.

                English: (one) "First-To-# Series" / (other) "First-To-# Series"
            """

        def game_leaders(self, *, count: int) -> LangStr:
            """
            ::

                Heading over the leaders of the current game.

                English: (one) "Game # Leaders" / (other) "Game # Leaders"
            """

        def games_to(
            self, *, wincount: str | LangStr, losecount: str | LangStr
        ) -> LangStr:
            """
            ::

                Series score line reading as wins-to-losses.

                English: "{wincount} games to {losecount}"
            """

        #: ::
        #:
        #:     Column label for the kill count in the score table.
        #:
        #:     English: "Kills"
        kills: LangStr

        def kills_tally(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                A player's kill count in the end-of-series tally.

                English: "{count} kills"
            """

        #: ::
        #:
        #:     Heading for the most-destroyed-player award.
        #:
        #:     English: "Most Destroyed Player"
        most_destroyed_player: LangStr

        #: ::
        #:
        #:     Heading for the most-valuable-player award.
        #:
        #:     English: "Most Valuable Player"
        most_valuable_player: LangStr

        #: ::
        #:
        #:     Heading for the most-violent-player award.
        #:
        #:     English: "Most Violent Player"
        most_violent_player: LangStr

        def must_invite_friends(self, *, gather: str | LangStr) -> LangStr:
            """
            ::

                Notice explaining how to get more players in.

                English: "Invite friends via {gather} or connect controllers to
                play."
            """

        #: ::
        #:
        #:     Column label for the player name in the score table.
        #:
        #:     English: "Player"
        player: LangStr

        #: ::
        #:
        #:     All-caps "SERIES!" celebration banner.
        #:
        #:     English: "SERIES!"
        series: LangStr

        def team_label(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Score-banner label naming a team.

                English: "{name}:"
            """

        #: ::
        #:
        #:     Label introducing the first game of a series.
        #:
        #:     English: "Up first:"
        up_first: LangStr

        def up_next(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                Label introducing the next game of a series.

                English: "Up next in game {count}:"
            """

        def wins(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Banner announcing the winner of a series.

                English: "{name} Wins!"
            """

        #: ::
        #:
        #:     Opening words of the series-victory banner.
        #:
        #:     English: "WINS THE"
        wins_the_series_intro: LangStr

    class StringsPartyGroup:
        """
        ::

            Party window: member list, chat, kick/mute controls.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Button to save a party to favorites.
        #:
        #:     English: "Add to Favorites"
        add_to_favorites: LangStr

        #: ::
        #:
        #:     Error when trying to kick the host.
        #:
        #:     English: "You can't kick the host."
        cant_kick_host: LangStr

        #: ::
        #:
        #:     Label for the chat message input.
        #:
        #:     English: "Chat Message"
        chat_message: LangStr

        #: ::
        #:
        #:     Status that chat is muted.
        #:
        #:     English: "Chat Muted"
        chat_muted: LangStr

        #: ::
        #:
        #:     Placeholder when the party has no members.
        #:
        #:     English: "Your party is empty"
        empty: LangStr

        #: ::
        #:
        #:     Parenthetical marker for the party host.
        #:
        #:     English: "(host)"
        host: LangStr

        #: ::
        #:
        #:     Button to start a vote to kick a player.
        #:
        #:     English: "Vote to Kick"
        kick_vote: LangStr

        #: ::
        #:
        #:     Menu choice to mute party chat.
        #:
        #:     English: "Mute Chat"
        mute_chat: LangStr

        #: ::
        #:
        #:     Title of the party window.
        #:
        #:     English: "Your Party"
        title: LangStr

        #: ::
        #:
        #:     Button to unmute chat.
        #:
        #:     English: "Unmute Chat"
        unmute_chat: LangStr

    class StringsPartyQueueGroup:
        """
        ::

            Party-join queue status messages.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Status while waiting in a full-party queue.
        #:
        #:     English: "Waiting in line (party is full)..."
        waiting_in_line: LangStr

    class StringsPlayGroup:
        """
        ::

            Play window: player-count range labels.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Player-count label 1-4.
        #:
        #:     English: "1-4 players"
        one_to_four_players: LangStr

        #: ::
        #:
        #:     Player-count label 2-8.
        #:
        #:     English: "2-8 players"
        two_to_eight_players: LangStr

    class StringsPlayModesGroup:
        """
        ::

            Play-mode names (Teams, Free-for-All, ...) shared across playlist
            UIs, session descriptions, and settings.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     The "Co-op" (cooperative) play-mode name.
        #:
        #:     English: "Co-op"
        coop: LangStr

        #: ::
        #:
        #:     The 'Free-for-All' play mode name (every player for themselves).
        #:
        #:     English: "Free-for-All"
        free_for_all: LangStr

        #: ::
        #:
        #:     The "Single Player / Co-op" play-mode name.
        #:
        #:     English: "Single Player / Co-op"
        single_player_coop: LangStr

        #: ::
        #:
        #:     The 'Teams' play mode name (used in playlist types, session
        #:     descriptions, etc.).
        #:
        #:     English: "Teams"
        teams: LangStr

    class StringsPlayOptionsGroup:
        """
        ::

            Playlist play-options: tutorial/shuffle toggles, team names/colors,
            unlock notices.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Error when a playlist has no playable games.
        #:
        #:     English: "This playlist contains no valid unlocked games."
        no_valid_games: LangStr

        #: ::
        #:
        #:     Setting label for the points needed to win.
        #:
        #:     English: "Points To Win"
        points_to_win: LangStr

        #: ::
        #:
        #:     Setting label for how many games a series runs.
        #:
        #:     English: "Series Length"
        series_length: LangStr

        #: ::
        #:
        #:     Checkbox to show the tutorial.
        #:
        #:     English: "Show Tutorial"
        show_tutorial: LangStr

        #: ::
        #:
        #:     Checkbox to shuffle the game order.
        #:
        #:     English: "Shuffle Game Order"
        shuffle_game_order: LangStr

        #: ::
        #:
        #:     Button to edit team names and colors.
        #:
        #:     English: "Team Names/Colors..."
        team_names_colors: LangStr

        #: ::
        #:
        #:     Note that an item must be unlocked in the store.
        #:
        #:     English: "This must be unlocked in the store."
        unlock_in_store: LangStr

    class StringsPlaylistGroup:
        """
        ::

            Playlist browser/editor UI:
            create/edit/delete/duplicate/share/import playlists and add/remove
            games.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Two-line button to add a game in the editor.
        #:
        #:     English: "Add Game"
        add_game_button: LangStr

        #: ::
        #:
        #:     Title of the add-game window.
        #:
        #:     English: "Add Game"
        add_game_title: LangStr

        #: ::
        #:
        #:     Error deleting the default playlist.
        #:
        #:     English: "You can't delete the default playlist."
        cant_delete_default: LangStr

        #: ::
        #:
        #:     Error editing the default playlist.
        #:
        #:     English: "Can't edit the default playlist! Duplicate it or create
        #:     a new one."
        cant_edit_default: LangStr

        #: ::
        #:
        #:     Error overwriting the default playlist.
        #:
        #:     English: "Can't overwrite the default playlist!"
        cant_overwrite_default: LangStr

        #: ::
        #:
        #:     Error when playlist name is taken.
        #:
        #:     English: "A playlist with that name already exists!"
        cant_save_already_exists: LangStr

        #: ::
        #:
        #:     Error saving an empty playlist.
        #:
        #:     English: "Can't save an empty playlist!"
        cant_save_empty: LangStr

        #: ::
        #:
        #:     Error sharing the default playlist.
        #:
        #:     English: "You can't share the default playlist."
        cant_share_default: LangStr

        def customize_title(self, *, type: str | LangStr) -> LangStr:
            """
            ::

                Title for the customize-playlists window.

                English: "Customize {type} Playlists"
            """

        def default_list_name(self, *, playmode: str | LangStr) -> LangStr:
            """
            ::

                Name of the built-in default playlist for a play mode.

                English: "Default {playmode} Playlist"
            """

        def default_new_list_name(self, *, playmode: str | LangStr) -> LangStr:
            """
            ::

                Default name offered for a newly created playlist.

                English: "My {playmode} Playlist"
            """

        #: ::
        #:
        #:     Two-line button to delete a playlist.
        #:
        #:     English: "Delete Playlist"
        delete_playlist: LangStr

        #: ::
        #:
        #:     Two-line button to duplicate a playlist.
        #:
        #:     English: "Duplicate Playlist"
        duplicate_playlist: LangStr

        #: ::
        #:
        #:     Two-line button to edit a game in the editor.
        #:
        #:     English: "Edit Game"
        edit_game_button: LangStr

        #: ::
        #:
        #:     Two-line button to edit a playlist.
        #:
        #:     English: "Edit Playlist"
        edit_playlist: LangStr

        #: ::
        #:
        #:     Title of the playlist editor window.
        #:
        #:     English: "Playlist Editor"
        editor_title: LangStr

        def export_success(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Confirmation after exporting a named playlist.

                English: "'{name}' exported."
            """

        #: ::
        #:
        #:     Button to get more game types.
        #:
        #:     English: "Get More Games..."
        get_more_games: LangStr

        #: ::
        #:
        #:     Button to get more maps.
        #:
        #:     English: "Get More Maps..."
        get_more_maps: LangStr

        #: ::
        #:
        #:     Instructions for importing a playlist by code.
        #:
        #:     English: "Use the following code to import this playlist
        #:     elsewhere:"
        import_instructions: LangStr

        def import_success(
            self, *, type: str | LangStr, name: str | LangStr
        ) -> LangStr:
            """
            ::

                Screen-message confirming a shared playlist was imported; {type}
                is the play-mode name (e.g. Teams, Free-for-All) and {name} the
                quoted playlist name.

                English: "Imported {type} playlist '{name}'"
            """

        #: ::
        #:
        #:     Name of the built-in slow-motion playlist.
        #:
        #:     English: "Just Epic"
        just_epic: LangStr

        #: ::
        #:
        #:     Name of the built-in sports-only playlist.
        #:
        #:     English: "Just Sports"
        just_sports: LangStr

        #: ::
        #:
        #:     Label for the playlist name field.
        #:
        #:     English: "Playlist Name"
        list_name: LangStr

        def map_select_title(self, *, game: str | LangStr) -> LangStr:
            """
            ::

                Title of the map-selection window.

                English: "{game}: Select a Map"
            """

        #: ::
        #:
        #:     Error screen-message when creating another playlist would exceed
        #:     the account limit.
        #:
        #:     English: "Max number of playlists reached."
        max_reached: LangStr

        #: ::
        #:
        #:     Two-line button to create a new playlist.
        #:
        #:     English: "New Playlist"
        new_playlist: LangStr

        #: ::
        #:
        #:     Error when no maps suit the game type.
        #:
        #:     English: "No valid maps found for this game type."
        no_valid_maps: LangStr

        #: ::
        #:
        #:     Title for the playlists list.
        #:
        #:     English: "Playlists"
        playlists: LangStr

        #: ::
        #:
        #:     Two-line button to remove a game in the editor.
        #:
        #:     English: "Remove Game"
        remove_game_button: LangStr

        def single_game_name(self, *, game: str | LangStr) -> LangStr:
            """
            ::

                Auto-generated playlist name for a playlist containing just one
                game; the placeholder is the game name.

                English: "Just {game}"
            """

    class StringsProfileGroup:
        """
        ::

            Player-profile editor strings: create/edit/delete profiles, the
            local/global/account profile explanations, and global-name upgrade
            flow.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Parenthetical marker labeling the account-based profile.
        #:
        #:     English: "(account profile)"
        account_profile: LangStr

        def account_profile_info(self, *, icons: str | LangStr) -> LangStr:
            """
            ::

                Explanation of what an account profile is.

                English: "This profile uses your account name and icon {icons}.
                Create custom profiles for different names or icons."
            """

        def available(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Status shown when a chosen global name is available.

                English: "The name {name} is available."
            """

        #: ::
        #:
        #:     Error when trying to delete the account profile.
        #:
        #:     English: "You can't delete your account profile."
        cant_delete_account_profile: LangStr

        #: ::
        #:
        #:     Lowercase field label for the profile character.
        #:
        #:     English: "character"
        character: LangStr

        def checking_availability(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Status shown while checking global-name availability.

                English: "Checking availability for "{name}"..."
            """

        #: ::
        #:
        #:     Lowercase field label for profile color.
        #:
        #:     English: "color"
        color: LangStr

        def delete_confirm(self, *, profile: str | LangStr) -> LangStr:
            """
            ::

                Confirmation before deleting a named profile.

                English: "Delete '{profile}'?"
            """

        #: ::
        #:
        #:     Button to get more player characters.
        #:
        #:     English: "Get More Characters..."
        get_more_characters: LangStr

        #: ::
        #:
        #:     Button to get more profile icons.
        #:
        #:     English: "Get More Icons..."
        get_more_icons: LangStr

        #: ::
        #:
        #:     Parenthetical marker labeling a global profile.
        #:
        #:     English: "(global profile)"
        global_profile: LangStr

        #: ::
        #:
        #:     Explanation of global profiles in the edit window.
        #:
        #:     English: "Global player profiles are guaranteed to have unique
        #:     names worldwide. They also include custom icons."
        global_profile_info: LangStr

        #: ::
        #:
        #:     Lowercase field label for profile highlight color.
        #:
        #:     English: "highlight"
        highlight: LangStr

        #: ::
        #:
        #:     Lowercase field label for profile icon.
        #:
        #:     English: "icon"
        icon: LangStr

        def in_game_clipped_name(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Preview of how a profile name appears in-game (possibly
                clipped).

                English: "In-game: {name}"
            """

        #: ::
        #:
        #:     Parenthetical marker labeling a local profile.
        #:
        #:     English: "(local profile)"
        local_profile: LangStr

        #: ::
        #:
        #:     Explanation of local profiles in the edit window.
        #:
        #:     English: "Local player profiles have no icons and their names are
        #:     not guaranteed to be unique. Upgrade to a global profile to
        #:     reserve a unique name and add a custom icon."
        local_profile_info: LangStr

        #: ::
        #:
        #:     Label for the profile name input field.
        #:
        #:     English: "Player Name"
        name_description: LangStr

        #: ::
        #:
        #:     Error when the profile name field is empty.
        #:
        #:     English: "Name cannot be empty!"
        name_not_empty: LangStr

        #: ::
        #:
        #:     Error when the player lacks enough tickets for an upgrade.
        #:
        #:     English: "Not enough Tickets!"
        not_enough_tickets: LangStr

        #: ::
        #:
        #:     Error when no item is selected.
        #:
        #:     English: "Nothing is selected!"
        nothing_selected: LangStr

        #: ::
        #:
        #:     Error when a profile name is already taken.
        #:
        #:     English: "A profile with that name already exists."
        profile_already_exists: LangStr

        #: ::
        #:
        #:     Status shown while a purchase is processing.
        #:
        #:     English: "Purchasing..."
        purchasing: LangStr

        #: ::
        #:
        #:     Title of the edit-profile window.
        #:
        #:     English: "Edit Profile"
        title_edit: LangStr

        #: ::
        #:
        #:     Title of the new-profile window.
        #:
        #:     English: "New Profile"
        title_new: LangStr

        def unavailable(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Status shown when a chosen global name is taken.

                English: ""{name}" is unavailable. Try another name."
            """

        #: ::
        #:
        #:     Explanation shown in the upgrade-to-global window.
        #:
        #:     English: "This will reserve your player name worldwide and allow
        #:     you to assign a custom icon to it."
        upgrade_profile_info: LangStr

        #: ::
        #:
        #:     Button/title to upgrade a profile to global.
        #:
        #:     English: "Upgrade to Global Profile"
        upgrade_to_global: LangStr

    class StringsProfilesGroup:
        """
        ::

            Player-profile management UI: profile lists, creation, and related
            hints.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Single-line parenthetical hint; keep the parentheses.
        #:
        #:     English: "(custom player names and appearances for this account)"
        explanation: LangStr

        #: ::
        #:
        #:     Error screen-message when creating another player profile would
        #:     exceed the account limit.
        #:
        #:     English: "Max number of profiles reached."
        max_reached: LangStr

        #: ::
        #:
        #:     Button label.
        #:
        #:     English: "New Profile"
        new_profile: LangStr

        #: ::
        #:
        #:     Section heading / window title for player-profile management.
        #:
        #:     English: "Player Profiles"
        title: LangStr

    class StringsReportGroup:
        """
        ::

            Player-report dialog: report reasons and explanation.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Report reason: cheating.
        #:
        #:     English: "Cheating"
        cheating: LangStr

        #: ::
        #:
        #:     Explanation atop the report dialog.
        #:
        #:     English: "Use this email to report cheating, inappropriate
        #:     language, or other bad behavior. Please describe below:"
        explanation: LangStr

        #: ::
        #:
        #:     Report reason: inappropriate language.
        #:
        #:     English: "Inappropriate Language"
        inappropriate_language: LangStr

        #: ::
        #:
        #:     Prompt asking what to report.
        #:
        #:     English: "What would you like to report?"
        reason: LangStr

    class StringsResourceTypeInfoGroup:
        """
        ::

            Currency info popups (tickets/tokens descriptions).

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Button to acquire tokens.
        #:
        #:     English: "Get Tokens"
        get_tokens: LangStr

        #: ::
        #:
        #:     Explanation of what tickets are and how to get them.
        #:
        #:     English: "Tickets can be used to unlock characters, maps,
        #:     minigames, and more in the store. Tickets can be found in chests
        #:     won through campaigns, tournaments, and achievements."
        tickets_description: LangStr

        #: ::
        #:
        #:     Explanation of what tokens are and how to get them.
        #:
        #:     English: "Tokens are used to speed up Chest unlocks and for other
        #:     game and account features. You can win Tokens in the game or buy
        #:     them in packs. Or buy a Gold Pass for infinite Tokens and never
        #:     hear about them again."
        tokens_description: LangStr

    class StringsScoreTypesGroup:
        """
        ::

            Column labels naming what a game's score measures (goals, flags,
            time survived, and so on) on score tables.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Score-column label for flags captured.
        #:
        #:     English: "Flags"
        flags: LangStr

        #: ::
        #:
        #:     Score-column label for goals scored.
        #:
        #:     English: "Goals"
        goals: LangStr

        #: ::
        #:
        #:     Score-column label for time survived.
        #:
        #:     English: "Survived"
        survived: LangStr

        #: ::
        #:
        #:     Score-column label for elapsed time.
        #:
        #:     English: "Time"
        time: LangStr

        #: ::
        #:
        #:     Score-column label for time spent holding something.
        #:
        #:     English: "Time Held"
        time_held: LangStr

    class StringsSendInfoGroup:
        """
        ::

            Send-info / promo-code dialog strings.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Explanation in the send-info dialog.
        #:
        #:     English: "Sends account and app state info to the developer.
        #:     Please include your name or reason for sending."
        send_info_description: LangStr

    class StringsServerGroup:
        """
        ::

            Broadcast messages sent to connected players about the hosting
            server's lifecycle.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Broadcast that the server is restarting.
        #:
        #:     English: "Server is restarting. Please rejoin in a moment..."
        restarting: LangStr

        #: ::
        #:
        #:     Broadcast that the server is shutting down.
        #:
        #:     English: "Server is shutting down..."
        shutting_down: LangStr

    class StringsSessionGroup:
        """
        ::

            Session-level player-flow broadcast messages: joins, departures, and
            player-limit notices.

            See source for the full asset list.
        """

        def not_enough_players(self, *, count: int) -> LangStr:
            """
            ::

                Warning that more players are needed to start.

                English: (one) "You need at least # player to start this game!"
                / (other) "You need at least # players to start this game!"
            """

        def player_delayed_join(self, *, player: str | LangStr) -> LangStr:
            """
            ::

                Notice that a joining player enters next round.

                English: "{player} will enter at the start of the next round."
            """

        def player_left(self, *, player: str | LangStr) -> LangStr:
            """
            ::

                Broadcast that a named player left the game.

                English: "{player} left the game."
            """

        def player_limit_reached(self, *, count: int) -> LangStr:
            """
            ::

                Notice that the session player limit blocks joining.

                English: (one) "Player limit of # reached; no more players can
                join." / (other) "Player limit of # reached; no more players can
                join."
            """

    class StringsSettingsAdvancedGroup:
        """
        ::

            Advanced-settings strings: language/translation section and misc
            toggles.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Checkbox forcing the in-game on-screen keyboard for text entry.
        #:
        #:     English: "Always Use Internal Keyboard"
        always_use_internal_keyboard: LangStr

        #: ::
        #:
        #:     Explanation under the always-use-internal-keyboard checkbox.
        #:
        #:     English: "(a simple, controller-friendly on-screen keyboard for
        #:     text editing)"
        always_use_internal_keyboard_description: LangStr

        #: ::
        #:
        #:     Checkbox disabling gyroscope-driven camera motion (mobile).
        #:
        #:     English: "Disable Camera Gyroscope Motion"
        disable_camera_gyro: LangStr

        #: ::
        #:
        #:     Checkbox disabling camera-shake effects.
        #:
        #:     English: "Disable Camera Shake"
        disable_camera_shake: LangStr

        def help_translate(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Blurb asking for community translation help, above the
                translation-site link.

                English: "{app_name}'s non-English translations are a community
                supported effort. If you'd like to contribute or correct a
                translation, follow the link below. Thanks in advance!"
            """

        #: ::
        #:
        #:     Checkbox allowing non-TLS server connections (a
        #:     network-workaround option).
        #:
        #:     English: "Use Insecure Connections"
        insecure_connections: LangStr

        #: ::
        #:
        #:     Explanation under the insecure-connections checkbox.
        #:
        #:     English: "not recommended, but may allow online play from
        #:     restricted countries or networks"
        insecure_connections_description: LangStr

        #: ::
        #:
        #:     Checkbox auto-kicking idle players.
        #:
        #:     English: "Kick Idle Players"
        kick_idle_players: LangStr

        #: ::
        #:
        #:     Selector for the display language.
        #:
        #:     English: "Language"
        language: LangStr

        #: ::
        #:
        #:     Button linking to the online modding guide.
        #:
        #:     English: "Modding Guide"
        modding_guide: LangStr

        #: ::
        #:
        #:     Button for submitting info/logs to the developer (also used for
        #:     entering promo codes).
        #:
        #:     English: "Send Info"
        send_info: LangStr

        #: ::
        #:
        #:     Checkbox playing demo games when idle.
        #:
        #:     English: "Show Demos When Idle"
        show_demos_when_idle: LangStr

        #: ::
        #:
        #:     Checkbox revealing deprecated login options.
        #:
        #:     English: "Show Deprecated Login Types"
        show_deprecated_login_types: LangStr

        #: ::
        #:
        #:     Checkbox showing network ping during games.
        #:
        #:     English: "Show In-Game Ping"
        show_in_game_ping: LangStr

        #: ::
        #:
        #:     Button revealing the user mods folder.
        #:
        #:     English: "Show Mods Folder"
        show_mods_folder: LangStr

        #: ::
        #:
        #:     Label for the advanced-settings category: language, promo codes,
        #:     developer options, and other misc settings.
        #:
        #:     English: "Advanced"
        title: LangStr

        #: ::
        #:
        #:     Status line while the translation status loads.
        #:
        #:     English: "checking translation status..."
        translation_checking: LangStr

        def translation_editor(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Button linking to the web translation editor.

                English: "{app_name} Translation Editor"
            """

        #: ::
        #:
        #:     Status line when the translation-status query fails.
        #:
        #:     English: "translation status unavailable"
        translation_fetch_error: LangStr

        #: ::
        #:
        #:     Checkbox subscribing to translation-update notifications for the
        #:     user's language.
        #:
        #:     English: "Inform me when my language needs updates"
        translation_inform_me: LangStr

        #: ::
        #:
        #:     Status line when the current language has missing/outdated
        #:     translations.
        #:
        #:     English: "** The current language needs updates!! **"
        translation_needs_updates: LangStr

        #: ::
        #:
        #:     Status line when the current language needs no translation
        #:     updates.
        #:
        #:     English: "The current language is up to date; woohoo!"
        translation_up_to_date: LangStr

    class StringsSettingsAudioGroup:
        """
        ::

            Audio-settings strings.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Slider for music volume.
        #:
        #:     English: "Music Volume"
        music_volume: LangStr

        #: ::
        #:
        #:     Slider for sound-effects volume.
        #:
        #:     English: "Sound Volume"
        sound_volume: LangStr

        #: ::
        #:
        #:     Explanation under the soundtracks button.
        #:
        #:     English: "(assign your own music to play during games)"
        soundtrack_description: LangStr

        #: ::
        #:
        #:     Button opening the custom-soundtracks feature.
        #:
        #:     English: "Soundtracks"
        soundtracks: LangStr

        #: ::
        #:
        #:     Label for the audio-settings category: volume levels and related
        #:     sound options.
        #:
        #:     English: "Audio"
        title: LangStr

    class StringsSettingsBenchmarksGroup:
        """
        ::

            Benchmark & stress-test window strings.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Error when starting a benchmark while another activity is running
        #:     one.
        #:
        #:     English: "Already present in another activity."
        already_running_in_activity: LangStr

        #: ::
        #:
        #:     Selector for stress-test bot count.
        #:
        #:     English: "Player Count"
        player_count: LangStr

        #: ::
        #:
        #:     Description heading for the stress-test playlist.
        #:
        #:     English: "Stress Test Playlist"
        playlist_description: LangStr

        #: ::
        #:
        #:     Field for stress-test playlist name.
        #:
        #:     English: "Playlist Name"
        playlist_name: LangStr

        #: ::
        #:
        #:     Selector for stress-test playlist type.
        #:
        #:     English: "Playlist Type"
        playlist_type: LangStr

        #: ::
        #:
        #:     Selector for stress-test round length.
        #:
        #:     English: "Round Duration"
        round_duration: LangStr

        #: ::
        #:
        #:     Button running the CPU benchmark.
        #:
        #:     English: "Run CPU Benchmark"
        run_cpu_benchmark: LangStr

        #: ::
        #:
        #:     Button running the media-reload benchmark.
        #:
        #:     English: "Run Media-Reload Benchmark"
        run_media_reload_benchmark: LangStr

        #: ::
        #:
        #:     Button starting a stress test.
        #:
        #:     English: "Run Stress Test"
        run_stress_test: LangStr

        #: ::
        #:
        #:     Section heading for the stress-test options.
        #:
        #:     English: "Stress Test"
        stress_test: LangStr

        #: ::
        #:
        #:     Title of the benchmarks window; also labels the button leading
        #:     there.
        #:
        #:     English: "Benchmarks & Stress Tests"
        title: LangStr

    class StringsSettingsControllersGamepadGroup:
        """
        ::

            Game-controller (gamepad) config-window strings: button assignment
            prompts and advanced options.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Title of the advanced controller-setup window.
        #:
        #:     English: "Advanced Controller Setup"
        advanced_title: LangStr

        #: ::
        #:
        #:     Slider for the analog-stick dead zone.
        #:
        #:     English: "Analog Stick Dead Zone"
        analog_stick_dead_zone: LangStr

        #: ::
        #:
        #:     Explanation under the dead-zone slider.
        #:
        #:     English: "(turn this up if your character 'drifts' when you
        #:     release the stick)"
        analog_stick_dead_zone_description: LangStr

        #: ::
        #:
        #:     Note that controller-setup changes apply to every controller of
        #:     the same type.
        #:
        #:     English: "(applies to all controllers of this type)"
        applies_to_all: LangStr

        #: ::
        #:
        #:     Checkbox enabling analog-stick auto-recalibration.
        #:
        #:     English: "Auto-Recalibrate Analog Stick"
        auto_recalibrate: LangStr

        #: ::
        #:
        #:     Explanation under the auto-recalibrate checkbox.
        #:
        #:     English: "(enable this if your character does not move at full
        #:     speed)"
        auto_recalibrate_description: LangStr

        #: ::
        #:
        #:     Tiny action label clearing one button assignment.
        #:
        #:     English: "clear"
        clear: LangStr

        #: ::
        #:
        #:     Tiny label for a controller's directional pad in the button
        #:     diagram.
        #:
        #:     English: "D-Pad"
        dpad: LangStr

        def dpad_numbered(self, *, num: int) -> LangStr:
            """
            ::

                Label for a numbered directional pad in the controller-setup
                diagram (2-in-1 devices have two).

                English: (one) "dpad #" / (other) "dpad #"
            """

        #: ::
        #:
        #:     Checkbox enabling the secondary-controller feature.
        #:
        #:     English: "Enable"
        enable: LangStr

        #: ::
        #:
        #:     Assignment slot for an additional start button.
        #:
        #:     English: "Extra Start Button"
        extra_start_button: LangStr

        #: ::
        #:
        #:     Hint shown when a dpad capture gets no input.
        #:
        #:     English: "If nothing happens, try assigning to the analog stick
        #:     instead."
        if_nothing_try_analog: LangStr

        #: ::
        #:
        #:     Hint shown when an analog-stick capture gets no input.
        #:
        #:     English: "If nothing happens, try assigning to the d-pad
        #:     instead."
        if_nothing_try_dpad: LangStr

        #: ::
        #:
        #:     Checkbox making the game ignore this controller entirely.
        #:
        #:     English: "Ignore Completely"
        ignore_completely: LangStr

        #: ::
        #:
        #:     Explanation under the ignore-completely checkbox.
        #:
        #:     English: "(prevent this controller from affecting either the game
        #:     or menus)"
        ignore_completely_description: LangStr

        def ignored_button(self, *, num: int) -> LangStr:
            """
            ::

                Assignment slot for a numbered button the game should ignore
                (slots 1-4).

                English: (one) "Ignored Button #" / (other) "Ignored Button #"
            """

        #: ::
        #:
        #:     Explanation under the ignored-button assignments.
        #:
        #:     English: "(use this to prevent 'home' or 'sync' buttons from
        #:     affecting the UI)"
        ignored_button_description: LangStr

        #: ::
        #:
        #:     Prompt while capturing an analog trigger assignment.
        #:
        #:     English: "Press any analog trigger..."
        press_any_analog_trigger: LangStr

        #: ::
        #:
        #:     Prompt while capturing which physical button to assign.
        #:
        #:     English: "Press any button..."
        press_any_button: LangStr

        #: ::
        #:
        #:     Prompt while capturing a button or dpad press.
        #:
        #:     English: "Press any button or dpad..."
        press_any_button_or_dpad: LangStr

        #: ::
        #:
        #:     Prompt while capturing a horizontal axis assignment.
        #:
        #:     English: "Press left or right..."
        press_left_right: LangStr

        #: ::
        #:
        #:     Prompt while capturing a vertical axis assignment.
        #:
        #:     English: "Press up or down..."
        press_up_down: LangStr

        def run_button(self, *, num: int) -> LangStr:
            """
            ::

                Assignment slot for a numbered run button (1 or 2).

                English: (one) "Run Button #" / (other) "Run Button #"
            """

        def run_trigger(self, *, num: int) -> LangStr:
            """
            ::

                Assignment slot for a numbered analog run trigger (1 or 2).

                English: (one) "Run Trigger #" / (other) "Run Trigger #"
            """

        #: ::
        #:
        #:     Explanation under the run-trigger assignments.
        #:
        #:     English: "(analog triggers let you run at variable speeds)"
        run_trigger_description: LangStr

        #: ::
        #:
        #:     Explanation of the secondary-controller feature for
        #:     2-controllers-in-1 devices.
        #:
        #:     English: "Use this to configure the second half of a
        #:     2-controllers-in-1 device that shows up as a single controller."
        second_half: LangStr

        #: ::
        #:
        #:     Section title for the secondary-controller settings.
        #:
        #:     English: "Secondary Controller"
        secondary: LangStr

        #: ::
        #:
        #:     Checkbox making the start button activate the default widget.
        #:
        #:     English: "Start Button Activates Default Widget"
        start_button_activates_default: LangStr

        #: ::
        #:
        #:     Explanation under the start-button checkbox.
        #:
        #:     English: "(turn this off if your start button is more of a 'menu'
        #:     button)"
        start_button_activates_default_description: LangStr

        #: ::
        #:
        #:     Title of the controller-setup window (assigning buttons for one
        #:     controller type).
        #:
        #:     English: "Controller Setup"
        title: LangStr

        #: ::
        #:
        #:     Button opening the 2-controllers-in-1 setup section.
        #:
        #:     English: "2-in-1 Controller Setup"
        two_in_one_setup: LangStr

        #: ::
        #:
        #:     Checkbox limiting this controller to menu navigation.
        #:
        #:     English: "Limit to Menu Use"
        ui_only: LangStr

        #: ::
        #:
        #:     Explanation under the menu-use-only checkbox.
        #:
        #:     English: "(prevent this controller from actually joining a game)"
        ui_only_description: LangStr

        #: ::
        #:
        #:     Checkbox making all unassigned buttons act as run.
        #:
        #:     English: "All Unassigned Buttons Run"
        unassigned_buttons_run: LangStr

        #: ::
        #:
        #:     Placeholder shown for a button assignment with no value.
        #:
        #:     English: "<unset>"
        unset: LangStr

        #: ::
        #:
        #:     Assignment slot for the VR view-reset button.
        #:
        #:     English: "VR Reorient Button"
        vr_reorient_button: LangStr

    class StringsSettingsControllersKeyboardGroup:
        """
        ::

            Keyboard config-window strings.

            See source for the full asset list.
        """

        def configuring(self, *, device: str | LangStr) -> LangStr:
            """
            ::

                Title of the keyboard-config window, naming the device being
                configured.

                English: "Configuring {device}"
            """

        #: ::
        #:
        #:     Note in the second-keyboard-player config about hardware keypress
        #:     limits.
        #:
        #:     English: "Note: most keyboards can only register a few keypresses
        #:     at once, so having a second keyboard player may work better if
        #:     there is a separate keyboard attached for them to use. Note that
        #:     you'll still need to assign unique keys to the two players even
        #:     in that case."
        keyboard2_note: LangStr

        #: ::
        #:
        #:     Prompt while capturing which key to assign.
        #:
        #:     English: "Press any key..."
        press_any_key: LangStr

    class StringsSettingsControllersTouchscreenGroup:
        """
        ::

            Touchscreen config-window strings.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Slider for action-control size.
        #:
        #:     English: "Action Control Scale"
        action_control_scale: LangStr

        #: ::
        #:
        #:     Section heading for action-control options.
        #:
        #:     English: "Actions"
        actions: LangStr

        #: ::
        #:
        #:     Option value: actions via on-screen buttons.
        #:
        #:     English: "buttons"
        buttons: LangStr

        #: ::
        #:
        #:     Hint that the on-screen controls can be dragged to reposition.
        #:
        #:     English: "< drag controls to reposition them >"
        drag_controls: LangStr

        #: ::
        #:
        #:     Option value: movement via an on-screen joystick.
        #:
        #:     English: "Joystick"
        joystick: LangStr

        #: ::
        #:
        #:     Section heading for movement-control options.
        #:
        #:     English: "Movement"
        movement: LangStr

        #: ::
        #:
        #:     Slider for movement-control size.
        #:
        #:     English: "Movement Control Scale"
        movement_control_scale: LangStr

        #: ::
        #:
        #:     Option value: controls via swiping.
        #:
        #:     English: "swipe"
        swipe: LangStr

        #: ::
        #:
        #:     Checkbox hiding the swipe-control icons.
        #:
        #:     English: "Hide Swipe Icons"
        swipe_controls_hidden: LangStr

        #: ::
        #:
        #:     Explanation of swipe-style controls.
        #:
        #:     English: "'Swipe' style controls take a little getting used to
        #:     but make it easier to play without looking at the controls."
        swipe_info: LangStr

        #: ::
        #:
        #:     Title of the touchscreen-controls config window; also labels the
        #:     button leading there.
        #:
        #:     English: "Configure Touchscreen"
        title: LangStr

    class StringsSettingsControllersGroup:
        """
        ::

            Controller-settings strings: the category title, hub buttons, and
            device-config notes; per-device-type config windows live in subdirs.

            See source for the full asset list.
        """

        gamepad: StringsSettingsControllersGamepadGroup
        keyboard: StringsSettingsControllersKeyboardGroup
        touchscreen: StringsSettingsControllersTouchscreenGroup

        #: ::
        #:
        #:     Note about controller-support variability on Android.
        #:
        #:     English: "Note: controller support varies by device and Android
        #:     version."
        android_note: LangStr

        def cant_configure_device(self, *, device: str | LangStr) -> LangStr:
            """
            ::

                Note shown for input devices that have no configurable options.

                English: "Sorry, {device} is not configurable."
            """

        #: ::
        #:
        #:     Button/title for configuring game controllers (controllers
        #:     settings window and the controller-select window title).
        #:
        #:     English: "Configure Controllers"
        configure_controllers: LangStr

        def configure_in_system_settings(
            self, *, device: str | LangStr
        ) -> LangStr:
            """
            ::

                Note for devices configured via the OS settings app instead of
                in-game.

                English: "{device} can be configured in the System Settings
                app."
            """

        #: ::
        #:
        #:     Button leading to keyboard player-1 key configuration.
        #:
        #:     English: "Configure Keyboard"
        configure_keyboard: LangStr

        #: ::
        #:
        #:     Button leading to keyboard player-2 key configuration.
        #:
        #:     English: "Configure Keyboard P2"
        configure_keyboard_p2: LangStr

        #: ::
        #:
        #:     Button leading to info about using phones/tablets as controllers.
        #:
        #:     English: "Mobile Devices as Controllers"
        configure_mobile: LangStr

        #: ::
        #:
        #:     Checkbox disabling incoming remote-app controller connections.
        #:
        #:     English: "Disable Remote-App Connections"
        disable_remote_app: LangStr

        #: ::
        #:
        #:     Windows-only checkbox disabling the XInput controller API.
        #:
        #:     English: "Disable XInput"
        disable_xinput: LangStr

        #: ::
        #:
        #:     Explanation under the disable-XInput checkbox.
        #:
        #:     English: "Allows more than 4 controllers but may not work as
        #:     well."
        disable_xinput_description: LangStr

        #: ::
        #:
        #:     Prompt in the controller-select window; displays until a button
        #:     is pressed on the controller to be configured.
        #:
        #:     English: "Press any button on the controller you want to
        #:     configure..."
        press_any_button_to_configure: LangStr

        #: ::
        #:
        #:     Wifi-quality advice in the mobile-devices-as-controllers info
        #:     window.
        #:
        #:     English: "For best results you'll need a lag-free wifi network.
        #:     You can reduce wifi lag by turning off other wireless devices, by
        #:     playing close to your wifi router, and by connecting the game
        #:     host directly to the network via ethernet."
        remote_best_results: LangStr

        def remote_configured_in_app(
            self, *, remote_app_name: str | LangStr
        ) -> LangStr:
            """
            ::

                Note shown when trying to configure the remote-control phone app
                as a controller; its settings live in that app.

                English: "{remote_app_name} is configured in the app itself."
            """

        def remote_explanation(
            self, *, remote_app_name: str | LangStr, app_name: str | LangStr
        ) -> LangStr:
            """
            ::

                Explanation in the mobile-devices-as-controllers info window;
                names the remote app and the game.

                English: "To use a smart-phone or tablet as a wireless
                controller, install the "{remote_app_name}" app on it. Any
                number of devices can connect to a {app_name} game over Wi-Fi,
                and it's free!"
            """

        #: ::
        #:
        #:     Label for the controller-settings category: game controllers,
        #:     keyboards, touch screens, and remote-control setup.
        #:
        #:     English: "Controllers"
        title: LangStr

    class StringsSettingsDevToolsGroup:
        """
        ::

            Dev-tools window strings.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Button copying system scripts into the user scripts dir for
        #:     modding.
        #:
        #:     English: "Create User System Scripts"
        create_user_system_scripts: LangStr

        #: ::
        #:
        #:     Button deleting the user copy of system scripts.
        #:
        #:     English: "Delete User System Scripts"
        delete_user_system_scripts: LangStr

        #: ::
        #:
        #:     Checkbox showing the on-screen dev-console button.
        #:
        #:     English: "Show Dev Console Button"
        show_dev_console_button: LangStr

        #: ::
        #:
        #:     Title of the dev-tools window; also labels the button leading
        #:     there.
        #:
        #:     English: "Dev Tools"
        title: LangStr

    class StringsSettingsGraphicsGroup:
        """
        ::

            Graphics-settings strings: the category title and option labels
            (shared quality words like Low/High live in strings/ui).

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Checkbox toggling fullscreen display.
        #:
        #:     English: "Fullscreen"
        fullscreen: LangStr

        def fullscreen_shortcut_format(
            self, *, name: str | LangStr, shortcut: str | LangStr
        ) -> LangStr:
            """
            ::

                Format joining the fullscreen checkbox label with its keyboard
                shortcut; pure substitution.

                English: "{name} [{shortcut}]"
            """

        #: ::
        #:
        #:     Selector for the frame-rate cap.
        #:
        #:     English: "Max FPS"
        max_fps: LangStr

        #: ::
        #:
        #:     Resolution option meaning the display's native resolution.
        #:
        #:     English: "Native"
        native: LangStr

        #: ::
        #:
        #:     Selector for render resolution.
        #:
        #:     English: "Resolution"
        resolution: LangStr

        #: ::
        #:
        #:     Checkbox showing the FPS counter.
        #:
        #:     English: "Show FPS"
        show_fps: LangStr

        #: ::
        #:
        #:     Selector for texture quality.
        #:
        #:     English: "Textures"
        textures: LangStr

        #: ::
        #:
        #:     Label for the graphics-settings category: resolution, quality,
        #:     fullscreen, and similar visual options.
        #:
        #:     English: "Graphics"
        title: LangStr

        #: ::
        #:
        #:     Checkbox adding a safe-area border for TVs.
        #:
        #:     English: "TV Border"
        tv_border: LangStr

        #: ::
        #:
        #:     Selector for vertical sync.
        #:
        #:     English: "Vertical Sync"
        vertical_sync: LangStr

        #: ::
        #:
        #:     Selector for overall visual quality.
        #:
        #:     English: "Visuals"
        visuals: LangStr

    class StringsSettingsNetTestingGroup:
        """
        ::

            Network-testing window strings.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Title of the network-testing window; also labels the button
        #:     leading there.
        #:
        #:     English: "Network Testing"
        title: LangStr

    class StringsSettingsPluginsGroup:
        """
        ::

            Plugin-management strings.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Checkbox auto-enabling newly-found plugins.
        #:
        #:     English: "Auto Enable New Plugins"
        auto_enable_new: LangStr

        #: ::
        #:
        #:     Button disabling every installed plugin.
        #:
        #:     English: "Disable All Plugins"
        disable_all: LangStr

        #: ::
        #:
        #:     Button enabling every installed plugin.
        #:
        #:     English: "Enable All Plugins"
        enable_all: LangStr

        #: ::
        #:
        #:     Placeholder when the plugins list is empty.
        #:
        #:     English: "No Plugins Installed"
        none_installed: LangStr

        #: ::
        #:
        #:     Title of the plugin-settings window.
        #:
        #:     English: "Plugin Settings"
        settings_title: LangStr

        #: ::
        #:
        #:     Title of the plugins window; also labels buttons leading there.
        #:
        #:     English: "Plugins"
        title: LangStr

    class StringsSettingsTestingGroup:
        """
        ::

            Shared strings for the value-testing windows (net/VR testing
            subclasses).

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Note atop value-testing windows that tweaks are session-only.
        #:
        #:     English: "Note: these values are only for testing and will be
        #:     lost when the app exits."
        for_testing_note: LangStr

    class StringsSettingsVrTestingGroup:
        """
        ::

            VR-testing window strings.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Title of the VR-testing window; also labels the button leading
        #:     there.
        #:
        #:     English: "VR Testing"
        title: LangStr

    class StringsSettingsGroup:
        """
        ::

            Settings-section strings: the hub window title and category names
            (each category name also titles its own sub-window).

            See source for the full asset list.
        """

        advanced: StringsSettingsAdvancedGroup
        audio: StringsSettingsAudioGroup
        benchmarks: StringsSettingsBenchmarksGroup
        controllers: StringsSettingsControllersGroup
        dev_tools: StringsSettingsDevToolsGroup
        graphics: StringsSettingsGraphicsGroup
        net_testing: StringsSettingsNetTestingGroup
        plugins: StringsSettingsPluginsGroup
        testing: StringsSettingsTestingGroup
        vr_testing: StringsSettingsVrTestingGroup

        #: ::
        #:
        #:     Title of the settings section (the hub window listing the
        #:     settings categories); also labels buttons leading there.
        #:
        #:     English: "Settings"
        title: LangStr

    class StringsSoundtrackGroup:
        """
        ::

            Custom-soundtrack editor strings: soundtrack list/edit/delete, music
            source picker, and playlist selection.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Error when trying to delete the default soundtrack.
        #:
        #:     English: "You can't delete the default soundtrack."
        cant_delete_default: LangStr

        #: ::
        #:
        #:     Error when trying to edit the default soundtrack.
        #:
        #:     English: "Can't edit default soundtrack. Duplicate it or create a
        #:     new one."
        cant_edit_default: LangStr

        #: ::
        #:
        #:     Error when trying to overwrite the default soundtrack.
        #:
        #:     English: "Can't overwrite default soundtrack"
        cant_overwrite_default: LangStr

        #: ::
        #:
        #:     Error when saving a soundtrack whose name is already taken.
        #:
        #:     English: "A soundtrack with that name already exists!"
        cant_save_already_exists: LangStr

        def copy_of(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Auto-generated name for a duplicated soundtrack.

                English: "{name} Copy"
            """

        #: ::
        #:
        #:     Placeholder label for an entry that plays the game's default
        #:     music.
        #:
        #:     English: "<default game music>"
        default_game_music: LangStr

        #: ::
        #:
        #:     Name of the built-in default soundtrack.
        #:
        #:     English: "Default Soundtrack"
        default_soundtrack_name: LangStr

        def delete_confirm(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Confirmation prompt before deleting a named soundtrack.

                English: "Delete soundtrack '{name}'?"
            """

        #: ::
        #:
        #:     Two-line button label to delete a soundtrack.
        #:
        #:     English: "Delete Soundtrack"
        delete_soundtrack: LangStr

        #: ::
        #:
        #:     Two-line button label to duplicate a soundtrack.
        #:
        #:     English: "Duplicate Soundtrack"
        duplicate_soundtrack: LangStr

        #: ::
        #:
        #:     Two-line button label to edit a soundtrack.
        #:
        #:     English: "Edit Soundtrack"
        edit_soundtrack: LangStr

        def error_playing_music(self, *, music: str | LangStr) -> LangStr:
            """
            ::

                Error message that a music file would not play.

                English: "Error playing music: {music}"
            """

        #: ::
        #:
        #:     Status while loading Music-app playlists.
        #:
        #:     English: "fetching Music App playlists..."
        fetching_itunes: LangStr

        #: ::
        #:
        #:     Title of the music-source picker.
        #:
        #:     English: "Music Source"
        music_source: LangStr

        #: ::
        #:
        #:     Warning shown in the editor when music volume is muted.
        #:
        #:     English: "Warning: music volume is set to 0"
        music_volume_zero_warning: LangStr

        #: ::
        #:
        #:     Two-line button label to create a new soundtrack.
        #:
        #:     English: "New Soundtrack"
        new_soundtrack: LangStr

        def new_soundtrack_name(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                Auto-generated default name for a newly-created soundtrack.

                English: "My Soundtrack {count}"
            """

        #: ::
        #:
        #:     Notice that a chosen folder holds no music.
        #:
        #:     English: "Folder contains no music files."
        no_music_files_in_folder: LangStr

        #: ::
        #:
        #:     Title of the Music-app playlist picker.
        #:
        #:     English: "Select A Playlist"
        select_a_playlist: LangStr

        #: ::
        #:
        #:     Tiny lowercase "test" button to preview a music entry.
        #:
        #:     English: "test"
        test: LangStr

        #: ::
        #:
        #:     Title of the soundtracks section; also labels the button leading
        #:     there.
        #:
        #:     English: "Soundtracks"
        title: LangStr

        #: ::
        #:
        #:     Music-source option: the built-in game music.
        #:
        #:     English: "Default Game Music"
        use_default_game_music: LangStr

        #: ::
        #:
        #:     Music-source option: a playlist from the system Music app.
        #:
        #:     English: "Music App Playlist"
        use_itunes_playlist: LangStr

        #: ::
        #:
        #:     Music-source option: a single music file.
        #:
        #:     English: "Music File (mp3, etc)"
        use_music_file: LangStr

        #: ::
        #:
        #:     Music-source option: a folder of music files.
        #:
        #:     English: "Folder of Music Files"
        use_music_folder: LangStr

        #: ::
        #:
        #:     Notice that the OS music app supplies the soundtrack.
        #:
        #:     English: "Using Music App for soundtrack..."
        using_music_app: LangStr

    class StringsStoreGroup:
        """
        ::

            Store item name labels and shop entry points.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Store label for physical merchandise.
        #:
        #:     English: "Merch!"
        merch: LangStr

        def pro_name(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Product name label for the Pro upgrade.

                English: "{app_name} Pro"
            """

        #: ::
        #:
        #:     Notice on locked play options that the item must be bought in the
        #:     store first.
        #:
        #:     English: "This must be unlocked in the store."
        unlock_in_store: LangStr

    class StringsTeamsGroup:
        """
        ::

            Default team names. Players can rename their teams, so these are the
            built-in defaults only; custom names are shown as-is and
            untranslated.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Default name of the enemy team.
        #:
        #:     English: "Bad Guys"
        bad_guys: LangStr

        #: ::
        #:
        #:     Default name of the blue team.
        #:
        #:     English: "Blue"
        blue: LangStr

        #: ::
        #:
        #:     Default name of the friendly team.
        #:
        #:     English: "Good Guys"
        good_guys: LangStr

        #: ::
        #:
        #:     Default name of the red team.
        #:
        #:     English: "Red"
        red: LangStr

    class StringsTipsGroup:
        """
        ::

            Gameplay tips shown between rounds and in the lobby. Advice
            delivered deadpan -- several are jokes first and hints second, and
            the humour is the point. Keep each one wry rather than translating
            it literally.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "You can "aim" your punches by spinning left or right.
        #:     This is useful for knocking bad guys off edges or scoring in
        #:     hockey."
        aim_punches: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "If you've got lots of players coming and going, turn on
        #:     'auto-kick-idle-players' under settings in case anyone forgets to
        #:     leave the game."
        auto_kick_idle: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "No, you can't get up on the ledge. You have to throw
        #:     bombs."
        cant_reach_ledge: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Despite their looks, all characters' abilities are
        #:     identical, so just pick whichever one you most closely resemble."
        characters_identical: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Try 'cooking off' bombs for a second or two before
        #:     throwing them."
        cook_off_bombs: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Create player profiles for yourself and your friends
        #:     with your preferred names and appearances instead of using random
        #:     ones."
        create_profiles: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "In Capture-the-Flag, your own flag must be at your base
        #:     to score. If the other team is about to score, stealing their
        #:     flag can be a good way to stop them."
        ctf_own_flag: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Curse boxes turn you into a ticking time bomb. The only
        #:     cure is to quickly grab a health-pack."
        curse_boxes: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "If you pick up a curse, your only hope for survival is
        #:     to find a health powerup in the next few seconds."
        curse_health_powerup: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Tired of the soundtrack? Replace it with your own! See
        #:     Settings->Audio->Soundtrack"
        custom_soundtrack: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Don't run all the time. Really. You will fall off
        #:     cliffs."
        dont_always_run: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Don't spin for too long; you'll become dizzy and fall."
        dont_overspin: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "This level never ends, but a high score here will earn
        #:     you eternal respect throughout the world."
        endless_high_score: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Punches do more damage the faster your fists are
        #:     moving, so try running, jumping, and spinning like crazy."
        fast_fists: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Always remember to floss."
        floss: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "You can judge when a bomb is going to explode based on
        #:     the color of sparks from its fuse: yellow..orange..red..BOOM."
        fuse_colors: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "In hockey, you'll maintain more speed if you turn
        #:     gradually."
        hockey_turn_gradually: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Hold any button to run. (Trigger buttons work well if
        #:     you have them)"
        hold_to_run: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Ice bombs are not very powerful, but they freeze
        #:     whoever they hit, leaving them vulnerable to shattering."
        ice_bombs: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Players can join and leave in the middle of most games,
        #:     and you can also plug and unplug controllers on the fly."
        join_leave_anytime: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Jumping just before throwing a bomb will make it go
        #:     higher."
        jump_before_throw: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Jump just as you're throwing to get bombs up to the
        #:     highest levels."
        jump_throw_high: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "If you stay in one place, you're toast. Run and dodge
        #:     to survive."
        keep_moving: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Land-mines are a good way to stop speedy enemies."
        land_mines_speedy: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Practice using your momentum to throw bombs more
        #:     accurately."
        momentum_accuracy: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "If you kill an enemy in one hit, you get double
        #:     points."
        one_hit_double_points: LangStr

        def pickup_flag(self, *, pickup: str | LangStr) -> LangStr:
            """
            ::

                Gameplay tip shown between rounds, in the game's dry deadpan
                voice.

                English: "Use the pick-up button to grab the flag < {pickup} >."
            """

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "It's easier to win with a friend or two helping."
        play_with_friends: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "If someone picks you up, punch them and they'll let go.
        #:     This works in real life too."
        punch_to_escape: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "If your framerate is choppy, try turning down
        #:     resolution or visuals in the game's graphics settings."
        reduce_visuals_framerate: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "If your device gets too warm or you'd like to conserve
        #:     battery power, turn down "Visuals" or "Resolution" in
        #:     Settings->Graphics."
        reduce_visuals_heat: LangStr

        def remote_app(self, *, remote_app_name: str | LangStr) -> LangStr:
            """
            ::

                Gameplay tip shown between rounds, in the game's dry deadpan
                voice.

                English: "Short on controllers? Install the '{remote_app_name}'
                app on your mobile devices to use them as controllers."
            """

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Hold down any button to run. You'll get places faster
        #:     but won't turn very well, so watch out for cliffs."
        run_watch_cliffs: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Your punches do much more damage if you are running or
        #:     spinning."
        running_spinning_damage: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Don't get too cocky with that energy shield; you can
        #:     still get yourself thrown off a cliff."
        shield_overconfidence: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "A perfectly timed running-jumping-spin-punch can kill
        #:     in a single hit and earn you lifelong respect from your friends."
        spin_punch_respect: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "If you get a sticky bomb stuck to you, jump around and
        #:     spin in circles. You might shake the bomb off, or if nothing
        #:     else, your last moments will be entertaining."
        sticky_bomb_dance: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "The head is the most vulnerable area, so a sticky-bomb
        #:     to the noggin usually means game-over."
        sticky_to_head: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Many things can be picked up and thrown, including
        #:     other players. Tossing your enemies off cliffs can be an
        #:     effective and emotionally fulfilling strategy."
        throw_players: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Throw strength depends on the direction you hold. To
        #:     toss something gently in front of you, don't hold any direction."
        throw_strength_direction: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Take out a group of enemies by setting off a bomb near
        #:     a TNT box."
        tnt_box: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Try tricking enemies into killing each other or running
        #:     off cliffs."
        trick_enemies: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "You take damage when you whack your head on things, so
        #:     try not to whack your head on things."
        whack_head: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Whip back and forth to get more distance on your
        #:     throws."
        whip_for_distance: LangStr

        #: ::
        #:
        #:     Gameplay tip shown between rounds, in the game's dry deadpan
        #:     voice.
        #:
        #:     English: "Run back and forth before throwing a bomb to 'whiplash'
        #:     it and throw it farther."
        whiplash_throw: LangStr

    class StringsTournamentEntryGroup:
        """
        ::

            Tournament-entry dialog: entry cost and watch-ad options.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Progress screen-message shown right after paying to enter a
        #:     tournament.
        #:
        #:     English: "Entering tournament..."
        entering: LangStr

        def tickets_count(self, *, count: int) -> LangStr:
            """
            ::

                Cost shown as a number of tickets.

                English: (one) "# Ticket" / (other) "# Tickets"
            """

        #: ::
        #:
        #:     Title of the tournament-entry dialog.
        #:
        #:     English: "Tournament Entry"
        title: LangStr

        #: ::
        #:
        #:     Button to watch an ad for tournament entry.
        #:
        #:     English: "Watch an Ad"
        watch_an_ad: LangStr

    class StringsTournamentScoresGroup:
        """
        ::

            Tournament standings window strings.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Placeholder when a tournament has no scores.
        #:
        #:     English: "No scores yet."
        no_scores_yet: LangStr

        #: ::
        #:
        #:     Title for the tournament standings window.
        #:
        #:     English: "Tournament Standings"
        tournament_standings: LangStr

    class StringsTutorialGroup:
        """
        ::

            Tutorial narration lines (the coach's spoken tips as you learn the
            controls) plus the skip-tutorial UI strings.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Notice shown while running the CPU-benchmark tutorial.
        #:
        #:     English: "Running tutorial at ludicrous-speed (primarily tests
        #:     CPU speed)"
        cpu_benchmark: LangStr

        #: ::
        #:
        #:     Tutorial greeting.
        #:
        #:     English: "Hi there!"
        phrase01: LangStr

        def phrase02(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Tutorial: welcome line.

                English: "Welcome to {app_name}!"
            """

        #: ::
        #:
        #:     Tutorial: intro to control tips.
        #:
        #:     English: "Here's a few tips for controlling your character:"
        phrase03: LangStr

        def phrase04(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Tutorial: physics intro.

                English: "Many things in {app_name} are PHYSICS based."
            """

        #: ::
        #:
        #:     Tutorial: punch example lead-in.
        #:
        #:     English: "For example, when you punch,.."
        phrase05: LangStr

        #: ::
        #:
        #:     Tutorial: punch damage explanation.
        #:
        #:     English: "..damage is based on the speed of your fists."
        phrase06: LangStr

        def phrase07(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Tutorial: weak-punch explanation.

                English: "See? We weren't moving, so that barely hurt {name}."
            """

        #: ::
        #:
        #:     Tutorial: jump-and-spin tip.
        #:
        #:     English: "Now let's jump and spin to get more speed."
        phrase08: LangStr

        #: ::
        #:
        #:     Tutorial: approval after a good move.
        #:
        #:     English: "Ah, that's better."
        phrase09: LangStr

        #: ::
        #:
        #:     Tutorial: running tip.
        #:
        #:     English: "Running helps too."
        phrase10: LangStr

        #: ::
        #:
        #:     Tutorial: how to run.
        #:
        #:     English: "Hold down ANY button to run."
        phrase11: LangStr

        #: ::
        #:
        #:     Tutorial: combined-move tip.
        #:
        #:     English: "For extra-awesome punches, try running AND spinning."
        phrase12: LangStr

        def phrase13(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Tutorial: apology after a hard hit.

                English: "Whoops; sorry 'bout that {name}."
            """

        def phrase14(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Tutorial: pick-up-and-throw tip.

                English: "You can pick up and throw things such as flags.. or
                {name}."
            """

        #: ::
        #:
        #:     Tutorial: intro to bombs.
        #:
        #:     English: "Lastly, there's bombs."
        phrase15: LangStr

        #: ::
        #:
        #:     Tutorial: bomb-throwing practice note.
        #:
        #:     English: "Throwing bombs takes practice."
        phrase16: LangStr

        #: ::
        #:
        #:     Tutorial: bad-throw reaction.
        #:
        #:     English: "Ouch! Not a very good throw."
        phrase17: LangStr

        #: ::
        #:
        #:     Tutorial: moving-throw tip.
        #:
        #:     English: "Moving helps you throw farther."
        phrase18: LangStr

        #: ::
        #:
        #:     Tutorial: jumping-throw tip.
        #:
        #:     English: "Jumping helps you throw higher."
        phrase19: LangStr

        #: ::
        #:
        #:     Tutorial: whiplash-throw tip.
        #:
        #:     English: ""Whiplash" your bombs for even longer throws."
        phrase20: LangStr

        #: ::
        #:
        #:     Tutorial: bomb-timing note.
        #:
        #:     English: "Timing your bombs can be tricky."
        phrase21: LangStr

        #: ::
        #:
        #:     Tutorial: mild dismay exclamation.
        #:
        #:     English: "Dang."
        phrase22: LangStr

        #: ::
        #:
        #:     Tutorial: cook-off-the-fuse tip.
        #:
        #:     English: "Try "cooking off" the fuse for a second or two."
        phrase23: LangStr

        #: ::
        #:
        #:     Tutorial: praise after a cooked bomb.
        #:
        #:     English: "Hooray! Nicely cooked."
        phrase24: LangStr

        #: ::
        #:
        #:     Tutorial: wrap-up line.
        #:
        #:     English: "Well, that's just about it."
        phrase25: LangStr

        #: ::
        #:
        #:     Tutorial: send-off encouragement.
        #:
        #:     English: "Now go get 'em, tiger!"
        phrase26: LangStr

        #: ::
        #:
        #:     Tutorial: parting motivational line.
        #:
        #:     English: "Remember your training, and you WILL come back alive!"
        phrase27: LangStr

        #: ::
        #:
        #:     Tutorial: wry qualifier after the pep talk.
        #:
        #:     English: "...well, maybe..."
        phrase28: LangStr

        #: ::
        #:
        #:     Tutorial: final good-luck wish.
        #:
        #:     English: "Good luck!"
        phrase29: LangStr

        #: ::
        #:
        #:     Tutorial: stand-in practice-character name.
        #:
        #:     English: "Fred"
        random_name1: LangStr

        #: ::
        #:
        #:     Tutorial: stand-in practice-character name.
        #:
        #:     English: "Harry"
        random_name2: LangStr

        #: ::
        #:
        #:     Tutorial: stand-in practice-character name.
        #:
        #:     English: "Bill"
        random_name3: LangStr

        #: ::
        #:
        #:     Tutorial: stand-in practice-character name.
        #:
        #:     English: "Chuck"
        random_name4: LangStr

        #: ::
        #:
        #:     Tutorial: stand-in practice-character name.
        #:
        #:     English: "Phil"
        random_name5: LangStr

        #: ::
        #:
        #:     Confirmation prompt before skipping the tutorial.
        #:
        #:     English: "Really skip the tutorial? Tap or press to confirm."
        skip_confirm: LangStr

        def skip_vote_count(
            self, *, count: str | LangStr, total: str | LangStr
        ) -> LangStr:
            """
            ::

                Tutorial: skip-vote tally.

                English: "{count}/{total} skip votes"
            """

        #: ::
        #:
        #:     Status shown while the tutorial is being skipped.
        #:
        #:     English: "skipping tutorial..."
        skipping: LangStr

        #: ::
        #:
        #:     Label preceding a gameplay tip.
        #:
        #:     English: "Tip"
        tip: LangStr

        #: ::
        #:
        #:     Hint on how to skip the tutorial.
        #:
        #:     English: "(tap or press anything to skip tutorial)"
        to_skip_press_anything: LangStr

    class StringsUiGroup:
        """
        ::

            Generic UI vocabulary: short labels (buttons, dialog titles,
            joiners) shared across many UIs. Purpose-specific wording belongs
            elsewhere - see each entry's docs for what it is and is not.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Generic "Achievements" label/heading.
        #:
        #:     English: "Achievements"
        achievements: LangStr

        #: ::
        #:
        #:     Generic "Activity" label.
        #:
        #:     English: "Activity"
        activity: LangStr

        #: ::
        #:
        #:     The app's name; byte-identical in every language.
        #:
        #:     English: "BombSquad"
        app_name: LangStr

        #: ::
        #:
        #:     Generic "Boost" button label.
        #:
        #:     English: "Boost"
        boost: LangStr

        #: ::
        #:
        #:     Button label to claim a reward.
        #:
        #:     English: "Claim"
        claim: LangStr

        #: ::
        #:
        #:     Generic "Demo" label.
        #:
        #:     English: "Demo"
        demo: LangStr

        #: ::
        #:
        #:     Generic "Easy" difficulty label.
        #:
        #:     English: "Easy"
        easy: LangStr

        #: ::
        #:
        #:     Generic "Epic Mode" label.
        #:
        #:     English: "Epic Mode"
        epic_mode: LangStr

        def exit_app_confirm(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Confirmation question for exiting the app.

                English: "Exit {app_name}?"
            """

        #: ::
        #:
        #:     Generic "Final Score" label.
        #:
        #:     English: "Final Score"
        final_score: LangStr

        #: ::
        #:
        #:     Emphatic "FREE!" label.
        #:
        #:     English: "FREE!"
        free: LangStr

        #: ::
        #:
        #:     The Apple "Game Center" service name; byte-identical in every
        #:     language.
        #:
        #:     English: "Game Center"
        game_center: LangStr

        #: ::
        #:
        #:     The "Google Play" service name; byte-identical in every language.
        #:
        #:     English: "Google Play"
        google_play: LangStr

        #: ::
        #:
        #:     Generic "Hard" difficulty label.
        #:
        #:     English: "Hard"
        hard: LangStr

        #: ::
        #:
        #:     Generic "Inbox" label.
        #:
        #:     English: "Inbox"
        inbox: LangStr

        #: ::
        #:
        #:     Generic "Kick" button label.
        #:
        #:     English: "Kick"
        kick: LangStr

        #: ::
        #:
        #:     Generic "Leaderboards" label.
        #:
        #:     English: "Leaderboards"
        leaderboards: LangStr

        #: ::
        #:
        #:     Generic "Map" label.
        #:
        #:     English: "Map"
        map: LangStr

        #: ::
        #:
        #:     Lowercase "not signed in" status indicator.
        #:
        #:     English: "not signed in"
        not_signed_in_status: LangStr

        #: ::
        #:
        #:     General 'Play' action label; used for the main-menu Play button
        #:     and the tournament-entry play button.
        #:
        #:     English: "Play"
        play: LangStr

        #: ::
        #:
        #:     Generic "Playlist" label.
        #:
        #:     English: "Playlist"
        playlist: LangStr

        #: ::
        #:
        #:     Generic "Points" label.
        #:
        #:     English: "Points"
        points: LangStr

        #: ::
        #:
        #:     Generic "Practice" label.
        #:
        #:     English: "Practice"
        practice: LangStr

        def quit_app_confirm(self, *, app_name: str | LangStr) -> LangStr:
            """
            ::

                Confirmation question for quitting the app (Mac wording).

                English: "Quit {app_name}?"
            """

        #: ::
        #:
        #:     Generic "Rank" label.
        #:
        #:     English: "Rank"
        rank: LangStr

        #: ::
        #:
        #:     The remote-control companion app's name; byte-identical in every
        #:     language.
        #:
        #:     English: "BombSquad Remote"
        remote_app_name: LangStr

        #: ::
        #:
        #:     Generic "Stats" label.
        #:
        #:     English: "Stats"
        stats: LangStr

        #: ::
        #:
        #:     Generic "Trophies" label.
        #:
        #:     English: "Trophies"
        trophies: LangStr

    class StringsV2UpgradeGroup:
        """
        ::

            Device-account -> V2-account upgrade prompt.

            See source for the full asset list.
        """

        def device_account_upgrade(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Warning to upgrade a device account to a V2 account.

                English: "Warning: You are signed in with a device account
                ({name}). Device accounts will be removed in a future update.
                Upgrade to a V2 account to keep your progress."
            """

    class StringsWatchGroup:
        """
        ::

            Watch-section strings: replay browsing and playback UI.

            See source for the full asset list.
        """

        def delete_confirm(self, *, replay: str | LangStr) -> LangStr:
            """
            ::

                Confirmation before deleting a named replay.

                English: "Delete "{replay}"?"
            """

        #: ::
        #:
        #:     Two-line button to delete a replay.
        #:
        #:     English: "Delete Replay"
        delete_replay_button: LangStr

        #: ::
        #:
        #:     Heading for the list of the player's replays.
        #:
        #:     English: "My Replays"
        my_replays: LangStr

        #: ::
        #:
        #:     Error when no replay is selected.
        #:
        #:     English: "No Replay Selected"
        no_replay_selected: LangStr

        def playback_speed(self, *, speed: str | LangStr) -> LangStr:
            """
            ::

                Label showing the current replay playback-speed multiplier
                (in-game replay controls and the watch section).

                English: "Playback Speed: {speed}"
            """

        def rename_replay(self, *, replay: str | LangStr) -> LangStr:
            """
            ::

                Prompt to rename a named replay.

                English: "Rename "{replay}" to:"
            """

        #: ::
        #:
        #:     Two-line button to rename a replay.
        #:
        #:     English: "Rename Replay"
        rename_replay_button: LangStr

        def rename_warning(self, *, replay: str | LangStr) -> LangStr:
            """
            ::

                Warning to rename a replay so it is not overwritten.

                English: "Rename "{replay}" after a game to keep it; otherwise
                it will be overwritten."
            """

        #: ::
        #:
        #:     Error when deleting a replay fails.
        #:
        #:     English: "Error deleting replay."
        replay_delete_error: LangStr

        #: ::
        #:
        #:     Label for the replay name field.
        #:
        #:     English: "Replay Name"
        replay_name: LangStr

        #: ::
        #:
        #:     Default name for the most recent replay.
        #:
        #:     English: "Last Game Replay"
        replay_name_default: LangStr

        #: ::
        #:
        #:     Error when renaming a replay fails.
        #:
        #:     English: "Error renaming replay."
        replay_rename_error: LangStr

        #: ::
        #:
        #:     Error message that a replay name is taken.
        #:
        #:     English: "A replay with that name already exists."
        replay_rename_error_already_exists: LangStr

        #: ::
        #:
        #:     Error when a replay rename name is bad.
        #:
        #:     English: "Can't rename replay; invalid name."
        replay_rename_error_invalid: LangStr

        #: ::
        #:
        #:     Title of the Watch section, where players view replays of
        #:     previous games; also labels the main-menu button leading there.
        #:
        #:     English: "Watch"
        title: LangStr

        #: ::
        #:
        #:     Two-line button to watch a replay.
        #:
        #:     English: "Watch Replay"
        watch_replay_button: LangStr

    class StringsGroup:
        """
        ::

            All standard game strings (everything non-bootstrap).

            See source for the full asset list.
        """

        account: StringsAccountGroup
        achievements: StringsAchievementsGroup
        app_invite: StringsAppInviteGroup
        characters: StringsCharactersGroup
        chest: StringsChestGroup
        controls: StringsControlsGroup
        coop: StringsCoopGroup
        coop_levels: StringsCoopLevelsGroup
        coop_score: StringsCoopScoreGroup
        credits: StringsCreditsGroup
        economy: StringsEconomyGroup
        file_selector: StringsFileSelectorGroup
        game: StringsGameGroup
        game_descriptions: StringsGameDescriptionsGroup
        game_names: StringsGameNamesGroup
        game_settings: StringsGameSettingsGroup
        gather: StringsGatherGroup
        get_remote: StringsGetRemoteGroup
        get_tokens: StringsGetTokensGroup
        help: StringsHelpGroup
        in_game_menu: StringsInGameMenuGroup
        inbox: StringsInboxGroup
        inventory: StringsInventoryGroup
        keyboard: StringsKeyboardGroup
        kiosk: StringsKioskGroup
        league: StringsLeagueGroup
        lobby: StringsLobbyGroup
        main_menu: StringsMainMenuGroup
        map_names: StringsMapNamesGroup
        multi_team: StringsMultiTeamGroup
        party: StringsPartyGroup
        party_queue: StringsPartyQueueGroup
        play: StringsPlayGroup
        play_modes: StringsPlayModesGroup
        play_options: StringsPlayOptionsGroup
        playlist: StringsPlaylistGroup
        profile: StringsProfileGroup
        profiles: StringsProfilesGroup
        report: StringsReportGroup
        resource_type_info: StringsResourceTypeInfoGroup
        score_types: StringsScoreTypesGroup
        send_info: StringsSendInfoGroup
        server: StringsServerGroup
        session: StringsSessionGroup
        settings: StringsSettingsGroup
        soundtrack: StringsSoundtrackGroup
        store: StringsStoreGroup
        teams: StringsTeamsGroup
        tips: StringsTipsGroup
        tournament_entry: StringsTournamentEntryGroup
        tournament_scores: StringsTournamentScoresGroup
        tutorial: StringsTutorialGroup
        ui: StringsUiGroup
        v2_upgrade: StringsV2UpgradeGroup
        watch: StringsWatchGroup

    class TexturesGroup:
        """
        ::

            All standard game textures (everything non-bootstrap).

            See source for the full asset list.
        """

        achievement_boxer: TextureVerifiedSpec
        achievement_cross_hair: TextureVerifiedSpec
        achievement_dual_wielding: TextureVerifiedSpec
        achievement_empty: TextureVerifiedSpec
        achievement_flawless_victory: TextureVerifiedSpec
        achievement_football_shutout: TextureVerifiedSpec
        achievement_football_victory: TextureVerifiedSpec
        achievement_free_loader: TextureVerifiedSpec
        achievement_got_the_moves: TextureVerifiedSpec
        achievement_in_control: TextureVerifiedSpec
        achievement_medal_large: TextureVerifiedSpec
        achievement_medal_medium: TextureVerifiedSpec
        achievement_medal_small: TextureVerifiedSpec
        achievement_mine: TextureVerifiedSpec
        achievement_off_you_go: TextureVerifiedSpec
        achievement_onslaught: TextureVerifiedSpec
        achievement_outline: TextureVerifiedSpec
        achievement_runaround: TextureVerifiedSpec
        achievement_sharing_is_caring: TextureVerifiedSpec
        achievement_stayin_alive: TextureVerifiedSpec
        achievement_super_punch: TextureVerifiedSpec
        achievement_team_player: TextureVerifiedSpec
        achievement_tnt: TextureVerifiedSpec
        achievement_wall: TextureVerifiedSpec
        achievements_icon: TextureVerifiedSpec
        action_hero_color: TextureVerifiedSpec
        action_hero_color_mask: TextureVerifiedSpec
        action_hero_icon: TextureVerifiedSpec
        action_hero_icon_color_mask: TextureVerifiedSpec
        advanced_icon: TextureVerifiedSpec
        agent_color: TextureVerifiedSpec
        agent_color_mask: TextureVerifiedSpec
        agent_icon: TextureVerifiedSpec
        agent_icon_color_mask: TextureVerifiedSpec
        ali_color: TextureVerifiedSpec
        ali_color_mask: TextureVerifiedSpec
        ali_icon: TextureVerifiedSpec
        ali_icon_color_mask: TextureVerifiedSpec
        ali_splash: TextureVerifiedSpec
        alien_color: TextureVerifiedSpec
        alien_color_mask: TextureVerifiedSpec
        alien_icon: TextureVerifiedSpec
        alien_icon_color_mask: TextureVerifiedSpec
        always_land_bgcolor: TextureVerifiedSpec
        always_land_level_color: TextureVerifiedSpec
        always_land_preview: TextureVerifiedSpec
        analog_stick: TextureVerifiedSpec
        assassin_color: TextureVerifiedSpec
        assassin_color_mask: TextureVerifiedSpec
        assassin_icon: TextureVerifiedSpec
        assassin_icon_color_mask: TextureVerifiedSpec
        audio_icon: TextureVerifiedSpec
        bar: TextureVerifiedSpec
        bear_color: TextureVerifiedSpec
        bear_color_mask: TextureVerifiedSpec
        bear_icon: TextureVerifiedSpec
        bear_icon_color_mask: TextureVerifiedSpec
        bg: TextureVerifiedSpec
        big_g: TextureVerifiedSpec
        big_gpreview: TextureVerifiedSpec
        bomb_color: TextureVerifiedSpec
        bomb_color_ice: TextureVerifiedSpec
        bomb_sticky_color: TextureVerifiedSpec
        bones_color: TextureVerifiedSpec
        bones_color_mask: TextureVerifiedSpec
        bones_icon: TextureVerifiedSpec
        bones_icon_color_mask: TextureVerifiedSpec
        bridgit_level_color: TextureVerifiedSpec
        bridgit_preview: TextureVerifiedSpec
        bunny_color: TextureVerifiedSpec
        bunny_color_mask: TextureVerifiedSpec
        bunny_icon: TextureVerifiedSpec
        bunny_icon_color_mask: TextureVerifiedSpec
        button_bomb: TextureVerifiedSpec
        button_jump: TextureVerifiedSpec
        button_pick_up: TextureVerifiedSpec
        button_punch: TextureVerifiedSpec
        ch_title_char1: TextureVerifiedSpec
        ch_title_char2: TextureVerifiedSpec
        ch_title_char3: TextureVerifiedSpec
        ch_title_char4: TextureVerifiedSpec
        ch_title_char5: TextureVerifiedSpec
        chest_icon: TextureVerifiedSpec
        chest_icon_empty: TextureVerifiedSpec
        chest_icon_multi: TextureVerifiedSpec
        chest_icon_tint: TextureVerifiedSpec
        chest_open_icon: TextureVerifiedSpec
        chest_open_icon_tint: TextureVerifiedSpec
        circle_zig_zag: TextureVerifiedSpec
        clay_stroke: TextureVerifiedSpec
        coin: TextureVerifiedSpec
        controller_icon: TextureVerifiedSpec
        courtyard_level_color: TextureVerifiedSpec
        courtyard_preview: TextureVerifiedSpec
        cowboy_color: TextureVerifiedSpec
        cowboy_color_mask: TextureVerifiedSpec
        cowboy_icon: TextureVerifiedSpec
        cowboy_icon_color_mask: TextureVerifiedSpec
        crag_castle_level_color: TextureVerifiedSpec
        crag_castle_preview: TextureVerifiedSpec
        cross_out: TextureVerifiedSpec
        cross_out_mask: TextureVerifiedSpec
        cute_spaz: TextureVerifiedSpec
        cyborg_color: TextureVerifiedSpec
        cyborg_color_mask: TextureVerifiedSpec
        cyborg_icon: TextureVerifiedSpec
        cyborg_icon_color_mask: TextureVerifiedSpec
        discord_icon: TextureVerifiedSpec
        discord_logo: TextureVerifiedSpec
        discord_server: TextureVerifiedSpec
        doom_shroom_bgcolor: TextureVerifiedSpec
        doom_shroom_level_color: TextureVerifiedSpec
        doom_shroom_preview: TextureVerifiedSpec
        down_button: TextureVerifiedSpec
        egg1: TextureVerifiedSpec
        egg2: TextureVerifiedSpec
        egg3: TextureVerifiedSpec
        egg4: TextureVerifiedSpec
        egg_tex1: TextureVerifiedSpec
        egg_tex2: TextureVerifiedSpec
        egg_tex3: TextureVerifiedSpec
        empty: TextureVerifiedSpec
        file: TextureVerifiedSpec
        flag_color: TextureVerifiedSpec
        folder: TextureVerifiedSpec
        football_stadium: TextureVerifiedSpec
        football_stadium_preview: TextureVerifiedSpec
        frame_inset: TextureVerifiedSpec
        frosty_color: TextureVerifiedSpec
        frosty_color_mask: TextureVerifiedSpec
        frosty_icon: TextureVerifiedSpec
        frosty_icon_color_mask: TextureVerifiedSpec
        game_center_icon: TextureVerifiedSpec
        github_logo: TextureVerifiedSpec
        gladiator_color: TextureVerifiedSpec
        gladiator_color_mask: TextureVerifiedSpec
        gladiator_icon: TextureVerifiedSpec
        gladiator_icon_color_mask: TextureVerifiedSpec
        gold_pass: TextureVerifiedSpec
        google_play_achievements_icon: TextureVerifiedSpec
        google_play_games_icon: TextureVerifiedSpec
        google_play_leaderboards_icon: TextureVerifiedSpec
        google_plus_icon: TextureVerifiedSpec
        google_plus_sign_in_button: TextureVerifiedSpec
        graphics_icon: TextureVerifiedSpec
        heart: TextureVerifiedSpec
        hockey_stadium: TextureVerifiedSpec
        hockey_stadium_preview: TextureVerifiedSpec
        icon_onslaught: TextureVerifiedSpec
        icon_runaround: TextureVerifiedSpec
        impact_bomb_color: TextureVerifiedSpec
        impact_bomb_color_lit: TextureVerifiedSpec
        inventory_icon: TextureVerifiedSpec
        jack_color: TextureVerifiedSpec
        jack_color_mask: TextureVerifiedSpec
        jack_icon: TextureVerifiedSpec
        jack_icon_color_mask: TextureVerifiedSpec
        jumpsuit_color: TextureVerifiedSpec
        jumpsuit_color_mask: TextureVerifiedSpec
        jumpsuit_icon: TextureVerifiedSpec
        jumpsuit_icon_color_mask: TextureVerifiedSpec
        kronk: TextureVerifiedSpec
        kronk_color_mask: TextureVerifiedSpec
        kronk_icon: TextureVerifiedSpec
        kronk_icon_color_mask: TextureVerifiedSpec
        lake_frigid: TextureVerifiedSpec
        lake_frigid_preview: TextureVerifiedSpec
        lake_frigid_reflections: TextureVerifiedSpec
        land_mine: TextureVerifiedSpec
        land_mine_lit: TextureVerifiedSpec
        leaderboards_icon: TextureVerifiedSpec
        left_button: TextureVerifiedSpec
        level_icon: TextureVerifiedSpec
        lock: TextureVerifiedSpec
        log_icon: TextureVerifiedSpec
        logo: TextureVerifiedSpec
        logo_easter: TextureVerifiedSpec
        map_preview_mask: TextureVerifiedSpec
        medal_bronze: TextureVerifiedSpec
        medal_complete: TextureVerifiedSpec
        medal_gold: TextureVerifiedSpec
        medal_silver: TextureVerifiedSpec
        mel_color: TextureVerifiedSpec
        mel_color_mask: TextureVerifiedSpec
        mel_icon: TextureVerifiedSpec
        mel_icon_color_mask: TextureVerifiedSpec
        menu_bg: TextureVerifiedSpec
        menu_icon: TextureVerifiedSpec
        merch: TextureVerifiedSpec
        meter: TextureVerifiedSpec
        monkey_face_level_color: TextureVerifiedSpec
        monkey_face_preview: TextureVerifiedSpec
        multiplayer_examples: TextureVerifiedSpec
        nature_background_color: TextureVerifiedSpec
        neo_spaz_color: TextureVerifiedSpec
        neo_spaz_color_mask: TextureVerifiedSpec
        neo_spaz_icon: TextureVerifiedSpec
        neo_spaz_icon_color_mask: TextureVerifiedSpec
        next_level_icon: TextureVerifiedSpec
        ninja_color: TextureVerifiedSpec
        ninja_color_mask: TextureVerifiedSpec
        ninja_icon: TextureVerifiedSpec
        ninja_icon_color_mask: TextureVerifiedSpec
        null: TextureVerifiedSpec
        old_lady_color: TextureVerifiedSpec
        old_lady_color_mask: TextureVerifiedSpec
        old_lady_icon: TextureVerifiedSpec
        old_lady_icon_color_mask: TextureVerifiedSpec
        opera_singer_color: TextureVerifiedSpec
        opera_singer_color_mask: TextureVerifiedSpec
        opera_singer_icon: TextureVerifiedSpec
        opera_singer_icon_color_mask: TextureVerifiedSpec
        ouya_icon: TextureVerifiedSpec
        ouya_obutton: TextureVerifiedSpec
        ouya_ubutton: TextureVerifiedSpec
        ouya_ybutton: TextureVerifiedSpec
        penguin_color: TextureVerifiedSpec
        penguin_color_mask: TextureVerifiedSpec
        penguin_icon: TextureVerifiedSpec
        penguin_icon_color_mask: TextureVerifiedSpec
        pixie_color: TextureVerifiedSpec
        pixie_color_mask: TextureVerifiedSpec
        pixie_icon: TextureVerifiedSpec
        pixie_icon_color_mask: TextureVerifiedSpec
        player_lineup: TextureVerifiedSpec
        plus_button: TextureVerifiedSpec
        powerup_bomb: TextureVerifiedSpec
        powerup_curse: TextureVerifiedSpec
        powerup_health: TextureVerifiedSpec
        powerup_ice_bombs: TextureVerifiedSpec
        powerup_impact_bombs: TextureVerifiedSpec
        powerup_land_mines: TextureVerifiedSpec
        powerup_punch: TextureVerifiedSpec
        powerup_shield: TextureVerifiedSpec
        powerup_speed: TextureVerifiedSpec
        powerup_sticky_bombs: TextureVerifiedSpec
        puck_color: TextureVerifiedSpec
        quote_bubble: TextureVerifiedSpec
        rampage_bgcolor: TextureVerifiedSpec
        rampage_bgcolor2: TextureVerifiedSpec
        rampage_level_color: TextureVerifiedSpec
        rampage_preview: TextureVerifiedSpec
        replay_icon: TextureVerifiedSpec
        right_button: TextureVerifiedSpec
        robot_color: TextureVerifiedSpec
        robot_color_mask: TextureVerifiedSpec
        robot_icon: TextureVerifiedSpec
        robot_icon_color_mask: TextureVerifiedSpec
        roundabout_level_color: TextureVerifiedSpec
        roundabout_preview: TextureVerifiedSpec
        santa_color: TextureVerifiedSpec
        santa_color_mask: TextureVerifiedSpec
        santa_icon: TextureVerifiedSpec
        santa_icon_color_mask: TextureVerifiedSpec
        settings_icon: TextureVerifiedSpec
        slash: TextureVerifiedSpec
        star: TextureVerifiedSpec
        step_right_up_level_color: TextureVerifiedSpec
        step_right_up_preview: TextureVerifiedSpec
        store_character: TextureVerifiedSpec
        store_character_easter: TextureVerifiedSpec
        store_character_xmas: TextureVerifiedSpec
        store_icon: TextureVerifiedSpec
        superhero_color: TextureVerifiedSpec
        superhero_color_mask: TextureVerifiedSpec
        superhero_icon: TextureVerifiedSpec
        superhero_icon_color_mask: TextureVerifiedSpec
        the_pad_level_color: TextureVerifiedSpec
        the_pad_preview: TextureVerifiedSpec
        ticket_roll: TextureVerifiedSpec
        ticket_roll_big: TextureVerifiedSpec
        ticket_rolls: TextureVerifiedSpec
        tickets: TextureVerifiedSpec
        tickets_more: TextureVerifiedSpec
        tickets_purple: TextureVerifiedSpec
        tip_top_bgcolor: TextureVerifiedSpec
        tip_top_level_color: TextureVerifiedSpec
        tip_top_preview: TextureVerifiedSpec
        tnt: TextureVerifiedSpec
        tokens1: TextureVerifiedSpec
        tokens2: TextureVerifiedSpec
        tokens3: TextureVerifiedSpec
        tokens4: TextureVerifiedSpec
        tower_dlevel_color: TextureVerifiedSpec
        tower_dpreview: TextureVerifiedSpec
        trees_color: TextureVerifiedSpec
        trophy: TextureVerifiedSpec
        tv: TextureVerifiedSpec
        up_button: TextureVerifiedSpec
        vr_fill_mound: TextureVerifiedSpec
        warrior_color: TextureVerifiedSpec
        warrior_color_mask: TextureVerifiedSpec
        warrior_icon: TextureVerifiedSpec
        warrior_icon_color_mask: TextureVerifiedSpec
        window_bottom_cap: TextureVerifiedSpec
        witch_color: TextureVerifiedSpec
        witch_color_mask: TextureVerifiedSpec
        witch_icon: TextureVerifiedSpec
        witch_icon_color_mask: TextureVerifiedSpec
        wizard_color: TextureVerifiedSpec
        wizard_color_mask: TextureVerifiedSpec
        wizard_icon: TextureVerifiedSpec
        wizard_icon_color_mask: TextureVerifiedSpec
        wrestler_color: TextureVerifiedSpec
        wrestler_color_mask: TextureVerifiedSpec
        wrestler_icon: TextureVerifiedSpec
        wrestler_icon_color_mask: TextureVerifiedSpec
        zig_zag_level_color: TextureVerifiedSpec
        zigzag_preview: TextureVerifiedSpec
        zoe_color: TextureVerifiedSpec
        zoe_color_mask: TextureVerifiedSpec
        zoe_icon: TextureVerifiedSpec
        zoe_icon_color_mask: TextureVerifiedSpec

    #: The ``audio`` group - 412 assets (``achievement``, ``action_hero1``,
    #: ``action_hero2``, ``action_hero3``, ``action_hero4``, and 407 more). Full
    #: list in source.
    audio: AudioGroup

    #: The ``meshes`` group - 360 assets (``achievement_outline``,
    #: ``action_hero_fore_arm``, ``action_hero_hand``, ``action_hero_head``,
    #: ``action_hero_lower_leg``, and 355 more). Full list in source.
    meshes: MeshesGroup

    #: The ``strings`` group - 1159 strings (``account``, ``achievements``,
    #: ``app_invite``, ``characters``, ``chest``, and 1154 more). Full list in
    #: source.
    strings: StringsGroup

    #: The ``textures`` group - 313 assets (``achievement_boxer``,
    #: ``achievement_cross_hair``, ``achievement_dual_wielding``,
    #: ``achievement_empty``, ``achievement_flawless_victory``, and 308 more).
    #: Full list in source.
    textures: TexturesGroup

_TREE = {
    'audio': {
        'achievement': 's',
        'action_hero1': 's',
        'action_hero2': 's',
        'action_hero3': 's',
        'action_hero4': 's',
        'action_hero_death': 's',
        'action_hero_fall': 's',
        'action_hero_hit1': 's',
        'action_hero_hit2': 's',
        'activate_beep': 's',
        'agent1': 's',
        'agent2': 's',
        'agent3': 's',
        'agent4': 's',
        'agent_death': 's',
        'agent_fall': 's',
        'agent_hit1': 's',
        'agent_hit2': 's',
        'alarm': 's',
        'ali1': 's',
        'ali2': 's',
        'ali3': 's',
        'ali4': 's',
        'ali_death': 's',
        'ali_fall': 's',
        'ali_hit1': 's',
        'ali_hit2': 's',
        'alien1': 's',
        'alien2': 's',
        'alien3': 's',
        'alien4': 's',
        'alien_death': 's',
        'alien_fall': 's',
        'alien_hit1': 's',
        'alien_hit2': 's',
        'announce_eight': 's',
        'announce_five': 's',
        'announce_four': 's',
        'announce_nine': 's',
        'announce_one': 's',
        'announce_seven': 's',
        'announce_six': 's',
        'announce_ten': 's',
        'announce_three': 's',
        'announce_two': 's',
        'assassin1': 's',
        'assassin2': 's',
        'assassin3': 's',
        'assassin4': 's',
        'assassin_death': 's',
        'assassin_fall': 's',
        'assassin_hit1': 's',
        'assassin_hit2': 's',
        'aww': 's',
        'bear1': 's',
        'bear2': 's',
        'bear3': 's',
        'bear4': 's',
        'bear_death': 's',
        'bear_fall': 's',
        'bear_hit1': 's',
        'bear_hit2': 's',
        'bell_high': 's',
        'bell_low': 's',
        'bell_med': 's',
        'big_impact': 's',
        'big_impact2': 's',
        'block': 's',
        'bomb_drop01': 's',
        'bomb_drop02': 's',
        'bomb_roll01': 's',
        'bones1': 's',
        'bones2': 's',
        'bones3': 's',
        'bones_death': 's',
        'bones_fall': 's',
        'boo': 's',
        'box_drop': 's',
        'boxing_bell': 's',
        'bunny1': 's',
        'bunny2': 's',
        'bunny3': 's',
        'bunny4': 's',
        'bunny_death': 's',
        'bunny_fall': 's',
        'bunny_hit1': 's',
        'bunny_hit2': 's',
        'bunny_jump': 's',
        'cash_register2': 's',
        'char_select_music': 's',
        'cheer': 's',
        'cork_pop2': 's',
        'cowboy1': 's',
        'cowboy2': 's',
        'cowboy3': 's',
        'cowboy4': 's',
        'cowboy_death': 's',
        'cowboy_fall': 's',
        'cowboy_hit1': 's',
        'cowboy_hit2': 's',
        'crowd_chant': 's',
        'cyborg1': 's',
        'cyborg2': 's',
        'cyborg3': 's',
        'cyborg4': 's',
        'cyborg_death': 's',
        'cyborg_fall': 's',
        'cyborg_hit1': 's',
        'cyborg_hit2': 's',
        'cymbal': 's',
        'debris_fall': 's',
        'deek2': 's',
        'ding_small': 's',
        'ding_small_high': 's',
        'dripity': 's',
        'drum_roll': 's',
        'drum_roll_short': 's',
        'explosion01': 's',
        'explosion02': 's',
        'explosion03': 's',
        'explosion04': 's',
        'explosion05': 's',
        'fanfare': 's',
        'flag_catcher_music': 's',
        'flying_music': 's',
        'foghorn': 's',
        'foot_impact01': 's',
        'foot_impact02': 's',
        'foot_impact03': 's',
        'forward_march_music': 's',
        'freeze': 's',
        'frosty01': 's',
        'frosty02': 's',
        'frosty03': 's',
        'frosty04': 's',
        'frosty05': 's',
        'frosty_death': 's',
        'frosty_fall': 's',
        'frosty_hit01': 's',
        'frosty_hit02': 's',
        'frosty_hit03': 's',
        'fuse01': 's',
        'gasp': 's',
        'gladiator1': 's',
        'gladiator2': 's',
        'gladiator3': 's',
        'gladiator4': 's',
        'gladiator_death': 's',
        'gladiator_fall': 's',
        'gladiator_hit1': 's',
        'gladiator_hit2': 's',
        'gong': 's',
        'grand_romp_music': 's',
        'gravel_skid': 's',
        'health_powerup': 's',
        'hiss': 's',
        'impact_hard': 's',
        'impact_hard2': 's',
        'impact_hard3': 's',
        'impact_medium': 's',
        'impact_medium2': 's',
        'jack01': 's',
        'jack02': 's',
        'jack03': 's',
        'jack04': 's',
        'jack05': 's',
        'jack06': 's',
        'jack_death01': 's',
        'jack_fall01': 's',
        'jack_hit01': 's',
        'jack_hit02': 's',
        'jack_hit03': 's',
        'jack_hit04': 's',
        'jack_hit05': 's',
        'jack_hit06': 's',
        'jack_hit07': 's',
        'jumpsuit1': 's',
        'jumpsuit2': 's',
        'jumpsuit3': 's',
        'jumpsuit4': 's',
        'jumpsuit_death': 's',
        'jumpsuit_fall': 's',
        'jumpsuit_hit1': 's',
        'jumpsuit_hit2': 's',
        'kronk1': 's',
        'kronk10': 's',
        'kronk2': 's',
        'kronk3': 's',
        'kronk4': 's',
        'kronk5': 's',
        'kronk6': 's',
        'kronk7': 's',
        'kronk8': 's',
        'kronk9': 's',
        'kronk_death': 's',
        'kronk_fall': 's',
        'laser': 's',
        'laser_reverse': 's',
        'mel01': 's',
        'mel02': 's',
        'mel03': 's',
        'mel04': 's',
        'mel05': 's',
        'mel06': 's',
        'mel07': 's',
        'mel08': 's',
        'mel09': 's',
        'mel10': 's',
        'mel_death01': 's',
        'mel_fall01': 's',
        'menu_music': 's',
        'metal_hit': 's',
        'metal_skid': 's',
        'nice': 's',
        'ninja_attack1': 's',
        'ninja_attack2': 's',
        'ninja_attack3': 's',
        'ninja_attack4': 's',
        'ninja_attack5': 's',
        'ninja_attack6': 's',
        'ninja_attack7': 's',
        'ninja_death1': 's',
        'ninja_fall1': 's',
        'ninja_hit1': 's',
        'ninja_hit2': 's',
        'ninja_hit3': 's',
        'ninja_hit4': 's',
        'ninja_hit5': 's',
        'ninja_hit6': 's',
        'ninja_hit7': 's',
        'ninja_hit8': 's',
        'old_lady1': 's',
        'old_lady2': 's',
        'old_lady3': 's',
        'old_lady4': 's',
        'old_lady_death': 's',
        'old_lady_fall': 's',
        'old_lady_hit1': 's',
        'old_lady_hit2': 's',
        'ooh': 's',
        'opera_singer1': 's',
        'opera_singer2': 's',
        'opera_singer3': 's',
        'opera_singer4': 's',
        'opera_singer_death': 's',
        'opera_singer_fall': 's',
        'opera_singer_hit1': 's',
        'opera_singer_hit2': 's',
        'orchestra_hit': 's',
        'orchestra_hit2': 's',
        'orchestra_hit3': 's',
        'orchestra_hit4': 's',
        'orchestra_hit_big1': 's',
        'orchestra_hit_big2': 's',
        'penguin1': 's',
        'penguin2': 's',
        'penguin3': 's',
        'penguin4': 's',
        'penguin_death': 's',
        'penguin_fall': 's',
        'penguin_hit1': 's',
        'penguin_hit2': 's',
        'pixie1': 's',
        'pixie2': 's',
        'pixie3': 's',
        'pixie4': 's',
        'pixie_death': 's',
        'pixie_fall': 's',
        'pixie_hit1': 's',
        'pixie_hit2': 's',
        'player_death': 's',
        'player_left': 's',
        'pop01': 's',
        'powerup01': 's',
        'punch_strong01': 's',
        'punch_strong02': 's',
        'punch_swish': 's',
        'punch_weak01': 's',
        'race_beep1': 's',
        'race_beep2': 's',
        'ref_whistle': 's',
        'rev_up': 's',
        'robot1': 's',
        'robot2': 's',
        'robot3': 's',
        'robot4': 's',
        'robot_death': 's',
        'robot_fall': 's',
        'robot_hit1': 's',
        'robot_hit2': 's',
        'run_away_music': 's',
        'santa01': 's',
        'santa02': 's',
        'santa03': 's',
        'santa04': 's',
        'santa05': 's',
        'santa_death': 's',
        'santa_fall': 's',
        'santa_hit01': 's',
        'santa_hit02': 's',
        'santa_hit03': 's',
        'santa_hit04': 's',
        'scamper01': 's',
        'scary_music': 's',
        'score': 's',
        'score_hit01': 's',
        'score_hit02': 's',
        'scores_epic_music': 's',
        'shatter': 's',
        'shield_down': 's',
        'shield_hit': 's',
        'shield_up': 's',
        'skid01': 's',
        'slow_epic_music': 's',
        'spawn': 's',
        'spaz_attack01': 's',
        'spaz_attack02': 's',
        'spaz_attack03': 's',
        'spaz_attack04': 's',
        'spaz_death01': 's',
        'spaz_eff': 's',
        'spaz_fall01': 's',
        'spaz_impact01': 's',
        'spaz_impact02': 's',
        'spaz_impact03': 's',
        'spaz_impact04': 's',
        'spaz_jump01': 's',
        'spaz_jump02': 's',
        'spaz_jump03': 's',
        'spaz_jump04': 's',
        'spaz_ow': 's',
        'spaz_pickup01': 's',
        'spaz_scream01': 's',
        'splatter': 's',
        'sports_music': 's',
        'sticky_impact': 's',
        'super_punch': 's',
        'superhero1': 's',
        'superhero2': 's',
        'superhero3': 's',
        'superhero4': 's',
        'superhero_death': 's',
        'superhero_fall': 's',
        'superhero_hit1': 's',
        'superhero_hit2': 's',
        'survival_music': 's',
        'swip': 's',
        'swip2': 's',
        'techno_hit01': 's',
        'tick': 's',
        'ticking': 's',
        'to_the_death_music': 's',
        'trash_rummage': 's',
        'victory_music': 's',
        'warn_beep': 's',
        'warn_beeps': 's',
        'warrior1': 's',
        'warrior2': 's',
        'warrior3': 's',
        'warrior4': 's',
        'warrior_death': 's',
        'warrior_fall': 's',
        'warrior_hit1': 's',
        'warrior_hit2': 's',
        'when_johnny_comes_marching_home_music': 's',
        'witch1': 's',
        'witch2': 's',
        'witch3': 's',
        'witch4': 's',
        'witch_death': 's',
        'witch_fall': 's',
        'witch_hit1': 's',
        'witch_hit2': 's',
        'wizard1': 's',
        'wizard2': 's',
        'wizard3': 's',
        'wizard4': 's',
        'wizard_death': 's',
        'wizard_fall': 's',
        'wizard_hit1': 's',
        'wizard_hit2': 's',
        'woo': 's',
        'woo2': 's',
        'woo3': 's',
        'wood_debris_fall': 's',
        'wow': 's',
        'wrestler1': 's',
        'wrestler2': 's',
        'wrestler3': 's',
        'wrestler4': 's',
        'wrestler_death': 's',
        'wrestler_fall': 's',
        'wrestler_hit1': 's',
        'wrestler_hit2': 's',
        'yeah': 's',
        'zoe_attack01': 's',
        'zoe_attack02': 's',
        'zoe_attack03': 's',
        'zoe_attack04': 's',
        'zoe_death01': 's',
        'zoe_eff': 's',
        'zoe_fall01': 's',
        'zoe_impact01': 's',
        'zoe_impact02': 's',
        'zoe_impact03': 's',
        'zoe_impact04': 's',
        'zoe_jump01': 's',
        'zoe_jump02': 's',
        'zoe_jump03': 's',
        'zoe_ow': 's',
        'zoe_pickup01': 's',
        'zoe_scream01': 's',
    },
    'meshes': {
        'achievement_outline': 'm',
        'action_hero_fore_arm': 'm',
        'action_hero_hand': 'm',
        'action_hero_head': 'm',
        'action_hero_lower_leg': 'm',
        'action_hero_pelvis': 'm',
        'action_hero_toes': 'm',
        'action_hero_torso': 'm',
        'action_hero_upper_arm': 'm',
        'action_hero_upper_leg': 'm',
        'agent_fore_arm': 'm',
        'agent_hand': 'm',
        'agent_head': 'm',
        'agent_lower_leg': 'm',
        'agent_pelvis': 'm',
        'agent_toes': 'm',
        'agent_torso': 'm',
        'agent_upper_arm': 'm',
        'agent_upper_leg': 'm',
        'ali_fore_arm': 'm',
        'ali_hand': 'm',
        'ali_head': 'm',
        'ali_lower_leg': 'm',
        'ali_pelvis': 'm',
        'ali_toes': 'm',
        'ali_torso': 'm',
        'ali_upper_arm': 'm',
        'ali_upper_leg': 'm',
        'alien_fore_arm': 'm',
        'alien_hand': 'm',
        'alien_head': 'm',
        'alien_lower_leg': 'm',
        'alien_pelvis': 'm',
        'alien_toes': 'm',
        'alien_torso': 'm',
        'alien_upper_arm': 'm',
        'alien_upper_leg': 'm',
        'always_land_bg': 'm',
        'always_land_level': 'm',
        'always_land_level_bottom': 'm',
        'always_land_vrfill_mound': 'm',
        'angry_computer_transparent': 'm',
        'assassin_fore_arm': 'm',
        'assassin_hand': 'm',
        'assassin_head': 'm',
        'assassin_lower_leg': 'm',
        'assassin_pelvis': 'm',
        'assassin_toes': 'm',
        'assassin_torso': 'm',
        'assassin_upper_arm': 'm',
        'assassin_upper_leg': 'm',
        'bear_fore_arm': 'm',
        'bear_hand': 'm',
        'bear_head': 'm',
        'bear_lower_leg': 'm',
        'bear_pelvis': 'm',
        'bear_toes': 'm',
        'bear_torso': 'm',
        'bear_upper_arm': 'm',
        'bear_upper_leg': 'm',
        'big_g': 'm',
        'big_gbottom': 'm',
        'bomb': 'm',
        'bomb_sticky': 'm',
        'bones_fore_arm': 'm',
        'bones_hand': 'm',
        'bones_head': 'm',
        'bones_lower_leg': 'm',
        'bones_pelvis': 'm',
        'bones_toes': 'm',
        'bones_torso': 'm',
        'bones_upper_arm': 'm',
        'bones_upper_leg': 'm',
        'bridgit_level_bottom': 'm',
        'bridgit_level_top': 'm',
        'bunny_fore_arm': 'm',
        'bunny_hand': 'm',
        'bunny_head': 'm',
        'bunny_lower_leg': 'm',
        'bunny_pelvis': 'm',
        'bunny_toes': 'm',
        'bunny_torso': 'm',
        'bunny_upper_arm': 'm',
        'bunny_upper_leg': 'm',
        'button_null': 'm',
        'courtyard_level': 'm',
        'courtyard_level_bottom': 'm',
        'cowboy_fore_arm': 'm',
        'cowboy_hand': 'm',
        'cowboy_head': 'm',
        'cowboy_lower_leg': 'm',
        'cowboy_pelvis': 'm',
        'cowboy_toes': 'm',
        'cowboy_torso': 'm',
        'cowboy_upper_arm': 'm',
        'cowboy_upper_leg': 'm',
        'crag_castle_level': 'm',
        'crag_castle_level_bottom': 'm',
        'crag_castle_vrfill_mound': 'm',
        'currency_meter': 'm',
        'currency_plus_button': 'm',
        'cyborg_fore_arm': 'm',
        'cyborg_hand': 'm',
        'cyborg_head': 'm',
        'cyborg_lower_leg': 'm',
        'cyborg_pelvis': 'm',
        'cyborg_toes': 'm',
        'cyborg_torso': 'm',
        'cyborg_upper_arm': 'm',
        'cyborg_upper_leg': 'm',
        'doom_shroom_bg': 'm',
        'doom_shroom_level': 'm',
        'doom_shroom_stem': 'm',
        'doom_shroom_vrfill': 'm',
        'egg': 'm',
        'football_stadium': 'm',
        'football_stadium_vrfill': 'm',
        'frame_inset': 'm',
        'frosty_fore_arm': 'm',
        'frosty_hand': 'm',
        'frosty_head': 'm',
        'frosty_lower_leg': 'm',
        'frosty_pelvis': 'm',
        'frosty_toes': 'm',
        'frosty_torso': 'm',
        'frosty_upper_arm': 'm',
        'frosty_upper_leg': 'm',
        'gladiator_fore_arm': 'm',
        'gladiator_hand': 'm',
        'gladiator_head': 'm',
        'gladiator_lower_leg': 'm',
        'gladiator_pelvis': 'm',
        'gladiator_toes': 'm',
        'gladiator_torso': 'm',
        'gladiator_upper_arm': 'm',
        'gladiator_upper_leg': 'm',
        'heart_opaque': 'm',
        'heart_transparent': 'm',
        'hockey_stadium_inner': 'm',
        'hockey_stadium_outer': 'm',
        'hockey_stadium_stands': 'm',
        'image2x1_vertical': 'm',
        'impact_bomb': 'm',
        'jack_fore_arm': 'm',
        'jack_hand': 'm',
        'jack_head': 'm',
        'jack_lower_leg': 'm',
        'jack_toes': 'm',
        'jack_torso': 'm',
        'jack_upper_arm': 'm',
        'jack_upper_leg': 'm',
        'jumpsuit_fore_arm': 'm',
        'jumpsuit_hand': 'm',
        'jumpsuit_head': 'm',
        'jumpsuit_lower_leg': 'm',
        'jumpsuit_pelvis': 'm',
        'jumpsuit_toes': 'm',
        'jumpsuit_torso': 'm',
        'jumpsuit_upper_arm': 'm',
        'jumpsuit_upper_leg': 'm',
        'kronk_fore_arm': 'm',
        'kronk_hand': 'm',
        'kronk_head': 'm',
        'kronk_lower_leg': 'm',
        'kronk_pelvis': 'm',
        'kronk_toes': 'm',
        'kronk_torso': 'm',
        'kronk_upper_arm': 'm',
        'kronk_upper_leg': 'm',
        'lake_frigid': 'm',
        'lake_frigid_reflections': 'm',
        'lake_frigid_top': 'm',
        'lake_frigid_vrfill': 'm',
        'land_mine': 'm',
        'level_select_button_opaque': 'm',
        'level_select_button_transparent': 'm',
        'logo': 'm',
        'logo_transparent': 'm',
        'mel_fore_arm': 'm',
        'mel_hand': 'm',
        'mel_head': 'm',
        'mel_lower_leg': 'm',
        'mel_toes': 'm',
        'mel_torso': 'm',
        'mel_upper_arm': 'm',
        'mel_upper_leg': 'm',
        'meter_transparent': 'm',
        'monkey_face_level': 'm',
        'monkey_face_level_bottom': 'm',
        'nature_background': 'm',
        'nature_background_vrfill': 'm',
        'neo_spaz_fore_arm': 'm',
        'neo_spaz_hand': 'm',
        'neo_spaz_head': 'm',
        'neo_spaz_lower_leg': 'm',
        'neo_spaz_pelvis': 'm',
        'neo_spaz_toes': 'm',
        'neo_spaz_torso': 'm',
        'neo_spaz_upper_arm': 'm',
        'neo_spaz_upper_leg': 'm',
        'ninja_fore_arm': 'm',
        'ninja_hand': 'm',
        'ninja_head': 'm',
        'ninja_lower_leg': 'm',
        'ninja_pelvis': 'm',
        'ninja_toes': 'm',
        'ninja_torso': 'm',
        'ninja_upper_arm': 'm',
        'ninja_upper_leg': 'm',
        'old_lady_fore_arm': 'm',
        'old_lady_hand': 'm',
        'old_lady_head': 'm',
        'old_lady_lower_leg': 'm',
        'old_lady_pelvis': 'm',
        'old_lady_toes': 'm',
        'old_lady_torso': 'm',
        'old_lady_upper_arm': 'm',
        'old_lady_upper_leg': 'm',
        'opera_singer_fore_arm': 'm',
        'opera_singer_hand': 'm',
        'opera_singer_head': 'm',
        'opera_singer_lower_leg': 'm',
        'opera_singer_pelvis': 'm',
        'opera_singer_toes': 'm',
        'opera_singer_torso': 'm',
        'opera_singer_upper_arm': 'm',
        'opera_singer_upper_leg': 'm',
        'penguin_fore_arm': 'm',
        'penguin_hand': 'm',
        'penguin_head': 'm',
        'penguin_lower_leg': 'm',
        'penguin_pelvis': 'm',
        'penguin_toes': 'm',
        'penguin_torso': 'm',
        'penguin_upper_arm': 'm',
        'penguin_upper_leg': 'm',
        'pixie_fore_arm': 'm',
        'pixie_hand': 'm',
        'pixie_head': 'm',
        'pixie_lower_leg': 'm',
        'pixie_pelvis': 'm',
        'pixie_toes': 'm',
        'pixie_torso': 'm',
        'pixie_upper_arm': 'm',
        'pixie_upper_leg': 'm',
        'plastic_eyes_transparent': 'm',
        'player_lineup1_transparent': 'm',
        'player_lineup2_transparent': 'm',
        'player_lineup3_transparent': 'm',
        'player_lineup4_transparent': 'm',
        'powerup': 'm',
        'powerup_simple': 'm',
        'puck': 'm',
        'rampage_bg': 'm',
        'rampage_bg2': 'm',
        'rampage_level': 'm',
        'rampage_level_bottom': 'm',
        'rampage_vrfill': 'm',
        'robot_fore_arm': 'm',
        'robot_hand': 'm',
        'robot_head': 'm',
        'robot_lower_leg': 'm',
        'robot_pelvis': 'm',
        'robot_toes': 'm',
        'robot_torso': 'm',
        'robot_upper_arm': 'm',
        'robot_upper_leg': 'm',
        'roundabout_level': 'm',
        'roundabout_level_bottom': 'm',
        'running_shoes': 'm',
        'santa_fore_arm': 'm',
        'santa_hand': 'm',
        'santa_head': 'm',
        'santa_lower_leg': 'm',
        'santa_toes': 'm',
        'santa_torso': 'm',
        'santa_upper_arm': 'm',
        'santa_upper_leg': 'm',
        'scroll_widget_short': 'm',
        'step_right_up_level': 'm',
        'step_right_up_level_bottom': 'm',
        'step_right_up_vrfill_mound': 'm',
        'superhero_fore_arm': 'm',
        'superhero_hand': 'm',
        'superhero_head': 'm',
        'superhero_lower_leg': 'm',
        'superhero_pelvis': 'm',
        'superhero_toes': 'm',
        'superhero_torso': 'm',
        'superhero_upper_arm': 'm',
        'superhero_upper_leg': 'm',
        'the_pad_bg': 'm',
        'the_pad_bgsmall': 'm',
        'the_pad_level': 'm',
        'the_pad_level_bottom': 'm',
        'the_pad_vrfill_bottom': 'm',
        'the_pad_vrfill_mound': 'm',
        'the_pad_vrfill_top': 'm',
        'tip_top_bg': 'm',
        'tip_top_level': 'm',
        'tip_top_level_bottom': 'm',
        'tnt': 'm',
        'toolbar_backing': 'm',
        'toolbar_backing_bottom': 'm',
        'toolbar_backing_bottom2': 'm',
        'toolbar_backing_opaque': 'm',
        'toolbar_backing_top': 'm',
        'toolbar_backing_top2': 'm',
        'toolbar_backing_transparent': 'm',
        'tower_dlevel': 'm',
        'tower_dlevel_bottom': 'm',
        'trees': 'm',
        'warrior_fore_arm': 'm',
        'warrior_hand': 'm',
        'warrior_head': 'm',
        'warrior_lower_leg': 'm',
        'warrior_pelvis': 'm',
        'warrior_toes': 'm',
        'warrior_torso': 'm',
        'warrior_upper_arm': 'm',
        'warrior_upper_leg': 'm',
        'window_bgblotch': 'm',
        'witch_fore_arm': 'm',
        'witch_hand': 'm',
        'witch_head': 'm',
        'witch_lower_leg': 'm',
        'witch_pelvis': 'm',
        'witch_toes': 'm',
        'witch_torso': 'm',
        'witch_upper_arm': 'm',
        'witch_upper_leg': 'm',
        'wizard_fore_arm': 'm',
        'wizard_hand': 'm',
        'wizard_head': 'm',
        'wizard_lower_leg': 'm',
        'wizard_pelvis': 'm',
        'wizard_toes': 'm',
        'wizard_torso': 'm',
        'wizard_upper_arm': 'm',
        'wizard_upper_leg': 'm',
        'wrestler_fore_arm': 'm',
        'wrestler_hand': 'm',
        'wrestler_head': 'm',
        'wrestler_lower_leg': 'm',
        'wrestler_pelvis': 'm',
        'wrestler_toes': 'm',
        'wrestler_torso': 'm',
        'wrestler_upper_arm': 'm',
        'wrestler_upper_leg': 'm',
        'zig_zag_level': 'm',
        'zig_zag_level_bottom': 'm',
        'zoe_fore_arm': 'm',
        'zoe_hand': 'm',
        'zoe_head': 'm',
        'zoe_lower_leg': 'm',
        'zoe_pelvis': 'm',
        'zoe_toes': 'm',
        'zoe_torso': 'm',
        'zoe_upper_arm': 'm',
        'zoe_upper_leg': 'm',
    },
    'strings': {
        'account': {
            'accounts': (),
            'achievement_progress': ('complete', 'total'),
            'ban_this_player': (),
            'campaign_progress': ('progress',),
            'create_an_account': (),
            'delete_account': (),
            'google_play_games_account_switch': (),
            'manage_account': (),
            'not_signed_in': (),
            'player_info': (),
            'report_this_player': (),
            'sign_in': (),
            'sign_in_for_codes': (),
            'sign_in_info': (),
            'sign_in_no_connection': (),
            'sign_in_with': ('service',),
            'sign_in_with_device': (),
            'sign_in_with_device_info': (),
            'sign_in_with_email': (),
            'sign_out': (),
            'signing_in': (),
            'signing_out': (),
            'submitting_code': (),
            'tickets': ('count',),
            'title': (),
            'trophies_this_season': (),
            'v2_link_instructions': (),
            'you_are_signed_in_as': (),
        },
        'achievements': {
            'boom_goes_the_dynamite': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'boxer': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'dual_wielding': {
                'description_full': (),
                'description_full_complete': (),
                'name': (),
            },
            'flawless_victory': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'free_loader': {
                'description_full': (),
                'description_full_complete': (),
                'name': (),
            },
            'gold_miner': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'got_the_moves': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'in_control': {
                'description_full': (),
                'description_full_complete': (),
                'name': (),
            },
            'last_stand_god': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'last_stand_master': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'last_stand_wizard': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'mine_games': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'off_you_go_then': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'onslaught_god': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'onslaught_master': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'onslaught_training_victory': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'onslaught_wizard': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'precision_bombing': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'pro_boxer': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'pro_football_shutout': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'pro_football_victory': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'pro_onslaught_victory': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'pro_runaround_victory': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'rookie_football_shutout': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'rookie_football_victory': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'rookie_onslaught_victory': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'runaround_god': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'runaround_master': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'runaround_wizard': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'sharing_is_caring': {
                'description_full': (),
                'description_full_complete': (),
                'name': (),
            },
            'stayin_alive': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'super_mega_punch': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'super_punch': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'team_player': {
                'description_full': (),
                'description_full_complete': (),
                'name': (),
            },
            'the_great_wall': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'the_wall': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'tnt_terror': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': (),
            },
            'uber_football_shutout': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'uber_football_victory': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'uber_onslaught_victory': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
            'uber_runaround_victory': {
                'description': (),
                'description_complete': (),
                'description_full': ('level',),
                'description_full_complete': ('level',),
                'name': ('level',),
            },
        },
        'app_invite': {
            'email_it': (),
            'enjoy': (),
            'friend_has_sent_promo': ('count', 'app_name', 'name'),
            'friend_promo_award': ('count',),
            'friend_promo_expire': ('expire_hours',),
            'friend_promo_instructions': ('app_name',),
            'friend_promo_redeem_long': ('count', 'max_uses'),
            'friend_promo_redeem_short': ('count',),
            'requesting_code': (),
            'share_code': (),
            'where_to_enter': (),
            'you_have_been_sent_promo': ('app_name',),
        },
        'characters': {
            'agent_johnson': (),
            'b9000': (),
            'bernard': (),
            'betty': (),
            'bones': (),
            'butch': (),
            'easter_bunny': (),
            'frosty': (),
            'gretel': (),
            'grumbledorf': (),
            'jack_morgan': (),
            'kronk': (),
            'lee': (),
            'lucky': (),
            'mel': (),
            'middle_man': (),
            'pascal': (),
            'pixel': (),
            'santa_claus': (),
            'snake_shadow': (),
            'spaz': (),
            'taobao_mascot': (),
            'todd_mcburton': (),
            'zoe': (),
        },
        'chest': {
            'open': (),
            'open_me': (),
            'open_now': (),
            'open_now_description': (),
            'prize_odds': (),
            'reduce_wait': (),
            'slot_description': (),
            'slot_number': ('num',),
            'stop_reminding_me': (),
            'unlocks_in': (),
        },
        'controls': {
            'fire_tv_remote_warning': ('remote_app_name',),
            'move': (),
            'move_directions': ('up', 'left', 'down', 'right'),
            'run': (),
            'run_hold_any_button': (),
            'run_hold_any_key': (),
        },
        'coop': {
            'achievement_label': (),
            'achievements_remaining': (),
            'campaign': (),
            'chest_slots_full_warning': (),
            'current_best': (),
            'custom': (),
            'difficulty_hard_only': (),
            'difficulty_hard_unlock_only': (),
            'entry_fee': (),
            'level_is_locked': ('level',),
            'level_must_be_completed_first': ('level',),
            'level_unlocked': (),
            'next_level': (),
            'no_achievements_remaining': (),
            'no_tournaments_in_test_build': (),
            'of_total': ('total',),
            'player_count_abbreviated': ('count',),
            'power_ranking_points': ('number',),
            'prizes': (),
            'time_remaining': (),
            'tournament': (),
            'tournament_checking_state': (),
            'tournament_ended': (),
            'tournament_info': (),
            'tournaments': (),
            'tournaments_disabled_workspace': (),
        },
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
        'coop_score': {
            'best_rating': ('rating',),
            'complete_level_to_proceed': (),
            'current_standing': ('rank',),
            'final_time': (),
            'friend_scores_unavailable': (),
            'last_games': ('count',),
            'level_unlocked': (),
            'multi_player_count': ('count',),
            'new_personal_best': (),
            'next_level': (),
            'not_enough_players_remaining': (),
            'out_of': ('rank', 'all'),
            'rating': (),
            'score_list_unavailable': (),
            'score_was': ('count',),
            'single_player_count': (),
            'tournament_standings': (),
            'world_scores_unavailable': (),
            'worlds_best_scores': (),
            'worlds_best_times': (),
            'your_best_scores': (),
            'your_best_times': (),
        },
        'credits': {
            'additional_audio_art_ideas': ('name',),
            'additional_music_from': ('name',),
            'all_my_family': (),
            'coding_graphics_audio': ('name',),
            'language_translations': (),
            'legal': (),
            'public_domain_music_via': ('name',),
            'software_based_on': ('name',),
            'song_credit': (
                'title',
                'performer',
                'composer',
                'arranger',
                'publisher',
                'source',
            ),
            'sound_and_music': (),
            'sounds_source': ('source',),
            'special_thanks': (),
            'thanks_especially_to': ('name',),
            'title': ('app_name',),
            'whoever_invented_coffee': (),
        },
        'economy': {
            'received_tickets': ('count',),
            'you_got_tokens': ('tokens',),
        },
        'file_selector': {
            'select_file': (),
            'select_file_or_folder': (),
            'select_folder': (),
            'use_this_folder': (),
        },
        'game': {
            'completion_bonus': (),
            'disqualified_player_left': ('team', 'player'),
            'double_kill': (),
            'draw': (),
            'epic_description_filter': ('description',),
            'epic_name_filter': ('name',),
            'fail': (),
            'final_scores': (),
            'five_kill': (),
            'flawless_wave': (),
            'game_on_map': ('name', 'mapname'),
            'killing_track_skipper': ('name',),
            'lap_number': ('current', 'total'),
            'lives_bonus': (),
            'multi_kill': ('count',),
            'name_betrayed': ('name', 'victim'),
            'name_died': ('name',),
            'name_killed': ('name', 'victim'),
            'name_scores': ('name',),
            'name_suicide': ('name',),
            'no_valid_maps_error': (),
            'onslaught_respawn': ('player', 'wave'),
            'own_flag_at_base_warning': (),
            'paused_by_host': (),
            'perfect_wave': (),
            'points_gained': ('points',),
            'points_gained_titled': ('points', 'title'),
            'press_any_button_continue': (),
            'press_any_button_play_again': (),
            'press_any_key_button_continue': (),
            'press_any_key_button_play_again': (),
            'press_jump_to_fly': (),
            'quad_kill': (),
            'reach_wave_2': (),
            'score': (),
            'solo_name_filter': ('name',),
            'time_bonus': (),
            'time_bonus_amount': ('amount',),
            'time_expired': (),
            'tip_title': (),
            'tournament_time_expired': (),
            'triple_kill': (),
            'turbo_warning': ('name',),
            'victory': (),
            'vs': (),
            'waiting_for_host': ('host',),
            'wave': (),
            'wave_number': ('number',),
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
        'game_settings': {
            'allow_negative_scores': (),
            'balance_total_lives': (),
            'bomb_spawning': (),
            'chosen_one_gets_gloves': (),
            'chosen_one_gets_shield': (),
            'chosen_one_time': (),
            'eight_seconds': (),
            'enable_impact_bombs': (),
            'enable_triple_bombs': (),
            'entire_team_must_finish': (),
            'epic_mode': (),
            'five_minutes': (),
            'flag_idle_return_time': (),
            'flag_touch_return_time': (),
            'four_seconds': (),
            'hold_time': (),
            'kills_to_win_per_player': (),
            'laps': (),
            'lives_per_player': (),
            'long': (),
            'longer': (),
            'mine_spawning': (),
            'no_mines': (),
            'none': (),
            'normal': (),
            'one_minute': (),
            'one_second': (),
            'pro_mode': (),
            'respawn_times': (),
            'score_to_win': (),
            'short': (),
            'shorter': (),
            'solo_mode': (),
            'target_count': (),
            'ten_minutes': (),
            'time_limit': (),
            'twenty_minutes': (),
            'two_minutes': (),
            'two_seconds': (),
        },
        'gather': {
            'about': (),
            'about_description': ('party', 'button'),
            'about_local_multiplayer_extra': (),
            'added_to_favorites': ('name',),
            'address_fetch_error': (),
            'checking': (),
            'connect': (),
            'copy_code': (),
            'copy_code_confirm': (),
            'dedicated_server_info': (),
            'delete_confirm_list': ('list',),
            'description_short': (),
            'disconnect_clients': ('count',),
            'discord_friends': (),
            'discord_join': (),
            'favorites': (),
            'favorites_save': (),
            'free_cloud_server_available': (),
            'free_cloud_server_available_minutes': ('minutes',),
            'free_cloud_server_not_available': (),
            'get_friend_invite_code': (),
            'host_public_party': (),
            'hosting_unavailable': (),
            'invalid_address_error': (),
            'invalid_code_error': (),
            'invalid_name_error': (),
            'invalid_port_error': (),
            'invite_a_friend': ('count',),
            'invite_friends': (),
            'join_public_party': (),
            'joinable_from_internet': (),
            'joinable_no': (),
            'joinable_yes': (),
            'local_network_description': (),
            'make_party_private': (),
            'make_party_public': (),
            'manual': (),
            'manual_address': (),
            'manual_description': (),
            'manual_join_section': (),
            'max_connections': (),
            'max_party_size': (),
            'nearby': (),
            'no_connection': (),
            'no_parties_added': (),
            'no_servers_found': (),
            'party_code': (),
            'party_name': (),
            'party_requires_password': (),
            'party_server_running': (),
            'party_size': (),
            'party_status_checking': (),
            'party_status_joinable': (),
            'party_status_no_connection': (),
            'party_status_not_public': (),
            'password_optional': (),
            'ping': (),
            'port': (),
            'private': (),
            'private_party_cloud_description': (),
            'private_party_host': (),
            'private_party_join': (),
            'public': (),
            'public_host_router_config': (),
            'router_forwarding': ('port',),
            'show_my_address': (),
            'start_hosting': (),
            'start_hosting_paid': ('cost',),
            'start_stop_hosting_minutes': ('minutes',),
            'stop_hosting': (),
            'title': (),
            'unable_to_resolve_host': (),
            'v2_account_required': (),
            'your_address_from_internet': (),
            'your_local_address': (),
        },
        'get_remote': {'info_short': ('app_name', 'remote_app_name')},
        'get_tokens': {
            'free': (),
            'gold_pass': (),
            'gold_pass_desc1': (),
            'gold_pass_desc2': (),
            'gold_pass_desc3': (),
            'not_enough_tokens': (),
            'num_tokens': ('count',),
            'purchase_never_available': (),
            'purchase_not_available': (),
            'remove_ads_offer': (),
            'shiny_new_currency': (),
            'you_have_gold_pass': (),
        },
        'help': {
            'bomb_info': (),
            'can_help': ('app_name',),
            'controllers': (),
            'controllers_info': ('app_name', 'remote_app_name'),
            'controls': (),
            'controls_subtitle': ('app_name',),
            'devices': (),
            'devices_info': ('app_name',),
            'friends': (),
            'friends_good': ('app_name',),
            'jump_info': (),
            'or_punching_something': (),
            'pick_up_info': (),
            'powerup_curse_description': (),
            'powerup_curse_name': (),
            'powerup_health_description': (),
            'powerup_health_name': (),
            'powerup_ice_bombs_description': (),
            'powerup_ice_bombs_name': (),
            'powerup_impact_bombs_description': (),
            'powerup_impact_bombs_name': (),
            'powerup_land_mines_description': (),
            'powerup_land_mines_name': (),
            'powerup_punch_description': (),
            'powerup_punch_name': (),
            'powerup_shield_description': (),
            'powerup_shield_name': (),
            'powerup_sticky_bombs_description': (),
            'powerup_sticky_bombs_name': (),
            'powerup_triple_bombs_description': (),
            'powerup_triple_bombs_name': (),
            'powerups': (),
            'powerups_subtitle': (),
            'punch_info': (),
            'run_info': (),
            'some_days': (),
            'title': ('app_name',),
            'to_get_the_most': (),
            'welcome': ('app_name',),
        },
        'in_game_menu': {
            'end_game': (),
            'end_replay': (),
            'end_test': (),
            'exit_to_menu_confirm': (),
            'just_player': ('name',),
            'leave_game': (),
            'leave_party': (),
            'leave_party_confirm': (),
            'resume': (),
        },
        'inbox': {
            'expired_ago': ('t',),
            'expires_in': ('t',),
            'final_standings': (),
            'must_update': (),
            'no_messages': (),
            'unclaimed_prizes': (),
            'your_prize': (),
        },
        'inventory': {
            'only_available_online': (),
            'only_available_signed_in': (),
            'title': (),
        },
        'keyboard': {
            'change_instructions': (),
            'configuring': ('device',),
            'no_others_available': (),
            'space_key': (),
            'switched': ('name',),
        },
        'kiosk': {
            'demo_menu': (),
            'full_menu': (),
            'single_player_examples': (),
            'versus_examples': (),
        },
        'league': {
            'achievements_unavailable_old_seasons': (),
            'activeness_all_time_info': (),
            'activeness_info': (),
            'all_time': (),
            'bronze': (),
            'current_season': ('number',),
            'diamond': (),
            'gold': (),
            'league': (),
            'league_president': (),
            'league_rank': (),
            'multipliers': (),
            'number_badge': ('number',),
            'power_ranking': (),
            'power_ranking_points_equals': ('number',),
            'power_ranking_points_mult': ('number',),
            'rank_in_league': ('rank', 'name', 'suffix'),
            'season': ('number',),
            'season_ended_days_ago': ('days',),
            'season_ends_days': ('days',),
            'season_ends_hours': ('hours',),
            'season_ends_minutes': ('minutes',),
            'silver': (),
            'to_ranked': (),
            'tournament_required': ('name',),
            'trophy_counts_reset': (),
            'up_to_date_bonus': (),
            'up_to_date_bonus_description': ('percent',),
            'your_power_ranking': (),
        },
        'lobby': {
            'bomb': (),
            'choosing_player': (),
            'create_edit_player': (),
            'press_any_button_to_join': (),
            'press_punch_to_join': (),
            'press_to_override_character': ('buttons',),
            'press_to_select_profile': ('buttons',),
            'press_to_select_team': ('buttons',),
            'ready': (),
        },
        'main_menu': {
            'credits': (),
            'exit_game': (),
            'host_navigating_menus': ('host',),
            'how_to_play': (),
            'mode_arcade': (),
            'mode_demo': (),
            'next_achievements': (),
            'quit': (),
            'test_build': (),
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
        'multi_team': {
            'best_of_final': ('count',),
            'best_of_series': ('count',),
            'deaths': (),
            'deaths_tally': ('count',),
            'first_to_final': ('count',),
            'first_to_series': ('count',),
            'game_leaders': ('count',),
            'games_to': ('wincount', 'losecount'),
            'kills': (),
            'kills_tally': ('count',),
            'most_destroyed_player': (),
            'most_valuable_player': (),
            'most_violent_player': (),
            'must_invite_friends': ('gather',),
            'player': (),
            'series': (),
            'team_label': ('name',),
            'up_first': (),
            'up_next': ('count',),
            'wins': ('name',),
            'wins_the_series_intro': (),
        },
        'party': {
            'add_to_favorites': (),
            'cant_kick_host': (),
            'chat_message': (),
            'chat_muted': (),
            'empty': (),
            'host': (),
            'kick_vote': (),
            'mute_chat': (),
            'title': (),
            'unmute_chat': (),
        },
        'party_queue': {'waiting_in_line': ()},
        'play': {'one_to_four_players': (), 'two_to_eight_players': ()},
        'play_modes': {
            'coop': (),
            'free_for_all': (),
            'single_player_coop': (),
            'teams': (),
        },
        'play_options': {
            'no_valid_games': (),
            'points_to_win': (),
            'series_length': (),
            'show_tutorial': (),
            'shuffle_game_order': (),
            'team_names_colors': (),
            'unlock_in_store': (),
        },
        'playlist': {
            'add_game_button': (),
            'add_game_title': (),
            'cant_delete_default': (),
            'cant_edit_default': (),
            'cant_overwrite_default': (),
            'cant_save_already_exists': (),
            'cant_save_empty': (),
            'cant_share_default': (),
            'customize_title': ('type',),
            'default_list_name': ('playmode',),
            'default_new_list_name': ('playmode',),
            'delete_playlist': (),
            'duplicate_playlist': (),
            'edit_game_button': (),
            'edit_playlist': (),
            'editor_title': (),
            'export_success': ('name',),
            'get_more_games': (),
            'get_more_maps': (),
            'import_instructions': (),
            'import_success': ('type', 'name'),
            'just_epic': (),
            'just_sports': (),
            'list_name': (),
            'map_select_title': ('game',),
            'max_reached': (),
            'new_playlist': (),
            'no_valid_maps': (),
            'playlists': (),
            'remove_game_button': (),
            'single_game_name': ('game',),
        },
        'profile': {
            'account_profile': (),
            'account_profile_info': ('icons',),
            'available': ('name',),
            'cant_delete_account_profile': (),
            'character': (),
            'checking_availability': ('name',),
            'color': (),
            'delete_confirm': ('profile',),
            'get_more_characters': (),
            'get_more_icons': (),
            'global_profile': (),
            'global_profile_info': (),
            'highlight': (),
            'icon': (),
            'in_game_clipped_name': ('name',),
            'local_profile': (),
            'local_profile_info': (),
            'name_description': (),
            'name_not_empty': (),
            'not_enough_tickets': (),
            'nothing_selected': (),
            'profile_already_exists': (),
            'purchasing': (),
            'title_edit': (),
            'title_new': (),
            'unavailable': ('name',),
            'upgrade_profile_info': (),
            'upgrade_to_global': (),
        },
        'profiles': {
            'explanation': (),
            'max_reached': (),
            'new_profile': (),
            'title': (),
        },
        'report': {
            'cheating': (),
            'explanation': (),
            'inappropriate_language': (),
            'reason': (),
        },
        'resource_type_info': {
            'get_tokens': (),
            'tickets_description': (),
            'tokens_description': (),
        },
        'score_types': {
            'flags': (),
            'goals': (),
            'survived': (),
            'time': (),
            'time_held': (),
        },
        'send_info': {'send_info_description': ()},
        'server': {'restarting': (), 'shutting_down': ()},
        'session': {
            'not_enough_players': ('count',),
            'player_delayed_join': ('player',),
            'player_left': ('player',),
            'player_limit_reached': ('count',),
        },
        'settings': {
            'advanced': {
                'always_use_internal_keyboard': (),
                'always_use_internal_keyboard_description': (),
                'disable_camera_gyro': (),
                'disable_camera_shake': (),
                'help_translate': ('app_name',),
                'insecure_connections': (),
                'insecure_connections_description': (),
                'kick_idle_players': (),
                'language': (),
                'modding_guide': (),
                'send_info': (),
                'show_demos_when_idle': (),
                'show_deprecated_login_types': (),
                'show_in_game_ping': (),
                'show_mods_folder': (),
                'title': (),
                'translation_checking': (),
                'translation_editor': ('app_name',),
                'translation_fetch_error': (),
                'translation_inform_me': (),
                'translation_needs_updates': (),
                'translation_up_to_date': (),
            },
            'audio': {
                'music_volume': (),
                'sound_volume': (),
                'soundtrack_description': (),
                'soundtracks': (),
                'title': (),
            },
            'benchmarks': {
                'already_running_in_activity': (),
                'player_count': (),
                'playlist_description': (),
                'playlist_name': (),
                'playlist_type': (),
                'round_duration': (),
                'run_cpu_benchmark': (),
                'run_media_reload_benchmark': (),
                'run_stress_test': (),
                'stress_test': (),
                'title': (),
            },
            'controllers': {
                'gamepad': {
                    'advanced_title': (),
                    'analog_stick_dead_zone': (),
                    'analog_stick_dead_zone_description': (),
                    'applies_to_all': (),
                    'auto_recalibrate': (),
                    'auto_recalibrate_description': (),
                    'clear': (),
                    'dpad': (),
                    'dpad_numbered': ('num',),
                    'enable': (),
                    'extra_start_button': (),
                    'if_nothing_try_analog': (),
                    'if_nothing_try_dpad': (),
                    'ignore_completely': (),
                    'ignore_completely_description': (),
                    'ignored_button': ('num',),
                    'ignored_button_description': (),
                    'press_any_analog_trigger': (),
                    'press_any_button': (),
                    'press_any_button_or_dpad': (),
                    'press_left_right': (),
                    'press_up_down': (),
                    'run_button': ('num',),
                    'run_trigger': ('num',),
                    'run_trigger_description': (),
                    'second_half': (),
                    'secondary': (),
                    'start_button_activates_default': (),
                    'start_button_activates_default_description': (),
                    'title': (),
                    'two_in_one_setup': (),
                    'ui_only': (),
                    'ui_only_description': (),
                    'unassigned_buttons_run': (),
                    'unset': (),
                    'vr_reorient_button': (),
                },
                'keyboard': {
                    'configuring': ('device',),
                    'keyboard2_note': (),
                    'press_any_key': (),
                },
                'touchscreen': {
                    'action_control_scale': (),
                    'actions': (),
                    'buttons': (),
                    'drag_controls': (),
                    'joystick': (),
                    'movement': (),
                    'movement_control_scale': (),
                    'swipe': (),
                    'swipe_controls_hidden': (),
                    'swipe_info': (),
                    'title': (),
                },
                'android_note': (),
                'cant_configure_device': ('device',),
                'configure_controllers': (),
                'configure_in_system_settings': ('device',),
                'configure_keyboard': (),
                'configure_keyboard_p2': (),
                'configure_mobile': (),
                'disable_remote_app': (),
                'disable_xinput': (),
                'disable_xinput_description': (),
                'press_any_button_to_configure': (),
                'remote_best_results': (),
                'remote_configured_in_app': ('remote_app_name',),
                'remote_explanation': ('remote_app_name', 'app_name'),
                'title': (),
            },
            'dev_tools': {
                'create_user_system_scripts': (),
                'delete_user_system_scripts': (),
                'show_dev_console_button': (),
                'title': (),
            },
            'graphics': {
                'fullscreen': (),
                'fullscreen_shortcut_format': ('name', 'shortcut'),
                'max_fps': (),
                'native': (),
                'resolution': (),
                'show_fps': (),
                'textures': (),
                'title': (),
                'tv_border': (),
                'vertical_sync': (),
                'visuals': (),
            },
            'net_testing': {'title': ()},
            'plugins': {
                'auto_enable_new': (),
                'disable_all': (),
                'enable_all': (),
                'none_installed': (),
                'settings_title': (),
                'title': (),
            },
            'testing': {'for_testing_note': ()},
            'vr_testing': {'title': ()},
            'title': (),
        },
        'soundtrack': {
            'cant_delete_default': (),
            'cant_edit_default': (),
            'cant_overwrite_default': (),
            'cant_save_already_exists': (),
            'copy_of': ('name',),
            'default_game_music': (),
            'default_soundtrack_name': (),
            'delete_confirm': ('name',),
            'delete_soundtrack': (),
            'duplicate_soundtrack': (),
            'edit_soundtrack': (),
            'error_playing_music': ('music',),
            'fetching_itunes': (),
            'music_source': (),
            'music_volume_zero_warning': (),
            'new_soundtrack': (),
            'new_soundtrack_name': ('count',),
            'no_music_files_in_folder': (),
            'select_a_playlist': (),
            'test': (),
            'title': (),
            'use_default_game_music': (),
            'use_itunes_playlist': (),
            'use_music_file': (),
            'use_music_folder': (),
            'using_music_app': (),
        },
        'store': {
            'merch': (),
            'pro_name': ('app_name',),
            'unlock_in_store': (),
        },
        'teams': {'bad_guys': (), 'blue': (), 'good_guys': (), 'red': ()},
        'tips': {
            'aim_punches': (),
            'auto_kick_idle': (),
            'cant_reach_ledge': (),
            'characters_identical': (),
            'cook_off_bombs': (),
            'create_profiles': (),
            'ctf_own_flag': (),
            'curse_boxes': (),
            'curse_health_powerup': (),
            'custom_soundtrack': (),
            'dont_always_run': (),
            'dont_overspin': (),
            'endless_high_score': (),
            'fast_fists': (),
            'floss': (),
            'fuse_colors': (),
            'hockey_turn_gradually': (),
            'hold_to_run': (),
            'ice_bombs': (),
            'join_leave_anytime': (),
            'jump_before_throw': (),
            'jump_throw_high': (),
            'keep_moving': (),
            'land_mines_speedy': (),
            'momentum_accuracy': (),
            'one_hit_double_points': (),
            'pickup_flag': ('pickup',),
            'play_with_friends': (),
            'punch_to_escape': (),
            'reduce_visuals_framerate': (),
            'reduce_visuals_heat': (),
            'remote_app': ('remote_app_name',),
            'run_watch_cliffs': (),
            'running_spinning_damage': (),
            'shield_overconfidence': (),
            'spin_punch_respect': (),
            'sticky_bomb_dance': (),
            'sticky_to_head': (),
            'throw_players': (),
            'throw_strength_direction': (),
            'tnt_box': (),
            'trick_enemies': (),
            'whack_head': (),
            'whip_for_distance': (),
            'whiplash_throw': (),
        },
        'tournament_entry': {
            'entering': (),
            'tickets_count': ('count',),
            'title': (),
            'watch_an_ad': (),
        },
        'tournament_scores': {'no_scores_yet': (), 'tournament_standings': ()},
        'tutorial': {
            'cpu_benchmark': (),
            'phrase01': (),
            'phrase02': ('app_name',),
            'phrase03': (),
            'phrase04': ('app_name',),
            'phrase05': (),
            'phrase06': (),
            'phrase07': ('name',),
            'phrase08': (),
            'phrase09': (),
            'phrase10': (),
            'phrase11': (),
            'phrase12': (),
            'phrase13': ('name',),
            'phrase14': ('name',),
            'phrase15': (),
            'phrase16': (),
            'phrase17': (),
            'phrase18': (),
            'phrase19': (),
            'phrase20': (),
            'phrase21': (),
            'phrase22': (),
            'phrase23': (),
            'phrase24': (),
            'phrase25': (),
            'phrase26': (),
            'phrase27': (),
            'phrase28': (),
            'phrase29': (),
            'random_name1': (),
            'random_name2': (),
            'random_name3': (),
            'random_name4': (),
            'random_name5': (),
            'skip_confirm': (),
            'skip_vote_count': ('count', 'total'),
            'skipping': (),
            'tip': (),
            'to_skip_press_anything': (),
        },
        'ui': {
            'achievements': (),
            'activity': (),
            'app_name': (),
            'boost': (),
            'claim': (),
            'demo': (),
            'easy': (),
            'epic_mode': (),
            'exit_app_confirm': ('app_name',),
            'final_score': (),
            'free': (),
            'game_center': (),
            'google_play': (),
            'hard': (),
            'inbox': (),
            'kick': (),
            'leaderboards': (),
            'map': (),
            'not_signed_in_status': (),
            'play': (),
            'playlist': (),
            'points': (),
            'practice': (),
            'quit_app_confirm': ('app_name',),
            'rank': (),
            'remote_app_name': (),
            'stats': (),
            'trophies': (),
        },
        'v2_upgrade': {'device_account_upgrade': ('name',)},
        'watch': {
            'delete_confirm': ('replay',),
            'delete_replay_button': (),
            'my_replays': (),
            'no_replay_selected': (),
            'playback_speed': ('speed',),
            'rename_replay': ('replay',),
            'rename_replay_button': (),
            'rename_warning': ('replay',),
            'replay_delete_error': (),
            'replay_name': (),
            'replay_name_default': (),
            'replay_rename_error': (),
            'replay_rename_error_already_exists': (),
            'replay_rename_error_invalid': (),
            'title': (),
            'watch_replay_button': (),
        },
    },
    'textures': {
        'achievement_boxer': 't',
        'achievement_cross_hair': 't',
        'achievement_dual_wielding': 't',
        'achievement_empty': 't',
        'achievement_flawless_victory': 't',
        'achievement_football_shutout': 't',
        'achievement_football_victory': 't',
        'achievement_free_loader': 't',
        'achievement_got_the_moves': 't',
        'achievement_in_control': 't',
        'achievement_medal_large': 't',
        'achievement_medal_medium': 't',
        'achievement_medal_small': 't',
        'achievement_mine': 't',
        'achievement_off_you_go': 't',
        'achievement_onslaught': 't',
        'achievement_outline': 't',
        'achievement_runaround': 't',
        'achievement_sharing_is_caring': 't',
        'achievement_stayin_alive': 't',
        'achievement_super_punch': 't',
        'achievement_team_player': 't',
        'achievement_tnt': 't',
        'achievement_wall': 't',
        'achievements_icon': 't',
        'action_hero_color': 't',
        'action_hero_color_mask': 't',
        'action_hero_icon': 't',
        'action_hero_icon_color_mask': 't',
        'advanced_icon': 't',
        'agent_color': 't',
        'agent_color_mask': 't',
        'agent_icon': 't',
        'agent_icon_color_mask': 't',
        'ali_color': 't',
        'ali_color_mask': 't',
        'ali_icon': 't',
        'ali_icon_color_mask': 't',
        'ali_splash': 't',
        'alien_color': 't',
        'alien_color_mask': 't',
        'alien_icon': 't',
        'alien_icon_color_mask': 't',
        'always_land_bgcolor': 't',
        'always_land_level_color': 't',
        'always_land_preview': 't',
        'analog_stick': 't',
        'assassin_color': 't',
        'assassin_color_mask': 't',
        'assassin_icon': 't',
        'assassin_icon_color_mask': 't',
        'audio_icon': 't',
        'bar': 't',
        'bear_color': 't',
        'bear_color_mask': 't',
        'bear_icon': 't',
        'bear_icon_color_mask': 't',
        'bg': 't',
        'big_g': 't',
        'big_gpreview': 't',
        'bomb_color': 't',
        'bomb_color_ice': 't',
        'bomb_sticky_color': 't',
        'bones_color': 't',
        'bones_color_mask': 't',
        'bones_icon': 't',
        'bones_icon_color_mask': 't',
        'bridgit_level_color': 't',
        'bridgit_preview': 't',
        'bunny_color': 't',
        'bunny_color_mask': 't',
        'bunny_icon': 't',
        'bunny_icon_color_mask': 't',
        'button_bomb': 't',
        'button_jump': 't',
        'button_pick_up': 't',
        'button_punch': 't',
        'ch_title_char1': 't',
        'ch_title_char2': 't',
        'ch_title_char3': 't',
        'ch_title_char4': 't',
        'ch_title_char5': 't',
        'chest_icon': 't',
        'chest_icon_empty': 't',
        'chest_icon_multi': 't',
        'chest_icon_tint': 't',
        'chest_open_icon': 't',
        'chest_open_icon_tint': 't',
        'circle_zig_zag': 't',
        'clay_stroke': 't',
        'coin': 't',
        'controller_icon': 't',
        'courtyard_level_color': 't',
        'courtyard_preview': 't',
        'cowboy_color': 't',
        'cowboy_color_mask': 't',
        'cowboy_icon': 't',
        'cowboy_icon_color_mask': 't',
        'crag_castle_level_color': 't',
        'crag_castle_preview': 't',
        'cross_out': 't',
        'cross_out_mask': 't',
        'cute_spaz': 't',
        'cyborg_color': 't',
        'cyborg_color_mask': 't',
        'cyborg_icon': 't',
        'cyborg_icon_color_mask': 't',
        'discord_icon': 't',
        'discord_logo': 't',
        'discord_server': 't',
        'doom_shroom_bgcolor': 't',
        'doom_shroom_level_color': 't',
        'doom_shroom_preview': 't',
        'down_button': 't',
        'egg1': 't',
        'egg2': 't',
        'egg3': 't',
        'egg4': 't',
        'egg_tex1': 't',
        'egg_tex2': 't',
        'egg_tex3': 't',
        'empty': 't',
        'file': 't',
        'flag_color': 't',
        'folder': 't',
        'football_stadium': 't',
        'football_stadium_preview': 't',
        'frame_inset': 't',
        'frosty_color': 't',
        'frosty_color_mask': 't',
        'frosty_icon': 't',
        'frosty_icon_color_mask': 't',
        'game_center_icon': 't',
        'github_logo': 't',
        'gladiator_color': 't',
        'gladiator_color_mask': 't',
        'gladiator_icon': 't',
        'gladiator_icon_color_mask': 't',
        'gold_pass': 't',
        'google_play_achievements_icon': 't',
        'google_play_games_icon': 't',
        'google_play_leaderboards_icon': 't',
        'google_plus_icon': 't',
        'google_plus_sign_in_button': 't',
        'graphics_icon': 't',
        'heart': 't',
        'hockey_stadium': 't',
        'hockey_stadium_preview': 't',
        'icon_onslaught': 't',
        'icon_runaround': 't',
        'impact_bomb_color': 't',
        'impact_bomb_color_lit': 't',
        'inventory_icon': 't',
        'jack_color': 't',
        'jack_color_mask': 't',
        'jack_icon': 't',
        'jack_icon_color_mask': 't',
        'jumpsuit_color': 't',
        'jumpsuit_color_mask': 't',
        'jumpsuit_icon': 't',
        'jumpsuit_icon_color_mask': 't',
        'kronk': 't',
        'kronk_color_mask': 't',
        'kronk_icon': 't',
        'kronk_icon_color_mask': 't',
        'lake_frigid': 't',
        'lake_frigid_preview': 't',
        'lake_frigid_reflections': 't',
        'land_mine': 't',
        'land_mine_lit': 't',
        'leaderboards_icon': 't',
        'left_button': 't',
        'level_icon': 't',
        'lock': 't',
        'log_icon': 't',
        'logo': 't',
        'logo_easter': 't',
        'map_preview_mask': 't',
        'medal_bronze': 't',
        'medal_complete': 't',
        'medal_gold': 't',
        'medal_silver': 't',
        'mel_color': 't',
        'mel_color_mask': 't',
        'mel_icon': 't',
        'mel_icon_color_mask': 't',
        'menu_bg': 't',
        'menu_icon': 't',
        'merch': 't',
        'meter': 't',
        'monkey_face_level_color': 't',
        'monkey_face_preview': 't',
        'multiplayer_examples': 't',
        'nature_background_color': 't',
        'neo_spaz_color': 't',
        'neo_spaz_color_mask': 't',
        'neo_spaz_icon': 't',
        'neo_spaz_icon_color_mask': 't',
        'next_level_icon': 't',
        'ninja_color': 't',
        'ninja_color_mask': 't',
        'ninja_icon': 't',
        'ninja_icon_color_mask': 't',
        'null': 't',
        'old_lady_color': 't',
        'old_lady_color_mask': 't',
        'old_lady_icon': 't',
        'old_lady_icon_color_mask': 't',
        'opera_singer_color': 't',
        'opera_singer_color_mask': 't',
        'opera_singer_icon': 't',
        'opera_singer_icon_color_mask': 't',
        'ouya_icon': 't',
        'ouya_obutton': 't',
        'ouya_ubutton': 't',
        'ouya_ybutton': 't',
        'penguin_color': 't',
        'penguin_color_mask': 't',
        'penguin_icon': 't',
        'penguin_icon_color_mask': 't',
        'pixie_color': 't',
        'pixie_color_mask': 't',
        'pixie_icon': 't',
        'pixie_icon_color_mask': 't',
        'player_lineup': 't',
        'plus_button': 't',
        'powerup_bomb': 't',
        'powerup_curse': 't',
        'powerup_health': 't',
        'powerup_ice_bombs': 't',
        'powerup_impact_bombs': 't',
        'powerup_land_mines': 't',
        'powerup_punch': 't',
        'powerup_shield': 't',
        'powerup_speed': 't',
        'powerup_sticky_bombs': 't',
        'puck_color': 't',
        'quote_bubble': 't',
        'rampage_bgcolor': 't',
        'rampage_bgcolor2': 't',
        'rampage_level_color': 't',
        'rampage_preview': 't',
        'replay_icon': 't',
        'right_button': 't',
        'robot_color': 't',
        'robot_color_mask': 't',
        'robot_icon': 't',
        'robot_icon_color_mask': 't',
        'roundabout_level_color': 't',
        'roundabout_preview': 't',
        'santa_color': 't',
        'santa_color_mask': 't',
        'santa_icon': 't',
        'santa_icon_color_mask': 't',
        'settings_icon': 't',
        'slash': 't',
        'star': 't',
        'step_right_up_level_color': 't',
        'step_right_up_preview': 't',
        'store_character': 't',
        'store_character_easter': 't',
        'store_character_xmas': 't',
        'store_icon': 't',
        'superhero_color': 't',
        'superhero_color_mask': 't',
        'superhero_icon': 't',
        'superhero_icon_color_mask': 't',
        'the_pad_level_color': 't',
        'the_pad_preview': 't',
        'ticket_roll': 't',
        'ticket_roll_big': 't',
        'ticket_rolls': 't',
        'tickets': 't',
        'tickets_more': 't',
        'tickets_purple': 't',
        'tip_top_bgcolor': 't',
        'tip_top_level_color': 't',
        'tip_top_preview': 't',
        'tnt': 't',
        'tokens1': 't',
        'tokens2': 't',
        'tokens3': 't',
        'tokens4': 't',
        'tower_dlevel_color': 't',
        'tower_dpreview': 't',
        'trees_color': 't',
        'trophy': 't',
        'tv': 't',
        'up_button': 't',
        'vr_fill_mound': 't',
        'warrior_color': 't',
        'warrior_color_mask': 't',
        'warrior_icon': 't',
        'warrior_icon_color_mask': 't',
        'window_bottom_cap': 't',
        'witch_color': 't',
        'witch_color_mask': 't',
        'witch_icon': 't',
        'witch_icon_color_mask': 't',
        'wizard_color': 't',
        'wizard_color_mask': 't',
        'wizard_icon': 't',
        'wizard_icon_color_mask': 't',
        'wrestler_color': 't',
        'wrestler_color_mask': 't',
        'wrestler_icon': 't',
        'wrestler_icon_color_mask': 't',
        'zig_zag_level_color': 't',
        'zigzag_preview': 't',
        'zoe_color': 't',
        'zoe_color_mask': 't',
        'zoe_icon': 't',
        'zoe_icon_color_mask': 't',
    },
}


if not TYPE_CHECKING:
    audio = AssetGroup(__asset_package__, _TREE['audio'], 'audio')
    meshes = AssetGroup(__asset_package__, _TREE['meshes'], 'meshes')
    strings = LangStrDir(__asset_package__, _TREE['strings'], 'strings')
    textures = AssetGroup(__asset_package__, _TREE['textures'], 'textures')
