# -*- coding: utf-8 -*-
"""
lbaselib.py - Lua Basic Library
===============================
Source: lbaselib.c (lua-5.3.6/src/lbaselib.c)

Basic library for Lua
See Copyright Notice in lua.h
"""

from typing import TYPE_CHECKING, Optional

from .lua import (
    LUA_TNIL, LUA_TBOOLEAN, LUA_TLIGHTUSERDATA, LUA_TNUMBER,
    LUA_TSTRING, LUA_TTABLE, LUA_TFUNCTION, LUA_TUSERDATA, LUA_TTHREAD,
    lua_typename,
)
from .lobject import (
    TValue, TString, Table, CClosure, LClosure,
    ttisnil, ttisboolean, ttisnumber, ttisinteger, ttisfloat, ttisstring,
    ttistable, ttisfunction, ttisLclosure, ttisCclosure, ttnov,
    ivalue, fltvalue, bvalue, svalue, hvalue,
    setivalue, setfltvalue, setnilvalue, setbvalue, setobj, setobj2s,
    LUA_TSHRSTR, LUA_TLNGSTR, LUA_TCCL, ctb,
)
from .llimits import lua_assert

if TYPE_CHECKING:
    from .lstate import LuaState


# =============================================================================
# lbaselib.c:26-50 - luaB_print
# =============================================================================

def luaB_print(L: 'LuaState') -> int:
    """
    lbaselib.c:26-50 - print (...)
    
    Receives any number of arguments and prints their values to stdout,
    using tostring to convert each argument to a string.
    
    static int luaB_print (lua_State *L)
    
    Source: lbaselib.c:26-50
    """
    ci = L.ci
    base = ci.base if ci else 1
    nargs = L.top - base
    
    parts = []
    for i in range(nargs):
        v = L.stack[base + i]
        s = luaB_tostring_value(L, v)
        parts.append(s)
    
    print("\t".join(parts))
    return 0


# =============================================================================
# lbaselib.c:52-68 - luaB_tonumber
# =============================================================================

def luaB_tonumber(L: 'LuaState') -> int:
    """
    lbaselib.c:52-68 - tonumber (e [, base])
    
    When called with no base, tonumber tries to convert its argument to a number.
    
    static int luaB_tonumber (lua_State *L)
    
    Source: lbaselib.c:52-68
    """
    ci = L.ci
    base_idx = ci.base if ci else 1
    nargs = L.top - base_idx
    
    if nargs < 1:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    v = L.stack[base_idx]
    result = L.stack[L.top]
    
    # Check for base argument
    num_base = 10
    if nargs >= 2:
        base_v = L.stack[base_idx + 1]
        if ttisinteger(base_v):
            num_base = ivalue(base_v)
    
    if ttisinteger(v):
        setivalue(result, ivalue(v))
    elif ttisfloat(v):
        setfltvalue(result, fltvalue(v))
    elif ttisstring(v):
        try:
            s = svalue(v).decode('utf-8').strip()
            if num_base == 10:
                if '.' in s or 'e' in s.lower() or 'E' in s:
                    setfltvalue(result, float(s))
                else:
                    # Try hex
                    if s.startswith('0x') or s.startswith('0X'):
                        setivalue(result, int(s, 16))
                    else:
                        setivalue(result, int(s))
            else:
                setivalue(result, int(s, num_base))
        except (ValueError, UnicodeDecodeError):
            setnilvalue(result)
    else:
        setnilvalue(result)
    
    L.top += 1
    return 1


# =============================================================================
# lbaselib.c:128-137 - luaB_tostring
# =============================================================================

