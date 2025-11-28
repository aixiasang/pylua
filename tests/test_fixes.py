# -*- coding: utf-8 -*-
"""
test_fixes.py - Test cases for bug fixes
========================================

Tests for:
1. Integer overflow handling (64-bit two's complement)
2. String interning
3. Float formatting
4. UpVal type consistency
5. ldump compatibility
"""

import sys
import os
import struct

# Add pylua to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest


class TestIntegerOverflow(unittest.TestCase):
    """Test integer overflow handling with 64-bit two's complement"""
    
    def test_l_castS2U_positive(self):
        """Test l_castS2U with positive numbers"""
        from pylua.llimits import l_castS2U
        
        self.assertEqual(l_castS2U(0), 0)
        self.assertEqual(l_castS2U(1), 1)
        self.assertEqual(l_castS2U(0x7FFFFFFFFFFFFFFF), 0x7FFFFFFFFFFFFFFF)
    
    def test_l_castS2U_negative(self):
        """Test l_castS2U with negative numbers"""
        from pylua.llimits import l_castS2U
        
        # -1 in 64-bit two's complement is 0xFFFFFFFFFFFFFFFF
        self.assertEqual(l_castS2U(-1), 0xFFFFFFFFFFFFFFFF)
        # -2 is 0xFFFFFFFFFFFFFFFE
        self.assertEqual(l_castS2U(-2), 0xFFFFFFFFFFFFFFFE)
        # LUA_MININTEGER (-2^63) should become 2^63
        self.assertEqual(l_castS2U(-0x8000000000000000), 0x8000000000000000)
    
    def test_l_castU2S_positive(self):
        """Test l_castU2S with small unsigned numbers"""
        from pylua.llimits import l_castU2S
        
        self.assertEqual(l_castU2S(0), 0)
        self.assertEqual(l_castU2S(1), 1)
        self.assertEqual(l_castU2S(0x7FFFFFFFFFFFFFFF), 0x7FFFFFFFFFFFFFFF)
    
    def test_l_castU2S_large(self):
        """Test l_castU2S with large unsigned numbers (should become negative)"""
        from pylua.llimits import l_castU2S
        
        # 0xFFFFFFFFFFFFFFFF should become -1
        self.assertEqual(l_castU2S(0xFFFFFFFFFFFFFFFF), -1)
        # 0x8000000000000000 should become -2^63
        self.assertEqual(l_castU2S(0x8000000000000000), -0x8000000000000000)
    
    def test_intop_add_overflow(self):
        """Test integer addition with overflow"""
        from pylua.lvm import intop_add
        from pylua.luaconf import LUA_MAXINTEGER, LUA_MININTEGER
        
        # MAX + 1 should wrap to MIN
        result = intop_add(LUA_MAXINTEGER, 1)
        self.assertEqual(result, LUA_MININTEGER)
        
        # MIN - 1 should wrap to MAX
        from pylua.lvm import intop_sub
        result = intop_sub(LUA_MININTEGER, 1)
        self.assertEqual(result, LUA_MAXINTEGER)
    
    def test_intop_mul_overflow(self):
        """Test integer multiplication with overflow"""
        from pylua.lvm import intop_mul
        
        # Large multiplication should wrap correctly
        result = intop_mul(0x100000000, 0x100000000)
        self.assertEqual(result, 0)  # Overflows to 0


class TestStringInterning(unittest.TestCase):
    """Test string interning functionality"""
    
    def test_basic_interning(self):
        """Test basic string interning"""
        from pylua.lstring import luaS_newlstr, get_interned_string, clear_string_table
        
        clear_string_table()
        
        # Create two strings with same content
        s1 = luaS_newlstr(None, b"hello", 5)
        s2 = luaS_newlstr(None, b"hello", 5)
        
        # They should be the same object
        self.assertIs(s1, s2)
    
    def test_different_strings(self):
        """Test that different strings are not interned together"""
        from pylua.lstring import luaS_newlstr, clear_string_table
        
        clear_string_table()
        
        s1 = luaS_newlstr(None, b"hello", 5)
        s2 = luaS_newlstr(None, b"world", 5)
        
        self.assertIsNot(s1, s2)
    
    def test_long_string_not_interned(self):
        """Test that long strings (>40 bytes) are not interned"""
        from pylua.lstring import luaS_newlstr, clear_string_table
        from pylua.llimits import LUAI_MAXSHORTLEN
        
        clear_string_table()
        
        # Create a long string
        long_content = b"x" * (LUAI_MAXSHORTLEN + 1)
        s1 = luaS_newlstr(None, long_content, len(long_content))
        s2 = luaS_newlstr(None, long_content, len(long_content))
        
        # Long strings should NOT be interned (different objects)
        self.assertIsNot(s1, s2)
    
    def test_hash_computation(self):
        """Test string hash computation"""
        from pylua.lstring import luaS_hash
        
        h1 = luaS_hash(b"hello")
        h2 = luaS_hash(b"hello")
        h3 = luaS_hash(b"world")
        
        # Same content should give same hash
        self.assertEqual(h1, h2)
        # Different content should (usually) give different hash
        self.assertNotEqual(h1, h3)


