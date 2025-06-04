# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to classic game tips.

These can be shown at opportune times such as between rounds."""
from __future__ import annotations

from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    pass


def get_all_tips() -> list[str]:
    """Return the complete list of tips."""
    tips = [
        (
            'If you are short on controllers,'
            ' install the \'${REMOTE_APP_NAME}\' app\n'
            'on your mobile devices to use them as controllers.'
        ),
        (
            'Create player profiles for yourself and your friends with\nyour '
            'preferred names and appearances instead of using random ones.'
        ),
        (
            'You can \'aim\' your punches by spinning left or right.\nThis is '
            'useful for knocking bad guys off edges or scoring in hockey.'
        ),
        (
            'If you pick up a curse, your only hope for survival is to\nfind a '
            'health powerup in the next few seconds.'
        ),
        (
            'A perfectly timed running-jumping-spin-punch can kill in a single '
            'hit\nand earn you lifelong respect from your friends.'
        ),
        'Always remember to floss.',
        'Don\'t run all the time.  Really.  You will fall off cliffs.',
        (
            'In Capture-the-Flag, your own flag must be at your base to score, '
            'If the other\nteam is about to score, stealing their flag can be '
            'a good way to stop them.'
        ),
        (
            'If you get a sticky-bomb stuck to you, jump around and spin in '
            'circles. You might\nshake the bomb off, or if nothing else your '
            'last moments will be entertaining.'
        ),
        (
            'You take damage when you whack your head on things,\n'
            'so try to not whack your head on things.'
        ),
        'If you kill an enemy in one hit you get double points for it.',
        (
            'Despite their looks, all characters\' abilities are identical,\n'
            'so just pick whichever one you most closely resemble.'
        ),
        'You can throw bombs higher if you jump just before throwing.',
        (
            'Throw strength is based on the direction you are holding.\n'
            'To toss something gently in front of you, don\'t'
            ' hold any direction.'
        ),
        (
            'If someone picks you up, punch them and they\'ll let go.\nThis '
            'works in real life too.'
        ),
        (
            'Don\'t get too cocky with that energy shield; you can still get '
            'yourself thrown off a cliff.'
        ),
        (
            'Many things can be picked up and thrown,'
            ' including other players.  '
            'Tossing\nyour enemies off cliffs can be an effective and '
            'emotionally fulfilling strategy.'
        ),
        (
            'Ice bombs are not very powerful, but they freeze\nwhoever they '
            'hit, leaving them vulnerable to shattering.'
        ),
        'Don\'t spin for too long; you\'ll become dizzy and fall.',
        (
            'Run back and forth before throwing a bomb\nto \'whiplash\' it '
            'and throw it farther.'
        ),
        (
            'Punches do more damage the faster your fists are moving,\nso '
            'try running, jumping, and spinning like crazy.'
        ),
        'In hockey, you\'ll maintain more speed if you turn gradually.',
        (
            'The head is the most vulnerable area, so a sticky-bomb\nto the '
            'noggin usually means game-over.'
        ),
        (
            'Hold down any button to run. You\'ll get places faster\nbut '
            'won\'t turn very well, so watch out for cliffs.'
        ),
        (
            'You can judge when a bomb is going to explode based on the\n'
            'color of sparks from its fuse:  yellow..orange..red..BOOM.'
        ),
    ]
    app = babase.app
    tips += [
        'If your framerate is choppy, try turning down resolution\nor '
        'visuals in the game\'s graphics settings.'
    ]

    if (
        app.classic is not None
        and app.classic.platform in ('android', 'ios')
        and not app.env.tv
    ):
        tips += [
            (
                'If your device gets too warm or you\'d like to conserve '
                'battery power,\nturn down "Visuals" or "Resolution" '
                'in Settings->Graphics'
            ),
        ]
    if app.classic is not None and app.classic.platform in ['mac', 'android']:
        tips += [
            'Tired of the soundtrack?  Replace it with your own!'
            '\nSee Settings->Audio->Soundtrack'
        ]

    # Hot-plugging is currently only on some platforms.
    # FIXME: Should add a platform entry for this so don't forget to update it.
    if app.classic is not None and app.classic.platform in [
        'mac',
        'android',
        'windows',
    ]:
        tips += [
            'Players can join and leave in the middle of most games,\n'
            'and you can also plug and unplug controllers on the fly.',
        ]
    return tips
