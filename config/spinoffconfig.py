# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=missing-module-docstring, invalid-name
from __future__ import annotations

# This file is exec'ed by tools/spinoff, allowing us to customize how
# this src project gits filtered into dst projects.

from batools.spinoff import SpinoffContext

# Grab the context we should apply to.
ctx = SpinoffContext.get_active()

# As a src project, we set up a baseline set of rules based on what we
# contain. The dst project config (exec'ed after us) is then free to
# override based on what they want of ours or what they add themselves.

# Any files/dirs with these base names will be ignored by spinoff on
# both src and dst.
ctx.ignore_names = {
    '__pycache__',
    '.git',
    '.mypy_cache',
}

# Special set of paths managed by spinoff but ALSO stored in git in the
# dst project. This is for bare minimum stuff needed to be always
# present in dst for bootstrapping, indexing by github, etc). Changes to
# these files in dst will be silently and happily overwritten by
# spinoff, so tread carefully.
ctx.git_mirrored_paths = {
    '.gitignore',
    '.gitattributes',
    'README.md',
    'config/jenkins',
}

# File names that can be quietly ignored or cleared out when found. This
# should encompass things like .DS_Store files created by the Mac Finder
# when browsing directories. This helps spinoff remove empty directories
# when doing a 'clean', etc.
ctx.cruft_file_names = {'.DS_Store'}

# These paths in the src project will be skipped over during updates and
# not synced into the dst project. The dst project can use this to trim
# out parts of the src project that it doesn't want or that it intends
# to 'override' with its own versions.
ctx.src_omit_paths = {
    '.gitignore',
    'config/spinoffconfig.py',
    'tools/spinoff',
    '.editorconfig',
    'src/assets/workspace',
}

# Use this to 'carve out' files or directories which will be git-managed
# on dst.
#
# By default, spinoff will consider dirs containing the files it syncs
# from src as 'spinoff-managed'; it will set them as git-ignored and
# will complain if any files appear in them that it does not manage
# itself (to prevent accidentally doing work in such places). Note that
# adding a dir to src_write_paths does not prevent files within it from
# being synced by spinoff; it just means that each of those individual
# spinoff-managed files will have their own gitignore entry since there
# can't be a single one covering the whole dir. So to keep things tidy,
# carve out the minimal set of exact file/dir paths that you need.
ctx.src_write_paths = {
    'tools/spinoff',
    'config/spinoffconfig.py',
}

# Use this to 'carve out' files or directories under spinoff managed
# dirs which will be completely ignored by spinoff (but *not* placed
# under git control).
#
# Normally spinoff will error if it finds any files under its managed
# dirs that it did not put there. This is to prevent accidentally
# working in these parts of a dst project; since spinoff-controlled
# stuff is git-ignored, git itself won't raise any warnings in such
# cases and it would be easy to accidentally blow away changes if
# spinoff didn't raise a stink.
#
# This list is used to suppress raising of said stink for specific
# locations. This allows build output or other dynamically generated
# files to exist under spinoff-managed directories. It is also possible
# to use src_write_paths for such carve-outs, but that can have the
# negative side-effect of greatly complicating the dst project's
# .gitignore file. Selectively marking a few specific files or dirs as
# unchecked instead can keep things tidier and more understandable.
#
# Note that files and paths marked as unchecked cannot be the
# destination for synced files, as that would be ambiguous (We can
# either sync the file ourself or expect someone else to write it, but
# not both).
ctx.src_unchecked_paths = {
    'src/ballistica/mgen',
    'src/ballistica/*/mgen',
    'src/assets/ba_data/python/*/_mgen',
    'src/meta/*/mgen',
    'ballisticakit-cmake/.clang-format',
    'ballisticakit-windows/*/BallisticaKit.ico',
    'ballisticakit-xcode/BallisticaKit Shared/Assets.xcassets/*/*.png',
    'ballisticakit-xcode/BallisticaKit Shared/Assets.xcassets/*/*/*.png',
    'ballisticakit-xcode/BallisticaKit Shared/Assets.xcassets/*/*/*/*/*.png',
    'ballisticakit-xcode/BallisticaKit.xcodeproj/'
    'project.xcworkspace/xcuserdata',
    'ballisticakit-android/BallisticaKit/src/*/res/*/*.png',
    'ballisticakit-android/BallisticaKit/src/*/assets/ballistica_files',
    'ballisticakit-android/local.properties',
    'ballisticakit-android/.gradle',
    'ballisticakit-android/build',
    'ballisticakit-android/BallisticaKit/build',
    'ballisticakit-android/BallisticaKit/.cxx',
}

# Paths/names/suffixes we consider 'project' files. These files are
# synced after all other files and go through batools.project.Updater
# class as part of their filtering. This allows them to update
# themselves in the same way as they do when running 'make update' for
# the project; adding the final filtered set of project source files to
# themself, etc.
ctx.project_file_paths = {'src/assets/ba_data/python/babase/_app.py'}
ctx.project_file_names = {
    'Makefile',
    'CMakeLists.txt',
    '.meta_manifest_public.json',
    '.meta_manifest_private.json',
    '.asset_manifest_public.json',
    '.asset_manifest_private.json',
}