def luaB_tostring(L: 'LuaState') -> int:
    """
    lbaselib.c:128-137 - tostring (v)
    
    Receives a value of any type and converts it to a string.
    
    static int luaB_tostring (lua_State *L)
    
    Source: lbaselib.c:128-137
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    v = L.stack[base]
    result_str = luaB_tostring_value(L, v)
    
    # Push result string
    result = L.stack[L.top]
    result_ts = TString()
    result_ts.tt = LUA_TSHRSTR
    result_ts.data = result_str.encode('utf-8')
    result_ts.shrlen = len(result_ts.data)
    result.value_.gc = result_ts
    result.tt_ = ctb(LUA_TSHRSTR)
    L.top += 1
    return 1


def luaB_tostring_value(L: 'LuaState', v: TValue) -> str:
    """
    Helper function to convert a TValue to string representation.
    Matches Lua's tostring behavior.
    """
    if ttisnil(v):
        return "nil"
    
    if ttisboolean(v):
        return "true" if bvalue(v) else "false"
    
    if ttisinteger(v):
        return str(ivalue(v))
    
    if ttisfloat(v):
        import math
        n = fltvalue(v)
        # Handle negative zero specially
        if n == 0:
            if math.copysign(1.0, n) < 0:
                return "-0"
            return "0"
        # Lua formats integers as X.0
        if n == int(n) and abs(n) < 1e14:
            return str(float(n))
        return str(n)
    
    if ttisstring(v):
        return svalue(v).decode('utf-8', errors='replace')
    
    # Check for __tostring metamethod for tables
    if ttistable(v):
        tab = hvalue(v)
        if tab.metatable is not None:
            # Look for __tostring in metatable
            from .lobject import TString, LUA_TSHRSTR
            from .lvm import _luaH_get
            # Create __tostring key
            tostring_key = TValue()
            tostring_key.tt_ = ctb(LUA_TSHRSTR)
            ts = TString()
            ts.tt = LUA_TSHRSTR
            ts.data = b"__tostring"
            ts.shrlen = 10
            tostring_key.value_.gc = ts
            
            tm = _luaH_get(tab.metatable, tostring_key)
            if tm is not None and not ttisnil(tm) and ttisfunction(tm):
                # Call __tostring metamethod
                from .ltm import luaT_callTM
                # Ensure stack space
                while len(L.stack) <= L.top + 3:
                    L.stack.append(TValue())
                # Call metamethod
                result_slot = L.top
                luaT_callTM(L, tm, v, v, L.stack[result_slot], 1)
                # Get result
                if ttisstring(L.stack[result_slot]):
                    return svalue(L.stack[result_slot]).decode('utf-8', errors='replace')
        return f"table: 0x{id(hvalue(v)):x}"
    
    if ttisfunction(v):
        return f"function: 0x{id(v.value_.gc):x}"
    
    # Other types
    tt = v.tt_ & 0x0F
    return f"<{lua_typename(tt)}: 0x{id(v.value_.gc):x}>"


# =============================================================================
# lbaselib.c:236-242 - luaB_type
# =============================================================================

def luaB_type(L: 'LuaState') -> int:
    """
    lbaselib.c:236-242 - type (v)
    
    Returns the type of its only argument, coded as a string.
    
    static int luaB_type (lua_State *L)
    
    Source: lbaselib.c:236-242
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    v = L.stack[base]
    tt = v.tt_ & 0x0F
    type_name = lua_typename(tt)
    
    # Push result string
    result = L.stack[L.top]
    result_ts = TString()
    result_ts.tt = LUA_TSHRSTR
    result_ts.data = type_name.encode('utf-8')
    result_ts.shrlen = len(result_ts.data)
    result.value_.gc = result_ts
    result.tt_ = ctb(LUA_TSHRSTR)
    L.top += 1
    return 1


# =============================================================================
# lbaselib.c:139-157 - luaB_error
# =============================================================================

