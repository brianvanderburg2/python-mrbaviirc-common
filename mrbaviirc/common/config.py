""" This module provides configuration-related classes. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2018-2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"

__all__ = ["Config"]


import threading
from typing import Any, Union, Sequence, Dict

from .constants import SENTINEL


class Config:
    """ A container for configuration information.

    This class is used by the app module as its configuration container.
    It may also be used as a standalone class.  While the configuration
    container does not attempt to limit the types of values stored or retrieved,
    it should be limited to simple data such as strings, integers, floats,
    lists, tuples, dicts.  When getting a value, these types are parsed
    recursively and any callable will be substituted with the return value of
    the call.
    """

    def __init__(self):
        """ Initialize the configuration. """
        self._lock = threading.RLock()
        self._sections = {}

    def set(
            self,
            name: str,
            value: Any,
            section: str = "config"
    ):
        """ Set a configuration value.

        Parameters
        ----------
        name : str
            The configuration value's name
        value : Any
            The configuration value to store.
        section : str, default="config"
            The section name to store the configuration value in.
        """
        with self._lock:
            section_container = self._sections.setdefault(section, {})
            section_container[name] = value

    def update(
            self,
            config: Dict[str, Any],
            section: str = "config"
    ):
        """ Update a configuratoin section.

        This will merge all values from the dictionary specified in `config`
        into the configuration section.

        Parameters
        ----------
        config : Dict[str, Any]
            A mapping of key name to configuration values to merge into the
            configuration.
        section : str, default="config"
            The section of the configuration to merge into
        """
        with self._lock:
            section_container = self._sections.setdefault(section, {})
            section_container.update(config)

    def get(
            self,
            name: str,
            default: Any = None,
            section: str = "config"
    ) -> Any:
        """ Get a configuratoin value.

        Parameters
        ----------
        name : str
            The configuration value's name
        default : Any, default=none
            The default value if the configuration value is not found
        section : str, default="config"
            The section name to find the configuration value in

        Returns
        -------
        Any
            If the configuration item is found it is returned.  Otherwise
            the default value is returned if specified, otherwise None is
            returned.
        """

        with self._lock:
            section_container = self._sections.get(section)
            if section_container is None:
                return default

            value = section_container.get(name, SENTINEL)
            if value is SENTINEL:
                return default

            return self._eval(value)

    def extract(
            self,
            prefix: str,
            sections: Union[str, Sequence] = "config"
    ) -> Dict[str, Any]:
        """ Extract multiple sections and reduce their names.

        For each section, find any configuration that begins with the prefix
        supplied and return a dictionary containing the results with the
        keys of the results being the orignal key's name with the leading
        prefix removed.

        IE. If a confguration is named "user.name" and extract is called with
        a name value of "user.", then the returned dictionary's key will be
        "name" instead of "user.name".

        Parameters
        ----------
        prefix : str
            The prefix for the key names to match
        section : Union(str, Sequence)
            The section or sections to look in. If section is a tuple or list
            then each section is processed in order.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing the extracted configuration keys.
        """

        results = {}
        prefix_len = len(prefix)

        if not isinstance(sections, (tuple, list)):
            sections = [sections]

        with self._lock:
            for section in sections:
                section_container = self._sections.get(section)
                if section_container is None:
                    continue

                section_results = {
                    i[prefix_len:] : self._eval(section_container[i])
                    for i in section_container
                    if i.startswith(prefix)
                }

                results.update(section_results)

        return results

    def _eval(self, value):
        """ Evaluate any config functions. """
        if isinstance(value, list):
            return [self._eval(i) for i in value]

        if isinstance(value, tuple):
            return tuple([self._eval(i) for i in value])

        if isinstance(value, dict):
            return {i : self._eval(value[i]) for i in value}

        if callable(value):
            return self._eval(value())

        return value
