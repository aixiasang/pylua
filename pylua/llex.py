# -*- coding: utf-8 -*-
"""
llex.py - Lexical Analyzer
==========================
Source: llex.h/llex.c (lua-5.3.6/src/llex.h, llex.c)

Lexical Analyzer
See Copyright Notice in lua.h
"""

from typing import Optional, TYPE_CHECKING, Union
from dataclasses import dataclass, field
from enum import IntEnum

from .lua import lua_Number, lua_Integer, LUA_ERRSYNTAX
from .llimits import MAX_INT, cast_byte, lua_assert
from .lobject import TString, TValue, luaO_str2num, ttisinteger, ttisfloat, ivalue, fltvalue

if TYPE_CHECKING:
    from .lstate import LuaState
    from .lzio import ZIO


# =============================================================================
# llex.h:14 - First Reserved Token
# =============================================================================
FIRST_RESERVED = 257


# =============================================================================
# llex.h:17-19 - Environment Name
# =============================================================================
LUA_ENV = "_ENV"


# =============================================================================
# llex.h:26-37 - Reserved Tokens (ORDER RESERVED)
# =============================================================================
class RESERVED(IntEnum):
    """
    llex.h:26-37 - Token enumeration
    WARNING: if you change the order of this enumeration, grep "ORDER RESERVED"
    """
    # Terminal symbols denoted by reserved words
    TK_AND = FIRST_RESERVED
    TK_BREAK = FIRST_RESERVED + 1
    TK_DO = FIRST_RESERVED + 2
    TK_ELSE = FIRST_RESERVED + 3
    TK_ELSEIF = FIRST_RESERVED + 4
    TK_END = FIRST_RESERVED + 5
    TK_FALSE = FIRST_RESERVED + 6
    TK_FOR = FIRST_RESERVED + 7
    TK_FUNCTION = FIRST_RESERVED + 8
    TK_GOTO = FIRST_RESERVED + 9
    TK_IF = FIRST_RESERVED + 10
    TK_IN = FIRST_RESERVED + 11
    TK_LOCAL = FIRST_RESERVED + 12
    TK_NIL = FIRST_RESERVED + 13
    TK_NOT = FIRST_RESERVED + 14
    TK_OR = FIRST_RESERVED + 15
    TK_REPEAT = FIRST_RESERVED + 16
    TK_RETURN = FIRST_RESERVED + 17
    TK_THEN = FIRST_RESERVED + 18
    TK_TRUE = FIRST_RESERVED + 19
    TK_UNTIL = FIRST_RESERVED + 20
    TK_WHILE = FIRST_RESERVED + 21
    # Other terminal symbols
    TK_IDIV = FIRST_RESERVED + 22    # //
    TK_CONCAT = FIRST_RESERVED + 23  # ..
    TK_DOTS = FIRST_RESERVED + 24    # ...
    TK_EQ = FIRST_RESERVED + 25      # ==
    TK_GE = FIRST_RESERVED + 26      # >=
    TK_LE = FIRST_RESERVED + 27      # <=
    TK_NE = FIRST_RESERVED + 28      # ~=
    TK_SHL = FIRST_RESERVED + 29     # <<
    TK_SHR = FIRST_RESERVED + 30     # >>
    TK_DBCOLON = FIRST_RESERVED + 31 # ::
    TK_EOS = FIRST_RESERVED + 32     # end of stream
    TK_FLT = FIRST_RESERVED + 33     # floating constant
    TK_INT = FIRST_RESERVED + 34     # integer constant
    TK_NAME = FIRST_RESERVED + 35    # identifier
    TK_STRING = FIRST_RESERVED + 36  # string literal


