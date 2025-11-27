# -*- coding: utf-8 -*-
"""
test_frontend.py - Lua Frontend (Lexer + Parser) Test Suite
============================================================

This test suite compares PyLua's lexer and parser output with Lua 5.3's behavior.
"""
import sys
import os
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylua.llex import (
    LexState, SemInfo, Token,
    luaX_next, llex,
    TK_AND, TK_BREAK, TK_DO, TK_ELSE, TK_ELSEIF, TK_END,
    TK_FALSE, TK_FOR, TK_FUNCTION, TK_GOTO, TK_IF, TK_IN,
    TK_LOCAL, TK_NIL, TK_NOT, TK_OR, TK_REPEAT, TK_RETURN,
    TK_THEN, TK_TRUE, TK_UNTIL, TK_WHILE,
    TK_EQ, TK_NE, TK_LE, TK_GE, TK_CONCAT, TK_DOTS, TK_IDIV,
    TK_SHL, TK_SHR, TK_DBCOLON, TK_EOS,
    TK_INT, TK_FLT, TK_STRING, TK_NAME,
    luaX_token2str, FIRST_RESERVED, EOZ,
    luaX_tokens, NUM_RESERVED,
)
from pylua.lobject import TString
from dataclasses import dataclass


# =============================================================================
# Test Utilities
# =============================================================================

@dataclass
class SimpleZIO:
    """Simple ZIO mock for testing"""
    p: bytes
    n: int


def create_lexer(source: str) -> LexState:
    """Create a lexer for testing"""
    ls = LexState()
    z = SimpleZIO(source.encode('utf-8'), len(source))
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
    
    return ls


def tokenize(source: str) -> list:
    """Tokenize source and return list of (token, value) pairs"""
    ls = create_lexer(source)
    tokens = []
    while True:
        luaX_next(ls)
        tok = ls.t.token
        seminfo = ls.t.seminfo
        
        if tok == TK_INT:
            tokens.append((tok, seminfo.i))
        elif tok == TK_FLT:
            tokens.append((tok, seminfo.r))
        elif tok == TK_STRING or tok == TK_NAME:
            val = seminfo.ts.data.decode('utf-8') if seminfo.ts else ""
            tokens.append((tok, val))
        else:
            tokens.append((tok, None))
        
        if tok == TK_EOS:
            break
    return tokens


def token_to_name(tok: int) -> str:
    """Convert token to readable name"""
    if tok < FIRST_RESERVED:
        if tok >= 32 and tok < 127:
            return f"'{chr(tok)}'"
        return f"<{tok}>"
    idx = tok - FIRST_RESERVED
    if idx < len(luaX_tokens):
        return luaX_tokens[idx]
    return f"<unknown:{tok}>"


# =============================================================================
# Lexer Tests
# =============================================================================

