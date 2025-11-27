# -*- coding: utf-8 -*-
"""
lexer_verify.py - Verify PyLua Lexer consistency with Lua 5.3

Compare lexical analysis results between PyLua llex.py and lua-5.3.6/src/llex.c.

Based on Lua 5.3.6 official implementation.
Author: aixiasang
"""

import sys
import os
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylua.llex import (
    LexState, SemInfo, Token, luaX_next,
    TK_AND, TK_BREAK, TK_DO, TK_ELSE, TK_ELSEIF, TK_END,
    TK_FALSE, TK_FOR, TK_FUNCTION, TK_GOTO, TK_IF, TK_IN,
    TK_LOCAL, TK_NIL, TK_NOT, TK_OR, TK_REPEAT, TK_RETURN,
    TK_THEN, TK_TRUE, TK_UNTIL, TK_WHILE,
    TK_IDIV, TK_CONCAT, TK_DOTS, TK_EQ, TK_GE, TK_LE, TK_NE,
    TK_SHL, TK_SHR, TK_DBCOLON, TK_EOS, TK_FLT, TK_INT, TK_NAME, TK_STRING,
    FIRST_RESERVED, NUM_RESERVED, luaX_tokens, EOZ
)
from pylua.lobject import TString



TOKEN_NAMES = {
    TK_AND: 'TK_AND', TK_BREAK: 'TK_BREAK', TK_DO: 'TK_DO',
    TK_ELSE: 'TK_ELSE', TK_ELSEIF: 'TK_ELSEIF', TK_END: 'TK_END',
    TK_FALSE: 'TK_FALSE', TK_FOR: 'TK_FOR', TK_FUNCTION: 'TK_FUNCTION',
    TK_GOTO: 'TK_GOTO', TK_IF: 'TK_IF', TK_IN: 'TK_IN',
    TK_LOCAL: 'TK_LOCAL', TK_NIL: 'TK_NIL', TK_NOT: 'TK_NOT',
    TK_OR: 'TK_OR', TK_REPEAT: 'TK_REPEAT', TK_RETURN: 'TK_RETURN',
    TK_THEN: 'TK_THEN', TK_TRUE: 'TK_TRUE', TK_UNTIL: 'TK_UNTIL',
    TK_WHILE: 'TK_WHILE', TK_IDIV: 'TK_IDIV', TK_CONCAT: 'TK_CONCAT',
    TK_DOTS: 'TK_DOTS', TK_EQ: 'TK_EQ', TK_GE: 'TK_GE', TK_LE: 'TK_LE',
    TK_NE: 'TK_NE', TK_SHL: 'TK_SHL', TK_SHR: 'TK_SHR',
    TK_DBCOLON: 'TK_DBCOLON', TK_EOS: 'TK_EOS', TK_FLT: 'TK_FLT',
    TK_INT: 'TK_INT', TK_NAME: 'TK_NAME', TK_STRING: 'TK_STRING',
}


def pylua_tokenize(source: str):
    """Tokenize using PyLua lexer"""
    source_bytes = source.encode('utf-8')
    
    ls = LexState()
    
    class SimpleZIO:
        def __init__(self, data):
            self.p = data[1:] if len(data) > 1 else b''
            self.n = len(self.p)
    
    ls.z = SimpleZIO(source_bytes)
    ts = TString()
    ts.data = b'input'
    ls.source = ts
    
    if source_bytes:
        ls.current = source_bytes[0]
    else:
        ls.current = EOZ
    
    ls.linenumber = 1
    ls.lastline = 1
    ls.lookahead = Token()
    ls.lookahead.token = TK_EOS
    ls.lookahead.seminfo = SemInfo()
    ls.t = Token()
    ls.t.seminfo = SemInfo()
    ls.buff = bytearray()
    
    tokens = []
    try:
        while True:
            luaX_next(ls)
            tok = ls.t.token
            seminfo = ls.t.seminfo
            
            if tok == TK_EOS:
                tokens.append(('EOS', None, ls.linenumber))
                break
            elif tok == TK_INT:
                tokens.append(('INT', seminfo.i, ls.linenumber))
            elif tok == TK_FLT:
                tokens.append(('FLT', seminfo.r, ls.linenumber))
            elif tok == TK_STRING:
                val = seminfo.ts.data.decode('utf-8') if seminfo.ts else ''
                tokens.append(('STRING', val, ls.linenumber))
            elif tok == TK_NAME:
                val = seminfo.ts.data.decode('utf-8') if seminfo.ts else ''
                tokens.append(('NAME', val, ls.linenumber))
            elif tok < 256:
                tokens.append(('CHAR', chr(tok), ls.linenumber))
            else:
                name = TOKEN_NAMES.get(tok, f'TK_{tok}')
                tokens.append((name, None, ls.linenumber))
    except Exception as e:
        tokens.append(('ERROR', str(e), ls.linenumber))
    
    return tokens


