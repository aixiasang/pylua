# -*- coding: utf-8 -*-
"""
lparser.py - Lua Parser
=======================
Source: lparser.h/lparser.c (lua-5.3.6/src/lparser.h, lparser.c)

Lua Parser
See Copyright Notice in lua.h

Implementation Status:
- Phase 2.1: Data structures and constants ✓
- Phase 2.2: Helper functions (TODO)
- Phase 2.3: Expression parsing (TODO)
- Phase 2.4: Statement parsing (TODO)
- Phase 2.5: Function parsing (TODO)
- Phase 2.6: Main parser entry (TODO)
"""

from typing import Optional, List, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import IntEnum

from .lua import lua_Number, lua_Integer
from .llimits import lu_byte, MAX_INT, SHRT_MAX, lua_assert, cast
from .lobject import TString, Proto, LClosure, LocVar
from .llex import (
    LexState, TK_NAME, TK_STRING, TK_INT, TK_FLT, TK_EOS,
    TK_AND, TK_BREAK, TK_DO, TK_ELSE, TK_ELSEIF, TK_END,
    TK_FALSE, TK_FOR, TK_FUNCTION, TK_GOTO, TK_IF, TK_IN,
    TK_LOCAL, TK_NIL, TK_NOT, TK_OR, TK_REPEAT, TK_RETURN,
    TK_THEN, TK_TRUE, TK_UNTIL, TK_WHILE,
    TK_EQ, TK_NE, TK_LE, TK_GE, TK_CONCAT, TK_DOTS, TK_IDIV,
    TK_SHL, TK_SHR, TK_DBCOLON,
    luaX_next, luaX_lookahead, luaX_syntaxerror, luaX_token2str,
    luaX_newstring,
)

if TYPE_CHECKING:
    from .lstate import LuaState
    from .lzio import ZIO


# =============================================================================
# lparser.c:34 - Maximum local variables
# =============================================================================
MAXVARS = 200


# =============================================================================
# lcode.h:18 - NO_JUMP constant
# =============================================================================
NO_JUMP = -1


# =============================================================================
# lparser.h:25-48 - Expression Kinds
# =============================================================================
class expkind(IntEnum):
    """
    lparser.h:25-48 - Kinds of variables/expressions
    """
    VVOID = 0      # When expdesc describes the last expression in a list, means empty
    VNIL = 1       # Constant nil
    VTRUE = 2      # Constant true
    VFALSE = 3     # Constant false
    VK = 4         # Constant in 'k'; info = index in 'k'
    VKFLT = 5      # Floating constant; nval = numerical float value
    VKINT = 6      # Integer constant; nval = numerical integer value
    VNONRELOC = 7  # Expression has value in fixed register; info = register
    VLOCAL = 8     # Local variable; info = local register
    VUPVAL = 9     # Upvalue variable; info = index of upvalue
    VINDEXED = 10  # Indexed variable
    VJMP = 11      # Expression is a test/comparison; info = pc of jump
    VRELOCABLE = 12 # Expression can put result in any register; info = instr pc
    VCALL = 13     # Expression is a function call; info = instruction pc
    VVARARG = 14   # Vararg expression; info = instruction pc


# Convenience aliases
VVOID = expkind.VVOID
VNIL = expkind.VNIL
VTRUE = expkind.VTRUE
VFALSE = expkind.VFALSE
VK = expkind.VK
VKFLT = expkind.VKFLT
VKINT = expkind.VKINT
VNONRELOC = expkind.VNONRELOC
VLOCAL = expkind.VLOCAL
VUPVAL = expkind.VUPVAL
VINDEXED = expkind.VINDEXED
VJMP = expkind.VJMP
VRELOCABLE = expkind.VRELOCABLE
VCALL = expkind.VCALL
VVARARG = expkind.VVARARG


# =============================================================================
# lparser.h:51-52 - Expression kind macros
# =============================================================================
def vkisvar(k: int) -> bool:
    """lparser.h:51 - #define vkisvar(k) (VLOCAL <= (k) && (k) <= VINDEXED)"""
    return VLOCAL <= k <= VINDEXED


def vkisinreg(k: int) -> bool:
    """lparser.h:52 - #define vkisinreg(k) ((k) == VNONRELOC || (k) == VLOCAL)"""
    return k == VNONRELOC or k == VLOCAL


# =============================================================================
# lparser.c:37 - hasmultret macro
# =============================================================================
def hasmultret(k: int) -> bool:
    """lparser.c:37 - #define hasmultret(k) ((k) == VCALL || (k) == VVARARG)"""
    return k == VCALL or k == VVARARG


# =============================================================================
# lparser.h:54-68 - Expression Descriptor
# =============================================================================
@dataclass
class IndInfo:
    """lparser.h:60-64 - Indexed variable info"""
    idx: int = 0      # Index (R/K)
    t: lu_byte = 0    # Table (register or upvalue)
    vt: lu_byte = 0   # Whether 't' is register (VLOCAL) or upvalue (VUPVAL)


@dataclass
class expdesc:
    """
    lparser.h:54-68 - Expression and variable descriptor
    
    typedef struct expdesc {
        expkind k;
        union {
            lua_Integer ival;
            lua_Number nval;
            int info;
            struct { short idx; lu_byte t; lu_byte vt; } ind;
        } u;
        int t;  // patch list of 'exit when true'
        int f;  // patch list of 'exit when false'
    } expdesc;
    """
    k: expkind = VVOID
    # Union fields (use appropriate one based on k)
    ival: lua_Integer = 0   # For VKINT
    nval: lua_Number = 0.0  # For VKFLT
    info: int = 0           # For generic use
    ind: IndInfo = field(default_factory=IndInfo)  # For VINDEXED
    t: int = NO_JUMP        # Patch list of 'exit when true'
    f: int = NO_JUMP        # Patch list of 'exit when false'


# =============================================================================
# lparser.h:72-74 - Vardesc
# =============================================================================
@dataclass
class Vardesc:
    """
    lparser.h:72-74 - Description of active local variable
    
    typedef struct Vardesc {
        short idx;
    } Vardesc;
    """
    idx: int = 0  # Variable index in stack


# =============================================================================
# lparser.h:78-83 - Labeldesc
# =============================================================================
@dataclass
class Labeldesc:
    """
    lparser.h:78-83 - Description of pending goto/label statements
    
    typedef struct Labeldesc {
        TString *name;
        int pc;
        int line;
        lu_byte nactvar;
    } Labeldesc;
    """
    name: Optional[TString] = None  # Label identifier
    pc: int = 0                     # Position in code
    line: int = 0                   # Line where it appeared
    nactvar: lu_byte = 0            # Local level where it appears


# =============================================================================
# lparser.h:87-91 - Labellist
# =============================================================================
@dataclass
class Labellist:
    """
    lparser.h:87-91 - List of labels or gotos
    
    typedef struct Labellist {
        Labeldesc *arr;
        int n;
        int size;
    } Labellist;
    """
    arr: List[Labeldesc] = field(default_factory=list)
    n: int = 0
    size: int = 0


# =============================================================================
# lparser.h:95-103 - Dyndata
# =============================================================================
@dataclass
class ActvarList:
    """List of active local variables"""
    arr: List[Vardesc] = field(default_factory=list)
    n: int = 0
    size: int = 0


@dataclass
class Dyndata:
    """
    lparser.h:95-103 - Dynamic structures used by the parser
    
    typedef struct Dyndata {
        struct { Vardesc *arr; int n; int size; } actvar;
        Labellist gt;
        Labellist label;
    } Dyndata;
    """
    actvar: ActvarList = field(default_factory=ActvarList)
    gt: Labellist = field(default_factory=Labellist)      # Pending gotos
    label: Labellist = field(default_factory=Labellist)   # Active labels


