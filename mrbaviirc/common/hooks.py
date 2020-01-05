""" Provide an simple callback hooks system """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2018-2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"

__all__ = ["CallbackEntry", "Hooks", "Signal"]


import threading
from typing import Optional, Callable, Any, Generator
import weakref


class CallbackEntry:
    """ Represent a registered callback entry. """
    def __init__(self, container, callback, data=None):
        self._container = weakref.ref(container)
        self._data = data

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
        container = self._container()
        if container is not None:
            container.unregister(self)

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

    def register(self, hook: str, callback: Callable[..., Any]) -> CallbackEntry:
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
        CallbackEntry
            An object that identifies this entry in the hooks.
        """

        entry = CallbackEntry(self, callback, hook)
        with self._lock:
            queue = self._hooks.setdefault(hook, [])
            queue.append(entry)

        return entry

    def unregister(self, entry: CallbackEntry):
        """ Remove a hook a previously registered hook callback.

        Parameters
        ----------
        entry : CallbackEntry
            The entry of a previously registered hook.

        """
        hook = entry._data # pylint: disable=protected-access
        with self._lock:
            queue = self._hooks.get(hook, None)
            if queue is not None:
                try:
                    queue.remove(entry)
                except ValueError:
                    pass

    def process(self, hook: str, *args, **kwargs) -> Generator[Any, None, None]:
        """ Process all registered callbacks for a hook, yielding the results.

        Note that it is possible for two different threads to process the same
        hook at the same time.  This method is intended to replace the original
        accumulate method.  Instead of providing a callback as follows:

            def sum_callback(value):
                global sum_value
                sum_value += value

            hook.accumulate("myhook", sum_callback, arg1, arg2)

        The code can be more cleanly written as:

            sum_value = 0
            for cur_value in hook.process("myhook", arg1, arg2):
                sum_value += cur_value

        This also allows to abort processing the hooks by simply not iterating
        over any more values.

        Parameters
        ----------
        hook : str
            The name of the hook to call
        *args
            Positional parameters to pass to the callbacks
        **kwargs
            Keyword parameters to pass to the callbacks

        Yields
        ------
        The results of the callbacks called.
        """

        # Release the lock before iterating so multiple threads can call hooks
        # at the same time. Clone the list so another thread's changes to the
        # hooks won't mess up us iterating over the hook list.
        with self._lock:
            queue = tuple(self._hooks.get(hook, []))

        for entry in queue:
            callback = entry.callback
            if callback is not None:
                result = callback(*args, **kwargs)
                callback = None # release the reference as soon as possible
                yield result

    def call(self, hook: str, *args, **kwargs):
        """ Call all registered callbacks for a given hook.

        Parameters
        ----------
        See the `process` method
        """

        # We just process all callbacks and discard the results
        # Is there a more pythonic way to do this?
        for result in self.process(hook, *args, **kwargs): # pylint: disable=unused-variable
            result = None

    def get(self, hook: str):
        """ Return a generator which will yield the callbacks.

        Note that the generator returns hard references to the callback. This
        usually isn't a problem if the value is only stored to a local variable
        in a function while iterating over it as the variable reference will be
        released by the end of the function. Otherwise, the variable stored to
        should be set to None after the iteration is complete.  This method
        can be used to call each callback with different parameters.  If all
        callbacks of a hook will be called with the same parameters, just use
        the `call` method if results are not needed or the `process` method
        if the results are needed.

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
        # clone and release lock just like in call
        with self._lock:
            queue = tuple(self._hooks.get(hook, []))

        for entry in queue:
            callback = entry.callback
            if callback is not None:
                yield callback


    def first(self, hook: str) -> Optional[Callable[..., Any]]:
        """ Return the first calback for the given hook.

        Note, this returns a hard reference so the result should be set to
        None as soon as convenient.

        Parameters
        ----------
        hook : str
            The name of the hook.

        Returns
        -------
        Callable[..., Any]
            The first active regisistered callback for the hook.
        None
            If no registered callback for the hook is active.
        """

        for callback in self.get(hook):
            return callback # Return the first item

        return None

    def last(self, hook: str) -> Optional[Callable[..., Any]]:
        """ Return the last callback for the given hook.

        Note, this returns a hard reference so the result should be set to
        None as soon as convenient.

        Parameters
        ----------
        hook : str
            The name of the hook.

        Returns
        -------
        Callable[..., Any]
            The last active regisistered callback for the hook.
        None
            If no registered callback for the hook is active.
        """
        result = None
        for callback in self.get(hook):
            result = callback

        return result

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


class Signal:
    """ This class represents a single hook to be used as a signal object.

    This class provides most all the same functions as the Hooks class, but
    does not use named hook registrations. In this way, it is useful as a
    simple signal mechanism.  See the Hooks class for the method details.
    The only difference is the methods do not take a "hook" parameter.
    """

    def __init__(self):
        """ Create the signal data. """
        self._lock = threading.RLock()
        self._entries = []
        self._queue = []

    def register(self, callback: Callable[..., Any]) -> CallbackEntry:
        """ See `Hooks.register` """

        entry = CallbackEntry(self, callback)
        with self._lock:
            self._entries.append(entry)

        return entry

    def unregister(self, entry: CallbackEntry):
        """ See `Hooks.unregister` """

        with self._lock:
            try:
                self._entries.remove(entry)
            except ValueError:
                pass

    def process(self, *args, **kwargs):
        """ See `Hooks.process` """

        # clone and release lock to allow multiple threads to call at the same time
        with self._lock:
            entries = tuple(self._entries)

        for entry in entries:
            callback = entry.callback
            if callback is not None:
                result = callback(*args, **kwargs)
                callback = None # release reference asap
                yield result

    def call(self, *args, **kwargs):
        """ See `Hooks.call` """
        for result in self.process(*args, **kwargs): # pylint: disable=unused-variable
            result = None

    def get(self):
        """ See `Hooks.get` """
        with self._lock:
            entries = tuple(self._entries)

        for entry in entries:
            callback = entry.callback
            if callback is not None:
                yield callback

    def first(self):
        """ See `Hooks.first` """
        for callback in self.get():
            return callback # first item

        return None

    def last(self):
        """ See `Hooks.last` """
        result = None
        for callback in self.get():
            result = callback

        return result

    def queue(self, *args, **kwargs):
        """ See `Hooks.queue` """
        with self._lock:
            self._queue.append((args, kwargs))

    def flush(self):
        """ See `Hooks.flush` """
        with self._lock:
            while self._queue:
                (args, kwargs) = self._queue.pop(0)
                self.call(*args, **kwargs)
