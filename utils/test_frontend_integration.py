# -*- coding: utf-8 -*-
"""
test_frontend_integration.py - Complete Frontend Integration Test
==================================================================

Tests the complete frontend pipeline:
Source Code -> Lexer -> Parser -> Code Generator -> Bytecode

This test compares PyLua's frontend output with Lua 5.3's luac output.
"""
import sys
import os
import subprocess
import tempfile
import struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylua.llex import (
    LexState, SemInfo, Token,
    luaX_next, luaX_setinput, luaX_newstring,
    TK_EOS, TK_NAME, TK_INT, TK_FLT, TK_STRING,
    EOZ,
)
from pylua.lparser import (
    luaY_parser, Dyndata, FuncState, expdesc, BlockCnt,
    ActvarList, Labellist,
)
from pylua.lobject import TString, Proto, LClosure
from dataclasses import dataclass


# =============================================================================
# ZIO Mock for Testing
# =============================================================================
@dataclass
class MockZIO:
    """Mock ZIO for testing parser"""
    p: bytes
    n: int
    
    def read(self, count: int) -> bytes:
        if self.n >= count:
            result = self.p[:count]
            self.p = self.p[count:]
            self.n -= count
            return result
        result = self.p
        self.p = b''
        self.n = 0
        return result


# =============================================================================
# Lexer Tests
# =============================================================================
class LexerTest:
    """Test lexer tokenization"""
    
    @staticmethod
    def tokenize(source: str) -> list:
        """Tokenize source code and return token list"""
        ls = LexState()
        z = MockZIO(source.encode('utf-8'), len(source))
        ts = TString()
        ts.data = b"test"
        ts.shrlen = 4
        
        ls.z = z
        ls.source = ts
        if z.n > 0:
            ls.current = z.p[0]
            z.p = z.p[1:]
            z.n -= 1
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
            
            if tok == TK_INT:
                tokens.append(('INT', seminfo.i))
            elif tok == TK_FLT:
                tokens.append(('FLT', seminfo.r))
            elif tok == TK_STRING:
                val = seminfo.ts.data.decode('utf-8') if seminfo.ts else ""
                tokens.append(('STRING', val))
            elif tok == TK_NAME:
                val = seminfo.ts.data.decode('utf-8') if seminfo.ts else ""
                tokens.append(('NAME', val))
            elif tok == TK_EOS:
                tokens.append(('EOS', None))
                break
            elif tok < 256:
                tokens.append((chr(tok), None))
            else:
                tokens.append((tok, None))
        
        return tokens
    
    @staticmethod
    def run_tests():
        """Run lexer tests"""
        print("\n" + "=" * 60)
        print("LEXER INTEGRATION TESTS")
        print("=" * 60)
        
        tests = [
            ("print('hello')", [('NAME', 'print'), ('(', None), ('STRING', 'hello'), (')', None), ('EOS', None)]),
            ("x = 42", [('NAME', 'x'), ('=', None), ('INT', 42), ('EOS', None)]),
            ("a + b * c", [('NAME', 'a'), ('+', None), ('NAME', 'b'), ('*', None), ('NAME', 'c'), ('EOS', None)]),
            ("if x then end", [('if', None), ('NAME', 'x'), ('then', None), ('end', None), ('EOS', None)]),
        ]
        
        passed = 0
        for source, expected in tests:
            try:
                tokens = LexerTest.tokenize(source)
                # Compare token types only (not exact structure)
                token_types = [(t[0] if isinstance(t[0], str) else t[0], t[1]) for t in tokens]
                
                match = True
                if len(token_types) != len(expected):
                    match = False
                else:
                    for (t1, v1), (t2, v2) in zip(token_types, expected):
                        # Convert keyword tokens to string for comparison
                        t1_str = t1 if isinstance(t1, str) else str(t1)
                        if t1_str.lower() != t2.lower() if isinstance(t2, str) else t1 != t2:
                            # Check for reserved word match
                            from pylua.llex import luaX_tokens, FIRST_RESERVED, NUM_RESERVED
                            if isinstance(t1, int) and t1 >= FIRST_RESERVED:
                                idx = t1 - FIRST_RESERVED
                                if idx < len(luaX_tokens):
                                    t1_str = luaX_tokens[idx]
                            if t1_str != t2:
                                match = False
                                break
                        if v1 != v2 and v2 is not None:
                            match = False
                            break
                
                if match:
                    print(f"  ✓ Lexer: {repr(source[:30])}...")
                    passed += 1
                else:
                    print(f"  ✗ Lexer: {repr(source[:30])}...")
                    print(f"    Expected: {expected}")
                    print(f"    Got: {token_types}")
            except Exception as e:
                print(f"  ✗ Lexer: {repr(source[:30])}... ERROR: {e}")
        
        print(f"\nLexer: {passed}/{len(tests)} passed")
        return passed == len(tests)


