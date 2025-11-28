# -*- coding: utf-8 -*-
"""
llimits.py - Limits, basic types, and some other 'installation-dependent' definitions
======================================================================================
Source: llimits.h (lua-5.3.6/src/llimits.h)

Limits, basic types, and some other 'installation-dependent' definitions
See Copyright Notice in lua.h
"""

from typing import Any
import sys

from .luaconf import (
    LUA_MAXINTEGER,
    LUAI_BITSINT, 
    LUA_NUMBER, 
    LUA_INTEGER,
    SIZEOF_INSTRUCTION,
)


# =============================================================================
# llimits.h:17-31 - Memory Size Types
# =============================================================================

# llimits.h:23-27 - 'lu_mem' and 'l_mem' are unsigned/signed integers big enough
# to count the total memory used by Lua (in bytes)
# In Python, we use int which has arbitrary precision

# llimits.h:26 - unsigned memory size type
lu_mem = int

# llimits.h:27 - signed memory size type
l_mem = int


# =============================================================================
# llimits.h:34-35 - Byte Type
# =============================================================================

# llimits.h:35 - chars used as small naturals (so that 'char' is reserved for characters)
# typedef unsigned char lu_byte;
lu_byte = int  # 0-255 range, we'll enforce in usage


# =============================================================================
# llimits.h:38-51 - Size Limits
# =============================================================================

# llimits.h:39 - maximum value for size_t
MAX_SIZET: int = (1 << 64) - 1  # 64-bit size_t max

# llimits.h:42-43 - maximum size visible for Lua (must be representable in a lua_Integer)
MAX_SIZE: int = min(MAX_SIZET, LUA_MAXINTEGER)  # llimits.h:42-43

# llimits.h:46 - maximum value for lu_mem
MAX_LUMEM: int = (1 << 64) - 1  # ~0 for 64-bit unsigned

# llimits.h:48 - maximum value for l_mem (signed)
MAX_LMEM: int = MAX_LUMEM >> 1  # llimits.h:48

# llimits.h:51 - maximum value of an int
MAX_INT: int = (1 << 31) - 1  # INT_MAX for 32-bit int

# Additional C limits
SHRT_MAX: int = (1 << 15) - 1  # Maximum value for short (32767)


# =============================================================================
# llimits.h:54-59 - Pointer to Integer Conversion
# =============================================================================

def point2uint(p: Any) -> int:
    """
    llimits.h:59 - conversion of pointer to unsigned integer
    This is for hashing only; there is no problem if the integer
    cannot hold the whole pointer value
    
    Args:
        p: Any Python object (used as pointer equivalent)
    
    Returns:
        Integer hash suitable for use as unsigned int
    """
    # In Python, we use id() which returns the memory address
    return id(p) & 0xFFFFFFFF  # Mask to 32-bit unsigned


# =============================================================================
# llimits.h:63-74 - Maximum Alignment Union
# =============================================================================

# llimits.h:67-73 - type to ensure maximum alignment
# In Python, we don't need explicit alignment handling
# This is for documentation purposes
class L_Umaxalign:
    """
    llimits.h:67-73 - Union type to ensure maximum alignment
    In C this is a union of various types for alignment.
    In Python, this is just a placeholder for documentation.
    """
    pass


# =============================================================================
# llimits.h:78-80 - Usual Argument Conversion Types
# =============================================================================

# llimits.h:79 - types of 'usual argument conversions' for lua_Number
l_uacNumber = float  # LUAI_UACNUMBER -> double

# llimits.h:80 - types of 'usual argument conversions' for lua_Integer
l_uacInt = int  # LUAI_UACINT -> lua_Integer


# =============================================================================
# llimits.h:83-101 - Assertion Macros
# =============================================================================

# llimits.h:85-91 - internal assertions for in-house debugging
# In Python, we use assert statements

def lua_assert(c: bool) -> None:
    """
    llimits.h:89 - lua_assert macro
    In release builds this is empty, in debug it asserts.
    
    Args:
        c: Condition to assert
    """
    assert c


def check_exp(c: bool, e: Any) -> Any:
    """
    llimits.h:85 - check_exp macro
    Assert condition and return expression.
    
    Args:
        c: Condition to check
        e: Expression to return
    
    Returns:
        The expression e
    """
    lua_assert(c)
    return e


def lua_longassert(c: bool) -> None:
    """
    llimits.h:87 - lua_longassert macro
    For conditions that may be too long for regular assert.
    
    Args:
        c: Condition to assert
    """
    if not c:
        lua_assert(False)


# llimits.h:97-101 - API check macros
def luai_apicheck(l: Any, e: bool) -> None:
    """
    llimits.h:98 - luai_apicheck macro
    Assertion for checking API calls.
    
    Args:
        l: Lua state (unused in default implementation)
        e: Condition to check
    """
    lua_assert(e)


def api_check(l: Any, e: bool, msg: str) -> None:
    """
    llimits.h:101 - api_check macro
    API check with message.
    
    Args:
        l: Lua state
        e: Condition to check
        msg: Error message
    """
    luai_apicheck(l, e and msg)


