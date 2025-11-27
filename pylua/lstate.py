# -*- coding: utf-8 -*-
"""
lstate.py - Global State
========================
Source: lstate.h/lstate.c (lua-5.3.6/src/lstate.h, lstate.c)

Global State
See Copyright Notice in lua.h
"""

from typing import Optional, List, Any, TYPE_CHECKING, Callable
from dataclasses import dataclass, field

from .lua import (
    LUA_NUMTAGS, LUA_MINSTACK, LUA_TTHREAD,
    lua_Number, lua_CFunction, lua_Hook,
)
from .llimits import (
    lu_byte, lu_mem, l_mem, Instruction,
    LUAI_MAXCCALLS, STRCACHE_N, STRCACHE_M,
)
from .lobject import (
    GCObject, TValue, Value, TString, Table,
    LUA_TLCL, ctb,
)
from .ltm import TMS

if TYPE_CHECKING:
    from .lzio import ZIO

# =============================================================================
# lstate.h:64-68 - Stack Constants
# =============================================================================
EXTRA_STACK: int = 5  # lstate.h:65 - extra stack space for TM calls
BASIC_STACK_SIZE: int = 2 * LUA_MINSTACK  # lstate.h:68 = 40

# =============================================================================
# lstate.h:71-73 - GC Kinds
# =============================================================================
KGC_NORMAL: int = 0     # lstate.h:72 - normal GC
KGC_EMERGENCY: int = 1  # lstate.h:73 - gc forced by allocation failure

# =============================================================================
# lstate.h:76-80 - String Table
# =============================================================================
@dataclass
class StringTable:
    """
    lstate.h:76-80 - String hash table
    
    typedef struct stringtable {
        TString **hash;
        int nuse;  /* number of elements */
        int size;
    } stringtable;
    
    Source: lstate.h:76-80
    """
    hash: List[Optional[TString]] = field(default_factory=list)  # lstate.h:77
    nuse: int = 0   # lstate.h:78 - number of elements
    size: int = 0   # lstate.h:79 - table size

# =============================================================================
# lstate.h:83-110 - CallInfo Structure
# =============================================================================
@dataclass
class CallInfo:
    """
    lstate.h:92-110 - Information about a call
    
    typedef struct CallInfo {
        StkId func;  /* function index in the stack */
        StkId top;   /* top for this function */
        struct CallInfo *previous, *next;  /* dynamic call link */
        union {
            struct {  /* only for Lua functions */
                StkId base;  /* base for this function */
                const Instruction *savedpc;
            } l;
            struct {  /* only for C functions */
                lua_KFunction k;  /* continuation in case of yields */
                ptrdiff_t old_errfunc;
                lua_KContext ctx;  /* context info. in case of yields */
            } c;
        } u;
        ptrdiff_t extra;
        short nresults;  /* expected number of results from this function */
        unsigned short callstatus;
    } CallInfo;
    
    Source: lstate.h:92-110
    """
    func: int = 0    # lstate.h:93 - function index in stack (StkId)
    top: int = 0     # lstate.h:94 - top for this function (StkId)
    previous: Optional['CallInfo'] = None  # lstate.h:95
    next: Optional['CallInfo'] = None      # lstate.h:95
    # Union u.l (Lua functions):
    base: int = 0              # lstate.h:98 - base for this function (StkId)
    savedpc: int = 0           # lstate.h:99 - saved PC (index into code)
    # Union u.c (C functions):
    k: Optional[Callable] = None  # lstate.h:102 - continuation function
    old_errfunc: int = 0          # lstate.h:103
    ctx: int = 0                  # lstate.h:104 - context for continuation
    # Common fields:
    extra: int = 0          # lstate.h:107
    nresults: int = 0       # lstate.h:108 - expected number of results
    callstatus: int = 0     # lstate.h:109 - call status bits

