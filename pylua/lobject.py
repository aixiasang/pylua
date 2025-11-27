# -*- coding: utf-8 -*-
"""
lobject.py - Type definitions for Lua objects
==============================================
Source: lobject.h/lobject.c (lua-5.3.6/src/lobject.h, lobject.c)

Type definitions for Lua objects
See Copyright Notice in lua.h
"""

from typing import Any, Optional, List, Union, TYPE_CHECKING, Callable
from dataclasses import dataclass, field
import math

from .lua import (
    LUA_TNONE, LUA_TNIL, LUA_TBOOLEAN, LUA_TLIGHTUSERDATA,
    LUA_TNUMBER, LUA_TSTRING, LUA_TTABLE, LUA_TFUNCTION,
    LUA_TUSERDATA, LUA_TTHREAD, LUA_NUMTAGS,
    lua_Number, lua_Integer, lua_CFunction,
    LUA_OPADD, LUA_OPSUB, LUA_OPMUL, LUA_OPMOD, LUA_OPPOW,
    LUA_OPDIV, LUA_OPIDIV, LUA_OPBAND, LUA_OPBOR, LUA_OPBXOR,
    LUA_OPSHL, LUA_OPSHR, LUA_OPUNM, LUA_OPBNOT,
)
from .llimits import (
    lu_byte, lu_mem, Instruction,
    cast, cast_byte, cast_num, cast_int, check_exp, lua_assert,
    l_castS2U, l_castU2S, MAX_INT,
    luai_numadd, luai_numsub, luai_nummul, luai_nummod,
    luai_numpow, luai_numdiv, luai_numidiv, luai_numunm,
)
from .luaconf import (
    LUA_NUMBER, LUA_INTEGER, LUA_MAXINTEGER, LUA_MININTEGER,
    lua_numbertointeger, LUA_IDSIZE,
)

if TYPE_CHECKING:
    from .lstate import LuaState

# =============================================================================
# lobject.h:19-28 - Extra Tags for Non-values
# =============================================================================
LUA_TPROTO: int = LUA_NUMTAGS        # lobject.h:22
LUA_TDEADKEY: int = LUA_NUMTAGS + 1  # lobject.h:23
LUA_TOTALTAGS: int = LUA_TPROTO + 2  # lobject.h:28

# =============================================================================
# lobject.h:32-66 - Tag Variant System
# =============================================================================
LUA_TLCL: int = LUA_TFUNCTION | (0 << 4)   # lobject.h:47
LUA_TLCF: int = LUA_TFUNCTION | (1 << 4)   # lobject.h:48
LUA_TCCL: int = LUA_TFUNCTION | (2 << 4)   # lobject.h:49
LUA_TSHRSTR: int = LUA_TSTRING | (0 << 4)  # lobject.h:53
LUA_TLNGSTR: int = LUA_TSTRING | (1 << 4)  # lobject.h:54
LUA_TNUMFLT: int = LUA_TNUMBER | (0 << 4)  # lobject.h:58
LUA_TNUMINT: int = LUA_TNUMBER | (1 << 4)  # lobject.h:59
BIT_ISCOLLECTABLE: int = 1 << 6            # lobject.h:63

def ctb(t: int) -> int:
    """lobject.h:66 - mark a tag as collectable"""
    return t | BIT_ISCOLLECTABLE

# =============================================================================
# lobject.h:69-87 - GCObject Common Header
# =============================================================================
@dataclass
class GCObject:
    """lobject.h:85-87 - Common type for all collectable objects"""
    next: Optional['GCObject'] = None  # lobject.h:79 - linked list
    tt: int = 0                        # lobject.h:79 - type tag
    marked: int = 0                    # lobject.h:79 - GC mark

# =============================================================================
# lobject.h:92-115 - Tagged Values (TValue)
# =============================================================================
@dataclass
class Value:
    """lobject.h:100-107 - Union of all Lua values"""
    gc: Optional[GCObject] = None      # lobject.h:101
    p: Any = None                      # lobject.h:102
    b: int = 0                         # lobject.h:103
    f: Optional[lua_CFunction] = None  # lobject.h:104
    i: lua_Integer = 0                 # lobject.h:105
    n: lua_Number = 0.0                # lobject.h:106

@dataclass
class TValue:
    """lobject.h:113-115 - Tagged Value structure"""
    value_: Value = field(default_factory=Value)
    tt_: int = LUA_TNIL

def NILCONSTANT() -> TValue:
    """lobject.h:120"""
    return TValue(value_=Value(gc=None), tt_=LUA_TNIL)