class TestFloatFormatting(unittest.TestCase):
    """Test float to string formatting"""
    
    def test_integer_format(self):
        """Test integer to string conversion"""
        from pylua.lobject import luaO_int2str
        
        self.assertEqual(luaO_int2str(0), "0")
        self.assertEqual(luaO_int2str(42), "42")
        self.assertEqual(luaO_int2str(-123), "-123")
    
    def test_float_format_basic(self):
        """Test float to string conversion"""
        from pylua.lobject import luaO_num2str
        
        # Floats that look like integers should have .0
        self.assertEqual(luaO_num2str(1.0), "1.0")
        self.assertEqual(luaO_num2str(-5.0), "-5.0")
        
        # Floats with fractional parts
        result = luaO_num2str(3.14)
        self.assertTrue('3.14' in result)
    
    def test_float_format_special(self):
        """Test special float values"""
        from pylua.lobject import luaO_num2str
        import math
        
        self.assertEqual(luaO_num2str(float('inf')), "inf")
        self.assertEqual(luaO_num2str(float('-inf')), "-inf")
        self.assertEqual(luaO_num2str(float('nan')), "nan")
    
    def test_looks_like_int(self):
        """Test _looks_like_int helper"""
        from pylua.lobject import _looks_like_int
        
        self.assertTrue(_looks_like_int("123"))
        self.assertTrue(_looks_like_int("-456"))
        self.assertFalse(_looks_like_int("1.5"))
        self.assertFalse(_looks_like_int("1e10"))


class TestUpValTypeConsistency(unittest.TestCase):
    """Test UpVal type consistency"""
    
    def test_upvalref_open(self):
        """Test UpValRef for open upvalues"""
        from pylua.lobject import UpValRef
        
        ref = UpValRef.from_stack(10)
        self.assertTrue(ref.is_open)
        self.assertEqual(ref.stack_index, 10)
    
    def test_upvalref_closed(self):
        """Test UpValRef for closed upvalues"""
        from pylua.lobject import UpValRef, TValue
        
        tv = TValue()
        ref = UpValRef.from_tvalue(tv)
        self.assertFalse(ref.is_open)
        self.assertIs(ref.tvalue, tv)
    
    def test_upisopen(self):
        """Test upisopen function with UpValRef"""
        from pylua.lobject import UpVal, UpValRef, TValue, upisopen
        
        # Open upvalue
        uv1 = UpVal()
        uv1.v = UpValRef.from_stack(5)
        self.assertTrue(upisopen(uv1))
        
        # Closed upvalue
        uv2 = UpVal()
        tv = TValue()
        uv2.v = UpValRef.from_tvalue(tv)
        uv2.value = tv
        self.assertFalse(upisopen(uv2))
    
    def test_upvalref_comparison(self):
        """Test UpValRef comparison for sorting"""
        from pylua.lobject import UpValRef
        
        ref1 = UpValRef.from_stack(5)
        ref2 = UpValRef.from_stack(10)
        
        self.assertTrue(ref1 < ref2)
        self.assertFalse(ref2 < ref1)
        self.assertEqual(ref1, 5)