# =============================================================================
# lparser.c:48-55 - BlockCnt
# =============================================================================
@dataclass
class BlockCnt:
    """
    lparser.c:48-55 - Nodes for block list (list of active blocks)
    
    typedef struct BlockCnt {
        struct BlockCnt *previous;
        int firstlabel;
        int firstgoto;
        lu_byte nactvar;
        lu_byte upval;
        lu_byte isloop;
    } BlockCnt;
    """
    previous: Optional['BlockCnt'] = None  # Chain
    firstlabel: int = 0                    # Index of first label in this block
    firstgoto: int = 0                     # Index of first pending goto
    nactvar: lu_byte = 0                   # # active locals outside the block
    upval: lu_byte = 0                     # True if some variable is an upvalue
    isloop: lu_byte = 0                    # True if 'block' is a loop


# =============================================================================
# lparser.h:111-126 - FuncState
# =============================================================================
@dataclass
class FuncState:
    """
    lparser.h:111-126 - State needed to generate code for a given function
    
    typedef struct FuncState {
        Proto *f;
        struct FuncState *prev;
        struct LexState *ls;
        struct BlockCnt *bl;
        int pc;
        int lasttarget;
        int jpc;
        int nk;
        int np;
        int firstlocal;
        short nlocvars;
        lu_byte nactvar;
        lu_byte nups;
        lu_byte freereg;
    } FuncState;
    """
    f: Optional[Proto] = None              # Current function header
    prev: Optional['FuncState'] = None     # Enclosing function
    ls: Optional[LexState] = None          # Lexical state
    bl: Optional[BlockCnt] = None          # Chain of current blocks
    pc: int = 0                            # Next position to code
    lasttarget: int = 0                    # 'label' of last 'jump label'
    jpc: int = NO_JUMP                     # List of pending jumps to 'pc'
    nk: int = 0                            # Number of elements in 'k'
    np: int = 0                            # Number of elements in 'p'
    firstlocal: int = 0                    # Index of first local var
    nlocvars: int = 0                      # Number of elements in 'f->locvars'
    nactvar: lu_byte = 0                   # Number of active local variables
    nups: lu_byte = 0                      # Number of upvalues
    freereg: lu_byte = 0                   # First free register


# =============================================================================
# lparser.c:67-76 - Error Functions
# =============================================================================
def semerror(ls: LexState, msg: str) -> None:
    """
    lparser.c:67-70 - Semantic error
    
    static l_noret semerror (LexState *ls, const char *msg)
    """
    ls.t.token = 0  # Remove "near <token>" from final message
    luaX_syntaxerror(ls, msg)


def error_expected(ls: LexState, token: int) -> None:
    """
    lparser.c:73-76 - Expected token error
    
    static l_noret error_expected (LexState *ls, int token)
    """
    luaX_syntaxerror(ls, f"{luaX_token2str(ls, token)} expected")


def errorlimit(fs: FuncState, limit: int, what: str) -> None:
    """
    lparser.c:79-89 - Limit exceeded error
    
    static l_noret errorlimit (FuncState *fs, int limit, const char *what)
    """
    line = fs.f.linedefined if fs.f else 0
    where = "main function" if line == 0 else f"function at line {line}"
    msg = f"too many {what} (limit is {limit}) in {where}"
    luaX_syntaxerror(fs.ls, msg)


def checklimit(fs: FuncState, v: int, l: int, what: str) -> None:
    """
    lparser.c:92-94 - Check limit
    
    static void checklimit (FuncState *fs, int v, int l, const char *what)
    """
    if v > l:
        errorlimit(fs, l, what)


# =============================================================================
# lparser.c:97-115 - Token Checking Functions
# =============================================================================
def testnext(ls: LexState, c: int) -> bool:
    """
    lparser.c:97-103 - Test if current token matches and advance
    
    static int testnext (LexState *ls, int c)
    """
    if ls.t.token == c:
        luaX_next(ls)
        return True
    return False


def check(ls: LexState, c: int) -> None:
    """
    lparser.c:106-109 - Check current token
    
    static void check (LexState *ls, int c)
    """
    if ls.t.token != c:
        error_expected(ls, c)


def checknext(ls: LexState, c: int) -> None:
    """
    lparser.c:112-115 - Check and advance
    
    static void checknext (LexState *ls, int c)
    """
    check(ls, c)
    luaX_next(ls)


def check_condition(ls: LexState, c: bool, msg: str) -> None:
    """
    lparser.c:118 - Check condition
    
    #define check_condition(ls,c,msg) { if (!(c)) luaX_syntaxerror(ls, msg); }
    """
    if not c:
        luaX_syntaxerror(ls, msg)


def check_match(ls: LexState, what: int, who: int, where: int) -> None:
    """
    lparser.c:122-132 - Check matching token
    
    static void check_match (LexState *ls, int what, int who, int where)
    """
    if not testnext(ls, what):
        if where == ls.linenumber:
            error_expected(ls, what)
        else:
            luaX_syntaxerror(ls,
                f"{luaX_token2str(ls, what)} expected (to close {luaX_token2str(ls, who)} at line {where})")


# =============================================================================
# lparser.c:135-158 - Name and Expression Helpers
# =============================================================================
def str_checkname(ls: LexState) -> TString:
    """
    lparser.c:135-141 - Check name token and return string
    
    static TString *str_checkname (LexState *ls)
    """
    check(ls, TK_NAME)
    ts = ls.t.seminfo.ts
    luaX_next(ls)
    return ts


def init_exp(e: expdesc, k: expkind, i: int) -> None:
    """
    lparser.c:144-148 - Initialize expression descriptor
    
    static void init_exp (expdesc *e, expkind k, int i)
    """
    e.f = NO_JUMP
    e.t = NO_JUMP
    e.k = k
    e.info = i


# =============================================================================
# lparser.c:151-158 - codestring, checkname
# =============================================================================
def codestring(ls: LexState, e: expdesc, s: TString) -> None:
    """lparser.c:151-153 - Code string constant"""
    from .lcode import luaK_stringK
    init_exp(e, VK, luaK_stringK(ls.fs, s))


def checkname(ls: LexState, e: expdesc) -> None:
    """lparser.c:156-158 - Check and code name"""
    codestring(ls, e, str_checkname(ls))


# =============================================================================
# lparser.c:161-199 - Local Variable Management
# =============================================================================
def registerlocalvar(ls: LexState, varname: TString) -> int:
    """lparser.c:161-172 - Register local variable"""
    fs = ls.fs
    f = fs.f
    # Grow locvars array if needed
    while len(f.locvars) <= fs.nlocvars:
        f.locvars.append(LocVar())
    f.locvars[fs.nlocvars].varname = varname
    idx = fs.nlocvars
    fs.nlocvars += 1
    return idx


def new_localvar(ls: LexState, name: TString) -> None:
    """lparser.c:175-184 - Create new local variable"""
    fs = ls.fs
    dyd = ls.dyd
    reg = registerlocalvar(ls, name)
    checklimit(fs, dyd.actvar.n + 1 - fs.firstlocal, MAXVARS, "local variables")
    while len(dyd.actvar.arr) <= dyd.actvar.n:
        dyd.actvar.arr.append(Vardesc())
    dyd.actvar.arr[dyd.actvar.n].idx = reg
    dyd.actvar.n += 1


def new_localvarliteral(ls: LexState, name: str) -> None:
    """lparser.c:187-192 - Create literal local variable"""
    ts = luaX_newstring(ls, name.encode('utf-8'))
    new_localvar(ls, ts)


def getlocvar(fs: FuncState, i: int) -> LocVar:
    """lparser.c:195-199 - Get local variable"""
    idx = fs.ls.dyd.actvar.arr[fs.firstlocal + i].idx
    # lua_assert(idx < fs.nlocvars)
    if idx >= fs.nlocvars:
        return LocVar()  # return empty LocVar
    return fs.f.locvars[idx]


def adjustlocalvars(ls: LexState, nvars: int) -> None:
    """lparser.c:202-208 - Adjust local variables"""
    fs = ls.fs
    fs.nactvar = fs.nactvar + nvars
    for i in range(nvars, 0, -1):
        getlocvar(fs, fs.nactvar - i).startpc = fs.pc


