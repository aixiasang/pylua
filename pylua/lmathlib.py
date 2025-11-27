# -*- coding: utf-8 -*-
"""
lmathlib.py - Lua Math Library
===============================
Source: lmathlib.c (lua-5.3.6/src/lmathlib.c)

Mathematical library for Lua
See Copyright Notice in lua.h
"""

import math
import random
from typing import TYPE_CHECKING

from .lobject import (
    TValue, TString, Table, CClosure,
    ttisnil, ttisnumber, ttisinteger, ttisfloat, ttisstring,
    ivalue, fltvalue, svalue,
    setivalue, setfltvalue, setnilvalue,
    LUA_TSHRSTR, LUA_TCCL, ctb,
)

if TYPE_CHECKING:
    from .lstate import LuaState


def _getnum(L: 'LuaState', idx: int):
    """Get number from stack at index"""
    ci = L.ci
    base = ci.base if ci else 1
    if L.top <= base + idx:
        return None
    v = L.stack[base + idx]
    if ttisinteger(v):
        return float(ivalue(v))
    elif ttisfloat(v):
        return fltvalue(v)
    return None


# =============================================================================
# lmathlib.c - math.abs
# =============================================================================

def math_abs(L: 'LuaState') -> int:
    """math.abs (x)"""
    n = _getnum(L, 0)
    if n is None:
        setnilvalue(L.stack[L.top])
    else:
        setfltvalue(L.stack[L.top], abs(n))
    L.top += 1
    return 1


# =============================================================================
# lmathlib.c - math.floor
# =============================================================================

def math_floor(L: 'LuaState') -> int:
    """math.floor (x)"""
    n = _getnum(L, 0)
    if n is None:
        setnilvalue(L.stack[L.top])
    else:
        result = math.floor(n)
        if result == int(result) and abs(result) < 2**63:
            setivalue(L.stack[L.top], int(result))
        else:
            setfltvalue(L.stack[L.top], result)
    L.top += 1
    return 1


# =============================================================================
# lmathlib.c - math.ceil
# =============================================================================

def math_ceil(L: 'LuaState') -> int:
    """math.ceil (x)"""
    n = _getnum(L, 0)
    if n is None:
        setnilvalue(L.stack[L.top])
    else:
        result = math.ceil(n)
        if result == int(result) and abs(result) < 2**63:
            setivalue(L.stack[L.top], int(result))
        else:
            setfltvalue(L.stack[L.top], result)
    L.top += 1
    return 1


# =============================================================================
# lmathlib.c - math.sqrt
# =============================================================================

def math_sqrt(L: 'LuaState') -> int:
    """math.sqrt (x)"""
    n = _getnum(L, 0)
    if n is None:
        setnilvalue(L.stack[L.top])
    else:
        setfltvalue(L.stack[L.top], math.sqrt(n))
    L.top += 1
    return 1


# =============================================================================
# lmathlib.c - math.sin/cos/tan
# =============================================================================

def math_sin(L: 'LuaState') -> int:
    """math.sin (x)"""
    n = _getnum(L, 0)
    if n is None:
        setnilvalue(L.stack[L.top])
    else:
        setfltvalue(L.stack[L.top], math.sin(n))
    L.top += 1
    return 1


def math_cos(L: 'LuaState') -> int:
    """math.cos (x)"""
    n = _getnum(L, 0)
    if n is None:
        setnilvalue(L.stack[L.top])
    else:
        setfltvalue(L.stack[L.top], math.cos(n))
    L.top += 1
    return 1


def math_tan(L: 'LuaState') -> int:
    """math.tan (x)"""
    n = _getnum(L, 0)
    if n is None:
        setnilvalue(L.stack[L.top])
    else:
        setfltvalue(L.stack[L.top], math.tan(n))
    L.top += 1
    return 1


# =============================================================================
# lmathlib.c - math.asin/acos/atan
# =============================================================================

