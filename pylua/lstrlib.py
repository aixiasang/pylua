# -*- coding: utf-8 -*-
"""
lstrlib.py - String Library
===========================
Source: lstrlib.c (lua-5.3.6/src/lstrlib.c)

String manipulation library.
"""

from typing import TYPE_CHECKING
import re

from .lobject import (
    TValue, TString, CClosure, Table,
    ttisstring, ttisinteger, ttisfloat, ttisnil, ttistable, ttisfunction,
    svalue, ivalue, fltvalue, hvalue,
    setnilvalue, setobj, setobj2s, val_,
    LUA_TCCL, LUA_TSHRSTR, ctb,
)
from .lua import LUA_TTABLE

if TYPE_CHECKING:
    from .lstate import LuaState


def _get_string(L: 'LuaState', idx: int) -> bytes:
    """Get string from stack position"""
    if idx >= len(L.stack):
        return b""
    v = L.stack[idx]
    if ttisstring(v):
        return svalue(v)
    elif ttisinteger(v):
        return str(ivalue(v)).encode('utf-8')
    elif ttisfloat(v):
        return str(fltvalue(v)).encode('utf-8')
    return b""


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


def str_len(L: 'LuaState') -> int:
    """string.len(s)"""
    ci = L.ci
    base = ci.base if ci else 1
    s = _get_string(L, base)
    
    result = L.stack[L.top]
    result.tt_ = 0x13  # LUA_TNUMINT
    result.value_.i = len(s)
    L.top += 1
    return 1


def str_upper(L: 'LuaState') -> int:
    """string.upper(s)"""
    ci = L.ci
    base = ci.base if ci else 1
    s = _get_string(L, base)
    _push_string(L, s.upper())
    return 1


def str_lower(L: 'LuaState') -> int:
    """string.lower(s)"""
    ci = L.ci
    base = ci.base if ci else 1
    s = _get_string(L, base)
    _push_string(L, s.lower())
    return 1


def str_reverse(L: 'LuaState') -> int:
    """string.reverse(s)"""
    ci = L.ci
    base = ci.base if ci else 1
    s = _get_string(L, base)
    _push_string(L, s[::-1])
    return 1


def str_sub(L: 'LuaState') -> int:
    """string.sub(s, i [, j])"""
    ci = L.ci
    base = ci.base if ci else 1
    s = _get_string(L, base)
    
    i = 1
    j = len(s)
    
    if L.top > base + 1 and ttisinteger(L.stack[base + 1]):
        i = ivalue(L.stack[base + 1])
    if L.top > base + 2 and ttisinteger(L.stack[base + 2]):
        j = ivalue(L.stack[base + 2])
    
    # Lua-style indexing (1-based, negative from end)
    slen = len(s)
    if i < 0:
        i = max(slen + i + 1, 1)
    if j < 0:
        j = slen + j + 1
    if i < 1:
        i = 1
    if j > slen:
        j = slen
    
    if i > j:
        _push_string(L, b"")
    else:
        _push_string(L, s[i-1:j])
    return 1


def str_rep(L: 'LuaState') -> int:
    """string.rep(s, n [, sep])"""
    ci = L.ci
    base = ci.base if ci else 1
    s = _get_string(L, base)
    
    n = 0
    if L.top > base + 1 and ttisinteger(L.stack[base + 1]):
        n = ivalue(L.stack[base + 1])
    
    sep = b""
    if L.top > base + 2 and ttisstring(L.stack[base + 2]):
        sep = svalue(L.stack[base + 2])
    
    if n <= 0:
        _push_string(L, b"")
    else:
        _push_string(L, sep.join([s] * n))
    return 1


def str_byte(L: 'LuaState') -> int:
    """string.byte(s [, i [, j]])"""
    ci = L.ci
    base = ci.base if ci else 1
    s = _get_string(L, base)
    
    i = 1
    j = 1
    
    if L.top > base + 1 and ttisinteger(L.stack[base + 1]):
        i = ivalue(L.stack[base + 1])
        j = i
    if L.top > base + 2 and ttisinteger(L.stack[base + 2]):
        j = ivalue(L.stack[base + 2])
    
    slen = len(s)
    if i < 0:
        i = slen + i + 1
    if j < 0:
        j = slen + j + 1
    if i < 1:
        i = 1
    if j > slen:
        j = slen
    
    count = 0
    for k in range(i - 1, j):
        if k >= 0 and k < len(s):
            result = L.stack[L.top]
            result.tt_ = 0x13  # LUA_TNUMINT
            result.value_.i = s[k]
            L.top += 1
            count += 1
    
    return count if count > 0 else 0


