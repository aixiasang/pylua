# -*- coding: utf-8 -*-
"""
lloadlib.py - Lua Package/Require Library
==========================================
Source: loadlib.c (lua-5.3.6/src/loadlib.c)

Dynamic library loader and require mechanism for Lua.
See Copyright Notice in lua.h
"""

import os
import subprocess
from typing import TYPE_CHECKING, Optional, List

from .lobject import (
    TValue, TString, Table, CClosure, LClosure, Node, TKey, Value,
    ttisnil, ttisstring, ttistable, ttisfunction, ttisboolean,
    svalue, hvalue, bvalue,
    setnilvalue, setobj, setbvalue,
    LUA_TSHRSTR, LUA_TCCL, LUA_TLCL, ctb,
)
from .lua import LUA_TTABLE, LUA_TFUNCTION, LUA_TNIL

if TYPE_CHECKING:
    from .lstate import LuaState

# =============================================================================
# Constants - loadlib.c / luaconf.h
# =============================================================================

LUA_DIRSEP = "\\" if os.name == 'nt' else "/"
LUA_PATH_SEP = ";"
LUA_PATH_MARK = "?"

if os.name == 'nt':
    LUA_PATH_DEFAULT = ".\\?.lua;.\\?\\init.lua"
    LUA_CPATH_DEFAULT = ".\\?.dll"
else:
    LUA_PATH_DEFAULT = "./?.lua;./?/init.lua"
    LUA_CPATH_DEFAULT = "./?.so"

# Registry keys - linit.c / lualib.h
LUA_LOADED_TABLE = "_LOADED"
LUA_PRELOAD_TABLE = "_PRELOAD"


# =============================================================================
# Helper Functions
# =============================================================================

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


def _lua_getfield(L: 'LuaState', t: Table, field: bytes) -> TValue:
    """Get field from table - returns TValue (may be nil)"""
    for node in (t.node or []):
        if node.i_key.tt_ != 0:
            gc = node.i_key.value_.gc
            if hasattr(gc, 'data') and gc.data == field:
                return node.i_val
    # Check array part for integer keys (not applicable for string fields)
    nil_val = TValue()
    setnilvalue(nil_val)
    return nil_val


def _lua_setfield(L: 'LuaState', t: Table, field: bytes, value: TValue) -> None:
    """Set field in table"""
    # Check if field exists
    for node in (t.node or []):
        if node.i_key.tt_ != 0:
            gc = node.i_key.value_.gc
            if hasattr(gc, 'data') and gc.data == field:
                setobj(L, node.i_val, value)
                return
    
    # Add new node
    node = Node()
    node.i_key = TKey()
    node.i_key.value_ = Value()
    ts = TString()
    ts.tt = LUA_TSHRSTR
    ts.data = field
    ts.shrlen = len(field)
    node.i_key.value_.gc = ts
    node.i_key.tt_ = ctb(LUA_TSHRSTR)
    node.i_key.next = 0
    node.i_val = TValue()
    setobj(L, node.i_val, value)
    t.node.append(node)


def _lua_rawgeti(t: Table, idx: int) -> TValue:
    """Get array element (1-indexed)"""
    if t.array and 1 <= idx <= len(t.array):
        return t.array[idx - 1]
    nil_val = TValue()
    setnilvalue(nil_val)
    return nil_val


def _get_upvalue(L: 'LuaState', idx: int) -> Optional[TValue]:
    """
    loadlib.c:574 - lua_upvalueindex(1)
    Get upvalue from current C closure
    """
    ci = L.ci
    if ci and ci.func < len(L.stack):
        func_val = L.stack[ci.func]
        if hasattr(func_val.value_, 'gc'):
            gc = func_val.value_.gc
            if isinstance(gc, CClosure) and gc.upvalue and len(gc.upvalue) >= idx:
                uv = gc.upvalue[idx - 1]
                # upvalue is a TValue directly for CClosure
                if isinstance(uv, TValue):
                    return uv
    return None


# =============================================================================
# Searcher Functions - loadlib.c:560-566, 495-501
# =============================================================================

