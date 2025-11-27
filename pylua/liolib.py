# -*- coding: utf-8 -*-
"""
liolib.py - Lua I/O Library
===========================
Source: liolib.c (lua-5.3.6/src/liolib.c)

Standard I/O (and system) library
See Copyright Notice in lua.h
"""

from typing import TYPE_CHECKING, Optional, Dict, Any
import sys
import os
import tempfile

from .lobject import (
    TValue, TString, Table, CClosure, Udata, Node, TKey, Value,
    ttisnil, ttisstring, ttisinteger, ttisnumber, ttisfunction,
    svalue, ivalue, fltvalue,
    setnilvalue, setbvalue, setivalue, setobj,
    LUA_TSHRSTR, LUA_TCCL, ctb,
)
from .lua import LUA_TTABLE, LUA_TUSERDATA

if TYPE_CHECKING:
    from .lstate import LuaState

# =============================================================================
# File Handle Type
# =============================================================================

LUA_FILEHANDLE = "FILE*"

# Global file handles
_stdin_handle = None
_stdout_handle = None
_stderr_handle = None
_default_input = None
_default_output = None

# File handle storage
_file_handles: Dict[int, Any] = {}
_next_handle_id = 1


def _push_string(L: 'LuaState', s: bytes) -> None:
    """Push string onto stack"""
    ts = TString()
    ts.tt = LUA_TSHRSTR
    ts.data = s
    ts.shrlen = len(s)
    L.stack[L.top].tt_ = ctb(LUA_TSHRSTR)
    L.stack[L.top].value_.gc = ts
    L.top += 1


def _get_string_arg(L: 'LuaState', arg: int) -> str:
    """Get string argument from stack (1-indexed from base)"""
    ci = L.ci
    base = ci.base if ci else 1
    idx = base + arg - 1
    if idx < L.top and ttisstring(L.stack[idx]):
        return svalue(L.stack[idx]).decode('utf-8', errors='replace')
    return ""


def _create_file_handle(L: 'LuaState', file_obj, closeable: bool = True) -> int:
    """Create a file handle as a table with methods"""
    global _next_handle_id
    handle_id = _next_handle_id
    _next_handle_id += 1
    _file_handles[handle_id] = {'file': file_obj, 'closeable': closeable}
    
    # Create file handle as a table with methods
    file_table = Table()
    file_table.tt = LUA_TTABLE
    file_table.metatable = None
    file_table.array = []
    file_table.sizearray = 0
    file_table.node = []
    file_table.flags = 0
    file_table.lsizenode = 0
    file_table._file_handle_id = handle_id  # Store handle ID
    
    # Add file methods
    _add_file_method(file_table, b"write", _file_write)
    _add_file_method(file_table, b"read", _file_read)
    _add_file_method(file_table, b"close", _file_close)
    _add_file_method(file_table, b"flush", _file_flush)
    _add_file_method(file_table, b"seek", _file_seek)
    _add_file_method(file_table, b"lines", _file_lines)
    
    L.stack[L.top].tt_ = ctb(LUA_TTABLE)
    L.stack[L.top].value_.gc = file_table
    L.top += 1
    return handle_id


def _add_file_method(file_table: Table, name: bytes, func) -> None:
    """Add a method to file handle table"""
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
    ts.data = name
    ts.shrlen = len(name)
    node.i_key.value_.gc = ts
    node.i_key.tt_ = ctb(LUA_TSHRSTR)
    node.i_key.next = 0
    node.i_val = TValue()
    node.i_val.tt_ = ctb(LUA_TCCL)
    node.i_val.value_.gc = closure
    file_table.node.append(node)


def _get_file_handle(L: 'LuaState', idx: int):
    """Get file handle from stack"""
    ci = L.ci
    base = ci.base if ci else 1
    stack_idx = base + idx - 1
    
    if stack_idx < L.top:
        v = L.stack[stack_idx]
        gc = v.value_.gc if hasattr(v.value_, 'gc') else None
        
        # Check for Table with _file_handle_id
        if isinstance(gc, Table) and hasattr(gc, '_file_handle_id'):
            handle_id = gc._file_handle_id
            if handle_id in _file_handles:
                return _file_handles[handle_id]['file']
        
        # Check for Udata
        if isinstance(gc, Udata):
            handle_id = gc.data
            if handle_id in _file_handles:
                return _file_handles[handle_id]['file']
    return None


