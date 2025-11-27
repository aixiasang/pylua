# -*- coding: utf-8 -*-
"""
test_llex.py - Test lexer implementation
"""
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylua.llex import (
    LexState, SemInfo, Token, 
    luaX_setinput, luaX_next, llex,
    TK_AND, TK_BREAK, TK_DO, TK_ELSE, TK_ELSEIF, TK_END,
    TK_FALSE, TK_FOR, TK_FUNCTION, TK_GOTO, TK_IF, TK_IN,
    TK_LOCAL, TK_NIL, TK_NOT, TK_OR, TK_REPEAT, TK_RETURN,
    TK_THEN, TK_TRUE, TK_UNTIL, TK_WHILE,
    TK_EQ, TK_NE, TK_LE, TK_GE, TK_CONCAT, TK_DOTS, TK_IDIV,
    TK_SHL, TK_SHR, TK_DBCOLON, TK_EOS,
    TK_INT, TK_FLT, TK_STRING, TK_NAME,
    luaX_token2str, FIRST_RESERVED
)
from pylua.lobject import TString
from dataclasses import dataclass


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
        ls.current = -1
    ls.linenumber = 1
    ls.lastline = 1
    ls.lookahead = Token()
    ls.lookahead.token = TK_EOS
    ls.t = Token()
    ls.t.seminfo = SemInfo()
    ls.buff = bytearray()
    
    return ls


def tokenize(source: str) -> list:
    """Tokenize source and return list of tokens"""
    ls = create_lexer(source)
    tokens = []
    while True:
        luaX_next(ls)
        tok = ls.t.token
        tokens.append(tok)
        if tok == TK_EOS:
            break
    return tokens


def test_keywords():
    """Test reserved word recognition"""
    print("Testing keywords...")
    
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
    
    passed = 0
    for word, expected in keywords:
        tokens = tokenize(word)
        if tokens[0] == expected:
            passed += 1
        else:
            print(f"  FAIL: '{word}' expected {expected}, got {tokens[0]}")
    
    print(f"  Keywords: {passed}/{len(keywords)} passed")
    return passed == len(keywords)


def test_operators():
    """Test operator recognition"""
    print("Testing operators...")
    
    operators = [
        ("==", TK_EQ), ("~=", TK_NE), ("<=", TK_LE), (">=", TK_GE),
        ("..", TK_CONCAT), ("...", TK_DOTS), ("//", TK_IDIV),
        ("<<", TK_SHL), (">>", TK_SHR), ("::", TK_DBCOLON),
    ]
    
    passed = 0
    for op, expected in operators:
        tokens = tokenize(op)
        if tokens[0] == expected:
            passed += 1
        else:
            print(f"  FAIL: '{op}' expected {expected}, got {tokens[0]}")
    
    print(f"  Operators: {passed}/{len(operators)} passed")
    return passed == len(operators)


def test_numbers():
    """Test number recognition"""
    print("Testing numbers...")
    
    numbers = [
        ("123", TK_INT),
        ("3.14", TK_FLT),
        ("0xff", TK_INT),
        ("0x10", TK_INT),
        ("1e10", TK_FLT),
        ("1.5e-3", TK_FLT),
    ]
    
    passed = 0
    for num, expected in numbers:
        tokens = tokenize(num)
        if tokens[0] == expected:
            passed += 1
        else:
            print(f"  FAIL: '{num}' expected {expected}, got {tokens[0]}")
    
    print(f"  Numbers: {passed}/{len(numbers)} passed")
    return passed == len(numbers)


def test_strings():
    """Test string recognition"""
    print("Testing strings...")
    
    strings = [
        ('"hello"', TK_STRING),
        ("'world'", TK_STRING),
        ('[[long string]]', TK_STRING),
        ('[=[level 1]=]', TK_STRING),
    ]
    
    passed = 0
    for s, expected in strings:
        try:
            tokens = tokenize(s)
            if tokens[0] == expected:
                passed += 1
            else:
                print(f"  FAIL: {s} expected {expected}, got {tokens[0]}")
        except Exception as e:
            print(f"  FAIL: {s} raised {e}")
    
    print(f"  Strings: {passed}/{len(strings)} passed")
    return passed == len(strings)


def test_identifiers():
    """Test identifier recognition"""
    print("Testing identifiers...")
    
    identifiers = ["x", "foo", "_bar", "test123", "_123"]
    
    passed = 0
    for ident in identifiers:
        tokens = tokenize(ident)
        if tokens[0] == TK_NAME:
            passed += 1
        else:
            print(f"  FAIL: '{ident}' expected TK_NAME, got {tokens[0]}")
    
    print(f"  Identifiers: {passed}/{len(identifiers)} passed")
    return passed == len(identifiers)


def test_complex():
    """Test complex source"""
    print("Testing complex source...")
    
    source = """
    local x = 10
    if x >= 5 then
        print("hello")
    end
    """
    
    try:
        tokens = tokenize(source)
        # Expected: local, x, =, 10, if, x, >=, 5, then, print, (, "hello", ), end, EOS
        expected_count = 15
        if len(tokens) == expected_count:
            print(f"  Complex: PASS ({len(tokens)} tokens)")
            return True
        else:
            print(f"  Complex: FAIL (expected {expected_count} tokens, got {len(tokens)})")
            return False
    except Exception as e:
        print(f"  Complex: FAIL ({e})")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Lua Lexer Tests")
    print("=" * 50)
    
    results = []
    results.append(test_keywords())
    results.append(test_operators())
    results.append(test_numbers())
    results.append(test_strings())
    results.append(test_identifiers())
    results.append(test_complex())
    
    print("=" * 50)
    passed = sum(results)
    print(f"Total: {passed}/{len(results)} test groups passed")
    
    if all(results):
        print("*** ALL TESTS PASSED ***")
    else:
        print("*** SOME TESTS FAILED ***")
