# Released under the MIT License. See LICENSE for details.
#
"""XCode related functionality."""
from __future__ import annotations

import os
import hashlib
from typing import TYPE_CHECKING

import openstep_parser as osp
from pbxproj import XcodeProject
from pbxproj.pbxextensions import TreeType, PBXGroup

# Need to patch XcodeProject slightly to support .cc files.
# noinspection PyProtectedMember
xcft = XcodeProject._FILE_TYPES  # pylint: disable=protected-access
if '.cc' not in xcft:
    xcft['.cc'] = xcft['.cpp']

# Normally header files are added to a copy-headers build phase;
# we don't want that (its only really relevant for frameworks and
# its something else we'd need to worry about restoring uuids for).
xcft['.h'] = (xcft['.h'][0], None)

if TYPE_CHECKING:
    from typing import Any


def update_xcode_project(
    projroot: str,
    path: str,
    existing_data: str,
    all_source_files: list[str],
    projname: str,
    force: bool = False,
) -> str:
    """Given an xcode project, update it for the current set of files."""

    pbasename = os.path.basename(path)
    if pbasename.endswith('-mac.xcodeproj') or pbasename.endswith(
        '-ios.xcodeproj'
    ):
        suffixes = ['.cc', '.h', '.m', '.mm']
        updater = Updater(
            projroot,
            path,
            existing_data,
            sorted(
                p
                for p in all_source_files
                if os.path.splitext(p)[1] in suffixes
            ),
            # has_app_delegate_mm=True,
            projname=projname,
        )
    else:
        suffixes = ['.cc', '.h', '.m', '.mm', '.swift']
        updater = Updater(
            projroot,
            path,
            existing_data,
            sorted(
                p
                for p in all_source_files
                if os.path.splitext(p)[1] in suffixes
            ),
            # has_app_delegate_mm=True,
            projname=projname,
        )

    return updater.run(force=force)