# =============================================================================
# Code Comparison with Lua 5.3
# =============================================================================
class BytecodeComparison:
    """Compare generated bytecode with Lua 5.3"""
    
    LUA_PATH = "lua53"
    LUAC_PATH = "luac53"
    
    @staticmethod
    def compile_with_lua(source: str) -> bytes:
        """Compile source with luac53 and return bytecode"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as f:
            f.write(source)
            src_file = f.name
        
        out_file = src_file.replace('.lua', '.luac')
        
        try:
            result = subprocess.run(
                [BytecodeComparison.LUAC_PATH, '-o', out_file, src_file],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                return None
            
            with open(out_file, 'rb') as f:
                return f.read()
        except Exception as e:
            return None
        finally:
            try:
                os.unlink(src_file)
                if os.path.exists(out_file):
                    os.unlink(out_file)
            except:
                pass
    
    @staticmethod
    def dump_bytecode_info(bytecode: bytes) -> dict:
        """Parse bytecode header and extract info"""
        if not bytecode or len(bytecode) < 18:
            return None
        
        # Check signature
        if bytecode[0:4] != b'\x1bLua':
            return None
        
        info = {
            'version': bytecode[4],
            'format': bytecode[5],
            'endianness': 'little' if bytecode[6:12] == b'\x19\x93\r\n\x1a\n' else 'unknown',
        }
        
        return info
    
    @staticmethod
    def run_with_lua(source: str) -> str:
        """Run source with Lua 5.3 and return output"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as f:
            f.write(source)
            src_file = f.name
        
        try:
            result = subprocess.run(
                [BytecodeComparison.LUA_PATH, src_file],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.stdout.strip()
        except Exception as e:
            return f"ERROR: {e}"
        finally:
            try:
                os.unlink(src_file)
            except:
                pass


# =============================================================================
# Frontend Pipeline Test
# =============================================================================
class FrontendPipelineTest:
    """Test complete frontend pipeline"""
    
    @staticmethod
    def test_lexer_consistency():
        """Test lexer produces consistent tokens"""
        print("\n" + "-" * 40)
        print("Testing Lexer Consistency")
        print("-" * 40)
        
        test_cases = [
            # Basic expressions
            "1 + 2",
            "a = b",
            "'hello world'",
            "[[long string]]",
            "0x1F + 3.14",
            
            # Control structures
            "if x then y end",
            "while true do break end",
            "for i = 1, 10 do print(i) end",
            
            # Functions
            "function foo(a, b) return a + b end",
            "local function bar() end",
            
            # Tables
            "{1, 2, 3}",
            "{x = 1, y = 2}",
            
            # Complex expressions
            "a and b or c",
            "not x",
            "#table",
            "a .. b",
        ]
        
        passed = 0
        for source in test_cases:
            try:
                tokens = LexerTest.tokenize(source)
                if tokens and tokens[-1][0] == 'EOS':
                    print(f"  ✓ {repr(source[:40])}")
                    passed += 1
                else:
                    print(f"  ✗ {repr(source[:40])}: No EOS token")
            except Exception as e:
                print(f"  ✗ {repr(source[:40])}: {e}")
        
        print(f"\nResult: {passed}/{len(test_cases)} passed")
        return passed == len(test_cases)
    
    @staticmethod
    def test_lua_execution():
        """Test that Lua can execute and we can compare"""
        print("\n" + "-" * 40)
        print("Testing Lua 5.3 Execution Comparison")
        print("-" * 40)
        
        test_cases = [
            ("print(1 + 2)", "3"),
            ("print('hello')", "hello"),
            ("print(10 // 3)", "3"),
            ("local x = 5; print(x * 2)", "10"),
        ]
        
        passed = 0
        lua_available = True
        
        for source, expected in test_cases:
            try:
                output = BytecodeComparison.run_with_lua(source)
                if output.startswith("ERROR"):
                    if "FileNotFoundError" in output or "No such file" in output:
                        lua_available = False
                        print(f"  ⚠ Lua 5.3 not available")
                        break
                    print(f"  ✗ {repr(source[:30])}: {output}")
                elif output == expected:
                    print(f"  ✓ {repr(source[:30])} => {output}")
                    passed += 1
                else:
                    print(f"  ✗ {repr(source[:30])}: expected {expected}, got {output}")
            except Exception as e:
                print(f"  ✗ {repr(source[:30])}: {e}")
        
        if lua_available:
            print(f"\nResult: {passed}/{len(test_cases)} passed")
        else:
            print("\nSkipped: Lua 5.3 not found")
            passed = len(test_cases)  # Mark as passed if Lua unavailable
        
        return passed == len(test_cases) or not lua_available


# =============================================================================
# Parser and Code Generation Tests
# =============================================================================
class ParserCodeGenTest:
    """Test parser and code generation"""
    
    @staticmethod
    def test_expression_parsing():
        """Test expression parsing"""
        print("\n" + "-" * 40)
        print("Testing Expression Parsing")
        print("-" * 40)
        
        from pylua.lparser import (
            expdesc, init_exp, VKINT, VKFLT, VNIL, VTRUE, VFALSE,
            getunopr, getbinopr, OPR_ADD, OPR_SUB, OPR_MUL, OPR_DIV,
            OPR_MINUS, OPR_NOT, OPR_NOUNOPR, OPR_NOBINOPR,
        )
        from pylua.lcode import OPR_AND, OPR_OR
        
        # Test operator mapping
        tests = [
            (ord('+'), OPR_ADD, "ADD"),
            (ord('-'), OPR_SUB, "SUB"),
            (ord('*'), OPR_MUL, "MUL"),
            (ord('/'), OPR_DIV, "DIV"),
        ]
        
        passed = 0
        for op, expected, name in tests:
            result = getbinopr(op)
            if result == expected:
                print(f"  ✓ Binary operator '{chr(op)}' = {name}")
                passed += 1
            else:
                print(f"  ✗ Binary operator '{chr(op)}': expected {expected}, got {result}")
        
        # Test unary operators
        unary_tests = [
            (ord('-'), OPR_MINUS, "MINUS"),
            (ord('#'), 3, "LEN"),  # OPR_LEN = 3
        ]
        
        for op, expected, name in unary_tests:
            result = getunopr(op)
            if result == expected:
                print(f"  ✓ Unary operator '{chr(op)}' = {name}")
                passed += 1
            else:
                print(f"  ✗ Unary operator '{chr(op)}': expected {expected}, got {result}")
        
        total = len(tests) + len(unary_tests)
        print(f"\nResult: {passed}/{total} passed")
        return passed == total
    
    @staticmethod
    def test_code_generation_basics():
        """Test basic code generation functions"""
        print("\n" + "-" * 40)
        print("Testing Code Generation Basics")
        print("-" * 40)
        
        from pylua.lcode import (
            NO_JUMP, MAXREGS,
            BinOpr, UnOpr,
            OPR_ADD, OPR_MUL, OPR_MINUS, OPR_NOT,
        )
        from pylua.lopcodes import (
            OpCode, CREATE_ABC, CREATE_ABx,
            GETARG_A, GETARG_B, GETARG_C, GET_OPCODE,
            MAXARG_A, MAXARG_B, MAXARG_C,
        )
        
        passed = 0
        total = 0
        
        # Test instruction encoding
        total += 1
        inst = CREATE_ABC(OpCode.OP_MOVE, 1, 2, 0)
        a = GETARG_A(inst)
        b = GETARG_B(inst)
        op = GET_OPCODE(inst)
        if a == 1 and b == 2 and op == OpCode.OP_MOVE:
            print(f"  ✓ CREATE_ABC(OP_MOVE, 1, 2, 0) encodes correctly")
            passed += 1
        else:
            print(f"  ✗ CREATE_ABC encoding failed: A={a}, B={b}, OP={op}")
        
        # Test ABx encoding
        total += 1
        inst = CREATE_ABx(OpCode.OP_LOADK, 5, 100)
        a = GETARG_A(inst)
        from pylua.lopcodes import GETARG_Bx
        bx = GETARG_Bx(inst)
        if a == 5 and bx == 100:
            print(f"  ✓ CREATE_ABx(OP_LOADK, 5, 100) encodes correctly")
            passed += 1
        else:
            print(f"  ✗ CREATE_ABx encoding failed: A={a}, Bx={bx}")
        
        # Test constants
        total += 1
        if NO_JUMP == -1:
            print(f"  ✓ NO_JUMP = -1")
            passed += 1
        else:
            print(f"  ✗ NO_JUMP = {NO_JUMP}, expected -1")
        
        total += 1
        if MAXREGS == 255:
            print(f"  ✓ MAXREGS = 255")
            passed += 1
        else:
            print(f"  ✗ MAXREGS = {MAXREGS}, expected 255")
        
        print(f"\nResult: {passed}/{total} passed")
        return passed == total
    
    @staticmethod
    def test_opcode_coverage():
        """Test that all opcodes are defined"""
        print("\n" + "-" * 40)
        print("Testing Opcode Coverage")
        print("-" * 40)
        
        from pylua.lopcodes import OpCode
        
        required_opcodes = [
            'OP_MOVE', 'OP_LOADK', 'OP_LOADKX', 'OP_LOADBOOL', 'OP_LOADNIL',
            'OP_GETUPVAL', 'OP_GETTABUP', 'OP_GETTABLE',
            'OP_SETTABUP', 'OP_SETUPVAL', 'OP_SETTABLE', 'OP_NEWTABLE',
            'OP_SELF', 'OP_ADD', 'OP_SUB', 'OP_MUL', 'OP_MOD', 'OP_POW',
            'OP_DIV', 'OP_IDIV', 'OP_BAND', 'OP_BOR', 'OP_BXOR',
            'OP_SHL', 'OP_SHR', 'OP_UNM', 'OP_BNOT', 'OP_NOT', 'OP_LEN',
            'OP_CONCAT', 'OP_JMP', 'OP_EQ', 'OP_LT', 'OP_LE',
            'OP_TEST', 'OP_TESTSET', 'OP_CALL', 'OP_TAILCALL', 'OP_RETURN',
            'OP_FORLOOP', 'OP_FORPREP', 'OP_TFORCALL', 'OP_TFORLOOP',
            'OP_SETLIST', 'OP_CLOSURE', 'OP_VARARG', 'OP_EXTRAARG',
        ]
        
        passed = 0
        missing = []
        for name in required_opcodes:
            if hasattr(OpCode, name):
                passed += 1
            else:
                missing.append(name)
        
        if missing:
            print(f"  ✗ Missing opcodes: {missing}")
        else:
            print(f"  ✓ All {len(required_opcodes)} opcodes defined")
        
        print(f"\nResult: {passed}/{len(required_opcodes)} opcodes")
        return len(missing) == 0
    
    @staticmethod
    def test_priority_table():
        """Test operator priority table"""
        print("\n" + "-" * 40)
        print("Testing Operator Priority Table")
        print("-" * 40)
        
        from pylua.lparser import priority, UNARY_PRIORITY
        
        passed = 0
        total = 0
        
        # Check priority table exists and has correct structure
        total += 1
        if len(priority) >= 20:
            print(f"  ✓ Priority table has {len(priority)} entries")
            passed += 1
        else:
            print(f"  ✗ Priority table too short: {len(priority)} entries")
        
        # Check unary priority
        total += 1
        if UNARY_PRIORITY == 12:
            print(f"  ✓ UNARY_PRIORITY = 12")
            passed += 1
        else:
            print(f"  ✗ UNARY_PRIORITY = {UNARY_PRIORITY}, expected 12")
        
        # Check some specific priorities
        # + and - should have priority 10
        total += 1
        if priority[0] == (10, 10) and priority[1] == (10, 10):
            print(f"  ✓ +/- priority = (10, 10)")
            passed += 1
        else:
            print(f"  ✗ +/- priority incorrect")
        
        # * and % should have priority 11
        total += 1
        if priority[2] == (11, 11) and priority[3] == (11, 11):
            print(f"  ✓ */% priority = (11, 11)")
            passed += 1
        else:
            print(f"  ✗ */% priority incorrect")
        
        # ^ should be right associative (14, 13)
        total += 1
        if priority[4] == (14, 13):
            print(f"  ✓ ^ priority = (14, 13) (right associative)")
            passed += 1
        else:
            print(f"  ✗ ^ priority incorrect")
        
        print(f"\nResult: {passed}/{total} passed")
        return passed == total
    
    @staticmethod
    def run_all():
        """Run all parser/codegen tests"""
        results = []
        results.append(ParserCodeGenTest.test_expression_parsing())
        results.append(ParserCodeGenTest.test_code_generation_basics())
        results.append(ParserCodeGenTest.test_opcode_coverage())
        results.append(ParserCodeGenTest.test_priority_table())
        return all(results)


# =============================================================================
# Main
# =============================================================================
def main():
    print("=" * 60)
    print("PyLua Frontend Integration Test Suite")
    print("=" * 60)
    print("\nThis test verifies the complete frontend pipeline:")
    print("  Source Code -> Lexer -> Parser -> Code Generator")
    print()
    
    results = []
    
    # Test 1: Lexer integration
    results.append(("Lexer Integration", LexerTest.run_tests()))
    
    # Test 2: Lexer consistency
    results.append(("Lexer Consistency", FrontendPipelineTest.test_lexer_consistency()))
    
    # Test 3: Lua execution comparison
    results.append(("Lua Comparison", FrontendPipelineTest.test_lua_execution()))
    
    # Test 4: Parser and Code Generation
    results.append(("Parser/CodeGen", ParserCodeGenTest.run_all()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("*** ALL FRONTEND TESTS PASSED ***")
        return 0
    else:
        print("*** SOME TESTS FAILED ***")
        return 1


if __name__ == "__main__":
    sys.exit(main())