# =============================================================================
# lstate.h:113-131 - CallInfo Status Bits
# =============================================================================
CIST_OAH: int = 1 << 0       # lstate.h:116 - original value of 'allowhook'
CIST_LUA: int = 1 << 1       # lstate.h:117 - call is running a Lua function
CIST_HOOKED: int = 1 << 2    # lstate.h:118 - call is running a debug hook
CIST_FRESH: int = 1 << 3     # lstate.h:119-120 - fresh invocation of luaV_execute
CIST_YPCALL: int = 1 << 4    # lstate.h:121 - yieldable protected call
CIST_TAIL: int = 1 << 5      # lstate.h:122 - call was tail called
CIST_HOOKYIELD: int = 1 << 6 # lstate.h:123 - last hook called yielded
CIST_LEQ: int = 1 << 7       # lstate.h:124 - using __lt for __le
CIST_FIN: int = 1 << 8       # lstate.h:125 - call is running a finalizer

def isLua(ci: CallInfo) -> bool:
    """
    lstate.h:127 - #define isLua(ci) ((ci)->callstatus & CIST_LUA)
    """
    return bool(ci.callstatus & CIST_LUA)

def setoah(st: int, v: int) -> int:
    """
    lstate.h:130 - #define setoah(st,v) ((st) = ((st) & ~CIST_OAH) | (v))
    assume that CIST_OAH has offset 0 and that 'v' is strictly 0/1
    """
    return (st & ~CIST_OAH) | v

def getoah(st: int) -> int:
    """
    lstate.h:131 - #define getoah(st) ((st) & CIST_OAH)
    """
    return st & CIST_OAH

# =============================================================================
# lstate.h:134-172 - Global State
# =============================================================================
@dataclass
class GlobalState:
    """
    lstate.h:137-172 - 'global state', shared by all threads
    
    typedef struct global_State {
        lua_Alloc frealloc;
        void *ud;
        l_mem totalbytes;
        l_mem GCdebt;
        lu_mem GCmemtrav;
        lu_mem GCestimate;
        stringtable strt;
        TValue l_registry;
        unsigned int seed;
        lu_byte currentwhite;
        lu_byte gcstate;
        lu_byte gckind;
        lu_byte gcrunning;
        GCObject *allgc;
        GCObject **sweepgc;
        GCObject *finobj;
        GCObject *gray;
        GCObject *grayagain;
        GCObject *weak;
        GCObject *ephemeron;
        GCObject *allweak;
        GCObject *tobefnz;
        GCObject *fixedgc;
        struct lua_State *twups;
        unsigned int gcfinnum;
        int gcpause;
        int gcstepmul;
        lua_CFunction panic;
        struct lua_State *mainthread;
        const lua_Number *version;
        TString *memerrmsg;
        TString *tmname[TM_N];
        struct Table *mt[LUA_NUMTAGS];
        TString *strcache[STRCACHE_N][STRCACHE_M];
    } global_State;
    
    Source: lstate.h:137-172
    """
    frealloc: Optional[Callable] = None  # lstate.h:138 - allocator function
    ud: Any = None                       # lstate.h:139 - allocator userdata
    totalbytes: int = 0      # lstate.h:140 - bytes allocated - GCdebt
    GCdebt: int = 0          # lstate.h:141 - bytes not yet compensated
    GCmemtrav: int = 0       # lstate.h:142 - memory traversed by GC
    GCestimate: int = 0      # lstate.h:143 - estimate of non-garbage memory
    strt: StringTable = field(default_factory=StringTable)  # lstate.h:144
    l_registry: TValue = field(default_factory=TValue)  # lstate.h:145
    seed: int = 0            # lstate.h:146 - randomized seed for hashes
    currentwhite: int = 0    # lstate.h:147
    gcstate: int = 0         # lstate.h:148 - state of garbage collector
    gckind: int = 0          # lstate.h:149 - kind of GC running
    gcrunning: int = 0       # lstate.h:150 - true if GC is running
    allgc: Optional[GCObject] = None   # lstate.h:151 - all collectable objects
    sweepgc: Optional[GCObject] = None # lstate.h:152 - current sweep position
    finobj: Optional[GCObject] = None  # lstate.h:153 - objects with finalizers
    gray: Optional[GCObject] = None    # lstate.h:154 - gray objects
    grayagain: Optional[GCObject] = None  # lstate.h:155
    weak: Optional[GCObject] = None    # lstate.h:156 - weak tables
    ephemeron: Optional[GCObject] = None  # lstate.h:157
    allweak: Optional[GCObject] = None # lstate.h:158
    tobefnz: Optional[GCObject] = None # lstate.h:159 - userdata to be GC'd
    fixedgc: Optional[GCObject] = None # lstate.h:160 - non-collectable objects
    twups: Optional['LuaState'] = None # lstate.h:161 - threads with open upvalues
    gcfinnum: int = 0        # lstate.h:162 - finalizers to call per GC step
    gcpause: int = 200       # lstate.h:163 - pause between GCs (default 200%)
    gcstepmul: int = 200     # lstate.h:164 - GC granularity (default 200%)
    panic: Optional[lua_CFunction] = None  # lstate.h:165 - panic function
    mainthread: Optional['LuaState'] = None  # lstate.h:166
    version: Optional[float] = None  # lstate.h:167 - version number pointer
    memerrmsg: Optional[TString] = None  # lstate.h:168 - OOM error message
    tmname: List[Optional[TString]] = field(
        default_factory=lambda: [None] * TMS.TM_N)  # lstate.h:169
    mt: List[Optional[Table]] = field(
        default_factory=lambda: [None] * LUA_NUMTAGS)  # lstate.h:170
    strcache: List[List[Optional[TString]]] = field(
        default_factory=lambda: [[None] * STRCACHE_M for _ in range(STRCACHE_N)])  # lstate.h:171