# =============================================================================
# lobject.h:122-184 - TValue Access Macros
# =============================================================================
def val_(o: TValue) -> Value:
    """lobject.h:123"""
    return o.value_

def rttype(o: TValue) -> int:
    """lobject.h:127"""
    return o.tt_

def novariant(x: int) -> int:
    """lobject.h:130"""
    return x & 0x0F

def ttype(o: TValue) -> int:
    """lobject.h:133"""
    return rttype(o) & 0x3F

def ttnov(o: TValue) -> int:
    """lobject.h:136"""
    return novariant(rttype(o))

def checktag(o: TValue, t: int) -> bool:
    """lobject.h:140"""
    return rttype(o) == t

def checktype(o: TValue, t: int) -> bool:
    """lobject.h:141"""
    return ttnov(o) == t

def ttisnumber(o: TValue) -> bool:
    """lobject.h:142"""
    return checktype(o, LUA_TNUMBER)

def ttisfloat(o: TValue) -> bool:
    """lobject.h:143"""
    return checktag(o, LUA_TNUMFLT)

def ttisinteger(o: TValue) -> bool:
    """lobject.h:144"""
    return checktag(o, LUA_TNUMINT)

def ttisnil(o: TValue) -> bool:
    """lobject.h:145"""
    return checktag(o, LUA_TNIL)

def ttisboolean(o: TValue) -> bool:
    """lobject.h:146"""
    return checktag(o, LUA_TBOOLEAN)

def ttislightuserdata(o: TValue) -> bool:
    """lobject.h:147"""
    return checktag(o, LUA_TLIGHTUSERDATA)

def ttisstring(o: TValue) -> bool:
    """lobject.h:148"""
    return checktype(o, LUA_TSTRING)

def ttisshrstring(o: TValue) -> bool:
    """lobject.h:149"""
    return checktag(o, ctb(LUA_TSHRSTR))

def ttislngstring(o: TValue) -> bool:
    """lobject.h:150"""
    return checktag(o, ctb(LUA_TLNGSTR))

def ttistable(o: TValue) -> bool:
    """lobject.h:151"""
    return checktag(o, ctb(LUA_TTABLE))

def ttisfunction(o: TValue) -> bool:
    """lobject.h:152"""
    return checktype(o, LUA_TFUNCTION)

def ttisclosure(o: TValue) -> bool:
    """lobject.h:153"""
    return (rttype(o) & 0x1F) == LUA_TFUNCTION

def ttisCclosure(o: TValue) -> bool:
    """lobject.h:154"""
    return checktag(o, ctb(LUA_TCCL))

def ttisLclosure(o: TValue) -> bool:
    """lobject.h:155"""
    return checktag(o, ctb(LUA_TLCL))

def ttislcf(o: TValue) -> bool:
    """lobject.h:156"""
    return checktag(o, LUA_TLCF)

def ttisfulluserdata(o: TValue) -> bool:
    """lobject.h:157"""
    return checktag(o, ctb(LUA_TUSERDATA))

def ttisthread(o: TValue) -> bool:
    """lobject.h:158"""
    return checktag(o, ctb(LUA_TTHREAD))

def ttisdeadkey(o: TValue) -> bool:
    """lobject.h:159"""
    return checktag(o, LUA_TDEADKEY)

def ivalue(o: TValue) -> lua_Integer:
    """lobject.h:163"""
    return check_exp(ttisinteger(o), val_(o).i)

def fltvalue(o: TValue) -> lua_Number:
    """lobject.h:164"""
    return check_exp(ttisfloat(o), val_(o).n)

def nvalue(o: TValue) -> lua_Number:
    """lobject.h:165-166"""
    check_exp(ttisnumber(o), None)
    if ttisinteger(o):
        return cast_num(val_(o).i)
    return val_(o).n

def gcvalue(o: TValue) -> GCObject:
    """lobject.h:167"""
    return check_exp(iscollectable(o), val_(o).gc)

def pvalue(o: TValue) -> Any:
    """lobject.h:168"""
    return check_exp(ttislightuserdata(o), val_(o).p)

def fvalue(o: TValue) -> lua_CFunction:
    """lobject.h:174"""
    return check_exp(ttislcf(o), val_(o).f)

def bvalue(o: TValue) -> int:
    """lobject.h:176"""
    return check_exp(ttisboolean(o), val_(o).b)

def deadvalue(o: TValue) -> Any:
    """lobject.h:179"""
    return check_exp(ttisdeadkey(o), val_(o).gc)

