# Released under the MIT License. See LICENSE for details.
#
"""Appearance functionality for spazzes."""
from __future__ import annotations

import bascenev1 as bs


def get_appearances(include_locked: bool = False) -> list[str]:
    """Get the list of available spaz appearances."""
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    plus = bs.app.plus
    assert plus is not None

    assert bs.app.classic is not None

    purchases = bs.app.classic.purchases

    disallowed = []
    if not include_locked:
        # Hmm yeah this'll be tough to hack...
        if 'characters.santa' not in purchases:
            disallowed.append('Santa Claus')
        if 'characters.frosty' not in purchases:
            disallowed.append('Frosty')
        if 'characters.bones' not in purchases:
            disallowed.append('Bones')
        if 'characters.bernard' not in purchases:
            disallowed.append('Bernard')
        if 'characters.pixie' not in purchases:
            disallowed.append('Pixel')
        if 'characters.pascal' not in purchases:
            disallowed.append('Pascal')
        if 'characters.actionhero' not in purchases:
            disallowed.append('Todd McBurton')
        if 'characters.taobaomascot' not in purchases:
            disallowed.append('Taobao Mascot')
        if 'characters.agent' not in purchases:
            disallowed.append('Agent Johnson')
        if 'characters.jumpsuit' not in purchases:
            disallowed.append('Lee')
        if 'characters.assassin' not in purchases:
            disallowed.append('Zola')
        if 'characters.wizard' not in purchases:
            disallowed.append('Grumbledorf')
        if 'characters.cowboy' not in purchases:
            disallowed.append('Butch')
        if 'characters.witch' not in purchases:
            disallowed.append('Witch')
        if 'characters.warrior' not in purchases:
            disallowed.append('Warrior')
        if 'characters.superhero' not in purchases:
            disallowed.append('Middle-Man')
        if 'characters.alien' not in purchases:
            disallowed.append('Alien')
        if 'characters.oldlady' not in purchases:
            disallowed.append('OldLady')
        if 'characters.gladiator' not in purchases:
            disallowed.append('Gladiator')
        if 'characters.wrestler' not in purchases:
            disallowed.append('Wrestler')
        if 'characters.operasinger' not in purchases:
            disallowed.append('Gretel')
        if 'characters.robot' not in purchases:
            disallowed.append('Robot')
        if 'characters.cyborg' not in purchases:
            disallowed.append('B-9000')
        if 'characters.bunny' not in purchases:
            disallowed.append('Easter Bunny')
        if 'characters.kronk' not in purchases:
            disallowed.append('Kronk')
        if 'characters.zoe' not in purchases:
            disallowed.append('Zoe')
        if 'characters.jackmorgan' not in purchases:
            disallowed.append('Jack Morgan')
        if 'characters.mel' not in purchases:
            disallowed.append('Mel')
        if 'characters.snakeshadow' not in purchases:
            disallowed.append('Snake Shadow')
    return [
        s
        for s in list(bs.app.classic.spaz_appearances.keys())
        if s not in disallowed
    ]


class Appearance:
    """Create and fill out one of these suckers to define a spaz appearance."""

    def __init__(self, name: str):
        assert bs.app.classic is not None
        self.name = name
        if self.name in bs.app.classic.spaz_appearances:
            raise RuntimeError(
                f'spaz appearance name "{self.name}" already exists.'
            )
        bs.app.classic.spaz_appearances[self.name] = self
        self.color_texture = ''
        self.color_mask_texture = ''
        self.icon_texture = ''
        self.icon_mask_texture = ''
        self.head_mesh = ''
        self.torso_mesh = ''
        self.pelvis_mesh = ''
        self.upper_arm_mesh = ''
        self.forearm_mesh = ''
        self.hand_mesh = ''
        self.upper_leg_mesh = ''
        self.lower_leg_mesh = ''
        self.toes_mesh = ''
        self.jump_sounds: list[str] = []
        self.attack_sounds: list[str] = []
        self.impact_sounds: list[str] = []
        self.death_sounds: list[str] = []
        self.pickup_sounds: list[str] = []
        self.fall_sounds: list[str] = []
        self.style = 'spaz'
        self.default_color: tuple[float, float, float] | None = None
        self.default_highlight: tuple[float, float, float] | None = None


