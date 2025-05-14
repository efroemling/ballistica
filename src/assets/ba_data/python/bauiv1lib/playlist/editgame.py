# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for editing a game config."""

from __future__ import annotations

import copy
import random
import logging
from typing import TYPE_CHECKING, cast, override

import bascenev1 as bs
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable


class PlaylistEditGameWindow(bui.MainWindow):
    """Window for editing a game config."""

    def __init__(
        self,
        gametype: type[bs.GameActivity],
        sessiontype: type[bs.Session],
        config: dict[str, Any] | None,
        completion_call: Callable[[dict[str, Any] | None, bui.MainWindow], Any],
        default_selection: str | None = None,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        edit_info: dict[str, Any] | None = None,
    ):
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-positional-arguments
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        from bascenev1 import (
            get_filtered_map_name,
            get_map_class,
            get_map_display_string,
        )

        assert bui.app.classic is not None
        store = bui.app.classic.store

        self._gametype = gametype
        self._sessiontype = sessiontype

        # If we're within an editing session we get passed edit_info
        # (returning from map selection window, etc).
        if edit_info is not None:
            self._edit_info = edit_info

        # ..otherwise determine whether we're adding or editing a game based
        # on whether an existing config was passed to us.
        else:
            if config is None:
                self._edit_info = {'editType': 'add'}
            else:
                self._edit_info = {'editType': 'edit'}

        self._r = 'gameSettingsWindow'

        valid_maps = gametype.get_supported_maps(sessiontype)
        if not valid_maps:
            bui.screenmessage(bui.Lstr(resource='noValidMapsErrorText'))
            raise RuntimeError('No valid maps found.')

        self._config = config
        self._settings_defs = gametype.get_available_settings(sessiontype)
        self._completion_call = completion_call

        # To start with, pick a random map out of the ones we own.
        unowned_maps = store.get_unowned_maps()
        valid_maps_owned = [m for m in valid_maps if m not in unowned_maps]
        if valid_maps_owned:
            self._map = valid_maps[random.randrange(len(valid_maps_owned))]

        # Hmmm.. we own none of these maps.. just pick a random un-owned one
        # I guess.. should this ever happen?
        else:
            self._map = valid_maps[random.randrange(len(valid_maps))]

        is_add = self._edit_info['editType'] == 'add'

        # If there's a valid map name in the existing config, use that.
        try:
            if (
                config is not None
                and 'settings' in config
                and 'map' in config['settings']
            ):
                filtered_map_name = get_filtered_map_name(
                    config['settings']['map']
                )
                if filtered_map_name in valid_maps:
                    self._map = filtered_map_name
        except Exception:
            logging.exception('Error getting map for editor.')

        if config is not None and 'settings' in config:
            self._settings = config['settings']
        else:
            self._settings = {}

        self._choice_selections: dict[str, int] = {}

        uiscale = bui.app.ui_v1.uiscale
        width = 820 if uiscale is bui.UIScale.SMALL else 620
        x_inset = 100 if uiscale is bui.UIScale.SMALL else 0
        height = (
            400
            if uiscale is bui.UIScale.SMALL
            else 460 if uiscale is bui.UIScale.MEDIUM else 550
        )
        spacing = 52
        y_extra = 15
        y_extra2 = 21
        yoffs = -30 if uiscale is bui.UIScale.SMALL else 0

        map_tex_name = get_map_class(self._map).get_preview_texture_name()
        if map_tex_name is None:
            raise RuntimeError(f'No map preview tex found for {self._map}.')
        map_tex = bui.gettexture(map_tex_name)

        top_extra = 20 if uiscale is bui.UIScale.SMALL else 0
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height + top_extra),
                scale=(
                    2.3
                    if uiscale is bui.UIScale.SMALL
                    else 1.35 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, 0) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(45 + x_inset, height - 82 + y_extra2 + yoffs),
            size=(60, 48) if is_add else (180, 65),
            label=(
                bui.charstr(bui.SpecialChar.BACK)
                if is_add
                else bui.Lstr(resource='cancelText')
            ),
            button_type='backSmall' if is_add else None,
            autoselect=True,
            scale=1.0 if is_add else 0.75,
            text_scale=1.3,
            on_activate_call=bui.Call(self._cancel),
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        add_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(width - (193 + x_inset), height - 82 + y_extra2 + yoffs),
            size=(200, 65),
            scale=0.75,
            text_scale=1.3,
            label=(
                bui.Lstr(resource=f'{self._r}.addGameText')
                if is_add
                else bui.Lstr(resource='applyText')
            ),
        )

        pbtn = bui.get_special_widget('squad_button')
        bui.widget(edit=add_button, right_widget=pbtn, up_widget=pbtn)

        bui.textwidget(
            parent=self._root_widget,
            position=(-8, height - 70 + y_extra2 + yoffs),
            size=(width, 25),
            text=gametype.get_display_string(),
            color=bui.app.ui_v1.title_color,
            maxwidth=235,
            scale=1.1,
            h_align='center',
            v_align='center',
        )

        map_height = 100

        scroll_height = map_height + 10  # map select and margin

        # Calc our total height we'll need
        scroll_height += spacing * len(self._settings_defs)

        scroll_width = width - (86 + 2 * x_inset)
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(
                44 + x_inset,
                (80 if uiscale is bui.UIScale.SMALL else 35) + y_extra + yoffs,
            ),
            size=(
                scroll_width,
                height - (166 if uiscale is bui.UIScale.SMALL else 116),
            ),
            highlight=False,
            claims_left_right=True,
            selection_loops_to_parent=True,
            border_opacity=0.4,
        )
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(scroll_width, scroll_height),
            background=False,
            claims_left_right=True,
            selection_loops_to_parent=True,
        )

        v = scroll_height - 5
        h = -40

        # Keep track of all the selectable widgets we make so we can wire
        # them up conveniently.
        widget_column: list[list[bui.Widget]] = []

        # Map select button.
        bui.textwidget(
            parent=self._subcontainer,
            position=(h + 49, v - 63),
            size=(100, 30),
            maxwidth=110,
            text=bui.Lstr(resource='mapText'),
            h_align='left',
            color=(0.8, 0.8, 0.8, 1.0),
            v_align='center',
        )

        bui.imagewidget(
            parent=self._subcontainer,
            size=(256 * 0.7, 125 * 0.7),
            position=(h + 261 - 128 + 128.0 * 0.56, v - 90),
            texture=map_tex,
            mesh_opaque=bui.getmesh('level_select_button_opaque'),
            mesh_transparent=bui.getmesh('level_select_button_transparent'),
            mask_texture=bui.gettexture('mapPreviewMask'),
        )
        map_button = btn = bui.buttonwidget(
            parent=self._subcontainer,
            size=(140, 60),
            position=(h + 448, v - 72),
            on_activate_call=bui.Call(self._select_map),
            scale=0.7,
            label=bui.Lstr(resource='mapSelectText'),
        )
        widget_column.append([btn])

        bui.textwidget(
            parent=self._subcontainer,
            position=(h + 363 - 123, v - 114),
            size=(100, 30),
            flatness=1.0,
            shadow=1.0,
            scale=0.55,
            maxwidth=256 * 0.7 * 0.8,
            text=get_map_display_string(self._map),
            h_align='center',
            color=(0.6, 1.0, 0.6, 1.0),
            v_align='center',
        )
        v -= map_height

        for setting in self._settings_defs:
            value = setting.default
            value_type = type(value)

            # Now, if there's an existing value for it in the config,
            # override with that.
            try:
                if (
                    config is not None
                    and 'settings' in config
                    and setting.name in config['settings']
                ):
                    value = value_type(config['settings'][setting.name])
            except Exception:
                logging.exception('Error getting game setting.')

            # Shove the starting value in there to start.
            self._settings[setting.name] = value

            name_translated = self._get_localized_setting_name(setting.name)

            mw1 = 280
            mw2 = 70

            # Handle types with choices specially:
            if isinstance(setting, bs.ChoiceSetting):
                for choice in setting.choices:
                    if len(choice) != 2:
                        raise ValueError(
                            "Expected 2-member tuples for 'choices'; got: "
                            + repr(choice)
                        )
                    if not isinstance(choice[0], str):
                        raise TypeError(
                            'First value for choice tuple must be a str; got: '
                            + repr(choice)
                        )
                    if not isinstance(choice[1], value_type):
                        raise TypeError(
                            'Choice type does not match default value; choice:'
                            + repr(choice)
                            + '; setting:'
                            + repr(setting)
                        )
                if value_type not in (int, float):
                    raise TypeError(
                        'Choice type setting must have int or float default; '
                        'got: ' + repr(setting)
                    )

                # Start at the choice corresponding to the default if possible.
                self._choice_selections[setting.name] = 0
                for index, choice in enumerate(setting.choices):
                    if choice[1] == value:
                        self._choice_selections[setting.name] = index
                        break

                v -= spacing
                bui.textwidget(
                    parent=self._subcontainer,
                    position=(h + 50, v),
                    size=(100, 30),
                    maxwidth=mw1,
                    text=name_translated,
                    h_align='left',
                    color=(0.8, 0.8, 0.8, 1.0),
                    v_align='center',
                )
                txt = bui.textwidget(
                    parent=self._subcontainer,
                    position=(h + 509 - 95, v),
                    size=(0, 28),
                    text=self._get_localized_setting_name(
                        setting.choices[self._choice_selections[setting.name]][
                            0
                        ]
                    ),
                    editable=False,
                    color=(0.6, 1.0, 0.6, 1.0),
                    maxwidth=mw2,
                    h_align='right',
                    v_align='center',
                    padding=2,
                )
                btn1 = bui.buttonwidget(
                    parent=self._subcontainer,
                    position=(h + 509 - 50 - 1, v),
                    size=(28, 28),
                    label='<',
                    autoselect=True,
                    on_activate_call=bui.Call(
                        self._choice_inc, setting.name, txt, setting, -1
                    ),
                    repeat=True,
                )
                btn2 = bui.buttonwidget(
                    parent=self._subcontainer,
                    position=(h + 509 + 5, v),
                    size=(28, 28),
                    label='>',
                    autoselect=True,
                    on_activate_call=bui.Call(
                        self._choice_inc, setting.name, txt, setting, 1
                    ),
                    repeat=True,
                )
                widget_column.append([btn1, btn2])

            elif isinstance(setting, (bs.IntSetting, bs.FloatSetting)):
                v -= spacing
                min_value = setting.min_value
                max_value = setting.max_value
                increment = setting.increment
                bui.textwidget(
                    parent=self._subcontainer,
                    position=(h + 50, v),
                    size=(100, 30),
                    text=name_translated,
                    h_align='left',
                    color=(0.8, 0.8, 0.8, 1.0),
                    v_align='center',
                    maxwidth=mw1,
                )
                txt = bui.textwidget(
                    parent=self._subcontainer,
                    position=(h + 509 - 95, v),
                    size=(0, 28),
                    text=str(value),
                    editable=False,
                    color=(0.6, 1.0, 0.6, 1.0),
                    maxwidth=mw2,
                    h_align='right',
                    v_align='center',
                    padding=2,
                )
                btn1 = bui.buttonwidget(
                    parent=self._subcontainer,
                    position=(h + 509 - 50 - 1, v),
                    size=(28, 28),
                    label='-',
                    autoselect=True,
                    on_activate_call=bui.Call(
                        self._inc,
                        txt,
                        min_value,
                        max_value,
                        -increment,
                        value_type,
                        setting.name,
                    ),
                    repeat=True,
                )
                btn2 = bui.buttonwidget(
                    parent=self._subcontainer,
                    position=(h + 509 + 5, v),
                    size=(28, 28),
                    label='+',
                    autoselect=True,
                    on_activate_call=bui.Call(
                        self._inc,
                        txt,
                        min_value,
                        max_value,
                        increment,
                        value_type,
                        setting.name,
                    ),
                    repeat=True,
                )
                widget_column.append([btn1, btn2])

            elif value_type == bool:
                v -= spacing
                bui.textwidget(
                    parent=self._subcontainer,
                    position=(h + 50, v),
                    size=(100, 30),
                    text=name_translated,
                    h_align='left',
                    color=(0.8, 0.8, 0.8, 1.0),
                    v_align='center',
                    maxwidth=mw1,
                )
                txt = bui.textwidget(
                    parent=self._subcontainer,
                    position=(h + 509 - 95, v),
                    size=(0, 28),
                    text=(
                        bui.Lstr(resource='onText')
                        if value
                        else bui.Lstr(resource='offText')
                    ),
                    editable=False,
                    color=(0.6, 1.0, 0.6, 1.0),
                    maxwidth=mw2,
                    h_align='right',
                    v_align='center',
                    padding=2,
                )
                cbw = bui.checkboxwidget(
                    parent=self._subcontainer,
                    text='',
                    position=(h + 505 - 50 - 5, v - 2),
                    size=(200, 30),
                    autoselect=True,
                    textcolor=(0.8, 0.8, 0.8),
                    value=value,
                    on_value_change_call=bui.Call(
                        self._check_value_change, setting.name, txt
                    ),
                )
                widget_column.append([cbw])

            else:
                raise TypeError(f'Invalid value type: {value_type}.')

        # Ok now wire up the column.
        try:
            prev_widgets: list[bui.Widget] | None = None
            for cwdg in widget_column:
                if prev_widgets is not None:
                    # Wire our rightmost to their rightmost.
                    bui.widget(edit=prev_widgets[-1], down_widget=cwdg[-1])
                    bui.widget(edit=cwdg[-1], up_widget=prev_widgets[-1])

                    # Wire our leftmost to their leftmost.
                    bui.widget(edit=prev_widgets[0], down_widget=cwdg[0])
                    bui.widget(edit=cwdg[0], up_widget=prev_widgets[0])
                prev_widgets = cwdg
        except Exception:
            logging.exception(
                'Error wiring up game-settings-select widget column.'
            )

        bui.buttonwidget(edit=add_button, on_activate_call=bui.Call(self._add))
        bui.containerwidget(
            edit=self._root_widget,
            selected_child=add_button,
            start_button=add_button,
        )

        if default_selection == 'map':
            bui.containerwidget(
                edit=self._root_widget, selected_child=self._scrollwidget
            )
            bui.containerwidget(
                edit=self._subcontainer, selected_child=map_button
            )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # Pull things out of self here so we don't refer to self in the
        # lambda below which would keep us alive.
        gametype = self._gametype
        sessiontype = self._sessiontype
        config = self._config
        completion_call = self._completion_call

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
                gametype=gametype,
                sessiontype=sessiontype,
                config=config,
                completion_call=completion_call,
            )
        )

    def _get_localized_setting_name(self, name: str) -> bui.Lstr:
        return bui.Lstr(translate=('settingNames', name))

    def _select_map(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.playlist.mapselect import PlaylistMapSelectWindow

        # No-op if we're not in control.
        if not self.main_window_has_control():
            return

        self._config = self._getconfig()

        # Replace ourself with the map-select UI.
        self.main_window_replace(
            PlaylistMapSelectWindow(
                self._gametype,
                self._sessiontype,
                self._config,
                self._edit_info,
                self._completion_call,
            )
        )

    def _choice_inc(
        self,
        setting_name: str,
        widget: bui.Widget,
        setting: bs.ChoiceSetting,
        increment: int,
    ) -> None:
        choices = setting.choices
        if increment > 0:
            self._choice_selections[setting_name] = min(
                len(choices) - 1, self._choice_selections[setting_name] + 1
            )
        else:
            self._choice_selections[setting_name] = max(
                0, self._choice_selections[setting_name] - 1
            )
        bui.textwidget(
            edit=widget,
            text=self._get_localized_setting_name(
                choices[self._choice_selections[setting_name]][0]
            ),
        )
        self._settings[setting_name] = choices[
            self._choice_selections[setting_name]
        ][1]

    def _cancel(self) -> None:
        self._completion_call(None, self)

    def _check_value_change(
        self, setting_name: str, widget: bui.Widget, value: int
    ) -> None:
        bui.textwidget(
            edit=widget,
            text=(
                bui.Lstr(resource='onText')
                if value
                else bui.Lstr(resource='offText')
            ),
        )
        self._settings[setting_name] = value

    def _getconfig(self) -> dict[str, Any]:
        settings = copy.deepcopy(self._settings)
        settings['map'] = self._map
        return {'settings': settings}

    def _add(self) -> None:
        self._completion_call(self._getconfig(), self)

    def _inc(
        self,
        ctrl: bui.Widget,
        min_val: int | float,
        max_val: int | float,
        increment: int | float,
        setting_type: type,
        setting_name: str,
    ) -> None:
        # pylint: disable=too-many-positional-arguments
        if setting_type == float:
            val = float(cast(str, bui.textwidget(query=ctrl)))
        else:
            val = int(cast(str, bui.textwidget(query=ctrl)))
        val += increment
        val = max(min_val, min(val, max_val))
        if setting_type == float:
            bui.textwidget(edit=ctrl, text=str(round(val, 2)))
        elif setting_type == int:
            bui.textwidget(edit=ctrl, text=str(int(val)))
        else:
            raise TypeError('invalid vartype: ' + str(setting_type))
        self._settings[setting_name] = val
