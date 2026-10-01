# Released under the MIT License. See LICENSE for details.
#
"""Windows debug-symbol (.pdb) lookup by CodeView key.

Windows binaries carry a **CodeView record** naming the exact pdb built
alongside them: a GUID plus an 'age' counter, emitted by the linker and
changing whenever the binary changes. Debuggers match pdbs to binaries
on that key, and -- crucially -- a minidump records it for every loaded
module. So a crash dump states exactly which pdb each of its modules
needs, even for a build you have never had locally.

That is what lets us archive third-party symbols (notably ANGLE's
``libGLESv2.pdb``) and find the right one for an arbitrary crash. Our
own prefab binaries are instead archived by exe content hash, which
works because you fetch those for a binary you already have; see
``prefabsymbols.py``. Both key kinds go through the same lookup
endpoint.
"""

import os
import struct
import urllib.error
import urllib.request

from efro.error import CleanError

#: PE data-directory index of the debug directory.
_DIR_DEBUG = 6

#: IMAGE_DEBUG_TYPE_CODEVIEW.
_DEBUG_TYPE_CODEVIEW = 2

#: Minidump stream id for the module list.
_STREAM_MODULE_LIST = 4

#: Size of one MINIDUMP_MODULE record.
_MODULE_REC_SIZE = 108


def _format_key(guid_bytes: bytes, age: int) -> str:
    """Format a CodeView GUID + age as a symbol-lookup key.

    The GUID's first three fields are little-endian on disk; debuggers
    render them big-endian, and the resulting hex string plus the age
    is the canonical symbol-server key. We keep it lowercase so keys
    compare and sort consistently (the server lowercases lookups).
    """
    d1, d2, d3 = struct.unpack_from('<IHH', guid_bytes, 0)
    tail = guid_bytes[8:16]
    guid = f'{d1:08x}{d2:04x}{d3:04x}' + ''.join(f'{b:02x}' for b in tail)
    return f'{guid}{age:x}'


def codeview_key_from_pe(path: str) -> tuple[str, str] | None:
    """Return ``(pdb_name, key)`` for a PE file, or None if absent.

    ``pdb_name`` is the base name recorded in the binary -- the name a
    debugger will look for, which is not always what the pdb file was
    called on disk (see prefab-symbols.md's CodeView gotcha).
    """
    with open(path, 'rb') as infile:
        data = infile.read()

    if len(data) < 0x40 or data[:2] != b'MZ':
        return None
    (pe_off,) = struct.unpack_from('<I', data, 0x3C)
    if len(data) < pe_off + 24 or data[pe_off : pe_off + 4] != b'PE\0\0':
        return None

    coff = pe_off + 4
    nsections, _ts = struct.unpack_from('<HI', data, coff + 2)
    (opt_size,) = struct.unpack_from('<H', data, coff + 16)
    opt = coff + 20
    (magic,) = struct.unpack_from('<H', data, opt)
    # Data directories sit after the optional header's fixed part; its
    # size differs between PE32 (0x60) and PE32+ (0x70).
    dirs = opt + (0x70 if magic == 0x20B else 0x60)
    dbg_rva, dbg_size = struct.unpack_from('<II', data, dirs + _DIR_DEBUG * 8)
    if not dbg_rva or not dbg_size:
        return None

    # Section table follows the optional header; we need it to map the
    # debug directory's RVA to a file offset.
    sections = opt + opt_size

    def rva_to_off(rva: int) -> int | None:
        for i in range(nsections):
            sec = sections + i * 40
            vaddr, vsize = struct.unpack_from('<II', data, sec + 12)
            rawsize, rawptr = struct.unpack_from('<II', data, sec + 16)
            if vaddr <= rva < vaddr + max(vsize, rawsize):
                return int(rawptr) + (rva - int(vaddr))
        return None

    dbg_off = rva_to_off(dbg_rva)
    if dbg_off is None:
        return None

    return _scan_debug_entries(data, dbg_off, dbg_size)


