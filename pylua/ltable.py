# -*- coding: utf-8 -*-
"""
ltable.py - Lua Tables (Hash)
=============================
Source: ltable.h/ltable.c (lua-5.3.6/src/ltable.h, ltable.c)

Lua tables (hash)
See Copyright Notice in lua.h

Implementation of tables (aka arrays, objects, or hash tables).
Tables keep its elements in two parts: an array part and a hash part.
"""

from typing import TYPE_CHECKING, Optional
import math
import struct

from .lobject import (
    TValue, Value, TString, Table, Node, TKey,
    ttisnil, ttisinteger, ttisfloat, ttisstring, ttisboolean,
    ttisnumber, ttistable, ttisfunction, ttisLclosure, ttisCclosure,
    ivalue, fltvalue, bvalue, svalue, hvalue, pvalue, fvalue, gcvalue,
    setivalue, setfltvalue, setnilvalue, setobj, setobj2s,
    ttype, novariant, val_, tsvalue, getstr,
    lmod, twoto, sizenode,
    LUA_TNUMINT, LUA_TNUMFLT, LUA_TSHRSTR, LUA_TLNGSTR,
    LUA_TBOOLEAN, LUA_TLIGHTUSERDATA, LUA_TLCF,
    ctb,
)
from .llimits import cast_int, cast_byte, lua_assert, MAX_INT
from .luaconf import LUA_MAXINTEGER

if TYPE_CHECKING:
    from .lstate import LuaState

# =============================================================================
# ltable.c:42-55 - Maximum Sizes
# =============================================================================

# ltable.c:46-47
MAXABITS = 31  # sizeof(int) * 8 - 1
MAXASIZE = 1 << MAXABITS

# ltable.c:55
MAXHBITS = MAXABITS - 1

# =============================================================================
# ltable.h:13-15 - Node Access Macros
# =============================================================================

def gnode(t: Table, i: int) -> Node:
    """ltable.h:13 - #define gnode(t,i) (&(t)->node[i])"""
    if t.node and 0 <= i < len(t.node):
        return t.node[i]
    # Return a dummy nil node for out of bounds
    return Node()


def gval(n: Node) -> TValue:
    """ltable.h:14 - #define gval(n) (&(n)->i_val)"""
    return n.i_val


def gnext(n: Node) -> int:
    """ltable.h:15 - #define gnext(n) ((n)->i_key.nk.next)"""
    return n.i_key.next


def gkey(n: Node) -> TValue:
    """ltable.h:19 - cast(const TValue*, (&(n)->i_key.tvk))
    Create TValue from TKey for comparison
    """
    tv = TValue()
    tv.tt_ = n.i_key.tt_
    tv.value_ = n.i_key.value_
    return tv


# =============================================================================
# ltable.c:58-72 - Hash Macros
# =============================================================================

def hashpow2(t: Table, n: int) -> int:
    """ltable.c:58 - #define hashpow2(t,n) (gnode(t, lmod((n), sizenode(t))))
    Returns the index of the node.
    """
    size = sizenode(t)
    if size == 0:
        return 0
    return lmod(n, size)


def hashstr(t: Table, ts: TString) -> int:
    """ltable.c:60 - #define hashstr(t,str) hashpow2(t, (str)->hash)"""
    return hashpow2(t, ts.hash)


def hashboolean(t: Table, p: int) -> int:
    """ltable.c:61 - #define hashboolean(t,p) hashpow2(t, p)"""
    return hashpow2(t, p)


def hashint(t: Table, i: int) -> int:
    """ltable.c:62 - #define hashint(t,i) hashpow2(t, i)"""
    # Handle negative integers properly
    if i < 0:
        i = i & 0xFFFFFFFFFFFFFFFF  # Convert to unsigned 64-bit
    return hashpow2(t, i)


def hashmod(t: Table, n: int) -> int:
    """ltable.c:69 - #define hashmod(t,n) (gnode(t, ((n) % ((sizenode(t)-1)|1))))"""
    size = sizenode(t)
    if size == 0:
        return 0
    return n % ((size - 1) | 1)


def point2uint(p) -> int:
    """Convert pointer to unsigned int for hashing"""
    return id(p) & 0xFFFFFFFF


def hashpointer(t: Table, p) -> int:
    """ltable.c:72 - #define hashpointer(t,p) hashmod(t, point2uint(p))"""
    return hashmod(t, point2uint(p))


# =============================================================================
# ltable.c:97-109 - l_hashfloat
# =============================================================================

def l_hashfloat(n: float) -> int:
    """ltable.c:97-109 - Hash for floating-point numbers"""
    if math.isnan(n) or math.isinf(n):
        return 0
    
    # frexp returns (mantissa, exponent) where mantissa is in [0.5, 1.0)
    mantissa, exp = math.frexp(n)
    
    # n = frexp(n, &i) * -INT_MIN
    INT_MIN = -2147483648
    ni = mantissa * -INT_MIN
    
    try:
        ni_int = int(ni)
        u = (exp & 0xFFFFFFFF) + (ni_int & 0xFFFFFFFF)
        INT_MAX = 2147483647
        if u <= INT_MAX:
            return cast_int(u)
        else:
            return cast_int(~u & 0xFFFFFFFF)
    except (ValueError, OverflowError):
        return 0


