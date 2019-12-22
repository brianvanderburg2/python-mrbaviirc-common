""" Provide an simple callback hooks system """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2018-2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"

__all__ = ["Hooks", "HookEntry"]


import threading
from typing import Callable, Any
import weakref


class HookEntry:
    """ Represent a registered hook entry. """

    def __init__(self, hooks, hook, callback):
        self._hooks = weakref.ref(hooks)
        self._hook = hook

        try:
            obj = callback.__self__
            func = callback.__func__

            self._weak = True
            self._obj = weakref.ref(obj, self._cleanup)
            self._func = weakref.ref(func, self._cleanup)
            self._type = type(callback)
        except AttributeError:
            self._weak = False
            self._obj = None
            self._func = callback
            self._type = None

        self._suspended = False

    def __call__(self, *args, **kwargs):
        if not self._suspended:
            # call strong reference callbacks directly
            if not self._weak:
                return (True, self._func(*args, **kwargs))

            # weak call, only called if reference is still good
            obj = self._obj()
            func = self._func()
            if obj is not  None and func is not None:
                meth = self._type(func, obj)
                return (True, meth(*args, **kwargs))

        return (False, None)

    def suspend(self):
        """ Suspend this hook callback from being called. """
        self._suspended = True

    def resume(self):
        """ Restore this hook callback to being called. """
        self._suspended = False

    def unregister(self):
        """ Unregister this hook. """
        hooks = self._hooks()
        if hooks is not None:
            hooks.unregister(self)

    def _cleanup(self, ref): # pylint: disable=unused-argument
        """ Unregister the hook when ref is zero. """
        self.unregister()

class Hooks:
    """ This class provides methods to register and fire hook callbacks.

    This class attempts to be thread safe but makes no guarantees.  Ideally
    hooks should only be called from the same thread they are registered on.
    It is also possibly to queue hook calls for later, in which case the queue
    method could be called in one thread then the flush method in a different
    thread.
    """

    def __init__(self):
        """ Create the events data. """
        self._lock = threading.RLock()
        self._hooks = {}
        self._queue = []
        self._called = []
        self._processing = False

    def register(self, hook: str, callback: Callable[...,Any]) -> HookEntry:
        """ Add a event callback for a given hook.

        Parameters
        ----------
        hook : str
            The name of the hook to register into.
        callback : Callable[...,Any]
            Specify the callback to be called. They will be called with the
            same arguments supplied to fire or queue the hook.  If an instance
            or class method is passed as the callback, it will be stored
            internnally as a weak reference and automatically unregister when
            that object no longer has any references to it.

        Returns
        -------
        HookEntry
            An object that identifies this entry in the hooks.
        """

        entry = HookEntry(self, hook, callback)
        with self._lock:
            queue = self._hooks.setdefault(hook, [])
            queue.append(entry)

        return entry

    def unregister(self, entry: HookEntry):
        """ Remove a hook a previously registered hook callback.

        Parameters
        ----------
        entry : HookEntry
            The entry of a previously registered hook.

        """
        hook = entry._hook # pylint: disable=protected-access
        with self._lock:
            queue = self._hooks.get(hook, None)
            if queue is not None:
                try:
                    queue.remove(entry)
                except ValueError:
                    pass

    def call(self, hook: str, *args, **kwargs):
        """ Call all registered callbacks for a given hook.

        Hook callbacks may also call more hooks, but if they do, those are not
        called until the current hook finishes.

        Parameters
        ----------
        hook : str
            The name of the hook to call
        *args
            Positional parameters to pass to the callbacks
        **kwargs
            Keyword parameters to pass to the callbacks
        """

        with self._lock:
            self._called.append((hook, args, kwargs))
            if not self._processing:
                try:
                    self._processing = True
                    while self._called:
                        (hook, args, kwargs) = self._called.pop(0)
                        queue = self._hooks.get(hook, None)
                        if queue is not None:
                            for entry in queue:
                                entry(*args, **kwargs)
                finally:
                    self._processing = False

    def queue(self, hook, *args, **kwargs):
        """ Queue a hook call for later calling.

        Parameters
        ----------
        hook : str
            The name of the hook to call
        *args
            Positional parameters to pass to the callbacks
        **kwargs
            Keyword parameters to pass to the callbacks
        """
        with self._lock:
            self._queue.append((hook, args, kwargs))

    def flush(self):
        """ Call all previously queued hook calls. """
        with self._lock:
            # lock is a reentreant lock so this is fine
            (hook, args, kwargs) = self._queue.pop(0)
            self.call(hook, *args, **kwargs)