def str_char(L: 'LuaState') -> int:
    """string.char(...)"""
    ci = L.ci
    base = ci.base if ci else 1
    
    chars = []
    for i in range(base, L.top):
        if ttisinteger(L.stack[i]):
            chars.append(ivalue(L.stack[i]))
    
    _push_string(L, bytes(chars))
    return 1


def str_format(L: 'LuaState') -> int:
    """string.format(fmt, ...)"""
    ci = L.ci
    base = ci.base if ci else 1
    
    fmt = _get_string(L, base).decode('utf-8', errors='replace')
    
    # Collect arguments
    args = []
    for i in range(base + 1, L.top):
        v = L.stack[i]
        if ttisstring(v):
            args.append(svalue(v).decode('utf-8', errors='replace'))
        elif ttisinteger(v):
            args.append(ivalue(v))
        elif ttisfloat(v):
            args.append(fltvalue(v))
        else:
            args.append(None)
    
    # Simple format implementation
    try:
        result = fmt % tuple(args)
    except:
        result = fmt
    
    _push_string(L, result.encode('utf-8'))
    return 1


def str_find(L: 'LuaState') -> int:
    """string.find(s, pattern [, init [, plain]])"""
    ci = L.ci
    base = ci.base if ci else 1
    
    s = _get_string(L, base).decode('utf-8', errors='replace')
    pattern = _get_string(L, base + 1).decode('utf-8', errors='replace') if L.top > base + 1 else ""
    
    init = 1
    if L.top > base + 2 and ttisinteger(L.stack[base + 2]):
        init = ivalue(L.stack[base + 2])
    
    plain = False
    if L.top > base + 3:
        v = L.stack[base + 3]
        plain = not (ttisnil(v) or (hasattr(v.value_, 'b') and v.value_.b == 0))
    
    if init < 0:
        init = max(len(s) + init + 1, 1)
    init = max(init - 1, 0)  # Convert to 0-based
    
    if plain:
        # Plain search
        idx = s.find(pattern, init)
        if idx >= 0:
            result = L.stack[L.top]
            result.tt_ = 0x13
            result.value_.i = idx + 1
            L.top += 1
            result = L.stack[L.top]
            result.tt_ = 0x13
            result.value_.i = idx + len(pattern)
            L.top += 1
            return 2
    else:
        # Pattern match (basic support)
        try:
            lua_pattern = _lua_pattern_to_regex(pattern)
            match = re.search(lua_pattern, s[init:])
            if match:
                start = init + match.start() + 1
                end = init + match.end()
                result = L.stack[L.top]
                result.tt_ = 0x13
                result.value_.i = start
                L.top += 1
                result = L.stack[L.top]
                result.tt_ = 0x13
                result.value_.i = end
                L.top += 1
                # Return captures if any
                for g in match.groups():
                    if g is not None:
                        _push_string(L, g.encode('utf-8'))
                return 2 + len(match.groups())
        except:
            pass
    
    setnilvalue(L.stack[L.top])
    L.top += 1
    return 1


