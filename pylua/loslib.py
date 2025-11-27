# -*- coding: utf-8 -*-
"""
loslib.py - Lua OS Library
===========================
Source: loslib.c (lua-5.3.6/src/loslib.c)

Operating System library for Lua
See Copyright Notice in lua.h
"""

import sys
import time
import os as python_os
from typing import TYPE_CHECKING

from .lobject import (
    TValue, TString, Table, CClosure,
    ttisnil, ttisboolean, ttisnumber, ttisinteger, ttisstring,
    ivalue, fltvalue, bvalue, svalue,
    setivalue, setfltvalue, setnilvalue, setbvalue,
    LUA_TSHRSTR, LUA_TCCL, ctb,
)

if TYPE_CHECKING:
    from .lstate import LuaState


# =============================================================================
# loslib.c:373-388 - os_exit
# =============================================================================

def os_exit(L: 'LuaState') -> int:
    """
    loslib.c:373-388 - os.exit ([code [, close]])
    
    Calls exit to terminate the program.
    
    static int os_exit (lua_State *L)
    
    Source: loslib.c:373-388
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    # Get exit code (default 0 for true/nil, 1 for false)
    code = 0
    if L.top > base:
        v = L.stack[base]
        if ttisboolean(v):
            code = 0 if bvalue(v) else 1
        elif ttisinteger(v):
            code = ivalue(v)
        elif ttisnumber(v):
            code = int(fltvalue(v))
    
    # Raise SystemExit to exit cleanly
    raise SystemExit(code)


# =============================================================================
# loslib.c:104-112 - os_clock
# =============================================================================

def os_clock(L: 'LuaState') -> int:
    """
    loslib.c:104-112 - os.clock ()
    
    Returns CPU time used by the program.
    
    static int os_clock (lua_State *L)
    
    Source: loslib.c:104-112
    """
    setfltvalue(L.stack[L.top], time.process_time())
    L.top += 1
    return 1


# =============================================================================
# loslib.c:288-317 - os_time
# =============================================================================

def os_time(L: 'LuaState') -> int:
    """
    loslib.c:288-317 - os.time ([table])
    
    Returns the current time.
    
    static int os_time (lua_State *L)
    
    Source: loslib.c:288-317
    """
    setivalue(L.stack[L.top], int(time.time()))
    L.top += 1
    return 1


# =============================================================================
# loslib.c:242-259 - os_date
# =============================================================================

def os_date(L: 'LuaState') -> int:
    """
    loslib.c:242-259 - os.date ([format [, time]])
    
    Returns a string or table containing date and time.
    
    static int os_date (lua_State *L)
    
    Source: loslib.c:242-259
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    # Default format
    fmt = "%c"
    t = time.time()
    
    if L.top > base and ttisstring(L.stack[base]):
        fmt = svalue(L.stack[base]).decode('utf-8')
    
    if L.top > base + 1 and ttisinteger(L.stack[base + 1]):
        t = ivalue(L.stack[base + 1])
    
    # Format time
    try:
        result = time.strftime(fmt, time.localtime(t))
    except:
        result = ""
    
    result_ts = TString()
    result_ts.tt = LUA_TSHRSTR
    result_ts.data = result.encode('utf-8')
    result_ts.shrlen = len(result_ts.data)
    L.stack[L.top].value_.gc = result_ts
    L.stack[L.top].tt_ = ctb(LUA_TSHRSTR)
    L.top += 1
    return 1


# =============================================================================
# loslib.c:133-141 - os_getenv
# =============================================================================

def os_getenv(L: 'LuaState') -> int:
    """
    loslib.c:133-141 - os.getenv (varname)
    
    Returns the value of environment variable varname.
    
    static int os_getenv (lua_State *L)
    
    Source: loslib.c:133-141
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base or not ttisstring(L.stack[base]):
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    varname = svalue(L.stack[base]).decode('utf-8')
    value = python_os.environ.get(varname)
    
    if value is None:
        setnilvalue(L.stack[L.top])
    else:
        result_ts = TString()
        result_ts.tt = LUA_TSHRSTR
        result_ts.data = value.encode('utf-8')
        result_ts.shrlen = len(result_ts.data)
        L.stack[L.top].value_.gc = result_ts
        L.stack[L.top].tt_ = ctb(LUA_TSHRSTR)
    
    L.top += 1
    return 1


# =============================================================================
# loslib.c:116-130 - os_remove
# =============================================================================

def os_remove(L: 'LuaState') -> int:
    """
    loslib.c:116-130 - os.remove(filename)
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base or not ttisstring(L.stack[base]):
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    filename = svalue(L.stack[base]).decode('utf-8')
    
    try:
        python_os.remove(filename)
        setbvalue(L.stack[L.top], 1)
        L.top += 1
        return 1
    except Exception as e:
        setnilvalue(L.stack[L.top])
        L.top += 1
        # Push error message
        err_ts = TString()
        err_ts.tt = LUA_TSHRSTR
        err_ts.data = str(e).encode('utf-8')
        err_ts.shrlen = len(err_ts.data)
        L.stack[L.top].value_.gc = err_ts
        L.stack[L.top].tt_ = ctb(LUA_TSHRSTR)
        L.top += 1
        return 2


# =============================================================================
# loslib.c:132-146 - os_rename
# =============================================================================