def _scan_debug_entries(
    data: bytes, dbg_off: int, dbg_size: int
) -> tuple[str, str] | None:
    """Return the first CodeView entry's ``(pdb_name, key)``, if any."""
    for i in range(dbg_size // 28):
        ent = dbg_off + i * 28
        (dtype,) = struct.unpack_from('<I', data, ent + 12)
        if dtype != _DEBUG_TYPE_CODEVIEW:
            continue
        size_of_data, _addr, rawptr = struct.unpack_from('<III', data, ent + 16)
        if data[rawptr : rawptr + 4] != b'RSDS':
            continue
        guid = data[rawptr + 4 : rawptr + 20]
        (age,) = struct.unpack_from('<I', data, rawptr + 20)
        raw_name = data[rawptr + 24 : rawptr + size_of_data].split(b'\0')[0]
        name = raw_name.decode('utf-8', 'replace').replace('\\', '/')
        return os.path.basename(name), _format_key(guid, age)
    return None


def codeview_keys_from_minidump(path: str) -> list[tuple[str, str, str]]:
    """Return ``(module_path, pdb_name, key)`` for a dump's modules.

    Paths are as recorded in the dump (so callers can tell an OS dll
    from ours -- see :func:`is_system_module_path`).

    Modules without a CodeView record (plenty of system dlls ship
    without one here) are skipped rather than reported, since there is
    nothing to look up for them.
    """
    with open(path, 'rb') as infile:
        data = infile.read()

    if data[:4] != b'MDMP':
        raise CleanError(f'Not a minidump file: {path}.')

    _sig, _ver, nstreams, dirrva = struct.unpack_from('<4sIII', data, 0)
    modlist: tuple[int, int] | None = None
    for i in range(nstreams):
        stype, dsize, drva = struct.unpack_from('<III', data, dirrva + i * 12)
        if stype == _STREAM_MODULE_LIST:
            modlist = (dsize, drva)
            break
    if modlist is None:
        return []

    _dsize, rva = modlist
    (nmods,) = struct.unpack_from('<I', data, rva)
    out: list[tuple[str, str, str]] = []
    for i in range(nmods):
        entry = _module_codeview(data, rva + 4 + i * _MODULE_REC_SIZE)
        if entry is not None:
            out.append(entry)
    return out


def is_system_module_path(path: str) -> bool:
    """Whether a dump module path looks like an OS-supplied binary.

    Used to skip lookups we know will miss: a dump lists ~125 modules,
    nearly all of them Windows' own dlls, and querying each one turns a
    two-second job into a two-minute one for no gain.
    """
    lowered = path.replace('\\', '/').lower()
    return (
        '/windows/system32/' in lowered
        or '/windows/syswow64/' in lowered
        or '/windows/winsxs/' in lowered
        or '/driverstore/' in lowered
    )


def _module_codeview(data: bytes, off: int) -> tuple[str, str, str] | None:
    """Return ``(module_path, pdb_name, key)`` for one dump module."""
    (namerva,) = struct.unpack_from('<I', data, off + 20)
    (namelen,) = struct.unpack_from('<I', data, namerva)
    modname = data[namerva + 4 : namerva + 4 + namelen].decode(
        'utf-16-le', 'replace'
    )

    cv_size, cv_rva = struct.unpack_from('<II', data, off + 76)
    if cv_size < 24 or data[cv_rva : cv_rva + 4] != b'RSDS':
        return None
    guid = data[cv_rva + 4 : cv_rva + 20]
    (age,) = struct.unpack_from('<I', data, cv_rva + 20)
    raw_name = data[cv_rva + 24 : cv_rva + cv_size].split(b'\0')[0]
    pdbname = raw_name.decode('utf-8', 'replace').replace('\\', '/')
    return modname, os.path.basename(pdbname), _format_key(guid, age)


def fetch_symbols_for_key(key: str, host: str) -> tuple[str, bytes] | None:
    """Fetch a symbols file by lookup key; None if the server has none.

    Shared by every caller so the endpoint, error handling and the
    'not published / expired' case stay in one place.
    """
    url = f'https://{host}/api/v1/prefab-symbols/{key}'
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            import json

            info = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise CleanError(
            f'Symbols lookup failed ({exc.code}) for {key}.'
        ) from exc
    except urllib.error.URLError as exc:
        raise CleanError(f'Symbols lookup failed for {key}: {exc}.') from exc

    with urllib.request.urlopen(info['download_url'], timeout=300) as response:
        return info['file_name'], response.read()