def luaB_error(L: 'LuaState') -> int:
    """
    lbaselib.c:139-157 - error (message [, level])
    
    Terminates the last protected function called and returns message
    as the error object.
    
    static int luaB_error (lua_State *L)
    
    Source: lbaselib.c:139-157
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top > base:
        v = L.stack[base]
        if ttisstring(v):
            msg = svalue(v).decode('utf-8', errors='replace')
        else:
            msg = luaB_tostring_value(L, v)
        raise RuntimeError(msg)
    else:
        raise RuntimeError("error")


# =============================================================================
# lbaselib.c:226-235 - luaB_next
# =============================================================================

def luaB_next(L: 'LuaState') -> int:
    """
    lbaselib.c:226-235 - next (table [, index])
    
    Source: lbaselib.c:226-235
    
    static int luaB_next (lua_State *L) {
      luaL_checktype(L, 1, LUA_TTABLE);
      lua_settop(L, 2);  /* create a 2nd argument if there isn't one */
      if (lua_next(L, 1))
        return 2;
      else {
        lua_pushnil(L);
        return 1;
      }
    }
    """
    from .ltable import luaH_next
    from .lobject import setobj2s
    
    ci = L.ci
    base = ci.base if ci else 1
    
    # luaL_checktype(L, 1, LUA_TTABLE)
    if L.top <= base or not ttistable(L.stack[base]):
        raise TypeError("bad argument #1 to 'next' (table expected)")
    
    t = hvalue(L.stack[base])
    
    # lua_settop(L, 2) - create a 2nd argument if there isn't one
    if L.top < base + 2:
        setnilvalue(L.stack[base + 1])
        L.top = base + 2
    
    # Get current key at position 2 (base + 1)
    key = L.stack[base + 1]
    
    # lua_next(L, 1) - calls luaH_next
    # luaH_next modifies key in place and pushes value
    result = luaH_next(L, t, key)
    
    if result > 0:
        # luaH_next already pushed the value, now push the key
        # Move key to proper return position
        key_copy = TValue()
        setobj(L, key_copy, key)
        
        # Stack now has: table, key, value (from luaH_next)
        # We need: key, value
        # Set return position
        setobj2s(L, L.stack[base], key_copy)  # key at return pos 1
        setobj2s(L, L.stack[base + 1], L.stack[L.top - 1])  # value at return pos 2
        L.top = base + 2
        return 2
    else:
        # lua_pushnil(L)
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1


# =============================================================================
# lbaselib.c:255-270 - luaB_pairs
# =============================================================================

def luaB_pairs(L: 'LuaState') -> int:
    """
    lbaselib.c:255-270 - pairs (t)
    
    If t has a metamethod __pairs, calls it with t as argument and returns
    the first three results. Otherwise, returns next, t, nil.
    
    static int luaB_pairs (lua_State *L)
    
    Source: lbaselib.c:255-270
    """
    from .ltm import TMS, luaT_gettmbyobj
    
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base:
        raise TypeError("bad argument #1 to 'pairs' (value expected)")
    
    t = L.stack[base]
    
    # Check for __pairs metamethod (Lua 5.2+)
    if ttistable(t):
        tab = hvalue(t)
        if tab.metatable is not None:
            from .lobject import TString, LUA_TSHRSTR
            from .lvm import _luaH_get
            # Create __pairs key
            pairs_key = TValue()
            pairs_key.tt_ = ctb(LUA_TSHRSTR)
            ts = TString()
            ts.tt = LUA_TSHRSTR
            ts.data = b"__pairs"
            ts.shrlen = 7
            pairs_key.value_.gc = ts
            
            tm = _luaH_get(tab.metatable, pairs_key)
            if tm is not None and not ttisnil(tm) and ttisfunction(tm):
                # Call metamethod: returns iterator, state, initial
                from .lobject import setobj
                setobj(L, L.stack[L.top], tm)
                L.top += 1
                setobj(L, L.stack[L.top], t)
                L.top += 1
                from .ldo import luaD_call
                luaD_call(L, L.top - 2, 3)
                return 3
    
    # Default: return next, t, nil
    # Push 'next' function
    next_closure = CClosure()
    next_closure.tt = LUA_TCCL
    next_closure.nupvalues = 0
    next_closure.f = luaB_next
    next_closure.upvalue = []
    from .lobject import setclCvalue
    setclCvalue(L, L.stack[L.top], next_closure)
    L.top += 1
    
    # Push table
    from .lobject import setobj
    setobj(L, L.stack[L.top], t)
    L.top += 1
    
    # Push nil
    setnilvalue(L.stack[L.top])
    L.top += 1
    
    return 3


# =============================================================================
# lbaselib.c:272-301 - luaB_ipairs
# =============================================================================

def ipairsaux(L: 'LuaState') -> int:
    """
    lbaselib.c:246-250 - Iterator function for ipairs
    
    static int ipairsaux (lua_State *L) {
        lua_Integer i = luaL_checkinteger(L, 2) + 1;
        lua_pushinteger(L, i);
        return (lua_geti(L, 1, i) == LUA_TNIL) ? 1 : 2;
    }
    
    Source: lbaselib.c:246-250
    """
    from .lobject import setobj, ttnov
    from .ltm import ttypename
    
    ci = L.ci
    base = ci.base if ci else 1
    
    t = L.stack[base]
    i = ivalue(L.stack[base + 1]) + 1
    
    # Push new index first
    setivalue(L.stack[L.top], i)
    L.top += 1
    
    # lua_geti(L, 1, i) - get t[i]
    if ttistable(t):
        tab = hvalue(t)
        if 1 <= i <= len(tab.array):
            v = tab.array[i - 1]
            if not ttisnil(v):
                setobj(L, L.stack[L.top], v)
                L.top += 1
                return 2
        # Index out of range or nil - return just the index (nil will be returned)
        L.top -= 1  # Remove the index we pushed
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    else:
        # Not a table - raise error with type info
        actual_type = ttypename(ttnov(t))
        raise TypeError(f"bad argument #1 to 'ipairs' (table expected, got {actual_type})")


def luaB_ipairs(L: 'LuaState') -> int:
    """
    lbaselib.c:257-266 - ipairs (t)
    
    Returns three values (an iterator function, the table, 0).
    Note: The given "table" may not be a table (lbaselib.c:255 comment)
    Type checking happens in ipairsaux when lua_geti is called.
    
    static int luaB_ipairs (lua_State *L)
    
    Source: lbaselib.c:257-266
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    # luaL_checkany(L, 1) - just check argument exists, not type
    if L.top <= base:
        raise TypeError("bad argument #1 to 'ipairs' (value expected)")
    
    t = L.stack[base]
    
    # Push ipairsaux function
    iter_closure = CClosure()
    iter_closure.tt = LUA_TCCL
    iter_closure.nupvalues = 0
    iter_closure.f = ipairsaux
    iter_closure.upvalue = []
    from .lobject import setclCvalue
    setclCvalue(L, L.stack[L.top], iter_closure)
    L.top += 1
    
    # Push table (or whatever value was passed)
    from .lobject import setobj
    setobj(L, L.stack[L.top], t)
    L.top += 1
    
    # Push 0 (initial index)
    setivalue(L.stack[L.top], 0)
    L.top += 1
    
    return 3