def math_asin(L: 'LuaState') -> int:
    """math.asin (x)"""
    n = _getnum(L, 0)
    if n is None:
        setnilvalue(L.stack[L.top])
    else:
        setfltvalue(L.stack[L.top], math.asin(n))
    L.top += 1
    return 1


def math_acos(L: 'LuaState') -> int:
    """math.acos (x)"""
    n = _getnum(L, 0)
    if n is None:
        setnilvalue(L.stack[L.top])
    else:
        setfltvalue(L.stack[L.top], math.acos(n))
    L.top += 1
    return 1


def math_atan(L: 'LuaState') -> int:
    """math.atan (y [, x])"""
    y = _getnum(L, 0)
    x = _getnum(L, 1)
    if y is None:
        setnilvalue(L.stack[L.top])
    elif x is None:
        setfltvalue(L.stack[L.top], math.atan(y))
    else:
        setfltvalue(L.stack[L.top], math.atan2(y, x))
    L.top += 1
    return 1


# =============================================================================
# lmathlib.c - math.exp/log
# =============================================================================

def math_exp(L: 'LuaState') -> int:
    """math.exp (x)"""
    n = _getnum(L, 0)
    if n is None:
        setnilvalue(L.stack[L.top])
    else:
        setfltvalue(L.stack[L.top], math.exp(n))
    L.top += 1
    return 1


def math_log(L: 'LuaState') -> int:
    """math.log (x [, base])"""
    x = _getnum(L, 0)
    base = _getnum(L, 1)
    if x is None:
        setnilvalue(L.stack[L.top])
    elif base is None:
        setfltvalue(L.stack[L.top], math.log(x))
    else:
        setfltvalue(L.stack[L.top], math.log(x, base))
    L.top += 1
    return 1


# =============================================================================
# lmathlib.c - math.deg/rad
# =============================================================================

def math_deg(L: 'LuaState') -> int:
    """math.deg (x)"""
    n = _getnum(L, 0)
    if n is None:
        setnilvalue(L.stack[L.top])
    else:
        setfltvalue(L.stack[L.top], math.degrees(n))
    L.top += 1
    return 1


def math_rad(L: 'LuaState') -> int:
    """math.rad (x)"""
    n = _getnum(L, 0)
    if n is None:
        setnilvalue(L.stack[L.top])
    else:
        setfltvalue(L.stack[L.top], math.radians(n))
    L.top += 1
    return 1


# =============================================================================
# lmathlib.c - math.min/max
# =============================================================================

def math_min(L: 'LuaState') -> int:
    """math.min (x, ...)"""
    ci = L.ci
    base = ci.base if ci else 1
    nargs = L.top - base
    
    if nargs == 0:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    min_val = _getnum(L, 0)
    for i in range(1, nargs):
        v = _getnum(L, i)
        if v is not None and (min_val is None or v < min_val):
            min_val = v
    
    if min_val is None:
        setnilvalue(L.stack[L.top])
    else:
        setfltvalue(L.stack[L.top], min_val)
    L.top += 1
    return 1


def math_max(L: 'LuaState') -> int:
    """math.max (x, ...)"""
    ci = L.ci
    base = ci.base if ci else 1
    nargs = L.top - base
    
    if nargs == 0:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    max_val = _getnum(L, 0)
    for i in range(1, nargs):
        v = _getnum(L, i)
        if v is not None and (max_val is None or v > max_val):
            max_val = v
    
    if max_val is None:
        setnilvalue(L.stack[L.top])
    else:
        setfltvalue(L.stack[L.top], max_val)
    L.top += 1
    return 1


# =============================================================================
# lmathlib.c - math.fmod/modf
# =============================================================================

def math_fmod(L: 'LuaState') -> int:
    """math.fmod (x, y)"""
    x = _getnum(L, 0)
    y = _getnum(L, 1)
    if x is None or y is None:
        setnilvalue(L.stack[L.top])
    else:
        setfltvalue(L.stack[L.top], math.fmod(x, y))
    L.top += 1
    return 1


