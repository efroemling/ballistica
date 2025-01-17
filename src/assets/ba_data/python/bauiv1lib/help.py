# Released under the MIT License. See LICENSE for details.
#
"""Provides help related ui."""

from __future__ import annotations

from typing import override

import random

import bauiv1 as bui


class HelpWindow(bui.MainWindow):
    """A window providing help on how to play."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('Help Window')

        self._r = 'helpWindow'

        getres = bui.app.lang.get_resource

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1050 if uiscale is bui.UIScale.SMALL else 750
        xoffs = 70 if uiscale is bui.UIScale.SMALL else 0
        yoffs = -33 if uiscale is bui.UIScale.SMALL else 0

        height = (
            500
            if uiscale is bui.UIScale.SMALL
            else 530 if uiscale is bui.UIScale.MEDIUM else 600
        )

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=(
                    1.55
                    if uiscale is bui.UIScale.SMALL
                    else 1.15 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, 0)
                    if uiscale is bui.UIScale.SMALL
                    else (0, 15) if uiscale is bui.UIScale.MEDIUM else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(
                0,
                height - (50 if uiscale is bui.UIScale.SMALL else 45) + yoffs,
            ),
            size=(width, 25),
            text=bui.Lstr(
                resource=f'{self._r}.titleText',
                subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
            ),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='top',
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(
                44 + xoffs,
                (92 if uiscale is bui.UIScale.SMALL else 55) + yoffs,
            ),
            simple_culling_v=100.0,
            size=(
                width - (88 + 2 * xoffs),
                height - (150 if uiscale is bui.UIScale.SMALL else 120),
            ),
            capture_arrows=True,
            border_opacity=0.4,
        )

        bui.widget(
            edit=self._scrollwidget,
            right_widget=bui.get_special_widget('squad_button'),
        )
        bui.containerwidget(
            edit=self._root_widget, selected_child=self._scrollwidget
        )

        # ugly: create this last so it gets first dibs at touch events (since
        # we have it close to the scroll widget)
        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            bui.widget(
                edit=self._scrollwidget,
                left_widget=bui.get_special_widget('back_button'),
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(xoffs + 50, height - 55),
                size=(60, 55),
                scale=0.8,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                extra_touch_border_scale=2.0,
                autoselect=True,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        self._sub_width = 810 if uiscale is bui.UIScale.SMALL else 660
        self._sub_height = (
            1590
            + bui.app.lang.get_resource(f'{self._r}.someDaysExtraSpace')
            + bui.app.lang.get_resource(
                f'{self._r}.orPunchingSomethingExtraSpace'
            )
        )

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
            claims_left_right=False,
        )

        spacing = 1.0
        h = self._sub_width * 0.5
        v = self._sub_height - 55
        logo_tex = bui.gettexture('logo')
        icon_buffer = 1.1
        header = (0.7, 1.0, 0.7, 1.0)
        header2 = (0.8, 0.8, 1.0, 1.0)
        paragraph = (0.8, 0.8, 1.0, 1.0)

        txt = bui.Lstr(
            resource=f'{self._r}.welcomeText',
            subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
        ).evaluate()
        txt_scale = 1.4
        txt_maxwidth = 480
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            res_scale=1.5,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            maxwidth=txt_maxwidth,
        )
        txt_width = min(
            txt_maxwidth,
            bui.get_string_width(txt, suppress_warning=True) * txt_scale,
        )

        icon_size = 70
        hval2 = h - (txt_width * 0.5 + icon_size * 0.5 * icon_buffer)
        bui.imagewidget(
            parent=self._subcontainer,
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, v - 0.45 * icon_size),
            texture=logo_tex,
        )

        app = bui.app
        assert app.classic is not None

        v -= spacing * 50.0
        txt = bui.Lstr(resource=f'{self._r}.someDaysText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=1.2,
            maxwidth=self._sub_width * 0.9,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
            flatness=1.0,
        )
        v -= spacing * 25.0 + getres(f'{self._r}.someDaysExtraSpace')
        txt_scale = 0.66
        txt = bui.Lstr(resource=f'{self._r}.orPunchingSomethingText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.9,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
            flatness=1.0,
        )
        v -= spacing * 27.0 + getres(f'{self._r}.orPunchingSomethingExtraSpace')
        txt_scale = 1.0
        txt = bui.Lstr(
            resource=f'{self._r}.canHelpText',
            subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
        ).evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=1.0,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
        )

        v -= spacing * 70.0
        txt_scale = 1.0
        txt = bui.Lstr(resource=f'{self._r}.toGetTheMostText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.9,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            flatness=1.0,
        )

        v -= spacing * 40.0
        txt_scale = 0.74
        txt = bui.Lstr(resource=f'{self._r}.friendsText').evaluate()
        hval2 = h - 220
        bui.textwidget(
            parent=self._subcontainer,
            position=(hval2, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=100,
            text=txt,
            h_align='right',
            color=header,
            v_align='center',
            flatness=1.0,
        )

        txt = bui.Lstr(
            resource=f'{self._r}.friendsGoodText',
            subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
        ).evaluate()
        txt_scale = 0.7
        bui.textwidget(
            parent=self._subcontainer,
            position=(hval2 + 10, v + 8),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=500,
            text=txt,
            h_align='left',
            color=paragraph,
            flatness=1.0,
        )

        app = bui.app

        v -= spacing * 45.0
        txt = (
            bui.Lstr(resource=f'{self._r}.devicesText').evaluate()
            if app.env.vr
            else bui.Lstr(resource=f'{self._r}.controllersText').evaluate()
        )
        txt_scale = 0.74
        hval2 = h - 220
        bui.textwidget(
            parent=self._subcontainer,
            position=(hval2, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=100,
            text=txt,
            h_align='right',
            v_align='center',
            color=header,
            flatness=1.0,
        )

        txt_scale = 0.7
        if not app.env.vr:
            infotxt = '.controllersInfoText'
            txt = bui.Lstr(
                resource=self._r + infotxt,
                fallback_resource=f'{self._r}.controllersInfoText',
                subs=[
                    ('${APP_NAME}', bui.Lstr(resource='titleText')),
                    ('${REMOTE_APP_NAME}', bui.get_remote_app_name()),
                ],
            ).evaluate()
        else:
            txt = bui.Lstr(
                resource=f'{self._r}.devicesInfoText',
                subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
            ).evaluate()

        bui.textwidget(
            parent=self._subcontainer,
            position=(hval2 + 10, v + 8),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=500,
            max_height=105,
            text=txt,
            h_align='left',
            color=paragraph,
            flatness=1.0,
        )

        v -= spacing * 150.0

        txt = bui.Lstr(resource=f'{self._r}.controlsText').evaluate()
        txt_scale = 1.4
        txt_maxwidth = 480
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            res_scale=1.5,
            maxwidth=txt_maxwidth,
        )
        txt_width = min(
            txt_maxwidth,
            bui.get_string_width(txt, suppress_warning=True) * txt_scale,
        )
        icon_size = 70

        hval2 = h - (txt_width * 0.5 + icon_size * 0.5 * icon_buffer)
        bui.imagewidget(
            parent=self._subcontainer,
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, v - 0.45 * icon_size),
            texture=logo_tex,
        )

        v -= spacing * 45.0

        txt_scale = 0.7
        txt = bui.Lstr(
            resource=f'{self._r}.controlsSubtitleText',
            subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
        ).evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.9,
            flatness=1.0,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
        )
        v -= spacing * 160.0

        sep = 70
        icon_size = 100
        # icon_size_2 = 30
        hval2 = h - sep
        vval2 = v
        bui.buttonwidget(
            parent=self._subcontainer,
            label='',
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, vval2 - 0.5 * icon_size),
            texture=bui.gettexture('buttonPunch'),
            color=(1, 0.7, 0.3),
            selectable=False,
            enable_sound=False,
            on_activate_call=bui.WeakCall(self._play_sound, 'spazAttack0', 4),
        )

        txt_scale = getres(f'{self._r}.punchInfoTextScale')
        txt = bui.Lstr(resource=f'{self._r}.punchInfoText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h - sep - 185 + 70, v + 120),
            size=(0, 0),
            scale=txt_scale,
            flatness=1.0,
            text=txt,
            h_align='center',
            color=(1, 0.7, 0.3, 1.0),
            v_align='top',
        )

        hval2 = h + sep
        vval2 = v
        bui.buttonwidget(
            parent=self._subcontainer,
            label='',
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, vval2 - 0.5 * icon_size),
            texture=bui.gettexture('buttonBomb'),
            color=(1, 0.3, 0.3),
            selectable=False,
            enable_sound=False,
            on_activate_call=bui.WeakCall(self._play_sound, 'explosion0', 5),
        )

        txt = bui.Lstr(resource=f'{self._r}.bombInfoText').evaluate()
        txt_scale = getres(f'{self._r}.bombInfoTextScale')
        bui.textwidget(
            parent=self._subcontainer,
            position=(h + sep + 50 + 60, v - 35),
            size=(0, 0),
            scale=txt_scale,
            flatness=1.0,
            maxwidth=270,
            text=txt,
            h_align='center',
            color=(1, 0.3, 0.3, 1.0),
            v_align='top',
        )

        hval2 = h
        vval2 = v + sep
        bui.buttonwidget(
            parent=self._subcontainer,
            label='',
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, vval2 - 0.5 * icon_size),
            texture=bui.gettexture('buttonPickUp'),
            color=(0.5, 0.5, 1),
            selectable=False,
            enable_sound=False,
            on_activate_call=bui.WeakCall(self._play_sound, 'spazPickup0', 1),
        )

        txtl = bui.Lstr(resource=f'{self._r}.pickUpInfoText')
        txt_scale = getres(f'{self._r}.pickUpInfoTextScale')
        bui.textwidget(
            parent=self._subcontainer,
            position=(h + 60 + 120, v + sep + 50),
            size=(0, 0),
            scale=txt_scale,
            flatness=1.0,
            text=txtl,
            h_align='center',
            color=(0.5, 0.5, 1, 1.0),
            v_align='top',
        )

        hval2 = h
        vval2 = v - sep
        bui.buttonwidget(
            parent=self._subcontainer,
            label='',
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, vval2 - 0.5 * icon_size),
            texture=bui.gettexture('buttonJump'),
            color=(0.4, 1, 0.4),
            selectable=False,
            enable_sound=False,
            on_activate_call=bui.WeakCall(self._play_sound, 'spazJump0', 4),
        )

        txt = bui.Lstr(resource=f'{self._r}.jumpInfoText').evaluate()
        txt_scale = getres(f'{self._r}.jumpInfoTextScale')
        bui.textwidget(
            parent=self._subcontainer,
            position=(h - 250 + 75, v - sep - 15 + 30),
            size=(0, 0),
            scale=txt_scale,
            flatness=1.0,
            text=txt,
            h_align='center',
            color=(0.4, 1, 0.4, 1.0),
            v_align='top',
        )

        txt = bui.Lstr(resource=f'{self._r}.runInfoText').evaluate()
        txt_scale = getres(f'{self._r}.runInfoTextScale')
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v - sep - 100),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.93,
            flatness=1.0,
            text=txt,
            h_align='center',
            color=(0.7, 0.7, 1.0, 1.0),
            v_align='center',
        )

        v -= spacing * 280.0

        txt = bui.Lstr(resource=f'{self._r}.powerupsText').evaluate()
        txt_scale = 1.4
        txt_maxwidth = 480
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            flatness=0.5,
            text=txt,
            h_align='center',
            color=header,
            v_align='center',
            maxwidth=txt_maxwidth,
        )
        txt_width = min(
            txt_maxwidth,
            bui.get_string_width(txt, suppress_warning=True) * txt_scale,
        )
        icon_size = 70
        hval2 = h - (txt_width * 0.5 + icon_size * 0.5 * icon_buffer)
        bui.imagewidget(
            parent=self._subcontainer,
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, v - 0.45 * icon_size),
            texture=logo_tex,
        )

        v -= spacing * 50.0
        txt_scale = getres(f'{self._r}.powerupsSubtitleTextScale')
        txt = bui.Lstr(resource=f'{self._r}.powerupsSubtitleText').evaluate()
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v),
            size=(0, 0),
            scale=txt_scale,
            maxwidth=self._sub_width * 0.9,
            text=txt,
            h_align='center',
            color=paragraph,
            v_align='center',
            flatness=1.0,
        )

        v -= spacing * 1.0

        mm1 = -270
        mm2 = -215
        mm3 = 0
        icon_size = 50
        shadow_size = 80
        shadow_offs_x = 3
        shadow_offs_y = -4
        t_big = 1.1
        t_small = 0.65

        shadow_tex = bui.gettexture('shadowSharp')

        for tex in [
            'powerupPunch',
            'powerupShield',
            'powerupBomb',
            'powerupHealth',
            'powerupIceBombs',
            'powerupImpactBombs',
            'powerupStickyBombs',
            'powerupLandMines',
            'powerupCurse',
        ]:
            name = bui.Lstr(resource=f'{self._r}.' + tex + 'NameText')
            desc = bui.Lstr(resource=f'{self._r}.' + tex + 'DescriptionText')

            v -= spacing * 60.0

            bui.imagewidget(
                parent=self._subcontainer,
                size=(shadow_size, shadow_size),
                position=(
                    h + mm1 + shadow_offs_x - 0.5 * shadow_size,
                    v + shadow_offs_y - 0.5 * shadow_size,
                ),
                texture=shadow_tex,
                color=(0, 0, 0),
                opacity=0.5,
            )
            bui.imagewidget(
                parent=self._subcontainer,
                size=(icon_size, icon_size),
                position=(h + mm1 - 0.5 * icon_size, v - 0.5 * icon_size),
                texture=bui.gettexture(tex),
            )

            txt_scale = t_big
            txtl = name
            bui.textwidget(
                parent=self._subcontainer,
                position=(h + mm2, v + 3),
                size=(0, 0),
                scale=txt_scale,
                maxwidth=200,
                flatness=1.0,
                text=txtl,
                h_align='left',
                color=header2,
                v_align='center',
            )
            txt_scale = t_small
            txtl = desc
            bui.textwidget(
                parent=self._subcontainer,
                position=(h + mm3, v),
                size=(0, 0),
                scale=txt_scale,
                maxwidth=300,
                flatness=1.0,
                text=txtl,
                h_align='left',
                color=paragraph,
                v_align='center',
                res_scale=0.5,
            )

    def _play_sound(self, text: str, num: int) -> None:
        bui.getsound(text + str(random.randint(1, num))).play()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )
