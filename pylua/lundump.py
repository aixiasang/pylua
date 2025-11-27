# -*- coding: utf-8 -*-
"""
lundump.py - Load precompiled Lua chunks
========================================
Source: lundump.h/lundump.c (lua-5.3.6/src/lundump.h, lundump.c)

Load precompiled Lua chunks
See Copyright Notice in lua.h
"""

from typing import Optional, Any, TYPE_CHECKING
from dataclasses import dataclass
import struct

from .lua import (
    LUA_SIGNATURE, LUA_ERRSYNTAX, LUA_TNIL, LUA_TBOOLEAN,
    LUA_VERSION_MAJOR, LUA_VERSION_MINOR,
)
from .llimits import (
    lu_byte, Instruction, cast_num, lua_assert, LUAI_MAXSHORTLEN,
)
from .luaconf import (
    SIZEOF_INT, SIZEOF_SIZE_T, SIZEOF_INSTRUCTION,
    SIZEOF_LUA_INTEGER, SIZEOF_LUA_NUMBER, BYTE_ORDER,
)
from .lobject import (
    LUA_TNUMFLT, LUA_TNUMINT, LUA_TSHRSTR, LUA_TLNGSTR,
    Proto, LClosure, TString, TValue, Value, Upvaldesc, LocVar,
    setnilvalue, setbvalue, setfltvalue, setivalue, setsvalue2n,
)
from .lzio import ZIO, luaZ_read

if TYPE_CHECKING:
    from .lstate import LuaState

# =============================================================================
# lundump.h:16-23 - Constants for Bytecode Verification
# =============================================================================
# lundump.h:16 - data to catch conversion errors
LUAC_DATA: bytes = b"\x19\x93\r\n\x1a\n"

# lundump.h:18-19 - test values
LUAC_INT: int = 0x5678       # lundump.h:18 - integer test value
LUAC_NUM: float = 370.5      # lundump.h:19 - float test value (cast_num(370.5))

# lundump.h:22 - version number
def MYINT(s: str) -> int:
    """lundump.h:21 - #define MYINT(s) (s[0]-'0')"""
    return ord(s[0]) - ord('0')

LUAC_VERSION: int = MYINT(LUA_VERSION_MAJOR) * 16 + MYINT(LUA_VERSION_MINOR)  # 0x53

# lundump.h:23 - official format
LUAC_FORMAT: int = 0

# =============================================================================
# lundump.c:32-36 - LoadState Structure
# =============================================================================
@dataclass
class LoadState:
    """
    lundump.c:32-36 - Load state for undump
    
    typedef struct {
        lua_State *L;
        ZIO *Z;
        const char *name;
    } LoadState;
    
    Source: lundump.c:32-36
    """
    L: Optional['LuaState'] = None  # lundump.c:33
    Z: Optional[ZIO] = None         # lundump.c:34
    name: str = ""                  # lundump.c:35

# =============================================================================
# lundump.c:39-42 - Error Function
# =============================================================================
def error(S: LoadState, why: str) -> None:
    """
    lundump.c:39-42 - Report error during undump
    
    static l_noret error(LoadState *S, const char *why) {
        luaO_pushfstring(S->L, "%s: %s precompiled chunk", S->name, why);
        luaD_throw(S->L, LUA_ERRSYNTAX);
    }
    
    Source: lundump.c:39-42
    """
    raise LuaUndumpError(f"{S.name}: {why} precompiled chunk")

class LuaUndumpError(Exception):
    """Exception raised during bytecode loading"""
    pass

# =============================================================================
# lundump.c:45-54 - Load Block
# =============================================================================
def LoadBlock(S: LoadState, size: int) -> bytes:
    """
    lundump.c:51-54 - Load a block of bytes
    
    static void LoadBlock (LoadState *S, void *b, size_t size) {
        if (luaZ_read(S->Z, b, size) != 0)
            error(S, "truncated");
    }
    
    Source: lundump.c:51-54
    """
    b = bytearray(size)
    if luaZ_read(S.Z, b, size) != 0:
        error(S, "truncated")
    return bytes(b)