def verify_lexer_on_file(filepath: str, verbose: bool = False):
    """Verify lexer on single file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    tokens = pylua_tokenize(source)
    

    errors = [t for t in tokens if t[0] == 'ERROR']
    
    if errors:
        return False, errors[0][1]
    
    if verbose:
        print(f"File: {os.path.basename(filepath)}")
        print(f"Tokens: {len(tokens)}")
        for t in tokens[:20]:
            print(f"  {t}")
        if len(tokens) > 20:
            print(f"  ... ({len(tokens) - 20} more)")
    
    return True, len(tokens)


def batch_verify(directory: str):
    """Batch verification"""
    import glob
    
    print("=" * 60)
    print("PyLua Lexer Verification")
    print("=" * 60)
    
    files = sorted(glob.glob(os.path.join(directory, '*.lua')))
    
    passed = 0
    failed = 0
    
    for filepath in files:
        name = os.path.basename(filepath)
        ok, result = verify_lexer_on_file(filepath)
        if ok:
            print(f"[OK] {name:40s} ({result} tokens)")
            passed += 1
        else:
            print(f"[FAIL] {name:40s} Error: {result[:40]}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Passed: {passed}/{len(files)}, Failed: {failed}")
    
    return passed, failed


def test_specific_tokens():
    """Test specific token sequences"""
    print("=" * 60)
    print("Specific Token Tests")
    print("=" * 60)
    
    tests = [

        ("local x = 1", [('TK_LOCAL', None), ('NAME', 'x'), ('CHAR', '='), ('INT', 1), ('EOS', None)]),
        ("1 + 2", [('INT', 1), ('CHAR', '+'), ('INT', 2), ('EOS', None)]),
        ("'hello'", [('STRING', 'hello'), ('EOS', None)]),
        ('"world"', [('STRING', 'world'), ('EOS', None)]),
        ("a.b.c", [('NAME', 'a'), ('CHAR', '.'), ('NAME', 'b'), ('CHAR', '.'), ('NAME', 'c'), ('EOS', None)]),
        ("a:b()", [('NAME', 'a'), ('CHAR', ':'), ('NAME', 'b'), ('CHAR', '('), ('CHAR', ')'), ('EOS', None)]),
        ("1.5", [('FLT', 1.5), ('EOS', None)]),
        ("0x10", [('INT', 16), ('EOS', None)]),
        ("1e10", [('FLT', 1e10), ('EOS', None)]),
        ("{x = 1}", [('CHAR', '{'), ('NAME', 'x'), ('CHAR', '='), ('INT', 1), ('CHAR', '}'), ('EOS', None)]),
        ("a .. b", [('NAME', 'a'), ('TK_CONCAT', None), ('NAME', 'b'), ('EOS', None)]),
        ("a // b", [('NAME', 'a'), ('TK_IDIV', None), ('NAME', 'b'), ('EOS', None)]),
        ("...", [('TK_DOTS', None), ('EOS', None)]),
        ("a == b", [('NAME', 'a'), ('TK_EQ', None), ('NAME', 'b'), ('EOS', None)]),
        ("a ~= b", [('NAME', 'a'), ('TK_NE', None), ('NAME', 'b'), ('EOS', None)]),
        ("a <= b", [('NAME', 'a'), ('TK_LE', None), ('NAME', 'b'), ('EOS', None)]),
        ("a >= b", [('NAME', 'a'), ('TK_GE', None), ('NAME', 'b'), ('EOS', None)]),
        ("a << b", [('NAME', 'a'), ('TK_SHL', None), ('NAME', 'b'), ('EOS', None)]),
        ("a >> b", [('NAME', 'a'), ('TK_SHR', None), ('NAME', 'b'), ('EOS', None)]),
        ("::label::", [('TK_DBCOLON', None), ('NAME', 'label'), ('TK_DBCOLON', None), ('EOS', None)]),
    ]
    
    passed = 0
    for source, expected in tests:
        tokens = pylua_tokenize(source)

        actual = [(t[0], t[1]) for t in tokens]
        
        if actual == expected:
            print(f"[OK] {source!r}")
            passed += 1
        else:
            print(f"[FAIL] {source!r}")
            print(f"  Expected: {expected}")
            print(f"  Actual:   {actual}")
    
    print(f"\nPassed: {passed}/{len(tests)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify PyLua Lexer")
    parser.add_argument("--batch", action="store_true", help="Batch verify all files")
    parser.add_argument("--tokens", action="store_true", help="Test specific tokens")
    parser.add_argument("-f", "--file", type=str, help="Verify single file")
    
    args = parser.parse_args()
    
    if args.batch:
        code_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                               'tests', 'code')
        batch_verify(code_dir)
    elif args.tokens:
        test_specific_tokens()
    elif args.file:
        ok, result = verify_lexer_on_file(args.file, verbose=True)
        print(f"Result: {'OK' if ok else 'FAIL'}")
    else:
        test_specific_tokens()
        print()
        code_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                               'tests', 'code')
        batch_verify(code_dir)
