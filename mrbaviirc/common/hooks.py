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
        except AttributeError:
            self._weak = False
            self._obj = None
            self._func = callback
            self._type = None
        else:
            self._weak = True
            self._obj = weakref.ref(obj, self._cleanup)
            self._func = weakref.ref(func, self._cleanup)
            self._type = type(callback)

        self._enabled = True

    @property
    def callback(self) -> Callable[..., Any]:
        """ Return the callback the hook entry represents.

        Note that two consequitive calls may produce different values. If
        a reference dies or such, then the second call may be None even if the
        first call was the callback.  The result of this should be stored in
        a variable then operations done on that reference.

        This is wrong:

            if entry.callback is not None:
                entry.callback() # second call to entry.callback may be None

        This is right:

            callback = entry.callback
            if callback is not None:
                callback()
            callback = None # make sure to release the reference once done

        Returns
        -------
        Callable[..., Any]
            The callback the hook reprsents
        None
            This is returned if the hook entry is disabled or a weak reference
            to an instance method has expired.
        """

        if self._enabled:
            if not self._weak:
                return self._func

            obj = self._obj()
            func = self._func()
            if obj is not None and func is not None:
                return self._type(func, obj)

        return None

    @property
    def enabled(self):
        """ Enable or disable the hook """
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = bool(value)

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
        """ Create the hooks data. """
        self._lock = threading.RLock()
        self._hooks = {}
        self._queue = []

    def register(self, hook: str, callback: Callable[..., Any]) -> HookEntry:
        """ Add a callback for a given hook.

        Parameters
        ----------
        hook : str
            The name of the hook to register into.
        callback : Callable[...,Any]
            Specify the callback to be called. They will be called with the
            same arguments supplied to fire or queue the hook.  If an instance
            or class method is passed as the callback, it will be stored
            internally as a weak reference and automatically unregister when
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

        Note that it is possible for two different threads to call the same
        hook at the same time.

        Parameters
        ----------
        hook : str
            The name of the hook to call
        *args
            Positional parameters to pass to the callbacks
        **kwargs
            Keyword parameters to pass to the callbacks
        """

        # Release the lock before iterating so multiple threads can call hooks
        # at the same time. Clone the list so another thread's changes to the
        # hooks won't mess up us iterating over the hook list.
        with self._lock:
            queue = tuple(self._hooks.get(hook, []))

        for entry in queue:
            callback = entry.callback
            if callback is not None:
                callback(*args, **kwargs)

    def get(self, hook: str):
        """ Return a generator which will yield the callbacks.

        This method replaces the previous accumulate method. Note that the
        generator returns hard references to the callback. This usually isn't
        a problem if the value is only stored to a local variable in a function
        while iterating over it as the variable reference will be released
        by the end of the function. Otherwise, the variable stored to should be
        set to None after the iteration is complete

        To understand the issue:

            obj = Obj()
            h = Hooks()

            h.register("hook", obj.fn)

            for i in h.get("hook"):
                pass

            obj = None
            # local variable i still references obj.fn, obj not released

            i = None
            # now obj is  released


        Parameters
        ----------
        hook : str
            The name of the hook to iterate over

        Yields
        ------
        Callable[...,Any]
            Each registered hook callback is returned as long as it is still
            enabled and live if it is a weak reference.
        """
        # clone and release just like in call
        with self._lock:
            queue = tuple(self._hooks.get(hook, []))

        for entry in queue:
            callback = entry.callback
            if callback is not None:
                yield callback

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
            while self._queue:
                (hook, args, kwargs) = self._queue.pop(0)
                self.call(hook, *args, **kwargs)


class Signal(Hooks):
    """ This class represents a single hook to be used as a signal object.

    This class provides all the same functions as the Hooks class, but does
    not support named hook registrations.  In this way, it is useful as a
    simple signal mechanism.  See the parent class for more detailed
    documentation.  The only difference is the varoius methods do not take
    a named hook, but instead just a single name internally
    """

    def register(self, callback: Callable[..., Any]) -> HookEntry:
        # pylint: disable=arguments-differ
        """ See parent class """
        return Hooks.register(self, "hook", callback)

    def call(self, *args, **kwargs):
        # pylint: disable=arguments-differ
        """ See parent class """
        return Hooks.call(self, "hook", *args, **kwargs)

    def get(self):
        # pylint: disable=arguments-differ
        """ See parent class """
        return Hooks.get(self, "hook")

    def queue(self, *args, **kwargs):
        # pylint: disable=arguments-differ
        """ See parent class. """
        return Hooks.queue("hook", *args, **kwargs)