def LoadVector(S: LoadState, n: int, elem_size: int) -> bytes:
    """
    lundump.c:49 - #define LoadVector(S,b,n) LoadBlock(S,b,(n)*sizeof((b)[0]))
    Load a vector of elements
    Source: lundump.c:49
    """
    return LoadBlock(S, n * elem_size)

def LoadVar(S: LoadState, size: int) -> bytes:
    """
    lundump.c:57 - #define LoadVar(S,x) LoadVector(S,&x,1)
    Load a single variable
    Source: lundump.c:57
    """
    return LoadBlock(S, size)

# =============================================================================
# lundump.c:60-85 - Load Basic Types
# =============================================================================
def LoadByte(S: LoadState) -> int:
    """
    lundump.c:60-64 - Load a single byte
    
    static lu_byte LoadByte (LoadState *S) {
        lu_byte x;
        LoadVar(S, x);
        return x;
    }
    
    Source: lundump.c:60-64
    """
    data = LoadVar(S, 1)
    return data[0]

def LoadInt(S: LoadState) -> int:
    """
    lundump.c:67-71 - Load an int
    
    static int LoadInt (LoadState *S) {
        int x;
        LoadVar(S, x);
        return x;
    }
    
    Source: lundump.c:67-71
    """
    data = LoadVar(S, SIZEOF_INT)
    return struct.unpack(f'{BYTE_ORDER}i', data)[0]

def LoadNumber(S: LoadState) -> float:
    """
    lundump.c:74-78 - Load a lua_Number (double)
    
    static lua_Number LoadNumber (LoadState *S) {
        lua_Number x;
        LoadVar(S, x);
        return x;
    }
    
    Source: lundump.c:74-78
    """
    data = LoadVar(S, SIZEOF_LUA_NUMBER)
    return struct.unpack(f'{BYTE_ORDER}d', data)[0]

def LoadInteger(S: LoadState) -> int:
    """
    lundump.c:81-85 - Load a lua_Integer (long long)
    
    static lua_Integer LoadInteger (LoadState *S) {
        lua_Integer x;
        LoadVar(S, x);
        return x;
    }
    
    Source: lundump.c:81-85
    """
    data = LoadVar(S, SIZEOF_LUA_INTEGER)
    return struct.unpack(f'{BYTE_ORDER}q', data)[0]

# =============================================================================
# lundump.c:88-110 - Load String
# =============================================================================
def LoadString(S: LoadState, p: Proto) -> Optional[TString]:
    """
    lundump.c:88-110 - Load a string
    
    static TString *LoadString (LoadState *S, Proto *p) {
        lua_State *L = S->L;
        size_t size = LoadByte(S);
        TString *ts;
        if (size == 0xFF)
            LoadVar(S, size);
        if (size == 0)
            return NULL;
        else if (--size <= LUAI_MAXSHORTLEN) {  /* short string? */
            char buff[LUAI_MAXSHORTLEN];
            LoadVector(S, buff, size);
            ts = luaS_newlstr(L, buff, size);
        }
        else {  /* long string */
            ts = luaS_createlngstrobj(L, size);
            setsvalue2s(L, L->top, ts);  /* anchor it ('loadVector' can GC) */
            luaD_inctop(L);
            LoadVector(S, getstr(ts), size);  /* load directly in final place */
            L->top--;  /* pop string */
        }
        luaC_objbarrier(L, p, ts);
        return ts;
    }
    
    Source: lundump.c:88-110
    """
    L = S.L
    size = LoadByte(S)  # lundump.c:90
    
    # lundump.c:92-93 - check for long size
    if size == 0xFF:
        size_data = LoadVar(S, SIZEOF_SIZE_T)
        size = struct.unpack(f'{BYTE_ORDER}Q', size_data)[0]
    
    # lundump.c:94-95 - null string
    if size == 0:
        return None
    
    size -= 1  # lundump.c:96 - discount the stored size byte
    
    # Create TString
    ts = TString()
    
    if size <= LUAI_MAXSHORTLEN:  # lundump.c:96 - short string
        data = LoadVector(S, size, 1)  # lundump.c:98
        ts.tt = LUA_TSHRSTR
        ts.shrlen = size
        ts.data = data
    else:  # lundump.c:101 - long string
        data = LoadVector(S, size, 1)  # lundump.c:105
        ts.tt = LUA_TLNGSTR
        ts.lnglen = size
        ts.data = data
    
    # lundump.c:108 - luaC_objbarrier(L, p, ts)
    # GC barrier for string reference in proto. Skipped in PyLua as we use
    # Python's reference counting instead of incremental GC.
    
    return ts

