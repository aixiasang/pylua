# -*- coding: utf-8 -*-
"""
ldebug.py - Debug Interface
===========================
Source: ldebug.h/ldebug.c (lua-5.3.6/src/ldebug.h, ldebug.c)

Debug Interface
See Copyright Notice in lua.h
"""

from typing import TYPE_CHECKING, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field

from .lua import (
    LUA_IDSIZE, LUA_HOOKLINE, LUA_HOOKCOUNT, LUA_HOOKRET, LUA_HOOKCALL,
    LUA_MASKCALL, LUA_MASKRET, LUA_MASKLINE, LUA_MASKCOUNT,
    LUA_YIELD, LUA_ERRRUN,
)
from .llimits import lua_assert, cast_int, cast_byte
from .lobject import (
    TValue, Proto, LClosure, CClosure, Table,
    ttisfunction, ttisLclosure, ttisCclosure, ttisstring, ttisclosure, ttisnil,
    clLvalue, clvalue, svalue, getstr, setobj2s, setobjs2s, setnilvalue,
    LUA_TLCL, LUA_TCCL,
)
from .lopcodes import (
    OpCode, GET_OPCODE, GETARG_A, GETARG_B, GETARG_C,
    GETARG_Bx, GETARG_sBx, GETARG_Ax,
    ISK, INDEXK, testAMode,
)
from .ltm import TMS

if TYPE_CHECKING:
    from .lstate import LuaState, CallInfo, GlobalState


# =============================================================================
# ldebug.h:14 - pcRel macro
# =============================================================================

def pcRel(pc: int, p: Proto) -> int:
    """
    ldebug.h:14 - #define pcRel(pc, p) (cast(int, (pc) - (p)->code) - 1)
    
    Calculate relative PC (0-indexed instruction number)
    """
    return pc - 1


# =============================================================================
# ldebug.h:16 - getfuncline macro
# =============================================================================

def getfuncline(f: Proto, pc: int) -> int:
    """
    ldebug.h:16 - #define getfuncline(f,pc) (((f)->lineinfo) ? (f)->lineinfo[pc] : -1)
    
    Get source line number for given PC
    """
    if f.lineinfo and 0 <= pc < len(f.lineinfo):
        return f.lineinfo[pc]
    return -1


# =============================================================================
# ldebug.h:18 - resethookcount macro
# =============================================================================

def resethookcount(L: 'LuaState') -> None:
    """ldebug.h:18 - #define resethookcount(L) (L->hookcount = L->basehookcount)"""
    L.hookcount = L.basehookcount


# =============================================================================
# ldebug.c:34 - noLuaClosure macro
# =============================================================================

def noLuaClosure(f) -> bool:
    """ldebug.c:34 - #define noLuaClosure(f) ((f) == NULL || (f)->c.tt == LUA_TCCL)"""
    if f is None:
        return True
    if hasattr(f, 'tt'):
        return f.tt == LUA_TCCL
    return isinstance(f, CClosure)


# =============================================================================
# ldebug.c:38 - ci_func macro
# =============================================================================

def ci_func(ci: 'CallInfo') -> LClosure:
    """ldebug.c:38 - #define ci_func(ci) (clLvalue((ci)->func))"""
    return clLvalue(ci.func)


# =============================================================================
# ldebug.c:45-48 - currentpc
# =============================================================================

def currentpc(ci: 'CallInfo') -> int:
    """
    ldebug.c:45-48 - Get current PC for a call info
    
    static int currentpc (CallInfo *ci) {
        lua_assert(isLua(ci));
        return pcRel(ci->u.l.savedpc, ci_func(ci)->p);
    }
    """
    return pcRel(ci.savedpc, ci_func(ci).p)


# =============================================================================
# ldebug.c:51-53 - currentline
# =============================================================================

def currentline(ci: 'CallInfo') -> int:
    """
    ldebug.c:51-53 - Get current source line for a call info
    
    static int currentline (CallInfo *ci) {
        return getfuncline(ci_func(ci)->p, currentpc(ci));
    }
    """
    return getfuncline(ci_func(ci).p, currentpc(ci))


# =============================================================================
# lua_Debug structure
# =============================================================================

