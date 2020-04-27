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
"""Appearance functionality for spazzes."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import List, Optional, Tuple


def get_appearances(include_locked: bool = False) -> List[str]:
    """Get the list of available spaz appearances."""
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    disallowed = []
    if not include_locked:
        # hmm yeah this'll be tough to hack...
        if not _ba.get_purchased('characters.santa'):
            disallowed.append('Santa Claus')
        if not _ba.get_purchased('characters.frosty'):
            disallowed.append('Frosty')
        if not _ba.get_purchased('characters.bones'):
            disallowed.append('Bones')
        if not _ba.get_purchased('characters.bernard'):
            disallowed.append('Bernard')
        if not _ba.get_purchased('characters.pixie'):
            disallowed.append('Pixel')
        if not _ba.get_purchased('characters.pascal'):
            disallowed.append('Pascal')
        if not _ba.get_purchased('characters.actionhero'):
            disallowed.append('Todd McBurton')
        if not _ba.get_purchased('characters.taobaomascot'):
            disallowed.append('Taobao Mascot')
        if not _ba.get_purchased('characters.agent'):
            disallowed.append('Agent Johnson')
        if not _ba.get_purchased('characters.jumpsuit'):
            disallowed.append('Lee')
        if not _ba.get_purchased('characters.assassin'):
            disallowed.append('Zola')
        if not _ba.get_purchased('characters.wizard'):
            disallowed.append('Grumbledorf')
        if not _ba.get_purchased('characters.cowboy'):
            disallowed.append('Butch')
        if not _ba.get_purchased('characters.witch'):
            disallowed.append('Witch')
        if not _ba.get_purchased('characters.warrior'):
            disallowed.append('Warrior')
        if not _ba.get_purchased('characters.superhero'):
            disallowed.append('Middle-Man')
        if not _ba.get_purchased('characters.alien'):
            disallowed.append('Alien')
        if not _ba.get_purchased('characters.oldlady'):
            disallowed.append('OldLady')
        if not _ba.get_purchased('characters.gladiator'):
            disallowed.append('Gladiator')
        if not _ba.get_purchased('characters.wrestler'):
            disallowed.append('Wrestler')
        if not _ba.get_purchased('characters.operasinger'):
            disallowed.append('Gretel')
        if not _ba.get_purchased('characters.robot'):
            disallowed.append('Robot')
        if not _ba.get_purchased('characters.cyborg'):
            disallowed.append('B-9000')
        if not _ba.get_purchased('characters.bunny'):
            disallowed.append('Easter Bunny')
        if not _ba.get_purchased('characters.kronk'):
            disallowed.append('Kronk')
        if not _ba.get_purchased('characters.zoe'):
            disallowed.append('Zoe')
        if not _ba.get_purchased('characters.jackmorgan'):
            disallowed.append('Jack Morgan')
        if not _ba.get_purchased('characters.mel'):
            disallowed.append('Mel')
        if not _ba.get_purchased('characters.snakeshadow'):
            disallowed.append('Snake Shadow')
    return [
        s for s in list(ba.app.spaz_appearances.keys()) if s not in disallowed
    ]


class Appearance:
    """Create and fill out one of these suckers to define a spaz appearance"""

    def __init__(self, name: str):
        self.name = name
        if self.name in ba.app.spaz_appearances:
            raise Exception('spaz appearance name "' + self.name +
                            '" already exists.')
        ba.app.spaz_appearances[self.name] = self
        self.color_texture = ''
        self.color_mask_texture = ''
        self.icon_texture = ''
        self.icon_mask_texture = ''
        self.head_model = ''
        self.torso_model = ''
        self.pelvis_model = ''
        self.upper_arm_model = ''
        self.forearm_model = ''
        self.hand_model = ''
        self.upper_leg_model = ''
        self.lower_leg_model = ''
        self.toes_model = ''
        self.jump_sounds: List[str] = []
        self.attack_sounds: List[str] = []
        self.impact_sounds: List[str] = []
        self.death_sounds: List[str] = []
        self.pickup_sounds: List[str] = []
        self.fall_sounds: List[str] = []
        self.style = 'spaz'
        self.default_color: Optional[Tuple[float, float, float]] = None
        self.default_highlight: Optional[Tuple[float, float, float]] = None


def register_appearances() -> None:
    """Register our builtin spaz appearances."""

    # this is quite ugly but will be going away so not worth cleaning up
    # pylint: disable=invalid-name
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    # Spaz #######################################
    t = Appearance('Spaz')
    t.color_texture = 'neoSpazColor'
    t.color_mask_texture = 'neoSpazColorMask'
    t.icon_texture = 'neoSpazIcon'
    t.icon_mask_texture = 'neoSpazIconColorMask'
    t.head_model = 'neoSpazHead'
    t.torso_model = 'neoSpazTorso'
    t.pelvis_model = 'neoSpazPelvis'
    t.upper_arm_model = 'neoSpazUpperArm'
    t.forearm_model = 'neoSpazForeArm'
    t.hand_model = 'neoSpazHand'
    t.upper_leg_model = 'neoSpazUpperLeg'
    t.lower_leg_model = 'neoSpazLowerLeg'
    t.toes_model = 'neoSpazToes'
    t.jump_sounds = ['spazJump01', 'spazJump02', 'spazJump03', 'spazJump04']
    t.attack_sounds = [
        'spazAttack01', 'spazAttack02', 'spazAttack03', 'spazAttack04'
    ]
    t.impact_sounds = [
        'spazImpact01', 'spazImpact02', 'spazImpact03', 'spazImpact04'
    ]
    t.death_sounds = ['spazDeath01']
    t.pickup_sounds = ['spazPickup01']
    t.fall_sounds = ['spazFall01']
    t.style = 'spaz'

    # Zoe #####################################
    t = Appearance('Zoe')
    t.color_texture = 'zoeColor'
    t.color_mask_texture = 'zoeColorMask'
    t.default_color = (0.6, 0.6, 0.6)
    t.default_highlight = (0, 1, 0)
    t.icon_texture = 'zoeIcon'
    t.icon_mask_texture = 'zoeIconColorMask'
    t.head_model = 'zoeHead'
    t.torso_model = 'zoeTorso'
    t.pelvis_model = 'zoePelvis'
    t.upper_arm_model = 'zoeUpperArm'
    t.forearm_model = 'zoeForeArm'
    t.hand_model = 'zoeHand'
    t.upper_leg_model = 'zoeUpperLeg'
    t.lower_leg_model = 'zoeLowerLeg'
    t.toes_model = 'zoeToes'
    t.jump_sounds = ['zoeJump01', 'zoeJump02', 'zoeJump03']
    t.attack_sounds = [
        'zoeAttack01', 'zoeAttack02', 'zoeAttack03', 'zoeAttack04'
    ]
    t.impact_sounds = [
        'zoeImpact01', 'zoeImpact02', 'zoeImpact03', 'zoeImpact04'
    ]
    t.death_sounds = ['zoeDeath01']
    t.pickup_sounds = ['zoePickup01']
    t.fall_sounds = ['zoeFall01']
    t.style = 'female'

    # Ninja ##########################################
    t = Appearance('Snake Shadow')
    t.color_texture = 'ninjaColor'
    t.color_mask_texture = 'ninjaColorMask'
    t.default_color = (1, 1, 1)
    t.default_highlight = (0.55, 0.8, 0.55)
    t.icon_texture = 'ninjaIcon'
    t.icon_mask_texture = 'ninjaIconColorMask'
    t.head_model = 'ninjaHead'
    t.torso_model = 'ninjaTorso'
    t.pelvis_model = 'ninjaPelvis'
    t.upper_arm_model = 'ninjaUpperArm'
    t.forearm_model = 'ninjaForeArm'
    t.hand_model = 'ninjaHand'
    t.upper_leg_model = 'ninjaUpperLeg'
    t.lower_leg_model = 'ninjaLowerLeg'
    t.toes_model = 'ninjaToes'
    ninja_attacks = ['ninjaAttack' + str(i + 1) + '' for i in range(7)]
    ninja_hits = ['ninjaHit' + str(i + 1) + '' for i in range(8)]
    ninja_jumps = ['ninjaAttack' + str(i + 1) + '' for i in range(7)]
    t.jump_sounds = ninja_jumps
    t.attack_sounds = ninja_attacks
    t.impact_sounds = ninja_hits
    t.death_sounds = ['ninjaDeath1']
    t.pickup_sounds = ninja_attacks
    t.fall_sounds = ['ninjaFall1']
    t.style = 'ninja'

    # Barbarian #####################################
    t = Appearance('Kronk')
    t.color_texture = 'kronk'
    t.color_mask_texture = 'kronkColorMask'
    t.default_color = (0.4, 0.5, 0.4)
    t.default_highlight = (1, 0.5, 0.3)
    t.icon_texture = 'kronkIcon'
    t.icon_mask_texture = 'kronkIconColorMask'
    t.head_model = 'kronkHead'
    t.torso_model = 'kronkTorso'
    t.pelvis_model = 'kronkPelvis'
    t.upper_arm_model = 'kronkUpperArm'
    t.forearm_model = 'kronkForeArm'
    t.hand_model = 'kronkHand'
    t.upper_leg_model = 'kronkUpperLeg'
    t.lower_leg_model = 'kronkLowerLeg'
    t.toes_model = 'kronkToes'
    kronk_sounds = [
        'kronk1', 'kronk2', 'kronk3', 'kronk4', 'kronk5', 'kronk6', 'kronk7',
        'kronk8', 'kronk9', 'kronk10'
    ]
    t.jump_sounds = kronk_sounds
    t.attack_sounds = kronk_sounds
    t.impact_sounds = kronk_sounds
    t.death_sounds = ['kronkDeath']
    t.pickup_sounds = kronk_sounds
    t.fall_sounds = ['kronkFall']
    t.style = 'kronk'

    # Chef ###########################################
    t = Appearance('Mel')
    t.color_texture = 'melColor'
    t.color_mask_texture = 'melColorMask'
    t.default_color = (1, 1, 1)
    t.default_highlight = (0.1, 0.6, 0.1)
    t.icon_texture = 'melIcon'
    t.icon_mask_texture = 'melIconColorMask'
    t.head_model = 'melHead'
    t.torso_model = 'melTorso'
    t.pelvis_model = 'kronkPelvis'
    t.upper_arm_model = 'melUpperArm'
    t.forearm_model = 'melForeArm'
    t.hand_model = 'melHand'
    t.upper_leg_model = 'melUpperLeg'
    t.lower_leg_model = 'melLowerLeg'
    t.toes_model = 'melToes'
    mel_sounds = [
        'mel01', 'mel02', 'mel03', 'mel04', 'mel05', 'mel06', 'mel07', 'mel08',
        'mel09', 'mel10'
    ]
    t.attack_sounds = mel_sounds
    t.jump_sounds = mel_sounds
    t.impact_sounds = mel_sounds
    t.death_sounds = ['melDeath01']
    t.pickup_sounds = mel_sounds
    t.fall_sounds = ['melFall01']
    t.style = 'mel'

    # Pirate #######################################
    t = Appearance('Jack Morgan')
    t.color_texture = 'jackColor'
    t.color_mask_texture = 'jackColorMask'
    t.default_color = (1, 0.2, 0.1)
    t.default_highlight = (1, 1, 0)
    t.icon_texture = 'jackIcon'
    t.icon_mask_texture = 'jackIconColorMask'
    t.head_model = 'jackHead'
    t.torso_model = 'jackTorso'
    t.pelvis_model = 'kronkPelvis'
    t.upper_arm_model = 'jackUpperArm'
    t.forearm_model = 'jackForeArm'
    t.hand_model = 'jackHand'
    t.upper_leg_model = 'jackUpperLeg'
    t.lower_leg_model = 'jackLowerLeg'
    t.toes_model = 'jackToes'
    hit_sounds = [
        'jackHit01', 'jackHit02', 'jackHit03', 'jackHit04', 'jackHit05',
        'jackHit06', 'jackHit07'
    ]
    sounds = ['jack01', 'jack02', 'jack03', 'jack04', 'jack05', 'jack06']
    t.attack_sounds = sounds
    t.jump_sounds = sounds
    t.impact_sounds = hit_sounds
    t.death_sounds = ['jackDeath01']
    t.pickup_sounds = sounds
    t.fall_sounds = ['jackFall01']
    t.style = 'pirate'

    # Santa ######################################
    t = Appearance('Santa Claus')
    t.color_texture = 'santaColor'
    t.color_mask_texture = 'santaColorMask'
    t.default_color = (1, 0, 0)
    t.default_highlight = (1, 1, 1)
    t.icon_texture = 'santaIcon'
    t.icon_mask_texture = 'santaIconColorMask'
    t.head_model = 'santaHead'
    t.torso_model = 'santaTorso'
    t.pelvis_model = 'kronkPelvis'
    t.upper_arm_model = 'santaUpperArm'
    t.forearm_model = 'santaForeArm'
    t.hand_model = 'santaHand'
    t.upper_leg_model = 'santaUpperLeg'
    t.lower_leg_model = 'santaLowerLeg'
    t.toes_model = 'santaToes'
    hit_sounds = ['santaHit01', 'santaHit02', 'santaHit03', 'santaHit04']
    sounds = ['santa01', 'santa02', 'santa03', 'santa04', 'santa05']
    t.attack_sounds = sounds
    t.jump_sounds = sounds
    t.impact_sounds = hit_sounds
    t.death_sounds = ['santaDeath']
    t.pickup_sounds = sounds
    t.fall_sounds = ['santaFall']
    t.style = 'santa'

    # Snowman ###################################
    t = Appearance('Frosty')
    t.color_texture = 'frostyColor'
    t.color_mask_texture = 'frostyColorMask'
    t.default_color = (0.5, 0.5, 1)
    t.default_highlight = (1, 0.5, 0)
    t.icon_texture = 'frostyIcon'
    t.icon_mask_texture = 'frostyIconColorMask'
    t.head_model = 'frostyHead'
    t.torso_model = 'frostyTorso'
    t.pelvis_model = 'frostyPelvis'
    t.upper_arm_model = 'frostyUpperArm'
    t.forearm_model = 'frostyForeArm'
    t.hand_model = 'frostyHand'
    t.upper_leg_model = 'frostyUpperLeg'
    t.lower_leg_model = 'frostyLowerLeg'
    t.toes_model = 'frostyToes'
    frosty_sounds = [
        'frosty01', 'frosty02', 'frosty03', 'frosty04', 'frosty05'
    ]
    frosty_hit_sounds = ['frostyHit01', 'frostyHit02', 'frostyHit03']
    t.attack_sounds = frosty_sounds
    t.jump_sounds = frosty_sounds
    t.impact_sounds = frosty_hit_sounds
    t.death_sounds = ['frostyDeath']
    t.pickup_sounds = frosty_sounds
    t.fall_sounds = ['frostyFall']
    t.style = 'frosty'

    # Skeleton ################################
    t = Appearance('Bones')
    t.color_texture = 'bonesColor'
    t.color_mask_texture = 'bonesColorMask'
    t.default_color = (0.6, 0.9, 1)
    t.default_highlight = (0.6, 0.9, 1)
    t.icon_texture = 'bonesIcon'
    t.icon_mask_texture = 'bonesIconColorMask'
    t.head_model = 'bonesHead'
    t.torso_model = 'bonesTorso'
    t.pelvis_model = 'bonesPelvis'
    t.upper_arm_model = 'bonesUpperArm'
    t.forearm_model = 'bonesForeArm'
    t.hand_model = 'bonesHand'
    t.upper_leg_model = 'bonesUpperLeg'
    t.lower_leg_model = 'bonesLowerLeg'
    t.toes_model = 'bonesToes'
    bones_sounds = ['bones1', 'bones2', 'bones3']
    bones_hit_sounds = ['bones1', 'bones2', 'bones3']
    t.attack_sounds = bones_sounds
    t.jump_sounds = bones_sounds
    t.impact_sounds = bones_hit_sounds
    t.death_sounds = ['bonesDeath']
    t.pickup_sounds = bones_sounds
    t.fall_sounds = ['bonesFall']
    t.style = 'bones'

    # Bear ###################################
    t = Appearance('Bernard')
    t.color_texture = 'bearColor'
    t.color_mask_texture = 'bearColorMask'
    t.default_color = (0.7, 0.5, 0.0)
    t.icon_texture = 'bearIcon'
    t.icon_mask_texture = 'bearIconColorMask'
    t.head_model = 'bearHead'
    t.torso_model = 'bearTorso'
    t.pelvis_model = 'bearPelvis'
    t.upper_arm_model = 'bearUpperArm'
    t.forearm_model = 'bearForeArm'
    t.hand_model = 'bearHand'
    t.upper_leg_model = 'bearUpperLeg'
    t.lower_leg_model = 'bearLowerLeg'
    t.toes_model = 'bearToes'
    bear_sounds = ['bear1', 'bear2', 'bear3', 'bear4']
    bear_hit_sounds = ['bearHit1', 'bearHit2']
    t.attack_sounds = bear_sounds
    t.jump_sounds = bear_sounds
    t.impact_sounds = bear_hit_sounds
    t.death_sounds = ['bearDeath']
    t.pickup_sounds = bear_sounds
    t.fall_sounds = ['bearFall']
    t.style = 'bear'

    # Penguin ###################################
    t = Appearance('Pascal')
    t.color_texture = 'penguinColor'
    t.color_mask_texture = 'penguinColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'penguinIcon'
    t.icon_mask_texture = 'penguinIconColorMask'
    t.head_model = 'penguinHead'
    t.torso_model = 'penguinTorso'
    t.pelvis_model = 'penguinPelvis'
    t.upper_arm_model = 'penguinUpperArm'
    t.forearm_model = 'penguinForeArm'
    t.hand_model = 'penguinHand'
    t.upper_leg_model = 'penguinUpperLeg'
    t.lower_leg_model = 'penguinLowerLeg'
    t.toes_model = 'penguinToes'
    penguin_sounds = ['penguin1', 'penguin2', 'penguin3', 'penguin4']
    penguin_hit_sounds = ['penguinHit1', 'penguinHit2']
    t.attack_sounds = penguin_sounds
    t.jump_sounds = penguin_sounds
    t.impact_sounds = penguin_hit_sounds
    t.death_sounds = ['penguinDeath']
    t.pickup_sounds = penguin_sounds
    t.fall_sounds = ['penguinFall']
    t.style = 'penguin'

    # Ali ###################################
    t = Appearance('Taobao Mascot')
    t.color_texture = 'aliColor'
    t.color_mask_texture = 'aliColorMask'
    t.default_color = (1, 0.5, 0)
    t.default_highlight = (1, 1, 1)
    t.icon_texture = 'aliIcon'
    t.icon_mask_texture = 'aliIconColorMask'
    t.head_model = 'aliHead'
    t.torso_model = 'aliTorso'
    t.pelvis_model = 'aliPelvis'
    t.upper_arm_model = 'aliUpperArm'
    t.forearm_model = 'aliForeArm'
    t.hand_model = 'aliHand'
    t.upper_leg_model = 'aliUpperLeg'
    t.lower_leg_model = 'aliLowerLeg'
    t.toes_model = 'aliToes'
    ali_sounds = ['ali1', 'ali2', 'ali3', 'ali4']
    ali_hit_sounds = ['aliHit1', 'aliHit2']
    t.attack_sounds = ali_sounds
    t.jump_sounds = ali_sounds
    t.impact_sounds = ali_hit_sounds
    t.death_sounds = ['aliDeath']
    t.pickup_sounds = ali_sounds
    t.fall_sounds = ['aliFall']
    t.style = 'ali'

    # cyborg ###################################
    t = Appearance('B-9000')
    t.color_texture = 'cyborgColor'
    t.color_mask_texture = 'cyborgColorMask'
    t.default_color = (0.5, 0.5, 0.5)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'cyborgIcon'
    t.icon_mask_texture = 'cyborgIconColorMask'
    t.head_model = 'cyborgHead'
    t.torso_model = 'cyborgTorso'
    t.pelvis_model = 'cyborgPelvis'
    t.upper_arm_model = 'cyborgUpperArm'
    t.forearm_model = 'cyborgForeArm'
    t.hand_model = 'cyborgHand'
    t.upper_leg_model = 'cyborgUpperLeg'
    t.lower_leg_model = 'cyborgLowerLeg'
    t.toes_model = 'cyborgToes'
    cyborg_sounds = ['cyborg1', 'cyborg2', 'cyborg3', 'cyborg4']
    cyborg_hit_sounds = ['cyborgHit1', 'cyborgHit2']
    t.attack_sounds = cyborg_sounds
    t.jump_sounds = cyborg_sounds
    t.impact_sounds = cyborg_hit_sounds
    t.death_sounds = ['cyborgDeath']
    t.pickup_sounds = cyborg_sounds
    t.fall_sounds = ['cyborgFall']
    t.style = 'cyborg'

    # Agent ###################################
    t = Appearance('Agent Johnson')
    t.color_texture = 'agentColor'
    t.color_mask_texture = 'agentColorMask'
    t.default_color = (0.3, 0.3, 0.33)
    t.default_highlight = (1, 0.5, 0.3)
    t.icon_texture = 'agentIcon'
    t.icon_mask_texture = 'agentIconColorMask'
    t.head_model = 'agentHead'
    t.torso_model = 'agentTorso'
    t.pelvis_model = 'agentPelvis'
    t.upper_arm_model = 'agentUpperArm'
    t.forearm_model = 'agentForeArm'
    t.hand_model = 'agentHand'
    t.upper_leg_model = 'agentUpperLeg'
    t.lower_leg_model = 'agentLowerLeg'
    t.toes_model = 'agentToes'
    agent_sounds = ['agent1', 'agent2', 'agent3', 'agent4']
    agent_hit_sounds = ['agentHit1', 'agentHit2']
    t.attack_sounds = agent_sounds
    t.jump_sounds = agent_sounds
    t.impact_sounds = agent_hit_sounds
    t.death_sounds = ['agentDeath']
    t.pickup_sounds = agent_sounds
    t.fall_sounds = ['agentFall']
    t.style = 'agent'

    # Jumpsuit ###################################
    t = Appearance('Lee')
    t.color_texture = 'jumpsuitColor'
    t.color_mask_texture = 'jumpsuitColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'jumpsuitIcon'
    t.icon_mask_texture = 'jumpsuitIconColorMask'
    t.head_model = 'jumpsuitHead'
    t.torso_model = 'jumpsuitTorso'
    t.pelvis_model = 'jumpsuitPelvis'
    t.upper_arm_model = 'jumpsuitUpperArm'
    t.forearm_model = 'jumpsuitForeArm'
    t.hand_model = 'jumpsuitHand'
    t.upper_leg_model = 'jumpsuitUpperLeg'
    t.lower_leg_model = 'jumpsuitLowerLeg'
    t.toes_model = 'jumpsuitToes'
    jumpsuit_sounds = ['jumpsuit1', 'jumpsuit2', 'jumpsuit3', 'jumpsuit4']
    jumpsuit_hit_sounds = ['jumpsuitHit1', 'jumpsuitHit2']
    t.attack_sounds = jumpsuit_sounds
    t.jump_sounds = jumpsuit_sounds
    t.impact_sounds = jumpsuit_hit_sounds
    t.death_sounds = ['jumpsuitDeath']
    t.pickup_sounds = jumpsuit_sounds
    t.fall_sounds = ['jumpsuitFall']
    t.style = 'spaz'

    # ActionHero ###################################
    t = Appearance('Todd McBurton')
    t.color_texture = 'actionHeroColor'
    t.color_mask_texture = 'actionHeroColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'actionHeroIcon'
    t.icon_mask_texture = 'actionHeroIconColorMask'
    t.head_model = 'actionHeroHead'
    t.torso_model = 'actionHeroTorso'
    t.pelvis_model = 'actionHeroPelvis'
    t.upper_arm_model = 'actionHeroUpperArm'
    t.forearm_model = 'actionHeroForeArm'
    t.hand_model = 'actionHeroHand'
    t.upper_leg_model = 'actionHeroUpperLeg'
    t.lower_leg_model = 'actionHeroLowerLeg'
    t.toes_model = 'actionHeroToes'
    action_hero_sounds = [
        'actionHero1', 'actionHero2', 'actionHero3', 'actionHero4'
    ]
    action_hero_hit_sounds = ['actionHeroHit1', 'actionHeroHit2']
    t.attack_sounds = action_hero_sounds
    t.jump_sounds = action_hero_sounds
    t.impact_sounds = action_hero_hit_sounds
    t.death_sounds = ['actionHeroDeath']
    t.pickup_sounds = action_hero_sounds
    t.fall_sounds = ['actionHeroFall']
    t.style = 'spaz'

    # Assassin ###################################
    t = Appearance('Zola')
    t.color_texture = 'assassinColor'
    t.color_mask_texture = 'assassinColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'assassinIcon'
    t.icon_mask_texture = 'assassinIconColorMask'
    t.head_model = 'assassinHead'
    t.torso_model = 'assassinTorso'
    t.pelvis_model = 'assassinPelvis'
    t.upper_arm_model = 'assassinUpperArm'
    t.forearm_model = 'assassinForeArm'
    t.hand_model = 'assassinHand'
    t.upper_leg_model = 'assassinUpperLeg'
    t.lower_leg_model = 'assassinLowerLeg'
    t.toes_model = 'assassinToes'
    assassin_sounds = ['assassin1', 'assassin2', 'assassin3', 'assassin4']
    assassin_hit_sounds = ['assassinHit1', 'assassinHit2']
    t.attack_sounds = assassin_sounds
    t.jump_sounds = assassin_sounds
    t.impact_sounds = assassin_hit_sounds
    t.death_sounds = ['assassinDeath']
    t.pickup_sounds = assassin_sounds
    t.fall_sounds = ['assassinFall']
    t.style = 'spaz'

    # Wizard ###################################
    t = Appearance('Grumbledorf')
    t.color_texture = 'wizardColor'
    t.color_mask_texture = 'wizardColorMask'
    t.default_color = (0.2, 0.4, 1.0)
    t.default_highlight = (0.06, 0.15, 0.4)
    t.icon_texture = 'wizardIcon'
    t.icon_mask_texture = 'wizardIconColorMask'
    t.head_model = 'wizardHead'
    t.torso_model = 'wizardTorso'
    t.pelvis_model = 'wizardPelvis'
    t.upper_arm_model = 'wizardUpperArm'
    t.forearm_model = 'wizardForeArm'
    t.hand_model = 'wizardHand'
    t.upper_leg_model = 'wizardUpperLeg'
    t.lower_leg_model = 'wizardLowerLeg'
    t.toes_model = 'wizardToes'
    wizard_sounds = ['wizard1', 'wizard2', 'wizard3', 'wizard4']
    wizard_hit_sounds = ['wizardHit1', 'wizardHit2']
    t.attack_sounds = wizard_sounds
    t.jump_sounds = wizard_sounds
    t.impact_sounds = wizard_hit_sounds
    t.death_sounds = ['wizardDeath']
    t.pickup_sounds = wizard_sounds
    t.fall_sounds = ['wizardFall']
    t.style = 'spaz'

    # Cowboy ###################################
    t = Appearance('Butch')
    t.color_texture = 'cowboyColor'
    t.color_mask_texture = 'cowboyColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'cowboyIcon'
    t.icon_mask_texture = 'cowboyIconColorMask'
    t.head_model = 'cowboyHead'
    t.torso_model = 'cowboyTorso'
    t.pelvis_model = 'cowboyPelvis'
    t.upper_arm_model = 'cowboyUpperArm'
    t.forearm_model = 'cowboyForeArm'
    t.hand_model = 'cowboyHand'
    t.upper_leg_model = 'cowboyUpperLeg'
    t.lower_leg_model = 'cowboyLowerLeg'
    t.toes_model = 'cowboyToes'
    cowboy_sounds = ['cowboy1', 'cowboy2', 'cowboy3', 'cowboy4']
    cowboy_hit_sounds = ['cowboyHit1', 'cowboyHit2']
    t.attack_sounds = cowboy_sounds
    t.jump_sounds = cowboy_sounds
    t.impact_sounds = cowboy_hit_sounds
    t.death_sounds = ['cowboyDeath']
    t.pickup_sounds = cowboy_sounds
    t.fall_sounds = ['cowboyFall']
    t.style = 'spaz'

    # Witch ###################################
    t = Appearance('Witch')
    t.color_texture = 'witchColor'
    t.color_mask_texture = 'witchColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'witchIcon'
    t.icon_mask_texture = 'witchIconColorMask'
    t.head_model = 'witchHead'
    t.torso_model = 'witchTorso'
    t.pelvis_model = 'witchPelvis'
    t.upper_arm_model = 'witchUpperArm'
    t.forearm_model = 'witchForeArm'
    t.hand_model = 'witchHand'
    t.upper_leg_model = 'witchUpperLeg'
    t.lower_leg_model = 'witchLowerLeg'
    t.toes_model = 'witchToes'
    witch_sounds = ['witch1', 'witch2', 'witch3', 'witch4']
    witch_hit_sounds = ['witchHit1', 'witchHit2']
    t.attack_sounds = witch_sounds
    t.jump_sounds = witch_sounds
    t.impact_sounds = witch_hit_sounds
    t.death_sounds = ['witchDeath']
    t.pickup_sounds = witch_sounds
    t.fall_sounds = ['witchFall']
    t.style = 'spaz'

    # Warrior ###################################
    t = Appearance('Warrior')
    t.color_texture = 'warriorColor'
    t.color_mask_texture = 'warriorColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'warriorIcon'
    t.icon_mask_texture = 'warriorIconColorMask'
    t.head_model = 'warriorHead'
    t.torso_model = 'warriorTorso'
    t.pelvis_model = 'warriorPelvis'
    t.upper_arm_model = 'warriorUpperArm'
    t.forearm_model = 'warriorForeArm'
    t.hand_model = 'warriorHand'
    t.upper_leg_model = 'warriorUpperLeg'
    t.lower_leg_model = 'warriorLowerLeg'
    t.toes_model = 'warriorToes'
    warrior_sounds = ['warrior1', 'warrior2', 'warrior3', 'warrior4']
    warrior_hit_sounds = ['warriorHit1', 'warriorHit2']
    t.attack_sounds = warrior_sounds
    t.jump_sounds = warrior_sounds
    t.impact_sounds = warrior_hit_sounds
    t.death_sounds = ['warriorDeath']
    t.pickup_sounds = warrior_sounds
    t.fall_sounds = ['warriorFall']
    t.style = 'spaz'

    # Superhero ###################################
    t = Appearance('Middle-Man')
    t.color_texture = 'superheroColor'
    t.color_mask_texture = 'superheroColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'superheroIcon'
    t.icon_mask_texture = 'superheroIconColorMask'
    t.head_model = 'superheroHead'
    t.torso_model = 'superheroTorso'
    t.pelvis_model = 'superheroPelvis'
    t.upper_arm_model = 'superheroUpperArm'
    t.forearm_model = 'superheroForeArm'
    t.hand_model = 'superheroHand'
    t.upper_leg_model = 'superheroUpperLeg'
    t.lower_leg_model = 'superheroLowerLeg'
    t.toes_model = 'superheroToes'
    superhero_sounds = ['superhero1', 'superhero2', 'superhero3', 'superhero4']
    superhero_hit_sounds = ['superheroHit1', 'superheroHit2']
    t.attack_sounds = superhero_sounds
    t.jump_sounds = superhero_sounds
    t.impact_sounds = superhero_hit_sounds
    t.death_sounds = ['superheroDeath']
    t.pickup_sounds = superhero_sounds
    t.fall_sounds = ['superheroFall']
    t.style = 'spaz'

    # Alien ###################################
    t = Appearance('Alien')
    t.color_texture = 'alienColor'
    t.color_mask_texture = 'alienColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'alienIcon'
    t.icon_mask_texture = 'alienIconColorMask'
    t.head_model = 'alienHead'
    t.torso_model = 'alienTorso'
    t.pelvis_model = 'alienPelvis'
    t.upper_arm_model = 'alienUpperArm'
    t.forearm_model = 'alienForeArm'
    t.hand_model = 'alienHand'
    t.upper_leg_model = 'alienUpperLeg'
    t.lower_leg_model = 'alienLowerLeg'
    t.toes_model = 'alienToes'
    alien_sounds = ['alien1', 'alien2', 'alien3', 'alien4']
    alien_hit_sounds = ['alienHit1', 'alienHit2']
    t.attack_sounds = alien_sounds
    t.jump_sounds = alien_sounds
    t.impact_sounds = alien_hit_sounds
    t.death_sounds = ['alienDeath']
    t.pickup_sounds = alien_sounds
    t.fall_sounds = ['alienFall']
    t.style = 'spaz'

    # OldLady ###################################
    t = Appearance('OldLady')
    t.color_texture = 'oldLadyColor'
    t.color_mask_texture = 'oldLadyColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'oldLadyIcon'
    t.icon_mask_texture = 'oldLadyIconColorMask'
    t.head_model = 'oldLadyHead'
    t.torso_model = 'oldLadyTorso'
    t.pelvis_model = 'oldLadyPelvis'
    t.upper_arm_model = 'oldLadyUpperArm'
    t.forearm_model = 'oldLadyForeArm'
    t.hand_model = 'oldLadyHand'
    t.upper_leg_model = 'oldLadyUpperLeg'
    t.lower_leg_model = 'oldLadyLowerLeg'
    t.toes_model = 'oldLadyToes'
    old_lady_sounds = ['oldLady1', 'oldLady2', 'oldLady3', 'oldLady4']
    old_lady_hit_sounds = ['oldLadyHit1', 'oldLadyHit2']
    t.attack_sounds = old_lady_sounds
    t.jump_sounds = old_lady_sounds
    t.impact_sounds = old_lady_hit_sounds
    t.death_sounds = ['oldLadyDeath']
    t.pickup_sounds = old_lady_sounds
    t.fall_sounds = ['oldLadyFall']
    t.style = 'spaz'

    # Gladiator ###################################
    t = Appearance('Gladiator')
    t.color_texture = 'gladiatorColor'
    t.color_mask_texture = 'gladiatorColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'gladiatorIcon'
    t.icon_mask_texture = 'gladiatorIconColorMask'
    t.head_model = 'gladiatorHead'
    t.torso_model = 'gladiatorTorso'
    t.pelvis_model = 'gladiatorPelvis'
    t.upper_arm_model = 'gladiatorUpperArm'
    t.forearm_model = 'gladiatorForeArm'
    t.hand_model = 'gladiatorHand'
    t.upper_leg_model = 'gladiatorUpperLeg'
    t.lower_leg_model = 'gladiatorLowerLeg'
    t.toes_model = 'gladiatorToes'
    gladiator_sounds = ['gladiator1', 'gladiator2', 'gladiator3', 'gladiator4']
    gladiator_hit_sounds = ['gladiatorHit1', 'gladiatorHit2']
    t.attack_sounds = gladiator_sounds
    t.jump_sounds = gladiator_sounds
    t.impact_sounds = gladiator_hit_sounds
    t.death_sounds = ['gladiatorDeath']
    t.pickup_sounds = gladiator_sounds
    t.fall_sounds = ['gladiatorFall']
    t.style = 'spaz'

    # Wrestler ###################################
    t = Appearance('Wrestler')
    t.color_texture = 'wrestlerColor'
    t.color_mask_texture = 'wrestlerColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'wrestlerIcon'
    t.icon_mask_texture = 'wrestlerIconColorMask'
    t.head_model = 'wrestlerHead'
    t.torso_model = 'wrestlerTorso'
    t.pelvis_model = 'wrestlerPelvis'
    t.upper_arm_model = 'wrestlerUpperArm'
    t.forearm_model = 'wrestlerForeArm'
    t.hand_model = 'wrestlerHand'
    t.upper_leg_model = 'wrestlerUpperLeg'
    t.lower_leg_model = 'wrestlerLowerLeg'
    t.toes_model = 'wrestlerToes'
    wrestler_sounds = ['wrestler1', 'wrestler2', 'wrestler3', 'wrestler4']
    wrestler_hit_sounds = ['wrestlerHit1', 'wrestlerHit2']
    t.attack_sounds = wrestler_sounds
    t.jump_sounds = wrestler_sounds
    t.impact_sounds = wrestler_hit_sounds
    t.death_sounds = ['wrestlerDeath']
    t.pickup_sounds = wrestler_sounds
    t.fall_sounds = ['wrestlerFall']
    t.style = 'spaz'

    # OperaSinger ###################################
    t = Appearance('Gretel')
    t.color_texture = 'operaSingerColor'
    t.color_mask_texture = 'operaSingerColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'operaSingerIcon'
    t.icon_mask_texture = 'operaSingerIconColorMask'
    t.head_model = 'operaSingerHead'
    t.torso_model = 'operaSingerTorso'
    t.pelvis_model = 'operaSingerPelvis'
    t.upper_arm_model = 'operaSingerUpperArm'
    t.forearm_model = 'operaSingerForeArm'
    t.hand_model = 'operaSingerHand'
    t.upper_leg_model = 'operaSingerUpperLeg'
    t.lower_leg_model = 'operaSingerLowerLeg'
    t.toes_model = 'operaSingerToes'
    opera_singer_sounds = [
        'operaSinger1', 'operaSinger2', 'operaSinger3', 'operaSinger4'
    ]
    opera_singer_hit_sounds = ['operaSingerHit1', 'operaSingerHit2']
    t.attack_sounds = opera_singer_sounds
    t.jump_sounds = opera_singer_sounds
    t.impact_sounds = opera_singer_hit_sounds
    t.death_sounds = ['operaSingerDeath']
    t.pickup_sounds = opera_singer_sounds
    t.fall_sounds = ['operaSingerFall']
    t.style = 'spaz'

    # Pixie ###################################
    t = Appearance('Pixel')
    t.color_texture = 'pixieColor'
    t.color_mask_texture = 'pixieColorMask'
    t.default_color = (0, 1, 0.7)
    t.default_highlight = (0.65, 0.35, 0.75)
    t.icon_texture = 'pixieIcon'
    t.icon_mask_texture = 'pixieIconColorMask'
    t.head_model = 'pixieHead'
    t.torso_model = 'pixieTorso'
    t.pelvis_model = 'pixiePelvis'
    t.upper_arm_model = 'pixieUpperArm'
    t.forearm_model = 'pixieForeArm'
    t.hand_model = 'pixieHand'
    t.upper_leg_model = 'pixieUpperLeg'
    t.lower_leg_model = 'pixieLowerLeg'
    t.toes_model = 'pixieToes'
    pixie_sounds = ['pixie1', 'pixie2', 'pixie3', 'pixie4']
    pixie_hit_sounds = ['pixieHit1', 'pixieHit2']
    t.attack_sounds = pixie_sounds
    t.jump_sounds = pixie_sounds
    t.impact_sounds = pixie_hit_sounds
    t.death_sounds = ['pixieDeath']
    t.pickup_sounds = pixie_sounds
    t.fall_sounds = ['pixieFall']
    t.style = 'pixie'

    # Robot ###################################
    t = Appearance('Robot')
    t.color_texture = 'robotColor'
    t.color_mask_texture = 'robotColorMask'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)
    t.icon_texture = 'robotIcon'
    t.icon_mask_texture = 'robotIconColorMask'
    t.head_model = 'robotHead'
    t.torso_model = 'robotTorso'
    t.pelvis_model = 'robotPelvis'
    t.upper_arm_model = 'robotUpperArm'
    t.forearm_model = 'robotForeArm'
    t.hand_model = 'robotHand'
    t.upper_leg_model = 'robotUpperLeg'
    t.lower_leg_model = 'robotLowerLeg'
    t.toes_model = 'robotToes'
    robot_sounds = ['robot1', 'robot2', 'robot3', 'robot4']
    robot_hit_sounds = ['robotHit1', 'robotHit2']
    t.attack_sounds = robot_sounds
    t.jump_sounds = robot_sounds
    t.impact_sounds = robot_hit_sounds
    t.death_sounds = ['robotDeath']
    t.pickup_sounds = robot_sounds
    t.fall_sounds = ['robotFall']
    t.style = 'spaz'

    # Bunny ###################################
    t = Appearance('Easter Bunny')
    t.color_texture = 'bunnyColor'
    t.color_mask_texture = 'bunnyColorMask'
    t.default_color = (1, 1, 1)
    t.default_highlight = (1, 0.5, 0.5)
    t.icon_texture = 'bunnyIcon'
    t.icon_mask_texture = 'bunnyIconColorMask'
    t.head_model = 'bunnyHead'
    t.torso_model = 'bunnyTorso'
    t.pelvis_model = 'bunnyPelvis'
    t.upper_arm_model = 'bunnyUpperArm'
    t.forearm_model = 'bunnyForeArm'
    t.hand_model = 'bunnyHand'
    t.upper_leg_model = 'bunnyUpperLeg'
    t.lower_leg_model = 'bunnyLowerLeg'
    t.toes_model = 'bunnyToes'
    bunny_sounds = ['bunny1', 'bunny2', 'bunny3', 'bunny4']
    bunny_hit_sounds = ['bunnyHit1', 'bunnyHit2']
    t.attack_sounds = bunny_sounds
    t.jump_sounds = ['bunnyJump']
    t.impact_sounds = bunny_hit_sounds
    t.death_sounds = ['bunnyDeath']
    t.pickup_sounds = bunny_sounds
    t.fall_sounds = ['bunnyFall']
    t.style = 'bunny'
