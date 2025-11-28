# -*- coding: utf-8 -*-
"""
ldump.py - save precompiled Lua chunks
======================================
Source: ldump.c (lua-5.3.6/src/ldump.c)

Save precompiled Lua chunks - Fully compatible with Lua 5.3.6 bytecode format.
See Copyright Notice in lua.h
"""

import struct
from typing import Optional, Callable, Any, TYPE_CHECKING
from io import BytesIO

from .lobject import (
    Proto, TString, TValue,
    LUA_TNIL, LUA_TBOOLEAN, LUA_TNUMFLT, LUA_TNUMINT,
    LUA_TSHRSTR, LUA_TLNGSTR,
    ttisnil, ttisboolean, ttisinteger, ttisfloat, ttisstring,
    ttisshrstring, ttislngstring,
    bvalue, ivalue, fltvalue, tsvalue, getstr, tsslen, ttype,
)
from .llimits import cast_byte, cast_int, lua_assert

if TYPE_CHECKING:
    from .lstate import LuaState

# =============================================================================
# lundump.h:12-18 - Bytecode Header Constants
# =============================================================================

# lundump.h:12
LUA_SIGNATURE = b"\x1bLua"

# lundump.h:14 - data to catch conversion errors
LUAC_DATA = b"\x19\x93\r\n\x1a\n"

# lundump.h:16 - version (5.3 = 0x53)
LUAC_VERSION = 0x53

# lundump.h:17 - format version (official = 0)
LUAC_FORMAT = 0

# lundump.h:18 - test numbers
LUAC_INT = 0x5678
LUAC_NUM = 370.5

# Size configuration for 64-bit platform (standard Lua 5.3)
SIZEOF_INT = 4
SIZEOF_SIZE_T = 8
SIZEOF_INSTRUCTION = 4
SIZEOF_LUA_INTEGER = 8
SIZEOF_LUA_NUMBER = 8


# =============================================================================
# ldump.c:22-28 - DumpState
# =============================================================================

class DumpState:
    """
    ldump.c:22-28 - State for bytecode dumping
    
    typedef struct {
        lua_State *L;
        lua_Writer writer;
        void *data;
        int strip;
        int status;
    } DumpState;
    """
    def __init__(self, L: 'LuaState', writer: Callable, data: Any, strip: int):
        self.L = L
        self.writer = writer
        self.data = data
        self.strip = strip
        self.status = 0
        self._buffer = BytesIO()
    
    def write(self, data: bytes) -> None:
        """Write data using the writer callback"""
        if self.status == 0 and len(data) > 0:
            self._buffer.write(data)
    
    def getvalue(self) -> bytes:
        return self._buffer.getvalue()


# =============================================================================
# ldump.c:40-55 - Basic Dump Functions
# =============================================================================

def DumpBlock(b: bytes, D: DumpState) -> None:
    """ldump.c:40-46 - Write raw bytes"""
    D.write(b)


def DumpVar(x: bytes, D: DumpState) -> None:
    """ldump.c:49 - #define DumpVar(x,D) DumpVector(&x,1,D)"""
    D.write(x)


def DumpByte(y: int, D: DumpState) -> None:
    """ldump.c:52-55 - Write single byte"""
    D.write(bytes([y & 0xFF]))


def DumpInt(x: int, D: DumpState) -> None:
    """ldump.c:58-60 - Write int (4 bytes, little-endian)"""
    D.write(struct.pack('<i', x))


def DumpNumber(x: float, D: DumpState) -> None:
    """ldump.c:63-65 - Write lua_Number (8-byte double, little-endian)"""
    D.write(struct.pack('<d', x))


def DumpInteger(x: int, D: DumpState) -> None:
    """ldump.c:68-70 - Write lua_Integer (8-byte signed int, little-endian)"""
    D.write(struct.pack('<q', x))


def DumpString(s: Optional[TString], D: DumpState) -> None:
    """
    ldump.c:73-87 - Write string
    
    static void DumpString (const TString *s, DumpState *D) {
        if (s == NULL)
            DumpByte(0, D);
        else {
            size_t size = tsslen(s) + 1;  /* include trailing '\\0' */
            const char *str = getstr(s);
            if (size < 0xFF)
                DumpByte(cast_int(size), D);
            else {
                DumpByte(0xFF, D);
                DumpVar(size, D);
            }
            DumpVector(str, size - 1, D);  /* no need to save '\\0' */
        }
    }
    """
    if s is None:
        DumpByte(0, D)
    else:
        size = tsslen(s) + 1  # include trailing '\0'
        str_data = getstr(s)
        if size < 0xFF:
            DumpByte(cast_int(size), D)
        else:
            DumpByte(0xFF, D)
            # DumpVar(size) - write size_t (8 bytes)
            D.write(struct.pack('<Q', size))
        # DumpVector(str, size - 1) - no need to save '\0'
        D.write(str_data[:size - 1])