def math_modf(L: 'LuaState') -> int:
    """math.modf (x) - returns integral and fractional parts"""
    n = _getnum(L, 0)
    if n is None:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    frac, intg = math.modf(n)
    if intg == int(intg) and abs(intg) < 2**63:
        setivalue(L.stack[L.top], int(intg))
    else:
        setfltvalue(L.stack[L.top], intg)
    L.top += 1
    setfltvalue(L.stack[L.top], frac)
    L.top += 1
    return 2


# =============================================================================
# lmathlib.c - math.random/randomseed
# =============================================================================

def math_random(L: 'LuaState') -> int:
    """math.random ([m [, n]])"""
    ci = L.ci
    base = ci.base if ci else 1
    nargs = L.top - base
    
    if nargs == 0:
        setfltvalue(L.stack[L.top], random.random())
    elif nargs == 1:
        m = int(_getnum(L, 0) or 1)
        setivalue(L.stack[L.top], random.randint(1, m))
    else:
        m = int(_getnum(L, 0) or 1)
        n = int(_getnum(L, 1) or 1)
        setivalue(L.stack[L.top], random.randint(m, n))
    
    L.top += 1
    return 1


def math_randomseed(L: 'LuaState') -> int:
    """math.randomseed (x)"""
    n = _getnum(L, 0)
    if n is not None:
        random.seed(int(n))
    return 0


# =============================================================================
# lmathlib.c - math.type
# =============================================================================

def math_type(L: 'LuaState') -> int:
    """math.type (x)"""
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    v = L.stack[base]
    if ttisinteger(v):
        result = "integer"
    elif ttisfloat(v):
        result = "float"
    else:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    result_ts = TString()
    result_ts.tt = LUA_TSHRSTR
    result_ts.data = result.encode('utf-8')
    result_ts.shrlen = len(result_ts.data)
    L.stack[L.top].value_.gc = result_ts
    L.stack[L.top].tt_ = ctb(LUA_TSHRSTR)
    L.top += 1
    return 1


# =============================================================================
# lmathlib.c - math.tointeger/ult
# =============================================================================

def math_tointeger(L: 'LuaState') -> int:
    """math.tointeger (x) - lvm.c:94-117 luaV_tointeger logic"""
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    v = L.stack[base]
    if ttisinteger(v):
        setivalue(L.stack[L.top], ivalue(v))
    elif ttisfloat(v):
        n = fltvalue(v)
        if n == int(n) and abs(n) < 2**63:
            setivalue(L.stack[L.top], int(n))
        else:
            setnilvalue(L.stack[L.top])
    elif ttisstring(v):
        # Try to convert string to integer (lvm.c:111-115)
        try:
            s = svalue(v).decode('utf-8', errors='replace').strip()
            # Try integer first
            try:
                n = int(s)
                if abs(n) < 2**63:
                    setivalue(L.stack[L.top], n)
                else:
                    setnilvalue(L.stack[L.top])
            except ValueError:
                # Try float, then check if integral
                try:
                    f = float(s)
                    if f == int(f) and abs(f) < 2**63:
                        setivalue(L.stack[L.top], int(f))
                    else:
                        setnilvalue(L.stack[L.top])
                except ValueError:
                    setnilvalue(L.stack[L.top])
        except:
            setnilvalue(L.stack[L.top])
    else:
        setnilvalue(L.stack[L.top])
    
    L.top += 1
    return 1


def math_ult(L: 'LuaState') -> int:
    """math.ult (m, n)"""
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top < base + 2:
        from .lobject import setbvalue
        setbvalue(L.stack[L.top], 0)
        L.top += 1
        return 1
    
    m = ivalue(L.stack[base]) if ttisinteger(L.stack[base]) else 0
    n = ivalue(L.stack[base + 1]) if ttisinteger(L.stack[base + 1]) else 0
    
    # Unsigned comparison
    um = m & 0xFFFFFFFFFFFFFFFF
    un = n & 0xFFFFFFFFFFFFFFFF
    
    from .lobject import setbvalue
    setbvalue(L.stack[L.top], 1 if um < un else 0)
    L.top += 1
    return 1


