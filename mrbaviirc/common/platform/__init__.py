""" Some platform helper functions. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2018-2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"

__all__ = ["path"]


import sys as _sys


# path
_platform = _sys.platform # pylint: disable=invalid-name

if _platform.startswith("linux"):
    from . import linuxpath as path
#elif _platform == "win32"
#    from . import winpath as path
#elif _platform == "darwin":
#    from . import macpath as path
else:
    # Should be raise an error or use a generic path module
    raise RuntimeError("Currently unsupported platform for mrbaviirc.common")
