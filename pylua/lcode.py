# -*- coding: utf-8 -*-
"""
lcode.py - Code Generator for Lua
=================================
Source: lcode.h/lcode.c (lua-5.3.6/src/lcode.h, lcode.c)

Code generator for Lua
See Copyright Notice in lua.h
"""

from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass
from enum import IntEnum

from .lua import lua_Integer, lua_Number, LUA_MULTRET
from .llimits import lu_byte, MAX_INT, lua_assert, cast_byte, cast_int
from .lobject import (
    TValue, TString, Proto,
    setivalue, setfltvalue, setnilvalue, setbvalue,
    ttisinteger, ttisfloat, ivalue, fltvalue,
)
from .lopcodes import (
    OpCode, Instruction,
    CREATE_ABC, CREATE_ABx, CREATE_Ax,
    GETARG_A, GETARG_B, GETARG_C, GETARG_Bx, GETARG_sBx,
    SETARG_A, SETARG_B, SETARG_C, SETARG_Bx, SETARG_sBx,
    GET_OPCODE, SET_OPCODE,
    MAXARG_A, MAXARG_B, MAXARG_C, MAXARG_Bx, MAXARG_sBx,
    ISK, INDEXK, RKASK, BITRK,
)

# Import opcodes from OpCode enum
OP_MOVE = OpCode.OP_MOVE
OP_LOADK = OpCode.OP_LOADK
OP_LOADKX = OpCode.OP_LOADKX
OP_LOADBOOL = OpCode.OP_LOADBOOL
OP_LOADNIL = OpCode.OP_LOADNIL
OP_GETUPVAL = OpCode.OP_GETUPVAL
OP_GETTABUP = OpCode.OP_GETTABUP
OP_GETTABLE = OpCode.OP_GETTABLE
OP_SETTABUP = OpCode.OP_SETTABUP
OP_SETUPVAL = OpCode.OP_SETUPVAL
OP_SETTABLE = OpCode.OP_SETTABLE
OP_NEWTABLE = OpCode.OP_NEWTABLE
OP_SELF = OpCode.OP_SELF
OP_ADD = OpCode.OP_ADD
OP_SUB = OpCode.OP_SUB
OP_MUL = OpCode.OP_MUL
OP_MOD = OpCode.OP_MOD
OP_POW = OpCode.OP_POW
OP_DIV = OpCode.OP_DIV
OP_IDIV = OpCode.OP_IDIV
OP_BAND = OpCode.OP_BAND
OP_BOR = OpCode.OP_BOR
OP_BXOR = OpCode.OP_BXOR
OP_SHL = OpCode.OP_SHL
OP_SHR = OpCode.OP_SHR
OP_UNM = OpCode.OP_UNM
OP_BNOT = OpCode.OP_BNOT
OP_NOT = OpCode.OP_NOT
OP_LEN = OpCode.OP_LEN
OP_CONCAT = OpCode.OP_CONCAT
OP_JMP = OpCode.OP_JMP
OP_EQ = OpCode.OP_EQ
OP_LT = OpCode.OP_LT
OP_LE = OpCode.OP_LE
OP_TEST = OpCode.OP_TEST
OP_TESTSET = OpCode.OP_TESTSET
OP_CALL = OpCode.OP_CALL
OP_TAILCALL = OpCode.OP_TAILCALL
OP_RETURN = OpCode.OP_RETURN
OP_FORLOOP = OpCode.OP_FORLOOP
OP_FORPREP = OpCode.OP_FORPREP
OP_TFORCALL = OpCode.OP_TFORCALL
OP_TFORLOOP = OpCode.OP_TFORLOOP
OP_SETLIST = OpCode.OP_SETLIST
OP_CLOSURE = OpCode.OP_CLOSURE
OP_VARARG = OpCode.OP_VARARG
OP_EXTRAARG = OpCode.OP_EXTRAARG

if TYPE_CHECKING:
    from .lparser import FuncState, expdesc
    from .llex import LexState


# =============================================================================
# lcode.h:20 - NO_JUMP constant
# =============================================================================
NO_JUMP = -1


# =============================================================================
# lcode.c:33 - Maximum registers
# =============================================================================
MAXREGS = 255


# =============================================================================
# lcode.h:26-37 - Binary Operators
# =============================================================================
class BinOpr(IntEnum):
    """lcode.h:26-37 - Binary operators (ORDER OPR)"""
    OPR_ADD = 0
    OPR_SUB = 1
    OPR_MUL = 2
    OPR_MOD = 3
    OPR_POW = 4
    OPR_DIV = 5
    OPR_IDIV = 6
    OPR_BAND = 7
    OPR_BOR = 8
    OPR_BXOR = 9
    OPR_SHL = 10
    OPR_SHR = 11
    OPR_CONCAT = 12
    OPR_EQ = 13
    OPR_LT = 14
    OPR_LE = 15
    OPR_NE = 16
    OPR_GT = 17
    OPR_GE = 18
    OPR_AND = 19
    OPR_OR = 20
    OPR_NOBINOPR = 21


# Convenience aliases
OPR_ADD = BinOpr.OPR_ADD
OPR_SUB = BinOpr.OPR_SUB
OPR_MUL = BinOpr.OPR_MUL
OPR_MOD = BinOpr.OPR_MOD
OPR_POW = BinOpr.OPR_POW
OPR_DIV = BinOpr.OPR_DIV
OPR_IDIV = BinOpr.OPR_IDIV
OPR_BAND = BinOpr.OPR_BAND
OPR_BOR = BinOpr.OPR_BOR
OPR_BXOR = BinOpr.OPR_BXOR
OPR_SHL = BinOpr.OPR_SHL
OPR_SHR = BinOpr.OPR_SHR
OPR_CONCAT = BinOpr.OPR_CONCAT
OPR_EQ = BinOpr.OPR_EQ
OPR_LT = BinOpr.OPR_LT
OPR_LE = BinOpr.OPR_LE
OPR_NE = BinOpr.OPR_NE
OPR_GT = BinOpr.OPR_GT
OPR_GE = BinOpr.OPR_GE
OPR_AND = BinOpr.OPR_AND
OPR_OR = BinOpr.OPR_OR
OPR_NOBINOPR = BinOpr.OPR_NOBINOPR


# =============================================================================
# lcode.h:40 - Unary Operators
# =============================================================================
class UnOpr(IntEnum):
    """lcode.h:40 - Unary operators"""
    OPR_MINUS = 0
    OPR_BNOT = 1
    OPR_NOT = 2
    OPR_LEN = 3
    OPR_NOUNOPR = 4


OPR_MINUS = UnOpr.OPR_MINUS
OPR_BNOT = UnOpr.OPR_BNOT
OPR_NOT = UnOpr.OPR_NOT
OPR_LEN = UnOpr.OPR_LEN
OPR_NOUNOPR = UnOpr.OPR_NOUNOPR


# =============================================================================
# lcode.c:36 - hasjumps macro
# =============================================================================
def hasjumps(e: 'expdesc') -> bool:
    """lcode.c:36 - #define hasjumps(e) ((e)->t != (e)->f)"""
    return e.t != e.f


# =============================================================================
# lcode.h:44 - getinstruction macro
# =============================================================================
def getinstruction(fs: 'FuncState', e: 'expdesc') -> Instruction:
    """lcode.h:44 - #define getinstruction(fs,e) ((fs)->f->code[(e)->u.info])"""
    return fs.f.code[e.info]


