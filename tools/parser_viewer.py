# -*- coding: utf-8 -*-
"""
parser_viewer.py - Parser Result Viewer

Provide interface to view and verify Parser output results, including:
- Bytecode instructions
- Constant table
- Local variables
- Upvalues
- Sub-functions

Can compare with Lua 5.3 luac -l output.

Based on Lua 5.3.6 official implementation.
Author: aixiasang
"""
import sys
import os
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylua.llex import (
    LexState, SemInfo, Token,
    luaX_next, luaX_setinput, luaX_newstring,
    TK_EOS, EOZ,
)
from pylua.lparser import (
    Dyndata, FuncState, expdesc, BlockCnt,
    ActvarList, Labellist, Vardesc, Labeldesc,
)
from pylua.lobject import TString, Proto, LClosure, LocVar
from pylua.lopcodes import (
    OpCode, GET_OPCODE, GETARG_A, GETARG_B, GETARG_C,
    GETARG_Bx, GETARG_sBx, GETARG_Ax,
    OpMode, getOpMode, getBMode, getCMode,
    OpArgMask,
)
from dataclasses import dataclass, field
from typing import Optional, List


# =============================================================================
# [comment removed]
# =============================================================================
OPCODE_NAMES = [
    "MOVE", "LOADK", "LOADKX", "LOADBOOL", "LOADNIL",
    "GETUPVAL", "GETTABUP", "GETTABLE",
    "SETTABUP", "SETUPVAL", "SETTABLE", "NEWTABLE",
    "SELF", "ADD", "SUB", "MUL", "MOD", "POW", "DIV", "IDIV",
    "BAND", "BOR", "BXOR", "SHL", "SHR",
    "UNM", "BNOT", "NOT", "LEN",
    "CONCAT", "JMP", "EQ", "LT", "LE",
    "TEST", "TESTSET", "CALL", "TAILCALL", "RETURN",
    "FORLOOP", "FORPREP", "TFORCALL", "TFORLOOP",
    "SETLIST", "CLOSURE", "VARARG", "EXTRAARG",
]


def opcode_name(op: int) -> str:
    """Get opcode name"""
    if 0 <= op < len(OPCODE_NAMES):
        return OPCODE_NAMES[op]
    return f"OP_{op}"


# =============================================================================
# [comment removed]
# =============================================================================
def format_instruction(inst: int, pc: int, f: Proto) -> str:
    """Format single instruction"""
    op = GET_OPCODE(inst)
    a = GETARG_A(inst)
    b = GETARG_B(inst)
    c = GETARG_C(inst)
    bx = GETARG_Bx(inst)
    sbx = GETARG_sBx(inst)
    
    name = opcode_name(op)
    
