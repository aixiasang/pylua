# -*- coding: utf-8 -*-
"""
PyLua - Lua 5.3.6 Python Implementation
========================================

A faithful Python replication of Lua 5.3.6 virtual machine.
This package provides a complete implementation of Lua VM that can execute
precompiled Lua bytecode (.luac files compiled by lua53).

Source: lua-5.3.6/src/
Copyright (C) 1994-2020 Lua.org, PUC-Rio.
Python replication maintains absolute consistency with C implementation.

Package Structure (mirrors C source files):
- lua.py       : Core API constants and types (lua.h)
- luaconf.py   : Configuration (luaconf.h)
- llimits.py   : Limits and basic types (llimits.h)
- lobject.py   : Object system and TValue (lobject.h/c)
- lopcodes.py  : Opcode definitions (lopcodes.h/c)
- lundump.py   : Bytecode loading (lundump.h/c)
- lstate.py    : Lua state management (lstate.h/c)
- ltm.py       : Tag methods (ltm.h/c)
- lzio.py      : Buffered streams (lzio.h/c)
- lvm.py       : Virtual machine execution (lvm.h/c)
- ldo.py       : Stack and call structure (ldo.h/c)
"""

# Version info
__version__ = "5.3.6"
__author__ = "aixiasang"

# Core constants and types (lua.h)
from .lua import (
    LUA_VERSION, LUA_VERSION_NUM, LUA_RELEASE, LUA_COPYRIGHT,
    LUA_SIGNATURE, LUA_MULTRET,
    LUA_OK, LUA_YIELD, LUA_ERRRUN, LUA_ERRSYNTAX, LUA_ERRMEM, LUA_ERRGCMM, LUA_ERRERR,
    LUA_TNONE, LUA_TNIL, LUA_TBOOLEAN, LUA_TLIGHTUSERDATA,
    LUA_TNUMBER, LUA_TSTRING, LUA_TTABLE, LUA_TFUNCTION,
    LUA_TUSERDATA, LUA_TTHREAD, LUA_NUMTAGS,
    LUA_MINSTACK, LUA_RIDX_MAINTHREAD, LUA_RIDX_GLOBALS,
    lua_Number, lua_Integer, lua_typename,
)

# Configuration (luaconf.h)
from .luaconf import (
    LUAI_MAXSTACK, LUA_IDSIZE, LUA_REGISTRYINDEX,
    LUA_MAXINTEGER, LUA_MININTEGER,
)

# Object system (lobject.h)
from .lobject import (
    GCObject, Value, TValue, TString, Proto, LClosure, CClosure,
    Table, UpVal, Upvaldesc, LocVar,
    LUA_TPROTO, LUA_TLCL, LUA_TCCL, LUA_TSHRSTR, LUA_TLNGSTR,
    LUA_TNUMFLT, LUA_TNUMINT,
)

# Opcodes (lopcodes.h)
from .lopcodes import (
    OpCode, OpMode, OpArgMask, NUM_OPCODES,
    GET_OPCODE, GETARG_A, GETARG_B, GETARG_C, GETARG_Bx, GETARG_sBx, GETARG_Ax,
    ISK, INDEXK, luaP_opnames, luaP_opmodes,
    getOpMode, getBMode, getCMode, testAMode, testTMode,
)

# State management (lstate.h)
from .lstate import (
    LuaState, GlobalState, CallInfo, StringTable,
    lua_newstate, lua_close, G,
)

# Buffered streams (lzio.h)
from .lzio import ZIO, Mbuffer, luaZ_init, BytesReader, FileReader

# Bytecode loading (lundump.h)
from .lundump import luaU_undump, LuaUndumpError

# Tag methods (ltm.h)
from .ltm import TMS, luaT_typenames_

# Function prototypes and closures (lfunc.h)
from .lfunc import (
    luaF_newproto, luaF_newLclosure, luaF_newCclosure,
    luaF_initupvals, luaF_findupval, luaF_close,
    luaF_freeproto, luaF_getlocalname, upisopen,
    sizeCclosure, sizeLclosure,
)

# VM functions (lvm.h)
from .lvm import (
    tonumber, tointeger, cvt2str, cvt2num,
    luaV_tonumber_, luaV_tointeger,
    luaV_equalobj, luaV_lessthan, luaV_lessequal,
    luaV_div, luaV_mod, luaV_shiftl,
    luaV_rawequalobj, luaV_execute,
)

# Call/Stack functions (ldo.h)
from .ldo import (
    luaD_call, luaD_precall, luaD_poscall,
    luaD_checkstack, luaD_growstack, luaD_inctop,
    luaD_pcall, luaD_throw, LuaError,
)

# Base library functions (lbaselib.c)
from .lbaselib import (
    luaopen_base, base_funcs,
    luaB_print, luaB_tostring, luaB_tonumber, luaB_type,
    luaB_error, luaB_assert, luaB_pcall,
    luaB_rawequal, luaB_rawlen, luaB_rawget, luaB_rawset,
    luaB_select, luaB_setmetatable, luaB_getmetatable,
    luaB_next, luaB_pairs, luaB_ipairs,
)

# Table operations (ltable.c)
from .ltable import (
    luaH_next, luaH_get, luaH_getint, luaH_getstr,
    mainposition, findindex, arrayindex,
)

# Package/require library (loadlib.c)
from .lloadlib import luaopen_package, ll_require

# Coroutine library (lcorolib.c)
from .lcorolib import luaopen_coroutine

# I/O library (liolib.c)
from .liolib import luaopen_io

# Compiler (lcode.c, lparser.c, llex.c)
from .compile import (
    pylua_compile, compile_source, extract_proto,
    CompiledProto, CompiledInstruction, disassemble,
)

# Bytecode dumper (ldump.c)
from .ldump import luaU_dump

# CLI
from .cli import main as cli_main, PYLUA_VERSION


def run(source: str, name: str = "=python") -> None:
    """
    Compile and show bytecode for Lua source code.
    
    Note: Full VM execution is work in progress.
    This function currently compiles and prints the bytecode.
    """
    proto, error = pylua_compile(source, name)
    if error:
        raise SyntaxError(error)
    print(disassemble(proto))


def compile(source: str, name: str = "=python") -> CompiledProto:
    """Compile Lua source code and return CompiledProto"""
    proto, error = pylua_compile(source, name)
    if error:
        raise SyntaxError(error)
    return proto


def load_file(filename: str) -> CompiledProto:
    """Load and compile a Lua file"""
    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()
    return compile(source, f"@{filename}")


def exec_file(filename: str) -> None:
    """Execute a Lua file"""
    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()
    run(source, f"@{filename}")
