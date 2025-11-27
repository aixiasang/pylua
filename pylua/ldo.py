# -*- coding: utf-8 -*-
"""
ldo.py - Stack and Call structure of Lua
========================================
Source: ldo.h/ldo.c (lua-5.3.6/src/ldo.h, ldo.c)

Stack and Call structure of Lua
See Copyright Notice in lua.h
"""

from typing import Optional, Callable, Any, TYPE_CHECKING

from .lua import LUA_MULTRET, LUA_MINSTACK, LUA_ERRMEM, LUA_ERRERR
from .llimits import lua_assert, cast_int
from .lobject import (
    TValue, LClosure, CClosure, Proto,
    ttisLclosure, ttisCclosure, ttisfunction, ttisnil, ttislcf,
    clLvalue, clCvalue, fvalue, setobj, setobjs2s, setnilvalue,
)
from .lstate import (
    LuaState, CallInfo, GlobalState,
    CIST_LUA, CIST_FRESH, CIST_TAIL, isLua, G,
    luaE_extendCI,
)

if TYPE_CHECKING:
    from .lzio import ZIO


# =============================================================================
# ldo.h:23-28 - Stack Check Macros
# =============================================================================

def luaD_checkstackaux(L: LuaState, n: int) -> None:
    """
    ldo.h:23-25 - Check stack size and grow if needed
    #define luaD_checkstackaux(L,n,pre,pos)  \
        if (L->stack_last - L->top <= (n)) \
          { pre; luaD_growstack(L, n); pos; }
    Source: ldo.h:23-25
    """
    if L.stack_last - L.top <= n:
        luaD_growstack(L, n)


def luaD_checkstack(L: LuaState, n: int) -> None:
    """
    ldo.h:28 - #define luaD_checkstack(L,n) luaD_checkstackaux(L,n,(void)0,(void)0)
    Source: ldo.h:28
    """
    luaD_checkstackaux(L, n)


# =============================================================================
# ldo.h:32-33 - Stack Save/Restore
# =============================================================================

def savestack(L: LuaState, p: int) -> int:
    """
    ldo.h:32 - #define savestack(L,p) ((char *)(p) - (char *)L->stack)
    In Python, we just return the index
    Source: ldo.h:32
    """
    return p


def restorestack(L: LuaState, n: int) -> int:
    """
    ldo.h:33 - #define restorestack(L,n) ((TValue *)((char *)L->stack + (n)))
    In Python, we just return the index
    Source: ldo.h:33
    """
    return n


# =============================================================================
# ldo.c:52 - luaD_inctop
# =============================================================================

def luaD_inctop(L: LuaState) -> None:
    """
    ldo.h:52 / ldo.c - Increment top with stack check
    
    LUAI_FUNC void luaD_inctop (lua_State *L);
    
    Source: ldo.c (inline implementation)
    """
    luaD_checkstack(L, 1)
    L.top += 1


# =============================================================================
# ldo.c - luaD_growstack
# =============================================================================

def luaD_growstack(L: LuaState, n: int) -> None:
    """
    ldo.h:50 / ldo.c - Grow the stack
    
    LUAI_FUNC void luaD_growstack (lua_State *L, int n);
    
    Source: ldo.c:177-193
    """
    from .llimits import LUAI_MAXSTACK
    
    oldsize = L.stacksize
    
    if oldsize > LUAI_MAXSTACK:
        raise MemoryError("stack overflow")
    
    newsize = 2 * oldsize
    if newsize < oldsize + n:
        newsize = oldsize + n
    if newsize > LUAI_MAXSTACK:
        newsize = LUAI_MAXSTACK
    
    luaD_reallocstack(L, newsize)


def luaD_reallocstack(L: LuaState, newsize: int) -> None:
    """
    ldo.h:49 / ldo.c - Reallocate the stack
    
    LUAI_FUNC void luaD_reallocstack (lua_State *L, int newsize);
    
    Source: ldo.c:143-175
    """
    from .lstate import EXTRA_STACK
    
    oldsize = len(L.stack)
    
    # Extend stack
    while len(L.stack) < newsize + EXTRA_STACK:
        L.stack.append(TValue())
    
    L.stacksize = newsize
    L.stack_last = newsize - EXTRA_STACK


# =============================================================================
# ldo.c:328-349 - adjust_varargs
# =============================================================================

def _adjust_varargs(L: LuaState, p: 'Proto', actual: int, func: int) -> int:
    """
    ldo.c:328-349 - Adjust parameters for vararg function
    
    Move fixed parameters to final position, leaving vararg in place.
    Returns the new base (position of first fixed parameter).
    
    static StkId adjust_varargs (lua_State *L, Proto *p, int actual)
    
    Source: ldo.c:328-349
    """
    nfixargs = p.numparams
    
    # First fixed argument is at func + 1
    fixed = func + 1
    
    # Final position of first argument is at L.top
    # (after all original arguments)
    base = L.top
    
    # Move fixed parameters to their final position
    for i in range(min(nfixargs, actual)):
        setobjs2s(L, L.stack[L.top], L.stack[fixed + i])
        setnilvalue(L.stack[fixed + i])  # Erase original (for GC)
        L.top += 1
    
    # Complete missing arguments with nil
    for i in range(actual, nfixargs):
        setnilvalue(L.stack[L.top])
        L.top += 1
    
    return base