# =============================================================================
# lstate.h:175-202 - lua_State ('per thread' state)
# =============================================================================
@dataclass
class LuaState(GCObject):
    """
    lstate.h:178-202 - 'per thread' state
    
    struct lua_State {
        CommonHeader;
        unsigned short nci;  /* number of items in 'ci' list */
        lu_byte status;
        StkId top;  /* first free slot in the stack */
        global_State *l_G;
        CallInfo *ci;  /* call info for current function */
        const Instruction *oldpc;  /* last pc traced */
        StkId stack_last;  /* last free slot in the stack */
        StkId stack;  /* stack base */
        UpVal *openupval;  /* list of open upvalues in this stack */
        GCObject *gclist;
        struct lua_State *twups;  /* list of threads with open upvalues */
        struct lua_longjmp *errorJmp;  /* current error recover point */
        CallInfo base_ci;  /* CallInfo for first level (C calling Lua) */
        volatile lua_Hook hook;
        ptrdiff_t errfunc;  /* current error handling function (stack index) */
        int stacksize;
        int basehookcount;
        int hookcount;
        unsigned short nny;  /* number of non-yieldable calls in stack */
        unsigned short nCcalls;  /* number of nested C calls */
        l_signalT hookmask;
        lu_byte allowhook;
    };
    
    Source: lstate.h:178-202
    """
    nci: int = 0             # lstate.h:180 - number of items in 'ci' list
    status: int = 0          # lstate.h:181 - thread status
    top: int = 0             # lstate.h:182 - first free slot in stack (StkId)
    l_G: Optional[GlobalState] = None  # lstate.h:183 - global state
    ci: Optional[CallInfo] = None      # lstate.h:184 - current call info
    oldpc: int = 0           # lstate.h:185 - last pc traced
    stack_last: int = 0      # lstate.h:186 - last free slot (StkId)
    stack: List[TValue] = field(default_factory=list)  # lstate.h:187
    openupval: Optional[Any] = None  # lstate.h:188 - open upvalues (UpVal)
    gclist: Optional[GCObject] = None  # lstate.h:189
    twups: Optional['LuaState'] = None # lstate.h:190
    errorJmp: Any = None     # lstate.h:191 - error recovery point
    base_ci: CallInfo = field(default_factory=CallInfo)  # lstate.h:192
    hook: Optional[lua_Hook] = None  # lstate.h:193
    errfunc: int = 0         # lstate.h:194 - error handler stack index
    stacksize: int = 0       # lstate.h:195
    basehookcount: int = 0   # lstate.h:196
    hookcount: int = 0       # lstate.h:197
    nny: int = 0             # lstate.h:198 - non-yieldable calls
    nCcalls: int = 0         # lstate.h:199 - nested C calls
    hookmask: int = 0        # lstate.h:200
    allowhook: int = 1       # lstate.h:201

