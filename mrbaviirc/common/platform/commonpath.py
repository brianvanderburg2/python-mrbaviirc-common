""" Common path functions. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2018-2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"

__all__ = ["get_package_data_dir", "get_temp_dir"]


import os
import tempfile


def get_package_data_dir(package, first=False):
    """ Get the package data directory.  For now this assumes a "data"
        subdirectory beside the package. """

    paths = getattr(package, "__path__")
    dirs = tuple(os.path.abspath(os.path.join(part, "data")) for part in paths)

    return dirs[0] if first else dirs


def get_temp_dir():
    """ Return a new temporary directory. """
    return tempfile.mkdtemp()