class TestLdumpCompatibility(unittest.TestCase):
    """Test ldump bytecode format compatibility"""
    
    def test_header_format(self):
        """Test bytecode header matches Lua 5.3 format"""
        from pylua.ldump_compat import (
            LUA_SIGNATURE, LUAC_VERSION, LUAC_FORMAT, LUAC_DATA,
            SIZEOF_INT, SIZEOF_SIZE_T, SIZEOF_INSTRUCTION,
            SIZEOF_LUA_INTEGER, SIZEOF_LUA_NUMBER,
            LUAC_INT, LUAC_NUM
        )
        
        # Check signature
        self.assertEqual(LUA_SIGNATURE, b"\x1bLua")
        
        # Check version
        self.assertEqual(LUAC_VERSION, 0x53)
        self.assertEqual(LUAC_FORMAT, 0)
        
        # Check sizes for 64-bit
        self.assertEqual(SIZEOF_INT, 4)
        self.assertEqual(SIZEOF_SIZE_T, 8)
        self.assertEqual(SIZEOF_INSTRUCTION, 4)
        self.assertEqual(SIZEOF_LUA_INTEGER, 8)
        self.assertEqual(SIZEOF_LUA_NUMBER, 8)
        
        # Check test values
        self.assertEqual(LUAC_INT, 0x5678)
        self.assertEqual(LUAC_NUM, 370.5)
    
    def test_dump_integer(self):
        """Test integer dumping format"""
        from pylua.ldump_compat import DumpState, DumpInteger
        
        D = DumpState(None, None, None, 0)
        DumpInteger(0x5678, D)
        
        result = D.getvalue()
        # Should be 8 bytes, little-endian
        self.assertEqual(len(result), 8)
        value = struct.unpack('<q', result)[0]
        self.assertEqual(value, 0x5678)
    
    def test_dump_number(self):
        """Test float dumping format"""
        from pylua.ldump_compat import DumpState, DumpNumber
        
        D = DumpState(None, None, None, 0)
        DumpNumber(370.5, D)
        
        result = D.getvalue()
        # Should be 8 bytes, little-endian double
        self.assertEqual(len(result), 8)
        value = struct.unpack('<d', result)[0]
        self.assertEqual(value, 370.5)


class TestTableHash(unittest.TestCase):
    """Test table hash implementation"""
    
    def test_hash_int(self):
        """Test integer hashing"""
        from pylua.ltable import hashint
        from pylua.lobject import Table
        
        t = Table()
        t.lsizenode = 4  # Size = 2^4 = 16 nodes
        t.node = [None] * 16
        
        # Hash should be consistent
        h1 = hashint(t, 42)
        h2 = hashint(t, 42)
        self.assertEqual(h1, h2)
        
        # Hash should be in valid range
        self.assertTrue(0 <= h1 < 16)
    
    def test_hash_float(self):
        """Test float hashing"""
        from pylua.ltable import l_hashfloat
        
        # Same float should give same hash
        h1 = l_hashfloat(3.14)
        h2 = l_hashfloat(3.14)
        self.assertEqual(h1, h2)
        
        # Special cases
        self.assertEqual(l_hashfloat(float('nan')), 0)
        self.assertEqual(l_hashfloat(float('inf')), 0)


