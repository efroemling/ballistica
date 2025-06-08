# Released under the MIT License. See LICENSE for details.
#
"""Updates src/assets/Makefile based on source assets present."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from efrotools.pyver import PYVER

if TYPE_CHECKING:
    pass

ASSETS_SRC = 'src/assets'
BUILD_DIR = 'build/assets'


def _get_targets(
    projroot: str,
    varname: str,
    inext: str,
    outext: str,
    all_targets: set,
    limit_to_prefix: str | None = None,
) -> str:
    """Generic function to map source extension to dst files."""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-positional-arguments

    src = ASSETS_SRC
    dst = BUILD_DIR
    targets = []

    # Create outext targets for all inext files we find.
    for root, _dname, fnames in os.walk(os.path.join(projroot, src)):
        src_abs = os.path.join(projroot, src)
        if limit_to_prefix is not None and not root.startswith(
            os.path.join(src_abs, limit_to_prefix)
        ):
            continue

        # Write the target to make sense from within src/assets/
        assert root.startswith(src_abs)
        dstrootvar = '$(BUILD_DIR)' + root.removeprefix(src_abs)
        dstfin = dst + root.removeprefix(src_abs)
        for fname in fnames:
            outname = fname[: -len(inext)] + outext
            if fname.endswith(inext):
                all_targets.add(os.path.join(dstfin, outname))
                targets.append(os.path.join(dstrootvar, outname))

    return '\n' + varname + ' = \\\n  ' + ' \\\n  '.join(sorted(targets))


def _get_py_targets(
    projroot: str,
    meta_manifests: dict[str, str],
    explicit_sources: set[str],
    src: str,
    dst: str,
    py_targets: list[str],
    # pyc_targets: list[str],
    so_targets: list[str],
    all_targets: set[str],
    subset: str,
) -> None:
    # pylint: disable=too-many-positional-arguments
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    py_generated_root = f'{ASSETS_SRC}/ba_data/python/babase/_mgen'

    def _do_get_targets(
        proot: str, fnames: list[str], is_explicit: bool = False
    ) -> None:
        # Special case: don't make targets for stuff in specific dirs.
        if proot in {
            f'{ASSETS_SRC}/ba_data/data/maps',
            f'{ASSETS_SRC}/mac_disk_image',
            f'{ASSETS_SRC}/workspace',
        }:
            return

        # Special case: exclude test modules.
        if f'/python{PYVER}/test/' in f'{proot}/':
            return

        assert proot.startswith(src), f'{proot} does not start with {src}'
        assert dst.startswith(BUILD_DIR)
        dstrootvar = (
            '$(BUILD_DIR)'
            + dst.removeprefix(BUILD_DIR)
            + proot.removeprefix(src)
        )
        dstfin = dst + proot[len(src) :]

        for fname in fnames:
            # Ignore non-python files and flycheck/emacs temp files.
            if (
                (not fname.endswith('.py') and not fname.endswith('.so'))
                or fname.startswith('flycheck_')
                or fname.startswith('.#')
            ):
                continue

            # Ignore any files in the list of explicit sources we got;
            # we explicitly add those at the end and don't want to do it
            # twice (since we don't know if this one will always exist
            # anyway).
            if (
                os.path.join(proot, fname) in explicit_sources
                and not is_explicit
            ):
                continue

            if proot.startswith(f'{ASSETS_SRC}/ba_data/python-site-packages'):
                in_subset = 'private-common'
            elif proot.startswith(f'{ASSETS_SRC}/ba_data') or proot.startswith(
                f'{ASSETS_SRC}/server'
            ):
                in_subset = 'public'
            elif proot.startswith('tools/efro') and not proot.startswith(
                'tools/efrotools'
            ):
                # We want to pull just 'efro' out of tools; not efrotools.
                in_subset = 'public_tools'
            elif proot.startswith('tools/bacommon'):
                in_subset = 'public_tools'
            elif proot.startswith(f'{ASSETS_SRC}/windows/x64'):
                in_subset = 'private-windows-x64'
            elif proot.startswith(f'{ASSETS_SRC}/windows/Win32'):
                in_subset = 'private-windows-Win32'
            elif proot.startswith(
                f'src/external/python-apple/macos/Python.xcframework/'
                f'macos-arm64_x86_64/Python.framework/'
                f'Versions/{PYVER}/lib/python{PYVER}'
            ):
                in_subset = 'private-apple-mac'
            # elif proot.startswith(f'{ASSETS_SRC}/pylib-apple'):
            #     in_subset = 'private-apple'
            elif proot.startswith(f'{ASSETS_SRC}/pylib-android'):
                in_subset = 'private-android'
            else:
                in_subset = 'private-common'

            if subset == 'all':
                pass
            elif subset != in_subset:
                continue

            if fname.endswith('.so'):
                # .so:
                targetpath = os.path.join(dstfin, fname)
                assert targetpath not in all_targets
                all_targets.add(targetpath)
                so_targets.append(os.path.join(dstrootvar, fname))
            else:
                # .py:
                targetpath = os.path.join(dstfin, fname)
                assert targetpath not in all_targets
                all_targets.add(targetpath)
                py_targets.append(os.path.join(dstrootvar, fname))

                # and .pyc:
                # fname_pyc = fname[:-3] + PYC_SUFFIX
                # all_targets.add(os.path.join(dstfin,
                # '__pycache__', fname_pyc))
                # pyc_targets.append(
                #     os.path.join(dstrootvar, '__pycache__', fname_pyc)
                # )

    # Create py and pyc targets for all physical scripts in src, with
    # the exception of our dynamically generated stuff.
    for physical_root, _dname, physical_fnames in os.walk(
        os.path.join(projroot, src)
    ):
        # Skip any generated files; we'll add those from the meta manifest.
        # (dont want our results to require a meta build beforehand)
        if physical_root == os.path.join(
            projroot, py_generated_root
        ) or physical_root.startswith(
            os.path.join(projroot, py_generated_root) + '/'
        ):
            continue

        _do_get_targets(
            physical_root.removeprefix(projroot + '/'), physical_fnames
        )

    # Now create targets for any of our dynamically generated stuff that
    # lives under this dir.
    meta_targets: list[str] = []
    for manifest in meta_manifests.values():
        # Sanity check; make sure meta system is giving actual paths;
        # no accidental makefile vars.
        if '$' in manifest:
            raise RuntimeError(
                'meta-manifest value contains a $; probably a bug.'
            )
        meta_targets += json.loads(manifest)

    meta_targets = [
        t
        for t in meta_targets
        if t.startswith(src + '/') and t.startswith(py_generated_root + '/')
    ]

    for target in meta_targets:
        _do_get_targets(
            proot=os.path.dirname(target), fnames=[os.path.basename(target)]
        )

    # Now create targets for any explicitly passed paths.
    for expsrc in explicit_sources:
        if expsrc.startswith(f'{src}/'):
            _do_get_targets(
                proot=os.path.dirname(expsrc),
                fnames=[os.path.basename(expsrc)],
                is_explicit=True,
            )


def _get_py_targets_subset(
    projroot: str,
    meta_manifests: dict[str, str],
    explicit_sources: set[str],
    all_targets: set[str],
    subset: str,
    suffix: str,
) -> str:
    # pylint: disable=too-many-positional-arguments

    copyrule_so: str | None = None

    # Map stuff from tools/ to build/assets/ba_data/python/
    if subset == 'public_tools':
        src = 'tools'
        dst = f'{BUILD_DIR}/ba_data/python'
        copyrule = '$(BUILD_DIR)/ba_data/python/%.py : $(TOOLS_DIR)/%.py'

    # Map stuff from mac python xcframework's lib dir to
    # build/assets/pylib-apple-mac
    elif subset == 'private-apple-mac':
        src = (
            f'src/external/python-apple/macos/Python.xcframework/'
            f'macos-arm64_x86_64/Python.framework/'
            f'Versions/{PYVER}/lib/python{PYVER}'
        )
        dst = f'{BUILD_DIR}/python-apple/macos/pylib'
        copyrule = (
            f'$(BUILD_DIR)/python-apple/macos/pylib/%.py :'
            f' $(SRC_DIR)/external/python-apple/macos/Python.xcframework/'
            f'macos-arm64_x86_64/Python.framework/'
            f'Versions/{PYVER}/lib/python{PYVER}/%.py'
        )
        copyrule_so = (
            f'$(BUILD_DIR)/python-apple/macos/pylib/%.so :'
            f' $(SRC_DIR)/external/python-apple/macos/Python.xcframework/'
            f'macos-arm64_x86_64/Python.framework/'
            f'Versions/{PYVER}/lib/python{PYVER}/%.so'
        )

    # Default - map stuff from src/assets/ to build/assets/
    else:
        src = ASSETS_SRC
        dst = BUILD_DIR
        copyrule = '$(BUILD_DIR)/%.py : %.py'

    # This could be a nice sanity check but some src paths aren't present
    # on various cloud-builds we do. Perhaps we could somehow only check
    # when we know everything is present?..
    if bool(False):
        if not os.path.exists(os.path.join(projroot, src)):
            raise RuntimeError(
                f'Expected src path not found in project: "{src}"'
            )

    py_targets: list[str] = []
    # pyc_targets: list[str] = []
    so_targets: list[str] = []

    _get_py_targets(
        projroot,
        meta_manifests,
        explicit_sources,
        src,
        dst,
        py_targets,
        # pyc_targets,
        so_targets,
        all_targets,
        subset=subset,
    )

    # Need to sort py and pyc combined to keep pairs together.
    # combined_targets = [
    #     (py_targets[i], pyc_targets[i]) for i in range(len(py_targets))
    # ]
    # combined_targets.sort()
    py_targets.sort()
    so_targets.sort()

    # py_targets = [t[0] for t in combined_targets]
    # pyc_targets = [t[1] for t in combined_targets]

    out = (
        f'\nSCRIPT_TARGETS_PY{suffix} = \\\n  '
        + ' \\\n  '.join(py_targets)
        + '\n'
    )

    # out += (
    #     f'\nSCRIPT_TARGETS_PYC{suffix} = \\\n  '
    #     + ' \\\n  '.join(pyc_targets)
    #     + '\n'
    # )

    out += (
        f'\nSCRIPT_TARGETS_SO{suffix} = \\\n  '
        + ' \\\n  '.join(so_targets)
        + '\n'
    )

    # We transform all non-public targets into efrocache-fetches in public.
    efc = '' if subset.startswith('public') else '# __EFROCACHE_TARGET__\n'

    out += (
        '\n# Rule to copy src asset scripts to dst.\n'
        '# (and make non-writable so I\'m less likely to '
        'accidentally edit them there)\n'
        f'{efc}$(SCRIPT_TARGETS_PY{suffix}) : {copyrule}\n'
        '\t@$(PCOMMANDBATCH) copy_python_file $^ $@\n'
    )

    if so_targets:
        assert copyrule_so is not None
        out += (
            '\n# Rule to copy src asset binary modules to dst.\n'
            '# (and make non-writable so I\'m less likely to '
            'accidentally edit them there)\n'
            f'{efc}$(SCRIPT_TARGETS_SO{suffix}) : {copyrule_so}\n'
            '\t@$(PCOMMANDBATCH) copy_python_file $^ $@\n'
        )

    # out += (
    #     '\n# Rule to copy src asset scripts to dst.\n'
    #     '# (and make non-writable so I\'m less likely to '
    #     'accidentally edit them there)\n'
    #     f'{efc}$(SCRIPT_TARGETS_PY{suffix}) : {copyrule}\n'
    #     '\t@echo Copying script: $(subst $(BUILD_DIR)/,,$@)\n'
    #     '\t@mkdir -p $(dir $@)\n'
    #     '\t@rm -f $@\n'
    #     '\t@cp $^ $@\n'
    #     '\t@chmod 444 $@\n'
    # )

    # Fancy new simple loop-based target generation.
    # out += (
    #     f'\n# These are too complex to define in a pattern rule;\n'
    #     f'# Instead we generate individual targets in a loop.\n'
    #     f'$(foreach element,$(SCRIPT_TARGETS_PYC{suffix}),\\\n'
    #     f'$(eval $(call make-opt-pyc-target,$(element))))'
    # )

    # Old code to explicitly emit individual targets.
    # if bool(False):
    #     out += (
    #         '\n# Looks like path mangling from py to pyc is too complex for'
    #         ' pattern rules so\n# just generating explicit targets'
    #         ' for each. Could perhaps look into using a\n# fancy for-loop'
    #         ' instead, but perhaps listing these explicitly isn\'t so bad.\n'
    #     )
    #     for i, target in enumerate(pyc_targets):
    #         # Note: there's currently a bug which can cause python bytecode
    #         # generation to be non-deterministic. This can break our blessing
    #         # process since we bless in core but then regenerate bytecode in
    #         # spinoffs. See https://bugs.python.org/issue34722
    #         # For now setting PYTHONHASHSEED=1 is a workaround.
    #         out += (
    #             '\n'
    #             + target
    #             + ': \\\n      '
    #             + py_targets[i]
    #             + '\n\t@echo Compiling script: $(subst $(BUILD_DIR),,$^)\n'
    #             '\t@rm -rf $@ && PYTHONHASHSEED=1 $(TOOLS_DIR)/pcommand'
    #             ' compile_python_file $^'
    #             ' && chmod 444 $@\n'
    #         )

    return out


def _get_extras_targets_win(
    projroot: str, all_targets: set[str], platform: str
) -> str:
    targets: list[str] = []
    base = f'{ASSETS_SRC}/windows'
    dstbase = 'windows'
    for root, _dnames, fnames in os.walk(os.path.join(projroot, base)):
        for fname in fnames:
            # Only include the platform we were passed.
            if not root.startswith(
                os.path.join(projroot, f'{ASSETS_SRC}/windows/{platform}')
            ):
                continue

            ext = os.path.splitext(fname)[-1]

            # "I don't like .DS_Store files. They're coarse and rough and
            # irritating and they get everywhere."
            if fname == '.DS_Store':
                continue

            # Ignore python files as they're handled separately.
            if ext in ['.py', '.pyc']:
                continue

            # Various stuff we expect to be there...
            if ext in [
                '.exe',
                '.dll',
                '.bat',
                '.txt',
                '.whl',
                '.ps1',
                '.css',
                '.sample',
                '.ico',
                '.pyd',
                '.ctypes',
                '.rst',
                '.fish',
                '.csh',
                '.cat',
                '.pdb',
                '.lib',
                '.html',
            ] or fname in [
                'activate',
                'README',
                'command_template',
                'fetch_macholib',
            ]:
                base_abs = os.path.join(projroot, base)
                assert root.startswith(base_abs)
                targetpath = os.path.join(
                    dstbase + root.removeprefix(base_abs), fname
                )
                # print(f'DSTBASE {dstbase} ROOT {root}
                # TARGETPATH {targetpath}')
                targets.append('$(BUILD_DIR)/' + targetpath)
                all_targets.add(BUILD_DIR + '/' + targetpath)
                continue

            # Complain if something new shows up instead of blindly
            # including it.
            raise RuntimeError(f'Unexpected extras file: {root}/{fname}')

    targets.sort()
    p_up = platform.upper()
    out = (
        f'\nEXTRAS_TARGETS_WIN_{p_up} = \\\n  ' + ' \\\n  '.join(targets) + '\n'
    )

    # We transform all these targets into efrocache-fetches in public.
    out += (
        '\n# Rule to copy src extras to build.\n'
        f'# __EFROCACHE_TARGET__\n'
        f'$(EXTRAS_TARGETS_WIN_{p_up}) : $(BUILD_DIR)/% :'
        ' %\n'
        '\t@$(PCOMMANDBATCH) copy_win_extra_file $^ $@\n'
        # '\t@echo Copying file: $(subst $(BUILD_DIR)/,,$@)\n'
        # '\t@mkdir -p $(dir $@)\n'
        # '\t@rm -f $@\n'
        # '\t@cp $^ $@\n'
    )

    return out


def generate_assets_makefile(
    projroot: str,
    fname: str,
    existing_data: str,
    meta_manifests: dict[str, str],
    explicit_sources: set[str],
) -> dict[str, str]:
    """Main script entry point."""
    # pylint: disable=too-many-locals
    from efrotools.project import getprojectconfig
    from pathlib import Path

    public = getprojectconfig(Path(projroot))['public']
    assert isinstance(public, bool)

    original = existing_data
    lines = original.splitlines()

    auto_start_public = lines.index('# __AUTOGENERATED_PUBLIC_BEGIN__')
    auto_end_public = lines.index('# __AUTOGENERATED_PUBLIC_END__')
    auto_start_private = lines.index('# __AUTOGENERATED_PRIVATE_BEGIN__')
    auto_end_private = lines.index('# __AUTOGENERATED_PRIVATE_END__')

    all_targets_public: set[str] = set()
    all_targets_private: set[str] = set()

    # We always auto-generate the public section.
    our_lines_public = [
        _get_py_targets_subset(
            projroot,
            meta_manifests,
            explicit_sources,
            all_targets_public,
            subset='public',
            suffix='_PUBLIC',
        ),
        _get_py_targets_subset(
            projroot,
            meta_manifests,
            explicit_sources,
            all_targets_public,
            subset='public_tools',
            suffix='_PUBLIC_TOOLS',
        ),
    ]

    # Only auto-generate the private section in the private repo.
    if public:
        our_lines_private = lines[auto_start_private + 1 : auto_end_private]
    else:
        our_lines_private = [
            _get_py_targets_subset(
                projroot,
                meta_manifests,
                explicit_sources,
                all_targets_private,
                subset='private-apple-mac',
                suffix='_PRIVATE_APPLE_MAC',
            ),
            _get_py_targets_subset(
                projroot,
                meta_manifests,
                explicit_sources,
                all_targets_private,
                subset='private-android',
                suffix='_PRIVATE_ANDROID',
            ),
            _get_py_targets_subset(
                projroot,
                meta_manifests,
                explicit_sources,
                all_targets_private,
                subset='private-common',
                suffix='_PRIVATE_COMMON',
            ),
            _get_py_targets_subset(
                projroot,
                meta_manifests,
                explicit_sources,
                all_targets_private,
                subset='private-windows-Win32',
                suffix='_PRIVATE_WIN_WIN32',
            ),
            _get_py_targets_subset(
                projroot,
                meta_manifests,
                explicit_sources,
                all_targets_private,
                subset='private-windows-x64',
                suffix='_PRIVATE_WIN_X64',
            ),
            _get_targets(
                projroot,
                'COB_TARGETS',
                '.collisionmesh.obj',
                '.cob',
                all_targets_private,
            ),
            _get_targets(
                projroot,
                'BOB_TARGETS',
                '.mesh.obj',
                '.bob',
                all_targets_private,
            ),
            _get_targets(
                projroot,
                'FONT_TARGETS',
                '.fdata',
                '.fdata',
                all_targets_private,
            ),
            _get_targets(
                projroot,
                'PEM_TARGETS',
                '.pem',
                '.pem',
                all_targets_private,
            ),
            _get_targets(
                projroot,
                'DATA_TARGETS',
                '.json',
                '.json',
                all_targets_private,
                limit_to_prefix='ba_data/data',
            ),
            _get_targets(
                projroot,
                'AUDIO_TARGETS',
                '.wav',
                '.ogg',
                all_targets_private,
            ),
            _get_targets(
                projroot,
                'TEX2D_DDS_TARGETS',
                '.tex2d.png',
                '.dds',
                all_targets_private,
            ),
            _get_targets(
                projroot,
                'TEX2D_PVR_TARGETS',
                '.tex2d.png',
                '.pvr',
                all_targets_private,
            ),
            _get_targets(
                projroot,
                'TEX2D_KTX_TARGETS',
                '.tex2d.png',
                '.ktx',
                all_targets_private,
            ),
            _get_targets(
                projroot,
                'TEX2D_PREVIEW_PNG_TARGETS',
                '.tex2d.png',
                '_preview.png',
                all_targets_private,
            ),
            _get_extras_targets_win(projroot, all_targets_private, 'Win32'),
            _get_extras_targets_win(projroot, all_targets_private, 'x64'),
        ]
    filtered = (
        lines[: auto_start_public + 1]
        + our_lines_public
        + lines[auto_end_public : auto_start_private + 1]
        + our_lines_private
        + lines[auto_end_private:]
    )
    out_files: dict[str, str] = {}

    out = '\n'.join(filtered) + '\n'

    out_files[fname] = out

    # Write a simple manifest of the things we expect to have in build.
    # We can use this to clear out orphaned files as part of builds.
    out_files['src/assets/.asset_manifest_public.json'] = _gen_manifest(
        all_targets_public
    )
    # Only *generate* the private manifest in the private repo. In public
    # we just give what's already on disk.
    manprivpath = 'src/assets/.asset_manifest_private.json'
    if not public:
        out_files[manprivpath] = _gen_manifest(all_targets_private)
    return out_files


def _gen_manifest(all_targets: set[str]) -> str:
    # Lastly, write a simple manifest of the things we expect to have
    # in build. We can use this to clear out orphaned files as part of builds.
    assert all(t.startswith(BUILD_DIR) for t in all_targets)
    manifest = sorted(t[13:] for t in all_targets)
    return json.dumps(manifest, indent=1)