# =============================================================================
# lstring.c:49-55 - luaS_hash
# =============================================================================

LUAI_HASHLIMIT = 5

def luaS_hash(s: bytes, seed: int = 0) -> int:
    """lstring.c:49-55 - Compute hash for string"""
    l = len(s)
    h = seed ^ l
    step = (l >> LUAI_HASHLIMIT) + 1
    
    while l >= step:
        h ^= ((h << 5) + (h >> 2) + cast_byte(s[l - 1])) & 0xFFFFFFFF
        l -= step
    
    return h & 0xFFFFFFFF


def luaS_hashlongstr(ts: TString) -> int:
    """lstring.c:58-65 - Hash for long strings"""
    if ts.extra == 0:  # no hash computed yet
        ts.hash = luaS_hash(ts.data, ts.hash)
        ts.extra = 1
    return ts.hash


# =============================================================================
# ltable.c:117-137 - mainposition
# =============================================================================

def mainposition(t: Table, key: TValue) -> int:
    """
    ltable.c:117-137 - mainposition
    
    Returns the index of the 'main' position of an element in a table
    (that is, the index of its hash value).
    """
    tt = ttype(key)
    
    if tt == LUA_TNUMINT:
        return hashint(t, ivalue(key))
    elif tt == LUA_TNUMFLT:
        return hashmod(t, l_hashfloat(fltvalue(key)))
    elif tt == LUA_TSHRSTR:
        ts = tsvalue(key)
        # Ensure hash is computed
        if ts.hash == 0 and len(ts.data) > 0:
            ts.hash = luaS_hash(ts.data)
        return hashstr(t, ts)
    elif tt == LUA_TLNGSTR:
        return hashpow2(t, luaS_hashlongstr(tsvalue(key)))
    elif tt == LUA_TBOOLEAN:
        return hashboolean(t, bvalue(key))
    elif tt == LUA_TLIGHTUSERDATA:
        return hashpointer(t, pvalue(key))
    elif tt == LUA_TLCF:
        return hashpointer(t, fvalue(key))
    else:
        # For other GC objects
        gc = gcvalue(key)
        if gc is not None:
            return hashpointer(t, gc)
        return 0


# =============================================================================
# ltable.c:144-151 - arrayindex
# =============================================================================

def arrayindex(key: TValue) -> int:
    """
    ltable.c:144-151 - arrayindex
    
    Returns the index for 'key' if 'key' is an appropriate key to live in
    the array part of the table, 0 otherwise.
    """
    if ttisinteger(key):
        k = ivalue(key)
        if 0 < k and k <= MAXASIZE:
            return cast_int(k)
    return 0


# =============================================================================
# ltable.c:159-183 - findindex
# =============================================================================

def findindex(L: 'LuaState', t: Table, key: TValue) -> int:
    """
    ltable.c:159-183 - findindex
    
    Returns the index of a 'key' for table traversals.
    First goes all elements in the array part, then elements in the hash part.
    The beginning of a traversal is signaled by 0.
    
    Note: PyLua uses simple list storage for hash nodes, so we use
    linear search instead of hash chain traversal.
    """
    if ttisnil(key):
        return 0  # first iteration
    
    i = arrayindex(key)
    if i != 0 and i <= t.sizearray:
        # key is inside array part
        return i
    else:
        # Search in hash part - linear scan since PyLua doesn't use hash chains
        if not t.node:
            raise RuntimeError("invalid key to 'next'")
        
        for n_idx, n in enumerate(t.node):
            # Skip nil keys
            if n.i_key.tt_ == 0:
                continue
            
            node_key = gkey(n)
            
            # Check if this is our key
            if luaV_rawequalobj(node_key, key):
                # key index in hash table + array size + 1
                return (n_idx + 1) + t.sizearray
        
        raise RuntimeError("invalid key to 'next'")


# =============================================================================
# lvm.c:406-427 - luaV_rawequalobj
# =============================================================================

def luaV_rawequalobj(t1: TValue, t2: TValue) -> bool:
    """
    lvm.c:406-427 - luaV_rawequalobj
    
    Raw equality without metamethods
    """
    if ttype(t1) != ttype(t2):
        # Different types means not equal (with some exceptions for numbers)
        if ttisnumber(t1) and ttisnumber(t2):
            # Compare as numbers
            from .lvm import luaV_equalobj
            return luaV_equalobj(None, t1, t2)
        return False
    
    # Same type
    tt = ttype(t1)
    
    if tt == LUA_TNUMINT:
        return ivalue(t1) == ivalue(t2)
    elif tt == LUA_TNUMFLT:
        return fltvalue(t1) == fltvalue(t2)
    elif tt == LUA_TBOOLEAN:
        return bvalue(t1) == bvalue(t2)
    elif tt == LUA_TSHRSTR:
        ts1 = tsvalue(t1)
        ts2 = tsvalue(t2)
        return ts1.data == ts2.data
    elif tt == LUA_TLNGSTR:
        ts1 = tsvalue(t1)
        ts2 = tsvalue(t2)
        return luaS_eqlngstr(ts1, ts2)
    elif ttisnil(t1):
        return True  # nil == nil
    else:
        # For other types (tables, functions, etc.), compare by reference
        return gcvalue(t1) is gcvalue(t2)


