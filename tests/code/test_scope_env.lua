-- test_scope_env.lua
-- Variable scope and environment tests

print("=== Scope and Environment Tests ===")

local passed = 0
local failed = 0

local function test(name, condition)
    if condition then
        passed = passed + 1
        print("PASS: " .. name)
    else
        failed = failed + 1
        print("FAIL: " .. name)
    end
end

-- ============================================================================
-- 1. Local Variables
-- ============================================================================
print("\n--- Local Variables ---")

local x = 10
test("local declaration", x == 10)

do
    local x = 20  -- shadows outer x
    test("shadowed local", x == 20)
end
test("outer after shadow", x == 10)

local a, b, c = 1, 2, 3
test("multiple locals", a == 1 and b == 2 and c == 3)

local d, e = 1
test("fewer values", d == 1 and e == nil)

local f, g = 1, 2, 3  -- extra value discarded
test("extra values", f == 1 and g == 2)

-- ============================================================================
-- 2. Block Scope
-- ============================================================================
print("\n--- Block Scope ---")

local outer = 100

if true then
    local inner = 200
    test("inner visible in if", inner == 200)
    test("outer visible in if", outer == 100)
end

-- inner is not accessible here
local inner_check = pcall(function() return inner end)
test("inner not accessible", inner_check == false or inner == nil)

-- for loop scope
local sum = 0
for i = 1, 3 do
    local square = i * i
    sum = sum + square
end
test("for loop local", sum == 14)

-- ============================================================================
-- 3. Global Variables
-- ============================================================================
print("\n--- Global Variables ---")

-- Access _G
test("_G is table", type(_G) == "table")
test("_G.print", _G.print == print)
test("_G.type", _G.type == type)

-- Set global via _G
_G.my_global = 42
test("set via _G", my_global == 42)

-- Read global
test("read global", _G.my_global == 42)

-- Clean up
_G.my_global = nil
test("clean global", my_global == nil)

-- ============================================================================
-- 4. Upvalues
-- ============================================================================
print("\n--- Upvalues ---")

local function make_adder(n)
    return function(x)
        return x + n  -- n is upvalue
    end
end

local add5 = make_adder(5)
local add10 = make_adder(10)

test("upvalue add5", add5(3) == 8)
test("upvalue add10", add10(3) == 13)
test("independent upvalues", add5(0) == 5 and add10(0) == 10)

-- Mutable upvalue
local function counter()
    local count = 0
    return function()
        count = count + 1
        return count
    end
end

local c = counter()
test("mutable upvalue 1", c() == 1)
test("mutable upvalue 2", c() == 2)
test("mutable upvalue 3", c() == 3)

-- ============================================================================
-- 5. Variable Resolution Order
-- ============================================================================
print("\n--- Resolution Order ---")

local level = "outer"

local function test_resolution()
    test("sees outer level", level == "outer")
    
    local level = "inner"
    test("sees inner level", level == "inner")
    
    do
        local level = "block"
        test("sees block level", level == "block")
    end
    
    test("back to inner", level == "inner")
end

test_resolution()
test("outer unchanged", level == "outer")

-- ============================================================================
-- 6. Closure Over Loop Variable
-- ============================================================================
print("\n--- Loop Variable Closure ---")

local funcs = {}
for i = 1, 3 do
    funcs[i] = function() return i end
end

test("closure 1", funcs[1]() == 1)
test("closure 2", funcs[2]() == 2)
test("closure 3", funcs[3]() == 3)

-- Generic for
funcs = {}
for k, v in pairs({a = 1, b = 2, c = 3}) do
    funcs[k] = function() return v end
end
test("pairs closure", funcs.a() == 1)

-- ============================================================================
-- 7. do-end Block
-- ============================================================================
print("\n--- do-end Block ---")

local result
do
    local temp = 10
    temp = temp * 2
    result = temp
end
test("do block result", result == 20)
-- temp is not accessible

-- Multiple blocks
local total = 0
do
    local x = 10
    total = total + x
end
do
    local x = 20
    total = total + x
end
test("multiple blocks", total == 30)

-- ============================================================================
-- 8. Function Parameters as Locals
-- ============================================================================
print("\n--- Parameter Scope ---")

local outer_param = 100

local function test_params(outer_param)  -- shadows outer
    return outer_param
end

test("param shadows", test_params(50) == 50)
test("outer unchanged", outer_param == 100)

-- Vararg scope
local function vararg_scope(...)
    local args = {...}
    return #args
end
test("vararg scope", vararg_scope(1, 2, 3) == 3)

-- ============================================================================
-- 9. Recursive Reference
-- ============================================================================
print("\n--- Recursive Reference ---")

local function factorial(n)
    if n <= 1 then return 1 end
    return n * factorial(n - 1)
end
test("recursive", factorial(5) == 120)

-- Mutual recursion
local is_even, is_odd

is_even = function(n)
    if n == 0 then return true end
    return is_odd(n - 1)
end

is_odd = function(n)
    if n == 0 then return false end
    return is_even(n - 1)
end

test("mutual even", is_even(4) == true)
test("mutual odd", is_odd(5) == true)

-- ============================================================================
-- 10. Environment Manipulation
-- ============================================================================
print("\n--- Environment ---")

-- Check _VERSION
test("_VERSION exists", type(_VERSION) == "string")
test("_VERSION Lua", _VERSION:find("Lua") ~= nil)

-- Iterate _G
local g_count = 0
for k, v in pairs(_G) do
    g_count = g_count + 1
end
test("_G has entries", g_count > 0)

-- ============================================================================
-- 11. Local Function
-- ============================================================================
print("\n--- Local Function ---")

-- Two equivalent forms
local function f1(x) return x + 1 end
local f2 = function(x) return x + 1 end

test("local function syntax", f1(5) == 6)
test("local function expr", f2(5) == 6)

-- Local function recursion
local function fib(n)
    if n < 2 then return n end
    return fib(n - 1) + fib(n - 2)
end
test("local function recursive", fib(10) == 55)

-- ============================================================================
-- 12. Variable Lifetime
-- ============================================================================
print("\n--- Variable Lifetime ---")

local captured
do
    local temp = "I exist"
    captured = function() return temp end
end
-- temp is out of scope but captured
test("captured survives", captured() == "I exist")

-- Collect references
local refs = {}
for i = 1, 3 do
    local val = i * 10
    refs[i] = function() return val end
end
test("refs survive", refs[1]() == 10 and refs[2]() == 20)

-- ============================================================================
-- Summary
-- ============================================================================
print("\n=== Summary ===")
print("Passed: " .. passed)
print("Failed: " .. failed)
print("Total: " .. (passed + failed))

if failed > 0 then
    os.exit(1)
else
    print("\nAll tests passed!")
end
