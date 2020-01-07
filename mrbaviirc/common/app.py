""" Classes for application objects. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2018-2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"

__all__ = ["BaseApp", "App"]


from typing import Optional
import threading
from argparse import ArgumentParser

#from .constants import SENTINEL
from .config import Config
from .hooks import Hooks
from .registry import ObjectRegistry
from .path import AppPaths


class BaseApp:
    """ The base application oject. """

    # Initialization

    def __init__(self):
        """
            Initialize.  Note the construction shouldn't perform any active
            operations, it's really just a place to specify configurations.
        """

        # Create basic components
        self._lock = threading.RLock()
        self._local = threading.local()
        self._main_thread = threading.current_thread()

        # Some common components
        self.config = Config()
        self.hooks = Hooks()
        self.registry = ObjectRegistry()

        # Properties we keep access to
        self._paths = None

    # Properties

    @property
    def lock(self):
        """ Return the application thread lock.

        Returns
        -------
        threading.RLock
            The application lock object.
        """
        return self._lock

    @property
    def main_thread(self):
        """ Return the main thread.

        Returns
        -------
        threading.Thread
            The thread that was active when the application oject was created
        """
        return self._main_thread

    @property
    def appname(self) -> str:
        """ Return the application name as used in paths.

        Returns
        -------
        str
            The application name as would be used in paths.
        """
        raise NotImplementedError

    @property
    def appversion(self) -> Optional[str]:
        """ Return the applicatoin version as used in paths.

        Returns
        -------
        str
            The application version string as used in paths.
        None
            If no version string is to be used.
        """
        return None

    @property
    def appvendor(self) -> Optional[str]:
        """ Return the application vendor name.

        Returns
        -------
        str
            The application vendor string as used in paths.
        None
            If no vendor string is to be used.
        """
        return None

    @property
    def displayname(self) -> str:
        """ Return the application display name.

        Returns
        -------
        str
            The application display name. Defaults to the appname property.
        """
        return self.appname

    @property
    def description(self) -> str:
        """ Return the application description.

        Returns
        -------
        str
            The application description. Defaults the the displayname property.
        """
        return self.displayname

    @property
    def paths(self) -> AppPaths:
        """ Return the application path object.

        Returns
        -------
        AppPaths
            The application path object
        """
        if self._paths is None:
            with self._lock:
                # check if another thread set while we were waiting on lock
                if self._paths is None:
                    self._paths = self.create_paths()
        return self._paths

    def create_paths(self) -> AppPaths:
        """ Create the application path object.

        Derived classes can override this to return a custom AppPath

        Returns
        -------
        AppPaths
            An instance or derived class of AppPaths
        """
        return AppPaths(self.appname, self.appversion, self.appvendor)

    # Execution related methods. """

    def startup(self):
        """ Perform startup here. """

    def shutdown(self):
        """ Perform shutdown here. """


class App(BaseApp):
    """ Represent a basic app with argument parsing, etc. """

    def __init__(self):
        """ Initialize the app object. """

        BaseApp.__init__(self)

        self.args = None # result of command line argument parsing

    # Command line argument related

    def create_arg_parser(self):
        """ Derived class can override this if needed to return a custom
            argument parser.
        """
        return ArgumentParser(description=self.description)

    def parse_args(self, parser):
        # pylint: disable=no-self-use
        """ Parse the arguments of the command line parser.

        A derived class can call this method then handle/validate the results.
        """
        return parser.parse_args()

    # Execution related

    def execute(self):
        """ Execute an application by calling the startup, main, and shutdown
            methods
        """
        self.startup()
        self.main()
        self.shutdown()

    def startup(self):
        """ Handle applicatoin startup related actions. """
        BaseApp.startup(self)

        parser = self.create_arg_parser()
        if parser:
            self.args = self.parse_args(parser)

    def main(self):
        """ Execute the main body of the application. """
        raise NotImplementedError()
