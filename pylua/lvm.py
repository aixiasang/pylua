# -*- coding: utf-8 -*-
"""
lvm.py - Lua Virtual Machine
============================
Source: lvm.h/lvm.c (lua-5.3.6/src/lvm.h, lvm.c)

Lua virtual machine
See Copyright Notice in lua.h
"""

from typing import Optional, Tuple, TYPE_CHECKING
import math

from .lua import (
    LUA_OPADD, LUA_OPSUB, LUA_OPMUL, LUA_OPMOD, LUA_OPPOW,
    LUA_OPDIV, LUA_OPIDIV, LUA_OPBAND, LUA_OPBOR, LUA_OPBXOR,
    LUA_OPSHL, LUA_OPSHR, LUA_OPUNM, LUA_OPBNOT,
    LUA_OPEQ, LUA_OPLT, LUA_OPLE,
    LUA_TNUMBER,
    lua_Integer, lua_Number,
)
from .luaconf import LUA_MAXINTEGER, LUA_MININTEGER, lua_numbertointeger
from .llimits import (
    lua_assert, cast_int, cast_num, l_castS2U, l_castU2S,
    luai_numadd, luai_numsub, luai_nummul, luai_nummod,
    luai_numpow, luai_numdiv, luai_numidiv, luai_numunm,
    luai_numlt, luai_numle, luai_numeq,
)
from .lobject import (
    TValue, Value, Proto, LClosure, Table, UpValRef,
    ttisinteger, ttisfloat, ttisnumber, ttisstring, ttisnil,
    ttistable, ttisfunction, ttisLclosure, ttisCclosure,
    ivalue, fltvalue, nvalue, tsvalue, hvalue,
    setivalue, setfltvalue, setnilvalue, setobj, setobj2s, setobjs2s,
    svalue, vslen, val_, ttnov, ctb,
)
from .lopcodes import (
    OpCode, GET_OPCODE, GETARG_A, GETARG_B, GETARG_C,
    GETARG_Bx, GETARG_sBx, GETARG_Ax,
    ISK, INDEXK, BITRK,
)
from .ltm import TMS, fasttm, luaT_gettmbyobj, luaT_trybinTM, luaT_callTM, luaT_callorderTM, ttypename

if TYPE_CHECKING:
    from .lstate import LuaState, CallInfo


# =============================================================================
# lvm.h:16-27 - Conversion Macros
# =============================================================================

# lvm.h:17 - #define cvt2str(o) ttisnumber(o)
def cvt2str(o: TValue) -> bool:
    """lvm.h:17 - Check if can convert to string (numbers only)"""
    return ttisnumber(o)

# lvm.h:24 - #define cvt2num(o) ttisstring(o)
def cvt2num(o: TValue) -> bool:
    """lvm.h:24 - Check if can convert to number (strings only)"""
    return ttisstring(o)

# lvm.h:36-37 - Floor to integer conversion mode
LUA_FLOORN2I: int = 0  # lvm.h:36


# =============================================================================
# UpValue Helper Functions (for handling UpValRef)
# =============================================================================

def _get_upval_value(L: 'LuaState', uv: 'UpVal') -> TValue:
    """
    Get the TValue from an upvalue, handling both legacy int and UpValRef.
    
    Args:
        L: Lua state (for stack access)
        uv: UpVal object
    
    Returns:
        TValue - the actual value
    """
    if isinstance(uv.v, UpValRef):
        if uv.v.is_open:
            return L.stack[uv.v.stack_index]
        else:
            return uv.v.tvalue
    elif isinstance(uv.v, int):
        return L.stack[uv.v]
    else:
        return uv.v if uv.v is not None else uv.value


def _set_upval_value(L: 'LuaState', uv: 'UpVal', val: TValue) -> None:
    """
    Set the value of an upvalue, handling both legacy int and UpValRef.
    
    Args:
        L: Lua state (for stack access)
        uv: UpVal object
        val: Value to set
    """
    if isinstance(uv.v, UpValRef):
        if uv.v.is_open:
            setobj(L, L.stack[uv.v.stack_index], val)
        else:
            setobj(L, uv.v.tvalue, val)
    elif isinstance(uv.v, int):
        setobj(L, L.stack[uv.v], val)
    else:
        target = uv.v if uv.v is not None else uv.value
        setobj(L, target, val)


# =============================================================================
# lvm.h:40-44 - tonumber and tointeger Macros
# =============================================================================

def tonumber(o: TValue) -> Tuple[bool, lua_Number]:
    """
    lvm.h:40-41 - Convert value to number
    #define tonumber(o,n) \
        (ttisfloat(o) ? (*(n) = fltvalue(o), 1) : luaV_tonumber_(o,n))
    
    Returns (success, number)
    """
    if ttisfloat(o):
        return (True, fltvalue(o))
    return luaV_tonumber_(o)


def tointeger(o: TValue, mode: int = LUA_FLOORN2I) -> Tuple[bool, lua_Integer]:
    """
    lvm.h:43-44 - Convert value to integer
    #define tointeger(o,i) \
        (ttisinteger(o) ? (*(i) = ivalue(o), 1) : luaV_tointeger(o,i,LUA_FLOORN2I))
    
    Returns (success, integer)
    """
    if ttisinteger(o):
        return (True, ivalue(o))
    return luaV_tointeger(o, mode)


# =============================================================================
# lvm.h:46 - intop Macro
# =============================================================================

def intop_add(v1: lua_Integer, v2: lua_Integer) -> lua_Integer:
    """lvm.h:46 - #define intop(op,v1,v2) l_castU2S(l_castS2U(v1) op l_castS2U(v2))"""
    return l_castU2S((l_castS2U(v1) + l_castS2U(v2)) & 0xFFFFFFFFFFFFFFFF)

def intop_sub(v1: lua_Integer, v2: lua_Integer) -> lua_Integer:
    return l_castU2S((l_castS2U(v1) - l_castS2U(v2)) & 0xFFFFFFFFFFFFFFFF)

def intop_mul(v1: lua_Integer, v2: lua_Integer) -> lua_Integer:
    return l_castU2S((l_castS2U(v1) * l_castS2U(v2)) & 0xFFFFFFFFFFFFFFFF)

def intop_band(v1: lua_Integer, v2: lua_Integer) -> lua_Integer:
    return l_castU2S(l_castS2U(v1) & l_castS2U(v2))

def intop_bor(v1: lua_Integer, v2: lua_Integer) -> lua_Integer:
    return l_castU2S(l_castS2U(v1) | l_castS2U(v2))

def intop_bxor(v1: lua_Integer, v2: lua_Integer) -> lua_Integer:
    return l_castU2S(l_castS2U(v1) ^ l_castS2U(v2))


# =============================================================================
# lvm.h:48 - luaV_rawequalobj Macro
# =============================================================================

def luaV_rawequalobj(t1: TValue, t2: TValue) -> bool:
    """lvm.h:48 - #define luaV_rawequalobj(t1,t2) luaV_equalobj(NULL,t1,t2)"""
    return luaV_equalobj(None, t1, t2)


# =============================================================================
# lvm.c:34 - MAXTAGLOOP
# =============================================================================

MAXTAGLOOP: int = 2000  # lvm.c:34 - limit for table tag-method chains

# Number of bits in mantissa for l_intfitsf check
NBM: int = 53  # For double precision float

# =============================================================================
# lvm.c:44-64 - l_intfitsf macro
# =============================================================================

def l_intfitsf(i: lua_Integer) -> bool:
    """
    lvm.c:59-60 - Check whether integer fits in float without rounding
    #define l_intfitsf(i) \
      (-((lua_Integer)1 << NBM) <= (i) && (i) <= ((lua_Integer)1 << NBM))
    """
    limit = 1 << NBM
    return -limit <= i <= limit


# =============================================================================
# lvm.c:72-85 - luaV_tonumber_
# =============================================================================

def luaV_tonumber_(obj: TValue) -> Tuple[bool, lua_Number]:
    """
    lvm.c:72-85 - Try to convert a value to a float
    
    int luaV_tonumber_ (const TValue *obj, lua_Number *n)
    
    Returns (success, number)
    Source: lvm.c:72-85
    """
    from .lobject import luaO_str2num
    
    if ttisinteger(obj):  # lvm.c:74-77
        return (True, cast_num(ivalue(obj)))
    elif cvt2num(obj):  # lvm.c:78-82 - string convertible to number?
        # Use luaO_str2num for proper string conversion
        temp = TValue()
        s = svalue(obj)
        if luaO_str2num(s, temp) != 0:
            # Successfully converted - get the number value
            if ttisinteger(temp):
                return (True, cast_num(ivalue(temp)))
            else:
                return (True, fltvalue(temp))
        return (False, 0.0)
    else:
        return (False, 0.0)  # lvm.c:84 - conversion failed


# =============================================================================
# lvm.c:94-117 - luaV_tointeger
# =============================================================================

def luaV_tointeger(obj: TValue, mode: int) -> Tuple[bool, lua_Integer]:
    """
    lvm.c:94-117 - Try to convert a value to an integer
    
    mode == 0: accepts only integral values
    mode == 1: takes the floor of the number
    mode == 2: takes the ceil of the number
    
    int luaV_tointeger (const TValue *obj, lua_Integer *p, int mode)
    
    Returns (success, integer)
    Source: lvm.c:94-117
    """
    if ttisfloat(obj):  # lvm.c:97-106
        n = fltvalue(obj)
        f = math.floor(n)
        if n != f:  # Not an integral value? - lvm.c:100
            if mode == 0:
                return (False, 0)  # lvm.c:101
            elif mode > 1:  # needs ceil? - lvm.c:102
                f += 1  # lvm.c:103
        # lvm.c:105 - lua_numbertointeger
        result, success = lua_numbertointeger(f)
        if success:
            return (True, result)
        return (False, 0)
    
    elif ttisinteger(obj):  # lvm.c:107-110
        return (True, ivalue(obj))
    
    elif cvt2num(obj):  # lvm.c:111-115 - string to number
        try:
            s = svalue(obj).decode('utf-8')
            # Try integer first
            if '.' not in s and 'e' not in s.lower():
                return (True, int(s))
            # Try float then convert
            n = float(s)
            f = math.floor(n)
            if n != f and mode == 0:
                return (False, 0)
            elif n != f and mode > 1:
                f += 1
            result, success = lua_numbertointeger(f)
            if success:
                return (True, result)
        except (ValueError, UnicodeDecodeError):
            pass
    
    return (False, 0)  # lvm.c:116


# =============================================================================
# lvm.c:135-152 - forlimit (For loop limit conversion)
# =============================================================================

def forlimit(obj: TValue, step: lua_Integer) -> Tuple[bool, lua_Integer, bool]:
    """
    lvm.c:135-152 - Try to convert a 'for' limit to an integer.
    
    static int forlimit (const TValue *obj, lua_Integer *p, lua_Integer step,
                         int *stopnow)
    
    Returns (success, limit_value, stopnow)
    
    The semantics of the loop are preserved:
    - If the limit can be converted to an integer (rounding down for positive step,
      up for negative), that is the limit.
    - Otherwise, if the limit is a number that's too large, use LUA_MAXINTEGER
      (no limit for positive step).
    - If the number is too negative, use LUA_MININTEGER.
    - 'stopnow' corrects the case when initial == LUA_MININTEGER.
    
    Source: lvm.c:135-152
    """
    stopnow = False
    mode = 2 if step < 0 else 1  # ceil for negative step, floor for positive
    
    ok, p = luaV_tointeger(obj, mode)
    if not ok:  # not fit in integer?
        # Try to convert to float
        ok_n, n = tonumber(obj)
        if not ok_n:  # cannot convert to float?
            return (False, 0, False)  # not a number
        
        if n > 0:  # float is larger than max integer
            p = LUA_MAXINTEGER
            if step < 0:
                stopnow = True
        else:  # float is smaller than min integer
            p = LUA_MININTEGER
            if step >= 0:
                stopnow = True
    
    return (True, p, stopnow)


# =============================================================================
# lvm.c:108-110 - luaV_div (Integer Division)
# =============================================================================

def luaV_div(L: 'LuaState', m: lua_Integer, n: lua_Integer) -> lua_Integer:
    """
    lvm.c:552-564 - Integer division; return 'm // n', that is, floor(m/n).
    
    lua_Integer luaV_div (lua_State *L, lua_Integer x, lua_Integer y)
    
    C division truncates its result (rounds towards zero).
    Python '//' is already floor division, so no correction needed.
    
    Source: lvm.c:552-564
    """
    if l_castS2U(n) + 1 <= 1:  # Special cases: -1 or 0
        if n == 0:
            raise ZeroDivisionError("attempt to divide by zero")
        # n == -1; avoid overflow with LUA_MININTEGER // -1
        # Use intop semantics: result = 0 - m with 64-bit wraparound
        return intop_sub(0, m)
    else:
        # Python // is already floor division
        return m // n


# =============================================================================
# lvm.c - luaV_mod (Integer Modulo)
# =============================================================================

def luaV_mod(L: 'LuaState', m: lua_Integer, n: lua_Integer) -> lua_Integer:
    """
    lvm.c:572-584 - Integer modulus; return 'm % n'.
    
    lua_Integer luaV_mod (lua_State *L, lua_Integer x, lua_Integer y)
    
    Lua modulo: the result has the same sign as the divisor.
    Python's % already follows this convention.
    
    Source: lvm.c:572-584
    """
    if l_castS2U(n) + 1 <= 1:  # Special cases: -1 or 0
        if n == 0:
            raise ZeroDivisionError("attempt to perform 'n%%0'")
        return 0  # m % -1 == 0 always
    else:
        # Python % already matches Lua semantics (result sign matches divisor)
        return m % n


# =============================================================================
# lvm.c - luaV_shiftl (Bit Shift)
# =============================================================================

def luaV_shiftl(x: lua_Integer, y: lua_Integer) -> lua_Integer:
    """
    lvm.c:110 (referenced from lobject.c:94-95) - Bit shift left
    
    lua_Integer luaV_shiftl (lua_Integer x, lua_Integer y)
    
    Source: lvm.c (~line 610)
    """
    NBITS = 64  # number of bits in lua_Integer
    if y < 0:  # Shift right?
        if y <= -NBITS:
            return 0
        return l_castU2S(l_castS2U(x) >> (-y))
    else:  # Shift left
        if y >= NBITS:
            return 0
        return l_castU2S((l_castS2U(x) << y) & 0xFFFFFFFFFFFFFFFF)


# =============================================================================
# lvm.c:248-268 - l_strcmp (String Comparison)
# =============================================================================

def l_strcmp(ls: bytes, rs: bytes) -> int:
    """
    lvm.c:248-268 - Compare two strings, returning an integer smaller-equal-
    -larger than zero if 'ls' is smaller-equal-larger than 'rs'.
    
    static int l_strcmp (const TString *ls, const TString *rs)
    
    The code is a little tricky because it allows '\0' in the strings.
    Source: lvm.c:248-268
    """
    # In Python, bytes comparison works correctly with embedded nulls
    if ls < rs:
        return -1
    elif ls > rs:
        return 1
    else:
        return 0


# =============================================================================
# lvm.c:281-293 - LTintfloat (Integer < Float comparison)
# =============================================================================

def LTintfloat(i: lua_Integer, f: lua_Number) -> bool:
    """
    lvm.c:281-293 - Check whether integer 'i' is less than float 'f'.
    
    static int LTintfloat (lua_Integer i, lua_Number f)
    
    If 'i' has an exact representation as a float ('l_intfitsf'), compare 
    numbers as floats. Otherwise, if 'f' is outside the range for integers, 
    result is trivial. Otherwise, compare them as integers.
    Source: lvm.c:281-293
    """
    if not l_intfitsf(i):
        # Integer doesn't fit exactly in float
        if f >= -cast_num(LUA_MININTEGER):  # -minint == maxint + 1
            return True  # f >= maxint + 1 > i
        elif f > cast_num(LUA_MININTEGER):  # minint < f <= maxint?
            return i < cast_int(f)  # compare them as integers
        else:  # f <= minint <= i (or 'f' is NaN) --> not(i < f)
            return False
    return luai_numlt(cast_num(i), f)  # compare them as floats


# =============================================================================
# lvm.c:300-312 - LEintfloat (Integer <= Float comparison)
# =============================================================================

def LEintfloat(i: lua_Integer, f: lua_Number) -> bool:
    """
    lvm.c:300-312 - Check whether integer 'i' is less than or equal to float 'f'.
    
    static int LEintfloat (lua_Integer i, lua_Number f)
    
    See comments on LTintfloat.
    Source: lvm.c:300-312
    """
    if not l_intfitsf(i):
        if f >= -cast_num(LUA_MININTEGER):  # -minint == maxint + 1
            return True  # f >= maxint + 1 > i
        elif f >= cast_num(LUA_MININTEGER):  # minint <= f <= maxint?
            return i <= cast_int(f)  # compare them as integers
        else:  # f < minint <= i (or 'f' is NaN) --> not(i <= f)
            return False
    return luai_numle(cast_num(i), f)  # compare them as floats


# =============================================================================
# lvm.c:318-335 - LTnum (Number < comparison)
# =============================================================================

