""" Tests for mrbaviirc.common.config """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"


from mrbaviirc.common.config import Config


def _cb():
    return "value"


def _cb2():
    return ["1", "2", _cb]


def _make_config():
    """ Make the config for use with the tests. """
    c = Config()

    c.set("key1", "value1")
    c.set("key2", "value2")

    c.update({"key7": "config-value7"})

    c.update(
        {"key3": "value3", "key4": "value4", "key7": "extra-value7"},
        "extra"
    )

    c.set("nestkey1", ["one", "two", ("three", _cb, {"key": 5, "key2": _cb2})])

    return c


def test_setget():
    """ Test basic set and get operations. """

    c = _make_config()

    assert c.get("key1") == "value1"
    assert c.get("key2") == "value2"
    assert c.get("key3") == None
    assert c.get("key4") == None

    assert c.get("key3", None, "extra") == "value3"
    assert c.get("key4", None, "extra") == "value4"


def test_extract():
    """ Test extracting a range of key values. """

    c = _make_config()

    assert c.extract("key") == {
        "1": "value1", "2": "value2", "7": "config-value7"
    }
    assert c.extract("key", "extra") == {
        "3": "value3", "4": "value4", "7": "extra-value7"
    }
    assert c.extract("key", ["config", "extra"]) == {
        "1": "value1", "2": "value2", "3": "value3", "4": "value4",
        "7": "extra-value7"
    }
    assert c.extract("key", ["extra", "config"]) == {
        "1": "value1", "2": "value2", "3": "value3", "4": "value4",
        "7": "config-value7"
    }


def test_nested():
    """ Test nested values with eval on callables. """

    c = _make_config()
    assert c.get("nestkey1") == [
        "one", "two", ("three", "value", {"key": 5, "key2": ["1", "2", "value"]})
    ]
