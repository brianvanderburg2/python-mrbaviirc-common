""" Logging related classes and methods. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2019"
__license__ = "Apache License 2.0"


__all__ = ["SharedLogFile"]


import errno
import fcntl
import io
import threading


class SharedLogFile:
    """ A class for logging to a file. Actual writes are not performed
        until the flush method is called. """

    def __init__(self, filename):
        """ Initialize the logfile. """
        self._filename = filename
        self._entries = []
        self._lock = threading.RLock()

    def flush(self, block=True):
        """ Flush the contents. """

        with self._lock:
            handle = io.open(self._filename, "at", encoding="utf-8", newline=None)
            with handle:
                cmd = fcntl.LOCK_EX
                if not block:
                    cmd |= fcntl.LOCK_NB

                try:
                    fcntl.lockf(handle, cmd)
                except IOError as ex:
                    if ex.errno in (errno.EACCES, errno.EAGAIN):
                        return False # Unable to lock the file
                    raise # Some other execption

                try:
                    for _entry in self._entries:
                        handle.write(_entry)

                    self._entries = []
                    handle.flush()
                    return True
                finally:
                    fcntl.lockf(handle, fcntl.LOCK_UN)

        # If we got here, we didn't flush
        return False

    def write(self, text):
        """ Write text to the log buffer. """
        with self._lock:
            self._entries.append(text)