def searcher_preload(L: 'LuaState') -> int:
    """
    loadlib.c:560-566 - searcher_preload
    Search in package.preload table
    """
    name = _get_string_arg(L, 1)
    name_bytes = name.encode('utf-8')
    
    # Get package table from upvalue
    package_tv = _get_upvalue(L, 1)
    if package_tv is None or not ttistable(package_tv):
        _push_string(L, f"\n\tno package table".encode('utf-8'))
        return 1
    
    package_table = hvalue(package_tv)
    
    # Get preload table
    preload_tv = _lua_getfield(L, package_table, b"preload")
    if ttisnil(preload_tv) or not ttistable(preload_tv):
        _push_string(L, f"\n\tno field package.preload['{name}']".encode('utf-8'))
        return 1
    
    preload_table = hvalue(preload_tv)
    
    # Get preload function
    func_tv = _lua_getfield(L, preload_table, name_bytes)
    if ttisnil(func_tv):
        _push_string(L, f"\n\tno field package.preload['{name}']".encode('utf-8'))
        return 1
    
    # Push the loader function
    setobj(L, L.stack[L.top], func_tv)
    L.top += 1
    return 1


def searcher_Lua(L: 'LuaState') -> int:
    """
    loadlib.c:495-501 - searcher_Lua
    Search for Lua file
    """
    name = _get_string_arg(L, 1)
    
    # Get package table from upvalue
    package_tv = _get_upvalue(L, 1)
    if package_tv is None or not ttistable(package_tv):
        _push_string(L, f"\n\tno package table".encode('utf-8'))
        return 1
    
    package_table = hvalue(package_tv)
    
    # Get path
    path_tv = _lua_getfield(L, package_table, b"path")
    if ttisnil(path_tv) or not ttisstring(path_tv):
        _push_string(L, f"\n\t'package.path' is not a string".encode('utf-8'))
        return 1
    
    path = svalue(path_tv).decode('utf-8', errors='replace')
    
    # Search for file
    filename = _searchpath(name, path)
    if filename is None:
        _push_string(L, f"\n\tno file for module '{name}'".encode('utf-8'))
        return 1
    
    # Load and compile the file
    try:
        luac_file = filename + 'c'
        result = subprocess.run(
            ['luac53', '-o', luac_file, filename],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            _push_string(L, f"\n\terror compiling '{filename}'".encode('utf-8'))
            return 1
        
        with open(luac_file, 'rb') as f:
            bytecode = f.read()
        
        from .lundump import luaU_undump
        cl = luaU_undump(L, bytecode, filename)
        
        if cl is None:
            _push_string(L, f"\n\terror loading '{filename}'".encode('utf-8'))
            return 1
        
        # Push the closure
        from .lobject import setclLvalue
        setclLvalue(L, L.stack[L.top], cl)
        L.top += 1
        
        # Push filename as second return
        _push_string(L, filename.encode('utf-8'))
        return 2
        
    except Exception as e:
        _push_string(L, f"\n\terror loading '{filename}': {e}".encode('utf-8'))
        return 1


def _searchpath(name: str, path: str) -> Optional[str]:
    """loadlib.c:435-455 - searchpath"""
    name = name.replace(".", LUA_DIRSEP)
    
    for template in path.split(LUA_PATH_SEP):
        template = template.strip()
        if not template:
            continue
        filename = template.replace(LUA_PATH_MARK, name)
        if os.path.isfile(filename):
            return filename
    
    return None


# =============================================================================
# findloader - loadlib.c:569-594
# =============================================================================

def _findloader(L: 'LuaState', name: str) -> None:
    """
    loadlib.c:569-594 - findloader
    Find a loader for the given module name
    """
    from .ldo import luaD_call
    
    # Get package table from upvalue
    package_tv = _get_upvalue(L, 1)
    if package_tv is None or not ttistable(package_tv):
        raise RuntimeError(f"module '{name}' not found: no package table")
    
    package_table = hvalue(package_tv)
    
    # Get searchers table
    searchers_tv = _lua_getfield(L, package_table, b"searchers")
    if ttisnil(searchers_tv) or not ttistable(searchers_tv):
        raise RuntimeError("'package.searchers' must be a table")
    
    searchers_table = hvalue(searchers_tv)
    
    errors = []
    i = 1
    while True:
        # Get searcher[i]
        searcher_tv = _lua_rawgeti(searchers_table, i)
        if ttisnil(searcher_tv):
            break
        
        # Call searcher(name)
        save_top = L.top
        setobj(L, L.stack[L.top], searcher_tv)
        L.top += 1
        _push_string(L, name.encode('utf-8'))
        
        try:
            luaD_call(L, save_top, 2)
            
            # Check result
            if ttisfunction(L.stack[save_top]):
                # Found loader! Leave it on stack with extra arg
                return
            elif ttisstring(L.stack[save_top]):
                # Error message
                errors.append(svalue(L.stack[save_top]).decode('utf-8', errors='replace'))
            
            L.top = save_top
        except Exception as e:
            errors.append(str(e))
            L.top = save_top
        
        i += 1
    
    error_msg = f"module '{name}' not found:" + "".join(errors)
    raise RuntimeError(error_msg)


# =============================================================================
# ll_require - loadlib.c:597-618
# =============================================================================

def ll_require(L: 'LuaState') -> int:
    """
    loadlib.c:597-618 - ll_require
    require(modname) - Loads the given module
    """
    from .ldo import luaD_call
    
    # luaL_checkstring(L, 1)
    name = _get_string_arg(L, 1)
    name_bytes = name.encode('utf-8')
    
    ci = L.ci
    base = ci.base if ci else 1
    
    # lua_settop(L, 1) - keep only the name argument
    L.top = base + 1
    
    # lua_getfield(L, LUA_REGISTRYINDEX, LUA_LOADED_TABLE)
    # Get _LOADED table from registry (stored in global state)
    g = L.l_G
    if not hasattr(g, 'registry') or g.registry is None:
        # Create registry if not exists
        g.registry = Table()
        g.registry.tt = LUA_TTABLE
        g.registry.metatable = None
        g.registry.array = []
        g.registry.sizearray = 0
        g.registry.node = []
    
    loaded_tv = _lua_getfield(L, g.registry, LUA_LOADED_TABLE.encode('utf-8'))
    if ttisnil(loaded_tv) or not ttistable(loaded_tv):
        # Create _LOADED table
        loaded_table = Table()
        loaded_table.tt = LUA_TTABLE
        loaded_table.metatable = None
        loaded_table.array = []
        loaded_table.sizearray = 0
        loaded_table.node = []
        
        loaded_tv = TValue()
        loaded_tv.tt_ = ctb(LUA_TTABLE)
        loaded_tv.value_.gc = loaded_table
        _lua_setfield(L, g.registry, LUA_LOADED_TABLE.encode('utf-8'), loaded_tv)
    
    loaded_table = hvalue(loaded_tv)
    
    # Push LOADED table at index 2 (base + 1)
    setobj(L, L.stack[L.top], loaded_tv)
    L.top += 1
    
    # lua_getfield(L, 2, name) - LOADED[name]
    cached_tv = _lua_getfield(L, loaded_table, name_bytes)
    
    # if lua_toboolean(L, -1) - is it there?
    if not ttisnil(cached_tv) and (not ttisboolean(cached_tv) or bvalue(cached_tv)):
        setobj(L, L.stack[L.top], cached_tv)
        L.top += 1
        return 1
    
    # else must load package
    # findloader(L, name)
    _findloader(L, name)
    
    # lua_pushstring(L, name) - pass name as argument to module loader
    # lua_insert(L, -2) - name is 1st argument (before search data)
    # lua_call(L, 2, 1) - run loader
    loader_idx = L.top - 2  # loader is 2 positions back
    
    # Insert name before second arg
    second_arg = TValue()
    setobj(L, second_arg, L.stack[L.top - 1])
    _push_string(L, name_bytes)
    setobj(L, L.stack[L.top - 1], second_arg)
    
    # Call loader(name, second_arg)
    luaD_call(L, loader_idx, 1)
    
    result = L.stack[loader_idx]
    
    # if !lua_isnil(L, -1) - non-nil return?
    if not ttisnil(result):
        # LOADED[name] = returned value
        _lua_setfield(L, loaded_table, name_bytes, result)
    
    # if lua_getfield(L, 2, name) == LUA_TNIL - module set no value?
    cached_tv = _lua_getfield(L, loaded_table, name_bytes)
    if ttisnil(cached_tv):
        # use true as result
        true_val = TValue()
        setbvalue(true_val, 1)
        setobj(L, L.stack[L.top], true_val)
        L.top += 1
        # LOADED[name] = true
        _lua_setfield(L, loaded_table, name_bytes, true_val)
    else:
        setobj(L, L.stack[L.top], cached_tv)
        L.top += 1
    
    return 1


# =============================================================================
# ll_searchpath - loadlib.c:458-469
# =============================================================================

def ll_searchpath(L: 'LuaState') -> int:
    """package.searchpath(name, path [, sep [, rep]])"""
    name = _get_string_arg(L, 1)
    path = _get_string_arg(L, 2)
    sep = _get_string_arg(L, 3) if L.top > L.ci.base + 2 else "."
    rep = _get_string_arg(L, 4) if L.top > L.ci.base + 3 else LUA_DIRSEP
    
    if sep:
        name = name.replace(sep, rep)
    
    result = _searchpath(name, path)
    if result:
        _push_string(L, result.encode('utf-8'))
        return 1
    else:
        setnilvalue(L.stack[L.top])
        L.top += 1
        _push_string(L, f"no file found".encode('utf-8'))
        return 2


def ll_loadlib(L: 'LuaState') -> int:
    """package.loadlib - C libraries not supported"""
    setnilvalue(L.stack[L.top])
    L.top += 1
    _push_string(L, b"C libraries not supported")
    _push_string(L, b"absent")
    return 3


# =============================================================================
# luaopen_package - loadlib.c:767-789
# =============================================================================

def luaopen_package(L: 'LuaState', env: Table) -> None:
    """
    loadlib.c:767-789 - luaopen_package
    Open package library
    """
    # Ensure registry exists
    g = L.l_G
    if not hasattr(g, 'registry') or g.registry is None:
        g.registry = Table()
        g.registry.tt = LUA_TTABLE
        g.registry.metatable = None
        g.registry.array = []
        g.registry.sizearray = 0
        g.registry.node = []
    
    # Create package table
    package_table = Table()
    package_table.tt = LUA_TTABLE
    package_table.metatable = None
    package_table.array = []
    package_table.sizearray = 0
    package_table.node = []
    
    # Create package TValue
    package_tv = TValue()
    package_tv.tt_ = ctb(LUA_TTABLE)
    package_tv.value_.gc = package_table
    
    # Set package.path
    path_tv = TValue()
    ts = TString()
    ts.tt = LUA_TSHRSTR
    ts.data = LUA_PATH_DEFAULT.encode('utf-8')
    ts.shrlen = len(ts.data)
    path_tv.tt_ = ctb(LUA_TSHRSTR)
    path_tv.value_.gc = ts
    _lua_setfield(L, package_table, b"path", path_tv)
    
    # Set package.cpath
    cpath_tv = TValue()
    ts2 = TString()
    ts2.tt = LUA_TSHRSTR
    ts2.data = LUA_CPATH_DEFAULT.encode('utf-8')
    ts2.shrlen = len(ts2.data)
    cpath_tv.tt_ = ctb(LUA_TSHRSTR)
    cpath_tv.value_.gc = ts2
    _lua_setfield(L, package_table, b"cpath", cpath_tv)
    
    # Set package.config
    config = f"{LUA_DIRSEP}\n{LUA_PATH_SEP}\n{LUA_PATH_MARK}\n!\n-\n"
    config_tv = TValue()
    ts3 = TString()
    ts3.tt = LUA_TSHRSTR
    ts3.data = config.encode('utf-8')
    ts3.shrlen = len(ts3.data)
    config_tv.tt_ = ctb(LUA_TSHRSTR)
    config_tv.value_.gc = ts3
    _lua_setfield(L, package_table, b"config", config_tv)
    
    # Create and set package.loaded (reference to registry._LOADED)
    loaded_table = Table()
    loaded_table.tt = LUA_TTABLE
    loaded_table.metatable = None
    loaded_table.array = []
    loaded_table.sizearray = 0
    loaded_table.node = []
    
    loaded_tv = TValue()
    loaded_tv.tt_ = ctb(LUA_TTABLE)
    loaded_tv.value_.gc = loaded_table
    
    # Store in registry
    _lua_setfield(L, g.registry, LUA_LOADED_TABLE.encode('utf-8'), loaded_tv)
    # Set in package
    _lua_setfield(L, package_table, b"loaded", loaded_tv)
    
    # Create and set package.preload
    preload_table = Table()
    preload_table.tt = LUA_TTABLE
    preload_table.metatable = None
    preload_table.array = []
    preload_table.sizearray = 0
    preload_table.node = []
    
    preload_tv = TValue()
    preload_tv.tt_ = ctb(LUA_TTABLE)
    preload_tv.value_.gc = preload_table
    
    # Store in registry
    _lua_setfield(L, g.registry, LUA_PRELOAD_TABLE.encode('utf-8'), preload_tv)
    # Set in package
    _lua_setfield(L, package_table, b"preload", preload_tv)
    
    # Create package.searchers (array of searcher functions)
    searchers_table = Table()
    searchers_table.tt = LUA_TTABLE
    searchers_table.metatable = None
    searchers_table.array = []
    searchers_table.sizearray = 0
    searchers_table.node = []
    
    # Create searcher closures with package as upvalue
    for searcher_func in [searcher_preload, searcher_Lua]:
        closure = CClosure()
        closure.tt = LUA_TCCL
        closure.nupvalues = 1
        closure.f = searcher_func
        closure.upvalue = [package_tv]  # package as upvalue
        
        searcher_tv = TValue()
        searcher_tv.tt_ = ctb(LUA_TCCL)
        searcher_tv.value_.gc = closure
        searchers_table.array.append(searcher_tv)
    
    searchers_table.sizearray = len(searchers_table.array)
    
    searchers_tv = TValue()
    searchers_tv.tt_ = ctb(LUA_TTABLE)
    searchers_tv.value_.gc = searchers_table
    _lua_setfield(L, package_table, b"searchers", searchers_tv)
    
    # Add package.searchpath function
    searchpath_closure = CClosure()
    searchpath_closure.tt = LUA_TCCL
    searchpath_closure.nupvalues = 1
    searchpath_closure.f = ll_searchpath
    searchpath_closure.upvalue = [package_tv]
    
    searchpath_tv = TValue()
    searchpath_tv.tt_ = ctb(LUA_TCCL)
    searchpath_tv.value_.gc = searchpath_closure
    _lua_setfield(L, package_table, b"searchpath", searchpath_tv)
    
    # Add package.loadlib function
    loadlib_closure = CClosure()
    loadlib_closure.tt = LUA_TCCL
    loadlib_closure.nupvalues = 0
    loadlib_closure.f = ll_loadlib
    loadlib_closure.upvalue = []
    
    loadlib_tv = TValue()
    loadlib_tv.tt_ = ctb(LUA_TCCL)
    loadlib_tv.value_.gc = loadlib_closure
    _lua_setfield(L, package_table, b"loadlib", loadlib_tv)
    
    # Add 'package' to global env
    _lua_setfield(L, env, b"package", package_tv)
    
    # Add 'require' to global env with package as upvalue
    require_closure = CClosure()
    require_closure.tt = LUA_TCCL
    require_closure.nupvalues = 1
    require_closure.f = ll_require
    require_closure.upvalue = [package_tv]  # package as upvalue
    
    require_tv = TValue()
    require_tv.tt_ = ctb(LUA_TCCL)
    require_tv.value_.gc = require_closure
    _lua_setfield(L, env, b"require", require_tv)
