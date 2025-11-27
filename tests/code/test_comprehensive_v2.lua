-- test_comprehensive_v2.lua
-- Comprehensive test suite for PyLua VM (500+ lines)
-- All tests verified to work correctly

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
section("PART 1: BASIC TYPES")

subsection("nil and boolean")
print(nil)
print(type(nil))
print(true)
print(false)
print(type(true))

subsection("integers")
print(0)
print(1)
print(-1)
print(42)
print(-42)
print(123456789)
print(-123456789)
print(type(42))

subsection("floats")
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
print(type("hello"))
print(#"")
print(#"a")
print(#"hello")

-- =============================================================================
-- PART 2: Arithmetic Operations
-- =============================================================================
section("PART 2: ARITHMETIC")

subsection("integer arithmetic")
print(0 + 0)
print(1 + 2)
print(10 + 20)
print(-5 + 3)
print(5 - 3)
print(3 - 5)
print(-5 - 3)
print(2 * 3)
print(10 * 20)
print(-5 * 3)

subsection("integer division and modulo")
print(10 // 3)
print(10 // 5)
print(-10 // 3)
print(10 // -3)
print(-10 // -3)
print(10 % 3)
print(10 % 5)
print(-10 % 3)
print(10 % -3)
print(-10 % -3)

subsection("float arithmetic")
print(1.5 + 2.5)
print(5.5 - 3.3)
print(2.5 * 4.0)
print(10.0 / 4.0)
print(10.0 // 3.0)
print(10.5 % 3.0)

subsection("power")
print(2 ^ 0)
print(2 ^ 1)
print(2 ^ 10)
print(2.0 ^ 0.5)

subsection("unary minus")
print(-0)
print(-1)
print(-(-1))
print(-3.14)

subsection("mixed arithmetic")
print(1 + 2.5)
print(10 - 2.5)
print(3 * 2.5)
print(10 / 4)

-- =============================================================================
-- PART 3: Bitwise Operations
-- =============================================================================
section("PART 3: BITWISE")

subsection("bitwise operations")
print(0xFF & 0x0F)
print(0xF0 | 0x0F)
print(0xFF ~ 0x0F)
print(~0)
print(~1)
print(1 << 4)
print(256 >> 4)
print(16 << -2)

-- =============================================================================
-- PART 4: Comparisons
-- =============================================================================
section("PART 4: COMPARISONS")

subsection("integer comparisons")
print(1 == 1)
print(1 == 2)
print(1 ~= 2)
print(1 < 2)
print(2 < 1)
print(1 <= 1)
print(2 > 1)
print(1 >= 1)

subsection("float comparisons")
print(1.5 == 1.5)
print(1.5 < 2.5)
print(1.5 <= 1.5)

subsection("mixed comparisons")
print(5 == 5.0)
print(5 < 5.5)
print(5.0 <= 5)

subsection("string comparisons")
print("a" == "a")
print("a" < "b")
print("abc" < "abd")
print("abc" <= "abc")

subsection("nil and boolean comparisons")
print(nil == nil)
print(true == true)
print(true ~= false)

-- =============================================================================
-- PART 5: Logical Operations
-- =============================================================================
section("PART 5: LOGICAL")

subsection("not operator")
print(not true)
print(not false)
print(not nil)
print(not 0)
print(not "")

subsection("and operator")
print(true and true)
print(true and false)
print(false and true)
print(1 and 2)
print(false and 2)

subsection("or operator")
print(true or false)
print(false or true)
print(nil or true)
print(1 or 2)
print(false or 2)

-- =============================================================================
-- PART 6: String Operations
-- =============================================================================
section("PART 6: STRINGS")

subsection("concatenation")
print("a" .. "b")
print("hello" .. " " .. "world")
print("" .. "test")
print("value: " .. 42)
print("pi: " .. 3.14)
print(1 .. 2 .. 3)

-- =============================================================================
-- PART 7: Table Operations
-- =============================================================================
section("PART 7: TABLES")

subsection("array tables")
local t1 = {10, 20, 30}
print(t1[1])
print(t1[2])
print(t1[3])
print(#t1)

subsection("table modification")
local t2 = {1, 2, 3}
t2[4] = 4
print(t2[4])
print(#t2)

subsection("string key tables")
local t3 = {}
t3["a"] = 1
t3["b"] = 2
print(t3["a"])
print(t3["b"])

local t4 = {x = 10, y = 20}
print(t4["x"])
print(t4["y"])
print(t4.x)
print(t4.y)

subsection("nested tables")
local t5 = {{1, 2}, {3, 4}}
print(t5[1][1])
print(t5[1][2])
print(t5[2][1])
print(t5[2][2])

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

if x == 10 then
    print("x == 10")
end

subsection("if-elseif-else")
local y = 20
if y < 10 then
    print("y < 10")
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

subsection("while loop")
local count = 0
local n = 5
while n > 0 do
    count = count + 1
    n = n - 1
end
print(count)

subsection("repeat-until")
count = 0
n = 5
repeat
    count = count + 1
    n = n - 1
until n == 0
print(count)

subsection("break")
sum = 0
for i = 1, 100 do
    if i > 5 then break end
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

local function multiply(a, b)
    return a * b
end
print(multiply(3, 4))

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

subsection("vararg functions")
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

subsection("recursion")
local function factorial(n)
    if n <= 1 then return 1 end
    return n * factorial(n - 1)
end
print(factorial(1))
print(factorial(5))
print(factorial(10))

local function fibonacci(n)
    if n <= 2 then return 1 end
    return fibonacci(n - 1) + fibonacci(n - 2)
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
print(tostring(3.14))
print(tostring("hello"))

subsection("tonumber")
print(tonumber(42))
print(tonumber("123"))
print(tonumber("45.67"))
print(tonumber("0x1F"))

subsection("type")
print(type(nil))
print(type(true))
print(type(42))
print(type("hello"))
print(type({}))
print(type(print))

subsection("rawlen")
print(rawlen("hello"))
print(rawlen({1, 2, 3}))

subsection("rawequal")
print(rawequal(1, 1))
print(rawequal(1, 2))
print(rawequal("a", "a"))
print(rawequal(nil, nil))

subsection("rawget and rawset")
local t = {10, 20, 30}
print(rawget(t, 1))
print(rawget(t, 2))
rawset(t, 4, 40)
print(rawget(t, 4))

subsection("select")
print(select("#", 1, 2, 3))
print(select(1, "a", "b", "c"))
print(select(2, "a", "b", "c"))

subsection("assert")
local ok = assert(true)
print(ok)

subsection("metatable")
local mt = {}
local obj = {}
setmetatable(obj, mt)
print(getmetatable(obj) == mt)

-- =============================================================================
-- PART 11: Edge Cases
-- =============================================================================
section("PART 11: EDGE CASES")

subsection("zero handling")
print(0 + 0)
print(0 * 5)
print(0 / 5)
print(0.0 + 0.0)

subsection("negative zero")
print(-0)
print(0 == -0)

subsection("large numbers")
print(1000000000)
print(1000000000 * 1000)

subsection("small floats")
print(0.000001)
print(1e-10)

subsection("empty operations")
print(#"")
local empty = {}
print(#empty)

-- =============================================================================
-- PART 12: Complex Expressions
-- =============================================================================
section("PART 12: COMPLEX EXPRESSIONS")

subsection("compound arithmetic")
print(1 + 2 * 3)
print((1 + 2) * 3)
print(10 - 5 + 3)
print(2 ^ 3 ^ 2)

subsection("compound comparisons")
print(1 < 2 and 2 < 3)
print(1 < 2 or 3 < 2)

subsection("compound logical")
print(not (true and false))
print(not (true or false))

subsection("mixed operations")
print(1 + 2 == 3)
print(2 * 3 > 5)
print("hello" .. " " .. "world" == "hello world")

-- =============================================================================
-- PART 13: Additional Arithmetic Tests
-- =============================================================================
section("PART 13: MORE ARITHMETIC")

subsection("boundary integer operations")
print(2147483647 + 1)
print(-2147483648 - 1)
print(1000000 * 1000000)
print(999999999 // 7)
print(999999999 % 7)

subsection("float precision")
print(0.1 + 0.2)
print(1.0 / 3.0)
print(2.0 / 3.0)
print(1.0 / 7.0)

subsection("mixed precision")
print(1 + 0.1)
print(100 - 0.01)
print(5 * 0.5)

-- =============================================================================
-- PART 14: More String Tests
-- =============================================================================
section("PART 14: MORE STRINGS")

subsection("string edge cases")
print("" .. "")
print("a" .. "")
print("" .. "b")
print(#"test string here")

subsection("number to string concat")
print("result=" .. 100)
print("value=" .. -50)
print("float=" .. 1.5)
print(100 .. "")
print(-50 .. "test")

-- =============================================================================
-- PART 15: More Table Tests
-- =============================================================================
section("PART 15: MORE TABLES")

subsection("table growth")
local grow = {}
for i = 1, 10 do
    grow[i] = i * 10
end
print(#grow)
print(grow[1])
print(grow[5])
print(grow[10])

subsection("mixed key types")
local mixed = {}
mixed[1] = "one"
mixed["two"] = 2
mixed[3] = "three"
print(mixed[1])
print(mixed["two"])
print(mixed[3])

subsection("table overwrite")
local over = {a = 1, b = 2}
over["a"] = 10
over["b"] = 20
print(over.a)
print(over.b)

-- =============================================================================
-- PART 16: More Control Flow
-- =============================================================================
section("PART 16: MORE CONTROL")

subsection("nested if")
local a, b = 5, 10
if a < b then
    if a < 3 then
        print("a < 3")
    else
        print("a >= 3")
    end
else
    print("a >= b")
end

subsection("nested loops")
local result = 0
for i = 1, 3 do
    for j = 1, 3 do
        result = result + i * j
    end
end
print(result)

subsection("loop with conditions")
local filtered = 0
for i = 1, 20 do
    if i % 2 == 0 then
        filtered = filtered + i
    end
end
print(filtered)

-- =============================================================================
-- PART 17: More Function Tests
-- =============================================================================
section("PART 17: MORE FUNCTIONS")

subsection("nested function calls")
local function double(x)
    return x * 2
end
local function triple(x)
    return x * 3
end
print(double(triple(5)))
print(triple(double(5)))

subsection("function as argument")
local function apply(f, x)
    return f(x)
end
print(apply(double, 10))
print(apply(triple, 10))

subsection("returning functions")
local function make_adder(n)
    return function(x)
        return x + n
    end
end
local add5 = make_adder(5)
local add10 = make_adder(10)
print(add5(3))
print(add10(3))

-- =============================================================================
-- PART 18: Complex Scenarios
-- =============================================================================
section("PART 18: COMPLEX")

subsection("fibonacci with table")
local function fib_table(n)
    local t = {1, 1}
    for i = 3, n do
        t[i] = t[i-1] + t[i-2]
    end
    return t[n]
end
print(fib_table(1))
print(fib_table(5))
print(fib_table(10))

subsection("accumulator pattern")
local function make_acc(init)
    local sum = init
    return function(x)
        sum = sum + x
        return sum
    end
end
local acc = make_acc(0)
print(acc(1))
print(acc(2))
print(acc(3))

subsection("conditional expression")
local function abs_val(x)
    return x < 0 and -x or x
end
print(abs_val(5))
print(abs_val(-5))
print(abs_val(0))

-- =============================================================================
-- COMPLETE
-- =============================================================================
section("TEST COMPLETE")
print("All tests executed successfully!")
