# -*- coding: utf-8 -*-
"""
test_pylua.py - Comprehensive test suite for PyLua implementation

Run with: py utils/test_pylua.py

Author: aixiasang
"""

import sys
import os
import math

# Add pylua to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylua.lvm import (
    tonumber, tointeger, luaV_tonumber_, luaV_tointeger,
    luaV_div, luaV_mod, luaV_shiftl,
    intop_add, intop_sub, intop_mul, intop_band, intop_bor, intop_bxor,
    l_strcmp, LTintfloat, LEintfloat, LTnum, LEnum,
    luaV_equalobj, luaV_lessthan, luaV_lessequal,
    forlimit, l_intfitsf,
)
from pylua.lobject import (
    TValue, Value, setivalue, setfltvalue, setsvalue, setnilvalue, setbvalue,
    ttisinteger, ttisfloat, ttisnumber, ttisstring, ttisnil, ttisboolean,
    ivalue, fltvalue, bvalue, svalue, TString, LUA_TSHRSTR,
)
from pylua.llimits import (
    luai_numadd, luai_numsub, luai_nummul, luai_nummod,
    luai_numpow, luai_numdiv, luai_numidiv, luai_numunm,
    luai_numlt, luai_numle, luai_numeq, luai_numisnan,
    l_castS2U, l_castU2S,
)
from pylua.luaconf import LUA_MAXINTEGER, LUA_MININTEGER

# Test counters
passed = 0
failed = 0

def test(name, condition, expected=None, got=None):
    """Run a single test"""
    global passed, failed
    if condition:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}")
        if expected is not None:
            print(f"  Expected: {expected}")
            print(f"  Got: {got}")

def make_int(v):
    """Create a TValue with integer"""
    tv = TValue()
    setivalue(tv, v)
    return tv

def make_float(v):
    """Create a TValue with float"""
    tv = TValue()
    setfltvalue(tv, v)
    return tv

def make_string(s):
    """Create a TValue with string"""
    from pylua.lobject import ctb
    tv = TValue()
    ts = TString()
    ts.tt = LUA_TSHRSTR
    if isinstance(s, str):
        ts.data = s.encode('utf-8')
    else:
        ts.data = s
    ts.shrlen = len(ts.data)
    tv.value_.gc = ts
    tv.tt_ = ctb(LUA_TSHRSTR)
    return tv

def make_nil():
    """Create a nil TValue"""
    tv = TValue()
    setnilvalue(tv)
    return tv

def make_bool(v):
    """Create a boolean TValue"""
    tv = TValue()
    setbvalue(tv, 1 if v else 0)
    return tv


print("=== PyLua Implementation Test Suite ===")
print()

# ============================================================================
# 1. Integer Operations Tests
# ============================================================================
print("\n--- Integer Operations ---")

test("intop_add", intop_add(1, 2) == 3, 3, intop_add(1, 2))
test("intop_add neg", intop_add(-5, 3) == -2, -2, intop_add(-5, 3))
test("intop_sub", intop_sub(5, 3) == 2, 2, intop_sub(5, 3))
test("intop_sub neg", intop_sub(3, 5) == -2, -2, intop_sub(3, 5))
test("intop_mul", intop_mul(4, 5) == 20, 20, intop_mul(4, 5))
test("intop_mul neg", intop_mul(-4, 5) == -20, -20, intop_mul(-4, 5))

# Integer division (Lua floor semantics)
test("luaV_div pos", luaV_div(None, 10, 3) == 3, 3, luaV_div(None, 10, 3))
test("luaV_div neg floor", luaV_div(None, -10, 3) == -4, -4, luaV_div(None, -10, 3))
test("luaV_div neg2", luaV_div(None, 10, -3) == -4, -4, luaV_div(None, 10, -3))
test("luaV_div neg neg", luaV_div(None, -10, -3) == 3, 3, luaV_div(None, -10, -3))