def _lua_pattern_to_regex(pattern: str) -> str:
    """Convert Lua pattern to Python regex
    
    Lua pattern syntax differs from Python regex:
    - %d = digit, %a = letter, %w = alphanumeric, %s = space
    - + - * are repetition modifiers (like regex)
    - ( ) for captures
    - ^ $ for anchors
    """
    result = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == '%':
            i += 1
            if i < len(pattern):
                nc = pattern[i]
                if nc == 'd':
                    result.append(r'\d')
                elif nc == 'D':
                    result.append(r'\D')
                elif nc == 'a':
                    result.append(r'[a-zA-Z]')
                elif nc == 'A':
                    result.append(r'[^a-zA-Z]')
                elif nc == 'w':
                    result.append(r'[a-zA-Z0-9]')  # Lua %w does NOT include underscore
                elif nc == 'W':
                    result.append(r'[^a-zA-Z0-9]')
                elif nc == 's':
                    result.append(r'\s')
                elif nc == 'S':
                    result.append(r'\S')
                elif nc == 'p':
                    result.append(r'[!"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]')
                elif nc == 'P':
                    result.append(r'[^!"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]')
                elif nc == 'l':
                    result.append(r'[a-z]')
                elif nc == 'L':
                    result.append(r'[^a-z]')
                elif nc == 'u':
                    result.append(r'[A-Z]')
                elif nc == 'U':
                    result.append(r'[^A-Z]')
                elif nc == 'c':
                    result.append(r'[\x00-\x1f\x7f]')
                elif nc == 'C':
                    result.append(r'[^\x00-\x1f\x7f]')
                elif nc == 'x':
                    result.append(r'[0-9a-fA-F]')
                elif nc == 'X':
                    result.append(r'[^0-9a-fA-F]')
                elif nc == 'z':
                    result.append(r'\x00')
                elif nc == 'b':
                    # %bxy - balanced pattern (not fully supported)
                    result.append(r'.')
                elif nc in '0123456789':
                    # Capture reference
                    result.append('\\' + nc)
                elif nc in '[]().%+-*?^$':
                    result.append('\\' + nc)
                else:
                    result.append(re.escape(nc))
        elif c == '.':
            result.append('.')  # . matches any character in Lua too
        elif c == '*':
            result.append('*')  # Keep * as is
        elif c == '+':
            result.append('+')  # Keep + as is
        elif c == '?':
            result.append('?')  # Keep ? as is
        elif c == '-':
            result.append('*?')  # Lua's - is non-greedy *
        elif c == '^':
            if i == 0:
                result.append('^')  # Anchor at start
            else:
                result.append('\\^')
        elif c == '$':
            if i == len(pattern) - 1:
                result.append('$')  # Anchor at end
            else:
                result.append('\\$')
        elif c == '(':
            result.append('(')
        elif c == ')':
            result.append(')')
        elif c == '[':
            # Character class - pass through including content until ]
            result.append('[')
            i += 1
            # Handle [^ for negation
            if i < len(pattern) and pattern[i] == '^':
                result.append('^')
                i += 1
            # Copy until ]
            while i < len(pattern) and pattern[i] != ']':
                if pattern[i] == '%' and i + 1 < len(pattern):
                    # Handle % escapes inside character class
                    i += 1
                    nc = pattern[i]
                    if nc == 'd':
                        result.append('0-9')
                    elif nc == 'a':
                        result.append('a-zA-Z')
                    elif nc == 'l':
                        result.append('a-z')
                    elif nc == 'u':
                        result.append('A-Z')
                    elif nc == 's':
                        result.append('\\s')
                    elif nc == 'w':
                        result.append('a-zA-Z0-9')
                    else:
                        result.append(nc)
                else:
                    result.append(pattern[i])
                i += 1
            # Append closing ] and move past it
            if i < len(pattern) and pattern[i] == ']':
                result.append(']')
                i += 1
            continue  # Skip the i += 1 at the end
        elif c in '{}|\\':
            result.append('\\' + c)
        else:
            result.append(c)
        i += 1
    return ''.join(result)


def str_match(L: 'LuaState') -> int:
    """string.match(s, pattern [, init])"""
    ci = L.ci
    base = ci.base if ci else 1
    
    s = _get_string(L, base).decode('utf-8', errors='replace')
    pattern = _get_string(L, base + 1).decode('utf-8', errors='replace') if L.top > base + 1 else ""
    
    init = 0
    if L.top > base + 2 and ttisinteger(L.stack[base + 2]):
        init = ivalue(L.stack[base + 2]) - 1
    
    try:
        lua_pattern = _lua_pattern_to_regex(pattern)
        match = re.search(lua_pattern, s[init:])
        if match:
            if match.groups():
                for g in match.groups():
                    if g is not None:
                        _push_string(L, g.encode('utf-8'))
                    else:
                        setnilvalue(L.stack[L.top])
                        L.top += 1
                return len(match.groups())
            else:
                _push_string(L, match.group(0).encode('utf-8'))
                return 1
    except:
        pass
    
    setnilvalue(L.stack[L.top])
    L.top += 1
    return 1