# =============================================================================
# ldo.c - luaD_precall
# =============================================================================

def luaD_precall(L: LuaState, func: int, nresults: int) -> int:
    """
    ldo.h:42 / ldo.c:320-400 - Prepare for a function call
    
    LUAI_FUNC int luaD_precall (lua_State *L, StkId func, int nresults);
    
    Returns 1 if C function, 0 if Lua function
    
    Source: ldo.c:320-400
    """
    from .lstate import CIST_LUA
    
    # Ensure we have a function at func
    if func >= len(L.stack):
        raise RuntimeError("attempt to call a nil value")
    
    fval = L.stack[func]
    
    if ttisLclosure(fval):
        # Lua function
        cl = clLvalue(fval)
        p = cl.p
        n = L.top - func - 1  # Number of actual arguments
        nfixargs = p.numparams
        fsize = p.maxstacksize
        
        # Ensure stack space
        luaD_checkstack(L, fsize + n)  # Extra space for vararg
        while len(L.stack) <= L.top + fsize + n:
            L.stack.append(TValue())
        
        # Handle vararg vs fixed arguments
        if p.is_vararg:
            # Vararg function - need to adjust parameter positions
            # ldo.c:328-349 - adjust_varargs
            base = _adjust_varargs(L, p, n, func)
        else:
            # Regular function - fill missing arguments with nil
            for i in range(n, nfixargs):
                setnilvalue(L.stack[L.top])
                L.top += 1
            base = func + 1
        
        # Create new CallInfo
        ci = luaE_extendCI(L)
        ci.func = func
        ci.base = base
        ci.top = base + fsize
        ci.savedpc = 0
        ci.nresults = nresults
        ci.callstatus = CIST_LUA
        
        L.top = ci.top
        L.ci = ci
        
        return 0  # Lua function
    
    elif ttisCclosure(fval) or ttislcf(fval):
        # C function (closure or light) - ldo.c:417-439
        if ttisCclosure(fval):
            ccl = clCvalue(fval)
            f = ccl.f
        else:
            # Light C function - ldo.c:420-422
            f = fvalue(fval)
        
        # Create new CallInfo - ldo.c:425-431
        ci = luaE_extendCI(L)
        ci.func = func
        ci.base = func + 1
        ci.top = L.top + LUA_MINSTACK
        ci.nresults = nresults
        ci.callstatus = 0  # Not Lua (C function)
        
        L.ci = ci
        
        # Ensure stack space
        luaD_checkstack(L, LUA_MINSTACK)
        
        # Call the C function - ldo.c:434
        if f is not None:
            n = f(L)
            luaD_poscall(L, ci, L.top - n, n)
        
        return 1  # C function
    
    else:
        # Try __call metamethod
        from .ltm import TMS, luaT_gettmbyobj
        tm = luaT_gettmbyobj(L, fval, TMS.TM_CALL)
        if tm is None or ttisnil(tm):
            raise TypeError("attempt to call a non-function value")
        
        # Shift arguments and retry with metamethod
        # Insert tm before func
        for i in range(L.top, func, -1):
            setobjs2s(L, L.stack[i], L.stack[i - 1])
        L.top += 1
        setobj(L, L.stack[func], tm)
        
        return luaD_precall(L, func, nresults)


# =============================================================================
# ldo.c - luaD_poscall
# =============================================================================

def luaD_poscall(L: LuaState, ci: CallInfo, firstResult: int, nres: int) -> int:
    """
    ldo.h:47-48 / ldo.c:401-430 - Post-call processing
    
    LUAI_FUNC int luaD_poscall (lua_State *L, CallInfo *ci, StkId firstResult, int nres);
    
    Source: ldo.c:401-430
    """
    wanted = ci.nresults
    
    # Restore previous CallInfo
    L.ci = ci.previous
    
    # Move results to proper position
    res = ci.func
    
    if wanted == LUA_MULTRET:
        # Return all results
        for i in range(nres):
            setobjs2s(L, L.stack[res + i], L.stack[firstResult + i])
        L.top = res + nres
        return 0
    
    # Return wanted results
    for i in range(min(nres, wanted)):
        setobjs2s(L, L.stack[res + i], L.stack[firstResult + i])
    
    # Fill missing results with nil
    for i in range(nres, wanted):
        setnilvalue(L.stack[res + i])
    
    L.top = res + wanted
    return 1


# =============================================================================
# ldo.c - luaD_call
# =============================================================================

def luaD_call(L: LuaState, func: int, nResults: int) -> None:
    """
    ldo.h:43 / ldo.c:432-446 - Call a function
    
    LUAI_FUNC void luaD_call (lua_State *L, StkId func, int nResults);
    
    Source: ldo.c:432-446
    """
    if luaD_precall(L, func, nResults) == 0:
        # Lua function
        from .lvm import luaV_execute
        luaV_execute(L)


