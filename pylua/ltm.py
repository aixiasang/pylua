# -*- coding: utf-8 -*-
"""
ltm.py - Tag methods
====================
Source: ltm.h/ltm.c (lua-5.3.6/src/ltm.h, ltm.c)

Tag methods
See Copyright Notice in lua.h
"""

from typing import Optional, List, TYPE_CHECKING
from enum import IntEnum

from .lua import LUA_NUMTAGS, LUA_TTABLE, LUA_TUSERDATA
from .lobject import LUA_TOTALTAGS

if TYPE_CHECKING:
    from .lobject import TValue, TString, Table
    from .lstate import LuaState, GlobalState, CallInfo

# =============================================================================
# ltm.h:14-44 - Tag Method Enumeration
# =============================================================================
class TMS(IntEnum):
    """
    ltm.h:18-44 - Tag Method enum
    
    WARNING: if you change the order of this enumeration,
    grep "ORDER TM" and "ORDER OP"
    """
    TM_INDEX = 0       # ltm.h:19 - __index
    TM_NEWINDEX = 1    # ltm.h:20 - __newindex
    TM_GC = 2          # ltm.h:21 - __gc
    TM_MODE = 3        # ltm.h:22 - __mode
    TM_LEN = 4         # ltm.h:23 - __len
    TM_EQ = 5          # ltm.h:24 - __eq (last tag method with fast access)
    TM_ADD = 6         # ltm.h:25 - __add
    TM_SUB = 7         # ltm.h:26 - __sub
    TM_MUL = 8         # ltm.h:27 - __mul
    TM_MOD = 9         # ltm.h:28 - __mod
    TM_POW = 10        # ltm.h:29 - __pow
    TM_DIV = 11        # ltm.h:30 - __div
    TM_IDIV = 12       # ltm.h:31 - __idiv
    TM_BAND = 13       # ltm.h:32 - __band
    TM_BOR = 14        # ltm.h:33 - __bor
    TM_BXOR = 15       # ltm.h:34 - __bxor
    TM_SHL = 16        # ltm.h:35 - __shl
    TM_SHR = 17        # ltm.h:36 - __shr
    TM_UNM = 18        # ltm.h:37 - __unm
    TM_BNOT = 19       # ltm.h:38 - __bnot
    TM_LT = 20         # ltm.h:39 - __lt
    TM_LE = 21         # ltm.h:40 - __le
    TM_CONCAT = 22     # ltm.h:41 - __concat
    TM_CALL = 23       # ltm.h:42 - __call
    TM_N = 24          # ltm.h:43 - number of elements in the enum

# =============================================================================
# ltm.h:48-51 - Fast Tag Method Access Macros
# =============================================================================
def gfasttm(g: 'GlobalState', et: Optional['Table'], e: TMS) -> Optional['TValue']:
    """
    ltm.h:48-49 - Get fast tag method
    #define gfasttm(g,et,e) ((et) == NULL ? NULL : \
      ((et)->flags & (1u<<(e))) ? NULL : luaT_gettm(et, e, (g)->tmname[e]))
    """
    if et is None:
        return None
    if et.flags & (1 << e):
        return None
    return luaT_gettm(et, e, g.tmname[e])

def fasttm(l: 'LuaState', et: Optional['Table'], e: TMS) -> Optional['TValue']:
    """
    ltm.h:51 - #define fasttm(l,et,e) gfasttm(G(l), et, e)
    """
    from .lstate import G
    return gfasttm(G(l), et, e)

# =============================================================================
# ltm.h:53-55 - Type Name Access
# =============================================================================
def ttypename(x: int) -> str:
    """
    ltm.h:53 - #define ttypename(x) luaT_typenames_[(x) + 1]
    """
    return luaT_typenames_[x + 1]

# =============================================================================
# ltm.c - Type Names Array
# =============================================================================
# ltm.c:19-32 - LUAI_DDEF const char *const luaT_typenames_[LUA_TOTALTAGS]
luaT_typenames_: List[str] = [
    "no value",       # ltm.c:20 - for LUA_TNONE (-1), index 0
    "nil",            # ltm.c:21 - LUA_TNIL (0)
    "boolean",        # ltm.c:22 - LUA_TBOOLEAN (1)
    "userdata",       # ltm.c:23 - LUA_TLIGHTUSERDATA (2)
    "number",         # ltm.c:24 - LUA_TNUMBER (3)
    "string",         # ltm.c:25 - LUA_TSTRING (4)
    "table",          # ltm.c:26 - LUA_TTABLE (5)
    "function",       # ltm.c:27 - LUA_TFUNCTION (6)
    "userdata",       # ltm.c:28 - LUA_TUSERDATA (7)
    "thread",         # ltm.c:29 - LUA_TTHREAD (8)
    "proto",          # ltm.c:30 - LUA_TPROTO (9) - internal
]

