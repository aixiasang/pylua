# -*- coding: utf-8 -*-
"""
ast_viewer.py - Lua AST Analysis Viewer

Standalone tool for analyzing Lua source code AST (Abstract Syntax Tree).

Features:
- Parse Lua source code to generate AST
- Visualize AST structure
- Support single file and batch analysis
- Support comparison with Lexer and Bytecode results

Based on Lua 5.3.6 official implementation.
Author: aixiasang

Usage:
  py tools/ast_viewer.py -c "local x = 1 + 2"
  py tools/ast_viewer.py -f tests/code/simple.lua
  py tools/ast_viewer.py --batch
  py tools/ast_viewer.py --all
"""

import sys
import os
import glob
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylua.last import ASTPrinter
from pylua.last_parser import parse_lua, print_ast, ASTParser


def analyze_source(source: str, name: str = "input", show_tokens: bool = False,
                   show_ast: bool = True, show_bytecode: bool = False) -> dict:
    """
    Analyze Lua source code
    
    Returns:
        {
            'tokens': [...],
            'ast': Chunk,
            'ast_text': str,
            'bytecode': str,
            'error': str or None
        }
    """
    result = {
        'tokens': None,
        'ast': None,
        'ast_text': None,
        'bytecode': None,
        'error': None
    }
    
    # Lexer analysis
    if show_tokens:
        try:
            from tools.parser_viewer import SimpleParser
            result['tokens'] = SimpleParser.tokenize(source)
        except Exception as e:
            result['tokens'] = f"Error: {e}"
    
    # AST analysis
    if show_ast:
        try:
            ast = parse_lua(source, name)
            result['ast'] = ast
            printer = ASTPrinter()
            result['ast_text'] = printer.print(ast)
        except Exception as e:
            result['error'] = str(e)
            result['ast_text'] = f"Parse Error: {e}"
    
    # Bytecode analysis
    if show_bytecode:
        try:
            import subprocess
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as f:
                f.write(source)
                src_file = f.name
            try:
                r = subprocess.run(['luac53', '-l', '-l', src_file],
                                  capture_output=True, timeout=5, text=True)
                result['bytecode'] = r.stdout if r.returncode == 0 else r.stderr
            finally:
                os.unlink(src_file)
        except Exception as e:
            result['bytecode'] = f"Error: {e}"
    
    return result


def print_analysis(source: str, name: str = "input", show_all: bool = False):
    """Print complete analysis results"""
    print("=" * 70)
    print(f"Analysis: {name}")
    print("=" * 70)
    
    # Display source code
    lines = source.strip().split('\n')
    if len(lines) <= 10:
        print("\nSource code:")
        for i, line in enumerate(lines, 1):
            print(f"  {i:3d} | {line}")
    else:
        print(f"\nSource code: ({len(lines)} lines)")
        for i, line in enumerate(lines[:5], 1):
            print(f"  {i:3d} | {line}")
        print("  ... ...")
        for i, line in enumerate(lines[-3:], len(lines) - 2):
            print(f"  {i:3d} | {line}")
    
    result = analyze_source(source, name, show_tokens=show_all, 
                           show_ast=True, show_bytecode=show_all)
    
    # Display Tokens
    if result['tokens']:
        print("\n" + "-" * 40)
        print("Tokens:")
        if isinstance(result['tokens'], str):
            print(f"  {result['tokens']}")
        else:
            for tok in result['tokens'][:30]:
                print(f"  {tok['line']:3d}: {tok['type']:10s} {repr(tok['value'])}")
            if len(result['tokens']) > 30:
                print(f"  ... total {len(result['tokens'])} tokens")
    
    # Display AST
    print("\n" + "-" * 40)
    print("AST (Abstract Syntax Tree):")
    if result['ast_text']:
        for line in result['ast_text'].split('\n'):
            print(f"  {line}")
    
    # Display Bytecode
    if result['bytecode']:
        print("\n" + "-" * 40)
        print("Bytecode (Lua 5.3 luac):")
        for line in result['bytecode'].split('\n')[:50]:
            if line.strip():
                print(f"  {line}")


def analyze_file(filepath: str, show_all: bool = False):
    """Analyze a single file"""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    print_analysis(source, os.path.basename(filepath), show_all)