def l_isfalse(o: TValue) -> bool:
    """lobject.h:181"""
    return ttisnil(o) or (ttisboolean(o) and bvalue(o) == 0)

def iscollectable(o: TValue) -> bool:
    """lobject.h:184"""
    return bool(rttype(o) & BIT_ISCOLLECTABLE)

def righttt(obj: TValue) -> bool:
    """lobject.h:188"""
    return ttype(obj) == gcvalue(obj).tt

def checkliveness(L: Any, obj: TValue) -> None:
    """lobject.h:190-192"""
    pass  # TODO: Implement with GC

# =============================================================================
# lobject.h:195-282 - Value Setting Macros
# =============================================================================
def settt_(o: TValue, t: int) -> None:
    """lobject.h:196"""
    o.tt_ = t

def setfltvalue(obj: TValue, x: lua_Number) -> None:
    """lobject.h:198-199"""
    val_(obj).n = x
    settt_(obj, LUA_TNUMFLT)

def chgfltvalue(obj: TValue, x: lua_Number) -> None:
    """lobject.h:201-202"""
    lua_assert(ttisfloat(obj))
    val_(obj).n = x

def setivalue(obj: TValue, x: lua_Integer) -> None:
    """lobject.h:204-205"""
    val_(obj).i = x
    settt_(obj, LUA_TNUMINT)

def chgivalue(obj: TValue, x: lua_Integer) -> None:
    """lobject.h:207-208"""
    lua_assert(ttisinteger(obj))
    val_(obj).i = x

def setnilvalue(obj: TValue) -> None:
    """lobject.h:210"""
    settt_(obj, LUA_TNIL)

def setfvalue(obj: TValue, x: lua_CFunction) -> None:
    """lobject.h:212-213"""
    val_(obj).f = x
    settt_(obj, LUA_TLCF)

def setpvalue(obj: TValue, x: Any) -> None:
    """lobject.h:215-216"""
    val_(obj).p = x
    settt_(obj, LUA_TLIGHTUSERDATA)

def setbvalue(obj: TValue, x: int) -> None:
    """lobject.h:218-219"""
    val_(obj).b = x
    settt_(obj, LUA_TBOOLEAN)

def setgcovalue(L: 'LuaState', obj: TValue, x: GCObject) -> None:
    """lobject.h:221-223"""
    val_(obj).gc = x
    settt_(obj, ctb(x.tt))

def setdeadvalue(obj: TValue) -> None:
    """lobject.h:255"""
    settt_(obj, LUA_TDEADKEY)

def setobj(L: 'LuaState', obj1: TValue, obj2: TValue) -> None:
    """lobject.h:259-261"""
    obj1.value_.gc = obj2.value_.gc
    obj1.value_.p = obj2.value_.p
    obj1.value_.b = obj2.value_.b
    obj1.value_.f = obj2.value_.f
    obj1.value_.i = obj2.value_.i
    obj1.value_.n = obj2.value_.n
    obj1.tt_ = obj2.tt_
    checkliveness(L, obj1)

setobjs2s = setobj  # lobject.h:269
setobj2s = setobj   # lobject.h:271
setobjt2t = setobj  # lobject.h:276
setobj2n = setobj   # lobject.h:278

def setobj2t(L: 'LuaState', o1: TValue, o2: TValue) -> None:
    """lobject.h:282"""
    setobj(L, o1, o2)

StkId = int  # lobject.h:294

# =============================================================================
# lobject.h:299-339 - String Types (TString)
# =============================================================================
@dataclass
class TString(GCObject):
    """lobject.h:303-312 - Header for string value"""
    extra: int = 0           # lobject.h:305 - reserved words for short; has hash for long
    shrlen: int = 0          # lobject.h:306 - length for short strings
    hash: int = 0            # lobject.h:307 - string hash
    lnglen: int = 0          # lobject.h:309 - length for long strings (union u)
    hnext: Optional['TString'] = None  # lobject.h:310 - hash table chain (union u)
    data: bytes = b""        # actual string bytes (follows struct in C)

def getstr(ts: 'TString') -> bytes:
    """lobject.h:328-329"""
    return ts.data

def tsslen(s: 'TString') -> int:
    """lobject.h:336"""
    if s.tt == LUA_TSHRSTR:
        return s.shrlen
    return s.lnglen