# =============================================================================
# lbaselib.c:195-205 - luaB_rawequal
# =============================================================================

def luaB_rawequal(L: 'LuaState') -> int:
    """
    lbaselib.c:195-205 - rawequal (v1, v2)
    
    Checks whether v1 is equal to v2, without invoking the __eq metamethod.
    
    static int luaB_rawequal (lua_State *L)
    
    Source: lbaselib.c:195-205
    """
    from .lvm import luaV_rawequalobj
    
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top < base + 2:
        setbvalue(L.stack[L.top], 0)
        L.top += 1
        return 1
    
    v1 = L.stack[base]
    v2 = L.stack[base + 1]
    
    result = luaV_rawequalobj(v1, v2)
    setbvalue(L.stack[L.top], 1 if result else 0)
    L.top += 1
    return 1


# =============================================================================
# lbaselib.c:207-217 - luaB_rawlen
# =============================================================================

def luaB_rawlen(L: 'LuaState') -> int:
    """
    lbaselib.c:207-217 - rawlen (v)
    
    Returns the length of the object v, which must be a table or a string,
    without invoking the __len metamethod.
    
    static int luaB_rawlen (lua_State *L)
    
    Source: lbaselib.c:207-217
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base:
        setivalue(L.stack[L.top], 0)
        L.top += 1
        return 1
    
    v = L.stack[base]
    
    if ttisstring(v):
        from .lobject import vslen
        setivalue(L.stack[L.top], vslen(v))
    elif ttistable(v):
        t = hvalue(v)
        # Count array part
        length = 0
        for i, elem in enumerate(t.array):
            if not ttisnil(elem):
                length = i + 1
        setivalue(L.stack[L.top], length)
    else:
        raise TypeError("bad argument #1 to 'rawlen' (table or string expected)")
    
    L.top += 1
    return 1


# =============================================================================
# lbaselib.c:219-227 - luaB_rawget
# =============================================================================

def luaB_rawget(L: 'LuaState') -> int:
    """
    lbaselib.c:219-227 - rawget (table, index)
    
    Gets the real value of table[index], without invoking the __index metamethod.
    
    static int luaB_rawget (lua_State *L)
    
    Source: lbaselib.c:219-227
    """
    from .lobject import setobj, setobj2s
    
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top < base + 2 or not ttistable(L.stack[base]):
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    t = hvalue(L.stack[base])
    key = L.stack[base + 1]
    
    # Use the same logic as _luaH_get from lvm.py
    from .lvm import _luaH_get
    result = _luaH_get(t, key)
    
    if result is not None:
        setobj(L, L.stack[L.top], result)
    else:
        setnilvalue(L.stack[L.top])
    
    L.top += 1
    return 1


# =============================================================================
# lbaselib.c:229-234 - luaB_rawset
# =============================================================================

def luaB_rawset(L: 'LuaState') -> int:
    """
    lbaselib.c:229-234 - rawset (table, index, value)
    
    Sets the real value of table[index] to value, without invoking the
    __newindex metamethod. Returns the table.
    
    static int luaB_rawset (lua_State *L)
    
    Source: lbaselib.c:229-234
    """
    from .lobject import setobj2s
    
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top < base + 3 or not ttistable(L.stack[base]):
        return 0
    
    t = hvalue(L.stack[base])
    key = L.stack[base + 1]
    val = L.stack[base + 2]
    
    # Use the same logic as _luaH_set from lvm.py
    from .lvm import _luaH_set
    _luaH_set(L, t, key, val)
    
    # Return the table
    setobj2s(L, L.stack[L.top], L.stack[base])
    L.top += 1
    return 1


# =============================================================================
# lbaselib.c:303-322 - luaB_select
# =============================================================================

def luaB_select(L: 'LuaState') -> int:
    """
    lbaselib.c:303-322 - select (index, ...)
    
    If index is a number, returns all arguments after argument number index;
    If index is the string "#", returns the total number of extra arguments.
    
    static int luaB_select (lua_State *L)
    
    Source: lbaselib.c:303-322
    """
    ci = L.ci
    base = ci.base if ci else 1
    nargs = L.top - base
    
    if nargs < 1:
        return 0
    
    idx = L.stack[base]
    
    if ttisstring(idx):
        s = svalue(idx).decode('utf-8')
        if s == "#":
            setivalue(L.stack[L.top], nargs - 1)
            L.top += 1
            return 1
    
    if ttisinteger(idx):
        i = ivalue(idx)
        if i < 0:
            i = nargs + i
        elif i > nargs - 1:
            i = nargs
        
        # Return all arguments from index i
        count = 0
        for j in range(i, nargs):
            from .lobject import setobj
            setobj(L, L.stack[L.top], L.stack[base + j])
            L.top += 1
            count += 1
        return count
    
    return 0


# =============================================================================
# lbaselib.c:324-344 - luaB_assert
# =============================================================================

def luaB_assert(L: 'LuaState') -> int:
    """
    lbaselib.c:324-344 - assert (v [, message])
    
    Calls error if the value of its argument is false.
    
    static int luaB_assert (lua_State *L)
    
    Source: lbaselib.c:324-344
    """
    from .lobject import l_isfalse
    
    ci = L.ci
    base = ci.base if ci else 1
    nargs = L.top - base
    
    if nargs < 1 or l_isfalse(L.stack[base]):
        msg = "assertion failed!"
        if nargs >= 2 and ttisstring(L.stack[base + 1]):
            msg = svalue(L.stack[base + 1]).decode('utf-8', errors='replace')
        raise RuntimeError(msg)
    
    # Return all arguments
    return nargs


# =============================================================================
# lbaselib.c:443-484 - luaB_pcall
# =============================================================================

def luaB_pcall(L: 'LuaState') -> int:
    """
    lbaselib.c:443-484 - pcall (f [, arg1, ...])
    
    Calls function f with the given arguments in protected mode.
    Returns status (true/false) plus results or error message.
    
    static int luaB_pcall (lua_State *L)
    
    Source: lbaselib.c:443-484
    """
    from .ldo import luaD_pcall, LuaError
    from .lobject import setobj
    
    ci = L.ci
    base = ci.base if ci else 1
    nargs = L.top - base
    
    if nargs < 1:
        # No function to call, return false
        setbvalue(L.stack[L.top], 0)
        L.top += 1
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 2
    
    # Get function and args
    func = L.stack[base]
    func_idx = base
    
    # Number of arguments to pass (excluding the function itself)
    nfunc_args = nargs - 1
    
    try:
        # Call in protected mode
        from .ldo import luaD_call
        
        # Shift function and args down to proper position
        # The function is at 'base', args at base+1..base+nfunc_args
        luaD_call(L, func_idx, -1)  # LUA_MULTRET
        
        # Success - prepend true
        # Move results down and insert true at the beginning
        nresults = L.top - func_idx
        
        # Shift results to make room for status
        for i in range(nresults - 1, -1, -1):
            setobj(L, L.stack[func_idx + i + 1], L.stack[func_idx + i])
        
        setbvalue(L.stack[func_idx], 1)  # true = success
        L.top = func_idx + nresults + 1
        
        return nresults + 1
        
    except (LuaError, RuntimeError, TypeError, Exception) as e:
        # Error occurred - return false, error_message
        error_msg = str(e)
        
        # Push false
        setbvalue(L.stack[func_idx], 0)
        
        # Push error message
        result_ts = TString()
        result_ts.tt = LUA_TSHRSTR
        result_ts.data = error_msg.encode('utf-8')
        result_ts.shrlen = len(result_ts.data)
        L.stack[func_idx + 1].value_.gc = result_ts
        L.stack[func_idx + 1].tt_ = ctb(LUA_TSHRSTR)
        
        L.top = func_idx + 2
        return 2


def luaB_xpcall(L: 'LuaState') -> int:
    """
    lbaselib.c:434-443 - xpcall (f, msgh [, arg1, ...])
    
    Calls function f in protected mode with error handler msgh.
    
    static int luaB_xpcall (lua_State *L)
    
    Source: lbaselib.c:434-443
    """
    from .ldo import LuaError, luaD_call
    from .lobject import setobj
    
    ci = L.ci
    base = ci.base if ci else 1
    nargs = L.top - base
    
    if nargs < 2:
        setbvalue(L.stack[L.top], 0)
        L.top += 1
        return 1
    
    func = L.stack[base]          # Function to call
    msgh = L.stack[base + 1]      # Error handler function
    
    # Check that msgh is a function
    if not ttisfunction(msgh):
        raise TypeError("bad argument #2 to 'xpcall' (function expected)")
    
    # Save error handler
    saved_msgh = TValue()
    setobj(L, saved_msgh, msgh)
    
    func_idx = base
    
    try:
        # Call the function
        luaD_call(L, func_idx, -1)
        
        # Success: return true, results...
        nresults = L.top - func_idx
        for i in range(nresults - 1, -1, -1):
            setobj(L, L.stack[func_idx + i + 1], L.stack[func_idx + i])
        
        setbvalue(L.stack[func_idx], 1)
        L.top = func_idx + nresults + 1
        return nresults + 1
        
    except (LuaError, RuntimeError, TypeError, Exception) as e:
        error_msg = str(e)
        
        # Call error handler with error message
        try:
            # Push error handler
            setobj(L, L.stack[func_idx], saved_msgh)
            L.top = func_idx + 1
            
            # Push error message as argument
            result_ts = TString()
            result_ts.tt = LUA_TSHRSTR
            result_ts.data = error_msg.encode('utf-8')
            result_ts.shrlen = len(result_ts.data)
            L.stack[L.top].value_.gc = result_ts
            L.stack[L.top].tt_ = ctb(LUA_TSHRSTR)
            L.top += 1
            
            # Call error handler
            luaD_call(L, func_idx, 1)
            
            # Get result from error handler
            handled_error = L.stack[func_idx]
            
            # Return false, handled_error
            setbvalue(L.stack[func_idx], 0)
            setobj(L, L.stack[func_idx + 1], handled_error)
            L.top = func_idx + 2
            return 2
            
        except Exception:
            # Error handler itself failed, just return original error
            setbvalue(L.stack[func_idx], 0)
            
            result_ts = TString()
            result_ts.tt = LUA_TSHRSTR
            result_ts.data = error_msg.encode('utf-8')
            result_ts.shrlen = len(result_ts.data)
            L.stack[func_idx + 1].value_.gc = result_ts
            L.stack[func_idx + 1].tt_ = ctb(LUA_TSHRSTR)
            
            L.top = func_idx + 2
            return 2


# =============================================================================
# lbaselib.c:486-515 - luaB_setmetatable
# =============================================================================

def luaB_setmetatable(L: 'LuaState') -> int:
    """
    lbaselib.c:486-515 - setmetatable (table, metatable)
    
    Sets the metatable for the given table.
    
    static int luaB_setmetatable (lua_State *L)
    
    Source: lbaselib.c:486-515
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top < base + 2 or not ttistable(L.stack[base]):
        return 0
    
    t = hvalue(L.stack[base])
    mt = L.stack[base + 1]
    
    if ttisnil(mt):
        t.metatable = None
    elif ttistable(mt):
        t.metatable = hvalue(mt)
    else:
        raise TypeError("bad argument #2 to 'setmetatable' (nil or table expected)")
    
    # Return the table
    from .lobject import setobj
    setobj(L, L.stack[L.top], L.stack[base])
    L.top += 1
    return 1