def LTnum(l: TValue, r: TValue) -> bool:
    """
    lvm.c:318-335 - Return 'l < r', for numbers.
    
    static int LTnum (const TValue *l, const TValue *r)
    
    Source: lvm.c:318-335
    """
    if ttisinteger(l):
        li = ivalue(l)
        if ttisinteger(r):
            return li < ivalue(r)  # both are integers
        else:  # 'l' is int and 'r' is float
            return LTintfloat(li, fltvalue(r))  # l < r ?
    else:
        lf = fltvalue(l)  # 'l' must be float
        if ttisfloat(r):
            return luai_numlt(lf, fltvalue(r))  # both are float
        elif math.isnan(lf):  # 'r' is int and 'l' is float
            return False  # NaN < i is always false
        else:  # without NaN, (l < r) <--> not(r <= l)
            return not LEintfloat(ivalue(r), lf)  # not (r <= l) ?


# =============================================================================
# lvm.c:341-358 - LEnum (Number <= comparison)
# =============================================================================

def LEnum(l: TValue, r: TValue) -> bool:
    """
    lvm.c:341-358 - Return 'l <= r', for numbers.
    
    static int LEnum (const TValue *l, const TValue *r)
    
    Source: lvm.c:341-358
    """
    if ttisinteger(l):
        li = ivalue(l)
        if ttisinteger(r):
            return li <= ivalue(r)  # both are integers
        else:  # 'l' is int and 'r' is float
            return LEintfloat(li, fltvalue(r))  # l <= r ?
    else:
        lf = fltvalue(l)  # 'l' must be float
        if ttisfloat(r):
            return luai_numle(lf, fltvalue(r))  # both are float
        elif math.isnan(lf):  # 'r' is int and 'l' is float
            return False  # NaN <= i is always false
        else:  # without NaN, (l <= r) <--> not(r < l)
            return not LTintfloat(ivalue(r), lf)  # not (r < l) ?


# =============================================================================
# lvm.h:96 - luaV_equalobj
# =============================================================================

def luaV_equalobj(L: Optional['LuaState'], t1: TValue, t2: TValue) -> bool:
    """
    lvm.c:407-450 - Main operation for equality of Lua values; return 't1 == t2'.
    
    int luaV_equalobj (lua_State *L, const TValue *t1, const TValue *t2)
    
    L == NULL means raw equality (no metamethods)
    Source: lvm.c:407-450
    """
    from .lobject import (
        ttype, ttisboolean, bvalue, ttislightuserdata, pvalue,
        ttislcf, fvalue, ttisshrstring, ttislngstring, ttisfulluserdata,
        uvalue, LUA_TNIL, LUA_TNUMINT, LUA_TNUMFLT, LUA_TBOOLEAN,
        LUA_TLIGHTUSERDATA, LUA_TLCF, LUA_TSHRSTR, LUA_TLNGSTR,
        LUA_TUSERDATA, LUA_TTABLE, l_isfalse,
    )
    from .llimits import luai_numeq
    
    tm = None  # metamethod
    
    # Check if not the same variant
    if ttype(t1) != ttype(t2):
        # Only numbers can be equal with different variants
        if ttnov(t1) != ttnov(t2) or ttnov(t1) != LUA_TNUMBER:
            return False
        else:  # two numbers with different variants - compare as integers
            ok1, i1 = tointeger(t1)
            ok2, i2 = tointeger(t2)
            return ok1 and ok2 and i1 == i2
    
    # values have same type and same variant
    tt = ttype(t1)
    
    if tt == LUA_TNIL:
        return True
    
    if tt == LUA_TNUMINT:
        return ivalue(t1) == ivalue(t2)
    
    if tt == LUA_TNUMFLT:
        return luai_numeq(fltvalue(t1), fltvalue(t2))
    
    if tt == LUA_TBOOLEAN:
        return bvalue(t1) == bvalue(t2)  # true must be 1
    
    if tt == LUA_TLIGHTUSERDATA:
        return pvalue(t1) == pvalue(t2)
    
    if tt == LUA_TLCF:
        return fvalue(t1) == fvalue(t2)
    
    if ttisshrstring(t1):
        # Short strings are interned, compare by identity first then content
        return svalue(t1) == svalue(t2)
    
    if ttislngstring(t1):
        return svalue(t1) == svalue(t2)
    
    if ttisfulluserdata(t1):
        if uvalue(t1) is uvalue(t2):
            return True
        elif L is None:
            return False
        tm = fasttm(L, uvalue(t1).metatable, TMS.TM_EQ)
        if tm is None:
            tm = fasttm(L, uvalue(t2).metatable, TMS.TM_EQ)
        # will try TM below
    
    elif ttistable(t1):
        if hvalue(t1) is hvalue(t2):
            return True
        elif L is None:
            return False
        tm = fasttm(L, hvalue(t1).metatable, TMS.TM_EQ)
        if tm is None:
            tm = fasttm(L, hvalue(t2).metatable, TMS.TM_EQ)
        # will try TM below
    
    else:
        # For other types (closures, threads), compare by gc reference
        return val_(t1).gc is val_(t2).gc
    
    # Try metamethod if found
    if tm is None:  # no TM?
        return False  # objects are different
    
    # Call TM and check result
    luaT_callTM(L, tm, t1, t2, L.top, 1)
    return not l_isfalse(L.stack[L.top])


# =============================================================================
# lvm.c:97-98 - luaV_lessthan / luaV_lessequal
# =============================================================================

def luaV_lessthan(L: 'LuaState', l: TValue, r: TValue) -> bool:
    """
    lvm.c:364-373 - Main operation less than; return 'l < r'.
    
    int luaV_lessthan (lua_State *L, const TValue *l, const TValue *r)
    
    Source: lvm.c:364-373
    """
    if ttisnumber(l) and ttisnumber(r):  # both operands are numbers?
        return LTnum(l, r)
    elif ttisstring(l) and ttisstring(r):  # both are strings?
        return l_strcmp(svalue(l), svalue(r)) < 0
    else:
        res = luaT_callorderTM(L, l, r, TMS.TM_LT)  # try __lt metamethod
        if res < 0:  # no metamethod?
            raise TypeError(f"attempt to compare {ttypename(ttnov(l))} with {ttypename(ttnov(r))}")
        return bool(res)


def luaV_lessequal(L: 'LuaState', l: TValue, r: TValue) -> bool:
    """
    lvm.c:384-400 - Main operation less than or equal to; return 'l <= r'.
    
    int luaV_lessequal (lua_State *L, const TValue *l, const TValue *r)
    
    If it needs a metamethod and there is no '__le', try '__lt', based on
    l <= r iff !(r < l) (assuming a total order).
    Source: lvm.c:384-400
    """
    from .lstate import CIST_LEQ
    
    if ttisnumber(l) and ttisnumber(r):  # both operands are numbers?
        return LEnum(l, r)
    elif ttisstring(l) and ttisstring(r):  # both are strings?
        return l_strcmp(svalue(l), svalue(r)) <= 0
    else:
        res = luaT_callorderTM(L, l, r, TMS.TM_LE)  # try 'le'
        if res >= 0:
            return bool(res)
        else:  # try 'lt':
            if L.ci is not None:
                L.ci.callstatus |= CIST_LEQ  # mark it is doing 'lt' for 'le'
            res = luaT_callorderTM(L, r, l, TMS.TM_LT)
            if L.ci is not None:
                L.ci.callstatus &= ~CIST_LEQ  # clear mark (using ^= would toggle)
            if res < 0:
                raise TypeError(f"attempt to compare {ttypename(ttnov(l))} with {ttypename(ttnov(r))}")
            return not bool(res)  # result is negated


# =============================================================================
# lvm.c:107 - luaV_concat
# =============================================================================

def tostring(L: 'LuaState', o: TValue) -> bool:
    """
    lvm.c:454-455 - Macro to ensure element at 'o' is a string
    #define tostring(L,o) (ttisstring(o) || (cvt2str(o) && (luaO_tostring(L, o), 1)))
    """
    from .lobject import TString, LUA_TSHRSTR, ctb
    
    if ttisstring(o):
        return True
    if cvt2str(o):  # number can be converted
        # Convert number to string
        if ttisinteger(o):
            s = str(ivalue(o)).encode('utf-8')
        else:
            n = fltvalue(o)
            # Format like Lua: use integer representation if exact
            if n == int(n) and abs(n) < 1e14:
                s = str(int(n)) + '.0'
                s = s.encode('utf-8')
            else:
                s = str(n).encode('utf-8')
        
        ts = TString()
        ts.tt = LUA_TSHRSTR
        ts.data = s
        ts.shrlen = len(s)
        o.value_.gc = ts
        o.tt_ = ctb(LUA_TSHRSTR)
        return True
    return False


def isemptystr(o: TValue) -> bool:
    """
    lvm.c:457 - #define isemptystr(o) (ttisshrstring(o) && tsvalue(o)->shrlen == 0)
    """
    from .lobject import ttisshrstring, tsvalue
    return ttisshrstring(o) and tsvalue(o).shrlen == 0