class TestLdebug(unittest.TestCase):
    """Test ldebug debug interface implementation"""
    
    def test_pcRel(self):
        """Test pcRel calculation"""
        from pylua.ldebug import pcRel
        from pylua.lobject import Proto
        
        p = Proto()
        p.code = [0] * 10
        
        # pcRel should return pc - 1
        self.assertEqual(pcRel(1, p), 0)
        self.assertEqual(pcRel(5, p), 4)
        self.assertEqual(pcRel(10, p), 9)
    
    def test_getfuncline(self):
        """Test getfuncline calculation"""
        from pylua.ldebug import getfuncline
        from pylua.lobject import Proto
        
        p = Proto()
        p.lineinfo = [1, 2, 3, 5, 5, 7]
        
        self.assertEqual(getfuncline(p, 0), 1)
        self.assertEqual(getfuncline(p, 2), 3)
        self.assertEqual(getfuncline(p, 5), 7)
        
        # Out of range
        self.assertEqual(getfuncline(p, 100), -1)
        
        # No lineinfo
        p2 = Proto()
        p2.lineinfo = None
        self.assertEqual(getfuncline(p2, 0), -1)
    
    def test_lua_Debug_struct(self):
        """Test lua_Debug structure"""
        from pylua.ldebug import lua_Debug
        
        ar = lua_Debug()
        
        # Default values
        self.assertEqual(ar.event, 0)
        self.assertIsNone(ar.name)
        self.assertEqual(ar.currentline, -1)
        self.assertEqual(ar.linedefined, 0)
        
        # Set values
        ar.name = "test_func"
        ar.what = "Lua"
        ar.currentline = 42
        
        self.assertEqual(ar.name, "test_func")
        self.assertEqual(ar.what, "Lua")
        self.assertEqual(ar.currentline, 42)
    
    def test_upvalname(self):
        """Test upvalname function"""
        from pylua.ldebug import upvalname
        from pylua.lobject import Proto, Upvaldesc, TString
        
        p = Proto()
        p.upvalues = []
        
        # Empty upvalues
        self.assertEqual(upvalname(p, 0), "?")
        
        # With named upvalue
        uv = Upvaldesc()
        ts = TString()
        ts.data = b"_ENV"
        uv.name = ts
        p.upvalues = [uv]
        
        self.assertEqual(upvalname(p, 0), "_ENV")
    
    def test_noLuaClosure(self):
        """Test noLuaClosure function"""
        from pylua.ldebug import noLuaClosure
        from pylua.lobject import LClosure, CClosure, LUA_TLCL, LUA_TCCL
        
        # None is considered not a Lua closure
        self.assertTrue(noLuaClosure(None))
        
        # CClosure is not a Lua closure
        cc = CClosure()
        cc.tt = LUA_TCCL
        self.assertTrue(noLuaClosure(cc))
        
        # LClosure is a Lua closure
        lc = LClosure()
        lc.tt = LUA_TLCL
        self.assertFalse(noLuaClosure(lc))
    
    def test_luaG_addinfo(self):
        """Test luaG_addinfo function"""
        from pylua.ldebug import luaG_addinfo
        from pylua.lobject import TString
        
        # Without source
        result = luaG_addinfo(None, "test error", None, 10)
        self.assertIn("?", result)
        self.assertIn("10", result)
        self.assertIn("test error", result)
        
        # With source
        src = TString()
        src.data = b"test.lua"
        result = luaG_addinfo(None, "syntax error", src, 42)
        self.assertIn("42", result)
        self.assertIn("syntax error", result)


class TestConstantFolding(unittest.TestCase):
    """Test constant folding optimization in lcode"""
    
    def test_integer_add_fold(self):
        """Test integer addition folding"""
        from pylua.lcode import constfolding
        from pylua.lparser import expdesc, VKINT
        
        e1 = expdesc()
        e1.k = VKINT
        e1.ival = 10
        
        e2 = expdesc()
        e2.k = VKINT
        e2.ival = 20
        
        # LUA_OPADD = 0
        result = constfolding(None, 0, e1, e2)
        
        self.assertTrue(result)
        self.assertEqual(e1.k, VKINT)
        self.assertEqual(e1.ival, 30)
    
    def test_float_mul_fold(self):
        """Test float multiplication folding"""
        from pylua.lcode import constfolding
        from pylua.lparser import expdesc, VKFLT
        
        e1 = expdesc()
        e1.k = VKFLT
        e1.nval = 2.5
        
        e2 = expdesc()
        e2.k = VKFLT
        e2.nval = 4.0
        
        # LUA_OPMUL = 2
        result = constfolding(None, 2, e1, e2)
        
        self.assertTrue(result)
        self.assertEqual(e1.k, VKFLT)
        self.assertEqual(e1.nval, 10.0)
    
    def test_div_always_float(self):
        """Test that division always returns float"""
        from pylua.lcode import constfolding
        from pylua.lparser import expdesc, VKINT, VKFLT
        
        e1 = expdesc()
        e1.k = VKINT
        e1.ival = 10
        
        e2 = expdesc()
        e2.k = VKINT
        e2.ival = 4
        
        # LUA_OPDIV = 5 - always returns float
        result = constfolding(None, 5, e1, e2)
        
        self.assertTrue(result)
        self.assertEqual(e1.k, VKFLT)
        self.assertEqual(e1.nval, 2.5)
    
    def test_div_by_zero_no_fold(self):
        """Test that division by zero is not folded"""
        from pylua.lcode import constfolding
        from pylua.lparser import expdesc, VKINT
        
        e1 = expdesc()
        e1.k = VKINT
        e1.ival = 10
        
        e2 = expdesc()
        e2.k = VKINT
        e2.ival = 0
        
        # Division by zero should not fold
        result = constfolding(None, 5, e1, e2)
        self.assertFalse(result)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
