# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=useless-suppression, disable=invalid-name, missing-docstring

# A TEMPLATE CONFIG FOR CREATED SPINOFF DST PROJECTS.
# THIS IS NOT USED AT RUNTIME; IT ONLY EXISTS FOR TYPE-CHECKING PURPOSES.

# This file is exec'ed by tools/spinoff, allowing us to customize
# how the parent project is filtered into ours.

from __future__ import annotations

from batools.spinoff import SpinoffContext

ctx = SpinoffContext.get_active()

# BallisticaKit will get replaced with this in default filtering.
ctx.dst_name = 'SPINOFF_TEMPLATE_NAME'

# Feature sets from the source project that we should include in dst.
# Set to None to include all feature sets. Check config/featuresets to
# see what is available. These will be names like 'base', 'scene_v1',
# etc. Note that the 'core' feature set as well as feature sets required
# by ones we pass will be implicitly included as well.
# __SRC_FEATURE_SETS__

# These paths in the src project will be ignored during updates and
# not synced into this dst project. We can use this to omit parts of
# the src project that we don't want or that we intend to 'override'
# with our own versions.
src_omit_paths: list[str] = []

# Add ours to the existing set.
ctx.src_omit_paths.update(src_omit_paths)

# Use this to 'carve out' directories or exact file paths which will be
# git-managed on dst. By default, spinoff will consider dirs containing
# the files it generates as 'spinoff-managed'; it will set them as
# git-ignored and will complain if any files appear in them that it does
# not manage itself (to prevent accidentally working in such places).
src_write_paths: list[str] = []

# Add ours to the existing set.
ctx.src_write_paths.update(src_write_paths)


# Define and register a filter-file-call.
# This will get called for each filtered file.
# The default_filter_file() call replaces variations of 'BallisticaKit'
# with the dst_name declared above.
def filter_file(context: SpinoffContext, src_path: str, text: str) -> str:
    text = context.default_filter_file(src_path, text)

    # Custom filtering would go here.

    return text


ctx.filter_file_call = filter_file
