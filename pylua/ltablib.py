# -*- coding: utf-8 -*-
"""
ltablib.py - Table Library
==========================
Source: ltablib.c (lua-5.3.6/src/ltablib.c)

Table manipulation library.
"""

from typing import TYPE_CHECKING, List

from .lobject import (
    TValue, TString, CClosure, Table, Node, TKey, Value,
    ttisstring, ttisinteger, ttisfloat, ttisnil, ttistable, ttisfunction,
    svalue, ivalue, fltvalue, hvalue,
    setnilvalue, setobj, setobj2s, val_,
    LUA_TCCL, LUA_TSHRSTR, LUA_TNUMINT, ctb,
)
from .lua import LUA_TTABLE

if TYPE_CHECKING:
    from .lstate import LuaState


def tab_insert(L: 'LuaState') -> int:
    """table.insert(list, [pos,] value) - ltablib.c:79-103 tinsert"""
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base or not ttistable(L.stack[base]):
        return 0
    
    t = hvalue(L.stack[base])
    e = len(t.array) + 1  # First empty element (1-based)
    
    nargs = L.top - base
    if nargs == 2:
        # table.insert(t, value) - insert at end
        pos = e
        val = L.stack[base + 1]
    elif nargs >= 3:
        # table.insert(t, pos, value)
        pos = ivalue(L.stack[base + 1]) if ttisinteger(L.stack[base + 1]) else 1
        val = L.stack[base + 2]
        
        # Expand array to hold new element
        while len(t.array) < e:
            t.array.append(TValue())
        
        # Move up elements: for (i = e; i > pos; i--) t[i] = t[i-1]
        for i in range(e, pos, -1):
            setobj(L, t.array[i - 1], t.array[i - 2])
    else:
        return 0
    
    # Insert value at position: t[pos] = v
    while len(t.array) < pos:
        t.array.append(TValue())
    t.sizearray = len(t.array)
    setobj(L, t.array[pos - 1], val)
    
    return 0


def tab_remove(L: 'LuaState') -> int:
    """table.remove(list [, pos])"""
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base or not ttistable(L.stack[base]):
        return 0
    
    t = hvalue(L.stack[base])
    size = len(t.array)
    
    if size == 0:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    pos = size  # Default: remove last
    if L.top > base + 1 and ttisinteger(L.stack[base + 1]):
        pos = ivalue(L.stack[base + 1])
    
    if pos < 1 or pos > size:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    # Copy removed element
    setobj(L, L.stack[L.top], t.array[pos - 1])
    L.top += 1
    
    # Shift elements
    for i in range(pos - 1, size - 1):
        setobj(L, t.array[i], t.array[i + 1])
    
    # Remove last element
    if size > 0:
        setnilvalue(t.array[size - 1])
        t.array.pop()
        t.sizearray = len(t.array)
    
    return 1


def tab_concat(L: 'LuaState') -> int:
    """table.concat(list [, sep [, i [, j]]])"""
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base or not ttistable(L.stack[base]):
        _push_string(L, b"")
        return 1
    
    t = hvalue(L.stack[base])
    
    sep = b""
    if L.top > base + 1 and ttisstring(L.stack[base + 1]):
        sep = svalue(L.stack[base + 1])
    
    i = 1
    if L.top > base + 2 and ttisinteger(L.stack[base + 2]):
        i = ivalue(L.stack[base + 2])
    
    j = len(t.array)
    if L.top > base + 3 and ttisinteger(L.stack[base + 3]):
        j = ivalue(L.stack[base + 3])
    
    parts = []
    for k in range(i - 1, j):
        if k >= 0 and k < len(t.array):
            v = t.array[k]
            if ttisstring(v):
                parts.append(svalue(v))
            elif ttisinteger(v):
                parts.append(str(ivalue(v)).encode('utf-8'))
            elif ttisfloat(v):
                parts.append(str(fltvalue(v)).encode('utf-8'))
    
    _push_string(L, sep.join(parts))
    return 1