# =============================================================================
# lobject.h:342-380 - Userdata Types
# =============================================================================
@dataclass
class Udata(GCObject):
    """lobject.h:346-352 - Header for userdata"""
    ttuv_: int = 0                      # lobject.h:348 - user value's tag
    metatable: Optional['Table'] = None # lobject.h:349 - metatable
    len: int = 0                        # lobject.h:350 - number of bytes
    user_: Value = field(default_factory=Value)  # lobject.h:351 - user value
    data: Any = None                    # actual userdata memory

def getudatamem(u: 'Udata') -> Any:
    """lobject.h:368-369"""
    return u.data

def setuservalue(L: 'LuaState', u: 'Udata', o: TValue) -> None:
    """lobject.h:371-374"""
    u.user_.gc = o.value_.gc
    u.user_.p = o.value_.p
    u.user_.b = o.value_.b
    u.user_.f = o.value_.f
    u.user_.i = o.value_.i
    u.user_.n = o.value_.n
    u.ttuv_ = rttype(o)
    checkliveness(L, o)

def getuservalue(L: 'LuaState', u: 'Udata', o: TValue) -> None:
    """lobject.h:377-380"""
    o.value_.gc = u.user_.gc
    o.value_.p = u.user_.p
    o.value_.b = u.user_.b
    o.value_.f = u.user_.f
    o.value_.i = u.user_.i
    o.value_.n = u.user_.n
    settt_(o, u.ttuv_)
    checkliveness(L, o)

# =============================================================================
# lobject.h:383-401 - Upvalue and Local Variable Descriptions
# =============================================================================
@dataclass
class Upvaldesc:
    """lobject.h:386-390 - Description of an upvalue for function prototypes"""
    name: Optional['TString'] = None  # lobject.h:387 - upvalue name
    instack: int = 0                  # lobject.h:388 - whether in stack
    idx: int = 0                      # lobject.h:389 - index

@dataclass
class LocVar:
    """lobject.h:397-401 - Description of a local variable"""
    varname: Optional['TString'] = None  # lobject.h:398 - variable name
    startpc: int = 0                     # lobject.h:399 - activation point
    endpc: int = 0                       # lobject.h:400 - deactivation point

# =============================================================================
# lobject.h:404-429 - Function Prototype (Proto)
# =============================================================================
@dataclass
class Proto(GCObject):
    """lobject.h:407-429 - Function Prototype structure"""
    numparams: int = 0           # lobject.h:409 - number of fixed parameters
    is_vararg: int = 0           # lobject.h:410 - is vararg function
    maxstacksize: int = 0        # lobject.h:411 - registers needed
    sizeupvalues: int = 0        # lobject.h:412 - upvalues array size
    sizek: int = 0               # lobject.h:413 - constants array size
    sizecode: int = 0            # lobject.h:414 - code array size
    sizelineinfo: int = 0        # lobject.h:415 - lineinfo array size
    sizep: int = 0               # lobject.h:416 - nested protos size
    sizelocvars: int = 0         # lobject.h:417 - local vars size
    linedefined: int = 0         # lobject.h:418 - first line defined
    lastlinedefined: int = 0     # lobject.h:419 - last line defined
    k: List[TValue] = field(default_factory=list)          # lobject.h:420
    code: List[Instruction] = field(default_factory=list)  # lobject.h:421
    p: List['Proto'] = field(default_factory=list)         # lobject.h:422
    lineinfo: List[int] = field(default_factory=list)      # lobject.h:423
    locvars: List[LocVar] = field(default_factory=list)    # lobject.h:424
    upvalues: List[Upvaldesc] = field(default_factory=list)  # lobject.h:425
    cache: Optional['LClosure'] = None  # lobject.h:426
    source: Optional['TString'] = None  # lobject.h:427
    gclist: Optional[GCObject] = None   # lobject.h:428

# =============================================================================
# lfunc.h:35-47 / lobject.h:433-463 - Upvalues and Closures
# =============================================================================
@dataclass
class UpVal:
    """lfunc.h:35-45 - Upvalues for Lua closures"""
    v: Optional[TValue] = None   # lfunc.h:36 - points to stack or own value
    refcount: int = 0            # lfunc.h:37 - reference counter
    next: Optional['UpVal'] = None  # lfunc.h:40 - open: linked list
    touched: int = 0                # lfunc.h:41 - open: mark for cycles
    value: TValue = field(default_factory=TValue)  # lfunc.h:43 - closed: the value

def upisopen(up: 'UpVal') -> bool:
    """lfunc.h:47"""
    return up.v is not up.value