def luaV_concat(L: 'LuaState', total: int) -> None:
    """
    lvm.c:474-511 - Main operation for concatenation: concat 'total' values in the stack.
    
    void luaV_concat (lua_State *L, int total)
    
    Source: lvm.c:474-511
    """
    from .lobject import TString, LUA_TSHRSTR, ctb, setsvalue2s
    
    lua_assert(total >= 2)
    
    while total > 1:
        top = L.top
        n = 2  # number of elements handled in this pass (at least 2)
        
        v1 = L.stack[top - 2]
        v2 = L.stack[top - 1]
        
        if not (ttisstring(v1) or cvt2str(v1)) or not tostring(L, v2):
            # Try __concat metamethod
            luaT_trybinTM(L, v1, v2, top - 2, TMS.TM_CONCAT)
        elif isemptystr(v2):  # second operand is empty?
            tostring(L, v1)  # result is first operand
        elif isemptystr(v1):  # first operand is an empty string?
            setobjs2s(L, L.stack[top - 2], L.stack[top - 1])  # result is second op
        else:
            # at least two non-empty string values; get as many as possible
            tl = vslen(v2)
            
            # collect total length and number of strings
            n = 1
            while n < total and tostring(L, L.stack[top - n - 1]):
                l = vslen(L.stack[top - n - 1])
                # Check for overflow
                if l >= (2**62) - tl:
                    raise RuntimeError("string length overflow")
                tl += l
                n += 1
            
            # Build result string
            parts = []
            for i in range(n, 0, -1):
                parts.append(svalue(L.stack[top - i]))
            result_bytes = b''.join(parts)
            
            # Create result TString
            ts = TString()
            ts.tt = LUA_TSHRSTR
            ts.data = result_bytes
            ts.shrlen = len(result_bytes)
            
            # Set result on stack
            setsvalue2s(L, L.stack[top - n], ts)
        
        total -= n - 1  # got 'n' strings to create 1 new
        L.top -= n - 1  # popped 'n' strings and pushed one


# =============================================================================
# lvm.c:111 - luaV_objlen
# =============================================================================

def luaV_objlen(L: 'LuaState', ra: int, rb: TValue) -> None:
    """
    lvm.c:517-543 - Main operation 'ra' = #rb'.
    
    void luaV_objlen (lua_State *L, StkId ra, const TValue *rb)
    
    Source: lvm.c:517-543
    """
    from .lobject import ttisshrstring, ttislngstring, tsvalue
    
    tm = None
    
    if ttistable(rb):  # table
        h = hvalue(rb)
        tm = fasttm(L, h.metatable, TMS.TM_LEN)
        if tm is not None:
            pass  # metamethod? break to call it
        else:
            # primitive len - count array part
            setivalue(L.stack[ra], luaH_getn(h))
            return
    
    elif ttisshrstring(rb):
        setivalue(L.stack[ra], tsvalue(rb).shrlen)
        return
    
    elif ttislngstring(rb):
        setivalue(L.stack[ra], tsvalue(rb).lnglen)
        return
    
    else:  # try metamethod
        tm = luaT_gettmbyobj(L, rb, TMS.TM_LEN)
        if ttisnil(tm):  # no metamethod?
            raise TypeError(f"attempt to get length of a {ttypename(ttnov(rb))} value")
    
    # Call metamethod
    luaT_callTM(L, tm, rb, rb, ra, 1)


def luaH_getn(t: 'Table') -> int:
    """
    ltable.c:614-634 - Get 'n' for table (raw length)
    
    Simplified implementation - count consecutive non-nil elements in array
    """
    # Count array part - find last non-nil
    j = len(t.array)
    while j > 0 and ttisnil(t.array[j - 1]):
        j -= 1
    return j


# =============================================================================
# lvm.c:736-741 - dojump macro
# =============================================================================

def dojump(L: 'LuaState', ci: 'CallInfo', i: int, e: int) -> None:
    """
    lvm.c:738-741 - Execute jump instruction
    #define dojump(ci,i,e) \
      { int a = GETARG_A(i); \
        if (a != 0) luaF_close(L, ci->u.l.base + a - 1); \
        ci->u.l.savedpc += GETARG_sBx(i) + e; }
    Source: lvm.c:738-741
    """
    from .lfunc import luaF_close
    a = GETARG_A(i)
    if a != 0:
        luaF_close(L, ci.base + a - 1)
    ci.savedpc += GETARG_sBx(i) + e


# =============================================================================
# lvm.c:786-1319 - luaV_execute (Main VM Loop)
# =============================================================================