# =============================================================================
# llimits.h:104-107 - Unused Variable Macro
# =============================================================================

def UNUSED(x: Any) -> None:
    """
    llimits.h:106 - macro to avoid warnings about unused variables
    
    Args:
        x: Unused variable
    """
    pass


# =============================================================================
# llimits.h:110-117 - Type Cast Macros
# =============================================================================

def cast(t: type, exp: Any) -> Any:
    """
    llimits.h:111 - cast macro (a macro highlights casts in the code)
    
    Args:
        t: Target type
        exp: Expression to cast
    
    Returns:
        Casted expression
    """
    return t(exp)


def cast_void(i: Any) -> None:
    """llimits.h:113 - cast to void"""
    return None


def cast_byte(i: int) -> int:
    """llimits.h:114 - cast to lu_byte (unsigned char, 0-255)"""
    return i & 0xFF


def cast_num(i: Any) -> float:
    """llimits.h:115 - cast to lua_Number (float/double)"""
    return float(i)


def cast_int(i: Any) -> int:
    """llimits.h:116 - cast to int"""
    return int(i)


def cast_uchar(i: int) -> int:
    """llimits.h:117 - cast to unsigned char"""
    return i & 0xFF


# =============================================================================
# llimits.h:120-132 - Signed/Unsigned Integer Conversion
# =============================================================================

# 64-bit integer bounds for two's complement arithmetic
_LUA_INTEGER_BITS = 64
_LUA_UNSIGNED_MAX = (1 << _LUA_INTEGER_BITS) - 1  # 0xFFFFFFFFFFFFFFFF
_LUA_INTEGER_MAX = (1 << (_LUA_INTEGER_BITS - 1)) - 1  # 0x7FFFFFFFFFFFFFFF
_LUA_INTEGER_MIN = -(1 << (_LUA_INTEGER_BITS - 1))  # -0x8000000000000000


def l_castS2U(i: int) -> int:
    """
    llimits.h:122 - cast a signed lua_Integer to lua_Unsigned
    
    #define l_castS2U(i) ((lua_Unsigned)(i))
    
    Converts signed 64-bit integer to unsigned 64-bit representation.
    This follows C's two's complement semantics.
    
    Args:
        i: Signed integer (may be negative)
    
    Returns:
        Unsigned 64-bit integer representation
    """
    # Mask to 64 bits to handle Python's arbitrary precision
    return i & _LUA_UNSIGNED_MAX


def l_castU2S(i: int) -> int:
    """
    llimits.h:131 - cast a lua_Unsigned to a signed lua_Integer
    
    #define l_castU2S(i) ((lua_Integer)(i))
    
    This cast is not strict ISO C, but two-complement architectures 
    should work fine.
    
    Converts unsigned 64-bit integer to signed 64-bit representation.
    If the high bit (bit 63) is set, the result is negative.
    
    Args:
        i: Unsigned 64-bit integer
    
    Returns:
        Signed 64-bit integer (two's complement)
    """
    # First ensure we're working with 64-bit unsigned
    i = i & _LUA_UNSIGNED_MAX
    # If bit 63 is set, convert to negative
    if i > _LUA_INTEGER_MAX:
        return i - (1 << _LUA_INTEGER_BITS)
    return i


# =============================================================================
# llimits.h:148-154 - Maximum Call Depth
# =============================================================================

# llimits.h:153 - maximum depth for nested C calls and syntactical nested 
# non-terminals in a program. (Value must fit in an unsigned short int.)
LUAI_MAXCCALLS: int = 200  # llimits.h:153

# llimits.h:145-146 - maximum stack for a Lua function
LUAI_MAXSTACK: int = 1000000  # llimits.h:145-146


# =============================================================================
# llimits.h:158-166 - Instruction Type
# =============================================================================

# llimits.h:163 - type for virtual-machine instructions;
# must be an unsigned with (at least) 4 bytes (see details in lopcodes.h)
# typedef unsigned int Instruction;
Instruction = int  # We'll use Python int, enforce 32-bit range in usage


# =============================================================================
# llimits.h:170-178 - Short String Length
# =============================================================================

# llimits.h:177 - Maximum length for short strings, that is, strings that are
# internalized. (Cannot be smaller than reserved words or tags for
# metamethods, as these strings must be internalized;
# #("function") = 8, #("__newindex") = 10.)
LUAI_MAXSHORTLEN: int = 40  # llimits.h:177


# =============================================================================
# llimits.h:181-189 - String Table Size
# =============================================================================

# llimits.h:188 - Initial size for the string table (must be power of 2).
# The Lua core alone registers ~50 strings (reserved words +
# metaevent keys + a few others). Libraries would typically add
# a few dozens more.
MINSTRTABSIZE: int = 128  # llimits.h:188


# =============================================================================
# llimits.h:192-200 - String Cache Configuration
# =============================================================================

# llimits.h:198-199 - Size of cache for strings in the API
STRCACHE_N: int = 53  # llimits.h:198 - number of sets (better be a prime)
STRCACHE_M: int = 2   # llimits.h:199 - size of each set


