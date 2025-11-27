"""
ldump.py - Lua bytecode dumper

Dumps compiled Lua proto to binary format compatible with Lua 5.3.

Source: ldump.c
"""

import struct
from typing import Optional, BinaryIO
from io import BytesIO

from .lobject import (
    LUA_TNIL, LUA_TBOOLEAN, LUA_TNUMFLT, LUA_TNUMINT, LUA_TSHRSTR, LUA_TLNGSTR,
)

# Lua 5.3 bytecode header constants
LUA_SIGNATURE = b"\x1bLua"
LUAC_VERSION = 0x53  # Lua 5.3
LUAC_FORMAT = 0
LUAC_DATA = b"\x19\x93\r\n\x1a\n"
SIZEOF_INT = 4
SIZEOF_SIZE_T = 8
SIZEOF_INSTRUCTION = 4
SIZEOF_LUA_INTEGER = 8
SIZEOF_LUA_NUMBER = 8
LUAC_INT = 0x5678
LUAC_NUM = 370.5


class DumpState:
    """State for bytecode dumping"""
    def __init__(self, strip: bool = False):
        self.strip = strip
        self.buffer = BytesIO()
    
    def write(self, data: bytes) -> None:
        self.buffer.write(data)
    
    def write_byte(self, b: int) -> None:
        self.buffer.write(bytes([b & 0xFF]))
    
    def write_int(self, n: int) -> None:
        self.buffer.write(struct.pack('<i', n))
    
    def write_size_t(self, n: int) -> None:
        self.buffer.write(struct.pack('<Q', n))
    
    def write_integer(self, n: int) -> None:
        self.buffer.write(struct.pack('<q', n))
    
    def write_number(self, n: float) -> None:
        self.buffer.write(struct.pack('<d', n))
    
    def write_instruction(self, inst: int) -> None:
        self.buffer.write(struct.pack('<I', inst & 0xFFFFFFFF))
    
    def write_string(self, s: Optional[str]) -> None:
        """Write a string in Lua format"""
        if s is None:
            self.write_byte(0)
            return
        
        data = s.encode('utf-8') if isinstance(s, str) else s
        size = len(data) + 1  # Include null terminator
        
        if size < 0xFF:
            self.write_byte(size)
        else:
            self.write_byte(0xFF)
            self.write_size_t(size)
        
        self.write(data)
    
    def getvalue(self) -> bytes:
        return self.buffer.getvalue()


def dump_header(D: DumpState) -> None:
    """Dump Lua bytecode header"""
    D.write(LUA_SIGNATURE)
    D.write_byte(LUAC_VERSION)
    D.write_byte(LUAC_FORMAT)
    D.write(LUAC_DATA)
    D.write_byte(SIZEOF_INT)
    D.write_byte(SIZEOF_SIZE_T)
    D.write_byte(SIZEOF_INSTRUCTION)
    D.write_byte(SIZEOF_LUA_INTEGER)
    D.write_byte(SIZEOF_LUA_NUMBER)
    D.write_integer(LUAC_INT)
    D.write_number(LUAC_NUM)


def dump_code(D: DumpState, proto: 'CompiledProto') -> None:
    """Dump instruction code"""
    n = len(proto.code)
    D.write_int(n)
    for inst in proto.code:
        D.write_instruction(inst)


def dump_constants(D: DumpState, proto: 'CompiledProto') -> None:
    """Dump constants table"""
    n = len(proto.constants)
    D.write_int(n)
    
    for idx, val in proto.constants:
        if val is None:
            D.write_byte(LUA_TNIL)
        elif isinstance(val, bool):
            D.write_byte(LUA_TBOOLEAN)
            D.write_byte(1 if val else 0)
        elif isinstance(val, int):
            D.write_byte(LUA_TNUMINT)
            D.write_integer(val)
        elif isinstance(val, float):
            D.write_byte(LUA_TNUMFLT)
            D.write_number(val)
        elif isinstance(val, str):
            # Remove quotes if present
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            
            data = val.encode('utf-8')
            if len(data) < 40:  # Short string threshold
                D.write_byte(LUA_TSHRSTR | 0x40)  # Short string with collectible bit
            else:
                D.write_byte(LUA_TLNGSTR | 0x40)  # Long string with collectible bit
            D.write_string(val)
        else:
            # Fallback: treat as string
            D.write_byte(LUA_TSHRSTR | 0x40)
            D.write_string(str(val))


def dump_upvalues(D: DumpState, proto: 'CompiledProto') -> None:
    """Dump upvalues"""
    n = len(proto.upvalues)
    D.write_int(n)
    
    for instack, idx, name in proto.upvalues:
        D.write_byte(instack)
        D.write_byte(idx)


def dump_protos(D: DumpState, proto: 'CompiledProto') -> None:
    """Dump nested prototypes"""
    n = len(proto.protos)
    D.write_int(n)
    
    for sub in proto.protos:
        dump_function(D, sub)


def dump_debug(D: DumpState, proto: 'CompiledProto') -> None:
    """Dump debug information"""
    if D.strip:
        # Stripped: no debug info
        D.write_int(0)  # lineinfo
        D.write_int(0)  # abslineinfo (Lua 5.4+, not in 5.3)
        D.write_int(0)  # locvars
        D.write_int(0)  # upvalues
        return
    
    # Line info
    n = len(proto.lineinfo) if proto.lineinfo else 0
    D.write_int(n)
    for line in (proto.lineinfo or []):
        D.write_int(line)
    
    # Local variables
    n = len(proto.locvars) if proto.locvars else 0
    D.write_int(n)
    for name, startpc, endpc in (proto.locvars or []):
        D.write_string(name)
        D.write_int(startpc)
        D.write_int(endpc)
    
    # Upvalue names
    n = len(proto.upvalues)
    D.write_int(n)
    for instack, idx, name in proto.upvalues:
        D.write_string(name if name else "")


def dump_function(D: DumpState, proto: 'CompiledProto') -> None:
    """Dump a function prototype"""
    # Source name
    if D.strip:
        D.write_string(None)
    else:
        D.write_string(proto.source)
    
    D.write_int(proto.linedefined)
    D.write_int(proto.lastlinedefined)
    D.write_byte(proto.numparams)
    D.write_byte(1 if proto.is_vararg else 0)
    D.write_byte(proto.maxstacksize)
    
    dump_code(D, proto)
    dump_constants(D, proto)
    dump_upvalues(D, proto)
    dump_protos(D, proto)
    dump_debug(D, proto)


def luaU_dump(proto: 'CompiledProto', strip: bool = False) -> bytes:
    """
    Dump compiled proto to Lua 5.3 bytecode format
    
    Source: ldump.c:luaU_dump
    """
    D = DumpState(strip)
    
    dump_header(D)
    D.write_byte(len(proto.upvalues))  # Number of upvalues
    dump_function(D, proto)
    
    return D.getvalue()