# Convenient aliases
TK_AND = RESERVED.TK_AND
TK_BREAK = RESERVED.TK_BREAK
TK_DO = RESERVED.TK_DO
TK_ELSE = RESERVED.TK_ELSE
TK_ELSEIF = RESERVED.TK_ELSEIF
TK_END = RESERVED.TK_END
TK_FALSE = RESERVED.TK_FALSE
TK_FOR = RESERVED.TK_FOR
TK_FUNCTION = RESERVED.TK_FUNCTION
TK_GOTO = RESERVED.TK_GOTO
TK_IF = RESERVED.TK_IF
TK_IN = RESERVED.TK_IN
TK_LOCAL = RESERVED.TK_LOCAL
TK_NIL = RESERVED.TK_NIL
TK_NOT = RESERVED.TK_NOT
TK_OR = RESERVED.TK_OR
TK_REPEAT = RESERVED.TK_REPEAT
TK_RETURN = RESERVED.TK_RETURN
TK_THEN = RESERVED.TK_THEN
TK_TRUE = RESERVED.TK_TRUE
TK_UNTIL = RESERVED.TK_UNTIL
TK_WHILE = RESERVED.TK_WHILE
TK_IDIV = RESERVED.TK_IDIV
TK_CONCAT = RESERVED.TK_CONCAT
TK_DOTS = RESERVED.TK_DOTS
TK_EQ = RESERVED.TK_EQ
TK_GE = RESERVED.TK_GE
TK_LE = RESERVED.TK_LE
TK_NE = RESERVED.TK_NE
TK_SHL = RESERVED.TK_SHL
TK_SHR = RESERVED.TK_SHR
TK_DBCOLON = RESERVED.TK_DBCOLON
TK_EOS = RESERVED.TK_EOS
TK_FLT = RESERVED.TK_FLT
TK_INT = RESERVED.TK_INT
TK_NAME = RESERVED.TK_NAME
TK_STRING = RESERVED.TK_STRING


# llex.h:40 - Number of reserved words
NUM_RESERVED = TK_WHILE - FIRST_RESERVED + 1


# =============================================================================
# llex.c:40-48 - Token Strings (ORDER RESERVED)
# =============================================================================
luaX_tokens = [
    "and", "break", "do", "else", "elseif",
    "end", "false", "for", "function", "goto", "if",
    "in", "local", "nil", "not", "or", "repeat",
    "return", "then", "true", "until", "while",
    "//", "..", "...", "==", ">=", "<=", "~=",
    "<<", ">>", "::", "<eof>",
    "<number>", "<integer>", "<name>", "<string>"
]


# =============================================================================
# llex.h:43-47 - SemInfo (Semantics Information)
# =============================================================================
@dataclass
class SemInfo:
    """
    llex.h:43-47 - Semantics information
    
    typedef union {
        lua_Number r;
        lua_Integer i;
        TString *ts;
    } SemInfo;
    """
    r: lua_Number = 0.0      # For floating constants
    i: lua_Integer = 0       # For integer constants
    ts: Optional[TString] = None  # For strings and identifiers


# =============================================================================
# llex.h:50-53 - Token Structure
# =============================================================================
@dataclass
class Token:
    """
    llex.h:50-53 - Token structure
    
    typedef struct Token {
        int token;
        SemInfo seminfo;
    } Token;
    """
    token: int = 0
    seminfo: SemInfo = field(default_factory=SemInfo)


# =============================================================================
# llex.h:58-72 - LexState Structure
# =============================================================================
@dataclass
class LexState:
    """
    llex.h:58-72 - Lexer state plus parser state shared by all functions
    
    typedef struct LexState {
        int current;         // current character
        int linenumber;      // input line counter
        int lastline;        // line of last token consumed
        Token t;             // current token
        Token lookahead;     // look ahead token
        struct FuncState *fs;// current function (parser)
        struct lua_State *L;
        ZIO *z;              // input stream
        Mbuffer *buff;       // buffer for tokens
        Table *h;            // to avoid collection/reuse strings
        struct Dyndata *dyd; // dynamic structures for parser
        TString *source;     // current source name
        TString *envn;       // environment variable name
    } LexState;
    """
    current: int = -1                    # llex.h:59 - current character (EOZ = -1)
    linenumber: int = 1                  # llex.h:60 - input line counter
    lastline: int = 1                    # llex.h:61 - line of last token consumed
    t: Token = field(default_factory=Token)           # llex.h:62 - current token
    lookahead: Token = field(default_factory=Token)   # llex.h:63 - look ahead token
    fs: Optional['FuncState'] = None     # llex.h:64 - current function (parser)
    L: Optional['LuaState'] = None       # llex.h:65
    z: Optional['ZIO'] = None            # llex.h:66 - input stream
    buff: bytearray = field(default_factory=bytearray)  # llex.h:67 - buffer for tokens
    h: Optional['Table'] = None          # llex.h:68 - string table
    dyd: Optional['Dyndata'] = None      # llex.h:69 - dynamic data for parser
    source: Optional[TString] = None     # llex.h:70 - current source name
    envn: Optional[TString] = None       # llex.h:71 - environment variable name


