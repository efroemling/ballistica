# Released under the MIT License. See LICENSE for details.
#
"""A collection of commands for use with this project.

All top level functions here can be run by passing them as the first
argument on the command line. (or pass no arguments to get a list of
them).
"""

# Note: we import as little as possible here at the module level to keep
# launch times fast; most imports should happen within individual
# command functions.

from __future__ import annotations

from efrotools import pcommand

# Pull in commands we want to expose. Its more efficient to define them
# in modules rather than inline here because we'll be able to load them
# via pyc. pylint: disable=unused-import
from efrotools.pcommands import (
    formatcode,
    formatscripts,
    formatmakefile,
    cpplint,
    pylint,
    pylint_files,
    mypy,
    mypy_files,
    dmypy,
    tool_config_install,
    sync,
    sync_all,
    scriptfiles,
    pycharm,
    clioncode,
    androidstudiocode,
    makefile_target_list,
    spelling,
    spelling_all,
    pytest,
    echo,
    copy_win_extra_file,
    compile_python_file,
    copy_python_file,
    compile_language_file,
    compile_mesh_file,
    compile_collision_mesh_file,
    compile_font_file,
    pyver,
    try_repeat,
    xcodebuild,
    xcoderun,
    xcodeshow,
    tweak_empty_py_files,
    make_ensure,
    make_target_debug,
    requirements_upgrade,
)
from efrotools.pcommands2 import (
    with_build_lock,
    sortlines,
    openal_build_android,
    openal_gather,
    pyright,
    build_pcommandbatch,
    batchserver,
    pcommandbatch_speed_test,
    null,
)
from batools.pcommands import (
    resize_image,
    check_clean_safety,
    archive_old_builds,
    lazy_increment_build,
    get_master_asset_src_dir,
    androidaddr,
    push_ipa,
    printcolors,
    prune_includes,
    python_version_android,
    python_version_apple,
    python_build_apple,
    python_version_android_base,
    python_build_apple_debug,
    python_build_android,
    python_build_android_debug,
    python_android_patch,
    python_android_patch_ssl,
    python_apple_patch,
    python_gather,
    python_gather_apple,
    python_gather_android,
    python_winprune,
    capitalize,
    upper,
    efrocache_update,
    efrocache_get,
    warm_start_asset_build,
    gen_docs_sphinx,
    checkenv,
    prefab_platform,
    ensure_prefab_platform,
    prefab_run_var,
    prefab_binary_path,
    compose_docker_gui_release,
    compose_docker_gui_debug,
    compose_docker_server_release,
    compose_docker_server_debug,
    compose_docker_arm64_gui_release,
    compose_docker_arm64_gui_debug,
    compose_docker_arm64_server_release,
    compose_docker_arm64_server_debug,
    save_docker_images,
    remove_docker_images,
    make_prefab,
    lazybuild,
    efro_gradle,
    stage_build,
    update_project,
    cmake_prep_dir,
    gen_binding_code,
    gen_flat_data_code,
    genchangelog,
    android_sdk_utils,
    logcat,
    gen_python_enums_module,
    gen_dummy_modules,
    version,
)
from batools.pcommands2 import (
    gen_python_init_module,
    gen_monolithic_register_modules,
    py_examine,
    clean_orphaned_assets,
    win_ci_install_prereqs,
    win_ci_binary_build,
    update_cmake_prefab_lib,
    android_archive_unstripped_libs,
    spinoff_test,
    spinoff_check_submodule_parent,
    tests_warm_start,
    wsl_path_to_win,
    wsl_build_check_win_drive,
    get_modern_make,
    asset_package_resolve,
    asset_package_assemble,
    cst_test,
)

# pylint: enable=unused-import


def run_pcommand_main() -> None:
    """Do the thing."""
    pcommand.pcommand_main(globals())