def luaV_execute(L: 'LuaState') -> None:
    """
    lvm.h:106 / lvm.c:786-1319 - Main VM execution loop
    
    void luaV_execute (lua_State *L)
    
    This is the heart of the Lua VM - executes bytecode instructions.
    Source: lvm.c:786-1319
    """
    from .lstate import CIST_FRESH, CIST_TAIL, isLua
    from .lfunc import luaF_close
    from .ldo import luaD_precall, luaD_poscall, luaD_call
    from .lobject import (
        clLvalue, l_isfalse, setbvalue, chgivalue, chgfltvalue,
        setclLvalue, getproto,
    )
    
    ci = L.ci  # lvm.c:787
    ci.callstatus |= CIST_FRESH  # lvm.c:791
    
    # newframe label - reentry point when frame changes
    while True:
        lua_assert(ci == L.ci)
        cl = clLvalue(L.stack[ci.func])  # lvm.c:794
        k = cl.p.k  # lvm.c:795 - constants table
        base = ci.base  # lvm.c:796
        
        # Main loop of interpreter - lvm.c:798
        while True:
            # vmfetch - lvm.c:756-763
            if ci.savedpc >= len(cl.p.code):
                return  # End of function
            i = cl.p.code[ci.savedpc]
            ci.savedpc += 1
            ra = base + GETARG_A(i)
            
            op = GET_OPCODE(i)
            
            # vmdispatch - lvm.c:802
            if op == OpCode.OP_MOVE:  # lvm.c:803-806
                rb = base + GETARG_B(i)
                setobjs2s(L, L.stack[ra], L.stack[rb])
            
            elif op == OpCode.OP_LOADK:  # lvm.c:807-811
                bx = GETARG_Bx(i)
                setobj2s(L, L.stack[ra], k[bx])
            
            elif op == OpCode.OP_LOADKX:  # lvm.c:812-818
                lua_assert(GET_OPCODE(cl.p.code[ci.savedpc]) == OpCode.OP_EXTRAARG)
                ax = GETARG_Ax(cl.p.code[ci.savedpc])
                ci.savedpc += 1
                setobj2s(L, L.stack[ra], k[ax])
            
            elif op == OpCode.OP_LOADBOOL:  # lvm.c:819-823
                setbvalue(L.stack[ra], GETARG_B(i))
                if GETARG_C(i):
                    ci.savedpc += 1
            
            elif op == OpCode.OP_LOADNIL:  # lvm.c:824-829
                b = GETARG_B(i)
                for j in range(b + 1):
                    setnilvalue(L.stack[ra + j])
            
            elif op == OpCode.OP_GETUPVAL:  # lvm.c:831-835
                b = GETARG_B(i)
                uv = cl.upvals[b]
                upval = _get_upval_value(L, uv)
                setobj2s(L, L.stack[ra], upval)
            
            elif op == OpCode.OP_GETTABUP:  # lvm.c:836-841
                b = GETARG_B(i)
                uv = cl.upvals[b]
                upval = _get_upval_value(L, uv)
                rc = _RKC(L, i, base, k)
                _gettable(L, upval, rc, ra)
            
            elif op == OpCode.OP_GETTABLE:  # lvm.c:842-847
                rb = L.stack[base + GETARG_B(i)]
                rc = _RKC(L, i, base, k)
                _gettable(L, rb, rc, ra)
            
            elif op == OpCode.OP_SETTABUP:  # lvm.c:848-854
                a = GETARG_A(i)
                uv = cl.upvals[a]
                upval = _get_upval_value(L, uv)
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                _settable(L, upval, rb, rc)
            
            elif op == OpCode.OP_SETUPVAL:  # lvm.c:855-859
                b = GETARG_B(i)
                uv = cl.upvals[b]
                _set_upval_value(L, uv, L.stack[ra])
            
            elif op == OpCode.OP_SETTABLE:  # lvm.c:861-866
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                _settable(L, L.stack[ra], rb, rc)
            
            elif op == OpCode.OP_NEWTABLE:  # lvm.c:867-876
                from .lobject import Table, luaO_fb2int, sethvalue
                b = GETARG_B(i)
                c = GETARG_C(i)
                t = Table()
                t.tt = 5  # LUA_TTABLE
                sethvalue(L, L.stack[ra], t)
                # Resize if needed
                if b != 0 or c != 0:
                    from .lobject import luaO_fb2int
                    t.sizearray = luaO_fb2int(b)
                    t.array = [TValue() for _ in range(t.sizearray)]
            
            elif op == OpCode.OP_SELF:  # lvm.c:877-888
                rb = L.stack[base + GETARG_B(i)]
                rc = _RKC(L, i, base, k)
                setobjs2s(L, L.stack[ra + 1], rb)
                _gettable(L, rb, rc, ra)
            
            elif op == OpCode.OP_ADD:  # lvm.c:889-902
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                if ttisinteger(rb) and ttisinteger(rc):
                    ib, ic = ivalue(rb), ivalue(rc)
                    setivalue(L.stack[ra], intop_add(ib, ic))
                else:
                    ok_b, nb = tonumber(rb)
                    ok_c, nc = tonumber(rc)
                    if ok_b and ok_c:
                        setfltvalue(L.stack[ra], luai_numadd(L, nb, nc))
                    else:
                        luaT_trybinTM(L, rb, rc, ra, TMS.TM_ADD)
            
            elif op == OpCode.OP_SUB:  # lvm.c:903-916
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                if ttisinteger(rb) and ttisinteger(rc):
                    ib, ic = ivalue(rb), ivalue(rc)
                    setivalue(L.stack[ra], intop_sub(ib, ic))
                else:
                    ok_b, nb = tonumber(rb)
                    ok_c, nc = tonumber(rc)
                    if ok_b and ok_c:
                        setfltvalue(L.stack[ra], luai_numsub(L, nb, nc))
                    else:
                        luaT_trybinTM(L, rb, rc, ra, TMS.TM_SUB)
            
            elif op == OpCode.OP_MUL:  # lvm.c:917-930
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                if ttisinteger(rb) and ttisinteger(rc):
                    ib, ic = ivalue(rb), ivalue(rc)
                    setivalue(L.stack[ra], intop_mul(ib, ic))
                else:
                    ok_b, nb = tonumber(rb)
                    ok_c, nc = tonumber(rc)
                    if ok_b and ok_c:
                        setfltvalue(L.stack[ra], luai_nummul(L, nb, nc))
                    else:
                        luaT_trybinTM(L, rb, rc, ra, TMS.TM_MUL)
            
            elif op == OpCode.OP_DIV:  # lvm.c:931-940 - float division
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                ok_b, nb = tonumber(rb)
                ok_c, nc = tonumber(rc)
                if ok_b and ok_c:
                    setfltvalue(L.stack[ra], luai_numdiv(L, nb, nc))
                else:
                    luaT_trybinTM(L, rb, rc, ra, TMS.TM_DIV)
            
            elif op == OpCode.OP_IDIV:  # lvm.c:1007-1020 - floor division
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                if ttisinteger(rb) and ttisinteger(rc):
                    ib, ic = ivalue(rb), ivalue(rc)
                    setivalue(L.stack[ra], luaV_div(L, ib, ic))
                else:
                    ok_b, nb = tonumber(rb)
                    ok_c, nc = tonumber(rc)
                    if ok_b and ok_c:
                        setfltvalue(L.stack[ra], luai_numidiv(L, nb, nc))
                    else:
                        luaT_trybinTM(L, rb, rc, ra, TMS.TM_IDIV)
            
            elif op == OpCode.OP_MOD:  # lvm.c:991-1006
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                if ttisinteger(rb) and ttisinteger(rc):
                    ib, ic = ivalue(rb), ivalue(rc)
                    setivalue(L.stack[ra], luaV_mod(L, ib, ic))
                else:
                    ok_b, nb = tonumber(rb)
                    ok_c, nc = tonumber(rc)
                    if ok_b and ok_c:
                        m = luai_nummod(L, nb, nc)
                        setfltvalue(L.stack[ra], m)
                    else:
                        luaT_trybinTM(L, rb, rc, ra, TMS.TM_MOD)
            
            elif op == OpCode.OP_POW:  # lvm.c:1021-1030
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                ok_b, nb = tonumber(rb)
                ok_c, nc = tonumber(rc)
                if ok_b and ok_c:
                    setfltvalue(L.stack[ra], luai_numpow(L, nb, nc))
                else:
                    luaT_trybinTM(L, rb, rc, ra, TMS.TM_POW)
            
            elif op == OpCode.OP_BAND:  # lvm.c:941-950
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                ok_b, ib = tointeger(rb)
                ok_c, ic = tointeger(rc)
                if ok_b and ok_c:
                    setivalue(L.stack[ra], intop_band(ib, ic))
                else:
                    luaT_trybinTM(L, rb, rc, ra, TMS.TM_BAND)
            
            elif op == OpCode.OP_BOR:  # lvm.c:951-960
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                ok_b, ib = tointeger(rb)
                ok_c, ic = tointeger(rc)
                if ok_b and ok_c:
                    setivalue(L.stack[ra], intop_bor(ib, ic))
                else:
                    luaT_trybinTM(L, rb, rc, ra, TMS.TM_BOR)
            
            elif op == OpCode.OP_BXOR:  # lvm.c:961-970
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                ok_b, ib = tointeger(rb)
                ok_c, ic = tointeger(rc)
                if ok_b and ok_c:
                    setivalue(L.stack[ra], intop_bxor(ib, ic))
                else:
                    luaT_trybinTM(L, rb, rc, ra, TMS.TM_BXOR)
            
            elif op == OpCode.OP_SHL:  # lvm.c:971-980
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                ok_b, ib = tointeger(rb)
                ok_c, ic = tointeger(rc)
                if ok_b and ok_c:
                    setivalue(L.stack[ra], luaV_shiftl(ib, ic))
                else:
                    luaT_trybinTM(L, rb, rc, ra, TMS.TM_SHL)
            
            elif op == OpCode.OP_SHR:  # lvm.c:981-990
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                ok_b, ib = tointeger(rb)
                ok_c, ic = tointeger(rc)
                if ok_b and ok_c:
                    setivalue(L.stack[ra], luaV_shiftl(ib, -ic))
                else:
                    luaT_trybinTM(L, rb, rc, ra, TMS.TM_SHR)
            
            elif op == OpCode.OP_UNM:  # lvm.c:1031-1045
                rb = L.stack[base + GETARG_B(i)]
                if ttisinteger(rb):
                    ib = ivalue(rb)
                    setivalue(L.stack[ra], intop_sub(0, ib))
                else:
                    ok, nb = tonumber(rb)
                    if ok:
                        setfltvalue(L.stack[ra], luai_numunm(L, nb))
                    else:
                        luaT_trybinTM(L, rb, rb, ra, TMS.TM_UNM)
            
            elif op == OpCode.OP_BNOT:  # lvm.c:1046-1056
                rb = L.stack[base + GETARG_B(i)]
                ok, ib = tointeger(rb)
                if ok:
                    setivalue(L.stack[ra], intop_bxor(~0, ib))
                else:
                    luaT_trybinTM(L, rb, rb, ra, TMS.TM_BNOT)
            
            elif op == OpCode.OP_NOT:  # lvm.c:1057-1062
                rb = L.stack[base + GETARG_B(i)]
                res = 1 if l_isfalse(rb) else 0
                setbvalue(L.stack[ra], res)
            
            elif op == OpCode.OP_LEN:  # lvm.c:1063-1066
                luaV_objlen(L, ra, L.stack[base + GETARG_B(i)])
            
            elif op == OpCode.OP_CONCAT:  # lvm.c:1067-1079
                b = GETARG_B(i)
                c = GETARG_C(i)
                L.top = base + c + 1
                luaV_concat(L, c - b + 1)
                setobjs2s(L, L.stack[ra], L.stack[base + b])
                L.top = ci.top
            
            elif op == OpCode.OP_JMP:  # lvm.c:1080-1083
                dojump(L, ci, i, 0)
            
            elif op == OpCode.OP_EQ:  # lvm.c:1084-1094
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                if luaV_equalobj(L, rb, rc) != GETARG_A(i):
                    ci.savedpc += 1
                else:
                    ni = cl.p.code[ci.savedpc]
                    dojump(L, ci, ni, 1)
            
            elif op == OpCode.OP_LT:  # lvm.c:1095-1103
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                if (1 if luaV_lessthan(L, rb, rc) else 0) != GETARG_A(i):
                    ci.savedpc += 1
                else:
                    ni = cl.p.code[ci.savedpc]
                    dojump(L, ci, ni, 1)
            
            elif op == OpCode.OP_LE:  # lvm.c:1104-1112
                rb = _RKB(L, i, base, k)
                rc = _RKC(L, i, base, k)
                if (1 if luaV_lessequal(L, rb, rc) else 0) != GETARG_A(i):
                    ci.savedpc += 1
                else:
                    ni = cl.p.code[ci.savedpc]
                    dojump(L, ci, ni, 1)
            
            elif op == OpCode.OP_TEST:  # lvm.c:1113-1119
                if (GETARG_C(i) and l_isfalse(L.stack[ra])) or \
                   (not GETARG_C(i) and not l_isfalse(L.stack[ra])):
                    ci.savedpc += 1
                else:
                    ni = cl.p.code[ci.savedpc]
                    dojump(L, ci, ni, 1)
            
            elif op == OpCode.OP_TESTSET:  # lvm.c:1120-1129
                rb = L.stack[base + GETARG_B(i)]
                if (GETARG_C(i) and l_isfalse(rb)) or \
                   (not GETARG_C(i) and not l_isfalse(rb)):
                    ci.savedpc += 1
                else:
                    setobjs2s(L, L.stack[ra], rb)
                    ni = cl.p.code[ci.savedpc]
                    dojump(L, ci, ni, 1)
            
            elif op == OpCode.OP_CALL:  # lvm.c:1130-1144
                b = GETARG_B(i)
                nresults = GETARG_C(i) - 1
                if b != 0:
                    L.top = ra + b
                if luaD_precall(L, ra, nresults):  # C function
                    if nresults >= 0:
                        L.top = ci.top
                    base = ci.base
                else:  # Lua function
                    ci = L.ci
                    break  # goto newframe
            
            elif op == OpCode.OP_TAILCALL:  # lvm.c:1145-1175
                b = GETARG_B(i)
                if b != 0:
                    L.top = ra + b
                from .lua import LUA_MULTRET
                lua_assert(GETARG_C(i) - 1 == LUA_MULTRET)
                if luaD_precall(L, ra, LUA_MULTRET):  # C function
                    base = ci.base
                else:
                    # Tail call optimization - lvm.c:1153-1172
                    nci = L.ci
                    oci = nci.previous
                    nfunc = nci.func
                    ofunc = oci.func
                    lim = nci.base + getproto(L.stack[nfunc]).numparams
                    if cl.p.sizep > 0:
                        luaF_close(L, oci.base)
                    # Move new frame into old one
                    aux = 0
                    while nfunc + aux < lim:
                        setobjs2s(L, L.stack[ofunc + aux], L.stack[nfunc + aux])
                        aux += 1
                    oci.base = ofunc + (nci.base - nfunc)
                    L.top = ofunc + (L.top - nfunc)
                    oci.top = L.top
                    oci.savedpc = nci.savedpc
                    oci.callstatus |= CIST_TAIL
                    L.ci = oci
                    ci = oci
                    break  # goto newframe
            
            elif op == OpCode.OP_RETURN:  # lvm.c:1176-1189
                b = GETARG_B(i)
                # Use len(cl.p.p) since sizep may not be set correctly
                if cl.p.p and len(cl.p.p) > 0:
                    luaF_close(L, base)
                nres = (b - 1) if b != 0 else cast_int(L.top - ra)
                b = luaD_poscall(L, ci, ra, nres)
                if ci.callstatus & CIST_FRESH:
                    return  # External invocation
                else:
                    ci = L.ci
                    if b:
                        L.top = ci.top
                    lua_assert(isLua(ci))
                    break  # goto newframe
            
            elif op == OpCode.OP_FORLOOP:  # lvm.c:1190-1213
                if ttisinteger(L.stack[ra]):  # integer loop
                    step = ivalue(L.stack[ra + 2])
                    idx = intop_add(ivalue(L.stack[ra]), step)
                    limit = ivalue(L.stack[ra + 1])
                    if (step > 0 and idx <= limit) or (step <= 0 and limit <= idx):
                        ci.savedpc += GETARG_sBx(i)
                        chgivalue(L.stack[ra], idx)
                        setivalue(L.stack[ra + 3], idx)
                else:  # float loop
                    step = fltvalue(L.stack[ra + 2])
                    idx = luai_numadd(L, fltvalue(L.stack[ra]), step)
                    limit = fltvalue(L.stack[ra + 1])
                    if (step > 0 and idx <= limit) or (step <= 0 and limit <= idx):
                        ci.savedpc += GETARG_sBx(i)
                        chgfltvalue(L.stack[ra], idx)
                        setfltvalue(L.stack[ra + 3], idx)
            
            elif op == OpCode.OP_FORPREP:  # lvm.c:1214-1241
                init = L.stack[ra]
                plimit = L.stack[ra + 1]
                pstep = L.stack[ra + 2]
                if ttisinteger(init) and ttisinteger(pstep):
                    ok, ilimit = tointeger(plimit)
                    if ok:
                        # All values are integer
                        initv = ivalue(init)
                        setivalue(plimit, ilimit)
                        setivalue(init, intop_sub(initv, ivalue(pstep)))
                        ci.savedpc += GETARG_sBx(i)
                        continue
                # Try making all values floats
                ok_l, nlimit = tonumber(plimit)
                if not ok_l:
                    raise RuntimeError("'for' limit must be a number")
                setfltvalue(plimit, nlimit)
                ok_s, nstep = tonumber(pstep)
                if not ok_s:
                    raise RuntimeError("'for' step must be a number")
                setfltvalue(pstep, nstep)
                ok_i, ninit = tonumber(init)
                if not ok_i:
                    raise RuntimeError("'for' initial value must be a number")
                setfltvalue(init, luai_numsub(L, ninit, nstep))
                ci.savedpc += GETARG_sBx(i)
            
            elif op == OpCode.OP_TFORCALL:  # lvm.c:1242-1254
                cb = ra + 3
                setobjs2s(L, L.stack[cb + 2], L.stack[ra + 2])
                setobjs2s(L, L.stack[cb + 1], L.stack[ra + 1])
                setobjs2s(L, L.stack[cb], L.stack[ra])
                L.top = cb + 3
                luaD_call(L, cb, GETARG_C(i))
                L.top = ci.top
                i = cl.p.code[ci.savedpc]
                ci.savedpc += 1
                ra = base + GETARG_A(i)
                lua_assert(GET_OPCODE(i) == OpCode.OP_TFORLOOP)
                # Fall through to TFORLOOP
                if not ttisnil(L.stack[ra + 1]):
                    setobjs2s(L, L.stack[ra], L.stack[ra + 1])
                    ci.savedpc += GETARG_sBx(i)
            
            elif op == OpCode.OP_TFORLOOP:  # lvm.c:1255-1262
                if not ttisnil(L.stack[ra + 1]):
                    setobjs2s(L, L.stack[ra], L.stack[ra + 1])
                    ci.savedpc += GETARG_sBx(i)
            
            elif op == OpCode.OP_SETLIST:  # lvm.c:1263-1284
                n = GETARG_B(i)
                c = GETARG_C(i)
                if n == 0:
                    n = cast_int(L.top - ra) - 1
                if c == 0:
                    lua_assert(GET_OPCODE(cl.p.code[ci.savedpc]) == OpCode.OP_EXTRAARG)
                    c = GETARG_Ax(cl.p.code[ci.savedpc])
                    ci.savedpc += 1
                h = hvalue(L.stack[ra])
                last = ((c - 1) * LFIELDS_PER_FLUSH) + n
                # Ensure array is large enough
                while last > len(h.array):
                    h.array.append(TValue())
                    h.sizearray = len(h.array)
                for j in range(n, 0, -1):
                    val = L.stack[ra + j]
                    setobj(L, h.array[last - 1], val)
                    last -= 1
                L.top = ci.top
            
            elif op == OpCode.OP_CLOSURE:  # lvm.c:1285-1294
                bx = GETARG_Bx(i)
                p = cl.p.p[bx]
                ncl = _pushclosure(L, p, cl.upvals, base, ra)
                setclLvalue(L, L.stack[ra], ncl)
            
            elif op == OpCode.OP_VARARG:  # lvm.c:1295-1312
                b = GETARG_B(i) - 1
                n = cast_int(base - ci.func) - cl.p.numparams - 1
                if n < 0:
                    n = 0
                if b < 0:
                    b = n
                    while len(L.stack) <= ra + n:
                        L.stack.append(TValue())
                    L.top = ra + n
                for j in range(b):
                    if j < n:
                        setobjs2s(L, L.stack[ra + j], L.stack[base - n + j])
                    else:
                        setnilvalue(L.stack[ra + j])
            
            elif op == OpCode.OP_EXTRAARG:  # lvm.c:1313-1316
                lua_assert(False)  # Should never be executed directly
            
            else:
                raise RuntimeError(f"Unknown opcode: {op}")
        
        # End of inner while - continue to newframe