# =============================================================================
# Constants
# =============================================================================
EOZ = -1  # End of input
LUA_MINBUFFER = 32
UTF8BUFFSZ = 8
UCHAR_MAX = 255


# =============================================================================
# Character Classification (lctype.c equivalents)
# =============================================================================
def lisdigit(c: int) -> bool:
    """Check if character is a digit"""
    return c >= 0 and chr(c).isdigit()

def lisxdigit(c: int) -> bool:
    """Check if character is a hex digit"""
    return c >= 0 and chr(c) in '0123456789abcdefABCDEF'

def lisspace(c: int) -> bool:
    """Check if character is whitespace"""
    return c >= 0 and chr(c) in ' \t\n\r\f\v'

def lislalpha(c: int) -> bool:
    """Check if character is letter or underscore"""
    return c >= 0 and (chr(c).isalpha() or chr(c) == '_')

def lislalnum(c: int) -> bool:
    """Check if character is alphanumeric or underscore"""
    return c >= 0 and (chr(c).isalnum() or chr(c) == '_')


# =============================================================================
# llex.c:32-36 - Lexer Macros
# =============================================================================
def next(ls: LexState) -> None:
    """llex.c:32 - #define next(ls) (ls->current = zgetc(ls->z))"""
    if ls.z and ls.z.n > 0:
        ls.current = ls.z.p[0]
        ls.z.p = ls.z.p[1:]
        ls.z.n -= 1
    else:
        ls.current = EOZ


def currIsNewline(ls: LexState) -> bool:
    """llex.c:36 - #define currIsNewline(ls) (ls->current == '\\n' || ls->current == '\\r')"""
    return ls.current == ord('\n') or ls.current == ord('\r')


# =============================================================================
# llex.c:57-67 - save
# =============================================================================
def save(ls: LexState, c: int) -> None:
    """
    llex.c:57-67 - Save character to buffer
    
    static void save (LexState *ls, int c)
    """
    if c >= 0:
        ls.buff.append(c if isinstance(c, int) else ord(c))


def save_and_next(ls: LexState) -> None:
    """llex.c:51 - #define save_and_next(ls) (save(ls, ls->current), next(ls))"""
    save(ls, ls.current)
    next(ls)


# =============================================================================
# Error Handling
# =============================================================================
class LexError(Exception):
    """Lexical error exception"""
    def __init__(self, msg: str, line: int, source: str = ""):
        self.msg = msg
        self.line = line
        self.source = source
        super().__init__(f"{source}:{line}: {msg}")


def lexerror(ls: LexState, msg: str, token: int) -> None:
    """
    llex.c:109-114 - Report lexical error
    
    static l_noret lexerror (LexState *ls, const char *msg, int token)
    """
    source_name = ls.source.data.decode('utf-8') if ls.source else "<unknown>"
    full_msg = f"{source_name}:{ls.linenumber}: {msg}"
    if token:
        token_str = txtToken(ls, token)
        full_msg += f" near {token_str}"
    raise LexError(full_msg, ls.linenumber, source_name)


def luaX_syntaxerror(ls: LexState, msg: str) -> None:
    """
    llex.c:117-119 - Report syntax error
    
    l_noret luaX_syntaxerror (LexState *ls, const char *msg)
    """
    lexerror(ls, msg, ls.t.token)


# =============================================================================
# llex.c:82-94 - luaX_token2str
# =============================================================================
def luaX_token2str(ls: LexState, token: int) -> str:
    """
    llex.c:82-94 - Convert token to string representation
    
    const char *luaX_token2str (LexState *ls, int token)
    """
    if token < FIRST_RESERVED:
        return f"'{chr(token)}'"
    else:
        s = luaX_tokens[token - FIRST_RESERVED]
        if token < TK_EOS:
            return f"'{s}'"
        else:
            return s


