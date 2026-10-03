# Released under the MIT License. See LICENSE for details.
#
"""Stage debug symbols for the modules named by a Windows crash dump.

The dump-driven counterpart to ``prefabsymbols``. That one asks "what
binaries do I have locally?" and fetches symbols for them, which is
right when you just built something. A crash report inverts the
question: you have a dump from a build you may never have had, and you
want whatever symbols it needs.

A minidump answers that itself -- every loaded module carries the
CodeView key of the pdb built with it -- so this walks the dump's
module list, fetches each key the server knows about, and lays the
results out so a symbolicating tool can find them.
"""

import os

from efro.error import CleanError
from efro.terminal import Clr

from batools.winsymbols import (
    codeview_keys_from_minidump,
    fetch_symbols_for_key,
    is_system_module_path,
)

#: Master-server host per fleet; mirrors prefabsymbols.
_FLEET_HOSTS = {
    'prod': 'www.ballistica.net',
    'test': 'test.ballistica.net',
    'dev': 'dev.ballistica.net',
}

#: Where fetched symbols land. Laid out one dir per key
#: (``<pdb-name>/<key>/<pdb-name>``) rather than flat: two dumps from
#: different builds both want a file called ``libGLESv2.pdb``, and a
#: flat dir would have them overwrite each other. This also happens to
#: be the layout a symbol server uses, so pointing a debugger's symbol
#: path at the root works without any extra glue.
_SYMBOLS_ROOT = 'build/windows-symbols'


def stage_symbols_for_dump(dump_path: str, host: str | None = None) -> str:
    """Fetch and stage symbols for every module a dump names.

    Returns the symbols root, suitable as a debugger symbol path.
    Modules the server has no symbols for are reported and skipped --
    most of a dump's modules are system dlls we will never have pdbs
    for, so that is the normal case rather than an error.
    """
    if not os.path.isfile(dump_path):
        raise CleanError(f'Dump not found: {dump_path}.')

    if host is None:
        fleet = os.environ.get('BA_FLEET', 'prod').lower()
        host = _FLEET_HOSTS.get(fleet)
        if host is None:
            raise CleanError(f"Invalid BA_FLEET value '{fleet}'.")

    all_modules = codeview_keys_from_minidump(dump_path)
    if not all_modules:
        raise CleanError(f'No modules with CodeView records in {dump_path}.')

    # Skip the OS's own dlls. A dump lists ~125 modules and nearly all
    # are Windows' -- querying each turns seconds into minutes to learn
    # what we already know (we archive symbols for our binaries and the
    # third-party ones we ship, not Microsoft's).
    modules = [m for m in all_modules if not is_system_module_path(m[0])]
    skipped = len(all_modules) - len(modules)

    print(
        f'Dump names {Clr.BLD}{len(all_modules)}{Clr.RST} module(s) with'
        f' symbol keys; querying {host} for {len(modules)}'
        f' ({skipped} OS module(s) skipped)...'
    )

    staged = 0
    for modpath, pdb_name, key in modules:
        modname = modpath.replace('\\', '/').rsplit('/', 1)[-1]
        # One module's lookup failing (a timeout, a transient 5xx) must
        # not throw away the symbols we already staged -- the useful
        # module is often not the last one queried.
        try:
            result = fetch_symbols_for_key(key, host)
        except CleanError as exc:
            print(f'{Clr.YLW}Lookup failed for {modname}: {exc}{Clr.RST}')
            continue
        if result is None:
            continue
        _file_name, payload = result
        destdir = os.path.join(_SYMBOLS_ROOT, pdb_name, key)
        os.makedirs(destdir, exist_ok=True)
        destpath = os.path.join(destdir, pdb_name)
        tmppath = f'{destpath}.download'
        with open(tmppath, 'wb') as outfile:
            outfile.write(payload)
        os.replace(tmppath, destpath)
        size_mb = len(payload) / (1024 * 1024)
        print(
            f'{Clr.GRN}Staged {Clr.BLD}{pdb_name}{Clr.RST}{Clr.GRN} for'
            f' {modname} ({size_mb:.1f} MB) -> {destpath}{Clr.RST}'
        )
        staged += 1

    if staged == 0:
        print(
            f'{Clr.YLW}No symbols found for any of this dump\'s modules.'
            f' They may not be archived, or may have expired.{Clr.RST}'
        )
    else:
        print(
            f'Staged {Clr.BLD}{staged}{Clr.RST} of {len(modules)}'
            f' module(s) under {Clr.BLD}{_SYMBOLS_ROOT}{Clr.RST}.'
        )
    return _SYMBOLS_ROOT
