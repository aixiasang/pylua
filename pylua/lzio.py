# -*- coding: utf-8 -*-
"""
lzio.py - Buffered streams
==========================
Source: lzio.h/lzio.c (lua-5.3.6/src/lzio.h, lzio.c)

Buffered streams
See Copyright Notice in lua.h
"""

from typing import Optional, Any, Callable, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field

from .llimits import cast_uchar

if TYPE_CHECKING:
    from .lstate import LuaState
    from .lua import lua_Reader

# =============================================================================
# lzio.h:16 - End of Stream Marker
# =============================================================================
EOZ: int = -1  # lzio.h:16 - end of stream

# =============================================================================
# lzio.h:23-27 - Memory Buffer Structure
# =============================================================================
@dataclass
class Mbuffer:
    """
    lzio.h:23-27 - Memory buffer structure
    
    typedef struct Mbuffer {
        char *buffer;
        size_t n;
        size_t buffsize;
    } Mbuffer;
    
    Source: lzio.h:23-27
    """
    buffer: bytes = b""      # lzio.h:24 - buffer data
    n: int = 0               # lzio.h:25 - current position/used size
    buffsize: int = 0        # lzio.h:26 - total buffer size

def luaZ_initbuffer(L: 'LuaState', buff: Mbuffer) -> None:
    """
    lzio.h:29 - #define luaZ_initbuffer(L, buff) ((buff)->buffer = NULL, (buff)->buffsize = 0)
    Initialize memory buffer
    Source: lzio.h:29
    """
    buff.buffer = b""
    buff.buffsize = 0

def luaZ_buffer(buff: Mbuffer) -> bytes:
    """
    lzio.h:31 - #define luaZ_buffer(buff) ((buff)->buffer)
    Get buffer data
    Source: lzio.h:31
    """
    return buff.buffer

def luaZ_sizebuffer(buff: Mbuffer) -> int:
    """
    lzio.h:32 - #define luaZ_sizebuffer(buff) ((buff)->buffsize)
    Get buffer size
    Source: lzio.h:32
    """
    return buff.buffsize

def luaZ_bufflen(buff: Mbuffer) -> int:
    """
    lzio.h:33 - #define luaZ_bufflen(buff) ((buff)->n)
    Get buffer used length
    Source: lzio.h:33
    """
    return buff.n

def luaZ_buffremove(buff: Mbuffer, i: int) -> None:
    """
    lzio.h:35 - #define luaZ_buffremove(buff,i) ((buff)->n -= (i))
    Remove bytes from buffer
    Source: lzio.h:35
    """
    buff.n -= i

def luaZ_resetbuffer(buff: Mbuffer) -> None:
    """
    lzio.h:36 - #define luaZ_resetbuffer(buff) ((buff)->n = 0)
    Reset buffer position
    Source: lzio.h:36
    """
    buff.n = 0

def luaZ_resizebuffer(L: 'LuaState', buff: Mbuffer, size: int) -> None:
    """
    lzio.h:39-42 - Resize buffer
    #define luaZ_resizebuffer(L, buff, size) \
        ((buff)->buffer = luaM_reallocvchar(L, (buff)->buffer, \
                    (buff)->buffsize, size), \
        (buff)->buffsize = size)
    Source: lzio.h:39-42
    """
    # In Python, we just create a new bytes object
    if size > len(buff.buffer):
        buff.buffer = buff.buffer + bytes(size - len(buff.buffer))
    else:
        buff.buffer = buff.buffer[:size]
    buff.buffsize = size

def luaZ_freebuffer(L: 'LuaState', buff: Mbuffer) -> None:
    """
    lzio.h:44 - #define luaZ_freebuffer(L, buff) luaZ_resizebuffer(L, buff, 0)
    Free buffer
    Source: lzio.h:44
    """
    luaZ_resizebuffer(L, buff, 0)

# =============================================================================
# lzio.h:55-61 - ZIO Structure (Buffered Input Stream)
# =============================================================================
@dataclass
class ZIO:
    """
    lzio.h:55-61 - Buffered input stream structure
    
    struct Zio {
        size_t n;           /* bytes still unread */
        const char *p;      /* current position in buffer */
        lua_Reader reader;  /* reader function */
        void *data;         /* additional data */
        lua_State *L;       /* Lua state (for reader) */
    };
    
    Source: lzio.h:55-61
    """
    n: int = 0                           # lzio.h:56 - bytes still unread
    p: bytes = b""                       # lzio.h:57 - current buffer data
    pos: int = 0                         # current position in p (Python addition)
    reader: Optional[Callable] = None   # lzio.h:58 - reader function
    data: Any = None                     # lzio.h:59 - additional data
    L: Optional['LuaState'] = None       # lzio.h:60 - Lua state