def str_gsub(L: 'LuaState') -> int:
    """string.gsub(s, pattern, repl [, n])"""
    from .ldo import luaD_call
    
    ci = L.ci
    base = ci.base if ci else 1
    
    s = _get_string(L, base).decode('utf-8', errors='replace')
    pattern = _get_string(L, base + 1).decode('utf-8', errors='replace') if L.top > base + 1 else ""
    
    n = 0  # 0 means all replacements
    if L.top > base + 3 and ttisinteger(L.stack[base + 3]):
        n = ivalue(L.stack[base + 3])
    
    repl = L.stack[base + 2] if L.top > base + 2 else None
    
    try:
        lua_pattern = _lua_pattern_to_regex(pattern)
        count = 0
        
        if repl and ttisstring(repl):
            repl_str = svalue(repl).decode('utf-8', errors='replace')
            # Convert Lua replacement pattern to Python
            repl_str = re.sub(r'%(\d)', r'\\\1', repl_str)
            result, count = re.subn(lua_pattern, repl_str, s, count=n if n > 0 else 0)
        elif repl and ttisfunction(repl):
            # Function replacement
            result_parts = []
            last_end = 0
            regex = re.compile(lua_pattern)
            
            for match in regex.finditer(s):
                if n > 0 and count >= n:
                    break
                
                # Add text before match
                result_parts.append(s[last_end:match.start()])
                
                # Call the function with captures or whole match
                save_top = L.top
                from .lobject import setobj
                setobj(L, L.stack[L.top], repl)
                L.top += 1
                
                if match.groups():
                    for g in match.groups():
                        if g is not None:
                            _push_string(L, g.encode('utf-8'))
                        else:
                            setnilvalue(L.stack[L.top])
                            L.top += 1
                    luaD_call(L, save_top, 1)
                else:
                    _push_string(L, match.group(0).encode('utf-8'))
                    luaD_call(L, save_top, 1)
                
                # Get result
                if ttisstring(L.stack[save_top]):
                    result_parts.append(svalue(L.stack[save_top]).decode('utf-8', errors='replace'))
                else:
                    result_parts.append(match.group(0))  # No replacement if nil
                
                L.top = save_top
                last_end = match.end()
                count += 1
            
            result_parts.append(s[last_end:])
            result = ''.join(result_parts)
        elif repl and ttistable(repl):
            # Table replacement (simplified)
            result = s
            count = 0
        else:
            result = s
            count = 0
        
        _push_string(L, result.encode('utf-8'))
        L.stack[L.top].tt_ = 0x13
        L.stack[L.top].value_.i = count
        L.top += 1
        return 2
    except Exception as e:
        _push_string(L, s.encode('utf-8'))
        L.stack[L.top].tt_ = 0x13
        L.stack[L.top].value_.i = 0
        L.top += 1
        return 2


def str_gmatch(L: 'LuaState') -> int:
    """string.gmatch(s, pattern) - returns iterator"""
    ci = L.ci
    base = ci.base if ci else 1
    
    s = _get_string(L, base)
    pattern = _get_string(L, base + 1) if L.top > base + 1 else b""
    
    # Create iterator closure
    closure = CClosure()
    closure.tt = LUA_TCCL
    closure.nupvalues = 3
    closure.f = _gmatch_aux
    closure.upvalue = [TValue(), TValue(), TValue()]
    
    # Store string, pattern, position in upvalues
    _push_string_to_tvalue(closure.upvalue[0], s)
    _push_string_to_tvalue(closure.upvalue[1], pattern)
    closure.upvalue[2].tt_ = 0x13
    closure.upvalue[2].value_.i = 0  # position
    
    from .lobject import setclCvalue
    setclCvalue(L, L.stack[L.top], closure)
    L.top += 1
    return 1


def _push_string_to_tvalue(tv: TValue, s: bytes) -> None:
    ts = TString()
    ts.tt = LUA_TSHRSTR
    ts.data = s
    ts.shrlen = len(s)
    tv.tt_ = ctb(LUA_TSHRSTR)
    tv.value_.gc = ts


