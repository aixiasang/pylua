# -*- coding: utf-8 -*-
"""
run_comparison_test.py - Compare PyLua and lua53 output

This script:
1. Runs lua53 on a .lua file and captures output
2. Compiles the .lua file to .luac
3. Runs PyLua on the .luac file and captures output
4. Compares the two outputs

Usage: py utils/run_comparison_test.py <test_file.lua>
       py utils/run_comparison_test.py --all

Author: aixiasang
"""

import sys
import os
import subprocess
import tempfile


def run_lua53(lua_file):
    """Run lua53 and capture output"""
    result = subprocess.run(
        ['lua53', lua_file],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    return result.stdout, result.returncode


def compile_lua(lua_file, luac_file):
    """Compile lua file to bytecode"""
    result = subprocess.run(
        ['luac53', '-o', luac_file, lua_file],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def run_pylua(luac_file):
    """Run PyLua on bytecode and capture output"""
    # Import PyLua modules
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from io import StringIO
    import contextlib
    
    # Capture stdout
    captured = StringIO()
    
    with open(luac_file, 'rb') as f:
        data = f.read()
    
    from pylua import LUA_SIGNATURE, lua_newstate, luaU_undump, luaV_execute, LUA_MULTRET
    from pylua.lstate import CallInfo, CIST_LUA
    from pylua.lobject import TValue, Table, TString, UpVal, CClosure, LUA_TTABLE, LUA_TCCL, LUA_TSHRSTR, Node
    from pylua.lobject import setclCvalue, setnilvalue, ctb, LUA_TLCL
    from pylua.lzio import ZIO, luaZ_init, BytesReader
    from pylua.ltm import luaT_init
    
    def default_alloc(ud, ptr, osize, nsize):
        return None
    
    def create_env_table(L):
        from pylua.lbaselib import luaopen_base, luaB_tostring_value
        
        env = Table()
        env.tt = LUA_TTABLE
        env.metatable = None
        env.array = []
        env.sizearray = 0
        env.node = []
        env.flags = 0
        env.lsizenode = 0
        
        # Output list to capture prints
        output_lines = []
        
        # Custom print that captures output for comparison
        def lua_print_capture(L):
            ci = L.ci
            base = ci.base if ci else 1
            nargs = L.top - base
            
            parts = []
            for i in range(nargs):
                v = L.stack[base + i]
                s = luaB_tostring_value(L, v)
                parts.append(s)
            
            line = "\t".join(parts)
            output_lines.append(line)
            return 0
        
        # Open base library
        luaopen_base(L, env)
        
        # Open os library
        from pylua.loslib import luaopen_os
        luaopen_os(L, env)
        
        # Open math library
        from pylua.lmathlib import luaopen_math
        luaopen_math(L, env)
        
        # Open string library
        from pylua.lstrlib import luaopen_string
        luaopen_string(L, env)
        
        # Open table library
        from pylua.ltablib import luaopen_table
        luaopen_table(L, env)
        
        # Open package library
        from pylua.lloadlib import luaopen_package
        luaopen_package(L, env)
        
        # Open coroutine library
        from pylua.lcorolib import luaopen_coroutine
        luaopen_coroutine(L, env)
        
        # Open io library
        from pylua.liolib import luaopen_io
        luaopen_io(L, env)
        
        # Override print with capturing version
        from pylua.lobject import TKey, ctb
        for node in env.node:
            if hasattr(node.i_key.value_.gc, 'data') and node.i_key.value_.gc.data == b"print":
                # Replace print function
                closure = CClosure()
                closure.tt = LUA_TCCL
                closure.nupvalues = 0
                closure.f = lua_print_capture
                closure.upvalue = []
                setclCvalue(L, node.i_val, closure)
                break
        
        return env, output_lines
    
    if not data.startswith(LUA_SIGNATURE):
        return None, "Not a valid Lua bytecode file"
    
    L = lua_newstate(default_alloc, None)
    if L is None:
        return None, "Failed to create Lua state"
    
    z = ZIO()
    reader = BytesReader(data)
    luaZ_init(L, z, reader, None)
    z.n = len(data) - 1
    z.p = data[1:]
    z.pos = 0
    
    try:
        cl = luaU_undump(L, z, luac_file)
        
        luaT_init(L)
        env, output_lines = create_env_table(L)
        
        env_val = TValue()
        env_val.tt_ = LUA_TTABLE | (1 << 6)
        env_val.value_.gc = env
        
        uv = UpVal()
        uv.v = env_val
        uv.value = env_val
        uv.refcount = 1
        
        if cl.nupvalues > 0:
            cl.upvals[0] = uv
        
        stack_size = max(cl.p.maxstacksize + 50, 100)
        while len(L.stack) < stack_size:
            L.stack.append(TValue())
        
        func_val = L.stack[0]
        func_val.value_.gc = cl
        func_val.tt_ = ctb(LUA_TLCL)
        
        ci = CallInfo()
        ci.func = 0
        ci.base = 1
        ci.top = 1 + cl.p.maxstacksize
        ci.savedpc = 0
        ci.nresults = LUA_MULTRET
        ci.callstatus = CIST_LUA
        ci.previous = L.base_ci
        L.base_ci.next = ci
        
        L.ci = ci
        L.top = ci.top
        L.stacksize = stack_size
        L.stack_last = stack_size - 5
        
        for i in range(1, ci.top + 1):
            if i < len(L.stack):
                setnilvalue(L.stack[i])
        
        luaV_execute(L)
        
        return "\n".join(output_lines), None
    
    except SystemExit as e:
        # os.exit was called - this is normal behavior
        return "\n".join(output_lines), None
        
    except Exception as e:
        import traceback
        return None, f"{type(e).__name__}: {e}\n{traceback.format_exc()}"


def normalize_output(output):
    """Normalize output for comparison"""
    if output is None:
        return []
    lines = output.strip().split('\n')
    normalized = []
    for line in lines:
        line = line.strip()
        # Normalize float precision differences
        try:
            f = float(line)
            # Round to 10 decimal places for comparison
            normalized.append(f"{f:.10g}")
        except ValueError:
            normalized.append(line)
    return normalized


def compare_outputs(lua_output, pylua_output):
    """Compare outputs and report differences"""
    lua_lines = normalize_output(lua_output)
    pylua_lines = normalize_output(pylua_output)
    
    if lua_lines == pylua_lines:
        return True, []
    
    differences = []
    max_lines = max(len(lua_lines), len(pylua_lines))
    
    for i in range(max_lines):
        lua_line = lua_lines[i] if i < len(lua_lines) else "<missing>"
        pylua_line = pylua_lines[i] if i < len(pylua_lines) else "<missing>"
        
        if lua_line != pylua_line:
            differences.append((i + 1, lua_line, pylua_line))
    
    return False, differences


def run_all_tests():
    """Run all tests in tests/code directory"""
    import glob
    
    test_dir = os.path.join("tests", "code")
    test_files = glob.glob(os.path.join(test_dir, "*.lua"))
    
    if not test_files:
        print(f"No test files found in {test_dir}")
        return 1
    
    passed = 0
    failed = 0
    errors = []
    
    print(f"Running {len(test_files)} tests...")
    print("=" * 60)
    
    for lua_file in sorted(test_files):
        base_name = os.path.basename(lua_file)
        luac_name = base_name.replace('.lua', '.luac')
        luac_file = os.path.join("tests", "out", luac_name)
        
        print(f"\n[{base_name}]", end=" ")
        
        # Run lua53
        lua_output, lua_rc = run_lua53(lua_file)
        
        if lua_rc != 0 and not lua_output:
            print("SKIP (lua53 failed)")
            continue
        
        # Compile
        if not compile_lua(lua_file, luac_file):
            print("SKIP (compile failed)")
            continue
        
        # Run PyLua
        pylua_output, error = run_pylua(luac_file)
        
        if error:
            print(f"ERROR: {error.split(chr(10))[0]}")
            errors.append((base_name, error))
            failed += 1
            continue
        
        # Compare
        match, differences = compare_outputs(lua_output, pylua_output)
        
        if match:
            print("PASS")
            passed += 1
        else:
            print(f"FAIL ({len(differences)} differences)")
            errors.append((base_name, f"{len(differences)} output differences"))
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {len(test_files)} total")
    
    if errors:
        print("\nFailed tests:")
        for name, err in errors:
            print(f"  - {name}: {err[:50]}...")
    
    return 0 if failed == 0 else 1


def main():
    if len(sys.argv) < 2:
        print("Usage: py run_comparison_test.py <test_file.lua>")
        print("       py run_comparison_test.py --all")
        return 1
    
    # Run all tests
    if sys.argv[1] == "--all":
        return run_all_tests()
    
    lua_file = sys.argv[1]
    
    # Check if file is in tests/code directory
    if not os.path.exists(lua_file):
        # Try tests/code directory
        alt_path = os.path.join("tests", "code", lua_file)
        if os.path.exists(alt_path):
            lua_file = alt_path
        else:
            print(f"Error: File not found: {lua_file}")
            return 1
    
    # Determine output path for luac
    base_name = os.path.basename(lua_file)
    luac_name = base_name.replace('.lua', '.luac')
    luac_file = os.path.join("tests", "out", luac_name)
    
    print(f"Testing: {lua_file}")
    print("=" * 60)
    
    # Run lua53
    print("Running lua53...")
    lua_output, lua_rc = run_lua53(lua_file)
    
    if lua_rc != 0 and not lua_output:
        print(f"lua53 failed with exit code {lua_rc} and no output")
        return 1
    elif lua_rc != 0:
        print(f"lua53 exited with code {lua_rc} (continuing with output comparison)")
    
    # Compile
    print(f"Compiling to {luac_file}...")
    
    if not compile_lua(lua_file, luac_file):
        print("Compilation failed")
        return 1
    
    # Run PyLua
    print("Running PyLua...")
    pylua_output, error = run_pylua(luac_file)
    
    if error:
        print(f"PyLua error: {error}")
        return 1
    
    # Compare
    print("Comparing outputs...")
    match, differences = compare_outputs(lua_output, pylua_output)
    
    print("-" * 60)
    
    if match:
        print("✓ PASS: Outputs match!")
        return 0
    else:
        print("✗ FAIL: Outputs differ!")
        print(f"\nFound {len(differences)} difference(s)")
        
        # Show first difference with context (5 lines before)
        first_diff = differences[0]
        line_num, lua_line, pylua_line = first_diff
        
        print(f"\n=== First difference at line {line_num} ===")
        
        # Get lua output lines for context
        lua_output_lines = normalize_output(lua_output)
        
        # Show context - 5 lines before the error
        print("\n--- Context (5 lines before error) ---")
        start_ctx = max(0, line_num - 6)
        for i in range(start_ctx, line_num - 1):
            if i < len(lua_output_lines):
                print(f"  [{i+1}] {lua_output_lines[i]}")
        
        print(f"\n--- Line {line_num} (MISMATCH) ---")
        print(f"  lua53:  {lua_line}")
        print(f"  pylua:  {pylua_line}")
        
        # Show all differences summary
        if len(differences) > 1:
            print(f"\n--- Other differences ({len(differences) - 1} more) ---")
            for ln, ll, pl in differences[1:5]:
                print(f"  Line {ln}: lua53='{ll}' vs pylua='{pl}'")
            if len(differences) > 5:
                print(f"  ... and {len(differences) - 5} more")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