def zgetc(z: ZIO) -> int:
    """
    lzio.h:20 - #define zgetc(z) (((z)->n--)>0 ? cast_uchar(*(z)->p++) : luaZ_fill(z))
    Get next character from stream
    Source: lzio.h:20
    """
    if z.n > 0:
        z.n -= 1
        c = z.p[z.pos] if z.pos < len(z.p) else 0
        z.pos += 1
        return cast_uchar(c)
    else:
        return luaZ_fill(z)

# =============================================================================
# lzio.c:14-24 - luaZ_fill
# =============================================================================
def luaZ_fill(z: ZIO) -> int:
    """
    lzio.h:64 / lzio.c:14-24 - Fill buffer from reader
    
    LUAI_FUNC int luaZ_fill (ZIO *z);
    
    Source: lzio.c:14-24
    """
    if z.reader is None:
        return EOZ
    
    # Call reader function
    # In C: const char *buff = z->reader(z->L, z->data, &size);
    result = z.reader(z.L, z.data)
    
    if result is None:
        return EOZ
    
    buff, size = result
    
    if buff is None or size == 0:
        return EOZ
    
    # lzio.c:21-23
    z.n = size - 1  # discount char being returned
    z.p = buff
    z.pos = 1       # first char is being returned
    
    return cast_uchar(buff[0])

# =============================================================================
# lzio.c:26-37 - luaZ_init
# =============================================================================
def luaZ_init(L: 'LuaState', z: ZIO, reader: Callable, data: Any) -> None:
    """
    lzio.h:47-48 / lzio.c:26-37 - Initialize ZIO
    
    LUAI_FUNC void luaZ_init (lua_State *L, ZIO *z, lua_Reader reader,
                                            void *data);
    
    Source: lzio.c:26-37
    """
    z.L = L           # lzio.c:27
    z.reader = reader # lzio.c:28
    z.data = data     # lzio.c:29
    z.n = 0           # lzio.c:30
    z.p = b""         # lzio.c:31
    z.pos = 0

# =============================================================================
# lzio.c:39-55 - luaZ_read
# =============================================================================
def luaZ_read(z: ZIO, b: bytearray, n: int) -> int:
    """
    lzio.h:49 / lzio.c:39-55 - Read n bytes from ZIO
    
    LUAI_FUNC size_t luaZ_read (ZIO* z, void *b, size_t n);
    
    Returns 0 on success, remaining bytes count on error (truncated)
    
    Source: lzio.c:39-55
    """
    b_pos = 0
    
    while n > 0:
        # lzio.c:42-43
        if z.n == 0:  # no bytes in buffer
            if luaZ_fill(z) == EOZ:  # try to read more
                return n  # no more input; return number of missing bytes
            else:
                z.n += 1  # luaZ_fill consumed first byte; put it back
                z.pos -= 1
        
        # lzio.c:44-50
        m = min(n, z.n)  # min between n and z->n
        
        # Copy data: memcpy(b, z->p, m)
        for i in range(m):
            if z.pos + i < len(z.p):
                b[b_pos + i] = z.p[z.pos + i]
        
        z.n -= m
        z.pos += m
        b_pos += m
        n -= m
    
    return 0  # success

# =============================================================================
# Helper class for reading from bytes
# =============================================================================
class BytesReader:
    """
    Helper class to create a reader function from bytes.
    Used for loading bytecode from memory.
    """
    def __init__(self, data: bytes):
        self.data = data
        self.read = False
    
    def __call__(self, L: 'LuaState', ud: Any) -> Optional[Tuple[bytes, int]]:
        """Reader function compatible with lua_Reader"""
        if self.read:
            return None
        self.read = True
        return (self.data, len(self.data))

class FileReader:
    """
    Helper class to create a reader function from file.
    Used for loading bytecode from file.
    """
    def __init__(self, file):
        self.file = file
        self.chunk_size = 4096
    
    def __call__(self, L: 'LuaState', ud: Any) -> Optional[Tuple[bytes, int]]:
        """Reader function compatible with lua_Reader"""
        data = self.file.read(self.chunk_size)
        if data:
            return (data, len(data))
        return None
