-- test_iterators.lua
-- Comprehensive iterator and loop tests

print("=== Iterator Tests ===")

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
-- 1. ipairs Tests
-- ============================================================================
print("\n--- ipairs Tests ---")

local arr = {10, 20, 30, 40, 50}
local sum = 0
local count = 0
for i, v in ipairs(arr) do
    sum = sum + v
    count = count + 1
end
test("ipairs sum", sum == 150)
test("ipairs count", count == 5)

-- ipairs stops at nil
local sparse = {1, 2, nil, 4, 5}
count = 0
for i, v in ipairs(sparse) do
    count = count + 1
end
test("ipairs stops at nil", count == 2)

-- Empty table
count = 0
for i, v in ipairs({}) do
    count = count + 1
end
test("ipairs empty table", count == 0)

-- ============================================================================
-- 2. pairs Tests
-- ============================================================================
print("\n--- pairs Tests ---")

local mixed = {a = 1, b = 2, c = 3}
local keys = {}
for k, v in pairs(mixed) do
    keys[#keys + 1] = k
end
test("pairs count", #keys == 3)

-- pairs with array part
local arr2 = {10, 20, 30}
arr2.x = 100
count = 0
for k, v in pairs(arr2) do
    count = count + 1
end
test("pairs mixed table", count == 4)

-- ============================================================================
-- 3. next Function
-- ============================================================================
print("\n--- next Function ---")

local t = {a = 1, b = 2}
local k, v = next(t)
test("next returns key-value", k ~= nil and v ~= nil)

k, v = next(t, nil)
test("next with nil index", k ~= nil)

-- next on empty table
k, v = next({})
test("next empty table", k == nil and v == nil)

-- ============================================================================
-- 4. Numeric For Loop Edge Cases
-- ============================================================================
print("\n--- Numeric For Edge Cases ---")

-- Zero iterations
count = 0
for i = 1, 0 do
    count = count + 1
end
test("for 1 to 0", count == 0)

-- Single iteration
count = 0
for i = 5, 5 do
    count = count + 1
end
test("for 5 to 5", count == 1)

-- Negative step
sum = 0
for i = 5, 1, -1 do
    sum = sum + i
end
test("for negative step", sum == 15)

-- Float loop
sum = 0
for i = 1.0, 3.0, 0.5 do
    sum = sum + i
end
test("for float step", sum == 9.0)  -- 1.0 + 1.5 + 2.0 + 2.5 + 3.0 = 10.0

-- ============================================================================
-- 5. While Loop Edge Cases
-- ============================================================================
print("\n--- While Loop Edge Cases ---")

-- Immediate false
count = 0
while false do
    count = count + 1
end
test("while false", count == 0)

-- Counter loop
count = 0
local n = 10
while n > 0 do
    count = count + 1
    n = n - 1
end
test("while counter", count == 10)

-- ============================================================================
-- 6. Repeat-Until Loop
-- ============================================================================
print("\n--- Repeat-Until Loop ---")

-- At least once
count = 0
repeat
    count = count + 1
until true
test("repeat at least once", count == 1)

-- Counter
count = 0
n = 5
repeat
    count = count + 1
    n = n - 1
until n == 0
test("repeat counter", count == 5)

-- ============================================================================
-- 7. Break in Loops
-- ============================================================================
print("\n--- Break Tests ---")

-- Break in for
sum = 0
for i = 1, 100 do
    if i > 5 then break end
    sum = sum + i
end
test("break in for", sum == 15)

-- Break in while
count = 0
while true do
    count = count + 1
    if count >= 3 then break end
end
test("break in while", count == 3)

-- Break in repeat
count = 0
repeat
    count = count + 1
    if count >= 4 then break end
until false
test("break in repeat", count == 4)

-- ============================================================================
-- 8. Nested Loops
-- ============================================================================
print("\n--- Nested Loops ---")

-- Matrix iteration
sum = 0
for i = 1, 3 do
    for j = 1, 3 do
        sum = sum + i * j
    end
end
test("nested for loops", sum == 36)  -- (1+2+3)*(1+2+3) = 36

-- Break from inner only
count = 0
for i = 1, 3 do
    for j = 1, 10 do
        if j > 2 then break end
        count = count + 1
    end
end
test("break inner loop", count == 6)  -- 3 * 2

-- ============================================================================
-- 9. Generic For with Custom Iterator
-- ============================================================================
print("\n--- Custom Iterator ---")

local function range(start, stop)
    local i = start - 1
    return function()
        i = i + 1
        if i <= stop then
            return i
        end
    end
end

sum = 0
for i in range(1, 5) do
    sum = sum + i
end
test("custom range iterator", sum == 15)

-- ============================================================================
-- 10. select Function
-- ============================================================================
print("\n--- select Tests ---")

test("select #", select("#", 1, 2, 3, 4, 5) == 5)
test("select 1", select(1, "a", "b", "c") == "a")
test("select 2", select(2, "a", "b", "c") == "b")
test("select -1", select(-1, "a", "b", "c") == "c")

-- Multiple returns from select
local a, b, c = select(2, 10, 20, 30, 40)
test("select multiple", a == 20 and b == 30 and c == 40)

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
