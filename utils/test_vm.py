# -*- coding: utf-8 -*-
"""
test_vm.py - Test VM execution

This script tests executing Lua 5.3 compiled bytecode.

Usage:
1. Create a test.lua file with some Lua code
2. Compile with: luac53 -o test.luac test.lua
3. Run: py utils/test_vm.py test.luac

Author: aixiasang
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylua import (
    LUA_VERSION, LUA_SIGNATURE, lua_newstate, luaU_undump, 
    LuaError, luaV_execute, luaD_precall, LUA_MULTRET,
)
from pylua.lstate import LuaState, CallInfo, CIST_LUA
from pylua.lobject import (
    TValue, Value, Table, LClosure, setclLvalue, setnilvalue, 
    LUA_TTABLE, LUA_TSHRSTR, TString, setsvalue2n, setivalue,
)
from pylua.lzio import ZIO, luaZ_init, BytesReader
from pylua.ltm import luaT_init


def default_alloc(ud, ptr, osize, nsize):
    return None


def create_env_table(L: LuaState) -> Table:
    """Create _ENV table with basic library functions"""
    from pylua.lbaselib import luaopen_base
    from pylua.loslib import luaopen_os
    from pylua.lmathlib import luaopen_math
    
    env = Table()
    env.tt = LUA_TTABLE
    env.metatable = None
    env.array = []
    env.sizearray = 0
    env.node = []
    env.flags = 0
    env.lsizenode = 0
    
    # Open base library (registers print, tostring, type, etc.)
    luaopen_base(L, env)
    
    # Open os library
    luaopen_os(L, env)
    
    # Open math library
    luaopen_math(L, env)
    
    # Open string library
    from pylua.lstrlib import luaopen_string
    luaopen_string(L, env)
    
    # Open table library
    from pylua.ltablib import luaopen_table
    luaopen_table(L, env)
    
    return env


def setup_state(L: LuaState, cl: LClosure) -> None:
    """Setup initial state for VM execution"""
    from pylua.lobject import UpVal, ctb, LUA_TLCL
    
    # Initialize tag method names
    luaT_init(L)
    
    # Create _ENV table
    env = create_env_table(L)
    
    # Set _ENV as first upvalue
    env_val = TValue()
    env_val.tt_ = LUA_TTABLE | (1 << 6)
    env_val.value_.gc = env
    
    # Create upvalue for _ENV
    uv = UpVal()
    uv.v = env_val  # Closed upvalue pointing to env_val
    uv.value = env_val
    uv.refcount = 1
    
    if cl.nupvalues > 0:
        cl.upvals[0] = uv
    
    # Ensure stack space
    stack_size = max(cl.p.maxstacksize + 50, 100)
    while len(L.stack) < stack_size:
        L.stack.append(TValue())
    
    # Push closure on stack at position 0
    func_val = L.stack[0]
    func_val.value_.gc = cl
    func_val.tt_ = ctb(LUA_TLCL)
    
    # Setup CallInfo
    ci = CallInfo()
    ci.func = 0
    ci.base = 1
    ci.top = 1 + cl.p.maxstacksize
    ci.savedpc = 0
    ci.nresults = LUA_MULTRET
    ci.callstatus = CIST_LUA
    ci.previous = L.base_ci
    L.base_ci.next = ci
    
    L.ci = ci
    L.top = ci.top
    L.stacksize = stack_size
    L.stack_last = stack_size - 5
    
    # Initialize nil values in stack
    for i in range(1, ci.top + 1):
        if i < len(L.stack):
            setnilvalue(L.stack[i])


def run_bytecode(filename: str) -> None:
    """Load and execute bytecode file"""
    print(f"PyLua VM - {LUA_VERSION}")
    print(f"Loading: {filename}")
    print("=" * 60)
    
    if not os.path.exists(filename):
        print(f"Error: File not found: {filename}")
        return
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    if not data.startswith(LUA_SIGNATURE):
        print("Error: Not a valid Lua bytecode file")
        return
    
    # Create Lua state
    L = lua_newstate(default_alloc, None)
    if L is None:
        print("Error: Failed to create Lua state")
        return
    
    # Load bytecode
    z = ZIO()
    reader = BytesReader(data)
    luaZ_init(L, z, reader, None)
    z.n = len(data) - 1
    z.p = data[1:]
    z.pos = 0
    
    try:
        cl = luaU_undump(L, z, filename)
        print("Bytecode loaded successfully")
        print("-" * 60)
        print("Executing...")
        print("-" * 60)
        
        # Setup state
        setup_state(L, cl)
        
        # Execute
        luaV_execute(L)
        
        print("-" * 60)
        print("Execution completed successfully!")
        
    except LuaError as e:
        print(f"Lua Error: {e}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


def main():
    if len(sys.argv) < 2:
        print("Usage: py test_vm.py <bytecode_file.luac>")
        return
    
    run_bytecode(sys.argv[1])


if __name__ == "__main__":
    main()
