""" Text utilities. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2018 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"

__all__ = ["dedent", "striplines", "makesingle"]


import textwrap


def dedent(text):
    """ Removing unneeded whitespace, newlines. """
    return textwrap.dedent(text).strip()

def striplines(text):
    """ Remove all leading/trailing whitespaces from lines and blank lines. """
    return "\n".join(
        line.strip() for line in text.splitlines() if len(line.strip())
    )

def makesingle(text):
    """ Make multiple lines into a single line joined by a space. """
    return " ".join(
        line.strip() for line in text.splitlines() if len(line.strip())
    )
