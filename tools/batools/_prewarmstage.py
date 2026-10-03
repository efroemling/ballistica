# Released under the MIT License. See LICENSE for details.
#
"""Build the bundled pycache_prewarm payload for store builds.

From-scratch assembly (see docs/initiatives/pyc-prewarm-bundling.md):
compiles every staged ``.py`` under a set of source roots into a
``pycache_prewarm`` dir laid out per-root with final cache-style pyc
file names (interpreter tag + opt suffix), plus a manifest of source
sizes/hashes that the on-device installer uses to verify each source
is unmodified before blessing a pyc against it.

Deliberately not incremental: store builds are rare, and rebuilding
the whole payload each time (a few seconds pooled) buys freedom from
every staleness/pruning bug an updating scheme could have.
"""

import os
import sys
import json
import shutil
import hashlib
import py_compile
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor

#: Root-relative name of the manifest within the prewarm dir.
MANIFEST_FILENAME = 'manifest.json'

#: Bump on manifest format changes (the C++ installer checks this).
MANIFEST_VERSION = 1

#: Digest size for source hashes. BLAKE2b so both sides get it for
#: free (stdlib hashlib here; vendored monocypher in the C++
#: installer). 16 bytes is ample for honesty-checking.
HASH_DIGEST_SIZE = 16

_POOL_CHUNK_SIZE = 32


@dataclass
class PrewarmResults:
    """What a :func:`build_prewarm` run produced."""

    compiled: int = 0
    #: Compile/hash failure descriptions; empty on full success.
    errors: list[str] = field(default_factory=list)


def _pyc_name(py_name: str, optimize: int) -> str:
    """Final cache-style pyc file name for a ``.py`` file name."""
    assert py_name.endswith('.py')
    opt = f'.opt-{optimize}' if optimize > 0 else ''
    return f'{py_name[:-3]}.{sys.implementation.cache_tag}{opt}.pyc'


def _build_batch(
    jobs: tuple[tuple[str, str, str, str], ...], optimize: int
) -> tuple[tuple[tuple[str, int, str], ...], tuple[str, ...]]:
    """Compile+hash a batch of files.

    Each job is ``(srcpath, dstpath, dfile, manifest_key)``. Returns
    manifest entries ``(manifest_key, source_size, source_hash_hex)``
    and error descriptions. Runs in worker processes/interpreters, so
    must stay importable at module level; args and returns are plain
    shareable types (tuples/strs/ints) for PEP 734 subinterpreter
    transport.
    """
    entries: list[tuple[str, int, str]] = []
    errors: list[str] = []
    for srcpath, dstpath, dfile, key in jobs:
        try:
            with open(srcpath, 'rb') as infile:
                srcbytes = infile.read()
            # Dst dirs were all pre-created by build_prewarm's
            # pre-pass (avoids per-file syscalls and any mkdir races
            # across workers).
            # UNCHECKED_HASH gives deterministic pyc bytes (no staged
            # mtimes baked in); the on-device installer rewrites the
            # header to timestamp mode against the installed source.
            py_compile.compile(
                srcpath,
                cfile=dstpath,
                dfile=dfile,
                doraise=True,
                optimize=optimize,
                invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
            )
            srchash = hashlib.blake2b(
                srcbytes, digest_size=HASH_DIGEST_SIZE
            ).hexdigest()
            entries.append((key, len(srcbytes), srchash))
        except Exception as exc:
            errors.append(f'{key}: {exc}')
    return tuple(entries), tuple(errors)


_BatchResult = tuple[tuple[tuple[str, int, str], ...], tuple[str, ...]]
_Job = tuple[str, str, str, str]


def _run_batches(
    executor: str, jobs: list[_Job], optimize: int
) -> list[_BatchResult]:
    """Run the job set under the requested parallelism strategy."""
    chunks = [
        tuple(jobs[i : i + _POOL_CHUNK_SIZE])
        for i in range(0, len(jobs), _POOL_CHUNK_SIZE)
    ]
    if executor == 'serial':
        return [_build_batch(tuple(jobs), optimize)]
    if executor in ('interpreter', 'auto'):
        try:
            return _run_interpreter_pool(chunks, optimize)
        except Exception:
            # Subinterpreter pools are new in 3.14; in 'auto' mode any
            # setup/runtime failure quietly degrades to serial (still
            # only ~1.3s for the full set). Explicit 'interpreter'
            # mode surfaces the error.
            if executor != 'auto':
                raise
            return [_build_batch(tuple(jobs), optimize)]
    if executor == 'process':
        try:
            with ProcessPoolExecutor() as pool:
                return list(
                    pool.map(_build_batch, chunks, [optimize] * len(chunks))
                )
        except PermissionError, NotImplementedError, OSError:
            # Restricted environments (sandboxes) can't spawn process
            # pools; fall back to in-process compiles.
            return [_build_batch(tuple(jobs), optimize)]
    raise ValueError(f"Invalid executor: '{executor}'.")