@dataclass
class CClosure(GCObject):
    """lobject.h:446-450 - C Closure"""
    nupvalues: int = 0                      # lobject.h:444
    gclist: Optional[GCObject] = None       # lobject.h:444
    f: Optional[lua_CFunction] = None       # lobject.h:448
    upvalue: List[TValue] = field(default_factory=list)  # lobject.h:449

@dataclass
class LClosure(GCObject):
    """lobject.h:453-457 - Lua Closure"""
    nupvalues: int = 0                      # lobject.h:444
    gclist: Optional[GCObject] = None       # lobject.h:444
    p: Optional[Proto] = None               # lobject.h:455
    upvals: List[Optional[UpVal]] = field(default_factory=list)  # lobject.h:456

Closure = Union[CClosure, LClosure]  # lobject.h:460-463

def isLfunction(o: TValue) -> bool:
    """lobject.h:466"""
    return ttisLclosure(o)

def getproto(o: TValue) -> Proto:
    """lobject.h:468"""
    return clLvalue(o).p

# =============================================================================
# lobject.h:471-507 - Tables
# =============================================================================
@dataclass
class TKey:
    """lobject.h:475-481 - Table key union"""
    value_: Value = field(default_factory=Value)  # TValuefields
    tt_: int = LUA_TNIL                           # TValuefields
    next: int = 0  # lobject.h:478 - for chaining

def setnodekey(L: 'LuaState', key: 'TKey', obj: TValue) -> None:
    """lobject.h:485-488"""
    key.value_.gc = obj.value_.gc
    key.value_.p = obj.value_.p
    key.value_.b = obj.value_.b
    key.value_.f = obj.value_.f
    key.value_.i = obj.value_.i
    key.value_.n = obj.value_.n
    key.tt_ = obj.tt_
    checkliveness(L, obj)

@dataclass
class Node:
    """lobject.h:491-494 - Table node"""
    i_val: TValue = field(default_factory=TValue)  # lobject.h:492
    i_key: TKey = field(default_factory=TKey)      # lobject.h:493

@dataclass
class Table(GCObject):
    """lobject.h:497-507 - Table structure"""
    flags: int = 0              # lobject.h:499
    lsizenode: int = 0          # lobject.h:500
    sizearray: int = 0          # lobject.h:501
    array: List[TValue] = field(default_factory=list)   # lobject.h:502
    node: List[Node] = field(default_factory=list)      # lobject.h:503
    lastfree: int = 0           # lobject.h:504
    metatable: Optional['Table'] = None  # lobject.h:505
    gclist: Optional[GCObject] = None    # lobject.h:506

def lmod(s: int, size: int) -> int:
    """lobject.h:514-515"""
    check_exp((size & (size - 1)) == 0, None)
    return cast_int(s & (size - 1))

def twoto(x: int) -> int:
    """lobject.h:518"""
    return 1 << x

def sizenode(t: 'Table') -> int:
    """lobject.h:519"""
    return twoto(t.lsizenode)

# =============================================================================
# lobject.h:522-531 - Nil Object and UTF8 Buffer
# =============================================================================
luaO_nilobject_: TValue = TValue(value_=Value(), tt_=LUA_TNIL)  # lobject.h:528

def luaO_nilobject() -> TValue:
    """lobject.h:525"""
    return luaO_nilobject_

UTF8BUFFSZ: int = 8  # lobject.h:531

# =============================================================================
# lstate.h:222-239 / lobject.h:169-177 - GCObject Conversions
# =============================================================================
def cast_u(o: GCObject) -> Any:
    """lstate.h:222"""
    return o

def gco2ts(o: GCObject) -> 'TString':
    """lstate.h:225-226"""
    # In Python, just return the object directly (it's already a TString)
    if isinstance(o, TString):
        return o
    check_exp(novariant(o.tt) == LUA_TSTRING, None)
    return o  # type: ignore

def gco2u(o: GCObject) -> 'Udata':
    """lstate.h:227"""
    if isinstance(o, Udata):
        return o
    check_exp(o.tt == LUA_TUSERDATA, None)
    return o  # type: ignore

def gco2lcl(o: GCObject) -> 'LClosure':
    """lstate.h:228"""
    # In Python, o is the LClosure object directly
    if isinstance(o, LClosure):
        return o
    check_exp(o.tt == LUA_TLCL, None)
    return o  # type: ignore

def gco2ccl(o: GCObject) -> 'CClosure':
    """lstate.h:229"""
    if isinstance(o, CClosure):
        return o
    check_exp(o.tt == LUA_TCCL, None)
    return o  # type: ignore