# =============================================================================
# llimits.h:203-206 - Minimum Buffer Size
# =============================================================================

# llimits.h:205 - minimum size for string buffer
LUA_MINBUFFER: int = 32  # llimits.h:205


# =============================================================================
# llimits.h:209-224 - Lock/Unlock Macros
# =============================================================================

def lua_lock(L: Any) -> None:
    """
    llimits.h:214 - macro executed whenever program enters the Lua core
    
    Args:
        L: Lua state
    """
    pass  # No-op in default implementation


def lua_unlock(L: Any) -> None:
    """
    llimits.h:215 - macro executed whenever program leaves the Lua core
    
    Args:
        L: Lua state
    """
    pass  # No-op in default implementation


def luai_threadyield(L: Any) -> None:
    """
    llimits.h:223 - macro executed during Lua functions at points where 
    the function can yield.
    
    Args:
        L: Lua state
    """
    lua_unlock(L)
    lua_lock(L)


# =============================================================================
# llimits.h:227-254 - User State Macros
# =============================================================================

def luai_userstateopen(L: Any) -> None:
    """llimits.h:233 - called when a new Lua state is created"""
    pass


def luai_userstateclose(L: Any) -> None:
    """llimits.h:237 - called when a Lua state is closed"""
    pass


def luai_userstatethread(L: Any, L1: Any) -> None:
    """llimits.h:241 - called when a new thread is created"""
    pass


def luai_userstatefree(L: Any, L1: Any) -> None:
    """llimits.h:245 - called when a thread is freed"""
    pass


def luai_userstateresume(L: Any, n: int) -> None:
    """llimits.h:249 - called when a coroutine is resumed"""
    pass


def luai_userstateyield(L: Any, n: int) -> None:
    """llimits.h:253 - called when a coroutine yields"""
    pass


# =============================================================================
# llimits.h:258-298 - Number Operation Macros
# =============================================================================

import math


def luai_numidiv(L: Any, a: float, b: float) -> float:
    """
    llimits.h:264 - floor division (defined as 'floor(a/b)')
    
    Args:
        L: Lua state (unused)
        a: Dividend
        b: Divisor
    
    Returns:
        Floor of a/b
    """
    return math.floor(a / b)


def luai_numdiv(L: Any, a: float, b: float) -> float:
    """
    llimits.h:269 - float division
    
    Args:
        L: Lua state (unused)
        a: Dividend
        b: Divisor
    
    Returns:
        a / b (inf if b==0 and a!=0, nan if both are 0)
    """
    if b == 0.0:
        if a == 0.0:
            return float('nan')
        elif a > 0:
            return float('inf')
        else:
            return float('-inf')
    return a / b


def luai_nummod(L: Any, a: float, b: float) -> float:
    """
    llimits.h:280-281 - modulo operation
    
    modulo: defined as 'a - floor(a/b)*b'; this definition gives NaN when
    'b' is huge, but the result should be 'a'. 'fmod' gives the result of
    'a - trunc(a/b)*b', and therefore must be corrected when 'trunc(a/b)
    ~= floor(a/b)'. That happens when the division has a non-integer
    negative result.
    
    Args:
        L: Lua state (unused)
        a: Dividend
        b: Divisor
    
    Returns:
        a mod b (Lua semantics)
    """
    m = math.fmod(a, b)
    if m * b < 0:
        m += b
    return m


def luai_numpow(L: Any, a: float, b: float) -> float:
    """
    llimits.h:286 - exponentiation
    
    Args:
        L: Lua state (unused)
        a: Base
        b: Exponent
    
    Returns:
        a ^ b
    """
    return math.pow(a, b)


def luai_numadd(L: Any, a: float, b: float) -> float:
    """llimits.h:291 - addition"""
    return a + b


def luai_numsub(L: Any, a: float, b: float) -> float:
    """llimits.h:292 - subtraction"""
    return a - b


def luai_nummul(L: Any, a: float, b: float) -> float:
    """llimits.h:293 - multiplication"""
    return a * b


def luai_numunm(L: Any, a: float) -> float:
    """llimits.h:294 - unary minus"""
    return -a


def luai_numeq(a: float, b: float) -> bool:
    """llimits.h:295 - equality comparison"""
    return a == b


def luai_numlt(a: float, b: float) -> bool:
    """llimits.h:296 - less than comparison"""
    return a < b


def luai_numle(a: float, b: float) -> bool:
    """llimits.h:297 - less than or equal comparison"""
    return a <= b


def luai_numisnan(a: float) -> bool:
    """llimits.h:298 - check if value is NaN"""
    return math.isnan(a)


# =============================================================================
# llimits.h:305-320 - Hard Tests (Debug Only)
# =============================================================================

def condmovestack(L: Any, pre: Any, pos: Any) -> None:
    """
    llimits.h:309 - macro to control inclusion of some hard tests on 
    stack reallocation (no-op in release)
    """
    pass


def condchangemem(L: Any, pre: Any, pos: Any) -> None:
    """
    llimits.h:317 - macro for memory change tests (no-op in release)
    """
    pass
