# Released under the MIT License. See LICENSE for details.
#
"""Text related bits."""

from enum import Enum
from functools import cache, cached_property
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

    # Full-size twins of the superscript icons above (see full_size).
    LOGO_FULL = '\ue06b'
    GOOGLE_PLAY_GAMES_LOGO_FULL = '\ue06c'
    GAME_CENTER_LOGO_FULL = '\ue06d'
    DISCORD_LOGO_FULL = '\ue06e'
    TEST_ACCOUNT_FULL = '\ue06f'
    LOCAL_ACCOUNT_FULL = '\ue070'
    EXPLODINARY_LOGO_FULL = '\ue071'
    FLAG_UNITED_STATES_FULL = '\ue072'
    FLAG_MEXICO_FULL = '\ue073'
    FLAG_GERMANY_FULL = '\ue074'
    FLAG_BRAZIL_FULL = '\ue075'
    FLAG_RUSSIA_FULL = '\ue076'
    FLAG_CHINA_FULL = '\ue077'
    FLAG_UNITED_KINGDOM_FULL = '\ue078'
    FLAG_CANADA_FULL = '\ue079'
    FLAG_INDIA_FULL = '\ue07a'
    FLAG_JAPAN_FULL = '\ue07b'
    FLAG_FRANCE_FULL = '\ue07c'
    FLAG_INDONESIA_FULL = '\ue07d'
    FLAG_ITALY_FULL = '\ue07e'
    FLAG_SOUTH_KOREA_FULL = '\ue07f'
    FLAG_NETHERLANDS_FULL = '\ue080'
    FEDORA_FULL = '\ue081'
    HAL_FULL = '\ue082'
    CROWN_FULL = '\ue083'
    YIN_YANG_FULL = '\ue084'
    EYE_BALL_FULL = '\ue085'
    SKULL_FULL = '\ue086'
    HEART_FULL = '\ue087'
    DRAGON_FULL = '\ue088'
    HELMET_FULL = '\ue089'
    MUSHROOM_FULL = '\ue08a'
    NINJA_STAR_FULL = '\ue08b'
    VIKING_HELMET_FULL = '\ue08c'
    MOON_FULL = '\ue08d'
    SPIDER_FULL = '\ue08e'
    FIREBALL_FULL = '\ue08f'
    FLAG_UNITED_ARAB_EMIRATES_FULL = '\ue090'
    FLAG_QATAR_FULL = '\ue091'
    FLAG_EGYPT_FULL = '\ue092'
    FLAG_KUWAIT_FULL = '\ue093'
    FLAG_ALGERIA_FULL = '\ue094'
    FLAG_SAUDI_ARABIA_FULL = '\ue095'
    FLAG_MALAYSIA_FULL = '\ue096'
    FLAG_CZECH_REPUBLIC_FULL = '\ue097'
    FLAG_AUSTRALIA_FULL = '\ue098'
    FLAG_SINGAPORE_FULL = '\ue099'
    OCULUS_LOGO_FULL = '\ue09a'
    STEAM_LOGO_FULL = '\ue09b'
    NVIDIA_LOGO_FULL = '\ue09c'
    FLAG_IRAN_FULL = '\ue09d'
    FLAG_POLAND_FULL = '\ue09e'
    FLAG_ARGENTINA_FULL = '\ue09f'
    FLAG_PHILIPPINES_FULL = '\ue0a0'
    FLAG_CHILE_FULL = '\ue0a1'
    MIKIROG_FULL = '\ue0a2'
    V2_LOGO_FULL = '\ue0a3'
    SANTA_HAT_FULL = '\ue0a4'
    POTATO_FULL = '\ue0a5'
    PALM_TREE_FULL = '\ue0a6'
    BOXING_GLOVE_FULL = '\ue0a7'
    ANNIVERSARY_15_CAKE_FULL = '\ue0a8'
    ANNIVERSARY_15_SPAZ_FULL = '\ue0a9'
    ANNIVERSARY_15_BOMB_FULL = '\ue0aa'

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
            case (
                cls.LOGO_FULL
                | cls.GOOGLE_PLAY_GAMES_LOGO_FULL
                | cls.GAME_CENTER_LOGO_FULL
                | cls.DISCORD_LOGO_FULL
                | cls.TEST_ACCOUNT_FULL
                | cls.LOCAL_ACCOUNT_FULL
                | cls.EXPLODINARY_LOGO_FULL
                | cls.FLAG_UNITED_STATES_FULL
                | cls.FLAG_MEXICO_FULL
                | cls.FLAG_GERMANY_FULL
                | cls.FLAG_BRAZIL_FULL
                | cls.FLAG_RUSSIA_FULL
                | cls.FLAG_CHINA_FULL
                | cls.FLAG_UNITED_KINGDOM_FULL
                | cls.FLAG_CANADA_FULL
                | cls.FLAG_INDIA_FULL
                | cls.FLAG_JAPAN_FULL
                | cls.FLAG_FRANCE_FULL
                | cls.FLAG_INDONESIA_FULL
                | cls.FLAG_ITALY_FULL
                | cls.FLAG_SOUTH_KOREA_FULL
                | cls.FLAG_NETHERLANDS_FULL
                | cls.FEDORA_FULL
                | cls.HAL_FULL
                | cls.CROWN_FULL
                | cls.YIN_YANG_FULL
                | cls.EYE_BALL_FULL
                | cls.SKULL_FULL
                | cls.HEART_FULL
                | cls.DRAGON_FULL
                | cls.HELMET_FULL
                | cls.MUSHROOM_FULL
                | cls.NINJA_STAR_FULL
                | cls.VIKING_HELMET_FULL
                | cls.MOON_FULL
                | cls.SPIDER_FULL
                | cls.FIREBALL_FULL
                | cls.FLAG_UNITED_ARAB_EMIRATES_FULL
                | cls.FLAG_QATAR_FULL
                | cls.FLAG_EGYPT_FULL
                | cls.FLAG_KUWAIT_FULL
                | cls.FLAG_ALGERIA_FULL
                | cls.FLAG_SAUDI_ARABIA_FULL
                | cls.FLAG_MALAYSIA_FULL
                | cls.FLAG_CZECH_REPUBLIC_FULL
                | cls.FLAG_AUSTRALIA_FULL
                | cls.FLAG_SINGAPORE_FULL
                | cls.OCULUS_LOGO_FULL
                | cls.STEAM_LOGO_FULL
                | cls.NVIDIA_LOGO_FULL
                | cls.FLAG_IRAN_FULL
                | cls.FLAG_POLAND_FULL
                | cls.FLAG_ARGENTINA_FULL
                | cls.FLAG_PHILIPPINES_FULL
                | cls.FLAG_CHILE_FULL
                | cls.MIKIROG_FULL
                | cls.V2_LOGO_FULL
                | cls.SANTA_HAT_FULL
                | cls.POTATO_FULL
                | cls.PALM_TREE_FULL
                | cls.BOXING_GLOVE_FULL
                | cls.ANNIVERSARY_15_CAKE_FULL
                | cls.ANNIVERSARY_15_SPAZ_FULL
                | cls.ANNIVERSARY_15_BOMB_FULL
            ):
                return 23073
            case _:
                assert_never(self)

    @cached_property
    def full_size(self) -> SpecialChar | None:
        """This character's full-size form, if it has one.

        Profile icons, flags and account/platform logos come in two
        forms: a small raised (superscript) one for showing next to a
        name -- the long-standing character, which is what travels in
        names -- and a full-size ``_FULL`` twin for showing framed or
        as a button label (newer clients only; see
        :attr:`min_engine_build`). The superscript form's metrics are
        derived from its twin's, so only the twin is ever tuned.

        Returns the twin for a superscript character, the character
        itself for a full-size one, and None for everything else. When
        adding a character, give it a case here: an icon gets both
        forms, paired here.
        """
        # One case per icon pair, exhaustively (mypy catches a member
        # nobody classified).
        # pylint: disable=too-many-return-statements, too-many-branches
        cls = type(self)
        match self:
            case cls.LOGO:
                return cls.LOGO_FULL
            case cls.GOOGLE_PLAY_GAMES_LOGO:
                return cls.GOOGLE_PLAY_GAMES_LOGO_FULL
            case cls.GAME_CENTER_LOGO:
                return cls.GAME_CENTER_LOGO_FULL
            case cls.DISCORD_LOGO:
                return cls.DISCORD_LOGO_FULL
            case cls.TEST_ACCOUNT:
                return cls.TEST_ACCOUNT_FULL
            case cls.LOCAL_ACCOUNT:
                return cls.LOCAL_ACCOUNT_FULL
            case cls.EXPLODINARY_LOGO:
                return cls.EXPLODINARY_LOGO_FULL
            case cls.FLAG_UNITED_STATES:
                return cls.FLAG_UNITED_STATES_FULL
            case cls.FLAG_MEXICO:
                return cls.FLAG_MEXICO_FULL
            case cls.FLAG_GERMANY:
                return cls.FLAG_GERMANY_FULL
            case cls.FLAG_BRAZIL:
                return cls.FLAG_BRAZIL_FULL
            case cls.FLAG_RUSSIA:
                return cls.FLAG_RUSSIA_FULL
            case cls.FLAG_CHINA:
                return cls.FLAG_CHINA_FULL
            case cls.FLAG_UNITED_KINGDOM:
                return cls.FLAG_UNITED_KINGDOM_FULL
            case cls.FLAG_CANADA:
                return cls.FLAG_CANADA_FULL
            case cls.FLAG_INDIA:
                return cls.FLAG_INDIA_FULL
            case cls.FLAG_JAPAN:
                return cls.FLAG_JAPAN_FULL
            case cls.FLAG_FRANCE:
                return cls.FLAG_FRANCE_FULL
            case cls.FLAG_INDONESIA:
                return cls.FLAG_INDONESIA_FULL
            case cls.FLAG_ITALY:
                return cls.FLAG_ITALY_FULL
            case cls.FLAG_SOUTH_KOREA:
                return cls.FLAG_SOUTH_KOREA_FULL
            case cls.FLAG_NETHERLANDS:
                return cls.FLAG_NETHERLANDS_FULL
            case cls.FEDORA:
                return cls.FEDORA_FULL
            case cls.HAL:
                return cls.HAL_FULL
            case cls.CROWN:
                return cls.CROWN_FULL
            case cls.YIN_YANG:
                return cls.YIN_YANG_FULL
            case cls.EYE_BALL:
                return cls.EYE_BALL_FULL
            case cls.SKULL:
                return cls.SKULL_FULL
            case cls.HEART:
                return cls.HEART_FULL
            case cls.DRAGON:
                return cls.DRAGON_FULL
            case cls.HELMET:
                return cls.HELMET_FULL
            case cls.MUSHROOM:
                return cls.MUSHROOM_FULL
            case cls.NINJA_STAR:
                return cls.NINJA_STAR_FULL
            case cls.VIKING_HELMET:
                return cls.VIKING_HELMET_FULL
            case cls.MOON:
                return cls.MOON_FULL
            case cls.SPIDER:
                return cls.SPIDER_FULL
            case cls.FIREBALL:
                return cls.FIREBALL_FULL
            case cls.FLAG_UNITED_ARAB_EMIRATES:
                return cls.FLAG_UNITED_ARAB_EMIRATES_FULL
            case cls.FLAG_QATAR:
                return cls.FLAG_QATAR_FULL
            case cls.FLAG_EGYPT:
                return cls.FLAG_EGYPT_FULL
            case cls.FLAG_KUWAIT:
                return cls.FLAG_KUWAIT_FULL
            case cls.FLAG_ALGERIA:
                return cls.FLAG_ALGERIA_FULL
            case cls.FLAG_SAUDI_ARABIA:
                return cls.FLAG_SAUDI_ARABIA_FULL
            case cls.FLAG_MALAYSIA:
                return cls.FLAG_MALAYSIA_FULL
            case cls.FLAG_CZECH_REPUBLIC:
                return cls.FLAG_CZECH_REPUBLIC_FULL
            case cls.FLAG_AUSTRALIA:
                return cls.FLAG_AUSTRALIA_FULL
            case cls.FLAG_SINGAPORE:
                return cls.FLAG_SINGAPORE_FULL
            case cls.OCULUS_LOGO:
                return cls.OCULUS_LOGO_FULL
            case cls.STEAM_LOGO:
                return cls.STEAM_LOGO_FULL
            case cls.NVIDIA_LOGO:
                return cls.NVIDIA_LOGO_FULL
            case cls.FLAG_IRAN:
                return cls.FLAG_IRAN_FULL
            case cls.FLAG_POLAND:
                return cls.FLAG_POLAND_FULL
            case cls.FLAG_ARGENTINA:
                return cls.FLAG_ARGENTINA_FULL
            case cls.FLAG_PHILIPPINES:
                return cls.FLAG_PHILIPPINES_FULL
            case cls.FLAG_CHILE:
                return cls.FLAG_CHILE_FULL
            case cls.MIKIROG:
                return cls.MIKIROG_FULL
            case cls.V2_LOGO:
                return cls.V2_LOGO_FULL
            case cls.SANTA_HAT:
                return cls.SANTA_HAT_FULL
            case cls.POTATO:
                return cls.POTATO_FULL
            case cls.PALM_TREE:
                return cls.PALM_TREE_FULL
            case cls.BOXING_GLOVE:
                return cls.BOXING_GLOVE_FULL
            case cls.ANNIVERSARY_15_CAKE:
                return cls.ANNIVERSARY_15_CAKE_FULL
            case cls.ANNIVERSARY_15_SPAZ:
                return cls.ANNIVERSARY_15_SPAZ_FULL
            case cls.ANNIVERSARY_15_BOMB:
                return cls.ANNIVERSARY_15_BOMB_FULL
            case (
                cls.LOGO_FULL
                | cls.GOOGLE_PLAY_GAMES_LOGO_FULL
                | cls.GAME_CENTER_LOGO_FULL
                | cls.DISCORD_LOGO_FULL
                | cls.TEST_ACCOUNT_FULL
                | cls.LOCAL_ACCOUNT_FULL
                | cls.EXPLODINARY_LOGO_FULL
                | cls.FLAG_UNITED_STATES_FULL
                | cls.FLAG_MEXICO_FULL
                | cls.FLAG_GERMANY_FULL
                | cls.FLAG_BRAZIL_FULL
                | cls.FLAG_RUSSIA_FULL
                | cls.FLAG_CHINA_FULL
                | cls.FLAG_UNITED_KINGDOM_FULL
                | cls.FLAG_CANADA_FULL
                | cls.FLAG_INDIA_FULL
                | cls.FLAG_JAPAN_FULL
                | cls.FLAG_FRANCE_FULL
                | cls.FLAG_INDONESIA_FULL
                | cls.FLAG_ITALY_FULL
                | cls.FLAG_SOUTH_KOREA_FULL
                | cls.FLAG_NETHERLANDS_FULL
                | cls.FEDORA_FULL
                | cls.HAL_FULL
                | cls.CROWN_FULL
                | cls.YIN_YANG_FULL
                | cls.EYE_BALL_FULL
                | cls.SKULL_FULL
                | cls.HEART_FULL
                | cls.DRAGON_FULL
                | cls.HELMET_FULL
                | cls.MUSHROOM_FULL
                | cls.NINJA_STAR_FULL
                | cls.VIKING_HELMET_FULL
                | cls.MOON_FULL
                | cls.SPIDER_FULL
                | cls.FIREBALL_FULL
                | cls.FLAG_UNITED_ARAB_EMIRATES_FULL
                | cls.FLAG_QATAR_FULL
                | cls.FLAG_EGYPT_FULL
                | cls.FLAG_KUWAIT_FULL
                | cls.FLAG_ALGERIA_FULL
                | cls.FLAG_SAUDI_ARABIA_FULL
                | cls.FLAG_MALAYSIA_FULL
                | cls.FLAG_CZECH_REPUBLIC_FULL
                | cls.FLAG_AUSTRALIA_FULL
                | cls.FLAG_SINGAPORE_FULL
                | cls.OCULUS_LOGO_FULL
                | cls.STEAM_LOGO_FULL
                | cls.NVIDIA_LOGO_FULL
                | cls.FLAG_IRAN_FULL
                | cls.FLAG_POLAND_FULL
                | cls.FLAG_ARGENTINA_FULL
                | cls.FLAG_PHILIPPINES_FULL
                | cls.FLAG_CHILE_FULL
                | cls.MIKIROG_FULL
                | cls.V2_LOGO_FULL
                | cls.SANTA_HAT_FULL
                | cls.POTATO_FULL
                | cls.PALM_TREE_FULL
                | cls.BOXING_GLOVE_FULL
                | cls.ANNIVERSARY_15_CAKE_FULL
                | cls.ANNIVERSARY_15_SPAZ_FULL
                | cls.ANNIVERSARY_15_BOMB_FULL
            ):
                return self
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
                | cls.TICKET
                | cls.DICE_BUTTON1
                | cls.DICE_BUTTON2
                | cls.DICE_BUTTON3
                | cls.DICE_BUTTON4
                | cls.PARTY_ICON
                | cls.TICKET_BACKING
                | cls.TROPHY1
                | cls.TROPHY2
                | cls.TROPHY3
                | cls.TROPHY0A
                | cls.TROPHY0B
                | cls.TROPHY4
                | cls.POPUP_ICON
            ):
                return None
            case _:
                assert_never(self)

    @property
    def is_superscript(self) -> bool:
        """Whether this is the raised form of a two-form icon."""
        full = self.full_size
        return full is not None and full is not self

    @property
    def superscript(self) -> SpecialChar | None:
        """This character's raised form, if it is a two-form icon."""
        if self.is_superscript:
            return self
        if self.full_size is self:
            return _superscript_of()[self]
        return None


@cache
def _superscript_of() -> dict[SpecialChar, SpecialChar]:
    """Map each full-size icon to its superscript form."""
    return {
        full: char
        for char in SpecialChar
        if (full := char.full_size) is not None and full is not char
    }


#: Chars that count as letters or symbols but draw nothing (the usual
#: tricks for blank-looking names).
_BLANK_CHARS = frozenset('ㅤᅟᅠﾠ⠀')


def has_visible_chars(text: str) -> bool:
    """Return whether text has anything that actually draws.

    True if at least one char is a letter, number, punctuation or
    symbol (other than a few that draw blank, such as Hangul fillers).
    Whitespace, format chars (zero-width spaces, direction marks, ...),
    control chars and lone combining marks don't count, so a name made
    only of those is invisible.
    """
    import unicodedata

    return any(
        unicodedata.category(c)[0] in 'LNPS' and c not in _BLANK_CHARS
        for c in text
    )
