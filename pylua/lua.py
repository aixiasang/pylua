# -*- coding: utf-8 -*-
"""
lua.py - Core API constants and type definitions
=================================================
Source: lua.h (lua-5.3.6/src/lua.h)

Lua - A Scripting Language
Lua.org, PUC-Rio, Brazil (http://www.lua.org)
See Copyright Notice at the end of this file
"""

from typing import Callable, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .lstate import LuaState

# =============================================================================
# lua.h:18-26 - Version Information
# =============================================================================

LUA_VERSION_MAJOR: str = "5"  # lua.h:18
LUA_VERSION_MINOR: str = "3"  # lua.h:19
LUA_VERSION_NUM: int = 503    # lua.h:20
LUA_VERSION_RELEASE: str = "6"  # lua.h:21

LUA_VERSION: str = f"Lua {LUA_VERSION_MAJOR}.{LUA_VERSION_MINOR}"  # lua.h:23
LUA_RELEASE: str = f"{LUA_VERSION}.{LUA_VERSION_RELEASE}"  # lua.h:24
LUA_COPYRIGHT: str = f"{LUA_RELEASE}  Copyright (C) 1994-2020 Lua.org, PUC-Rio"  # lua.h:25
LUA_AUTHORS: str = "R. Ierusalimschy, L. H. de Figueiredo, W. Celes"  # lua.h:26


# =============================================================================
# lua.h:29-33 - Precompiled Code Marks
# =============================================================================

# lua.h:30 - mark for precompiled code ('<esc>Lua')
LUA_SIGNATURE: bytes = b"\x1bLua"

# lua.h:33 - option for multiple returns in 'lua_pcall' and 'lua_call'
LUA_MULTRET: int = -1


# =============================================================================
# lua.h:36-42 - Pseudo-indices
# =============================================================================

# lua.h:41 - Registry index (defined after LUAI_MAXSTACK is known)
# Will be set after luaconf imports
# LUA_REGISTRYINDEX = (-LUAI_MAXSTACK - 1000)

def lua_upvalueindex(i: int) -> int:
    """
    lua.h:42 - Get upvalue pseudo-index
    
    Args:
        i: Upvalue index (1-based)
    
    Returns:
        Pseudo-index for upvalue
    """
    from .luaconf import LUAI_MAXSTACK
    LUA_REGISTRYINDEX = -LUAI_MAXSTACK - 1000
    return LUA_REGISTRYINDEX - i


# =============================================================================
# lua.h:45-52 - Thread Status Codes
# =============================================================================

LUA_OK: int = 0        # lua.h:46 - no errors
LUA_YIELD: int = 1     # lua.h:47 - thread yielded
LUA_ERRRUN: int = 2    # lua.h:48 - runtime error
LUA_ERRSYNTAX: int = 3 # lua.h:49 - syntax error during precompilation
LUA_ERRMEM: int = 4    # lua.h:50 - memory allocation error
LUA_ERRGCMM: int = 5   # lua.h:51 - error running a __gc metamethod
LUA_ERRERR: int = 6    # lua.h:52 - error in error handling


# =============================================================================
# lua.h:58-73 - Basic Types
# =============================================================================

LUA_TNONE: int = -1           # lua.h:61 - invalid type (used internally)

LUA_TNIL: int = 0             # lua.h:63 - nil type
LUA_TBOOLEAN: int = 1         # lua.h:64 - boolean type
LUA_TLIGHTUSERDATA: int = 2   # lua.h:65 - light userdata type
LUA_TNUMBER: int = 3          # lua.h:66 - number type
LUA_TSTRING: int = 4          # lua.h:67 - string type
LUA_TTABLE: int = 5           # lua.h:68 - table type
LUA_TFUNCTION: int = 6        # lua.h:69 - function type
LUA_TUSERDATA: int = 7        # lua.h:70 - userdata type
LUA_TTHREAD: int = 8          # lua.h:71 - thread (coroutine) type

LUA_NUMTAGS: int = 9          # lua.h:73 - number of tags


# =============================================================================
# lua.h:77-84 - Stack and Registry Constants
# =============================================================================

# lua.h:78 - minimum Lua stack available to a C function
LUA_MINSTACK: int = 20