def register_appearances() -> None:
    """Register our builtin spaz appearances."""

    # This is quite ugly but will be going away so not worth cleaning up.
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    # Spaz #######################################
    t = Appearance('Spaz')
    t.color_texture = 'neoSpazColor'
    t.color_mask_texture = 'neoSpazColorMask'
    t.icon_texture = 'neoSpazIcon'
    t.icon_mask_texture = 'neoSpazIconColorMask'
    t.head_mesh = 'neoSpazHead'
    t.torso_mesh = 'neoSpazTorso'
    t.pelvis_mesh = 'neoSpazPelvis'
    t.upper_arm_mesh = 'neoSpazUpperArm'
    t.forearm_mesh = 'neoSpazForeArm'
    t.hand_mesh = 'neoSpazHand'
    t.upper_leg_mesh = 'neoSpazUpperLeg'
    t.lower_leg_mesh = 'neoSpazLowerLeg'
    t.toes_mesh = 'neoSpazToes'
    t.jump_sounds = ['spazJump01', 'spazJump02', 'spazJump03', 'spazJump04']
    t.attack_sounds = [
        'spazAttack01',
        'spazAttack02',
        'spazAttack03',
        'spazAttack04',
    ]
    t.impact_sounds = [
        'spazImpact01',
        'spazImpact02',
        'spazImpact03',
        'spazImpact04',
    ]
    t.death_sounds = ['spazDeath01']
    t.pickup_sounds = ['spazPickup01']
    t.fall_sounds = ['spazFall01']
    t.style = 'spaz'

    # Zoe #####################################
    t = Appearance('Zoe')
    t.color_texture = 'zoeColor'
    t.color_mask_texture = 'zoeColorMask'
    t.icon_texture = 'zoeIcon'
    t.icon_mask_texture = 'zoeIconColorMask'
    t.head_mesh = 'zoeHead'
    t.torso_mesh = 'zoeTorso'
    t.pelvis_mesh = 'zoePelvis'
    t.upper_arm_mesh = 'zoeUpperArm'
    t.forearm_mesh = 'zoeForeArm'
    t.hand_mesh = 'zoeHand'
    t.upper_leg_mesh = 'zoeUpperLeg'
    t.lower_leg_mesh = 'zoeLowerLeg'
    t.toes_mesh = 'zoeToes'
    t.jump_sounds = ['zoeJump01', 'zoeJump02', 'zoeJump03']
    t.attack_sounds = [
        'zoeAttack01',
        'zoeAttack02',
        'zoeAttack03',
        'zoeAttack04',
    ]
    t.impact_sounds = [
        'zoeImpact01',
        'zoeImpact02',
        'zoeImpact03',
        'zoeImpact04',
    ]
    t.death_sounds = ['zoeDeath01']
    t.pickup_sounds = ['zoePickup01']
    t.fall_sounds = ['zoeFall01']
    t.style = 'female'
    t.default_color = (0.6, 0.6, 0.6)
    t.default_highlight = (0, 1, 0)

    # Ninja ##########################################
    t = Appearance('Snake Shadow')
    t.color_texture = 'ninjaColor'
    t.color_mask_texture = 'ninjaColorMask'
    t.icon_texture = 'ninjaIcon'
    t.icon_mask_texture = 'ninjaIconColorMask'
    t.head_mesh = 'ninjaHead'
    t.torso_mesh = 'ninjaTorso'
    t.pelvis_mesh = 'ninjaPelvis'
    t.upper_arm_mesh = 'ninjaUpperArm'
    t.forearm_mesh = 'ninjaForeArm'
    t.hand_mesh = 'ninjaHand'
    t.upper_leg_mesh = 'ninjaUpperLeg'
    t.lower_leg_mesh = 'ninjaLowerLeg'
    t.toes_mesh = 'ninjaToes'
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
    t.default_color = (1, 1, 1)
    t.default_highlight = (0.55, 0.8, 0.55)

    # Barbarian #####################################
    t = Appearance('Kronk')
    t.color_texture = 'kronk'
    t.color_mask_texture = 'kronkColorMask'
    t.icon_texture = 'kronkIcon'
    t.icon_mask_texture = 'kronkIconColorMask'
    t.head_mesh = 'kronkHead'
    t.torso_mesh = 'kronkTorso'
    t.pelvis_mesh = 'kronkPelvis'
    t.upper_arm_mesh = 'kronkUpperArm'
    t.forearm_mesh = 'kronkForeArm'
    t.hand_mesh = 'kronkHand'
    t.upper_leg_mesh = 'kronkUpperLeg'
    t.lower_leg_mesh = 'kronkLowerLeg'
    t.toes_mesh = 'kronkToes'
    kronk_sounds = [
        'kronk1',
        'kronk2',
        'kronk3',
        'kronk4',
        'kronk5',
        'kronk6',
        'kronk7',
        'kronk8',
        'kronk9',
        'kronk10',
    ]
    t.jump_sounds = kronk_sounds
    t.attack_sounds = kronk_sounds
    t.impact_sounds = kronk_sounds
    t.death_sounds = ['kronkDeath']
    t.pickup_sounds = kronk_sounds
    t.fall_sounds = ['kronkFall']
    t.style = 'kronk'
    t.default_color = (0.4, 0.5, 0.4)
    t.default_highlight = (1, 0.5, 0.3)

    # Chef ###########################################
    t = Appearance('Mel')
    t.color_texture = 'melColor'
    t.color_mask_texture = 'melColorMask'
    t.icon_texture = 'melIcon'
    t.icon_mask_texture = 'melIconColorMask'
    t.head_mesh = 'melHead'
    t.torso_mesh = 'melTorso'
    t.pelvis_mesh = 'kronkPelvis'
    t.upper_arm_mesh = 'melUpperArm'
    t.forearm_mesh = 'melForeArm'
    t.hand_mesh = 'melHand'
    t.upper_leg_mesh = 'melUpperLeg'
    t.lower_leg_mesh = 'melLowerLeg'
    t.toes_mesh = 'melToes'
    mel_sounds = [
        'mel01',
        'mel02',
        'mel03',
        'mel04',
        'mel05',
        'mel06',
        'mel07',
        'mel08',
        'mel09',
        'mel10',
    ]
    t.jump_sounds = mel_sounds
    t.attack_sounds = mel_sounds
    t.impact_sounds = mel_sounds
    t.death_sounds = ['melDeath01']
    t.pickup_sounds = mel_sounds
    t.fall_sounds = ['melFall01']
    t.style = 'mel'
    t.default_color = (1, 1, 1)
    t.default_highlight = (0.1, 0.6, 0.1)

    # Pirate #######################################
    t = Appearance('Jack Morgan')
    t.color_texture = 'jackColor'
    t.color_mask_texture = 'jackColorMask'
    t.icon_texture = 'jackIcon'
    t.icon_mask_texture = 'jackIconColorMask'
    t.head_mesh = 'jackHead'
    t.torso_mesh = 'jackTorso'
    t.pelvis_mesh = 'kronkPelvis'
    t.upper_arm_mesh = 'jackUpperArm'
    t.forearm_mesh = 'jackForeArm'
    t.hand_mesh = 'jackHand'
    t.upper_leg_mesh = 'jackUpperLeg'
    t.lower_leg_mesh = 'jackLowerLeg'
    t.toes_mesh = 'jackToes'
    hit_sounds = [
        'jackHit01',
        'jackHit02',
        'jackHit03',
        'jackHit04',
        'jackHit05',
        'jackHit06',
        'jackHit07',
    ]
    sounds = ['jack01', 'jack02', 'jack03', 'jack04', 'jack05', 'jack06']
    t.jump_sounds = sounds
    t.attack_sounds = sounds
    t.impact_sounds = hit_sounds
    t.death_sounds = ['jackDeath01']
    t.pickup_sounds = sounds
    t.fall_sounds = ['jackFall01']
    t.style = 'pirate'
    t.default_color = (1, 0.2, 0.1)
    t.default_highlight = (1, 1, 0)

    # Santa ######################################
    t = Appearance('Santa Claus')
    t.color_texture = 'santaColor'
    t.color_mask_texture = 'santaColorMask'
    t.icon_texture = 'santaIcon'
    t.icon_mask_texture = 'santaIconColorMask'
    t.head_mesh = 'santaHead'
    t.torso_mesh = 'santaTorso'
    t.pelvis_mesh = 'kronkPelvis'
    t.upper_arm_mesh = 'santaUpperArm'
    t.forearm_mesh = 'santaForeArm'
    t.hand_mesh = 'santaHand'
    t.upper_leg_mesh = 'santaUpperLeg'
    t.lower_leg_mesh = 'santaLowerLeg'
    t.toes_mesh = 'santaToes'
    hit_sounds = ['santaHit01', 'santaHit02', 'santaHit03', 'santaHit04']
    sounds = ['santa01', 'santa02', 'santa03', 'santa04', 'santa05']
    t.jump_sounds = sounds
    t.attack_sounds = sounds
    t.impact_sounds = hit_sounds
    t.death_sounds = ['santaDeath']
    t.pickup_sounds = sounds
    t.fall_sounds = ['santaFall']
    t.style = 'santa'
    t.default_color = (1, 0, 0)
    t.default_highlight = (1, 1, 1)

    # Snowman ###################################
    t = Appearance('Frosty')
    t.color_texture = 'frostyColor'
    t.color_mask_texture = 'frostyColorMask'
    t.icon_texture = 'frostyIcon'
    t.icon_mask_texture = 'frostyIconColorMask'
    t.head_mesh = 'frostyHead'
    t.torso_mesh = 'frostyTorso'
    t.pelvis_mesh = 'frostyPelvis'
    t.upper_arm_mesh = 'frostyUpperArm'
    t.forearm_mesh = 'frostyForeArm'
    t.hand_mesh = 'frostyHand'
    t.upper_leg_mesh = 'frostyUpperLeg'
    t.lower_leg_mesh = 'frostyLowerLeg'
    t.toes_mesh = 'frostyToes'
    frosty_sounds = ['frosty01', 'frosty02', 'frosty03', 'frosty04', 'frosty05']
    frosty_hit_sounds = ['frostyHit01', 'frostyHit02', 'frostyHit03']
    t.jump_sounds = frosty_sounds
    t.attack_sounds = frosty_sounds
    t.impact_sounds = frosty_hit_sounds
    t.death_sounds = ['frostyDeath']
    t.pickup_sounds = frosty_sounds
    t.fall_sounds = ['frostyFall']
    t.style = 'frosty'
    t.default_color = (0.5, 0.5, 1)
    t.default_highlight = (1, 0.5, 0)

    # Skeleton ################################
    t = Appearance('Bones')
    t.color_texture = 'bonesColor'
    t.color_mask_texture = 'bonesColorMask'
    t.icon_texture = 'bonesIcon'
    t.icon_mask_texture = 'bonesIconColorMask'
    t.head_mesh = 'bonesHead'
    t.torso_mesh = 'bonesTorso'
    t.pelvis_mesh = 'bonesPelvis'
    t.upper_arm_mesh = 'bonesUpperArm'
    t.forearm_mesh = 'bonesForeArm'
    t.hand_mesh = 'bonesHand'
    t.upper_leg_mesh = 'bonesUpperLeg'
    t.lower_leg_mesh = 'bonesLowerLeg'
    t.toes_mesh = 'bonesToes'
    bones_sounds = ['bones1', 'bones2', 'bones3']
    bones_hit_sounds = ['bones1', 'bones2', 'bones3']
    t.jump_sounds = bones_sounds
    t.attack_sounds = bones_sounds
    t.impact_sounds = bones_hit_sounds
    t.death_sounds = ['bonesDeath']
    t.pickup_sounds = bones_sounds
    t.fall_sounds = ['bonesFall']
    t.style = 'bones'
    t.default_color = (0.6, 0.9, 1)
    t.default_highlight = (0.6, 0.9, 1)

    # Bear ###################################
    t = Appearance('Bernard')
    t.color_texture = 'bearColor'
    t.color_mask_texture = 'bearColorMask'
    t.icon_texture = 'bearIcon'
    t.icon_mask_texture = 'bearIconColorMask'
    t.head_mesh = 'bearHead'
    t.torso_mesh = 'bearTorso'
    t.pelvis_mesh = 'bearPelvis'
    t.upper_arm_mesh = 'bearUpperArm'
    t.forearm_mesh = 'bearForeArm'
    t.hand_mesh = 'bearHand'
    t.upper_leg_mesh = 'bearUpperLeg'
    t.lower_leg_mesh = 'bearLowerLeg'
    t.toes_mesh = 'bearToes'
    bear_sounds = ['bear1', 'bear2', 'bear3', 'bear4']
    bear_hit_sounds = ['bearHit1', 'bearHit2']
    t.jump_sounds = bear_sounds
    t.attack_sounds = bear_sounds
    t.impact_sounds = bear_hit_sounds
    t.death_sounds = ['bearDeath']
    t.pickup_sounds = bear_sounds
    t.fall_sounds = ['bearFall']
    t.style = 'bear'
    t.default_color = (0.7, 0.5, 0.0)

    # Penguin ###################################
    t = Appearance('Pascal')
    t.color_texture = 'penguinColor'
    t.color_mask_texture = 'penguinColorMask'
    t.icon_texture = 'penguinIcon'
    t.icon_mask_texture = 'penguinIconColorMask'
    t.head_mesh = 'penguinHead'
    t.torso_mesh = 'penguinTorso'
    t.pelvis_mesh = 'penguinPelvis'
    t.upper_arm_mesh = 'penguinUpperArm'
    t.forearm_mesh = 'penguinForeArm'
    t.hand_mesh = 'penguinHand'
    t.upper_leg_mesh = 'penguinUpperLeg'
    t.lower_leg_mesh = 'penguinLowerLeg'
    t.toes_mesh = 'penguinToes'
    penguin_sounds = ['penguin1', 'penguin2', 'penguin3', 'penguin4']
    penguin_hit_sounds = ['penguinHit1', 'penguinHit2']
    t.jump_sounds = penguin_sounds
    t.attack_sounds = penguin_sounds
    t.impact_sounds = penguin_hit_sounds
    t.death_sounds = ['penguinDeath']
    t.pickup_sounds = penguin_sounds
    t.fall_sounds = ['penguinFall']
    t.style = 'penguin'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # Ali ###################################
    t = Appearance('Taobao Mascot')
    t.color_texture = 'aliColor'
    t.color_mask_texture = 'aliColorMask'
    t.icon_texture = 'aliIcon'
    t.icon_mask_texture = 'aliIconColorMask'
    t.head_mesh = 'aliHead'
    t.torso_mesh = 'aliTorso'
    t.pelvis_mesh = 'aliPelvis'
    t.upper_arm_mesh = 'aliUpperArm'
    t.forearm_mesh = 'aliForeArm'
    t.hand_mesh = 'aliHand'
    t.upper_leg_mesh = 'aliUpperLeg'
    t.lower_leg_mesh = 'aliLowerLeg'
    t.toes_mesh = 'aliToes'
    ali_sounds = ['ali1', 'ali2', 'ali3', 'ali4']
    ali_hit_sounds = ['aliHit1', 'aliHit2']
    t.jump_sounds = ali_sounds
    t.attack_sounds = ali_sounds
    t.impact_sounds = ali_hit_sounds
    t.death_sounds = ['aliDeath']
    t.pickup_sounds = ali_sounds
    t.fall_sounds = ['aliFall']
    t.style = 'ali'
    t.default_color = (1, 0.5, 0)
    t.default_highlight = (1, 1, 1)

    # Cyborg ###################################
    t = Appearance('B-9000')
    t.color_texture = 'cyborgColor'
    t.color_mask_texture = 'cyborgColorMask'
    t.icon_texture = 'cyborgIcon'
    t.icon_mask_texture = 'cyborgIconColorMask'
    t.head_mesh = 'cyborgHead'
    t.torso_mesh = 'cyborgTorso'
    t.pelvis_mesh = 'cyborgPelvis'
    t.upper_arm_mesh = 'cyborgUpperArm'
    t.forearm_mesh = 'cyborgForeArm'
    t.hand_mesh = 'cyborgHand'
    t.upper_leg_mesh = 'cyborgUpperLeg'
    t.lower_leg_mesh = 'cyborgLowerLeg'
    t.toes_mesh = 'cyborgToes'
    cyborg_sounds = ['cyborg1', 'cyborg2', 'cyborg3', 'cyborg4']
    cyborg_hit_sounds = ['cyborgHit1', 'cyborgHit2']
    t.jump_sounds = cyborg_sounds
    t.attack_sounds = cyborg_sounds
    t.impact_sounds = cyborg_hit_sounds
    t.death_sounds = ['cyborgDeath']
    t.pickup_sounds = cyborg_sounds
    t.fall_sounds = ['cyborgFall']
    t.style = 'cyborg'
    t.default_color = (0.5, 0.5, 0.5)
    t.default_highlight = (1, 0, 0)

    # Agent ###################################
    t = Appearance('Agent Johnson')
    t.color_texture = 'agentColor'
    t.color_mask_texture = 'agentColorMask'
    t.icon_texture = 'agentIcon'
    t.icon_mask_texture = 'agentIconColorMask'
    t.head_mesh = 'agentHead'
    t.torso_mesh = 'agentTorso'
    t.pelvis_mesh = 'agentPelvis'
    t.upper_arm_mesh = 'agentUpperArm'
    t.forearm_mesh = 'agentForeArm'
    t.hand_mesh = 'agentHand'
    t.upper_leg_mesh = 'agentUpperLeg'
    t.lower_leg_mesh = 'agentLowerLeg'
    t.toes_mesh = 'agentToes'
    agent_sounds = ['agent1', 'agent2', 'agent3', 'agent4']
    agent_hit_sounds = ['agentHit1', 'agentHit2']
    t.jump_sounds = agent_sounds
    t.attack_sounds = agent_sounds
    t.impact_sounds = agent_hit_sounds
    t.death_sounds = ['agentDeath']
    t.pickup_sounds = agent_sounds
    t.fall_sounds = ['agentFall']
    t.style = 'agent'
    t.default_color = (0.3, 0.3, 0.33)
    t.default_highlight = (1, 0.5, 0.3)

    # Jumpsuit ###################################
    t = Appearance('Lee')
    t.color_texture = 'jumpsuitColor'
    t.color_mask_texture = 'jumpsuitColorMask'
    t.icon_texture = 'jumpsuitIcon'
    t.icon_mask_texture = 'jumpsuitIconColorMask'
    t.head_mesh = 'jumpsuitHead'
    t.torso_mesh = 'jumpsuitTorso'
    t.pelvis_mesh = 'jumpsuitPelvis'
    t.upper_arm_mesh = 'jumpsuitUpperArm'
    t.forearm_mesh = 'jumpsuitForeArm'
    t.hand_mesh = 'jumpsuitHand'
    t.upper_leg_mesh = 'jumpsuitUpperLeg'
    t.lower_leg_mesh = 'jumpsuitLowerLeg'
    t.toes_mesh = 'jumpsuitToes'
    jumpsuit_sounds = ['jumpsuit1', 'jumpsuit2', 'jumpsuit3', 'jumpsuit4']
    jumpsuit_hit_sounds = ['jumpsuitHit1', 'jumpsuitHit2']
    t.jump_sounds = jumpsuit_sounds
    t.attack_sounds = jumpsuit_sounds
    t.impact_sounds = jumpsuit_hit_sounds
    t.death_sounds = ['jumpsuitDeath']
    t.pickup_sounds = jumpsuit_sounds
    t.fall_sounds = ['jumpsuitFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # ActionHero ###################################
    t = Appearance('Todd McBurton')
    t.color_texture = 'actionHeroColor'
    t.color_mask_texture = 'actionHeroColorMask'
    t.icon_texture = 'actionHeroIcon'
    t.icon_mask_texture = 'actionHeroIconColorMask'
    t.head_mesh = 'actionHeroHead'
    t.torso_mesh = 'actionHeroTorso'
    t.pelvis_mesh = 'actionHeroPelvis'
    t.upper_arm_mesh = 'actionHeroUpperArm'
    t.forearm_mesh = 'actionHeroForeArm'
    t.hand_mesh = 'actionHeroHand'
    t.upper_leg_mesh = 'actionHeroUpperLeg'
    t.lower_leg_mesh = 'actionHeroLowerLeg'
    t.toes_mesh = 'actionHeroToes'
    action_hero_sounds = [
        'actionHero1',
        'actionHero2',
        'actionHero3',
        'actionHero4',
    ]
    action_hero_hit_sounds = ['actionHeroHit1', 'actionHeroHit2']
    t.jump_sounds = action_hero_sounds
    t.attack_sounds = action_hero_sounds
    t.impact_sounds = action_hero_hit_sounds
    t.death_sounds = ['actionHeroDeath']
    t.pickup_sounds = action_hero_sounds
    t.fall_sounds = ['actionHeroFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # Assassin ###################################
    t = Appearance('Zola')
    t.color_texture = 'assassinColor'
    t.color_mask_texture = 'assassinColorMask'
    t.icon_texture = 'assassinIcon'
    t.icon_mask_texture = 'assassinIconColorMask'
    t.head_mesh = 'assassinHead'
    t.torso_mesh = 'assassinTorso'
    t.pelvis_mesh = 'assassinPelvis'
    t.upper_arm_mesh = 'assassinUpperArm'
    t.forearm_mesh = 'assassinForeArm'
    t.hand_mesh = 'assassinHand'
    t.upper_leg_mesh = 'assassinUpperLeg'
    t.lower_leg_mesh = 'assassinLowerLeg'
    t.toes_mesh = 'assassinToes'
    assassin_sounds = ['assassin1', 'assassin2', 'assassin3', 'assassin4']
    assassin_hit_sounds = ['assassinHit1', 'assassinHit2']
    t.jump_sounds = assassin_sounds
    t.attack_sounds = assassin_sounds
    t.impact_sounds = assassin_hit_sounds
    t.death_sounds = ['assassinDeath']
    t.pickup_sounds = assassin_sounds
    t.fall_sounds = ['assassinFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # Wizard ###################################
    t = Appearance('Grumbledorf')
    t.color_texture = 'wizardColor'
    t.color_mask_texture = 'wizardColorMask'
    t.icon_texture = 'wizardIcon'
    t.icon_mask_texture = 'wizardIconColorMask'
    t.head_mesh = 'wizardHead'
    t.torso_mesh = 'wizardTorso'
    t.pelvis_mesh = 'wizardPelvis'
    t.upper_arm_mesh = 'wizardUpperArm'
    t.forearm_mesh = 'wizardForeArm'
    t.hand_mesh = 'wizardHand'
    t.upper_leg_mesh = 'wizardUpperLeg'
    t.lower_leg_mesh = 'wizardLowerLeg'
    t.toes_mesh = 'wizardToes'
    wizard_sounds = ['wizard1', 'wizard2', 'wizard3', 'wizard4']
    wizard_hit_sounds = ['wizardHit1', 'wizardHit2']
    t.jump_sounds = wizard_sounds
    t.attack_sounds = wizard_sounds
    t.impact_sounds = wizard_hit_sounds
    t.death_sounds = ['wizardDeath']
    t.pickup_sounds = wizard_sounds
    t.fall_sounds = ['wizardFall']
    t.style = 'spaz'
    t.default_color = (0.2, 0.4, 1.0)
    t.default_highlight = (0.06, 0.15, 0.4)

    # Cowboy ###################################
    t = Appearance('Butch')
    t.color_texture = 'cowboyColor'
    t.color_mask_texture = 'cowboyColorMask'
    t.icon_texture = 'cowboyIcon'
    t.icon_mask_texture = 'cowboyIconColorMask'
    t.head_mesh = 'cowboyHead'
    t.torso_mesh = 'cowboyTorso'
    t.pelvis_mesh = 'cowboyPelvis'
    t.upper_arm_mesh = 'cowboyUpperArm'
    t.forearm_mesh = 'cowboyForeArm'
    t.hand_mesh = 'cowboyHand'
    t.upper_leg_mesh = 'cowboyUpperLeg'
    t.lower_leg_mesh = 'cowboyLowerLeg'
    t.toes_mesh = 'cowboyToes'
    cowboy_sounds = ['cowboy1', 'cowboy2', 'cowboy3', 'cowboy4']
    cowboy_hit_sounds = ['cowboyHit1', 'cowboyHit2']
    t.jump_sounds = cowboy_sounds
    t.attack_sounds = cowboy_sounds
    t.impact_sounds = cowboy_hit_sounds
    t.death_sounds = ['cowboyDeath']
    t.pickup_sounds = cowboy_sounds
    t.fall_sounds = ['cowboyFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # Witch ###################################
    t = Appearance('Witch')
    t.color_texture = 'witchColor'
    t.color_mask_texture = 'witchColorMask'
    t.icon_texture = 'witchIcon'
    t.icon_mask_texture = 'witchIconColorMask'
    t.head_mesh = 'witchHead'
    t.torso_mesh = 'witchTorso'
    t.pelvis_mesh = 'witchPelvis'
    t.upper_arm_mesh = 'witchUpperArm'
    t.forearm_mesh = 'witchForeArm'
    t.hand_mesh = 'witchHand'
    t.upper_leg_mesh = 'witchUpperLeg'
    t.lower_leg_mesh = 'witchLowerLeg'
    t.toes_mesh = 'witchToes'
    witch_sounds = ['witch1', 'witch2', 'witch3', 'witch4']
    witch_hit_sounds = ['witchHit1', 'witchHit2']
    t.jump_sounds = witch_sounds
    t.attack_sounds = witch_sounds
    t.impact_sounds = witch_hit_sounds
    t.death_sounds = ['witchDeath']
    t.pickup_sounds = witch_sounds
    t.fall_sounds = ['witchFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # Warrior ###################################
    t = Appearance('Warrior')
    t.color_texture = 'warriorColor'
    t.color_mask_texture = 'warriorColorMask'
    t.icon_texture = 'warriorIcon'
    t.icon_mask_texture = 'warriorIconColorMask'
    t.head_mesh = 'warriorHead'
    t.torso_mesh = 'warriorTorso'
    t.pelvis_mesh = 'warriorPelvis'
    t.upper_arm_mesh = 'warriorUpperArm'
    t.forearm_mesh = 'warriorForeArm'
    t.hand_mesh = 'warriorHand'
    t.upper_leg_mesh = 'warriorUpperLeg'
    t.lower_leg_mesh = 'warriorLowerLeg'
    t.toes_mesh = 'warriorToes'
    warrior_sounds = ['warrior1', 'warrior2', 'warrior3', 'warrior4']
    warrior_hit_sounds = ['warriorHit1', 'warriorHit2']
    t.jump_sounds = warrior_sounds
    t.attack_sounds = warrior_sounds
    t.impact_sounds = warrior_hit_sounds
    t.death_sounds = ['warriorDeath']
    t.pickup_sounds = warrior_sounds
    t.fall_sounds = ['warriorFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # Superhero ###################################
    t = Appearance('Middle-Man')
    t.color_texture = 'superheroColor'
    t.color_mask_texture = 'superheroColorMask'
    t.icon_texture = 'superheroIcon'
    t.icon_mask_texture = 'superheroIconColorMask'
    t.head_mesh = 'superheroHead'
    t.torso_mesh = 'superheroTorso'
    t.pelvis_mesh = 'superheroPelvis'
    t.upper_arm_mesh = 'superheroUpperArm'
    t.forearm_mesh = 'superheroForeArm'
    t.hand_mesh = 'superheroHand'
    t.upper_leg_mesh = 'superheroUpperLeg'
    t.lower_leg_mesh = 'superheroLowerLeg'
    t.toes_mesh = 'superheroToes'
    superhero_sounds = ['superhero1', 'superhero2', 'superhero3', 'superhero4']
    superhero_hit_sounds = ['superheroHit1', 'superheroHit2']
    t.jump_sounds = superhero_sounds
    t.attack_sounds = superhero_sounds
    t.impact_sounds = superhero_hit_sounds
    t.death_sounds = ['superheroDeath']
    t.pickup_sounds = superhero_sounds
    t.fall_sounds = ['superheroFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # Alien ###################################
    t = Appearance('Alien')
    t.color_texture = 'alienColor'
    t.color_mask_texture = 'alienColorMask'
    t.icon_texture = 'alienIcon'
    t.icon_mask_texture = 'alienIconColorMask'
    t.head_mesh = 'alienHead'
    t.torso_mesh = 'alienTorso'
    t.pelvis_mesh = 'alienPelvis'
    t.upper_arm_mesh = 'alienUpperArm'
    t.forearm_mesh = 'alienForeArm'
    t.hand_mesh = 'alienHand'
    t.upper_leg_mesh = 'alienUpperLeg'
    t.lower_leg_mesh = 'alienLowerLeg'
    t.toes_mesh = 'alienToes'
    alien_sounds = ['alien1', 'alien2', 'alien3', 'alien4']
    alien_hit_sounds = ['alienHit1', 'alienHit2']
    t.jump_sounds = alien_sounds
    t.attack_sounds = alien_sounds
    t.impact_sounds = alien_hit_sounds
    t.death_sounds = ['alienDeath']
    t.pickup_sounds = alien_sounds
    t.fall_sounds = ['alienFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # OldLady ###################################
    t = Appearance('OldLady')
    t.color_texture = 'oldLadyColor'
    t.color_mask_texture = 'oldLadyColorMask'
    t.icon_texture = 'oldLadyIcon'
    t.icon_mask_texture = 'oldLadyIconColorMask'
    t.head_mesh = 'oldLadyHead'
    t.torso_mesh = 'oldLadyTorso'
    t.pelvis_mesh = 'oldLadyPelvis'
    t.upper_arm_mesh = 'oldLadyUpperArm'
    t.forearm_mesh = 'oldLadyForeArm'
    t.hand_mesh = 'oldLadyHand'
    t.upper_leg_mesh = 'oldLadyUpperLeg'
    t.lower_leg_mesh = 'oldLadyLowerLeg'
    t.toes_mesh = 'oldLadyToes'
    old_lady_sounds = ['oldLady1', 'oldLady2', 'oldLady3', 'oldLady4']
    old_lady_hit_sounds = ['oldLadyHit1', 'oldLadyHit2']
    t.jump_sounds = old_lady_sounds
    t.attack_sounds = old_lady_sounds
    t.impact_sounds = old_lady_hit_sounds
    t.death_sounds = ['oldLadyDeath']
    t.pickup_sounds = old_lady_sounds
    t.fall_sounds = ['oldLadyFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # Gladiator ###################################
    t = Appearance('Gladiator')
    t.color_texture = 'gladiatorColor'
    t.color_mask_texture = 'gladiatorColorMask'
    t.icon_texture = 'gladiatorIcon'
    t.icon_mask_texture = 'gladiatorIconColorMask'
    t.head_mesh = 'gladiatorHead'
    t.torso_mesh = 'gladiatorTorso'
    t.pelvis_mesh = 'gladiatorPelvis'
    t.upper_arm_mesh = 'gladiatorUpperArm'
    t.forearm_mesh = 'gladiatorForeArm'
    t.hand_mesh = 'gladiatorHand'
    t.upper_leg_mesh = 'gladiatorUpperLeg'
    t.lower_leg_mesh = 'gladiatorLowerLeg'
    t.toes_mesh = 'gladiatorToes'
    gladiator_sounds = ['gladiator1', 'gladiator2', 'gladiator3', 'gladiator4']
    gladiator_hit_sounds = ['gladiatorHit1', 'gladiatorHit2']
    t.jump_sounds = gladiator_sounds
    t.attack_sounds = gladiator_sounds
    t.impact_sounds = gladiator_hit_sounds
    t.death_sounds = ['gladiatorDeath']
    t.pickup_sounds = gladiator_sounds
    t.fall_sounds = ['gladiatorFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # Wrestler ###################################
    t = Appearance('Wrestler')
    t.color_texture = 'wrestlerColor'
    t.color_mask_texture = 'wrestlerColorMask'
    t.icon_texture = 'wrestlerIcon'
    t.icon_mask_texture = 'wrestlerIconColorMask'
    t.head_mesh = 'wrestlerHead'
    t.torso_mesh = 'wrestlerTorso'
    t.pelvis_mesh = 'wrestlerPelvis'
    t.upper_arm_mesh = 'wrestlerUpperArm'
    t.forearm_mesh = 'wrestlerForeArm'
    t.hand_mesh = 'wrestlerHand'
    t.upper_leg_mesh = 'wrestlerUpperLeg'
    t.lower_leg_mesh = 'wrestlerLowerLeg'
    t.toes_mesh = 'wrestlerToes'
    wrestler_sounds = ['wrestler1', 'wrestler2', 'wrestler3', 'wrestler4']
    wrestler_hit_sounds = ['wrestlerHit1', 'wrestlerHit2']
    t.jump_sounds = wrestler_sounds
    t.attack_sounds = wrestler_sounds
    t.impact_sounds = wrestler_hit_sounds
    t.death_sounds = ['wrestlerDeath']
    t.pickup_sounds = wrestler_sounds
    t.fall_sounds = ['wrestlerFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # OperaSinger ###################################
    t = Appearance('Gretel')
    t.color_texture = 'operaSingerColor'
    t.color_mask_texture = 'operaSingerColorMask'
    t.icon_texture = 'operaSingerIcon'
    t.icon_mask_texture = 'operaSingerIconColorMask'
    t.head_mesh = 'operaSingerHead'
    t.torso_mesh = 'operaSingerTorso'
    t.pelvis_mesh = 'operaSingerPelvis'
    t.upper_arm_mesh = 'operaSingerUpperArm'
    t.forearm_mesh = 'operaSingerForeArm'
    t.hand_mesh = 'operaSingerHand'
    t.upper_leg_mesh = 'operaSingerUpperLeg'
    t.lower_leg_mesh = 'operaSingerLowerLeg'
    t.toes_mesh = 'operaSingerToes'
    opera_singer_sounds = [
        'operaSinger1',
        'operaSinger2',
        'operaSinger3',
        'operaSinger4',
    ]
    opera_singer_hit_sounds = ['operaSingerHit1', 'operaSingerHit2']
    t.jump_sounds = opera_singer_sounds
    t.attack_sounds = opera_singer_sounds
    t.impact_sounds = opera_singer_hit_sounds
    t.death_sounds = ['operaSingerDeath']
    t.pickup_sounds = opera_singer_sounds
    t.fall_sounds = ['operaSingerFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # Pixie ###################################
    t = Appearance('Pixel')
    t.color_texture = 'pixieColor'
    t.color_mask_texture = 'pixieColorMask'
    t.icon_texture = 'pixieIcon'
    t.icon_mask_texture = 'pixieIconColorMask'
    t.head_mesh = 'pixieHead'
    t.torso_mesh = 'pixieTorso'
    t.pelvis_mesh = 'pixiePelvis'
    t.upper_arm_mesh = 'pixieUpperArm'
    t.forearm_mesh = 'pixieForeArm'
    t.hand_mesh = 'pixieHand'
    t.upper_leg_mesh = 'pixieUpperLeg'
    t.lower_leg_mesh = 'pixieLowerLeg'
    t.toes_mesh = 'pixieToes'
    pixie_sounds = ['pixie1', 'pixie2', 'pixie3', 'pixie4']
    pixie_hit_sounds = ['pixieHit1', 'pixieHit2']
    t.jump_sounds = pixie_sounds
    t.attack_sounds = pixie_sounds
    t.impact_sounds = pixie_hit_sounds
    t.death_sounds = ['pixieDeath']
    t.pickup_sounds = pixie_sounds
    t.fall_sounds = ['pixieFall']
    t.style = 'pixie'
    t.default_color = (0, 1, 0.7)
    t.default_highlight = (0.65, 0.35, 0.75)

    # Robot ###################################
    t = Appearance('Robot')
    t.color_texture = 'robotColor'
    t.color_mask_texture = 'robotColorMask'
    t.icon_texture = 'robotIcon'
    t.icon_mask_texture = 'robotIconColorMask'
    t.head_mesh = 'robotHead'
    t.torso_mesh = 'robotTorso'
    t.pelvis_mesh = 'robotPelvis'
    t.upper_arm_mesh = 'robotUpperArm'
    t.forearm_mesh = 'robotForeArm'
    t.hand_mesh = 'robotHand'
    t.upper_leg_mesh = 'robotUpperLeg'
    t.lower_leg_mesh = 'robotLowerLeg'
    t.toes_mesh = 'robotToes'
    robot_sounds = ['robot1', 'robot2', 'robot3', 'robot4']
    robot_hit_sounds = ['robotHit1', 'robotHit2']
    t.jump_sounds = robot_sounds
    t.attack_sounds = robot_sounds
    t.impact_sounds = robot_hit_sounds
    t.death_sounds = ['robotDeath']
    t.pickup_sounds = robot_sounds
    t.fall_sounds = ['robotFall']
    t.style = 'spaz'
    t.default_color = (0.3, 0.5, 0.8)
    t.default_highlight = (1, 0, 0)

    # Bunny ###################################
    t = Appearance('Easter Bunny')
    t.color_texture = 'bunnyColor'
    t.color_mask_texture = 'bunnyColorMask'
    t.icon_texture = 'bunnyIcon'
    t.icon_mask_texture = 'bunnyIconColorMask'
    t.head_mesh = 'bunnyHead'
    t.torso_mesh = 'bunnyTorso'
    t.pelvis_mesh = 'bunnyPelvis'
    t.upper_arm_mesh = 'bunnyUpperArm'
    t.forearm_mesh = 'bunnyForeArm'
    t.hand_mesh = 'bunnyHand'
    t.upper_leg_mesh = 'bunnyUpperLeg'
    t.lower_leg_mesh = 'bunnyLowerLeg'
    t.toes_mesh = 'bunnyToes'
    bunny_sounds = ['bunny1', 'bunny2', 'bunny3', 'bunny4']
    bunny_hit_sounds = ['bunnyHit1', 'bunnyHit2']
    t.jump_sounds = ['bunnyJump']
    t.attack_sounds = bunny_sounds
    t.impact_sounds = bunny_hit_sounds
    t.death_sounds = ['bunnyDeath']
    t.pickup_sounds = bunny_sounds
    t.fall_sounds = ['bunnyFall']
    t.style = 'bunny'
    t.default_color = (1, 1, 1)
    t.default_highlight = (1, 0.5, 0.5)
