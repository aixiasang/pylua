#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylua.compile import compile_source

source = 'print("hello"); local x = 1; local y = 1.5; local z = "test"'
cl, err = compile_source(source)
if err:
    print(f"Error: {err}")
else:
    print("Constants from proto.k:")
    for i, k in enumerate(cl.p.k):
        tt = getattr(k, 'tt_', None)
        val = getattr(k, 'value_', None)
        print(f"  {i}: tt_={tt}, value_={val}")
        if val:
            if hasattr(val, 'i'):
                print(f"      .i = {val.i}")
            if hasattr(val, 'n'):
                print(f"      .n = {val.n}")
            if hasattr(val, 'gc'):
                gc = val.gc
                print(f"      .gc = {gc}, data={getattr(gc, 'data', None)}")