def DumpStringRaw(s: Optional[bytes], D: DumpState) -> None:
    """
    Write string from raw bytes (helper for cases where we don't have TString)
    """
    if s is None:
        DumpByte(0, D)
    else:
        size = len(s) + 1  # include trailing '\0'
        if size < 0xFF:
            DumpByte(cast_int(size), D)
        else:
            DumpByte(0xFF, D)
            D.write(struct.pack('<Q', size))
        D.write(s)


# =============================================================================
# ldump.c:90-93 - DumpCode
# =============================================================================

def DumpCode(f: Proto, D: DumpState) -> None:
    """
    ldump.c:90-93 - Dump instruction code
    
    static void DumpCode (const Proto *f, DumpState *D) {
        DumpInt(f->sizecode, D);
        DumpVector(f->code, f->sizecode, D);
    }
    """
    n = len(f.code)
    DumpInt(n, D)
    for inst in f.code:
        D.write(struct.pack('<I', inst & 0xFFFFFFFF))


# =============================================================================
# ldump.c:98-125 - DumpConstants
# =============================================================================

def DumpConstants(f: Proto, D: DumpState) -> None:
    """
    ldump.c:98-125 - Dump constants table
    
    static void DumpConstants (const Proto *f, DumpState *D) {
        int i;
        int n = f->sizek;
        DumpInt(n, D);
        for (i = 0; i < n; i++) {
            const TValue *o = &f->k[i];
            DumpByte(ttype(o), D);
            switch (ttype(o)) {
            case LUA_TNIL:
                break;
            case LUA_TBOOLEAN:
                DumpByte(bvalue(o), D);
                break;
            case LUA_TNUMFLT:
                DumpNumber(fltvalue(o), D);
                break;
            case LUA_TNUMINT:
                DumpInteger(ivalue(o), D);
                break;
            case LUA_TSHRSTR:
            case LUA_TLNGSTR:
                DumpString(tsvalue(o), D);
                break;
            default:
                lua_assert(0);
            }
        }
    }
    """
    n = len(f.k)
    DumpInt(n, D)
    
    for o in f.k:
        tt = ttype(o)
        DumpByte(tt, D)
        
        if tt == LUA_TNIL:
            pass
        elif tt == LUA_TBOOLEAN:
            DumpByte(bvalue(o), D)
        elif tt == LUA_TNUMFLT:
            DumpNumber(fltvalue(o), D)
        elif tt == LUA_TNUMINT:
            DumpInteger(ivalue(o), D)
        elif tt == LUA_TSHRSTR or tt == LUA_TLNGSTR:
            DumpString(tsvalue(o), D)
        else:
            lua_assert(False)


# =============================================================================
# ldump.c:128-134 - DumpProtos
# =============================================================================

def DumpProtos(f: Proto, D: DumpState) -> None:
    """
    ldump.c:128-134 - Dump nested prototypes
    
    static void DumpProtos (const Proto *f, DumpState *D) {
        int i;
        int n = f->sizep;
        DumpInt(n, D);
        for (i = 0; i < n; i++)
            DumpFunction(f->p[i], f->source, D);
    }
    """
    n = len(f.p)
    DumpInt(n, D)
    for sub in f.p:
        DumpFunction(sub, f.source, D)


# =============================================================================
# ldump.c:137-144 - DumpUpvalues
# =============================================================================

def DumpUpvalues(f: Proto, D: DumpState) -> None:
    """
    ldump.c:137-144 - Dump upvalues
    
    static void DumpUpvalues (const Proto *f, DumpState *D) {
        int i, n = f->sizeupvalues;
        DumpInt(n, D);
        for (i = 0; i < n; i++) {
            DumpByte(f->upvalues[i].instack, D);
            DumpByte(f->upvalues[i].idx, D);
        }
    }
    """
    n = len(f.upvalues)
    DumpInt(n, D)
    for uv in f.upvalues:
        DumpByte(uv.instack, D)
        DumpByte(uv.idx, D)


# =============================================================================
# ldump.c:147-163 - DumpDebug
# =============================================================================

def DumpDebug(f: Proto, D: DumpState) -> None:
    """
    ldump.c:147-163 - Dump debug information
    
    static void DumpDebug (const Proto *f, DumpState *D) {
        int i, n;
        n = (D->strip) ? 0 : f->sizelineinfo;
        DumpInt(n, D);
        DumpVector(f->lineinfo, n, D);
        n = (D->strip) ? 0 : f->sizelocvars;
        DumpInt(n, D);
        for (i = 0; i < n; i++) {
            DumpString(f->locvars[i].varname, D);
            DumpInt(f->locvars[i].startpc, D);
            DumpInt(f->locvars[i].endpc, D);
        }
        n = (D->strip) ? 0 : f->sizeupvalues;
        DumpInt(n, D);
        for (i = 0; i < n; i++)
            DumpString(f->upvalues[i].name, D);
    }
    """
    # Line info
    n = 0 if D.strip else len(f.lineinfo)
    DumpInt(n, D)
    for i in range(n):
        DumpInt(f.lineinfo[i], D)
    
    # Local variables
    n = 0 if D.strip else len(f.locvars)
    DumpInt(n, D)
    for i in range(n):
        lv = f.locvars[i]
        DumpString(lv.varname, D)
        DumpInt(lv.startpc, D)
        DumpInt(lv.endpc, D)
    
    # Upvalue names
    n = 0 if D.strip else len(f.upvalues)
    DumpInt(n, D)
    for i in range(n):
        DumpString(f.upvalues[i].name, D)


