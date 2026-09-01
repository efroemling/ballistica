# Released under the MIT License. See LICENSE for details.
#
"""Fast side-by-side ``.pyc`` staging for archive-based payloads.

Creates/updates/prunes ``foo.pyc`` files next to every ``foo.py``
under a staged tree — the layout zipimport consumes when importing
directly out of an apk/zip (see internal
``docs/initiatives/android-apk-direct-ba-data.md``).

The emitted pycs use hash-based *unchecked-hash* invalidation (PEP
552): loaded unconditionally by zipimport, immune to apk zip-timestamp
normalization, and byte-deterministic. Freshness *here* is tracked via
timestamps instead — each generated pyc's mtime is set exactly equal
to its source's, so an up-to-date tree is verified with pure stat
calls (no reads) and a no-op pass costs only milliseconds. A root
stamp file records the interpreter bytecode magic so interpreter
upgrades force a full regeneration despite fresh-looking timestamps.

Split out of :mod:`batools.staging` to keep that module under the
line limit.
"""

import os
import py_compile
import importlib.util
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor

#: Root-relative name of our stamp file. Starts with a dot so android
#: payload manifests (which skip dotfiles) never ship it.
STAMP_FILENAME = '.pycstamp'

# Bump to force full pyc regeneration on format/behavior changes.
_STAMP_VERSION = 1

# Below this many stale files the process-pool spinup costs more than
# it saves; compile in-process instead.
_MIN_FILES_FOR_POOL = 20

_POOL_CHUNK_SIZE = 25


@dataclass
class PycUpdateResults:
    """What a :func:`update_pycs` pass did."""

    compiled: int = 0
    pruned: int = 0
    up_to_date: int = 0
    #: Compile-failure descriptions; empty on full success.
    errors: list[str] = field(default_factory=list)


def _stamp_value() -> str:
    return f'{_STAMP_VERSION} {importlib.util.MAGIC_NUMBER.hex()}\n'


def _compile_batch(root: str, jobs: list[tuple[str, int]]) -> list[str]:
    """Compile a batch of relative .py paths under root.

    Returns error descriptions (empty on success). Runs in worker
    processes, so must stay importable at module level.
    """
    errors: list[str] = []
    for relpath, mtime_ns in jobs:
        pypath = os.path.join(root, relpath)
        pycpath = pypath + 'c'
        try:
            # dfile: embed the root-relative path so pyc bytes are
            # deterministic across machines/checkout locations (and
            # device tracebacks aren't host paths).
            py_compile.compile(
                pypath,
                cfile=pycpath,
                dfile=relpath,
                doraise=True,
                invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
            )
            # Pin the pyc's mtime to the source's exactly; our
            # freshness check is strict equality.
            os.utime(pycpath, ns=(mtime_ns, mtime_ns))
        except Exception as exc:
            errors.append(f'{relpath}: {exc}')
    return errors


def update_pycs(root: str, force: bool = False) -> PycUpdateResults:
    """Create/update/prune side-by-side pycs under a staged tree.

    Walks ``root``; every ``.py`` gets an adjacent unchecked-hash
    ``.pyc`` (regenerated when its mtime doesn't exactly match the
    source's), and orphaned ``.pyc`` files (source gone) are removed.
    Compile errors are collected in the returned results rather than
    raised; callers treat a non-empty ``errors`` as a build failure.
    """
    results = PycUpdateResults()

    # Interpreter/format change? Regenerate everything.
    stamp_path = os.path.join(root, STAMP_FILENAME)
    try:
        with open(stamp_path, encoding='utf-8') as infile:
            stamp_current = infile.read() == _stamp_value()
    except OSError:
        stamp_current = False
    if not stamp_current:
        force = True

    stale: list[tuple[str, int]] = []  # (relpath, mtime_ns)
    prune: list[str] = []

    rootpfx = len(root.rstrip(os.sep)) + 1

    def scan(dirpath: str) -> None:
        pys: dict[str, os.DirEntry] = {}
        pycs: dict[str, os.DirEntry] = {}
        with os.scandir(dirpath) as entries:
            for entry in entries:
                name = entry.name
                if entry.is_dir(follow_symlinks=False):
                    scan(entry.path)
                elif name.endswith('.py'):
                    pys[name] = entry
                elif name.endswith('.pyc'):
                    pycs[name] = entry
        for name, entry in pys.items():
            pycentry = pycs.pop(name + 'c', None)
            src_mtime = entry.stat().st_mtime_ns
            if (
                force
                or pycentry is None
                or pycentry.stat().st_mtime_ns != src_mtime
            ):
                stale.append((entry.path[rootpfx:], src_mtime))
            else:
                results.up_to_date += 1
        prune.extend(entry.path for entry in pycs.values())

    scan(root)

    for pycpath in prune:
        os.remove(pycpath)
    results.pruned = len(prune)

    if stale:
        if len(stale) < _MIN_FILES_FOR_POOL:
            results.errors += _compile_batch(root, stale)
        else:
            chunks = [
                stale[i : i + _POOL_CHUNK_SIZE]
                for i in range(0, len(stale), _POOL_CHUNK_SIZE)
            ]
            try:
                with ProcessPoolExecutor() as pool:
                    for errs in pool.map(
                        _compile_batch, [root] * len(chunks), chunks
                    ):
                        results.errors += errs
            except PermissionError, NotImplementedError, OSError:
                # Restricted environments (sandboxes) can't spawn
                # process pools; fall back to in-process compiles.
                results.errors += _compile_batch(root, stale)
        results.compiled = len(stale) - len(results.errors)

    # Only certify the tree once it fully succeeded.
    if not results.errors:
        with open(stamp_path, 'w', encoding='utf-8') as outfile:
            outfile.write(_stamp_value())
    return results
