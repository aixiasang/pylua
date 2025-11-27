# -*- coding: utf-8 -*-
"""
lopcodes.py - Opcodes for Lua virtual machine
=============================================
Source: lopcodes.h/lopcodes.c (lua-5.3.6/src/lopcodes.h, lopcodes.c)

Opcodes for Lua virtual machine
See Copyright Notice in lua.h
"""

from typing import List
from enum import IntEnum

from .llimits import Instruction, cast, cast_int, lu_byte

# =============================================================================
# lopcodes.h:13-29 - Instruction Format Description
# =============================================================================
# We assume that instructions are unsigned numbers.
# All instructions have an opcode in the first 6 bits.
# Instructions can have the following fields:
#   'A' : 8 bits
#   'B' : 9 bits
#   'C' : 9 bits
#   'Ax' : 26 bits ('A', 'B', and 'C' together)
#   'Bx' : 18 bits ('B' and 'C' together)
#   'sBx' : signed Bx
#
# A signed argument is represented in excess K; that is, the number
# value is the unsigned value minus K. K is exactly the maximum value
# for that argument (so that -max is represented by 0, and +max is
# represented by 2*max), which is half the maximum for the corresponding
# unsigned argument.

# =============================================================================
# lopcodes.h:32 - Instruction Modes
# =============================================================================
class OpMode(IntEnum):
    """lopcodes.h:32 - enum OpMode - basic instruction format"""
    iABC = 0   # lopcodes.h:32
    iABx = 1   # lopcodes.h:32
    iAsBx = 2  # lopcodes.h:32
    iAx = 3    # lopcodes.h:32

# =============================================================================
# lopcodes.h:35-51 - Size and Position of Opcode Arguments
# =============================================================================
SIZE_C: int = 9       # lopcodes.h:38
SIZE_B: int = 9       # lopcodes.h:39
SIZE_Bx: int = SIZE_C + SIZE_B  # lopcodes.h:40 = 18
SIZE_A: int = 8       # lopcodes.h:41
SIZE_Ax: int = SIZE_C + SIZE_B + SIZE_A  # lopcodes.h:42 = 26
SIZE_OP: int = 6      # lopcodes.h:44

POS_OP: int = 0                   # lopcodes.h:46
POS_A: int = POS_OP + SIZE_OP     # lopcodes.h:47 = 6
POS_C: int = POS_A + SIZE_A       # lopcodes.h:48 = 14
POS_B: int = POS_C + SIZE_C       # lopcodes.h:49 = 23
POS_Bx: int = POS_C               # lopcodes.h:50 = 14
POS_Ax: int = POS_A               # lopcodes.h:51 = 6

# =============================================================================
# lopcodes.h:54-76 - Limits for Opcode Arguments
# =============================================================================
# lopcodes.h:60-61
MAXARG_Bx: int = (1 << SIZE_Bx) - 1      # lopcodes.h:60 = 262143
MAXARG_sBx: int = MAXARG_Bx >> 1         # lopcodes.h:61 = 131071 (signed)

# lopcodes.h:68
MAXARG_Ax: int = (1 << SIZE_Ax) - 1      # lopcodes.h:68 = 67108863

# lopcodes.h:74-76
MAXARG_A: int = (1 << SIZE_A) - 1        # lopcodes.h:74 = 255
MAXARG_B: int = (1 << SIZE_B) - 1        # lopcodes.h:75 = 511
MAXARG_C: int = (1 << SIZE_C) - 1        # lopcodes.h:76 = 511

# =============================================================================
# lopcodes.h:79-83 - Mask Macros
# =============================================================================
def MASK1(n: int, p: int) -> int:
    """
    lopcodes.h:80 - creates a mask with 'n' 1 bits at position 'p'
    #define MASK1(n,p) ((~((~(Instruction)0)<<(n)))<<(p))
    """
    return ((~((~0) << n)) & 0xFFFFFFFF) << p