def txtToken(ls: LexState, token: int) -> str:
    """
    llex.c:97-106 - Get text representation of current token
    
    static const char *txtToken (LexState *ls, int token)
    """
    if token in (TK_NAME, TK_STRING, TK_FLT, TK_INT):
        return f"'{ls.buff.decode('utf-8', errors='replace')}'"
    else:
        return luaX_token2str(ls, token)


# =============================================================================
# llex.c:127-144 - luaX_newstring
# =============================================================================
def luaX_newstring(ls: LexState, s: bytes) -> TString:
    """
    llex.c:127-144 - Create new string and anchor it
    
    TString *luaX_newstring (LexState *ls, const char *str, size_t l)
    """
    ts = TString()
    ts.data = s
    ts.shrlen = len(s)
    ts.tt = 4  # LUA_TSHRSTR
    ts.hash = hash(s)
    return ts


# =============================================================================
# llex.c:151-159 - inclinenumber
# =============================================================================
def inclinenumber(ls: LexState) -> None:
    """
    llex.c:151-159 - Increment line number and skip newline sequence
    
    static void inclinenumber (LexState *ls)
    """
    old = ls.current
    lua_assert(currIsNewline(ls))
    next(ls)  # Skip '\n' or '\r'
    if currIsNewline(ls) and ls.current != old:
        next(ls)  # Skip '\n\r' or '\r\n'
    ls.linenumber += 1
    if ls.linenumber >= MAX_INT:
        lexerror(ls, "chunk has too many lines", 0)


# =============================================================================
# llex.c:162-175 - luaX_setinput
# =============================================================================
def luaX_setinput(L: 'LuaState', ls: LexState, z: 'ZIO', 
                  source: TString, firstchar: int) -> None:
    """
    llex.c:162-175 - Initialize lexer state
    
    void luaX_setinput (lua_State *L, LexState *ls, ZIO *z, TString *source, int firstchar)
    """
    ls.t.token = 0
    ls.L = L
    ls.current = firstchar
    ls.lookahead.token = TK_EOS
    ls.z = z
    ls.fs = None
    ls.linenumber = 1
    ls.lastline = 1
    ls.source = source
    ls.envn = TString()
    ls.envn.data = LUA_ENV.encode('utf-8')
    ls.envn.shrlen = len(LUA_ENV)
    ls.buff = bytearray()


# =============================================================================
# llex.c:186-206 - check_next1, check_next2
# =============================================================================
def check_next1(ls: LexState, c: int) -> bool:
    """
    llex.c:186-192 - Check if current char matches and advance
    
    static int check_next1 (LexState *ls, int c)
    """
    if ls.current == c:
        next(ls)
        return True
    return False


def check_next2(ls: LexState, set_str: str) -> bool:
    """
    llex.c:199-206 - Check if current char is in set and save it
    
    static int check_next2 (LexState *ls, const char *set)
    """
    if ls.current >= 0 and chr(ls.current) in set_str:
        save_and_next(ls)
        return True
    return False


# =============================================================================
# llex.c:214-243 - read_numeral
# =============================================================================
def read_numeral(ls: LexState, seminfo: SemInfo) -> int:
    """
    llex.c:214-243 - Read a number
    
    static int read_numeral (LexState *ls, SemInfo *seminfo)
    """
    expo = "Ee"
    first = ls.current
    lua_assert(lisdigit(ls.current))
    save_and_next(ls)
    
    if first == ord('0') and check_next2(ls, "xX"):
        expo = "Pp"
    
    while True:
        if check_next2(ls, expo):
            check_next2(ls, "-+")
        if lisxdigit(ls.current):
            save_and_next(ls)
        elif ls.current == ord('.'):
            save_and_next(ls)
        else:
            break
    
    # Convert buffer to number
    obj = TValue()
    num_str = bytes(ls.buff)
    if luaO_str2num(num_str, obj) == 0:
        lexerror(ls, "malformed number", TK_FLT)
    
    if ttisinteger(obj):
        seminfo.i = ivalue(obj)
        return TK_INT
    else:
        lua_assert(ttisfloat(obj))
        seminfo.r = fltvalue(obj)
        return TK_FLT


