# -*- coding: utf-8 -*-
"""
frontend_test_suite.py - Complete Frontend Test Suite

Perform complete frontend analysis for each Lua file:
1. Lexer test - Lexical analysis
2. AST Parser test - Syntax tree construction
3. Bytecode analysis - Compare with Lua 5.3

Used to verify the correctness of PyLua frontend implementation.

Based on Lua 5.3.6 official implementation.
Author: aixiasang
"""

import sys
import os
import glob
import time
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class FileTestResult:
    """Test result for single file"""
    filename: str
    # Lexer
    lexer_ok: bool = False
    token_count: int = 0
    lexer_error: str = ""
    # AST
    ast_ok: bool = False
    ast_node_count: int = 0
    ast_error: str = ""
    # Bytecode
    bytecode_ok: bool = False
    func_count: int = 0
    inst_count: int = 0
    bytecode_error: str = ""
    # Timing
    lexer_time: float = 0
    ast_time: float = 0


def test_lexer(source: str) -> Tuple[bool, int, str, float]:
    """Test lexical analysis"""
    from pylua.llex import (
        LexState, SemInfo, Token, luaX_next, TK_EOS, EOZ
    )
    from pylua.lobject import TString
    
    start = time.time()
    try:
        ls = LexState()
        source_bytes = source.encode('utf-8')
        
        class SimpleZIO:
            def __init__(self, data):
                self.p = data[1:] if data else b''
                self.n = len(data) - 1 if data else 0
        
        ls.z = SimpleZIO(source_bytes)
        ts = TString()
        ts.data = b"test"
        ls.source = ts
        
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
        
        count = 0
        while True:
            luaX_next(ls)
            count += 1
            if ls.t.token == TK_EOS:
                break
        
        elapsed = time.time() - start
        return True, count, "", elapsed
    
    except Exception as e:
        elapsed = time.time() - start
        return False, 0, str(e), elapsed


def test_ast(source: str, name: str) -> Tuple[bool, int, str, float]:
    """Test AST parsing"""
    from pylua.last_parser import parse_lua
    from pylua.last import ASTPrinter
    
    start = time.time()
    try:
        ast = parse_lua(source, name)
        printer = ASTPrinter()
        ast_text = printer.print(ast)
        node_count = ast_text.count('\n') + 1
        
        elapsed = time.time() - start
        return True, node_count, "", elapsed
    
    except Exception as e:
        elapsed = time.time() - start
        return False, 0, str(e), elapsed


def test_bytecode(source: str) -> Tuple[bool, int, int, str]:
    """Get Lua 5.3 bytecode info"""
    import subprocess
    import tempfile
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', 
                                         delete=False, encoding='utf-8') as f:
            f.write(source)
            src_file = f.name
        
        try:
            result = subprocess.run(
                ['luac53', '-l', src_file],
                capture_output=True,
                timeout=10,
                text=True
            )
            
            if result.returncode != 0:
                return False, 0, 0, result.stderr.strip()
            

            output = result.stdout
            func_count = output.count('function <') + output.count('main <')
            

            import re
            inst_matches = re.findall(r'\t(\d+)\t\[\d+\]\t(\w+)', output)
            inst_count = len(inst_matches)
            
            return True, func_count, inst_count, ""
        
        finally:
            os.unlink(src_file)
    
    except FileNotFoundError:
        return False, 0, 0, "luac53 not found"
    except Exception as e:
        return False, 0, 0, str(e)


def test_file(filepath: str) -> FileTestResult:
    """Test single file"""
    result = FileTestResult(filename=os.path.basename(filepath))
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
    except Exception as e:
        result.lexer_error = str(e)
        result.ast_error = str(e)
        result.bytecode_error = str(e)
        return result
    

    result.lexer_ok, result.token_count, result.lexer_error, result.lexer_time = \
        test_lexer(source)
    

    result.ast_ok, result.ast_node_count, result.ast_error, result.ast_time = \
        test_ast(source, result.filename)
    

    result.bytecode_ok, result.func_count, result.inst_count, result.bytecode_error = \
        test_bytecode(source)
    
    return result


