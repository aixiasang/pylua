# -*- coding: utf-8 -*-
"""
PyLua Quick Test - Quick test for compilation, bytecode analysis and execution

Based on Lua 5.3.6 official implementation.
Author: aixiasang
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pylua.compile import pylua_compile, disassemble
from pylua.lvm import execute_lua


def test_compile(source: str, name: str = "test"):
    """Compile and show bytecode"""
    print(f"\n{'='*60}")
    print(f"Source: {source[:50]}{'...' if len(source) > 50 else ''}")
    print(f"{'='*60}")
    
    proto, err = pylua_compile(source, name)
    if proto:
        print(disassemble(proto, show_constants=True, show_locals=True))
        return proto
    else:
        print(f"Error: {err}")
        return None


def test_run(source: str, name: str = "test"):
    """Compile and execute Lua code"""
    print(f"\n{'='*60}")
    print(f"Run: {source[:50]}{'...' if len(source) > 50 else ''}")
    print(f"{'='*60}")
    print("Output:")
    try:
        execute_lua(source, name)
        print("\n[OK]")
    except Exception as e:
        print(f"\n[Error] {e}")


def main():
    print("PyLua Quick Test")
    print("=" * 60)
    
    # Test 1: Hello World
    test_compile('print("Hello World")', "hello")
    
    # Test 2: Arithmetic with constant folding
    test_compile('return 1 + 2 * 3 - 4 / 2', "math")
    
    # Test 3: Variables
    test_compile('local a, b = 10, 20; return a + b', "vars")
    
    # Test 4: If statement
    test_compile('local x = 5; if x > 3 then return "big" else return "small" end', "if")
    
    # Test 5: For loop
    test_compile('local sum = 0; for i = 1, 10 do sum = sum + i end; return sum', "for")
    
    # Test 6: Function
    test_compile('local function add(a, b) return a + b end; return add(1, 2)', "func")
    
    # Test 7: Table
    test_compile('local t = {x = 1, y = 2}; return t.x + t.y', "table")
    
    # Test 8: Closure
    test_compile('''
local function counter()
    local n = 0
    return function() n = n + 1; return n end
end
''', "closure")
    
    # Test 9: String operations
    test_compile('local s = "hello" .. " " .. "world"; return s, #s', "string")
    
    # Test 10: Multi-value print
    test_compile('print(1, 2, 3, "test")', "print")
    
    print("\n" + "=" * 60)
    print("EXECUTION TESTS")
    print("=" * 60)
    
    # Execution tests
    test_run('print("Hello, PyLua!")')
    test_run('print(1 + 2 * 3)')
    test_run('local x = 10; local y = 20; print("sum =", x + y)')
    test_run('for i = 1, 5 do print(i) end')
    test_run('local function fact(n) if n <= 1 then return 1 end; return n * fact(n-1) end; print("5! =", fact(5))')
    test_run('local function counter() local n = 0; return function() n = n + 1; return n end end; local c = counter(); print(c(), c(), c())')
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
