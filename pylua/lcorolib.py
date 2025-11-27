# -*- coding: utf-8 -*-
"""
lcorolib.py - Lua Coroutine Library
===================================
Source: lcorolib.c, lstate.c, ldo.c (lua-5.3.6/src/)

Coroutine Library - Absolute consistency with Lua 5.3 C implementation.
See Copyright Notice in lua.h

Key Design (matching C):
- Each coroutine is a full lua_State with its own stack and CallInfo chain
- lua_yield sets status to LUA_YIELD and throws (like longjmp)
- lua_resume restores execution and calls luaV_execute
"""

from typing import TYPE_CHECKING, Optional, List, Callable
from dataclasses import dataclass, field
import copy

from .lobject import (
    TValue, TString, Table, CClosure, LClosure, Node, TKey, Value,
    ttisnil, ttisfunction, ttisLclosure, ttisCclosure,
    setnilvalue, setbvalue, setobj, setobj2s,
    LUA_TSHRSTR, LUA_TCCL, LUA_TLCL, ctb,
)
from .lua import LUA_OK, LUA_YIELD, LUA_ERRRUN, LUA_TTHREAD, LUA_TTABLE, LUA_MINSTACK
from .lstate import LuaState, CallInfo, GlobalState, BASIC_STACK_SIZE, CIST_LUA

if TYPE_CHECKING:
    pass


# =============================================================================
# Coroutine Status Strings - lcorolib.c:111-135
# =============================================================================
CO_RUN = b"running"
CO_SUS = b"suspended"
CO_NOR = b"normal"
CO_DEAD = b"dead"


# =============================================================================
# YieldException - Simulates luaD_throw(L, LUA_YIELD)
# =============================================================================
class LuaYield(Exception):
    """
    ldo.c:713 - luaD_throw(L, LUA_YIELD)
    
    Exception used to implement yield. In C, this is done via longjmp.
    In Python, we use an exception to unwind the stack.
    """
    def __init__(self, nresults: int):
        self.nresults = nresults
        super().__init__("lua yield")


# =============================================================================
# Global State for Coroutines
# =============================================================================
_running_thread: Optional[LuaState] = None  # Currently running coroutine


def _push_string(L: LuaState, s: bytes) -> None:
    """Push string onto stack"""
    ts = TString()
    ts.tt = LUA_TSHRSTR
    ts.data = s
    ts.shrlen = len(s)
    L.stack[L.top].tt_ = ctb(LUA_TSHRSTR)
    L.stack[L.top].value_.gc = ts
    L.top += 1


def _copy_tvalue(src: TValue) -> TValue:
    """Deep copy a TValue"""
    dst = TValue()
    dst.tt_ = src.tt_
    dst.value_ = Value()
    dst.value_.gc = src.value_.gc
    dst.value_.p = src.value_.p
    dst.value_.b = src.value_.b
    dst.value_.f = src.value_.f
    dst.value_.i = src.value_.i
    dst.value_.n = src.value_.n
    return dst


# =============================================================================
# lua_newthread - lstate.c:255-282
# =============================================================================
def lua_newthread(L: LuaState) -> LuaState:
    """
    lstate.c:255-282 - Create a new thread (coroutine)
    
    LUA_API lua_State *lua_newthread (lua_State *L)
    
    Creates a new lua_State that shares global state with L.
    """
    # Create new lua_State
    L1 = LuaState()
    L1.l_G = L.l_G  # Share global state
    L1.status = LUA_OK
    L1.nny = 1  # Start as non-yieldable (will be set to 0 in resume)
    L1.nCcalls = 0
    
    # Initialize stack - lstate.c:151-168
    L1.stack = [TValue() for _ in range(BASIC_STACK_SIZE)]
    L1.stacksize = BASIC_STACK_SIZE
    L1.top = 0
    L1.stack_last = BASIC_STACK_SIZE - 5  # EXTRA_STACK
    
    # Initialize first CallInfo - lstate.c:161-167
    L1.base_ci = CallInfo()
    L1.base_ci.next = None
    L1.base_ci.previous = None
    L1.base_ci.callstatus = 0
    L1.base_ci.func = 0
    setnilvalue(L1.stack[0])
    L1.top = 1
    L1.base_ci.top = L1.top + LUA_MINSTACK
    L1.ci = L1.base_ci
    
    # Copy hook settings from parent
    L1.hookmask = L.hookmask
    L1.basehookcount = L.basehookcount
    L1.hook = L.hook
    L1.hookcount = L.basehookcount
    
    return L1