def _run_interpreter_pool(
    chunks: list[tuple[_Job, ...]], optimize: int
) -> list[_BatchResult]:
    """Run batches on a PEP 734 subinterpreter pool.

    True parallelism without process-spawn costs, and works in
    sandboxes that forbid subprocesses. Each subinterpreter builds
    sys.path fresh, so it can't unpickle references to this module
    unless we add our tools dir; ``site.addsitedir`` is a stdlib
    callable (pickles by reference cleanly) that does exactly that as
    the worker initializer.
    """
    import site
    from concurrent.futures import InterpreterPoolExecutor

    tooldir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with InterpreterPoolExecutor(
        initializer=site.addsitedir, initargs=(tooldir,)
    ) as pool:
        return list(pool.map(_build_batch, chunks, [optimize] * len(chunks)))


def build_prewarm(
    out_dir: str,
    roots: list[tuple[str, str]],
    optimize: int,
    executor: str = 'auto',
) -> PrewarmResults:
    """Assemble a pycache_prewarm dir from scratch.

    ``roots`` is ``(root_key, source_dir)`` pairs; each staged ``.py``
    under a source dir compiles to
    ``<out_dir>/<root_key>/<relpath>/<name>.<cache_tag>[.opt-N].pyc``
    and gets a ``<root_key>/<relpath>`` manifest entry recording the
    source's size and BLAKE2b hash. Any existing ``out_dir`` is
    removed first.

    ``executor`` selects the parallelism strategy: ``'auto'``
    (default: subinterpreter pool, serial on any pool-setup
    failure), ``'interpreter'``, ``'process'`` (serial fallback
    where process pools are unavailable, e.g. sandboxes), or
    ``'serial'``. Benchmarks (M-series mac, 1028 files):
    subinterpreters ~0.26s vs ~1.25s serial.
    """
    results = PrewarmResults()

    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # Gather the full job list.
    jobs: list[tuple[str, str, str, str]] = []
    for root_key, srcdir in roots:
        if not os.path.isdir(srcdir):
            raise RuntimeError(f"Prewarm source dir not found: '{srcdir}'.")
        for dpath, dnames, fnames in os.walk(srcdir):
            dnames[:] = [d for d in dnames if d != '__pycache__']
            for fname in sorted(fnames):
                if not fname.endswith('.py'):
                    continue
                srcpath = os.path.join(dpath, fname)
                # Normalize to '/' so manifest keys, payload layout,
                # and dfiles are host-OS-independent (staging always
                # runs on posix python today, but cheap insurance).
                relpath = os.path.relpath(srcpath, srcdir).replace(os.sep, '/')
                dstpath = os.path.join(
                    out_dir,
                    root_key,
                    os.path.dirname(relpath),
                    _pyc_name(fname, optimize),
                )
                # dfile: root-relative so pyc bytes carry no
                # build-machine paths (and stay deterministic).
                jobs.append(
                    (srcpath, dstpath, relpath, f'{root_key}/{relpath}')
                )

    # Pre-create all dst dirs in one pass so workers never mkdir
    # (no cross-worker races, fewer syscalls).
    for dstdir in {os.path.dirname(job[1]) for job in jobs}:
        os.makedirs(dstdir, exist_ok=True)

    manifest_entries: dict[str, dict[str, int | str]] = {}
    for batchresult in _run_batches(executor, jobs, optimize):
        entries, errors = batchresult
        for key, size, srchash in entries:
            manifest_entries[key] = {'s': size, 'h': srchash}
        results.errors += list(errors)
        results.compiled += len(entries)

    # Only write the manifest on full success; a partial payload
    # without one is inert (the installer requires the manifest).
    if not results.errors:
        manifest = {
            'version': MANIFEST_VERSION,
            'cache_tag': sys.implementation.cache_tag,
            'optimize': optimize,
            'entries': manifest_entries,
        }
        with open(
            os.path.join(out_dir, MANIFEST_FILENAME), 'w', encoding='utf-8'
        ) as outfile:
            json.dump(manifest, outfile, separators=(',', ':'), sort_keys=True)
    return results