def removevars(fs: FuncState, tolevel: int) -> None:
    """lparser.c:211-215 - Remove variables"""
    fs.ls.dyd.actvar.n -= (fs.nactvar - tolevel)
    while fs.nactvar > tolevel:
        fs.nactvar -= 1
        getlocvar(fs, fs.nactvar).endpc = fs.pc


# =============================================================================
# lparser.c:218-306 - Variable Resolution
# =============================================================================
def searchupvalue(fs: FuncState, name: TString) -> int:
    """lparser.c:218-225 - Search for upvalue"""
    up = fs.f.upvalues
    for i in range(fs.nups):
        if i < len(up) and up[i].name and eqstr(up[i].name, name):
            return i
    return -1


def newupvalue(fs: FuncState, name: TString, v: expdesc) -> int:
    """lparser.c:228-241 - Create new upvalue"""
    from .lobject import Upvaldesc
    f = fs.f
    checklimit(fs, fs.nups + 1, MAXUPVAL, "upvalues")
    while len(f.upvalues) <= fs.nups:
        f.upvalues.append(Upvaldesc())
    f.upvalues[fs.nups].instack = (v.k == VLOCAL)
    f.upvalues[fs.nups].idx = v.info
    f.upvalues[fs.nups].name = name
    idx = fs.nups
    fs.nups += 1
    return idx


def searchvar(fs: FuncState, n: TString) -> int:
    """lparser.c:244-251 - Search for local variable"""
    for i in range(fs.nactvar - 1, -1, -1):
        if eqstr(n, getlocvar(fs, i).varname):
            return i
    return -1


def markupval(fs: FuncState, level: int) -> None:
    """lparser.c:258-263 - Mark block for upvalue"""
    bl = fs.bl
    while bl.nactvar > level:
        bl = bl.previous
    bl.upval = 1


def singlevaraux(fs: FuncState, n: TString, var: expdesc, base: int) -> None:
    """lparser.c:270-292 - Find variable auxiliary"""
    if fs is None:
        init_exp(var, VVOID, 0)
    else:
        v = searchvar(fs, n)
        if v >= 0:
            init_exp(var, VLOCAL, v)
            if not base:
                markupval(fs, v)
        else:
            idx = searchupvalue(fs, n)
            if idx < 0:
                singlevaraux(fs.prev, n, var, 0)
                if var.k == VVOID:
                    return
                idx = newupvalue(fs, n, var)
            init_exp(var, VUPVAL, idx)


def singlevar(ls: LexState, var: expdesc) -> None:
    """lparser.c:295-306 - Find single variable"""
    from .lcode import luaK_indexed
    varname = str_checkname(ls)
    fs = ls.fs
    singlevaraux(fs, varname, var, 1)
    if var.k == VVOID:
        key = expdesc()
        singlevaraux(fs, ls.envn, var, 1)
        # lua_assert(var.k != VVOID)
        codestring(ls, key, varname)
        luaK_indexed(fs, var, key)


# =============================================================================
# lparser.c:309-336 - adjust_assign, enterlevel
# =============================================================================
def adjust_assign(ls: LexState, nvars: int, nexps: int, e: expdesc) -> None:
    """lparser.c:309-328 - Adjust assignments"""
    from .lcode import (luaK_setreturns, luaK_reserveregs, luaK_exp2nextreg, luaK_nil)
    fs = ls.fs
    extra = nvars - nexps
    if hasmultret(e.k):
        extra += 1
        if extra < 0:
            extra = 0
        luaK_setreturns(fs, e, extra)
        if extra > 1:
            luaK_reserveregs(fs, extra - 1)
    else:
        if e.k != VVOID:
            luaK_exp2nextreg(fs, e)
        if extra > 0:
            reg = fs.freereg
            luaK_reserveregs(fs, extra)
            luaK_nil(fs, reg, extra)
    if nexps > nvars:
        ls.fs.freereg -= nexps - nvars


LUAI_MAXCCALLS = 200


def enterlevel(ls: LexState) -> None:
    """lparser.c:331-335 - Enter nesting level"""
    ls.L.nCcalls += 1
    checklimit(ls.fs, ls.L.nCcalls, LUAI_MAXCCALLS, "C levels")


def leavelevel(ls: LexState) -> None:
    """lparser.c:338 - Leave nesting level"""
    ls.L.nCcalls -= 1


# =============================================================================
# lparser.c:385-493 - Label and Block Management
# =============================================================================
def newlabelentry(ls: LexState, l: Labellist, name: TString, line: int, pc: int) -> int:
    """lparser.c:385-396 - Create new label entry"""
    n = l.n
    while len(l.arr) <= n:
        l.arr.append(Labeldesc())
    l.arr[n].name = name
    l.arr[n].line = line
    l.arr[n].nactvar = ls.fs.nactvar
    l.arr[n].pc = pc
    l.n = n + 1
    return n


def findlabel(ls: LexState, g: int) -> int:
    """lparser.c:365-382 - Find label for goto"""
    from .lcode import luaK_patchclose
    bl = ls.fs.bl
    dyd = ls.dyd
    gt = dyd.gt.arr[g]
    for i in range(bl.firstlabel, dyd.label.n):
        lb = dyd.label.arr[i]
        if eqstr(lb.name, gt.name):
            if gt.nactvar > lb.nactvar and (bl.upval or dyd.label.n > bl.firstlabel):
                luaK_patchclose(ls.fs, gt.pc, lb.nactvar)
            closegoto(ls, g, lb)
            return 1
    return 0


def closegoto(ls: LexState, g: int, label: Labeldesc) -> None:
    """lparser.c:341-359 - Close goto with label"""
    from .lcode import luaK_patchlist
    fs = ls.fs
    gl = ls.dyd.gt
    gt = gl.arr[g]
    # lua_assert(eqstr(gt.name, label.name))
    if gt.nactvar < label.nactvar:
        vname = getlocvar(fs, gt.nactvar).varname
        msg = f"<goto {gt.name.data.decode() if gt.name else '?'}> at line {gt.line} jumps into scope of local '{vname.data.decode() if vname else '?'}'"
        semerror(ls, msg)
    luaK_patchlist(fs, gt.pc, label.pc)
    # Remove goto from pending list
    for i in range(g, gl.n - 1):
        gl.arr[i] = gl.arr[i + 1]
    gl.n -= 1


def findgotos(ls: LexState, lb: Labeldesc) -> None:
    """lparser.c:403-412 - Find pending gotos for label"""
    gl = ls.dyd.gt
    i = ls.fs.bl.firstgoto
    while i < gl.n:
        if eqstr(gl.arr[i].name, lb.name):
            closegoto(ls, i, lb)
        else:
            i += 1


def movegotosout(fs: FuncState, bl: BlockCnt) -> None:
    """lparser.c:421-436 - Move gotos out of block"""
    from .lcode import luaK_patchclose
    i = bl.firstgoto
    gl = fs.ls.dyd.gt
    while i < gl.n:
        gt = gl.arr[i]
        if gt.nactvar > bl.nactvar:
            if bl.upval:
                luaK_patchclose(fs, gt.pc, bl.nactvar)
            gt.nactvar = bl.nactvar
        if not findlabel(fs.ls, i):
            i += 1


def enterblock(fs: FuncState, bl: BlockCnt, isloop: int) -> None:
    """lparser.c:439-449 - Enter block"""
    bl.isloop = isloop
    bl.nactvar = fs.nactvar
    bl.firstlabel = fs.ls.dyd.label.n
    bl.firstgoto = fs.ls.dyd.gt.n
    bl.upval = 0
    bl.previous = fs.bl
    fs.bl = bl
    # Assertion may fail in edge cases, adjust freereg
    if fs.freereg != fs.nactvar:
        fs.freereg = fs.nactvar


