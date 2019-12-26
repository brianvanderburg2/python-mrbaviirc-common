""" Some common path functions and classes applications. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2018-2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"

__all__ = ["AppPathsBase", "AppPaths"]


import os
import tempfile
from typing import Sequence, Optional

from . import platform


class AppPathsBase:
    """ An application path base object. """
    def __init__(self):
        """ Initialize the applications paths object. """

        self._temp_dir = None

    # Many of the paths are just implemented as properties
    @property
    def user_data_dir(self) -> str:
        """ Return the read/write user data directory.

        Returns
        -------
        str
            The path where user data files should be read and written.
        """
        raise NotImplementedError()

    @property
    def sys_data_dirs(self) -> Sequence[str]:
        """ Return the list of data directories to read data files from.

        Returns
        -------
        Sequence[str]
            A list of directories for reading data files.
        """
        raise NotImplementedError()

    @property
    def user_config_dir(self) -> str:
        """ Return the read/write user configuration directory.

        Returns
        -------
        str
            The path where user configuration files should be read and written.
        """
        raise NotImplementedError()

    @property
    def sys_config_dirs(self) -> Sequence[str]:
        """ Return the list of directories to read configuration files from.

        Returns
        -------
        Sequence[str]
            A list of directories for reading configuration files.
        """
        raise NotImplementedError()

    @property
    def cache_dir(self) -> str:
        """ Return a directory for storing cached files.

        Returns
        -------
        str
            Cache directory
        """
        return os.path.join(self.user_data_dir, "cache")

    @property
    def runtime_dir(self) -> str:
        """ Return the runtime directory.

        Returns
        -------
        str
            Directory where runtime files such as sockets should be created
        """
        return os.path.join(self.temp_dir, "run")

    @property
    def temp_dir(self) -> str:
        """ Returns a temp directory for storing files.  Multiple calls will
        access the same directory.

        Returns
        -------
        str
            A temp directory for storing files.
        """
        if self._temp_dir is None or not os.path.isdir(self._temp_dir):
            self._temp_dir = tempfile.mkdtemp()

        return self._temp_dir


class AppPaths(AppPathsBase):
    """ An applications paths object.

    This application paths object uses the default platform path to get path
    names.  It contains the appname, version, and vendor information.
    """

    def __init__(
            self,
            appname: str,
            version: Optional[str] = None,
            vendor: Optional[str] = None,
            prefix: Optional[str] = None
    ):
        """ Initialize the paths object.

        Parameters
        ----------
        appname : str
            The application name as would be used for a directory path.
        version : Optional[str]
            The application version information as would be used for a path
        vendor : Optional[str]
            The application vendor as would be used for a path.
        prefix : Optional[str]
            The install prefix.  This may not be used on some platforms or
            for some paths/.

        """
        AppPathsBase.__init__(self)
        self._appname = appname
        self._version = version
        self._vendor = vendor
        self._prefix = prefix
        self._paths = platform.path

    @property
    def user_data_dir(self):
        return self._paths.get_user_data_dir(
            self._appname, self._version, self._vendor
        )

    @property
    def sys_data_dirs(self):
        return self._paths.get_sys_data_dirs(
            self._appname, self._version, self._vendor, self._prefix
        )

    @property
    def user_config_dir(self):
        return self._paths.get_user_config_dir(
            self._appname, self._version, self._vendor
        )

    @property
    def sys_config_dirs(self):
        return self._paths.get_sys_config_dirs(
            self._appname, self._version, self._vendor
        )

    @property
    def cache_dir(self):
        return self._paths.get_cache_dir(
            self._appname, self._version, self._vendor
        )

    @property
    def runtime_dir(self):
        return self._paths.get_runtime_dir(
            self._appname, self._version, self._vendor
        )