# =============================================================================
# lcode.c:43-55 - tonumeral
# =============================================================================
def tonumeral(e: 'expdesc', v: Optional[TValue]) -> bool:
    """
    lcode.c:43-55 - If expression is a numeric constant, fills 'v' with value
    
    static int tonumeral(const expdesc *e, TValue *v)
    """
    from .lparser import VKINT, VKFLT
    
    if hasjumps(e):
        return False
    
    if e.k == VKINT:
        if v is not None:
            setivalue(v, e.ival)
        return True
    elif e.k == VKFLT:
        if v is not None:
            setfltvalue(v, e.nval)
        return True
    else:
        return False


# =============================================================================
# lcode.c:64-83 - luaK_nil
# =============================================================================
def luaK_nil(fs: 'FuncState', from_reg: int, n: int) -> None:
    """
    lcode.c:64-83 - Create OP_LOADNIL instruction with optimization
    
    void luaK_nil (FuncState *fs, int from, int n)
    """
    l = from_reg + n - 1  # Last register to set nil
    
    if fs.pc > fs.lasttarget:  # No jumps to current position?
        if fs.pc > 0:
            previous = fs.f.code[fs.pc - 1]
            if GET_OPCODE(previous) == OP_LOADNIL:
                pfrom = GETARG_A(previous)
                pl = pfrom + GETARG_B(previous)
                if (pfrom <= from_reg <= pl + 1) or (from_reg <= pfrom <= l + 1):
                    from_reg = min(from_reg, pfrom)
                    l = max(l, pl)
                    fs.f.code[fs.pc - 1] = CREATE_ABC(OP_LOADNIL, from_reg, l - from_reg, 0)
                    return
    
    luaK_codeABC(fs, OP_LOADNIL, from_reg, n - 1, 0)


# =============================================================================
# lcode.c:90-96, 100-117 - Jump utilities
# =============================================================================
def getjump(fs: 'FuncState', pc: int) -> int:
    """lcode.c:90-96 - Get destination of jump instruction"""
    offset = GETARG_sBx(fs.f.code[pc])
    if offset == NO_JUMP:
        return NO_JUMP
    return (pc + 1) + offset


def fixjump(fs: 'FuncState', pc: int, dest: int) -> None:
    """lcode.c:100-106 - Fix jump instruction to jump to dest"""
    jmp = fs.f.code[pc]
    offset = dest - (pc + 1)
    # lua_assert(dest != NO_JUMP)
    if dest == NO_JUMP:
        return
    if abs(offset) > MAXARG_sBx:
        raise RuntimeError("control structure too long")
    fs.f.code[pc] = (jmp & ~(0x3FFFF << 14)) | ((offset + MAXARG_sBx) << 14)


# =============================================================================
# lcode.c:119-126 - luaK_concat
# =============================================================================
def luaK_concat(fs: 'FuncState', l1_ref: list, l2: int) -> None:
    """
    lcode.c:119-126 - Concatenate jump lists
    
    void luaK_concat (FuncState *fs, int *l1, int l2)
    l1_ref is a list [l1] to allow modification
    """
    if l2 == NO_JUMP:
        return
    elif l1_ref[0] == NO_JUMP:
        l1_ref[0] = l2
    else:
        list_val = l1_ref[0]
        while True:
            next_val = getjump(fs, list_val)
            if next_val == NO_JUMP:
                break
            list_val = next_val
        fixjump(fs, list_val, l2)


# =============================================================================
# lcode.c:128-131 - luaK_jump
# =============================================================================
def luaK_jump(fs: 'FuncState') -> int:
    """
    lcode.c:128-131 - Create unconditional jump
    
    int luaK_jump (FuncState *fs)
    """
    jpc = fs.jpc
    fs.jpc = NO_JUMP
    j = luaK_codeAsBx(fs, OP_JMP, 0, NO_JUMP)
    luaK_concat(fs, [j], jpc)
    return j


# =============================================================================
# lcode.c:178-181 - luaK_getlabel
# =============================================================================
def luaK_getlabel(fs: 'FuncState') -> int:
    """
    lcode.c:178-181 - Get label (current position)
    
    int luaK_getlabel (FuncState *fs)
    """
    fs.lasttarget = fs.pc
    return fs.pc


# =============================================================================
# lcode.c:217-224 - luaK_patchlist
# =============================================================================
def luaK_patchlist(fs: 'FuncState', list_val: int, target: int) -> None:
    """
    lcode.c:217-224 - Patch jump list to target
    
    void luaK_patchlist (FuncState *fs, int list, int target)
    """
    if target == fs.pc:
        luaK_patchtohere(fs, list_val)
    else:
        # lua_assert(target < fs.pc)
        patchlistaux(fs, list_val, target, NO_REG, target)


def luaK_patchtohere(fs: 'FuncState', list_val: int) -> None:
    """
    lcode.c:227-230 - Patch jump list to current position
    
    void luaK_patchtohere (FuncState *fs, int list)
    """
    luaK_getlabel(fs)
    jpc_ref = [fs.jpc]
    luaK_concat(fs, jpc_ref, list_val)
    fs.jpc = jpc_ref[0]


# =============================================================================
# lcode.c:236-253 - Instruction Encoding
# =============================================================================
def luaK_codeABC(fs: 'FuncState', o: OpCode, a: int, b: int, c: int) -> int:
    """
    lcode.c:248-253 - Code ABC instruction
    
    int luaK_codeABC (FuncState *fs, OpCode o, int A, int B, int C)
    """
    # lua_assert(a <= MAXARG_A and b <= MAXARG_B and c <= MAXARG_C)
    return luaK_code(fs, CREATE_ABC(o, a, b, c))


def luaK_codeABx(fs: 'FuncState', o: OpCode, a: int, bx: int) -> int:
    """
    lcode.c:256-260 - Code ABx instruction
    
    int luaK_codeABx (FuncState *fs, OpCode o, int A, unsigned int Bx)
    """
    # lua_assert(a <= MAXARG_A and bx <= MAXARG_Bx)
    return luaK_code(fs, CREATE_ABx(o, a, bx))


def luaK_codeAsBx(fs: 'FuncState', o: OpCode, a: int, sbx: int) -> int:
    """lcode.h:46 - #define luaK_codeAsBx(fs,o,A,sBx) luaK_codeABx(fs,o,A,(sBx)+MAXARG_sBx)"""
    return luaK_codeABx(fs, o, a, sbx + MAXARG_sBx)


def luaK_code(fs: 'FuncState', i: Instruction) -> int:
    """
    lcode.c:236-246 - Emit instruction
    
    static int luaK_code (FuncState *fs, Instruction i)
    """
    f = fs.f
    # Discharge pending jumps
    dischargejpc(fs)
    # Extend code array if needed
    while len(f.code) <= fs.pc:
        f.code.append(0)
    f.code[fs.pc] = i
    # Save line info
    while len(f.lineinfo) <= fs.pc:
        f.lineinfo.append(0)
    f.lineinfo[fs.pc] = fs.ls.lastline if fs.ls else 0
    pc = fs.pc
    fs.pc += 1
    return pc


def dischargejpc(fs: 'FuncState') -> None:
    """
    lcode.c:183-189 - Discharge pending jumps
    
    static void dischargejpc (FuncState *fs)
    """
    patchlistaux(fs, fs.jpc, fs.pc, NO_REG, fs.pc)
    fs.jpc = NO_JUMP


# =============================================================================
# lcode.c:134-176 - Patch helpers (simplified)
# =============================================================================
NO_REG = MAXARG_A


# =============================================================================
# lcode.c:262-284 - luaK_checkstack, luaK_reserveregs
# =============================================================================
def luaK_checkstack(fs: 'FuncState', n: int) -> None:
    """
    lcode.c:262-268 - Check stack space
    
    void luaK_checkstack (FuncState *fs, int n)
    """
    newstack = fs.freereg + n
    if newstack > fs.f.maxstacksize:
        if newstack >= MAXREGS:
            raise RuntimeError(f"function or expression needs too many registers (limit is {MAXREGS})")
        fs.f.maxstacksize = newstack