def gco2cl(o: GCObject) -> Closure:
    """lstate.h:230-231"""
    if isinstance(o, LClosure):
        return o
    if isinstance(o, CClosure):
        return o
    check_exp(novariant(o.tt) == LUA_TFUNCTION, None)
    return o  # type: ignore

def gco2t(o: GCObject) -> 'Table':
    """lstate.h:232"""
    if isinstance(o, Table):
        return o
    check_exp(o.tt == LUA_TTABLE, None)
    return o  # type: ignore

def gco2p(o: GCObject) -> Proto:
    """lstate.h:233"""
    if isinstance(o, Proto):
        return o
    check_exp(o.tt == LUA_TPROTO, None)
    return o  # type: ignore

def gco2th(o: GCObject) -> 'LuaState':
    """lstate.h:234"""
    from .lstate import LuaState
    if isinstance(o, LuaState):
        return o
    check_exp(o.tt == LUA_TTHREAD, None)
    return o  # type: ignore

def obj2gco(v: GCObject) -> GCObject:
    """lstate.h:238-239"""
    check_exp(novariant(v.tt) < LUA_TDEADKEY, None)
    return v

def tsvalue(o: TValue) -> 'TString':
    """lobject.h:169"""
    return check_exp(ttisstring(o), gco2ts(val_(o).gc))

def uvalue(o: TValue) -> 'Udata':
    """lobject.h:170"""
    return check_exp(ttisfulluserdata(o), gco2u(val_(o).gc))

def clvalue(o: TValue) -> Closure:
    """lobject.h:171"""
    return check_exp(ttisclosure(o), gco2cl(val_(o).gc))

def clLvalue(o: TValue) -> 'LClosure':
    """lobject.h:172"""
    return check_exp(ttisLclosure(o), gco2lcl(val_(o).gc))

def clCvalue(o: TValue) -> 'CClosure':
    """lobject.h:173"""
    return check_exp(ttisCclosure(o), gco2ccl(val_(o).gc))

def hvalue(o: TValue) -> 'Table':
    """lobject.h:175"""
    return check_exp(ttistable(o), gco2t(val_(o).gc))

def thvalue(o: TValue) -> 'LuaState':
    """lobject.h:177"""
    return check_exp(ttisthread(o), gco2th(val_(o).gc))

# =============================================================================
# lobject.h:225-253 - Typed Value Setters
# =============================================================================
def setsvalue(L: 'LuaState', obj: TValue, x: 'TString') -> None:
    """lobject.h:225-228"""
    val_(obj).gc = obj2gco(x)
    settt_(obj, ctb(x.tt))
    checkliveness(L, obj)

setsvalue2s = setsvalue  # lobject.h:272
setsvalue2n = setsvalue  # lobject.h:279

def setuvalue(L: 'LuaState', obj: TValue, x: 'Udata') -> None:
    """lobject.h:230-233"""
    val_(obj).gc = obj2gco(x)
    settt_(obj, ctb(LUA_TUSERDATA))
    checkliveness(L, obj)

def setthvalue(L: 'LuaState', obj: TValue, x: 'LuaState') -> None:
    """lobject.h:235-238"""
    val_(obj).gc = obj2gco(x)
    settt_(obj, ctb(LUA_TTHREAD))
    checkliveness(L, obj)

def setclLvalue(L: 'LuaState', obj: TValue, x: 'LClosure') -> None:
    """lobject.h:240-243"""
    val_(obj).gc = obj2gco(x)
    settt_(obj, ctb(LUA_TLCL))
    checkliveness(L, obj)

def setclCvalue(L: 'LuaState', obj: TValue, x: 'CClosure') -> None:
    """lobject.h:245-248"""
    val_(obj).gc = obj2gco(x)
    settt_(obj, ctb(LUA_TCCL))
    checkliveness(L, obj)

def sethvalue(L: 'LuaState', obj: TValue, x: 'Table') -> None:
    """lobject.h:250-253"""
    val_(obj).gc = obj2gco(x)
    settt_(obj, ctb(LUA_TTABLE))
    checkliveness(L, obj)

sethvalue2s = sethvalue  # lobject.h:273

def setptvalue(L: 'LuaState', obj: TValue, x: Proto) -> None:
    """lobject.h:274 (implicit)"""
    val_(obj).gc = obj2gco(x)
    settt_(obj, ctb(LUA_TPROTO))
    checkliveness(L, obj)

setptvalue2s = setptvalue  # lobject.h:274