# =============================================================================
# File Method Implementations - liolib.c:721-732
# =============================================================================

def _file_write(L: 'LuaState') -> int:
    """f:write(...) - Write to file"""
    f = _get_file_handle(L, 1)
    if f is None:
        setnilvalue(L.stack[L.top])
        L.top += 1
        _push_string(L, b"invalid file handle")
        return 2
    
    ci = L.ci
    base = ci.base if ci else 1
    
    for i in range(base + 1, L.top):
        v = L.stack[i]
        if ttisstring(v):
            s = svalue(v).decode('utf-8', errors='replace')
            f.write(s)
        elif ttisnumber(v):
            if ttisinteger(v):
                f.write(str(ivalue(v)))
            else:
                f.write(str(fltvalue(v)))
    
    # Return file handle for chaining
    setobj(L, L.stack[L.top], L.stack[base])
    L.top += 1
    return 1


def _file_read(L: 'LuaState') -> int:
    """f:read(...) - Read from file"""
    f = _get_file_handle(L, 1)
    if f is None:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    ci = L.ci
    base = ci.base if ci else 1
    
    # Get format argument
    format_arg = L.stack[base + 1] if L.top > base + 1 else None
    
    try:
        if format_arg is None or ttisnil(format_arg):
            # Default: read line
            line = f.readline()
            if line:
                if line.endswith('\n'):
                    line = line[:-1]
                _push_string(L, line.encode('utf-8'))
            else:
                setnilvalue(L.stack[L.top])
                L.top += 1
        elif ttisstring(format_arg):
            fmt = svalue(format_arg).decode('utf-8')
            if fmt == "*a" or fmt == "a":
                content = f.read()
                _push_string(L, content.encode('utf-8') if isinstance(content, str) else content)
            elif fmt == "*l" or fmt == "l":
                line = f.readline()
                if line.endswith('\n'):
                    line = line[:-1]
                _push_string(L, line.encode('utf-8'))
            elif fmt == "*L" or fmt == "L":
                line = f.readline()
                _push_string(L, line.encode('utf-8'))
            else:
                setnilvalue(L.stack[L.top])
                L.top += 1
        elif ttisinteger(format_arg) or ttisnumber(format_arg):
            n = ivalue(format_arg) if ttisinteger(format_arg) else int(fltvalue(format_arg))
            content = f.read(n)
            _push_string(L, content.encode('utf-8') if isinstance(content, str) else content)
        else:
            setnilvalue(L.stack[L.top])
            L.top += 1
    except Exception:
        setnilvalue(L.stack[L.top])
        L.top += 1
    
    return 1


def _file_close(L: 'LuaState') -> int:
    """f:close() - Close file"""
    f = _get_file_handle(L, 1)
    if f is None:
        setnilvalue(L.stack[L.top])
        L.top += 1
        _push_string(L, b"invalid file handle")
        return 2
    
    try:
        f.close()
        setbvalue(L.stack[L.top], 1)
        L.top += 1
        return 1
    except Exception as e:
        setnilvalue(L.stack[L.top])
        L.top += 1
        _push_string(L, str(e).encode('utf-8'))
        return 2


def _file_flush(L: 'LuaState') -> int:
    """f:flush() - Flush file"""
    f = _get_file_handle(L, 1)
    if f:
        try:
            f.flush()
        except:
            pass
    setbvalue(L.stack[L.top], 1)
    L.top += 1
    return 1


