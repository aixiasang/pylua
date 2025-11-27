# -*- coding: utf-8 -*-
"""
compile.py - PyLua Compiler Interface

Provides a clean interface for compiling Lua source code using lparser + lcode.
Compatible with luac53 output format.

Source: Combines functionality from lparser.c, lcode.c, and ldump.c
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass, field

from .llex import (
    LexState, SemInfo, Token, luaX_next, luaX_newstring,
    TK_EOS, EOZ
)
from .lparser import (
    FuncState, Dyndata, expdesc, BlockCnt,
    open_func, close_func, statlist, check, init_exp, newupvalue,
    VLOCAL
)
from .lobject import TString, Proto, LClosure, TValue, Table
from .lfunc import luaF_newLclosure, luaF_newproto
from .lopcodes import OpCode, GET_OPCODE, GETARG_A, GETARG_B, GETARG_C, GETARG_Bx, GETARG_sBx


# Opcode name mapping (using OpCode enum)
OPCODE_NAMES = {
    OpCode.OP_MOVE: "MOVE",
    OpCode.OP_LOADK: "LOADK",
    OpCode.OP_LOADKX: "LOADKX",
    OpCode.OP_LOADBOOL: "LOADBOOL",
    OpCode.OP_LOADNIL: "LOADNIL",
    OpCode.OP_GETUPVAL: "GETUPVAL",
    OpCode.OP_GETTABUP: "GETTABUP",
    OpCode.OP_GETTABLE: "GETTABLE",
    OpCode.OP_SETTABUP: "SETTABUP",
    OpCode.OP_SETUPVAL: "SETUPVAL",
    OpCode.OP_SETTABLE: "SETTABLE",
    OpCode.OP_NEWTABLE: "NEWTABLE",
    OpCode.OP_SELF: "SELF",
    OpCode.OP_ADD: "ADD",
    OpCode.OP_SUB: "SUB",
    OpCode.OP_MUL: "MUL",
    OpCode.OP_MOD: "MOD",
    OpCode.OP_POW: "POW",
    OpCode.OP_DIV: "DIV",
    OpCode.OP_IDIV: "IDIV",
    OpCode.OP_BAND: "BAND",
    OpCode.OP_BOR: "BOR",
    OpCode.OP_BXOR: "BXOR",
    OpCode.OP_SHL: "SHL",
    OpCode.OP_SHR: "SHR",
    OpCode.OP_UNM: "UNM",
    OpCode.OP_BNOT: "BNOT",
    OpCode.OP_NOT: "NOT",
    OpCode.OP_LEN: "LEN",
    OpCode.OP_CONCAT: "CONCAT",
    OpCode.OP_JMP: "JMP",
    OpCode.OP_EQ: "EQ",
    OpCode.OP_LT: "LT",
    OpCode.OP_LE: "LE",
    OpCode.OP_TEST: "TEST",
    OpCode.OP_TESTSET: "TESTSET",
    OpCode.OP_CALL: "CALL",
    OpCode.OP_TAILCALL: "TAILCALL",
    OpCode.OP_RETURN: "RETURN",
    OpCode.OP_FORLOOP: "FORLOOP",
    OpCode.OP_FORPREP: "FORPREP",
    OpCode.OP_TFORCALL: "TFORCALL",
    OpCode.OP_TFORLOOP: "TFORLOOP",
    OpCode.OP_SETLIST: "SETLIST",
    OpCode.OP_CLOSURE: "CLOSURE",
    OpCode.OP_VARARG: "VARARG",
    OpCode.OP_EXTRAARG: "EXTRAARG",
}


@dataclass
class CompiledInstruction:
    """Compiled instruction representation"""
    pc: int              # Program counter (1-based)
    line: int            # Source line number
    opcode: int          # Opcode value
    opname: str          # Opcode name
    a: int = 0           # A argument
    b: int = 0           # B argument
    c: int = 0           # C argument
    bx: int = 0          # Bx argument
    sbx: int = 0         # sBx argument
    raw: int = 0         # Raw instruction


@dataclass
class CompiledProto:
    """Compiled function prototype"""
    source: str = ""
    line_start: int = 0
    line_end: int = 0
    num_params: int = 0
    is_vararg: bool = False
    max_stack: int = 0
    num_upvalues: int = 0
    instructions: List[CompiledInstruction] = field(default_factory=list)
    constants: List[Tuple[int, any]] = field(default_factory=list)
    locals: List[Tuple[str, int, int]] = field(default_factory=list)
    upvalues: List[Tuple[str, int, int]] = field(default_factory=list)
    children: List['CompiledProto'] = field(default_factory=list)
    
    # Aliases for compatibility with ldump
    @property
    def linedefined(self) -> int:
        return self.line_start
    
    @property
    def lastlinedefined(self) -> int:
        return self.line_end
    
    @property
    def numparams(self) -> int:
        return self.num_params
    
    @property
    def maxstacksize(self) -> int:
        return self.max_stack
    
    @property
    def code(self) -> List[int]:
        """Return raw instruction codes"""
        return [inst.raw for inst in self.instructions]
    
    @property
    def lineinfo(self) -> List[int]:
        """Return line info for each instruction"""
        return [inst.line for inst in self.instructions]
    
    @property
    def locvars(self) -> List[Tuple[str, int, int]]:
        """Return local variables"""
        return self.locals
    
    @property
    def protos(self) -> List['CompiledProto']:
        """Return nested prototypes"""
        return self.children


class MockLuaState:
    """Mock LuaState for compilation"""
    def __init__(self):
        self.stack = [TValue() for _ in range(1000)]
        self.top = 0
        self.l_G = None
        self.ci = None
        self.nCcalls = 0
        self.nny = 0


class SimpleZIO:
    """Simple ZIO implementation"""
    def __init__(self, data: bytes):
        self.p = data[1:] if len(data) > 1 else b''
        self.n = len(self.p)
        self.reader = None
        self.data = None


def compile_source(source: str, name: str = "input") -> Tuple[Optional[LClosure], str]:
    """
    Compile Lua source code using PyLua
    
    Returns: (LClosure or None, error message)
    """
    try:
        source_bytes = source.encode('utf-8')
        
        L = MockLuaState()
        
        # Create LexState
        ls = LexState()
        ls.z = SimpleZIO(source_bytes)
        
        # Create source name
        ts = TString()
        ts.data = name.encode('utf-8')
        ls.source = ts
        
        # Initialize lexer
        if source_bytes:
            ls.current = source_bytes[0]
        else:
            ls.current = EOZ
        
        ls.linenumber = 1
        ls.lastline = 1
        ls.lookahead = Token()
        ls.lookahead.token = TK_EOS
        ls.t = Token()
        ls.t.seminfo = SemInfo()
        ls.buff = bytearray()
        ls.L = L
        
        # Create Dyndata
        dyd = Dyndata()
        ls.dyd = dyd
        
        # Create environment name
        envn = TString()
        envn.data = b"_ENV"
        ls.envn = envn
        
        # Create scanner table (mock)
        ls.h = Table()
        
        # Create main closure
        cl = luaF_newLclosure(L, 1)
        
        # Create FuncState
        fs = FuncState()
        fs.f = luaF_newproto(L)
        cl.p = fs.f
        fs.f.source = ts
        
        # Compile main function
        bl = BlockCnt()
        v = expdesc()
        
        open_func(ls, fs, bl)
        fs.f.is_vararg = 1
        init_exp(v, VLOCAL, 0)
        newupvalue(fs, ls.envn, v)
        
        luaX_next(ls)
        statlist(ls)
        check(ls, TK_EOS)
        close_func(ls)
        
        return cl, ""
    
    except Exception as e:
        import traceback
        return None, f"{type(e).__name__}: {e}\n{traceback.format_exc()}"


def decode_instruction(inst: int, lineinfo: int = 0) -> CompiledInstruction:
    """Decode a single instruction"""
    op = GET_OPCODE(inst)
    a = GETARG_A(inst)
    b = GETARG_B(inst)
    c = GETARG_C(inst)
    bx = GETARG_Bx(inst)
    sbx = GETARG_sBx(inst)
    
    return CompiledInstruction(
        pc=0,
        line=lineinfo,
        opcode=op,
        opname=OPCODE_NAMES.get(op, f"OP_{op}"),
        a=a, b=b, c=c, bx=bx, sbx=sbx,
        raw=inst
    )


def extract_proto(proto: Proto, depth: int = 0) -> CompiledProto:
    """Extract compilation info from Proto object"""
    cp = CompiledProto()
    
    if proto.source:
        cp.source = proto.source.data.decode('utf-8') if proto.source.data else ""
    cp.line_start = proto.linedefined
    cp.line_end = proto.lastlinedefined
    cp.num_params = proto.numparams
    cp.is_vararg = proto.is_vararg != 0
    cp.max_stack = proto.maxstacksize
    cp.num_upvalues = len(proto.upvalues) if proto.upvalues else 0
    
    # Extract instructions
    for i, inst in enumerate(proto.code):
        lineinfo = proto.lineinfo[i] if proto.lineinfo and i < len(proto.lineinfo) else 0
        ci = decode_instruction(inst, lineinfo)
        ci.pc = i + 1
        cp.instructions.append(ci)
    
    # Extract constants - determine correct value based on tt_ type tag
    # tt_ type definitions:
    # - LUA_TNUMINT = 19 (LUA_TNUMBER | (1 << 4))
    # - LUA_TNUMFLT = 3  (LUA_TNUMBER | (0 << 4))
    # - LUA_TSTRING = 4 (with BIT_ISCOLLECTABLE=64 becomes 68)
    # - LUA_TBOOLEAN = 1
    # - LUA_TNIL = 0
    for i, k in enumerate(proto.k):
        if hasattr(k, 'tt_') and hasattr(k, 'value_'):
            tt = k.tt_ & 0x3F  # Remove collectable flag
            base_tt = tt & 0x0F  # Base type
            
            if tt == 19:  # LUA_TNUMINT - integer
                cp.constants.append((i + 1, k.value_.i))
            elif tt == 3:  # LUA_TNUMFLT - float
                cp.constants.append((i + 1, k.value_.n))
            elif base_tt == 4:  # LUA_TSTRING - string
                if k.value_.gc and hasattr(k.value_.gc, 'data'):
                    val = k.value_.gc.data.decode('utf-8') if k.value_.gc.data else ""
                    cp.constants.append((i + 1, f'"{val}"'))
                else:
                    cp.constants.append((i + 1, str(k)))
            elif base_tt == 1:  # LUA_TBOOLEAN
                cp.constants.append((i + 1, bool(k.value_.b)))
            elif base_tt == 0:  # LUA_TNIL
                cp.constants.append((i + 1, "nil"))
            else:
                cp.constants.append((i + 1, str(k)))
        elif hasattr(k, 'value_'):
            # Fallback: try old-style detection
            if hasattr(k.value_, 'gc') and k.value_.gc and hasattr(k.value_.gc, 'data'):
                val = k.value_.gc.data.decode('utf-8') if k.value_.gc.data else ""
                cp.constants.append((i + 1, f'"{val}"'))
            elif hasattr(k.value_, 'n') and k.value_.n != 0.0:
                cp.constants.append((i + 1, k.value_.n))
            elif hasattr(k.value_, 'i'):
                cp.constants.append((i + 1, k.value_.i))
            else:
                cp.constants.append((i + 1, str(k)))
        else:
            cp.constants.append((i + 1, str(k)))
    
    # Extract local variables
    for i, lv in enumerate(proto.locvars):
        name = lv.varname.data.decode('utf-8') if lv.varname and lv.varname.data else f"var{i}"
        cp.locals.append((name, lv.startpc, lv.endpc))
    
    # Extract upvalues
    for i, uv in enumerate(proto.upvalues):
        name = uv.name.data.decode('utf-8') if uv.name and uv.name.data else f"upval{i}"
        cp.upvalues.append((name, uv.instack, uv.idx))
    
    # Recursively extract child functions
    for p in proto.p:
        cp.children.append(extract_proto(p, depth + 1))
    
    return cp


def format_compiled_proto(cp: CompiledProto, indent: int = 0) -> str:
    """Format compiled function prototype for display"""
    prefix = "  " * indent
    lines = []
    
    vararg = "+" if cp.is_vararg else ""
    lines.append(f"{prefix}function <{cp.source}:{cp.line_start},{cp.line_end}> "
                 f"({len(cp.instructions)} instructions)")
    lines.append(f"{prefix}{cp.num_params}{vararg} params, {cp.max_stack} slots, "
                 f"{cp.num_upvalues} upvalues, {len(cp.locals)} locals, "
                 f"{len(cp.constants)} constants, {len(cp.children)} functions")
    
    for inst in cp.instructions:
        lines.append(f"{prefix}  {inst.pc:4d} [{inst.line:3d}] {inst.opname:12s} "
                     f"{inst.a:4d} {inst.b:4d} {inst.c:4d}")
    
    if cp.constants:
        lines.append(f"{prefix}constants ({len(cp.constants)}):")
        for idx, val in cp.constants:
            lines.append(f"{prefix}  {idx}: {val}")
    
    if cp.locals:
        lines.append(f"{prefix}locals ({len(cp.locals)}):")
        for i, (name, start, end) in enumerate(cp.locals):
            lines.append(f"{prefix}  {i}: {name} [{start}-{end}]")
    
    if cp.upvalues:
        lines.append(f"{prefix}upvalues ({len(cp.upvalues)}):")
        for i, (name, instack, idx) in enumerate(cp.upvalues):
            lines.append(f"{prefix}  {i}: {name} (instack={instack}, idx={idx})")
    
    for child in cp.children:
        lines.append("")
        lines.append(format_compiled_proto(child, indent))
    
    return '\n'.join(lines)


def pylua_compile(source: str, name: str = "input") -> Tuple[Optional[CompiledProto], str]:
    """
    Compile Lua source code and return CompiledProto
    """
    cl, error = compile_source(source, name)
    if cl is None:
        return None, error
    
    if cl.p is None:
        return None, "No Proto generated"
    
    return extract_proto(cl.p), ""


def disassemble(proto: CompiledProto, 
                show_constants: bool = False,
                show_locals: bool = False, 
                show_upvalues: bool = False) -> str:
    """
    Disassemble a CompiledProto to human-readable format.
    
    Similar to `luac -l` output format.
    
    Args:
        proto: CompiledProto to disassemble
        show_constants: If True, show constants list
        show_locals: If True, show local variables
        show_upvalues: If True, show upvalues
    
    Returns:
        Disassembled bytecode as string
    """
    lines = []
    
    # Function header
    vararg = "+" if proto.is_vararg else ""
    lines.append(f"function <{proto.source}:{proto.line_start},{proto.line_end}> "
                 f"({len(proto.instructions)} instructions)")
    lines.append(f"{proto.num_params}{vararg} params, {proto.max_stack} slots, "
                 f"{proto.num_upvalues} upvalues, {len(proto.locals)} locals, "
                 f"{len(proto.constants)} constants, {len(proto.children)} functions")
    
    # Instructions - formatted like luac output
    for inst in proto.instructions:
        line_str = f"[{inst.line:3d}]" if inst.line else "[  0]"
        lines.append(f"    {inst.pc:4d}  {line_str}  {inst.opname:<12s}  {inst.a:4d} {inst.b:4d} {inst.c:4d}")
    
    # Constants
    if show_constants and proto.constants:
        lines.append(f"constants ({len(proto.constants)}):")
        for idx, val in proto.constants:
            lines.append(f"    {idx:4d}  {val}")
    
    # Locals
    if show_locals and proto.locals:
        lines.append(f"locals ({len(proto.locals)}):")
        for i, (name, start, end) in enumerate(proto.locals):
            lines.append(f"    {i:4d}  {name:<12s}  {start:4d}  {end:4d}")
    
    # Upvalues
    if show_upvalues and proto.upvalues:
        lines.append(f"upvalues ({len(proto.upvalues)}):")
        for i, (name, instack, idx) in enumerate(proto.upvalues):
            lines.append(f"    {i:4d}  {name:<12s}  {instack:4d}  {idx:4d}")
    
    # Nested functions
    for child in proto.children:
        lines.append("")
        lines.append(disassemble(child, show_constants, show_locals, show_upvalues))
    
    return '\n'.join(lines)