# lua.h:82-84 - predefined values in the registry
LUA_RIDX_MAINTHREAD: int = 1  # lua.h:82 - main thread index in registry
LUA_RIDX_GLOBALS: int = 2     # lua.h:83 - global table index in registry
LUA_RIDX_LAST: int = LUA_RIDX_GLOBALS  # lua.h:84


# =============================================================================
# lua.h:87-98 - Type Definitions (Python equivalents)
# =============================================================================

# lua.h:88 - type of numbers in Lua (lua_Number)
# In Python, we use float (which is C double)
lua_Number = float

# lua.h:92 - type for integer functions (lua_Integer)
# In Python, we use int (arbitrary precision, but we'll limit to 64-bit range)
lua_Integer = int

# lua.h:95 - unsigned integer type (lua_Unsigned)
lua_Unsigned = int

# lua.h:98 - type for continuation-function contexts
lua_KContext = int


# =============================================================================
# lua.h:101-123 - Function Type Definitions
# =============================================================================

# lua.h:104 - Type for C functions registered with Lua
# typedef int (*lua_CFunction) (lua_State *L);
lua_CFunction = Callable[['LuaState'], int]

# lua.h:109 - Type for continuation functions
# typedef int (*lua_KFunction) (lua_State *L, int status, lua_KContext ctx);
lua_KFunction = Callable[['LuaState', int, lua_KContext], int]

# lua.h:115 - Type for functions that read blocks when loading Lua chunks
# typedef const char * (*lua_Reader) (lua_State *L, void *ud, size_t *sz);
lua_Reader = Callable[['LuaState', Any], tuple]  # Returns (data, size)

# lua.h:117 - Type for functions that write blocks when dumping Lua chunks
# typedef int (*lua_Writer) (lua_State *L, const void *p, size_t sz, void *ud);
lua_Writer = Callable[['LuaState', bytes, int, Any], int]

# lua.h:123 - Type for memory-allocation functions
# typedef void * (*lua_Alloc) (void *ud, void *ptr, size_t osize, size_t nsize);
lua_Alloc = Callable[[Any, Any, int, int], Any]


# =============================================================================
# lua.h:195-217 - Comparison and Arithmetic Operation Codes
# =============================================================================

# lua.h:195-208 - Arithmetic operation codes (ORDER TM, ORDER OP)
LUA_OPADD: int = 0    # lua.h:195 - addition (+)
LUA_OPSUB: int = 1    # lua.h:196 - subtraction (-)
LUA_OPMUL: int = 2    # lua.h:197 - multiplication (*)
LUA_OPMOD: int = 3    # lua.h:198 - modulo (%)
LUA_OPPOW: int = 4    # lua.h:199 - exponentiation (^)
LUA_OPDIV: int = 5    # lua.h:200 - float division (/)
LUA_OPIDIV: int = 6   # lua.h:201 - floor division (//)
LUA_OPBAND: int = 7   # lua.h:202 - bitwise AND (&)
LUA_OPBOR: int = 8    # lua.h:203 - bitwise OR (|)
LUA_OPBXOR: int = 9   # lua.h:204 - bitwise XOR (~)
LUA_OPSHL: int = 10   # lua.h:205 - left shift (<<)
LUA_OPSHR: int = 11   # lua.h:206 - right shift (>>)
LUA_OPUNM: int = 12   # lua.h:207 - unary minus (-)
LUA_OPBNOT: int = 13  # lua.h:208 - bitwise NOT (~)

# lua.h:212-214 - Comparison operation codes
LUA_OPEQ: int = 0     # lua.h:212 - equality (==)
LUA_OPLT: int = 1     # lua.h:213 - less than (<)
LUA_OPLE: int = 2     # lua.h:214 - less or equal (<=)


# =============================================================================
# lua.h:301-309 - Garbage Collection Options
# =============================================================================

LUA_GCSTOP: int = 0       # lua.h:301 - stop GC
LUA_GCRESTART: int = 1    # lua.h:302 - restart GC
LUA_GCCOLLECT: int = 2    # lua.h:303 - perform a full GC cycle
LUA_GCCOUNT: int = 3      # lua.h:304 - return amount of memory in use (KB)
LUA_GCCOUNTB: int = 4     # lua.h:305 - return remainder of memory/1024
LUA_GCSTEP: int = 5       # lua.h:306 - perform an incremental GC step
LUA_GCSETPAUSE: int = 6   # lua.h:307 - set GC pause
LUA_GCSETSTEPMUL: int = 7 # lua.h:308 - set GC step multiplier
LUA_GCISRUNNING: int = 9  # lua.h:309 - check if GC is running


