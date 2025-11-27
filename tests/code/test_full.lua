-- test_full.lua
-- Comprehensive test suite for PyLua VM (500+ lines)
-- Tests all basic operations, library functions, and edge cases

local function section(name)
    print("")
    print("======================================")
    print("=== " .. name .. " ===")
    print("======================================")
end

local function subsection(name)
    print("")
    print("--- " .. name .. " ---")
end

-- =============================================================================
-- PART 1: Basic Types and Values
-- =============================================================================
section("PART 1: BASIC TYPES AND VALUES")

subsection("nil")
print(nil)
print(type(nil))

subsection("boolean")
print(true)
print(false)
print(type(true))
print(type(false))

subsection("numbers - integers")
print(0)
print(1)
print(-1)
print(42)
print(-42)
print(123456789)
print(-123456789)
print(9223372036854775807)  -- max int64
print(-9223372036854775808) -- min int64
print(type(42))

subsection("numbers - floats")
print(0.0)
print(1.0)
print(-1.0)
print(3.14159265358979)
print(-3.14159265358979)
print(1.5e10)
print(1.5e-10)
print(type(3.14))

subsection("strings")
print("")
print("hello")
print("hello world")
print("with\ttab")
print("with\nnewline")
print(type("hello"))

subsection("string length")
print(#"")
print(#"a")
print(#"hello")
print(#"hello world")

-- =============================================================================
-- PART 2: Arithmetic Operations
-- =============================================================================
section("PART 2: ARITHMETIC OPERATIONS")

subsection("integer addition")
print(0 + 0)
print(1 + 1)
print(1 + 2)
print(10 + 20)
print(-5 + 3)
print(-5 + (-3))
print(1000000 + 1000000)

subsection("integer subtraction")
print(0 - 0)
print(5 - 3)
print(3 - 5)
print(10 - 20)
print(-5 - 3)
print(-5 - (-3))

subsection("integer multiplication")
print(0 * 5)
print(1 * 5)
print(2 * 3)
print(10 * 20)
print(-5 * 3)
print(-5 * (-3))
print(1000 * 1000)

subsection("integer division (//)")
print(10 // 3)
print(10 // 5)
print(15 // 4)
print(-10 // 3)
print(10 // -3)
print(-10 // -3)
print(0 // 5)
print(100 // 7)

subsection("integer modulo (%)")
print(10 % 3)
print(10 % 5)
print(15 % 4)
print(-10 % 3)
print(10 % -3)
print(-10 % -3)
print(0 % 5)
print(100 % 7)

subsection("float addition")
print(0.0 + 0.0)
print(1.5 + 2.5)
print(10.1 + 20.2)
print(-5.5 + 3.3)

subsection("float subtraction")
print(5.5 - 3.3)
print(3.3 - 5.5)
print(-5.5 - 3.3)

subsection("float multiplication")
print(2.0 * 3.0)
print(2.5 * 4.0)
print(-2.5 * 3.0)

subsection("float division (/)")
print(10.0 / 4.0)
print(7.0 / 2.0)
print(1.0 / 3.0)
print(-10.0 / 4.0)

subsection("float floor division (//)")
print(10.0 // 3.0)
print(10.5 // 3.0)
print(-10.0 // 3.0)

subsection("float modulo (%)")
print(10.0 % 3.0)
print(10.5 % 3.0)
print(-10.0 % 3.0)

subsection("power (^)")
print(2 ^ 0)
print(2 ^ 1)
print(2 ^ 2)
print(2 ^ 3)
print(2 ^ 10)
print(2.0 ^ 0.5)
print(10 ^ -1)

subsection("unary minus")
print(-0)
print(-1)
print(-(-1))
print(-42)
print(-3.14)
print(-(-3.14))

subsection("mixed int/float arithmetic")
print(1 + 2.5)
print(2.5 + 1)
print(10 - 2.5)
print(2.5 - 10)
print(3 * 2.5)
print(2.5 * 3)
print(10 / 4)
print(7 / 2)

-- =============================================================================
-- PART 3: Bitwise Operations
-- =============================================================================
section("PART 3: BITWISE OPERATIONS")

subsection("bitwise AND (&)")
print(0xFF & 0x0F)
print(0xF0 & 0x0F)
print(0xFF & 0xFF)
print(0x00 & 0xFF)
print(255 & 15)

subsection("bitwise OR (|)")
print(0xF0 | 0x0F)
print(0x00 | 0xFF)
print(0xFF | 0xFF)
print(240 | 15)

subsection("bitwise XOR (~)")
print(0xFF ~ 0x0F)
print(0xF0 ~ 0x0F)
print(0xFF ~ 0xFF)
print(255 ~ 15)

subsection("bitwise NOT (~)")
print(~0)
print(~1)
print(~(-1))
print(~255)

subsection("left shift (<<)")
print(1 << 0)
print(1 << 1)
print(1 << 4)
print(1 << 8)
print(1 << 16)
print(255 << 4)

subsection("right shift (>>)")
print(256 >> 0)
print(256 >> 1)
print(256 >> 4)
print(256 >> 8)
print(255 >> 4)

subsection("negative shifts")
print(16 << -2)
print(1 >> -4)

-- =============================================================================
-- PART 4: Comparison Operations
-- =============================================================================
section("PART 4: COMPARISON OPERATIONS")

subsection("integer comparisons")
print(1 == 1)
print(1 == 2)
print(1 ~= 1)
print(1 ~= 2)
print(1 < 2)
print(2 < 1)
print(1 <= 1)
print(1 <= 2)
print(2 <= 1)
print(2 > 1)
print(1 > 2)
print(1 >= 1)
print(2 >= 1)
print(1 >= 2)

subsection("float comparisons")
print(1.5 == 1.5)
print(1.5 == 2.5)
print(1.5 ~= 1.5)
print(1.5 ~= 2.5)
print(1.5 < 2.5)
print(2.5 < 1.5)
print(1.5 <= 1.5)
print(1.5 <= 2.5)

subsection("mixed int/float comparisons")
print(5 == 5.0)
print(5 == 5.1)
print(5 < 5.5)
print(5 > 4.5)
print(5 <= 5.0)
print(5.0 <= 5)
print(5.0 == 5)

subsection("string comparisons")
print("a" == "a")
print("a" == "b")
print("a" ~= "a")
print("a" ~= "b")
print("a" < "b")
print("b" < "a")
print("aa" < "ab")
print("abc" < "abd")
print("abc" <= "abc")
print("abc" >= "abc")

subsection("nil comparisons")
print(nil == nil)
print(nil ~= nil)

subsection("boolean comparisons")
print(true == true)
print(false == false)
print(true == false)
print(true ~= false)

-- =============================================================================
-- PART 5: Logical Operations
-- =============================================================================
section("PART 5: LOGICAL OPERATIONS")

subsection("not operator")
print(not true)
print(not false)
print(not nil)
print(not 0)
print(not 1)
print(not "")
print(not "hello")
print(not {})

subsection("and operator")
print(true and true)
print(true and false)
print(false and true)
print(false and false)
print(nil and true)
print(1 and 2)
print(false and 2)
print(nil and 2)

subsection("or operator")
print(true or true)
print(true or false)
print(false or true)
print(false or false)
print(nil or true)
print(nil or false)
print(1 or 2)
print(false or 2)
print(nil or 2)

-- =============================================================================
-- PART 6: String Operations
-- =============================================================================
section("PART 6: STRING OPERATIONS")

subsection("concatenation (..) - strings")
print("a" .. "b")
print("hello" .. " " .. "world")
print("" .. "test")
print("test" .. "")
print("" .. "")
print("abc" .. "def" .. "ghi")

subsection("concatenation (..) - numbers")
print("value: " .. 42)
print("pi: " .. 3.14)
print(42 .. " is a number")
print(3.14 .. " is pi")
print(1 .. 2 .. 3)

subsection("concatenation - mixed")
print("result = " .. (1 + 2))
print("sum of 10 and 20 is " .. (10 + 20))

subsection("string length edge cases")
local s1 = ""
local s2 = "a"
local s3 = "hello world"
print(#s1)
print(#s2)
print(#s3)

-- =============================================================================
-- PART 7: Table Operations
-- =============================================================================
section("PART 7: TABLE OPERATIONS")

subsection("table creation and access")
local t1 = {}
print(type(t1))

local t2 = {10, 20, 30}
print(t2[1])
print(t2[2])
print(t2[3])
print(t2[4])

local t3 = {a = 1, b = 2, c = 3}
print(t3["a"])
print(t3["b"])
print(t3["c"])
print(t3["d"])

subsection("table length")
local t4 = {1, 2, 3, 4, 5}
print(#t4)

local t5 = {}
print(#t5)

local t6 = {10, 20, 30, 40}
print(#t6)

subsection("table modification")
local t7 = {1, 2, 3}
t7[4] = 4
print(t7[4])
print(#t7)

t7[2] = 20
print(t7[2])

t7["key"] = "value"
print(t7["key"])

subsection("nested tables")
local t8 = {{1, 2}, {3, 4}}
print(t8[1][1])
print(t8[1][2])
print(t8[2][1])
print(t8[2][2])

subsection("mixed keys")
local t9 = {[1] = "one", [2] = "two", ["three"] = 3}
print(t9[1])
print(t9[2])
print(t9["three"])

-- =============================================================================
-- PART 8: Control Flow
-- =============================================================================
section("PART 8: CONTROL FLOW")

subsection("if-then-else")
local x = 10
if x > 5 then
    print("x > 5")
else
    print("x <= 5")
end

if x < 5 then
    print("x < 5")
else
    print("x >= 5")
end

if x == 10 then
    print("x == 10")
end

subsection("if-elseif-else")
local y = 20
if y < 10 then
    print("y < 10")
elseif y < 20 then
    print("10 <= y < 20")
elseif y == 20 then
    print("y == 20")
else
    print("y > 20")
end

subsection("numeric for loop")
local sum = 0
for i = 1, 5 do
    sum = sum + i
end
print(sum)

sum = 0
for i = 1, 10, 2 do
    sum = sum + i
end
print(sum)

sum = 0
for i = 10, 1, -1 do
    sum = sum + i
end
print(sum)

sum = 0
for i = 10, 1, -2 do
    sum = sum + i
end
print(sum)

subsection("while loop")
local count = 0
local n = 5
while n > 0 do
    count = count + 1
    n = n - 1
end
print(count)

subsection("repeat-until loop")
count = 0
n = 5
repeat
    count = count + 1
    n = n - 1
until n == 0
print(count)

subsection("break statement")
sum = 0
for i = 1, 100 do
    if i > 5 then
        break
    end
    sum = sum + i
end
print(sum)

-- =============================================================================
-- PART 9: Functions
-- =============================================================================
section("PART 9: FUNCTIONS")

subsection("basic functions")
local function add(a, b)
    return a + b
end
print(add(1, 2))
print(add(10, 20))
print(add(-5, 5))

local function multiply(a, b)
    return a * b
end
print(multiply(3, 4))
print(multiply(5, 6))

subsection("multiple return values")
local function minmax(a, b)
    if a < b then
        return a, b
    else
        return b, a
    end
end
local min, max = minmax(5, 3)
print(min)
print(max)

min, max = minmax(10, 20)
print(min)
print(max)

subsection("variable arguments")
local function sum_all(...)
    local args = {...}
    local total = 0
    for i = 1, #args do
        total = total + args[i]
    end
    return total
end
print(sum_all(1, 2, 3))
print(sum_all(1, 2, 3, 4, 5))
print(sum_all(10))

subsection("closures")
local function make_counter()
    local count = 0
    return function()
        count = count + 1
        return count
    end
end

local counter = make_counter()
print(counter())
print(counter())
print(counter())

local counter2 = make_counter()
print(counter2())

subsection("recursive functions")
local function factorial(n)
    if n <= 1 then
        return 1
    else
        return n * factorial(n - 1)
    end
end
print(factorial(1))
print(factorial(5))
print(factorial(10))

local function fibonacci(n)
    if n <= 2 then
        return 1
    else
        return fibonacci(n - 1) + fibonacci(n - 2)
    end
end
print(fibonacci(1))
print(fibonacci(5))
print(fibonacci(10))

-- =============================================================================
-- PART 10: Library Functions
-- =============================================================================
section("PART 10: LIBRARY FUNCTIONS")

subsection("tostring")
print(tostring(nil))
print(tostring(true))
print(tostring(false))
print(tostring(42))
print(tostring(-42))
print(tostring(3.14))
print(tostring("hello"))

subsection("tonumber")
print(tonumber(42))
print(tonumber(3.14))
print(tonumber("123"))
print(tonumber("45.67"))
print(tonumber("0x1F"))
print(tonumber("invalid"))

subsection("type")
print(type(nil))
print(type(true))
print(type(42))
print(type(3.14))
print(type("hello"))
print(type({}))
print(type(print))

subsection("rawlen")
print(rawlen("hello"))
print(rawlen(""))
print(rawlen({1, 2, 3}))
print(rawlen({}))

subsection("rawequal")
print(rawequal(1, 1))
print(rawequal(1, 2))
print(rawequal("a", "a"))
print(rawequal("a", "b"))
print(rawequal(nil, nil))
print(rawequal(true, true))
print(rawequal(true, false))

subsection("rawget and rawset")
local t = {10, 20, 30}
print(rawget(t, 1))
print(rawget(t, 2))
print(rawget(t, 3))
print(rawget(t, 4))

rawset(t, 4, 40)
print(rawget(t, 4))

rawset(t, "key", "value")
print(rawget(t, "key"))

subsection("select")
print(select("#"))
print(select("#", 1, 2, 3))
print(select("#", "a", "b", "c", "d", "e"))
print(select(1, "a", "b", "c"))
print(select(2, "a", "b", "c"))
print(select(3, "a", "b", "c"))

subsection("assert")
local ok = assert(true)
print(ok)

ok = assert(1)
print(ok)

ok = assert("hello")
print(ok)

subsection("setmetatable and getmetatable")
local mt = {__index = function(t, k) return "default" end}
local obj = {}
setmetatable(obj, mt)
print(getmetatable(obj) == mt)

-- =============================================================================
-- PART 11: Edge Cases and Special Values
-- =============================================================================
section("PART 11: EDGE CASES")

subsection("zero handling")
print(0 + 0)
print(0 - 0)
print(0 * 5)
print(0 / 5)
print(0 // 5)
print(0 % 5)
print(0.0 + 0.0)
print(0.0 - 0.0)
print(0.0 * 5.0)
print(0.0 / 5.0)

subsection("negative zero")
print(-0)
print(-0.0)
print(0 == -0)
print(0.0 == -0.0)

subsection("large numbers")
print(1000000000)
print(1000000000 * 1000)
print(9223372036854775807)
print(-9223372036854775808)

subsection("small floats")
print(0.000001)
print(1e-10)
print(1e-15)

subsection("large floats")
print(1e10)
print(1e50)
print(1e100)

subsection("empty operations")
print(#"")
print(#"" == 0)
local empty = {}
print(#empty)
print(#empty == 0)

-- =============================================================================
-- PART 12: Complex Expressions
-- =============================================================================
section("PART 12: COMPLEX EXPRESSIONS")

subsection("compound arithmetic")
print(1 + 2 * 3)
print((1 + 2) * 3)
print(10 - 5 + 3)
print(10 - (5 + 3))
print(2 ^ 3 ^ 2)
print((2 ^ 3) ^ 2)
print(10 // 3 + 10 % 3)

subsection("compound comparisons")
print(1 < 2 and 2 < 3)
print(1 < 2 and 3 < 2)
print(1 < 2 or 3 < 2)
print(3 < 2 or 4 < 3)

subsection("compound logical")
print(not (true and false))
print(not (true or false))
print((not true) and false)
print((not false) or true)

subsection("mixed operations")
print(1 + 2 == 3)
print(2 * 3 > 5)
print(10 // 3 == 3 and 10 % 3 == 1)
print("hello" .. " " .. "world" == "hello world")

-- =============================================================================
-- COMPLETE
-- =============================================================================
section("TEST COMPLETE")
print("All tests executed successfully!")