@dataclass
class lua_Debug:
    """
    lua.h:411-425 - Debug information structure
    
    typedef struct lua_Debug {
        int event;
        const char *name;
        const char *namewhat;
        const char *what;
        const char *source;
        int currentline;
        int linedefined;
        int lastlinedefined;
        unsigned char nups;
        unsigned char nparams;
        char isvararg;
        char istailcall;
        char short_src[LUA_IDSIZE];
        /* private part */
        struct CallInfo *i_ci;
    } lua_Debug;
    """
    event: int = 0
    name: Optional[str] = None
    namewhat: Optional[str] = None
    what: Optional[str] = None
    source: Optional[str] = None
    currentline: int = -1
    linedefined: int = 0
    lastlinedefined: int = 0
    nups: int = 0
    nparams: int = 0
    isvararg: int = 0
    istailcall: int = 0
    short_src: str = ""
    # Private part
    i_ci: Optional['CallInfo'] = None


# =============================================================================
# ldebug.c:81-92 - lua_sethook
# =============================================================================

def lua_sethook(L: 'LuaState', func: Optional[Callable], mask: int, count: int) -> None:
    """
    ldebug.c:81-92 - Set debug hook
    
    LUA_API void lua_sethook (lua_State *L, lua_Hook func, int mask, int count)
    """
    if func is None or mask == 0:  # turn off hooks?
        mask = 0
        func = None
    if isLua(L.ci):
        L.oldpc = L.ci.savedpc
    L.hook = func
    L.basehookcount = count
    resethookcount(L)
    L.hookmask = cast_byte(mask)


# =============================================================================
# ldebug.c:95-107 - lua_gethook, lua_gethookmask, lua_gethookcount
# =============================================================================

def lua_gethook(L: 'LuaState') -> Optional[Callable]:
    """ldebug.c:95-97 - Get current hook function"""
    return L.hook


def lua_gethookmask(L: 'LuaState') -> int:
    """ldebug.c:100-102 - Get current hook mask"""
    return L.hookmask


def lua_gethookcount(L: 'LuaState') -> int:
    """ldebug.c:105-107 - Get current hook count"""
    return L.basehookcount


# =============================================================================
# ldebug.c:110-124 - lua_getstack
# =============================================================================

def lua_getstack(L: 'LuaState', level: int, ar: lua_Debug) -> int:
    """
    ldebug.c:110-124 - Get information about the interpreter stack
    
    LUA_API int lua_getstack (lua_State *L, int level, lua_Debug *ar)
    """
    if level < 0:
        return 0  # invalid (negative) level
    
    ci = L.ci
    while level > 0 and ci is not None and ci != L.base_ci:
        level -= 1
        ci = ci.previous
    
    if level == 0 and ci is not None and ci != L.base_ci:
        ar.i_ci = ci
        return 1
    else:
        return 0  # no such level


# =============================================================================
# ldebug.c:127-131 - upvalname
# =============================================================================

def upvalname(p: Proto, uv: int) -> str:
    """
    ldebug.c:127-131 - Get upvalue name
    
    static const char *upvalname (Proto *p, int uv)
    """
    if p.upvalues and uv < len(p.upvalues):
        s = p.upvalues[uv].name
        if s is not None:
            return getstr(s).decode('utf-8', errors='replace')
    return "?"


# =============================================================================
# ldebug.c:212-227 - funcinfo
# =============================================================================

def funcinfo(ar: lua_Debug, cl) -> None:
    """
    ldebug.c:212-227 - Fill in function info
    
    static void funcinfo (lua_Debug *ar, Closure *cl)
    """
    from .lobject import luaO_chunkid
    
    if noLuaClosure(cl):
        ar.source = "=[C]"
        ar.linedefined = -1
        ar.lastlinedefined = -1
        ar.what = "C"
    else:
        p = cl.p
        if p.source is not None:
            ar.source = getstr(p.source).decode('utf-8', errors='replace')
        else:
            ar.source = "=?"
        ar.linedefined = p.linedefined
        ar.lastlinedefined = p.lastlinedefined
        ar.what = "main" if ar.linedefined == 0 else "Lua"
    
    ar.short_src = luaO_chunkid(ar.source, LUA_IDSIZE)


# =============================================================================
# ldebug.c:263-307 - auxgetinfo
# =============================================================================

