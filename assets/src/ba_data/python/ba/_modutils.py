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

import os

import _ba


def get_human_readable_user_scripts_path() -> str:
    """Return a human readable location of user-scripts.

    This is NOT a valid filesystem path; may be something like "(SD Card)".
    """
    from ba import _lang
    app = _ba.app
    path = app.user_scripts_directory
    if path is None:
        return '<Not Available>'

    # On newer versions of android, the user's external storage dir is probably
    # only visible to the user's processes and thus not really useful printed
    # in its entirety; lets print it as <External Storage>/myfilepath.
    if app.platform == 'android':
        ext_storage_path = (_ba.android_get_external_storage_path())
        if (ext_storage_path is not None
                and app.user_scripts_directory.startswith(ext_storage_path)):
            path = ('<' +
                    _lang.Lstr(resource='externalStorageText').evaluate() +
                    '>' + app.user_scripts_directory[len(ext_storage_path):])
    return path


def show_user_scripts() -> None:
    """Open or nicely print the location of the user-scripts directory."""
    from ba import _lang
    from ba._enums import Permission
    app = _ba.app

    # First off, if we need permission for this, ask for it.
    if not _ba.have_permission(Permission.STORAGE):
        _ba.playsound(_ba.getsound('error'))
        _ba.screenmessage(_lang.Lstr(resource='storagePermissionAccessText'),
                          color=(1, 0, 0))
        _ba.request_permission(Permission.STORAGE)
        return

    # Secondly, if the dir doesn't exist, attempt to make it.
    if not os.path.exists(app.user_scripts_directory):
        os.makedirs(app.user_scripts_directory)

    # On android, attempt to write a file in their user-scripts dir telling
    # them about modding. This also has the side-effect of allowing us to
    # media-scan that dir so it shows up in android-file-transfer, since it
    # doesn't seem like there's a way to inform the media scanner of an empty
    # directory, which means they would have to reboot their device before
    # they can see it.
    if app.platform == 'android':
        try:
            usd = app.user_scripts_directory
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
        _ba.open_dir_externally(app.user_scripts_directory)

    # Otherwise we just print a pretty version of it.
    else:
        _ba.screenmessage(get_human_readable_user_scripts_path())


def create_user_system_scripts() -> None:
    """Set up a copy of Ballistica system scripts under your user scripts dir.

    (for editing and experiment with)
    """
    app = _ba.app
    import shutil
    path = (app.user_scripts_directory + '/sys/' + app.version)
    if os.path.exists(path):
        shutil.rmtree(path)
    if os.path.exists(path + "_tmp"):
        shutil.rmtree(path + "_tmp")
    os.makedirs(path + '_tmp', exist_ok=True)

    # Hmm; shutil.copytree doesn't seem to work nicely on android,
    # so lets do it manually.
    src_dir = app.system_scripts_directory
    dst_dir = path + "_tmp"
    filenames = os.listdir(app.system_scripts_directory)
    for fname in filenames:
        print('COPYING', src_dir + '/' + fname, '->', dst_dir)
        shutil.copyfile(src_dir + '/' + fname, dst_dir + '/' + fname)

    print('MOVING', path + "_tmp", path)
    shutil.move(path + "_tmp", path)
    print(
        ('Created system scripts at :\'' + path +
         '\'\nRestart Ballistica to use them. (use ba.quit() to exit the game)'
         ))
    if app.platform == 'android':
        print('Note: the new files may not be visible via '
              'android-file-transfer until you restart your device.')


def delete_user_system_scripts() -> None:
    """Clean out the scripts created by create_user_system_scripts()."""
    import shutil
    app = _ba.app
    path = (app.user_scripts_directory + '/sys/' + app.version)
    if os.path.exists(path):
        shutil.rmtree(path)
        print(
            'User system scripts deleted.\nRestart Ballistica to use internal'
            ' scripts. (use ba.quit() to exit the game)')
    else:
        print('User system scripts not found.')

    # If the sys path is empty, kill it.
    dpath = app.user_scripts_directory + '/sys'
    if os.path.isdir(dpath) and not os.listdir(dpath):
        os.rmdir(dpath)
