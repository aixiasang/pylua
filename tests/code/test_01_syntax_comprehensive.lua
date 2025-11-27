-- ============================================================================
-- Comprehensive Lua 5.3 Syntax Test Suite
-- Test every Lua syntax feature in depth
-- Target: ~800 lines comprehensive coverage
-- ============================================================================

print("=== Comprehensive Lua 5.3 Syntax Test ===\n")

local test_count = 0
local pass_count = 0

local function test(name, condition)
    test_count = test_count + 1
    if condition then
        pass_count = pass_count + 1
        print("  PASS: " .. name)
    else
        print("  FAIL: " .. name)
    end
end

-- ============================================================================
-- 1. LITERALS & BASIC TYPES
-- ============================================================================
print("\n[1] Literals & Basic Types")

test("nil type", type(nil) == "nil")
test("nil equality", nil == nil)
test("true type", type(true) == "boolean")
test("false type", type(false) == "boolean")
test("integer literal", 42 == 42)
test("negative integer", -100 == -100)
test("hex integer", 0xFF == 255)
test("float literal", 3.14 > 3.13)
test("scientific notation", 1.5e3 == 1500)
test("int + int", 10 + 20 == 30)
test("int - int", 50 - 30 == 20)
test("int * int", 6 * 7 == 42)
test("int // int", 10 // 3 == 3)
test("int % int", 10 % 3 == 1)
test("power", 2 ^ 10 == 1024)
test("bitwise and", (0xF0 & 0x0F) == 0)
test("bitwise or", (0xF0 | 0x0F) == 0xFF)
test("bitwise xor", (0xFF ~ 0x0F) == 0xF0)
test("left shift", (1 << 8) == 256)
test("right shift", (256 >> 4) == 16)
test("string literal", "hello" == "hello")
test("string concat", "hello" .. " " .. "world" == "hello world")
test("string length", #"hello" == 5)
test("empty string", "" == "")
test("string comparison", "abc" < "def")
test("tonumber", tonumber("123") == 123)
test("tostring", tostring(123) == "123")

-- ============================================================================
-- 2. VARIABLES & SCOPE
-- ============================================================================
print("\n[2] Variables & Scope")

do
    local x = 10
    test("local var", x == 10)
    x = 20
    test("local reassign", x == 20)
end

global_var = 100
test("global var", global_var == 100)

local a, b, c = 1, 2, 3
test("multiple assign", a == 1 and b == 2 and c == 3)

local x, y = 1, 2
x, y = y, x
test("swap", x == 2 and y == 1)

local function make_counter()
    local count = 0
    return function()
        count = count + 1
        return count
    end
end
local counter = make_counter()
test("closure 1", counter() == 1)
test("closure 2", counter() == 2)
test("closure 3", counter() == 3)

-- ============================================================================
-- 3. TABLES
-- ============================================================================
print("\n[3] Tables")

local empty = {}
test("empty table", type(empty) == "table")

local arr = {1, 2, 3}
test("array [1]", arr[1] == 1)
test("array [2]", arr[2] == 2)
test("array length", #arr == 3)

local map = {x = 10, y = 20}
test("map.x", map.x == 10)
test("map['y']", map["y"] == 20)

local nested = {a = {b = {c = "deep"}}}
test("nested", nested.a.b.c == "deep")

local matrix = {{1,2},{3,4}}
test("matrix", matrix[2][1] == 3)

local sparse = {}
sparse[1] = "a"
sparse[10] = "b"
test("sparse[1]", sparse[1] == "a")
test("sparse[10]", sparse[10] == "b")

-- ============================================================================
-- 4. CONTROL FLOW
-- ============================================================================
print("\n[4] Control Flow")

local result
if 10 > 0 then
    result = "pos"
end
test("if then", result == "pos")

if 10 > 20 then
    result = "a"
else
    result = "b"
end
test("if else", result == "b")

if 10 > 20 then
    result = "x"
elseif 10 > 5 then
    result = "y"
else
    result = "z"
end
test("elseif", result == "y")

local count = 0
while count < 5 do
    count = count + 1
end
test("while", count == 5)

count = 0
repeat
    count = count + 1
until count >= 5
test("repeat", count == 5)

local sum = 0
for i = 1, 10 do
    sum = sum + i
end
test("for 1-10", sum == 55)

sum = 0
for i = 1, 10, 2 do
    sum = sum + i
end
test("for step", sum == 25)

sum = 0
for i, v in ipairs({5, 10, 15}) do
    sum = sum + v
end
test("ipairs", sum == 30)

count = 0
for i = 1, 100 do
    if i > 10 then break end
    count = count + 1
end
test("break", count == 10)

-- ============================================================================
-- 5. FUNCTIONS
-- ============================================================================
print("\n[5] Functions")

local function add(a, b)
    return a + b
end
test("basic function", add(3, 4) == 7)

local function minmax(a, b)
    if a < b then return a, b else return b, a end
end
local min, max = minmax(5, 3)
test("multi return", min == 3 and max == 5)

local function sum_all(...)
    local total = 0
    for i, v in ipairs({...}) do
        total = total + v
    end
    return total
end
test("varargs", sum_all(1, 2, 3, 4, 5) == 15)

local function factorial(n)
    if n <= 1 then return 1 else return n * factorial(n-1) end
end
test("factorial 5", factorial(5) == 120)
test("factorial 10", factorial(10) == 3628800)

local function map(fn, arr)
    local result = {}
    for i, v in ipairs(arr) do
        result[i] = fn(v)
    end
    return result
end
local doubled = map(function(x) return x * 2 end, {1, 2, 3})
test("map", doubled[1] == 2 and doubled[2] == 4)

-- ============================================================================
-- 6. METATABLES
-- ============================================================================
print("\n[6] Metatables")

local t = {}
local mt = {}
setmetatable(t, mt)
test("setmetatable", getmetatable(t) == mt)

local v1 = {x = 1}
local v2 = {x = 2}
setmetatable(v1, {
    __add = function(a, b) return {x = a.x + b.x} end
})
local v3 = v1 + v2
test("__add", v3.x == 3)

setmetatable(v1, {
    __eq = function(a, b) return a.x == b.x end
})
setmetatable(v2, getmetatable(v1))
test("__eq", v1 ~= v2)

local data = {x = 100}
local proxy = {}
setmetatable(proxy, {__index = data})
test("__index", proxy.x == 100)

local store = {}
local tracked = {}
setmetatable(tracked, {
    __newindex = function(t, k, v) store[k] = v end,
    __index = store
})
tracked.val = 42
test("__newindex", store.val == 42)

local custom = {1, 2, 3}
setmetatable(custom, {__len = function(t) return 999 end})
test("__len", #custom == 999)

local callable = {value = 10}
setmetatable(callable, {
    __call = function(t, x) return t.value + x end
})
test("__call", callable(5) == 15)

-- ============================================================================
-- 7. STRING OPERATIONS
-- ============================================================================
print("\n[7] String Operations")

local s = "Hello World"
test("str length", #s == 11)
test("str:sub 1", s:sub(1, 5) == "Hello")
test("str:sub 2", s:sub(7, 11) == "World")
test("str:sub neg", s:sub(-5) == "World")

-- ============================================================================
-- 8. ADVANCED PATTERNS
-- ============================================================================
print("\n[8] Advanced Patterns")

local Point = {}
Point.__index = Point
function Point.new(x, y)
    local self = setmetatable({}, Point)
    self.x = x
    self.y = y
    return self
end
function Point:distance()
    return (self.x * self.x + self.y * self.y) ^ 0.5
end
local p = Point.new(3, 4)
test("OOP", p:distance() == 5.0)

local function range(n)
    local i = 0
    return function()
        i = i + 1
        if i <= n then return i end
    end
end
sum = 0
for i in range(10) do
    sum = sum + i
end
test("iterator", sum == 55)

-- ============================================================================
-- TEST SUMMARY
-- ============================================================================
print("\n" .. string.rep("=", 60))
print("TEST SUMMARY")
print(string.rep("=", 60))
print("Total tests: " .. test_count)
print("Passed: " .. pass_count)
print("Failed: " .. (test_count - pass_count))
print("Success rate: " .. string.format("%.1f%%", (pass_count / test_count) * 100))
print(string.rep("=", 60))

if pass_count == test_count then
    print("\n*** ALL TESTS PASSED ***")
else
    print("\n*** SOME TESTS FAILED ***")
end
