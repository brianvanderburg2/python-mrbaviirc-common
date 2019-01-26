""" A mixin to provide service factory related methods. """

from __future__ import absolute_import

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2018 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


import threading


from ..util.imp import Exporter
from ..constants import SENTINEL


export = Exporter(globals())


@export
class ServiceContainerMixin(object):
    """ A mixing object providing configuration-related methods. """

    def __init__(self):
        """ Initialize the service container mixin. """
        self._service_factories = {}
        self._service_singletons = {}
        self._service_instances = {}
        self._service_lock = threading.RLock()
    
    def register_factory(self, name, factory):
        """ Registry a given factory. This should occur in the main thread. """
        self._service_factories[name] = factory

    def unregister_factory(self, name):
        """ Remove a registered factory. This should occur in the main thread. """
        self._service_factories.pop(name, None)

    def call_factory(self, name, *args, **kwargs):
        """ Call a factory. """
        if not name in self._service_factories:
            raise KeyError("No such service factory{0}".format(name))

        with self._service_lock:
            factory = self._service_factories[name]
            return factory(*args, **kwargs)

    def register_singleton(self, name, factory):
        """ Registry a singleton. This should occur in the main thread. """
        self._service_singletons[name] = factory
    
    def unregister_singleton(self, name):
        """ Remove a registered singleton. This should occur in the main thread. """
        self._service_singletons.pop(name, None)
        self.clear_singleton(name)

    def get_singleton(self, name):
        """ Get the service instance. """
        if not name in self._service_singletons:
            raise KeyError("No such service singleton {0}".format(name))

        with self._service_lock:
            factory = self._service_singletons[name]

            if name in self._service_instances:
                return self._service_instances[name]

            # Object not set yet:
            obj = self._service_instances[name] = factory()
            return obj

    def clear_singleton(self, name):
        """ Remove the current service singleton instance if any. """
        with self._service_lock:
            self._service_instances.pop(name, None)
    
    def clear_singletons(self):
        """ Remove all service singleton instances. """
        with self._service_lock:
            self._service_instances.clear()

    def set_service_singleton(self, name, instance):
        """ Manually set the instance. """
        with self._service_lock:
            self._service_instances[name] = instance