# =============================================================================
# ldump.c:166-181 - DumpFunction
# =============================================================================

def DumpFunction(f: Proto, psource: Optional[TString], D: DumpState) -> None:
    """
    ldump.c:166-181 - Dump a function prototype
    
    static void DumpFunction (const Proto *f, TString *psource, DumpState *D) {
        if (D->strip || f->source == psource)
            DumpString(NULL, D);  /* no debug info or same source as its parent */
        else
            DumpString(f->source, D);
        DumpInt(f->linedefined, D);
        DumpInt(f->lastlinedefined, D);
        DumpByte(f->numparams, D);
        DumpByte(f->is_vararg, D);
        DumpByte(f->maxstacksize, D);
        DumpCode(f, D);
        DumpConstants(f, D);
        DumpUpvalues(f, D);
        DumpProtos(f, D);
        DumpDebug(f, D);
    }
    """
    # Source name
    if D.strip or f.source is psource:
        DumpString(None, D)  # no debug info or same source as parent
    else:
        DumpString(f.source, D)
    
    DumpInt(f.linedefined, D)
    DumpInt(f.lastlinedefined, D)
    DumpByte(f.numparams, D)
    DumpByte(f.is_vararg, D)
    DumpByte(f.maxstacksize, D)
    
    DumpCode(f, D)
    DumpConstants(f, D)
    DumpUpvalues(f, D)
    DumpProtos(f, D)
    DumpDebug(f, D)


# =============================================================================
# ldump.c:184-196 - DumpHeader
# =============================================================================

def DumpHeader(D: DumpState) -> None:
    """
    ldump.c:184-196 - Dump Lua bytecode header
    
    static void DumpHeader (DumpState *D) {
        DumpLiteral(LUA_SIGNATURE, D);
        DumpByte(LUAC_VERSION, D);
        DumpByte(LUAC_FORMAT, D);
        DumpLiteral(LUAC_DATA, D);
        DumpByte(sizeof(int), D);
        DumpByte(sizeof(size_t), D);
        DumpByte(sizeof(Instruction), D);
        DumpByte(sizeof(lua_Integer), D);
        DumpByte(sizeof(lua_Number), D);
        DumpInteger(LUAC_INT, D);
        DumpNumber(LUAC_NUM, D);
    }
    """
    # DumpLiteral(LUA_SIGNATURE)
    D.write(LUA_SIGNATURE)
    DumpByte(LUAC_VERSION, D)
    DumpByte(LUAC_FORMAT, D)
    # DumpLiteral(LUAC_DATA)
    D.write(LUAC_DATA)
    DumpByte(SIZEOF_INT, D)
    DumpByte(SIZEOF_SIZE_T, D)
    DumpByte(SIZEOF_INSTRUCTION, D)
    DumpByte(SIZEOF_LUA_INTEGER, D)
    DumpByte(SIZEOF_LUA_NUMBER, D)
    DumpInteger(LUAC_INT, D)
    DumpNumber(LUAC_NUM, D)


# =============================================================================
# ldump.c:202-214 - luaU_dump
# =============================================================================

def luaU_dump(L: 'LuaState', f: Proto, w: Callable = None, 
              data: Any = None, strip: int = 0) -> bytes:
    """
    ldump.c:202-214 - dump Lua function as precompiled chunk
    
    int luaU_dump(lua_State *L, const Proto *f, lua_Writer w, void *data,
                  int strip) {
        DumpState D;
        D.L = L;
        D.writer = w;
        D.data = data;
        D.strip = strip;
        D.status = 0;
        DumpHeader(&D);
        DumpByte(f->sizeupvalues, &D);
        DumpFunction(f, NULL, &D);
        return D.status;
    }
    
    Returns the dumped bytecode as bytes.
    """
    D = DumpState(L, w, data, strip)
    
    DumpHeader(D)
    DumpByte(len(f.upvalues), D)  # f->sizeupvalues
    DumpFunction(f, None, D)
    
    return D.getvalue()


# =============================================================================
# Convenience functions
# =============================================================================

def dump_bytecode(proto: Proto, strip: bool = False) -> bytes:
    """
    Convenience function to dump Proto to bytecode
    
    Args:
        proto: The Proto object to dump
        strip: Whether to strip debug info
    
    Returns:
        Lua 5.3 compatible bytecode as bytes
    """
    return luaU_dump(None, proto, None, None, 1 if strip else 0)
