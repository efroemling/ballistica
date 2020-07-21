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
"""Provides UI to edit a player profile."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, cast

import _ba
import ba

if TYPE_CHECKING:
    from typing import Tuple, Optional, List
    from bastd.ui.colorpicker import ColorPicker


class EditProfileWindow(ba.Window):
    """Window for editing a player profile."""

    # FIXME: WILL NEED TO CHANGE THIS FOR UILOCATION.
    def reload_window(self) -> None:
        """Transitions out and recreates ourself."""
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            EditProfileWindow(self.getname(),
                              self._in_main_menu).get_root_widget())

    def __init__(self,
                 existing_profile: Optional[str],
                 in_main_menu: bool,
                 transition: str = 'in_right'):
        # FIXME: Tidy this up a bit.
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        from ba.internal import get_player_profile_colors
        self._in_main_menu = in_main_menu
        self._existing_profile = existing_profile
        self._r = 'editProfileWindow'
        self._spazzes: List[str] = []
        self._icon_textures: List[ba.Texture] = []
        self._icon_tint_textures: List[ba.Texture] = []

        # Grab profile colors or pick random ones.
        self._color, self._highlight = get_player_profile_colors(
            existing_profile)
        uiscale = ba.app.ui.uiscale
        self._width = width = 780.0 if uiscale is ba.UIScale.SMALL else 680.0
        self._x_inset = x_inset = 50.0 if uiscale is ba.UIScale.SMALL else 0.0
        self._height = height = (
            350.0 if uiscale is ba.UIScale.SMALL else
            400.0 if uiscale is ba.UIScale.MEDIUM else 450.0)
        spacing = 40
        self._base_scale = (2.05 if uiscale is ba.UIScale.SMALL else
                            1.5 if uiscale is ba.UIScale.MEDIUM else 1.0)
        top_extra = 15 if uiscale is ba.UIScale.SMALL else 15
        super().__init__(root_widget=ba.containerwidget(
            size=(width, height + top_extra),
            transition=transition,
            scale=self._base_scale,
            stack_offset=(0, 15) if uiscale is ba.UIScale.SMALL else (0, 0)))
        cancel_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(52 + x_inset, height - 60),
            size=(155, 60),
            scale=0.8,
            autoselect=True,
            label=ba.Lstr(resource='cancelText'),
            on_activate_call=self._cancel)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)
        save_button = btn = ba.buttonwidget(parent=self._root_widget,
                                            position=(width - (177 + x_inset),
                                                      height - 60),
                                            size=(155, 60),
                                            autoselect=True,
                                            scale=0.8,
                                            label=ba.Lstr(resource='saveText'))
        ba.widget(edit=save_button, left_widget=cancel_button)
        ba.widget(edit=cancel_button, right_widget=save_button)
        ba.containerwidget(edit=self._root_widget, start_button=btn)
        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, height - 38),
                      size=(0, 0),
                      text=(ba.Lstr(resource=self._r + '.titleNewText')
                            if existing_profile is None else ba.Lstr(
                                resource=self._r + '.titleEditText')),
                      color=ba.app.ui.title_color,
                      maxwidth=290,
                      scale=1.0,
                      h_align='center',
                      v_align='center')

        # Make a list of spaz icons.
        self.refresh_characters()
        profile = ba.app.config.get('Player Profiles',
                                    {}).get(self._existing_profile, {})

        if 'global' in profile:
            self._global = profile['global']
        else:
            self._global = False

        if 'icon' in profile:
            self._icon = profile['icon']
        else:
            self._icon = ba.charstr(ba.SpecialChar.LOGO)

        assigned_random_char = False

        # Look for existing character choice or pick random one otherwise.
        try:
            icon_index = self._spazzes.index(profile['character'])
        except Exception:
            # Let's set the default icon to spaz for our first profile; after
            # that we go random.
            # (SCRATCH THAT.. we now hard-code account-profiles to start with
            # spaz which has a similar effect)
            # try: p_len = len(ba.app.config['Player Profiles'])
            # except Exception: p_len = 0
            # if p_len == 0: icon_index = self._spazzes.index('Spaz')
            # else:
            random.seed()
            icon_index = random.randrange(len(self._spazzes))
            assigned_random_char = True
        self._icon_index = icon_index
        ba.buttonwidget(edit=save_button, on_activate_call=self.save)

        v = height - 115.0
        self._name = ('' if self._existing_profile is None else
                      self._existing_profile)
        self._is_account_profile = (self._name == '__account__')

        # If we just picked a random character, see if it has specific
        # colors/highlights associated with it and assign them if so.
        if assigned_random_char:
            clr = ba.app.spaz_appearances[
                self._spazzes[icon_index]].default_color
            if clr is not None:
                self._color = clr
            highlight = ba.app.spaz_appearances[
                self._spazzes[icon_index]].default_highlight
            if highlight is not None:
                self._highlight = highlight

        # Assign a random name if they had none.
        if self._name == '':
            names = _ba.get_random_names()
            self._name = names[random.randrange(len(names))]

        self._clipped_name_text = ba.textwidget(parent=self._root_widget,
                                                text='',
                                                position=(540 + x_inset,
                                                          v - 8),
                                                flatness=1.0,
                                                shadow=0.0,
                                                scale=0.55,
                                                size=(0, 0),
                                                maxwidth=100,
                                                h_align='center',
                                                v_align='center',
                                                color=(1, 1, 0, 0.5))

        if not self._is_account_profile and not self._global:
            ba.textwidget(parent=self._root_widget,
                          text=ba.Lstr(resource=self._r + '.nameText'),
                          position=(200 + x_inset, v - 6),
                          size=(0, 0),
                          h_align='right',
                          v_align='center',
                          color=(1, 1, 1, 0.5),
                          scale=0.9)

        self._upgrade_button = None
        if self._is_account_profile:
            if _ba.get_account_state() == 'signed_in':
                sval = _ba.get_account_display_string()
            else:
                sval = '??'
            ba.textwidget(parent=self._root_widget,
                          position=(self._width * 0.5, v - 7),
                          size=(0, 0),
                          scale=1.2,
                          text=sval,
                          maxwidth=270,
                          h_align='center',
                          v_align='center')
            txtl = ba.Lstr(
                resource='editProfileWindow.accountProfileText').evaluate()
            b_width = min(
                270.0,
                _ba.get_string_width(txtl, suppress_warning=True) * 0.6)
            ba.textwidget(parent=self._root_widget,
                          position=(self._width * 0.5, v - 39),
                          size=(0, 0),
                          scale=0.6,
                          color=ba.app.ui.infotextcolor,
                          text=txtl,
                          maxwidth=270,
                          h_align='center',
                          v_align='center')
            self._account_type_info_button = ba.buttonwidget(
                parent=self._root_widget,
                label='?',
                size=(15, 15),
                text_scale=0.6,
                position=(self._width * 0.5 + b_width * 0.5 + 13, v - 47),
                button_type='square',
                color=(0.6, 0.5, 0.65),
                autoselect=True,
                on_activate_call=self.show_account_profile_info)
        elif self._global:

            b_size = 60
            self._icon_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(self._width * 0.5 - 160 - b_size * 0.5, v - 38 - 15),
                size=(b_size, b_size),
                color=(0.6, 0.5, 0.6),
                label='',
                button_type='square',
                text_scale=1.2,
                on_activate_call=self._on_icon_press)
            self._icon_button_label = ba.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5 - 160, v - 35),
                draw_controller=btn,
                h_align='center',
                v_align='center',
                size=(0, 0),
                color=(1, 1, 1),
                text='',
                scale=2.0)

            ba.textwidget(parent=self._root_widget,
                          h_align='center',
                          v_align='center',
                          position=(self._width * 0.5 - 160, v - 55 - 15),
                          size=(0, 0),
                          draw_controller=btn,
                          text=ba.Lstr(resource=self._r + '.iconText'),
                          scale=0.7,
                          color=ba.app.ui.title_color,
                          maxwidth=120)

            self._update_icon()

            ba.textwidget(parent=self._root_widget,
                          position=(self._width * 0.5, v - 7),
                          size=(0, 0),
                          scale=1.2,
                          text=self._name,
                          maxwidth=240,
                          h_align='center',
                          v_align='center')
            # FIXME hard coded strings are bad
            txtl = ba.Lstr(
                resource='editProfileWindow.globalProfileText').evaluate()
            b_width = min(
                240.0,
                _ba.get_string_width(txtl, suppress_warning=True) * 0.6)
            ba.textwidget(parent=self._root_widget,
                          position=(self._width * 0.5, v - 39),
                          size=(0, 0),
                          scale=0.6,
                          color=ba.app.ui.infotextcolor,
                          text=txtl,
                          maxwidth=240,
                          h_align='center',
                          v_align='center')
            self._account_type_info_button = ba.buttonwidget(
                parent=self._root_widget,
                label='?',
                size=(15, 15),
                text_scale=0.6,
                position=(self._width * 0.5 + b_width * 0.5 + 13, v - 47),
                button_type='square',
                color=(0.6, 0.5, 0.65),
                autoselect=True,
                on_activate_call=self.show_global_profile_info)
        else:
            self._text_field = ba.textwidget(
                parent=self._root_widget,
                position=(220 + x_inset, v - 30),
                size=(265, 40),
                text=self._name,
                h_align='left',
                v_align='center',
                max_chars=16,
                description=ba.Lstr(resource=self._r + '.nameDescriptionText'),
                autoselect=True,
                editable=True,
                padding=4,
                color=(0.9, 0.9, 0.9, 1.0),
                on_return_press_call=ba.Call(save_button.activate))

            # FIXME hard coded strings are bad
            txtl = ba.Lstr(
                resource='editProfileWindow.localProfileText').evaluate()
            b_width = min(
                270.0,
                _ba.get_string_width(txtl, suppress_warning=True) * 0.6)
            ba.textwidget(parent=self._root_widget,
                          position=(self._width * 0.5, v - 43),
                          size=(0, 0),
                          scale=0.6,
                          color=ba.app.ui.infotextcolor,
                          text=txtl,
                          maxwidth=270,
                          h_align='center',
                          v_align='center')
            self._account_type_info_button = ba.buttonwidget(
                parent=self._root_widget,
                label='?',
                size=(15, 15),
                text_scale=0.6,
                position=(self._width * 0.5 + b_width * 0.5 + 13, v - 50),
                button_type='square',
                color=(0.6, 0.5, 0.65),
                autoselect=True,
                on_activate_call=self.show_local_profile_info)
            self._upgrade_button = ba.buttonwidget(
                parent=self._root_widget,
                label=ba.Lstr(resource='upgradeText'),
                size=(40, 17),
                text_scale=1.0,
                button_type='square',
                position=(self._width * 0.5 + b_width * 0.5 + 13 + 43, v - 51),
                color=(0.6, 0.5, 0.65),
                autoselect=True,
                on_activate_call=self.upgrade_profile)

        self._update_clipped_name()
        self._clipped_name_timer = ba.Timer(0.333,
                                            ba.WeakCall(
                                                self._update_clipped_name),
                                            timetype=ba.TimeType.REAL,
                                            repeat=True)

        v -= spacing * 3.0
        b_size = 80
        b_size_2 = 100
        b_offs = 150
        self._color_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width * 0.5 - b_offs - b_size * 0.5, v - 50),
            size=(b_size, b_size),
            color=self._color,
            label='',
            button_type='square')
        origin = self._color_button.get_screen_space_center()
        ba.buttonwidget(edit=self._color_button,
                        on_activate_call=ba.WeakCall(self._make_picker,
                                                     'color', origin))
        ba.textwidget(parent=self._root_widget,
                      h_align='center',
                      v_align='center',
                      position=(self._width * 0.5 - b_offs, v - 65),
                      size=(0, 0),
                      draw_controller=btn,
                      text=ba.Lstr(resource=self._r + '.colorText'),
                      scale=0.7,
                      color=ba.app.ui.title_color,
                      maxwidth=120)

        self._character_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width * 0.5 - b_size_2 * 0.5, v - 60),
            up_widget=self._account_type_info_button,
            on_activate_call=self._on_character_press,
            size=(b_size_2, b_size_2),
            label='',
            color=(1, 1, 1),
            mask_texture=ba.gettexture('characterIconMask'))
        if not self._is_account_profile and not self._global:
            ba.containerwidget(edit=self._root_widget,
                               selected_child=self._text_field)
        ba.textwidget(parent=self._root_widget,
                      h_align='center',
                      v_align='center',
                      position=(self._width * 0.5, v - 80),
                      size=(0, 0),
                      draw_controller=btn,
                      text=ba.Lstr(resource=self._r + '.characterText'),
                      scale=0.7,
                      color=ba.app.ui.title_color,
                      maxwidth=130)

        self._highlight_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width * 0.5 + b_offs - b_size * 0.5, v - 50),
            up_widget=self._upgrade_button if self._upgrade_button is not None
            else self._account_type_info_button,
            size=(b_size, b_size),
            color=self._highlight,
            label='',
            button_type='square')

        if not self._is_account_profile and not self._global:
            ba.widget(edit=cancel_button, down_widget=self._text_field)
            ba.widget(edit=save_button, down_widget=self._text_field)
            ba.widget(edit=self._color_button, up_widget=self._text_field)
        ba.widget(edit=self._account_type_info_button,
                  down_widget=self._character_button)

        origin = self._highlight_button.get_screen_space_center()
        ba.buttonwidget(edit=self._highlight_button,
                        on_activate_call=ba.WeakCall(self._make_picker,
                                                     'highlight', origin))
        ba.textwidget(parent=self._root_widget,
                      h_align='center',
                      v_align='center',
                      position=(self._width * 0.5 + b_offs, v - 65),
                      size=(0, 0),
                      draw_controller=btn,
                      text=ba.Lstr(resource=self._r + '.highlightText'),
                      scale=0.7,
                      color=ba.app.ui.title_color,
                      maxwidth=120)
        self._update_character()

    def upgrade_profile(self) -> None:
        """Attempt to ugrade the profile to global."""
        from bastd.ui import account
        from bastd.ui.profile import upgrade as pupgrade
        if _ba.get_account_state() != 'signed_in':
            account.show_sign_in_prompt()
            return

        pupgrade.ProfileUpgradeWindow(self)

    def show_account_profile_info(self) -> None:
        """Show an explanation of account profiles."""
        from bastd.ui.confirm import ConfirmWindow
        icons_str = ' '.join([
            ba.charstr(n) for n in [
                ba.SpecialChar.GOOGLE_PLAY_GAMES_LOGO,
                ba.SpecialChar.GAME_CENTER_LOGO,
                ba.SpecialChar.GAME_CIRCLE_LOGO, ba.SpecialChar.OUYA_LOGO,
                ba.SpecialChar.LOCAL_ACCOUNT, ba.SpecialChar.ALIBABA_LOGO,
                ba.SpecialChar.OCULUS_LOGO, ba.SpecialChar.NVIDIA_LOGO
            ]
        ])
        txtl = ba.Lstr(resource='editProfileWindow.accountProfileInfoText',
                       subs=[('${ICONS}', icons_str)])
        ConfirmWindow(txtl,
                      cancel_button=False,
                      width=500,
                      height=300,
                      origin_widget=self._account_type_info_button)

    def show_local_profile_info(self) -> None:
        """Show an explanation of local profiles."""
        from bastd.ui.confirm import ConfirmWindow
        txtl = ba.Lstr(resource='editProfileWindow.localProfileInfoText')
        ConfirmWindow(txtl,
                      cancel_button=False,
                      width=600,
                      height=250,
                      origin_widget=self._account_type_info_button)

    def show_global_profile_info(self) -> None:
        """Show an explanation of global profiles."""
        from bastd.ui.confirm import ConfirmWindow
        txtl = ba.Lstr(resource='editProfileWindow.globalProfileInfoText')
        ConfirmWindow(txtl,
                      cancel_button=False,
                      width=600,
                      height=250,
                      origin_widget=self._account_type_info_button)

    def refresh_characters(self) -> None:
        """Refresh available characters/icons."""
        from bastd.actor import spazappearance
        self._spazzes = spazappearance.get_appearances()
        self._spazzes.sort()
        self._icon_textures = [
            ba.gettexture(ba.app.spaz_appearances[s].icon_texture)
            for s in self._spazzes
        ]
        self._icon_tint_textures = [
            ba.gettexture(ba.app.spaz_appearances[s].icon_mask_texture)
            for s in self._spazzes
        ]

    def on_icon_picker_pick(self, icon: str) -> None:
        """An icon has been selected by the picker."""
        self._icon = icon
        self._update_icon()

    def on_character_picker_pick(self, character: str) -> None:
        """A character has been selected by the picker."""
        if not self._root_widget:
            return

        # The player could have bought a new one while the picker was up.
        self.refresh_characters()
        self._icon_index = self._spazzes.index(
            character) if character in self._spazzes else 0
        self._update_character()

    def _on_character_press(self) -> None:
        from bastd.ui import characterpicker
        characterpicker.CharacterPicker(
            parent=self._root_widget,
            position=self._character_button.get_screen_space_center(),
            selected_character=self._spazzes[self._icon_index],
            delegate=self,
            tint_color=self._color,
            tint2_color=self._highlight)

    def _on_icon_press(self) -> None:
        from bastd.ui import iconpicker
        iconpicker.IconPicker(
            parent=self._root_widget,
            position=self._icon_button.get_screen_space_center(),
            selected_icon=self._icon,
            delegate=self,
            tint_color=self._color,
            tint2_color=self._highlight)

    def _make_picker(self, picker_type: str, origin: Tuple[float,
                                                           float]) -> None:
        from bastd.ui import colorpicker
        if picker_type == 'color':
            initial_color = self._color
        elif picker_type == 'highlight':
            initial_color = self._highlight
        else:
            raise ValueError('invalid picker_type: ' + picker_type)
        colorpicker.ColorPicker(
            parent=self._root_widget,
            position=origin,
            offset=(self._base_scale *
                    (-100 if picker_type == 'color' else 100), 0),
            initial_color=initial_color,
            delegate=self,
            tag=picker_type)

    def _cancel(self) -> None:
        from bastd.ui.profile.browser import ProfileBrowserWindow
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            ProfileBrowserWindow(
                'in_left',
                selected_profile=self._existing_profile,
                in_main_menu=self._in_main_menu).get_root_widget())

    def _set_color(self, color: Tuple[float, float, float]) -> None:
        self._color = color
        if self._color_button:
            ba.buttonwidget(edit=self._color_button, color=color)

    def _set_highlight(self, color: Tuple[float, float, float]) -> None:
        self._highlight = color
        if self._highlight_button:
            ba.buttonwidget(edit=self._highlight_button, color=color)

    def color_picker_closing(self, picker: ColorPicker) -> None:
        """Called when a color picker is closing."""
        if not self._root_widget:
            return
        tag = picker.get_tag()
        if tag == 'color':
            ba.containerwidget(edit=self._root_widget,
                               selected_child=self._color_button)
        elif tag == 'highlight':
            ba.containerwidget(edit=self._root_widget,
                               selected_child=self._highlight_button)
        else:
            print('color_picker_closing got unknown tag ' + str(tag))

    def color_picker_selected_color(self, picker: ColorPicker,
                                    color: Tuple[float, float, float]) -> None:
        """Called when a color is selected in a color picker."""
        if not self._root_widget:
            return
        tag = picker.get_tag()
        if tag == 'color':
            self._set_color(color)
        elif tag == 'highlight':
            self._set_highlight(color)
        else:
            print('color_picker_selected_color got unknown tag ' + str(tag))
        self._update_character()

    def _update_clipped_name(self) -> None:
        if not self._clipped_name_text:
            return
        name = self.getname()
        if name == '__account__':
            name = (_ba.get_account_name()
                    if _ba.get_account_state() == 'signed_in' else '???')
        if len(name) > 10 and not (self._global or self._is_account_profile):
            ba.textwidget(edit=self._clipped_name_text,
                          text=ba.Lstr(resource='inGameClippedNameText',
                                       subs=[('${NAME}', name[:10] + '...')]))
        else:
            ba.textwidget(edit=self._clipped_name_text, text='')

    def _update_character(self, change: int = 0) -> None:
        self._icon_index = (self._icon_index + change) % len(self._spazzes)
        if self._character_button:
            ba.buttonwidget(
                edit=self._character_button,
                texture=self._icon_textures[self._icon_index],
                tint_texture=self._icon_tint_textures[self._icon_index],
                tint_color=self._color,
                tint2_color=self._highlight)

    def _update_icon(self) -> None:
        if self._icon_button_label:
            ba.textwidget(edit=self._icon_button_label, text=self._icon)

    def getname(self) -> str:
        """Return the current profile name value."""
        if self._is_account_profile:
            new_name = '__account__'
        elif self._global:
            new_name = self._name
        else:
            new_name = cast(str, ba.textwidget(query=self._text_field))
        return new_name

    def save(self, transition_out: bool = True) -> bool:
        """Save has been selected."""
        from bastd.ui.profile.browser import ProfileBrowserWindow
        new_name = self.getname().strip()

        if not new_name:
            ba.screenmessage(ba.Lstr(resource='nameNotEmptyText'))
            ba.playsound(ba.getsound('error'))
            return False

        if transition_out:
            ba.playsound(ba.getsound('gunCocking'))

        # Delete old in case we're renaming.
        if self._existing_profile and self._existing_profile != new_name:
            _ba.add_transaction({
                'type': 'REMOVE_PLAYER_PROFILE',
                'name': self._existing_profile
            })

            # Also lets be aware we're no longer global if we're taking a
            # new name (will need to re-request it).
            self._global = False

        _ba.add_transaction({
            'type': 'ADD_PLAYER_PROFILE',
            'name': new_name,
            'profile': {
                'character': self._spazzes[self._icon_index],
                'color': list(self._color),
                'global': self._global,
                'icon': self._icon,
                'highlight': list(self._highlight)
            }
        })

        if transition_out:
            _ba.run_transactions()
            ba.containerwidget(edit=self._root_widget, transition='out_right')
            ba.app.ui.set_main_menu_window(
                ProfileBrowserWindow(
                    'in_left',
                    selected_profile=new_name,
                    in_main_menu=self._in_main_menu).get_root_widget())
        return True
