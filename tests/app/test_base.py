""" Tests for mrbaviirc.app.base """

from __future__ import absolute_import

__author__      = "Brian AllenVanderburg II"
__copyright__   = "Copyright 2018"
__license__     = "Apache License 2.0"

from mrbaviirc.common.app import base
from mrbaviirc.common.util import functools

class DerivedAppHelper(base.BaseAppHelper):

    @property
    def appname(self):
        return "Test"

def test_register_singleton():
    helper = DerivedAppHelper()

    called = [0]
    def db():
        called[0] += 1
        return 100
    helper.register_singleton("db", db)

    assert called[0] == 0
    assert helper.get_singleton("db") == 100
    assert called[0] == 1
    assert helper.get_singleton("db") == 100
    assert called[0] == 1

def test_register_factory():
    helper = DerivedAppHelper()

    called = [0]
    def db():
        called[0] += 1
        return 100
    helper.register_factory("db", db)

    assert called[0] == 0
    assert helper.call_factory("db") == 100
    assert called[0] == 1
    assert helper.call_factory("db") == 100
    assert called[0] == 2


def test_path():
    helper = DerivedAppHelper()
    path = helper.path
    assert("Test" in path.get_user_data_dir())
