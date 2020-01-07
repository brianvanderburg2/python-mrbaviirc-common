""" Registry related classes.

This module provides functions and classes which store registries of objects.
It is not related to the Windows registry.
"""

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2018-2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"

__all__ = ["ObjectRegistry"]


import threading
from typing import Optional, Any


class ObjectRegistry:
    """ Represent a registry of objects grouped by registry names. """

    def __init__(self):
        """ Initialize the registry. """
        self._lock = threading.RLock()
        self._registry = {}

    def register(self, registry: str, value: Any, name: Optional[str] = None):
        """ Register an object with the registry.

        Parameters
        ----------
        registry : str
            The named registry to identify the object as.
        value : Any
            The object to store in the registry
        name : Optional[str], default=None
            The name to identify the object as.  Multiple objects may be given
            the same name.  This is just used for the get method.
        """
        with self._lock:
            registry_list = self._registry.setdefault(registry, [])
            registry_list.append((name, value))

    def get(self, registry: str, name: Optional[str] = None) -> Any:
        """ Returns a sequence of the registered values.

        Parameters
        ----------
        registry : str
            The named registry the object was registered with
        name : Optional[str], default=None
            The name the object was registered as.  If specified, only objects
            with the same name willl be returned. If not specified, all objects
            within the named registry will be returned.

        Returns
        -------
        A tuple of the found registered items.
        """
        with self._lock:
            results = tuple(
                value
                for (stored_name, value) in self._registry.get(registry, [])
                if name is None or name == stored_name
            )
            return results

    def first(self, registry: str, name: Optional[str] = None) -> Optional[Any]:
        """ Returns the first matching object.

        Parameters
        ----------
        See the `get` method

        Returns
        -------
        Any
            The first matching value
        None
            If the value was not found
        """
        results = self.get(registry, name)
        if results:
            return results[0]

        return None

    def last(self, registry: str, name: Optional[str] = None) -> Optional[Any]:
        """ Returns the last matching object.

        Parameters
        ----------
        See the `get` method

        Returns
        -------
        Any
            The last matching value
        None
            If the value was not found
        """

        results = self.get(registry, name)
        if results:
            return results[-1]

        return None
