# -*- coding: utf-8 -*-
"""
test_undump.py - Test bytecode loading

This script tests loading Lua 5.3 compiled bytecode files.

Usage:
1. Create a test.lua file with some Lua code
2. Compile with: luac53 -o test.luac test.lua
3. Run: py utils/test_undump.py test.luac

Author: aixiasang
"""

import sys
import os

# Add pylua to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylua import (
    LUA_VERSION, LUA_SIGNATURE, LUA_OK,
    lua_newstate, luaU_undump, LuaUndumpError,
    OpCode, GET_OPCODE, GETARG_A, GETARG_B, GETARG_C, GETARG_Bx, GETARG_sBx,
    luaP_opnames, getOpMode, OpMode,
    LUA_TNIL, LUA_TBOOLEAN, LUA_TNUMFLT, LUA_TNUMINT, LUA_TSHRSTR, LUA_TLNGSTR,
)
from pylua.lzio import ZIO, luaZ_init, FileReader, BytesReader


def default_alloc(ud, ptr, osize, nsize):
    """Default memory allocator (Python handles memory)"""
    return None


def disassemble_instruction(i: int, pc: int) -> str:
    """Disassemble a single instruction"""
    op = GET_OPCODE(i)
    a = GETARG_A(i)
    mode = getOpMode(op)
    
    name = luaP_opnames[op] if op < len(luaP_opnames) else f"OP_{op}"
    
    if mode == OpMode.iABC:
        b = GETARG_B(i)
        c = GETARG_C(i)
        return f"{pc:4d}\t{name:12s}\t{a} {b} {c}"
    elif mode == OpMode.iABx:
        bx = GETARG_Bx(i)
        return f"{pc:4d}\t{name:12s}\t{a} {bx}"
    elif mode == OpMode.iAsBx:
        sbx = GETARG_sBx(i)
        return f"{pc:4d}\t{name:12s}\t{a} {sbx}"
    elif mode == OpMode.iAx:
        ax = (i >> 6) & 0x3FFFFFF
        return f"{pc:4d}\t{name:12s}\t{ax}"
    
    return f"{pc:4d}\t{name:12s}\t?"


def print_constant(k, idx: int) -> str:
    """Format a constant for printing"""
    tt = k.tt_
    if tt == LUA_TNIL:
        return f"[{idx}] nil"
    elif tt == LUA_TBOOLEAN:
        return f"[{idx}] {bool(k.value_.b)}"
    elif tt == LUA_TNUMFLT:
        return f"[{idx}] {k.value_.n}"
    elif tt == LUA_TNUMINT:
        return f"[{idx}] {k.value_.i}"
    elif tt in (LUA_TSHRSTR, LUA_TLNGSTR) or (tt & 0x0F) == 4:
        if k.value_.gc and hasattr(k.value_.gc, 'data'):
            try:
                s = k.value_.gc.data.decode('utf-8')
                return f'[{idx}] "{s}"'
            except:
                return f'[{idx}] <binary string>'
        return f"[{idx}] <string>"
    else:
        return f"[{idx}] <type {tt}>"


def print_proto(p, indent: int = 0) -> None:
    """Print prototype information"""
    prefix = "  " * indent
    
    # Source info
    source_name = "<unknown>"
    if p.source and hasattr(p.source, 'data'):
        try:
            source_name = p.source.data.decode('utf-8')
        except:
            pass
    
    print(f"{prefix}Function: {source_name}")
    print(f"{prefix}  Lines: {p.linedefined}-{p.lastlinedefined}")
    print(f"{prefix}  Params: {p.numparams}, Vararg: {p.is_vararg}, MaxStack: {p.maxstacksize}")
    print(f"{prefix}  Upvalues: {p.sizeupvalues}, Locals: {p.sizelocvars}, Constants: {p.sizek}")
    
    # Constants
    if p.sizek > 0:
        print(f"{prefix}  Constants ({p.sizek}):")
        for i, k in enumerate(p.k):
            print(f"{prefix}    {print_constant(k, i)}")
    
    # Code
    print(f"{prefix}  Instructions ({p.sizecode}):")
    for pc, instr in enumerate(p.code):
        line = p.lineinfo[pc] if pc < len(p.lineinfo) else 0
        dis = disassemble_instruction(instr, pc)
        print(f"{prefix}    [{line:3d}] {dis}")
    
    # Upvalues
    if p.sizeupvalues > 0:
        print(f"{prefix}  Upvalues ({p.sizeupvalues}):")
        for i, uv in enumerate(p.upvalues):
            name = "<unknown>"
            if uv.name and hasattr(uv.name, 'data'):
                try:
                    name = uv.name.data.decode('utf-8')
                except:
                    pass
            print(f"{prefix}    [{i}] {name} (instack={uv.instack}, idx={uv.idx})")
    
    # Locals
    if p.sizelocvars > 0:
        print(f"{prefix}  Locals ({p.sizelocvars}):")
        for i, lv in enumerate(p.locvars):
            name = "<unknown>"
            if lv.varname and hasattr(lv.varname, 'data'):
                try:
                    name = lv.varname.data.decode('utf-8')
                except:
                    pass
            print(f"{prefix}    [{i}] {name} (pc={lv.startpc}-{lv.endpc})")
    
    # Nested functions
    if p.sizep > 0:
        print(f"{prefix}  Nested functions ({p.sizep}):")
        for i, np in enumerate(p.p):
            print(f"{prefix}    --- Function {i} ---")
            print_proto(np, indent + 2)


def load_bytecode(filename: str) -> None:
    """Load and display bytecode file"""
    print(f"PyLua - {LUA_VERSION} Bytecode Loader")
    print(f"Loading: {filename}")
    print("=" * 60)
    
    # Check file exists
    if not os.path.exists(filename):
        print(f"Error: File not found: {filename}")
        return
    
    # Read file
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Check signature
    if not data.startswith(LUA_SIGNATURE):
        print(f"Error: Not a valid Lua bytecode file (missing signature)")
        return
    
    print(f"File size: {len(data)} bytes")
    print(f"Signature: {data[:4].hex()} (OK)")
    
    # Create Lua state
    L = lua_newstate(default_alloc, None)
    if L is None:
        print("Error: Failed to create Lua state")
        return
    
    # Create ZIO
    z = ZIO()
    reader = BytesReader(data)
    luaZ_init(L, z, reader, None)
    
    # Skip first byte of signature (already verified)
    z.n = len(data) - 1
    z.p = data[1:]
    z.pos = 0
    
    try:
        # Load bytecode
        cl = luaU_undump(L, z, filename)
        
        print("\n" + "=" * 60)
        print("BYTECODE LOADED SUCCESSFULLY!")
        print("=" * 60)
        
        # Print prototype info
        if cl.p:
            print_proto(cl.p)
        
        print("\n" + "=" * 60)
        print("LOAD COMPLETE")
        
    except LuaUndumpError as e:
        print(f"\nError loading bytecode: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


def main():
    if len(sys.argv) < 2:
        print("Usage: py test_undump.py <bytecode_file.luac>")
        print("\nTo create a bytecode file:")
        print("  1. Write Lua code to test.lua")
        print("  2. Compile: lua53 -o test.luac test.lua")
        print("  3. Run: py test_undump.py test.luac")
        return
    
    load_bytecode(sys.argv[1])


if __name__ == "__main__":
    main()