# =============================================================================
# Math Library Registration
# =============================================================================

math_funcs = {
    "abs": math_abs,
    "floor": math_floor,
    "ceil": math_ceil,
    "sqrt": math_sqrt,
    "sin": math_sin,
    "cos": math_cos,
    "tan": math_tan,
    "asin": math_asin,
    "acos": math_acos,
    "atan": math_atan,
    "exp": math_exp,
    "log": math_log,
    "deg": math_deg,
    "rad": math_rad,
    "min": math_min,
    "max": math_max,
    "fmod": math_fmod,
    "modf": math_modf,
    "random": math_random,
    "randomseed": math_randomseed,
    "type": math_type,
    "tointeger": math_tointeger,
    "ult": math_ult,
}

# Math constants
MATH_PI = math.pi
MATH_HUGE = float('inf')
MATH_MAXINTEGER = 2**63 - 1
MATH_MININTEGER = -(2**63)


def luaopen_math(L: 'LuaState', env: 'Table') -> None:
    """
    Open math library
    """
    from .lobject import Node, TKey, TValue, setclCvalue
    
    # Create math table
    math_table = Table()
    math_table.tt = 5  # LUA_TTABLE
    math_table.metatable = None
    math_table.array = []
    math_table.sizearray = 0
    math_table.node = []
    math_table.flags = 0
    math_table.lsizenode = 0
    
    # Add functions to math table
    for name, func in math_funcs.items():
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
        math_table.node.append(node)
    
    # Add constants
    def add_const(name, value):
        key = TValue()
        key.tt_ = ctb(LUA_TSHRSTR)
        key_str = TString()
        key_str.tt = LUA_TSHRSTR
        key_str.data = name.encode('utf-8')
        key_str.shrlen = len(key_str.data)
        key.value_.gc = key_str
        
        val = TValue()
        setfltvalue(val, value)
        
        node = Node()
        node.i_key = TKey()
        node.i_key.value_ = key.value_
        node.i_key.tt_ = key.tt_
        node.i_key.next = 0
        node.i_val = val
        math_table.node.append(node)
    
    def add_int_const(name, value):
        key = TValue()
        key.tt_ = ctb(LUA_TSHRSTR)
        key_str = TString()
        key_str.tt = LUA_TSHRSTR
        key_str.data = name.encode('utf-8')
        key_str.shrlen = len(key_str.data)
        key.value_.gc = key_str
        
        val = TValue()
        setivalue(val, value)
        
        node = Node()
        node.i_key = TKey()
        node.i_key.value_ = key.value_
        node.i_key.tt_ = key.tt_
        node.i_key.next = 0
        node.i_val = val
        math_table.node.append(node)
    
    add_const("pi", MATH_PI)
    add_const("huge", MATH_HUGE)
    add_int_const("maxinteger", MATH_MAXINTEGER)
    add_int_const("mininteger", MATH_MININTEGER)
    
    math_table.lsizenode = len(math_table.node)
    
    # Add math table to environment
    math_key = TValue()
    math_key.tt_ = ctb(LUA_TSHRSTR)
    math_str = TString()
    math_str.tt = LUA_TSHRSTR
    math_str.data = b"math"
    math_str.shrlen = 4
    math_key.value_.gc = math_str
    
    math_val = TValue()
    math_val.tt_ = ctb(5)  # LUA_TTABLE with collectable
    math_val.value_.gc = math_table
    
    node = Node()
    node.i_key = TKey()
    node.i_key.value_ = math_key.value_
    node.i_key.tt_ = math_key.tt_
    node.i_key.next = 0
    node.i_val = math_val
    env.node.append(node)
    env.lsizenode = len(env.node)