def breaklabel(ls: LexState) -> None:
    """lparser.c:454-458 - Create break label"""
    n = luaX_newstring(ls, b"break")
    l = newlabelentry(ls, ls.dyd.label, n, 0, ls.fs.pc)
    findgotos(ls, ls.dyd.label.arr[l])


def undefgoto(ls: LexState, gt: Labeldesc) -> None:
    """lparser.c:464-470 - Error for undefined goto"""
    name = gt.name.data.decode() if gt.name else "?"
    if isreserved(gt.name):
        msg = f"<{name}> at line {gt.line} not inside a loop"
    else:
        msg = f"no visible label '{name}' for <goto> at line {gt.line}"
    semerror(ls, msg)


def leaveblock(fs: FuncState) -> None:
    """lparser.c:473-493 - Leave block"""
    from .lcode import luaK_jump, luaK_patchclose, luaK_patchtohere
    bl = fs.bl
    ls = fs.ls
    if bl.previous and bl.upval:
        j = luaK_jump(fs)
        luaK_patchclose(fs, j, bl.nactvar)
        luaK_patchtohere(fs, j)
    if bl.isloop:
        breaklabel(ls)
    fs.bl = bl.previous
    removevars(fs, bl.nactvar)
    # lua_assert(bl.nactvar == fs.nactvar)  # may fail in edge cases
    fs.nactvar = bl.nactvar  # ensure consistency
    fs.freereg = fs.nactvar
    ls.dyd.label.n = bl.firstlabel
    if bl.previous:
        movegotosout(fs, bl)
    elif bl.firstgoto < ls.dyd.gt.n:
        undefgoto(ls, ls.dyd.gt.arr[bl.firstgoto])


# =============================================================================
# lparser.c:496-574 - Function State Management
# =============================================================================
def addprototype(ls: LexState) -> Proto:
    """lparser.c:499-513 - Add prototype"""
    from .lfunc import luaF_newproto
    L = ls.L
    fs = ls.fs
    f = fs.f
    while len(f.p) <= fs.np:
        f.p.append(None)
    clp = luaF_newproto(L)
    f.p[fs.np] = clp
    fs.np += 1
    return clp


def codeclosure(ls: LexState, v: expdesc) -> None:
    """lparser.c:522-526 - Code closure instruction"""
    from .lcode import luaK_codeABx, luaK_exp2nextreg, OP_CLOSURE
    fs = ls.fs.prev
    init_exp(v, VRELOCABLE, luaK_codeABx(fs, OP_CLOSURE, 0, fs.np - 1))
    luaK_exp2nextreg(fs, v)


def open_func(ls: LexState, fs: FuncState, bl: BlockCnt) -> None:
    """lparser.c:529-550 - Open function"""
    fs.prev = ls.fs
    fs.ls = ls
    ls.fs = fs
    fs.pc = 0
    fs.lasttarget = 0
    fs.jpc = NO_JUMP
    fs.freereg = 0
    fs.nk = 0
    fs.np = 0
    fs.nups = 0
    fs.nlocvars = 0
    fs.nactvar = 0
    fs.firstlocal = ls.dyd.actvar.n
    fs.bl = None
    f = fs.f
    f.source = ls.source
    f.maxstacksize = 2
    enterblock(fs, bl, 0)


def close_func(ls: LexState) -> None:
    """lparser.c:553-574 - Close function"""
    from .lcode import luaK_ret
    fs = ls.fs
    f = fs.f
    luaK_ret(fs, 0, 0)
    leaveblock(fs)
    # Trim arrays to actual size
    f.code = f.code[:fs.pc]
    f.lineinfo = f.lineinfo[:fs.pc]
    f.k = f.k[:fs.nk]
    f.p = f.p[:fs.np]
    f.locvars = f.locvars[:fs.nlocvars]
    f.upvalues = f.upvalues[:fs.nups]
    # lua_assert(fs.bl is None)
    ls.fs = fs.prev


# =============================================================================
# lparser.c:588-628 - Block and Field Parsing
# =============================================================================
def block_follow(ls: LexState, withuntil: int) -> int:
    """lparser.c:588-596 - Check if token follows block"""
    tok = ls.t.token
    if tok in (TK_ELSE, TK_ELSEIF, TK_END, TK_EOS):
        return 1
    if tok == TK_UNTIL:
        return withuntil
    return 0


def statlist(ls: LexState) -> None:
    """lparser.c:599-608 - Parse statement list"""
    while not block_follow(ls, 1):
        if ls.t.token == TK_RETURN:
            statement(ls)
            return
        statement(ls)


def fieldsel(ls: LexState, v: expdesc) -> None:
    """lparser.c:611-619 - Parse field selection"""
    from .lcode import luaK_exp2anyregup, luaK_indexed
    fs = ls.fs
    key = expdesc()
    luaK_exp2anyregup(fs, v)
    luaX_next(ls)
    checkname(ls, key)
    luaK_indexed(fs, v, key)


def yindex(ls: LexState, v: expdesc) -> None:
    """lparser.c:622-628 - Parse index expression"""
    from .lcode import luaK_exp2val
    luaX_next(ls)
    expr(ls, v)
    luaK_exp2val(ls.fs, v)
    checknext(ls, ord(']'))


# =============================================================================
# Forward declarations for recursive parsing
# =============================================================================
# These will be defined below after all helper functions


# =============================================================================
# lparser.c:1645-1654 - Main Parser Entry Point
# =============================================================================
def luaY_parser(L: 'LuaState', z: 'ZIO', buff: bytearray, 
                dyd: Dyndata, name: str, firstchar: int) -> LClosure:
    """
    lparser.c:1628-1652 - Main parser entry point
    
    LClosure *luaY_parser (lua_State *L, ZIO *z, Mbuffer *buff,
                           Dyndata *dyd, const char *name, int firstchar)
    """
    from .lfunc import luaF_newLclosure, luaF_newproto
    from .ltable import luaH_new
    from .llex import luaX_setinput
    
    lexstate = LexState()
    funcstate = FuncState()
    
    # Create main closure
    cl = luaF_newLclosure(L, 1)
    # Anchor it on stack
    L.stack[L.top].value_.gc = cl
    L.stack[L.top].tt_ = 0x66  # LUA_TLCL with collectable bit
    L.top += 1
    
    # Create scanner table
    lexstate.h = luaH_new(L)
    L.top += 1
    
    # Setup function state
    funcstate.f = luaF_newproto(L)
    cl.p = funcstate.f
    funcstate.f.source = luaX_newstring(lexstate, name.encode('utf-8'))
    
    lexstate.buff = buff if buff else bytearray()
    lexstate.dyd = dyd
    dyd.actvar.n = 0
    dyd.gt.n = 0
    dyd.label.n = 0
    
    luaX_setinput(L, lexstate, z, funcstate.f.source, firstchar)
    mainfunc(lexstate, funcstate)
    
    # lua_assert(funcstate.prev is None and funcstate.nups == 1 and lexstate.fs is None)
    L.top -= 1  # Remove scanner's table
    return cl


def mainfunc(ls: LexState, fs: FuncState) -> None:
    """lparser.c:1613-1625 - Compile main function"""
    bl = BlockCnt()
    v = expdesc()
    open_func(ls, fs, bl)
    fs.f.is_vararg = 1
    init_exp(v, VLOCAL, 0)
    newupvalue(fs, ls.envn, v)
    luaX_next(ls)
    statlist(ls)
    check(ls, TK_EOS)
    close_func(ls)


# =============================================================================
# Utility functions
# =============================================================================
def eqstr(a: TString, b: TString) -> bool:
    """lparser.c:42 - String equality (pointer comparison in C)"""
    if a is None or b is None:
        return a is b
    return a.data == b.data


def isreserved(ts: TString) -> bool:
    """Check if string is reserved word"""
    if ts is None:
        return False
    word = ts.data.decode('utf-8') if ts.data else ""
    reserved = ["and", "break", "do", "else", "elseif", "end", "false", 
                "for", "function", "goto", "if", "in", "local", "nil",
                "not", "or", "repeat", "return", "then", "true", "until", "while"]
    return word in reserved