def os_rename(L: 'LuaState') -> int:
    """
    loslib.c:132-146 - os.rename(oldname, newname)
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base + 1:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    if not ttisstring(L.stack[base]) or not ttisstring(L.stack[base + 1]):
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    oldname = svalue(L.stack[base]).decode('utf-8')
    newname = svalue(L.stack[base + 1]).decode('utf-8')
    
    try:
        python_os.rename(oldname, newname)
        setbvalue(L.stack[L.top], 1)
        L.top += 1
        return 1
    except Exception as e:
        setnilvalue(L.stack[L.top])
        L.top += 1
        err_ts = TString()
        err_ts.tt = LUA_TSHRSTR
        err_ts.data = str(e).encode('utf-8')
        err_ts.shrlen = len(err_ts.data)
        L.stack[L.top].value_.gc = err_ts
        L.stack[L.top].tt_ = ctb(LUA_TSHRSTR)
        L.top += 1
        return 2


# =============================================================================
# loslib.c:109-114 - os_execute
# =============================================================================

def os_execute(L: 'LuaState') -> int:
    """
    loslib.c:109-114 - os.execute([command])
    """
    import subprocess
    
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base or ttisnil(L.stack[base]):
        # Check if shell is available
        setbvalue(L.stack[L.top], 1)
        L.top += 1
        return 1
    
    if not ttisstring(L.stack[base]):
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    command = svalue(L.stack[base]).decode('utf-8')
    
    try:
        result = python_os.system(command)
        setbvalue(L.stack[L.top], 1 if result == 0 else 0)
        L.top += 1
        # Push "exit"
        exit_ts = TString()
        exit_ts.tt = LUA_TSHRSTR
        exit_ts.data = b"exit"
        exit_ts.shrlen = 4
        L.stack[L.top].value_.gc = exit_ts
        L.stack[L.top].tt_ = ctb(LUA_TSHRSTR)
        L.top += 1
        setivalue(L.stack[L.top], result)
        L.top += 1
        return 3
    except Exception:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1


# =============================================================================
# loslib.c:148-159 - os_tmpname
# =============================================================================

def os_tmpname(L: 'LuaState') -> int:
    """
    loslib.c:148-159 - os.tmpname()
    """
    import tempfile
    
    try:
        fd, path = tempfile.mkstemp()
        python_os.close(fd)
        
        result_ts = TString()
        result_ts.tt = LUA_TSHRSTR
        result_ts.data = path.encode('utf-8')
        result_ts.shrlen = len(result_ts.data)
        L.stack[L.top].value_.gc = result_ts
        L.stack[L.top].tt_ = ctb(LUA_TSHRSTR)
        L.top += 1
        return 1
    except Exception:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1


# =============================================================================
# OS Library Registration
# =============================================================================

os_funcs = {
    "exit": os_exit,
    "clock": os_clock,
    "time": os_time,
    "date": os_date,
    "getenv": os_getenv,
    "remove": os_remove,
    "rename": os_rename,
    "execute": os_execute,
    "tmpname": os_tmpname,
}


def luaopen_os(L: 'LuaState', env: 'Table') -> None:
    """
    loslib.c:390-402 - Open OS library
    
    Registers OS library functions in _G.os table.
    
    LUAMOD_API int luaopen_os (lua_State *L)
    
    Source: loslib.c:390-402
    """
    from .lobject import Node, TKey, TValue, setclCvalue, sethvalue
    
    # Create os table
    os_table = Table()
    os_table.tt = 5  # LUA_TTABLE
    os_table.metatable = None
    os_table.array = []
    os_table.sizearray = 0
    os_table.node = []
    os_table.flags = 0
    os_table.lsizenode = 0
    
    # Add functions to os table
    for name, func in os_funcs.items():
        closure = CClosure()
        closure.tt = LUA_TCCL
        closure.nupvalues = 0
        closure.f = func
        closure.upvalue = []
        
        key = TValue()
        key.tt_ = ctb(LUA_TSHRSTR)
        key_str = TString()
        key_str.tt = LUA_TSHRSTR
        key_str.data = name.encode('utf-8')
        key_str.shrlen = len(key_str.data)
        key.value_.gc = key_str
        
        val = TValue()
        setclCvalue(L, val, closure)
        
        node = Node()
        node.i_key = TKey()
        node.i_key.value_ = key.value_
        node.i_key.tt_ = key.tt_
        node.i_key.next = 0
        node.i_val = val
        os_table.node.append(node)
    
    os_table.lsizenode = len(os_table.node)
    
    # Add os table to environment
    os_key = TValue()
    os_key.tt_ = ctb(LUA_TSHRSTR)
    os_str = TString()
    os_str.tt = LUA_TSHRSTR
    os_str.data = b"os"
    os_str.shrlen = 2
    os_key.value_.gc = os_str
    
    os_val = TValue()
    os_val.tt_ = ctb(5)  # LUA_TTABLE with collectable
    os_val.value_.gc = os_table
    
    node = Node()
    node.i_key = TKey()
    node.i_key.value_ = os_key.value_
    node.i_key.tt_ = os_key.tt_
    node.i_key.next = 0
    node.i_val = os_val
    env.node.append(node)
    env.lsizenode = len(env.node)