def luaK_reserveregs(fs: 'FuncState', n: int) -> None:
    """
    lcode.c:271-275 - Reserve n registers
    
    void luaK_reserveregs (FuncState *fs, int n)
    """
    luaK_checkstack(fs, n)
    fs.freereg += n


# =============================================================================
# lcode.c:278-284 - freereg
# =============================================================================
def freereg(fs: 'FuncState', reg: int) -> None:
    """
    lcode.c:386-391 - Free register 'reg', if it is neither a constant index 
    nor a local variable.
    
    static void freereg (FuncState *fs, int reg)
    """
    if not ISK(reg) and reg >= fs.nactvar:
        fs.freereg -= 1
        # lua_assert(reg == fs.freereg)
        if reg != fs.freereg:
            # Adjust freereg to maintain consistency
            fs.freereg = reg


# =============================================================================
# lcode.c:458-462 - luaK_stringK
# =============================================================================
def luaK_stringK(fs: 'FuncState', s: TString) -> int:
    """
    lcode.c:458-462 - Add a string to list of constants and return its index.
    
    int luaK_stringK (FuncState *fs, TString *s) {
      TValue o;
      setsvalue(fs->ls->L, &o, s);
      return addk(fs, &o, &o);  /* use string itself as key */
    }
    """
    o = TValue()
    setsvalue(o, s)
    return addk(fs, o, o)  # use string itself as key


# =============================================================================
# lcode.c:471-476 - luaK_intK
# =============================================================================
def luaK_intK(fs: 'FuncState', n: lua_Integer) -> int:
    """
    lcode.c:471-476 - Add an integer to list of constants and return its index.
    Integers use userdata as keys to avoid collision with floats with
    same value; conversion to 'void*' is used only for hashing.
    
    int luaK_intK (FuncState *fs, lua_Integer n) {
      TValue k, o;
      setpvalue(&k, cast(void*, cast(size_t, n)));
      setivalue(&o, n);
      return addk(fs, &k, &o);
    }
    """
    k = TValue()
    o = TValue()
    # setpvalue - use integer as "pointer value" key to avoid float collision
    setpvalue(k, n)  # use integer as pointer value
    setivalue(o, n)
    return addk(fs, k, o)


# =============================================================================
# lcode.c:481-485 - luaK_numberK
# =============================================================================
def luaK_numberK(fs: 'FuncState', r: lua_Number) -> int:
    """
    lcode.c:481-485 - Add a float to list of constants and return its index.
    
    static int luaK_numberK (FuncState *fs, lua_Number r) {
      TValue o;
      setfltvalue(&o, r);
      return addk(fs, &o, &o);  /* use number itself as key */
    }
    """
    o = TValue()
    setfltvalue(o, r)
    return addk(fs, o, o)  # use number itself as key


# =============================================================================
# lcode.c:491-495 - boolK
# =============================================================================
def boolK(fs: 'FuncState', b: int) -> int:
    """
    lcode.c:491-495 - Add a boolean to list of constants and return its index.
    
    static int boolK (FuncState *fs, int b) {
      TValue o;
      setbvalue(&o, b);
      return addk(fs, &o, &o);  /* use boolean itself as key */
    }
    """
    o = TValue()
    setbvalue(o, b)
    return addk(fs, o, o)  # use boolean itself as key


# =============================================================================
# lcode.c:501-507 - nilK
# =============================================================================
def nilK(fs: 'FuncState') -> int:
    """
    lcode.c:501-507 - Add nil to list of constants and return its index.
    
    static int nilK (FuncState *fs) {
      TValue k, v;
      setnilvalue(&v);
      /* cannot use nil as key; instead use table itself to represent nil */
      sethvalue(fs->ls->L, &k, fs->ls->h);
      return addk(fs, &k, &v);
    }
    """
    k = TValue()
    v = TValue()
    setnilvalue(v)
    # cannot use nil as key; instead use table itself to represent nil
    # Use scanner table's unique identifier as key
    sethvalue(k, fs.ls)  # use ls object to represent scanner table
    return addk(fs, k, v)


# =============================================================================
# lcode.c:428-452 - addk
# =============================================================================
def addk(fs: 'FuncState', key: TValue, v: TValue) -> int:
    """
    lcode.c:428-452 - Add constant 'v' to prototype's list of constants.
    Use scanner's table to cache position of constants in constant list
    and try to reuse constants.
    
    static int addk (FuncState *fs, TValue *key, TValue *v) {
      lua_State *L = fs->ls->L;
      Proto *f = fs->f;
      TValue *idx = luaH_set(L, fs->ls->h, key);  /* index scanner table */
      int k, oldsize;
      if (ttisinteger(idx)) {  /* is there an index there? */
        k = cast_int(ivalue(idx));
        /* correct value? (warning: must distinguish floats from integers!) */
        if (k < fs->nk && ttype(&f->k[k]) == ttype(v) &&
                          luaV_rawequalobj(&f->k[k], v))
          return k;  /* reuse index */
      }
      /* constant not found; create a new entry */
      oldsize = f->sizek;
      k = fs->nk;
      setivalue(idx, k);
      luaM_growvector(...);
      while (oldsize < f->sizek) setnilvalue(&f->k[oldsize++]);
      setobj(L, &f->k[k], v);
      fs->nk++;
      return k;
    }
    """
    f = fs.f
    
    # Simulate luaH_set - find/set key in scanner table
    # Use ls._h_cache as scanner table
    if not hasattr(fs.ls, '_h_cache'):
        fs.ls._h_cache = {}
    
    h = fs.ls._h_cache
    
    # Create cache key based on TValue type
    cache_key = _tvalue_to_cache_key(key)
    
    # if (ttisinteger(idx)) - check if index exists in cache
    if cache_key in h:
        k = h[cache_key]
        # if (k < fs->nk && ttype(&f->k[k]) == ttype(v) && luaV_rawequalobj(&f->k[k], v))
        if k < fs.nk:
            existing = f.k[k]
            # type match && value match
            if _ttype_equal(existing, v) and _luaV_rawequalobj(existing, v):
                return k  # reuse index
    
    # constant not found; create a new entry
    k = fs.nk
    
    # setivalue(idx, k) - update cache
    h[cache_key] = k
    
    # Expand constant table
    while len(f.k) <= k:
        f.k.append(None)
    
    # setobj - set constant value
    f.k[k] = v
    fs.nk += 1
    
    return k