# =============================================================================
# VM Helper Functions - RK Macros
# =============================================================================

from .lopcodes import LFIELDS_PER_FLUSH

def _RKB(L: 'LuaState', i: int, base: int, k: list) -> TValue:
    """
    lvm.c:727 - #define RKB(i) check_exp(getBMode(GET_OPCODE(i)) == OpArgK, \
        ISK(GETARG_B(i)) ? k+INDEXK(GETARG_B(i)) : base+GETARG_B(i))
    Get RK value for B argument
    """
    b = GETARG_B(i)
    if ISK(b):
        return k[INDEXK(b)]
    return L.stack[base + b]


def _RKC(L: 'LuaState', i: int, base: int, k: list) -> TValue:
    """
    lvm.c:729 - #define RKC(i) check_exp(getCMode(GET_OPCODE(i)) == OpArgK, \
        ISK(GETARG_C(i)) ? k+INDEXK(GETARG_C(i)) : base+GETARG_C(i))
    Get RK value for C argument
    """
    c = GETARG_C(i)
    if ISK(c):
        return k[INDEXK(c)]
    return L.stack[base + c]


# =============================================================================
# VM Helper Functions - Table Access
# =============================================================================

def _gettable(L: 'LuaState', t: TValue, key: TValue, ra: int) -> None:
    """
    lvm.c:67-69 / lvm.c:774-776 - Get value from table
    
    Source: lvm.c:67-69 (luaV_gettable macro)
    """
    if ttistable(t):
        tab = hvalue(t)
        # Try to get from table
        result = _luaH_get(tab, key)
        if result is not None and not ttisnil(result):
            setobj2s(L, L.stack[ra], result)
            return
        # Key not found - pass the nil result as slot to indicate t is a table
        luaV_finishget(L, t, key, ra, result if result is not None else TValue())
    else:
        # Not a table - slot is None
        luaV_finishget(L, t, key, ra, None)