# [comment removed]
    if op == OpCode.OP_MOVE:
        return f"{name}\t{a} {b}"
    elif op == OpCode.OP_LOADK:
        k = f.k[bx] if bx < len(f.k) else "?"
        return f"{name}\t{a} {bx}\t; {format_constant(k)}"
    elif op == OpCode.OP_LOADKX:
        return f"{name}\t{a}"
    elif op == OpCode.OP_LOADBOOL:
        return f"{name}\t{a} {b} {c}"
    elif op == OpCode.OP_LOADNIL:
        return f"{name}\t{a} {b}"
    elif op == OpCode.OP_GETUPVAL:
        uname = f.upvalues[b].name.data.decode() if b < len(f.upvalues) and f.upvalues[b].name else f"upval{b}"
        return f"{name}\t{a} {b}\t; {uname}"
    elif op == OpCode.OP_GETTABUP:
        uname = f.upvalues[b].name.data.decode() if b < len(f.upvalues) and f.upvalues[b].name else f"upval{b}"
        if c & 0x100:  # ISK(c)
            k = f.k[c & 0xFF] if (c & 0xFF) < len(f.k) else "?"
            return f"{name}\t{a} {b} {c}\t; {uname} {format_constant(k)}"
        return f"{name}\t{a} {b} {c}\t; {uname}"
    elif op == OpCode.OP_GETTABLE:
        if c & 0x100:
            k = f.k[c & 0xFF] if (c & 0xFF) < len(f.k) else "?"
            return f"{name}\t{a} {b} {c}\t; {format_constant(k)}"
        return f"{name}\t{a} {b} {c}"
    elif op == OpCode.OP_SETTABUP:
        uname = f.upvalues[a].name.data.decode() if a < len(f.upvalues) and f.upvalues[a].name else f"upval{a}"
        return f"{name}\t{a} {b} {c}\t; {uname}"
    elif op == OpCode.OP_SETUPVAL:
        uname = f.upvalues[b].name.data.decode() if b < len(f.upvalues) and f.upvalues[b].name else f"upval{b}"
        return f"{name}\t{a} {b}\t; {uname}"
    elif op == OpCode.OP_SETTABLE:
        return f"{name}\t{a} {b} {c}"
    elif op == OpCode.OP_NEWTABLE:
        return f"{name}\t{a} {b} {c}"
    elif op == OpCode.OP_SELF:
        if c & 0x100:
            k = f.k[c & 0xFF] if (c & 0xFF) < len(f.k) else "?"
            return f"{name}\t{a} {b} {c}\t; {format_constant(k)}"
        return f"{name}\t{a} {b} {c}"
    elif op in (OpCode.OP_ADD, OpCode.OP_SUB, OpCode.OP_MUL, OpCode.OP_MOD,
                OpCode.OP_POW, OpCode.OP_DIV, OpCode.OP_IDIV,
                OpCode.OP_BAND, OpCode.OP_BOR, OpCode.OP_BXOR,
                OpCode.OP_SHL, OpCode.OP_SHR):
        return f"{name}\t{a} {b} {c}"
    elif op in (OpCode.OP_UNM, OpCode.OP_BNOT, OpCode.OP_NOT, OpCode.OP_LEN):
        return f"{name}\t{a} {b}"
    elif op == OpCode.OP_CONCAT:
        return f"{name}\t{a} {b} {c}"
    elif op == OpCode.OP_JMP:
        return f"{name}\t{a} {sbx}\t; to {pc + sbx + 2}"
    elif op in (OpCode.OP_EQ, OpCode.OP_LT, OpCode.OP_LE):
        return f"{name}\t{a} {b} {c}"
    elif op == OpCode.OP_TEST:
        return f"{name}\t{a} {c}"
    elif op == OpCode.OP_TESTSET:
        return f"{name}\t{a} {b} {c}"
    elif op == OpCode.OP_CALL:
        return f"{name}\t{a} {b} {c}"
    elif op == OpCode.OP_TAILCALL:
        return f"{name}\t{a} {b} {c}"
    elif op == OpCode.OP_RETURN:
        return f"{name}\t{a} {b}"
    elif op == OpCode.OP_FORLOOP:
        return f"{name}\t{a} {sbx}\t; to {pc + sbx + 2}"
    elif op == OpCode.OP_FORPREP:
        return f"{name}\t{a} {sbx}\t; to {pc + sbx + 2}"
    elif op == OpCode.OP_TFORCALL:
        return f"{name}\t{a} {c}"
    elif op == OpCode.OP_TFORLOOP:
        return f"{name}\t{a} {sbx}\t; to {pc + sbx + 2}"
    elif op == OpCode.OP_SETLIST:
        return f"{name}\t{a} {b} {c}"
    elif op == OpCode.OP_CLOSURE:
        return f"{name}\t{a} {bx}\t; {bx}"
    elif op == OpCode.OP_VARARG:
        return f"{name}\t{a} {b}"
    elif op == OpCode.OP_EXTRAARG:
        ax = GETARG_Ax(inst)
        return f"{name}\t{ax}"
    else:
        return f"{name}\t{a} {b} {c}"


def format_constant(k) -> str:
    """Format constant value"""
    if k is None:
        return "nil"
    if hasattr(k, 'tt_'):
        # TValue
        from pylua.lobject import ttisnil, ttisboolean, ttisinteger, ttisfloat, ttisstring
        from pylua.lobject import bvalue, ivalue, fltvalue
        if ttisnil(k):
            return "nil"
        elif ttisboolean(k):
            return "true" if bvalue(k) else "false"
        elif ttisinteger(k):
            return str(ivalue(k))
        elif ttisfloat(k):
            return str(fltvalue(k))
        elif ttisstring(k):
            s = k.value_.gc
            if hasattr(s, 'data'):
                return f'"{s.data.decode()}"'
            return str(s)
    if hasattr(k, 'data'):
        # TString
        return f'"{k.data.decode()}"'
    if isinstance(k, (int, float)):
        return str(k)
    if isinstance(k, str):
        return f'"{k}"'
    return str(k)