def _tvalue_to_cache_key(tv: TValue):
    """
    Convert TValue to cache key.
    Based on C code handling of different types:
    - string: use string content
    - integer pointer value (lightuserdata): use ('pvalue', n)
    - float: use ('number', n)
    - boolean: use ('boolean', b)
    - table (for nil): use ('table', id)
    
    Note: type tag may have BIT_ISCOLLECTABLE (64)
    Need to use tt & 0x3F to get base type
    """
    if not isinstance(tv, TValue):
        # Compatible with old call style
        if isinstance(tv, TString):
            return ('string', tv.data)
        elif isinstance(tv, int) and not isinstance(tv, bool):
            return ('pvalue', tv)  # integer as pointer value
        elif isinstance(tv, float):
            return ('number', tv)
        elif isinstance(tv, bool):
            return ('boolean', tv)
        else:
            return ('other', id(tv))
    
    if hasattr(tv, 'tt_'):
        tt = tv.tt_
        # Remove BIT_ISCOLLECTABLE flag to get base type
        base_tt = tt & 0x3F  # remove collectable bit (bit 6)
        variant_tt = tt & 0x0F  # only look at lower 4 bits for base type
        
        # LUA_TSTRING = 4 (may have collectable flag)
        if variant_tt == 4 and hasattr(tv, 'value_') and hasattr(tv.value_, 'gc'):
            gc = tv.value_.gc
            if hasattr(gc, 'data'):
                return ('string', gc.data)
        # LUA_TNUMINT = 19 (LUA_TNUMBER=3 | (1 << 4)=16)
        elif base_tt == 19 and hasattr(tv, 'value_') and hasattr(tv.value_, 'i'):
            return ('integer', tv.value_.i)
        # LUA_TNUMFLT = 3 (LUA_TNUMBER | (0 << 4))
        elif base_tt == 3 and hasattr(tv, 'value_') and hasattr(tv.value_, 'n'):
            return ('number', tv.value_.n)
        # LUA_TBOOLEAN = 1
        elif variant_tt == 1 and hasattr(tv, 'value_') and hasattr(tv.value_, 'b'):
            return ('boolean', tv.value_.b)
        # LUA_TLIGHTUSERDATA = 2 (for integer pointer value key)
        elif variant_tt == 2 and hasattr(tv, 'value_') and hasattr(tv.value_, 'p'):
            return ('pvalue', tv.value_.p)
        # LUA_TTABLE = 5 (for nil key, may have collectable flag)
        elif variant_tt == 5 and hasattr(tv, 'value_') and hasattr(tv.value_, 'gc'):
            return ('table', id(tv.value_.gc))
    
    # Fallback to value_ based detection
    if hasattr(tv, 'value_'):
        val = tv.value_
        if hasattr(val, 'gc') and hasattr(val.gc, 'data'):
            return ('string', val.gc.data)
        elif hasattr(val, 'i'):
            return ('integer', val.i)
        elif hasattr(val, 'n'):
            return ('number', val.n)
        elif hasattr(val, 'b'):
            return ('boolean', val.b)
        elif hasattr(val, 'p'):
            return ('pvalue', val.p)
    
    return ('other', id(tv))


def _ttype_equal(a: TValue, b: TValue) -> bool:
    """
    Check if two TValue have the same type.
    Corresponds to C: ttype(&f->k[k]) == ttype(v)
    
    lobject.h:133 - #define ttype(o) (rttype(o) & 0x3F)
    ttype removes BIT_ISCOLLECTABLE (bit 6) before comparison
    """
    if a is None or b is None:
        return a is b
    
    # Get type tags
    tt_a = getattr(a, 'tt_', -1)
    tt_b = getattr(b, 'tt_', -1)
    
    if tt_a >= 0 and tt_b >= 0:
        # ttype(o) = rttype(o) & 0x3F - remove collectable bit
        return (tt_a & 0x3F) == (tt_b & 0x3F)
    
    # Fallback to value-based type detection
    def get_type(tv):
        if hasattr(tv, 'value_'):
            val = tv.value_
            if hasattr(val, 'gc') and hasattr(val.gc, 'data'):
                return 'string'
            elif hasattr(val, 'i'):
                return 'integer'
            elif hasattr(val, 'n'):
                return 'number'
            elif hasattr(val, 'b'):
                return 'boolean'
            elif hasattr(val, 'p'):
                return 'pvalue'
        return 'unknown'
    
    return get_type(a) == get_type(b)


def _luaV_rawequalobj(a: TValue, b: TValue) -> bool:
    """
    Compare two TValue for equality (raw comparison, no metamethods).
    Corresponds to C: luaV_rawequalobj(&f->k[k], v)
    """
    if a is None or b is None:
        return a is b
    
    # First check type
    if not _ttype_equal(a, b):
        return False
    
    # Compare values
    if hasattr(a, 'value_') and hasattr(b, 'value_'):
        av, bv = a.value_, b.value_
        # String comparison
        if hasattr(av, 'gc') and hasattr(bv, 'gc'):
            if hasattr(av.gc, 'data') and hasattr(bv.gc, 'data'):
                return av.gc.data == bv.gc.data
        # Integer comparison
        if hasattr(av, 'i') and hasattr(bv, 'i'):
            return av.i == bv.i
        # Float comparison
        if hasattr(av, 'n') and hasattr(bv, 'n'):
            return av.n == bv.n
        # Boolean comparison
        if hasattr(av, 'b') and hasattr(bv, 'b'):
            return av.b == bv.b
        # Pointer value comparison
        if hasattr(av, 'p') and hasattr(bv, 'p'):
            return av.p == bv.p
    
    return False


# =============================================================================
# TValue Helper Functions
# =============================================================================
def setsvalue(o: TValue, s: TString) -> None:
    """
    lobject.h:225-228 - setsvalue set string value
    
    #define setsvalue(L,obj,x) \
      { TValue *io = (obj); TString *x_ = (x); \
        val_(io).gc = obj2gco(x_); settt_(io, ctb(x_->tt)); \
        checkliveness(L,io); }
    """
    if not hasattr(o, 'value_'):
        o.value_ = type('Value', (), {})()
    o.value_.gc = s
    # Use ctb(s.tt) - string is GC object, needs BIT_ISCOLLECTABLE
    # s.tt should be LUA_TSHRSTR (4) or LUA_TLNGSTR (20)
    tt = getattr(s, 'tt', 4)  # default short string
    o.tt_ = tt | 64  # ctb(tt) = tt | BIT_ISCOLLECTABLE


def setpvalue(o: TValue, p) -> None:
    """Set lightuserdata value (used for integer key)"""
    if not hasattr(o, 'value_'):
        o.value_ = type('Value', (), {})()
    o.value_.p = p
    o.tt_ = 2  # LUA_TLIGHTUSERDATA


def sethvalue(o: TValue, h) -> None:
    """Set table value (used for nil key)"""
    if not hasattr(o, 'value_'):
        o.value_ = type('Value', (), {})()
    o.value_.gc = h
    o.tt_ = 5  # LUA_TTABLE


# =============================================================================
# lcode.c:366-454 - Expression discharge (simplified stubs)
# =============================================================================
def luaK_dischargevars(fs: 'FuncState', e: 'expdesc') -> None:
    """lcode.c:366-390 - Discharge variables to registers"""
    from .lparser import VLOCAL, VUPVAL, VINDEXED, VCALL, VVARARG, VNONRELOC, VRELOCABLE
    
    if e.k == VLOCAL:
        e.k = VNONRELOC
    elif e.k == VUPVAL:
        e.info = luaK_codeABC(fs, OP_GETUPVAL, 0, e.info, 0)
        e.k = VRELOCABLE
    elif e.k == VINDEXED:
        # lcode.c:567-580 - Handle indexed variable
        freereg(fs, e.ind.idx)  # free idx register first
        if e.ind.vt == VLOCAL:  # 't' is in a register?
            freereg(fs, e.ind.t)  # free t register
            op = OP_GETTABLE
        else:
            # lua_assert(e.ind.vt == VUPVAL)
            op = OP_GETTABUP  # 't' is in an upvalue
        e.info = luaK_codeABC(fs, op, 0, e.ind.t, e.ind.idx)
        e.k = VRELOCABLE
    elif e.k == VCALL or e.k == VVARARG:
        luaK_setoneret(fs, e)


def luaK_exp2nextreg(fs: 'FuncState', e: 'expdesc') -> None:
    """lcode.c:494-500 - Put expression in next register"""
    luaK_dischargevars(fs, e)
    freeexp(fs, e)
    luaK_reserveregs(fs, 1)
    exp2reg(fs, e, fs.freereg - 1)