def MASK0(n: int, p: int) -> int:
    """
    lopcodes.h:83 - creates a mask with 'n' 0 bits at position 'p'
    #define MASK0(n,p) (~MASK1(n,p))
    """
    return (~MASK1(n, p)) & 0xFFFFFFFF

# =============================================================================
# lopcodes.h:85-127 - Instruction Manipulation Macros
# =============================================================================
def GET_OPCODE(i: Instruction) -> int:
    """
    lopcodes.h:89 - #define GET_OPCODE(i) (cast(OpCode, ((i)>>POS_OP) & MASK1(SIZE_OP,0)))
    """
    return (i >> POS_OP) & MASK1(SIZE_OP, 0)

def SET_OPCODE(i: Instruction, o: int) -> Instruction:
    """
    lopcodes.h:90-91 - SET_OPCODE
    #define SET_OPCODE(i,o) ((i) = (((i)&MASK0(SIZE_OP,POS_OP)) | \
            ((cast(Instruction, o)<<POS_OP)&MASK1(SIZE_OP,POS_OP))))
    """
    return ((i & MASK0(SIZE_OP, POS_OP)) | 
            ((o << POS_OP) & MASK1(SIZE_OP, POS_OP)))

def getarg(i: Instruction, pos: int, size: int) -> int:
    """
    lopcodes.h:93 - #define getarg(i,pos,size) (cast(int, ((i)>>pos) & MASK1(size,0)))
    """
    return cast_int((i >> pos) & MASK1(size, 0))

def setarg(i: Instruction, v: int, pos: int, size: int) -> Instruction:
    """
    lopcodes.h:94-95 - setarg
    #define setarg(i,v,pos,size) ((i) = (((i)&MASK0(size,pos)) | \
                ((cast(Instruction, v)<<pos)&MASK1(size,pos))))
    """
    return ((i & MASK0(size, pos)) | 
            ((v << pos) & MASK1(size, pos)))

def GETARG_A(i: Instruction) -> int:
    """lopcodes.h:97 - #define GETARG_A(i) getarg(i, POS_A, SIZE_A)"""
    return getarg(i, POS_A, SIZE_A)

def SETARG_A(i: Instruction, v: int) -> Instruction:
    """lopcodes.h:98 - #define SETARG_A(i,v) setarg(i, v, POS_A, SIZE_A)"""
    return setarg(i, v, POS_A, SIZE_A)

def GETARG_B(i: Instruction) -> int:
    """lopcodes.h:100 - #define GETARG_B(i) getarg(i, POS_B, SIZE_B)"""
    return getarg(i, POS_B, SIZE_B)

def SETARG_B(i: Instruction, v: int) -> Instruction:
    """lopcodes.h:101 - #define SETARG_B(i,v) setarg(i, v, POS_B, SIZE_B)"""
    return setarg(i, v, POS_B, SIZE_B)

def GETARG_C(i: Instruction) -> int:
    """lopcodes.h:103 - #define GETARG_C(i) getarg(i, POS_C, SIZE_C)"""
    return getarg(i, POS_C, SIZE_C)

def SETARG_C(i: Instruction, v: int) -> Instruction:
    """lopcodes.h:104 - #define SETARG_C(i,v) setarg(i, v, POS_C, SIZE_C)"""
    return setarg(i, v, POS_C, SIZE_C)

def GETARG_Bx(i: Instruction) -> int:
    """lopcodes.h:106 - #define GETARG_Bx(i) getarg(i, POS_Bx, SIZE_Bx)"""
    return getarg(i, POS_Bx, SIZE_Bx)

def SETARG_Bx(i: Instruction, v: int) -> Instruction:
    """lopcodes.h:107 - #define SETARG_Bx(i,v) setarg(i, v, POS_Bx, SIZE_Bx)"""
    return setarg(i, v, POS_Bx, SIZE_Bx)

def GETARG_Ax(i: Instruction) -> int:
    """lopcodes.h:109 - #define GETARG_Ax(i) getarg(i, POS_Ax, SIZE_Ax)"""
    return getarg(i, POS_Ax, SIZE_Ax)