class Updater:
    """Does the thing."""

    project: Any

    def __init__(
        self,
        projroot: str,
        path: str,
        existing_data: str,
        sources: list[str],
        projname: str,
        # has_app_delegate_mm: bool = False,
    ) -> None:
        if not path.endswith('.xcodeproj'):
            raise RuntimeError(f"Path does not end in .xcodeproj: '{path}'.")

        self.projroot = projroot
        self.path = path
        self.existing_data = existing_data
        self.sources = sources
        self.project = None
        # self.has_app_delegate_mm = has_app_delegate_mm

        # Project name variations.
        self.pnameu = projname
        self.pnamel = projname.lower()

        # uuids associated with a given file path
        # (grp/file obj and possibly build-files)
        self.old_path_uuids: dict[str, list[str]] = {}
        self.new_path_uuids: dict[str, list[str]] = {}

        self.print_test = False

    def run(self, force: bool = False) -> str:
        """Do the thing."""
        # pylint: disable=too-many-locals

        projpath = os.path.join(self.projroot, self.path, 'project.pbxproj')

        # Make a hash out of all paths we'd add combined with the incoming
        # state of this project. If this calced hash matches the current
        # on-disk hash, we can assume our output would match the input
        # and just deliver the input.
        projsrc = self.existing_data

        fhash = self.hash_inputs(
            self.sources, include_us=True, project_source=projsrc
        )

        # WARNING - this cache naming convention assumes all project
        # basenames are unique regardless of dir (currently true but
        # maybe won't always be).
        _dirname, basename = os.path.split(self.path)
        basebasename = os.path.splitext(basename)[0]
        cachedir = os.path.join(self.projroot, '.cache')
        os.makedirs(cachedir, exist_ok=True)
        hashpath = os.path.join(cachedir, f'xcode_src_hash_{basebasename}')

        if os.path.exists(hashpath):
            with open(hashpath, encoding='utf-8') as infile:
                currenthash = infile.read()
        else:
            currenthash = None

        # If hash still matches, return incoming project state.
        if currenthash == fhash and not force:
            # with open(projpath, encoding='utf-8') as infile:
            #     existing_file = infile.read()
            # FIXME: Its weird to be feeding our hash file back out to
            #  the project system; we should probably just manage it
            #  completely internally.
            return self.existing_data

        tree = osp.OpenStepDecoder.ParseFromString(self.existing_data)
        self.project = XcodeProject(tree, projpath)
        # self.project = XcodeProject.load(projpath)

        bgrp = self._get_unique_group('ballistica')
        assert isinstance(bgrp.get_id(), str)

        # Store uuids for all existing paths under ballistica and then
        # blow it away. When we're done rebuilding ballistica we'll
        # restore uuids on any paths that got remade. This keeps changes
        # to the pbxproj file much more minimal which is good for git,
        # and is simpler to accomplish than doing more selective
        # adds/removes would be.
        self._store_path_uuids(bgrp.get_id(), self.old_path_uuids, '')
        self.project.remove_group_by_id(bgrp.get_id())

        srcgrp = self._get_unique_group(f'{self.pnameu} Shared')
        self.add_paths(srcgrp)

        # if self.has_app_delegate_mm:
        #     self.mod_app_delegate_mm()

        # Groups we made should be sorted already since we sorted while
        # building them, but let's sort the top level group we placed
        # our stuff *into*.
        srcgrp.children.sort(
            key=lambda c: self.project.objects[c].get_name().lower()
        )

        # Now store uuids for the new stuff we made.
        bgrp = self._get_unique_group('ballistica')
        assert isinstance(bgrp.get_id(), str)
        self._store_path_uuids(bgrp.get_id(), self.new_path_uuids, '')

        # Now filter the raw project file to replace new uuids with old
        # ones when possible.
        self._filter_uuids(projpath)

        # Now go through and, for every object with a path equal to its
        # name, kill the name. This seems to match what xcode does so our
        # project structure stays more similar to theirs.
        bgrp = self._get_unique_group('ballistica')
        assert isinstance(bgrp.get_id(), str)
        self._trim_names(bgrp.get_id(), '')

        projsrc = repr(self.project) + '\n'

        # A few hacky last tweaks on the final project source to
        # get ours matching xcode's 100% when possible.
        projsrc = projsrc.replace(
            '/* Build configuration list for PBXProject'
            f' "{self.pnameu} macOS Legacy" */',
            '/* Build configuration list for PBXProject'
            f' "{self.pnamel}-mac" */',
        )

        # The hash we generated above used the project as it exists on disk
        # for checking purposes, so for the one we return we need to
        # regenerate it here to use the project source we just created.
        fhash = self.hash_inputs(
            self.sources, include_us=True, project_source=projsrc
        )
        # Store the new hash.
        if fhash != currenthash:
            with open(hashpath, 'w', encoding='utf-8') as outfile:
                outfile.write(fhash)

        return projsrc

    def _target_name_for_buildfile(self, buildfile: Any) -> str:
        for target in self.project.objects.get_targets():
            for build_phase_id in target.buildPhases:
                build_phase = self.project.objects[build_phase_id]
                if build_phase.isa == 'PBXSourcesBuildPhase':
                    if buildfile.get_id() in build_phase.files:
                        assert isinstance(target.name, str)
                        return target.name

        raise RuntimeError(
            f'Could not deduce target name from build file {buildfile}.'
        )

    def _filter_uuids(self, projpath: str) -> None:
        projtxt = repr(self.project) + '\n'

        # For any path that used to exist in our project, if we
        # find a new uuid for it, replace it with the old one.
        for oldpath, olduuids in self.old_path_uuids.items():
            newuuids = self.new_path_uuids.get(oldpath)
            if newuuids is not None:
                if len(olduuids) != len(newuuids):
                    print(
                        f'uuids count changed for path {oldpath}; unexpected.'
                    )
                else:
                    for olduuid, newuuid in zip(olduuids, newuuids):
                        projtxt = projtxt.replace(newuuid, olduuid)

        # Now replace our existing project with this filtered one.
        # This will properly update ordering for the id swaps we just made.
        tree = osp.OpenStepDecoder.ParseFromString(projtxt)
        self.project = XcodeProject(tree, projpath)

    def _trim_names(self, objid: str, parentpath: str) -> None:
        obj = self.project.objects[objid]
        assert hasattr(obj, 'name')
        objpath = os.path.join(parentpath, obj.name)
        if isinstance(obj, PBXGroup):
            for childid in obj.children:
                self._trim_names(childid, objpath)

        assert hasattr(obj, 'path')
        if obj.path == obj.name:
            delattr(obj, 'name')

    def _store_path_uuids(
        self, objid: str, uuids: dict[str, list[str]], parentpath: str
    ) -> None:
        obj = self.project.objects[objid]

        # Hmmm - seems sometimes things have name but sometimes just path.
        # (assuming maybe when they're identical or something?..)
        if hasattr(obj, 'name'):
            objpath = os.path.join(parentpath, obj.name)
        else:
            assert hasattr(obj, 'path')
            assert '/' not in obj.path
            objpath = os.path.join(parentpath, obj.path)

        # Store this uuid with this path.
        uuidentry = uuids.setdefault(objpath, [])
        uuidentry.append(objid)

        if isinstance(obj, PBXGroup):
            for childid in obj.children:
                self._store_path_uuids(childid, uuids, objpath)
        else:
            buildfiles = self.project.get_build_files_for_file(objid)

            # We'll replace the new buildfile ids with our previous ones;
            # however can come out shuffled (the buildfile for target A
            # might be given the UUID that was previously assigned to the
            # buildfile for target B, etc.) We can fix this by sorting
            # our buildfiles by the target they go with.
            buildfiles.sort(key=self._target_name_for_buildfile)
            for buildfile in buildfiles:
                uuidentry.append(buildfile.get_id())

    def _get_unique_group(self, name: str) -> Any:
        grps = self.project.get_groups_by_name(name)
        if len(grps) != 1:
            raise RuntimeError(
                f'Expected exactly 1 "{name}" group; found {len(grps)}.'
            )
        return grps[0]

    # (No longer used; just leaving here as reference though)
    def mod_app_delegate_mm(self) -> None:
        """Set per-file compiler flags."""
        files = self.project.get_files_by_name('app_delegate.mm')
        if len(files) != 1:
            # Update: no longer expecting to always find this now that
            # it has been moved to base.
            if self.pnameu == 'Ballistica' + 'Kit':
                raise RuntimeError(
                    f'Expected to find exactly 1 app_delegate.mm;'
                    f' found {len(files)}.'
                )
        else:
            bfiles = self.project.get_build_files_for_file(files[0].get_id())

            for bfile in bfiles:
                bfile.add_compiler_flags('-fobjc-arc')

    def hash_inputs(
        self, sources: list[str], include_us: bool, project_source: str
    ) -> str:
        """Make a simple hash based on inputs to the project."""

        if TYPE_CHECKING:
            # Help Mypy infer the right type for this.
            hashobj = hashlib.md5()
        else:
            hashobj = getattr(hashlib, 'md5')()

        # If they're not providing project-source, use what's on disk.

        # Hash our sorted list of sources; when sources are added, removed,
        # or renamed we'll want to rebuild.
        for source in sorted(sources):
            hashobj.update(source.encode())

        # Also hash the project-source we were passed. We do this so that
        # we know to re-run our generation if xcode itself (or whatever else)
        # modifies the project. We want to do that because our generated
        # output might be slightly different than what xcode writes and
        # we want our version to always win out and get stored in git;
        # otherwise CI project checks would see mismatches and complain
        # that the project is out of date. Ideally our output will exactly
        # match xcode's so no rewrites will need to happen, but this way
        # we'll behave even if they do need to.
        hashobj.update(project_source.encode())

        # Also include the full source of this module so we rebuild
        # when logic here is updated.
        if include_us:
            with open(__file__, 'rb') as infile:
                hashobj.update(infile.read())

        return hashobj.hexdigest()

    @staticmethod
    def _xcodesortkey(val: str) -> str:
        # Yes this is super nitpicky, but I'd like to have things
        # show up in xcode such that doing a 'sort by name' doesn't move
        # anything around. The main funky bit of logic with xcode's
        # sorting seems to be that foo.cc shows up *after* foobar.cc,
        # whereas in vanilla Python sorts it comes before. A quick hack
        # to fix this is to replace the . with something that comes after
        # the alphabet instead of before.
        return val.lower().replace('.', '~')

    def add_paths(self, parent_pbxgrp: Any) -> None:
        """Do the thing."""

        # PBXGroups we create for each dir we come across in paths.
        dir_pbxgrps: dict[str, Any] = {}

        # For each path, create/fetch its chain of dirs as PBXGroups and
        # drop the file in the bottom one.
        for source in self.sources:
            parts = source.split('/')
            assert all(p for p in parts)
            for i in range(len(parts) - 1):
                thisname = parts[i]
                thispath = '/'.join(parts[: i + 1])
                if thispath not in dir_pbxgrps:
                    if i == 0:
                        # Root; provide full path.
                        pbxgrp = self.project.get_or_create_group(
                            thisname,
                            os.path.abspath(
                                os.path.join(self.projroot, 'src', thispath)
                            ),
                            parent_pbxgrp,
                            make_relative=True,
                        )
                    else:
                        # Non-root; provide relative path from parent.
                        parentpath = '/'.join(parts[:i])
                        pbxgrp = self.project.get_or_create_group(
                            thisname,
                            thisname,
                            dir_pbxgrps[parentpath],
                            make_relative=True,
                        )
                    dir_pbxgrps[thispath] = pbxgrp

            assert os.path.dirname(source)  # All sources should be in a dir.
            self.project.add_file(
                os.path.basename(source),
                dir_pbxgrps[os.path.dirname(source)],
                force=False,
                tree=TreeType.GROUP,
                target_name=self._target_names_for_file(
                    os.path.basename(source)
                ),
            )

    def _target_names_for_file(self, filename: str) -> list[str] | None:
        # Cocoa stuff only applies to our macOS targets.
        if filename.startswith('Cocoa') and filename.endswith('.swift'):
            return [
                f'{self.pnameu} macOS TestBuild',
                f'{self.pnameu} macOS AppStore',
                f'{self.pnameu} macOS Steam',
            ]
        # A few things only for AppStore bound builds.
        if filename in {'StoreKitContext.swift', 'GameCenterContext.swift'}:
            return [
                f'{self.pnameu} iOS',
                f'{self.pnameu} tvOS',
                f'{self.pnameu} macOS AppStore',
            ]

        # UIKit stuff applies to our iOS/tvOS targets.
        if filename.startswith('UIKit') and filename.endswith('.swift'):
            return [
                f'{self.pnameu} iOS',
                f'{self.pnameu} tvOS',
            ]

        # Everything else applies to everything.
        return None