def luaK_exp2anyreg(fs: 'FuncState', e: 'expdesc') -> int:
    """lcode.c:503-514 - Put expression in any register"""
    from .lparser import VNONRELOC
    
    luaK_dischargevars(fs, e)
    if e.k == VNONRELOC:
        if not hasjumps(e):
            return e.info
        if e.info >= fs.nactvar:
            exp2reg(fs, e, e.info)
            return e.info
    luaK_exp2nextreg(fs, e)
    return e.info


def luaK_setoneret(fs: 'FuncState', e: 'expdesc') -> None:
    """lcode.c:463-473 - Set expression for single return"""
    from .lparser import VCALL, VVARARG, VNONRELOC, VRELOCABLE
    
    if e.k == VCALL:
        e.k = VNONRELOC
        e.info = GETARG_A(getinstruction(fs, e))
    elif e.k == VVARARG:
        inst = getinstruction(fs, e)
        fs.f.code[e.info] = (inst & ~(0xFF << 23)) | (2 << 23)  # SETARG_B(inst, 2)
        e.k = VRELOCABLE


def luaK_setreturns(fs: 'FuncState', e: 'expdesc', nresults: int) -> None:
    """lcode.c:476-490 - Set returns for call or vararg"""
    from .lparser import VCALL, VVARARG
    
    if e.k == VCALL:
        inst = getinstruction(fs, e)
        fs.f.code[e.info] = (inst & ~(0xFF << 14)) | ((nresults + 1) << 14)  # SETARG_C
    elif e.k == VVARARG:
        inst = getinstruction(fs, e)
        fs.f.code[e.info] = (inst & ~(0xFF << 23)) | ((nresults + 1) << 23)  # SETARG_B
        fs.f.code[e.info] = (fs.f.code[e.info] & ~(0xFF << 6)) | (fs.freereg << 6)  # SETARG_A
        luaK_reserveregs(fs, 1)


def luaK_setmultret(fs: 'FuncState', e: 'expdesc') -> None:
    """lcode.h:48 - #define luaK_setmultret(fs,e) luaK_setreturns(fs, e, LUA_MULTRET)"""
    from .lua import LUA_MULTRET
    luaK_setreturns(fs, e, LUA_MULTRET)


def getjumpcontrol(fs: 'FuncState', pc: int) -> int:
    """lcode.c:179-185 - Get jump control instruction
    
    Returns the position of the instruction "controlling" a given
    jump (that is, its condition), or the jump itself if it is
    unconditional.
    """
    if pc >= 1:
        prev_inst = fs.f.code[pc - 1]
        op = prev_inst & 0x3F
        # testTMode: check if instruction is a test (EQ, LT, LE, TEST, TESTSET)
        if op in (OP_EQ.value, OP_LT.value, OP_LE.value, 
                  OP_TEST.value, OP_TESTSET.value):
            return pc - 1
    return pc


def patchtestreg(fs: 'FuncState', node: int, reg: int) -> bool:
    """lcode.c:195-207 - Patch destination register for a TESTSET instruction"""
    ctrl_pc = getjumpcontrol(fs, node)
    i = fs.f.code[ctrl_pc]
    op = i & 0x3F
    
    if op != OP_TESTSET.value:
        return False  # cannot patch other instructions
    
    # GETARG_B: bits 23-31, GETARG_C: bits 14-22
    b = (i >> 23) & 0x1FF  # GETARG_B
    c = (i >> 14) & 0x1FF  # GETARG_C
    
    if reg != NO_REG and reg != b:
        # SETARG_A
        fs.f.code[ctrl_pc] = (i & ~(0xFF << 6)) | (reg << 6)
    else:
        # change instruction to simple test
        # CREATE_ABC(OP_TEST, GETARG_B(*i), 0, GETARG_C(*i))
        # A=GETARG_B, B=0, C=GETARG_C
        # Layout: op(6) | A(8) | C(9) | B(9)
        fs.f.code[ctrl_pc] = (OP_TEST.value) | (b << 6) | (c << 14) | (0 << 23)
    
    return True


def need_value(fs: 'FuncState', list: int) -> bool:
    """lcode.c:659-665 - Check whether list has any jump that do not produce a value"""
    while list != NO_JUMP:
        ctrl_pc = getjumpcontrol(fs, list)
        i = fs.f.code[ctrl_pc]
        op = i & 0x3F
        if op != OP_TESTSET.value:
            return True
        list = getjump(fs, list)
    return False


def code_loadbool(fs: 'FuncState', A: int, b: int, jump: int) -> int:
    """lcode.c:649-652 - Code LOADBOOL instruction"""
    luaK_getlabel(fs)  # those instructions may be jump targets
    return luaK_codeABC(fs, OP_LOADBOOL, A, b, jump)


def patchlistaux(fs: 'FuncState', list: int, vtarget: int, reg: int, dtarget: int) -> None:
    """lcode.c:224-234 - Traverse a list of tests, patching their destination"""
    while list != NO_JUMP:
        next_jump = getjump(fs, list)
        if patchtestreg(fs, list, reg):
            fixjump(fs, list, vtarget)
        else:
            fixjump(fs, list, dtarget)  # jump to default target
        list = next_jump


def exp2reg(fs: 'FuncState', e: 'expdesc', reg: int) -> None:
    """lcode.c:675-696 - Put expression result in register
    
    Ensures final expression result (including results from its jump
    lists) is in register 'reg'.
    """
    from .lparser import VNONRELOC
    
    discharge2reg(fs, e, reg)
    
    if e.k == VJMP:
        # expression itself is a test? put this jump in 't' list
        e_t_ref = [e.t]
        luaK_concat(fs, e_t_ref, e.info)
        e.t = e_t_ref[0]
    
    if hasjumps(e):
        final = NO_JUMP  # position after whole expression
        p_f = NO_JUMP    # position of an eventual LOAD false
        p_t = NO_JUMP    # position of an eventual LOAD true
        
        if need_value(fs, e.t) or need_value(fs, e.f):
            fj = NO_JUMP if e.k == VJMP else luaK_jump(fs)
            p_f = code_loadbool(fs, reg, 0, 1)
            p_t = code_loadbool(fs, reg, 1, 0)
            luaK_patchtohere(fs, fj)
        
        final = luaK_getlabel(fs)
        patchlistaux(fs, e.f, final, reg, p_f)
        patchlistaux(fs, e.t, final, reg, p_t)
    
    e.f = NO_JUMP
    e.t = NO_JUMP
    e.info = reg
    e.k = VNONRELOC


def discharge2reg(fs: 'FuncState', e: 'expdesc', reg: int) -> None:
    """lcode.c:420-453 - Discharge expression to register"""
    from .lparser import (VNIL, VTRUE, VFALSE, VK, VKFLT, VKINT,
                          VRELOCABLE, VNONRELOC, VJMP)
    
    luaK_dischargevars(fs, e)
    
    if e.k == VNIL:
        luaK_nil(fs, reg, 1)
    elif e.k == VFALSE or e.k == VTRUE:
        luaK_codeABC(fs, OP_LOADBOOL, reg, 1 if e.k == VTRUE else 0, 0)
    elif e.k == VK:
        luaK_codek(fs, reg, e.info)
    elif e.k == VKFLT:
        luaK_codek(fs, reg, luaK_numberK(fs, e.nval))
    elif e.k == VKINT:
        luaK_codek(fs, reg, luaK_intK(fs, e.ival))
    elif e.k == VRELOCABLE:
        inst = getinstruction(fs, e)
        fs.f.code[e.info] = (inst & ~(0xFF << 6)) | (reg << 6)  # SETARG_A
    elif e.k == VNONRELOC:
        if reg != e.info:
            luaK_codeABC(fs, OP_MOVE, reg, e.info, 0)
    else:
        # lua_assert(e.k == VJMP)
        return
    
    e.info = reg
    e.k = VNONRELOC