# =============================================================================
# ltm.c:35-50 - Tag Method Names
# =============================================================================
# These are the metamethod names used in Lua
luaT_eventname: List[str] = [
    "__index",     # TM_INDEX
    "__newindex",  # TM_NEWINDEX
    "__gc",        # TM_GC
    "__mode",      # TM_MODE
    "__len",       # TM_LEN
    "__eq",        # TM_EQ
    "__add",       # TM_ADD
    "__sub",       # TM_SUB
    "__mul",       # TM_MUL
    "__mod",       # TM_MOD
    "__pow",       # TM_POW
    "__div",       # TM_DIV
    "__idiv",      # TM_IDIV
    "__band",      # TM_BAND
    "__bor",       # TM_BOR
    "__bxor",      # TM_BXOR
    "__shl",       # TM_SHL
    "__shr",       # TM_SHR
    "__unm",       # TM_UNM
    "__bnot",      # TM_BNOT
    "__lt",        # TM_LT
    "__le",        # TM_LE
    "__concat",    # TM_CONCAT
    "__call",      # TM_CALL
]

# =============================================================================
# ltm.h:60-72 / ltm.c - Tag Method Functions
# =============================================================================
def luaT_gettm(events: 'Table', event: TMS, ename: 'TString') -> Optional['TValue']:
    """
    ltm.h:60 / ltm.c:59-67 - Get tag method from table
    
    const TValue *luaT_gettm (Table *events, TMS event, TString *ename) {
        const TValue *tm = luaH_getshortstr(events, ename);
        lua_assert(event <= TM_EQ);
        if (ttisnil(tm)) {  /* no tag method? */
            events->flags |= cast_byte(1u<<event);  /* cache this fact */
            return NULL;
        }
        else return tm;
    }
    
    Source: ltm.c:59-67
    """
    from .lobject import ttisnil
    from .llimits import cast_byte
    
    # Search in table for metamethod
    tm = _luaH_getshortstr(events, ename)
    
    if tm is None or ttisnil(tm):
        # Cache this fact
        events.flags |= cast_byte(1 << event)
        return None
    
    return tm


def luaT_gettmbyobj(L: 'LuaState', o: 'TValue', event: TMS) -> 'TValue':
    """
    ltm.h:61-62 / ltm.c:70-83 - Get tag method by object
    
    const TValue *luaT_gettmbyobj (lua_State *L, const TValue *o, TMS event) {
        Table *mt;
        switch (ttnov(o)) {
            case LUA_TTABLE:
                mt = hvalue(o)->metatable;
                break;
            case LUA_TUSERDATA:
                mt = uvalue(o)->metatable;
                break;
            default:
                mt = G(L)->mt[ttnov(o)];
        }
        return (mt ? luaH_getshortstr(mt, G(L)->tmname[event]) : luaO_nilobject);
    }
    
    Source: ltm.c:70-83
    """
    from .lobject import (
        ttistable, hvalue, ttisfulluserdata, uvalue,
        ttnov, luaO_nilobject
    )
    from .lstate import G
    
    mt: Optional['Table'] = None
    tt = ttnov(o)
    
    if tt == LUA_TTABLE:
        mt = hvalue(o).metatable
    elif tt == LUA_TUSERDATA:
        mt = uvalue(o).metatable
    else:
        g = G(L)
        if tt < len(g.mt):
            mt = g.mt[tt]
    
    if mt is not None:
        g = G(L)
        if event < len(g.tmname) and g.tmname[event] is not None:
            result = _luaH_getshortstr(mt, g.tmname[event])
            if result is not None:
                return result
    
    return luaO_nilobject()


def luaT_init(L: 'LuaState') -> None:
    """
    ltm.h:63 / ltm.c:37-52 - Initialize tag method names
    
    void luaT_init (lua_State *L) {
        static const char *const luaT_eventname[] = {  /* ORDER TM */
            "__index", "__newindex",
            "__gc", "__mode", "__len", "__eq",
            "__add", "__sub", "__mul", "__mod", "__pow",
            "__div", "__idiv",
            "__band", "__bor", "__bxor", "__shl", "__shr",
            "__unm", "__bnot", "__lt", "__le",
            "__concat", "__call"
        };
        int i;
        for (i=0; i<TM_N; i++) {
            G(L)->tmname[i] = luaS_new(L, luaT_eventname[i]);
            luaC_fix(L, obj2gco(G(L)->tmname[i]));
        }
    }
    
    Source: ltm.c:37-52
    """
    from .lstate import G
    from .lobject import TString, LUA_TSHRSTR
    
    g = G(L)
    
    for i, name in enumerate(luaT_eventname):
        ts = TString()
        ts.tt = LUA_TSHRSTR
        ts.data = name.encode('utf-8')
        ts.shrlen = len(ts.data)
        g.tmname[i] = ts


