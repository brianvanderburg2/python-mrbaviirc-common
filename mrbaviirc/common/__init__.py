""" Common classes and methods library.

This package is intended to provide reusable code classes and libraries that
may be common to use by other projects.
"""


__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2018-2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"
__version__ = "0.0.0"


import sys as _sys


# check we are using at least version 3.5
if _sys.version_info[0:2] < (3, 5):
    raise RuntimeError("{} needs at least python version 3.5".format(__package__))

# import our fixups
from . import _fixups # pylint: disable=wrong-import-position
del _fixups
