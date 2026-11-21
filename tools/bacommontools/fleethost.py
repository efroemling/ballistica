# Released under the MIT License. See LICENSE for details.
#
"""Fleet name resolution for developer tools.

Only meaningful for developer setups; public users always talk to
prod. Kept tiny (stdlib only) so fast commands can use it without
pulling in bacloud.
"""

import socket


def resolve_fleet_name(name: str) -> str | None:
    """Return the fleet value a tool argument names, or None if invalid.

    ``prod`` stays ``prod``. A per-machine fleet value (``dev`` or
    ``test`` followed by a machine name, lowercase letters and digits,
    e.g. ``devfromini``) is returned as-is. The bare ``dev`` and
    ``test`` mean *this machine's* dev or test fleet: the kind plus
    the machine's short hostname, lowercased with dashes dropped (the
    original shared fleets with those names are retired).
    """
    name = name.lower()
    if name in ('dev', 'test'):
        suffix = socket.gethostname().split('.')[0].lower().replace('-', '')
        name = f'{name}{suffix}'
    if name == 'prod':
        return name
    if (
        name.startswith(('test', 'dev'))
        and name not in ('dev', 'test')
        and name.isalnum()
        and name.islower()
    ):
        return name
    return None


def fleet_master_host(name: str) -> str | None:
    """The master server host for a fleet name, or None if invalid.

    Takes anything :func:`resolve_fleet_name` takes. ``prod`` is
    ``www.ballistica.net``; every other fleet is
    ``<value>.ballistica.net``, so a new machine's fleet needs no
    change here.
    """
    fleet = resolve_fleet_name(name)
    if fleet is None:
        return None
    if fleet == 'prod':
        return 'www.ballistica.net'
    return f'{fleet}.ballistica.net'
