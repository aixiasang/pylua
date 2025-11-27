#!/usr/bin/env python3
"""
PyLua Command Line Interface

A Python implementation of Lua 5.3 compiler and runtime.
Compatible with luac53 command line interface, with additional features.

Usage:
    pylua [options] [filenames]

luac53-compatible options:
    -l          List (use -l -l for full listing)
    -o name     Output to file 'name' (default is "luac.out")
    -p          Parse only (syntax check)
    -s          Strip debug information
    -v          Show version information
    --          Stop handling options

Extended options:
    -e stat     Execute string 'stat'
    -i          Enter interactive mode
    --tokens    Show lexer tokens
    --ast       Show parser AST (proto structure)
    --compile   Compile and show bytecode (default)
    --run       Compile and execute
    --help      Show this help message

Examples:
    pylua -l test.lua           # List bytecode
    pylua -p test.lua           # Syntax check only
    pylua -e "print('hello')"   # Execute Lua code
    pylua --tokens test.lua     # Show tokens
    pylua --run test.lua        # Execute file
    pylua -i                    # Interactive mode
"""

import sys
import os
import argparse
from typing import Optional, List, Tuple

# Version info
PYLUA_VERSION = "0.1.0"
LUA_VERSION = "5.3"
PYLUA_COPYRIGHT = "PyLua - A Python implementation of Lua 5.3"


def get_version_string() -> str:
    """Get version string similar to luac53"""
    return f"PyLua {PYLUA_VERSION} (Lua {LUA_VERSION} compatible)"


def compile_file(filename: str) -> Tuple[Optional['CompiledProto'], str]:
    """Compile a Lua file and return CompiledProto"""
    from .compile import pylua_compile
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        return pylua_compile(source, f"@{filename}")
    except FileNotFoundError:
        return None, f"cannot open {filename}: No such file or directory"
    except Exception as e:
        return None, str(e)


def compile_string(source: str, name: str = "=(command line)") -> Tuple[Optional['CompiledProto'], str]:
    """Compile a Lua string and return CompiledProto"""
    from .compile import pylua_compile
    return pylua_compile(source, name)


def tokenize_source(source: str, name: str = "=stdin") -> List[dict]:
    """Tokenize Lua source and return list of tokens"""
    from .llex import LexState, luaX_setinput, luaX_next, TK_EOS, luaX_token2str
    from .lzio import Mbuffer, ZIO
    
    tokens = []
    
    # Create lexer state
    ls = LexState()
    ls.buff = Mbuffer()
    ls.L = None
    ls.lookahead.token = TK_EOS
    ls.linenumber = 1
    ls.lastline = 1
    ls.source = name
    ls.envn = "_ENV"
    ls.decpoint = ord('.')
    
    # Create ZIO from source
    z = ZIO(source.encode('utf-8'))
    luaX_setinput(None, ls, z, name, ord(source[0]) if source else -1)
    
    # Collect tokens
    while True:
        luaX_next(ls)
        token_type = ls.t.token
        
        token_info = {
            'type': token_type,
            'name': luaX_token2str(ls, token_type),
            'line': ls.linenumber,
        }
        
        # Add semantic info if present
        if hasattr(ls.t, 'seminfo'):
            si = ls.t.seminfo
            if hasattr(si, 'i'):
                token_info['value'] = si.i
            elif hasattr(si, 'r'):
                token_info['value'] = si.r
            elif hasattr(si, 'ts') and si.ts:
                if hasattr(si.ts, 'data'):
                    token_info['value'] = si.ts.data.decode('utf-8') if isinstance(si.ts.data, bytes) else si.ts.data
        
        tokens.append(token_info)
        
        if token_type == TK_EOS:
            break
    
    return tokens


def print_tokens(tokens: List[dict]) -> None:
    """Print tokens in a readable format"""
    print("=" * 60)
    print("TOKENS")
    print("=" * 60)
    print(f"{'Line':<6} {'Type':<20} {'Name':<15} {'Value'}")
    print("-" * 60)
    
    for tok in tokens:
        line = tok.get('line', 0)
        typ = tok.get('type', 0)
        name = tok.get('name', '?')
        value = tok.get('value', '')
        
        if value:
            print(f"{line:<6} {typ:<20} {name:<15} {value}")
        else:
            print(f"{line:<6} {typ:<20} {name:<15}")


def print_bytecode(proto: 'CompiledProto', full: bool = False) -> None:
    """Print bytecode listing similar to luac -l"""
    from .compile import disassemble
    print(disassemble(proto, show_constants=full, show_locals=full, show_upvalues=full))


def print_proto_structure(proto: 'CompiledProto', indent: int = 0) -> None:
    """Print proto structure (AST-like view)"""
    prefix = "  " * indent
    
    print(f"{prefix}Proto: {proto.source}")
    print(f"{prefix}  linedefined: {proto.linedefined}")
    print(f"{prefix}  lastlinedefined: {proto.lastlinedefined}")
    print(f"{prefix}  numparams: {proto.numparams}")
    print(f"{prefix}  is_vararg: {proto.is_vararg}")
    print(f"{prefix}  maxstacksize: {proto.maxstacksize}")
    print(f"{prefix}  instructions: {len(proto.code)}")
    print(f"{prefix}  constants: {len(proto.constants)}")
    print(f"{prefix}  upvalues: {len(proto.upvalues)}")
    print(f"{prefix}  protos: {len(proto.protos)}")
    
    # Print constants
    if proto.constants:
        print(f"{prefix}  Constants:")
        for idx, val in proto.constants:
            print(f"{prefix}    [{idx}] {val}")
    
    # Print nested protos
    for i, sub in enumerate(proto.protos):
        print(f"{prefix}  SubProto[{i}]:")
        print_proto_structure(sub, indent + 2)