def _settable(L: 'LuaState', t: TValue, key: TValue, val: TValue) -> None:
    """
    lvm.c:90-92 / lvm.c:780-782 - Set value in table
    
    Source: lvm.c:90-92 (luaV_settable macro)
    """
    if ttistable(t):
        tab = hvalue(t)
        # Check if key exists - if so, just set it
        existing = _luaH_get(tab, key)
        if existing is not None and not ttisnil(existing):
            _luaH_set(L, tab, key, val)
            return
        # Key doesn't exist - check for __newindex metamethod
        if tab.metatable is not None:
            luaV_finishset(L, t, key, val, TValue())  # Pass non-None slot
        else:
            # No metatable, just set
            _luaH_set(L, tab, key, val)
        return
    # Not a table - try metamethod
    luaV_finishset(L, t, key, val, None)


def _luaH_get(t: 'Table', key: TValue) -> Optional[TValue]:
    """
    ltable.c - Get value from table (simplified)
    """
    from .lobject import TString
    
    if ttisnil(key):
        return None
    
    # Check for integer key (including float that represents integer)
    int_key = None
    if ttisinteger(key):
        int_key = ivalue(key)
    elif ttisfloat(key):
        f = fltvalue(key)
        if f == int(f) and abs(f) < 2**63:
            int_key = int(f)
    
    if int_key is not None and 1 <= int_key <= t.sizearray:
        return t.array[int_key - 1]
    
    # Get key data for string comparison
    key_data = None
    if ttisstring(key):
        gc = val_(key).gc
        if isinstance(gc, TString):
            key_data = gc.data
        elif hasattr(gc, 'data'):
            key_data = gc.data
    
    # Search in hash part
    if hasattr(t, 'node') and t.node:
        for node in t.node:
            # Node uses i_key (TKey) and i_val (TValue)
            node_key = node.i_key
            if node_key is None or node_key.tt_ == 0:  # nil key
                continue
            
            # Compare string keys
            if key_data is not None:
                node_gc = node_key.value_.gc
                if isinstance(node_gc, TString) and node_gc.data == key_data:
                    return node.i_val
                if hasattr(node_gc, 'data') and node_gc.data == key_data:
                    return node.i_val
            
            # General equality check - create TValue wrapper for comparison
            node_tv = TValue()
            node_tv.value_ = node_key.value_
            node_tv.tt_ = node_key.tt_
            if _values_equal(node_tv, key):
                return node.i_val
    
    return None


def _values_equal(a: TValue, b: TValue) -> bool:
    """Compare two TValues for equality"""
    from .lobject import TString
    
    if a.tt_ != b.tt_:
        return False
    
    if ttisnil(a):
        return True
    
    if ttisinteger(a):
        return a.value_.i == b.value_.i
    
    if ttisfloat(a):
        return a.value_.n == b.value_.n
    
    if ttisstring(a):
        gc_a = val_(a).gc
        gc_b = val_(b).gc
        if isinstance(gc_a, TString) and isinstance(gc_b, TString):
            return gc_a.data == gc_b.data
        if hasattr(gc_a, 'data') and hasattr(gc_b, 'data'):
            return gc_a.data == gc_b.data
    
    return val_(a).gc is val_(b).gc


def _luaH_set(L: 'LuaState', t: 'Table', key: TValue, val: TValue) -> None:
    """
    ltable.c - Set value in table (simplified)
    """
    from .lobject import TString, Node
    
    if ttisnil(key):
        raise RuntimeError("table index is nil")
    
    # Check for integer key (including float that represents integer)
    int_key = None
    if ttisinteger(key):
        int_key = ivalue(key)
    elif ttisfloat(key):
        f = fltvalue(key)
        if f == int(f) and abs(f) < 2**63:
            int_key = int(f)
    
    if int_key is not None and int_key >= 1:
        # Use array part
        while int_key > t.sizearray:
            t.array.append(TValue())
            t.sizearray = len(t.array)
        setobj(L, t.array[int_key - 1], val)
        return
    
    # Use hash part
    if not hasattr(t, 'node') or t.node is None:
        t.node = []
    
    # Get key data for string comparison
    key_data = None
    if ttisstring(key):
        gc = val_(key).gc
        if isinstance(gc, TString):
            key_data = gc.data
        elif hasattr(gc, 'data'):
            key_data = gc.data
    
    # Find existing key (Node uses i_key and i_val)
    for node in t.node:
        node_key = node.i_key
        if node_key is None or node_key.tt_ == 0:  # nil key
            continue
        
        if key_data is not None:
            node_gc = node_key.value_.gc
            if isinstance(node_gc, TString) and node_gc.data == key_data:
                setobj(L, node.i_val, val)
                return
            if hasattr(node_gc, 'data') and node_gc.data == key_data:
                setobj(L, node.i_val, val)
                return
        
        # General equality check
        node_tv = TValue()
        node_tv.value_ = node_key.value_
        node_tv.tt_ = node_key.tt_
        if _values_equal(node_tv, key):
            setobj(L, node.i_val, val)
            return
    
    # Add new key (use i_key and i_val)
    # Must copy the key's Value to avoid sharing (stack values can change)
    from .lobject import TKey, Value
    node = Node()
    node.i_key = TKey()
    # Copy value fields individually to avoid sharing the Value object
    old_val = key.value_
    new_val = Value()
    new_val.gc = old_val.gc
    new_val.p = old_val.p
    new_val.b = old_val.b
    new_val.f = old_val.f
    new_val.i = old_val.i
    new_val.n = old_val.n
    node.i_key.value_ = new_val
    node.i_key.tt_ = key.tt_
    node.i_key.next = 0
    node.i_val = TValue()
    setobj(L, node.i_val, val)
    t.node.append(node)


# =============================================================================
# VM Helper Functions - Closure Creation
# =============================================================================

def _pushclosure(L: 'LuaState', p: 'Proto', encup: list, base: int, ra: int) -> 'LClosure':
    """
    lvm.c:580-616 - pushclosure - Create and initialize a new closure
    
    Source: lvm.c:580-616
    """
    from .lfunc import luaF_newLclosure
    from .lobject import UpVal
    
    # Use len(p.upvalues) instead of p.sizeupvalues (which may not be set correctly)
    nup = len(p.upvalues) if p.upvalues else 0
    
    ncl = luaF_newLclosure(L, nup)
    ncl.p = p
    
    # Initialize upvalues
    for i in range(nup):
        if p.upvalues[i].instack:
            # Upvalue refers to local variable in enclosing function
            idx = base + p.upvalues[i].idx
            # Find or create open upvalue
            uv = _findupval(L, idx)
            ncl.upvals[i] = uv
        else:
            # Upvalue refers to enclosing function's upvalue
            upidx = p.upvalues[i].idx
            if encup and upidx < len(encup):
                ncl.upvals[i] = encup[upidx]
            else:
                # Fallback: create a nil upvalue
                uv = UpVal()
                uv.v = TValue()
                setnilvalue(uv.v)
                ncl.upvals[i] = uv
    
    # Cache closure
    p.cache = ncl
    
    return ncl


