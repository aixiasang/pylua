# -*- coding: utf-8 -*-
"""
lfunc.py - Auxiliary functions to manipulate prototypes and closures
====================================================================
Source: lfunc.h/lfunc.c (lua-5.3.6/src/lfunc.h, lfunc.c)

Auxiliary functions to manipulate prototypes and closures
See Copyright Notice in lua.h
"""

from typing import Optional, List, TYPE_CHECKING
from dataclasses import dataclass, field

from .llimits import lu_byte, cast_byte, lua_assert
from .lobject import (
    GCObject, TValue, Proto, LClosure, CClosure, UpVal, UpValRef,
    LUA_TPROTO, LUA_TLCL, LUA_TCCL,
    setnilvalue, setobj, getstr, upisopen,
)

if TYPE_CHECKING:
    from .lstate import LuaState


# =============================================================================
# lfunc.h:13-17 - Closure Size Macros
# =============================================================================

def sizeCclosure(n: int) -> int:
    """
    lfunc.h:13-14 - Size of C closure with n upvalues
    #define sizeCclosure(n) (cast(int, sizeof(CClosure)) + \
                             cast(int, sizeof(TValue)*((n)-1)))
    Source: lfunc.h:13-14
    """
    # In Python, we don't need actual memory size, just the count
    return n


def sizeLclosure(n: int) -> int:
    """
    lfunc.h:16-17 - Size of Lua closure with n upvalues
    #define sizeLclosure(n) (cast(int, sizeof(LClosure)) + \
                             cast(int, sizeof(TValue *)*((n)-1)))
    Source: lfunc.h:16-17
    """
    return n


# =============================================================================
# lfunc.h:35-47 - UpVal Structure (also in lobject.py)
# =============================================================================
# UpVal is defined in lobject.py, but we include the key macro here

# upisopen is now imported from lobject.py


# =============================================================================
# lfunc.c:25-30 - luaF_newCclosure
# =============================================================================

def luaF_newCclosure(L: 'LuaState', n: int) -> CClosure:
    """
    lfunc.c:25-30 - Create a new C closure
    
    CClosure *luaF_newCclosure (lua_State *L, int n) {
        GCObject *o = luaC_newobj(L, LUA_TCCL, sizeCclosure(n));
        CClosure *c = gco2ccl(o);
        c->nupvalues = cast_byte(n);
        return c;
    }
    
    Source: lfunc.c:25-30
    """
    c = CClosure()
    c.tt = LUA_TCCL
    c.nupvalues = cast_byte(n)
    c.upvalue = [TValue() for _ in range(n)]
    c.f = None
    c.gclist = None
    # TODO: Link to GC via luaC_newobj
    return c


# =============================================================================
# lfunc.c:33-40 - luaF_newLclosure
# =============================================================================

def luaF_newLclosure(L: 'LuaState', n: int) -> LClosure:
    """
    lfunc.c:33-40 - Create a new Lua closure
    
    LClosure *luaF_newLclosure (lua_State *L, int n) {
        GCObject *o = luaC_newobj(L, LUA_TLCL, sizeLclosure(n));
        LClosure *c = gco2lcl(o);
        c->p = NULL;
        c->nupvalues = cast_byte(n);
        while (n--) c->upvals[n] = NULL;
        return c;
    }
    
    Source: lfunc.c:33-40
    """
    c = LClosure()
    c.tt = LUA_TLCL
    c.p = None
    c.nupvalues = cast_byte(n)
    c.upvals = [None] * n  # Initialize all upvals to NULL
    c.gclist = None
    # TODO: Link to GC via luaC_newobj
    return c


# =============================================================================
# lfunc.c:45-54 - luaF_initupvals
# =============================================================================

def luaF_initupvals(L: 'LuaState', cl: LClosure) -> None:
    """
    lfunc.c:45-54 - Fill a closure with new closed upvalues
    
    void luaF_initupvals (lua_State *L, LClosure *cl) {
        int i;
        for (i = 0; i < cl->nupvalues; i++) {
            UpVal *uv = luaM_new(L, UpVal);
            uv->refcount = 1;
            uv->v = &uv->u.value;  /* make it closed */
            setnilvalue(uv->v);
            cl->upvals[i] = uv;
        }
    }
    
    Source: lfunc.c:45-54
    """
    for i in range(cl.nupvalues):
        uv = UpVal()
        uv.refcount = 1
        uv.value = TValue()  # Create the closed value
        uv.v = uv.value      # Point to own value (closed)
        setnilvalue(uv.v)
        cl.upvals[i] = uv


