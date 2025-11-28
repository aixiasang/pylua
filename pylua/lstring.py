# -*- coding: utf-8 -*-
"""
lstring.py - String table (keeps all strings handled by Lua)
=============================================================
Source: lstring.h/lstring.c (lua-5.3.6/src/lstring.h, lstring.c)

String table (keeps all strings handled by Lua)
See Copyright Notice in lua.h
"""

from typing import TYPE_CHECKING, Optional, Dict, List
from dataclasses import dataclass

from .llimits import (
    cast_byte, lua_assert, LUAI_MAXSHORTLEN, MINSTRTABSIZE,
    MAX_INT, l_castS2U,
)
from .lobject import TString, LUA_TSHRSTR, LUA_TLNGSTR

if TYPE_CHECKING:
    from .lstate import LuaState, GlobalState

# =============================================================================
# lstring.c:25 - Memory Error Message
# =============================================================================
MEMERRMSG = "not enough memory"

# =============================================================================
# lstring.c:32-34 - Hash Limit
# =============================================================================
# Lua will use at most ~(2^LUAI_HASHLIMIT) bytes from a string to compute its hash
LUAI_HASHLIMIT = 5


# =============================================================================
# String Interning Pool - Python implementation
# =============================================================================

class StringTable:
    """
    lstate.h:76-80 - String hash table for interning short strings
    
    This is the Python implementation of Lua's string interning mechanism.
    Short strings (length <= LUAI_MAXSHORTLEN) are interned, meaning that
    identical strings share the same object.
    """
    def __init__(self, initial_size: int = MINSTRTABSIZE):
        self.size: int = initial_size
        self.nuse: int = 0  # Number of elements
        # Hash table: maps hash value to list of TStrings
        self.hash: Dict[int, List[TString]] = {}
        # Direct lookup by string content for fast access
        self._content_map: Dict[bytes, TString] = {}
    
    def get(self, content: bytes) -> Optional[TString]:
        """Get interned string by content, or None if not found"""
        return self._content_map.get(content)
    
    def intern(self, content: bytes, h: int) -> TString:
        """Intern a string (add to table if not exists, return existing if found)"""
        # Check if already interned
        existing = self._content_map.get(content)
        if existing is not None:
            return existing
        
        # Create new TString
        ts = TString()
        ts.tt = LUA_TSHRSTR
        ts.data = content
        ts.shrlen = len(content)
        ts.hash = h
        ts.extra = 0
        
        # Add to hash table
        if h not in self.hash:
            self.hash[h] = []
        self.hash[h].append(ts)
        
        # Add to content map
        self._content_map[content] = ts
        self.nuse += 1
        
        # Resize if needed
        if self.nuse >= self.size and self.size <= MAX_INT // 2:
            self._resize(self.size * 2)
        
        return ts
    
    def remove(self, ts: TString) -> None:
        """Remove a string from the table"""
        content = ts.data
        if content in self._content_map:
            del self._content_map[content]
            self.nuse -= 1
            
            # Remove from hash list
            h = ts.hash
            if h in self.hash:
                self.hash[h] = [s for s in self.hash[h] if s is not ts]
    
    def _resize(self, new_size: int) -> None:
        """Resize the hash table"""
        self.size = new_size
        # Rehash is not strictly needed in Python dict implementation
        # but we track the size for compatibility


# Global string table instance
_string_table = StringTable()


# =============================================================================
# lstring.c:49-55 - luaS_hash
# =============================================================================

def luaS_hash(s: bytes, seed: int = 0) -> int:
    """
    lstring.c:49-55 - Compute hash for string
    
    unsigned int luaS_hash (const char *str, size_t l, unsigned int seed) {
        unsigned int h = seed ^ cast(unsigned int, l);
        size_t step = (l >> LUAI_HASHLIMIT) + 1;
        for (; l >= step; l -= step)
            h ^= ((h<<5) + (h>>2) + cast_byte(str[l - 1]));
        return h;
    }
    """
    l = len(s)
    h = (seed ^ l) & 0xFFFFFFFF
    step = (l >> LUAI_HASHLIMIT) + 1
    
    while l >= step:
        h ^= ((h << 5) + (h >> 2) + cast_byte(s[l - 1])) & 0xFFFFFFFF
        h &= 0xFFFFFFFF
        l -= step
    
    return h


# =============================================================================
# lstring.c:40-46 - luaS_eqlngstr
# =============================================================================

def luaS_eqlngstr(a: TString, b: TString) -> bool:
    """
    lstring.c:40-46 - equality for long strings
    
    int luaS_eqlngstr (TString *a, TString *b) {
        size_t len = a->u.lnglen;
        lua_assert(a->tt == LUA_TLNGSTR && b->tt == LUA_TLNGSTR);
        return (a == b) ||  /* same instance or... */
            ((len == b->u.lnglen) &&  /* equal length and ... */
             (memcmp(getstr(a), getstr(b), len) == 0));  /* equal contents */
    }
    """
    lua_assert(a.tt == LUA_TLNGSTR and b.tt == LUA_TLNGSTR)
    return (a is b) or (a.lnglen == b.lnglen and a.data == b.data)


# =============================================================================
# lstring.c:58-65 - luaS_hashlongstr
# =============================================================================