def _file_seek(L: 'LuaState') -> int:
    """f:seek([whence [, offset]]) - Seek in file"""
    f = _get_file_handle(L, 1)
    if f is None:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1
    
    ci = L.ci
    base = ci.base if ci else 1
    
    whence = "cur"
    offset = 0
    
    if L.top > base + 1 and ttisstring(L.stack[base + 1]):
        whence = svalue(L.stack[base + 1]).decode('utf-8')
    
    if L.top > base + 2 and ttisinteger(L.stack[base + 2]):
        offset = ivalue(L.stack[base + 2])
    
    try:
        whence_map = {"set": 0, "cur": 1, "end": 2}
        pos = f.seek(offset, whence_map.get(whence, 1))
        from .lobject import setivalue
        setivalue(L.stack[L.top], pos)
        L.top += 1
        return 1
    except Exception:
        setnilvalue(L.stack[L.top])
        L.top += 1
        return 1


def _file_lines(L: 'LuaState') -> int:
    """f:lines() - Return line iterator"""
    f = _get_file_handle(L, 1)
    if f is None:
        raise RuntimeError("invalid file handle")
    
    def lines_iterator(L2: 'LuaState') -> int:
        try:
            line = f.readline()
            if line:
                if line.endswith('\n'):
                    line = line[:-1]
                _push_string(L2, line.encode('utf-8'))
                return 1
            else:
                setnilvalue(L2.stack[L2.top])
                L2.top += 1
                return 1
        except:
            setnilvalue(L2.stack[L2.top])
            L2.top += 1
            return 1
    
    closure = CClosure()
    closure.tt = LUA_TCCL
    closure.nupvalues = 0
    closure.f = lines_iterator
    closure.upvalue = []
    
    L.stack[L.top].tt_ = ctb(LUA_TCCL)
    L.stack[L.top].value_.gc = closure
    L.top += 1
    return 1


# =============================================================================
# I/O Library Functions - liolib.c:702-714
# =============================================================================

def io_open(L: 'LuaState') -> int:
    """
    liolib.c:322-338 - io.open(filename [, mode])
    """
    filename = _get_string_arg(L, 1)
    mode = _get_string_arg(L, 2) if L.top > L.ci.base + 1 else "r"
    
    # Convert Lua mode to Python mode
    py_mode = mode.replace('b', '')
    if 'b' in mode:
        py_mode += 'b'
    
    try:
        f = open(filename, py_mode)
        _create_file_handle(L, f)
        return 1
    except Exception as e:
        setnilvalue(L.stack[L.top])
        L.top += 1
        _push_string(L, str(e).encode('utf-8'))
        return 2