def luaK_codek(fs: 'FuncState', reg: int, k: int) -> int:
    """lcode.c:352-362 - Code constant load"""
    if k <= MAXARG_Bx:
        return luaK_codeABx(fs, OP_LOADK, reg, k)
    else:
        p = luaK_codeABx(fs, OP_LOADKX, reg, 0)
        luaK_code(fs, CREATE_Ax(OP_EXTRAARG, k))
        return p


def freeexp(fs: 'FuncState', e: 'expdesc') -> None:
    """lcode.c:287-290 - Free expression register"""
    from .lparser import VNONRELOC
    
    if e.k == VNONRELOC:
        freereg(fs, e.info)


# =============================================================================
# lcode.c - Stub for indexed
# =============================================================================
def luaK_indexed(fs: 'FuncState', t: 'expdesc', k: 'expdesc') -> None:
    """lcode.c:724-751 - Generate code for indexed expression"""
    from .lparser import VINDEXED, VUPVAL, VLOCAL
    
    # lua_assert(not hasjumps(t))
    t.ind.t = t.info
    t.ind.idx = luaK_exp2RK(fs, k)
    t.ind.vt = VUPVAL if t.k == VUPVAL else VLOCAL
    t.k = VINDEXED


def luaK_exp2RK(fs: 'FuncState', e: 'expdesc') -> int:
    """lcode.c:559-585 - Convert expression to R/K"""
    from .lparser import VTRUE, VFALSE, VNIL, VKINT, VKFLT, VK
    
    luaK_exp2val(fs, e)
    
    if e.k == VTRUE or e.k == VFALSE or e.k == VNIL:
        if fs.nk <= MAXARG_Bx:
            if e.k == VNIL:
                e.info = nilK(fs)
            else:
                e.info = boolK(fs, 1 if e.k == VTRUE else 0)
            e.k = VK
            return RKASK(e.info)
    elif e.k == VKINT:
        e.info = luaK_intK(fs, e.ival)
        e.k = VK
        if e.info <= MAXARG_Bx:
            return RKASK(e.info)
    elif e.k == VKFLT:
        e.info = luaK_numberK(fs, e.nval)
        e.k = VK
        if e.info <= MAXARG_Bx:
            return RKASK(e.info)
    elif e.k == VK:
        if e.info <= MAXARG_Bx:
            return RKASK(e.info)
    
    return luaK_exp2anyreg(fs, e)


def luaK_exp2val(fs: 'FuncState', e: 'expdesc') -> None:
    """lcode.c:517-521 - Convert to value"""
    if hasjumps(e):
        luaK_exp2anyreg(fs, e)
    else:
        luaK_dischargevars(fs, e)


# Placeholder for VJMP
VJMP = 11  # From lparser.py


# =============================================================================
# Additional code generation functions
# =============================================================================
def luaK_exp2anyregup(fs: 'FuncState', e: 'expdesc') -> None:
    """lcode.c:523-527 - Put expression in any register or upvalue"""
    from .lparser import VUPVAL
    if e.k != VUPVAL or hasjumps(e):
        luaK_exp2anyreg(fs, e)


def luaK_self(fs: 'FuncState', e: 'expdesc', key: 'expdesc') -> None:
    """lcode.c:754-762 - Self expression (method call)"""
    luaK_exp2anyreg(fs, e)
    freeexp(fs, e)
    func = fs.freereg
    luaK_reserveregs(fs, 2)
    luaK_codeABC(fs, OP_SELF, func, e.info, luaK_exp2RK(fs, key))
    freeexp(fs, key)
    e.info = func
    from .lparser import VNONRELOC
    e.k = VNONRELOC


def luaK_goiftrue(fs: 'FuncState', e: 'expdesc') -> None:
    """lcode.c:840-860 - Generate code to jump if true"""
    from .lparser import VJMP, VNIL, VFALSE, VK, VKFLT, VKINT, VTRUE
    luaK_dischargevars(fs, e)
    pc = NO_JUMP
    if e.k == VJMP:
        invertjump(fs, e)
        pc = e.info
    elif e.k in (VK, VKFLT, VKINT, VTRUE):
        pc = NO_JUMP  # Always true, do nothing
    else:
        pc = jumponcond(fs, e, 0)
    e_f_ref = [e.f]
    luaK_concat(fs, e_f_ref, pc)
    e.f = e_f_ref[0]
    luaK_patchtohere(fs, e.t)
    e.t = NO_JUMP


def luaK_goiffalse(fs: 'FuncState', e: 'expdesc') -> None:
    """lcode.c:863-883 - Generate code to jump if false"""
    from .lparser import VJMP, VNIL, VFALSE
    luaK_dischargevars(fs, e)
    pc = NO_JUMP
    if e.k == VJMP:
        pc = e.info
    elif e.k in (VNIL, VFALSE):
        pc = NO_JUMP  # Always false
    else:
        pc = jumponcond(fs, e, 1)
    e_t_ref = [e.t]
    luaK_concat(fs, e_t_ref, pc)
    e.t = e_t_ref[0]
    luaK_patchtohere(fs, e.f)
    e.f = NO_JUMP


def invertjump(fs: 'FuncState', e: 'expdesc') -> None:
    """lcode.c:796-805 - Invert jump condition"""
    pc = getjumpcontrol(fs, e.info)
    inst = fs.f.code[pc]
    fs.f.code[pc] = (inst & ~(1 << 6)) | ((1 - GETARG_A(inst)) << 6)


def jumponcond(fs: 'FuncState', e: 'expdesc', cond: int) -> int:
    """lcode.c:809-825 - Jump on condition"""
    from .lparser import VRELOCABLE
    if e.k == VRELOCABLE:
        ie = getinstruction(fs, e)
        if GET_OPCODE(ie) == OP_NOT:
            fs.pc -= 1
            return condjump(fs, OP_TEST, GETARG_B(ie), 0, 1 - cond)
    discharge2anyreg(fs, e)
    freeexp(fs, e)
    return condjump(fs, OP_TESTSET, NO_REG, e.info, cond)


def condjump(fs: 'FuncState', op: OpCode, a: int, b: int, c: int) -> int:
    """lcode.c:... - Conditional jump"""
    luaK_codeABC(fs, op, a, b, c)
    return luaK_jump(fs)


def discharge2anyreg(fs: 'FuncState', e: 'expdesc') -> None:
    """lcode.c:397-402 - Discharge to any register"""
    from .lparser import VNONRELOC
    if e.k != VNONRELOC:
        luaK_reserveregs(fs, 1)
        discharge2reg(fs, e, fs.freereg - 1)


def luaK_storevar(fs: 'FuncState', var: 'expdesc', ex: 'expdesc') -> None:
    """lcode.c:889-914 - Store expression in variable"""
    from .lparser import VLOCAL, VUPVAL, VINDEXED
    if var.k == VLOCAL:
        freeexp(fs, ex)
        exp2reg(fs, ex, var.info)
        return
    elif var.k == VUPVAL:
        e = luaK_exp2anyreg(fs, ex)
        luaK_codeABC(fs, OP_SETUPVAL, e, var.info, 0)
    elif var.k == VINDEXED:
        op = OP_SETTABLE if var.ind.vt == VLOCAL else OP_SETTABUP
        e = luaK_exp2RK(fs, ex)
        luaK_codeABC(fs, op, var.ind.t, var.ind.idx, e)
    freeexp(fs, ex)


