# Released under the MIT License. See LICENSE for details.
#
"""Text related functionality."""

from __future__ import annotations


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import babase


def timestring(
    timeval: float | int,
    centi: bool = True,
) -> babase.Lstr:
    """Generate a babase.Lstr for displaying a time value.

    Category: **General Utility Functions**

    Given a time value, returns a babase.Lstr with:
    (hours if > 0 ) : minutes : seconds : (centiseconds if centi=True).

    WARNING: the underlying Lstr value is somewhat large so don't use this
    to rapidly update Node text values for an onscreen timer or you may
    consume significant network bandwidth.  For that purpose you should
    use a 'timedisplay' Node and attribute connections.

    """
    from babase._language import Lstr

    # We take float seconds but operate on int milliseconds internally.
    timeval = int(1000 * timeval)
    bits = []
    subs = []
    hval = (timeval // 1000) // (60 * 60)
    if hval != 0:
        bits.append('${H}')
        subs.append(
            (
                '${H}',
                Lstr(
                    resource='timeSuffixHoursText',
                    subs=[('${COUNT}', str(hval))],
                ),
            )
        )
    mval = ((timeval // 1000) // 60) % 60
    if mval != 0:
        bits.append('${M}')
        subs.append(
            (
                '${M}',
                Lstr(
                    resource='timeSuffixMinutesText',
                    subs=[('${COUNT}', str(mval))],
                ),
            )
        )

    # We add seconds if its non-zero *or* we haven't added anything else.
    if centi:
        # pylint: disable=consider-using-f-string
        sval = timeval / 1000.0 % 60.0
        if sval >= 0.005 or not bits:
            bits.append('${S}')
            subs.append(
                (
                    '${S}',
                    Lstr(
                        resource='timeSuffixSecondsText',
                        subs=[('${COUNT}', ('%.2f' % sval))],
                    ),
                )
            )
    else:
        sval = timeval // 1000 % 60
        if sval != 0 or not bits:
            bits.append('${S}')
            subs.append(
                (
                    '${S}',
                    Lstr(
                        resource='timeSuffixSecondsText',
                        subs=[('${COUNT}', str(sval))],
                    ),
                )
            )
    return Lstr(value=' '.join(bits), subs=subs)