# =============================================================================
# lstate.h:205 - G(L) Macro
# =============================================================================
def G(L: LuaState) -> GlobalState:
    """
    lstate.h:205 - #define G(L) (L->l_G)
    Get global state from lua_State
    """
    return L.l_G

# =============================================================================
# lstate.h:208-239 - GCUnion (for conversions)
# =============================================================================
# Note: GCUnion and conversion macros are defined in lobject.py

# =============================================================================
# lstate.h:243 - Get Total Bytes Allocated
# =============================================================================
def gettotalbytes(g: GlobalState) -> int:
    """
    lstate.h:243 - #define gettotalbytes(g) cast(lu_mem, (g)->totalbytes + (g)->GCdebt)
    actual number of total bytes allocated
    """
    return g.totalbytes + g.GCdebt

# =============================================================================
# lstate.c Functions (Stubs - to be implemented)
# =============================================================================
def luaE_setdebt(g: GlobalState, debt: int) -> None:
    """
    lstate.h:245 / lstate.c - Set GC debt
    LUAI_FUNC void luaE_setdebt (global_State *g, l_mem debt);
    """
    g.totalbytes -= debt - g.GCdebt
    g.GCdebt = debt

def luaE_freethread(L: LuaState, L1: LuaState) -> None:
    """
    lstate.h:246 / lstate.c - Free a thread
    LUAI_FUNC void luaE_freethread (lua_State *L, lua_State *L1);
    """
    # TODO: Implement thread cleanup
    pass

def luaE_extendCI(L: LuaState) -> CallInfo:
    """
    lstate.h:247 / lstate.c:49-62 - Extend CallInfo list
    LUAI_FUNC CallInfo *luaE_extendCI (lua_State *L);
    
    Source: lstate.c:49-62
    """
    ci = CallInfo()
    if L.ci is not None:
        L.ci.next = ci
        ci.previous = L.ci
    L.nci += 1
    return ci

def luaE_freeCI(L: LuaState) -> None:
    """
    lstate.h:248 / lstate.c:64-73 - Free unused CallInfo list
    LUAI_FUNC void luaE_freeCI (lua_State *L);
    
    Source: lstate.c:64-73
    """
    ci = L.ci
    if ci is not None:
        next_ci = ci.next
        ci.next = None
        while next_ci is not None:
            free_ci = next_ci
            next_ci = next_ci.next
            L.nci -= 1

def luaE_shrinkCI(L: LuaState) -> None:
    """
    lstate.h:249 / lstate.c:75-88 - Shrink CallInfo list
    LUAI_FUNC void luaE_shrinkCI (lua_State *L);
    
    Source: lstate.c:75-88
    """
    # Free extra CallInfo structures
    luaE_freeCI(L)