def SETARG_Ax(i: Instruction, v: int) -> Instruction:
    """lopcodes.h:110 - #define SETARG_Ax(i,v) setarg(i, v, POS_Ax, SIZE_Ax)"""
    return setarg(i, v, POS_Ax, SIZE_Ax)

def GETARG_sBx(i: Instruction) -> int:
    """lopcodes.h:112 - #define GETARG_sBx(i) (GETARG_Bx(i)-MAXARG_sBx)"""
    return GETARG_Bx(i) - MAXARG_sBx

def SETARG_sBx(i: Instruction, b: int) -> Instruction:
    """lopcodes.h:113 - #define SETARG_sBx(i,b) SETARG_Bx((i),cast(unsigned int, (b)+MAXARG_sBx))"""
    return SETARG_Bx(i, (b + MAXARG_sBx) & 0xFFFFFFFF)

def CREATE_ABC(o: int, a: int, b: int, c: int) -> Instruction:
    """
    lopcodes.h:116-119 - CREATE_ABC
    #define CREATE_ABC(o,a,b,c) ((cast(Instruction, o)<<POS_OP) \
                | (cast(Instruction, a)<<POS_A) \
                | (cast(Instruction, b)<<POS_B) \
                | (cast(Instruction, c)<<POS_C))
    """
    return ((o << POS_OP) | (a << POS_A) | (b << POS_B) | (c << POS_C))

def CREATE_ABx(o: int, a: int, bc: int) -> Instruction:
    """
    lopcodes.h:121-123 - CREATE_ABx
    #define CREATE_ABx(o,a,bc) ((cast(Instruction, o)<<POS_OP) \
                | (cast(Instruction, a)<<POS_A) \
                | (cast(Instruction, bc)<<POS_Bx))
    """
    return ((o << POS_OP) | (a << POS_A) | (bc << POS_Bx))

def CREATE_Ax(o: int, a: int) -> Instruction:
    """
    lopcodes.h:125-126 - CREATE_Ax
    #define CREATE_Ax(o,a) ((cast(Instruction, o)<<POS_OP) \
                | (cast(Instruction, a)<<POS_Ax))
    """
    return ((o << POS_OP) | (a << POS_Ax))

# =============================================================================
# lopcodes.h:129-147 - RK (Register/Constant) Macros
# =============================================================================
# lopcodes.h:134 - this bit 1 means constant (0 means register)
BITRK: int = 1 << (SIZE_B - 1)  # = 256

def ISK(x: int) -> bool:
    """lopcodes.h:137 - #define ISK(x) ((x) & BITRK) - test whether value is a constant"""
    return bool(x & BITRK)

def INDEXK(r: int) -> int:
    """lopcodes.h:140 - #define INDEXK(r) ((int)(r) & ~BITRK) - gets the index of the constant"""
    return r & (~BITRK)

MAXINDEXRK: int = BITRK - 1  # lopcodes.h:143 = 255

def RKASK(x: int) -> int:
    """lopcodes.h:147 - #define RKASK(x) ((x) | BITRK) - code a constant index as a RK value"""
    return x | BITRK

# =============================================================================
# lopcodes.h:150-153 - Invalid Register
# =============================================================================
NO_REG: int = MAXARG_A  # lopcodes.h:153 = 255