# =============================================================================
# lundump.c:113-118 - Load Code
# =============================================================================
def LoadCode(S: LoadState, f: Proto) -> None:
    """
    lundump.c:113-118 - Load function code (instructions)
    
    static void LoadCode (LoadState *S, Proto *f) {
        int n = LoadInt(S);
        f->code = luaM_newvector(S->L, n, Instruction);
        f->sizecode = n;
        LoadVector(S, f->code, n);
    }
    
    Source: lundump.c:113-118
    """
    n = LoadInt(S)  # lundump.c:114
    f.sizecode = n  # lundump.c:116
    
    # lundump.c:117 - load instructions
    data = LoadVector(S, n, SIZEOF_INSTRUCTION)
    f.code = []
    for i in range(n):
        offset = i * SIZEOF_INSTRUCTION
        instr = struct.unpack(f'{BYTE_ORDER}I', data[offset:offset+SIZEOF_INSTRUCTION])[0]
        f.code.append(instr)

# =============================================================================
# lundump.c:124-155 - Load Constants
# =============================================================================
def LoadConstants(S: LoadState, f: Proto) -> None:
    """
    lundump.c:124-155 - Load function constants
    
    static void LoadConstants (LoadState *S, Proto *f) {
        int i;
        int n = LoadInt(S);
        f->k = luaM_newvector(S->L, n, TValue);
        f->sizek = n;
        for (i = 0; i < n; i++)
            setnilvalue(&f->k[i]);
        for (i = 0; i < n; i++) {
            TValue *o = &f->k[i];
            int t = LoadByte(S);
            switch (t) {
                case LUA_TNIL: setnilvalue(o); break;
                case LUA_TBOOLEAN: setbvalue(o, LoadByte(S)); break;
                case LUA_TNUMFLT: setfltvalue(o, LoadNumber(S)); break;
                case LUA_TNUMINT: setivalue(o, LoadInteger(S)); break;
                case LUA_TSHRSTR: case LUA_TLNGSTR:
                    setsvalue2n(S->L, o, LoadString(S, f)); break;
                default: lua_assert(0);
            }
        }
    }
    
    Source: lundump.c:124-155
    """
    n = LoadInt(S)  # lundump.c:126
    f.sizek = n     # lundump.c:128
    
    # lundump.c:129-130 - initialize with nil
    f.k = [TValue() for _ in range(n)]
    for i in range(n):
        setnilvalue(f.k[i])
    
    # lundump.c:131-154 - load each constant
    for i in range(n):
        o = f.k[i]
        t = LoadByte(S)  # lundump.c:133
        
        if t == LUA_TNIL:        # lundump.c:135
            setnilvalue(o)
        elif t == LUA_TBOOLEAN:  # lundump.c:138
            setbvalue(o, LoadByte(S))
        elif t == LUA_TNUMFLT:   # lundump.c:141
            setfltvalue(o, LoadNumber(S))
        elif t == LUA_TNUMINT:   # lundump.c:144
            setivalue(o, LoadInteger(S))
        elif t == LUA_TSHRSTR or t == LUA_TLNGSTR:  # lundump.c:147-148
            ts = LoadString(S, f)
            if ts is not None:
                setsvalue2n(S.L, o, ts)
        else:  # lundump.c:151
            lua_assert(False)

