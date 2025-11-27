# -*- coding: utf-8 -*-
"""
PyLua VM Execution Test
=======================
Test the VM execution with various Lua code examples.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pylua.lvm import execute_lua


def test(name: str, source: str):
    """Run a test case"""
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"Source: {source[:50]}{'...' if len(source) > 50 else ''}")
    print(f"{'='*60}")
    print("Output:")
    try:
        execute_lua(source)
        print(f"\n[SUCCESS]")
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")


def main():
    print("PyLua VM Execution Tests")
    print("=" * 60)
    
    # Test 1: Simple print
    test("Simple print", "print(42)")
    
    # Test 2: Multiple values
    test("Multiple values", "print(1, 2, 3)")
    
    # Test 3: String print
    test("String print", 'print("Hello")')
    
    # Test 4: Arithmetic
    test("Arithmetic", "print(1 + 2 * 3)")
    
    # Test 5: Local variables
    test("Local variables", "local x = 10; local y = 20; print(x + y)")
    
    # Test 6: If statement
    test("If statement", """
local x = 10
if x > 5 then
    print("big")
else
    print("small")
end
""")
    
    # Test 7: For loop
    test("For loop", """
local sum = 0
for i = 1, 5 do
    sum = sum + i
    print(i)
end
print("sum:", sum)
""")
    
    # Test 8: While loop
    test("While loop", """
local i = 1
while i <= 3 do
    print("i =", i)
    i = i + 1
end
""")
    
    # Test 9: Function definition and call
    test("Function", """
local function add(a, b)
    return a + b
end
print(add(10, 20))
""")
    
    # Test 10: Table
    test("Table", """
local t = {x = 1, y = 2}
print(t.x)
print(t.y)
""")
    
    # Test 11: String concatenation
    test("String concat", """
local a = "Hello"
local b = "World"
print(a .. " " .. b)
""")
    
    # Test 12: Boolean logic
    test("Boolean", """
local x = true
local y = false
print(x and y)
print(x or y)
print(not x)
""")
    
    # Test 13: Comparison
    test("Comparison", """
print(1 < 2)
print(2 > 1)
print(1 == 1)
print(1 ~= 2)
""")
    
    # Test 14: Type function
    test("Type function", """
print(type(123))
print(type("hello"))
print(type(true))
print(type(nil))
print(type({}))
""")
    
    # Test 15: tostring/tonumber
    test("Conversion", """
print(tostring(123))
print(tonumber("456"))
""")
    
    # Test 16: Nested function calls
    test("Nested calls", """
local function double(x)
    return x * 2
end
local function triple(x)
    return x * 3
end
print(double(triple(5)))
""")
    
    # Test 17: Closure
    test("Closure", """
local function counter()
    local n = 0
    return function()
        n = n + 1
        return n
    end
end
local c = counter()
print(c())
print(c())
print(c())
""")
    
    # Test 18: Recursive function
    test("Recursion (factorial)", """
local function fact(n)
    if n <= 1 then
        return 1
    end
    return n * fact(n - 1)
end
print(fact(5))
print(fact(10))
""")
    
    # Test 19: Table array
    test("Table array", """
local arr = {10, 20, 30, 40, 50}
print(arr[1])
print(arr[3])
print(arr[5])
print(#arr)
""")
    
    # Test 20: Repeat-until
    test("Repeat-until", """
local i = 0
repeat
    i = i + 1
    print(i)
until i >= 3
""")
    
    # Test 21: Multiple return values
    test("Multiple returns", """
local function minmax(a, b, c)
    local min = a
    local max = a
    if b < min then min = b end
    if c < min then min = c end
    if b > max then max = b end
    if c > max then max = c end
    return min, max
end
local lo, hi = minmax(5, 2, 8)
print("min:", lo, "max:", hi)
""")
    
    # Test 22: Table with method-like access
    test("Table methods", """
local obj = {
    value = 100,
    getValue = function(self)
        return self.value
    end
}
print(obj:getValue())
""")
    
    # Test 23: Fibonacci
    test("Fibonacci", """
local function fib(n)
    if n <= 1 then return n end
    return fib(n-1) + fib(n-2)
end
for i = 0, 10 do
    print("fib(" .. i .. ") =", fib(i))
end
""")
    
    # Test 24: Generic for with pairs
    test("Generic for (pairs)", """
local t = {a = 1, b = 2, c = 3}
for k, v in pairs(t) do
    print(k, "=", v)
end
""")
    
    # Test 25: ipairs
    test("ipairs", """
local arr = {"one", "two", "three"}
for i, v in ipairs(arr) do
    print(i, v)
end
""")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
