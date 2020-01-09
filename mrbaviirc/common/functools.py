""" Provide some function and method utilities """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2016-2017 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"

__all__ = ["lazy_property"]


import threading


class lazy_property: # pylint: disable=invalid-name
    """ Create a property that is evaulated once and remembered.

    This is done in a thread safe manor so that only one thread will set the
    property intially.  Once the property is set on an object, it is accessed
    directly by any future calls unless it is deleted, then this decorator
    will be called again.
    """

    def __init__(self, method):
        """ Create the lazy attribute. """
        self._lock = threading.Lock()
        self._method = method
        self.__name__ = method.__name__
        self.__doc__ = method.__doc__
        self.__module__ = method.__module__

    def __get__(self, obj, owner):
        """ Get our lazy attribute in a thread-safe way. """
        if obj is None: # accessed via classname.propname
            return self

        name = self._method.__name__
        obj_dict = obj.__dict__

        with self._lock:
            # check again in case another thread acquired lock first and set it
            if not name in obj_dict:
                obj_dict[name] = self._method(obj)

        # Value should be set at this point.
        return obj.__dict__[name]