def svalue(o: TValue) -> bytes:
    """lobject.h:333 - get string bytes from TValue"""
    return getstr(tsvalue(o))

def vslen(o: TValue) -> int:
    """lobject.h:339 - get string length from TValue"""
    return tsslen(tsvalue(o))


# =============================================================================
# lobject.c - Object Utility Functions
# =============================================================================

def luaO_int2fb(x: int) -> int:
    """
    lobject.c:41-53 - converts an integer to a "floating point byte"
    represented as (eeeeexxx), where the real value is (1xxx) * 2^(eeeee - 1)
    if eeeee != 0 and (xxx) otherwise.
    
    Source: lobject.c:41-53
    """
    e = 0  # exponent
    if x < 8:
        return x
    while x >= (8 << 4):  # coarse steps
        x = (x + 0xf) >> 4  # x = ceil(x / 16)
        e += 4
    while x >= (8 << 1):  # fine steps
        x = (x + 1) >> 1  # x = ceil(x / 2)
        e += 1
    return ((e + 1) << 3) | (cast_int(x) - 8)


def luaO_fb2int(x: int) -> int:
    """
    lobject.c:57-59 - converts back from floating point byte
    
    Source: lobject.c:57-59
    """
    if x < 8:
        return x
    return ((x & 7) + 8) << ((x >> 3) - 1)


# lobject.c:66-75 - log_2 table for ceillog2
_luaO_log_2: List[int] = [
    0,1,2,2,3,3,3,3,4,4,4,4,4,4,4,4,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,
    6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,
    7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,
    7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,
    8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,
    8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,
    8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,
    8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8
]


def luaO_ceillog2(x: int) -> int:
    """
    lobject.c:65-80 - Computes ceil(log2(x))
    
    Source: lobject.c:65-80
    """
    l = 0
    x -= 1
    while x >= 256:
        l += 8
        x >>= 8
    return l + _luaO_log_2[x] if x >= 0 else l


def luaO_hexavalue(c: int) -> int:
    """
    lobject.c:163-166 - get hex digit value
    
    Source: lobject.c:163-166
    """
    if ord('0') <= c <= ord('9'):
        return c - ord('0')
    else:
        return (c | 0x20) - ord('a') + 10  # tolower and compute


def luaO_utf8esc(buff: bytearray, x: int) -> int:
    """
    lobject.c:346-361 - UTF-8 escape sequence
    
    Returns number of bytes put in buffer (backwards from end)
    
    Source: lobject.c:346-361
    """
    n = 1  # number of bytes put in buffer (backwards)
    lua_assert(x <= 0x10FFFF)
    if x < 0x80:  # ascii?
        buff[UTF8BUFFSZ - 1] = x
    else:  # need continuation bytes
        mfb = 0x3f  # maximum that fits in first byte
        while True:  # add continuation bytes
            buff[UTF8BUFFSZ - n] = 0x80 | (x & 0x3f)
            n += 1
            x >>= 6  # remove added bits
            mfb >>= 1  # now there is one less bit available in first byte
            if x <= mfb:
                break
        buff[UTF8BUFFSZ - n] = ((~mfb << 1) & 0xFF) | x  # add first byte
    return n


# lobject.c:478-483 - String formatting constants
RETS: str = "..."
PRE: str = '[string "'
POS: str = '"]'


def luaO_chunkid(source: str, bufflen: int) -> str:
    """
    lobject.c:487-521 - Format chunk id for error messages
    
    Source: lobject.c:487-521
    """
    l = len(source)
    if not source:
        return ""
    
    if source[0] == '=':  # 'literal' source
        if l <= bufflen:
            return source[1:]
        else:
            return source[1:bufflen]
    
    elif source[0] == '@':  # file name
        if l <= bufflen:
            return source[1:]
        else:  # add '...' before rest of name
            return RETS + source[1 + l - (bufflen - len(RETS)):]
    
    else:  # string; format as [string "source"]
        nl_pos = source.find('\n')  # find first new line
        out = PRE
        remain = bufflen - len(PRE) - len(RETS) - len(POS) - 1
        
        if l < remain and nl_pos == -1:  # small one-line source?
            out += source
        else:
            if nl_pos != -1:
                l = nl_pos
            if l > remain:
                l = remain
            out += source[:l] + RETS
        
        out += POS
        return out


# =============================================================================
# lobject.c:331-343 - luaO_str2num
# =============================================================================