# Integer modulo (Lua semantics)
test("luaV_mod pos", luaV_mod(None, 10, 3) == 1, 1, luaV_mod(None, 10, 3))
test("luaV_mod neg", luaV_mod(None, -10, 3) == 2, 2, luaV_mod(None, -10, 3))  # Lua: -10 % 3 = 2
test("luaV_mod neg2", luaV_mod(None, 10, -3) == -2, -2, luaV_mod(None, 10, -3))  # Lua: 10 % -3 = -2

# Division by -1 (overflow case)
test("luaV_div -1", luaV_div(None, LUA_MININTEGER, -1) == LUA_MININTEGER, 
     LUA_MININTEGER, luaV_div(None, LUA_MININTEGER, -1))
test("luaV_mod -1", luaV_mod(None, LUA_MININTEGER, -1) == 0, 0, 
     luaV_mod(None, LUA_MININTEGER, -1))


# ============================================================================
# 2. Bitwise Operations Tests
# ============================================================================
print("\n--- Bitwise Operations ---")

test("intop_band", intop_band(0xFF, 0x0F) == 0x0F, 0x0F, intop_band(0xFF, 0x0F))
test("intop_bor", intop_bor(0xF0, 0x0F) == 0xFF, 0xFF, intop_bor(0xF0, 0x0F))
test("intop_bxor", intop_bxor(0xFF, 0x0F) == 0xF0, 0xF0, intop_bxor(0xFF, 0x0F))
test("bnot", intop_bxor(~0, 0) == -1, -1, intop_bxor(~0, 0))

# Shifts
test("shl", luaV_shiftl(1, 4) == 16, 16, luaV_shiftl(1, 4))
test("shr", luaV_shiftl(16, -2) == 4, 4, luaV_shiftl(16, -2))
test("neg shl", luaV_shiftl(16, -2) == 4, 4, luaV_shiftl(16, -2))
test("neg shr", luaV_shiftl(1, 4) == 16, 16, luaV_shiftl(1, 4))
test("shl overflow", luaV_shiftl(1, 64) == 0, 0, luaV_shiftl(1, 64))
test("shr overflow", luaV_shiftl(1, -64) == 0, 0, luaV_shiftl(1, -64))


# ============================================================================
# 3. Float Operations Tests
# ============================================================================
print("\n--- Float Operations ---")

test("luai_numadd", luai_numadd(None, 1.5, 2.5) == 4.0, 4.0, luai_numadd(None, 1.5, 2.5))
test("luai_numsub", luai_numsub(None, 5.5, 3.0) == 2.5, 2.5, luai_numsub(None, 5.5, 3.0))
test("luai_nummul", luai_nummul(None, 2.5, 4.0) == 10.0, 10.0, luai_nummul(None, 2.5, 4.0))
test("luai_numdiv", luai_numdiv(None, 10.0, 4.0) == 2.5, 2.5, luai_numdiv(None, 10.0, 4.0))
test("luai_numidiv", luai_numidiv(None, 10.0, 3.0) == 3.0, 3.0, luai_numidiv(None, 10.0, 3.0))
test("luai_numpow", luai_numpow(None, 2.0, 3.0) == 8.0, 8.0, luai_numpow(None, 2.0, 3.0))
test("luai_numunm", luai_numunm(None, 5.0) == -5.0, -5.0, luai_numunm(None, 5.0))

# Float modulo
m = luai_nummod(None, 10.5, 3.0)
test("luai_nummod", abs(m - 1.5) < 0.0001, 1.5, m)

# Negative modulo (Lua semantics)
m = luai_nummod(None, -10.0, 3.0)
test("luai_nummod neg", abs(m - 2.0) < 0.0001, 2.0, m)


# ============================================================================
# 4. TValue tonumber/tointeger Tests
# ============================================================================
print("\n--- TValue Conversion ---")

# tonumber
tv_int = make_int(42)
ok, n = tonumber(tv_int)
test("tonumber int", ok and n == 42.0, 42.0, n)

tv_flt = make_float(3.14)
ok, n = tonumber(tv_flt)
test("tonumber float", ok and abs(n - 3.14) < 0.0001, 3.14, n)