# =============================================================================
# lua_xmove - lapi.c:118-131
# =============================================================================
def lua_xmove(from_L: LuaState, to_L: LuaState, n: int) -> None:
    """
    lapi.c:118-131 - Move values between threads
    
    LUA_API void lua_xmove (lua_State *from, lua_State *to, int n)
    """
    if from_L is to_L or n <= 0:
        return
    
    from_L.top -= n
    for i in range(n):
        # Copy value by creating new Value to avoid reference issues
        src = from_L.stack[from_L.top + i]
        dst = to_L.stack[to_L.top]
        # Deep copy the value
        dst.tt_ = src.tt_
        dst.value_ = Value()
        dst.value_.gc = src.value_.gc
        dst.value_.p = src.value_.p
        dst.value_.b = src.value_.b
        dst.value_.f = src.value_.f
        dst.value_.i = src.value_.i
        dst.value_.n = src.value_.n
        to_L.top += 1


# =============================================================================
# lua_resume - ldo.c:648-684
# =============================================================================
def lua_resume(L: LuaState, from_L: Optional[LuaState], nargs: int) -> int:
    """
    ldo.c:648-684 - Resume a coroutine
    
    LUA_API int lua_resume (lua_State *L, lua_State *from, int nargs)
    """
    from .ldo import luaD_precall, luaD_poscall
    from .lvm import luaV_execute
    
    global _running_thread
    
    oldnny = L.nny
    
    # Check if can resume - ldo.c:652-657
    if L.status == LUA_OK:
        if L.ci is not L.base_ci:
            # Not at base level
            L.status = LUA_ERRRUN
            return LUA_ERRRUN
    elif L.status != LUA_YIELD:
        # Dead coroutine
        L.status = LUA_ERRRUN
        return LUA_ERRRUN
    
    # Set nCcalls - ldo.c:658-660
    L.nCcalls = (from_L.nCcalls + 1) if from_L else 1
    
    L.nny = 0  # Allow yields - ldo.c:662
    
    old_running = _running_thread
    _running_thread = L
    
    try:
        status = _resume(L, nargs)
    except LuaYield:
        status = LUA_YIELD
    except Exception as e:
        L.status = LUA_ERRRUN
        status = LUA_ERRRUN
    finally:
        _running_thread = old_running
    
    L.nny = oldnny
    L.nCcalls -= 1
    
    return status


def _resume(L: LuaState, nargs: int) -> int:
    """
    ldo.c:619-645 - Internal resume function
    
    static void resume (lua_State *L, void *ud)
    """
    from .ldo import luaD_precall, luaD_poscall
    from .lvm import luaV_execute
    
    firstArg = L.top - nargs
    ci = L.ci
    
    if L.status == LUA_OK:
        # Starting a coroutine - ldo.c:623-626
        func_idx = firstArg - 1
        if not luaD_precall(L, func_idx, -1):  # Lua function
            luaV_execute(L)
    else:
        # Resuming from previous yield - ldo.c:627-644
        L.status = LUA_OK
        ci.func = ci.extra  # Restore saved func - ldo.c:630
        
        # Check if yielded inside Lua code
        if ci.callstatus & CIST_LUA:
            # Just continue running Lua code - ldo.c:632
            luaV_execute(L)
        else:
            # C function yield - call continuation if exists - ldo.c:633-641
            if ci.k is not None:
                n = ci.k(L, LUA_YIELD, ci.ctx)
                firstArg = L.top - n
            luaD_poscall(L, ci, firstArg, nargs)
        
        # unroll(L, NULL) - run continuation - ldo.c:643
        # Continue executing until we reach base_ci
        _unroll(L)
    
    return L.status