# =============================================================================
# [comment removed]
# =============================================================================
def dump_proto(f: Proto, level: int = 0, name: str = "main") -> None:
    """Print function prototype info"""
    indent = "  " * level
    
# [comment removed]
    source = f.source.data.decode() if f.source and f.source.data else "?"
    print(f"\n{indent}function <{source}:{f.linedefined},{f.lastlinedefined}> ({len(f.code)} instructions)")
    
# [comment removed]
    params = f.numparams
    vararg = "+" if f.is_vararg else ""
    print(f"{indent}{params}{vararg} params, {f.maxstacksize} slots, {len(f.upvalues)} upvalues, {len(f.locvars)} locals, {len(f.k)} constants, {len(f.p)} functions")
    
# [comment removed]
    for i, inst in enumerate(f.code):
        line = f.lineinfo[i] if i < len(f.lineinfo) else 0
        instr = format_instruction(inst, i, f)
        print(f"{indent}\t{i+1}\t[{line}]\t{instr}")
    
# [comment removed]
    if f.k:
        print(f"\n{indent}constants ({len(f.k)}):")
        for i, k in enumerate(f.k):
            print(f"{indent}\t{i+1}\t{format_constant(k)}")
    
# [comment removed]
    if f.locvars:
        print(f"\n{indent}locals ({len(f.locvars)}):")
        for i, v in enumerate(f.locvars):
            name = v.varname.data.decode() if v.varname and v.varname.data else f"var{i}"
            print(f"{indent}\t{i}\t{name}\t{v.startpc+1}\t{v.endpc+1}")
    
    # Upvalues
    if f.upvalues:
        print(f"\n{indent}upvalues ({len(f.upvalues)}):")
        for i, u in enumerate(f.upvalues):
            name = u.name.data.decode() if u.name and u.name.data else f"upval{i}"
            instack = "1" if u.instack else "0"
            print(f"{indent}\t{i}\t{name}\t{instack}\t{u.idx}")
    
# [comment removed]
    for i, p in enumerate(f.p):
        if p:
            dump_proto(p, level + 1, f"proto_{i}")