# =============================================================================
# lopcodes.h:167-234 - OpCode Enumeration
# =============================================================================
class OpCode(IntEnum):
    """
    lopcodes.h:167-234 - Lua VM opcodes
    
    R(x) - register
    Kst(x) - constant (in constant table)
    RK(x) == if ISK(x) then Kst(INDEXK(x)) else R(x)
    """
    # lopcodes.h:171 - A B    R(A) := R(B)
    OP_MOVE = 0
    # lopcodes.h:172 - A Bx   R(A) := Kst(Bx)
    OP_LOADK = 1
    # lopcodes.h:173 - A      R(A) := Kst(extra arg)
    OP_LOADKX = 2
    # lopcodes.h:174 - A B C  R(A) := (Bool)B; if (C) pc++
    OP_LOADBOOL = 3
    # lopcodes.h:175 - A B    R(A), R(A+1), ..., R(A+B) := nil
    OP_LOADNIL = 4
    # lopcodes.h:176 - A B    R(A) := UpValue[B]
    OP_GETUPVAL = 5
    # lopcodes.h:178 - A B C  R(A) := UpValue[B][RK(C)]
    OP_GETTABUP = 6
    # lopcodes.h:179 - A B C  R(A) := R(B)[RK(C)]
    OP_GETTABLE = 7
    # lopcodes.h:181 - A B C  UpValue[A][RK(B)] := RK(C)
    OP_SETTABUP = 8
    # lopcodes.h:182 - A B    UpValue[B] := R(A)
    OP_SETUPVAL = 9
    # lopcodes.h:183 - A B C  R(A)[RK(B)] := RK(C)
    OP_SETTABLE = 10
    # lopcodes.h:185 - A B C  R(A) := {} (size = B,C)
    OP_NEWTABLE = 11
    # lopcodes.h:187 - A B C  R(A+1) := R(B); R(A) := R(B)[RK(C)]
    OP_SELF = 12
    # lopcodes.h:189 - A B C  R(A) := RK(B) + RK(C)
    OP_ADD = 13
    # lopcodes.h:190 - A B C  R(A) := RK(B) - RK(C)
    OP_SUB = 14
    # lopcodes.h:191 - A B C  R(A) := RK(B) * RK(C)
    OP_MUL = 15
    # lopcodes.h:192 - A B C  R(A) := RK(B) % RK(C)
    OP_MOD = 16
    # lopcodes.h:193 - A B C  R(A) := RK(B) ^ RK(C)
    OP_POW = 17
    # lopcodes.h:194 - A B C  R(A) := RK(B) / RK(C)
    OP_DIV = 18
    # lopcodes.h:195 - A B C  R(A) := RK(B) // RK(C)
    OP_IDIV = 19
    # lopcodes.h:196 - A B C  R(A) := RK(B) & RK(C)
    OP_BAND = 20
    # lopcodes.h:197 - A B C  R(A) := RK(B) | RK(C)
    OP_BOR = 21
    # lopcodes.h:198 - A B C  R(A) := RK(B) ~ RK(C)
    OP_BXOR = 22
    # lopcodes.h:199 - A B C  R(A) := RK(B) << RK(C)
    OP_SHL = 23
    # lopcodes.h:200 - A B C  R(A) := RK(B) >> RK(C)
    OP_SHR = 24
    # lopcodes.h:201 - A B    R(A) := -R(B)
    OP_UNM = 25
    # lopcodes.h:202 - A B    R(A) := ~R(B)
    OP_BNOT = 26
    # lopcodes.h:203 - A B    R(A) := not R(B)
    OP_NOT = 27
    # lopcodes.h:204 - A B    R(A) := length of R(B)
    OP_LEN = 28
    # lopcodes.h:206 - A B C  R(A) := R(B).. ... ..R(C)
    OP_CONCAT = 29
    # lopcodes.h:208 - A sBx  pc+=sBx; if (A) close all upvalues >= R(A - 1)
    OP_JMP = 30
    # lopcodes.h:209 - A B C  if ((RK(B) == RK(C)) ~= A) then pc++
    OP_EQ = 31
    # lopcodes.h:210 - A B C  if ((RK(B) <  RK(C)) ~= A) then pc++
    OP_LT = 32
    # lopcodes.h:211 - A B C  if ((RK(B) <= RK(C)) ~= A) then pc++
    OP_LE = 33
    # lopcodes.h:213 - A C    if not (R(A) <=> C) then pc++
    OP_TEST = 34
    # lopcodes.h:214 - A B C  if (R(B) <=> C) then R(A) := R(B) else pc++
    OP_TESTSET = 35
    # lopcodes.h:216 - A B C  R(A), ... ,R(A+C-2) := R(A)(R(A+1), ... ,R(A+B-1))
    OP_CALL = 36
    # lopcodes.h:217 - A B C  return R(A)(R(A+1), ... ,R(A+B-1))
    OP_TAILCALL = 37
    # lopcodes.h:218 - A B    return R(A), ... ,R(A+B-2)
    OP_RETURN = 38
    # lopcodes.h:220-221 - A sBx  R(A)+=R(A+2); if R(A) <?= R(A+1) then { pc+=sBx; R(A+3)=R(A) }
    OP_FORLOOP = 39
    # lopcodes.h:222 - A sBx  R(A)-=R(A+2); pc+=sBx
    OP_FORPREP = 40
    # lopcodes.h:224 - A C    R(A+3), ... ,R(A+2+C) := R(A)(R(A+1), R(A+2));
    OP_TFORCALL = 41
    # lopcodes.h:225 - A sBx  if R(A+1) ~= nil then { R(A)=R(A+1); pc += sBx }
    OP_TFORLOOP = 42
    # lopcodes.h:227 - A B C  R(A)[(C-1)*FPF+i] := R(A+i), 1 <= i <= B
    OP_SETLIST = 43
    # lopcodes.h:229 - A Bx   R(A) := closure(KPROTO[Bx])
    OP_CLOSURE = 44
    # lopcodes.h:231 - A B    R(A), R(A+1), ..., R(A+B-2) = vararg
    OP_VARARG = 45
    # lopcodes.h:233 - Ax     extra (larger) argument for previous opcode
    OP_EXTRAARG = 46