def auxgetinfo(L: 'LuaState', what: str, ar: lua_Debug, f, ci: Optional['CallInfo']) -> int:
    """
    ldebug.c:263-307 - Auxiliary function to get debug info
    
    static int auxgetinfo (lua_State *L, const char *what, lua_Debug *ar,
                           Closure *f, CallInfo *ci)
    """
    status = 1
    for c in what:
        if c == 'S':
            funcinfo(ar, f)
        elif c == 'l':
            ar.currentline = currentline(ci) if ci and isLua(ci) else -1
        elif c == 'u':
            ar.nups = 0 if f is None else getattr(f, 'nupvalues', 0)
            if noLuaClosure(f):
                ar.isvararg = 1
                ar.nparams = 0
            else:
                ar.isvararg = f.p.is_vararg
                ar.nparams = f.p.numparams
        elif c == 't':
            ar.istailcall = (ci.callstatus & CIST_TAIL) if ci else 0
        elif c == 'n':
            ar.namewhat = getfuncname(L, ci, ar)
            if ar.namewhat is None:
                ar.namewhat = ""
                ar.name = None
        elif c in ('L', 'f'):
            pass  # handled by lua_getinfo
        else:
            status = 0  # invalid option
    
    return status


# =============================================================================
# ldebug.c:249-260 - getfuncname
# =============================================================================

def getfuncname(L: 'LuaState', ci: Optional['CallInfo'], ar: lua_Debug) -> Optional[str]:
    """
    ldebug.c:249-260 - Get function name
    
    static const char *getfuncname (lua_State *L, CallInfo *ci, const char **name)
    """
    if ci is None:
        return None
    if ci.callstatus & CIST_FIN:  # is this a finalizer?
        ar.name = "__gc"
        return "metamethod"
    # calling function is a known Lua function?
    if not (ci.callstatus & CIST_TAIL) and ci.previous and isLua(ci.previous):
        return funcnamefromcode(L, ci.previous, ar)
    return None


# =============================================================================
# ldebug.c:310-340 - lua_getinfo
# =============================================================================

def lua_getinfo(L: 'LuaState', what: str, ar: lua_Debug) -> int:
    """
    ldebug.c:310-340 - Get information about a specific function or function invocation
    
    LUA_API int lua_getinfo (lua_State *L, const char *what, lua_Debug *ar)
    """
    cl = None
    ci = None
    func = None
    
    if what.startswith('>'):
        ci = None
        func = L.stack[L.top - 1]
        what = what[1:]  # skip the '>'
        L.top -= 1  # pop function
    else:
        ci = ar.i_ci
        func = ci.func
    
    if ttisclosure(func):
        cl = clvalue(func)
    
    status = auxgetinfo(L, what, ar, cl, ci)
    
    if 'f' in what:
        setobjs2s(L, L.stack[L.top], func)
        L.top += 1
    
    if 'L' in what:
        collectvalidlines(L, cl)
    
    return status


# =============================================================================
# ldebug.c:230-246 - collectvalidlines
# =============================================================================

def collectvalidlines(L: 'LuaState', f) -> None:
    """
    ldebug.c:230-246 - Collect valid source lines
    
    static void collectvalidlines (lua_State *L, Closure *f)
    """
    from .ltable import luaH_new, luaH_setint
    from .lobject import sethvalue, setbvalue
    
    if noLuaClosure(f):
        setnilvalue(L.stack[L.top])
        L.top += 1
    else:
        lineinfo = f.p.lineinfo
        t = luaH_new(L)  # new table to store active lines
        sethvalue(L, L.stack[L.top], t)
        L.top += 1
        
        v = TValue()
        setbvalue(v, True)
        
        if lineinfo:
            for line in lineinfo:
                luaH_setint(L, t, line, v)


# =============================================================================
# ldebug.c:356-373 - kname
# =============================================================================

def kname(p: Proto, pc: int, c: int, name_out: list) -> None:
    """
    ldebug.c:356-373 - Find a "name" for the RK value 'c'
    
    static void kname (Proto *p, int pc, int c, const char **name)
    """
    if ISK(c):  # is 'c' a constant?
        kvalue = p.k[INDEXK(c)]
        if ttisstring(kvalue):
            name_out[0] = svalue(kvalue)
            return
    else:  # 'c' is a register
        what, name = getobjname(p, pc, c)
        if what and what.startswith('c'):  # found a constant name?
            name_out[0] = name
            return
    name_out[0] = "?"


# =============================================================================
# ldebug.c:376-380 - filterpc
# =============================================================================

def filterpc(pc: int, jmptarget: int) -> int:
    """ldebug.c:376-380"""
    if pc < jmptarget:  # is code conditional (inside a jump)?
        return -1  # cannot know who sets that register
    return pc  # current position sets that register


# =============================================================================
# ldebug.c:386-429 - findsetreg
# =============================================================================

