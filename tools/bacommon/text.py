# Released under the MIT License. See LICENSE for details.
#
"""Text related bits."""

from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, assert_never

if TYPE_CHECKING:
    pass


class SpecialChar(Enum):
    """Custom unicode characters the engine can display.

    Each value is the character itself, ready to drop into a string.
    These utilize the private-use block of unicode characters
    (U+E000-U+F8FF) and are specific to the game; exporting or
    rendering them elsewhere will be meaningless.

    This is the one list of these characters; the engine's own table
    is generated from it. It is also available as
    ``babase.SpecialChar`` and ``bauiv1.SpecialChar``.
    """

    LEFT_ARROW = '\ue001'
    RIGHT_ARROW = '\ue002'
    UP_ARROW = '\ue003'
    DOWN_ARROW = '\ue004'
    LEFT_BUTTON = '\ue005'
    TOP_BUTTON = '\ue006'
    RIGHT_BUTTON = '\ue007'
    BOTTOM_BUTTON = '\ue008'
    DELETE = '\ue009'
    SHIFT = '\ue00a'
    BACK = '\ue00b'
    LOGO_FLAT = '\ue00c'
    REWIND_BUTTON = '\ue00d'
    PLAY_PAUSE_BUTTON = '\ue00e'
    FAST_FORWARD_BUTTON = '\ue00f'
    DPAD_CENTER_BUTTON = '\ue010'
    PLAY_STATION_CROSS_BUTTON = '\ue011'
    PLAY_STATION_CIRCLE_BUTTON = '\ue012'
    PLAY_STATION_TRIANGLE_BUTTON = '\ue013'
    PLAY_STATION_SQUARE_BUTTON = '\ue014'
    PLAY_BUTTON = '\ue015'
    PAUSE_BUTTON = '\ue016'
    CLOSE = '\ue017'
    OUYA_BUTTON_O = '\ue019'
    OUYA_BUTTON_U = '\ue01a'
    OUYA_BUTTON_Y = '\ue01b'
    OUYA_BUTTON_A = '\ue01c'
    TOKEN = '\ue01d'
    LOGO = '\ue01e'
    TICKET = '\ue01f'
    GOOGLE_PLAY_GAMES_LOGO = '\ue020'
    GAME_CENTER_LOGO = '\ue021'
    DICE_BUTTON1 = '\ue022'
    DICE_BUTTON2 = '\ue023'
    DICE_BUTTON3 = '\ue024'
    DICE_BUTTON4 = '\ue025'
    DISCORD_LOGO = '\ue026'
    PARTY_ICON = '\ue027'
    TEST_ACCOUNT = '\ue028'
    TICKET_BACKING = '\ue029'
    TROPHY1 = '\ue02a'
    TROPHY2 = '\ue02b'
    TROPHY3 = '\ue02c'
    TROPHY0A = '\ue02d'
    TROPHY0B = '\ue02e'
    TROPHY4 = '\ue02f'
    LOCAL_ACCOUNT = '\ue030'
    EXPLODINARY_LOGO = '\ue031'
    FLAG_UNITED_STATES = '\ue032'
    FLAG_MEXICO = '\ue033'
    FLAG_GERMANY = '\ue034'
    FLAG_BRAZIL = '\ue035'
    FLAG_RUSSIA = '\ue036'
    FLAG_CHINA = '\ue037'
    FLAG_UNITED_KINGDOM = '\ue038'
    FLAG_CANADA = '\ue039'
    FLAG_INDIA = '\ue03a'
    FLAG_JAPAN = '\ue03b'
    FLAG_FRANCE = '\ue03c'
    FLAG_INDONESIA = '\ue03d'
    FLAG_ITALY = '\ue03e'
    FLAG_SOUTH_KOREA = '\ue03f'
    FLAG_NETHERLANDS = '\ue040'
    FEDORA = '\ue041'
    HAL = '\ue042'
    CROWN = '\ue043'
    YIN_YANG = '\ue044'
    EYE_BALL = '\ue045'
    SKULL = '\ue046'
    HEART = '\ue047'
    DRAGON = '\ue048'
    HELMET = '\ue049'
    MUSHROOM = '\ue04a'
    NINJA_STAR = '\ue04b'
    VIKING_HELMET = '\ue04c'
    MOON = '\ue04d'
    SPIDER = '\ue04e'
    FIREBALL = '\ue04f'
    FLAG_UNITED_ARAB_EMIRATES = '\ue050'
    FLAG_QATAR = '\ue051'
    FLAG_EGYPT = '\ue052'
    FLAG_KUWAIT = '\ue053'
    FLAG_ALGERIA = '\ue054'
    FLAG_SAUDI_ARABIA = '\ue055'
    FLAG_MALAYSIA = '\ue056'
    FLAG_CZECH_REPUBLIC = '\ue057'
    FLAG_AUSTRALIA = '\ue058'
    FLAG_SINGAPORE = '\ue059'
    OCULUS_LOGO = '\ue05a'
    STEAM_LOGO = '\ue05b'
    NVIDIA_LOGO = '\ue05c'
    FLAG_IRAN = '\ue05d'
    FLAG_POLAND = '\ue05e'
    FLAG_ARGENTINA = '\ue05f'
    FLAG_PHILIPPINES = '\ue060'
    FLAG_CHILE = '\ue061'
    MIKIROG = '\ue062'
    V2_LOGO = '\ue063'
    SANTA_HAT = '\ue064'
    POTATO = '\ue065'
    PALM_TREE = '\ue066'
    BOXING_GLOVE = '\ue067'
    ANNIVERSARY_15_CAKE = '\ue068'
    ANNIVERSARY_15_SPAZ = '\ue069'
    ANNIVERSARY_15_BOMB = '\ue06a'
    POPUP_ICON = '\ue018'

    @cached_property
    def min_engine_build(self) -> int:
        """The first engine build able to draw this character.

        Older builds have no glyph for it and show a blank, so anything
        offering characters to a particular client (a store, an icon
        picker) should leave out ones newer than that client's build.

        When adding a character, give it its own case here returning
        the build number that first ships its glyph. Everything that
        predates this property returns 0 (we don't know when those
        were added, and every client we talk to can draw them).
        """
        cls = type(self)
        match self:
            case (
                cls.LEFT_ARROW
                | cls.RIGHT_ARROW
                | cls.UP_ARROW
                | cls.DOWN_ARROW
                | cls.LEFT_BUTTON
                | cls.TOP_BUTTON
                | cls.RIGHT_BUTTON
                | cls.BOTTOM_BUTTON
                | cls.DELETE
                | cls.SHIFT
                | cls.BACK
                | cls.LOGO_FLAT
                | cls.REWIND_BUTTON
                | cls.PLAY_PAUSE_BUTTON
                | cls.FAST_FORWARD_BUTTON
                | cls.DPAD_CENTER_BUTTON
                | cls.PLAY_STATION_CROSS_BUTTON
                | cls.PLAY_STATION_CIRCLE_BUTTON
                | cls.PLAY_STATION_TRIANGLE_BUTTON
                | cls.PLAY_STATION_SQUARE_BUTTON
                | cls.PLAY_BUTTON
                | cls.PAUSE_BUTTON
                | cls.CLOSE
                | cls.OUYA_BUTTON_O
                | cls.OUYA_BUTTON_U
                | cls.OUYA_BUTTON_Y
                | cls.OUYA_BUTTON_A
                | cls.TOKEN
                | cls.LOGO
                | cls.TICKET
                | cls.GOOGLE_PLAY_GAMES_LOGO
                | cls.GAME_CENTER_LOGO
                | cls.DICE_BUTTON1
                | cls.DICE_BUTTON2
                | cls.DICE_BUTTON3
                | cls.DICE_BUTTON4
                | cls.DISCORD_LOGO
                | cls.PARTY_ICON
                | cls.TEST_ACCOUNT
                | cls.TICKET_BACKING
                | cls.TROPHY1
                | cls.TROPHY2
                | cls.TROPHY3
                | cls.TROPHY0A
                | cls.TROPHY0B
                | cls.TROPHY4
                | cls.LOCAL_ACCOUNT
                | cls.EXPLODINARY_LOGO
                | cls.FLAG_UNITED_STATES
                | cls.FLAG_MEXICO
                | cls.FLAG_GERMANY
                | cls.FLAG_BRAZIL
                | cls.FLAG_RUSSIA
                | cls.FLAG_CHINA
                | cls.FLAG_UNITED_KINGDOM
                | cls.FLAG_CANADA
                | cls.FLAG_INDIA
                | cls.FLAG_JAPAN
                | cls.FLAG_FRANCE
                | cls.FLAG_INDONESIA
                | cls.FLAG_ITALY
                | cls.FLAG_SOUTH_KOREA
                | cls.FLAG_NETHERLANDS
                | cls.FEDORA
                | cls.HAL
                | cls.CROWN
                | cls.YIN_YANG
                | cls.EYE_BALL
                | cls.SKULL
                | cls.HEART
                | cls.DRAGON
                | cls.HELMET
                | cls.MUSHROOM
                | cls.NINJA_STAR
                | cls.VIKING_HELMET
                | cls.MOON
                | cls.SPIDER
                | cls.FIREBALL
                | cls.FLAG_UNITED_ARAB_EMIRATES
                | cls.FLAG_QATAR
                | cls.FLAG_EGYPT
                | cls.FLAG_KUWAIT
                | cls.FLAG_ALGERIA
                | cls.FLAG_SAUDI_ARABIA
                | cls.FLAG_MALAYSIA
                | cls.FLAG_CZECH_REPUBLIC
                | cls.FLAG_AUSTRALIA
                | cls.FLAG_SINGAPORE
                | cls.OCULUS_LOGO
                | cls.STEAM_LOGO
                | cls.NVIDIA_LOGO
                | cls.FLAG_IRAN
                | cls.FLAG_POLAND
                | cls.FLAG_ARGENTINA
                | cls.FLAG_PHILIPPINES
                | cls.FLAG_CHILE
                | cls.MIKIROG
                | cls.V2_LOGO
                | cls.SANTA_HAT
                | cls.POTATO
                | cls.PALM_TREE
                | cls.BOXING_GLOVE
                | cls.POPUP_ICON
            ):
                return 0
            case (
                cls.ANNIVERSARY_15_CAKE
                | cls.ANNIVERSARY_15_SPAZ
                | cls.ANNIVERSARY_15_BOMB
            ):
                return 23057
            case _:
                assert_never(self)
