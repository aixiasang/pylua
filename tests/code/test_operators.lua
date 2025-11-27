-- test_operators.lua
-- Operator and bitwise operation tests

print("=== Operator Tests ===")

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
-- 1. Arithmetic Operators
-- ============================================================================
print("\n--- Arithmetic ---")

test("addition", 3 + 5 == 8)
test("subtraction", 10 - 4 == 6)
test("multiplication", 6 * 7 == 42)
test("division", 10 / 4 == 2.5)
test("floor division", 10 // 3 == 3)
test("modulo", 10 % 3 == 1)
test("power", 2 ^ 10 == 1024)
test("unary minus", -(-5) == 5)

-- Float arithmetic
test("float add", 1.5 + 2.5 == 4.0)
test("float mul", 0.1 * 10 == 1.0)
test("float div", 5.0 / 2.0 == 2.5)

-- Mixed int/float
test("int + float", 1 + 0.5 == 1.5)
test("float floor div", 7.5 // 2 == 3.0)

-- Negative modulo
test("negative mod", -7 % 3 == 2)  -- Lua: result has same sign as divisor
test("mod negative divisor", 7 % -3 == -2)

-- ============================================================================
-- 2. Relational Operators
-- ============================================================================
print("\n--- Relational ---")

test("equal", 5 == 5)
test("not equal", 5 ~= 6)
test("less than", 3 < 5)
test("greater than", 5 > 3)
test("less equal", 5 <= 5)
test("greater equal", 5 >= 5)

-- String comparison
test("string equal", "hello" == "hello")
test("string less", "abc" < "abd")
test("string greater", "xyz" > "abc")

-- Type comparison
test("different types", 5 ~= "5")
test("nil equal", nil == nil)
test("bool equal", true == true)

-- ============================================================================
-- 3. Logical Operators
-- ============================================================================
print("\n--- Logical ---")

test("and true", true and true == true)
test("and false", true and false == false)
test("or true", false or true == true)
test("or false", false or false == false)
test("not true", not true == false)
test("not false", not false == true)

-- Short circuit
local called = false
local function side_effect() called = true; return true end

called = false
local _ = false and side_effect()
test("and short circuit", called == false)

called = false
_ = true or side_effect()
test("or short circuit", called == false)

-- Truthiness
test("not nil", not nil == true)
test("not 0", not 0 == false)  -- 0 is truthy in Lua!
test("not empty string", not "" == false)  -- "" is truthy

-- and/or return values
test("and value true", (5 and 6) == 6)
test("and value false", (nil and 6) == nil)
test("or value true", (5 or 6) == 5)
test("or value false", (nil or 6) == 6)

-- ============================================================================
-- 4. Bitwise Operators
-- ============================================================================
print("\n--- Bitwise ---")

test("band", 12 & 10 == 8)        -- 1100 & 1010 = 1000
test("bor", 12 | 10 == 14)        -- 1100 | 1010 = 1110
test("bxor", 12 ~ 10 == 6)        -- 1100 ^ 1010 = 0110
test("bnot", ~0 == -1)            -- all bits flipped
test("shl", 1 << 4 == 16)         -- shift left
test("shr", 16 >> 2 == 4)         -- shift right

-- More complex bitwise
test("band mask", 0xFF & 0x0F == 0x0F)
test("bor combine", 0xF0 | 0x0F == 0xFF)
test("xor toggle", 0xFF ~ 0x0F == 0xF0)

-- Negative shifts (Lua 5.3+)
test("shift negative", 16 >> 2 == 4)
test("left shift", 3 << 3 == 24)

-- ============================================================================
-- 5. Concatenation
-- ============================================================================
print("\n--- Concatenation ---")

test("string concat", "hello" .. " " .. "world" == "hello world")
test("number concat", "value: " .. 42 == "value: 42")
test("multi concat", "a" .. "b" .. "c" == "abc")

-- Automatic conversion
test("int to string", 1 .. 2 .. 3 == "123")

-- ============================================================================
-- 6. Length Operator
-- ============================================================================
print("\n--- Length ---")

test("string length", #"hello" == 5)
test("table length", #{1, 2, 3, 4} == 4)
test("empty string", #"" == 0)
test("empty table", #{} == 0)

-- ============================================================================
-- 7. Operator Precedence
-- ============================================================================
print("\n--- Precedence ---")

test("arith precedence", 2 + 3 * 4 == 14)
test("power right assoc", 2 ^ 2 ^ 3 == 256)  -- 2^(2^3) = 2^8
test("unary minus", -2 ^ 2 == -4)  -- -(2^2)
test("compare chain", (1 < 2) == true)
test("mixed", 1 + 2 * 3 - 4 / 2 == 5)

-- Parentheses
test("paren override", (2 + 3) * 4 == 20)

-- ============================================================================
-- 8. Comparison Chains (Lua style)
-- ============================================================================
print("\n--- Comparisons ---")

-- Note: Lua doesn't support chained comparisons like Python
local a, b, c = 1, 2, 3
test("not chained", (a < b) and (b < c))
test("range check", a >= 1 and a <= 10)

-- ============================================================================
-- 9. Special Values
-- ============================================================================
print("\n--- Special Values ---")

test("divide by zero", 1 / 0 == math.huge)
test("negative inf", -1 / 0 == -math.huge)

local nan = 0 / 0
test("nan not equal self", nan ~= nan)

test("huge comparison", math.huge > 1e308)
test("mininteger", math.mininteger < 0)

-- ============================================================================
-- 10. Operator Metamethods
-- ============================================================================
print("\n--- Operator Metamethods ---")

local Vector = {}
Vector.__index = Vector

function Vector.new(x, y)
    return setmetatable({x = x, y = y}, Vector)
end

function Vector.__add(a, b)
    return Vector.new(a.x + b.x, a.y + b.y)
end

function Vector.__sub(a, b)
    return Vector.new(a.x - b.x, a.y - b.y)
end

function Vector.__mul(a, b)
    if type(b) == "number" then
        return Vector.new(a.x * b, a.y * b)
    else
        return Vector.new(a.x * b.x, a.y * b.y)
    end
end

function Vector.__unm(v)
    return Vector.new(-v.x, -v.y)
end

function Vector.__eq(a, b)
    return a.x == b.x and a.y == b.y
end

function Vector.__lt(a, b)
    return (a.x * a.x + a.y * a.y) < (b.x * b.x + b.y * b.y)
end

function Vector.__len(v)
    return math.sqrt(v.x * v.x + v.y * v.y)
end

local v1 = Vector.new(1, 2)
local v2 = Vector.new(3, 4)

local v3 = v1 + v2
test("__add", v3.x == 4 and v3.y == 6)

local v4 = v2 - v1
test("__sub", v4.x == 2 and v4.y == 2)

local v5 = v1 * 2
test("__mul scalar", v5.x == 2 and v5.y == 4)

local v6 = -v1
test("__unm", v6.x == -1 and v6.y == -2)

test("__eq true", v1 == Vector.new(1, 2))
test("__eq false", v1 == v2 == false)

test("__lt", v1 < v2)

-- ============================================================================
-- 11. Bitwise Metamethods
-- ============================================================================
print("\n--- Bitwise Metamethods ---")

local BitInt = {}
BitInt.__index = BitInt

function BitInt.new(n)
    return setmetatable({value = n}, BitInt)
end

function BitInt.__band(a, b)
    local av = type(a) == "table" and a.value or a
    local bv = type(b) == "table" and b.value or b
    return BitInt.new(av & bv)
end

function BitInt.__bor(a, b)
    local av = type(a) == "table" and a.value or a
    local bv = type(b) == "table" and b.value or b
    return BitInt.new(av | bv)
end

function BitInt.__bnot(a)
    return BitInt.new(~a.value)
end

local bi1 = BitInt.new(0xF0)
local bi2 = BitInt.new(0x0F)

local bi3 = bi1 & bi2
test("__band", bi3.value == 0)

local bi4 = bi1 | bi2
test("__bor", bi4.value == 0xFF)

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