# =============================================================================
# lbaselib.c:517-530 - luaB_getmetatable
# =============================================================================

def luaB_getmetatable(L: 'LuaState') -> int:
    """
    lbaselib.c:517-530 - getmetatable (object)
    
    Returns the metatable of the given object.
    
    static int luaB_getmetatable (lua_State *L)
    
    Source: lbaselib.c:517-530
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    v = L.stack[base]
    
    if ttistable(v):
        t = hvalue(v)
        if t.metatable:
            from .lobject import sethvalue
            sethvalue(L, L.stack[L.top], t.metatable)
        else:
            setnilvalue(L.stack[L.top])
    else:
        setnilvalue(L.stack[L.top])
    
    L.top += 1
    return 1


# =============================================================================
# Base Library Registration
# =============================================================================

# Base library functions table
base_funcs = {
    "print": luaB_print,
    "tostring": luaB_tostring,
    "tonumber": luaB_tonumber,
    "type": luaB_type,
    "error": luaB_error,
    "assert": luaB_assert,
    "pcall": luaB_pcall,
    "xpcall": luaB_xpcall,
    "rawequal": luaB_rawequal,
    "rawlen": luaB_rawlen,
    "rawget": luaB_rawget,
    "rawset": luaB_rawset,
    "select": luaB_select,
    "setmetatable": luaB_setmetatable,
    "getmetatable": luaB_getmetatable,
    "next": luaB_next,
    "pairs": luaB_pairs,
    "ipairs": luaB_ipairs,
}


def luaopen_base(L: 'LuaState', env: 'Table') -> None:
    """
    lbaselib.c:532-558 - Open base library
    
    Registers all base library functions in the given environment table.
    
    LUAMOD_API int luaopen_base (lua_State *L)
    
    Source: lbaselib.c:532-558
    """
    from .lobject import Node, TKey, TValue, setclCvalue
    
    for name, func in base_funcs.items():
        # Create CClosure
        closure = CClosure()
        closure.tt = LUA_TCCL
        closure.nupvalues = 0
        closure.f = func
        closure.upvalue = []
        
        # Create key
        key = TValue()
        key.tt_ = ctb(LUA_TSHRSTR)
        key_str = TString()
        key_str.tt = LUA_TSHRSTR
        key_str.data = name.encode('utf-8')
        key_str.shrlen = len(key_str.data)
        key.value_.gc = key_str
        
        # Create value
        val = TValue()
        setclCvalue(L, val, closure)
        
        # Add to table
        node = Node()
        node.i_key = TKey()
        node.i_key.value_ = key.value_
        node.i_key.tt_ = key.tt_
        node.i_key.next = 0
        node.i_val = val
        env.node.append(node)
    
    # Add _G pointing to env itself
    from .lua import LUA_TTABLE
    key = TValue()
    key.tt_ = ctb(LUA_TSHRSTR)
    key_str = TString()
    key_str.tt = LUA_TSHRSTR
    key_str.data = b"_G"
    key_str.shrlen = 2
    key.value_.gc = key_str
    
    val = TValue()
    val.tt_ = ctb(LUA_TTABLE)
    val.value_.gc = env
    
    node = Node()
    node.i_key = TKey()
    node.i_key.value_ = key.value_
    node.i_key.tt_ = key.tt_
    node.i_key.next = 0
    node.i_val = val
    env.node.append(node)
    
    # Add _VERSION
    key = TValue()
    key.tt_ = ctb(LUA_TSHRSTR)
    key_str = TString()
    key_str.tt = LUA_TSHRSTR
    key_str.data = b"_VERSION"
    key_str.shrlen = 8
    key.value_.gc = key_str
    
    val = TValue()
    val.tt_ = ctb(LUA_TSHRSTR)
    val_str = TString()
    val_str.tt = LUA_TSHRSTR
    val_str.data = b"Lua 5.3"
    val_str.shrlen = 7
    val.value_.gc = val_str
    
    node = Node()
    node.i_key = TKey()
    node.i_key.value_ = key.value_
    node.i_key.tt_ = key.tt_
    node.i_key.next = 0
    node.i_val = val
    env.node.append(node)
    
    env.lsizenode = len(env.node)