# =============================================================================
# lundump.c:158-170 - Load Protos (nested functions)
# =============================================================================
def LoadProtos(S: LoadState, f: Proto) -> None:
    """
    lundump.c:158-170 - Load nested function prototypes
    
    static void LoadProtos (LoadState *S, Proto *f) {
        int i;
        int n = LoadInt(S);
        f->p = luaM_newvector(S->L, n, Proto *);
        f->sizep = n;
        for (i = 0; i < n; i++)
            f->p[i] = NULL;
        for (i = 0; i < n; i++) {
            f->p[i] = luaF_newproto(S->L);
            luaC_objbarrier(S->L, f, f->p[i]);
            LoadFunction(S, f->p[i], f->source);
        }
    }
    
    Source: lundump.c:158-170
    """
    n = LoadInt(S)  # lundump.c:160
    f.sizep = n     # lundump.c:162
    
    # lundump.c:163-164 - initialize with NULL
    f.p = [None] * n
    
    # lundump.c:165-169 - load each proto
    for i in range(n):
        f.p[i] = luaF_newproto(S.L)  # lundump.c:166
        # lundump.c:167 - luaC_objbarrier(S->L, f, f->p[i])
        # GC barrier skipped in PyLua (Python reference counting)
        LoadFunction(S, f.p[i], f.source)  # lundump.c:168

# =============================================================================
# lundump.c:173-184 - Load Upvalues
# =============================================================================
def LoadUpvalues(S: LoadState, f: Proto) -> None:
    """
    lundump.c:173-184 - Load upvalue descriptions
    
    static void LoadUpvalues (LoadState *S, Proto *f) {
        int i, n;
        n = LoadInt(S);
        f->upvalues = luaM_newvector(S->L, n, Upvaldesc);
        f->sizeupvalues = n;
        for (i = 0; i < n; i++)
            f->upvalues[i].name = NULL;
        for (i = 0; i < n; i++) {
            f->upvalues[i].instack = LoadByte(S);
            f->upvalues[i].idx = LoadByte(S);
        }
    }
    
    Source: lundump.c:173-184
    """
    n = LoadInt(S)      # lundump.c:175
    f.sizeupvalues = n  # lundump.c:177
    
    # lundump.c:178-179 - initialize
    f.upvalues = [Upvaldesc() for _ in range(n)]
    for i in range(n):
        f.upvalues[i].name = None
    
    # lundump.c:180-183 - load upvalue info
    for i in range(n):
        f.upvalues[i].instack = LoadByte(S)  # lundump.c:181
        f.upvalues[i].idx = LoadByte(S)       # lundump.c:182

# =============================================================================
# lundump.c:187-206 - Load Debug Info
# =============================================================================
def LoadDebug(S: LoadState, f: Proto) -> None:
    """
    lundump.c:187-206 - Load debug information
    
    static void LoadDebug (LoadState *S, Proto *f) {
        int i, n;
        n = LoadInt(S);
        f->lineinfo = luaM_newvector(S->L, n, int);
        f->sizelineinfo = n;
        LoadVector(S, f->lineinfo, n);
        n = LoadInt(S);
        f->locvars = luaM_newvector(S->L, n, LocVar);
        f->sizelocvars = n;
        for (i = 0; i < n; i++)
            f->locvars[i].varname = NULL;
        for (i = 0; i < n; i++) {
            f->locvars[i].varname = LoadString(S, f);
            f->locvars[i].startpc = LoadInt(S);
            f->locvars[i].endpc = LoadInt(S);
        }
        n = LoadInt(S);
        for (i = 0; i < n; i++)
            f->upvalues[i].name = LoadString(S, f);
    }
    
    Source: lundump.c:187-206
    """
    # lundump.c:189-192 - load line info
    n = LoadInt(S)
    f.sizelineinfo = n
    data = LoadVector(S, n, SIZEOF_INT)
    f.lineinfo = []
    for i in range(n):
        offset = i * SIZEOF_INT
        line = struct.unpack(f'{BYTE_ORDER}i', data[offset:offset+SIZEOF_INT])[0]
        f.lineinfo.append(line)
    
    # lundump.c:193-202 - load local variables
    n = LoadInt(S)
    f.sizelocvars = n
    f.locvars = [LocVar() for _ in range(n)]
    for i in range(n):
        f.locvars[i].varname = None
    for i in range(n):
        f.locvars[i].varname = LoadString(S, f)  # lundump.c:199
        f.locvars[i].startpc = LoadInt(S)        # lundump.c:200
        f.locvars[i].endpc = LoadInt(S)          # lundump.c:201
    
    # lundump.c:203-205 - load upvalue names
    n = LoadInt(S)
    for i in range(n):
        f.upvalues[i].name = LoadString(S, f)  # lundump.c:205