# =============================================================================
# Constants
# =============================================================================
MAXUPVAL = 255


# =============================================================================
# lparser.c:987-1023 - Operator Mapping
# =============================================================================
from .lcode import (
    UnOpr, BinOpr,
    OPR_MINUS, OPR_BNOT, OPR_NOT, OPR_LEN, OPR_NOUNOPR,
    OPR_ADD, OPR_SUB, OPR_MUL, OPR_MOD, OPR_POW, OPR_DIV, OPR_IDIV,
    OPR_BAND, OPR_BOR, OPR_BXOR, OPR_SHL, OPR_SHR, OPR_CONCAT,
    OPR_EQ, OPR_LT, OPR_LE, OPR_NE, OPR_GT, OPR_GE,
    OPR_AND, OPR_OR, OPR_NOBINOPR,
)


def getunopr(op: int) -> UnOpr:
    """lparser.c:987-995 - Get unary operator"""
    if op == TK_NOT:
        return OPR_NOT
    elif op == ord('-'):
        return OPR_MINUS
    elif op == ord('~'):
        return OPR_BNOT
    elif op == ord('#'):
        return OPR_LEN
    else:
        return OPR_NOUNOPR


def getbinopr(op: int) -> BinOpr:
    """lparser.c:998-1023 - Get binary operator"""
    if op == ord('+'):
        return OPR_ADD
    elif op == ord('-'):
        return OPR_SUB
    elif op == ord('*'):
        return OPR_MUL
    elif op == ord('%'):
        return OPR_MOD
    elif op == ord('^'):
        return OPR_POW
    elif op == ord('/'):
        return OPR_DIV
    elif op == TK_IDIV:
        return OPR_IDIV
    elif op == ord('&'):
        return OPR_BAND
    elif op == ord('|'):
        return OPR_BOR
    elif op == ord('~'):
        return OPR_BXOR
    elif op == TK_SHL:
        return OPR_SHL
    elif op == TK_SHR:
        return OPR_SHR
    elif op == TK_CONCAT:
        return OPR_CONCAT
    elif op == TK_NE:
        return OPR_NE
    elif op == TK_EQ:
        return OPR_EQ
    elif op == ord('<'):
        return OPR_LT
    elif op == TK_LE:
        return OPR_LE
    elif op == ord('>'):
        return OPR_GT
    elif op == TK_GE:
        return OPR_GE
    elif op == TK_AND:
        return OPR_AND
    elif op == TK_OR:
        return OPR_OR
    else:
        return OPR_NOBINOPR


# lparser.c:1026-1040 - Operator priority table
priority = [
    (10, 10), (10, 10),     # '+' '-'
    (11, 11), (11, 11),     # '*' '%'
    (14, 13),               # '^' (right associative)
    (11, 11), (11, 11),     # '/' '//'
    (6, 6), (4, 4), (5, 5), # '&' '|' '~'
    (7, 7), (7, 7),         # '<<' '>>'
    (9, 8),                 # '..' (right associative)
    (3, 3), (3, 3), (3, 3), # ==, <, <=
    (3, 3), (3, 3), (3, 3), # ~=, >, >=
    (2, 2), (1, 1)          # and, or
]

UNARY_PRIORITY = 12


# =============================================================================
# lparser.c:872-984 - Expression Parsing
# =============================================================================
def primaryexp(ls: LexState, v: expdesc) -> None:
    """lparser.c:872-891 - Parse primary expression"""
    from .lcode import luaK_dischargevars
    tok = ls.t.token
    if tok == ord('('):
        line = ls.linenumber
        luaX_next(ls)
        expr(ls, v)
        check_match(ls, ord(')'), ord('('), line)
        luaK_dischargevars(ls.fs, v)
    elif tok == TK_NAME:
        singlevar(ls, v)
    else:
        luaX_syntaxerror(ls, "unexpected symbol")


def suffixedexp(ls: LexState, v: expdesc) -> None:
    """lparser.c:894-929 - Parse suffixed expression"""
    from .lcode import luaK_exp2anyregup, luaK_indexed, luaK_self, luaK_exp2nextreg
    fs = ls.fs
    line = ls.linenumber
    primaryexp(ls, v)
    while True:
        tok = ls.t.token
        if tok == ord('.'):
            fieldsel(ls, v)
        elif tok == ord('['):
            key = expdesc()
            luaK_exp2anyregup(fs, v)
            yindex(ls, key)
            luaK_indexed(fs, v, key)
        elif tok == ord(':'):
            key = expdesc()
            luaX_next(ls)
            checkname(ls, key)
            luaK_self(fs, v, key)
            funcargs(ls, v, line)
        elif tok in (ord('('), TK_STRING, ord('{')):
            luaK_exp2nextreg(fs, v)
            funcargs(ls, v, line)
        else:
            return


def simpleexp(ls: LexState, v: expdesc) -> None:
    """lparser.c:932-984 - Parse simple expression"""
    from .lcode import luaK_codeABC, OP_VARARG
    tok = ls.t.token
    if tok == TK_FLT:
        init_exp(v, VKFLT, 0)
        v.nval = ls.t.seminfo.r
    elif tok == TK_INT:
        init_exp(v, VKINT, 0)
        v.ival = ls.t.seminfo.i
    elif tok == TK_STRING:
        codestring(ls, v, ls.t.seminfo.ts)
    elif tok == TK_NIL:
        init_exp(v, VNIL, 0)
    elif tok == TK_TRUE:
        init_exp(v, VTRUE, 0)
    elif tok == TK_FALSE:
        init_exp(v, VFALSE, 0)
    elif tok == TK_DOTS:
        fs = ls.fs
        check_condition(ls, fs.f.is_vararg, "cannot use '...' outside a vararg function")
        init_exp(v, VVARARG, luaK_codeABC(fs, OP_VARARG, 0, 1, 0))
    elif tok == ord('{'):
        constructor(ls, v)
        return
    elif tok == TK_FUNCTION:
        luaX_next(ls)
        body(ls, v, 0, ls.linenumber)
        return
    else:
        suffixedexp(ls, v)
        return
    luaX_next(ls)


def subexpr(ls: LexState, v: expdesc, limit: int) -> BinOpr:
    """lparser.c:1049-1076 - Parse sub-expression with precedence"""
    from .lcode import luaK_prefix, luaK_infix, luaK_posfix
    enterlevel(ls)
    uop = getunopr(ls.t.token)
    if uop != OPR_NOUNOPR:
        line = ls.linenumber
        luaX_next(ls)
        subexpr(ls, v, UNARY_PRIORITY)
        luaK_prefix(ls.fs, uop, v, line)
    else:
        simpleexp(ls, v)
    
    op = getbinopr(ls.t.token)
    while op != OPR_NOBINOPR and priority[op][0] > limit:
        v2 = expdesc()
        line = ls.linenumber
        luaX_next(ls)
        luaK_infix(ls.fs, op, v)
        nextop = subexpr(ls, v2, priority[op][1])
        luaK_posfix(ls.fs, op, v, v2, line)
        op = nextop
    
    leavelevel(ls)
    return op


def expr(ls: LexState, v: expdesc) -> None:
    """lparser.c:1079-1081 - Parse expression"""
    subexpr(ls, v, 0)


# =============================================================================
# lparser.c:1094-1175 - Block and Assignment
# =============================================================================
def block(ls: LexState) -> None:
    """lparser.c:1094-1101 - Parse block"""
    fs = ls.fs
    bl = BlockCnt()
    enterblock(fs, bl, 0)
    statlist(ls)
    leaveblock(fs)


class LHS_assign:
    """lparser.c:1108-1111 - Left-hand side of assignment"""
    def __init__(self):
        self.prev = None
        self.v = expdesc()


