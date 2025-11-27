-- test_closures_advanced.lua
-- Advanced closure and scope tests

print("=== Advanced Closure Tests ===")

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
-- 1. Basic Closure
-- ============================================================================
print("\n--- Basic Closure ---")

local function make_counter()
    local count = 0
    return function()
        count = count + 1
        return count
    end
end

local counter = make_counter()
test("closure first call", counter() == 1)
test("closure second call", counter() == 2)
test("closure third call", counter() == 3)

-- Independent counters
local counter1 = make_counter()
local counter2 = make_counter()
counter1()
counter1()
counter2()
test("independent closures", counter1() == 3 and counter2() == 2)

-- ============================================================================
-- 2. Multiple Upvalues
-- ============================================================================
print("\n--- Multiple Upvalues ---")

local function make_adder_multiplier(add, mul)
    return function(x)
        return (x + add) * mul
    end
end

local f = make_adder_multiplier(5, 2)
test("multiple upvalues", f(10) == 30)  -- (10 + 5) * 2 = 30

-- ============================================================================
-- 3. Nested Closures
-- ============================================================================
print("\n--- Nested Closures ---")

local function outer(x)
    local function middle(y)
        local function inner(z)
            return x + y + z
        end
        return inner
    end
    return middle
end

local result = outer(1)(2)(3)
test("nested closures", result == 6)

-- ============================================================================
-- 4. Closure Over Loop Variable
-- ============================================================================
print("\n--- Closure Over Loop Variable ---")

local funcs = {}
for i = 1, 5 do
    funcs[i] = function() return i end
end

-- Each closure captures its own 'i'
test("closure loop var 1", funcs[1]() == 1)
test("closure loop var 3", funcs[3]() == 3)
test("closure loop var 5", funcs[5]() == 5)

-- ============================================================================
-- 5. Mutable Upvalue
-- ============================================================================
print("\n--- Mutable Upvalue ---")

local function make_accumulator(initial)
    local total = initial
    return {
        add = function(x) total = total + x end,
        get = function() return total end,
        reset = function() total = initial end
    }
end

local acc = make_accumulator(0)
acc.add(10)
acc.add(20)
test("accumulator add", acc.get() == 30)
acc.reset()
test("accumulator reset", acc.get() == 0)

-- ============================================================================
-- 6. Closure Returning Closure
-- ============================================================================
print("\n--- Closure Returning Closure ---")

local function curry_add(a)
    return function(b)
        return function(c)
            return a + b + c
        end
    end
end

test("curried function", curry_add(1)(2)(3) == 6)

-- ============================================================================
-- 7. Recursive Closure
-- ============================================================================
print("\n--- Recursive Closure ---")

local function make_factorial()
    local fact
    fact = function(n)
        if n <= 1 then return 1 end
        return n * fact(n - 1)
    end
    return fact
end

local factorial = make_factorial()
test("recursive closure 5!", factorial(5) == 120)
test("recursive closure 10!", factorial(10) == 3628800)

-- ============================================================================
-- 8. Shared Upvalue
-- ============================================================================
print("\n--- Shared Upvalue ---")

local function make_pair()
    local value = 0
    local function get() return value end
    local function set(v) value = v end
    return get, set
end

local get, set = make_pair()
test("shared upvalue initial", get() == 0)
set(42)
test("shared upvalue modified", get() == 42)

-- ============================================================================
-- 9. Upvalue Lifetime
-- ============================================================================
print("\n--- Upvalue Lifetime ---")

local stored_func
do
    local x = 100
    stored_func = function() return x end
end
-- x is out of scope but captured
test("upvalue lifetime", stored_func() == 100)

-- ============================================================================
-- 10. Higher Order Functions
-- ============================================================================
print("\n--- Higher Order Functions ---")

local function map(t, f)
    local result = {}
    for i, v in ipairs(t) do
        result[i] = f(v)
    end
    return result
end

local function filter(t, pred)
    local result = {}
    for i, v in ipairs(t) do
        if pred(v) then
            result[#result + 1] = v
        end
    end
    return result
end

local function reduce(t, f, init)
    local acc = init
    for i, v in ipairs(t) do
        acc = f(acc, v)
    end
    return acc
end

local nums = {1, 2, 3, 4, 5}

local doubled = map(nums, function(x) return x * 2 end)
test("map", doubled[1] == 2 and doubled[3] == 6)

local evens = filter(nums, function(x) return x % 2 == 0 end)
test("filter", #evens == 2 and evens[1] == 2 and evens[2] == 4)

local sum = reduce(nums, function(a, b) return a + b end, 0)
test("reduce", sum == 15)

-- ============================================================================
-- 11. Method with Closure
-- ============================================================================
print("\n--- Method with Closure ---")

local function make_object(name)
    local obj = {}
    local private_value = 0
    
    function obj:get_name() return name end
    function obj:get_value() return private_value end
    function obj:set_value(v) private_value = v end
    
    return obj
end

local obj = make_object("test")
test("method closure name", obj:get_name() == "test")
obj:set_value(99)
test("method closure value", obj:get_value() == 99)

-- ============================================================================
-- 12. Coroutine-like with Closures
-- ============================================================================
print("\n--- Generator Pattern ---")

local function range(from, to)
    local current = from - 1
    return function()
        current = current + 1
        if current <= to then
            return current
        end
        return nil
    end
end

local gen = range(1, 3)
test("generator 1", gen() == 1)
test("generator 2", gen() == 2)
test("generator 3", gen() == 3)
test("generator end", gen() == nil)

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