# lopcodes.h:237 - #define NUM_OPCODES (cast(int, OP_EXTRAARG) + 1)
NUM_OPCODES: int = int(OpCode.OP_EXTRAARG) + 1  # = 47

# =============================================================================
# lopcodes.h:274-279 - Argument Mask Types
# =============================================================================
class OpArgMask(IntEnum):
    """lopcodes.h:274-279 - enum OpArgMask"""
    OpArgN = 0  # lopcodes.h:275 - argument is not used
    OpArgU = 1  # lopcodes.h:276 - argument is used
    OpArgR = 2  # lopcodes.h:277 - argument is a register or a jump offset
    OpArgK = 3  # lopcodes.h:278 - argument is a constant or register/constant

# =============================================================================
# lopcodes.h:265-287 - Opcode Mode Information
# =============================================================================
# lopcodes.h:265-272:
# masks for instruction properties. The format is:
# bits 0-1: op mode
# bits 2-3: C arg mode
# bits 4-5: B arg mode
# bit 6: instruction set register A
# bit 7: operator is a test (next instruction must be a jump)

def getOpMode(m: int) -> OpMode:
    """lopcodes.h:283 - #define getOpMode(m) (cast(enum OpMode, luaP_opmodes[m] & 3))"""
    return OpMode(luaP_opmodes[m] & 3)

def getBMode(m: int) -> OpArgMask:
    """lopcodes.h:284 - #define getBMode(m) (cast(enum OpArgMask, (luaP_opmodes[m] >> 4) & 3))"""
    return OpArgMask((luaP_opmodes[m] >> 4) & 3)

def getCMode(m: int) -> OpArgMask:
    """lopcodes.h:285 - #define getCMode(m) (cast(enum OpArgMask, (luaP_opmodes[m] >> 2) & 3))"""
    return OpArgMask((luaP_opmodes[m] >> 2) & 3)

def testAMode(m: int) -> bool:
    """lopcodes.h:286 - #define testAMode(m) (luaP_opmodes[m] & (1 << 6))"""
    return bool(luaP_opmodes[m] & (1 << 6))

def testTMode(m: int) -> bool:
    """lopcodes.h:287 - #define testTMode(m) (luaP_opmodes[m] & (1 << 7))"""
    return bool(luaP_opmodes[m] & (1 << 7))

# =============================================================================
# lopcodes.h:293-294 - SETLIST Fields Per Flush
# =============================================================================
LFIELDS_PER_FLUSH: int = 50  # lopcodes.h:294