def tab_sort(L: 'LuaState') -> int:
    """table.sort(list [, comp])"""
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base or not ttistable(L.stack[base]):
        return 0
    
    t = hvalue(L.stack[base])
    
    # Check for comparison function
    comp_func = None
    if L.top > base + 1 and ttisfunction(L.stack[base + 1]):
        comp_func = L.stack[base + 1]
    
    # Simple sort (no custom comparator for now)
    if comp_func is None:
        # Use default comparison
        def get_key(v):
            if ttisinteger(v):
                return (0, ivalue(v))
            elif ttisfloat(v):
                return (0, fltvalue(v))
            elif ttisstring(v):
                return (1, svalue(v))
            return (2, 0)
        
        indices = list(range(len(t.array)))
        indices.sort(key=lambda i: get_key(t.array[i]))
        
        new_array = [TValue() for _ in range(len(t.array))]
        for new_idx, old_idx in enumerate(indices):
            setobj(L, new_array[new_idx], t.array[old_idx])
        t.array = new_array
    else:
        # Custom comparator sort using Lua function
        def lua_compare(a, b):
            # Call comparison function
            from .ldo import luaD_call
            save_top = L.top
            setobj(L, L.stack[L.top], comp_func)
            setobj(L, L.stack[L.top + 1], a)
            setobj(L, L.stack[L.top + 2], b)
            L.top += 3
            luaD_call(L, save_top, 1)
            result = L.stack[save_top]
            L.top = save_top
            return not (ttisnil(result) or (hasattr(result.value_, 'b') and result.value_.b == 0))
        
        # Simple bubble sort for custom comparator
        n = len(t.array)
        for i in range(n):
            for j in range(0, n - i - 1):
                if not lua_compare(t.array[j], t.array[j + 1]):
                    # Swap
                    temp = TValue()
                    setobj(L, temp, t.array[j])
                    setobj(L, t.array[j], t.array[j + 1])
                    setobj(L, t.array[j + 1], temp)
    
    return 0


def tab_pack(L: 'LuaState') -> int:
    """table.pack(...)"""
    ci = L.ci
    base = ci.base if ci else 1
    
    n = L.top - base
    
    # Create table
    t = Table()
    t.tt = LUA_TTABLE
    t.metatable = None
    t.array = [TValue() for _ in range(n)]
    t.sizearray = n
    t.node = []
    t.flags = 0
    t.lsizenode = 0
    
    # Copy values
    for i in range(n):
        setobj(L, t.array[i], L.stack[base + i])
    
    # Add 'n' field
    node = Node()
    node.i_key = TKey()
    node.i_key.value_ = Value()
    ts = TString()
    ts.tt = LUA_TSHRSTR
    ts.data = b"n"
    ts.shrlen = 1
    node.i_key.value_.gc = ts
    node.i_key.tt_ = ctb(LUA_TSHRSTR)
    node.i_key.next = 0
    node.i_val = TValue()
    node.i_val.tt_ = LUA_TNUMINT
    node.i_val.value_.i = n
    t.node.append(node)
    
    # Push result
    result = L.stack[L.top]
    result.tt_ = ctb(LUA_TTABLE)
    result.value_.gc = t
    L.top += 1
    
    return 1


def tab_unpack(L: 'LuaState') -> int:
    """table.unpack(list [, i [, j]])"""
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base or not ttistable(L.stack[base]):
        return 0
    
    t = hvalue(L.stack[base])
    
    i = 1
    if L.top > base + 1 and ttisinteger(L.stack[base + 1]):
        i = ivalue(L.stack[base + 1])
    
    j = len(t.array)
    if L.top > base + 2 and ttisinteger(L.stack[base + 2]):
        j = ivalue(L.stack[base + 2])
    
    count = 0
    for k in range(i - 1, j):
        if k >= 0 and k < len(t.array):
            setobj(L, L.stack[L.top], t.array[k])
        else:
            setnilvalue(L.stack[L.top])
        L.top += 1
        count += 1
    
    return count