# =============================================================================
# lfunc.c:57-80 - luaF_findupval
# =============================================================================

def luaF_findupval(L: 'LuaState', level: int) -> UpVal:
    """
    lfunc.c:57-80 - Find or create an upvalue pointing to stack level
    
    UpVal *luaF_findupval (lua_State *L, StkId level) {
        UpVal **pp = &L->openupval;
        UpVal *p;
        UpVal *uv;
        lua_assert(isintwups(L) || L->openupval == NULL);
        while (*pp != NULL && (p = *pp)->v >= level) {
            lua_assert(upisopen(p));
            if (p->v == level)  /* found a corresponding upvalue? */
                return p;  /* return it */
            pp = &p->u.open.next;
        }
        /* not found: create a new upvalue */
        uv = luaM_new(L, UpVal);
        uv->refcount = 0;
        uv->u.open.next = *pp;  /* link it to list of open upvalues */
        uv->u.open.touched = 1;
        *pp = uv;
        uv->v = level;  /* current value lives in the stack */
        if (!isintwups(L)) {  /* thread not in list of threads with upvalues? */
            L->twups = G(L)->twups;  /* link it to the list */
            G(L)->twups = L;
        }
        return uv;
    }
    
    Source: lfunc.c:57-80
    """
    from .lstate import G
    
    # Helper to get stack index from upvalue
    def get_stack_index(uv: UpVal) -> int:
        if isinstance(uv.v, UpValRef):
            return uv.v.stack_index if uv.v.is_open else -1
        elif isinstance(uv.v, int):
            return uv.v
        return -1
    
    # Search existing open upvalues (sorted by descending stack index)
    pp = L.openupval  # Start of open upvalue list
    prev = None
    
    while pp is not None:
        p = pp
        lua_assert(upisopen(p))
        p_level = get_stack_index(p)
        
        # Found a corresponding upvalue?
        if p_level == level:
            return p
        # Passed the insertion point?
        if p_level < level:
            break
        
        prev = p
        pp = p.next
    
    # Not found: create a new upvalue with UpValRef wrapper
    uv = UpVal()
    uv.refcount = 0
    uv.next = pp  # Link it to list of open upvalues
    uv.touched = 1
    uv.v = UpValRef.from_stack(level)  # Use UpValRef for type safety
    
    # Insert into list (sorted by descending stack index)
    if prev is None:
        L.openupval = uv
    else:
        prev.next = uv
    
    # Thread management for GC
    # TODO: isintwups check and twups list management
    
    return uv


# =============================================================================
# lfunc.c:83-96 - luaF_close
# =============================================================================

def luaF_close(L: 'LuaState', level: int) -> None:
    """
    lfunc.c:83-96 - Close all upvalues at or above given stack level
    
    void luaF_close (lua_State *L, StkId level) {
        UpVal *uv;
        while (L->openupval != NULL && (uv = L->openupval)->v >= level) {
            lua_assert(upisopen(uv));
            L->openupval = uv->u.open.next;  /* remove from 'open' list */
            if (uv->refcount == 0)  /* no references? */
                luaM_free(L, uv);  /* free upvalue */
            else {
                setobj(L, &uv->u.value, uv->v);  /* move value to upvalue slot */
                uv->v = &uv->u.value;  /* now current value lives here */
                luaC_upvalbarrier(L, uv);
            }
        }
    }
    
    Source: lfunc.c:83-96
    """
    # Helper to get stack index from upvalue
    def get_stack_index(uv: UpVal) -> int:
        if isinstance(uv.v, UpValRef):
            return uv.v.stack_index if uv.v.is_open else -1
        elif isinstance(uv.v, int):
            return uv.v
        return -1
    
    while L.openupval is not None:
        uv = L.openupval
        uv_level = get_stack_index(uv)
        
        # Check if upvalue is at or above level
        if uv_level < level:
            break
        
        lua_assert(upisopen(uv))
        L.openupval = uv.next  # Remove from 'open' list
        
        if uv.refcount == 0:  # No references?
            pass  # Free upvalue (Python GC handles this)
        else:
            # Move value from stack to upvalue's own storage
            if uv_level >= 0 and uv_level < len(L.stack):
                setobj(L, uv.value, L.stack[uv_level])
            # Close the upvalue - now points to its own value
            uv.v = UpValRef.from_tvalue(uv.value)
            # TODO: luaC_upvalbarrier(L, uv)


# =============================================================================
# lfunc.c:99-122 - luaF_newproto
# =============================================================================