# =============================================================================
# lopcodes.c:20-69 - Opcode Names
# =============================================================================
# lopcodes.c:20-68 - LUAI_DDEF const char *const luaP_opnames[NUM_OPCODES+1]
luaP_opnames: List[str] = [
    "MOVE",      # lopcodes.c:21
    "LOADK",     # lopcodes.c:22
    "LOADKX",    # lopcodes.c:23
    "LOADBOOL",  # lopcodes.c:24
    "LOADNIL",   # lopcodes.c:25
    "GETUPVAL",  # lopcodes.c:26
    "GETTABUP",  # lopcodes.c:27
    "GETTABLE",  # lopcodes.c:28
    "SETTABUP",  # lopcodes.c:29
    "SETUPVAL",  # lopcodes.c:30
    "SETTABLE",  # lopcodes.c:31
    "NEWTABLE",  # lopcodes.c:32
    "SELF",      # lopcodes.c:33
    "ADD",       # lopcodes.c:34
    "SUB",       # lopcodes.c:35
    "MUL",       # lopcodes.c:36
    "MOD",       # lopcodes.c:37
    "POW",       # lopcodes.c:38
    "DIV",       # lopcodes.c:39
    "IDIV",      # lopcodes.c:40
    "BAND",      # lopcodes.c:41
    "BOR",       # lopcodes.c:42
    "BXOR",      # lopcodes.c:43
    "SHL",       # lopcodes.c:44
    "SHR",       # lopcodes.c:45
    "UNM",       # lopcodes.c:46
    "BNOT",      # lopcodes.c:47
    "NOT",       # lopcodes.c:48
    "LEN",       # lopcodes.c:49
    "CONCAT",    # lopcodes.c:50
    "JMP",       # lopcodes.c:51
    "EQ",        # lopcodes.c:52
    "LT",        # lopcodes.c:53
    "LE",        # lopcodes.c:54
    "TEST",      # lopcodes.c:55
    "TESTSET",   # lopcodes.c:56
    "CALL",      # lopcodes.c:57
    "TAILCALL",  # lopcodes.c:58
    "RETURN",    # lopcodes.c:59
    "FORLOOP",   # lopcodes.c:60
    "FORPREP",   # lopcodes.c:61
    "TFORCALL",  # lopcodes.c:62
    "TFORLOOP",  # lopcodes.c:63
    "SETLIST",   # lopcodes.c:64
    "CLOSURE",   # lopcodes.c:65
    "VARARG",    # lopcodes.c:66
    "EXTRAARG",  # lopcodes.c:67
    None,        # lopcodes.c:68 - NULL terminator
]

# =============================================================================
# lopcodes.c:72-123 - Opcode Modes
# =============================================================================
def opmode(t: int, a: int, b: int, c: int, m: int) -> int:
    """
    lopcodes.c:72 - #define opmode(t,a,b,c,m) (((t)<<7) | ((a)<<6) | ((b)<<4) | ((c)<<2) | (m))
    """
    return ((t << 7) | (a << 6) | (b << 4) | (c << 2) | m)

# lopcodes.c:74-123 - LUAI_DDEF const lu_byte luaP_opmodes[NUM_OPCODES]
# Format: opmode(T, A, B, C, mode)
#   T: is test (next instruction must be jump)
#   A: instruction sets register A
#   B: B argument mode (OpArgMask)
#   C: C argument mode (OpArgMask)
#   mode: instruction mode (OpMode)