def _unroll(L: LuaState) -> None:
    """
    ldo.c:548-559 - Execute full continuation of coroutine
    
    static void unroll (lua_State *L, void *ud)
    """
    from .ldo import luaD_poscall
    from .lvm import luaV_execute
    
    while L.ci is not L.base_ci:
        if not (L.ci.callstatus & CIST_LUA):
            # C function - finish it
            luaD_poscall(L, L.ci, L.ci.func, 0)
        else:
            # Lua function - execute
            luaV_execute(L)
            break  # luaV_execute handles the rest


# =============================================================================
# lua_yield / lua_yieldk - ldo.c:692-718
# =============================================================================
def lua_yield(L: LuaState, nresults: int) -> int:
    """
    ldo.c:692-718 - Yield from a coroutine
    
    LUA_API int lua_yieldk (lua_State *L, int nresults, lua_KContext ctx, lua_KFunction k)
    
    Simplified version without continuation support.
    """
    ci = L.ci
    
    # Check if can yield - ldo.c:698-703
    if L.nny > 0:
        raise RuntimeError("attempt to yield from outside a coroutine")
    
    L.status = LUA_YIELD  # ldo.c:704
    ci.extra = ci.func    # ldo.c:705 - save current 'func'
    
    if ci.callstatus & CIST_LUA:
        # Inside Lua code - just return (VM will handle it)
        return 0
    else:
        # C function - throw to unwind - ldo.c:713
        ci.func = L.top - nresults - 1
        raise LuaYield(nresults)


def lua_isyieldable(L: LuaState) -> bool:
    """
    ldo.c:687-689 - Check if can yield
    
    LUA_API int lua_isyieldable (lua_State *L)
    """
    return L.nny == 0


