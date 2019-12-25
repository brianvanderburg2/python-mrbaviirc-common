""" Time utilities. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2018-2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"

__all__ = ["StopWatch"]


try:
    # pylint: disable=invalid-name
    from time import monotonic
    timenow = monotonic
    timedelta = lambda a, b: a - b
    timesecs = lambda a: a
except ImportError:
    # pylint: disable=invalid-name
    from datetime import datetime
    timenow = datetime.now
    timedelta = lambda a, b: a - b
    timesecs = lambda a: a.total_seconds()


class StopWatch:
    """ A stop-able timer class. """

    def __init__(self, start: bool = False, elapsed: float = 0.0):
        """ Initialize the stopwatch.

        Parameters
        ----------
        start : bool, default=False
            Whether to start the stopwatch after creating it
        elapsed : float, default=0.0
            The initial elapsed value of the stopwatch
        """
        self._elapsed = elapsed
        self._timer = None

        if start:
            self.start()

    def start(self):
        """ Start the stopwatch. """

        if self._timer is None:
            self._timer = timenow()

    def stop(self) -> float:
        """ Stop the stopwatch.

        Returns
        -------
        float
            The current elapsed time.

        """
        if self._timer is not None:
            now = timenow()
            delta = timedelta(now, self._timer)
            self._timer = None

            self._elapsed += timesecs(delta)

        return self._elapsed

    def reset(self) -> float:
        """ Reset the timer.

        Returns
        -------
        float
            The current elapsed time

        """
        current = self.stop()
        self._elapsed = 0.0
        self._timer = None

        return current

    @property
    def time(self) -> float:
        """ Return the elapsed stopwatch time.

        Returns
        -------
        float
            The current elapsed time
        """
        if self._timer:
            now = timenow()
            delta = timedelta(now, self._timer)

            return self._elapsed + timesecs(delta)

        return self._elapsed

    def __enter__(self):
        """ Use as context manager starting on enter and stopping on exit """
        self.start()
        return self

    def __exit__(self, *args):
        """ Stop stopwatch on exit. """
        self.stop()

    def __int__(self) -> int:
        """ Cast to integer.

        Returns
        -------
        int
            The current elapsed time as an integer
        """
        return int(self.time)

    def __float__(self) -> float:
        """ Cast to float value.

        Returns
        -------
        float
            The current elapsed time as a float
        """
        return float(self.time)

    def __bool__(self) -> bool:
        """ Return if the stopwatch is running.

        Returns
        -------
        bool
            True if the stopwatch is running, otherwise False
        """
        return self._timer is not None

    __nonzero__ = __bool__

    def __str__(self) -> str:
        """ Return the value as a string.

        Return
        ------
        str
            The current elapsed time as a string
        """
        return str(self.time)

    def __repr__(self):
        return "{0}.{1}({2}, {3})".format(
            self.__class__.__module__,
            self.__class__.__name__,
            bool(self),
            float(self)
        )
