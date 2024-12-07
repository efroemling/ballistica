# Released under the MIT License. See LICENSE for details.
#
"""Defines Actors related to controls guides."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any, Sequence


class ControlsGuide(bs.Actor):
    """A screen overlay of game controls.

    category: Gameplay Classes

    Shows button mappings based on what controllers are connected.
    Handy to show at the start of a series or whenever there might
    be newbies watching.
    """

    def __init__(
        self,
        *,
        position: tuple[float, float] = (390.0, 120.0),
        scale: float = 1.0,
        delay: float = 0.0,
        lifespan: float | None = None,
        bright: bool = False,
    ):
        """Instantiate an overlay.

        delay: is the time in seconds before the overlay fades in.

        lifespan: if not None, the overlay will fade back out and die after
                  that long (in seconds).

        bright: if True, brighter colors will be used; handy when showing
                over gameplay but may be too bright for join-screens, etc.
        """
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        super().__init__()
        show_title = True
        scale *= 0.75
        image_size = 90.0 * scale
        offs = 74.0 * scale
        offs5 = 43.0 * scale
        ouya = False
        maxw = 50
        xtweak = -2.8 * scale
        self._lifespan = lifespan
        self._dead = False
        self._bright = bright
        self._cancel_timer: bs.Timer | None = None
        self._fade_in_timer: bs.Timer | None = None
        self._update_timer: bs.Timer | None = None
        self._title_text: bs.Node | None
        clr: Sequence[float]
        punch_pos = (position[0] - offs * 1.1, position[1])
        jump_pos = (position[0], position[1] - offs)
        bomb_pos = (position[0] + offs * 1.1, position[1])
        pickup_pos = (position[0], position[1] + offs)
        self._force_hide_button_names = False

        if show_title:
            self._title_text_pos_top = (
                position[0],
                position[1] + 139.0 * scale,
            )
            self._title_text_pos_bottom = (
                position[0],
                position[1] + 139.0 * scale,
            )
            clr = (1, 1, 1) if bright else (0.7, 0.7, 0.7)
            tval = bs.Lstr(
                value='${A}:', subs=[('${A}', bs.Lstr(resource='controlsText'))]
            )
            self._title_text = bs.newnode(
                'text',
                attrs={
                    'text': tval,
                    'host_only': True,
                    'scale': 1.1 * scale,
                    'shadow': 0.5,
                    'flatness': 1.0,
                    'maxwidth': 480,
                    'v_align': 'center',
                    'h_align': 'center',
                    'color': clr,
                },
            )
        else:
            self._title_text = None
        pos = jump_pos
        clr = (0.4, 1, 0.4)
        self._jump_image = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('buttonJump'),
                'absolute_scale': True,
                'host_only': True,
                'vr_depth': 10,
                'position': pos,
                'scale': (image_size, image_size),
                'color': clr,
            },
        )
        self._jump_text = bs.newnode(
            'text',
            attrs={
                'v_align': 'top',
                'h_align': 'center',
                'scale': 1.5 * scale,
                'flatness': 1.0,
                'host_only': True,
                'shadow': 1.0,
                'maxwidth': maxw,
                'position': (pos[0] + xtweak, pos[1] - offs5),
                'color': clr,
            },
        )
        clr = (0.2, 0.6, 1) if ouya else (1, 0.7, 0.3)
        pos = punch_pos
        self._punch_image = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('buttonPunch'),
                'absolute_scale': True,
                'host_only': True,
                'vr_depth': 10,
                'position': pos,
                'scale': (image_size, image_size),
                'color': clr,
            },
        )
        self._punch_text = bs.newnode(
            'text',
            attrs={
                'v_align': 'top',
                'h_align': 'center',
                'scale': 1.5 * scale,
                'flatness': 1.0,
                'host_only': True,
                'shadow': 1.0,
                'maxwidth': maxw,
                'position': (pos[0] + xtweak, pos[1] - offs5),
                'color': clr,
            },
        )
        pos = bomb_pos
        clr = (1, 0.3, 0.3)
        self._bomb_image = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('buttonBomb'),
                'absolute_scale': True,
                'host_only': True,
                'vr_depth': 10,
                'position': pos,
                'scale': (image_size, image_size),
                'color': clr,
            },
        )
        self._bomb_text = bs.newnode(
            'text',
            attrs={
                'h_align': 'center',
                'v_align': 'top',
                'scale': 1.5 * scale,
                'flatness': 1.0,
                'host_only': True,
                'shadow': 1.0,
                'maxwidth': maxw,
                'position': (pos[0] + xtweak, pos[1] - offs5),
                'color': clr,
            },
        )
        pos = pickup_pos
        clr = (1, 0.8, 0.3) if ouya else (0.8, 0.5, 1)
        self._pickup_image = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('buttonPickUp'),
                'absolute_scale': True,
                'host_only': True,
                'vr_depth': 10,
                'position': pos,
                'scale': (image_size, image_size),
                'color': clr,
            },
        )
        self._pick_up_text = bs.newnode(
            'text',
            attrs={
                'v_align': 'top',
                'h_align': 'center',
                'scale': 1.5 * scale,
                'flatness': 1.0,
                'host_only': True,
                'shadow': 1.0,
                'maxwidth': maxw,
                'position': (pos[0] + xtweak, pos[1] - offs5),
                'color': clr,
            },
        )
        clr = (0.9, 0.9, 2.0, 1.0) if bright else (0.8, 0.8, 2.0, 1.0)
        self._run_text_pos_top = (position[0], position[1] - 135.0 * scale)
        self._run_text_pos_bottom = (position[0], position[1] - 172.0 * scale)
        sval = 1.0 * scale if bs.app.env.vr else 0.8 * scale
        self._run_text = bs.newnode(
            'text',
            attrs={
                'scale': sval,
                'host_only': True,
                'shadow': 1.0 if bs.app.env.vr else 0.5,
                'flatness': 1.0,
                'maxwidth': 380,
                'v_align': 'top',
                'h_align': 'center',
                'color': clr,
            },
        )
        clr = (1, 1, 1) if bright else (0.7, 0.7, 0.7)
        self._extra_text = bs.newnode(
            'text',
            attrs={
                'scale': 0.8 * scale,
                'host_only': True,
                'shadow': 0.5,
                'flatness': 1.0,
                'maxwidth': 380,
                'v_align': 'top',
                'h_align': 'center',
                'color': clr,
            },
        )

        self._extra_image_1 = None
        self._extra_image_2 = None

        self._nodes = [
            self._bomb_image,
            self._bomb_text,
            self._punch_image,
            self._punch_text,
            self._jump_image,
            self._jump_text,
            self._pickup_image,
            self._pick_up_text,
            self._run_text,
            self._extra_text,
        ]
        if show_title:
            assert self._title_text
            self._nodes.append(self._title_text)

        # Start everything invisible.
        for node in self._nodes:
            node.opacity = 0.0

        # Don't do anything until our delay has passed.
        bs.timer(delay, bs.WeakCall(self._start_updating))

    @staticmethod
    def _meaningful_button_name(
        device: bs.InputDevice, button_name: str
    ) -> str:
        """Return a flattened string button name; empty for non-meaningful."""
        if not device.has_meaningful_button_names:
            return ''
        assert bs.app.classic is not None
        button = bs.app.classic.get_input_device_mapped_value(
            device, button_name
        )
        # -1 means unset; let's show that.
        if button == -1:
            return bs.Lstr(resource='configGamepadWindow.unsetText').evaluate()
        return device.get_button_name(button).evaluate()

    def _start_updating(self) -> None:
        # Ok, our delay has passed. Now lets periodically see if we can fade
        # in (if a touch-screen is present we only want to show up if gamepads
        # are connected, etc).
        # Also set up a timer so if we haven't faded in by the end of our
        # duration, abort.
        if self._lifespan is not None:
            self._cancel_timer = bs.Timer(
                self._lifespan,
                bs.WeakCall(self.handlemessage, bs.DieMessage(immediate=True)),
            )
        self._fade_in_timer = bs.Timer(
            1.0, bs.WeakCall(self._check_fade_in), repeat=True
        )
        self._check_fade_in()  # Do one check immediately.

    def _check_fade_in(self) -> None:
        assert bs.app.classic is not None

        # If we have a touchscreen, we only fade in if we have a player
        # with an input device that is *not* the touchscreen. Otherwise
        # it is confusing to see the touchscreen buttons right next to
        # our display buttons.
        touchscreen: bs.InputDevice | None = bs.getinputdevice(
            'TouchScreen', '#1', doraise=False
        )

        if touchscreen is not None:
            # We look at the session's players; not the activity's.
            # We want to get ones who are still in the process of
            # selecting a character, etc.
            input_devices = [
                p.inputdevice for p in bs.getsession().sessionplayers
            ]
            input_devices = [
                i for i in input_devices if i and i is not touchscreen
            ]
            fade_in = False
            if input_devices:
                # Only count this one if it has non-empty button names
                # (filters out wiimotes, the remote-app, etc).
                for device in input_devices:
                    for name in (
                        'buttonPunch',
                        'buttonJump',
                        'buttonBomb',
                        'buttonPickUp',
                    ):
                        if self._meaningful_button_name(device, name) != '':
                            fade_in = True
                            break
                    if fade_in:
                        break  # No need to keep looking.
        else:
            # No touch-screen; fade in immediately.
            fade_in = True
        if fade_in:
            self._cancel_timer = None  # Didn't need this.
            self._fade_in_timer = None  # Done with this.
            self._fade_in()

    def _fade_in(self) -> None:
        for node in self._nodes:
            bs.animate(node, 'opacity', {0: 0.0, 2.0: 1.0})

        # If we were given a lifespan, transition out after it.
        if self._lifespan is not None:
            bs.timer(
                self._lifespan, bs.WeakCall(self.handlemessage, bs.DieMessage())
            )
        self._update()
        self._update_timer = bs.Timer(
            1.0, bs.WeakCall(self._update), repeat=True
        )

    def _update(self) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals

        if self._dead:
            return

        classic = bs.app.classic
        assert classic is not None

        punch_button_names = set()
        jump_button_names = set()
        pickup_button_names = set()
        bomb_button_names = set()

        # We look at the session's players; not the activity's - we want to
        # get ones who are still in the process of selecting a character, etc.
        input_devices = [p.inputdevice for p in bs.getsession().sessionplayers]
        input_devices = [i for i in input_devices if i]

        # If there's no players with input devices yet, try to default to
        # showing keyboard controls.
        if not input_devices:
            kbd = bs.getinputdevice('Keyboard', '#1', doraise=False)
            if kbd is not None:
                input_devices.append(kbd)

        # We word things specially if we have nothing but keyboards.
        all_keyboards = input_devices and all(
            i.name == 'Keyboard' for i in input_devices
        )
        only_remote = len(input_devices) == 1 and all(
            i.name == 'Amazon Fire TV Remote' for i in input_devices
        )

        right_button_names = set()
        left_button_names = set()
        up_button_names = set()
        down_button_names = set()

        # For each player in the game with an input device,
        # get the name of the button for each of these 4 actions.
        # If any of them are uniform across all devices, display the name.
        for device in input_devices:
            # We only care about movement buttons in the case of keyboards.
            if all_keyboards:
                right_button_names.add(
                    self._meaningful_button_name(device, 'buttonRight')
                )
                left_button_names.add(
                    self._meaningful_button_name(device, 'buttonLeft')
                )
                down_button_names.add(
                    self._meaningful_button_name(device, 'buttonDown')
                )
                up_button_names.add(
                    self._meaningful_button_name(device, 'buttonUp')
                )

            # Ignore empty values; things like the remote app or
            # wiimotes can return these.
            bname = self._meaningful_button_name(device, 'buttonPunch')
            if bname != '':
                punch_button_names.add(bname)
            bname = self._meaningful_button_name(device, 'buttonJump')
            if bname != '':
                jump_button_names.add(bname)
            bname = self._meaningful_button_name(device, 'buttonBomb')
            if bname != '':
                bomb_button_names.add(bname)
            bname = self._meaningful_button_name(device, 'buttonPickUp')
            if bname != '':
                pickup_button_names.add(bname)

        # If we have no values yet, we may want to throw out some sane
        # defaults.
        if all(
            not lst
            for lst in (
                punch_button_names,
                jump_button_names,
                bomb_button_names,
                pickup_button_names,
            )
        ):
            # Otherwise on android show standard buttons.
            if classic.platform == 'android':
                punch_button_names.add('X')
                jump_button_names.add('A')
                bomb_button_names.add('B')
                pickup_button_names.add('Y')

        run_text = bs.Lstr(
            value='${R}: ${B}',
            subs=[
                ('${R}', bs.Lstr(resource='runText')),
                (
                    '${B}',
                    bs.Lstr(
                        resource=(
                            'holdAnyKeyText'
                            if all_keyboards
                            else 'holdAnyButtonText'
                        )
                    ),
                ),
            ],
        )

        # If we're all keyboards, lets show move keys too.
        if (
            all_keyboards
            and len(up_button_names) == 1
            and len(down_button_names) == 1
            and len(left_button_names) == 1
            and len(right_button_names) == 1
        ):
            up_text = list(up_button_names)[0]
            down_text = list(down_button_names)[0]
            left_text = list(left_button_names)[0]
            right_text = list(right_button_names)[0]
            run_text = bs.Lstr(
                value='${M}: ${U}, ${L}, ${D}, ${R}\n${RUN}',
                subs=[
                    ('${M}', bs.Lstr(resource='moveText')),
                    ('${U}', up_text),
                    ('${L}', left_text),
                    ('${D}', down_text),
                    ('${R}', right_text),
                    ('${RUN}', run_text),
                ],
            )

        if self._force_hide_button_names:
            jump_button_names.clear()
            punch_button_names.clear()
            bomb_button_names.clear()
            pickup_button_names.clear()

        self._run_text.text = run_text
        w_text: bs.Lstr | str
        if only_remote and self._lifespan is None:
            w_text = bs.Lstr(
                resource='fireTVRemoteWarningText',
                subs=[('${REMOTE_APP_NAME}', bs.get_remote_app_name())],
            )
        else:
            w_text = ''
        self._extra_text.text = w_text
        if len(punch_button_names) == 1:
            self._punch_text.text = list(punch_button_names)[0]
        else:
            self._punch_text.text = ''

        if len(jump_button_names) == 1:
            tval = list(jump_button_names)[0]
        else:
            tval = ''
        self._jump_text.text = tval
        if tval == '':
            self._run_text.position = self._run_text_pos_top
            self._extra_text.position = (
                self._run_text_pos_top[0],
                self._run_text_pos_top[1] - 50,
            )
        else:
            self._run_text.position = self._run_text_pos_bottom
            self._extra_text.position = (
                self._run_text_pos_bottom[0],
                self._run_text_pos_bottom[1] - 50,
            )
        if len(bomb_button_names) == 1:
            self._bomb_text.text = list(bomb_button_names)[0]
        else:
            self._bomb_text.text = ''

        # Also move our title up/down depending on if this is shown.
        if len(pickup_button_names) == 1:
            self._pick_up_text.text = list(pickup_button_names)[0]
            if self._title_text is not None:
                self._title_text.position = self._title_text_pos_top
        else:
            self._pick_up_text.text = ''
            if self._title_text is not None:
                self._title_text.position = self._title_text_pos_bottom

    def _die(self) -> None:
        for node in self._nodes:
            node.delete()
        self._nodes = []
        self._update_timer = None
        self._dead = True

    @override
    def exists(self) -> bool:
        return not self._dead

    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            if msg.immediate:
                self._die()
            else:
                # If they don't need immediate, fade out our nodes and
                # die later.
                for node in self._nodes:
                    bs.animate(node, 'opacity', {0: node.opacity, 3.0: 0.0})
                bs.timer(3.1, bs.WeakCall(self._die))
            return None
        return super().handlemessage(msg)
