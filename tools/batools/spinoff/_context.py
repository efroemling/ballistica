# Released under the MIT License. See LICENSE for details.
#
"""Spinoff system for spawning child projects from a ballistica project."""
# pylint: disable=too-many-lines

from __future__ import annotations

import os
import sys
import fnmatch
import tempfile
import subprocess
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, assert_never

from efrotools.code import format_python_str, format_cpp_str
from efrotools.project import getprojectconfig
from efrotools.util import replace_exact
from efro.error import CleanError
from efro.terminal import Clr
from efro.util import timedelta_str

from batools.featureset import FeatureSet
from batools.spinoff._state import (
    EntityType,
    DstEntitySet,
    SrcEntity,
    DstEntity,
)

if TYPE_CHECKING:
    from typing import Callable, Iterable, Any

    from batools.project import ProjectUpdater


class SpinoffContext:
    """Guts of the spinoff system."""

    _active_context: SpinoffContext | None = None

    class BackportInProgressError(Exception):
        """Error we can raise to bow out of processing during a backport."""

    class Mode(Enum):
        """Mode the context can operate in."""

        STATUS = 'status'
        UPDATE = 'update'
        CHECK = 'check'
        CLEAN_LIST = 'cleanlist'
        CLEAN = 'clean'
        CLEAN_CHECK = 'cleancheck'
        OVERRIDE = 'override'
        DIFF = 'diff'
        BACKPORT = 'backport'
        DESCRIBE_PATH = 'describe_path'

    def __init__(
        self,
        src_root: str,
        dst_root: str,
        mode: Mode,
        *,
        force: bool = False,
        verbose: bool = False,
        print_full_lists: bool = False,
        override_paths: list[str] | None = None,
        backport_file: str | None = None,
        auto_backport: bool = False,
        describe_path: str | None = None,
    ) -> None:
        # pylint: disable=too-many-statements

        #: By default, if dst files have their modtimes changed but
        #: still line up with src files, we can recover. But one may
        #: choose to error in that case to track down things mucking
        #: with dst files when they shouldn't be.
        self.strict: bool = False

        self._mode = mode
        self._force = force
        self._verbose = verbose
        self._print_full_lists = print_full_lists
        self._override_paths = override_paths
        self._backport_file = backport_file
        self._auto_backport = auto_backport
        self._describe_path = describe_path

        self._project_updater: ProjectUpdater | None = None

        if not os.path.isdir(src_root):
            raise CleanError(f"Spinoff src dir not found: '{src_root}'.")
        if not os.path.isdir(dst_root):
            raise CleanError(f"Spinoff dst dir not found: '{dst_root}'.")

        # The requested set of FeatureSet names (or None to include all).
        self.src_feature_sets: set[str] | None = None

        # Just to be safe, make sure we're working with abs paths.
        self._src_root = os.path.abspath(src_root)
        self._dst_root = os.path.abspath(dst_root)

        self._data_file_path = os.path.join(self._dst_root, '.spinoffdata')

        self._built_parent_repo_tool_configs = False

        self._auto_backport_success_count = 0
        self._auto_backport_fail_count = 0

        self._src_name = 'BallisticaKit'

        self._public: bool = getprojectconfig(Path(self._src_root))['public']
        assert isinstance(self._public, bool)

        self._src_all_feature_sets = {
            f.name: f for f in FeatureSet.get_all_for_project(self._src_root)
        }

        # Generate our list of tags for selectively stripping out code.
        # __SPINOFF_STRIP_BEGIN__ / __SPINOFF_STRIP_END__ will *always*
        # strip code in spinoff projects and
        # __SPINOFF_REQUIRE_FOO_BEGIN__ / __SPINOFF_REQUIRE_FOO_END__ will
        # strip code only when feature-set foo is not present in the
        # spinoff project.

        # begin-tag / end-tag / associated-feature-set-name
        self._strip_tags: list[tuple[str, str, str | None]] = [
            ('__SPINOFF_STRIP_BEGIN__', '__SPINOFF_STRIP_END__', None)
        ]
        for fsetname in sorted(self._src_all_feature_sets.keys()):
            fnsu = fsetname.upper()
            self._strip_tags.append(
                (
                    f'__SPINOFF_REQUIRE_{fnsu}_BEGIN__',
                    f'__SPINOFF_REQUIRE_{fnsu}_END__',
                    fsetname,
                )
            )

        self._src_git_files: set[str] | None = None
        self._dst_git_files: set[str] | None = None
        self._dst_git_file_dirs: set[str] | None = None

        self.filter_file_call: Callable[[SpinoffContext, str, str], str] = type(
            self
        ).default_filter_file

        self.filter_path_call: Callable[[SpinoffContext, str], str] = type(
            self
        ).default_filter_path

        self._execution_error = False

        self.project_file_paths = set[str]()
        self.project_file_names = set[str]()
        self.project_file_suffixes = set[str]()

        # Set of files/symlinks in src.
        self._src_entities: dict[str, SrcEntity] = {}

        # Set of files/symlinks in dst.
        self._dst_entities: dict[str, DstEntity] = {}

        # Src entities for which errors have occurred
        # (dst modified independently, etc).
        self._src_error_entities: dict[str, str] = {}

        # Dst entries with errors
        # (non-spinoff files in spinoff-owned dirs, etc).
        self._dst_error_entities: dict[str, str] = {}

        # Entities in src we should filter/copy.
        self._src_copy_entities = set[str]()

        # Entities in src we should simply re-cache modtimes/sizes for.
        self._src_recache_entities = set[str]()

        # Dst entities still found in src.
        self._dst_entities_claimed = set[str]()

        # Entities in dst we should kill.
        self._dst_purge_entities = set[str]()

        # Normally spinoff errors if it finds any files in its managed dirs
        # that it did not put there. This is to prevent accidentally working
        # in these parts of a dst project; since these sections are git-ignored,
        # git itself won't raise any warnings in such cases and it would be easy
        # to accidentally lose work otherwise.
        # This list can be used to suppress spinoff's errors for specific
        # locations. This is generally used to allow build output or other
        # dynamically generated files to exist within spinoff-managed
        # directories. It is possible to use src_write_paths for such purposes,
        # but this has the side-effect of greatly complicating the dst
        # project's gitignore list; selectively marking a few dirs as
        # unchecked makes for a cleaner setup. Just be careful to not set
        # excessively broad regions as unchecked; you don't want to mask
        # actual useful error messages.
        self.src_unchecked_paths = set[str]()

        # TODO(ericf): describe this.
        self.project_file_paths = set[str]()

        # Anything under these dirs WILL be filtered.
        self.filter_dirs = set[str]()

        # ELSE anything under these dirs will NOT be filtered.
        self.no_filter_dirs = set[str]()

        # ELSE files matching these exact base names WILL be filtered
        # (so FOO matches a/b/FOO as well as just FOO).
        self.filter_file_names = set[str]()

        # ELSE files matching these exact base names will NOT be filtered.
        self.no_filter_file_names = set[str]()

        # ELSE files with these extensions WILL be filtered.
        self.filter_file_extensions = set[str]()

        # ELSE files with these extensions will NOT be filtered.
        self.no_filter_file_extensions = set[str]()

        self._spinoff_managed_dirs: set[str] | None = None

        # These paths in the src project will be skipped over during updates and
        # not synced into the dst project. The dst project can use this to
        # trim out parts of the src project that it doesn't want or that it
        # intends to 'override' with its own versions.
        self.src_omit_paths = set[str]()

        # Any files/dirs with these base names will be ignored by spinoff
        # on both src and dst.
        self.ignore_names = set[str]()

        # Use this to 'carve out' directories or exact file paths which will be
        # git-managed on dst. By default, spinoff will consider dirs containing
        # the files it generates as 'spinoff-managed'; it will set them as
        # git-ignored and will complain if any files appear in them that it does
        # not manage itself (to prevent accidentally working in such places).
        self.src_write_paths = set[str]()

        # Paths which will NOT be gitignored/etc. (in dst format)
        self.dst_write_paths = set[str]()

        # Special set of paths managed by spinoff but ALSO stored in git in
        # the dst project. This is for bare minimum stuff needed to be always
        # present in dst for bootstrapping, indexing by github, etc). Changes
        # to these files in dst will be silently and happily overwritten by
        # spinoff, so tread carefully.
        self.git_mirrored_paths = set[str]()

        # File names that can be quietly ignored or cleared out when found.
        # This should encompass things like .DS_Store files created by the
        # Mac Finder when browsing directories. This helps spinoff remove
        # empty directories when doing a 'clean', etc.
        self.cruft_file_names = set[str]()

        self.dst_name = 'Untitled'

        self._src_config_path = os.path.join(
            self._src_root, 'config', 'spinoffconfig.py'
        )
        if not os.path.exists(self._src_config_path):
            raise CleanError(
                f"Spinoff src config not found at '{self._src_config_path}'."
            )
        self._dst_config_path = os.path.join(
            self._dst_root, 'config', 'spinoffconfig.py'
        )
        if not os.path.exists(self._dst_config_path):
            raise CleanError(
                f"Spinoff dst config not found at '{self._dst_config_path}'."
            )

        # Sets various stuff from user config .py files.
        self._apply_project_configs()

        # Based on feature-sets they requested, calc which feature-sets
        # from src we *exclude*.
        (
            self._src_retain_feature_sets,
            self._src_omit_feature_sets,
        ) = self._calc_src_retain_omit_feature_sets()

        # Generate a version of src_omit_paths that includes some extra values
        self._src_omit_paths_expanded = self.src_omit_paths.copy()
        # Include feature-set omissions. Basically, omitting a feature
        # set simply omits particular names at a few particular places.
        self._add_feature_set_omit_paths(self._src_omit_paths_expanded)

        # Create a version of dst-write-paths that also includes filtered
        # src-write-paths as well as parents of everything.
        # (so if a/b/c is added as a write path, stuff under a and a/b
        # will also be covered).
        # We also add git_mirrored_paths since that stuff is intended
        # to be in git as well.
        self._dst_write_paths_expanded = self._filter_paths(
            self.src_write_paths
        )
        self._dst_write_paths_expanded.update(self.dst_write_paths)
        self._dst_write_paths_expanded.update(
            self._filter_paths(self.git_mirrored_paths)
        )
        for path in self._dst_write_paths_expanded.copy():
            for subpath in _get_dir_levels(path):
                self._dst_write_paths_expanded.add(subpath)

        # Create a version of src_unchecked_paths for dst.
        self._dst_unchecked_paths = self._filter_paths(self.src_unchecked_paths)
        self._sanity_test_setup()
        self._generate_env_hash()

    def _calc_src_retain_omit_feature_sets(self) -> tuple[set[str], set[str]]:
        # If they want everything, omit nothing.
        if self.src_feature_sets is None:
            return set(self._src_all_feature_sets.keys()), set()

        # Based on the requested set, calc the total sets we'll need.
        # Also always include 'core' since we'd be totally broken
        # without it.
        reqs = FeatureSet.resolve_requirements(
            list(self._src_all_feature_sets.values()),
            self.src_feature_sets | {'core'},
        )

        # Now simply return any sets *not* included in our resolved set.
        omits = {s for s in self._src_all_feature_sets.keys() if s not in reqs}
        return (reqs, omits)

    def _add_feature_set_omit_paths(self, paths: set[str]) -> None:
        for fsname in sorted(self._src_omit_feature_sets):
            featureset = self._src_all_feature_sets.get(fsname)
            if featureset is None:
                raise CleanError(
                    f"src_omit_feature_sets entry '{featureset}' not found"
                    f' on src project.'
                )

            # Omit its config file.
            # Make sure this featureset exists on src.
            fsconfigpath = f'config/featuresets/featureset_{fsname}.py'
            paths.add(fsconfigpath)

            # Omit its Python package.
            fspackagename = featureset.name_python_package
            paths.add(f'src/assets/ba_data/python/{fspackagename}')

            # Omit its C++ dir.
            paths.add(f'src/ballistica/{fsname}')

            # Omits its meta dir.
            fsmetapackagename = featureset.name_python_package_meta
            paths.add(f'src/meta/{fsmetapackagename}')

            # Omit its tests package.
            fstestspackagename = featureset.name_python_package_tests
            paths.add(f'tests/{fstestspackagename}')

    @classmethod
    def get_active(cls) -> SpinoffContext:
        """Return the context currently running."""
        if cls._active_context is None:
            raise RuntimeError('No active context.')
        return cls._active_context

    def run(self) -> None:
        """Do the thing."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        self._read_state()

        # First, ask git if there are any untracked files in src. we use
        # git's managed file list so these wouldn't get synced which
        # would be confusing. So we'd rather just error in this case.
        try:
            output = subprocess.check_output(
                ['git', 'status', '--porcelain=v2'],
                cwd=self._src_root,
            ).decode()
            if any(line.startswith('?') for line in output.splitlines()):
                raise CleanError(
                    'There appear to be files in the src project'
                    ' untracked by git. Everything must be added to'
                    ' git for spinoff to function.'
                )
        except subprocess.CalledProcessError as exc:
            raise CleanError(
                "'git status' command failed in src dir."
                ' Spinoff requires the src project to be git managed.'
            ) from exc

        # Get the list of src files managed by git.
        self._src_git_files = set[str](
            subprocess.run(
                ['git', 'ls-files'],
                check=True,
                cwd=self._src_root,
                capture_output=True,
            )
            .stdout.decode()
            .splitlines()
        )

        # Ignore anything under omitted paths/names.
        self._filter_src_git_file_list()

        # Go through the final set of files we're syncing to dst and
        # make sure none of them fall under our unchecked-paths list.
        # That would mean we are writing a file but we're also declaring
        # that we don't care if anyone else writes that file, which
        # could lead to ambiguous/dangerous situations where spinoff as
        # well as some command on dst write to the same file.
        for path in self._src_git_files:
            if _any_path_contains(self.src_unchecked_paths, path):
                self._src_error_entities[path] = (
                    'Synced file falls under src_unchecked_paths, which'
                    " is not allowed. Either don't sync the file or carve"
                    ' it out from src_unchecked_paths.'
                )

        # Now map whatever is left to paths in dst.
        self._dst_git_files = set(
            self._filter_path(s) for s in self._src_git_files
        )

        # Build a set of all dirs on dst containing a mapped file
        # (excluding root).
        fdirs = self._dst_git_file_dirs = set[str]()
        for dst_git_file in self._dst_git_files:
            dname = os.path.dirname(dst_git_file)
            if dname:
                # Expand to include directories above these as well.
                # We want this set to be 'everything that (even recursively)
                # contains a synced dst file'.
                for leveldir in _get_dir_levels(dname):
                    fdirs.add(leveldir)

        # Now take that list and filter out ones under our write paths
        # to get our final list of spinoff-managed-dirs.
        self._calc_spinoff_managed_dirs()

        # Check our spinoff-managed-dirs for any unrecognized files/etc.
        # Since we git-ignore all of them, this is an important safety
        # feature to avoid blowing away work.
        self._check_spinoff_managed_dirs()

        if self._mode in {
            self.Mode.CLEAN,
            self.Mode.CLEAN_LIST,
            self.Mode.CLEAN_CHECK,
        }:
            # For clean operations, simply stuff all dst entities
            # into our purge list.
            self._purge_all_dst_entities()
        else:
            # For normal operations, queue up our copy ops/etc.
            self._register_sync_operations()

            # Tracked dst files that didn't get claimed can be killed.
            for key in self._dst_entities:
                if key not in self._dst_entities_claimed:
                    self._dst_purge_entities.add(key)

        # Special case: if we're doing an auto-backport, stop here.
        # Otherwise we wind up showing all the errors we probably just fixed.
        if self._mode is self.Mode.BACKPORT and self._auto_backport:
            bpcolor = Clr.YLW if self._auto_backport_fail_count else Clr.GRN
            print(
                f'{bpcolor}Auto-backport complete; backported'
                f' {self._auto_backport_success_count}; '
                f'skipped {self._auto_backport_fail_count}.{Clr.RST}'
            )
            raise self.BackportInProgressError

        if self._mode is self.Mode.DESCRIBE_PATH:
            self._do_describe_path()
        # If anything is off, print errors; otherwise actually do the deed.
        elif self._src_error_entities or self._dst_error_entities:
            self._print_error_entities()
        else:
            if (
                self._mode is self.Mode.STATUS
                or self._mode is self.Mode.CLEAN_LIST
            ):
                self._status()
            elif self._mode is self.Mode.DIFF:
                self._diff()
            elif (
                self._mode is self.Mode.UPDATE or self._mode is self.Mode.CLEAN
            ):
                self._update()
            elif self._mode is self.Mode.OVERRIDE:
                self._override()
            elif self._mode is self.Mode.BACKPORT:
                # If backport gets here, the file they passed isn't erroring.
                raise CleanError(
                    'Nothing needs backporting.'
                    if self._backport_file is None
                    else 'Provided file does not need backporting.'
                )
            elif (
                self._mode is self.Mode.CHECK
                or self._mode is self.Mode.CLEAN_CHECK
            ):
                pass
            else:
                assert_never(self._mode)

        # Always write state at this point. Even if there have been
        # errors, we want to keep track of the latest states we have for
        # anything wrote/etc.
        self._write_state()

        # Bail at this point if anything went wrong.
        if (
            self._src_error_entities
            or self._dst_error_entities
            or self._execution_error
        ):
            # Any of these have printed error info already so no need to
            # do so ourself.
            raise CleanError()

        # If we did anything that possibly deleted stuff, clean up any
        # empty dirs that got left behind (hmm should we be more selective
        # here to avoid dirs we didn't manage?..)
        if self._mode is self.Mode.CLEAN or self._mode is self.Mode.UPDATE:
            self._clean_cruft()

        # Update .gitignore to ignore everything spinoff-managed.
        if self._mode is self.Mode.UPDATE or self._mode is self.Mode.OVERRIDE:
            self._write_gitignore()

    def _do_describe_path(self) -> None:
        assert self._describe_path is not None
        path = self._describe_path

        # Currently operating only on dst paths.
        if path.startswith('/') and not path.startswith(self._dst_root):
            raise CleanError('Please supply a path in the dst dir.')

        # Allow abs paths.
        path = path.removeprefix(f'{self._dst_root}/')

        if self._src_error_entities or self._dst_error_entities:
            print(
                f'{Clr.RED}Note: Errors are present;'
                f' this info may not be fully accurate.{Clr.RST}'
            )
        print(f'{Clr.BLD}dstpath: {Clr.BLU}{path}{Clr.RST}')

        def _printval(name: Any, val: Any) -> None:
            print(f'  {name}: {Clr.BLU}{val}{Clr.RST}')

        _printval('exists', os.path.exists(os.path.join(self._dst_root, path)))

        # Adapted from code in _check_spinoff_managed_dirs.
        managed = False
        unchecked = False
        git_mirrored = False

        dstrootsl = f'{self._dst_root}/'
        assert self._spinoff_managed_dirs is not None
        for rdir in self._spinoff_managed_dirs:
            for root, dirnames, fnames in os.walk(
                os.path.join(self._dst_root, rdir),
                topdown=True,
            ):
                # Completely ignore ignore-names in both dirs and files
                # and cruft-file names in files.
                for dirname in dirnames.copy():
                    if dirname in self.ignore_names:
                        dirnames.remove(dirname)
                for fname in fnames.copy():
                    if (
                        fname in self.ignore_names
                        or fname in self.cruft_file_names
                    ):
                        fnames.remove(fname)

                for fname in fnames:
                    dst_path_full = os.path.join(root, fname)
                    assert dst_path_full.startswith(dstrootsl)
                    dst_path = dst_path_full.removeprefix(dstrootsl)
                    if dst_path == path:
                        managed = True
                    if _any_path_contains(self._dst_unchecked_paths, dst_path):
                        unchecked = True
                    if _any_path_contains(self.git_mirrored_paths, dst_path):
                        git_mirrored = True
        _printval(
            'spinoff-managed',
            managed,
        )
        _printval(
            'unchecked',
            unchecked,
        )
        _printval(
            'git-mirrored',
            git_mirrored,
        )

    def _apply_project_configs(self) -> None:
        # pylint: disable=exec-used
        try:
            assert self._active_context is None
            type(self)._active_context = self

            # Apply both src and dist spinoff configs.
            for config_path in (self._src_config_path, self._dst_config_path):
                exec_context: dict = {}
                with open(config_path, encoding='utf-8') as infile:
                    config_contents = infile.read()

                # Use compile here so we can provide a nice file path for
                # error tracebacks.
                exec(
                    compile(config_contents, config_path, 'exec'),
                    exec_context,
                    exec_context,
                )

        finally:
            assert type(self)._active_context is self
            type(self)._active_context = None

    def _calc_spinoff_managed_dirs(self) -> None:
        assert self._dst_git_file_dirs is not None
        # Take our list of dirs containing stuff synced in from src
        # and strip out anything that has been explicitly been called
        # out as a write-path. What's left will the set of dirs we consider
        # spinoff-managed.
        all_spinoff_managed_dirs = set[str]()
        for gitfiledir in self._dst_git_file_dirs:
            # If we see this exact dir in our expanded write-paths set,
            # (which includes parents), pop it out.
            if gitfiledir in self._dst_write_paths_expanded:
                continue
            all_spinoff_managed_dirs.add(gitfiledir)

        top_level_spinoff_managed_dirs = set[str]()

        # Now take this big soup of dirs and filter it down to top-level ones.
        for rdir in all_spinoff_managed_dirs:
            if any(rdir.startswith(f'{d}/') for d in all_spinoff_managed_dirs):
                continue
            top_level_spinoff_managed_dirs.add(rdir)

        self._spinoff_managed_dirs = top_level_spinoff_managed_dirs

    def _sanity_test_setup(self) -> None:
        # Sanity tests:
        # None of our names lists should ever end in a trailing backslash
        # (currently breaks our logic).
        for entitylist in [
            self.filter_dirs,
            self.no_filter_dirs,
            self.filter_file_names,
            self.no_filter_file_names,
            self.filter_file_extensions,
            self.no_filter_file_extensions,
            self.git_mirrored_paths,
            self._src_omit_paths_expanded,
            self.ignore_names,
            self.src_unchecked_paths,
        ]:
            for ent in entitylist:
                if ent.endswith('/'):
                    raise RuntimeError(f"list item {ent} ends in '/'")

        # Make sure nothing in a directory list refers to something that's a
        # file.
        for entitylist in [
            self.filter_dirs,
            self.no_filter_dirs,
        ]:
            for ent in entitylist:
                if os.path.exists(ent):
                    if not os.path.isdir(ent):
                        raise RuntimeError(
                            f'list item {ent} in a dir-list is not a dir'
                        )

        # Likewise make sure nothing in a file list refers to a
        # directory.
        for ent in []:
            if os.path.exists(ent):
                if os.path.isdir(ent):
                    raise RuntimeError(
                        f'list item {ent} in a file-list is a dir'
                    )

    def _generate_env_hash(self) -> None:
        # pylint: disable=cyclic-import
        from efrotools.util import get_files_hash

        # noinspection PyUnresolvedReferences
        import batools.spinoff
        import batools.project

        # Generate an 'env' hash we can tag tracked files with, so that
        # if spinoff scripts or config files change it will invalidate
        # all tracked files.
        hashfiles = set[str]()

        # Add all Python files under our 'spinoff' and 'project'
        # subpackages since those are most likely to affect results.
        for pkgdir in [
            os.path.dirname(batools.spinoff.__file__),
            os.path.dirname(batools.project.__file__),
        ]:
            for root, _subdirs, fnames in os.walk(pkgdir):
                for fname in fnames:
                    if fname.endswith('.py') and not fname.startswith(
                        'flycheck_'
                    ):
                        hashfiles.add(os.path.join(root, fname))

        # Also add src & dst config files since they can affect
        # anything.
        hashfiles.add(self._src_config_path)
        hashfiles.add(self._dst_config_path)

        self._envhash = get_files_hash(sorted(hashfiles))

    def _read_state(self) -> None:
        """Read persistent state from disk."""
        if os.path.exists(self._data_file_path):
            self._dst_entities = DstEntitySet.read_from_file(
                self._data_file_path
            ).entities

    def _write_state(self) -> None:
        """Write persistent state to disk."""
        DstEntitySet(entities=self._dst_entities).write_to_file(
            self._data_file_path
        )

    def _write_gitignore(self) -> None:
        """filter/write out a gitignore file."""
        assert self._dst_git_files is not None
        assert self._spinoff_managed_dirs is not None

        # We've currently got a list of spinoff-managed-dirs which each
        # results in a gitignore entry. On top of that we add entries
        # for individual files that aren't covered by those dirs.
        gitignore_entries = self._spinoff_managed_dirs.copy()
        for gitpath in self._dst_git_files:
            if self._should_add_gitignore_path(gitpath):
                gitignore_entries.add(gitpath)

        # Pull in src .gitignore.
        with open(
            os.path.join(self._src_root, '.gitignore'), encoding='utf-8'
        ) as infile:
            gitignoreraw = infile.read()

        # Run standard filters on it.
        gitignoreraw = self._filter_file('.gitignore', gitignoreraw)
        gitignorelines = gitignoreraw.splitlines()

        # Now add our ignore entries at the bottom.
        start_line = (
            '# Ignore everything managed by spinoff.\n'
            '# To control this, modify src_write_paths in'
            " 'config/spinoffconfig.py'.\n"
            "# If you ever want to 'flatten' your project and remove it"
            ' from spinoff\n'
            '# control completely: simply delete this section, delete'
            " the 'tools/spinoff'\n"
            "# symlink, and delete 'config/spinoffconfig.py'. Then you can add"
            ' everything\n'
            '# in its current state to your git repo and forget that spinoff'
            ' ever existed.'
        )
        if gitignorelines and gitignorelines[-1] != '':
            gitignorelines.append('')
        gitignorelines.append(start_line)
        for entry in sorted(gitignore_entries):
            gitignorelines.append(f'/{entry}')

        # Add a blurb about this coming from spinoff.
        blurb = (
            '# THIS FILE IS AUTOGENERATED BY SPINOFF;'
            ' MAKE ANY EDITS IN SOURCE PROJECT'
        )
        gitignorelines = [blurb, ''] + gitignorelines
        with open(
            os.path.join(self._dst_root, '.gitignore'), 'w', encoding='utf-8'
        ) as outfile:
            outfile.write('\n'.join(gitignorelines) + '\n')

    def _filter_path(self, path: str) -> str:
        """Run filtering on a given path."""

        return self.filter_path_call(self, path)

    def default_filter_path(self, text: str) -> str:
        """Run default filtering on path text."""
        return self.default_filter_text(text)

    def replace_path_components(
        self, path: str, replace_src: str, replace_dst: str
    ) -> str:
        """Replace a path hierarchy with another.

        Does the right thing for parents. For instance, src 'a/b/c'
        and dst 'a2/b2/c2' will correctly filter 'a/foo' to 'a2/foo'
        and 'a/b/foo' to 'a2/b2/foo'.
        """
        pathsrc = replace_src.split('/')
        pathdst = replace_dst.split('/')
        assert len(pathsrc) == len(pathdst)
        splits = path.split('/')
        cmplen = min(len(splits), len(pathsrc))
        if splits[:cmplen] == pathsrc[:cmplen]:
            return '/'.join(pathdst[:cmplen] + splits[cmplen:])
        return path

    def default_filter_text(self, text: str) -> str:
        """Run default filtering on a piece of text."""

        # Replace uppercase, lowercase, and mixed versions of our name.
        return (
            text.replace(self._src_name.upper(), self.dst_name.upper())
            .replace(self._src_name.lower(), self.dst_name.lower())
            .replace(self._src_name, self.dst_name)
        )

    def default_filter_file(self, src_path: str, text: str) -> str:
        """Run default filtering on a file."""
        # pylint: disable=too-many-branches

        # Strip out any sections frames by our strip-begin/end tags.

        def _first_index_containing_string(
            items: list[str], substring: str
        ) -> int | None:
            for f_index, f_item in enumerate(items):
                if substring in f_item:
                    return f_index
            return None

        # Quick-out if no begin-tags are found in the entire text.
        if any(t[0] in text for t in self._strip_tags):
            lines = text.splitlines()

            for begin_tag, end_tag, fsetname in self._strip_tags:
                # For sections requiring a specific fset, don't touch
                # it if we're keeping that set.
                if (
                    fsetname is not None
                    and fsetname in self._src_retain_feature_sets
                ):
                    continue
                while (
                    index := _first_index_containing_string(lines, begin_tag)
                ) is not None:
                    # while begin_tag in lines:
                    # index = lines.index(begin_tag)
                    endindex = index
                    while end_tag not in lines[endindex]:
                        endindex += 1

                    # If the line after us is blank,
                    # include it too to keep spacing clean.
                    if (
                        len(lines) > (endindex + 1)
                        and not lines[endindex + 1].strip()
                    ):
                        endindex += 1

                    del lines[index : endindex + 1]

            text = '\n'.join(lines) + '\n'

        # Add warnings to some of the git-managed files that we write.
        if src_path == 'README.md':
            blurb = (
                '(this readme is autogenerated by spinoff; '
                'make any edits in source project)'
            )
            lines = self.default_filter_text(text).splitlines()
            return '\n'.join([blurb, ' '] + lines)
        if 'Jenkinsfile' in src_path:
            blurb = (
                '// THIS FILE IS AUTOGENERATED BY SPINOFF;'
                ' MAKE ANY EDITS IN SOURCE PROJECT'
            )
            lines = self.default_filter_text(text).splitlines()
            return '\n'.join([blurb, ''] + lines)
        if src_path in ['.gitattributes']:
            blurb = (
                '# THIS FILE IS AUTOGENERATED BY SPINOFF;'
                ' MAKE ANY EDITS IN SOURCE PROJECT'
            )
            lines = self.default_filter_text(text).splitlines()
            return '\n'.join([blurb, ''] + lines)

        # Jetbrains dict files will get sorted differently after filtering
        # words; go ahead and do that as we filter to avoid triggering
        # difference errors next time the dst dict is saved.
        # FIXME: generalize this for any jetbrains dict path; not just mine.
        if src_path.endswith('/ericf.xml'):
            from efrotools.code import sort_jetbrains_dict

            return sort_jetbrains_dict(self.default_filter_text(text))

        # baenv.py will run a standard app loop if exec'ed, but this
        # requires base. Error instead if base is missing.
        if src_path == 'src/assets/ba_data/python/baenv.py':
            assert 'base' in self._src_all_feature_sets
            if 'base' in self._src_omit_feature_sets:
                text = replace_exact(
                    text,
                    '        import babase\n',
                    '        # (Hack; spinoff disabled babase).\n'
                    '        if TYPE_CHECKING:\n'
                    '            from typing import Any\n'
                    '\n'
                    '        # import babase\n'
                    '\n'
                    '        babase: Any = None\n'
                    '        if bool(True):\n'
                    "            raise CleanError('babase not present')\n",
                    label=src_path,
                )

        # In our public repo, if the plus featureset is not included, we
        # don't want to fetch or link against the precompiled plus
        # library.
        assert 'plus' in self._src_all_feature_sets
        if self._public and 'plus' in self._src_omit_feature_sets:
            if src_path == 'ballisticakit-cmake/CMakeLists.txt':
                # Strip precompiled plus library out of the cmake file.
                text = replace_exact(
                    text,
                    '${CMAKE_CURRENT_BINARY_DIR}/prefablib/libballisticaplus.a'
                    ' ode ',
                    'ode ',
                    label=src_path,
                    count=2,
                )
            if src_path.startswith(
                'ballisticakit-windows/'
            ) and src_path.endswith('.vcxproj'):
                # Strip precompiled plus library out of visual studio projects.
                text = replace_exact(
                    text,
                    '  <ItemGroup>\r\n'
                    '    <Library Include="..\\..\\build\\prefab\\lib\\windows'
                    '\\$(Configuration)_$(Platform)\\'
                    '$(MSBuildProjectName)Plus.lib" />\r\n'
                    '  </ItemGroup>\r\n',
                    '',
                    label=src_path,
                )
            if src_path == 'Makefile':
                # Remove downloads of prebuilt plus lib for win builds.
                text = replace_exact(
                    text,
                    '   build/prefab/lib/windows/Debug_$(WINPREVSP)/'
                    'BallisticaKitGenericPlus.lib \\\n'
                    '   build/prefab/lib/windows/Debug_$(WINPREVSP)/'
                    'BallisticaKitGenericPlus.pdb\n',
                    '',
                    count=2,
                    label=src_path,
                )
                text = replace_exact(
                    text,
                    '   build/prefab/lib/windows/Release_$(WINPREVSP)/'
                    'BallisticaKitGenericPlus.lib \\\n'
                    '   build/prefab/lib/windows/Release_$(WINPREVSP)/'
                    'BallisticaKitGenericPlus.pdb\n',
                    '',
                    count=2,
                    label=src_path,
                )
                # Remove prebuilt lib download for cmake & cmake-modular
                # targets.
                text = replace_exact(
                    text,
                    '\t@tools/pcommand update_cmake_prefab_lib standard'
                    ' $(CM_BT_LC) \\\n'
                    '      build/cmake/$(CM_BT_LC)\n',
                    '',
                    label=src_path,
                )
                text = replace_exact(
                    text,
                    '\t@tools/pcommand update_cmake_prefab_lib server'
                    ' $(CM_BT_LC) \\\n'
                    '      build/cmake/server-$(CM_BT_LC)\n',
                    '',
                    label=src_path,
                )
                text = replace_exact(
                    text,
                    '\t@tools/pcommand update_cmake_prefab_lib standard'
                    ' $(CM_BT_LC) \\\n'
                    '      build/cmake/modular-$(CM_BT_LC)\n',
                    '',
                    label=src_path,
                )
                text = replace_exact(
                    text,
                    '\t@tools/pcommand update_cmake_prefab_lib server'
                    ' $(CM_BT_LC) \\\n'
                    '      build/cmake/modular-server-$(CM_BT_LC)\n',
                    '',
                    label=src_path,
                )

        return self.default_filter_text(text)

    def _encoding_for_file(self, path: str) -> str:
        """Returns the text encoding a file requires."""

        # Just make sure this path is valid; at some point we may want to
        # crack the file.
        if not os.path.isfile(path):
            raise RuntimeError('invalid path passed to _encoding_for_file')

        # These files seem to get cranky if we try to convert them to utf-8.
        # TODO: I think I read that MSVC 2017+ might be more lenient here;
        # should check that out because this is annoying.
        if path.endswith('BallisticaKit.rc') or path.endswith('Resource.rc'):
            return 'utf-16le'
        return 'utf-8'

    def _filter_file(self, src_path: str, text: str) -> str:
        """Run filtering on a given file."""

        # Run our registered filter call.
        out = self.filter_file_call(self, src_path, text)

        # Run formatting on some files if they change. Otherwise, running
        # a preflight in the dst project could change things, leading to
        # 'spinoff-managed-file-changed' errors.

        # Note that we use our parent repo for these commands to pick up their
        # tool configs, since those might not exist yet in our child repo.
        # (This also means we need to make sure tool configs have been
        # generated in the parent repo).

        # WARNING: hard-coding a few 'script' files that don't end in .py too.
        # The proper way might be to ask the parent repo for its full list of
        # script files but that would add more expense.
        if (
            src_path.endswith('.py')
            # or src_path in {'tools/cloudshell'}
        ) and out != text:
            self._ensure_parent_repo_tool_configs_exist()
            out = format_python_str(projroot=self._src_root, code=out)

        # Ditto for .cc
        if src_path.endswith('.cc') and out != text:
            self._ensure_parent_repo_tool_configs_exist()
            out = format_cpp_str(
                projroot=Path(self._src_root),
                text=out,
                filename=os.path.basename(src_path),
            )

        return out

    def _ensure_parent_repo_tool_configs_exist(self) -> None:
        if not self._built_parent_repo_tool_configs:
            # Interestingly, seems we need to use shell command cd here
            # instead of just passing cwd arg.
            subprocess.run(
                f'cd {self._src_root} && make env',
                shell=True,
                check=True,
                capture_output=True,
            )
            self._built_parent_repo_tool_configs = True

    def _should_filter_src_file(self, path: str) -> bool:
        """Return whether a given file should be filtered."""
        basename = os.path.basename(path)
        ext = os.path.splitext(basename)[1]
        if any(path.startswith(f'{p}/') for p in self.filter_dirs):
            return True
        if any(path.startswith(f'{p}/') for p in self.no_filter_dirs):
            return False
        if basename in self.filter_file_names:
            return True
        if basename in self.no_filter_file_names:
            return False
        if ext in self.filter_file_extensions:
            return True
        if ext in self.no_filter_file_extensions:
            return False
        raise RuntimeError(f"No filter rule for path '{path}'.")

    def _should_add_gitignore_path(self, path: str) -> bool:
        """Return whether a file path should be added to gitignore."""
        assert self._spinoff_managed_dirs is not None

        # Special case: specific dirs/files we *always* want in git
        # should never get added to gitignore.
        if _any_path_contains(self.git_mirrored_paths, path):
            return False

        # If there's a spinoff-managed dir above us, we're already covered.
        if any(path.startswith(f'{d}/') for d in self._spinoff_managed_dirs):
            return False

        # Go ahead and ignore.
        return True

    def _print_error_entities(self) -> None:
        """Print info about entity errors encountered."""
        print(
            '\nSpinoff Error(s) Found:\n'
            "  Tips: To resolve 'spinoff-managed file modified' errors,\n"
            "         use the 'backport' subcommand.\n"
            "        To debug other issues, try the 'describe-path'"
            ' subcommand.\n',
            file=sys.stderr,
        )
        for key, val in sorted(self._src_error_entities.items()):
            dst = self._src_entities[key].dst
            print(
                f'     {Clr.RED}Error: {dst}{Clr.RST} ({val})',
                file=sys.stderr,
            )
        for key, val in sorted(self._dst_error_entities.items()):
            print(
                f'     {Clr.RED}Error: {key}{Clr.RST} ({val})',
                file=sys.stderr,
            )
        print('')

    def _validate_final_lists(self) -> None:
        """Check some last things on our entities lists before we update."""

        # Go through the final set of files we're syncing to dst and
        # make sure none of them fall under our unchecked-paths list.
        # That would mean we are writing a file but we're also declaring
        # that we don't care if anyone else writes that file, which
        # could lead to ambiguous/dangerous situations where spinoff as
        # well as some command on dst write to the same file.
        # print('CHECKING', self._src_copy_entities)
        # for ent in self._src_copy_entities:
        #     if _any_path_contains(self._dst_unchecked_paths, ent):
        #         raise CleanError('FOUND BAD PATH', ent)

        for ent in self._dst_purge_entities.copy():
            if _any_path_contains(self.git_mirrored_paths, ent):
                print(
                    'WARNING; git-mirrored entity'
                    f" '{ent}' unexpectedly found on purge list. Ignoring.",
                    file=sys.stderr,
                )
                self._dst_purge_entities.remove(ent)

    def _purge_all_dst_entities(self) -> None:
        """Go through everything in dst and add it to our purge list.

        (or error if unsafe to do so)
        """
        for key, val in list(self._dst_entities.items()):
            # We never want to purge git-managed stuff.
            if _any_path_contains(self.git_mirrored_paths, key):
                continue

            dst_path = key
            dst_path_full = os.path.join(self._dst_root, dst_path)

            # If dst doesnt exist we just ignore it.
            if not os.path.exists(dst_path_full):
                continue

            # For symlinks we just error if dst is no longer a symlink;
            # otherwise kill it.
            if val.entity_type is EntityType.SYMLINK:
                if not os.path.islink(dst_path_full):
                    self._dst_error_entities[dst_path] = 'expected a symlink'
                    continue
                self._dst_purge_entities.add(dst_path)
                continue

            # Cor regular files we try to make sure nothing changed
            # since we put it there.
            src_path = val.src_path
            assert src_path is not None
            src_path_full = os.path.join(self._src_root, src_path)
            dst_size = val.dst_size
            dst_mtime = val.dst_mtime

            if (os.path.getsize(dst_path_full) == dst_size) and (
                os.path.getmtime(dst_path_full) == dst_mtime
            ):
                self._dst_purge_entities.add(key)
            else:
                self._attempt_purge_modified_dst(
                    src_path, src_path_full, dst_path, dst_path_full, key
                )

    def _attempt_purge_modified_dst(
        self,
        src_path: str,
        src_path_full: str,
        dst_path: str,
        dst_path_full: str,
        key: str,
    ) -> None:
        # pylint: disable=too-many-positional-arguments

        # Ick; dst changed.  Now the only way we allow
        # the delete is if we can re-filter its src
        # and come up with the same dst again
        # (meaning it probably just had its timestamp
        # changed and nothing else).
        if self._should_filter_src_file(src_path):
            encoding = self._encoding_for_file(src_path_full)
            with open(src_path_full, 'rb') as infile:
                try:
                    src_data = self._filter_file(
                        src_path, infile.read().decode(encoding)
                    )
                except Exception:
                    print(f"Error decoding/filtering file: '{src_path}'.")
                    raise
            with open(dst_path_full, 'rb') as infile:
                try:
                    dst_data = infile.read().decode(encoding)
                except Exception:
                    print(f"Error decoding file: '{dst_path}'.")
                    raise
            still_same = src_data == dst_data
        else:
            with open(src_path_full, 'rb') as infile_b:
                src_data_b = infile_b.read()
            with open(dst_path_full, 'rb') as infile_b:
                dst_data_b = infile_b.read()
            still_same = src_data_b == dst_data_b
        if still_same:
            self._dst_purge_entities.add(key)
        else:
            self._dst_error_entities[dst_path] = 'spinoff-managed file modified'

    def _remove_empty_folders(
        self, path: str, remove_root: bool = True
    ) -> None:
        """Remove empty folders."""
        if not os.path.isdir(path):
            return

        # Ignore symlinks.
        if os.path.islink(path):
            return

        # Remove empty subdirs.
        fnames = os.listdir(path)
        if fnames:
            for fname in fnames:
                # Special case; never recurse into .git dirs; blowing
                # away empty dirs there can be harmful. Note: Do we want
                # to use ignore_names here? Seems like we'd still want
                # to delete other entries there like __pycache__ though.
                if fname == '.git':
                    continue

                fullpath = os.path.join(path, fname)
                if os.path.isdir(fullpath):
                    self._remove_empty_folders(fullpath)

        # If folder is *now* empty, delete it.
        fnames = os.listdir(path)
        if not fnames and remove_root:
            os.rmdir(path)

    def _handle_recache_entities(self) -> None:
        """Re-cache some special case entries.

        For these entries we simply re-cache modtimes/sizes
        but don't touch any actual files.
        """
        for src_path in self._src_recache_entities:
            src_entity = self._src_entities[src_path]
            dst_path = src_entity.dst
            src_path_full = os.path.join(self._src_root, src_path)
            dst_path_full = os.path.join(self._dst_root, dst_path)
            self._dst_entities[dst_path] = DstEntity(
                entity_type=src_entity.entity_type,
                env_hash=self._envhash,
                src_path=src_path,
                src_mtime=os.path.getmtime(src_path_full),
                src_size=os.path.getsize(src_path_full),
                dst_mtime=os.path.getmtime(dst_path_full),
                dst_size=os.path.getsize(dst_path_full),
            )

    def _status(self) -> None:
        self._validate_final_lists()
        self._handle_recache_entities()
        max_print = 10

        # FIXME: We should show .gitignore here in cases when it would change
        #  (we handle that specially).
        if self._src_copy_entities:
            print(
                f'\n{len(self._src_copy_entities)}'
                f' file(s) would be updated:\n',
                file=sys.stderr,
            )
            src_copy_entities_truncated = sorted(self._src_copy_entities)
            if (
                not self._print_full_lists
                and len(src_copy_entities_truncated) > max_print
            ):
                src_copy_entities_truncated = src_copy_entities_truncated[
                    :max_print
                ]
            for ename in src_copy_entities_truncated:
                dst_path_full = os.path.join(
                    self._dst_root, self._src_entities[ename].dst
                )
                exists = os.path.exists(dst_path_full)
                modstr = 'modified' if exists else 'new'
                dstent = self._src_entities[ename].dst
                print(
                    f'     {Clr.GRN}{modstr}:  {dstent}{Clr.RST}',
                    file=sys.stderr,
                )
            if len(src_copy_entities_truncated) != len(self._src_copy_entities):
                morecnt = len(self._src_copy_entities) - len(
                    src_copy_entities_truncated
                )
                print(
                    f'    {Clr.GRN}{Clr.BLD}(plus {morecnt} more;'
                    f' pass --full for complete list){Clr.RST}',
                    file=sys.stderr,
                )
        dst_purge_entities_valid: set[str] = set()
        if self._dst_purge_entities:
            self._list_dst_purge_entities(dst_purge_entities_valid, max_print)
        if not self._src_copy_entities and not dst_purge_entities_valid:
            print(f'{Clr.GRN}Spinoff is up-to-date.{Clr.RST}', file=sys.stderr)
        else:
            print('')

    def _list_dst_purge_entities(
        self, dst_purge_entities_valid: set[str], max_print: int
    ) -> None:
        for ent in self._dst_purge_entities:
            dst_path_full = os.path.join(self._dst_root, ent)

            # Only make note of the deletion if it exists.
            if (
                os.path.exists(dst_path_full)
                # and ent not in self._dst_entities_delete_quietly
            ):
                dst_purge_entities_valid.add(ent)
        if dst_purge_entities_valid:
            print(
                f'\n{len(dst_purge_entities_valid)} file(s)'
                ' would be removed:\n',
                file=sys.stderr,
            )
        dst_purge_entities_truncated = sorted(dst_purge_entities_valid)
        if (
            not self._print_full_lists
            and len(dst_purge_entities_truncated) > max_print
        ):
            dst_purge_entities_truncated = dst_purge_entities_truncated[
                :max_print
            ]
        for ent in sorted(dst_purge_entities_truncated):
            print(f'     {Clr.GRN}{ent}{Clr.RST}', file=sys.stderr)
        if len(dst_purge_entities_truncated) != len(dst_purge_entities_valid):
            num_more = len(dst_purge_entities_valid) - len(
                dst_purge_entities_truncated
            )
            print(
                f'     {Clr.GRN}{Clr.BLD}(plus {num_more} more;'
                f' pass --full for complete list){Clr.RST}',
                file=sys.stderr,
            )

    def _override(self) -> None:
        """Add one or more overrides."""
        try:
            override_paths, src_paths = self._check_override_paths()

            # To take an existing dst file out of spinoff management we need
            # to do 3 things:
            # - Add it to src_omit_paths to keep the src version from being
            #   synced in.
            # - Add it to src_write_paths to ensure git has control over
            #   its location in dst.
            # - Remove our dst entry for it to prevent spinoff from blowing
            #   it away when it sees the src entry no longer exists.

            if not os.path.exists(self._dst_config_path):
                raise RuntimeError(
                    f"Config file not found: '{self._dst_config_path}'."
                )
            with open(self._dst_config_path, encoding='utf-8') as infile:
                config = infile.read()

            config = _add_config_list_entry(config, 'src_omit_paths', src_paths)
            config = _add_config_list_entry(
                config, 'src_write_paths', src_paths
            )

            # Ok, now we simply remove it from tracking while leaving the
            # existing file in place.
            for override_path in override_paths:
                del self._dst_entities[override_path]

            with open(self._dst_config_path, 'w', encoding='utf-8') as outfile:
                outfile.write(config)

            for override_path in override_paths:
                print(
                    f"'{override_path}' overridden. It should now show"
                    ' up as untracked by git (you probably want to add it).'
                )

        except Exception as exc:
            self._execution_error = True
            print(f'{Clr.RED}Error{Clr.RST}: {exc}', file=sys.stderr)

    def _check_override_paths(self) -> tuple[set[str], set[str]]:
        assert self._override_paths is not None
        # Return the set of dst overridden paths and the src paths
        # they came from.
        src_paths = set[str]()
        override_paths = set[str]()
        for arg in self._override_paths:
            override_path_full = os.path.abspath(arg)
            if not override_path_full.startswith(self._dst_root):
                raise CleanError(
                    f'Override-path {override_path_full} does not reside'
                    f' under dst ({self._dst_root}).'
                )
            # TODO(ericf): generalize this now that we're no longer hard-coded
            #  to use submodules/ballistica. Should disallow any path under
            #  any submodule I suppose.
            if override_path_full.startswith(
                os.path.join(self._dst_root, 'submodules')
            ):
                raise RuntimeError('Path can not reside under submodules.')
            override_path = override_path_full[len(self._dst_root) + 1 :]
            if not os.path.exists(override_path_full):
                raise RuntimeError(f"Path does not exist: '{override_path}'.")

            # For the time being we only support individual files here.
            if not os.path.isfile(override_path_full):
                raise RuntimeError(
                    f"path does not appear to be a file: '{override_path}'."
                )

            # Make sure this is a file we're tracking.
            if override_path not in self._dst_entities:
                raise RuntimeError(
                    f'Path does not appear to be'
                    f" tracked by spinoff: '{override_path}'."
                )

            # Disallow git-mirrored-paths.
            # We would have to add special handling for this.
            if _any_path_contains(self.git_mirrored_paths, override_path):
                raise RuntimeError(
                    'Not allowed to override special git-managed path:'
                    f" '{override_path}'."
                )

            src_path = self._dst_entities[override_path].src_path
            assert src_path is not None
            src_paths.add(src_path)
            override_paths.add(override_path)
        return override_paths, src_paths

    def _diff(self) -> None:
        self._validate_final_lists()
        self._handle_recache_entities()

        if os.system('which colordiff > /dev/null 2>&1') == 0:
            display_diff_cmd = 'colordiff'
        else:
            print(
                'NOTE: for color-coded output, install "colordiff" via brew.',
                file=sys.stderr,
            )
            display_diff_cmd = 'diff'

        for src_path in sorted(self._src_copy_entities):
            src_entity = self._src_entities[src_path]
            dst_path = src_entity.dst
            src_path_full = os.path.join(self._src_root, src_path)
            dst_path_full = os.path.join(self._dst_root, dst_path)
            try:
                if src_entity.entity_type is EntityType.SYMLINK:
                    pass

                elif src_entity.entity_type is EntityType.FILE:
                    self._diff_file(
                        src_path,
                        src_path_full,
                        dst_path,
                        dst_path_full,
                        display_diff_cmd,
                    )
                else:
                    assert_never(src_entity.entity_type)

            except Exception as exc:
                self._execution_error = True
                print(
                    f"{Clr.RED}Error diffing file: '{src_path_full}'"
                    f'{Clr.RST}: {exc}',
                    file=sys.stderr,
                )

    def _diff_file(
        self,
        src_path: str,
        src_path_full: str,
        dst_path: str,
        dst_path_full: str,
        display_diff_cmd: str,
    ) -> None:
        # pylint: disable=too-many-positional-arguments

        if os.path.isfile(src_path_full) and os.path.isfile(dst_path_full):
            # We want to show how this update would change the dst file,
            # so we need to compare a filtered version of src to the
            # existing dst. For non-filtered src files we can just do a
            # direct compare
            delete_file_name: str | None
            if self._should_filter_src_file(src_path):
                with tempfile.NamedTemporaryFile('wb', delete=False) as tmpf:
                    with open(src_path_full, 'rb') as infile:
                        encoding = self._encoding_for_file(src_path_full)
                        try:
                            contents_in = infile.read().decode(encoding)
                        except Exception:
                            print(f"Error decoding file: '{src_path}'.")
                            raise
                        contents_out = self._filter_file(src_path, contents_in)
                        tmpf.write(contents_out.encode(encoding))
                        delete_file_name = tmpf.name
                        tmpf.close()
                diff_src_path_full = delete_file_name
            else:
                diff_src_path_full = src_path_full
                delete_file_name = None
            result = os.system(
                f'diff "{diff_src_path_full}" "{dst_path_full}"'
                f' > /dev/null 2>&1'
            )
            if result != 0:
                print(f'\n{dst_path}:')
                os.system(
                    f'{display_diff_cmd} "{dst_path_full}"'
                    f' "{diff_src_path_full}"'
                )
                print('')

            if delete_file_name is not None:
                os.remove(delete_file_name)

    def _is_project_file(self, path: str) -> bool:
        if path.startswith('tools/') or path.startswith('src/external'):
            return False
        bname = os.path.basename(path)
        return (
            path in self.project_file_paths
            or bname in self.project_file_names
            or any(bname.endswith(s) for s in self.project_file_suffixes)
        )

    def _update(self) -> None:
        """Run a variation of the "update" command."""
        self._validate_final_lists()
        self._handle_recache_entities()

        # Let's print individual updates only if there's few of them.
        print_individual_updates = len(self._src_copy_entities) < 50

        project_src_paths: list[str] = []

        # Run all file updates except for project ones (Makefiles, etc.)
        # Which we wait for until the end.
        for src_path in sorted(self._src_copy_entities):
            if self._is_project_file(src_path):
                project_src_paths.append(src_path)
            else:
                self._handle_src_copy(src_path, print_individual_updates)

        # Now attempt to remove anything in our purge list.
        removed_f_count = self._remove_purge_entities()

        # Update project files after all other copies and deletes are done.
        # This is because these files take the state of the project on disk
        # into account, so we need all files they're looking at to be final.
        if project_src_paths:
            from batools.project import ProjectUpdater

            assert self._project_updater is None
            self._project_updater = ProjectUpdater(
                self._dst_root,
                check=False,
                fix=False,
                empty=True,
                projname=self.default_filter_text(self._src_name),
            )

            # For project-updater to do its thing, we need to provide
            # filtered source versions of *all* project files which
            # might be changing. (Some project files may implicitly
            # generate others as part of their own generation so we need
            # all sources in place before any generation happens).
            for src_path in project_src_paths:
                self._handle_src_copy_project_updater_register(src_path)

            # Ok; everything is registered. Can now use the updater to
            # filter dst versions of these.
            self._project_updater.prepare_to_generate()
            for src_path in project_src_paths:
                self._handle_src_copy(
                    src_path, print_individual_updates, is_project_file=True
                )

        # Print some overall results.
        if self._src_copy_entities:
            print(
                f'{len(self._src_copy_entities)} file(s) updated.',
                file=sys.stderr,
            )

        if removed_f_count > 0:
            print(f'{removed_f_count} file(s) removed.', file=sys.stderr)

        # If we didn't update any files or delete anything, say so.
        if removed_f_count == 0 and not self._src_copy_entities:
            print('Spinoff is up-to-date.', file=sys.stderr)

    def _handle_src_copy_project_updater_register(self, src_path: str) -> None:
        src_entity = self._src_entities[src_path]
        dst_path = src_entity.dst
        src_path_full = os.path.join(self._src_root, src_path)
        # dst_path_full = os.path.join(self._dst_root, dst_path)

        # Currently assuming these are filtered.
        assert self._should_filter_src_file(src_path)
        assert src_entity.entity_type is EntityType.FILE
        encoding = self._encoding_for_file(src_path_full)
        with open(src_path_full, 'rb') as infile:
            try:
                contents_in = infile.read().decode(encoding)
            except Exception:
                print(f"Error decoding file: '{src_path}'.")
                raise
        contents_out = self._filter_file(src_path, contents_in)

        # Take the filtered spinoff contents from src and plug that into
        # the project updater as the 'current' version of the file. The
        # updater will then update it based on the current state of the
        # project.
        assert self._project_updater is not None
        self._project_updater.enqueue_update(dst_path, contents_out)

    def _handle_src_copy(
        self,
        src_path: str,
        print_individual_updates: bool,
        is_project_file: bool = False,
    ) -> None:
        # pylint: disable=too-many-locals
        src_entity = self._src_entities[src_path]
        dst_path = src_entity.dst
        src_path_full = os.path.join(self._src_root, src_path)
        dst_path_full = os.path.join(self._dst_root, dst_path)
        try:
            # Create its containing dir if need be.
            dirname = os.path.dirname(dst_path_full)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            mode = os.lstat(src_path_full).st_mode

            if src_entity.entity_type is EntityType.SYMLINK:
                assert not is_project_file  # Undefined.
                linkto = os.readlink(src_path_full)
                if os.path.islink(dst_path_full):
                    os.remove(dst_path_full)
                os.symlink(linkto, dst_path_full)
                dst_entity = DstEntity(
                    entity_type=src_entity.entity_type,
                    env_hash=None,
                    src_path=None,
                    src_mtime=None,
                    src_size=None,
                    dst_mtime=None,
                    dst_size=None,
                )

            elif src_entity.entity_type is EntityType.FILE:
                dst_entity = self._handle_src_copy_file(
                    src_path,
                    src_path_full,
                    dst_path,
                    dst_path_full,
                    src_entity,
                    is_project_file,
                )
                os.chmod(dst_path_full, mode)
            else:
                raise RuntimeError(
                    f"Invalid entity type: '{src_entity.entity_type}'."
                )

            # NOTE TO SELF - was using lchmod here but it doesn't exist
            # on linux (apparently symlinks can't have perms modified).
            # Now doing a chmod above only for the 'file' path.
            # os.lchmod(dst_path_full, mode)
            self._dst_entities[dst_path] = dst_entity
            if print_individual_updates:
                print(
                    f'  updated: {Clr.GRN}{dst_path}{Clr.RST}', file=sys.stderr
                )

        except Exception as exc:
            # Attempt to remove whatever we just put there so we avoid
            # 'non-managed-file-found' errors in subsequent runs.
            try:
                if os.path.exists(dst_path_full):
                    os.unlink(dst_path_full)
            except Exception as exc2:
                print(
                    f'{Clr.RED}Error removing failed dst file: {exc2}{Clr.RST}'
                )
            self._execution_error = True
            verbose_note = (
                '' if self._verbose else ' (use --verbose for full traceback)'
            )
            print(
                f'{Clr.RED}Error copying/filtering file:'
                f" '{src_path_full}'{Clr.RST}: {exc}{verbose_note}",
                file=sys.stderr,
            )
            if self._verbose:
                import traceback

                traceback.print_exc(file=sys.stderr)

    def _handle_src_copy_file(
        self,
        src_path: str,
        src_path_full: str,
        dst_path: str,
        dst_path_full: str,
        src_entity: SrcEntity,
        is_project_file: bool,
    ) -> DstEntity:
        # pylint: disable=too-many-positional-arguments

        # If this is a project file, we already fed the filtered
        # src into our ProjectUpdater instance, so all we do here is
        # have the updater give us its output.
        if is_project_file:
            assert self._project_updater is not None
            try:
                pupdatedata = self._project_updater.generate_file(dst_path)
            except Exception:
                if bool(False):
                    print(f"ProjectUpdate error generating '{dst_path}'.")
                    import traceback

                    traceback.print_exc()
                raise
            with open(dst_path_full, 'w', encoding='utf-8') as outfile:
                outfile.write(pupdatedata)
        else:
            # Normal non-project file path.
            if not self._should_filter_src_file(src_path):
                with open(src_path_full, 'rb') as infile:
                    data = infile.read()
                with open(dst_path_full, 'wb') as outfile:
                    outfile.write(data)
            else:
                with open(src_path_full, 'rb') as infile:
                    encoding = self._encoding_for_file(src_path_full)
                    try:
                        contents_in = infile.read().decode(encoding)
                    except Exception:
                        print(f"Error decoding file: '{src_path}'.")
                        raise
                    contents_out = self._filter_file(src_path, contents_in)
                    with open(dst_path_full, 'wb') as outfile:
                        outfile.write(contents_out.encode(encoding))

        return DstEntity(
            entity_type=src_entity.entity_type,
            env_hash=self._envhash,
            src_path=src_path,
            src_mtime=os.path.getmtime(src_path_full),
            src_size=os.path.getsize(src_path_full),
            dst_mtime=os.path.getmtime(dst_path_full),
            dst_size=os.path.getsize(dst_path_full),
        )

    def _remove_purge_entities(self) -> int:
        removed_f_count = 0
        if self._dst_purge_entities:
            for ent in sorted(self._dst_purge_entities):
                dst_path_full = os.path.join(self._dst_root, ent)
                try:
                    if os.path.isfile(dst_path_full) or os.path.islink(
                        dst_path_full
                    ):
                        os.remove(dst_path_full)
                        del self._dst_entities[ent]
                        removed_f_count += 1
                    elif not os.path.exists(dst_path_full):
                        # It's already gone; no biggie.
                        del self._dst_entities[ent]
                    else:
                        print(
                            f"Anomaly removing file: '{dst_path_full}'.",
                            file=sys.stderr,
                        )
                except Exception:
                    self._execution_error = True
                    print(
                        f"Error removing file: '{dst_path_full}'.",
                        file=sys.stderr,
                    )
        return removed_f_count

    def _clean_cruft(self) -> None:
        """Clear out some known cruft-y files.

        Makes us more likely to be able to clear directories (.DS_Store, etc)
        """

        # Go through our list of dirs above files we've mapped to dst,
        # cleaning out any 'cruft' files we find there.
        assert self._dst_git_file_dirs is not None
        for dstdir in self._dst_git_file_dirs:
            dstdirfull = os.path.join(self._dst_root, dstdir)
            if not os.path.isdir(dstdirfull):
                continue
            for fname in os.listdir(dstdirfull):
                if fname in self.cruft_file_names:
                    cruftpath = os.path.join(dstdirfull, fname)
                    try:
                        os.remove(cruftpath)
                    except Exception:
                        print(
                            f"error removing cruft file: '{cruftpath}'.",
                            file=sys.stderr,
                        )
        self._remove_empty_folders(self._dst_root, False)

    def _check_spinoff_managed_dirs(self) -> None:
        assert self._spinoff_managed_dirs is not None
        # Spinoff-managed dirs are marked gitignore which means we are
        # fully responsible for them. We thus want to be careful
        # to avoid silently blowing away work that may have happened
        # in one. So let's be rather strict about it and complain about
        # any files we come across that aren't directly managed by us
        # (or cruft).
        dstrootsl = f'{self._dst_root}/'
        for rdir in self._spinoff_managed_dirs:
            for root, dirnames, fnames in os.walk(
                os.path.join(self._dst_root, rdir),
                topdown=True,
            ):
                # Completely ignore ignore-names in both dirs and files
                # and cruft-file names in files.
                for dirname in dirnames.copy():
                    if dirname in self.ignore_names:
                        dirnames.remove(dirname)
                for fname in fnames.copy():
                    if (
                        fname in self.ignore_names
                        or fname in self.cruft_file_names
                    ):
                        fnames.remove(fname)

                for fname in fnames:
                    dst_path_full = os.path.join(root, fname)
                    assert dst_path_full.startswith(dstrootsl)
                    dst_path = dst_path_full.removeprefix(dstrootsl)

                    # If its not a mapped-in file from src and not
                    # covered by generated-paths or git-mirror-paths,
                    # complain.
                    if (
                        dst_path not in self._dst_entities
                        and not _any_path_contains(
                            self._dst_unchecked_paths, dst_path
                        )
                        and not _any_path_contains(
                            self.git_mirrored_paths, dst_path
                        )
                        and not self._force
                    ):
                        self._dst_error_entities[dst_path] = (
                            'non-spinoff file in spinoff-managed dir;'
                            ' --force to ignore'
                        )

    def _filter_src_git_file_list(self) -> None:
        # Create a filtered version of src git files based on our omit
        # entries.
        out = set[str]()
        assert self._src_git_files is not None
        for gitpath in self._src_git_files:
            # If omit-path contains this one or any component is found
            # in omit-names, pretend it doesn't exist.
            if _any_path_contains(self._src_omit_paths_expanded, gitpath):
                continue  # Omitting
            if any(name in gitpath.split('/') for name in self.ignore_names):
                continue
            out.add(gitpath)
        self._src_git_files = out

    def _register_sync_operations(self) -> None:
        assert self._src_git_files is not None
        for src_path in self._src_git_files:
            dst_path = self._filter_path(src_path)

            src_path_full = os.path.join(self._src_root, src_path)
            dst_path_full = os.path.join(self._dst_root, dst_path)

            if os.path.islink(src_path_full):
                self._do_copy_symlink(
                    src_path, src_path_full, dst_path, dst_path_full
                )
            else:
                assert os.path.isfile(src_path_full)
                self._do_file_copy_and_filter(
                    src_path, src_path_full, dst_path, dst_path_full
                )

    def _do_copy_symlink(
        self,
        src_path: str,
        src_path_full: str,
        dst_path: str,
        dst_path_full: str,
    ) -> None:
        self._src_entities[src_path] = SrcEntity(
            entity_type=EntityType.SYMLINK, dst=dst_path
        )
        if dst_path not in self._dst_entities:
            self._src_copy_entities.add(src_path)
        else:
            dst_type = self._dst_entities[dst_path].entity_type
            if dst_type is not EntityType.SYMLINK:
                self._src_error_entities[src_path] = (
                    f'expected symlink; found {dst_type}'
                )
            else:
                # Ok; looks like there's a symlink already there.
                self._dst_entities_claimed.add(dst_path)

                # See if existing link is pointing to the right place &
                # schedule a copy if not.
                linkto = os.readlink(src_path_full)
                if (
                    not os.path.islink(dst_path_full)
                    or os.readlink(dst_path_full) != linkto
                ):
                    self._src_copy_entities.add(src_path)

    def _do_file_copy_and_filter(
        self,
        src_path: str,
        src_path_full: str,
        dst_path: str,
        dst_path_full: str,
    ) -> None:
        self._src_entities[src_path] = SrcEntity(
            entity_type=EntityType.FILE, dst=dst_path
        )
        if dst_path not in self._dst_entities:
            # If we're unaware of dst, copy or error if something's
            # there already (except for our git-managed files in which
            # case we *expect* something to be there).
            if (
                os.path.exists(dst_path_full)
                and not _any_path_contains(self.git_mirrored_paths, src_path)
                and not self._force
            ):
                self._src_error_entities[src_path] = (
                    'would overwrite non-spinoff file in dst;'
                    ' --force to override'
                )
            else:
                self._src_copy_entities.add(src_path)
        else:
            dst_type = self._dst_entities[dst_path].entity_type
            if dst_type is not EntityType.FILE:
                self._src_error_entities[src_path] = (
                    f'expected file; found {dst_type}'
                )
            else:
                dst_exists = os.path.isfile(dst_path_full)

                # Ok; we know of a dst file and it seems to exist. If both
                # src and dst data still lines up with our cache we can
                # assume there's nothing to be done.
                dst_entity = self._dst_entities[dst_path]
                # pylint: disable=too-many-boolean-expressions
                if (
                    dst_exists
                    and dst_entity.env_hash == self._envhash
                    and os.path.getsize(dst_path_full) == dst_entity.dst_size
                    and os.path.getmtime(dst_path_full) == dst_entity.dst_mtime
                    and os.path.getsize(src_path_full) == dst_entity.src_size
                    and os.path.getmtime(src_path_full) == dst_entity.src_mtime
                ):
                    pass
                else:
                    # *Something* differs from our cache; we have work to do.
                    self._do_differing_file_copy_and_filter(
                        src_path,
                        src_path_full,
                        dst_path,
                        dst_path_full,
                        dst_entity,
                        dst_exists,
                    )

                self._dst_entities_claimed.add(dst_path)

    def _do_differing_file_copy_and_filter(
        self,
        src_path: str,
        src_path_full: str,
        dst_path: str,
        dst_path_full: str,
        dst_entity: DstEntity,
        dst_exists: bool,
    ) -> None:
        # pylint: disable=too-many-positional-arguments
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        # Ok, *something* differs from our cache. Need to take a closer look.

        # With no dst we have to do the copy of course.
        if not dst_exists:
            self._src_copy_entities.add(src_path)
            return

        do_backport = False

        src_datab: bytes | None = None
        dst_datab: bytes | None = None
        src_data: str | None = None
        dst_data: str | None = None

        # In strict mode we want it to always be an error if dst mod-time
        # varies from the version we wrote (we want to track down anyone
        # writing to our managed files who is not us).
        # Note that we need to ignore git-mirrored-paths because git might
        # be mucking with modtimes itself.
        if (
            self.strict
            and not self._force
            and os.path.getmtime(dst_path_full) != dst_entity.dst_mtime
            and not _any_path_contains(self.git_mirrored_paths, src_path)
        ):
            # Try to include when the dst file got modified in
            # case its helpful.
            sincestr = (
                ''
                if dst_entity.dst_mtime is None
                else (
                    ' '
                    + timedelta_str(
                        os.path.getmtime(dst_path_full) - dst_entity.dst_mtime,
                        maxparts=1,
                        decimals=2,
                    )
                )
            )
            self._src_error_entities[src_path] = (
                f'[STRICT] spinoff-managed file modified{sincestr}'
                f' after spinoff wrote it;'
                f' --force to overwrite from src'
            )
            return

        is_project_file = self._is_project_file(src_path)

        if is_project_file:
            # Project files apply arbitrary logic on top of our
            # copying/filtering (which we cannot check here) so we can
            # never assume results are unchanging.
            results_are_same = False
        else:
            # Let's filter the src file and if it matches dst we can just
            # re-grab our cache info and call it a day.
            if self._should_filter_src_file(src_path):
                encoding = self._encoding_for_file(src_path_full)
                with open(src_path_full, 'rb') as infile:
                    try:
                        src_data = self._filter_file(
                            src_path, infile.read().decode(encoding)
                        )
                    except Exception:
                        print(f"Error decoding/filtering file: '{src_path}'.")
                        raise
                with open(dst_path_full, 'rb') as infile:
                    try:
                        dst_data = infile.read().decode(encoding)
                    except Exception:
                        print(f"Error decoding file: '{dst_path}'.")
                        raise
                results_are_same = src_data == dst_data

                # Bytes versions are only used very rarely by 'backport'
                # command so let's lazy compute them here.
                src_datab = dst_datab = None
            else:
                # Ok our src isn't filtered; can be a bit more streamlined.
                with open(src_path_full, 'rb') as infile:
                    src_datab = infile.read()
                with open(dst_path_full, 'rb') as infile:
                    dst_datab = infile.read()
                results_are_same = src_datab == dst_datab

                # No string versions needed in this case.
                src_data = dst_data = None

        if results_are_same:
            # Things match; just update the times we've got recorded
            # for these fellas.
            self._src_recache_entities.add(src_path)
        else:
            if (os.path.getsize(dst_path_full) == dst_entity.dst_size) and (
                os.path.getmtime(dst_path_full) == dst_entity.dst_mtime
            ):
                # If it looks like dst did not change, we can go
                # through with a standard update.
                self._src_copy_entities.add(src_path)
            elif _any_path_contains(self.git_mirrored_paths, src_path):
                # Ok, dst changed but it is managed by git so this
                # happens (switching git branches or whatever else...)
                # in this case we just blindly replace it; no erroring.
                self._src_copy_entities.add(src_path)
            elif self._force:
                # If the user is forcing the issue, do the overwrite.
                self._src_copy_entities.add(src_path)
            elif (os.path.getsize(src_path_full) == dst_entity.src_size) and (
                os.path.getmtime(src_path_full) == dst_entity.src_mtime
            ):
                # Ok, dst changed but src did not. This is an error.

                # Try to include when the dst file got modified in
                # case its helpful.
                sincestr = (
                    ''
                    if dst_entity.dst_mtime is None
                    else (
                        ' '
                        + timedelta_str(
                            os.path.getmtime(dst_path_full)
                            - dst_entity.dst_mtime,
                            maxparts=1,
                            decimals=2,
                        )
                    )
                )
                self._src_error_entities[src_path] = (
                    f'spinoff-managed file modified{sincestr}'
                    f' after spinoff wrote it;'
                    f' --force to overwrite from src'
                )

                # Allow backport process here to correct this.
                if self._mode is self.Mode.BACKPORT and (
                    self._backport_file == dst_path
                    or self._backport_file is None
                ):
                    do_backport = True
            else:
                # Ok, *nothing* matches (file contents don't match
                # and both modtimes differ from cached ones).
                # User needs to sort this mess out.
                self._src_error_entities[src_path] = (
                    'src AND spinoff-managed file modified;'
                    ' --force to overwrite from src'
                )

                # Allow backport process here to correct this.
                if self._mode is self.Mode.BACKPORT and (
                    self._backport_file == dst_path
                    or self._backport_file is None
                ):
                    do_backport = True

        if do_backport:
            # Lazy compute string version if needed.
            if src_data is None:
                assert src_datab is not None
                src_data = src_datab.decode()
            if dst_data is None:
                assert dst_datab is not None
                dst_data = dst_datab.decode()
            self._backport(src_path, dst_path, src_data, dst_data)

    def _backport(
        self, src_path: str, dst_path: str, src_data: str, dst_data: str
    ) -> None:
        is_filtered = self._should_filter_src_file(src_path)
        full_src_path = os.path.join(self._src_root, src_path)

        # If we're doing auto-backport, just do the thing (when we can)
        # and keep on going.
        if self._auto_backport:
            if is_filtered:
                print(
                    f"{Clr.YLW}Can't auto-backport filtered file:{Clr.RST}"
                    f' {Clr.BLD}{dst_path}{Clr.RST}'
                )
                self._auto_backport_fail_count += 1
            else:
                src_path_full = os.path.join(self._src_root, src_path)
                dst_path_full = os.path.join(self._dst_root, dst_path)
                assert os.path.isfile(src_path_full)
                assert os.path.isfile(dst_path_full)
                subprocess.run(['cp', dst_path_full, src_path_full], check=True)
                print(
                    f'{Clr.BLU}Auto-backporting{Clr.RST}'
                    f' {Clr.BLD}{dst_path}{Clr.RST}'
                )
                self._auto_backport_success_count += 1
            return

        # Ok NOT auto-backporting; we'll show a diff and stop after the
        # first file.

        # If this isn't a filtered file, it makes things easier.
        if not is_filtered:
            print(
                f'Backporting {Clr.BLD}{dst_path}{Clr.RST}:\n'
                f'{Clr.GRN}This file is NOT filtered so backporting'
                f' is simple.{Clr.RST}\n'
                f'{Clr.BLU}{Clr.BLD}LEFT:{Clr.RST}'
                f' src file\n'
                f'{Clr.BLU}{Clr.BLD}RIGHT:{Clr.RST} dst file\n'
                f'{Clr.BLU}{Clr.BLD}YOUR MISSION:{Clr.RST}'
                f' move changes from dst back to src.\n'
                f"{Clr.CYN}Or pass '--auto' to the backport subcommand"
                f' to do this for you.{Clr.RST}'
            )
            subprocess.run(
                [
                    'opendiff',
                    os.path.join(self._src_root, src_path),
                    os.path.join(self._dst_root, dst_path),
                ],
                check=True,
                capture_output=True,
            )

        else:
            # It IS filtered.

            print(
                f'Backporting {Clr.BLD}{dst_path}{Clr.RST}:\n'
                f'{Clr.YLW}This file is filtered which complicates'
                f' backporting a bit.{Clr.RST}\n'
                f'{Clr.BLU}{Clr.BLD}LEFT:{Clr.RST}'
                f' {Clr.CYN}{Clr.BLD}FILTERED{Clr.RST}'
                ' src file\n'
                f'{Clr.BLU}{Clr.BLD}RIGHT:{Clr.RST} dst file\n'
                f'{Clr.BLU}{Clr.BLD}YOUR MISSION:{Clr.RST}'
                f' modify {Clr.CYN}{Clr.BLD}ORIGINAL{Clr.RST}'
                f' src file such that filtered src matches dst:\n'
                f'{Clr.BLD}{full_src_path}{Clr.RST}'
            )
            with tempfile.TemporaryDirectory() as tempdir:
                srcname = os.path.basename(src_path)
                dstname = os.path.basename(dst_path)
                tsrcpath = os.path.join(tempdir, f'FILTERED-PARENT({srcname})')
                tdstpath = os.path.join(tempdir, f'SPINOFF({dstname})')
                with open(tsrcpath, 'w', encoding='utf-8') as outfile:
                    outfile.write(src_data)
                with open(tdstpath, 'w', encoding='utf-8') as outfile:
                    outfile.write(dst_data)
                subprocess.run(
                    ['opendiff', tsrcpath, tdstpath],
                    check=True,
                    capture_output=True,
                )

        # Bow out after this one single file. Otherwise we wind up showing
        # all errors (one of which we might have just fixed) which is
        # misleading.
        raise self.BackportInProgressError()

    def _filter_paths(self, paths: Iterable[str]) -> set[str]:
        return set(self._filter_path(p) for p in paths)


def _any_path_contains(paths: Iterable[str], path: str) -> bool:
    assert not path.endswith('/')

    for tpath in paths:
        # Use simple logic if there's no special chars used by fnmatch.
        if not any(char in tpath for char in ('*', '?', '[')):
            if tpath == path or path.startswith(f'{tpath}/'):
                return True
        else:
            # Bust out the fancy logic.
            # Split both paths into segments ('a/b/c' -> ['a','b','c'])
            # and compare each using fnmatch. If all segments
            # from tpath match corresponding ones in path then tpath
            # is a parent.
            pathsegs = path.split('/')
            tpathsegs = tpath.split('/')
            if len(tpathsegs) > len(pathsegs):
                continue  # tpath is deeper than path; can't contain it.
            all_matches = True
            for i in range(len(tpathsegs)):  # pylint: disable=C0200
                seg_matches = fnmatch.fnmatchcase(pathsegs[i], tpathsegs[i])
                if not seg_matches:
                    all_matches = False
                    break
            if all_matches:
                return True
    return False


def _get_dir_levels(dirpath: str) -> list[str]:
    """For 'a/b/c' return ['a', 'a/b', 'a/b/c']."""
    splits = dirpath.split('/')
    return ['/'.join(splits[: (i + 1)]) for i in range(len(splits))]


def _add_config_list_entry(
    config: str, list_name: str, add_paths: set[str]
) -> str:
    # pylint: disable=eval-used
    splits = config.split(f'{list_name}: list[str] = [')
    if len(splits) != 2:
        raise RuntimeError('Parse error.')
    splits2 = splits[1].split(']')
    paths = eval(f'[{splits2[0]}]')
    assert isinstance(paths, list)
    for add_path in add_paths:
        if add_path in paths:
            raise RuntimeError(
                f'Path already present in {list_name} in spinoffconfig:'
                f" '{add_path}'."
            )
        paths.append(add_path)

    config = (
        splits[0]
        + f'{list_name}: list[str] = [\n'
        + ''.join([f'    {repr(p)},\n' for p in sorted(paths)])
        + ']'.join([''] + splits2[1:])
    )
    return config