def tab_move(L: 'LuaState') -> int:
    """table.move(a1, f, e, t [, a2])"""
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base or not ttistable(L.stack[base]):
        return 0
    
    a1 = hvalue(L.stack[base])
    
    f = ivalue(L.stack[base + 1]) if L.top > base + 1 and ttisinteger(L.stack[base + 1]) else 1
    e = ivalue(L.stack[base + 2]) if L.top > base + 2 and ttisinteger(L.stack[base + 2]) else 1
    t_pos = ivalue(L.stack[base + 3]) if L.top > base + 3 and ttisinteger(L.stack[base + 3]) else 1
    
    a2 = a1
    if L.top > base + 4 and ttistable(L.stack[base + 4]):
        a2 = hvalue(L.stack[base + 4])
    
    # Copy elements
    count = e - f + 1
    if count > 0:
        # Ensure destination has space
        dest_end = t_pos + count - 1
        while len(a2.array) < dest_end:
            a2.array.append(TValue())
        a2.sizearray = len(a2.array)
        
        # Copy (handle overlap by direction)
        if t_pos <= f or a1 != a2:
            for i in range(count):
                src_idx = f + i - 1
                dst_idx = t_pos + i - 1
                if 0 <= src_idx < len(a1.array):
                    setobj(L, a2.array[dst_idx], a1.array[src_idx])
                else:
                    setnilvalue(a2.array[dst_idx])
        else:
            for i in range(count - 1, -1, -1):
                src_idx = f + i - 1
                dst_idx = t_pos + i - 1
                if 0 <= src_idx < len(a1.array):
                    setobj(L, a2.array[dst_idx], a1.array[src_idx])
                else:
                    setnilvalue(a2.array[dst_idx])
    
    # Return destination table
    result = L.stack[L.top]
    result.tt_ = ctb(LUA_TTABLE)
    result.value_.gc = a2
    L.top += 1
    
    return 1


def _push_string(L: 'LuaState', s: bytes) -> None:
    """Push a string onto the stack"""
    ts = TString()
    ts.tt = LUA_TSHRSTR
    ts.data = s
    ts.shrlen = len(s)
    
    result = L.stack[L.top]
    result.tt_ = ctb(LUA_TSHRSTR)
    result.value_.gc = ts
    L.top += 1


# Table library function table
table_funcs = {
    "insert": tab_insert,
    "remove": tab_remove,
    "concat": tab_concat,
    "sort": tab_sort,
    "pack": tab_pack,
    "unpack": tab_unpack,
    "move": tab_move,
}


def luaopen_table(L: 'LuaState', env: Table) -> None:
    """Open table library into environment table"""
    from .lobject import Node, TKey, Value
    
    # Create table table
    table_table = Table()
    table_table.tt = LUA_TTABLE
    table_table.metatable = None
    table_table.array = []
    table_table.sizearray = 0
    table_table.node = []
    table_table.flags = 0
    table_table.lsizenode = 0
    
    # Add functions
    for name, func in table_funcs.items():
        closure = CClosure()
        closure.tt = LUA_TCCL
        closure.nupvalues = 0
        closure.f = func
        closure.upvalue = []
        
        node = Node()
        node.i_key = TKey()
        node.i_key.value_ = Value()
        ts = TString()
        ts.tt = LUA_TSHRSTR
        ts.data = name.encode('utf-8')
        ts.shrlen = len(ts.data)
        node.i_key.value_.gc = ts
        node.i_key.tt_ = ctb(LUA_TSHRSTR)
        node.i_key.next = 0
        node.i_val = TValue()
        node.i_val.tt_ = ctb(LUA_TCCL)
        node.i_val.value_.gc = closure
        table_table.node.append(node)
    
    # Add 'table' to env
    node = Node()
    node.i_key = TKey()
    node.i_key.value_ = Value()
    ts = TString()
    ts.tt = LUA_TSHRSTR
    ts.data = b"table"
    ts.shrlen = 5
    node.i_key.value_.gc = ts
    node.i_key.tt_ = ctb(LUA_TSHRSTR)
    node.i_key.next = 0
    node.i_val = TValue()
    node.i_val.tt_ = ctb(LUA_TTABLE)
    node.i_val.value_.gc = table_table
    env.node.append(node)