def luaS_eqlngstr(a: TString, b: TString) -> bool:
    """lstring.c:40-46 - equality for long strings"""
    if a is b:
        return True
    if a.lnglen != b.lnglen:
        return False
    return a.data == b.data


# =============================================================================
# ltable.c:186-203 - luaH_next
# =============================================================================

def luaH_next(L: 'LuaState', t: Table, key: TValue) -> int:
    """
    ltable.c:186-203 - luaH_next
    
    Traverse table returning next key-value pair.
    Returns number of values pushed (0 if end of table, 2 otherwise).
    key is updated in place to the new key.
    """
    i = findindex(L, t, key)
    
    # Try array part first
    while i < t.sizearray:
        if t.array and i < len(t.array) and not ttisnil(t.array[i]):
            # Found a non-nil value in array
            # Set key to i+1 (1-indexed)
            setivalue(key, i + 1)
            # Push value - key is at top-1, value at top
            setobj2s(L, L.stack[L.top], t.array[i])
            L.top += 1
            return 1
        i += 1
    
    # Try hash part
    hash_idx = i - t.sizearray
    node_count = len(t.node) if t.node else 0
    
    while hash_idx < node_count:
        n = t.node[hash_idx]
        if not ttisnil(gval(n)):
            # Found a non-nil value in hash
            # Set key from node
            node_key = gkey(n)
            setobj(L, key, node_key)
            # Push value
            setobj2s(L, L.stack[L.top], gval(n))
            L.top += 1
            return 1
        hash_idx += 1
    
    return 0  # no more elements


# =============================================================================
# ltable.c - luaH_get, luaH_getint, luaH_getstr, luaH_getshortstr
# =============================================================================

def luaH_getint(t: Table, key: int) -> Optional[TValue]:
    """ltable.c:592-612 - Get value for integer key"""
    # Check array part first
    if 1 <= key <= t.sizearray:
        if t.array and key <= len(t.array):
            return t.array[key - 1]
    
    # Search hash part
    if not t.node or len(t.node) == 0:
        return None
    
    # Create a TValue for the key
    key_tv = TValue()
    setivalue(key_tv, key)
    
    n_idx = mainposition(t, key_tv)
    
    while True:
        if n_idx < 0 or n_idx >= len(t.node):
            break
        
        n = t.node[n_idx]
        node_key = gkey(n)
        
        if ttisinteger(node_key) and ivalue(node_key) == key:
            return gval(n)
        
        nx = gnext(n)
        if nx == 0:
            break
        n_idx += nx
    
    return None


def luaH_getshortstr(t: Table, key: TString) -> Optional[TValue]:
    """ltable.c:569-589 - Get value for short string key"""
    if not t.node or len(t.node) == 0:
        return None
    
    # Create TValue for key
    key_tv = TValue()
    key_tv.tt_ = ctb(LUA_TSHRSTR)
    key_tv.value_.gc = key
    
    n_idx = hashstr(t, key)
    
    while True:
        if n_idx < 0 or n_idx >= len(t.node):
            break
        
        n = t.node[n_idx]
        node_key = gkey(n)
        
        if ttisstring(node_key):
            node_ts = tsvalue(node_key)
            if node_ts.data == key.data:
                return gval(n)
        
        nx = gnext(n)
        if nx == 0:
            break
        n_idx += nx
    
    return None


def luaH_getstr(t: Table, key: TString) -> Optional[TValue]:
    """ltable.c:615-621 - Get value for string key"""
    if key.tt == LUA_TSHRSTR:
        return luaH_getshortstr(t, key)
    else:
        # Long string
        key_tv = TValue()
        key_tv.tt_ = ctb(LUA_TLNGSTR)
        key_tv.value_.gc = key
        return luaH_get(t, key_tv)


def luaH_get(t: Table, key: TValue) -> Optional[TValue]:
    """ltable.c:624-648 - Generic get"""
    if ttisnil(key):
        return None
    
    tt = ttype(key)
    
    if tt == LUA_TSHRSTR:
        return luaH_getshortstr(t, tsvalue(key))
    elif tt == LUA_TNUMINT:
        return luaH_getint(t, ivalue(key))
    elif tt == LUA_TNUMFLT:
        # Check if it's really an integer
        fv = fltvalue(key)
        if fv == int(fv):
            return luaH_getint(t, int(fv))
    
    # Generic hash lookup
    if not t.node or len(t.node) == 0:
        return None
    
    n_idx = mainposition(t, key)
    
    while True:
        if n_idx < 0 or n_idx >= len(t.node):
            break
        
        n = t.node[n_idx]
        if luaV_rawequalobj(gkey(n), key):
            return gval(n)
        
        nx = gnext(n)
        if nx == 0:
            break
        n_idx += nx
    
    return None