luaP_opmodes: List[int] = [
    # lopcodes.c:76  - OP_MOVE:     T=0, A=1, B=OpArgR, C=OpArgN, mode=iABC
    opmode(0, 1, OpArgMask.OpArgR, OpArgMask.OpArgN, OpMode.iABC),
    # lopcodes.c:77  - OP_LOADK:    T=0, A=1, B=OpArgK, C=OpArgN, mode=iABx
    opmode(0, 1, OpArgMask.OpArgK, OpArgMask.OpArgN, OpMode.iABx),
    # lopcodes.c:78  - OP_LOADKX:   T=0, A=1, B=OpArgN, C=OpArgN, mode=iABx
    opmode(0, 1, OpArgMask.OpArgN, OpArgMask.OpArgN, OpMode.iABx),
    # lopcodes.c:79  - OP_LOADBOOL: T=0, A=1, B=OpArgU, C=OpArgU, mode=iABC
    opmode(0, 1, OpArgMask.OpArgU, OpArgMask.OpArgU, OpMode.iABC),
    # lopcodes.c:80  - OP_LOADNIL:  T=0, A=1, B=OpArgU, C=OpArgN, mode=iABC
    opmode(0, 1, OpArgMask.OpArgU, OpArgMask.OpArgN, OpMode.iABC),
    # lopcodes.c:81  - OP_GETUPVAL: T=0, A=1, B=OpArgU, C=OpArgN, mode=iABC
    opmode(0, 1, OpArgMask.OpArgU, OpArgMask.OpArgN, OpMode.iABC),
    # lopcodes.c:82  - OP_GETTABUP: T=0, A=1, B=OpArgU, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgU, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:83  - OP_GETTABLE: T=0, A=1, B=OpArgR, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgR, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:84  - OP_SETTABUP: T=0, A=0, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 0, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:85  - OP_SETUPVAL: T=0, A=0, B=OpArgU, C=OpArgN, mode=iABC
    opmode(0, 0, OpArgMask.OpArgU, OpArgMask.OpArgN, OpMode.iABC),
    # lopcodes.c:86  - OP_SETTABLE: T=0, A=0, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 0, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:87  - OP_NEWTABLE: T=0, A=1, B=OpArgU, C=OpArgU, mode=iABC
    opmode(0, 1, OpArgMask.OpArgU, OpArgMask.OpArgU, OpMode.iABC),
    # lopcodes.c:88  - OP_SELF:     T=0, A=1, B=OpArgR, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgR, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:89  - OP_ADD:      T=0, A=1, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:90  - OP_SUB:      T=0, A=1, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:91  - OP_MUL:      T=0, A=1, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:92  - OP_MOD:      T=0, A=1, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:93  - OP_POW:      T=0, A=1, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:94  - OP_DIV:      T=0, A=1, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:95  - OP_IDIV:     T=0, A=1, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:96  - OP_BAND:     T=0, A=1, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:97  - OP_BOR:      T=0, A=1, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:98  - OP_BXOR:     T=0, A=1, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:99  - OP_SHL:      T=0, A=1, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:100 - OP_SHR:      T=0, A=1, B=OpArgK, C=OpArgK, mode=iABC
    opmode(0, 1, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:101 - OP_UNM:      T=0, A=1, B=OpArgR, C=OpArgN, mode=iABC
    opmode(0, 1, OpArgMask.OpArgR, OpArgMask.OpArgN, OpMode.iABC),
    # lopcodes.c:102 - OP_BNOT:     T=0, A=1, B=OpArgR, C=OpArgN, mode=iABC
    opmode(0, 1, OpArgMask.OpArgR, OpArgMask.OpArgN, OpMode.iABC),
    # lopcodes.c:103 - OP_NOT:      T=0, A=1, B=OpArgR, C=OpArgN, mode=iABC
    opmode(0, 1, OpArgMask.OpArgR, OpArgMask.OpArgN, OpMode.iABC),
    # lopcodes.c:104 - OP_LEN:      T=0, A=1, B=OpArgR, C=OpArgN, mode=iABC
    opmode(0, 1, OpArgMask.OpArgR, OpArgMask.OpArgN, OpMode.iABC),
    # lopcodes.c:105 - OP_CONCAT:   T=0, A=1, B=OpArgR, C=OpArgR, mode=iABC
    opmode(0, 1, OpArgMask.OpArgR, OpArgMask.OpArgR, OpMode.iABC),
    # lopcodes.c:106 - OP_JMP:      T=0, A=0, B=OpArgR, C=OpArgN, mode=iAsBx
    opmode(0, 0, OpArgMask.OpArgR, OpArgMask.OpArgN, OpMode.iAsBx),
    # lopcodes.c:107 - OP_EQ:       T=1, A=0, B=OpArgK, C=OpArgK, mode=iABC
    opmode(1, 0, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:108 - OP_LT:       T=1, A=0, B=OpArgK, C=OpArgK, mode=iABC
    opmode(1, 0, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:109 - OP_LE:       T=1, A=0, B=OpArgK, C=OpArgK, mode=iABC
    opmode(1, 0, OpArgMask.OpArgK, OpArgMask.OpArgK, OpMode.iABC),
    # lopcodes.c:110 - OP_TEST:     T=1, A=0, B=OpArgN, C=OpArgU, mode=iABC
    opmode(1, 0, OpArgMask.OpArgN, OpArgMask.OpArgU, OpMode.iABC),
    # lopcodes.c:111 - OP_TESTSET:  T=1, A=1, B=OpArgR, C=OpArgU, mode=iABC
    opmode(1, 1, OpArgMask.OpArgR, OpArgMask.OpArgU, OpMode.iABC),
    # lopcodes.c:112 - OP_CALL:     T=0, A=1, B=OpArgU, C=OpArgU, mode=iABC
    opmode(0, 1, OpArgMask.OpArgU, OpArgMask.OpArgU, OpMode.iABC),
    # lopcodes.c:113 - OP_TAILCALL: T=0, A=1, B=OpArgU, C=OpArgU, mode=iABC
    opmode(0, 1, OpArgMask.OpArgU, OpArgMask.OpArgU, OpMode.iABC),
    # lopcodes.c:114 - OP_RETURN:   T=0, A=0, B=OpArgU, C=OpArgN, mode=iABC
    opmode(0, 0, OpArgMask.OpArgU, OpArgMask.OpArgN, OpMode.iABC),
    # lopcodes.c:115 - OP_FORLOOP:  T=0, A=1, B=OpArgR, C=OpArgN, mode=iAsBx
    opmode(0, 1, OpArgMask.OpArgR, OpArgMask.OpArgN, OpMode.iAsBx),
    # lopcodes.c:116 - OP_FORPREP:  T=0, A=1, B=OpArgR, C=OpArgN, mode=iAsBx
    opmode(0, 1, OpArgMask.OpArgR, OpArgMask.OpArgN, OpMode.iAsBx),
    # lopcodes.c:117 - OP_TFORCALL: T=0, A=0, B=OpArgN, C=OpArgU, mode=iABC
    opmode(0, 0, OpArgMask.OpArgN, OpArgMask.OpArgU, OpMode.iABC),
    # lopcodes.c:118 - OP_TFORLOOP: T=0, A=1, B=OpArgR, C=OpArgN, mode=iAsBx
    opmode(0, 1, OpArgMask.OpArgR, OpArgMask.OpArgN, OpMode.iAsBx),
    # lopcodes.c:119 - OP_SETLIST:  T=0, A=0, B=OpArgU, C=OpArgU, mode=iABC
    opmode(0, 0, OpArgMask.OpArgU, OpArgMask.OpArgU, OpMode.iABC),
    # lopcodes.c:120 - OP_CLOSURE:  T=0, A=1, B=OpArgU, C=OpArgN, mode=iABx
    opmode(0, 1, OpArgMask.OpArgU, OpArgMask.OpArgN, OpMode.iABx),
    # lopcodes.c:121 - OP_VARARG:   T=0, A=1, B=OpArgU, C=OpArgN, mode=iABC
    opmode(0, 1, OpArgMask.OpArgU, OpArgMask.OpArgN, OpMode.iABC),
    # lopcodes.c:122 - OP_EXTRAARG: T=0, A=0, B=OpArgU, C=OpArgU, mode=iAx
    opmode(0, 0, OpArgMask.OpArgU, OpArgMask.OpArgU, OpMode.iAx),
]