def luaO_str2num(s: bytes, o: TValue) -> int:
    """
    lobject.c:331-343 - Convert string to number
    
    size_t luaO_str2num (const char *s, TValue *o)
    
    Try as integer first, then as float.
    Returns length of converted string (including trailing '\\0'), or 0 on failure.
    
    Source: lobject.c:331-343
    """
    if not s:
        return 0
    
    try:
        text = s.decode('utf-8').strip()
    except UnicodeDecodeError:
        return 0
    
    if not text:
        return 0
    
    # Try as integer first - lobject.c:334-336
    result = _l_str2int(text)
    if result is not None:
        setivalue(o, result)
        return len(s) + 1
    
    # Try as float - lobject.c:337-339
    result = _l_str2d(text)
    if result is not None:
        setfltvalue(o, result)
        return len(s) + 1
    
    return 0  # conversion failed


def _l_str2int(s: str) -> Optional[lua_Integer]:
    """
    lobject.c:299-328 - Try to convert string to integer
    
    Handles decimal and hexadecimal integers.
    Returns None on failure.
    """
    s = s.strip()
    if not s:
        return None
    
    neg = False
    idx = 0
    
    # Check for sign
    if s[idx] == '-':
        neg = True
        idx += 1
    elif s[idx] == '+':
        idx += 1
    
    if idx >= len(s):
        return None
    
    # Check for hex
    if idx + 1 < len(s) and s[idx] == '0' and s[idx + 1] in 'xX':
        # Hexadecimal - lobject.c:305-316
        idx += 2
        if idx >= len(s):
            return None
        
        a = 0
        while idx < len(s) and s[idx] in '0123456789abcdefABCDEF':
            a = a * 16 + int(s[idx], 16)
            idx += 1
    else:
        # Decimal - lobject.c:318-321
        if not s[idx].isdigit():
            return None
        
        a = 0
        while idx < len(s) and s[idx].isdigit():
            a = a * 10 + int(s[idx])
            idx += 1
    
    # Skip trailing spaces
    while idx < len(s) and s[idx].isspace():
        idx += 1
    
    # Check nothing left - lobject.c:323
    if idx != len(s):
        return None
    
    # Apply sign and check overflow
    if neg:
        a = -a
    
    # Check bounds
    if a < LUA_MININTEGER or a > LUA_MAXINTEGER:
        return None
    
    return a


def _l_str2d(s: str) -> Optional[lua_Number]:
    """
    lobject.c:274-293 - Try to convert string to float
    
    Handles decimal and hexadecimal floats.
    Returns None on failure.
    """
    s = s.strip()
    if not s:
        return None
    
    # Reject 'inf' and 'nan' - lobject.c:278-279
    lower = s.lower()
    if 'inf' in lower or 'nan' in lower:
        return None
    
    try:
        # Python's float() handles most cases including hex floats
        # Check for hex float
        if '0x' in lower or '0X' in s:
            # Python 3 supports hex float literals with float.fromhex
            # But format is different: Python uses 0x1.5p+5, Lua uses 0x1.5p5
            return _parse_hex_float(s)
        else:
            return float(s)
    except (ValueError, OverflowError):
        return None


def _parse_hex_float(s: str) -> Optional[lua_Number]:
    """
    Parse hexadecimal floating point number (Lua format)
    
    Lua format: 0x1.8p10 or 0x1.8p+10 or 0x1.8p-10
    """
    s = s.strip().lower()
    
    neg = False
    if s.startswith('-'):
        neg = True
        s = s[1:]
    elif s.startswith('+'):
        s = s[1:]
    
    if not s.startswith('0x'):
        return None
    
    s = s[2:]  # Remove 0x
    
    # Split by 'p' for exponent
    if 'p' in s:
        mantissa_str, exp_str = s.split('p', 1)
    else:
        mantissa_str = s
        exp_str = '0'
    
    # Parse mantissa (may have decimal point)
    if '.' in mantissa_str:
        int_part, frac_part = mantissa_str.split('.', 1)
    else:
        int_part = mantissa_str
        frac_part = ''
    
    # Convert hex mantissa to value
    try:
        int_val = int(int_part, 16) if int_part else 0
        frac_val = 0.0
        for i, c in enumerate(frac_part):
            frac_val += int(c, 16) / (16.0 ** (i + 1))
        
        mantissa = float(int_val) + frac_val
        
        # Parse exponent
        exp = int(exp_str) if exp_str else 0
        
        # Result = mantissa * 2^exp
        result = mantissa * (2.0 ** exp)
        
        if neg:
            result = -result
        
        return result
    except (ValueError, OverflowError):
        return None