# =============================================================================
# llex.c:251-264 - skip_sep
# =============================================================================
def skip_sep(ls: LexState) -> int:
    """
    llex.c:251-264 - Skip separator sequence [=*[ or ]=*]
    
    static size_t skip_sep (LexState *ls)
    """
    count = 0
    s = ls.current
    lua_assert(s == ord('[') or s == ord(']'))
    save_and_next(ls)
    while ls.current == ord('='):
        save_and_next(ls)
        count += 1
    if ls.current == s:
        return count + 2
    elif count == 0:
        return 1
    else:
        return 0


# =============================================================================
# llex.c:267-303 - read_long_string
# =============================================================================
def read_long_string(ls: LexState, seminfo: Optional[SemInfo], sep: int) -> None:
    """
    llex.c:267-303 - Read long string or comment
    
    static void read_long_string (LexState *ls, SemInfo *seminfo, size_t sep)
    """
    line = ls.linenumber
    save_and_next(ls)  # Skip 2nd '['
    
    if currIsNewline(ls):
        inclinenumber(ls)
    
    while True:
        if ls.current == EOZ:
            what = "string" if seminfo else "comment"
            lexerror(ls, f"unfinished long {what} (starting at line {line})", TK_EOS)
        elif ls.current == ord(']'):
            if skip_sep(ls) == sep:
                save_and_next(ls)  # Skip 2nd ']'
                break
        elif ls.current == ord('\n') or ls.current == ord('\r'):
            save(ls, ord('\n'))
            inclinenumber(ls)
            if seminfo is None:
                ls.buff.clear()
        else:
            if seminfo is not None:
                save_and_next(ls)
            else:
                next(ls)
    
    if seminfo is not None:
        seminfo.ts = luaX_newstring(ls, bytes(ls.buff[sep:-sep]))


# =============================================================================
# llex.c:306-366 - Escape sequence helpers
# =============================================================================
def esccheck(ls: LexState, c: bool, msg: str) -> None:
    """llex.c:306-312 - Check escape condition"""
    if not c:
        if ls.current != EOZ:
            save_and_next(ls)
        lexerror(ls, msg, TK_STRING)


def gethexa(ls: LexState) -> int:
    """llex.c:315-319 - Get hex digit value"""
    save_and_next(ls)
    esccheck(ls, lisxdigit(ls.current), "hexadecimal digit expected")
    return int(chr(ls.current), 16) if ls.current >= 0 else 0


def readhexaesc(ls: LexState) -> int:
    """llex.c:322-327 - Read hex escape \\xNN"""
    r = gethexa(ls)
    r = (r << 4) + gethexa(ls)
    del ls.buff[-2:]  # Remove saved chars
    return r


def readutf8esc(ls: LexState) -> int:
    """llex.c:330-345 - Read UTF-8 escape \\u{NNNN}"""
    i = 4
    save_and_next(ls)  # Skip 'u'
    esccheck(ls, ls.current == ord('{'), "missing '{'")
    r = gethexa(ls)
    while True:
        save_and_next(ls)
        if not lisxdigit(ls.current):
            break
        i += 1
        r = (r << 4) + (int(chr(ls.current), 16) if ls.current >= 0 else 0)
        esccheck(ls, r <= 0x10FFFF, "UTF-8 value too large")
    esccheck(ls, ls.current == ord('}'), "missing '}'")
    next(ls)  # Skip '}'
    del ls.buff[-i:]  # Remove saved chars
    return r


def luaO_utf8esc(buff: bytearray, x: int) -> int:
    """Convert UTF-8 codepoint to bytes"""
    n = 0
    if x < 0x80:
        buff.append(x)
        n = 1
    elif x < 0x800:
        buff.append(0xC0 | (x >> 6))
        buff.append(0x80 | (x & 0x3F))
        n = 2
    elif x < 0x10000:
        buff.append(0xE0 | (x >> 12))
        buff.append(0x80 | ((x >> 6) & 0x3F))
        buff.append(0x80 | (x & 0x3F))
        n = 3
    else:
        buff.append(0xF0 | (x >> 18))
        buff.append(0x80 | ((x >> 12) & 0x3F))
        buff.append(0x80 | ((x >> 6) & 0x3F))
        buff.append(0x80 | (x & 0x3F))
        n = 4
    return n


