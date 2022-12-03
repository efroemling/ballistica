# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to modding."""
from __future__ import annotations

from typing import TYPE_CHECKING
import os

import _ba

if TYPE_CHECKING:
    from typing import Sequence


def get_human_readable_user_scripts_path() -> str:
    """Return a human readable location of user-scripts.

    This is NOT a valid filesystem path; may be something like "(SD Card)".
    """
    app = _ba.app
    path: str | None = app.python_directory_user
    if path is None:
        return '<Not Available>'

    # These days, on Android, we use getExternalFilesDir() as the base of our
    # app's user-scripts dir, which gives us paths like:
    # /storage/emulated/0/Android/data/net.froemling.bombsquad/files
    # Userspace apps tend to show that as:
    # Android/data/net.froemling.bombsquad/files
    # We'd like to display it that way, but I'm not sure if there's a clean
    # way to get the root of the external storage area (/storage/emulated/0)
    # so that we could strip it off. There is
    # Environment.getExternalStorageDirectory() but that is deprecated.
    # So for now let's just be conservative and trim off recognized prefixes
    # and show the whole ugly path as a fallback.
    # Note that we used to use externalStorageText resource but gonna try
    # without it for now. (simply 'foo' instead of <External Storage>/foo).
    if app.platform == 'android':
        for pre in ['/storage/emulated/0/']:
            if path.startswith(pre):
                path = path.removeprefix(pre)
                break
    return path


def _request_storage_permission() -> bool:
    """If needed, requests storage permission from the user (& return true)."""
    from ba._language import Lstr
    from ba._generated.enums import Permission

    if not _ba.have_permission(Permission.STORAGE):
        _ba.playsound(_ba.getsound('error'))
        _ba.screenmessage(
            Lstr(resource='storagePermissionAccessText'), color=(1, 0, 0)
        )
        _ba.timer(1.0, lambda: _ba.request_permission(Permission.STORAGE))
        return True
    return False


def show_user_scripts() -> None:
    """Open or nicely print the location of the user-scripts directory."""
    app = _ba.app

    # First off, if we need permission for this, ask for it.
    if _request_storage_permission():
        return

    # Secondly, if the dir doesn't exist, attempt to make it.
    if not os.path.exists(app.python_directory_user):
        os.makedirs(app.python_directory_user)

    # On android, attempt to write a file in their user-scripts dir telling
    # them about modding. This also has the side-effect of allowing us to
    # media-scan that dir so it shows up in android-file-transfer, since it
    # doesn't seem like there's a way to inform the media scanner of an empty
    # directory, which means they would have to reboot their device before
    # they can see it.
    if app.platform == 'android':
        try:
            usd: str | None = app.python_directory_user
            if usd is not None and os.path.isdir(usd):
                file_name = usd + '/about_this_folder.txt'
                with open(file_name, 'w', encoding='utf-8') as outfile:
                    outfile.write(
                        'You can drop files in here to mod the game.'
                        '  See settings/advanced'
                        ' in the game for more info.'
                    )

        except Exception:
            from ba import _error

            _error.print_exception('error writing about_this_folder stuff')

    # On a few platforms we try to open the dir in the UI.
    if app.platform in ['mac', 'windows']:
        _ba.open_dir_externally(app.python_directory_user)

    # Otherwise we just print a pretty version of it.
    else:
        _ba.screenmessage(get_human_readable_user_scripts_path())


def create_user_system_scripts() -> None:
    """Set up a copy of Ballistica system scripts under your user scripts dir.

    (for editing and experiment with)
    """
    import shutil

    app = _ba.app

    # First off, if we need permission for this, ask for it.
    if _request_storage_permission():
        return

    path = app.python_directory_user + '/sys/' + app.version
    pathtmp = path + '_tmp'
    if os.path.exists(path):
        shutil.rmtree(path)
    if os.path.exists(pathtmp):
        shutil.rmtree(pathtmp)

    def _ignore_filter(src: str, names: Sequence[str]) -> Sequence[str]:
        del src, names  # Unused

        # We simply skip all __pycache__ directories. (the user would have
        # to blow them away anyway to make changes;
        # See https://github.com/efroemling/ballistica/wiki
        # /Knowledge-Nuggets#python-cache-files-gotcha
        return ('__pycache__',)

    print(f'COPYING "{app.python_directory_app}" -> "{pathtmp}".')
    shutil.copytree(app.python_directory_app, pathtmp, ignore=_ignore_filter)

    print(f'MOVING "{pathtmp}" -> "{path}".')
    shutil.move(pathtmp, path)
    print(
        f"Created system scripts at :'{path}"
        f"'\nRestart {_ba.appname()} to use them."
        f' (use ba.quit() to exit the game)'
    )
    if app.platform == 'android':
        print(
            'Note: the new files may not be visible via '
            'android-file-transfer until you restart your device.'
        )


def delete_user_system_scripts() -> None:
    """Clean out the scripts created by create_user_system_scripts()."""
    import shutil

    app = _ba.app
    path = app.python_directory_user + '/sys/' + app.version
    if os.path.exists(path):
        shutil.rmtree(path)
        print(
            f'User system scripts deleted.\n'
            f'Restart {_ba.appname()} to use internal'
            f' scripts. (use ba.quit() to exit the game)'
        )
    else:
        print('User system scripts not found.')

    # If the sys path is empty, kill it.
    dpath = app.python_directory_user + '/sys'
    if os.path.isdir(dpath) and not os.listdir(dpath):
        os.rmdir(dpath)
