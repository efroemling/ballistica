# Released under the MIT License. See LICENSE for details.
#
"""Provides UI to edit a player profile."""

from __future__ import annotations

import random
from typing import cast, override

from bauiv1lib.colorpicker import ColorPicker
from bauiv1lib.characterpicker import CharacterPickerDelegate
from bauiv1lib.iconpicker import IconPickerDelegate
import bauiv1 as bui
import bascenev1 as bs


class EditProfileWindow(
    bui.MainWindow, CharacterPickerDelegate, IconPickerDelegate
):
    """Window for editing a player profile."""

    def reload_window(self) -> None:
        """Transitions out and recreates ourself."""

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        # Replace ourself with ourself, but keep the same back location.
        assert self.main_window_back_state is not None
        self.main_window_replace(
            EditProfileWindow(self.getname()),
            back_state=self.main_window_back_state,
        )

    # def __del__(self) -> None:
    #     print(f'~EditProfileWindow({id(self)})')

    def __init__(
        self,
        existing_profile: str | None,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # FIXME: Tidy this up a bit.
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        assert bui.app.classic is not None
        # print(f'EditProfileWindow({id(self)})')

        plus = bui.app.plus
        assert plus is not None

        self._existing_profile = existing_profile
        self._r = 'editProfileWindow'
        self._spazzes: list[str] = []
        self._icon_textures: list[bui.Texture] = []
        self._icon_tint_textures: list[bui.Texture] = []

        # Grab profile colors or pick random ones.
        (
            self._color,
            self._highlight,
        ) = bui.app.classic.get_player_profile_colors(existing_profile)
        uiscale = bui.app.ui_v1.uiscale
        self._width = width = 880.0 if uiscale is bui.UIScale.SMALL else 680.0
        self._x_inset = x_inset = 100.0 if uiscale is bui.UIScale.SMALL else 0.0
        self._height = height = (
            500.0
            if uiscale is bui.UIScale.SMALL
            else 400.0 if uiscale is bui.UIScale.MEDIUM else 450.0
        )
        yoffs = -42 if uiscale is bui.UIScale.SMALL else 0
        spacing = 40
        self._base_scale = (
            2.0
            if uiscale is bui.UIScale.SMALL
            else 1.35 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        top_extra = 70 if uiscale is bui.UIScale.SMALL else 15
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height + top_extra),
                scale=self._base_scale,
                stack_offset=(0, 0),
                toolbar_visibility=None,
            ),
            transition=transition,
            origin_widget=origin_widget,
        )
        cancel_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(52 + x_inset, height - 60 + yoffs),
            size=(155, 60),
            scale=0.8,
            autoselect=True,
            label=bui.Lstr(resource='cancelText'),
            on_activate_call=self._cancel,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        save_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(width - (177 + x_inset), height - 60 + yoffs),
            size=(155, 60),
            autoselect=True,
            scale=0.8,
            label=bui.Lstr(resource='saveText'),
        )
        bui.widget(edit=save_button, left_widget=cancel_button)
        bui.widget(edit=cancel_button, right_widget=save_button)
        bui.containerwidget(edit=self._root_widget, start_button=btn)
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, height - 38 + yoffs),
            size=(0, 0),
            text=(
                bui.Lstr(resource=f'{self._r}.titleNewText')
                if existing_profile is None
                else bui.Lstr(resource=f'{self._r}.titleEditText')
            ),
            color=bui.app.ui_v1.title_color,
            maxwidth=290,
            scale=1.0,
            h_align='center',
            v_align='center',
        )

        # Make a list of spaz icons.
        self.refresh_characters()
        profile = bui.app.config.get('Player Profiles', {}).get(
            self._existing_profile, {}
        )

        if 'global' in profile:
            self._global = profile['global']
        else:
            self._global = False

        if 'icon' in profile:
            self._icon = profile['icon']
        else:
            self._icon = bui.charstr(bui.SpecialChar.LOGO)

        assigned_random_char = False

        # Look for existing character choice or pick random one otherwise.
        try:
            icon_index = self._spazzes.index(profile['character'])
        except Exception:
            # Let's set the default icon to spaz for our first profile; after
            # that we go random.
            # (SCRATCH THAT.. we now hard-code account-profiles to start with
            # spaz which has a similar effect)
            # try: p_len = len(bui.app.config['Player Profiles'])
            # except Exception: p_len = 0
            # if p_len == 0: icon_index = self._spazzes.index('Spaz')
            # else:
            random.seed()
            icon_index = random.randrange(len(self._spazzes))
            assigned_random_char = True
        self._icon_index = icon_index
        bui.buttonwidget(edit=save_button, on_activate_call=self.save)

        v = height - 115.0 + yoffs
        self._name = (
            '' if self._existing_profile is None else self._existing_profile
        )
        self._is_account_profile = self._name == '__account__'

        # If we just picked a random character, see if it has specific
        # colors/highlights associated with it and assign them if so.
        if assigned_random_char:
            assert bui.app.classic is not None
            clr = bui.app.classic.spaz_appearances[
                self._spazzes[icon_index]
            ].default_color
            if clr is not None:
                self._color = clr
            highlight = bui.app.classic.spaz_appearances[
                self._spazzes[icon_index]
            ].default_highlight
            if highlight is not None:
                self._highlight = highlight

        # Assign a random name if they had none.
        if self._name == '':
            names = bs.get_random_names()
            self._name = names[random.randrange(len(names))]

        self._clipped_name_text = bui.textwidget(
            parent=self._root_widget,
            text='',
            position=(580 + x_inset, v - 8),
            flatness=1.0,
            shadow=0.0,
            scale=0.55,
            size=(0, 0),
            maxwidth=100,
            h_align='center',
            v_align='center',
            color=(1, 1, 0, 0.5),
        )

        if not self._is_account_profile and not self._global:
            bui.textwidget(
                parent=self._root_widget,
                text=bui.Lstr(resource=f'{self._r}.nameText'),
                position=(200 + x_inset, v - 6),
                size=(0, 0),
                h_align='right',
                v_align='center',
                color=(1, 1, 1, 0.5),
                scale=0.9,
            )

        self._upgrade_button = None
        if self._is_account_profile:
            if plus.get_v1_account_state() == 'signed_in':
                sval = plus.get_v1_account_display_string()
            else:
                sval = '??'
            bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, v - 7),
                size=(0, 0),
                scale=1.2,
                text=sval,
                maxwidth=270,
                h_align='center',
                v_align='center',
            )
            txtl = bui.Lstr(
                resource='editProfileWindow.accountProfileText'
            ).evaluate()
            b_width = min(
                270.0,
                bui.get_string_width(txtl, suppress_warning=True) * 0.6,
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, v - 39),
                size=(0, 0),
                scale=0.6,
                color=bui.app.ui_v1.infotextcolor,
                text=txtl,
                maxwidth=270,
                h_align='center',
                v_align='center',
            )
            self._account_type_info_button = bui.buttonwidget(
                parent=self._root_widget,
                label='?',
                size=(15, 15),
                text_scale=0.6,
                position=(self._width * 0.5 + b_width * 0.5 + 13, v - 47),
                button_type='square',
                color=(0.6, 0.5, 0.65),
                autoselect=True,
                on_activate_call=self.show_account_profile_info,
            )
        elif self._global:
            b_size = 60
            self._icon_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(self._width * 0.5 - 160 - b_size * 0.5, v - 38 - 15),
                size=(b_size, b_size),
                color=(0.6, 0.5, 0.6),
                label='',
                button_type='square',
                text_scale=1.2,
                on_activate_call=self._on_icon_press,
            )
            self._icon_button_label = bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5 - 160, v - 35),
                draw_controller=btn,
                h_align='center',
                v_align='center',
                size=(0, 0),
                color=(1, 1, 1),
                text='',
                scale=2.0,
            )

            bui.textwidget(
                parent=self._root_widget,
                h_align='center',
                v_align='center',
                position=(self._width * 0.5 - 160, v - 55 - 15),
                size=(0, 0),
                draw_controller=btn,
                text=bui.Lstr(resource=f'{self._r}.iconText'),
                scale=0.7,
                color=bui.app.ui_v1.title_color,
                maxwidth=120,
            )

            self._update_icon()

            bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, v - 7),
                size=(0, 0),
                scale=1.2,
                text=self._name,
                maxwidth=240,
                h_align='center',
                v_align='center',
            )
            # FIXME hard coded strings are bad
            txtl = bui.Lstr(
                resource='editProfileWindow.globalProfileText'
            ).evaluate()
            b_width = min(
                240.0,
                bui.get_string_width(txtl, suppress_warning=True) * 0.6,
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, v - 39),
                size=(0, 0),
                scale=0.6,
                color=bui.app.ui_v1.infotextcolor,
                text=txtl,
                maxwidth=240,
                h_align='center',
                v_align='center',
            )
            self._account_type_info_button = bui.buttonwidget(
                parent=self._root_widget,
                label='?',
                size=(15, 15),
                text_scale=0.6,
                position=(self._width * 0.5 + b_width * 0.5 + 13, v - 47),
                button_type='square',
                color=(0.6, 0.5, 0.65),
                autoselect=True,
                on_activate_call=self.show_global_profile_info,
            )
        else:
            self._text_field = bui.textwidget(
                parent=self._root_widget,
                position=(220 + x_inset, v - 30),
                size=(265, 40),
                text=self._name,
                h_align='left',
                v_align='center',
                max_chars=16,
                description=bui.Lstr(resource=f'{self._r}.nameDescriptionText'),
                autoselect=True,
                editable=True,
                padding=4,
                color=(0.9, 0.9, 0.9, 1.0),
                on_return_press_call=bui.Call(save_button.activate),
            )

            # FIXME hard coded strings are bad
            txtl = bui.Lstr(
                resource='editProfileWindow.localProfileText'
            ).evaluate()
            b_width = min(
                270.0,
                bui.get_string_width(txtl, suppress_warning=True) * 0.6,
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, v - 43),
                size=(0, 0),
                scale=0.6,
                color=bui.app.ui_v1.infotextcolor,
                text=txtl,
                maxwidth=270,
                h_align='center',
                v_align='center',
            )
            self._account_type_info_button = bui.buttonwidget(
                parent=self._root_widget,
                label='?',
                size=(15, 15),
                text_scale=0.6,
                position=(self._width * 0.5 + b_width * 0.5 + 13, v - 50),
                button_type='square',
                color=(0.6, 0.5, 0.65),
                autoselect=True,
                on_activate_call=self.show_local_profile_info,
            )
            self._upgrade_button = bui.buttonwidget(
                parent=self._root_widget,
                label=bui.Lstr(resource='upgradeText'),
                size=(40, 17),
                text_scale=1.0,
                button_type='square',
                position=(self._width * 0.5 + b_width * 0.5 + 13 + 43, v - 51),
                color=(0.6, 0.5, 0.65),
                autoselect=True,
                on_activate_call=self.upgrade_profile,
            )
            self._random_name_button = bui.buttonwidget(
                parent=self._root_widget,
                label=bui.Lstr(resource='randomText'),
                size=(30, 20),
                position=(495 + x_inset, v - 20),
                button_type='square',
                color=(0.6, 0.5, 0.65),
                autoselect=True,
                on_activate_call=self.assign_random_name,
            )

        self._update_clipped_name()
        self._clipped_name_timer = bui.AppTimer(
            0.333, bui.WeakCall(self._update_clipped_name), repeat=True
        )

        v -= spacing * 3.0
        b_size = 80
        b_size_2 = 100
        b_offs = 150
        self._color_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width * 0.5 - b_offs - b_size * 0.5, v - 50),
            size=(b_size, b_size),
            color=self._color,
            label='',
            button_type='square',
        )
        origin = self._color_button.get_screen_space_center()
        bui.buttonwidget(
            edit=self._color_button,
            on_activate_call=bui.WeakCall(self._make_picker, 'color', origin),
        )
        bui.textwidget(
            parent=self._root_widget,
            h_align='center',
            v_align='center',
            position=(self._width * 0.5 - b_offs, v - 65),
            size=(0, 0),
            draw_controller=btn,
            text=bui.Lstr(resource=f'{self._r}.colorText'),
            scale=0.7,
            color=bui.app.ui_v1.title_color,
            maxwidth=120,
        )

        self._character_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width * 0.5 - b_size_2 * 0.5, v - 60),
            up_widget=self._account_type_info_button,
            on_activate_call=self._on_character_press,
            size=(b_size_2, b_size_2),
            label='',
            color=(1, 1, 1),
            mask_texture=bui.gettexture('characterIconMask'),
        )
        if not self._is_account_profile and not self._global:
            bui.containerwidget(
                edit=self._root_widget, selected_child=self._text_field
            )
        bui.textwidget(
            parent=self._root_widget,
            h_align='center',
            v_align='center',
            position=(self._width * 0.5, v - 80),
            size=(0, 0),
            draw_controller=btn,
            text=bui.Lstr(resource=f'{self._r}.characterText'),
            scale=0.7,
            color=bui.app.ui_v1.title_color,
            maxwidth=130,
        )

        self._highlight_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width * 0.5 + b_offs - b_size * 0.5, v - 50),
            up_widget=(
                self._upgrade_button
                if self._upgrade_button is not None
                else self._account_type_info_button
            ),
            size=(b_size, b_size),
            color=self._highlight,
            label='',
            button_type='square',
        )

        if not self._is_account_profile and not self._global:
            bui.widget(edit=cancel_button, down_widget=self._text_field)
            bui.widget(edit=save_button, down_widget=self._text_field)
            bui.widget(edit=self._color_button, up_widget=self._text_field)
        bui.widget(
            edit=self._account_type_info_button,
            down_widget=self._character_button,
        )

        origin = self._highlight_button.get_screen_space_center()
        bui.buttonwidget(
            edit=self._highlight_button,
            on_activate_call=bui.WeakCall(
                self._make_picker, 'highlight', origin
            ),
        )
        bui.textwidget(
            parent=self._root_widget,
            h_align='center',
            v_align='center',
            position=(self._width * 0.5 + b_offs, v - 65),
            size=(0, 0),
            draw_controller=btn,
            text=bui.Lstr(resource=f'{self._r}.highlightText'),
            scale=0.7,
            color=bui.app.ui_v1.title_color,
            maxwidth=120,
        )
        self._update_character()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # Pull things out of self here; if we do it within the lambda
        # we'll keep ourself alive which is bad.

        existing_profile = self._existing_profile
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
                existing_profile=existing_profile,
            )
        )

    def assign_random_name(self) -> None:
        """Assigning a random name to the player."""
        names = bs.get_random_names()
        name = names[random.randrange(len(names))]
        bui.textwidget(
            edit=self._text_field,
            text=name,
        )

    def upgrade_profile(self) -> None:
        """Attempt to upgrade the profile to global."""
        from bauiv1lib.account.signin import show_sign_in_prompt
        from bauiv1lib.profile import upgrade as pupgrade

        new_name = self.getname().strip()

        if self._existing_profile and self._existing_profile != new_name:
            bui.screenmessage(
                'Unsaved changes found; you must save first.', color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        plus = bui.app.plus
        assert plus is not None

        if plus.accounts.primary is None:
            show_sign_in_prompt()
            return

        pupgrade.ProfileUpgradeWindow(self)

    def show_account_profile_info(self) -> None:
        """Show an explanation of account profiles."""
        from bauiv1lib.confirm import ConfirmWindow

        icons_str = ' '.join(
            [
                bui.charstr(n)
                for n in [
                    bui.SpecialChar.GOOGLE_PLAY_GAMES_LOGO,
                    bui.SpecialChar.GAME_CENTER_LOGO,
                    bui.SpecialChar.LOCAL_ACCOUNT,
                    bui.SpecialChar.OCULUS_LOGO,
                    bui.SpecialChar.NVIDIA_LOGO,
                    bui.SpecialChar.V2_LOGO,
                ]
            ]
        )
        txtl = bui.Lstr(
            resource='editProfileWindow.accountProfileInfoText',
            subs=[('${ICONS}', icons_str)],
        )
        ConfirmWindow(
            txtl,
            cancel_button=False,
            width=500,
            height=300,
            origin_widget=self._account_type_info_button,
        )

    def show_local_profile_info(self) -> None:
        """Show an explanation of local profiles."""
        from bauiv1lib.confirm import ConfirmWindow

        txtl = bui.Lstr(resource='editProfileWindow.localProfileInfoText')
        ConfirmWindow(
            txtl,
            cancel_button=False,
            width=600,
            height=250,
            origin_widget=self._account_type_info_button,
        )

    def show_global_profile_info(self) -> None:
        """Show an explanation of global profiles."""
        from bauiv1lib.confirm import ConfirmWindow

        txtl = bui.Lstr(resource='editProfileWindow.globalProfileInfoText')
        ConfirmWindow(
            txtl,
            cancel_button=False,
            width=600,
            height=250,
            origin_widget=self._account_type_info_button,
        )

    def refresh_characters(self) -> None:
        """Refresh available characters/icons."""
        from bascenev1lib.actor import spazappearance

        assert bui.app.classic is not None

        self._spazzes = spazappearance.get_appearances()
        self._spazzes.sort()
        self._icon_textures = [
            bui.gettexture(bui.app.classic.spaz_appearances[s].icon_texture)
            for s in self._spazzes
        ]
        self._icon_tint_textures = [
            bui.gettexture(
                bui.app.classic.spaz_appearances[s].icon_mask_texture
            )
            for s in self._spazzes
        ]

    @override
    def on_icon_picker_pick(self, icon: str) -> None:
        """An icon has been selected by the picker."""
        self._icon = icon
        self._update_icon()

    @override
    def on_icon_picker_get_more_press(self) -> None:
        """User wants to get more icons."""
        from bauiv1lib.store.browser import StoreBrowserWindow

        if not self.main_window_has_control():
            return

        self.main_window_replace(
            StoreBrowserWindow(
                minimal_toolbars=True,
                show_tab=StoreBrowserWindow.TabID.ICONS,
            )
        )

    @override
    def on_character_picker_pick(self, character: str) -> None:
        """A character has been selected by the picker."""
        if not self._root_widget:
            return

        # The player could have bought a new one while the picker was
        # up.
        self.refresh_characters()
        self._icon_index = (
            self._spazzes.index(character) if character in self._spazzes else 0
        )
        self._update_character()

    @override
    def on_character_picker_get_more_press(self) -> None:
        from bauiv1lib.store.browser import StoreBrowserWindow

        if not self.main_window_has_control():
            return

        self.main_window_replace(
            StoreBrowserWindow(
                minimal_toolbars=True,
                show_tab=StoreBrowserWindow.TabID.CHARACTERS,
            )
        )

    def _on_character_press(self) -> None:
        from bauiv1lib.characterpicker import CharacterPicker

        CharacterPicker(
            parent=self._root_widget,
            position=self._character_button.get_screen_space_center(),
            selected_character=self._spazzes[self._icon_index],
            delegate=self,
            tint_color=self._color,
            tint2_color=self._highlight,
        )

    def _on_icon_press(self) -> None:
        from bauiv1lib.iconpicker import IconPicker

        IconPicker(
            parent=self._root_widget,
            position=self._icon_button.get_screen_space_center(),
            selected_icon=self._icon,
            delegate=self,
            tint_color=self._color,
            tint2_color=self._highlight,
        )

    def _make_picker(
        self, picker_type: str, origin: tuple[float, float]
    ) -> None:
        if picker_type == 'color':
            initial_color = self._color
        elif picker_type == 'highlight':
            initial_color = self._highlight
        else:
            raise ValueError('invalid picker_type: ' + picker_type)
        ColorPicker(
            parent=self._root_widget,
            position=origin,
            offset=(
                self._base_scale * (-100 if picker_type == 'color' else 100),
                0,
            ),
            initial_color=initial_color,
            delegate=self,
            tag=picker_type,
        )

    def _cancel(self) -> None:
        self.main_window_back()

    def _set_color(self, color: tuple[float, float, float]) -> None:
        self._color = color
        if self._color_button:
            bui.buttonwidget(edit=self._color_button, color=color)

    def _set_highlight(self, color: tuple[float, float, float]) -> None:
        self._highlight = color
        if self._highlight_button:
            bui.buttonwidget(edit=self._highlight_button, color=color)

    def color_picker_closing(self, picker: ColorPicker) -> None:
        """Called when a color picker is closing."""
        if not self._root_widget:
            return
        tag = picker.get_tag()
        if tag == 'color':
            bui.containerwidget(
                edit=self._root_widget, selected_child=self._color_button
            )
        elif tag == 'highlight':
            bui.containerwidget(
                edit=self._root_widget, selected_child=self._highlight_button
            )
        else:
            print('color_picker_closing got unknown tag ' + str(tag))

    def color_picker_selected_color(
        self, picker: ColorPicker, color: tuple[float, float, float]
    ) -> None:
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
        plus = bui.app.plus
        assert plus is not None

        if not self._clipped_name_text:
            return
        name = self.getname()
        if name == '__account__':
            name = (
                plus.get_v1_account_name()
                if plus.get_v1_account_state() == 'signed_in'
                else '???'
            )
        if len(name) > 10 and not (self._global or self._is_account_profile):
            name = name.strip()
            display_name = (name[:10] + '...') if len(name) > 10 else name
            bui.textwidget(
                edit=self._clipped_name_text,
                text=bui.Lstr(
                    resource='inGameClippedNameText',
                    subs=[('${NAME}', display_name)],
                ),
            )
        else:
            bui.textwidget(edit=self._clipped_name_text, text='')

    def _update_character(self, change: int = 0) -> None:
        self._icon_index = (self._icon_index + change) % len(self._spazzes)
        if self._character_button:
            bui.buttonwidget(
                edit=self._character_button,
                texture=self._icon_textures[self._icon_index],
                tint_texture=self._icon_tint_textures[self._icon_index],
                tint_color=self._color,
                tint2_color=self._highlight,
            )

    def _update_icon(self) -> None:
        if self._icon_button_label:
            bui.textwidget(edit=self._icon_button_label, text=self._icon)

    def getname(self) -> str:
        """Return the current profile name value."""
        if self._is_account_profile:
            new_name = '__account__'
        elif self._global:
            new_name = self._name
        else:
            new_name = cast(str, bui.textwidget(query=self._text_field))
        return new_name

    def save(self, transition_out: bool = True) -> bool:
        """Save has been selected."""

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return False

        plus = bui.app.plus
        assert plus is not None

        new_name = self.getname().strip()

        if not new_name:
            bui.screenmessage(bui.Lstr(resource='nameNotEmptyText'))
            bui.getsound('error').play()
            return False

        # Make sure we're not renaming to another existing profile.
        profiles: dict = bui.app.config.get('Player Profiles', {})
        if self._existing_profile != new_name and new_name in profiles.keys():
            bui.screenmessage(
                bui.Lstr(resource='editProfileWindow.profileAlreadyExistsText')
            )
            bui.getsound('error').play()
            return False

        if transition_out:
            bui.getsound('gunCocking').play()

        # Delete old in case we're renaming.
        if self._existing_profile and self._existing_profile != new_name:
            plus.add_v1_account_transaction(
                {
                    'type': 'REMOVE_PLAYER_PROFILE',
                    'name': self._existing_profile,
                }
            )

            # Also lets be aware we're no longer global if we're taking
            # a new name (will need to re-request it).
            self._global = False

        plus.add_v1_account_transaction(
            {
                'type': 'ADD_PLAYER_PROFILE',
                'name': new_name,
                'profile': {
                    'character': self._spazzes[self._icon_index],
                    'color': list(self._color),
                    'global': self._global,
                    'icon': self._icon,
                    'highlight': list(self._highlight),
                },
            }
        )

        if transition_out:
            plus.run_v1_account_transactions()
            self.main_window_back()

        return True
