# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.baclassiccharacterassets.261009h``
(bascenev1).

Everything a classic character is made of: body textures and color masks, body
part meshes, voice sounds, icons and icon color masks, and display names -- a
whole character from one package, which is what a .bchar character definition
here needs. Bundled with the game; a newer version is fetched on demand when a
server-delivered character definition references it, and CAS dedupe means that
costs roughly the new character's own art.
"""

# ba_meta require api 9
# ba_meta require asset-package 546

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

from typing import TYPE_CHECKING

from bacommon.assetpackage import ApverNum

from bascenev1._assetref import AssetGroup, CharacterGroup

from babase import LangStrDir

# a-0.baclassiccharacterassets.261009h
_ASSET_PACKAGE = ApverNum(546)

if TYPE_CHECKING:
    from bascenev1._assetref import (
        CharacterHandle,
        MeshHandle,
        SoundHandle,
        TextureHandle,
    )
    from babase import LangStr

    class AudioGroup:
        """
        ::

            Character voice and body sounds.

            See source for the full asset list.
        """

        agent1: SoundHandle
        agent2: SoundHandle
        agent3: SoundHandle
        agent4: SoundHandle
        agent_death: SoundHandle
        agent_fall: SoundHandle
        agent_hit1: SoundHandle
        agent_hit2: SoundHandle
        alien1: SoundHandle
        alien2: SoundHandle
        alien3: SoundHandle
        alien4: SoundHandle
        alien_death: SoundHandle
        alien_fall: SoundHandle
        alien_hit1: SoundHandle
        alien_hit2: SoundHandle
        assassin1: SoundHandle
        assassin2: SoundHandle
        assassin3: SoundHandle
        assassin4: SoundHandle
        assassin_death: SoundHandle
        assassin_fall: SoundHandle
        assassin_hit1: SoundHandle
        assassin_hit2: SoundHandle
        bear1: SoundHandle
        bear2: SoundHandle
        bear3: SoundHandle
        bear4: SoundHandle
        bear_death: SoundHandle
        bear_fall: SoundHandle
        bear_hit1: SoundHandle
        bear_hit2: SoundHandle
        bones1: SoundHandle
        bones2: SoundHandle
        bones3: SoundHandle
        bones_death: SoundHandle
        bones_fall: SoundHandle
        bunny1: SoundHandle
        bunny2: SoundHandle
        bunny3: SoundHandle
        bunny4: SoundHandle
        bunny_death: SoundHandle
        bunny_fall: SoundHandle
        bunny_hit1: SoundHandle
        bunny_hit2: SoundHandle
        bunny_jump: SoundHandle
        cyborg1: SoundHandle
        cyborg2: SoundHandle
        cyborg3: SoundHandle
        cyborg4: SoundHandle
        cyborg_death: SoundHandle
        cyborg_fall: SoundHandle
        cyborg_hit1: SoundHandle
        cyborg_hit2: SoundHandle
        frosty01: SoundHandle
        frosty02: SoundHandle
        frosty03: SoundHandle
        frosty04: SoundHandle
        frosty05: SoundHandle
        frosty_death: SoundHandle
        frosty_fall: SoundHandle
        frosty_hit01: SoundHandle
        frosty_hit02: SoundHandle
        frosty_hit03: SoundHandle
        gladiator1: SoundHandle
        gladiator2: SoundHandle
        gladiator3: SoundHandle
        gladiator4: SoundHandle
        gladiator_death: SoundHandle
        gladiator_fall: SoundHandle
        gladiator_hit1: SoundHandle
        gladiator_hit2: SoundHandle
        jack01: SoundHandle
        jack02: SoundHandle
        jack03: SoundHandle
        jack04: SoundHandle
        jack05: SoundHandle
        jack06: SoundHandle
        jack_death01: SoundHandle
        jack_fall01: SoundHandle
        jack_hit01: SoundHandle
        jack_hit02: SoundHandle
        jack_hit03: SoundHandle
        jack_hit04: SoundHandle
        jack_hit05: SoundHandle
        jack_hit06: SoundHandle
        jack_hit07: SoundHandle
        kronk1: SoundHandle
        kronk10: SoundHandle
        kronk2: SoundHandle
        kronk3: SoundHandle
        kronk4: SoundHandle
        kronk5: SoundHandle
        kronk6: SoundHandle
        kronk7: SoundHandle
        kronk8: SoundHandle
        kronk9: SoundHandle
        kronk_death: SoundHandle
        kronk_fall: SoundHandle
        mel01: SoundHandle
        mel02: SoundHandle
        mel03: SoundHandle
        mel04: SoundHandle
        mel05: SoundHandle
        mel06: SoundHandle
        mel07: SoundHandle
        mel08: SoundHandle
        mel09: SoundHandle
        mel10: SoundHandle
        mel_death01: SoundHandle
        mel_fall01: SoundHandle
        ninja_attack1: SoundHandle
        ninja_attack2: SoundHandle
        ninja_attack3: SoundHandle
        ninja_attack4: SoundHandle
        ninja_attack5: SoundHandle
        ninja_attack6: SoundHandle
        ninja_attack7: SoundHandle
        ninja_death1: SoundHandle
        ninja_fall1: SoundHandle
        ninja_hit1: SoundHandle
        ninja_hit2: SoundHandle
        ninja_hit3: SoundHandle
        ninja_hit4: SoundHandle
        ninja_hit5: SoundHandle
        ninja_hit6: SoundHandle
        ninja_hit7: SoundHandle
        ninja_hit8: SoundHandle
        old_lady1: SoundHandle
        old_lady2: SoundHandle
        old_lady3: SoundHandle
        old_lady4: SoundHandle
        old_lady_death: SoundHandle
        old_lady_fall: SoundHandle
        old_lady_hit1: SoundHandle
        old_lady_hit2: SoundHandle
        penguin1: SoundHandle
        penguin2: SoundHandle
        penguin3: SoundHandle
        penguin4: SoundHandle
        penguin_death: SoundHandle
        penguin_fall: SoundHandle
        penguin_hit1: SoundHandle
        penguin_hit2: SoundHandle
        pixie1: SoundHandle
        pixie2: SoundHandle
        pixie3: SoundHandle
        pixie4: SoundHandle
        pixie_death: SoundHandle
        pixie_fall: SoundHandle
        pixie_hit1: SoundHandle
        pixie_hit2: SoundHandle
        robot1: SoundHandle
        robot2: SoundHandle
        robot3: SoundHandle
        robot4: SoundHandle
        robot_death: SoundHandle
        robot_fall: SoundHandle
        robot_hit1: SoundHandle
        robot_hit2: SoundHandle
        santa01: SoundHandle
        santa02: SoundHandle
        santa03: SoundHandle
        santa04: SoundHandle
        santa05: SoundHandle
        santa_death: SoundHandle
        santa_fall: SoundHandle
        santa_hit01: SoundHandle
        santa_hit02: SoundHandle
        santa_hit03: SoundHandle
        santa_hit04: SoundHandle
        spaz_attack01: SoundHandle
        spaz_attack02: SoundHandle
        spaz_attack03: SoundHandle
        spaz_attack04: SoundHandle
        spaz_death01: SoundHandle
        spaz_fall01: SoundHandle
        spaz_impact01: SoundHandle
        spaz_impact02: SoundHandle
        spaz_impact03: SoundHandle
        spaz_impact04: SoundHandle
        spaz_jump01: SoundHandle
        spaz_jump02: SoundHandle
        spaz_jump03: SoundHandle
        spaz_jump04: SoundHandle
        spaz_pickup01: SoundHandle
        warrior1: SoundHandle
        warrior2: SoundHandle
        warrior3: SoundHandle
        warrior4: SoundHandle
        warrior_death: SoundHandle
        warrior_fall: SoundHandle
        warrior_hit1: SoundHandle
        warrior_hit2: SoundHandle
        witch1: SoundHandle
        witch2: SoundHandle
        witch3: SoundHandle
        witch4: SoundHandle
        witch_death: SoundHandle
        witch_fall: SoundHandle
        witch_hit1: SoundHandle
        witch_hit2: SoundHandle
        wizard1: SoundHandle
        wizard2: SoundHandle
        wizard3: SoundHandle
        wizard4: SoundHandle
        wizard_death: SoundHandle
        wizard_fall: SoundHandle
        wizard_hit1: SoundHandle
        wizard_hit2: SoundHandle
        wrestler1: SoundHandle
        wrestler2: SoundHandle
        wrestler3: SoundHandle
        wrestler4: SoundHandle
        wrestler_death: SoundHandle
        wrestler_fall: SoundHandle
        wrestler_hit1: SoundHandle
        wrestler_hit2: SoundHandle
        zoe_attack01: SoundHandle
        zoe_attack02: SoundHandle
        zoe_attack03: SoundHandle
        zoe_attack04: SoundHandle
        zoe_death01: SoundHandle
        zoe_fall01: SoundHandle
        zoe_impact01: SoundHandle
        zoe_impact02: SoundHandle
        zoe_impact03: SoundHandle
        zoe_impact04: SoundHandle
        zoe_jump01: SoundHandle
        zoe_jump02: SoundHandle
        zoe_jump03: SoundHandle
        zoe_pickup01: SoundHandle

    class MeshesGroup:
        """
        ::

            Character body part meshes.

            See source for the full asset list.
        """

        agent_fore_arm: MeshHandle
        agent_hand: MeshHandle
        agent_head: MeshHandle
        agent_lower_leg: MeshHandle
        agent_pelvis: MeshHandle
        agent_toes: MeshHandle
        agent_torso: MeshHandle
        agent_upper_arm: MeshHandle
        agent_upper_leg: MeshHandle
        alien_fore_arm: MeshHandle
        alien_hand: MeshHandle
        alien_head: MeshHandle
        alien_lower_leg: MeshHandle
        alien_pelvis: MeshHandle
        alien_toes: MeshHandle
        alien_torso: MeshHandle
        alien_upper_arm: MeshHandle
        alien_upper_leg: MeshHandle
        assassin_fore_arm: MeshHandle
        assassin_hand: MeshHandle
        assassin_head: MeshHandle
        assassin_lower_leg: MeshHandle
        assassin_pelvis: MeshHandle
        assassin_toes: MeshHandle
        assassin_torso: MeshHandle
        assassin_upper_arm: MeshHandle
        assassin_upper_leg: MeshHandle
        bear_fore_arm: MeshHandle
        bear_hand: MeshHandle
        bear_head: MeshHandle
        bear_lower_leg: MeshHandle
        bear_pelvis: MeshHandle
        bear_toes: MeshHandle
        bear_torso: MeshHandle
        bear_upper_arm: MeshHandle
        bear_upper_leg: MeshHandle
        bones_fore_arm: MeshHandle
        bones_hand: MeshHandle
        bones_head: MeshHandle
        bones_lower_leg: MeshHandle
        bones_pelvis: MeshHandle
        bones_toes: MeshHandle
        bones_torso: MeshHandle
        bones_upper_arm: MeshHandle
        bones_upper_leg: MeshHandle
        bunny_fore_arm: MeshHandle
        bunny_hand: MeshHandle
        bunny_head: MeshHandle
        bunny_lower_leg: MeshHandle
        bunny_pelvis: MeshHandle
        bunny_toes: MeshHandle
        bunny_torso: MeshHandle
        bunny_upper_arm: MeshHandle
        bunny_upper_leg: MeshHandle
        cyborg_fore_arm: MeshHandle
        cyborg_hand: MeshHandle
        cyborg_head: MeshHandle
        cyborg_lower_leg: MeshHandle
        cyborg_pelvis: MeshHandle
        cyborg_toes: MeshHandle
        cyborg_torso: MeshHandle
        cyborg_upper_arm: MeshHandle
        cyborg_upper_leg: MeshHandle
        frosty_fore_arm: MeshHandle
        frosty_hand: MeshHandle
        frosty_head: MeshHandle
        frosty_lower_leg: MeshHandle
        frosty_pelvis: MeshHandle
        frosty_toes: MeshHandle
        frosty_torso: MeshHandle
        frosty_upper_arm: MeshHandle
        frosty_upper_leg: MeshHandle
        gladiator_fore_arm: MeshHandle
        gladiator_hand: MeshHandle
        gladiator_head: MeshHandle
        gladiator_lower_leg: MeshHandle
        gladiator_pelvis: MeshHandle
        gladiator_toes: MeshHandle
        gladiator_torso: MeshHandle
        gladiator_upper_arm: MeshHandle
        gladiator_upper_leg: MeshHandle
        hair_tuft1: MeshHandle
        hair_tuft1b: MeshHandle
        hair_tuft2: MeshHandle
        hair_tuft3: MeshHandle
        hair_tuft4: MeshHandle
        jack_fore_arm: MeshHandle
        jack_hand: MeshHandle
        jack_head: MeshHandle
        jack_lower_leg: MeshHandle
        jack_toes: MeshHandle
        jack_torso: MeshHandle
        jack_upper_arm: MeshHandle
        jack_upper_leg: MeshHandle
        kronk_fore_arm: MeshHandle
        kronk_hand: MeshHandle
        kronk_head: MeshHandle
        kronk_lower_leg: MeshHandle
        kronk_pelvis: MeshHandle
        kronk_toes: MeshHandle
        kronk_torso: MeshHandle
        kronk_upper_arm: MeshHandle
        kronk_upper_leg: MeshHandle
        mel_fore_arm: MeshHandle
        mel_hand: MeshHandle
        mel_head: MeshHandle
        mel_lower_leg: MeshHandle
        mel_toes: MeshHandle
        mel_torso: MeshHandle
        mel_upper_arm: MeshHandle
        mel_upper_leg: MeshHandle
        neo_spaz_fore_arm: MeshHandle
        neo_spaz_hand: MeshHandle
        neo_spaz_head: MeshHandle
        neo_spaz_lower_leg: MeshHandle
        neo_spaz_pelvis: MeshHandle
        neo_spaz_toes: MeshHandle
        neo_spaz_torso: MeshHandle
        neo_spaz_upper_arm: MeshHandle
        neo_spaz_upper_leg: MeshHandle
        ninja_fore_arm: MeshHandle
        ninja_hand: MeshHandle
        ninja_head: MeshHandle
        ninja_lower_leg: MeshHandle
        ninja_pelvis: MeshHandle
        ninja_toes: MeshHandle
        ninja_torso: MeshHandle
        ninja_upper_arm: MeshHandle
        ninja_upper_leg: MeshHandle
        old_lady_fore_arm: MeshHandle
        old_lady_hand: MeshHandle
        old_lady_head: MeshHandle
        old_lady_lower_leg: MeshHandle
        old_lady_pelvis: MeshHandle
        old_lady_toes: MeshHandle
        old_lady_torso: MeshHandle
        old_lady_upper_arm: MeshHandle
        old_lady_upper_leg: MeshHandle
        penguin_fore_arm: MeshHandle
        penguin_hand: MeshHandle
        penguin_head: MeshHandle
        penguin_lower_leg: MeshHandle
        penguin_pelvis: MeshHandle
        penguin_toes: MeshHandle
        penguin_torso: MeshHandle
        penguin_upper_arm: MeshHandle
        penguin_upper_leg: MeshHandle
        pixie_fore_arm: MeshHandle
        pixie_hand: MeshHandle
        pixie_head: MeshHandle
        pixie_lower_leg: MeshHandle
        pixie_pelvis: MeshHandle
        pixie_toes: MeshHandle
        pixie_torso: MeshHandle
        pixie_upper_arm: MeshHandle
        pixie_upper_leg: MeshHandle
        pixie_wing: MeshHandle
        robot_fore_arm: MeshHandle
        robot_hand: MeshHandle
        robot_head: MeshHandle
        robot_lower_leg: MeshHandle
        robot_pelvis: MeshHandle
        robot_toes: MeshHandle
        robot_torso: MeshHandle
        robot_upper_arm: MeshHandle
        robot_upper_leg: MeshHandle
        santa_fore_arm: MeshHandle
        santa_hand: MeshHandle
        santa_head: MeshHandle
        santa_lower_leg: MeshHandle
        santa_toes: MeshHandle
        santa_torso: MeshHandle
        santa_upper_arm: MeshHandle
        santa_upper_leg: MeshHandle
        warrior_fore_arm: MeshHandle
        warrior_hand: MeshHandle
        warrior_head: MeshHandle
        warrior_lower_leg: MeshHandle
        warrior_pelvis: MeshHandle
        warrior_toes: MeshHandle
        warrior_torso: MeshHandle
        warrior_upper_arm: MeshHandle
        warrior_upper_leg: MeshHandle
        witch_fore_arm: MeshHandle
        witch_hand: MeshHandle
        witch_head: MeshHandle
        witch_lower_leg: MeshHandle
        witch_pelvis: MeshHandle
        witch_toes: MeshHandle
        witch_torso: MeshHandle
        witch_upper_arm: MeshHandle
        witch_upper_leg: MeshHandle
        wizard_fore_arm: MeshHandle
        wizard_hand: MeshHandle
        wizard_head: MeshHandle
        wizard_lower_leg: MeshHandle
        wizard_pelvis: MeshHandle
        wizard_toes: MeshHandle
        wizard_torso: MeshHandle
        wizard_upper_arm: MeshHandle
        wizard_upper_leg: MeshHandle
        wrestler_fore_arm: MeshHandle
        wrestler_hand: MeshHandle
        wrestler_head: MeshHandle
        wrestler_lower_leg: MeshHandle
        wrestler_pelvis: MeshHandle
        wrestler_toes: MeshHandle
        wrestler_torso: MeshHandle
        wrestler_upper_arm: MeshHandle
        wrestler_upper_leg: MeshHandle
        zoe_fore_arm: MeshHandle
        zoe_hand: MeshHandle
        zoe_head: MeshHandle
        zoe_lower_leg: MeshHandle
        zoe_pelvis: MeshHandle
        zoe_toes: MeshHandle
        zoe_torso: MeshHandle
        zoe_upper_arm: MeshHandle
        zoe_upper_leg: MeshHandle

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
        #:     picker, and gameplay UIs. Invented proper name: keep verbatim in
        #:     Latin-script locales; transliterate phonetically in non-Latin
        #:     scripts. Established legacy renames in some locales are
        #:     intentional and were seeded.
        #:
        #:     English: "Zoe"
        zoe: LangStr

    class StringsGroup:
        """
        ::

            Character display names.

            See source for the full asset list.
        """

        characters: StringsCharactersGroup

    class TexturesGroup:
        """
        ::

            Character body textures and their color masks, and each character's
            icon and icon color mask.

            See source for the full asset list.
        """

        agent_color: TextureHandle
        agent_color_mask: TextureHandle
        agent_icon: TextureHandle
        agent_icon_color_mask: TextureHandle
        alien_color: TextureHandle
        alien_color_mask: TextureHandle
        alien_icon: TextureHandle
        alien_icon_color_mask: TextureHandle
        assassin_color: TextureHandle
        assassin_color_mask: TextureHandle
        assassin_icon: TextureHandle
        assassin_icon_color_mask: TextureHandle
        bear_color: TextureHandle
        bear_color_mask: TextureHandle
        bear_icon: TextureHandle
        bear_icon_color_mask: TextureHandle
        bones_color: TextureHandle
        bones_color_mask: TextureHandle
        bones_icon: TextureHandle
        bones_icon_color_mask: TextureHandle
        bunny_color: TextureHandle
        bunny_color_mask: TextureHandle
        bunny_icon: TextureHandle
        bunny_icon_color_mask: TextureHandle
        cyborg_color: TextureHandle
        cyborg_color_mask: TextureHandle
        cyborg_icon: TextureHandle
        cyborg_icon_color_mask: TextureHandle
        frosty_color: TextureHandle
        frosty_color_mask: TextureHandle
        frosty_icon: TextureHandle
        frosty_icon_color_mask: TextureHandle
        gladiator_color: TextureHandle
        gladiator_color_mask: TextureHandle
        gladiator_icon: TextureHandle
        gladiator_icon_color_mask: TextureHandle
        jack_color: TextureHandle
        jack_color_mask: TextureHandle
        jack_icon: TextureHandle
        jack_icon_color_mask: TextureHandle
        kronk: TextureHandle
        kronk_color_mask: TextureHandle
        kronk_icon: TextureHandle
        kronk_icon_color_mask: TextureHandle
        mel_color: TextureHandle
        mel_color_mask: TextureHandle
        mel_icon: TextureHandle
        mel_icon_color_mask: TextureHandle
        neo_spaz_color: TextureHandle
        neo_spaz_color_mask: TextureHandle
        neo_spaz_icon: TextureHandle
        neo_spaz_icon_color_mask: TextureHandle
        ninja_color: TextureHandle
        ninja_color_mask: TextureHandle
        ninja_icon: TextureHandle
        ninja_icon_color_mask: TextureHandle
        old_lady_color: TextureHandle
        old_lady_color_mask: TextureHandle
        old_lady_icon: TextureHandle
        old_lady_icon_color_mask: TextureHandle
        penguin_color: TextureHandle
        penguin_color_mask: TextureHandle
        penguin_icon: TextureHandle
        penguin_icon_color_mask: TextureHandle
        pixie_color: TextureHandle
        pixie_color_mask: TextureHandle
        pixie_icon: TextureHandle
        pixie_icon_color_mask: TextureHandle
        pixie_wings: TextureHandle
        pixie_wings_color_mask: TextureHandle
        robot_color: TextureHandle
        robot_color_mask: TextureHandle
        robot_icon: TextureHandle
        robot_icon_color_mask: TextureHandle
        santa_color: TextureHandle
        santa_color_mask: TextureHandle
        santa_icon: TextureHandle
        santa_icon_color_mask: TextureHandle
        warrior_color: TextureHandle
        warrior_color_mask: TextureHandle
        warrior_icon: TextureHandle
        warrior_icon_color_mask: TextureHandle
        witch_color: TextureHandle
        witch_color_mask: TextureHandle
        witch_icon: TextureHandle
        witch_icon_color_mask: TextureHandle
        wizard_color: TextureHandle
        wizard_color_mask: TextureHandle
        wizard_icon: TextureHandle
        wizard_icon_color_mask: TextureHandle
        wrestler_color: TextureHandle
        wrestler_color_mask: TextureHandle
        wrestler_icon: TextureHandle
        wrestler_icon_color_mask: TextureHandle
        zoe_color: TextureHandle
        zoe_color_mask: TextureHandle
        zoe_icon: TextureHandle
        zoe_icon_color_mask: TextureHandle

    class CharactersGroup:
        """Character-group type; see source for the full list."""

        agent_johnson: CharacterHandle
        b9000: CharacterHandle
        bernard: CharacterHandle
        betty: CharacterHandle
        bones: CharacterHandle
        easter_bunny: CharacterHandle
        frosty: CharacterHandle
        grumbledorf: CharacterHandle
        jack_morgan: CharacterHandle
        kronk: CharacterHandle
        lucky: CharacterHandle
        mel: CharacterHandle
        pascal: CharacterHandle
        pixel: CharacterHandle
        santa_claus: CharacterHandle
        snake_shadow: CharacterHandle
        spaz: CharacterHandle
        zoe: CharacterHandle

    #: The ``audio`` group - 232 assets (``agent1``, ``agent2``, ``agent3``,
    #: ``agent4``, ``agent_death``, and 227 more). Full list in source.
    audio: AudioGroup

    #: The ``meshes`` group - 219 assets (``agent_fore_arm``, ``agent_hand``,
    #: ``agent_head``, ``agent_lower_leg``, ``agent_pelvis``, and 214 more).
    #: Full list in source.
    meshes: MeshesGroup

    #: The ``strings`` group - 18 strings (``characters``, and 17 more). Full
    #: list in source.
    strings: StringsGroup

    #: The ``textures`` group - 98 assets (``agent_color``,
    #: ``agent_color_mask``, ``agent_icon``, ``agent_icon_color_mask``,
    #: ``alien_color``, and 93 more). Full list in source.
    textures: TexturesGroup

    #: The ``characters`` group - 18 characters (``agent_johnson``, ``b9000``,
    #: ``bernard``, ``betty``, ``bones``, and 13 more). Full list in source.
    characters: CharactersGroup

_TREE = {
    'audio': {
        'agent1': 's',
        'agent2': 's',
        'agent3': 's',
        'agent4': 's',
        'agent_death': 's',
        'agent_fall': 's',
        'agent_hit1': 's',
        'agent_hit2': 's',
        'alien1': 's',
        'alien2': 's',
        'alien3': 's',
        'alien4': 's',
        'alien_death': 's',
        'alien_fall': 's',
        'alien_hit1': 's',
        'alien_hit2': 's',
        'assassin1': 's',
        'assassin2': 's',
        'assassin3': 's',
        'assassin4': 's',
        'assassin_death': 's',
        'assassin_fall': 's',
        'assassin_hit1': 's',
        'assassin_hit2': 's',
        'bear1': 's',
        'bear2': 's',
        'bear3': 's',
        'bear4': 's',
        'bear_death': 's',
        'bear_fall': 's',
        'bear_hit1': 's',
        'bear_hit2': 's',
        'bones1': 's',
        'bones2': 's',
        'bones3': 's',
        'bones_death': 's',
        'bones_fall': 's',
        'bunny1': 's',
        'bunny2': 's',
        'bunny3': 's',
        'bunny4': 's',
        'bunny_death': 's',
        'bunny_fall': 's',
        'bunny_hit1': 's',
        'bunny_hit2': 's',
        'bunny_jump': 's',
        'cyborg1': 's',
        'cyborg2': 's',
        'cyborg3': 's',
        'cyborg4': 's',
        'cyborg_death': 's',
        'cyborg_fall': 's',
        'cyborg_hit1': 's',
        'cyborg_hit2': 's',
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
        'gladiator1': 's',
        'gladiator2': 's',
        'gladiator3': 's',
        'gladiator4': 's',
        'gladiator_death': 's',
        'gladiator_fall': 's',
        'gladiator_hit1': 's',
        'gladiator_hit2': 's',
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
        'robot1': 's',
        'robot2': 's',
        'robot3': 's',
        'robot4': 's',
        'robot_death': 's',
        'robot_fall': 's',
        'robot_hit1': 's',
        'robot_hit2': 's',
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
        'spaz_attack01': 's',
        'spaz_attack02': 's',
        'spaz_attack03': 's',
        'spaz_attack04': 's',
        'spaz_death01': 's',
        'spaz_fall01': 's',
        'spaz_impact01': 's',
        'spaz_impact02': 's',
        'spaz_impact03': 's',
        'spaz_impact04': 's',
        'spaz_jump01': 's',
        'spaz_jump02': 's',
        'spaz_jump03': 's',
        'spaz_jump04': 's',
        'spaz_pickup01': 's',
        'warrior1': 's',
        'warrior2': 's',
        'warrior3': 's',
        'warrior4': 's',
        'warrior_death': 's',
        'warrior_fall': 's',
        'warrior_hit1': 's',
        'warrior_hit2': 's',
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
        'wrestler1': 's',
        'wrestler2': 's',
        'wrestler3': 's',
        'wrestler4': 's',
        'wrestler_death': 's',
        'wrestler_fall': 's',
        'wrestler_hit1': 's',
        'wrestler_hit2': 's',
        'zoe_attack01': 's',
        'zoe_attack02': 's',
        'zoe_attack03': 's',
        'zoe_attack04': 's',
        'zoe_death01': 's',
        'zoe_fall01': 's',
        'zoe_impact01': 's',
        'zoe_impact02': 's',
        'zoe_impact03': 's',
        'zoe_impact04': 's',
        'zoe_jump01': 's',
        'zoe_jump02': 's',
        'zoe_jump03': 's',
        'zoe_pickup01': 's',
    },
    'meshes': {
        'agent_fore_arm': 'm',
        'agent_hand': 'm',
        'agent_head': 'm',
        'agent_lower_leg': 'm',
        'agent_pelvis': 'm',
        'agent_toes': 'm',
        'agent_torso': 'm',
        'agent_upper_arm': 'm',
        'agent_upper_leg': 'm',
        'alien_fore_arm': 'm',
        'alien_hand': 'm',
        'alien_head': 'm',
        'alien_lower_leg': 'm',
        'alien_pelvis': 'm',
        'alien_toes': 'm',
        'alien_torso': 'm',
        'alien_upper_arm': 'm',
        'alien_upper_leg': 'm',
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
        'bones_fore_arm': 'm',
        'bones_hand': 'm',
        'bones_head': 'm',
        'bones_lower_leg': 'm',
        'bones_pelvis': 'm',
        'bones_toes': 'm',
        'bones_torso': 'm',
        'bones_upper_arm': 'm',
        'bones_upper_leg': 'm',
        'bunny_fore_arm': 'm',
        'bunny_hand': 'm',
        'bunny_head': 'm',
        'bunny_lower_leg': 'm',
        'bunny_pelvis': 'm',
        'bunny_toes': 'm',
        'bunny_torso': 'm',
        'bunny_upper_arm': 'm',
        'bunny_upper_leg': 'm',
        'cyborg_fore_arm': 'm',
        'cyborg_hand': 'm',
        'cyborg_head': 'm',
        'cyborg_lower_leg': 'm',
        'cyborg_pelvis': 'm',
        'cyborg_toes': 'm',
        'cyborg_torso': 'm',
        'cyborg_upper_arm': 'm',
        'cyborg_upper_leg': 'm',
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
        'hair_tuft1': 'm',
        'hair_tuft1b': 'm',
        'hair_tuft2': 'm',
        'hair_tuft3': 'm',
        'hair_tuft4': 'm',
        'jack_fore_arm': 'm',
        'jack_hand': 'm',
        'jack_head': 'm',
        'jack_lower_leg': 'm',
        'jack_toes': 'm',
        'jack_torso': 'm',
        'jack_upper_arm': 'm',
        'jack_upper_leg': 'm',
        'kronk_fore_arm': 'm',
        'kronk_hand': 'm',
        'kronk_head': 'm',
        'kronk_lower_leg': 'm',
        'kronk_pelvis': 'm',
        'kronk_toes': 'm',
        'kronk_torso': 'm',
        'kronk_upper_arm': 'm',
        'kronk_upper_leg': 'm',
        'mel_fore_arm': 'm',
        'mel_hand': 'm',
        'mel_head': 'm',
        'mel_lower_leg': 'm',
        'mel_toes': 'm',
        'mel_torso': 'm',
        'mel_upper_arm': 'm',
        'mel_upper_leg': 'm',
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
        'pixie_wing': 'm',
        'robot_fore_arm': 'm',
        'robot_hand': 'm',
        'robot_head': 'm',
        'robot_lower_leg': 'm',
        'robot_pelvis': 'm',
        'robot_toes': 'm',
        'robot_torso': 'm',
        'robot_upper_arm': 'm',
        'robot_upper_leg': 'm',
        'santa_fore_arm': 'm',
        'santa_hand': 'm',
        'santa_head': 'm',
        'santa_lower_leg': 'm',
        'santa_toes': 'm',
        'santa_torso': 'm',
        'santa_upper_arm': 'm',
        'santa_upper_leg': 'm',
        'warrior_fore_arm': 'm',
        'warrior_hand': 'm',
        'warrior_head': 'm',
        'warrior_lower_leg': 'm',
        'warrior_pelvis': 'm',
        'warrior_toes': 'm',
        'warrior_torso': 'm',
        'warrior_upper_arm': 'm',
        'warrior_upper_leg': 'm',
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
        'characters': {
            'agent_johnson': (),
            'b9000': (),
            'bernard': (),
            'betty': (),
            'bones': (),
            'easter_bunny': (),
            'frosty': (),
            'grumbledorf': (),
            'jack_morgan': (),
            'kronk': (),
            'lucky': (),
            'mel': (),
            'pascal': (),
            'pixel': (),
            'santa_claus': (),
            'snake_shadow': (),
            'spaz': (),
            'zoe': (),
        }
    },
    'textures': {
        'agent_color': 't',
        'agent_color_mask': 't',
        'agent_icon': 't',
        'agent_icon_color_mask': 't',
        'alien_color': 't',
        'alien_color_mask': 't',
        'alien_icon': 't',
        'alien_icon_color_mask': 't',
        'assassin_color': 't',
        'assassin_color_mask': 't',
        'assassin_icon': 't',
        'assassin_icon_color_mask': 't',
        'bear_color': 't',
        'bear_color_mask': 't',
        'bear_icon': 't',
        'bear_icon_color_mask': 't',
        'bones_color': 't',
        'bones_color_mask': 't',
        'bones_icon': 't',
        'bones_icon_color_mask': 't',
        'bunny_color': 't',
        'bunny_color_mask': 't',
        'bunny_icon': 't',
        'bunny_icon_color_mask': 't',
        'cyborg_color': 't',
        'cyborg_color_mask': 't',
        'cyborg_icon': 't',
        'cyborg_icon_color_mask': 't',
        'frosty_color': 't',
        'frosty_color_mask': 't',
        'frosty_icon': 't',
        'frosty_icon_color_mask': 't',
        'gladiator_color': 't',
        'gladiator_color_mask': 't',
        'gladiator_icon': 't',
        'gladiator_icon_color_mask': 't',
        'jack_color': 't',
        'jack_color_mask': 't',
        'jack_icon': 't',
        'jack_icon_color_mask': 't',
        'kronk': 't',
        'kronk_color_mask': 't',
        'kronk_icon': 't',
        'kronk_icon_color_mask': 't',
        'mel_color': 't',
        'mel_color_mask': 't',
        'mel_icon': 't',
        'mel_icon_color_mask': 't',
        'neo_spaz_color': 't',
        'neo_spaz_color_mask': 't',
        'neo_spaz_icon': 't',
        'neo_spaz_icon_color_mask': 't',
        'ninja_color': 't',
        'ninja_color_mask': 't',
        'ninja_icon': 't',
        'ninja_icon_color_mask': 't',
        'old_lady_color': 't',
        'old_lady_color_mask': 't',
        'old_lady_icon': 't',
        'old_lady_icon_color_mask': 't',
        'penguin_color': 't',
        'penguin_color_mask': 't',
        'penguin_icon': 't',
        'penguin_icon_color_mask': 't',
        'pixie_color': 't',
        'pixie_color_mask': 't',
        'pixie_icon': 't',
        'pixie_icon_color_mask': 't',
        'pixie_wings': 't',
        'pixie_wings_color_mask': 't',
        'robot_color': 't',
        'robot_color_mask': 't',
        'robot_icon': 't',
        'robot_icon_color_mask': 't',
        'santa_color': 't',
        'santa_color_mask': 't',
        'santa_icon': 't',
        'santa_icon_color_mask': 't',
        'warrior_color': 't',
        'warrior_color_mask': 't',
        'warrior_icon': 't',
        'warrior_icon_color_mask': 't',
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
        'zoe_color': 't',
        'zoe_color_mask': 't',
        'zoe_icon': 't',
        'zoe_icon_color_mask': 't',
    },
}

_CHARACTERS = {
    'characters': {
        'agent_johnson': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/agent_color"},'
                '"cm":{"a":546,"n":"textures/agent_color_mask"},'
                '"mh":{"a":546,"n":"meshes/agent_head"},'
                '"mt":{"a":546,"n":"meshes/agent_torso"},'
                '"mua":{"a":546,"n":"meshes/agent_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/agent_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/agent_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/agent_toes"},'
                '"mfa":{"a":546,"n":"meshes/agent_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/agent_hand"},'
                '"mp":{"a":546,"n":"meshes/agent_pelvis"},'
                '"sj":[{"a":546,"n":"audio/agent1"},{"a":546,'
                '"n":"audio/agent2"},{"a":546,"n":"audio/agent3"},'
                '{"a":546,"n":"audio/agent4"}],"sa":[{"a":546,'
                '"n":"audio/agent1"},{"a":546,"n":"audio/agent2"},'
                '{"a":546,"n":"audio/agent3"},{"a":546,'
                '"n":"audio/agent4"}],"si":[{"a":546,'
                '"n":"audio/agent_hit1"},{"a":546,'
                '"n":"audio/agent_hit2"}],"sd":[{"a":546,'
                '"n":"audio/agent_death"}],"sp":[{"a":546,'
                '"n":"audio/agent1"},{"a":546,"n":"audio/agent2"},'
                '{"a":546,"n":"audio/agent3"},{"a":546,'
                '"n":"audio/agent4"}],"sf":[{"a":546,'
                '"n":"audio/agent_fall"}],"cl":[0.3,0.3,0.33],"hl":[1.0,0.5,'
                '0.3],"le":"n","re":"n","rs":0.2}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/agent_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/agent_icon_color_mask\\"},\\"cl\\":[0.3,'
                '0.3,0.33],\\"hl\\":[1.0,0.5,0.3]}}","_t":"ci"}'
            ),
            'strings/characters/agent_johnson',
        ),
        'b9000': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/cyborg_color"},'
                '"cm":{"a":546,"n":"textures/cyborg_color_mask"},'
                '"mh":{"a":546,"n":"meshes/cyborg_head"},'
                '"mt":{"a":546,"n":"meshes/cyborg_torso"},'
                '"mua":{"a":546,"n":"meshes/cyborg_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/cyborg_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/cyborg_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/cyborg_toes"},'
                '"mfa":{"a":546,"n":"meshes/cyborg_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/cyborg_hand"},'
                '"mp":{"a":546,"n":"meshes/cyborg_pelvis"},'
                '"sj":[{"a":546,"n":"audio/cyborg1"},{"a":546,'
                '"n":"audio/cyborg2"},{"a":546,"n":"audio/cyborg3"},'
                '{"a":546,"n":"audio/cyborg4"}],"sa":[{"a":546,'
                '"n":"audio/cyborg1"},{"a":546,"n":"audio/cyborg2"},'
                '{"a":546,"n":"audio/cyborg3"},{"a":546,'
                '"n":"audio/cyborg4"}],"si":[{"a":546,'
                '"n":"audio/cyborg_hit1"},{"a":546,'
                '"n":"audio/cyborg_hit2"}],"sd":[{"a":546,'
                '"n":"audio/cyborg_death"}],"sp":[{"a":546,'
                '"n":"audio/cyborg1"},{"a":546,"n":"audio/cyborg2"},'
                '{"a":546,"n":"audio/cyborg3"},{"a":546,'
                '"n":"audio/cyborg4"}],"sf":[{"a":546,'
                '"n":"audio/cyborg_fall"}],"cl":[0.5,0.5,0.5],"hl":[1.0,0.0,'
                '0.0],"le":"n","re":"n","rs":0.85}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/cyborg_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/cyborg_icon_color_mask\\"},'
                '\\"hl\\":[1.0,0.0,0.0]}}","_t":"ci"}'
            ),
            'strings/characters/b9000',
        ),
        'bernard': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/bear_color"},'
                '"cm":{"a":546,"n":"textures/bear_color_mask"},'
                '"mh":{"a":546,"n":"meshes/bear_head"},'
                '"mt":{"a":546,"n":"meshes/bear_torso"},'
                '"mua":{"a":546,"n":"meshes/bear_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/bear_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/bear_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/bear_toes"},'
                '"mfa":{"a":546,"n":"meshes/bear_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/bear_hand"},'
                '"mp":{"a":546,"n":"meshes/bear_pelvis"},'
                '"sj":[{"a":546,"n":"audio/bear1"},{"a":546,'
                '"n":"audio/bear2"},{"a":546,"n":"audio/bear3"},'
                '{"a":546,"n":"audio/bear4"}],"sa":[{"a":546,'
                '"n":"audio/bear1"},{"a":546,"n":"audio/bear2"},'
                '{"a":546,"n":"audio/bear3"},{"a":546,'
                '"n":"audio/bear4"}],"si":[{"a":546,'
                '"n":"audio/bear_hit1"},{"a":546,'
                '"n":"audio/bear_hit2"}],"sd":[{"a":546,'
                '"n":"audio/bear_death"}],"sp":[{"a":546,'
                '"n":"audio/bear1"},{"a":546,"n":"audio/bear2"},'
                '{"a":546,"n":"audio/bear3"},{"a":546,'
                '"n":"audio/bear4"}],"sf":[{"a":546,'
                '"n":"audio/bear_fall"}],"cl":[0.7,0.5,0.0],"tr":0.25,'
                '"so":[-0.02,-0.01,0.01],"le":"l","re":"l","es":0.73,'
                '"eo":[0.065,0.064,0.205],"ec":[0.0,0.0,0.0],"eb":[0.5,0.5,'
                '0.5],"lc":[0.2,0.1,0.1],"rs":0.05}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/bear_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/bear_icon_color_mask\\"},\\"cl\\":[0.7,'
                '0.5,0.0]}}","_t":"ci"}'
            ),
            'strings/characters/bernard',
        ),
        'betty': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/old_lady_color"},'
                '"cm":{"a":546,"n":"textures/old_lady_color_mask"},'
                '"mh":{"a":546,"n":"meshes/old_lady_head"},'
                '"mt":{"a":546,"n":"meshes/old_lady_torso"},'
                '"mua":{"a":546,"n":"meshes/old_lady_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/old_lady_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/old_lady_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/old_lady_toes"},'
                '"mfa":{"a":546,"n":"meshes/old_lady_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/old_lady_hand"},'
                '"sj":[{"a":546,"n":"audio/old_lady1"},{"a":546,'
                '"n":"audio/old_lady2"},{"a":546,"n":"audio/old_lady3"},'
                '{"a":546,"n":"audio/old_lady4"}],"sa":[{"a":546,'
                '"n":"audio/old_lady1"},{"a":546,"n":"audio/old_lady2"},'
                '{"a":546,"n":"audio/old_lady3"},{"a":546,'
                '"n":"audio/old_lady4"}],"si":[{"a":546,'
                '"n":"audio/old_lady_hit1"},{"a":546,'
                '"n":"audio/old_lady_hit2"}],"sd":[{"a":546,'
                '"n":"audio/old_lady_death"}],"sp":[{"a":546,'
                '"n":"audio/old_lady1"},{"a":546,"n":"audio/old_lady2"},'
                '{"a":546,"n":"audio/old_lady3"},{"a":546,'
                '"n":"audio/old_lady4"}],"sf":[{"a":546,'
                '"n":"audio/old_lady_fall"}],"cl":[0.2,1.0,1.0],"hl":[0.5,'
                '0.25,1.0],"le":"n","re":"n"}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/old_lady_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/old_lady_icon_color_mask\\"},'
                '\\"cl\\":[0.2,1.0,1.0],\\"hl\\":[0.5,0.25,1.0]}}","_t":"ci"}'
            ),
            'strings/characters/betty',
        ),
        'bones': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/bones_color"},'
                '"cm":{"a":546,"n":"textures/bones_color_mask"},'
                '"mh":{"a":546,"n":"meshes/bones_head"},'
                '"mt":{"a":546,"n":"meshes/bones_torso"},'
                '"mua":{"a":546,"n":"meshes/bones_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/bones_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/bones_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/bones_toes"},'
                '"mfa":{"a":546,"n":"meshes/bones_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/bones_hand"},'
                '"mp":{"a":546,"n":"meshes/bones_pelvis"},'
                '"sj":[{"a":546,"n":"audio/bones1"},{"a":546,'
                '"n":"audio/bones2"},{"a":546,"n":"audio/bones3"}],'
                '"sa":[{"a":546,"n":"audio/bones1"},{"a":546,'
                '"n":"audio/bones2"},{"a":546,"n":"audio/bones3"}],'
                '"si":[{"a":546,"n":"audio/bones1"},{"a":546,'
                '"n":"audio/bones2"},{"a":546,"n":"audio/bones3"}],'
                '"sd":[{"a":546,"n":"audio/bones_death"}],'
                '"sp":[{"a":546,"n":"audio/bones1"},{"a":546,'
                '"n":"audio/bones2"},{"a":546,"n":"audio/bones3"}],'
                '"sf":[{"a":546,"n":"audio/bones_fall"}],"cl":[0.6,0.9,'
                '1.0],"hl":[0.6,0.9,1.0],"le":"n","re":"n"}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/bones_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/bones_icon_color_mask\\"},\\"cl\\":[0.6,'
                '0.9,1.0],\\"hl\\":[0.6,0.9,1.0]}}","_t":"ci"}'
            ),
            'strings/characters/bones',
        ),
        'easter_bunny': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/bunny_color"},'
                '"cm":{"a":546,"n":"textures/bunny_color_mask"},'
                '"mh":{"a":546,"n":"meshes/bunny_head"},'
                '"mt":{"a":546,"n":"meshes/bunny_torso"},'
                '"mua":{"a":546,"n":"meshes/bunny_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/bunny_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/bunny_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/bunny_toes"},'
                '"mfa":{"a":546,"n":"meshes/bunny_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/bunny_hand"},'
                '"sj":[{"a":546,"n":"audio/bunny_jump"}],'
                '"sa":[{"a":546,"n":"audio/bunny1"},{"a":546,'
                '"n":"audio/bunny2"},{"a":546,"n":"audio/bunny3"},'
                '{"a":546,"n":"audio/bunny4"}],"si":[{"a":546,'
                '"n":"audio/bunny_hit1"},{"a":546,'
                '"n":"audio/bunny_hit2"}],"sd":[{"a":546,'
                '"n":"audio/bunny_death"}],"sp":[{"a":546,'
                '"n":"audio/bunny1"},{"a":546,"n":"audio/bunny2"},'
                '{"a":546,"n":"audio/bunny3"},{"a":546,'
                '"n":"audio/bunny4"}],"sf":[{"a":546,'
                '"n":"audio/bunny_fall"}],"cl":[1.0,1.0,1.0],"hl":[1.0,0.5,'
                '0.5],"tr":0.13,"so":[0.03,-0.05,0.0],"es":1.2,"eo":[0.07,'
                '-0.08,0.05],"eb":[0.6,0.6,0.6],"lc":[0.6,0.5,0.5],"ln":-5.0,'
                '"rs":0.02}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/bunny_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/bunny_icon_color_mask\\"},\\"cl\\":[1.0,'
                '1.0,1.0],\\"hl\\":[1.0,0.5,0.5]}}","_t":"ci"}'
            ),
            'strings/characters/easter_bunny',
        ),
        'frosty': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/frosty_color"},'
                '"cm":{"a":546,"n":"textures/frosty_color_mask"},'
                '"mh":{"a":546,"n":"meshes/frosty_head"},'
                '"mt":{"a":546,"n":"meshes/frosty_torso"},'
                '"mua":{"a":546,"n":"meshes/frosty_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/frosty_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/frosty_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/frosty_toes"},'
                '"mfa":{"a":546,"n":"meshes/frosty_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/frosty_hand"},'
                '"mp":{"a":546,"n":"meshes/frosty_pelvis"},'
                '"sj":[{"a":546,"n":"audio/frosty01"},{"a":546,'
                '"n":"audio/frosty02"},{"a":546,"n":"audio/frosty03"},'
                '{"a":546,"n":"audio/frosty04"},{"a":546,'
                '"n":"audio/frosty05"}],"sa":[{"a":546,'
                '"n":"audio/frosty01"},{"a":546,"n":"audio/frosty02"},'
                '{"a":546,"n":"audio/frosty03"},{"a":546,'
                '"n":"audio/frosty04"},{"a":546,"n":"audio/frosty05"}],'
                '"si":[{"a":546,"n":"audio/frosty_hit01"},{"a":546,'
                '"n":"audio/frosty_hit02"},{"a":546,'
                '"n":"audio/frosty_hit03"}],"sd":[{"a":546,'
                '"n":"audio/frosty_death"}],"sp":[{"a":546,'
                '"n":"audio/frosty01"},{"a":546,"n":"audio/frosty02"},'
                '{"a":546,"n":"audio/frosty03"},{"a":546,'
                '"n":"audio/frosty04"},{"a":546,"n":"audio/frosty05"}],'
                '"sf":[{"a":546,"n":"audio/frosty_fall"}],"cl":[0.5,0.5,'
                '1.0],"hl":[1.0,0.5,0.0],"tr":0.3,"so":[-0.04,0.03,0.0],'
                '"le":"n","re":"n"}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/frosty_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/frosty_icon_color_mask\\"},'
                '\\"cl\\":[0.5,0.5,1.0],\\"hl\\":[1.0,0.5,0.0]}}","_t":"ci"}'
            ),
            'strings/characters/frosty',
        ),
        'grumbledorf': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/wizard_color"},'
                '"cm":{"a":546,"n":"textures/wizard_color_mask"},'
                '"mh":{"a":546,"n":"meshes/wizard_head"},'
                '"mt":{"a":546,"n":"meshes/wizard_torso"},'
                '"mua":{"a":546,"n":"meshes/wizard_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/wizard_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/wizard_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/wizard_toes"},'
                '"mfa":{"a":546,"n":"meshes/wizard_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/wizard_hand"},'
                '"mp":{"a":546,"n":"meshes/wizard_pelvis"},'
                '"sj":[{"a":546,"n":"audio/wizard1"},{"a":546,'
                '"n":"audio/wizard2"},{"a":546,"n":"audio/wizard3"},'
                '{"a":546,"n":"audio/wizard4"}],"sa":[{"a":546,'
                '"n":"audio/wizard1"},{"a":546,"n":"audio/wizard2"},'
                '{"a":546,"n":"audio/wizard3"},{"a":546,'
                '"n":"audio/wizard4"}],"si":[{"a":546,'
                '"n":"audio/wizard_hit1"},{"a":546,'
                '"n":"audio/wizard_hit2"}],"sd":[{"a":546,'
                '"n":"audio/wizard_death"}],"sp":[{"a":546,'
                '"n":"audio/wizard1"},{"a":546,"n":"audio/wizard2"},'
                '{"a":546,"n":"audio/wizard3"},{"a":546,'
                '"n":"audio/wizard4"}],"sf":[{"a":546,'
                '"n":"audio/wizard_fall"}],"cl":[0.2,0.4,1.0],"hl":[0.06,'
                '0.15,0.4]}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/wizard_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/wizard_icon_color_mask\\"},'
                '\\"cl\\":[0.2,0.4,1.0],\\"hl\\":[0.06,0.15,0.4]}}",'
                '"_t":"ci"}'
            ),
            'strings/characters/grumbledorf',
        ),
        'jack_morgan': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/jack_color"},'
                '"cm":{"a":546,"n":"textures/jack_color_mask"},'
                '"mh":{"a":546,"n":"meshes/jack_head"},'
                '"mt":{"a":546,"n":"meshes/jack_torso"},'
                '"mua":{"a":546,"n":"meshes/jack_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/jack_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/jack_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/jack_toes"},'
                '"mfa":{"a":546,"n":"meshes/jack_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/jack_hand"},'
                '"mp":{"a":546,"n":"meshes/kronk_pelvis"},'
                '"sj":[{"a":546,"n":"audio/jack01"},{"a":546,'
                '"n":"audio/jack02"},{"a":546,"n":"audio/jack03"},'
                '{"a":546,"n":"audio/jack04"},{"a":546,'
                '"n":"audio/jack05"},{"a":546,"n":"audio/jack06"}],'
                '"sa":[{"a":546,"n":"audio/jack01"},{"a":546,'
                '"n":"audio/jack02"},{"a":546,"n":"audio/jack03"},'
                '{"a":546,"n":"audio/jack04"},{"a":546,'
                '"n":"audio/jack05"},{"a":546,"n":"audio/jack06"}],'
                '"si":[{"a":546,"n":"audio/jack_hit01"},{"a":546,'
                '"n":"audio/jack_hit02"},{"a":546,'
                '"n":"audio/jack_hit03"},{"a":546,'
                '"n":"audio/jack_hit04"},{"a":546,'
                '"n":"audio/jack_hit05"},{"a":546,'
                '"n":"audio/jack_hit06"},{"a":546,'
                '"n":"audio/jack_hit07"}],"sd":[{"a":546,'
                '"n":"audio/jack_death01"}],"sp":[{"a":546,'
                '"n":"audio/jack01"},{"a":546,"n":"audio/jack02"},'
                '{"a":546,"n":"audio/jack03"},{"a":546,'
                '"n":"audio/jack04"},{"a":546,"n":"audio/jack05"},'
                '{"a":546,"n":"audio/jack06"}],"sf":[{"a":546,'
                '"n":"audio/jack_fall01"}],"cl":[1.0,0.2,0.1],"hl":[1.0,1.0,'
                '0.0],"tr":0.25,"so":[-0.04,0.03,0.0],"le":"n","lc":[0.3,0.2,'
                '0.15]}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/jack_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/jack_icon_color_mask\\"},\\"cl\\":[1.0,'
                '0.2,0.1],\\"hl\\":[1.0,1.0,0.0]}}","_t":"ci"}'
            ),
            'strings/characters/jack_morgan',
        ),
        'kronk': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/kronk"},'
                '"cm":{"a":546,"n":"textures/kronk_color_mask"},'
                '"mh":{"a":546,"n":"meshes/kronk_head"},'
                '"mt":{"a":546,"n":"meshes/kronk_torso"},'
                '"mua":{"a":546,"n":"meshes/kronk_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/kronk_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/kronk_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/kronk_toes"},'
                '"mfa":{"a":546,"n":"meshes/kronk_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/kronk_hand"},'
                '"mp":{"a":546,"n":"meshes/kronk_pelvis"},'
                '"sj":[{"a":546,"n":"audio/kronk1"},{"a":546,'
                '"n":"audio/kronk2"},{"a":546,"n":"audio/kronk3"},'
                '{"a":546,"n":"audio/kronk4"},{"a":546,'
                '"n":"audio/kronk5"},{"a":546,"n":"audio/kronk6"},'
                '{"a":546,"n":"audio/kronk7"},{"a":546,'
                '"n":"audio/kronk8"},{"a":546,"n":"audio/kronk9"},'
                '{"a":546,"n":"audio/kronk10"}],"sa":[{"a":546,'
                '"n":"audio/kronk1"},{"a":546,"n":"audio/kronk2"},'
                '{"a":546,"n":"audio/kronk3"},{"a":546,'
                '"n":"audio/kronk4"},{"a":546,"n":"audio/kronk5"},'
                '{"a":546,"n":"audio/kronk6"},{"a":546,'
                '"n":"audio/kronk7"},{"a":546,"n":"audio/kronk8"},'
                '{"a":546,"n":"audio/kronk9"},{"a":546,'
                '"n":"audio/kronk10"}],"si":[{"a":546,'
                '"n":"audio/kronk1"},{"a":546,"n":"audio/kronk2"},'
                '{"a":546,"n":"audio/kronk3"},{"a":546,'
                '"n":"audio/kronk4"},{"a":546,"n":"audio/kronk5"},'
                '{"a":546,"n":"audio/kronk6"},{"a":546,'
                '"n":"audio/kronk7"},{"a":546,"n":"audio/kronk8"},'
                '{"a":546,"n":"audio/kronk9"},{"a":546,'
                '"n":"audio/kronk10"}],"sd":[{"a":546,'
                '"n":"audio/kronk_death"}],"sp":[{"a":546,'
                '"n":"audio/kronk1"},{"a":546,"n":"audio/kronk2"},'
                '{"a":546,"n":"audio/kronk3"},{"a":546,'
                '"n":"audio/kronk4"},{"a":546,"n":"audio/kronk5"},'
                '{"a":546,"n":"audio/kronk6"},{"a":546,'
                '"n":"audio/kronk7"},{"a":546,"n":"audio/kronk8"},'
                '{"a":546,"n":"audio/kronk9"},{"a":546,'
                '"n":"audio/kronk10"}],"sf":[{"a":546,'
                '"n":"audio/kronk_fall"}],"cl":[0.4,0.5,0.4],"hl":[1.0,0.5,'
                '0.3],"tr":0.2,"so":[-0.03,0.0,0.0],"es":0.8,"lc":[0.3,0.2,'
                '0.1],"ln":20.0}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/kronk_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/kronk_icon_color_mask\\"},\\"cl\\":[0.4,'
                '0.5,0.4],\\"hl\\":[1.0,0.5,0.3]}}","_t":"ci"}'
            ),
            'strings/characters/kronk',
        ),
        'lucky': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/assassin_color"},'
                '"cm":{"a":546,"n":"textures/assassin_color_mask"},'
                '"mh":{"a":546,"n":"meshes/assassin_head"},'
                '"mt":{"a":546,"n":"meshes/assassin_torso"},'
                '"mua":{"a":546,"n":"meshes/assassin_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/assassin_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/assassin_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/assassin_toes"},'
                '"mfa":{"a":546,"n":"meshes/assassin_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/assassin_hand"},'
                '"mp":{"a":546,"n":"meshes/assassin_pelvis"},'
                '"sj":[{"a":546,"n":"audio/assassin1"},{"a":546,'
                '"n":"audio/assassin2"},{"a":546,"n":"audio/assassin3"},'
                '{"a":546,"n":"audio/assassin4"}],"sa":[{"a":546,'
                '"n":"audio/assassin1"},{"a":546,"n":"audio/assassin2"},'
                '{"a":546,"n":"audio/assassin3"},{"a":546,'
                '"n":"audio/assassin4"}],"si":[{"a":546,'
                '"n":"audio/assassin_hit1"},{"a":546,'
                '"n":"audio/assassin_hit2"}],"sd":[{"a":546,'
                '"n":"audio/assassin_death"}],"sp":[{"a":546,'
                '"n":"audio/assassin1"},{"a":546,"n":"audio/assassin2"},'
                '{"a":546,"n":"audio/assassin3"},{"a":546,'
                '"n":"audio/assassin4"}],"sf":[{"a":546,'
                '"n":"audio/assassin_fall"}],"cl":[0.2,1.0,0.5],"hl":[1.0,'
                '0.3,0.0]}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/assassin_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/assassin_icon_color_mask\\"},'
                '\\"cl\\":[0.2,1.0,0.5],\\"hl\\":[1.0,0.3,0.0]}}","_t":"ci"}'
            ),
            'strings/characters/lucky',
        ),
        'mel': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/mel_color"},'
                '"cm":{"a":546,"n":"textures/mel_color_mask"},'
                '"mh":{"a":546,"n":"meshes/mel_head"},'
                '"mt":{"a":546,"n":"meshes/mel_torso"},'
                '"mua":{"a":546,"n":"meshes/mel_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/mel_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/mel_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/mel_toes"},'
                '"mfa":{"a":546,"n":"meshes/mel_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/mel_hand"},'
                '"mp":{"a":546,"n":"meshes/kronk_pelvis"},'
                '"sj":[{"a":546,"n":"audio/mel01"},{"a":546,'
                '"n":"audio/mel02"},{"a":546,"n":"audio/mel03"},'
                '{"a":546,"n":"audio/mel04"},{"a":546,'
                '"n":"audio/mel05"},{"a":546,"n":"audio/mel06"},'
                '{"a":546,"n":"audio/mel07"},{"a":546,'
                '"n":"audio/mel08"},{"a":546,"n":"audio/mel09"},'
                '{"a":546,"n":"audio/mel10"}],"sa":[{"a":546,'
                '"n":"audio/mel01"},{"a":546,"n":"audio/mel02"},'
                '{"a":546,"n":"audio/mel03"},{"a":546,'
                '"n":"audio/mel04"},{"a":546,"n":"audio/mel05"},'
                '{"a":546,"n":"audio/mel06"},{"a":546,'
                '"n":"audio/mel07"},{"a":546,"n":"audio/mel08"},'
                '{"a":546,"n":"audio/mel09"},{"a":546,'
                '"n":"audio/mel10"}],"si":[{"a":546,"n":"audio/mel01"},'
                '{"a":546,"n":"audio/mel02"},{"a":546,'
                '"n":"audio/mel03"},{"a":546,"n":"audio/mel04"},'
                '{"a":546,"n":"audio/mel05"},{"a":546,'
                '"n":"audio/mel06"},{"a":546,"n":"audio/mel07"},'
                '{"a":546,"n":"audio/mel08"},{"a":546,'
                '"n":"audio/mel09"},{"a":546,"n":"audio/mel10"}],'
                '"sd":[{"a":546,"n":"audio/mel_death01"}],'
                '"sp":[{"a":546,"n":"audio/mel01"},{"a":546,'
                '"n":"audio/mel02"},{"a":546,"n":"audio/mel03"},'
                '{"a":546,"n":"audio/mel04"},{"a":546,'
                '"n":"audio/mel05"},{"a":546,"n":"audio/mel06"},'
                '{"a":546,"n":"audio/mel07"},{"a":546,'
                '"n":"audio/mel08"},{"a":546,"n":"audio/mel09"},'
                '{"a":546,"n":"audio/mel10"}],"sf":[{"a":546,'
                '"n":"audio/mel_fall01"}],"cl":[1.0,1.0,1.0],"hl":[0.1,0.6,'
                '0.1],"tr":0.23,"so":[-0.04,0.03,0.0],"es":1.05,"eo":[0.075,'
                '-0.026,0.165],"eb":[0.63,0.53,0.49],"lc":[0.8,0.55,0.45]}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/mel_icon\\"},\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/mel_icon_color_mask\\"},\\"cl\\":[1.0,'
                '1.0,1.0],\\"hl\\":[0.1,0.6,0.1]}}","_t":"ci"}'
            ),
            'strings/characters/mel',
        ),
        'pascal': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/penguin_color"},'
                '"cm":{"a":546,"n":"textures/penguin_color_mask"},'
                '"mh":{"a":546,"n":"meshes/penguin_head"},'
                '"mt":{"a":546,"n":"meshes/penguin_torso"},'
                '"mua":{"a":546,"n":"meshes/penguin_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/penguin_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/penguin_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/penguin_toes"},'
                '"mp":{"a":546,"n":"meshes/penguin_pelvis"},'
                '"sj":[{"a":546,"n":"audio/penguin1"},{"a":546,'
                '"n":"audio/penguin2"},{"a":546,"n":"audio/penguin3"},'
                '{"a":546,"n":"audio/penguin4"}],"sa":[{"a":546,'
                '"n":"audio/penguin1"},{"a":546,"n":"audio/penguin2"},'
                '{"a":546,"n":"audio/penguin3"},{"a":546,'
                '"n":"audio/penguin4"}],"si":[{"a":546,'
                '"n":"audio/penguin_hit1"},{"a":546,'
                '"n":"audio/penguin_hit2"}],"sd":[{"a":546,'
                '"n":"audio/penguin_death"}],"sp":[{"a":546,'
                '"n":"audio/penguin1"},{"a":546,"n":"audio/penguin2"},'
                '{"a":546,"n":"audio/penguin3"},{"a":546,'
                '"n":"audio/penguin4"}],"sf":[{"a":546,'
                '"n":"audio/penguin_fall"}],"cl":[0.3,0.5,0.8],"hl":[1.0,0.0,'
                '0.0],"tr":0.25,"so":[-0.02,-0.01,0.0],"le":"l","re":"l",'
                '"es":0.65,"eo":[0.065,0.014,0.155],"ec":[0.0,0.0,0.0],'
                '"eb":[0.5,0.5,0.5],"lc":[0.1,0.1,0.1],"rs":0.2,"fl":true}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/penguin_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/penguin_icon_color_mask\\"},'
                '\\"cl\\":[0.3,0.5,0.8],\\"hl\\":[1.0,0.0,0.0]}}","_t":"ci"}'
            ),
            'strings/characters/pascal',
        ),
        'pixel': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/pixie_color"},'
                '"cm":{"a":546,"n":"textures/pixie_color_mask"},'
                '"mh":{"a":546,"n":"meshes/pixie_head"},'
                '"mt":{"a":546,"n":"meshes/pixie_torso"},'
                '"mua":{"a":546,"n":"meshes/pixie_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/pixie_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/pixie_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/pixie_toes"},'
                '"mfa":{"a":546,"n":"meshes/pixie_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/pixie_hand"},'
                '"mp":{"a":546,"n":"meshes/pixie_pelvis"},'
                '"sj":[{"a":546,"n":"audio/pixie1"},{"a":546,'
                '"n":"audio/pixie2"},{"a":546,"n":"audio/pixie3"},'
                '{"a":546,"n":"audio/pixie4"}],"sa":[{"a":546,'
                '"n":"audio/pixie1"},{"a":546,"n":"audio/pixie2"},'
                '{"a":546,"n":"audio/pixie3"},{"a":546,'
                '"n":"audio/pixie4"}],"si":[{"a":546,'
                '"n":"audio/pixie_hit1"},{"a":546,'
                '"n":"audio/pixie_hit2"}],"sd":[{"a":546,'
                '"n":"audio/pixie_death"}],"sp":[{"a":546,'
                '"n":"audio/pixie1"},{"a":546,"n":"audio/pixie2"},'
                '{"a":546,"n":"audio/pixie3"},{"a":546,'
                '"n":"audio/pixie4"}],"sf":[{"a":546,'
                '"n":"audio/pixie_fall"}],"cl":[0.0,1.0,0.7],"hl":[0.65,0.35,'
                '0.75],"tr":0.11,"so":[0.03,0.0,-0.02],"lt":0.06,"la":0.045,'
                '"ss":0.03,"ia":0.2,"aw":0.3,"iw":0.02,"es":0.85,"eo":[0.083,'
                '0.004,0.2],"ec":[0.1,0.3,0.1],"eb":[0.58,0.55,0.6],'
                '"lc":[0.73,0.53,0.6],"ln":10.0,"rs":0.35,'
                '"at":{"w":[{"t":"fx","s":[{"m":{"a":546,'
                '"n":"meshes/pixie_wing"},"t":{"a":546,'
                '"n":"textures/pixie_wings"},"tm":{"a":546,'
                '"n":"textures/pixie_wings_color_mask"}}]}]}}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/pixie_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/pixie_icon_color_mask\\"},\\"cl\\":[0.0,'
                '1.0,0.7],\\"hl\\":[0.65,0.35,0.75]}}","_t":"ci"}'
            ),
            'strings/characters/pixel',
        ),
        'santa_claus': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/santa_color"},'
                '"cm":{"a":546,"n":"textures/santa_color_mask"},'
                '"mh":{"a":546,"n":"meshes/santa_head"},'
                '"mt":{"a":546,"n":"meshes/santa_torso"},'
                '"mua":{"a":546,"n":"meshes/santa_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/santa_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/santa_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/santa_toes"},'
                '"mfa":{"a":546,"n":"meshes/santa_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/santa_hand"},'
                '"mp":{"a":546,"n":"meshes/kronk_pelvis"},'
                '"sj":[{"a":546,"n":"audio/santa01"},{"a":546,'
                '"n":"audio/santa02"},{"a":546,"n":"audio/santa03"},'
                '{"a":546,"n":"audio/santa04"},{"a":546,'
                '"n":"audio/santa05"}],"sa":[{"a":546,'
                '"n":"audio/santa01"},{"a":546,"n":"audio/santa02"},'
                '{"a":546,"n":"audio/santa03"},{"a":546,'
                '"n":"audio/santa04"},{"a":546,"n":"audio/santa05"}],'
                '"si":[{"a":546,"n":"audio/santa_hit01"},{"a":546,'
                '"n":"audio/santa_hit02"},{"a":546,'
                '"n":"audio/santa_hit03"},{"a":546,'
                '"n":"audio/santa_hit04"}],"sd":[{"a":546,'
                '"n":"audio/santa_death"}],"sp":[{"a":546,'
                '"n":"audio/santa01"},{"a":546,"n":"audio/santa02"},'
                '{"a":546,"n":"audio/santa03"},{"a":546,'
                '"n":"audio/santa04"},{"a":546,"n":"audio/santa05"}],'
                '"sf":[{"a":546,"n":"audio/santa_fall"}],"cl":[1.0,0.0,'
                '0.0],"hl":[1.0,1.0,1.0],"tr":0.2,"so":[-0.04,0.03,0.0],'
                '"es":0.9,"eo":[0.065,-0.016,0.235],"lc":[0.5,0.4,0.3]}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/santa_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/santa_icon_color_mask\\"},\\"cl\\":[1.0,'
                '0.0,0.0],\\"hl\\":[1.0,1.0,1.0]}}","_t":"ci"}'
            ),
            'strings/characters/santa_claus',
        ),
        'snake_shadow': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/ninja_color"},'
                '"cm":{"a":546,"n":"textures/ninja_color_mask"},'
                '"mh":{"a":546,"n":"meshes/ninja_head"},'
                '"mt":{"a":546,"n":"meshes/ninja_torso"},'
                '"mua":{"a":546,"n":"meshes/ninja_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/ninja_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/ninja_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/ninja_toes"},'
                '"mfa":{"a":546,"n":"meshes/ninja_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/ninja_hand"},'
                '"mp":{"a":546,"n":"meshes/ninja_pelvis"},'
                '"sj":[{"a":546,"n":"audio/ninja_attack1"},'
                '{"a":546,"n":"audio/ninja_attack2"},{"a":546,'
                '"n":"audio/ninja_attack3"},{"a":546,'
                '"n":"audio/ninja_attack4"},{"a":546,'
                '"n":"audio/ninja_attack5"},{"a":546,'
                '"n":"audio/ninja_attack6"},{"a":546,'
                '"n":"audio/ninja_attack7"}],"sa":[{"a":546,'
                '"n":"audio/ninja_attack1"},{"a":546,'
                '"n":"audio/ninja_attack2"},{"a":546,'
                '"n":"audio/ninja_attack3"},{"a":546,'
                '"n":"audio/ninja_attack4"},{"a":546,'
                '"n":"audio/ninja_attack5"},{"a":546,'
                '"n":"audio/ninja_attack6"},{"a":546,'
                '"n":"audio/ninja_attack7"}],"si":[{"a":546,'
                '"n":"audio/ninja_hit1"},{"a":546,'
                '"n":"audio/ninja_hit2"},{"a":546,'
                '"n":"audio/ninja_hit3"},{"a":546,'
                '"n":"audio/ninja_hit4"},{"a":546,'
                '"n":"audio/ninja_hit5"},{"a":546,'
                '"n":"audio/ninja_hit6"},{"a":546,'
                '"n":"audio/ninja_hit7"},{"a":546,'
                '"n":"audio/ninja_hit8"}],"sd":[{"a":546,'
                '"n":"audio/ninja_death1"}],"sp":[{"a":546,'
                '"n":"audio/ninja_attack1"},{"a":546,'
                '"n":"audio/ninja_attack2"},{"a":546,'
                '"n":"audio/ninja_attack3"},{"a":546,'
                '"n":"audio/ninja_attack4"},{"a":546,'
                '"n":"audio/ninja_attack5"},{"a":546,'
                '"n":"audio/ninja_attack6"},{"a":546,'
                '"n":"audio/ninja_attack7"}],"sf":[{"a":546,'
                '"n":"audio/ninja_fall1"}],"cl":[1.0,1.0,1.0],"hl":[0.55,0.8,'
                '0.55],"ss":0.056,"ec":[0.2,0.1,0.0],"ln":20.0,"rs":0.15}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/ninja_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/ninja_icon_color_mask\\"},\\"cl\\":[1.0,'
                '1.0,1.0],\\"hl\\":[0.55,0.8,0.55]}}","_t":"ci"}'
            ),
            'strings/characters/snake_shadow',
        ),
        'spaz': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/neo_spaz_color"},'
                '"cm":{"a":546,"n":"textures/neo_spaz_color_mask"},'
                '"mh":{"a":546,"n":"meshes/neo_spaz_head"},'
                '"mt":{"a":546,"n":"meshes/neo_spaz_torso"},'
                '"mua":{"a":546,"n":"meshes/neo_spaz_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/neo_spaz_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/neo_spaz_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/neo_spaz_toes"},'
                '"mfa":{"a":546,"n":"meshes/neo_spaz_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/neo_spaz_hand"},'
                '"mp":{"a":546,"n":"meshes/neo_spaz_pelvis"},'
                '"sj":[{"a":546,"n":"audio/spaz_jump01"},{"a":546,'
                '"n":"audio/spaz_jump02"},{"a":546,'
                '"n":"audio/spaz_jump03"},{"a":546,'
                '"n":"audio/spaz_jump04"}],"sa":[{"a":546,'
                '"n":"audio/spaz_attack01"},{"a":546,'
                '"n":"audio/spaz_attack02"},{"a":546,'
                '"n":"audio/spaz_attack03"},{"a":546,'
                '"n":"audio/spaz_attack04"}],"si":[{"a":546,'
                '"n":"audio/spaz_impact01"},{"a":546,'
                '"n":"audio/spaz_impact02"},{"a":546,'
                '"n":"audio/spaz_impact03"},{"a":546,'
                '"n":"audio/spaz_impact04"}],"sd":[{"a":546,'
                '"n":"audio/spaz_death01"}],"sp":[{"a":546,'
                '"n":"audio/spaz_pickup01"}],"sf":[{"a":546,'
                '"n":"audio/spaz_fall01"}],"cl":[0.5,0.5,0.5]}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/neo_spaz_icon\\"},'
                '\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/neo_spaz_icon_color_mask\\"}}}",'
                '"_t":"ci"}'
            ),
            'strings/characters/spaz',
        ),
        'zoe': (
            (
                '{"b":{"ct":{"a":546,"n":"textures/zoe_color"},'
                '"cm":{"a":546,"n":"textures/zoe_color_mask"},'
                '"mh":{"a":546,"n":"meshes/zoe_head"},'
                '"mt":{"a":546,"n":"meshes/zoe_torso"},'
                '"mua":{"a":546,"n":"meshes/zoe_upper_arm"},'
                '"mul":{"a":546,"n":"meshes/zoe_upper_leg"},'
                '"mll":{"a":546,"n":"meshes/zoe_lower_leg"},'
                '"mto":{"a":546,"n":"meshes/zoe_toes"},'
                '"mfa":{"a":546,"n":"meshes/zoe_fore_arm"},'
                '"mhn":{"a":546,"n":"meshes/zoe_hand"},'
                '"mp":{"a":546,"n":"meshes/zoe_pelvis"},'
                '"sj":[{"a":546,"n":"audio/zoe_jump01"},{"a":546,'
                '"n":"audio/zoe_jump02"},{"a":546,'
                '"n":"audio/zoe_jump03"}],"sa":[{"a":546,'
                '"n":"audio/zoe_attack01"},{"a":546,'
                '"n":"audio/zoe_attack02"},{"a":546,'
                '"n":"audio/zoe_attack03"},{"a":546,'
                '"n":"audio/zoe_attack04"}],"si":[{"a":546,'
                '"n":"audio/zoe_impact01"},{"a":546,'
                '"n":"audio/zoe_impact02"},{"a":546,'
                '"n":"audio/zoe_impact03"},{"a":546,'
                '"n":"audio/zoe_impact04"}],"sd":[{"a":546,'
                '"n":"audio/zoe_death01"}],"sp":[{"a":546,'
                '"n":"audio/zoe_pickup01"}],"sf":[{"a":546,'
                '"n":"audio/zoe_fall01"}],"cl":[0.6,0.6,0.6],"hl":[0.0,1.0,'
                '0.0],"tr":0.11,"so":[0.03,0.0,-0.02],"lt":0.06,"la":0.045,'
                '"ss":0.03,"ia":0.2,"aw":0.3,"iw":0.02,"es":0.95,"eo":[0.08,'
                '-0.036,0.205],"ec":[0.55,0.3,0.7],"eb":[0.54,0.51,0.55],'
                '"lc":[0.6,0.35,0.31],"ln":15.0,"at":{"h":[{"t":"an",'
                '"s":[{"m":{"a":546,"n":"meshes/hair_tuft1"},"o":[1.0,'
                '1.0,1.0,0.02,0.16,0.05]}],"p":[-0.173,0.124,0.153],'
                '"q":[0.88999,-0.2665,-0.369995,0.0],"k":0.2,"d":0.7,'
                '"r":0.375},{"t":"an","s":[{"m":{"a":546,'
                '"n":"meshes/hair_tuft2"},"o":[1.0,1.0,1.0,-0.01,0.03,0.06,'
                '0.976305,0.216397,0.0,0.0]}],"p":[0.196,0.098,0.118],'
                '"q":[0.858162,-0.229591,0.45918,3e-06],"k":0.3,"d":0.7},'
                '{"t":"a2","s":[{"m":{"a":546,"n":"meshes/hair_tuft3"},'
                '"o":[1.0,1.0,1.0,0.0,0.0,0.0,0.0,0.0,1.0,0.0]},'
                '{"m":{"a":546,"n":"meshes/hair_tuft4"},"o":[1.0,1.0,'
                '1.0,0.0,0.0,0.04,0.0,0.0,1.0,0.0]}],"p":[0.0,0.28,-0.224],'
                '"q":[0.0,0.0,0.852526,0.522685],"k":0.67,"d":0.8,"l":0.8,'
                '"r":0.625,"kc":-0.26}]}}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/zoe_icon\\"},\\"cm\\":{\\"a\\":546,'
                '\\"n\\":\\"textures/zoe_icon_color_mask\\"},\\"cl\\":[0.6,'
                '0.6,0.6],\\"hl\\":[0.0,1.0,0.0]}}","_t":"ci"}'
            ),
            'strings/characters/zoe',
        ),
    },
}


if not TYPE_CHECKING:
    audio = AssetGroup(_ASSET_PACKAGE, _TREE['audio'], 'audio')
    meshes = AssetGroup(_ASSET_PACKAGE, _TREE['meshes'], 'meshes')
    strings = LangStrDir(_ASSET_PACKAGE, _TREE['strings'], 'strings')
    textures = AssetGroup(_ASSET_PACKAGE, _TREE['textures'], 'textures')
    characters = CharacterGroup(
        _ASSET_PACKAGE, _CHARACTERS['characters'], 'characters'
    )