def findsetreg(p: Proto, lastpc: int, reg: int) -> int:
    """
    ldebug.c:386-429 - Try to find last instruction before 'lastpc' that modified register 'reg'
    
    static int findsetreg (Proto *p, int lastpc, int reg)
    """
    setreg = -1  # keep last instruction that changed 'reg'
    jmptarget = 0  # any code before this address is conditional
    
    for pc in range(lastpc):
        if pc >= len(p.code):
            break
        i = p.code[pc]
        op = GET_OPCODE(i)
        a = GETARG_A(i)
        
        if op == OpCode.OP_LOADNIL:
            b = GETARG_B(i)
            if a <= reg <= a + b:  # set registers from 'a' to 'a+b'
                setreg = filterpc(pc, jmptarget)
        elif op == OpCode.OP_TFORCALL:
            if reg >= a + 2:  # affect all regs above its base
                setreg = filterpc(pc, jmptarget)
        elif op in (OpCode.OP_CALL, OpCode.OP_TAILCALL):
            if reg >= a:  # affect all registers above base
                setreg = filterpc(pc, jmptarget)
        elif op == OpCode.OP_JMP:
            b = GETARG_sBx(i)
            dest = pc + 1 + b
            # jump is forward and do not skip 'lastpc'?
            if pc < dest <= lastpc:
                if dest > jmptarget:
                    jmptarget = dest  # update 'jmptarget'
        else:
            if testAMode(op) and reg == a:  # any instruction that set A
                setreg = filterpc(pc, jmptarget)
    
    return setreg


# =============================================================================
# ldebug.c:432-483 - getobjname
# =============================================================================

def getobjname(p: Proto, lastpc: int, reg: int) -> Tuple[Optional[str], Optional[str]]:
    """
    ldebug.c:432-483 - Get object name for error messages
    
    static const char *getobjname (Proto *p, int lastpc, int reg, const char **name)
    
    Returns (kind, name) tuple
    """
    from .lfunc import luaF_getlocalname
    
    name = luaF_getlocalname(p, reg + 1, lastpc)
    if name:  # is a local?
        return ("local", name)
    
    # else try symbolic execution
    pc = findsetreg(p, lastpc, reg)
    if pc != -1 and pc < len(p.code):  # could find instruction?
        i = p.code[pc]
        op = GET_OPCODE(i)
        
        if op == OpCode.OP_MOVE:
            b = GETARG_B(i)  # move from 'b' to 'a'
            if b < GETARG_A(i):
                return getobjname(p, pc, b)  # get name for 'b'
        
        elif op in (OpCode.OP_GETTABUP, OpCode.OP_GETTABLE):
            k = GETARG_C(i)  # key index
            t = GETARG_B(i)  # table index
            if op == OpCode.OP_GETTABLE:
                vn = luaF_getlocalname(p, t + 1, pc)
            else:
                vn = upvalname(p, t)
            
            name_out = ["?"]
            kname(p, pc, k, name_out)
            name = name_out[0]
            
            return ("global" if vn == "_ENV" else "field", name)
        
        elif op == OpCode.OP_GETUPVAL:
            name = upvalname(p, GETARG_B(i))
            return ("upvalue", name)
        
        elif op in (OpCode.OP_LOADK, OpCode.OP_LOADKX):
            if op == OpCode.OP_LOADK:
                b = GETARG_Bx(i)
            else:
                b = GETARG_Ax(p.code[pc + 1])
            if b < len(p.k) and ttisstring(p.k[b]):
                name = svalue(p.k[b])
                return ("constant", name)
        
        elif op == OpCode.OP_SELF:
            k = GETARG_C(i)  # key index
            name_out = ["?"]
            kname(p, pc, k, name_out)
            return ("method", name_out[0])
    
    return (None, None)  # could not find reasonable name


# =============================================================================
# ldebug.c:492-536 - funcnamefromcode
# =============================================================================