def check_conflict(ls: LexState, lh: LHS_assign, v: expdesc) -> None:
    """lparser.c:1120-1145 - Check assignment conflict"""
    from .lcode import luaK_codeABC, luaK_reserveregs, OP_MOVE, OP_GETUPVAL
    fs = ls.fs
    extra = fs.freereg
    conflict = False
    curr = lh
    while curr is not None:
        if curr.v.k == VINDEXED:
            if curr.v.ind.vt == v.k and curr.v.ind.t == v.info:
                conflict = True
                curr.v.ind.vt = VLOCAL
                curr.v.ind.t = extra
            if v.k == VLOCAL and curr.v.ind.idx == v.info:
                conflict = True
                curr.v.ind.idx = extra
        curr = curr.prev
    if conflict:
        op = OP_MOVE if v.k == VLOCAL else OP_GETUPVAL
        luaK_codeABC(fs, op, extra, v.info, 0)
        luaK_reserveregs(fs, 1)


def assignment(ls: LexState, lh: LHS_assign, nvars: int) -> None:
    """lparser.c:1148-1175 - Parse assignment"""
    from .lcode import luaK_setoneret, luaK_storevar
    e = expdesc()
    check_condition(ls, vkisvar(lh.v.k), "syntax error")
    if testnext(ls, ord(',')):
        nv = LHS_assign()
        nv.prev = lh
        suffixedexp(ls, nv.v)
        if nv.v.k != VINDEXED:
            check_conflict(ls, lh, nv.v)
        checklimit(ls.fs, nvars + ls.L.nCcalls, LUAI_MAXCCALLS, "C levels")
        assignment(ls, nv, nvars + 1)
    else:
        checknext(ls, ord('='))
        nexps = explist(ls, e)
        if nexps != nvars:
            adjust_assign(ls, nvars, nexps, e)
        else:
            luaK_setoneret(ls.fs, e)
            luaK_storevar(ls.fs, lh.v, e)
            return
    init_exp(e, VNONRELOC, ls.fs.freereg - 1)
    luaK_storevar(ls.fs, lh.v, e)


def explist(ls: LexState, v: expdesc) -> int:
    """lparser.c:805-815 - Parse expression list"""
    from .lcode import luaK_exp2nextreg
    n = 1
    expr(ls, v)
    while testnext(ls, ord(',')):
        luaK_exp2nextreg(ls.fs, v)
        expr(ls, v)
        n += 1
    return n


# =============================================================================
# lparser.c:1178-1239 - Control Statements
# =============================================================================
def cond(ls: LexState) -> int:
    """lparser.c:1178-1185 - Parse condition"""
    from .lcode import luaK_goiftrue
    v = expdesc()
    expr(ls, v)
    if v.k == VNIL:
        v.k = VFALSE
    luaK_goiftrue(ls.fs, v)
    return v.f


def gotostat(ls: LexState, pc: int) -> None:
    """lparser.c:1188-1200 - Parse goto/break statement"""
    line = ls.linenumber
    if testnext(ls, TK_GOTO):
        label = str_checkname(ls)
    else:
        luaX_next(ls)  # skip break
        label = luaX_newstring(ls, b"break")
    g = newlabelentry(ls, ls.dyd.gt, label, line, pc)
    findlabel(ls, g)


def whilestat(ls: LexState, line: int) -> None:
    """lparser.c:1242-1258 - Parse while statement"""
    from .lcode import luaK_getlabel, luaK_jumpto, luaK_patchtohere
    fs = ls.fs
    bl = BlockCnt()
    luaX_next(ls)  # skip WHILE
    whileinit = luaK_getlabel(fs)
    condexit = cond(ls)
    enterblock(fs, bl, 1)
    checknext(ls, TK_DO)
    block(ls)
    luaK_jumpto(fs, whileinit)
    check_match(ls, TK_END, TK_WHILE, line)
    leaveblock(fs)
    luaK_patchtohere(fs, condexit)


def repeatstat(ls: LexState, line: int) -> None:
    """lparser.c:1261-1278 - Parse repeat statement"""
    from .lcode import luaK_getlabel, luaK_patchclose, luaK_patchlist
    fs = ls.fs
    repeat_init = luaK_getlabel(fs)
    bl1 = BlockCnt()
    bl2 = BlockCnt()
    enterblock(fs, bl1, 1)
    enterblock(fs, bl2, 0)
    luaX_next(ls)  # skip REPEAT
    statlist(ls)
    check_match(ls, TK_UNTIL, TK_REPEAT, line)
    condexit = cond(ls)
    if bl2.upval:
        luaK_patchclose(fs, condexit, bl2.nactvar)
    leaveblock(fs)
    luaK_patchlist(fs, condexit, repeat_init)
    leaveblock(fs)


def ifstat(ls: LexState, line: int) -> None:
    """lparser.c:1418-1429 - Parse if statement"""
    from .lcode import luaK_patchtohere
    fs = ls.fs
    escapelist = [NO_JUMP]
    test_then_block(ls, escapelist)
    while ls.t.token == TK_ELSEIF:
        test_then_block(ls, escapelist)
    if testnext(ls, TK_ELSE):
        block(ls)
    check_match(ls, TK_END, TK_IF, line)
    luaK_patchtohere(fs, escapelist[0])


def test_then_block(ls: LexState, escapelist: list) -> None:
    """lparser.c:1383-1415 - Parse test then block"""
    from .lcode import luaK_goiffalse, luaK_goiftrue, luaK_jump, luaK_concat, luaK_patchtohere
    bl = BlockCnt()
    fs = ls.fs
    v = expdesc()
    luaX_next(ls)  # skip IF or ELSEIF
    expr(ls, v)
    checknext(ls, TK_THEN)
    if ls.t.token == TK_GOTO or ls.t.token == TK_BREAK:
        luaK_goiffalse(ls.fs, v)
        enterblock(fs, bl, 0)
        gotostat(ls, v.t)
        while testnext(ls, ord(';')):
            pass
        if block_follow(ls, 0):
            leaveblock(fs)
            return
        else:
            jf = luaK_jump(fs)
    else:
        luaK_goiftrue(ls.fs, v)
        enterblock(fs, bl, 0)
        jf = v.f
    statlist(ls)
    leaveblock(fs)
    if ls.t.token == TK_ELSE or ls.t.token == TK_ELSEIF:
        luaK_concat(fs, escapelist, luaK_jump(fs))
    luaK_patchtohere(fs, jf)


# =============================================================================
# lparser.c:1281-1380 - For Statements
# =============================================================================
def exp1(ls: LexState) -> int:
    """lparser.c:1281-1289 - Parse single expression"""
    from .lcode import luaK_exp2nextreg
    e = expdesc()
    expr(ls, e)
    luaK_exp2nextreg(ls.fs, e)
    # lua_assert(e.k == VNONRELOC)
    return e.info


def forbody(ls: LexState, base: int, line: int, nvars: int, isnum: int) -> None:
    """lparser.c:1292-1315 - Parse for body"""
    from .lcode import (luaK_codeAsBx, luaK_jump, luaK_patchtohere,
                        luaK_codeABC, luaK_fixline, luaK_patchlist,
                        luaK_reserveregs, OP_FORPREP, OP_FORLOOP,
                        OP_TFORCALL, OP_TFORLOOP)
    bl = BlockCnt()
    fs = ls.fs
    adjustlocalvars(ls, 3)
    checknext(ls, TK_DO)
    if isnum:
        prep = luaK_codeAsBx(fs, OP_FORPREP, base, NO_JUMP)
    else:
        prep = luaK_jump(fs)
    enterblock(fs, bl, 0)
    adjustlocalvars(ls, nvars)
    luaK_reserveregs(fs, nvars)
    block(ls)
    leaveblock(fs)
    luaK_patchtohere(fs, prep)
    if isnum:
        endfor = luaK_codeAsBx(fs, OP_FORLOOP, base, NO_JUMP)
    else:
        luaK_codeABC(fs, OP_TFORCALL, base, 0, nvars)
        luaK_fixline(fs, line)
        endfor = luaK_codeAsBx(fs, OP_TFORLOOP, base + 2, NO_JUMP)
    luaK_patchlist(fs, endfor, prep + 1)
    luaK_fixline(fs, line)