def luaT_objtypename(L: 'LuaState', o: 'TValue') -> str:
    """
    ltm.h:58 / ltm.c:90-99 - Get object type name
    
    const char *luaT_objtypename (lua_State *L, const TValue *o) {
        Table *mt;
        if ((ttistable(o) && (mt = hvalue(o)->metatable) != NULL) ||
            (ttisfulluserdata(o) && (mt = uvalue(o)->metatable) != NULL)) {
            const TValue *name = luaH_getshortstr(mt, luaS_new(L, "__name"));
            if (ttisstring(name))
                return getstr(tsvalue(name));
        }
        return ttypename(ttnov(o));
    }
    
    Source: ltm.c:90-99
    """
    from .lobject import (
        ttistable, hvalue, ttisfulluserdata, uvalue,
        ttnov, ttisstring, tsvalue, getstr, TString, LUA_TSHRSTR
    )
    
    mt = None
    
    if ttistable(o):
        mt = hvalue(o).metatable
    elif ttisfulluserdata(o):
        mt = uvalue(o).metatable
    
    if mt is not None:
        # Create __name key
        name_key = TString()
        name_key.tt = LUA_TSHRSTR
        name_key.data = b"__name"
        name_key.shrlen = 6
        
        name = _luaH_getshortstr(mt, name_key)
        if name is not None and ttisstring(name):
            return getstr(tsvalue(name)).decode('utf-8', errors='replace')
    
    return ttypename(ttnov(o))


def luaT_callTM(L: 'LuaState', f: 'TValue', p1: 'TValue', 
                p2: 'TValue', p3: 'TValue', hasres: int) -> None:
    """
    ltm.h:65-66 / ltm.c:102-121 - Call tag method
    
    void luaT_callTM (lua_State *L, const TValue *f, const TValue *p1,
                      const TValue *p2, TValue *p3, int hasres) {
        ptrdiff_t result = savestack(L, p3);
        StkId func = L->top;
        setobj2s(L, func, f);  /* push function */
        setobj2s(L, func + 1, p1);  /* 1st argument */
        setobj2s(L, func + 2, p2);  /* 2nd argument */
        L->top += 3;
        if (!hasres)
            setobj2s(L, L->top++, p3);  /* 3rd argument */
        if (isLua(L->ci))
            luaD_call(L, func, hasres);
        else
            luaD_callnoyield(L, func, hasres);
        if (hasres) {
            p3 = restorestack(L, result);
            setobjs2s(L, p3, --L->top);
        }
    }
    
    Source: ltm.c:102-121
    """
    from .lobject import setobj2s, setobjs2s, TValue
    from .lstate import isLua
    from .ldo import luaD_call, luaD_callnoyield, savestack, restorestack
    
    # Ensure stack space
    while len(L.stack) <= L.top + 4:
        L.stack.append(TValue())
    
    result = savestack(L, p3) if isinstance(p3, int) else L.top
    func = L.top
    
    setobj2s(L, L.stack[func], f)      # push function
    setobj2s(L, L.stack[func + 1], p1) # 1st argument
    setobj2s(L, L.stack[func + 2], p2) # 2nd argument
    L.top += 3
    
    if not hasres:
        if isinstance(p3, int):
            setobj2s(L, L.stack[L.top], L.stack[p3])
        else:
            setobj2s(L, L.stack[L.top], p3)
        L.top += 1
    
    # Call metamethod
    if L.ci is not None and isLua(L.ci):
        luaD_call(L, func, hasres)
    else:
        luaD_callnoyield(L, func, hasres)
    
    if hasres:
        L.top -= 1
        if isinstance(p3, int):
            setobjs2s(L, L.stack[p3], L.stack[L.top])
        else:
            setobjs2s(L, p3, L.stack[L.top])