def utf8esc(ls: LexState) -> None:
    """llex.c:348-353 - Handle UTF-8 escape"""
    buff = bytearray()
    codepoint = readutf8esc(ls)
    luaO_utf8esc(buff, codepoint)
    for b in buff:
        save(ls, b)


def readdecesc(ls: LexState) -> int:
    """llex.c:356-366 - Read decimal escape \\DDD"""
    r = 0
    count = 0
    for i in range(3):
        if lisdigit(ls.current):
            r = 10 * r + (ls.current - ord('0'))
            save_and_next(ls)
            count += 1
        else:
            break
    esccheck(ls, r <= UCHAR_MAX, "decimal escape too large")
    del ls.buff[-count:]  # Remove read digits
    return r


# =============================================================================
# llex.c:369-429 - read_string
# =============================================================================
def read_string(ls: LexState, delimiter: int, seminfo: SemInfo) -> None:
    """
    llex.c:369-429 - Read string literal
    
    static void read_string (LexState *ls, int del, SemInfo *seminfo)
    """
    save_and_next(ls)  # Keep delimiter
    
    while ls.current != delimiter:
        if ls.current == EOZ:
            lexerror(ls, "unfinished string", TK_EOS)
        elif ls.current == ord('\n') or ls.current == ord('\r'):
            lexerror(ls, "unfinished string", TK_STRING)
        elif ls.current == ord('\\'):
            save_and_next(ls)  # Keep '\\' for error messages
            c = None
            
            if ls.current == ord('a'):
                c = ord('\a')
                next(ls)
            elif ls.current == ord('b'):
                c = ord('\b')
                next(ls)
            elif ls.current == ord('f'):
                c = ord('\f')
                next(ls)
            elif ls.current == ord('n'):
                c = ord('\n')
                next(ls)
            elif ls.current == ord('r'):
                c = ord('\r')
                next(ls)
            elif ls.current == ord('t'):
                c = ord('\t')
                next(ls)
            elif ls.current == ord('v'):
                c = ord('\v')
                next(ls)
            elif ls.current == ord('x'):
                c = readhexaesc(ls)
                next(ls)
            elif ls.current == ord('u'):
                utf8esc(ls)
                del ls.buff[-1:]  # Remove '\\'
                continue
            elif ls.current == ord('\n') or ls.current == ord('\r'):
                inclinenumber(ls)
                c = ord('\n')
            elif ls.current == ord('\\') or ls.current == ord('"') or ls.current == ord("'"):
                c = ls.current
                next(ls)
            elif ls.current == EOZ:
                continue  # Will raise error next loop
            elif ls.current == ord('z'):
                del ls.buff[-1:]  # Remove '\\'
                next(ls)
                while ls.current >= 0 and lisspace(ls.current):
                    if currIsNewline(ls):
                        inclinenumber(ls)
                    else:
                        next(ls)
                continue
            else:
                esccheck(ls, lisdigit(ls.current), "invalid escape sequence")
                c = readdecesc(ls)
            
            if c is not None:
                del ls.buff[-1:]  # Remove '\\'
                save(ls, c)
        else:
            save_and_next(ls)
    
    save_and_next(ls)  # Skip delimiter
    seminfo.ts = luaX_newstring(ls, bytes(ls.buff[1:-1]))