def fornum(ls: LexState, varname: TString, line: int) -> None:
    """lparser.c:1318-1337 - Parse numeric for"""
    from .lcode import luaK_codek, luaK_intK, luaK_reserveregs
    fs = ls.fs
    base = fs.freereg
    new_localvarliteral(ls, "(for index)")
    new_localvarliteral(ls, "(for limit)")
    new_localvarliteral(ls, "(for step)")
    new_localvar(ls, varname)
    checknext(ls, ord('='))
    exp1(ls)
    checknext(ls, ord(','))
    exp1(ls)
    if testnext(ls, ord(',')):
        exp1(ls)
    else:
        luaK_codek(fs, fs.freereg, luaK_intK(fs, 1))
        luaK_reserveregs(fs, 1)
    forbody(ls, base, line, 1, 1)


def forlist(ls: LexState, indexname: TString) -> None:
    """lparser.c:1340-1362 - Parse generic for"""
    from .lcode import luaK_checkstack
    fs = ls.fs
    e = expdesc()
    nvars = 4
    base = fs.freereg
    new_localvarliteral(ls, "(for generator)")
    new_localvarliteral(ls, "(for state)")
    new_localvarliteral(ls, "(for control)")
    new_localvar(ls, indexname)
    while testnext(ls, ord(',')):
        new_localvar(ls, str_checkname(ls))
        nvars += 1
    checknext(ls, TK_IN)
    line = ls.linenumber
    adjust_assign(ls, 3, explist(ls, e), e)
    luaK_checkstack(fs, 3)
    forbody(ls, base, line, nvars - 3, 0)


def forstat(ls: LexState, line: int) -> None:
    """lparser.c:1365-1380 - Parse for statement"""
    fs = ls.fs
    bl = BlockCnt()
    enterblock(fs, bl, 1)
    luaX_next(ls)  # skip 'for'
    varname = str_checkname(ls)
    tok = ls.t.token
    if tok == ord('='):
        fornum(ls, varname, line)
    elif tok == ord(',') or tok == TK_IN:
        forlist(ls, varname)
    else:
        luaX_syntaxerror(ls, "'=' or 'in' expected")
    check_match(ls, TK_END, TK_FOR, line)
    leaveblock(fs)


# =============================================================================
# lparser.c:1432-1502 - Function and Local Statements
# =============================================================================
def localfunc(ls: LexState) -> None:
    """lparser.c:1432-1440 - Parse local function"""
    b = expdesc()
    fs = ls.fs
    new_localvar(ls, str_checkname(ls))
    adjustlocalvars(ls, 1)
    body(ls, b, 0, ls.linenumber)
    getlocvar(fs, b.info).startpc = fs.pc


def localstat(ls: LexState) -> None:
    """lparser.c:1443-1460 - Parse local statement"""
    nvars = 0
    e = expdesc()
    while True:
        new_localvar(ls, str_checkname(ls))
        nvars += 1
        if not testnext(ls, ord(',')):
            break
    if testnext(ls, ord('=')):
        nexps = explist(ls, e)
    else:
        e.k = VVOID
        nexps = 0
    adjust_assign(ls, nvars, nexps, e)
    adjustlocalvars(ls, nvars)


def funcname(ls: LexState, v: expdesc) -> int:
    """lparser.c:1463-1474 - Parse function name"""
    ismethod = 0
    singlevar(ls, v)
    while ls.t.token == ord('.'):
        fieldsel(ls, v)
    if ls.t.token == ord(':'):
        ismethod = 1
        fieldsel(ls, v)
    return ismethod


def funcstat(ls: LexState, line: int) -> None:
    """lparser.c:1477-1486 - Parse function statement"""
    from .lcode import luaK_storevar, luaK_fixline
    v = expdesc()
    b = expdesc()
    luaX_next(ls)  # skip FUNCTION
    ismethod = funcname(ls, v)
    body(ls, b, ismethod, line)
    luaK_storevar(ls.fs, v, b)
    luaK_fixline(ls.fs, line)


def exprstat(ls: LexState) -> None:
    """lparser.c:1489-1502 - Parse expression statement"""
    from .lcode import getinstruction, SETARG_C
    fs = ls.fs
    v = LHS_assign()
    suffixedexp(ls, v.v)
    if ls.t.token == ord('=') or ls.t.token == ord(','):
        v.prev = None
        assignment(ls, v, 1)
    else:
        check_condition(ls, v.v.k == VCALL, "syntax error")
        # Set instruction's C argument to 1
        inst = getinstruction(fs, v.v)
        fs.f.code[v.v.info] = (inst & ~(0xFF << 14)) | (1 << 14)


def retstat(ls: LexState) -> None:
    """lparser.c:1505-1535 - Parse return statement"""
    from .lcode import (luaK_setmultret, luaK_exp2anyreg, luaK_exp2nextreg,
                        luaK_ret, getinstruction, SET_OPCODE, OP_TAILCALL)
    from .lua import LUA_MULTRET
    fs = ls.fs
    e = expdesc()
    if block_follow(ls, 1) or ls.t.token == ord(';'):
        first = 0
        nret = 0
    else:
        nret = explist(ls, e)
        if hasmultret(e.k):
            luaK_setmultret(fs, e)
            if e.k == VCALL and nret == 1:
                inst = getinstruction(fs, e)
                fs.f.code[e.info] = SET_OPCODE(inst, OP_TAILCALL)
            first = fs.nactvar
            nret = LUA_MULTRET
        else:
            if nret == 1:
                first = luaK_exp2anyreg(fs, e)
            else:
                luaK_exp2nextreg(fs, e)
                first = fs.nactvar
                # lua_assert(nret == fs.freereg - first)
    luaK_ret(fs, first, nret)
    testnext(ls, ord(';'))


# =============================================================================
# lparser.c:1538-1604 - statement
# =============================================================================
def statement(ls: LexState) -> None:
    """lparser.c:1538-1604 - Parse statement"""
    from .lcode import luaK_jump
    line = ls.linenumber
    enterlevel(ls)
    tok = ls.t.token
    
    if tok == ord(';'):
        luaX_next(ls)
    elif tok == TK_IF:
        ifstat(ls, line)
    elif tok == TK_WHILE:
        whilestat(ls, line)
    elif tok == TK_DO:
        luaX_next(ls)
        block(ls)
        check_match(ls, TK_END, TK_DO, line)
    elif tok == TK_FOR:
        forstat(ls, line)
    elif tok == TK_REPEAT:
        repeatstat(ls, line)
    elif tok == TK_FUNCTION:
        funcstat(ls, line)
    elif tok == TK_LOCAL:
        luaX_next(ls)
        if testnext(ls, TK_FUNCTION):
            localfunc(ls)
        else:
            localstat(ls)
    elif tok == TK_DBCOLON:
        luaX_next(ls)
        labelstat(ls, str_checkname(ls), line)
    elif tok == TK_RETURN:
        luaX_next(ls)
        retstat(ls)
    elif tok == TK_BREAK or tok == TK_GOTO:
        gotostat(ls, luaK_jump(ls.fs))
    else:
        exprstat(ls)
    
    # Ensure stack state consistency
    if ls.fs.freereg < ls.fs.nactvar:
        ls.fs.freereg = ls.fs.nactvar
    if ls.fs.f.maxstacksize < ls.fs.freereg:
        ls.fs.f.maxstacksize = ls.fs.freereg
    ls.fs.freereg = ls.fs.nactvar
    leavelevel(ls)


def labelstat(ls: LexState, label: TString, line: int) -> None:
    """lparser.c:1224-1239 - Parse label statement"""
    from .lcode import luaK_getlabel
    fs = ls.fs
    ll = ls.dyd.label
    checkrepeated(fs, ll, label)
    checknext(ls, TK_DBCOLON)
    l = newlabelentry(ls, ll, label, line, luaK_getlabel(fs))
    skipnoopstat(ls)
    if block_follow(ls, 0):
        ll.arr[l].nactvar = fs.bl.nactvar
    findgotos(ls, ll.arr[l])