# =============================================================================
# lundump.c:209-223 - Load Function
# =============================================================================
def LoadFunction(S: LoadState, f: Proto, psource: Optional[TString]) -> None:
    """
    lundump.c:209-223 - Load a function prototype
    
    static void LoadFunction (LoadState *S, Proto *f, TString *psource) {
        f->source = LoadString(S, f);
        if (f->source == NULL)  /* no source in dump? */
            f->source = psource;  /* reuse parent's source */
        f->linedefined = LoadInt(S);
        f->lastlinedefined = LoadInt(S);
        f->numparams = LoadByte(S);
        f->is_vararg = LoadByte(S);
        f->maxstacksize = LoadByte(S);
        LoadCode(S, f);
        LoadConstants(S, f);
        LoadUpvalues(S, f);
        LoadProtos(S, f);
        LoadDebug(S, f);
    }
    
    Source: lundump.c:209-223
    """
    f.source = LoadString(S, f)  # lundump.c:210
    if f.source is None:          # lundump.c:211
        f.source = psource        # lundump.c:212
    
    f.linedefined = LoadInt(S)      # lundump.c:213
    f.lastlinedefined = LoadInt(S)  # lundump.c:214
    f.numparams = LoadByte(S)       # lundump.c:215
    f.is_vararg = LoadByte(S)       # lundump.c:216
    f.maxstacksize = LoadByte(S)    # lundump.c:217
    
    LoadCode(S, f)       # lundump.c:218
    LoadConstants(S, f)  # lundump.c:219
    LoadUpvalues(S, f)   # lundump.c:220
    LoadProtos(S, f)     # lundump.c:221
    LoadDebug(S, f)      # lundump.c:222

# =============================================================================
# lundump.c:226-232 / 235-238 - Check Literal and Size
# =============================================================================
def checkliteral(S: LoadState, s: bytes, msg: str) -> None:
    """
    lundump.c:226-232 - Check literal bytes match
    
    static void checkliteral (LoadState *S, const char *s, const char *msg) {
        char buff[sizeof(LUA_SIGNATURE) + sizeof(LUAC_DATA)];
        size_t len = strlen(s);
        LoadVector(S, buff, len);
        if (memcmp(s, buff, len) != 0)
            error(S, msg);
    }
    
    Source: lundump.c:226-232
    """
    buff = LoadVector(S, len(s), 1)  # lundump.c:229
    if buff != s:                     # lundump.c:230
        error(S, msg)

def fchecksize(S: LoadState, size: int, tname: str) -> None:
    """
    lundump.c:235-238 - Check type size matches
    
    static void fchecksize (LoadState *S, size_t size, const char *tname) {
        if (LoadByte(S) != size)
            error(S, luaO_pushfstring(S->L, "%s size mismatch in", tname));
    }
    
    Source: lundump.c:235-238
    """
    if LoadByte(S) != size:  # lundump.c:236
        error(S, f"{tname} size mismatch in")

# =============================================================================
# lundump.c:243-259 - Check Header
# =============================================================================
def checkHeader(S: LoadState) -> None:
    """
    lundump.c:243-259 - Check bytecode header
    
    static void checkHeader (LoadState *S) {
        checkliteral(S, LUA_SIGNATURE + 1, "not a");
        if (LoadByte(S) != LUAC_VERSION)
            error(S, "version mismatch in");
        if (LoadByte(S) != LUAC_FORMAT)
            error(S, "format mismatch in");
        checkliteral(S, LUAC_DATA, "corrupted");
        checksize(S, int);
        checksize(S, size_t);
        checksize(S, Instruction);
        checksize(S, lua_Integer);
        checksize(S, lua_Number);
        if (LoadInteger(S) != LUAC_INT)
            error(S, "endianness mismatch in");
        if (LoadNumber(S) != LUAC_NUM)
            error(S, "float format mismatch in");
    }
    
    Source: lundump.c:243-259
    """
    # lundump.c:244 - check signature (skip first byte, already checked)
    checkliteral(S, LUA_SIGNATURE[1:], "not a")
    
    # lundump.c:245-246 - check version
    if LoadByte(S) != LUAC_VERSION:
        error(S, "version mismatch in")
    
    # lundump.c:247-248 - check format
    if LoadByte(S) != LUAC_FORMAT:
        error(S, "format mismatch in")
    
    # lundump.c:249 - check LUAC_DATA
    checkliteral(S, LUAC_DATA, "corrupted")
    
    # lundump.c:250-254 - check sizes
    fchecksize(S, SIZEOF_INT, "int")
    fchecksize(S, SIZEOF_SIZE_T, "size_t")
    fchecksize(S, SIZEOF_INSTRUCTION, "Instruction")
    fchecksize(S, SIZEOF_LUA_INTEGER, "lua_Integer")
    fchecksize(S, SIZEOF_LUA_NUMBER, "lua_Number")
    
    # lundump.c:255-256 - check endianness
    if LoadInteger(S) != LUAC_INT:
        error(S, "endianness mismatch in")
    
    # lundump.c:257-258 - check float format
    if LoadNumber(S) != LUAC_NUM:
        error(S, "float format mismatch in")

