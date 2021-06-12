# Released under the MIT License. See LICENSE for details.
#
"""Tools related to ios development."""

from __future__ import annotations

import pathlib
import subprocess
import sys
from dataclasses import dataclass

from efrotools import getlocalconfig, getconfig

MODES = {
    'debug': {
        'configuration': 'Debug'
    },
    'release': {
        'configuration': 'Release'
    }
}


@dataclass
class Config:
    """Configuration values for this project."""

    # Project relative xcodeproj path ('MyAppName/MyAppName.xcodeproj').
    projectpath: str

    # App bundle name ('MyAppName.app').
    app_bundle_name: str

    # Base name of the ipa archive to be pushed ('myappname').
    archive_name: str

    # Scheme to build ('MyAppName iOS').
    scheme: str


@dataclass
class LocalConfig:
    """Configuration values specific to the machine."""

    # Sftp host ('myuserid@myserver.com').
    sftp_host: str

    # Path to push ipa to ('/home/myhome/dir/where/i/want/this/).
    sftp_dir: str


def push_ipa(root: pathlib.Path, modename: str) -> None:
    """Construct ios IPA and push it to staging server for device testing.

    This takes some shortcuts to minimize turnaround time;
    It doesn't recreate the ipa completely each run, uses rsync
    for speedy pushes to the staging server, etc.
    The use case for this is quick build iteration on a device
    that is not physically near the build machine.
    """

    # Load both the local and project config data.
    cfg = Config(**getconfig(root)['push_ipa_config'])
    lcfg = LocalConfig(**getlocalconfig(root)['push_ipa_local_config'])

    if modename not in MODES:
        raise Exception('invalid mode: "' + str(modename) + '"')
    mode = MODES[modename]

    pcommand_path = pathlib.Path(root, 'tools/pcommand')
    xcprojpath = pathlib.Path(root, cfg.projectpath)
    app_dir = subprocess.run(
        [pcommand_path, 'xcode_build_path', xcprojpath, mode['configuration']],
        check=True,
        capture_output=True).stdout.decode().strip()
    built_app_path = pathlib.Path(app_dir, cfg.app_bundle_name)

    workdir = pathlib.Path(root, 'build', 'push_ipa')
    workdir.mkdir(parents=True, exist_ok=True)

    pathlib.Path(root, 'build').mkdir(parents=True, exist_ok=True)
    exportoptionspath = pathlib.Path(root, workdir, 'exportoptions.plist')
    ipa_dir_path = pathlib.Path(root, workdir, 'ipa')
    ipa_dir_path.mkdir(parents=True, exist_ok=True)

    # Inject our latest build into an existing xcarchive (creating if needed).
    archivepath = _add_build_to_xcarchive(workdir, xcprojpath, built_app_path,
                                          cfg)

    # Export an IPA from said xcarchive.
    ipa_path = _export_ipa_from_xcarchive(archivepath, exportoptionspath,
                                          ipa_dir_path, cfg)

    # And lastly sync said IPA up to our staging server.
    print('Pushing to staging server...')
    sys.stdout.flush()
    subprocess.run(
        [
            'rsync', '--verbose', ipa_path, '-e',
            'ssh -oBatchMode=yes -oStrictHostKeyChecking=yes',
            f'{lcfg.sftp_host}:{lcfg.sftp_dir}'
        ],
        check=True,
    )

    print('iOS Package Updated Successfully!')


def _add_build_to_xcarchive(workdir: pathlib.Path, xcprojpath: pathlib.Path,
                            built_app_path: pathlib.Path,
                            cfg: Config) -> pathlib.Path:
    archivepathbase = pathlib.Path(workdir, cfg.archive_name)
    archivepath = pathlib.Path(workdir, cfg.archive_name + '.xcarchive')

    # Rebuild a full archive if one doesn't exist.
    if not archivepath.exists():
        print('Base archive not found; doing full build (can take a while)...')
        sys.stdout.flush()
        args = [
            'xcodebuild', 'archive', '-project',
            str(xcprojpath), '-scheme', cfg.scheme, '-configuration',
            MODES['debug']['configuration'], '-archivePath',
            str(archivepathbase)
        ]
        subprocess.run(args, check=True, capture_output=False)

    # Now copy our just-built app into the archive.
    print('Copying build to archive...')
    sys.stdout.flush()
    archive_app_path = pathlib.Path(
        archivepath, 'Products/Applications/' + cfg.app_bundle_name)
    subprocess.run(['rm', '-rf', archive_app_path], check=True)
    subprocess.run(['cp', '-r', built_app_path, archive_app_path], check=True)
    return archivepath


def _export_ipa_from_xcarchive(archivepath: pathlib.Path,
                               exportoptionspath: pathlib.Path,
                               ipa_dir_path: pathlib.Path,
                               cfg: Config) -> pathlib.Path:
    import textwrap
    print('Exporting IPA...')
    exportoptions = textwrap.dedent("""
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
         "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
                <key>compileBitcode</key>
                <false/>
                <key>destination</key>
                <string>export</string>
                <key>method</key>
                <string>development</string>
                <key>signingStyle</key>
                <string>automatic</string>
                <key>stripSwiftSymbols</key>
                <true/>
                <key>teamID</key>
                <string>G7TQB7SM63</string>
                <key>thinning</key>
                <string>&lt;none&gt;</string>
        </dict>
        </plist>
    """).strip()
    with exportoptionspath.open('w') as outfile:
        outfile.write(exportoptions)

    sys.stdout.flush()
    args = [
        'xcodebuild', '-allowProvisioningUpdates', '-exportArchive',
        '-archivePath',
        str(archivepath), '-exportOptionsPlist',
        str(exportoptionspath), '-exportPath',
        str(ipa_dir_path)
    ]
    try:
        subprocess.run(args, check=True, capture_output=True)
    except Exception:
        print('Error exporting code-signed archive; '
              ' perhaps try running "security unlock-keychain login.keychain"')
        raise

    ipa_path_exported = pathlib.Path(ipa_dir_path, cfg.scheme + '.ipa')
    ipa_path = pathlib.Path(ipa_dir_path, cfg.archive_name + '.ipa')
    subprocess.run(['mv', ipa_path_exported, ipa_path], check=True)
    return ipa_path
