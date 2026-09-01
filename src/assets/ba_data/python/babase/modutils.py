# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to modding."""

from typing import TYPE_CHECKING
import os

import _babase
from babase._logging import applog

if TYPE_CHECKING:
    from typing import Sequence


def get_human_readable_user_scripts_path() -> str:
    """Return a human readable location of user-scripts.

    This is NOT a valid filesystem path; may be something like "(SD Card)".
    """
    app = _babase.app
    path: str | None = app.env.python_directory_user
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
    if app.classic is not None and app.classic.platform == 'android':
        for pre in ['/storage/emulated/0/']:
            if path.startswith(pre):
                path = path.removeprefix(pre)
                break
    return path


def _request_storage_permission() -> bool:
    """If needed, requests storage permission from the user (& return true)."""
    from babase import _builtinassets
    from babase._generated.enums import Permission

    if not _babase.have_permission(Permission.STORAGE):
        _builtinassets.audio.error.get().play()
        _babase.screenmessage(
            _builtinassets.strings.ui.storage_permission_needed,
            color=(1, 0, 0),
        )
        _babase.apptimer(
            1.0, lambda: _babase.request_permission(Permission.STORAGE)
        )
        return True
    return False


def show_user_scripts() -> None:
    """Open or nicely print the location of the user-scripts directory."""
    app = _babase.app
    env = app.env

    # First off, if we need permission for this, ask for it.
    if _request_storage_permission():
        return

    # If we're running in a nonstandard environment its possible this is unset.
    if env.python_directory_user is None:
        _babase.screenmessage('<unset>')
        return

    # Secondly, if the dir doesn't exist, attempt to make it.
    if not os.path.exists(env.python_directory_user):
        os.makedirs(env.python_directory_user)

    # On android, attempt to write a file in their user-scripts dir telling
    # them about modding. This also has the side-effect of allowing us to
    # media-scan that dir so it shows up in android-file-transfer, since it
    # doesn't seem like there's a way to inform the media scanner of an empty
    # directory, which means they would have to reboot their device before
    # they can see it.
    if app.classic is not None and app.classic.platform == 'android':
        try:
            usd: str | None = env.python_directory_user
            if usd is not None and os.path.isdir(usd):
                file_name = usd + '/about_this_folder.txt'
                with open(file_name, 'w', encoding='utf-8') as outfile:
                    outfile.write(
                        'You can drop files in here to mod the game.'
                        '  See settings/advanced in the game for more info.'
                    )

        except Exception:
            applog.exception('Error writing about_this_folder stuff.')

    # On platforms that support it, open the dir in the UI.
    if _babase.supports_open_dir_externally():
        _babase.open_dir_externally(env.python_directory_user)

    # Otherwise we just print a pretty version of it.
    else:
        _babase.screenmessage(get_human_readable_user_scripts_path())


def _split_archive_path(path: str) -> tuple[str, str]:
    """Split a path into an archive into (archive_file, inner_prefix)."""
    prefix_parts: list[str] = []
    cur = path
    while cur and not os.path.isfile(cur):
        parent, tail = os.path.split(cur)
        if parent == cur:
            break
        prefix_parts.insert(0, tail)
        cur = parent
    if not cur or not os.path.isfile(cur):
        raise RuntimeError(f"No archive found along path '{path}'.")
    return cur, '/'.join(prefix_parts)


def _extract_archive_scripts(srcpath: str, dstpath: str) -> None:
    """Extract Python sources living inside an archive to a real dir.

    Used for app-script dirs served directly out of an archive (e.g.
    the Android apk). Skips ``.pyc`` entries; the copy is for humans
    to read and edit, and the filesystem importer ignores adjacent
    pycs anyway.
    """
    import shutil
    import zipfile

    archive, prefix = _split_archive_path(srcpath)
    with zipfile.ZipFile(archive) as zfile:
        for member in zfile.namelist():
            if not member.startswith(prefix + '/') or member.endswith('/'):
                continue
            if member.endswith('.pyc') or '__pycache__' in member:
                continue
            relpath = member[len(prefix) + 1 :]
            dstfile = os.path.join(dstpath, relpath)
            os.makedirs(os.path.dirname(dstfile), exist_ok=True)
            with zfile.open(member) as src, open(dstfile, 'wb') as dst:
                shutil.copyfileobj(src, dst)


def create_user_system_scripts() -> None:
    """Set up a copy of Ballistica app scripts under user scripts dir.

    (for editing and experimenting)
    """
    import shutil

    app = _babase.app
    env = app.env

    # First off, if we need permission for this, ask for it.
    if _request_storage_permission():
        return

    # Its possible these are unset in non-standard environments.
    if env.python_directory_user is None:
        raise RuntimeError('user python dir unset')
    if env.python_directory_app is None:
        raise RuntimeError('app python dir unset')

    path = (
        f'{env.python_directory_user}/sys/'
        f'{env.engine_version}_{env.engine_build_number}'
    )
    pathtmp = path + '_tmp'
    if os.path.exists(path):
        print('Delete Existing User Scripts first!')
        _babase.screenmessage(
            'Delete Existing User Scripts first!',
            color=(1, 0, 0),
        )
        return
    if os.path.exists(pathtmp):
        shutil.rmtree(pathtmp)

    def _ignore_filter(src: str, names: Sequence[str]) -> Sequence[str]:
        del src, names  # Unused

        # We simply skip all __pycache__ directories. (the user would have
        # to blow them away anyway to make changes;
        # See https://github.com/efroemling/ballistica/wiki
        # /Knowledge-Nuggets#python-cache-files-gotcha
        return ('__pycache__',)

    print(f'COPYING "{env.python_directory_app}" -> "{pathtmp}".')
    if os.path.isdir(env.python_directory_app):
        shutil.copytree(
            env.python_directory_app, pathtmp, ignore=_ignore_filter
        )
    else:
        # App scripts served directly out of an archive (e.g. the
        # Android apk); extract them instead.
        _extract_archive_scripts(env.python_directory_app, pathtmp)

    print(f'MOVING "{pathtmp}" -> "{path}".')
    shutil.move(pathtmp, path)
    print(
        f"Created system scripts at :'{path}"
        f"'\nRestart {_babase.appname()} to use them."
        f' (use babase.quit() to exit the game)'
    )
    _babase.screenmessage('Created User System Scripts', color=(0, 1, 0))
    if app.classic is not None and app.classic.platform == 'android':
        print(
            'Note: the new files may not be visible via '
            'android-file-transfer until you restart your device.'
        )


def delete_user_system_scripts() -> None:
    """Clean out the scripts created by create_user_system_scripts()."""
    import shutil

    env = _babase.app.env

    if env.python_directory_user is None:
        raise RuntimeError('user python dir unset')

    path = (
        f'{env.python_directory_user}/sys/'
        f'{env.engine_version}_{env.engine_build_number}'
    )
    if os.path.exists(path):
        shutil.rmtree(path)
        print('User system scripts deleted.')
        _babase.screenmessage('Deleted User System Scripts', color=(0, 1, 0))
        _babase.screenmessage(
            f'Closing {_babase.appname()} to make changes.', color=(0, 1, 0)
        )
        _babase.apptimer(2.0, _babase.quit)
    else:
        print(f"User system scripts not found at '{path}'.")
        _babase.screenmessage('User Scripts Not Found', color=(1, 0, 0))

    # If the sys path is empty, kill it.
    dpath = env.python_directory_user + '/sys'
    if os.path.isdir(dpath) and not os.listdir(dpath):
        os.rmdir(dpath)
