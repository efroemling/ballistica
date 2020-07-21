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
"""Provides UI for editing a game in a playlist."""

from __future__ import annotations

import copy
import random
from typing import TYPE_CHECKING, cast

import _ba
import ba

if TYPE_CHECKING:
    from typing import Type, Any, Dict, Callable, Optional, Union, List


class PlaylistEditGameWindow(ba.Window):
    """Window for editing a game in a playlist."""

    def __init__(self,
                 gameclass: Type[ba.GameActivity],
                 sessiontype: Type[ba.Session],
                 config: Optional[Dict[str, Any]],
                 completion_call: Callable[[Optional[Dict[str, Any]]], Any],
                 default_selection: str = None,
                 transition: str = 'in_right',
                 edit_info: Dict[str, Any] = None):
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        from ba.internal import (get_unowned_maps, get_filtered_map_name,
                                 get_map_class, get_map_display_string)
        self._gameclass = gameclass
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

        valid_maps = gameclass.get_supported_maps(sessiontype)
        if not valid_maps:
            ba.screenmessage(ba.Lstr(resource='noValidMapsErrorText'))
            raise Exception('No valid maps')

        self._settings_defs = gameclass.get_available_settings(sessiontype)
        self._completion_call = completion_call

        # To start with, pick a random map out of the ones we own.
        unowned_maps = get_unowned_maps()
        valid_maps_owned = [m for m in valid_maps if m not in unowned_maps]
        if valid_maps_owned:
            self._map = valid_maps[random.randrange(len(valid_maps_owned))]

        # Hmmm.. we own none of these maps.. just pick a random un-owned one
        # I guess.. should this ever happen?
        else:
            self._map = valid_maps[random.randrange(len(valid_maps))]

        is_add = (self._edit_info['editType'] == 'add')

        # If there's a valid map name in the existing config, use that.
        try:
            if (config is not None and 'settings' in config
                    and 'map' in config['settings']):
                filtered_map_name = get_filtered_map_name(
                    config['settings']['map'])
                if filtered_map_name in valid_maps:
                    self._map = filtered_map_name
        except Exception:
            ba.print_exception('Error getting map for editor.')

        if config is not None and 'settings' in config:
            self._settings = config['settings']
        else:
            self._settings = {}

        self._choice_selections: Dict[str, int] = {}

        uiscale = ba.app.ui.uiscale
        width = 720 if uiscale is ba.UIScale.SMALL else 620
        x_inset = 50 if uiscale is ba.UIScale.SMALL else 0
        height = (365 if uiscale is ba.UIScale.SMALL else
                  460 if uiscale is ba.UIScale.MEDIUM else 550)
        spacing = 52
        y_extra = 15
        y_extra2 = 21

        map_tex_name = (get_map_class(self._map).get_preview_texture_name())
        if map_tex_name is None:
            raise Exception('no map preview tex found for' + self._map)
        map_tex = ba.gettexture(map_tex_name)

        top_extra = 20 if uiscale is ba.UIScale.SMALL else 0
        super().__init__(root_widget=ba.containerwidget(
            size=(width, height + top_extra),
            transition=transition,
            scale=(2.19 if uiscale is ba.UIScale.SMALL else
                   1.35 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -17) if uiscale is ba.UIScale.SMALL else (0, 0)))

        btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(45 + x_inset, height - 82 + y_extra2),
            size=(180, 70) if is_add else (180, 65),
            label=ba.Lstr(resource='backText') if is_add else ba.Lstr(
                resource='cancelText'),
            button_type='back' if is_add else None,
            autoselect=True,
            scale=0.75,
            text_scale=1.3,
            on_activate_call=ba.Call(self._cancel))
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        add_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(width - (193 + x_inset), height - 82 + y_extra2),
            size=(200, 65),
            scale=0.75,
            text_scale=1.3,
            label=ba.Lstr(resource=self._r +
                          '.addGameText') if is_add else ba.Lstr(
                              resource='doneText'))

        if ba.app.ui.use_toolbars:
            pbtn = _ba.get_special_widget('party_button')
            ba.widget(edit=add_button, right_widget=pbtn, up_widget=pbtn)

        ba.textwidget(parent=self._root_widget,
                      position=(-8, height - 70 + y_extra2),
                      size=(width, 25),
                      text=gameclass.get_display_string(),
                      color=ba.app.ui.title_color,
                      maxwidth=235,
                      scale=1.1,
                      h_align='center',
                      v_align='center')

        map_height = 100

        scroll_height = map_height + 10  # map select and margin

        # Calc our total height we'll need
        scroll_height += spacing * len(self._settings_defs)

        scroll_width = width - (86 + 2 * x_inset)
        self._scrollwidget = ba.scrollwidget(parent=self._root_widget,
                                             position=(44 + x_inset,
                                                       35 + y_extra),
                                             size=(scroll_width, height - 116),
                                             highlight=False,
                                             claims_left_right=True,
                                             claims_tab=True,
                                             selection_loops_to_parent=True)
        self._subcontainer = ba.containerwidget(parent=self._scrollwidget,
                                                size=(scroll_width,
                                                      scroll_height),
                                                background=False,
                                                claims_left_right=True,
                                                claims_tab=True,
                                                selection_loops_to_parent=True)

        v = scroll_height - 5
        h = -40

        # Keep track of all the selectable widgets we make so we can wire
        # them up conveniently.
        widget_column: List[List[ba.Widget]] = []

        # Map select button.
        ba.textwidget(parent=self._subcontainer,
                      position=(h + 49, v - 63),
                      size=(100, 30),
                      maxwidth=110,
                      text=ba.Lstr(resource='mapText'),
                      h_align='left',
                      color=(0.8, 0.8, 0.8, 1.0),
                      v_align='center')

        ba.imagewidget(
            parent=self._subcontainer,
            size=(256 * 0.7, 125 * 0.7),
            position=(h + 261 - 128 + 128.0 * 0.56, v - 90),
            texture=map_tex,
            model_opaque=ba.getmodel('level_select_button_opaque'),
            model_transparent=ba.getmodel('level_select_button_transparent'),
            mask_texture=ba.gettexture('mapPreviewMask'))
        map_button = btn = ba.buttonwidget(
            parent=self._subcontainer,
            size=(140, 60),
            position=(h + 448, v - 72),
            on_activate_call=ba.Call(self._select_map),
            scale=0.7,
            label=ba.Lstr(resource='mapSelectText'))
        widget_column.append([btn])

        ba.textwidget(parent=self._subcontainer,
                      position=(h + 363 - 123, v - 114),
                      size=(100, 30),
                      flatness=1.0,
                      shadow=1.0,
                      scale=0.55,
                      maxwidth=256 * 0.7 * 0.8,
                      text=get_map_display_string(self._map),
                      h_align='center',
                      color=(0.6, 1.0, 0.6, 1.0),
                      v_align='center')
        v -= map_height

        for setting in self._settings_defs:
            value = setting.default
            value_type = type(value)

            # Now, if there's an existing value for it in the config,
            # override with that.
            try:
                if (config is not None and 'settings' in config
                        and setting.name in config['settings']):
                    value = value_type(config['settings'][setting.name])
            except Exception:
                ba.print_exception()

            # Shove the starting value in there to start.
            self._settings[setting.name] = value

            name_translated = self._get_localized_setting_name(setting.name)

            mw1 = 280
            mw2 = 70

            # Handle types with choices specially:
            if isinstance(setting, ba.ChoiceSetting):
                # if 'choices' in setting:
                for choice in setting.choices:
                    if len(choice) != 2:
                        raise ValueError(
                            "Expected 2-member tuples for 'choices'; got: " +
                            repr(choice))
                    if not isinstance(choice[0], str):
                        raise TypeError(
                            'First value for choice tuple must be a str; got: '
                            + repr(choice))
                    if not isinstance(choice[1], value_type):
                        raise TypeError(
                            'Choice type does not match default value; choice:'
                            + repr(choice) + '; setting:' + repr(setting))
                if value_type not in (int, float):
                    raise TypeError(
                        'Choice type setting must have int or float default; '
                        'got: ' + repr(setting))

                # Start at the choice corresponding to the default if possible.
                self._choice_selections[setting.name] = 0
                for index, choice in enumerate(setting.choices):
                    if choice[1] == value:
                        self._choice_selections[setting.name] = index
                        break

                v -= spacing
                ba.textwidget(parent=self._subcontainer,
                              position=(h + 50, v),
                              size=(100, 30),
                              maxwidth=mw1,
                              text=name_translated,
                              h_align='left',
                              color=(0.8, 0.8, 0.8, 1.0),
                              v_align='center')
                txt = ba.textwidget(
                    parent=self._subcontainer,
                    position=(h + 509 - 95, v),
                    size=(0, 28),
                    text=self._get_localized_setting_name(setting.choices[
                        self._choice_selections[setting.name]][0]),
                    editable=False,
                    color=(0.6, 1.0, 0.6, 1.0),
                    maxwidth=mw2,
                    h_align='right',
                    v_align='center',
                    padding=2)
                btn1 = ba.buttonwidget(parent=self._subcontainer,
                                       position=(h + 509 - 50 - 1, v),
                                       size=(28, 28),
                                       label='<',
                                       autoselect=True,
                                       on_activate_call=ba.Call(
                                           self._choice_inc, setting.name, txt,
                                           setting, -1),
                                       repeat=True)
                btn2 = ba.buttonwidget(parent=self._subcontainer,
                                       position=(h + 509 + 5, v),
                                       size=(28, 28),
                                       label='>',
                                       autoselect=True,
                                       on_activate_call=ba.Call(
                                           self._choice_inc, setting.name, txt,
                                           setting, 1),
                                       repeat=True)
                widget_column.append([btn1, btn2])

            elif isinstance(setting, (ba.IntSetting, ba.FloatSetting)):
                v -= spacing
                min_value = setting.min_value
                max_value = setting.max_value
                increment = setting.increment
                ba.textwidget(parent=self._subcontainer,
                              position=(h + 50, v),
                              size=(100, 30),
                              text=name_translated,
                              h_align='left',
                              color=(0.8, 0.8, 0.8, 1.0),
                              v_align='center',
                              maxwidth=mw1)
                txt = ba.textwidget(parent=self._subcontainer,
                                    position=(h + 509 - 95, v),
                                    size=(0, 28),
                                    text=str(value),
                                    editable=False,
                                    color=(0.6, 1.0, 0.6, 1.0),
                                    maxwidth=mw2,
                                    h_align='right',
                                    v_align='center',
                                    padding=2)
                btn1 = ba.buttonwidget(parent=self._subcontainer,
                                       position=(h + 509 - 50 - 1, v),
                                       size=(28, 28),
                                       label='-',
                                       autoselect=True,
                                       on_activate_call=ba.Call(
                                           self._inc, txt, min_value,
                                           max_value, -increment, value_type,
                                           setting.name),
                                       repeat=True)
                btn2 = ba.buttonwidget(parent=self._subcontainer,
                                       position=(h + 509 + 5, v),
                                       size=(28, 28),
                                       label='+',
                                       autoselect=True,
                                       on_activate_call=ba.Call(
                                           self._inc, txt, min_value,
                                           max_value, increment, value_type,
                                           setting.name),
                                       repeat=True)
                widget_column.append([btn1, btn2])

            elif value_type == bool:
                v -= spacing
                ba.textwidget(parent=self._subcontainer,
                              position=(h + 50, v),
                              size=(100, 30),
                              text=name_translated,
                              h_align='left',
                              color=(0.8, 0.8, 0.8, 1.0),
                              v_align='center',
                              maxwidth=mw1)
                txt = ba.textwidget(
                    parent=self._subcontainer,
                    position=(h + 509 - 95, v),
                    size=(0, 28),
                    text=ba.Lstr(resource='onText') if value else ba.Lstr(
                        resource='offText'),
                    editable=False,
                    color=(0.6, 1.0, 0.6, 1.0),
                    maxwidth=mw2,
                    h_align='right',
                    v_align='center',
                    padding=2)
                cbw = ba.checkboxwidget(parent=self._subcontainer,
                                        text='',
                                        position=(h + 505 - 50 - 5, v - 2),
                                        size=(200, 30),
                                        autoselect=True,
                                        textcolor=(0.8, 0.8, 0.8),
                                        value=value,
                                        on_value_change_call=ba.Call(
                                            self._check_value_change,
                                            setting.name, txt))
                widget_column.append([cbw])

            else:
                raise Exception()

        # Ok now wire up the column.
        try:
            # pylint: disable=unsubscriptable-object
            prev_widgets: Optional[List[ba.Widget]] = None
            for cwdg in widget_column:
                if prev_widgets is not None:
                    # Wire our rightmost to their rightmost.
                    ba.widget(edit=prev_widgets[-1], down_widget=cwdg[-1])
                    ba.widget(cwdg[-1], up_widget=prev_widgets[-1])

                    # Wire our leftmost to their leftmost.
                    ba.widget(edit=prev_widgets[0], down_widget=cwdg[0])
                    ba.widget(cwdg[0], up_widget=prev_widgets[0])
                prev_widgets = cwdg
        except Exception:
            ba.print_exception(
                'Error wiring up game-settings-select widget column.')

        ba.buttonwidget(edit=add_button, on_activate_call=ba.Call(self._add))
        ba.containerwidget(edit=self._root_widget,
                           selected_child=add_button,
                           start_button=add_button)

        if default_selection == 'map':
            ba.containerwidget(edit=self._root_widget,
                               selected_child=self._scrollwidget)
            ba.containerwidget(edit=self._subcontainer,
                               selected_child=map_button)

    def _get_localized_setting_name(self, name: str) -> ba.Lstr:
        return ba.Lstr(translate=('settingNames', name))

    def _select_map(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.playlist.mapselect import PlaylistMapSelectWindow

        # Replace ourself with the map-select UI.
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            PlaylistMapSelectWindow(self._gameclass, self._sessiontype,
                                    copy.deepcopy(self._getconfig()),
                                    self._edit_info,
                                    self._completion_call).get_root_widget())

    def _choice_inc(self, setting_name: str, widget: ba.Widget,
                    setting: ba.ChoiceSetting, increment: int) -> None:
        choices = setting.choices
        if increment > 0:
            self._choice_selections[setting_name] = min(
                len(choices) - 1, self._choice_selections[setting_name] + 1)
        else:
            self._choice_selections[setting_name] = max(
                0, self._choice_selections[setting_name] - 1)
        ba.textwidget(edit=widget,
                      text=self._get_localized_setting_name(
                          choices[self._choice_selections[setting_name]][0]))
        self._settings[setting_name] = choices[
            self._choice_selections[setting_name]][1]

    def _cancel(self) -> None:
        self._completion_call(None)

    def _check_value_change(self, setting_name: str, widget: ba.Widget,
                            value: int) -> None:
        ba.textwidget(edit=widget,
                      text=ba.Lstr(resource='onText') if value else ba.Lstr(
                          resource='offText'))
        self._settings[setting_name] = value

    def _getconfig(self) -> Dict[str, Any]:
        settings = copy.deepcopy(self._settings)
        settings['map'] = self._map
        return {'settings': settings}

    def _add(self) -> None:
        self._completion_call(copy.deepcopy(self._getconfig()))

    def _inc(self, ctrl: ba.Widget, min_val: Union[int, float],
             max_val: Union[int, float], increment: Union[int, float],
             setting_type: Type, setting_name: str) -> None:
        if setting_type == float:
            val = float(cast(str, ba.textwidget(query=ctrl)))
        else:
            val = int(cast(str, ba.textwidget(query=ctrl)))
        val += increment
        val = max(min_val, min(val, max_val))
        if setting_type == float:
            ba.textwidget(edit=ctrl, text=str(round(val, 2)))
        elif setting_type == int:
            ba.textwidget(edit=ctrl, text=str(int(val)))
        else:
            raise TypeError('invalid vartype: ' + str(setting_type))
        self._settings[setting_name] = val
