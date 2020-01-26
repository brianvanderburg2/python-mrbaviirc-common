""" Tests for mrbaviirc.common.util.functools """

__author__      = "Brian AllenVanderburg II"
__copyright__   = "Copyright 2018"
__license__     = "Apache License 2.0"


from mrbaviirc.common import functools

# lazyprop
class LazyPropTester:

    def __init__(self):
        self.prop1_count = 0
        self.prop2_count = 0

    @functools.lazy_property
    def prop1(self):
        self.prop1_count += 1
        return 12

    @functools.lazy_property
    def prop2(self):
        self.prop2_count += 1
        return self.prop1 + 12

def test_lazyprop():
    tester1 = LazyPropTester()

    # No access yet
    assert(tester1.prop1_count == 0)
    assert(tester1.prop2_count == 0)
    
    # First access
    assert(tester1.prop1 == 12)
    assert(tester1.prop1_count == 1)

    assert(tester1.prop2 == 24)
    assert(tester1.prop2_count == 1)
    
    # Second access
    assert(tester1.prop1 == 12)
    assert(tester1.prop2_count == 1)

    assert(tester1.prop2 == 24)
    assert(tester1.prop1_count == 1)