# =============================================================================
# State Creation/Initialization (from lstate.c)
# =============================================================================
def stack_init(L1: LuaState, L: LuaState) -> None:
    """
    lstate.c:91-109 - Initialize stack
    static void stack_init (lua_State *L1, lua_State *L)
    
    Source: lstate.c:91-109
    """
    from .lobject import setnilvalue
    
    # Initialize stack with BASIC_STACK_SIZE
    L1.stacksize = BASIC_STACK_SIZE
    L1.stack = [TValue() for _ in range(BASIC_STACK_SIZE + EXTRA_STACK)]
    L1.top = 0  # lstate.c:96 - L1->top = L1->stack
    L1.stack_last = BASIC_STACK_SIZE - EXTRA_STACK  # lstate.c:97
    
    # Initialize base CallInfo
    ci = L1.base_ci
    ci.next = None
    ci.previous = None
    ci.callstatus = 0
    ci.func = L1.top  # lstate.c:101
    
    # Push nil for function slot
    setnilvalue(L1.stack[L1.top])
    L1.top += 1
    
    ci.top = L1.top + LUA_MINSTACK  # lstate.c:104
    L1.ci = ci  # lstate.c:105

def f_luaopen(L: LuaState, ud: Any) -> None:
    """
    lstate.c:171-182 - Open Lua state
    static void f_luaopen (lua_State *L, void *ud)
    
    Source: lstate.c:171-182
    """
    g = G(L)
    stack_init(L, L)
    # TODO: Initialize registry table
    # TODO: Initialize string table
    # TODO: Initialize metatables
    # TODO: Initialize tag method names
    g.gcrunning = 1  # Allow GC

def preinit_thread(L: LuaState, g: GlobalState) -> None:
    """
    lstate.c:158-169 - Pre-initialize thread
    static void preinit_thread (lua_State *L, global_State *g)
    
    Source: lstate.c:158-169
    """
    L.l_G = g
    L.stack = []
    L.ci = None
    L.nci = 0
    L.stacksize = 0
    L.twups = L  # thread is not in twups list
    L.errorJmp = None
    L.nCcalls = 0
    L.hook = None
    L.hookmask = 0
    L.basehookcount = 0
    L.allowhook = 1
    L.hookcount = L.basehookcount
    L.openupval = None
    L.nny = 1  # non-yieldable
    L.status = 0
    L.errfunc = 0

def lua_newstate(f: Callable, ud: Any) -> Optional[LuaState]:
    """
    lstate.c:221-262 - Create new Lua state
    LUA_API lua_State *lua_newstate (lua_Alloc f, void *ud)
    
    Source: lstate.c:221-262
    """
    from .lua import LUA_VERSION_NUM
    
    # Create global state
    g = GlobalState()
    g.frealloc = f
    g.ud = ud
    g.currentwhite = 1 << 0  # White0
    g.gcstate = 0  # GCSpause
    g.gckind = KGC_NORMAL
    g.gcrunning = 0  # No GC while building state
    g.gcfinnum = 0
    g.allgc = None
    g.finobj = None
    g.tobefnz = None
    g.fixedgc = None
    g.sweepgc = None
    g.gray = None
    g.grayagain = None
    g.weak = None
    g.ephemeron = None
    g.allweak = None
    g.gcpause = 200  # 200%
    g.gcstepmul = 200  # 200%
    g.version = float(LUA_VERSION_NUM)
    
    # Initialize string table
    g.strt.size = 0
    g.strt.nuse = 0
    g.strt.hash = []
    
    # Create main thread
    L = LuaState()
    L.tt = LUA_TTHREAD
    L.marked = g.currentwhite
    L.next = None
    
    preinit_thread(L, g)
    g.mainthread = L
    g.twups = L  # main thread always in list
    
    # Initialize state
    f_luaopen(L, None)
    
    return L

def lua_close(L: LuaState) -> None:
    """
    lstate.c:296-310 - Close Lua state
    LUA_API void lua_close (lua_State *L)
    
    Source: lstate.c:296-310
    """
    g = G(L)
    L = g.mainthread  # Only close from main thread
    # TODO: Close all upvalues
    # TODO: Run all finalizers
    # TODO: Free all objects
    # TODO: Free global state