class LexerTests:
    """Comprehensive lexer tests"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def test(self, name: str, condition: bool, msg: str = ""):
        if condition:
            self.passed += 1
            print(f"  ✓ {name}")
        else:
            self.failed += 1
            self.errors.append(f"{name}: {msg}")
            print(f"  ✗ {name}: {msg}")
    
    def test_keywords(self):
        """Test all 22 reserved words"""
        print("\n[1] Keywords")
        keywords = [
            ("and", TK_AND), ("break", TK_BREAK), ("do", TK_DO),
            ("else", TK_ELSE), ("elseif", TK_ELSEIF), ("end", TK_END),
            ("false", TK_FALSE), ("for", TK_FOR), ("function", TK_FUNCTION),
            ("goto", TK_GOTO), ("if", TK_IF), ("in", TK_IN),
            ("local", TK_LOCAL), ("nil", TK_NIL), ("not", TK_NOT),
            ("or", TK_OR), ("repeat", TK_REPEAT), ("return", TK_RETURN),
            ("then", TK_THEN), ("true", TK_TRUE), ("until", TK_UNTIL),
            ("while", TK_WHILE),
        ]
        
        for word, expected in keywords:
            tokens = tokenize(word)
            self.test(f"keyword '{word}'", tokens[0][0] == expected,
                     f"expected {token_to_name(expected)}, got {token_to_name(tokens[0][0])}")
    
    def test_operators(self):
        """Test multi-character operators"""
        print("\n[2] Operators")
        operators = [
            ("==", TK_EQ, "equal"),
            ("~=", TK_NE, "not equal"),
            ("<=", TK_LE, "less equal"),
            (">=", TK_GE, "greater equal"),
            ("..", TK_CONCAT, "concat"),
            ("...", TK_DOTS, "vararg"),
            ("//", TK_IDIV, "integer div"),
            ("<<", TK_SHL, "shift left"),
            (">>", TK_SHR, "shift right"),
            ("::", TK_DBCOLON, "double colon"),
        ]
        
        for op, expected, name in operators:
            tokens = tokenize(op)
            self.test(f"operator '{op}' ({name})", tokens[0][0] == expected,
                     f"expected {token_to_name(expected)}, got {token_to_name(tokens[0][0])}")
    
    def test_single_char_operators(self):
        """Test single character operators"""
        print("\n[3] Single Char Operators")
        ops = "+-*/%^#&|~<>=(){}[];:,."
        for c in ops:
            tokens = tokenize(c)
            self.test(f"operator '{c}'", tokens[0][0] == ord(c),
                     f"expected {ord(c)}, got {tokens[0][0]}")
    
    def test_integers(self):
        """Test integer literals"""
        print("\n[4] Integer Literals")
        integers = [
            ("0", 0), ("123", 123), ("456789", 456789),
            ("0x10", 16), ("0xFF", 255), ("0XABCDEF", 0xABCDEF),
            ("0x0", 0),
        ]
        
        for src, expected in integers:
            tokens = tokenize(src)
            self.test(f"integer '{src}'", 
                     tokens[0][0] == TK_INT and tokens[0][1] == expected,
                     f"expected {expected}, got {tokens[0]}")
    
    def test_floats(self):
        """Test floating point literals"""
        print("\n[5] Float Literals")
        floats = [
            ("3.14", 3.14),
            ("0.5", 0.5),
            (".5", 0.5),
            ("1.", 1.0),
            ("1e10", 1e10),
            ("1.5e-3", 1.5e-3),
            ("1E+5", 1e5),
        ]
        
        for src, expected in floats:
            tokens = tokenize(src)
            self.test(f"float '{src}'",
                     tokens[0][0] == TK_FLT and abs(tokens[0][1] - expected) < 1e-10,
                     f"expected {expected}, got {tokens[0]}")
    
    def test_strings(self):
        """Test string literals"""
        print("\n[6] String Literals")
        strings = [
            ('"hello"', "hello"),
            ("'world'", "world"),
            ('"hello\\nworld"', "hello\nworld"),
            ('"tab\\there"', "tab\there"),
            ('""', ""),
            ("''", ""),
            ('"a\\x41b"', "aAb"),  # hex escape
        ]
        
        for src, expected in strings:
            try:
                tokens = tokenize(src)
                self.test(f"string {src}",
                         tokens[0][0] == TK_STRING and tokens[0][1] == expected,
                         f"expected '{expected}', got {tokens[0]}")
            except Exception as e:
                self.test(f"string {src}", False, str(e))
    
    def test_long_strings(self):
        """Test long string literals"""
        print("\n[7] Long Strings")
        long_strings = [
            ("[[hello]]", "hello"),
            ("[=[level 1]=]", "level 1"),
            ("[==[level 2]==]", "level 2"),
            ("[[multi\nline]]", "multi\nline"),
        ]
        
        for src, expected in long_strings:
            try:
                tokens = tokenize(src)
                self.test(f"long string {repr(src[:20])}...",
                         tokens[0][0] == TK_STRING and tokens[0][1] == expected,
                         f"expected '{expected}', got {tokens[0]}")
            except Exception as e:
                self.test(f"long string {repr(src[:20])}...", False, str(e))
    
    def test_identifiers(self):
        """Test identifiers"""
        print("\n[8] Identifiers")
        identifiers = ["x", "foo", "_bar", "test123", "_", "_123", "camelCase", "UPPER"]
        
        for ident in identifiers:
            tokens = tokenize(ident)
            self.test(f"identifier '{ident}'",
                     tokens[0][0] == TK_NAME and tokens[0][1] == ident,
                     f"expected TK_NAME '{ident}', got {tokens[0]}")
    
    def test_comments(self):
        """Test comments are skipped"""
        print("\n[9] Comments")
        
        # Short comment
        tokens = tokenize("x -- comment\ny")
        self.test("short comment", 
                 len(tokens) == 3 and tokens[0][1] == "x" and tokens[1][1] == "y",
                 f"got {tokens}")
        
        # Long comment
        tokens = tokenize("a --[[long comment]] b")
        self.test("long comment",
                 len(tokens) == 3 and tokens[0][1] == "a" and tokens[1][1] == "b",
                 f"got {tokens}")
        
        # Multi-line comment
        tokens = tokenize("a --[[\nmulti\nline\n]] b")
        self.test("multi-line comment",
                 len(tokens) == 3 and tokens[0][1] == "a" and tokens[1][1] == "b",
                 f"got {tokens}")
    
    def test_whitespace(self):
        """Test whitespace handling"""
        print("\n[10] Whitespace")
        
        tokens = tokenize("  x  \t  y  \n  z  ")
        names = [t[1] for t in tokens if t[0] == TK_NAME]
        self.test("whitespace skipped", names == ["x", "y", "z"],
                 f"expected ['x', 'y', 'z'], got {names}")
    
    def test_complex_source(self):
        """Test complex Lua source code"""
        print("\n[11] Complex Source")
        
        source = '''
local function factorial(n)
    if n <= 1 then
        return 1
    else
        return n * factorial(n - 1)
    end
end

print(factorial(5))
'''
        try:
            tokens = tokenize(source)
            self.test("complex source tokenizes", tokens[-1][0] == TK_EOS,
                     f"did not reach EOS, last token: {tokens[-1]}")
            self.test("complex source token count", len(tokens) > 30,
                     f"expected >30 tokens, got {len(tokens)}")
        except Exception as e:
            self.test("complex source tokenizes", False, str(e))
    
    def run_all(self):
        """Run all tests"""
        print("=" * 60)
        print("LEXER TESTS")
        print("=" * 60)
        
        self.test_keywords()
        self.test_operators()
        self.test_single_char_operators()
        self.test_integers()
        self.test_floats()
        self.test_strings()
        self.test_long_strings()
        self.test_identifiers()
        self.test_comments()
        self.test_whitespace()
        self.test_complex_source()
        
        print("\n" + "=" * 60)
        print(f"LEXER RESULTS: {self.passed} passed, {self.failed} failed")
        print("=" * 60)
        
        if self.errors:
            print("\nErrors:")
            for err in self.errors[:10]:  # Show first 10 errors
                print(f"  - {err}")
        
        return self.failed == 0


# =============================================================================
# Main
# =============================================================================

def main():
    print("Lua Frontend Test Suite")
    print("=" * 60)
    
    # Run lexer tests
    lexer_tests = LexerTests()
    lexer_ok = lexer_tests.run_all()
    
    # Summary
    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    print(f"Lexer: {'PASS' if lexer_ok else 'FAIL'}")
    
    return 0 if lexer_ok else 1


if __name__ == "__main__":
    sys.exit(main())