def luaD_callnoyield(L: LuaState, func: int, nResults: int) -> None:
    """
    ldo.h:44 / ldo.c:448-453 - Call without allowing yield
    
    LUAI_FUNC void luaD_callnoyield (lua_State *L, StkId func, int nResults);
    
    Source: ldo.c:448-453
    """
    L.nny += 1
    luaD_call(L, func, nResults)
    L.nny -= 1


# =============================================================================
# ldo.c - luaD_throw
# =============================================================================

class LuaError(Exception):
    """Lua runtime error"""
    def __init__(self, errcode: int, message: str = ""):
        self.errcode = errcode
        self.message = message
        super().__init__(message)


def luaD_throw(L: LuaState, errcode: int) -> None:
    """
    ldo.h:54 / ldo.c - Throw an error
    
    LUAI_FUNC l_noret luaD_throw (lua_State *L, int errcode);
    
    Source: ldo.c:117-134
    """
    raise LuaError(errcode)


# =============================================================================
# ldo.c - luaD_hook
# =============================================================================

def luaD_hook(L: LuaState, event: int, line: int) -> None:
    """
    ldo.h:41 / ldo.c:232-257 - Call hook function
    
    LUAI_FUNC void luaD_hook (lua_State *L, int event, int line);
    
    Source: ldo.c:232-257
    """
    hook = L.hook
    if hook is not None and L.allowhook:
        ci = L.ci
        # Prepare debug info
        from .lua import LuaDebug
        ar = LuaDebug()
        ar.event = event
        ar.currentline = line
        ar.i_ci = ci
        
        L.allowhook = 0
        hook(L, ar)
        L.allowhook = 1


# =============================================================================
# ldo.c - luaD_pcall
# =============================================================================

def luaD_pcall(L: LuaState, func: Callable, u: Any, old_top: int, ef: int) -> int:
    """
    ldo.h:45-46 / ldo.c:659-686 - Protected call
    
    LUAI_FUNC int luaD_pcall (lua_State *L, Pfunc func, void *u,
                                          ptrdiff_t oldtop, ptrdiff_t ef);
    
    Source: ldo.c:659-686
    """
    from .lua import LUA_OK, LUA_ERRRUN
    
    oldnny = L.nny
    oldci = L.ci
    olderrfunc = L.errfunc
    L.errfunc = ef
    
    try:
        func(L, u)
        status = LUA_OK
    except LuaError as e:
        status = e.errcode
        # Restore state
        L.ci = oldci
        L.top = old_top
    except Exception as e:
        status = LUA_ERRRUN
        L.ci = oldci
        L.top = old_top
    
    L.nny = oldnny
    L.errfunc = olderrfunc
    
    return status


# =============================================================================
# ldo.c - luaD_shrinkstack
# =============================================================================

def luaD_shrinkstack(L: LuaState) -> None:
    """
    ldo.h:51 / ldo.c:195-218 - Shrink stack if too large
    
    LUAI_FUNC void luaD_shrinkstack (lua_State *L);
    
    Source: ldo.c:195-218
    """
    # Don't shrink below BASIC_STACK_SIZE
    from .lstate import BASIC_STACK_SIZE
    
    inuse = L.top
    ci = L.ci
    while ci is not None:
        if ci.top > inuse:
            inuse = ci.top
        ci = ci.previous
    
    goodsize = inuse + (inuse // 8) + (2 * LUA_MINSTACK)
    if goodsize > BASIC_STACK_SIZE:
        # Stack is using more than expected, don't shrink for now
        pass


# =============================================================================
# ldo.c - luaD_protectedparser
# =============================================================================

def luaD_protectedparser(L: LuaState, z: 'ZIO', name: str, mode: str) -> int:
    """
    ldo.h:39-40 / ldo.c:780-805 - Protected parser
    
    LUAI_FUNC int luaD_protectedparser (lua_State *L, ZIO *z, const char *name,
                                                      const char *mode);
    
    Source: ldo.c:780-805
    """
    from .lua import LUA_OK
    from .lundump import luaU_undump, LuaUndumpError
    
    try:
        cl = luaU_undump(L, z, name)
        # Push closure on stack
        from .lobject import setclLvalue
        setclLvalue(L, L.stack[L.top], cl)
        L.top += 1
        return LUA_OK
    except LuaUndumpError as e:
        from .lua import LUA_ERRSYNTAX
        return LUA_ERRSYNTAX
    except Exception as e:
        from .lua import LUA_ERRMEM
        return LUA_ERRMEM


# =============================================================================
# ldo.c - luaD_rawrunprotected
# =============================================================================

def luaD_rawrunprotected(L: LuaState, f: Callable, ud: Any) -> int:
    """
    ldo.h:55 / ldo.c:136-150 - Run protected
    
    LUAI_FUNC int luaD_rawrunprotected (lua_State *L, Pfunc f, void *ud);
    
    Source: ldo.c:136-150
    """
    from .lua import LUA_OK, LUA_ERRRUN
    
    oldnCcalls = L.nCcalls
    
    try:
        f(L, ud)
        return LUA_OK
    except LuaError as e:
        return e.errcode
    except Exception:
        return LUA_ERRRUN
    finally:
        L.nCcalls = oldnCcalls