def execute_source(source: str, name: str = "=(command line)") -> int:
    """Execute Lua source code (compilation + bytecode listing)"""
    # Compile and show results
    proto, error = compile_string(source, name)
    if error:
        print(f"pylua: {error}", file=sys.stderr)
        return 1
    
    # Show compilation result
    print(f"Compiled successfully: {len(proto.code)} instructions")
    print_bytecode(proto, full=False)
    
    # Note: Full VM execution requires complete library setup
    # For now, compilation verification is the primary feature
    return 0


def execute_file(filename: str) -> int:
    """Execute a Lua file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        return execute_source(source, f"@{filename}")
    except FileNotFoundError:
        print(f"pylua: cannot open {filename}: No such file or directory", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"pylua: {e}", file=sys.stderr)
        return 1


def write_bytecode(proto: 'CompiledProto', filename: str, strip: bool = False) -> bool:
    """Write compiled bytecode to file (Lua 5.3 format)"""
    from .ldump import luaU_dump
    
    try:
        data = luaU_dump(proto, strip)
        with open(filename, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"pylua: cannot write {filename}: {e}", file=sys.stderr)
        return False


def interactive_mode() -> int:
    """Enter interactive mode (REPL)"""
    print(get_version_string())
    print('Type "exit" or Ctrl+D to quit')
    print()
    
    while True:
        try:
            line = input("> ")
            if line.strip().lower() in ('exit', 'quit'):
                break
            if not line.strip():
                continue
            
            # Try to execute
            execute_source(line)
            
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue
        except Exception as e:
            print(f"Error: {e}")
    
    return 0


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point"""
    if args is None:
        args = sys.argv[1:]
    
    # Parse arguments manually for luac compatibility
    listing = 0  # 0=no, 1=basic, 2=full
    output_file = "luac.out"
    parse_only = False
    strip_debug = False
    execute_string = None
    interactive = False
    show_tokens = False
    show_ast = False
    run_mode = False
    show_version = False
    show_help = False
    filenames = []
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg == '--':
            # Stop processing options
            filenames.extend(args[i+1:])
            break
        elif arg == '-l':
            listing += 1
        elif arg == '-o':
            if i + 1 >= len(args):
                print("pylua: -o needs argument", file=sys.stderr)
                return 1
            i += 1
            output_file = args[i]
        elif arg == '-p':
            parse_only = True
        elif arg == '-s':
            strip_debug = True
        elif arg == '-v':
            show_version = True
        elif arg == '-e':
            if i + 1 >= len(args):
                print("pylua: -e needs argument", file=sys.stderr)
                return 1
            i += 1
            execute_string = args[i]
        elif arg == '-i':
            interactive = True
        elif arg == '--tokens':
            show_tokens = True
        elif arg == '--ast':
            show_ast = True
        elif arg == '--run':
            run_mode = True
        elif arg == '--compile':
            pass  # default behavior
        elif arg == '--help' or arg == '-h':
            show_help = True
        elif arg == '--version':
            show_version = True
        elif arg.startswith('-'):
            print(f"pylua: unrecognized option '{arg}'", file=sys.stderr)
            return 1
        else:
            filenames.append(arg)
        
        i += 1
    
    # Handle special modes
    if show_help:
        print(__doc__)
        return 0
    
    if show_version:
        print(get_version_string())
        return 0
    
    # Execute string mode
    if execute_string is not None:
        return execute_source(execute_string)
    
    # Interactive mode
    if interactive:
        return interactive_mode()
    
    # No files specified
    if not filenames:
        if sys.stdin.isatty():
            return interactive_mode()
        else:
            # Read from stdin
            source = sys.stdin.read()
            proto, error = compile_string(source, "=stdin")
            if error:
                print(f"pylua: {error}", file=sys.stderr)
                return 1
            if listing:
                print_bytecode(proto, full=(listing > 1))
            return 0
    
    # Process files
    for filename in filenames:
        # Show tokens
        if show_tokens:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    source = f.read()
                tokens = tokenize_source(source, f"@{filename}")
                print(f"\n=== {filename} ===")
                print_tokens(tokens)
            except Exception as e:
                print(f"pylua: {filename}: {e}", file=sys.stderr)
                return 1
            continue
        
        # Compile
        proto, error = compile_file(filename)
        if error:
            print(f"pylua: {error}", file=sys.stderr)
            return 1
        
        # Parse only (syntax check)
        if parse_only:
            continue
        
        # Show AST
        if show_ast:
            print(f"\n=== {filename} ===")
            print_proto_structure(proto)
            continue
        
        # Run mode
        if run_mode:
            ret = execute_file(filename)
            if ret != 0:
                return ret
            continue
        
        # Listing mode
        if listing:
            print(f"\n=== {filename} ===")
            print_bytecode(proto, full=(listing > 1))
            continue
        
        # Default: write bytecode
        if not write_bytecode(proto, output_file, strip_debug):
            return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
