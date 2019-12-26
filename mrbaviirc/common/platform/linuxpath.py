""" Linux-style paths. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2018-2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"

__all__ = [
    "get_user_data_dir", "get_sys_data_dirs", "get_user_config_dir",
    "get_sys_config_dirs", "get_cache_dir", "get_runtime_dir"
]


import os
import tempfile

# bring in common paths
from .commonpath import * # pylint: disable=wildcard-import
from . import commonpath as _common
__all__.extend(_common.__all__)
del _common


def _uniq(items):
    copy = []
    for i in items:
        if not i in copy:
            copy.append(i)
    return copy

def _normalize(base, vendor, name, version):
    """ Combine a base path bith the app name/vendor/version information. """
    parts = []
    if vendor is not None:
        parts.append(vendor)
    if name is not None:
        parts.append(name)
    if version is not None:
        parts.append(version)

    return os.path.join(base, *parts)

def _apply_prefix(prefix, dirs):
    """ Fix up the prefix in a list of directories. """
    if prefix[-1] == os.sep:
        prefix = prefix[:-1]

    if prefix in dirs or (prefix + os.sep) in dirs:
        return

    # If any of the paths in the dirs is part of the user home directory, we
    # assume the user may have set one of the XDG variables to be able to
    # override some application search path with there own, so insert the prefix
    # after any of those paths.
    insert_pos = 0
    what = os.path.expanduser("~")
    for (pos, entry) in enumerate(dirs):
        if entry == what or entry.startswith(what + os.path.sep):
            insert_pos = pos + 1

    dirs.insert(insert_pos, prefix)


def get_user_data_dir(name=None, version=None, vendor=None):
    """ Return the directory to read/write user data files. """
    base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    return _normalize(base, vendor, name, version)

def get_sys_data_dirs(name=None, version=None, vendor=None, prefix=None):
    """ Return the base system data directories for reading only. """
    bases = os.environ.get(
        "XDG_DATA_DIRS",
        os.pathsep.join(["/usr/local/share", "/usr/share"]),
    ).split(os.pathsep)

    if prefix:
        _apply_prefix(os.path.join(prefix, "share"), bases)

    return _uniq([_normalize(base, vendor, name, version) for base in bases])

def get_user_config_dir(name=None, version=None, vendor=None):
    """ Return the base directory to read/write user configuration files. """
    base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return _normalize(base, vendor, name, version)

def get_sys_config_dirs(name=None, version=None, vendor=None):
    """ Return the base system configuration directories. """
    bases = os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg").split(os.pathsep)

    if not "/etc" in bases:
        bases.append("/etc")

    return _uniq([_normalize(base, vendor, name, version) for base in bases])

def get_cache_dir(name=None, version=None, vendor=None):
    """ Return a base cache directory. """
    base = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    return _normalize(base, vendor, name, version)

def get_runtime_dir(name=None, version=None, vendor=None):
    """ Return base directory for runtime files. """
    runtimedir = os.environ.get("XDG_RUNTIME_DIR")

    if os.path.isdir(runtimedir):
        return _normalize(runtimedir, vendor, name, version)

    # log warning once logging module is done
    # perhaps should return None if no runtime dir and let application
    # handle it, or add an atexit handler to cleanup the function when done
    return tempfile.mkdtemp()