def checkrepeated(fs: FuncState, ll: Labellist, label: TString) -> None:
    """lparser.c:1204-1214 - Check for repeated labels"""
    for i in range(fs.bl.firstlabel, ll.n):
        if eqstr(label, ll.arr[i].name):
            name = label.data.decode() if label.data else "?"
            msg = f"label '{name}' already defined on line {ll.arr[i].line}"
            semerror(fs.ls, msg)


def skipnoopstat(ls: LexState) -> None:
    """lparser.c:1218-1221 - Skip no-op statements"""
    while ls.t.token == ord(';') or ls.t.token == TK_DBCOLON:
        statement(ls)


# =============================================================================
# lparser.c:638-860 - Constructor and Function Body
# =============================================================================
class ConsControl:
    """lparser.c:638-644 - Constructor control"""
    def __init__(self):
        self.v = expdesc()
        self.t = None
        self.nh = 0
        self.na = 0
        self.tostore = 0


def constructor(ls: LexState, t: expdesc) -> None:
    """lparser.c:725-748 - Parse table constructor"""
    from .lcode import luaK_codeABC, luaK_exp2nextreg, OP_NEWTABLE
    from .lobject import luaO_int2fb
    fs = ls.fs
    line = ls.linenumber
    pc = luaK_codeABC(fs, OP_NEWTABLE, 0, 0, 0)
    cc = ConsControl()
    cc.t = t
    init_exp(t, VRELOCABLE, pc)
    init_exp(cc.v, VVOID, 0)
    luaK_exp2nextreg(ls.fs, t)
    checknext(ls, ord('{'))
    while True:
        # lua_assert(cc.v.k == VVOID or cc.tostore > 0)
        if ls.t.token == ord('}'):
            break
        closelistfield(fs, cc)
        field(ls, cc)
        if not (testnext(ls, ord(',')) or testnext(ls, ord(';'))):
            break
    check_match(ls, ord('}'), ord('{'), line)
    lastlistfield(fs, cc)
    # Set initial table size
    inst = fs.f.code[pc]
    fs.f.code[pc] = (inst & ~(0xFF << 23)) | (luaO_int2fb(cc.na) << 23)
    fs.f.code[pc] = (fs.f.code[pc] & ~(0xFF << 14)) | (luaO_int2fb(cc.nh) << 14)


def closelistfield(fs: FuncState, cc: ConsControl) -> None:
    """lparser.c:667-675 - Close list field"""
    from .lcode import luaK_exp2nextreg, luaK_setlist
    if cc.v.k == VVOID:
        return
    luaK_exp2nextreg(fs, cc.v)
    cc.v.k = VVOID
    if cc.tostore == 50:  # LFIELDS_PER_FLUSH
        luaK_setlist(fs, cc.t.info, cc.na, cc.tostore)
        cc.tostore = 0


def lastlistfield(fs: FuncState, cc: ConsControl) -> None:
    """lparser.c:678-688 - Last list field"""
    from .lcode import luaK_setmultret, luaK_setlist, luaK_exp2nextreg
    from .lua import LUA_MULTRET
    if cc.tostore == 0:
        return
    if hasmultret(cc.v.k):
        luaK_setmultret(fs, cc.v)
        luaK_setlist(fs, cc.t.info, cc.na, LUA_MULTRET)
        cc.na -= 1
    else:
        if cc.v.k != VVOID:
            luaK_exp2nextreg(fs, cc.v)
        luaK_setlist(fs, cc.t.info, cc.na, cc.tostore)


def recfield(ls: LexState, cc: ConsControl) -> None:
    """lparser.c:647-665 - Parse record field"""
    from .lcode import luaK_exp2RK, luaK_codeABC, luaK_exp2val, OP_SETTABLE
    fs = ls.fs
    key = expdesc()
    val = expdesc()
    if ls.t.token == TK_NAME:
        checklimit(fs, cc.nh, MAX_INT, "items in a constructor")
        checkname(ls, key)
    else:
        yindex(ls, key)
    cc.nh += 1
    checknext(ls, ord('='))
    rkkey = luaK_exp2RK(fs, key)
    expr(ls, val)
    luaK_codeABC(fs, OP_SETTABLE, cc.t.info, rkkey, luaK_exp2RK(fs, val))
    fs.freereg = cc.t.info + 1


def listfield(ls: LexState, cc: ConsControl) -> None:
    """lparser.c:691-697 - Parse list field"""
    expr(ls, cc.v)
    checklimit(ls.fs, cc.na, MAX_INT, "items in a constructor")
    cc.na += 1
    cc.tostore += 1


def field(ls: LexState, cc: ConsControl) -> None:
    """lparser.c:703-722 - Parse constructor field"""
    tok = ls.t.token
    if tok == TK_NAME:
        if luaX_lookahead(ls) != ord('='):
            listfield(ls, cc)
        else:
            recfield(ls, cc)
    elif tok == ord('['):
        recfield(ls, cc)
    else:
        listfield(ls, cc)


def parlist(ls: LexState) -> None:
    """lparser.c:754-780 - Parse parameter list"""
    from .lcode import luaK_reserveregs
    fs = ls.fs
    f = fs.f
    nparams = 0
    f.is_vararg = 0
    if ls.t.token != ord(')'):
        while True:
            if ls.t.token == TK_NAME:
                new_localvar(ls, str_checkname(ls))
                nparams += 1
            elif ls.t.token == TK_DOTS:
                luaX_next(ls)
                f.is_vararg = 1
            else:
                luaX_syntaxerror(ls, "<name> or '...' expected")
            if f.is_vararg or not testnext(ls, ord(',')):
                break
    adjustlocalvars(ls, nparams)
    f.numparams = fs.nactvar
    luaK_reserveregs(fs, fs.nactvar)


def body(ls: LexState, e: expdesc, ismethod: int, line: int) -> None:
    """lparser.c:783-802 - Parse function body"""
    new_fs = FuncState()
    bl = BlockCnt()
    new_fs.f = addprototype(ls)
    new_fs.f.linedefined = line
    open_func(ls, new_fs, bl)
    checknext(ls, ord('('))
    if ismethod:
        new_localvarliteral(ls, "self")
        adjustlocalvars(ls, 1)
    parlist(ls)
    checknext(ls, ord(')'))
    statlist(ls)
    new_fs.f.lastlinedefined = ls.linenumber
    check_match(ls, TK_END, TK_FUNCTION, line)
    codeclosure(ls, e)
    close_func(ls)


def funcargs(ls: LexState, f: expdesc, line: int) -> None:
    """lparser.c:818-860 - Parse function arguments"""
    from .lcode import (luaK_exp2nextreg, luaK_setmultret, luaK_codeABC,
                        luaK_fixline, OP_CALL)
    from .lua import LUA_MULTRET
    fs = ls.fs
    args = expdesc()
    tok = ls.t.token
    if tok == ord('('):
        luaX_next(ls)
        if ls.t.token == ord(')'):
            args.k = VVOID
        else:
            explist(ls, args)
            luaK_setmultret(fs, args)
        check_match(ls, ord(')'), ord('('), line)
    elif tok == ord('{'):
        constructor(ls, args)
    elif tok == TK_STRING:
        codestring(ls, args, ls.t.seminfo.ts)
        luaX_next(ls)
    else:
        luaX_syntaxerror(ls, "function arguments expected")
    
    # lua_assert(f.k == VNONRELOC)
    base = f.info
    if hasmultret(args.k):
        nparams = LUA_MULTRET
    else:
        if args.k != VVOID:
            luaK_exp2nextreg(fs, args)
        nparams = fs.freereg - (base + 1)
    init_exp(f, VCALL, luaK_codeABC(fs, OP_CALL, base, nparams + 1, 2))
    luaK_fixline(fs, line)
    fs.freereg = base + 1