def run_all_tests(directory: str, verbose: bool = False) -> Dict:
    """Run all tests"""
    print("=" * 80)
    print("PyLua Frontend Complete Test Suite")
    print("=" * 80)
    print()
    
    files = sorted(glob.glob(os.path.join(directory, '*.lua')))
    
    results = {
        'total': len(files),
        'lexer_pass': 0,
        'ast_pass': 0,
        'bytecode_pass': 0,
        'all_pass': 0,
        'details': []
    }
    
    # Header
    print(f"{'File':<40} {'Lexer':>8} {'AST':>8} {'Bytecode':>10} {'Status':>8}")
    print("-" * 80)
    
    for filepath in files:
        result = test_file(filepath)
        results['details'].append(result)
        
        if result.lexer_ok:
            results['lexer_pass'] += 1
        if result.ast_ok:
            results['ast_pass'] += 1
        if result.bytecode_ok:
            results['bytecode_pass'] += 1
        
        all_ok = result.lexer_ok and result.ast_ok and result.bytecode_ok
        if all_ok:
            results['all_pass'] += 1
        

        lexer_str = f"{result.token_count:>5}tk" if result.lexer_ok else "FAIL"
        ast_str = f"{result.ast_node_count:>5}nd" if result.ast_ok else "FAIL"
        bc_str = f"{result.func_count}f/{result.inst_count}i" if result.bytecode_ok else "FAIL"
        status = "[OK]" if all_ok else "[FAIL]"
        
        print(f"{result.filename:<40} {lexer_str:>8} {ast_str:>8} {bc_str:>10} {status:>8}")
        
        if verbose and not all_ok:
            if result.lexer_error:
                print(f"    Lexer: {result.lexer_error[:60]}")
            if result.ast_error:
                print(f"    AST: {result.ast_error[:60]}")
            if result.bytecode_error:
                print(f"    Bytecode: {result.bytecode_error[:60]}")
    
    # Summary
    print("-" * 80)
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Files: {results['total']}")
    print(f"Lexer Pass:  {results['lexer_pass']}/{results['total']} "
          f"({100*results['lexer_pass']/results['total']:.1f}%)")
    print(f"AST Pass:    {results['ast_pass']}/{results['total']} "
          f"({100*results['ast_pass']/results['total']:.1f}%)")
    print(f"Bytecode:    {results['bytecode_pass']}/{results['total']} "
          f"({100*results['bytecode_pass']/results['total']:.1f}%)")
    print(f"All Pass:    {results['all_pass']}/{results['total']} "
          f"({100*results['all_pass']/results['total']:.1f}%)")
    

    total_tokens = sum(r.token_count for r in results['details'] if r.lexer_ok)
    total_nodes = sum(r.ast_node_count for r in results['details'] if r.ast_ok)
    total_funcs = sum(r.func_count for r in results['details'] if r.bytecode_ok)
    total_insts = sum(r.inst_count for r in results['details'] if r.bytecode_ok)
    total_lexer_time = sum(r.lexer_time for r in results['details'])
    total_ast_time = sum(r.ast_time for r in results['details'])
    
    print()
    print("Statistics:")
    print(f"  Total Tokens: {total_tokens:,}")
    print(f"  Total AST Nodes: {total_nodes:,}")
    print(f"  Total Functions: {total_funcs:,}")
    print(f"  Total Instructions: {total_insts:,}")
    print(f"  Lexer Time: {total_lexer_time:.3f}s")
    print(f"  AST Time: {total_ast_time:.3f}s")
    
    if results['all_pass'] == results['total']:
        print()
        print("*** ALL TESTS PASSED ***")
    
    return results


def detailed_file_test(filepath: str):
    """Detailed test for single file"""
    print("=" * 80)
    print(f"Detailed Test: {os.path.basename(filepath)}")
    print("=" * 80)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    

    lines = source.split('\n')
    print(f"\nSource: {len(lines)} lines")
    for i, line in enumerate(lines[:10], 1):
        print(f"  {i:3d} | {line[:70]}")
    if len(lines) > 10:
        print(f"  ... ({len(lines) - 10} more lines)")
    
    # Lexer
    print("\n--- Lexer ---")
    ok, count, error, elapsed = test_lexer(source)
    if ok:
        print(f"[OK] {count} tokens in {elapsed:.3f}s")
    else:
        print(f"[FAIL] {error}")
    
    # AST
    print("\n--- AST Parser ---")
    ok, count, error, elapsed = test_ast(source, os.path.basename(filepath))
    if ok:
        print(f"[OK] {count} nodes in {elapsed:.3f}s")
        

        from pylua.last_parser import parse_lua
        from pylua.last import ASTPrinter
        ast = parse_lua(source, os.path.basename(filepath))
        printer = ASTPrinter()
        ast_text = printer.print(ast)
        ast_lines = ast_text.split('\n')
        print("\nAST Preview:")
        for line in ast_lines[:15]:
            print(f"  {line}")
        if len(ast_lines) > 15:
            print(f"  ... ({len(ast_lines) - 15} more lines)")
    else:
        print(f"[FAIL] {error}")
    
    # Bytecode
    print("\n--- Lua 5.3 Bytecode ---")
    ok, funcs, insts, error = test_bytecode(source)
    if ok:
        print(f"[OK] {funcs} functions, {insts} instructions")
        

        from tools.bytecode_compare import get_lua53_bytecode, format_proto
        output, protos = get_lua53_bytecode(source)
        if protos:
            print("\nBytecode Preview:")
            proto = protos[0]
            print(f"  Main function: {proto.num_params} params, "
                  f"{proto.max_stack} slots, {len(proto.instructions)} insts")
            for inst in proto.instructions[:10]:
                comment = f" ; {inst.comment}" if inst.comment else ""
                print(f"    {inst.pc:3d} [{inst.line:3d}] {inst.opcode:12s} "
                      f"{inst.a:3d} {inst.b:3d} {inst.c:3d}{comment}")
            if len(proto.instructions) > 10:
                print(f"    ... ({len(proto.instructions) - 10} more)")
    else:
        print(f"[FAIL] {error}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="PyLua Frontend Complete Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("-f", "--file", type=str, help="Test single file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    
    args = parser.parse_args()
    
    if args.file:
        if os.path.exists(args.file):
            detailed_file_test(args.file)
        else:
            print(f"File not found: {args.file}")
    else:
        code_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                               'tests', 'code')
        run_all_tests(code_dir, args.verbose)


if __name__ == "__main__":
    main()