# =============================================================================
# lundump.c:265-286 - luaU_undump (Main Entry Point)
# =============================================================================
def luaU_undump(L: 'LuaState', Z: ZIO, name: str) -> LClosure:
    """
    lundump.h:26 / lundump.c:265-286 - Load precompiled chunk
    
    LClosure* luaU_undump (lua_State* L, ZIO* Z, const char* name)
    
    static void LoadFunction (LoadState *S, Proto *f, TString *psource);
    
    LClosure *luaU_undump(lua_State *L, ZIO *Z, const char *name) {
        LoadState S;
        LClosure *cl;
        if (*name == '@' || *name == '=')
            S.name = name + 1;
        else if (*name == LUA_SIGNATURE[0])
            S.name = "binary string";
        else
            S.name = name;
        S.L = L;
        S.Z = Z;
        checkHeader(&S);
        cl = luaF_newLclosure(L, LoadByte(&S));
        setclLvalue(L, L->top, cl);
        luaD_inctop(L);
        cl->p = luaF_newproto(L);
        luaC_objbarrier(L, cl, cl->p);
        LoadFunction(&S, cl->p, NULL);
        lua_assert(cl->nupvalues == cl->p->sizeupvalues);
        luai_verifycode(L, buff, cl->p);
        return cl;
    }
    
    Source: lundump.c:265-286
    """
    S = LoadState()
    
    # lundump.c:268-273 - set name
    if name and (name[0] == '@' or name[0] == '='):
        S.name = name[1:]  # lundump.c:269
    elif name and len(name) > 0 and ord(name[0]) == LUA_SIGNATURE[0]:
        S.name = "binary string"  # lundump.c:271
    else:
        S.name = name  # lundump.c:273
    
    S.L = L  # lundump.c:274
    S.Z = Z  # lundump.c:275
    
    checkHeader(S)  # lundump.c:276
    
    # lundump.c:277 - create closure
    nupvalues = LoadByte(S)
    cl = luaF_newLclosure(L, nupvalues)
    
    # lundump.c:278-279 - push closure on stack (anchor for GC)
    from .lobject import setclLvalue, ctb, LUA_TLCL
    setclLvalue(L, L.stack[L.top], cl)
    L.top += 1  # luaD_inctop equivalent
    
    # lundump.c:280 - create prototype
    cl.p = luaF_newproto(L)
    
    # lundump.c:281 - luaC_objbarrier(L, cl, cl->p)
    # GC barrier - in Python, we don't need explicit barriers since we use
    # reference counting. The barrier ensures the collector knows about the
    # reference from cl to cl->p. We skip this as PyLua doesn't implement
    # incremental GC.
    
    # lundump.c:282 - load function
    LoadFunction(S, cl.p, None)
    
    # lundump.c:283 - verify upvalue count
    lua_assert(cl.nupvalues == cl.p.sizeupvalues)
    
    # lundump.c:284 - luai_verifycode(L, buff, cl->p)
    # Code verification - optional, skipped in release builds
    # In debug builds, this validates the bytecode. We skip it as
    # PyLua trusts the Lua 5.3 compiler output.
    
    # Pop the anchor (closure is returned, not left on stack)
    L.top -= 1
    
    return cl

# =============================================================================
# Import Functions from lfunc.py
# =============================================================================
from .lfunc import luaF_newproto, luaF_newLclosure