def luaS_hashlongstr(ts: TString) -> int:
    """
    lstring.c:58-65 - Hash for long strings (computed lazily)
    
    unsigned int luaS_hashlongstr (TString *ts) {
        lua_assert(ts->tt == LUA_TLNGSTR);
        if (ts->extra == 0) {  /* no hash? */
            ts->hash = luaS_hash(getstr(ts), ts->u.lnglen, ts->hash);
            ts->extra = 1;  /* now it has its hash */
        }
        return ts->hash;
    }
    """
    lua_assert(ts.tt == LUA_TLNGSTR)
    if ts.extra == 0:  # no hash?
        ts.hash = luaS_hash(ts.data, ts.hash)
        ts.extra = 1  # now it has its hash
    return ts.hash


# =============================================================================
# lstring.c:116-126 - luaS_init
# =============================================================================

def luaS_init(L: 'LuaState') -> None:
    """
    lstring.c:116-126 - Initialize the string table and the string cache
    
    void luaS_init (lua_State *L) {
        global_State *g = G(L);
        int i, j;
        luaS_resize(L, MINSTRTABSIZE);  /* initial size of string table */
        /* pre-create memory-error message */
        g->memerrmsg = luaS_newliteral(L, MEMERRMSG);
        luaC_fix(L, obj2gco(g->memerrmsg));  /* it should never be collected */
        for (i = 0; i < STRCACHE_N; i++)  /* fill cache with valid strings */
            for (j = 0; j < STRCACHE_M; j++)
                g->strcache[i][j] = g->memerrmsg;
    }
    """
    global _string_table
    _string_table = StringTable(MINSTRTABSIZE)
    
    # Pre-create memory-error message
    from .lstate import G
    g = G(L)
    g.memerrmsg = luaS_newlstr(L, MEMERRMSG.encode('utf-8'), len(MEMERRMSG))


# =============================================================================
# lstring.c:167-193 - internshrstr
# =============================================================================

def internshrstr(L: 'LuaState', s: bytes) -> TString:
    """
    lstring.c:167-193 - checks whether short string exists and reuses it or creates a new one
    
    This is the core interning function for short strings.
    """
    global _string_table
    
    # Check if already interned
    existing = _string_table.get(s)
    if existing is not None:
        return existing
    
    # Get seed from global state if available
    seed = 0
    try:
        from .lstate import G
        seed = G(L).seed if L and L.l_G else 0
    except:
        pass
    
    # Compute hash and intern
    h = luaS_hash(s, seed)
    return _string_table.intern(s, h)


# =============================================================================
# lstring.c:147-151 - luaS_createlngstrobj
# =============================================================================

def luaS_createlngstrobj(L: 'LuaState', content: bytes) -> TString:
    """
    lstring.c:147-151 - Create a long string object (not interned)
    
    TString *luaS_createlngstrobj (lua_State *L, size_t l) {
        TString *ts = createstrobj(L, l, LUA_TLNGSTR, G(L)->seed);
        ts->u.lnglen = l;
        return ts;
    }
    """
    seed = 0
    try:
        from .lstate import G
        seed = G(L).seed if L and L.l_G else 0
    except:
        pass
    
    ts = TString()
    ts.tt = LUA_TLNGSTR
    ts.data = content
    ts.lnglen = len(content)
    ts.hash = seed  # Initial seed, actual hash computed lazily
    ts.extra = 0    # Hash not computed yet
    ts.shrlen = 0
    
    return ts


# =============================================================================
# lstring.c:199-207 - luaS_newlstr
# =============================================================================

def luaS_newlstr(L: 'LuaState', s: bytes, length: int = None) -> TString:
    """
    lstring.c:199-207 - new string (with explicit length)
    
    TString *luaS_newlstr (lua_State *L, const char *str, size_t l) {
        if (l <= LUAI_MAXSHORTLEN)  /* short string? */
            return internshrstr(L, str, l);
        else {
            TString *ts;
            if (l >= (MAX_SIZE - sizeof(TString))/sizeof(char))
                luaM_toobig(L);
            ts = luaS_createlngstrobj(L, l);
            memcpy(getstr(ts), str, l * sizeof(char));
            return ts;
        }
    }
    """
    if length is None:
        length = len(s)
    
    # Ensure we only use the specified length
    content = s[:length]
    
    if length <= LUAI_MAXSHORTLEN:
        # Short string - intern it
        return internshrstr(L, content)
    else:
        # Long string - don't intern
        return luaS_createlngstrobj(L, content)


# =============================================================================
# lstring.c:210-212 - luaS_new
# =============================================================================

def luaS_new(L: 'LuaState', s: str) -> TString:
    """
    lstring.c:210-212 - new string from null-terminated C string
    
    TString *luaS_new (lua_State *L, const char *str) {
        return luaS_newlstr(L, str, strlen(str));
    }
    """
    if isinstance(s, str):
        s = s.encode('utf-8')
    return luaS_newlstr(L, s, len(s))


# =============================================================================
# Utility Functions
# =============================================================================

def luaS_newliteral(L: 'LuaState', s: str) -> TString:
    """Create a string from a literal"""
    return luaS_new(L, s)


def get_interned_string(content: bytes) -> Optional[TString]:
    """Get an interned string by content, or None if not found"""
    return _string_table.get(content)


def clear_string_table() -> None:
    """Clear the string table (useful for testing/reset)"""
    global _string_table
    _string_table = StringTable()


def get_string_table_stats() -> dict:
    """Get statistics about the string table"""
    return {
        'size': _string_table.size,
        'nuse': _string_table.nuse,
        'buckets': len(_string_table.hash),
    }