def funcnamefromcode(L: 'LuaState', ci: 'CallInfo', ar: lua_Debug) -> Optional[str]:
    """
    ldebug.c:492-536 - Try to find a name for a function based on the code that called it
    
    static const char *funcnamefromcode (lua_State *L, CallInfo *ci, const char **name)
    """
    from .lstate import G
    
    tm = None
    p = ci_func(ci).p  # calling function
    pc = currentpc(ci)  # calling instruction index
    
    if pc < 0 or pc >= len(p.code):
        return None
    
    i = p.code[pc]  # calling instruction
    
    if ci.callstatus & CIST_HOOKED:  # was it called inside a hook?
        ar.name = "?"
        return "hook"
    
    op = GET_OPCODE(i)
    
    if op in (OpCode.OP_CALL, OpCode.OP_TAILCALL):
        kind, name = getobjname(p, pc, GETARG_A(i))
        ar.name = name
        return kind
    
    elif op == OpCode.OP_TFORCALL:  # for iterator
        ar.name = "for iterator"
        return "for iterator"
    
    # other instructions can do calls through metamethods
    elif op in (OpCode.OP_SELF, OpCode.OP_GETTABUP, OpCode.OP_GETTABLE):
        tm = TMS.TM_INDEX
    elif op in (OpCode.OP_SETTABUP, OpCode.OP_SETTABLE):
        tm = TMS.TM_NEWINDEX
    elif op in (OpCode.OP_ADD, OpCode.OP_SUB, OpCode.OP_MUL, OpCode.OP_MOD,
                OpCode.OP_POW, OpCode.OP_DIV, OpCode.OP_IDIV, OpCode.OP_BAND,
                OpCode.OP_BOR, OpCode.OP_BXOR, OpCode.OP_SHL, OpCode.OP_SHR):
        offset = op.value - OpCode.OP_ADD.value  # ORDER OP
        tm = TMS(offset + TMS.TM_ADD.value)  # ORDER TM
    elif op == OpCode.OP_UNM:
        tm = TMS.TM_UNM
    elif op == OpCode.OP_BNOT:
        tm = TMS.TM_BNOT
    elif op == OpCode.OP_LEN:
        tm = TMS.TM_LEN
    elif op == OpCode.OP_CONCAT:
        tm = TMS.TM_CONCAT
    elif op == OpCode.OP_EQ:
        tm = TMS.TM_EQ
    elif op == OpCode.OP_LT:
        tm = TMS.TM_LT
    elif op == OpCode.OP_LE:
        tm = TMS.TM_LE
    else:
        return None  # cannot find a reasonable name
    
    if tm is not None:
        g = G(L)
        if g.tmname and tm.value < len(g.tmname):
            ar.name = getstr(g.tmname[tm.value]).decode('utf-8', errors='replace')
        else:
            ar.name = tm.name
        return "metamethod"
    
    return None


# =============================================================================
# ldebug.c:586-589 - luaG_typeerror
# =============================================================================

def luaG_typeerror(L: 'LuaState', o: TValue, op: str) -> None:
    """
    ldebug.c:586-589 - Raise a type error
    
    l_noret luaG_typeerror (lua_State *L, const TValue *o, const char *op)
    """
    from .ltm import luaT_objtypename
    t = luaT_objtypename(L, o)
    luaG_runerror(L, f"attempt to {op} a {t} value")


# =============================================================================
# ldebug.c:592-595 - luaG_concaterror
# =============================================================================

def luaG_concaterror(L: 'LuaState', p1: TValue, p2: TValue) -> None:
    """ldebug.c:592-595 - Raise a concatenation error"""
    from .lvm import cvt2str
    if ttisstring(p1) or cvt2str(p1):
        p1 = p2
    luaG_typeerror(L, p1, "concatenate")


# =============================================================================
# ldebug.c:598-604 - luaG_opinterror
# =============================================================================

def luaG_opinterror(L: 'LuaState', p1: TValue, p2: TValue, msg: str) -> None:
    """ldebug.c:598-604 - Raise an arithmetic error"""
    from .lvm import tonumber
    ok, temp = tonumber(p1)
    if not ok:  # first operand is wrong?
        p2 = p1  # now second is wrong
    luaG_typeerror(L, p2, msg)


# =============================================================================
# ldebug.c:610-615 - luaG_tointerror
# =============================================================================

def luaG_tointerror(L: 'LuaState', p1: TValue, p2: TValue) -> None:
    """ldebug.c:610-615 - Error when both values are numbers but not integers"""
    from .lvm import tointeger
    ok, temp = tointeger(p1)
    if not ok:
        p2 = p1
    luaG_runerror(L, "number has no integer representation")


# =============================================================================
# ldebug.c:618-625 - luaG_ordererror
# =============================================================================

def luaG_ordererror(L: 'LuaState', p1: TValue, p2: TValue) -> None:
    """ldebug.c:618-625 - Raise an order comparison error"""
    from .ltm import luaT_objtypename
    t1 = luaT_objtypename(L, p1)
    t2 = luaT_objtypename(L, p2)
    if t1 == t2:
        luaG_runerror(L, f"attempt to compare two {t1} values")
    else:
        luaG_runerror(L, f"attempt to compare {t1} with {t2}")


