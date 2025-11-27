-- ============================================================================
-- Test 12: Table Advanced Operations
-- 测试表的高级操作特性
-- ============================================================================

print("=== Test 12: Table Advanced Operations ===")

local total_tests = 0
local passed_tests = 0

-- Helper function
local function test(name, condition)
    total_tests = total_tests + 1
    if condition then
        passed_tests = passed_tests + 1
        print("  PASS: " .. name)
    else
        print("  FAIL: " .. name)
    end
end

-- ============================================================================
-- [1] Table as Array Tests
-- ============================================================================
print("\n[1] Table as Array Tests")

-- Test 1.1: Basic array operations
local arr = {10, 20, 30}
test("array length", #arr == 3)
test("array index 1", arr[1] == 10)
test("array index 3", arr[3] == 30)

-- Test 1.2: Array modification
arr[2] = 25
test("array modify", arr[2] == 25)
arr[4] = 40
test("array extend", #arr == 4)

-- Test 1.3: Array with holes
local sparse = {1, 2, nil, 4}
test("sparse array access", sparse[4] == 4)

-- ============================================================================
-- [2] Table as Dictionary Tests
-- ============================================================================
print("\n[2] Table as Dictionary Tests")

-- Test 2.1: String keys
local dict = {name = "Alice", age = 30}
test("dict string key", dict.name == "Alice")
test("dict bracket access", dict["age"] == 30)

-- Test 2.2: Mixed keys
local mixed = {[1] = "first", key = "value", [10] = "tenth"}
test("mixed numeric", mixed[1] == "first")
test("mixed string", mixed.key == "value")
test("mixed sparse", mixed[10] == "tenth")

-- Test 2.3: Dynamic keys
local key = "dynamic"
local t = {}
t[key] = "value"
test("dynamic key", t.dynamic == "value")

-- ============================================================================
-- [3] Table Insert and Remove Tests
-- ============================================================================
print("\n[3] Table Insert and Remove Tests")

-- Test 3.1: Insert at end
local t1 = {1, 2, 3}
table.insert(t1, 4)
test("insert end length", #t1 == 4)
test("insert end value", t1[4] == 4)

-- Test 3.2: Insert at position
local t2 = {1, 2, 4}
table.insert(t2, 3, 3)
test("insert pos length", #t2 == 4)
test("insert pos value", t2[3] == 3)
test("insert pos shifted", t2[4] == 4)

-- Test 3.3: Remove from end
local t3 = {1, 2, 3, 4}
local removed = table.remove(t3)
test("remove end value", removed == 4)
test("remove end length", #t3 == 3)

-- Test 3.4: Remove from position
local t4 = {1, 2, 3, 4}
local removed2 = table.remove(t4, 2)
test("remove pos value", removed2 == 2)
test("remove pos length", #t4 == 3)
test("remove pos shifted", t4[2] == 3)

-- ============================================================================
-- [4] Table Concat Tests
-- ============================================================================
print("\n[4] Table Concat Tests")

-- Test 4.1: Basic concat
local t1 = {"a", "b", "c"}
test("concat basic", table.concat(t1) == "abc")

-- Test 4.2: Concat with separator
local t2 = {"a", "b", "c"}
test("concat sep", table.concat(t2, ",") == "a,b,c")

-- Test 4.3: Concat with range
local t3 = {"a", "b", "c", "d", "e"}
test("concat range", table.concat(t3, "-", 2, 4) == "b-c-d")

-- Test 4.4: Concat numbers
local t4 = {1, 2, 3}
test("concat numbers", table.concat(t4, ",") == "1,2,3")

-- ============================================================================
-- [5] Table Length Tests
-- ============================================================================
print("\n[5] Table Length Tests")

-- Test 5.1: Continuous array
local t1 = {1, 2, 3, 4, 5}
test("length continuous", #t1 == 5)

-- Test 5.2: Array with nil at end
local t2 = {1, 2, 3}
t2[5] = 5
test("length with gap", #t2 == 3 or #t2 == 5)  -- undefined behavior

-- Test 5.3: Empty table
local t3 = {}
test("length empty", #t3 == 0)

-- Test 5.4: Table with only string keys
local t4 = {a = 1, b = 2}
test("length dict", #t4 == 0)

-- ============================================================================
-- [6] Table Iteration Tests
-- ============================================================================
print("\n[6] Table Iteration Tests")

-- Test 6.1: ipairs iteration
local arr = {10, 20, 30}
local sum = 0
for i, v in ipairs(arr) do
    sum = sum + v
end
test("ipairs sum", sum == 60)

-- Test 6.2: pairs iteration
local dict = {a = 1, b = 2, c = 3}
local count = 0
for k, v in pairs(dict) do
    count = count + 1
end
test("pairs count", count == 3)

-- Test 6.3: Numeric for loop
local arr2 = {5, 10, 15}
local total = 0
for i = 1, #arr2 do
    total = total + arr2[i]
end
test("numeric for", total == 30)

-- ============================================================================
-- [7] Table as Set Tests
-- ============================================================================
print("\n[7] Table as Set Tests")

-- Test 7.1: Set membership
local set = {apple = true, banana = true, orange = true}
test("set member", set.apple == true)
test("set non-member", set.grape == nil)

-- Test 7.2: Set operations
local function set_union(a, b)
    local result = {}
    for k in pairs(a) do result[k] = true end
    for k in pairs(b) do result[k] = true end
    return result
end

local s1 = {a = true, b = true}
local s2 = {b = true, c = true}
local s3 = set_union(s1, s2)
test("set union a", s3.a == true)
test("set union b", s3.b == true)
test("set union c", s3.c == true)

-- ============================================================================
-- [8] Nested Tables Tests
-- ============================================================================
print("\n[8] Nested Tables Tests")

-- Test 8.1: 2D array
local matrix = {
    {1, 2, 3},
    {4, 5, 6},
    {7, 8, 9}
}
test("matrix access", matrix[2][2] == 5)
test("matrix corner", matrix[3][3] == 9)

-- Test 8.2: Deep nesting
local deep = {
    level1 = {
        level2 = {
            level3 = {
                value = 42
            }
        }
    }
}
test("deep nesting", deep.level1.level2.level3.value == 42)

-- Test 8.3: Array of tables
local records = {
    {name = "Alice", age = 30},
    {name = "Bob", age = 25},
    {name = "Charlie", age = 35}
}
test("array of tables", records[2].name == "Bob")

-- ============================================================================
-- [9] Table Reference Tests
-- ============================================================================
print("\n[9] Table Reference Tests")

-- Test 9.1: Table assignment is by reference
local t1 = {1, 2, 3}
local t2 = t1
t2[1] = 10
test("reference modify", t1[1] == 10)

-- Test 9.2: Table comparison
local t3 = {1, 2, 3}
local t4 = {1, 2, 3}
test("table not equal", t3 ~= t4)  -- different references
test("table self equal", t3 == t3)

-- ============================================================================
-- [10] Table Copying Tests
-- ============================================================================
print("\n[10] Table Copying Tests")

-- Test 10.1: Shallow copy
local function shallow_copy(t)
    local copy = {}
    for k, v in pairs(t) do
        copy[k] = v
    end
    return copy
end

local orig = {a = 1, b = 2, c = 3}
local copy = shallow_copy(orig)
copy.a = 10
test("shallow copy independent", orig.a == 1)
test("shallow copy value", copy.a == 10)

-- Test 10.2: Array copy
local arr1 = {1, 2, 3}
local arr2 = {}
for i, v in ipairs(arr1) do
    arr2[i] = v
end
arr2[1] = 10
test("array copy independent", arr1[1] == 1)

-- ============================================================================
-- [11] Table as Stack Tests
-- ============================================================================
print("\n[11] Table as Stack Tests")

-- Test 11.1: Stack operations
local stack = {}
table.insert(stack, "a")
table.insert(stack, "b")
table.insert(stack, "c")
test("stack size", #stack == 3)

local top = table.remove(stack)
test("stack pop", top == "c")
test("stack size after pop", #stack == 2)

-- ============================================================================
-- [12] Table as Queue Tests
-- ============================================================================
print("\n[12] Table as Queue Tests")

-- Test 12.1: Queue operations
local queue = {}
table.insert(queue, "first")
table.insert(queue, "second")
table.insert(queue, "third")

local front = table.remove(queue, 1)
test("queue dequeue", front == "first")
test("queue size", #queue == 2)
test("queue next", queue[1] == "second")

-- ============================================================================
-- [13] Table Sorting Tests
-- ============================================================================
print("\n[13] Table Sorting Tests")

-- Test 13.1: Sort numbers (would need table.sort implementation)
-- Skipping as table.sort not implemented yet

-- Test 13.2: Manual sorting check
local function is_sorted(t)
    for i = 1, #t - 1 do
        if t[i] > t[i + 1] then
            return false
        end
    end
    return true
end

test("sorted check true", is_sorted({1, 2, 3, 4}))
test("sorted check false", not is_sorted({1, 3, 2, 4}))

-- ============================================================================
-- [14] Table with Nil Values Tests
-- ============================================================================
print("\n[14] Table with Nil Values Tests")

-- Test 14.1: Nil removes key
local t = {a = 1, b = 2, c = 3}
t.b = nil
test("nil removes key", t.b == nil)

local count = 0
for k, v in pairs(t) do
    count = count + 1
end
test("nil reduces count", count == 2)

-- Test 14.2: Nil in array
local arr = {1, 2, 3, 4}
arr[2] = nil
test("nil in array", arr[2] == nil)
test("nil array length", #arr == 4 or #arr == 1)  -- undefined

-- ============================================================================
-- [15] Complex Table Patterns Tests
-- ============================================================================
print("\n[15] Complex Table Patterns Tests")

-- Test 15.1: Memoization table
local fib_cache = {}
local function fib(n)
    if n <= 1 then return n end
    if fib_cache[n] then return fib_cache[n] end
    
    local result = fib(n - 1) + fib(n - 2)
    fib_cache[n] = result
    return result
end

test("memoization result", fib(10) == 55)
test("memoization cached", fib_cache[10] == 55)

-- Test 15.2: Lookup table
local operations = {
    add = function(a, b) return a + b end,
    sub = function(a, b) return a - b end,
    mul = function(a, b) return a * b end,
    div = function(a, b) return a / b end
}

test("lookup add", operations.add(10, 5) == 15)
test("lookup mul", operations.mul(10, 5) == 50)

-- Test 15.3: Configuration table
local config = {
    debug = true,
    max_retries = 3,
    timeout = 30,
    servers = {"server1", "server2", "server3"}
}

test("config flag", config.debug == true)
test("config number", config.max_retries == 3)
test("config array", #config.servers == 3)

-- Test 15.4: Graph representation
local graph = {
    A = {B = 1, C = 4},
    B = {A = 1, C = 2, D = 5},
    C = {A = 4, B = 2, D = 1},
    D = {B = 5, C = 1}
}

test("graph edge AB", graph.A.B == 1)
test("graph edge CD", graph.C.D == 1)
test("graph bidirectional", graph.B.A == graph.A.B)

-- ============================================================================
-- Summary
-- ============================================================================
print("\n" .. string.rep("=", 60))
print("TEST SUMMARY")
print(string.rep("=", 60))
print("Total tests: " .. total_tests)
print("Passed: " .. passed_tests)
print("Failed: " .. (total_tests - passed_tests))
print("Success rate: " .. string.format("%.1f", (passed_tests / total_tests * 100)) .. "%")
print(string.rep("=", 60))

if passed_tests == total_tests then
    print("\n*** ALL TABLE ADVANCED TESTS PASSED ***")
else
    print("\n*** SOME TESTS FAILED ***")
end
