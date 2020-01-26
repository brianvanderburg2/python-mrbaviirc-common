""" Tests for mrbaviirc.common.util.imp """

from __future__ import absolute_import

__author__      = "Brian AllenVanderburg II"
__copyright__   = "Copyright 2018"
__license__     = "Apache License 2.0"


import pytest

from mrbaviirc.common import imp

# Exporter
def test_exporter_symbol():
    glbls = {"__package__": "mrbaviirc.common.util"}
    export = imp.Exporter(glbls)

    @export
    def test():
        pass
    assert("test" in glbls["__all__"])

    export(ID=500)
    assert(glbls["ID"] == 500)
    assert("ID" in glbls["__all__"])

    with pytest.raises(imp.ExportError):
        export(ID=501)

    with pytest.raises(imp.ExportError):
        @export
        def test():
            pass

def test_exporter_extend():
    import os
    from mrbaviirc.common import functools
    
    glbls = {"__package__": "mrbaviirc.common"}
    export = imp.Exporter(glbls)

    export.extend(os)
    assert(glbls["__all__"] == os.__all__)
    assert(glbls["path"] == os.path)


    glbls = {"__package__": "mrbaviirc.common"}
    export = imp.Exporter(glbls)

    export.extend("os")
    assert(glbls["__all__"] == os.__all__)
    assert(glbls["path"] == os.path)

    glbls = {"__package__": "mrbaviirc.common"}
    export = imp.Exporter(glbls)

    export.extend(".functools")
    assert(glbls["__all__"] == functools.__all__)
    assert(glbls["lazy_property"] == functools.lazy_property)



    
