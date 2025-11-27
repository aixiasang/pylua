-- test_table_lib.lua
-- Table library function tests

print("=== Table Library Tests ===")

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
-- 1. table.insert
-- ============================================================================
print("\n--- table.insert ---")

local t = {1, 2, 3}
table.insert(t, 4)
test("insert at end", t[4] == 4 and #t == 4)

t = {1, 2, 3}
table.insert(t, 2, 10)
test("insert at position", t[2] == 10 and t[3] == 2)
test("insert shifts", #t == 4)

t = {}
table.insert(t, "first")
test("insert empty", t[1] == "first")

-- ============================================================================
-- 2. table.remove
-- ============================================================================
print("\n--- table.remove ---")

t = {10, 20, 30, 40}
local removed = table.remove(t)
test("remove last", removed == 40 and #t == 3)

t = {10, 20, 30, 40}
removed = table.remove(t, 2)
test("remove at position", removed == 20)
test("remove shifts", t[2] == 30 and #t == 3)

t = {1}
removed = table.remove(t)
test("remove to empty", removed == 1 and #t == 0)

-- ============================================================================
-- 3. table.concat
-- ============================================================================
print("\n--- table.concat ---")

t = {"a", "b", "c"}
test("concat basic", table.concat(t) == "abc")
test("concat sep", table.concat(t, "-") == "a-b-c")
test("concat range", table.concat(t, ",", 1, 2) == "a,b")

t = {}
test("concat empty", table.concat(t) == "")

t = {"only"}
test("concat single", table.concat(t, ",") == "only")

-- With numbers
t = {1, 2, 3}
test("concat numbers", table.concat(t, "+") == "1+2+3")

-- ============================================================================
-- 4. table.sort
-- ============================================================================
print("\n--- table.sort ---")

t = {3, 1, 4, 1, 5, 9, 2, 6}
table.sort(t)
test("sort ascending", t[1] == 1 and t[2] == 1 and t[#t] == 9)

t = {3, 1, 4, 1, 5}
table.sort(t, function(a, b) return a > b end)
test("sort descending", t[1] == 5 and t[#t] == 1)

-- Sort strings
t = {"banana", "apple", "cherry"}
table.sort(t)
test("sort strings", t[1] == "apple" and t[3] == "cherry")

-- Empty and single element
t = {}
table.sort(t)
test("sort empty", #t == 0)

t = {42}
table.sort(t)
test("sort single", t[1] == 42)

-- ============================================================================
-- 5. table.pack
-- ============================================================================
print("\n--- table.pack ---")

t = table.pack(1, 2, 3)
test("pack creates table", type(t) == "table")
test("pack values", t[1] == 1 and t[2] == 2 and t[3] == 3)
test("pack n field", t.n == 3)

t = table.pack()
test("pack empty", t.n == 0)

t = table.pack(nil, 2, nil)
test("pack with nils", t.n == 3 and t[2] == 2)

-- ============================================================================
-- 6. table.unpack
-- ============================================================================
print("\n--- table.unpack ---")

t = {10, 20, 30}
local a, b, c = table.unpack(t)
test("unpack all", a == 10 and b == 20 and c == 30)

a, b = table.unpack(t, 2, 3)
test("unpack range", a == 20 and b == 30)

a = table.unpack(t, 1, 1)
test("unpack single", a == 10)

-- With function call
local function sum3(x, y, z)
    return x + y + z
end
test("unpack in call", sum3(table.unpack({1, 2, 3})) == 6)

-- ============================================================================
-- 7. table.move
-- ============================================================================
print("\n--- table.move ---")

local t1 = {1, 2, 3, 4, 5}
local t2 = {}
table.move(t1, 2, 4, 1, t2)
test("move to new table", t2[1] == 2 and t2[2] == 3 and t2[3] == 4)

t1 = {1, 2, 3, 4, 5}
table.move(t1, 1, 3, 3)  -- shift right within same table
test("move overlap right", t1[3] == 1 and t1[4] == 2 and t1[5] == 3)

t1 = {0, 0, 1, 2, 3}
table.move(t1, 3, 5, 1)  -- shift left within same table
test("move overlap left", t1[1] == 1 and t1[2] == 2 and t1[3] == 3)

-- ============================================================================
-- 8. # Operator (Length)
-- ============================================================================
print("\n--- Length Operator ---")

t = {1, 2, 3, 4, 5}
test("length basic", #t == 5)

t = {}
test("length empty", #t == 0)

t = {[1] = "a", [2] = "b", [5] = "e"}  -- sparse
test("length sparse", #t >= 2)  -- Lua behavior with holes is implementation-defined

-- ============================================================================
-- 9. Table Access Patterns
-- ============================================================================
print("\n--- Access Patterns ---")

t = {}
t.x = 10
t["y"] = 20
test("dot vs bracket", t.x == 10 and t.y == 20)

local key = "dynamic"
t[key] = 100
test("dynamic key", t.dynamic == 100)

-- Nested tables
t = {inner = {value = 42}}
test("nested access", t.inner.value == 42)

-- Method call syntax
t = {value = 10}
function t:get() return self.value end
test("method syntax", t:get() == 10)

-- ============================================================================
-- 10. Table Iteration Patterns
-- ============================================================================
print("\n--- Iteration Patterns ---")

t = {a = 1, b = 2, c = 3}
local sum = 0
local count = 0
for k, v in pairs(t) do
    sum = sum + v
    count = count + 1
end
test("pairs iteration", sum == 6 and count == 3)

t = {10, 20, 30}
sum = 0
for i, v in ipairs(t) do
    sum = sum + v
end
test("ipairs iteration", sum == 60)

-- ============================================================================
-- 11. Table as Set
-- ============================================================================
print("\n--- Table as Set ---")

local set = {}
set["apple"] = true
set["banana"] = true

test("set contains", set["apple"] == true)
test("set not contains", set["cherry"] == nil)

set["banana"] = nil
test("set remove", set["banana"] == nil)

-- ============================================================================
-- 12. Table as Stack
-- ============================================================================
print("\n--- Table as Stack ---")

local stack = {}

-- push
stack[#stack + 1] = 1
stack[#stack + 1] = 2
stack[#stack + 1] = 3
test("stack push", #stack == 3)

-- pop
local top = stack[#stack]
stack[#stack] = nil
test("stack pop", top == 3 and #stack == 2)

-- ============================================================================
-- 13. Table as Queue
-- ============================================================================
print("\n--- Table as Queue ---")

local queue = {first = 1, last = 0}

local function enqueue(q, val)
    q.last = q.last + 1
    q[q.last] = val
end

local function dequeue(q)
    if q.first > q.last then return nil end
    local val = q[q.first]
    q[q.first] = nil
    q.first = q.first + 1
    return val
end

enqueue(queue, "a")
enqueue(queue, "b")
enqueue(queue, "c")
test("queue enqueue", queue.last - queue.first + 1 == 3)

local first = dequeue(queue)
test("queue dequeue", first == "a")

-- ============================================================================
-- 14. Shallow Copy
-- ============================================================================
print("\n--- Shallow Copy ---")

local function shallow_copy(t)
    local copy = {}
    for k, v in pairs(t) do
        copy[k] = v
    end
    return copy
end

local original = {x = 1, y = 2, inner = {z = 3}}
local copy = shallow_copy(original)

test("copy has values", copy.x == 1 and copy.y == 2)
test("copy is different", copy ~= original)
test("inner is same ref", copy.inner == original.inner)

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