# =============================================================================
# [comment removed]
# =============================================================================
def luac_dump(source: str, source_name: str = "test.lua") -> str:
    """Get bytecode listing using luac -l"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as f:
        f.write(source)
        src_file = f.name
    
    try:
        result = subprocess.run(
            ['luac53', '-l', '-l', src_file],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode == 0:
            return result.stdout
        return f"Error: {result.stderr}"
    except FileNotFoundError:
        return "luac53 not found"
    except Exception as e:
        return f"Error: {e}"
    finally:
        try:
            os.unlink(src_file)
        except:
            pass


# =============================================================================
# [comment removed]
# =============================================================================
class SimpleParser:
    """Simple Parser wrapper for testing"""
    
    @staticmethod
    def parse_source(source: str, name: str = "test") -> Proto:
        """
        Parse Lua source code and return Proto
        
        Note: Full implementation requires integrating all components.
        This provides a simplified test interface.
        """
        raise NotImplementedError(
            "Full Parser implementation is in development.\n"
            "Please use luac to compile then load via lundump."
        )
    
    @staticmethod
    def tokenize(source: str) -> list:
        """Tokenize test"""
        from pylua.llex import (
            LexState, SemInfo, Token,
            luaX_next, TK_EOS, TK_NAME, TK_INT, TK_FLT, TK_STRING,
            FIRST_RESERVED, NUM_RESERVED, luaX_tokens, EOZ,
        )
        
        ls = LexState()
        source_bytes = source.encode('utf-8')
        
# [comment removed]
        class SimpleZIO:
            def __init__(self, data):
                self.p = data
                self.n = len(data)
                self.pos = 0
        
        ls.z = SimpleZIO(source_bytes)
        
# [comment removed]
        ts = TString()
        ts.data = b"test"
        ls.source = ts
        
# [comment removed]
        if source_bytes:
            ls.current = source_bytes[0]
            ls.z.p = source_bytes[1:]
            ls.z.n = len(source_bytes) - 1
        else:
            ls.current = EOZ
        
        ls.linenumber = 1
        ls.lastline = 1
        ls.lookahead = Token()
        ls.lookahead.token = TK_EOS
        ls.t = Token()
        ls.t.seminfo = SemInfo()
        ls.buff = bytearray()
        
        tokens = []
        while True:
            luaX_next(ls)
            tok = ls.t.token
            seminfo = ls.t.seminfo
            
            if tok == TK_EOS:
                tokens.append({'type': 'EOS', 'value': None, 'line': ls.linenumber})
                break
            elif tok == TK_INT:
                tokens.append({'type': 'INT', 'value': seminfo.i, 'line': ls.linenumber})
            elif tok == TK_FLT:
                tokens.append({'type': 'FLT', 'value': seminfo.r, 'line': ls.linenumber})
            elif tok == TK_STRING:
                val = seminfo.ts.data.decode() if seminfo.ts else ""
                tokens.append({'type': 'STRING', 'value': val, 'line': ls.linenumber})
            elif tok == TK_NAME:
                val = seminfo.ts.data.decode() if seminfo.ts else ""
                tokens.append({'type': 'NAME', 'value': val, 'line': ls.linenumber})
            elif tok >= FIRST_RESERVED and tok < FIRST_RESERVED + NUM_RESERVED:
                kw = luaX_tokens[tok - FIRST_RESERVED]
                tokens.append({'type': 'KEYWORD', 'value': kw, 'line': ls.linenumber})
            elif tok < 256:
                tokens.append({'type': 'CHAR', 'value': chr(tok), 'line': ls.linenumber})
            else:
# [comment removed]
                from pylua.llex import (
                    TK_IDIV, TK_CONCAT, TK_DOTS, TK_EQ, TK_GE, TK_LE, TK_NE,
                    TK_SHL, TK_SHR, TK_DBCOLON
                )
                token_names = {
                    TK_IDIV: '//',
                    TK_CONCAT: '..',
                    TK_DOTS: '...',
                    TK_EQ: '==',
                    TK_GE: '>=',
                    TK_LE: '<=',
                    TK_NE: '~=',
                    TK_SHL: '<<',
                    TK_SHR: '>>',
                    TK_DBCOLON: '::',
                }
                val = token_names.get(tok, f'TOKEN_{tok}')
                tokens.append({'type': 'OPERATOR', 'value': val, 'line': ls.linenumber})
        
        return tokens


# =============================================================================
# [comment removed]
# =============================================================================
def interactive_test():
    """Interactive test mode"""
    print("=" * 60)
    print("PyLua Parser Viewer")
    print("=" * 60)
    print("\nCommands:")
    print("  lex <code>   - Show lexical analysis result")
    print("  luac <code>  - Show Lua 5.3 compilation result")
    print("  file <path>  - Analyze file")
    print("  quit         - Exit")
    print()
    
    while True:
        try:
            line = input(">>> ").strip()
            if not line:
                continue
            
            if line.startswith("quit") or line.startswith("exit"):
                break
            
            if line.startswith("lex "):
                source = line[4:]
                print("\nLexical analysis result:")
                tokens = SimpleParser.tokenize(source)
                for tok in tokens:
                    print(f"  {tok['line']:3d}: {tok['type']:10s} {tok['value']}")
            
            elif line.startswith("luac "):
                source = line[5:]
                print("\nLua 5.3 compilation result:")
                result = luac_dump(source)
                print(result)
            
            elif line.startswith("file "):
                path = line[5:].strip()
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        source = f.read()
                    
                    print(f"\nFile: {path}")
                    print("-" * 40)
                    print("\nLexical analysis:")
                    tokens = SimpleParser.tokenize(source)
                    for tok in tokens[:20]:
                        print(f"  {tok['line']:3d}: {tok['type']:10s} {tok['value']}")
                    if len(tokens) > 20:
                        print(f"  ... total {len(tokens)} tokens")
                    
                    print("\nLua 5.3 compilation result:")
                    result = luac_dump(source, path)
                    print(result)
                else:
                    print(f"File not found: {path}")
            
            else:
                # Direct input, show both
                print("\nLexical analysis:")
                tokens = SimpleParser.tokenize(line)
                for tok in tokens:
                    print(f"  {tok['line']:3d}: {tok['type']:10s} {tok['value']}")
                
                print("\nLua 5.3 compilation result:")
                result = luac_dump(line)
                print(result)
        
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"Error: {e}")


# =============================================================================
# [comment removed]
# =============================================================================
def batch_test():
    """Batch test common Lua code"""
    print("=" * 60)
    print("PyLua Parser Batch Test")
    print("=" * 60)
    
    test_cases = [
        # Basic
        ("Simple add", "return 1 + 2"),
        ("Variable assignment", "local x = 10"),
        ("Multiple variables", "local a, b = 1, 2"),
        
        # Functions
        ("Simple function", "function foo() return 1 end"),
        ("Function with params", "function add(a, b) return a + b end"),
        ("Anonymous function", "local f = function(x) return x * 2 end"),
        
        # Control flow
        ("if statement", "if x then y = 1 end"),
        ("if-else", "if x then y = 1 else y = 2 end"),
        ("while loop", "while x do x = x - 1 end"),
        ("for loop", "for i = 1, 10 do print(i) end"),
        ("for-in loop", "for k, v in pairs(t) do print(k, v) end"),
        
        # Tables
        ("Empty table", "local t = {}"),
        ("List table", "local t = {1, 2, 3}"),
        ("Dict table", "local t = {x = 1, y = 2}"),
        ("Mixed table", "local t = {1, 2, x = 3}"),
        
        # Calls
        ("Method call", "obj:method()"),
        ("Chained call", "a.b.c.d"),
        
        # Operators
        ("Logical operation", "return a and b or c"),
        ("Bitwise operation", "return a & b | c"),
        ("String concat", "return 'hello' .. 'world'"),
    ]
    
    for name, source in test_cases:
        print(f"\n{'='*40}")
        print(f"Test: {name}")
        print(f"Code: {source}")
        print("-" * 40)
        
# [comment removed]
        print("Tokens:")
        tokens = SimpleParser.tokenize(source)
        for tok in tokens:
            print(f"  {tok['type']:10s} {repr(tok['value'])}")
        
# [comment removed]
        print("\nLuac output:")
        result = luac_dump(source)
# [comment removed]
        for line in result.split('\n'):
            if line.strip() and not line.startswith('main'):
                print(f"  {line}")


# =============================================================================
# Main
# =============================================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PyLua Parser Viewer")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--batch", "-b", action="store_true", help="Batch test")
    parser.add_argument("--file", "-f", type=str, help="Analyze specified file")
    parser.add_argument("--code", "-c", type=str, help="Analyze specified code")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_test()
    elif args.batch:
        batch_test()
    elif args.file:
        if os.path.exists(args.file):
            with open(args.file, 'r', encoding='utf-8') as f:
                source = f.read()
            print(f"File: {args.file}")
            print("=" * 60)
            print("\nLexical analysis:")
            tokens = SimpleParser.tokenize(source)
            for tok in tokens[:50]:
                print(f"  {tok['line']:3d}: {tok['type']:10s} {tok['value']}")
            if len(tokens) > 50:
                print(f"  ... total {len(tokens)} tokens")
            print("\nLuac compilation result:")
            print(luac_dump(source, args.file))
        else:
            print(f"File not found: {args.file}")
    elif args.code:
        print(f"Code: {args.code}")
        print("=" * 60)
        print("\nLexical analysis:")
        tokens = SimpleParser.tokenize(args.code)
        for tok in tokens:
            print(f"  {tok['line']:3d}: {tok['type']:10s} {tok['value']}")
        print("\nLuac compilation result:")
        print(luac_dump(args.code))
    else:
        # Default: run batch test
        batch_test()
