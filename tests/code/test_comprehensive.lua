-- test_comprehensive.lua
-- Comprehensive test suite for Lua 5.3 behavior validation
-- Run with: lua53 test_comprehensive.lua

print("=== Lua 5.3 Comprehensive Test Suite ===")
print()

local passed = 0
local failed = 0

local function test(name, condition, expected, got)
    if condition then
        passed = passed + 1
        print("PASS: " .. name)
    else
        failed = failed + 1
        print("FAIL: " .. name)
        if expected ~= nil then
            print("  Expected: " .. tostring(expected))
            print("  Got: " .. tostring(got))
        end
    end
end

-- ============================================================================
-- 1. Integer Arithmetic Tests
-- ============================================================================
print("\n--- Integer Arithmetic ---")

test("int add", 1 + 2 == 3, 3, 1 + 2)
test("int sub", 5 - 3 == 2, 2, 5 - 3)
test("int mul", 4 * 5 == 20, 20, 4 * 5)
test("int div", 10 // 3 == 3, 3, 10 // 3)
test("int mod", 10 % 3 == 1, 1, 10 % 3)
test("int neg", -5 == -(5), -5, -(5))

-- Negative division and modulo (Lua semantics)
test("neg div floor", -10 // 3 == -4, -4, -10 // 3)
test("neg mod", -10 % 3 == 2, 2, -10 % 3)
test("mod neg divisor", 10 % -3 == -2, -2, 10 % -3)
test("neg neg mod", -10 % -3 == -1, -1, -10 % -3)

-- Large integers
local large1 = 9223372036854775807  -- LUA_MAXINTEGER
local large2 = -9223372036854775808 -- LUA_MININTEGER
test("large int", large1 + 1 == large2, nil, nil) -- Overflow wraps
test("min int neg", -large2 == large2, nil, nil) -- Special case

-- ============================================================================
-- 2. Float Arithmetic Tests
-- ============================================================================
print("\n--- Float Arithmetic ---")

test("float add", 1.5 + 2.5 == 4.0, 4.0, 1.5 + 2.5)
test("float sub", 5.5 - 3.0 == 2.5, 2.5, 5.5 - 3.0)
test("float mul", 2.5 * 4.0 == 10.0, 10.0, 2.5 * 4.0)
test("float div", 10.0 / 4.0 == 2.5, 2.5, 10.0 / 4.0)
test("float idiv", 10.0 // 3.0 == 3.0, 3.0, 10.0 // 3.0)
test("float mod", math.abs(10.5 % 3.0 - 1.5) < 0.0001, 1.5, 10.5 % 3.0)
test("float pow", 2.0 ^ 3.0 == 8.0, 8.0, 2.0 ^ 3.0)

-- Infinity and NaN
local inf = 1/0
local ninf = -1/0
local nan = 0/0

test("infinity", inf > 1e308, true, inf > 1e308)
test("neg infinity", ninf < -1e308, true, ninf < -1e308)
test("nan neq nan", nan ~= nan, true, nan ~= nan)
test("nan not lt", not (nan < 0), true, not (nan < 0))
test("nan not gt", not (nan > 0), true, not (nan > 0))

-- ============================================================================
-- 3. Mixed Integer/Float Arithmetic
-- ============================================================================
print("\n--- Mixed Int/Float Arithmetic ---")

test("int + float", 1 + 2.5 == 3.5, 3.5, 1 + 2.5)
test("float + int", 2.5 + 1 == 3.5, 3.5, 2.5 + 1)
test("int * float", 2 * 2.5 == 5.0, 5.0, 2 * 2.5)
test("int / int float", 7 / 2 == 3.5, 3.5, 7 / 2)  -- / always produces float

-- ============================================================================
-- 4. Bitwise Operations
-- ============================================================================
print("\n--- Bitwise Operations ---")

test("band", 0xFF & 0x0F == 0x0F, 0x0F, 0xFF & 0x0F)
test("bor", 0xF0 | 0x0F == 0xFF, 0xFF, 0xF0 | 0x0F)
test("bxor", 0xFF ~ 0x0F == 0xF0, 0xF0, 0xFF ~ 0x0F)
test("bnot", ~0 == -1, -1, ~0)
test("shl", 1 << 4 == 16, 16, 1 << 4)
test("shr", 16 >> 2 == 4, 4, 16 >> 2)

-- Negative shifts
test("neg shl", 16 << -2 == 4, 4, 16 << -2)  -- negative left = right shift
test("neg shr", 1 >> -4 == 16, 16, 1 >> -4)  -- negative right = left shift

-- Large shifts
test("shl overflow", 1 << 64 == 0, 0, 1 << 64)
test("shr overflow", 1 >> 64 == 0, 0, 1 >> 64)

-- ============================================================================
-- 5. Comparison Operations
-- ============================================================================
print("\n--- Comparison Operations ---")

-- Integer comparisons
test("int eq", 5 == 5, true, 5 == 5)
test("int neq", 5 ~= 6, true, 5 ~= 6)
test("int lt", 3 < 5, true, 3 < 5)
test("int le", 5 <= 5, true, 5 <= 5)
test("int gt", 5 > 3, true, 5 > 3)
test("int ge", 5 >= 5, true, 5 >= 5)

-- Float comparisons
test("float eq", 1.5 == 1.5, true, 1.5 == 1.5)
test("float lt", 1.5 < 2.5, true, 1.5 < 2.5)
test("float le", 2.5 <= 2.5, true, 2.5 <= 2.5)

-- Mixed int/float comparisons (critical for precision)
test("int eq float", 5 == 5.0, true, 5 == 5.0)
test("int lt float", 5 < 5.5, true, 5 < 5.5)
test("int gt float", 5 > 4.5, true, 5 > 4.5)
test("float eq int", 5.0 == 5, true, 5.0 == 5)

-- String comparisons
test("str eq", "abc" == "abc", true, "abc" == "abc")
test("str neq", "abc" ~= "abd", true, "abc" ~= "abd")
test("str lt", "abc" < "abd", true, "abc" < "abd")
test("str le", "abc" <= "abc", true, "abc" <= "abc")
test("str gt", "abd" > "abc", true, "abd" > "abc")

-- Boolean and nil
test("nil eq nil", nil == nil, true, nil == nil)
test("false eq false", false == false, true, false == false)
test("false neq true", false ~= true, true, false ~= true)

-- ============================================================================
-- 6. String Operations
-- ============================================================================
print("\n--- String Operations ---")

test("str concat", "hello" .. " " .. "world" == "hello world", "hello world", "hello" .. " " .. "world")
test("str len", #"hello" == 5, 5, #"hello")
test("empty str len", #"" == 0, 0, #"")

-- Number to string conversion in concat
test("num concat", "value: " .. 42 == "value: 42", "value: 42", "value: " .. 42)
test("float concat", "pi: " .. 3.14 == "pi: 3.14", "pi: 3.14", "pi: " .. 3.14)

-- Multiple concatenations
local s = ""
for i = 1, 5 do
    s = s .. tostring(i)
end
test("loop concat", s == "12345", "12345", s)

-- ============================================================================
-- 7. Table Operations
-- ============================================================================
print("\n--- Table Operations ---")

local t = {1, 2, 3, 4, 5}
test("table len", #t == 5, 5, #t)

local t2 = {}
t2[1] = "a"
t2[2] = "b"
t2[3] = "c"
test("table set/get", t2[2] == "b", "b", t2[2])
test("table len after set", #t2 == 3, 3, #t2)

-- Mixed keys
local t3 = {[1] = "one", ["two"] = 2, [3.0] = "three"}
test("int key", t3[1] == "one", "one", t3[1])
test("str key", t3["two"] == 2, 2, t3["two"])
test("float key (as int)", t3[3] == "three", "three", t3[3])

-- ============================================================================
-- 8. For Loop Tests
-- ============================================================================
print("\n--- For Loop Tests ---")

local sum = 0
for i = 1, 5 do
    sum = sum + i
end
test("for loop sum", sum == 15, 15, sum)

sum = 0
for i = 1, 10, 2 do
    sum = sum + i
end
test("for loop step 2", sum == 25, 25, sum)  -- 1+3+5+7+9 = 25

sum = 0
for i = 5, 1, -1 do
    sum = sum + i
end
test("for loop negative step", sum == 15, 15, sum)

-- Float for loop
sum = 0.0
for i = 0.0, 1.0, 0.25 do
    sum = sum + i
end
test("float for loop", math.abs(sum - 2.5) < 0.0001, 2.5, sum)

-- ============================================================================
-- 9. Logical Operations
-- ============================================================================
print("\n--- Logical Operations ---")

test("not true", not true == false, false, not true)
test("not false", not false == true, true, not false)
test("not nil", not nil == true, true, not nil)
test("not 0", not 0 == false, false, not 0)  -- 0 is truthy in Lua!
test("not empty str", not "" == false, false, not "")  -- "" is truthy

test("and short circuit", false and error("should not run") or true, true, nil)
test("or short circuit", true or error("should not run") and true, true, nil)

test("and value", 1 and 2 == 2, 2, 1 and 2)
test("or value", false or 3 == 3, 3, false or 3)

-- ============================================================================
-- 10. Type Checking
-- ============================================================================
print("\n--- Type Checking ---")

test("type nil", type(nil) == "nil", "nil", type(nil))
test("type bool", type(true) == "boolean", "boolean", type(true))
test("type number int", type(42) == "number", "number", type(42))
test("type number float", type(3.14) == "number", "number", type(3.14))
test("type string", type("hello") == "string", "string", type("hello"))
test("type table", type({}) == "table", "table", type({}))
test("type function", type(print) == "function", "function", type(print))

-- ============================================================================
-- Summary
-- ============================================================================
print("\n=== Test Summary ===")
print("Passed: " .. passed)
print("Failed: " .. failed)
print("Total: " .. (passed + failed))

if failed > 0 then
    os.exit(1)
else
    print("\nAll tests passed!")
    os.exit(0)
end
