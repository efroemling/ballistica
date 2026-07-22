# Released under the MIT License. See LICENSE for details.
#
"""Provides a window to display game credits."""

from typing import TYPE_CHECKING, override

import bauiv1 as bui
from bauiv1 import stdassets

if TYPE_CHECKING:
    from typing import Sequence


class CreditsWindow(bui.MainWindow):
    """Window for displaying game credits."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('Credits Window')

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 990 if uiscale is bui.UIScale.SMALL else 670
        height = 750 if uiscale is bui.UIScale.SMALL else 500

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            2.0
            if uiscale is bui.UIScale.SMALL
            else 1.2 if uiscale is bui.UIScale.MEDIUM else 1.0
        )

        # Scale down if necessary so the full width of our UI is
        # visible.
        min_width = 800
        if screensize[0] / scale < min_width:
            scale *= (screensize[0] / scale) / min_width

        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(width - 80, screensize[0] / scale)
        target_height = min(height - 80, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height

        scroll_width = target_width

        # Use the full screen area in small mode (we'll include our
        # title in the scrollable content).
        if uiscale is bui.UIScale.SMALL:
            scroll_height = target_height
            scroll_y = yoffs - scroll_height
        else:
            yoffs += 30
            scroll_height = target_height - 29
            scroll_y = yoffs - 58 - scroll_height

        self._r = 'creditsWindow'
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                id=f'{self.main_window_id_prefix}|back',
                position=(40, yoffs - 46),
                size=(60, 55),
                scale=0.8,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
                autoselect=True,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        scroll = bui.scrollwidget(
            parent=self._root_widget,
            size=(scroll_width, scroll_height),
            position=(width * 0.5 - scroll_width * 0.5, scroll_y),
            capture_arrows=True,
            border_opacity=0.4,
            center_small_content_horizontally=True,
        )

        if uiscale is bui.UIScale.SMALL:
            bui.widget(
                edit=scroll,
                left_widget=bui.get_special_widget('back_button'),
            )
        bui.widget(
            edit=scroll,
            right_widget=bui.get_special_widget('squad_button'),
        )
        bui.containerwidget(edit=self._root_widget, selected_child=scroll)

        def _format_names(names2: Sequence[str], inset: float) -> str:
            sval = ''
            # measure a series since there's overlaps and stuff..
            space_width = (
                bui.get_string_width(' ' * 10, suppress_warning=True) / 10.0
            )
            spacing = 330.0
            col1 = inset
            col2 = col1 + spacing
            col3 = col2 + spacing
            line_width = 0.0
            nline = ''
            for name in names2:
                # move to the next column (or row) and print
                if line_width > col3:
                    sval += nline + '\n'
                    nline = ''
                    line_width = 0

                if line_width > col2:
                    target = col3
                elif line_width > col1:
                    target = col2
                else:
                    target = col1
                spacingstr = ' ' * int((target - line_width) / space_width)
                nline += spacingstr
                nline += name
                line_width = bui.get_string_width(nline, suppress_warning=True)
            if nline != '':
                sval += nline + '\n'
            return sval

        sound_and_music = bui.Lstr(
            resource=f'{self._r}.songCreditText'
        ).evaluate()
        sound_and_music = sound_and_music.replace(
            '${TITLE}', "'William Tell (Trumpet Entry)'"
        )
        sound_and_music = sound_and_music.replace(
            '${PERFORMER}', 'The Apollo Symphony Orchestra'
        )
        sound_and_music = sound_and_music.replace(
            '${PERFORMER}', 'The Apollo Symphony Orchestra'
        )
        sound_and_music = sound_and_music.replace(
            '${COMPOSER}', 'Gioacchino Rossini'
        )
        sound_and_music = sound_and_music.replace('${ARRANGER}', 'Chris Worth')
        sound_and_music = sound_and_music.replace('${PUBLISHER}', 'BMI')
        sound_and_music = sound_and_music.replace(
            '${SOURCE}', 'www.AudioSparx.com'
        )
        spc = '     '
        sound_and_music = spc + sound_and_music.replace('\n', '\n' + spc)
        names = [
            'HubOfTheUniverseProd',
            'Jovica',
            'LG',
            'Leady',
            'Percy Duke',
            'PhreaKsAccount',
            'Pogotron',
            'Rock Savage',
            'anamorphosis',
            'benboncan',
            'cdrk',
            'chipfork',
            'guitarguy1985',
            'jascha',
            'joedeshon',
            'loofa',
            'm_O_m',
            'mich3d',
            'sandyrb',
            'shakaharu',
            'sirplus',
            'stickman',
            'thanvannispen',
            'virotic',
            'zimbot',
        ]
        names.sort(key=lambda x: x.lower())
        freesound_names = _format_names(names, 90)

        translation_contributors = bui.get_legacy_langdata().get(
            'translation_contributors', []
        )

        translation_names = _format_names(translation_contributors, 60)

        # Need to bake this out and chop it up since we're passing our
        # 65535 vertex limit for meshes..
        # We can remove that limit once we drop support for GL ES2.. :-/
        # (or add mesh splitting under the hood)
        credits_text = (
            '  '
            + stdassets.strings.credits.coding_graphics_audio(
                name='Eric Froemling'
            ).evaluate()
            + '\n'
            '\n'
            '  '
            + stdassets.strings.credits.additional_audio_art_ideas(
                name='Raphael Suter'
            ).evaluate()
            + '\n'
            '\n'
            '  ' + stdassets.strings.credits.sound_and_music.evaluate() + '\n'
            '\n' + sound_and_music + '\n'
            '\n'
            '     '
            + stdassets.strings.credits.public_domain_music_via(
                name='Musopen.com'
            ).evaluate()
            + '\n'
            '        '
            + stdassets.strings.credits.thanks_especially_to(
                name='the US Army, Navy, and Marine Bands'
            ).evaluate()
            + '\n'
            '\n'
            '     '
            + stdassets.strings.credits.additional_music_from(
                name='The YouTube Audio Library'
            ).evaluate()
            + '\n'
            '\n'
            '     '
            + stdassets.strings.credits.sounds_source(
                source='Freesound.org'
            ).evaluate()
            + '\n'
            '\n' + freesound_names + '\n'
            '\n'
            '  '
            + stdassets.strings.credits.language_translations.evaluate()
            + '\n'
            '\n'
            + '\n'.join(translation_names.splitlines()[:146])
            + '\n'.join(translation_names.splitlines()[146:])
            + '\n'
            '\n'
            '  Shout Out to Awesome Mods / Modders / Contributors:\n\n'
            '     BombDash ModPack\n'
            '     TheMikirog & SoK - BombSquad Joyride Modpack\n'
            '     Mrmaxmeier - BombSquad-Community-Mod-Manager\n'
            '     Ritiek Malhotra \n'
            '     Dliwk\n'
            '     vishal332008\n'
            '     itsre3\n'
            '     Drooopyyy\n'
            '     Loup\n'
            '\n'
            '  Holiday theme vector art designed by Freepik\n'
            '\n'
            '  ' + stdassets.strings.credits.special_thanks.evaluate() + '\n'
            '\n'
            '     Todd, Laura, and Robert Froemling\n'
            '     '
            + stdassets.strings.credits.all_my_family.evaluate().replace(
                '\n', '\n     '
            )
            + '\n'
            '     '
            + stdassets.strings.credits.whoever_invented_coffee.evaluate()
            + '\n'
            '\n'
            '  ' + stdassets.strings.credits.legal.evaluate() + '\n'
            '\n'
            '     '
            + stdassets.strings.credits.software_based_on(
                name='the Khronos Group'
            ).evaluate()
            + '\n'
            '\n'
            '                                       '
            '                      www.ballistica.net\n'
        )

        txt = credits_text
        lines = txt.splitlines()
        line_height = 20

        scale = 0.55
        self._sub_width = min(700, width - 80)
        self._sub_height = line_height * len(lines) + 40

        inline_title_height = 50

        # Make space for our title when we're stuffing it inline.
        if uiscale is bui.UIScale.SMALL:
            self._sub_height += inline_title_height

        container = self._subcontainer = bui.containerwidget(
            parent=scroll,
            id=f'{self.main_window_id_prefix}|sub',
            size=(self._sub_width, self._sub_height),
            background=False,
            claims_left_right=False,
        )

        # Stick our title on the scrollable content in small ui mode so
        # we can use the full screen area for said content.
        bui.textwidget(
            parent=(
                self._subcontainer
                if uiscale is bui.UIScale.SMALL
                else self._root_widget
            ),
            position=(
                (self._sub_width * 0.5, self._sub_height - 20)
                if uiscale is bui.UIScale.SMALL
                else (width * 0.5, yoffs - 28)
            ),
            size=(0, 0),
            scale=0.8 if uiscale is bui.UIScale.SMALL else 1.0,
            text=stdassets.strings.credits.title(
                app_name=stdassets.strings.ui.app_name
            ),
            h_align='center',
            v_align='center',
            color=bui.app.ui_v1.title_color,
            maxwidth=scroll_width * 0.7,
        )

        voffs = -inline_title_height if uiscale is bui.UIScale.SMALL else 0

        for line in lines:
            bui.textwidget(
                parent=container,
                padding=4,
                color=(0.7, 0.9, 0.7, 1.0),
                scale=scale,
                flatness=1.0,
                size=(0, 0),
                position=(0, self._sub_height - 20 + voffs),
                h_align='left',
                v_align='top',
                text=line,
            )
            voffs -= line_height

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    @override
    def main_window_should_preserve_selection(self) -> bool:
        return True
