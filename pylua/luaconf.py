# -*- coding: utf-8 -*-
"""
luaconf.py - Configuration file for Lua
=======================================
Source: luaconf.h (lua-5.3.6/src/luaconf.h)

Configuration file for Lua
See Copyright Notice in lua.h
"""

import sys
import struct

# =============================================================================
# luaconf.h:86-95 - Bits in Integer
# =============================================================================

# luaconf.h:91-95 - LUAI_BITSINT defines the (minimum) number of bits in an 'int'
# Python int is arbitrary precision, but we simulate 32-bit for compatibility
LUAI_BITSINT: int = 32  # luaconf.h:91


# =============================================================================
# luaconf.h:98-148 - Number Type Configuration
# =============================================================================

# luaconf.h:109-111 - predefined options for LUA_INT_TYPE
LUA_INT_INT: int = 1
LUA_INT_LONG: int = 2
LUA_INT_LONGLONG: int = 3

# luaconf.h:114-116 - predefined options for LUA_FLOAT_TYPE
LUA_FLOAT_FLOAT: int = 1
LUA_FLOAT_DOUBLE: int = 2
LUA_FLOAT_LONGDOUBLE: int = 3

# luaconf.h:143-144 - default configuration for 64-bit Lua
LUA_INT_TYPE: int = LUA_INT_LONGLONG  # luaconf.h:143
LUA_FLOAT_TYPE: int = LUA_FLOAT_DOUBLE  # luaconf.h:147


# =============================================================================
# luaconf.h:162-224 - Path Configuration
# =============================================================================

# luaconf.h:168-170 - Path separators and marks
LUA_PATH_SEP: str = ";"    # luaconf.h:168 - template separator in path
LUA_PATH_MARK: str = "?"   # luaconf.h:169 - substitution mark
LUA_EXEC_DIR: str = "!"    # luaconf.h:170 - Windows: executable's directory

# luaconf.h:182
LUA_VDIR: str = "5.3"

# luaconf.h:220-224 - directory separator
if sys.platform == "win32":
    LUA_DIRSEP: str = "\\"  # luaconf.h:221
else:
    LUA_DIRSEP: str = "/"   # luaconf.h:223


# =============================================================================
# luaconf.h:486-590 - Number Configuration (Double)
# =============================================================================

# luaconf.h:488 - LUA_NUMBER type
# In Python, we use float (C double equivalent)
LUA_NUMBER = float

# luaconf.h:495 - format for writing floats
LUA_NUMBER_FMT: str = "%.14g"  # luaconf.h:495

# luaconf.h:510-590 - Integer Configuration

# luaconf.h:564-568 - long long configuration (default for 64-bit Lua)
LUA_INTEGER = int  # Python int is arbitrary precision

# luaconf.h:566 - format modifier for reading/writing integers
LUA_INTEGER_FRMLEN: str = "ll"

# luaconf.h:568-569 - integer limits (64-bit signed)
LUA_MAXINTEGER: int = (1 << 63) - 1   # luaconf.h:568 - 9223372036854775807
LUA_MININTEGER: int = -(1 << 63)      # luaconf.h:569 - -9223372036854775808

# luaconf.h:527 - integer format
LUA_INTEGER_FMT: str = "%lld"

# luaconf.h:537 - LUA_UNSIGNED type
LUA_UNSIGNED = int  # Python handles unsigned naturally


# =============================================================================
# luaconf.h:722-732 - Stack Configuration
# =============================================================================

# luaconf.h:729 - LUAI_MAXSTACK limits the size of the Lua stack
# CHANGE it if you need a different limit. This limit is arbitrary;
# its only purpose is to stop Lua from consuming unlimited stack
# space (and to reserve some numbers for pseudo-indices).
if LUAI_BITSINT >= 32:
    LUAI_MAXSTACK: int = 1000000  # luaconf.h:729
else:
    LUAI_MAXSTACK: int = 15000    # luaconf.h:731


# =============================================================================
# luaconf.h:735-740 - Extra Space Configuration
# =============================================================================

# luaconf.h:740 - LUA_EXTRASPACE defines the size of a raw memory area
# associated with a Lua state with very fast access
# In Python, this is simulated as we don't need raw memory management
LUA_EXTRASPACE: int = struct.calcsize('P')  # sizeof(void *)


# =============================================================================
# luaconf.h:743-748 - Debug Information Configuration
# =============================================================================

# luaconf.h:748 - LUA_IDSIZE gives the maximum size for the description
# of the source of a function in debug information
LUA_IDSIZE: int = 60  # luaconf.h:748


# =============================================================================
# luaconf.h:751-762 - Buffer Configuration
# =============================================================================

# luaconf.h:758-762 - LUAL_BUFFERSIZE is the buffer size used by the
# lauxlib buffer system
if LUA_FLOAT_TYPE == LUA_FLOAT_LONGDOUBLE:
    LUAL_BUFFERSIZE: int = 8192  # luaconf.h:759
else:
    # luaconf.h:761 - ((int)(0x80 * sizeof(void*) * sizeof(lua_Integer)))
    # For 64-bit: 0x80 * 8 * 8 = 4096
    LUAL_BUFFERSIZE: int = 0x80 * struct.calcsize('P') * 8


# =============================================================================
# luaconf.h:772-773 - Quote Macros (Compatibility)
# =============================================================================

def LUA_QL(x: str) -> str:
    """
    luaconf.h:772 - Quote a program element in error messages
    """
    return f"'{x}'"


LUA_QS: str = "'%s'"  # luaconf.h:773


# =============================================================================
# Additional Configuration Derived from luaconf.h
# =============================================================================

# Registry index (from lua.h:41, depends on LUAI_MAXSTACK)
LUA_REGISTRYINDEX: int = -LUAI_MAXSTACK - 1000


# =============================================================================
# luaconf.h:447-450 - Number to Integer Conversion
# =============================================================================

def lua_numbertointeger(n: float) -> tuple:
    """
    luaconf.h:447-450 - lua_numbertointeger converts a float number to an 
    integer, or returns (None, False) if float is not within the range of 
    a lua_Integer.
    
    Args:
        n: Float number to convert
    
    Returns:
        Tuple of (integer_value, success_flag)
    """
    # luaconf.h:448-450
    # ((n) >= (LUA_NUMBER)(LUA_MININTEGER) &&
    #  (n) < -(LUA_NUMBER)(LUA_MININTEGER) &&
    #     (*(p) = (LUA_INTEGER)(n), 1))
    if n >= float(LUA_MININTEGER) and n < -float(LUA_MININTEGER):
        return (int(n), True)
    return (None, False)


# =============================================================================
# Size Constants for Binary Format Compatibility
# =============================================================================

# These are used for bytecode loading/dumping to ensure compatibility
# with C compiled bytecode

# Size of C types in bytes (for 64-bit platform compatibility)
SIZEOF_INT: int = 4           # C int
SIZEOF_SIZE_T: int = 8        # C size_t (64-bit)
SIZEOF_INSTRUCTION: int = 4   # Lua Instruction (unsigned int)
SIZEOF_LUA_INTEGER: int = 8   # lua_Integer (long long)
SIZEOF_LUA_NUMBER: int = 8    # lua_Number (double)

# Byte order for struct unpacking
# Lua bytecode uses native byte order, we detect it
if sys.byteorder == 'little':
    BYTE_ORDER: str = '<'  # Little endian
else:
    BYTE_ORDER: str = '>'  # Big endian
