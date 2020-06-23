# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Functionality related to modding."""
from __future__ import annotations

from typing import TYPE_CHECKING
import os

import _ba

if TYPE_CHECKING:
    from typing import Optional, List, Sequence


def get_human_readable_user_scripts_path() -> str:
    """Return a human readable location of user-scripts.

    This is NOT a valid filesystem path; may be something like "(SD Card)".
    """
    from ba import _lang
    app = _ba.app
    path: Optional[str] = app.python_directory_user
    if path is None:
        return '<Not Available>'

    # On newer versions of android, the user's external storage dir is probably
    # only visible to the user's processes and thus not really useful printed
    # in its entirety; lets print it as <External Storage>/myfilepath.
    if app.platform == 'android':
        ext_storage_path: Optional[str] = (
            _ba.android_get_external_storage_path())
        if (ext_storage_path is not None
                and app.python_directory_user.startswith(ext_storage_path)):
            path = ('<' +
                    _lang.Lstr(resource='externalStorageText').evaluate() +
                    '>' + app.python_directory_user[len(ext_storage_path):])
    return path


def _request_storage_permission() -> bool:
    """If needed, requests storage permission from the user (& return true)."""
    from ba._lang import Lstr
    from ba._enums import Permission
    if not _ba.have_permission(Permission.STORAGE):
        _ba.playsound(_ba.getsound('error'))
        _ba.screenmessage(Lstr(resource='storagePermissionAccessText'),
                          color=(1, 0, 0))
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
            usd: Optional[str] = app.python_directory_user
            if usd is not None and os.path.isdir(usd):
                file_name = usd + '/about_this_folder.txt'
                with open(file_name, 'w') as outfile:
                    outfile.write('You can drop files in here to mod the game.'
                                  '  See settings/advanced'
                                  ' in the game for more info.')
                _ba.android_media_scan_file(file_name)
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

    path = (app.python_directory_user + '/sys/' + app.version)
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
        return ('__pycache__', )

    print(f'COPYING "{app.python_directory_app}" -> "{pathtmp}".')
    shutil.copytree(app.python_directory_app, pathtmp, ignore=_ignore_filter)

    print(f'MOVING "{pathtmp}" -> "{path}".')
    shutil.move(pathtmp, path)
    print(f"Created system scripts at :'{path}"
          f"'\nRestart {_ba.appname()} to use them."
          f' (use ba.quit() to exit the game)')
    if app.platform == 'android':
        print('Note: the new files may not be visible via '
              'android-file-transfer until you restart your device.')


def delete_user_system_scripts() -> None:
    """Clean out the scripts created by create_user_system_scripts()."""
    import shutil
    app = _ba.app
    path = (app.python_directory_user + '/sys/' + app.version)
    if os.path.exists(path):
        shutil.rmtree(path)
        print(f'User system scripts deleted.\n'
              f'Restart {_ba.appname()} to use internal'
              f' scripts. (use ba.quit() to exit the game)')
    else:
        print('User system scripts not found.')

    # If the sys path is empty, kill it.
    dpath = app.python_directory_user + '/sys'
    if os.path.isdir(dpath) and not os.listdir(dpath):
        os.rmdir(dpath)