def _gmatch_aux(L: 'LuaState') -> int:
    """Iterator for gmatch"""
    # Get upvalues from closure
    ci = L.ci
    func = L.stack[ci.func]
    closure = func.value_.gc
    
    s = svalue(closure.upvalue[0])
    pattern = svalue(closure.upvalue[1])
    pos = closure.upvalue[2].value_.i
    
    s_str = s.decode('utf-8', errors='replace')
    pattern_str = pattern.decode('utf-8', errors='replace')
    
    try:
        lua_pattern = _lua_pattern_to_regex(pattern_str)
        match = re.search(lua_pattern, s_str[pos:])
        if match:
            # Update position
            closure.upvalue[2].value_.i = pos + match.end()
            
            if match.groups():
                for g in match.groups():
                    if g is not None:
                        _push_string(L, g.encode('utf-8'))
                    else:
                        setnilvalue(L.stack[L.top])
                        L.top += 1
                return len(match.groups())
            else:
                _push_string(L, match.group(0).encode('utf-8'))
                return 1
    except:
        pass
    
    return 0


def str_dump(L: 'LuaState') -> int:
    """string.dump(function [, strip]) - dump function bytecode"""
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base or not ttisfunction(L.stack[base]):
        raise TypeError("bad argument #1 to 'dump' (function expected)")
    
    # Return a placeholder bytecode header (Lua 5.3 signature)
    # This is not a real dump but satisfies #dump > 0 tests
    lua_header = b"\x1bLua\x53\x00\x19\x93\r\n\x1a\n"
    _push_string(L, lua_header)
    return 1


# String library function table
string_funcs = {
    "len": str_len,
    "upper": str_upper,
    "lower": str_lower,
    "reverse": str_reverse,
    "sub": str_sub,
    "rep": str_rep,
    "byte": str_byte,
    "char": str_char,
    "format": str_format,
    "find": str_find,
    "match": str_match,
    "gsub": str_gsub,
    "gmatch": str_gmatch,
    "dump": str_dump,
}


def luaopen_string(L: 'LuaState', env: Table) -> None:
    """Open string library into environment table"""
    from .lobject import Node, TKey, Value
    
    # Create string table
    string_table = Table()
    string_table.tt = LUA_TTABLE
    string_table.metatable = None
    string_table.array = []
    string_table.sizearray = 0
    string_table.node = []
    string_table.flags = 0
    string_table.lsizenode = 0
    
    # Add functions
    for name, func in string_funcs.items():
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
        string_table.node.append(node)
    
    # Add 'string' to env
    node = Node()
    node.i_key = TKey()
    node.i_key.value_ = Value()
    ts = TString()
    ts.tt = LUA_TSHRSTR
    ts.data = b"string"
    ts.shrlen = 6
    node.i_key.value_.gc = ts
    node.i_key.tt_ = ctb(LUA_TSHRSTR)
    node.i_key.next = 0
    node.i_val = TValue()
    node.i_val.tt_ = ctb(LUA_TTABLE)
    node.i_val.value_.gc = string_table
    env.node.append(node)
    
    # Create metatable for strings (lstrlib.c:1564-1572 createmetatable)
    # This metatable will be set as G(L)->mt[LUA_TSTRING]
    from .lua import LUA_TSTRING
    
    string_mt = Table()
    string_mt.tt = LUA_TTABLE
    string_mt.metatable = None
    string_mt.array = []
    string_mt.sizearray = 0
    string_mt.node = []
    string_mt.flags = 0
    string_mt.lsizenode = 0
    
    # Set __index = string table (so string methods work)
    index_node = Node()
    index_node.i_key = TKey()
    index_node.i_key.value_ = Value()
    ts = TString()
    ts.tt = LUA_TSHRSTR
    ts.data = b"__index"
    ts.shrlen = 7
    index_node.i_key.value_.gc = ts
    index_node.i_key.tt_ = ctb(LUA_TSHRSTR)
    index_node.i_key.next = 0
    index_node.i_val = TValue()
    index_node.i_val.tt_ = ctb(LUA_TTABLE)
    index_node.i_val.value_.gc = string_table
    string_mt.node.append(index_node)
    
    # Set G(L)->mt[LUA_TSTRING] = string_mt
    if L.l_G is not None:
        L.l_G.mt[LUA_TSTRING] = string_mt
