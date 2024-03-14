# Released under the MIT License. See LICENSE for details.
#
"""Provides help related ui."""

from __future__ import annotations

import bauiv1 as bui


class HelpWindow(bui.Window):
    """A window providing help on how to play."""

    def __init__(
        self, main_menu: bool = False, origin_widget: bui.Widget | None = None
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        bui.set_analytics_screen('Help Window')

        # If they provided an origin-widget, scale up from that.
        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None
            transition = 'in_right'

        self._r = 'helpWindow'

        getres = bui.app.lang.get_resource

        self._main_menu = main_menu
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1050 if uiscale is bui.UIScale.SMALL else 750
        x_offs = 150 if uiscale is bui.UIScale.SMALL else 0
        height = (
            460
            if uiscale is bui.UIScale.SMALL
            else 530 if uiscale is bui.UIScale.MEDIUM else 600
        )

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                transition=transition,
                toolbar_visibility='menu_minimal',
                scale_origin_stack_offset=scale_origin,
                scale=(
                    1.77
                    if uiscale is bui.UIScale.SMALL
                    else 1.25 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, -30)
                    if uiscale is bui.UIScale.SMALL
                    else (0, 15) if uiscale is bui.UIScale.MEDIUM else (0, 0)
                ),
            )
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(0, height - (50 if uiscale is bui.UIScale.SMALL else 45)),
            size=(width, 25),
            text=bui.Lstr(
                resource=self._r + '.titleText',
                subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
            ),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='top',
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(44 + x_offs, 55 if uiscale is bui.UIScale.SMALL else 55),
            simple_culling_v=100.0,
            size=(
                width - (88 + 2 * x_offs),
                height - 120 + (5 if uiscale is bui.UIScale.SMALL else 0),
            ),
            capture_arrows=True,
        )

        if bui.app.ui_v1.use_toolbars:
            bui.widget(
                edit=self._scrollwidget,
                right_widget=bui.get_special_widget('party_button'),
            )
        bui.containerwidget(
            edit=self._root_widget, selected_child=self._scrollwidget
        )

        # ugly: create this last so it gets first dibs at touch events (since
        # we have it close to the scroll widget)
        if uiscale is bui.UIScale.SMALL and bui.app.ui_v1.use_toolbars:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self._close
            )
            bui.widget(
                edit=self._scrollwidget,
                left_widget=bui.get_special_widget('back_button'),
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(
                    x_offs + (40 + 0 if uiscale is bui.UIScale.SMALL else 70),
                    height - (59 if uiscale is bui.UIScale.SMALL else 50),
                ),
                size=(140, 60),
                scale=0.7 if uiscale is bui.UIScale.SMALL else 0.8,
                label=(
                    bui.Lstr(resource='backText')
                    if self._main_menu
                    else 'Close'
                ),
                button_type='back' if self._main_menu else None,
                extra_touch_border_scale=2.0,
                autoselect=True,
                on_activate_call=self._close,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

            if self._main_menu:
                bui.buttonwidget(
                    edit=btn,
                    button_type='backSmall',
                    size=(60, 55),
                    label=bui.charstr(bui.SpecialChar.BACK),
                )

        self._sub_width = 660
        self._sub_height = (
            1590
            + bui.app.lang.get_resource(self._r + '.someDaysExtraSpace')
            + bui.app.lang.get_resource(
                self._r + '.orPunchingSomethingExtraSpace'
            )
        )

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
            claims_left_right=False,
            claims_tab=False,
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
            resource=self._r + '.welcomeText',
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
        txt = bui.Lstr(resource=self._r + '.someDaysText').evaluate()
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
        v -= spacing * 25.0 + getres(self._r + '.someDaysExtraSpace')
        txt_scale = 0.66
        txt = bui.Lstr(resource=self._r + '.orPunchingSomethingText').evaluate()
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
        v -= spacing * 27.0 + getres(self._r + '.orPunchingSomethingExtraSpace')
        txt_scale = 1.0
        txt = bui.Lstr(
            resource=self._r + '.canHelpText',
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
        txt = bui.Lstr(resource=self._r + '.toGetTheMostText').evaluate()
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
        txt = bui.Lstr(resource=self._r + '.friendsText').evaluate()
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
            resource=self._r + '.friendsGoodText',
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
            bui.Lstr(resource=self._r + '.devicesText').evaluate()
            if app.env.vr
            else bui.Lstr(resource=self._r + '.controllersText').evaluate()
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
                fallback_resource=self._r + '.controllersInfoText',
                subs=[
                    ('${APP_NAME}', bui.Lstr(resource='titleText')),
                    ('${REMOTE_APP_NAME}', bui.get_remote_app_name()),
                ],
            ).evaluate()
        else:
            txt = bui.Lstr(
                resource=self._r + '.devicesInfoText',
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

        txt = bui.Lstr(resource=self._r + '.controlsText').evaluate()
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
            resource=self._r + '.controlsSubtitleText',
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
        bui.imagewidget(
            parent=self._subcontainer,
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, vval2 - 0.5 * icon_size),
            texture=bui.gettexture('buttonPunch'),
            color=(1, 0.7, 0.3),
        )

        txt_scale = getres(self._r + '.punchInfoTextScale')
        txt = bui.Lstr(resource=self._r + '.punchInfoText').evaluate()
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
        bui.imagewidget(
            parent=self._subcontainer,
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, vval2 - 0.5 * icon_size),
            texture=bui.gettexture('buttonBomb'),
            color=(1, 0.3, 0.3),
        )

        txt = bui.Lstr(resource=self._r + '.bombInfoText').evaluate()
        txt_scale = getres(self._r + '.bombInfoTextScale')
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
        bui.imagewidget(
            parent=self._subcontainer,
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, vval2 - 0.5 * icon_size),
            texture=bui.gettexture('buttonPickUp'),
            color=(0.5, 0.5, 1),
        )

        txtl = bui.Lstr(resource=self._r + '.pickUpInfoText')
        txt_scale = getres(self._r + '.pickUpInfoTextScale')
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
        bui.imagewidget(
            parent=self._subcontainer,
            size=(icon_size, icon_size),
            position=(hval2 - 0.5 * icon_size, vval2 - 0.5 * icon_size),
            texture=bui.gettexture('buttonJump'),
            color=(0.4, 1, 0.4),
        )

        txt = bui.Lstr(resource=self._r + '.jumpInfoText').evaluate()
        txt_scale = getres(self._r + '.jumpInfoTextScale')
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

        txt = bui.Lstr(resource=self._r + '.runInfoText').evaluate()
        txt_scale = getres(self._r + '.runInfoTextScale')
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

        txt = bui.Lstr(resource=self._r + '.powerupsText').evaluate()
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
        txt_scale = getres(self._r + '.powerupsSubtitleTextScale')
        txt = bui.Lstr(resource=self._r + '.powerupsSubtitleText').evaluate()
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
            name = bui.Lstr(resource=self._r + '.' + tex + 'NameText')
            desc = bui.Lstr(resource=self._r + '.' + tex + 'DescriptionText')

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

    def _close(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.mainmenu import MainMenuWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        if self._main_menu:
            assert bui.app.classic is not None
            bui.app.ui_v1.set_main_menu_window(
                MainMenuWindow(transition='in_left').get_root_widget(),
                from_window=self._root_widget,
            )