# =============================================================================
# llex.c:432-549 - llex (main lexer function)
# =============================================================================
def llex(ls: LexState, seminfo: SemInfo) -> int:
    """
    llex.c:432-549 - Main lexer function
    
    static int llex (LexState *ls, SemInfo *seminfo)
    """
    ls.buff.clear()
    
    while True:
        if ls.current == ord('\n') or ls.current == ord('\r'):
            inclinenumber(ls)
        elif ls.current in (ord(' '), ord('\f'), ord('\t'), ord('\v')):
            next(ls)
        elif ls.current == ord('-'):
            next(ls)
            if ls.current != ord('-'):
                return ord('-')
            # Comment
            next(ls)
            if ls.current == ord('['):
                sep = skip_sep(ls)
                ls.buff.clear()
                if sep >= 2:
                    read_long_string(ls, None, sep)
                    ls.buff.clear()
                    continue
            # Short comment
            while not currIsNewline(ls) and ls.current != EOZ:
                next(ls)
        elif ls.current == ord('['):
            sep = skip_sep(ls)
            if sep >= 2:
                read_long_string(ls, seminfo, sep)
                return TK_STRING
            elif sep == 0:
                lexerror(ls, "invalid long string delimiter", TK_STRING)
            return ord('[')
        elif ls.current == ord('='):
            next(ls)
            if check_next1(ls, ord('=')):
                return TK_EQ
            return ord('=')
        elif ls.current == ord('<'):
            next(ls)
            if check_next1(ls, ord('=')):
                return TK_LE
            elif check_next1(ls, ord('<')):
                return TK_SHL
            return ord('<')
        elif ls.current == ord('>'):
            next(ls)
            if check_next1(ls, ord('=')):
                return TK_GE
            elif check_next1(ls, ord('>')):
                return TK_SHR
            return ord('>')
        elif ls.current == ord('/'):
            next(ls)
            if check_next1(ls, ord('/')):
                return TK_IDIV
            return ord('/')
        elif ls.current == ord('~'):
            next(ls)
            if check_next1(ls, ord('=')):
                return TK_NE
            return ord('~')
        elif ls.current == ord(':'):
            next(ls)
            if check_next1(ls, ord(':')):
                return TK_DBCOLON
            return ord(':')
        elif ls.current == ord('"') or ls.current == ord("'"):
            read_string(ls, ls.current, seminfo)
            return TK_STRING
        elif ls.current == ord('.'):
            save_and_next(ls)
            if check_next1(ls, ord('.')):
                if check_next1(ls, ord('.')):
                    return TK_DOTS
                return TK_CONCAT
            elif not lisdigit(ls.current):
                return ord('.')
            return read_numeral(ls, seminfo)
        elif ls.current >= ord('0') and ls.current <= ord('9'):
            return read_numeral(ls, seminfo)
        elif ls.current == EOZ:
            return TK_EOS
        else:
            if lislalpha(ls.current):
                # Identifier or reserved word
                while lislalnum(ls.current):
                    save_and_next(ls)
                ts = luaX_newstring(ls, bytes(ls.buff))
                seminfo.ts = ts
                # Check if reserved word
                word = ts.data.decode('utf-8')
                if word in luaX_tokens[:NUM_RESERVED]:
                    return luaX_tokens.index(word) + FIRST_RESERVED
                return TK_NAME
            else:
                # Single-char token
                c = ls.current
                next(ls)
                return c


# =============================================================================
# llex.c:552-560 - luaX_next
# =============================================================================
def luaX_next(ls: LexState) -> None:
    """
    llex.c:552-560 - Get next token
    
    void luaX_next (LexState *ls)
    """
    ls.lastline = ls.linenumber
    if ls.lookahead.token != TK_EOS:
        # Copy lookahead token to current token (cannot use shallow copy!)
        ls.t.token = ls.lookahead.token
        ls.t.seminfo.r = ls.lookahead.seminfo.r
        ls.t.seminfo.i = ls.lookahead.seminfo.i
        ls.t.seminfo.ts = ls.lookahead.seminfo.ts
        ls.lookahead.token = TK_EOS
    else:
        ls.t.token = llex(ls, ls.t.seminfo)


# =============================================================================
# llex.c:563-567 - luaX_lookahead
# =============================================================================
def luaX_lookahead(ls: LexState) -> int:
    """
    llex.c:563-567 - Look ahead one token
    
    int luaX_lookahead (LexState *ls)
    """
    lua_assert(ls.lookahead.token == TK_EOS)
    ls.lookahead.token = llex(ls, ls.lookahead.seminfo)
    return ls.lookahead.token


# =============================================================================
# llex.c:70-79 - luaX_init (called during state creation)
# =============================================================================
def luaX_init(L: 'LuaState') -> None:
    """
    llex.c:70-79 - Initialize lexer
    
    void luaX_init (lua_State *L)
    
    Creates env name and reserves keywords.
    """
    # In PyLua, we don't need to pre-create reserved word strings
    # since we use Python string comparison directly
    pass