# =============================================================================
# lua.h:401-414 - Debug API Event Codes and Masks
# =============================================================================

# lua.h:401-405 - Event codes
LUA_HOOKCALL: int = 0     # lua.h:401 - call hook
LUA_HOOKRET: int = 1      # lua.h:402 - return hook
LUA_HOOKLINE: int = 2     # lua.h:403 - line hook
LUA_HOOKCOUNT: int = 3    # lua.h:404 - count hook
LUA_HOOKTAILCALL: int = 4 # lua.h:405 - tail call hook

# lua.h:411-414 - Event masks
LUA_MASKCALL: int = (1 << LUA_HOOKCALL)   # lua.h:411
LUA_MASKRET: int = (1 << LUA_HOOKRET)     # lua.h:412
LUA_MASKLINE: int = (1 << LUA_HOOKLINE)   # lua.h:413
LUA_MASKCOUNT: int = (1 << LUA_HOOKCOUNT) # lua.h:414


# =============================================================================
# lua.h:440-456 - Debug Information Structure
# =============================================================================

class LuaDebug:
    """
    lua.h:440-456 - struct lua_Debug
    Activation record for debug information
    """
    
    def __init__(self):
        # lua.h:441
        self.event: int = 0
        # lua.h:442 - (n) name of function
        self.name: Optional[str] = None
        # lua.h:443 - (n) 'global', 'local', 'field', 'method'
        self.namewhat: Optional[str] = None
        # lua.h:444 - (S) 'Lua', 'C', 'main', 'tail'
        self.what: Optional[str] = None
        # lua.h:445 - (S) source of function
        self.source: Optional[str] = None
        # lua.h:446 - (l) current line
        self.currentline: int = 0
        # lua.h:447 - (S) line where function was defined
        self.linedefined: int = 0
        # lua.h:448 - (S) last line where function was defined
        self.lastlinedefined: int = 0
        # lua.h:449 - (u) number of upvalues
        self.nups: int = 0
        # lua.h:450 - (u) number of parameters
        self.nparams: int = 0
        # lua.h:451 - (u) is vararg function
        self.isvararg: int = 0
        # lua.h:452 - (t) is tail call
        self.istailcall: int = 0
        # lua.h:453 - (S) short source representation
        self.short_src: str = ""
        # lua.h:455 - private: active function CallInfo
        self.i_ci: Any = None


# =============================================================================
# lua.h:420 - Hook Function Type
# =============================================================================

# typedef void (*lua_Hook) (lua_State *L, lua_Debug *ar);
lua_Hook = Callable[['LuaState', LuaDebug], None]


# =============================================================================
# Type Names Array (for error messages)
# =============================================================================

# Defined in ltm.c but used everywhere
LUA_TYPENAME: List[str] = [
    "no value",      # LUA_TNONE (-1)
    "nil",           # LUA_TNIL (0)
    "boolean",       # LUA_TBOOLEAN (1)
    "userdata",      # LUA_TLIGHTUSERDATA (2)
    "number",        # LUA_TNUMBER (3)
    "string",        # LUA_TSTRING (4)
    "table",         # LUA_TTABLE (5)
    "function",      # LUA_TFUNCTION (6)
    "userdata",      # LUA_TUSERDATA (7)
    "thread",        # LUA_TTHREAD (8)
]


def lua_typename(t: int) -> str:
    """
    Get type name string for a type tag.
    
    Args:
        t: Type tag (LUA_TNIL, LUA_TBOOLEAN, etc.)
    
    Returns:
        Human-readable type name
    """
    # Index 0 is for LUA_TNONE (-1), so add 1
    if t < LUA_TNONE or t >= LUA_NUMTAGS:
        return "unknown"
    return LUA_TYPENAME[t + 1]


# =============================================================================
# Copyright Notice (from lua.h:461-482)
# =============================================================================
"""
Copyright (C) 1994-2020 Lua.org, PUC-Rio.

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