# =============================================================================
# ldebug.c:629-638 - luaG_addinfo
# =============================================================================

def luaG_addinfo(L: 'LuaState', msg: str, src: Optional['TString'], line: int) -> str:
    """
    ldebug.c:629-638 - Add src:line information to 'msg'
    
    const char *luaG_addinfo (lua_State *L, const char *msg, TString *src, int line)
    """
    from .lobject import luaO_chunkid
    
    if src:
        buff = luaO_chunkid(getstr(src).decode('utf-8', errors='replace'), LUA_IDSIZE)
    else:
        buff = "?"
    
    return f"{buff}:{line}: {msg}"


# =============================================================================
# ldebug.c:641-650 - luaG_errormsg
# =============================================================================

def luaG_errormsg(L: 'LuaState') -> None:
    """
    ldebug.c:641-650 - Raise error message
    
    l_noret luaG_errormsg (lua_State *L)
    """
    from .ldo import luaD_throw
    
    if L.errfunc != 0:  # is there an error handling function?
        # TODO: Call error handler
        pass
    
    luaD_throw(L, LUA_ERRRUN)


# =============================================================================
# ldebug.c:653-664 - luaG_runerror
# =============================================================================

def luaG_runerror(L: 'LuaState', fmt: str, *args) -> None:
    """
    ldebug.c:653-664 - Raise a runtime error
    
    l_noret luaG_runerror (lua_State *L, const char *fmt, ...)
    """
    msg = fmt % args if args else fmt
    ci = L.ci
    
    if ci and isLua(ci):
        p = ci_func(ci).p
        msg = luaG_addinfo(L, msg, p.source, currentline(ci))
    
    raise RuntimeError(msg)


# =============================================================================
# ldebug.c:667-699 - luaG_traceexec
# =============================================================================

def luaG_traceexec(L: 'LuaState') -> None:
    """
    ldebug.c:667-699 - Trace execution (for hooks)
    
    void luaG_traceexec (lua_State *L)
    """
    from .ldo import luaD_hook
    
    ci = L.ci
    mask = L.hookmask
    L.hookcount -= 1
    counthook = (L.hookcount == 0 and (mask & LUA_MASKCOUNT))
    
    if counthook:
        resethookcount(L)  # reset count
    elif not (mask & LUA_MASKLINE):
        return  # no line hook and count != 0; nothing to be done
    
    if ci.callstatus & CIST_HOOKYIELD:  # called hook last time?
        ci.callstatus &= ~CIST_HOOKYIELD  # erase mark
        return  # do not call hook again
    
    if counthook:
        luaD_hook(L, LUA_HOOKCOUNT, -1)  # call count hook
    
    if mask & LUA_MASKLINE:
        p = ci_func(ci).p
        npc = pcRel(ci.savedpc, p)
        newline = getfuncline(p, npc)
        if npc == 0 or ci.savedpc <= L.oldpc or newline != getfuncline(p, pcRel(L.oldpc, p)):
            luaD_hook(L, LUA_HOOKLINE, newline)  # call line hook
    
    L.oldpc = ci.savedpc
    
    if L.status == LUA_YIELD:  # did hook yield?
        if counthook:
            L.hookcount = 1  # undo decrement to zero
        ci.savedpc -= 1  # undo increment
        ci.callstatus |= CIST_HOOKYIELD  # mark that it yielded


# =============================================================================
# Helper Functions
# =============================================================================

def isLua(ci: 'CallInfo') -> bool:
    """Check if CallInfo is for a Lua function"""
    if ci is None:
        return False
    # Check if ci.func is a Lua closure
    func = ci.func
    if func is None:
        return False
    return ttisLclosure(func)


# CallInfo status bits (from lstate.h)
CIST_OAH = 1 << 0    # original value of 'allowhook'
CIST_LUA = 1 << 1    # call is running a Lua function
CIST_HOOKED = 1 << 2  # call is running a debug hook
CIST_FRESH = 1 << 3   # call is running on a fresh invocation of luaV_execute
CIST_YPCALL = 1 << 4  # call is a yieldable protected call
CIST_TAIL = 1 << 5    # call was tail called
CIST_HOOKYIELD = 1 << 6  # last hook called yielded
CIST_LEQ = 1 << 7     # using __le instead of __lt
CIST_FIN = 1 << 8     # call is running a finalizer