def luaK_prefix(fs: 'FuncState', op: UnOpr, e: 'expdesc', line: int) -> None:
    """lcode.c:1066-1079 - Prefix operator"""
    from .lparser import VKINT, VKFLT
    
    # LUA_OPUNM = 12, LUA_OPBNOT = 13
    LUA_OPUNM = 12
    
    e2 = expdesc_new()
    e2.t = NO_JUMP
    e2.f = NO_JUMP
    e2.k = VKINT
    e2.ival = 0
    
    if op == OPR_MINUS:
        # op + LUA_OPUNM = 0 + 12 = 12
        if constfolding(fs, op + LUA_OPUNM, e, e2):
            return
        # Fall through to code
    elif op == OPR_BNOT:
        # op + LUA_OPUNM = 1 + 12 = 13
        if constfolding(fs, op + LUA_OPUNM, e, e2):
            return
    elif op == OPR_NOT:
        codenot(fs, e)
        return
    elif op == OPR_LEN:
        pass  # Fall through
    
    luaK_exp2anyreg(fs, e)
    freeexp(fs, e)
    from .lparser import VRELOCABLE
    e.info = luaK_codeABC(fs, OP_UNM + op, 0, e.info, 0)
    e.k = VRELOCABLE


def luaK_infix(fs: 'FuncState', op: BinOpr, v: 'expdesc') -> None:
    """lcode.c:939-965 - Binary operator (left operand)"""
    if op == OPR_AND:
        luaK_goiftrue(fs, v)
    elif op == OPR_OR:
        luaK_goiffalse(fs, v)
    elif op == OPR_CONCAT:
        luaK_exp2nextreg(fs, v)
    elif op in (OPR_ADD, OPR_SUB, OPR_MUL, OPR_DIV, OPR_IDIV,
                OPR_MOD, OPR_POW, OPR_BAND, OPR_BOR, OPR_BXOR,
                OPR_SHL, OPR_SHR):
        if not tonumeral(v, None):
            luaK_exp2RK(fs, v)
    else:
        luaK_exp2RK(fs, v)


def luaK_posfix(fs: 'FuncState', op: BinOpr, e1: 'expdesc', 
                e2: 'expdesc', line: int) -> None:
    """lcode.c:968-1034 - Binary operator (right operand)"""
    from .lparser import VNONRELOC
    if op == OPR_AND:
        # lua_assert(e1.t == NO_JUMP)
        luaK_dischargevars(fs, e2)
        e1_f_ref = [e1.f]
        luaK_concat(fs, e1_f_ref, e2.f)
        e1.f = e1_f_ref[0]
        e1.k = e2.k
        e1.info = e2.info
        e1.nval = e2.nval
        e1.ival = e2.ival
        e1.t = e2.t
    elif op == OPR_OR:
        # lua_assert(e1.f == NO_JUMP)
        luaK_dischargevars(fs, e2)
        e1_t_ref = [e1.t]
        luaK_concat(fs, e1_t_ref, e2.t)
        e1.t = e1_t_ref[0]
        e1.k = e2.k
        e1.info = e2.info
        e1.nval = e2.nval
        e1.ival = e2.ival
        e1.f = e2.f
    elif op == OPR_CONCAT:
        luaK_exp2val(fs, e2)
        if e2.k == VRELOCABLE and GET_OPCODE(getinstruction(fs, e2)) == OP_CONCAT:
            # lua_assert(e1.info == GETARG_B(getinstruction(fs, e2)) - 1)
            freeexp(fs, e1)
            inst = getinstruction(fs, e2)
            fs.f.code[e2.info] = (inst & ~(0xFF << 23)) | (e1.info << 23)
            e1.k = VRELOCABLE
            e1.info = e2.info
        else:
            luaK_exp2nextreg(fs, e2)
            codebinexpval(fs, OP_CONCAT, e1, e2, line)
    elif op in (OPR_ADD, OPR_SUB, OPR_MUL, OPR_DIV, OPR_IDIV,
                OPR_MOD, OPR_POW, OPR_BAND, OPR_BOR, OPR_BXOR,
                OPR_SHL, OPR_SHR):
        # Try constant folding
        # op starts from OPR_ADD, corresponds to LUA_OPADD=0
        lua_op = op - OPR_ADD
        if not constfolding(fs, lua_op, e1, e2):
            codebinexpval(fs, OP_ADD + (op - OPR_ADD), e1, e2, line)
    elif op in (OPR_EQ, OPR_LT, OPR_LE, OPR_NE, OPR_GT, OPR_GE):
        codecomp(fs, op, e1, e2)
    

def codebinexpval(fs: 'FuncState', op: OpCode, e1: 'expdesc', 
                  e2: 'expdesc', line: int) -> None:
    """lcode.c:... - Code binary expression"""
    rk1 = luaK_exp2RK(fs, e1)
    rk2 = luaK_exp2RK(fs, e2)
    freeexps(fs, e1, e2)
    from .lparser import VRELOCABLE
    e1.info = luaK_codeABC(fs, op, 0, rk1, rk2)
    e1.k = VRELOCABLE
    luaK_fixline(fs, line)


def codecomp(fs: 'FuncState', opr: BinOpr, e1: 'expdesc', e2: 'expdesc') -> None:
    """lcode.c:1037-1060 - Emit code for comparisons
    
    static void codecomp (FuncState *fs, BinOpr opr, expdesc *e1, expdesc *e2)
    
    e1 was already put in R/K form by luaK_infix.
    """
    from .lparser import VJMP, VK, VNONRELOC
    
    # C: int rk1 = (e1->k == VK) ? RKASK(e1->u.info) : e1->u.info;
    if e1.k == VK:
        rk1 = RKASK(e1.info)
    else:
        # lua_assert(e1->k == VNONRELOC)
        rk1 = e1.info
    
    rk2 = luaK_exp2RK(fs, e2)
    freeexps(fs, e1, e2)
    
    if opr == OPR_NE:
        # '(a ~= b)' ==> 'not (a == b)'
        e1.info = condjump(fs, OP_EQ, 0, rk1, rk2)
    elif opr == OPR_GT or opr == OPR_GE:
        # '(a > b)' ==> '(b < a)';  '(a >= b)' ==> '(b <= a)'
        op = (opr - OPR_NE) + OP_EQ
        e1.info = condjump(fs, op, 1, rk2, rk1)  # invert operands
    else:
        # '==', '<', '<=' use their own opcodes
        op = (opr - OPR_EQ) + OP_EQ
        e1.info = condjump(fs, op, 1, rk1, rk2)
    
    e1.k = VJMP


def freeexps(fs: 'FuncState', e1: 'expdesc', e2: 'expdesc') -> None:
    """lcode.c:407-418 - Free registers used by expressions 'e1' and 'e2' 
    (if any) in proper order.
    """
    from .lparser import VNONRELOC
    if e1.k == VNONRELOC and e2.k == VNONRELOC:
        if e1.info > e2.info:
            freereg(fs, e1.info)
            freereg(fs, e2.info)
        else:
            freereg(fs, e2.info)
            freereg(fs, e1.info)
    else:
        if e2.k == VNONRELOC:
            freereg(fs, e2.info)
        if e1.k == VNONRELOC:
            freereg(fs, e1.info)


def removevalues(fs: 'FuncState', list: int) -> None:
    """
    lcode.c:213-216 - Traverse a list of tests ensuring no one produces a value
    
    static void removevalues (FuncState *fs, int list) {
      for (; list != NO_JUMP; list = getjump(fs, list))
          patchtestreg(fs, list, NO_REG);
    }
    """
    while list != NO_JUMP:
        next_list = getjump(fs, list)
        patchtestreg(fs, list, NO_REG)
        list = next_list