def luaT_callbinTM(L: 'LuaState', p1: 'TValue', p2: 'TValue',
                   res: int, event: TMS) -> int:
    """
    ltm.h:67-68 / ltm.c:124-132 - Call binary tag method
    
    int luaT_callbinTM (lua_State *L, const TValue *p1, const TValue *p2,
                        StkId res, TMS event) {
        const TValue *tm = luaT_gettmbyobj(L, p1, event);
        if (ttisnil(tm))
            tm = luaT_gettmbyobj(L, p2, event);
        if (ttisnil(tm)) return 0;
        luaT_callTM(L, tm, p1, p2, res, 1);
        return 1;
    }
    
    Source: ltm.c:124-132
    """
    from .lobject import ttisnil
    
    # Try first operand
    tm = luaT_gettmbyobj(L, p1, event)
    if ttisnil(tm):
        # Try second operand
        tm = luaT_gettmbyobj(L, p2, event)
    
    if ttisnil(tm):
        return 0
    
    luaT_callTM(L, tm, p1, p2, res, 1)
    return 1


def luaT_trybinTM(L: 'LuaState', p1: 'TValue', p2: 'TValue',
                  res: int, event: TMS) -> None:
    """
    ltm.h:69-70 / ltm.c:135-155 - Try binary tag method (error if not found)
    
    void luaT_trybinTM (lua_State *L, const TValue *p1, const TValue *p2,
                        StkId res, TMS event) {
        if (!luaT_callbinTM(L, p1, p2, res, event)) {
            switch (event) {
                case TM_CONCAT:
                    luaG_concaterror(L, p1, p2);
                case TM_BAND: case TM_BOR: case TM_BXOR:
                case TM_SHL: case TM_SHR: case TM_BNOT: {
                    lua_Number dummy;
                    if (tonumber(p1, &dummy) && tonumber(p2, &dummy))
                        luaG_tointerror(L, p1, p2);
                    else
                        luaG_opinterror(L, p1, p2, "perform bitwise operation on");
                }
                default:
                    luaG_opinterror(L, p1, p2, "perform arithmetic on");
            }
        }
    }
    
    Source: ltm.c:135-155
    """
    from .lobject import ttnov
    
    if not luaT_callbinTM(L, p1, p2, res, event):
        # No metamethod found, raise error
        if event == TMS.TM_CONCAT:
            raise TypeError(f"attempt to concatenate a {ttypename(ttnov(p1))} with a {ttypename(ttnov(p2))}")
        elif event in (TMS.TM_BAND, TMS.TM_BOR, TMS.TM_BXOR, 
                       TMS.TM_SHL, TMS.TM_SHR, TMS.TM_BNOT):
            raise TypeError(f"attempt to perform bitwise operation on a {ttypename(ttnov(p1))}")
        else:
            raise TypeError(f"attempt to perform arithmetic on a {ttypename(ttnov(p1))}")


def luaT_callorderTM(L: 'LuaState', p1: 'TValue', p2: 'TValue',
                     event: TMS) -> int:
    """
    ltm.h:71-72 / ltm.c:158-164 - Call order tag method
    
    int luaT_callorderTM (lua_State *L, const TValue *p1, const TValue *p2,
                          TMS event) {
        if (!luaT_callbinTM(L, p1, p2, L->top, event))
            return -1;  /* no metamethod */
        else
            return !l_isfalse(L->top);
    }
    
    Source: ltm.c:158-164
    """
    from .lobject import l_isfalse, TValue
    
    # Ensure stack space
    while len(L.stack) <= L.top:
        L.stack.append(TValue())
    
    if not luaT_callbinTM(L, p1, p2, L.top, event):
        return -1  # No metamethod
    
    return 0 if l_isfalse(L.stack[L.top]) else 1


# =============================================================================
# ltm.c - Helper function for table lookup
# =============================================================================

def _luaH_getshortstr(t: 'Table', key: 'TString') -> Optional['TValue']:
    """
    ltable.c - Get value by short string key
    Simplified implementation for metamethod lookup
    """
    from .lobject import ttisstring, svalue, TValue, ttisnil
    
    if t is None:
        return None
    
    key_data = key.data if hasattr(key, 'data') else None
    if key_data is None:
        return None
    
    # Search in hash part (node list) - Node uses i_key and i_val
    if hasattr(t, 'node') and t.node:
        for node in t.node:
            # Node uses i_key (TKey) and i_val (TValue)
            node_key = getattr(node, 'i_key', None)
            if node_key is None:
                continue
            
            # Check if node key matches
            if hasattr(node_key, 'value_') and node_key.value_ is not None:
                gc = node_key.value_.gc
                if gc is not None and hasattr(gc, 'data') and gc.data == key_data:
                    return node.i_val
    
    return None