# tointeger
tv_int = make_int(42)
ok, i = tointeger(tv_int)
test("tointeger int", ok and i == 42, 42, i)

tv_flt = make_float(3.0)  # Exact integer
ok, i = tointeger(tv_flt)
test("tointeger float exact", ok and i == 3, 3, i)

tv_flt = make_float(3.5)  # Not exact - should fail with mode 0
ok, i = tointeger(tv_flt, 0)
test("tointeger float non-exact", not ok, False, ok)


# ============================================================================
# 5. String Comparison Tests
# ============================================================================
print("\n--- String Comparison ---")

test("l_strcmp eq", l_strcmp(b"abc", b"abc") == 0, 0, l_strcmp(b"abc", b"abc"))
test("l_strcmp lt", l_strcmp(b"abc", b"abd") < 0, True, l_strcmp(b"abc", b"abd") < 0)
test("l_strcmp gt", l_strcmp(b"abd", b"abc") > 0, True, l_strcmp(b"abd", b"abc") > 0)
test("l_strcmp prefix", l_strcmp(b"abc", b"abcd") < 0, True, l_strcmp(b"abc", b"abcd") < 0)
test("l_strcmp empty", l_strcmp(b"", b"a") < 0, True, l_strcmp(b"", b"a") < 0)


# ============================================================================
# 6. Numeric Comparison Functions Tests
# ============================================================================
print("\n--- Numeric Comparison Functions ---")

# l_intfitsf tests
test("l_intfitsf small", l_intfitsf(1000), True, l_intfitsf(1000))
test("l_intfitsf max53", l_intfitsf(2**53), True, l_intfitsf(2**53))
test("l_intfitsf over53", not l_intfitsf(2**54), True, not l_intfitsf(2**54))

# LTintfloat tests
test("LTintfloat true", LTintfloat(3, 3.5), True, LTintfloat(3, 3.5))
test("LTintfloat false", not LTintfloat(4, 3.5), True, not LTintfloat(4, 3.5))
test("LTintfloat eq false", not LTintfloat(3, 3.0), True, not LTintfloat(3, 3.0))

# LEintfloat tests
test("LEintfloat true lt", LEintfloat(3, 3.5), True, LEintfloat(3, 3.5))
test("LEintfloat true eq", LEintfloat(3, 3.0), True, LEintfloat(3, 3.0))
test("LEintfloat false", not LEintfloat(4, 3.5), True, not LEintfloat(4, 3.5))

# LTnum tests
tv1, tv2 = make_int(3), make_int(5)
test("LTnum int lt", LTnum(tv1, tv2), True, LTnum(tv1, tv2))
test("LTnum int not lt", not LTnum(tv2, tv1), True, not LTnum(tv2, tv1))

tv1, tv2 = make_float(2.5), make_float(3.5)
test("LTnum float lt", LTnum(tv1, tv2), True, LTnum(tv1, tv2))

tv1, tv2 = make_int(3), make_float(3.5)
test("LTnum mixed int<float", LTnum(tv1, tv2), True, LTnum(tv1, tv2))

tv1, tv2 = make_float(2.5), make_int(3)
test("LTnum mixed float<int", LTnum(tv1, tv2), True, LTnum(tv1, tv2))

# LEnum tests
tv1, tv2 = make_int(3), make_int(3)
test("LEnum int eq", LEnum(tv1, tv2), True, LEnum(tv1, tv2))

tv1, tv2 = make_int(3), make_float(3.0)
test("LEnum mixed eq", LEnum(tv1, tv2), True, LEnum(tv1, tv2))


# ============================================================================
# 7. luaV_equalobj Tests
# ============================================================================
print("\n--- luaV_equalobj Tests ---")

# Nil equality
tv1, tv2 = make_nil(), make_nil()
test("equalobj nil", luaV_equalobj(None, tv1, tv2), True, luaV_equalobj(None, tv1, tv2))