def batch_test():
    """Batch test"""
    print("=" * 70)
    print("PyLua AST Batch Test")
    print("=" * 70)
    
    test_cases = [
        # Basic cases
        ("Empty program", ""),
        ("Comment", "-- comment"),
        ("Simple assignment", "local x = 1"),
        ("Multiple assignment", "local a, b = 1, 2"),
        
        # Expression cases
        ("Arithmetic expression", "return 1 + 2 * 3"),
        ("Logical expression", "return a and b or c"),
        ("Comparison expression", "return x > 0 and x < 10"),
        ("String concatenation", "return 'a' .. 'b' .. 'c'"),
        ("Unary operators", "return -x + #t + not b"),
        
        # Table cases
        ("Empty table", "local t = {}"),
        ("List table", "local t = {1, 2, 3}"),
        ("Dictionary table", "local t = {x = 1, y = 2}"),
        ("Mixed table", "local t = {1, x = 2, [3] = 4}"),
        
        # Function cases
        ("Simple function", "function f() return 1 end"),
        ("Function with params", "function add(a, b) return a + b end"),
        ("Local function", "local function f() end"),
        ("Anonymous function", "local f = function(x) return x end"),
        ("Vararg function", "function f(...) return ... end"),
        
        # Control flow cases
        ("If statement", "if x then y = 1 end"),
        ("If-else", "if x then y = 1 else y = 2 end"),
        ("If-elseif", "if a then b() elseif c then d() else e() end"),
        ("While loop", "while x > 0 do x = x - 1 end"),
        ("Repeat loop", "repeat x = x + 1 until x > 10"),
        ("Numeric for", "for i = 1, 10 do print(i) end"),
        ("For with step", "for i = 10, 1, -1 do print(i) end"),
        ("Generic for", "for k, v in pairs(t) do print(k, v) end"),
        ("Do block", "do local x = 1 end"),
        
        # Call cases
        ("Simple call", "print('hello')"),
        ("Method call", "obj:method()"),
        ("Chained call", "a.b.c()"),
        ("String argument", "print 'hello'"),
        ("Table argument", "f{1, 2}"),
        
        # Other cases
        ("Break", "while true do break end"),
        ("Goto/label", "goto done; ::done::"),
    ]
    
    passed = 0
    failed = 0
    
    for name, source in test_cases:
        try:
            ast = parse_lua(source, name)
            printer = ASTPrinter()
            ast_text = printer.print(ast)
            print(f"\n[OK] {name}")
            # Display brief AST
            lines = ast_text.split('\n')
            for line in lines[:5]:
                print(f"    {line}")
            if len(lines) > 5:
                print(f"    ... ({len(lines)} lines)")
            passed += 1
        except Exception as e:
            print(f"\n[FAIL] {name}")
            print(f"    Error: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed, {len(test_cases)} total")


def analyze_all_code_files():
    """Analyze all Lua files in code directory"""
    print("=" * 70)
    print("Analyze All Test Files")
    print("=" * 70)
    
    code_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                           'tests', 'code')
    
    if not os.path.exists(code_dir):
        print(f"Directory not found: {code_dir}")
        return
    
    files = sorted(glob.glob(os.path.join(code_dir, '*.lua')))
    
    results = {'passed': 0, 'failed': 0, 'errors': []}
    
    for filepath in files:
        name = os.path.basename(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            ast = parse_lua(source, name)
            printer = ASTPrinter()
            ast_text = printer.print(ast)
            
            # Count AST nodes
            node_count = ast_text.count('\n') + 1
            
            print(f"[OK] {name:40s} ({node_count:4d} nodes)")
            results['passed'] += 1
            
        except Exception as e:
            print(f"[FAIL] {name:40s} Error: {e}")
            results['failed'] += 1
            results['errors'].append((name, str(e)))
    
    print("\n" + "=" * 70)
    print(f"Results: {results['passed']} passed, {results['failed']} failed")
    
    if results['errors']:
        print("\nFailure details:")
        for name, error in results['errors']:
            print(f"  - {name}: {error}")


def main():
    parser = argparse.ArgumentParser(
        description="PyLua AST Analysis Viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -c "local x = 1 + 2"           # Analyze code string
  %(prog)s -f tests/code/simple.lua       # Analyze file
  %(prog)s --batch                         # Run batch tests
  %(prog)s --all                           # Analyze all test files
  %(prog)s -c "print(1)" --full           # Show full info
"""
    )
    
    parser.add_argument("-c", "--code", type=str, help="Analyze code string")
    parser.add_argument("-f", "--file", type=str, help="Analyze file")
    parser.add_argument("--batch", action="store_true", help="Run batch tests")
    parser.add_argument("--all", action="store_true", help="Analyze all test files")
    parser.add_argument("--full", action="store_true", help="Show full info (tokens, bytecode)")
    
    args = parser.parse_args()
    
    if args.batch:
        batch_test()
    elif args.all:
        analyze_all_code_files()
    elif args.file:
        analyze_file(args.file, show_all=args.full)
    elif args.code:
        print_analysis(args.code, "input", show_all=args.full)
    else:
        # Default: run batch test
        batch_test()


if __name__ == "__main__":
    main()