def _findupval(L: 'LuaState', level: int) -> 'UpVal':
    """
    Find or create an upvalue pointing to stack level
    """
    from .lobject import UpVal, UpValRef
    
    # Helper to get stack index from upvalue
    def get_stack_index(uv):
        if isinstance(uv.v, UpValRef):
            return uv.v.stack_index if uv.v.is_open else -1
        elif isinstance(uv.v, int):
            return uv.v
        return -1
    
    # Search existing open upvalues
    pp = L.openupval
    while pp is not None:
        if get_stack_index(pp) == level:
            return pp
        pp = getattr(pp, 'next', None)
    
    # Create new upvalue with UpValRef for type safety
    uv = UpVal()
    uv.v = UpValRef.from_stack(level)  # Points to stack slot
    uv.refcount = 1
    uv.next = L.openupval
    L.openupval = uv
    
    return uv


# =============================================================================
# VM Helper Functions - luaV_finishget/set
# =============================================================================

def luaV_finishget(L: 'LuaState', t: TValue, key: TValue, val: int, slot: Optional[TValue]) -> None:
    """
    lvm.h:101-102 / lvm.c:160-193 - Finish the table access 'val = t[key]'
    
    Source: lvm.c:160-193
    """
    # Track whether 't' is a table (slot not None means t is a table)
    is_table = slot is not None
    
    for loop in range(MAXTAGLOOP):
        if not is_table:  # 't' is not a table
            tm = luaT_gettmbyobj(L, t, TMS.TM_INDEX)
            if ttisnil(tm):
                raise TypeError(f"attempt to index a {ttypename(ttnov(t))} value")
        else:  # 't' is a table
            tm = fasttm(L, hvalue(t).metatable, TMS.TM_INDEX)
            if tm is None:
                # No __index metamethod, return nil
                setnilvalue(L.stack[val])
                return
        
        if ttisfunction(tm):
            # Call metamethod
            luaT_callTM(L, tm, t, key, L.stack[val], 1)
            return
        
        # __index is a table, use it as the new 't'
        t = tm
        if ttistable(t):
            is_table = True
            result = _luaH_get(hvalue(t), key)
            if result is not None and not ttisnil(result):
                setobj2s(L, L.stack[val], result)
                return
            # Key not found in __index table, continue loop
        else:
            is_table = False
    
    raise RuntimeError("'__index' chain too long; possible loop")


def luaV_finishset(L: 'LuaState', t: TValue, key: TValue, val: TValue, slot: Optional[TValue]) -> None:
    """
    lvm.h:103-104 / lvm.c:196-248 - Finish a table assignment 't[key] = val'
    
    Source: lvm.c:196-248
    """
    # Track whether 't' is a table
    is_table = slot is not None
    
    for loop in range(MAXTAGLOOP):
        if is_table:  # 't' is a table
            tm = fasttm(L, hvalue(t).metatable, TMS.TM_NEWINDEX)
            if tm is None:
                # No metamethod, do raw set
                _luaH_set(L, hvalue(t), key, val)
                return
        else:
            tm = luaT_gettmbyobj(L, t, TMS.TM_NEWINDEX)
            if ttisnil(tm):
                raise TypeError(f"attempt to index a {ttypename(ttnov(t))} value")
        
        if ttisfunction(tm):
            luaT_callTM(L, tm, t, key, val, 0)
            return
        
        # __newindex is a table
        t = tm
        if ttistable(t):
            is_table = True
            existing = _luaH_get(hvalue(t), key)
            if existing is not None and not ttisnil(existing):
                # Found existing slot, set it
                _luaH_set(L, hvalue(t), key, val)
                return
            # Key doesn't exist, continue loop
        else:
            is_table = False
    
    raise RuntimeError("'__newindex' chain too long; possible loop")


def luaV_finishOp(L: 'LuaState') -> None:
    """
    lvm.c:656-711 - Finish execution of an opcode interrupted by yield
    
    Source: lvm.c:656-711
    """
    from .lopcodes import OpCode, GETARG_A, GETARG_B, GET_OPCODE
    
    ci = L.ci
    base = ci.base
    
    # Get interrupted instruction
    inst = getproto(L.stack[ci.func]).code[ci.savedpc - 1]
    op = GET_OPCODE(inst)
    
    # Finish execution based on opcode
    if op in (OpCode.OP_ADD, OpCode.OP_SUB, OpCode.OP_MUL, OpCode.OP_DIV,
              OpCode.OP_IDIV, OpCode.OP_BAND, OpCode.OP_BOR, OpCode.OP_BXOR,
              OpCode.OP_SHL, OpCode.OP_SHR, OpCode.OP_MOD, OpCode.OP_POW,
              OpCode.OP_UNM, OpCode.OP_BNOT, OpCode.OP_LEN,
              OpCode.OP_GETTABUP, OpCode.OP_GETTABLE, OpCode.OP_SELF):
        # Move result to destination register
        L.top -= 1
        setobjs2s(L, L.stack[base + GETARG_A(inst)], L.stack[L.top])
    
    elif op in (OpCode.OP_LE, OpCode.OP_LT, OpCode.OP_EQ):
        # Handle comparison result
        from .lstate import CIST_LEQ
        res = not l_isfalse(L.stack[L.top - 1])
        L.top -= 1
        if ci.callstatus & CIST_LEQ:
            ci.callstatus &= ~CIST_LEQ
            res = not res
        # Check if condition matches expected
        if res != GETARG_A(inst):
            ci.savedpc += 1  # Skip jump
    
    elif op == OpCode.OP_CONCAT:
        # Handle concatenation result
        top = L.top - 1
        b = GETARG_B(inst)
        total = top - 1 - (base + b)
        setobjs2s(L, L.stack[top - 2], L.stack[top])
        if total > 1:
            L.top = top - 1
            luaV_concat(L, total)
        setobjs2s(L, L.stack[base + GETARG_A(inst)], L.stack[L.top - 1])
        L.top = ci.top
    
    elif op == OpCode.OP_TFORCALL:
        L.top = ci.top
    
    elif op == OpCode.OP_CALL:
        from .lopcodes import GETARG_C
        if GETARG_C(inst) - 1 >= 0:
            L.top = ci.top


# =============================================================================
# Import additional helpers for ltm
# =============================================================================

from .ltm import luaT_callTM, ttypename
from .lobject import ttnov


# =============================================================================
# High-level execution helpers
# =============================================================================

def execute_lua(source: str, name: str = "=python") -> None:
    """
    Compile and execute Lua source code.
    
    This is a high-level helper function that:
    1. Compiles the source code
    2. Creates a LuaState
    3. Loads standard libraries
    4. Executes the compiled bytecode
    
    Args:
        source: Lua source code to execute
        name: Name for error messages (default "=python")
    
    Raises:
        SyntaxError: If compilation fails
        RuntimeError: If execution fails
    """
    from .compile import compile_source
    from .lstate import lua_newstate
    from .ldo import luaD_call
    from .lobject import setclLvalue
    from .lbaselib import luaopen_base
    from .lstrlib import luaopen_string
    from .ltablib import luaopen_table
    from .lmathlib import luaopen_math
    from .liolib import luaopen_io
    from .lcorolib import luaopen_coroutine
    
    # Compile source
    cl, error = compile_source(source, name)
    if cl is None:
        raise SyntaxError(f"Compilation error: {error}")
    
    # Create state with default allocator
    def default_alloc(ud, ptr, osize, nsize):
        # Python handles memory, just return a dummy
        return object() if nsize > 0 else None
    
    L = lua_newstate(default_alloc, None)
    
    # Create global environment table
    from .lobject import Table
    env = Table()
    env.node = []
    env.array = []
    env.metatable = None
    
    # Store in registry
    from .lstate import G
    G(L).l_registry = env
    
    # Load standard libraries
    luaopen_base(L, env)
    try:
        luaopen_string(L)
    except:
        pass
    try:
        luaopen_table(L)
    except:
        pass
    try:
        luaopen_math(L)
    except:
        pass
    try:
        luaopen_io(L)
    except:
        pass
    try:
        luaopen_coroutine(L)
    except:
        pass
    
    # Set up upvalue[0] to point to _ENV (global environment)
    from .lobject import UpVal
    
    # Create upvalue pointing to global environment
    uv = UpVal()
    uv.v = TValue()
    uv.v.tt_ = 69  # LUA_TTABLE | BIT_ISCOLLECTABLE
    uv.v.value_ = Value()
    uv.v.value_.gc = env
    
    # Replace or set upvals[0]
    if cl.upvals is None or len(cl.upvals) == 0:
        cl.upvals = [uv]
    else:
        cl.upvals[0] = uv
    
    # Push closure onto stack
    setclLvalue(L, L.stack[L.top], cl)
    L.top += 1
    
    # Execute
    try:
        luaD_call(L, L.top - 1, 0)
    except Exception as e:
        raise RuntimeError(f"Execution error: {e}")
