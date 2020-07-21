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
"""Provides a window to display game credits."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Tuple, Optional, Sequence


class CreditsListWindow(ba.Window):
    """Window for displaying game credits."""

    def __init__(self, origin_widget: ba.Widget = None):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        import json
        ba.set_analytics_screen('Credits Window')

        # if they provided an origin-widget, scale up from that
        scale_origin: Optional[Tuple[float, float]]
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None
            transition = 'in_right'

        uiscale = ba.app.ui.uiscale
        width = 870 if uiscale is ba.UIScale.SMALL else 670
        x_inset = 100 if uiscale is ba.UIScale.SMALL else 0
        height = 398 if uiscale is ba.UIScale.SMALL else 500

        self._r = 'creditsWindow'
        super().__init__(root_widget=ba.containerwidget(
            size=(width, height),
            transition=transition,
            toolbar_visibility='menu_minimal',
            scale_origin_stack_offset=scale_origin,
            scale=(2.0 if uiscale is ba.UIScale.SMALL else
                   1.3 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -8) if uiscale is ba.UIScale.SMALL else (0, 0)))

        if ba.app.ui.use_toolbars and uiscale is ba.UIScale.SMALL:
            ba.containerwidget(edit=self._root_widget,
                               on_cancel_call=self._back)
        else:
            btn = ba.buttonwidget(
                parent=self._root_widget,
                position=(40 + x_inset, height -
                          (68 if uiscale is ba.UIScale.SMALL else 62)),
                size=(140, 60),
                scale=0.8,
                label=ba.Lstr(resource='backText'),
                button_type='back',
                on_activate_call=self._back,
                autoselect=True)
            ba.containerwidget(edit=self._root_widget, cancel_button=btn)

            ba.buttonwidget(
                edit=btn,
                button_type='backSmall',
                position=(40 + x_inset, height -
                          (68 if uiscale is ba.UIScale.SMALL else 62) + 5),
                size=(60, 48),
                label=ba.charstr(ba.SpecialChar.BACK))

        ba.textwidget(parent=self._root_widget,
                      position=(0, height -
                                (59 if uiscale is ba.UIScale.SMALL else 54)),
                      size=(width, 30),
                      text=ba.Lstr(resource=self._r + '.titleText',
                                   subs=[('${APP_NAME}',
                                          ba.Lstr(resource='titleText'))]),
                      h_align='center',
                      color=ba.app.ui.title_color,
                      maxwidth=330,
                      v_align='center')

        scroll = ba.scrollwidget(parent=self._root_widget,
                                 position=(40 + x_inset, 35),
                                 size=(width - (80 + 2 * x_inset),
                                       height - 100),
                                 capture_arrows=True)

        if ba.app.ui.use_toolbars:
            ba.widget(edit=scroll,
                      right_widget=_ba.get_special_widget('party_button'))
            if uiscale is ba.UIScale.SMALL:
                ba.widget(edit=scroll,
                          left_widget=_ba.get_special_widget('back_button'))

        def _format_names(names2: Sequence[str], inset: float) -> str:
            sval = ''
            # measure a series since there's overlaps and stuff..
            space_width = _ba.get_string_width(' ' * 10,
                                               suppress_warning=True) / 10.0
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
                line_width = _ba.get_string_width(nline, suppress_warning=True)
            if nline != '':
                sval += nline + '\n'
            return sval

        sound_and_music = ba.Lstr(resource=self._r +
                                  '.songCreditText').evaluate()
        sound_and_music = sound_and_music.replace(
            '${TITLE}', "'William Tell (Trumpet Entry)'")
        sound_and_music = sound_and_music.replace(
            '${PERFORMER}', 'The Apollo Symphony Orchestra')
        sound_and_music = sound_and_music.replace(
            '${PERFORMER}', 'The Apollo Symphony Orchestra')
        sound_and_music = sound_and_music.replace('${COMPOSER}',
                                                  'Gioacchino Rossini')
        sound_and_music = sound_and_music.replace('${ARRANGER}', 'Chris Worth')
        sound_and_music = sound_and_music.replace('${PUBLISHER}', 'BMI')
        sound_and_music = sound_and_music.replace('${SOURCE}',
                                                  'www.AudioSparx.com')
        spc = '     '
        sound_and_music = spc + sound_and_music.replace('\n', '\n' + spc)
        names = [
            'HubOfTheUniverseProd', 'Jovica', 'LG', 'Leady', 'Percy Duke',
            'PhreaKsAccount', 'Pogotron', 'Rock Savage', 'anamorphosis',
            'benboncan', 'cdrk', 'chipfork', 'guitarguy1985', 'jascha',
            'joedeshon', 'loofa', 'm_O_m', 'mich3d', 'sandyrb', 'shakaharu',
            'sirplus', 'stickman', 'thanvannispen', 'virotic', 'zimbot'
        ]
        names.sort(key=lambda x: x.lower())
        freesound_names = _format_names(names, 90)

        try:
            with open('ba_data/data/langdata.json') as infile:
                translation_contributors = (json.loads(
                    infile.read())['translation_contributors'])
        except Exception:
            ba.print_exception('Error reading translation contributors.')
            translation_contributors = []

        translation_names = _format_names(translation_contributors, 60)

        # Need to bake this out and chop it up since we're passing our
        # 65535 vertex limit for meshes..
        # We can remove that limit once we drop support for GL ES2.. :-/
        # (or add mesh splitting under the hood)
        credits_text = (
            '  ' + ba.Lstr(resource=self._r +
                           '.codingGraphicsAudioText').evaluate().replace(
                               '${NAME}', 'Eric Froemling') + '\n'
            '\n'
            '  ' + ba.Lstr(resource=self._r +
                           '.additionalAudioArtIdeasText').evaluate().replace(
                               '${NAME}', 'Raphael Suter') + '\n'
            '\n'
            '  ' +
            ba.Lstr(resource=self._r + '.soundAndMusicText').evaluate() + '\n'
            '\n' + sound_and_music + '\n'
            '\n'
            '     ' + ba.Lstr(resource=self._r +
                              '.publicDomainMusicViaText').evaluate().replace(
                                  '${NAME}', 'Musopen.com') + '\n'
            '        ' +
            ba.Lstr(resource=self._r +
                    '.thanksEspeciallyToText').evaluate().replace(
                        '${NAME}', 'the US Army, Navy, and Marine Bands') +
            '\n'
            '\n'
            '     ' + ba.Lstr(resource=self._r +
                              '.additionalMusicFromText').evaluate().replace(
                                  '${NAME}', 'The YouTube Audio Library') +
            '\n'
            '\n'
            '     ' +
            ba.Lstr(resource=self._r + '.soundsText').evaluate().replace(
                '${SOURCE}', 'Freesound.org') + '\n'
            '\n' + freesound_names + '\n'
            '\n'
            '  ' + ba.Lstr(resource=self._r +
                           '.languageTranslationsText').evaluate() + '\n'
            '\n' + '\n'.join(translation_names.splitlines()[:146]) +
            '\n'.join(translation_names.splitlines()[146:]) + '\n'
            '\n'
            '  Shout Out to Awesome Mods / Modders:\n\n'
            '     BombDash ModPack\n'
            '     TheMikirog & SoK - BombSquad Joyride Modpack\n'
            '     Mrmaxmeier - BombSquad-Community-Mod-Manager\n'
            '\n'
            '  Holiday theme vector art designed by Freepik\n'
            '\n'
            '  ' +
            ba.Lstr(resource=self._r + '.specialThanksText').evaluate() + '\n'
            '\n'
            '     Todd, Laura, and Robert Froemling\n'
            '     ' +
            ba.Lstr(resource=self._r + '.allMyFamilyText').evaluate().replace(
                '\n', '\n     ') + '\n'
            '     ' + ba.Lstr(resource=self._r +
                              '.whoeverInventedCoffeeText').evaluate() + '\n'
            '\n'
            '  ' + ba.Lstr(resource=self._r + '.legalText').evaluate() + '\n'
            '\n'
            '     ' + ba.Lstr(resource=self._r +
                              '.softwareBasedOnText').evaluate().replace(
                                  '${NAME}', 'the Khronos Group') + '\n'
            '\n'
            '                                       '
            '                      www.froemling.net\n')

        txt = credits_text
        lines = txt.splitlines()
        line_height = 20

        scale = 0.55
        self._sub_width = width - 80
        self._sub_height = line_height * len(lines) + 40

        container = self._subcontainer = ba.containerwidget(
            parent=scroll,
            size=(self._sub_width, self._sub_height),
            background=False,
            claims_left_right=False,
            claims_tab=False)

        voffs = 0
        for line in lines:
            ba.textwidget(parent=container,
                          padding=4,
                          color=(0.7, 0.9, 0.7, 1.0),
                          scale=scale,
                          flatness=1.0,
                          size=(0, 0),
                          position=(0, self._sub_height - 20 + voffs),
                          h_align='left',
                          v_align='top',
                          text=ba.Lstr(value=line))
            voffs -= line_height

    def _back(self) -> None:
        from bastd.ui.mainmenu import MainMenuWindow
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            MainMenuWindow(transition='in_left').get_root_widget())