def io_close(L: 'LuaState') -> int:
    """
    liolib.c:255-265 - io.close([file])
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top > base:
        f = _get_file_handle(L, 1)
        if f:
            try:
                f.close()
                setbvalue(L.stack[L.top], 1)
                L.top += 1
                return 1
            except:
                pass
    
    setnilvalue(L.stack[L.top])
    L.top += 1
    _push_string(L, b"cannot close file")
    return 2


def io_flush(L: 'LuaState') -> int:
    """
    liolib.c:268-271 - io.flush()
    """
    global _default_output
    if _default_output:
        try:
            _default_output.flush()
        except:
            pass
    sys.stdout.flush()
    setbvalue(L.stack[L.top], 1)
    L.top += 1
    return 1


def io_input(L: 'LuaState') -> int:
    """
    liolib.c:285-286 - io.input([file])
    """
    global _default_input
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top > base:
        if ttisstring(L.stack[base]):
            # Open file for input
            filename = _get_string_arg(L, 1)
            try:
                _default_input = open(filename, 'r')
            except:
                raise RuntimeError(f"cannot open file '{filename}'")
        else:
            _default_input = _get_file_handle(L, 1)
    
    # Return current input
    if _default_input:
        _create_file_handle(L, _default_input, False)
    else:
        _create_file_handle(L, sys.stdin, False)
    return 1


def io_output(L: 'LuaState') -> int:
    """
    liolib.c:289-290 - io.output([file])
    """
    global _default_output
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top > base:
        if ttisstring(L.stack[base]):
            filename = _get_string_arg(L, 1)
            try:
                _default_output = open(filename, 'w')
            except:
                raise RuntimeError(f"cannot open file '{filename}'")
        else:
            _default_output = _get_file_handle(L, 1)
    
    if _default_output:
        _create_file_handle(L, _default_output, False)
    else:
        _create_file_handle(L, sys.stdout, False)
    return 1


def io_read(L: 'LuaState') -> int:
    """
    liolib.c:293-295 - io.read(...)
    """
    global _default_input
    f = _default_input or sys.stdin
    
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base:
        # Default: read line
        try:
            line = f.readline()
            if line:
                if line.endswith('\n'):
                    line = line[:-1]
                _push_string(L, line.encode('utf-8'))
            else:
                setnilvalue(L.stack[L.top])
                L.top += 1
            return 1
        except:
            setnilvalue(L.stack[L.top])
            L.top += 1
            return 1
    
    format_arg = L.stack[base]
    if ttisstring(format_arg):
        fmt = svalue(format_arg).decode('utf-8')
        if fmt == "*a" or fmt == "a":
            # Read all
            content = f.read()
            _push_string(L, content.encode('utf-8'))
        elif fmt == "*l" or fmt == "l":
            # Read line without newline
            line = f.readline()
            if line.endswith('\n'):
                line = line[:-1]
            _push_string(L, line.encode('utf-8'))
        elif fmt == "*L" or fmt == "L":
            # Read line with newline
            line = f.readline()
            _push_string(L, line.encode('utf-8'))
        elif fmt == "*n" or fmt == "n":
            # Read number
            # Not fully implemented
            setnilvalue(L.stack[L.top])
            L.top += 1
        else:
            setnilvalue(L.stack[L.top])
            L.top += 1
    elif ttisinteger(format_arg) or ttisnumber(format_arg):
        # Read n bytes
        n = ivalue(format_arg) if ttisinteger(format_arg) else int(fltvalue(format_arg))
        content = f.read(n)
        _push_string(L, content.encode('utf-8') if isinstance(content, str) else content)
    else:
        setnilvalue(L.stack[L.top])
        L.top += 1
    
    return 1


def io_write(L: 'LuaState') -> int:
    """
    liolib.c:297-300 - io.write(...)
    """
    global _default_output
    f = _default_output or sys.stdout
    
    ci = L.ci
    base = ci.base if ci else 1
    
    for i in range(base, L.top):
        v = L.stack[i]
        if ttisstring(v):
            s = svalue(v).decode('utf-8', errors='replace')
            f.write(s)
        elif ttisnumber(v):
            if ttisinteger(v):
                f.write(str(ivalue(v)))
            else:
                f.write(str(fltvalue(v)))
    
    try:
        f.flush()
    except:
        pass
    
    # Return file handle
    _create_file_handle(L, f, False)
    return 1


def io_lines(L: 'LuaState') -> int:
    """
    liolib.c:340-355 - io.lines([filename, ...])
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top > base and ttisstring(L.stack[base]):
        filename = _get_string_arg(L, 1)
        try:
            f = open(filename, 'r')
        except:
            raise RuntimeError(f"cannot open file '{filename}'")
    else:
        f = _default_input or sys.stdin
    
    # Create iterator function
    def lines_iterator(L2):
        try:
            line = f.readline()
            if line:
                if line.endswith('\n'):
                    line = line[:-1]
                _push_string(L2, line.encode('utf-8'))
                return 1
            else:
                setnilvalue(L2.stack[L2.top])
                L2.top += 1
                return 1
        except:
            setnilvalue(L2.stack[L2.top])
            L2.top += 1
            return 1
    
    closure = CClosure()
    closure.tt = LUA_TCCL
    closure.nupvalues = 0
    closure.f = lines_iterator
    closure.upvalue = []
    
    L.stack[L.top].tt_ = ctb(LUA_TCCL)
    L.stack[L.top].value_.gc = closure
    L.top += 1
    return 1


def io_tmpfile(L: 'LuaState') -> int:
    """
    liolib.c:318-321 - io.tmpfile()
    """
    try:
        f = tempfile.TemporaryFile(mode='w+')
        _create_file_handle(L, f)
        return 1
    except:
        setnilvalue(L.stack[L.top])
        L.top += 1
        _push_string(L, b"cannot create temporary file")
        return 2