# Integer equality
tv1, tv2 = make_int(42), make_int(42)
test("equalobj int eq", luaV_equalobj(None, tv1, tv2), True, luaV_equalobj(None, tv1, tv2))

tv1, tv2 = make_int(42), make_int(43)
test("equalobj int neq", not luaV_equalobj(None, tv1, tv2), True, not luaV_equalobj(None, tv1, tv2))

# Float equality
tv1, tv2 = make_float(3.14), make_float(3.14)
test("equalobj float eq", luaV_equalobj(None, tv1, tv2), True, luaV_equalobj(None, tv1, tv2))

# Mixed int/float equality
tv1, tv2 = make_int(5), make_float(5.0)
test("equalobj int-float eq", luaV_equalobj(None, tv1, tv2), True, luaV_equalobj(None, tv1, tv2))

tv1, tv2 = make_float(5.0), make_int(5)
test("equalobj float-int eq", luaV_equalobj(None, tv1, tv2), True, luaV_equalobj(None, tv1, tv2))

tv1, tv2 = make_int(5), make_float(5.5)
test("equalobj int-float neq", not luaV_equalobj(None, tv1, tv2), True, not luaV_equalobj(None, tv1, tv2))

# String equality
tv1, tv2 = make_string("hello"), make_string("hello")
test("equalobj str eq", luaV_equalobj(None, tv1, tv2), True, luaV_equalobj(None, tv1, tv2))

tv1, tv2 = make_string("hello"), make_string("world")
test("equalobj str neq", not luaV_equalobj(None, tv1, tv2), True, not luaV_equalobj(None, tv1, tv2))

# Boolean equality
tv1, tv2 = make_bool(True), make_bool(True)
test("equalobj bool eq", luaV_equalobj(None, tv1, tv2), True, luaV_equalobj(None, tv1, tv2))

tv1, tv2 = make_bool(True), make_bool(False)
test("equalobj bool neq", not luaV_equalobj(None, tv1, tv2), True, not luaV_equalobj(None, tv1, tv2))

# Different types
tv1, tv2 = make_int(5), make_string("5")
test("equalobj type diff", not luaV_equalobj(None, tv1, tv2), True, not luaV_equalobj(None, tv1, tv2))


# ============================================================================
# 8. forlimit Tests
# ============================================================================
print("\n--- forlimit Tests ---")

# Integer limit
tv = make_int(10)
ok, limit, stop = forlimit(tv, 1)
test("forlimit int", ok and limit == 10 and not stop, (True, 10, False), (ok, limit, stop))

# Float limit with positive step (floor)
tv = make_float(10.5)
ok, limit, stop = forlimit(tv, 1)
test("forlimit float floor", ok and limit == 10, (True, 10, None), (ok, limit, stop))

# Float limit with negative step (ceil)
tv = make_float(10.5)
ok, limit, stop = forlimit(tv, -1)
test("forlimit float ceil", ok and limit == 11, (True, 11, None), (ok, limit, stop))

# Large float (beyond integer range)
tv = make_float(1e100)
ok, limit, stop = forlimit(tv, 1)
test("forlimit large float", ok and limit == LUA_MAXINTEGER, (True, LUA_MAXINTEGER, None), (ok, limit, stop))


# ============================================================================
# 9. Cast Functions Tests
# ============================================================================
print("\n--- Cast Functions ---")

test("l_castS2U positive", l_castS2U(5) == 5, 5, l_castS2U(5))
test("l_castS2U negative", l_castS2U(-1) == (1 << 64) - 1, (1 << 64) - 1, l_castS2U(-1))

test("l_castU2S small", l_castU2S(5) == 5, 5, l_castU2S(5))
test("l_castU2S large", l_castU2S((1 << 64) - 1) == -1, -1, l_castU2S((1 << 64) - 1))


# ============================================================================
# Summary
# ============================================================================
print("\n=== Test Summary ===")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Total: {passed + failed}")

if failed > 0:
    print("\nSome tests failed!")
    sys.exit(1)
else:
    print("\nAll tests passed!")
    sys.exit(0)
