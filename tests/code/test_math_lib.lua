-- test_math_lib.lua
-- Math library function tests

print("=== Math Library Tests ===")

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

local function approx(a, b, eps)
    eps = eps or 0.0001
    return math.abs(a - b) < eps
end

-- ============================================================================
-- 1. Basic Math Functions
-- ============================================================================
print("\n--- Basic Math ---")

test("math.abs positive", math.abs(5) == 5)
test("math.abs negative", math.abs(-5) == 5)
test("math.abs zero", math.abs(0) == 0)
test("math.abs float", math.abs(-3.14) == 3.14)

test("math.floor", math.floor(3.7) == 3)
test("math.floor negative", math.floor(-3.2) == -4)
test("math.floor integer", math.floor(5) == 5)

test("math.ceil", math.ceil(3.2) == 4)
test("math.ceil negative", math.ceil(-3.7) == -3)
test("math.ceil integer", math.ceil(5) == 5)

-- ============================================================================
-- 2. Power and Roots
-- ============================================================================
print("\n--- Power and Roots ---")

test("math.sqrt 4", math.sqrt(4) == 2)
test("math.sqrt 9", math.sqrt(9) == 3)
test("math.sqrt 2", approx(math.sqrt(2), 1.4142135))

-- ============================================================================
-- 3. Trigonometric Functions
-- ============================================================================
print("\n--- Trigonometric ---")

test("math.sin 0", math.sin(0) == 0)
test("math.sin pi/2", approx(math.sin(math.pi / 2), 1))
test("math.sin pi", approx(math.sin(math.pi), 0))

test("math.cos 0", math.cos(0) == 1)
test("math.cos pi/2", approx(math.cos(math.pi / 2), 0))
test("math.cos pi", approx(math.cos(math.pi), -1))

test("math.tan 0", math.tan(0) == 0)
test("math.tan pi/4", approx(math.tan(math.pi / 4), 1))

-- ============================================================================
-- 4. Inverse Trigonometric
-- ============================================================================
print("\n--- Inverse Trigonometric ---")

test("math.asin 0", math.asin(0) == 0)
test("math.asin 1", approx(math.asin(1), math.pi / 2))

test("math.acos 1", math.acos(1) == 0)
test("math.acos 0", approx(math.acos(0), math.pi / 2))

test("math.atan 0", math.atan(0) == 0)
test("math.atan 1", approx(math.atan(1), math.pi / 4))

-- atan2 style
test("math.atan 2 args", approx(math.atan(1, 1), math.pi / 4))

-- ============================================================================
-- 5. Exponential and Logarithmic
-- ============================================================================
print("\n--- Exponential and Logarithmic ---")

test("math.exp 0", math.exp(0) == 1)
test("math.exp 1", approx(math.exp(1), 2.718281828))

test("math.log e", approx(math.log(math.exp(1)), 1))
test("math.log 1", math.log(1) == 0)

test("math.log base 10", approx(math.log(100, 10), 2))
test("math.log base 2", approx(math.log(8, 2), 3))

-- ============================================================================
-- 6. Min and Max
-- ============================================================================
print("\n--- Min and Max ---")

test("math.min 2 args", math.min(3, 5) == 3)
test("math.min 3 args", math.min(7, 2, 9) == 2)
test("math.min negative", math.min(-5, -3) == -5)

test("math.max 2 args", math.max(3, 5) == 5)
test("math.max 3 args", math.max(7, 2, 9) == 9)
test("math.max negative", math.max(-5, -3) == -3)

-- ============================================================================
-- 7. Degree and Radian Conversion
-- ============================================================================
print("\n--- Degree/Radian ---")

test("math.deg pi", approx(math.deg(math.pi), 180))
test("math.deg pi/2", approx(math.deg(math.pi / 2), 90))

test("math.rad 180", approx(math.rad(180), math.pi))
test("math.rad 90", approx(math.rad(90), math.pi / 2))

-- ============================================================================
-- 8. Modulo and Integer Division
-- ============================================================================
print("\n--- Modulo ---")

test("math.fmod 5,3", math.fmod(5, 3) == 2)
test("math.fmod 10,3", math.fmod(10, 3) == 1)
test("math.fmod float", approx(math.fmod(5.5, 2), 1.5))

-- ============================================================================
-- 9. modf (integral and fractional parts)
-- ============================================================================
print("\n--- modf ---")

local int_part, frac_part = math.modf(3.5)
test("math.modf 3.5 int", int_part == 3)
test("math.modf 3.5 frac", frac_part == 0.5)

int_part, frac_part = math.modf(-3.5)
test("math.modf -3.5 int", int_part == -3)
test("math.modf -3.5 frac", frac_part == -0.5)

-- ============================================================================
-- 10. Math Constants
-- ============================================================================
print("\n--- Constants ---")

test("math.pi", approx(math.pi, 3.14159265))
test("math.huge", math.huge > 1e308)
test("math.maxinteger", math.maxinteger == 9223372036854775807)
test("math.mininteger", math.mininteger == -9223372036854775808)

-- ============================================================================
-- 11. Type Functions
-- ============================================================================
print("\n--- Type Functions ---")

test("math.type integer", math.type(42) == "integer")
test("math.type float", math.type(3.14) == "float")
test("math.type non-number", math.type("42") == nil)

test("math.tointeger 42", math.tointeger(42) == 42)
test("math.tointeger 3.0", math.tointeger(3.0) == 3)
test("math.tointeger 3.5", math.tointeger(3.5) == nil)
-- Note: Lua 5.3 can convert string "42" to integer 42, so this should return 42
test("math.tointeger string int", math.tointeger("42") == 42)
test("math.tointeger string float", math.tointeger("3.5") == nil)

-- ============================================================================
-- 12. Random (basic checks)
-- ============================================================================
print("\n--- Random ---")

math.randomseed(12345)
local r1 = math.random()
test("math.random 0-1", r1 >= 0 and r1 < 1)

local r2 = math.random(10)
test("math.random 1-n", r2 >= 1 and r2 <= 10)

local r3 = math.random(5, 10)
test("math.random m-n", r3 >= 5 and r3 <= 10)

-- ============================================================================
-- 13. Unsigned Comparison
-- ============================================================================
print("\n--- Unsigned ---")

test("math.ult positive", math.ult(1, 2) == true)
test("math.ult equal", math.ult(5, 5) == false)
test("math.ult negative as unsigned", math.ult(-1, 1) == false)  -- -1 is max unsigned

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