# =============================================================================
# getco - lcorolib.c:21-25
# =============================================================================
def getco(L: LuaState) -> Optional[LuaState]:
    """
    lcorolib.c:21-25 - Get coroutine from first argument
    
    static lua_State *getco (lua_State *L)
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base:
        return None
    
    v = L.stack[base]
    # Check if it's a thread
    if hasattr(v.value_, 'gc') and isinstance(v.value_.gc, LuaState):
        return v.value_.gc
    # Check table wrapper
    if hasattr(v.value_, 'gc') and hasattr(v.value_.gc, '_coroutine'):
        return v.value_.gc._coroutine
    return None


# =============================================================================
# auxresume - lcorolib.c:28-54
# =============================================================================
def auxresume(L: LuaState, co: LuaState, narg: int) -> int:
    """
    lcorolib.c:28-54 - Auxiliary resume function
    
    static int auxresume (lua_State *L, lua_State *co, int narg)
    """
    # Check if dead - lcorolib.c:34-37
    # lua_gettop returns stack top relative to base (top - base)
    co_gettop = co.top - (co.ci.func + 1) if co.ci else co.top - 1
    
    if co.status == LUA_OK and co_gettop == 0:
        # Dead coroutine (finished, nothing on stack)
        _push_string(L, b"cannot resume dead coroutine")
        return -1
    elif co.status != LUA_OK and co.status != LUA_YIELD:
        # Error state
        _push_string(L, b"cannot resume dead coroutine")
        return -1
    
    # Move arguments to coroutine - lcorolib.c:38
    lua_xmove(L, co, narg)
    
    # Resume - lcorolib.c:39
    status = lua_resume(co, L, narg)
    
    if status == LUA_OK or status == LUA_YIELD:
        # Get number of results - lcorolib.c:41
        # lua_gettop(co) = co.top - (co.ci.func + 1)
        nres = co.top - (co.ci.func + 1) if co.ci else co.top
        if nres < 0:
            nres = 0
        # Move results back - lcorolib.c:47
        lua_xmove(co, L, nres)
        return nres
    else:
        # Move error message - lcorolib.c:51
        lua_xmove(co, L, 1)
        return -1


# =============================================================================
# luaB_coresume - lcorolib.c:57-71
# =============================================================================
def luaB_coresume(L: LuaState) -> int:
    """
    lcorolib.c:57-71 - coroutine.resume(co [, val1, ...])
    
    static int luaB_coresume (lua_State *L)
    """
    co = getco(L)
    if co is None:
        setbvalue(L.stack[L.top], 0)
        L.top += 1
        _push_string(L, b"bad argument #1 (thread expected)")
        return 2
    
    ci = L.ci
    base = ci.base if ci else 1
    narg = L.top - base - 1  # Arguments after coroutine
    
    r = auxresume(L, co, narg)
    
    if r < 0:
        # Error - lcorolib.c:61-65
        # Error message is already on stack from auxresume
        # Push false, then insert it before error message
        setbvalue(L.stack[L.top], 0)
        L.top += 1
        # lua_insert(L, -2): move false before error message
        if L.top >= 2:
            err_msg = _copy_tvalue(L.stack[L.top - 2])  # error message
            false_val = _copy_tvalue(L.stack[L.top - 1])  # false
            setobj(L, L.stack[L.top - 2], false_val)
            setobj(L, L.stack[L.top - 1], err_msg)
        return 2
    else:
        # Success - lcorolib.c:66-70
        # lua_pushboolean(L, 1) then lua_insert(L, -(r+1))
        # Insert true before all results
        # 
        # Before: stack has r results at positions [top-r] to [top-1]
        # After:  stack has true at [top-r-1], results shifted right
        
        # First, make room by shifting results right
        for i in range(r - 1, -1, -1):
            # Copy from [top-r+i] to [top-r+i+1]
            src_idx = L.top - r + i
            dst_idx = L.top - r + i + 1
            src = L.stack[src_idx]
            dst = L.stack[dst_idx]
            dst.tt_ = src.tt_
            dst.value_ = Value()
            dst.value_.gc = src.value_.gc
            dst.value_.p = src.value_.p
            dst.value_.b = src.value_.b
            dst.value_.f = src.value_.f
            dst.value_.i = src.value_.i
            dst.value_.n = src.value_.n
        
        # Put true at the beginning
        setbvalue(L.stack[L.top - r], 1)
        L.top += 1
        
        return r + 1


# =============================================================================
# luaB_cocreate - lcorolib.c:89-96
# =============================================================================
def luaB_cocreate(L: LuaState) -> int:
    """
    lcorolib.c:89-96 - coroutine.create(f)
    
    static int luaB_cocreate (lua_State *L)
    """
    ci = L.ci
    base = ci.base if ci else 1
    
    if L.top <= base or not ttisfunction(L.stack[base]):
        raise TypeError("bad argument #1 to 'create' (function expected)")
    
    # Create new thread - lcorolib.c:91
    NL = lua_newthread(L)
    
    # Push function onto new thread's stack - lcorolib.c:92
    setobj(NL, NL.stack[NL.top], L.stack[base])
    NL.top += 1
    
    # Push thread onto L's stack - lcorolib.c:93
    # Use a table wrapper to hold the coroutine reference
    thread_holder = Table()
    thread_holder.tt = LUA_TTABLE
    thread_holder._coroutine = NL
    
    L.stack[L.top].tt_ = ctb(LUA_TTHREAD)
    L.stack[L.top].value_.gc = thread_holder
    L.top += 1
    
    return 1


# =============================================================================
# luaB_cowrap / luaB_auxwrap - lcorolib.c:74-87, 99-103
# =============================================================================
def luaB_cowrap(L: LuaState) -> int:
    """
    lcorolib.c:99-103 - coroutine.wrap(f)
    
    static int luaB_cowrap (lua_State *L)
    """
    # Create coroutine
    luaB_cocreate(L)
    
    # Get the created thread
    thread_holder = L.stack[L.top - 1].value_.gc
    co = thread_holder._coroutine
    
    # Create wrapper function
    def wrap_func(L2: LuaState) -> int:
        ci = L2.ci
        base = ci.base if ci else 1
        narg = L2.top - base
        
        r = auxresume(L2, co, narg)
        
        if r < 0:
            # Error - propagate
            raise RuntimeError(
                L2.stack[L2.top - 1].value_.gc.data.decode('utf-8')
                if hasattr(L2.stack[L2.top - 1].value_.gc, 'data')
                else "coroutine error"
            )
        return r
    
    # Replace thread with wrapper function
    L.top -= 1
    
    closure = CClosure()
    closure.tt = LUA_TCCL
    closure.nupvalues = 0
    closure.f = wrap_func
    closure.upvalue = []
    
    L.stack[L.top].tt_ = ctb(LUA_TCCL)
    L.stack[L.top].value_.gc = closure
    L.top += 1
    
    return 1


# =============================================================================
# luaB_yield - lcorolib.c:106-108
# =============================================================================
def luaB_yield(L: LuaState) -> int:
    """
    lcorolib.c:106-108 - coroutine.yield(...)
    
    static int luaB_yield (lua_State *L)
    """
    ci = L.ci
    base = ci.base if ci else 1
    nargs = L.top - base
    
    return lua_yield(L, nargs)


# =============================================================================
# luaB_costatus - lcorolib.c:111-135
# =============================================================================
def luaB_costatus(L: LuaState) -> int:
    """
    lcorolib.c:111-135 - coroutine.status(co)
    
    static int luaB_costatus (lua_State *L)
    """
    global _running_thread
    
    co = getco(L)
    if co is None:
        _push_string(L, CO_DEAD)
        return 1
    
    if _running_thread is co:
        _push_string(L, CO_RUN)
    elif co.status == LUA_YIELD:
        _push_string(L, CO_SUS)
    elif co.status == LUA_OK:
        # Check stack state
        if co.ci is co.base_ci and co.top <= 1:
            _push_string(L, CO_DEAD)
        else:
            _push_string(L, CO_SUS)  # Initial state
    else:
        _push_string(L, CO_DEAD)
    
    return 1


# =============================================================================
# luaB_corunning - lcorolib.c:144-148
# =============================================================================
def luaB_corunning(L: LuaState) -> int:
    """
    lcorolib.c:144-148 - coroutine.running()
    
    static int luaB_corunning (lua_State *L)
    """
    global _running_thread
    
    if _running_thread is None:
        # Main thread
        setnilvalue(L.stack[L.top])
        L.top += 1
        setbvalue(L.stack[L.top], 1)  # true = main thread
        L.top += 1
    else:
        # Current coroutine
        thread_holder = Table()
        thread_holder.tt = LUA_TTABLE
        thread_holder._coroutine = _running_thread
        
        L.stack[L.top].tt_ = ctb(LUA_TTHREAD)
        L.stack[L.top].value_.gc = thread_holder
        L.top += 1
        setbvalue(L.stack[L.top], 0)  # false = not main
        L.top += 1
    
    return 2


# =============================================================================
# luaB_isyieldable - lcorolib.c:138-141
# =============================================================================
def luaB_isyieldable(L: LuaState) -> int:
    """
    lcorolib.c:138-141 - coroutine.isyieldable()
    
    static int luaB_yieldable (lua_State *L)
    """
    setbvalue(L.stack[L.top], 1 if lua_isyieldable(L) else 0)
    L.top += 1
    return 1


# =============================================================================
# luaopen_coroutine - lcorolib.c:151-167
# =============================================================================
def luaopen_coroutine(L: LuaState, env: Table) -> None:
    """
    lcorolib.c:151-167 - Open coroutine library
    
    LUAMOD_API int luaopen_coroutine (lua_State *L)
    """
    # Create coroutine table
    coroutine_table = Table()
    coroutine_table.tt = LUA_TTABLE
    coroutine_table.metatable = None
    coroutine_table.array = []
    coroutine_table.sizearray = 0
    coroutine_table.node = []
    coroutine_table.flags = 0
    coroutine_table.lsizenode = 0
    
    # Function table - lcorolib.c:151-161
    funcs = [
        (b"create", luaB_cocreate),
        (b"resume", luaB_coresume),
        (b"running", luaB_corunning),
        (b"status", luaB_costatus),
        (b"wrap", luaB_cowrap),
        (b"yield", luaB_yield),
        (b"isyieldable", luaB_isyieldable),
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
        coroutine_table.node.append(node)
    
    # Create coroutine TValue
    coroutine_tv = TValue()
    coroutine_tv.tt_ = ctb(LUA_TTABLE)
    coroutine_tv.value_.gc = coroutine_table
    
    # Add 'coroutine' to env
    node = Node()
    node.i_key = TKey()
    node.i_key.value_ = Value()
    ts = TString()
    ts.tt = LUA_TSHRSTR
    ts.data = b"coroutine"
    ts.shrlen = 9
    node.i_key.value_.gc = ts
    node.i_key.tt_ = ctb(LUA_TSHRSTR)
    node.i_key.next = 0
    node.i_val = coroutine_tv
    env.node.append(node)