ctx.project_file_suffixes = {
    '.vcxproj',
    '.vcxproj.filters',
    '.pbxproj',
}

# Everything actually synced into dst will use the following filter
# rules:

# If files are 'filtered' it means they will have all instances of
# BallisticaKit in their names and contents replaced with their project
# name. Other custom filtering can also be applied. Obviously filtering
# should not be run on certain files (binary data, etc.) and disabling
# it where not needed can improve efficiency and make backporting easier
# (editing spinoff-managed files in dst and getting those changes back
# into src).

# Anything under these dirs WILL be filtered.
ctx.filter_dirs = {
    'ballisticakit-cmake',
    'ballisticakit-xcode/BallisticaKit.xcodeproj',
    'config',
    'src/assets/pdoc',
}

# ELSE anything under these dirs will NOT be filtered.
ctx.no_filter_dirs = {
    'src/external',
    'src/assets/pylib-android',
    'src/assets/pylib-apple',
    'src/assets/ba_data/python-site-packages',
    'src/assets/windows',
}

# ELSE files matching these exact base names WILL be filtered (so FOO
# matches a/b/FOO as well as just FOO).
ctx.filter_file_names = {
    'Makefile',
    '.gitignore',
    '.dockerignore',
    '.gitattributes',
    'README',
    'README.md',
    'bootstrap',
    'configure',
    'Makefile.am',
    'Makefile.in',
    'Jenkinsfile',
    'assets_phase_android',
    'testfoo.py',
    'testfoo2.py',
    'assets_phase_xcode',
    'ballistica_maya_tools.mel',
    'check_python_syntax',
    'pcommand',
    'vmshell',
    'cloudshell',
    'BUCK',
    'BUCK_WIN',
    'upgrade_vms',
    'flycheck-dir-locals.el',
    '.projectile',
    '.editorconfig',
    'ci.yml',
    'cd.yml',
    'deploy_docs.yml',
    'nightly.yml',
    'release.yml',
    'ballistica_dev_dockerfile',
    'ballistica_dev_image.yaml',
    'ci.yaml',
    'ci_build_and_test_windows.yaml',
    'cd.yaml',
    'deploy_docs.yaml',
    'release.yaml',
    'LICENSE',
    'cloudtool',
    'bacloud',
    'config_template.toml',
    '.efrocachemap',
}

# ELSE files matching these exact base names will NOT be filtered.
ctx.no_filter_file_names = {
    'PVRTexToolCLI',
    'composite',
    'etcpack',
    'astcenc',
    'convert',
    'make_bob',
    'nvcompress',
    'INSTALL',
    'install-sh',
    'LICENSE.txt',
    'gradlew',
    '.style.yapf',
    '.clang-format',
    '.pylintrc',
    'CPPLINT.cfg',
    '.mypy.ini',
    '._ba_sources_hash',
    '._baplus_sources_hash',
    '._bascenev1_sources_hash',
    '._bauiv1_sources_hash',
}

# ELSE files with these extensions WILL be filtered.
ctx.filter_file_extensions = {
    '.py',
    '.pyi',
    '.md',
    '.cpp',
    '.cc',
    '.c',
    '.h',
    '.m',
    '.mm',
    '.metal',
    '.swift',
    '.storyboard',
    '.pbxproj',
    '.xcworkspacedata',
    '.xcscheme',
    '.bat',
    '.entitlements',
    '.json',
    '.plist',
    '.strings',
    '.ac',
    '.m4',
    '.txt',
    '.settings',
    '.in',
    '.props',
    '.html',
    '.cmake',
    '.sh',
    '.sln',
    '.vcxproj',
    '.user',
    '.cmd',
    '.hlsl',
    '.gradle',
    '.xml',
    '.java',
    '.kt',
    '.pro',
    '.aidl',
    '.iml',
    '.properties',
    '.rc',
    '.mk',
    '.r',
    '.frag',
    '.vert',
    '.xcsettings',
    '.xcstrings',
    '.filters',
    '.rst_t',
}

# ELSE files with these extensions will NOT be filtered.
ctx.no_filter_file_extensions = {
    '.png',
    '.exe',
    '.psd',
    '.obj',
    '.wav',
    '.fdata',
    '.icns',
    '.ico',
    '.lib',
    '.dll',
    '.dc',
    '.generated',
    '.default',
    '.minimal',
    '.spec',
    '.x',
    '.pl',
    '.nib',
    '.Porting',
    '.touch',
    '.MacOSX',
    '.ds',
    '.WinCE',
    '.hgignore',
    '.inl',
    '.man',
    '.BIN',
    '.bin',
    '.pyd',
    '.jar',
    '.aar',
    '.zip',
    '.keystore',
    '.bmp',
    '.pem',
}