def luaF_newproto(L: 'LuaState') -> Proto:
    """
    lfunc.c:99-122 - Create a new function prototype
    
    Proto *luaF_newproto (lua_State *L) {
        GCObject *o = luaC_newobj(L, LUA_TPROTO, sizeof(Proto));
        Proto *f = gco2p(o);
        f->k = NULL;
        f->sizek = 0;
        f->p = NULL;
        f->sizep = 0;
        f->code = NULL;
        f->cache = NULL;
        f->sizecode = 0;
        f->lineinfo = NULL;
        f->sizelineinfo = 0;
        f->upvalues = NULL;
        f->sizeupvalues = 0;
        f->numparams = 0;
        f->is_vararg = 0;
        f->maxstacksize = 0;
        f->locvars = NULL;
        f->sizelocvars = 0;
        f->linedefined = 0;
        f->lastlinedefined = 0;
        f->source = NULL;
        return f;
    }
    
    Source: lfunc.c:99-122
    """
    f = Proto()
    f.tt = LUA_TPROTO
    f.k = []           # lfunc.c:102 - f->k = NULL
    f.sizek = 0        # lfunc.c:103
    f.p = []           # lfunc.c:104 - f->p = NULL
    f.sizep = 0        # lfunc.c:105
    f.code = []        # lfunc.c:106 - f->code = NULL
    f.cache = None     # lfunc.c:107
    f.sizecode = 0     # lfunc.c:108
    f.lineinfo = []    # lfunc.c:109 - f->lineinfo = NULL
    f.sizelineinfo = 0 # lfunc.c:110
    f.upvalues = []    # lfunc.c:111 - f->upvalues = NULL
    f.sizeupvalues = 0 # lfunc.c:112
    f.numparams = 0    # lfunc.c:113
    f.is_vararg = 0    # lfunc.c:114
    f.maxstacksize = 0 # lfunc.c:115
    f.locvars = []     # lfunc.c:116 - f->locvars = NULL
    f.sizelocvars = 0  # lfunc.c:117
    f.linedefined = 0  # lfunc.c:118
    f.lastlinedefined = 0  # lfunc.c:119
    f.source = None    # lfunc.c:120
    f.gclist = None
    # TODO: Link to GC via luaC_newobj
    return f


# =============================================================================
# lfunc.c:125-133 - luaF_freeproto
# =============================================================================

def luaF_freeproto(L: 'LuaState', f: Proto) -> None:
    """
    lfunc.c:125-133 - Free a prototype
    
    void luaF_freeproto (lua_State *L, Proto *f) {
        luaM_freearray(L, f->code, f->sizecode);
        luaM_freearray(L, f->p, f->sizep);
        luaM_freearray(L, f->k, f->sizek);
        luaM_freearray(L, f->lineinfo, f->sizelineinfo);
        luaM_freearray(L, f->locvars, f->sizelocvars);
        luaM_freearray(L, f->upvalues, f->sizeupvalues);
        luaM_free(L, f);
    }
    
    Source: lfunc.c:125-133
    """
    # In Python, we just clear references and let GC handle it
    f.code = []
    f.p = []
    f.k = []
    f.lineinfo = []
    f.locvars = []
    f.upvalues = []
    f.sizecode = 0
    f.sizep = 0
    f.sizek = 0
    f.sizelineinfo = 0
    f.sizelocvars = 0
    f.sizeupvalues = 0


# =============================================================================
# lfunc.c:140-150 - luaF_getlocalname
# =============================================================================

def luaF_getlocalname(f: Proto, local_number: int, pc: int) -> Optional[str]:
    """
    lfunc.c:140-150 - Get local variable name at given PC
    
    Look for n-th local variable at line 'line' in function 'func'.
    Returns NULL if not found.
    
    const char *luaF_getlocalname (const Proto *f, int local_number, int pc) {
        int i;
        for (i = 0; i<f->sizelocvars && f->locvars[i].startpc <= pc; i++) {
            if (pc < f->locvars[i].endpc) {  /* is variable active? */
                local_number--;
                if (local_number == 0)
                    return getstr(f->locvars[i].varname);
            }
        }
        return NULL;  /* not found */
    }
    
    Source: lfunc.c:140-150
    """
    for i in range(f.sizelocvars):
        if i >= len(f.locvars):
            break
        if f.locvars[i].startpc > pc:
            break
        if pc < f.locvars[i].endpc:  # Is variable active?
            local_number -= 1
            if local_number == 0:
                if f.locvars[i].varname is not None:
                    return getstr(f.locvars[i].varname).decode('utf-8', errors='replace')
    return None  # Not found