def codenot(fs: 'FuncState', e: 'expdesc') -> None:
    """
    lcode.c:910-939 - Code 'not e', doing constant folding.
    """
    from .lparser import VNIL, VFALSE, VK, VKFLT, VKINT, VTRUE, VJMP, VRELOCABLE
    luaK_dischargevars(fs, e)
    if e.k in (VNIL, VFALSE):
        e.k = VTRUE  # true == not nil == not false
    elif e.k in (VK, VKFLT, VKINT, VTRUE):
        e.k = VFALSE  # false == not "x" == not 0.5 == not 1 == not true
    elif e.k == VJMP:
        invertjump(fs, e)
    elif e.k == VRELOCABLE or e.k == VNONRELOC:
        discharge2anyreg(fs, e)
        freeexp(fs, e)
        e.info = luaK_codeABC(fs, OP_NOT, 0, e.info, 0)
        e.k = VRELOCABLE
    # interchange true and false lists
    e.f, e.t = e.t, e.f
    # values are useless when negated
    removevalues(fs, e.f)
    removevalues(fs, e.t)


def _luaV_shiftl(x: int, y: int) -> int:
    """
    lvm.c:593-601 - Lua shift operation
    
    lua_Integer luaV_shiftl (lua_Integer x, lua_Integer y) {
      if (y < 0) {  /* shift right? */
        if (y <= -NBITS) return 0;
        else return intop(>>, x, -y);
      }
      else {
        if (y >= NBITS) return 0;
        else return intop(<<, x, y);
      }
    }
    
    NBITS = 64 (64-bit integer)
    """
    NBITS = 64
    if y < 0:  # shift right?
        if y <= -NBITS:
            return 0
        else:
            return x >> (-y)
    else:
        if y >= NBITS:
            return 0
        else:
            return x << y


def _tonumeral_for_fold(e: 'expdesc') -> tuple:
    """Convert expression to numeral for constant folding
    
    Returns (success, value, is_integer)
    """
    from .lparser import VKINT, VKFLT
    
    if e.k == VKINT:
        return (True, e.ival, True)
    elif e.k == VKFLT:
        return (True, e.nval, False)
    return (False, 0, False)


def constfolding(fs: 'FuncState', op: int, e1: 'expdesc', e2: 'expdesc') -> bool:
    """lcode.c:978-996 - Constant folding
    
    Try to "constant-fold" an operation; return True if successful.
    """
    from .lparser import VKINT, VKFLT
    
    # Check if both operands are numeric constants
    ok1, v1, is_int1 = _tonumeral_for_fold(e1)
    ok2, v2, is_int2 = _tonumeral_for_fold(e2)
    
    if not ok1 or not ok2:
        return False
    
    # Perform operation
    # Reference: lobject.c:123-160 - luaO_arith
    # Key: LUA_OPDIV and LUA_OPPOW always return float!
    try:
        import math
        
        # op corresponds to Lua arithmetic opcode
        # LUA_OPADD=0, LUA_OPSUB=1, LUA_OPMUL=2, LUA_OPMOD=3, 
        # LUA_OPPOW=4, LUA_OPDIV=5, LUA_OPIDIV=6, LUA_OPBAND=7,
        # LUA_OPBOR=8, LUA_OPBXOR=9, LUA_OPSHL=10, LUA_OPSHR=11, LUA_OPUNM=12
        
        # Bitwise operations: only on integers
        if op in (7, 8, 9, 10, 11, 13):  # BAND, BOR, BXOR, SHL, SHR, BNOT
            if op == 7:  # BAND
                res = int(v1) & int(v2)
            elif op == 8:  # BOR
                res = int(v1) | int(v2)
            elif op == 9:  # BXOR
                res = int(v1) ^ int(v2)
            elif op == 10:  # SHL - use luaV_shiftl semantics
                res = _luaV_shiftl(int(v1), int(v2))
            elif op == 11:  # SHR - luaV_shiftl(v1, -v2)
                res = _luaV_shiftl(int(v1), -int(v2))
            elif op == 13:  # BNOT (unary)
                res = ~int(v1)
            # Bitwise result is always integer
            e1.k = VKINT
            e1.ival = int(res)
            return True
        
        # DIV and POW: always return float (lobject.c:136-142)
        elif op == 4:  # POW - operate only on floats
            res = float(v1) ** float(v2)
            if math.isnan(res) or res == 0:
                return False
            e1.k = VKFLT
            e1.nval = res
            return True
        elif op == 5:  # DIV - operate only on floats
            if v2 == 0:
                return False
            res = float(v1) / float(v2)
            if math.isnan(res) or res == 0:
                return False
            e1.k = VKFLT
            e1.nval = res
            return True
        
        # Other operations: if both operands are integers, result is integer; otherwise float
        else:
            if op == 0:  # ADD
                res = v1 + v2
            elif op == 1:  # SUB
                res = v1 - v2
            elif op == 2:  # MUL
                res = v1 * v2
            elif op == 3:  # MOD
                if v2 == 0:
                    return False
                res = v1 % v2
            elif op == 6:  # IDIV
                if v2 == 0:
                    return False
                res = v1 // v2
            elif op == 12:  # UNM (unary minus)
                res = -v1
            else:
                return False
            
            # lobject.c:144-155 - check result type
            # if both operands are integers, result is integer
            if is_int1 and is_int2:
                e1.k = VKINT
                e1.ival = int(res)
            else:
                # float result
                if math.isnan(res) or res == 0:
                    return False
                e1.k = VKFLT
                e1.nval = float(res)
            return True
        
    except (ZeroDivisionError, OverflowError, ValueError):
        return False


def luaK_jumpto(fs: 'FuncState', t: int) -> None:
    """lcode.h:50 - Jump to target"""
    luaK_patchlist(fs, luaK_jump(fs), t)


def luaK_fixline(fs: 'FuncState', line: int) -> None:
    """lcode.c:... - Fix line info"""
    if fs.pc > 0:
        fs.f.lineinfo[fs.pc - 1] = line


def luaK_ret(fs: 'FuncState', first: int, nret: int) -> None:
    """lcode.c:... - Generate return"""
    luaK_codeABC(fs, OP_RETURN, first, nret + 1, 0)


def luaK_setlist(fs: 'FuncState', base: int, nelems: int, tostore: int) -> None:
    """lcode.c:... - Generate SETLIST"""
    from .lua import LUA_MULTRET
    c = (nelems - 1) // 50 + 1  # LFIELDS_PER_FLUSH = 50
    b = tostore if tostore != LUA_MULTRET else 0
    # lua_assert(tostore != 0)
    if tostore == 0:
        return
    if c <= MAXARG_C:
        luaK_codeABC(fs, OP_SETLIST, base, b, c)
    else:
        luaK_codeABC(fs, OP_SETLIST, base, b, 0)
        luaK_code(fs, c)


def luaK_patchclose(fs: 'FuncState', list_val: int, level: int) -> None:
    """lcode.c:... - Patch close (for upvalues)"""
    level += 1  # Adjust for Lua's 1-based indexing
    while list_val != NO_JUMP:
        next_val = getjump(fs, list_val)
        inst = fs.f.code[list_val]
        fs.f.code[list_val] = (inst & ~(0xFF << 6)) | (level << 6)
        list_val = next_val


def SET_OPCODE(i: int, o: int) -> int:
    """Set opcode in instruction"""
    return (i & ~0x3F) | o


def SETARG_C(i: int, c: int) -> int:
    """Set C argument"""
    return (i & ~(0x1FF << 14)) | (c << 14)


def expdesc_new():
    """Create new expdesc"""
    from .lparser import expdesc
    return expdesc()


# Import VNONRELOC for use
from .lparser import VNONRELOC, VRELOCABLE, VK