def io_type(L: 'LuaState') -> int:
    """
    liolib.c:232-248 - io.type(obj)
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top > base:
        v = L.stack[base]
        if hasattr(v.value_, 'gc') and isinstance(v.value_.gc, Udata):
            handle_id = v.value_.gc.data
            if handle_id in _file_handles:
                f = _file_handles[handle_id]['file']
                if hasattr(f, 'closed') and f.closed:
                    _push_string(L, b"closed file")
                else:
                    _push_string(L, b"file")
                return 1
    
    setnilvalue(L.stack[L.top])
    L.top += 1
    return 1


def io_popen(L: 'LuaState') -> int:
    """
    liolib.c:305-316 - io.popen(prog [, mode])
    """
    import subprocess
    
    prog = _get_string_arg(L, 1)
    mode = _get_string_arg(L, 2) if L.top > L.ci.base + 1 else "r"
    
    try:
        if 'r' in mode:
            p = subprocess.Popen(prog, shell=True, stdout=subprocess.PIPE, text=True)
            _create_file_handle(L, p.stdout)
        else:
            p = subprocess.Popen(prog, shell=True, stdin=subprocess.PIPE, text=True)
            _create_file_handle(L, p.stdin)
        return 1
    except Exception as e:
        setnilvalue(L.stack[L.top])
        L.top += 1
        _push_string(L, str(e).encode('utf-8'))
        return 2


# =============================================================================
# liolib.c:769-777 - luaopen_io
# =============================================================================

def luaopen_io(L: 'LuaState', env: Table) -> None:
    """
    liolib.c:769-777 - luaopen_io
    Open I/O library
    """
    # Create io table
    io_table = Table()
    io_table.tt = LUA_TTABLE
    io_table.metatable = None
    io_table.array = []
    io_table.sizearray = 0
    io_table.node = []
    io_table.flags = 0
    io_table.lsizenode = 0
    
    # Add functions
    funcs = [
        (b"close", io_close),
        (b"flush", io_flush),
        (b"input", io_input),
        (b"lines", io_lines),
        (b"open", io_open),
        (b"output", io_output),
        (b"popen", io_popen),
        (b"read", io_read),
        (b"tmpfile", io_tmpfile),
        (b"type", io_type),
        (b"write", io_write),
    ]
    
    for name, func in funcs:
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
        ts.data = name
        ts.shrlen = len(name)
        node.i_key.value_.gc = ts
        node.i_key.tt_ = ctb(LUA_TSHRSTR)
        node.i_key.next = 0
        node.i_val = TValue()
        node.i_val.tt_ = ctb(LUA_TCCL)
        node.i_val.value_.gc = closure
        io_table.node.append(node)
    
    # Add stdin, stdout, stderr
    _create_file_handle(L, sys.stdin, False)
    stdin_val = TValue()
    setobj(L, stdin_val, L.stack[L.top - 1])
    L.top -= 1
    
    node = Node()
    node.i_key = TKey()
    node.i_key.value_ = Value()
    ts = TString()
    ts.tt = LUA_TSHRSTR
    ts.data = b"stdin"
    ts.shrlen = 5
    node.i_key.value_.gc = ts
    node.i_key.tt_ = ctb(LUA_TSHRSTR)
    node.i_key.next = 0
    node.i_val = stdin_val
    io_table.node.append(node)
    
    # Create io TValue
    io_tv = TValue()
    io_tv.tt_ = ctb(LUA_TTABLE)
    io_tv.value_.gc = io_table
    
    # Add 'io' to env
    node = Node()
    node.i_key = TKey()
    node.i_key.value_ = Value()
    ts = TString()
    ts.tt = LUA_TSHRSTR
    ts.data = b"io"
    ts.shrlen = 2
    node.i_key.value_.gc = ts
    node.i_key.tt_ = ctb(LUA_TSHRSTR)
    node.i_key.next = 0
    node.i_val = io_tv
    env.node.append(node)
