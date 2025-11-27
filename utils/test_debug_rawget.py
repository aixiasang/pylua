#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_debug_rawget.py - Debug rawget issue

Author: aixiasang
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylua.lstate import lua_newstate, LuaState
from pylua.lundump import luaU_undump, ZIO, LUA_SIGNATURE
from pylua.lvm import luaV_execute
from pylua.ltm import luaT_init
from pylua.lobject import (
    TValue, Table, LClosure, UpVal, CClosure, TString,
    LUA_TTABLE, LUA_TLCL, LUA_TCCL, LUA_TSHRSTR,
    setnilvalue, setobj, setobj2s, hvalue, ttistable,
    ctb,
)

def default_alloc(ud, ptr, osize, nsize):
    return None

# Read bytecode
with open('test_rawget_hello.luac', 'rb') as f:
    data = f.read()

L = lua_newstate(default_alloc, None)
luaT_init(L)

# Create env table
env = Table()
env.tt = LUA_TTABLE
env.metatable = None
env.array = []
env.sizearray = 0
env.node = []
env.flags = 0
env.lsizenode = 0

# Add print function
from pylua.lbaselib import luaopen_base
luaopen_base(L, env)

# Load bytecode
z = ZIO()
z.data = data
z.p = 0
z.n = len(data)
z.name = "test"

cl = luaU_undump(L, z, "@test")

# Setup state
from pylua.lobject import LUA_TLCL
cl.upvals = [UpVal()]
cl.upvals[0].v = env
cl.upvals[0].value = TValue()
cl.upvals[0].value.tt_ = ctb(LUA_TTABLE)
cl.upvals[0].value.value_.gc = env

# Setup stack
stack_size = 200
L.stack = [TValue() for _ in range(stack_size)]
L.stacksize = stack_size
L.stack_last = stack_size - 5
L.top = 1
L.stack[0].value_.gc = cl
L.stack[0].tt_ = ctb(LUA_TLCL)

# Create CallInfo
from pylua.lstate import CallInfo, luaE_extendCI, CIST_LUA
ci = luaE_extendCI(L)
ci.func = 0
ci.base = 1
ci.top = 1 + cl.p.maxstacksize
ci.savedpc = 0
ci.nresults = 0
ci.callstatus = CIST_LUA
L.ci = ci
L.top = ci.top

# Execute
try:
    luaV_execute(L)
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
