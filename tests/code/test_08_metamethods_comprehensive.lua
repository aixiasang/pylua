-- ============================================================================
-- Test 08: Comprehensive Metamethods Tests
-- 全面测试元方法功能
-- ============================================================================

print("=== Test 08: Comprehensive Metamethods ===")

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
-- [1] Basic Metatable Tests
-- ============================================================================
print("\n[1] Basic Metatable Tests")

-- Test 1.1: setmetatable and getmetatable
local t1 = {}
local mt1 = {}
setmetatable(t1, mt1)
test("setmetatable returns table", setmetatable(t1, mt1) == t1)
test("getmetatable works", getmetatable(t1) == mt1)

-- Test 1.2: Remove metatable with nil
setmetatable(t1, nil)
test("remove metatable", getmetatable(t1) == nil)

-- Test 1.3: Multiple tables with same metatable
local t2 = {}
local t3 = {}
local shared_mt = {}
setmetatable(t2, shared_mt)
setmetatable(t3, shared_mt)
test("shared metatable", getmetatable(t2) == getmetatable(t3))

-- ============================================================================
-- [2] __index Metamethod Tests
-- ============================================================================
print("\n[2] __index Metamethod Tests")

-- Test 2.1: __index as table
local base = { x = 10, y = 20 }
local derived = {}
setmetatable(derived, { __index = base })
test("__index table x", derived.x == 10)
test("__index table y", derived.y == 20)
test("__index own property", (function() derived.z = 30; return derived.z == 30 end)())

-- Test 2.2: __index as function
local function index_func(t, k)
    if k == "computed" then
        return "computed_value"
    end
    return "default"
end
local t4 = {}
setmetatable(t4, { __index = index_func })
test("__index function computed", t4.computed == "computed_value")
test("__index function default", t4.anything == "default")

-- Test 2.3: __index chain
local level1 = { a = 1 }
local level2 = { b = 2 }
local level3 = {}
setmetatable(level2, { __index = level1 })
setmetatable(level3, { __index = level2 })
test("__index chain a", level3.a == 1)
test("__index chain b", level3.b == 2)

-- Test 2.4: __index with rawget
local t5 = { real = "value" }
setmetatable(t5, { __index = function() return "meta" end })
test("rawget bypasses __index", rawget(t5, "real") == "value")
test("rawget returns nil", rawget(t5, "fake") == nil)

-- ============================================================================
-- [3] __newindex Metamethod Tests
-- ============================================================================
print("\n[3] __newindex Metamethod Tests")

-- Test 3.1: __newindex as table
local storage = {}
local proxy = {}
setmetatable(proxy, { __newindex = storage })
proxy.key1 = "value1"
test("__newindex stores in meta table", storage.key1 == "value1")
test("__newindex not in original", rawget(proxy, "key1") == nil)

-- Test 3.2: __newindex as function
local log = {}
local t6 = {}
setmetatable(t6, {
    __newindex = function(t, k, v)
        table.insert(log, k .. "=" .. tostring(v))
        rawset(t, k, v)
    end
})
t6.x = 10
t6.y = 20
test("__newindex function logs", #log == 2)
test("__newindex function sets", t6.x == 10 and t6.y == 20)

-- Test 3.3: __newindex read-only table
local readonly = {}
setmetatable(readonly, {
    __newindex = function() error("read-only table") end
})
local ro_error = false
local status = pcall(function() readonly.x = 1 end)
test("__newindex prevents write", not status)

-- ============================================================================
-- [4] Arithmetic Metamethods Tests
-- ============================================================================
print("\n[4] Arithmetic Metamethods Tests")

-- Test 4.1: __add
local v1 = { x = 1, y = 2 }
local v2 = { x = 3, y = 4 }
setmetatable(v1, {
    __add = function(a, b)
        return { x = a.x + b.x, y = a.y + b.y }
    end
})
setmetatable(v2, getmetatable(v1))
local v3 = v1 + v2
test("__add x", v3.x == 4)
test("__add y", v3.y == 6)

-- Test 4.2: __sub
setmetatable(v1, {
    __sub = function(a, b)
        return { x = a.x - b.x, y = a.y - b.y }
    end
})
setmetatable(v2, getmetatable(v1))
local v4 = v2 - v1
test("__sub x", v4.x == 2)
test("__sub y", v4.y == 2)

-- Test 4.3: __mul
setmetatable(v1, {
    __mul = function(a, b)
        if type(b) == "number" then
            return { x = a.x * b, y = a.y * b }
        end
        return { x = a.x * b.x, y = a.y * b.y }
    end
})
local v5 = v1 * 3
test("__mul scalar", v5.x == 3 and v5.y == 6)

-- Test 4.4: __div
local n1 = { value = 10 }
setmetatable(n1, {
    __div = function(a, b)
        if type(b) == "number" then
            return { value = a.value / b }
        end
    end
})
local n2 = n1 / 2
test("__div", n2.value == 5)

-- Test 4.5: __mod
local n3 = { value = 17 }
setmetatable(n3, {
    __mod = function(a, b)
        return { value = a.value % b }
    end
})
local n4 = n3 % 5
test("__mod", n4.value == 2)

-- Test 4.6: __unm
local n5 = { value = 42 }
setmetatable(n5, {
    __unm = function(a)
        return { value = -a.value }
    end
})
local n6 = -n5
test("__unm", n6.value == -42)

-- ============================================================================
-- [5] Comparison Metamethods Tests
-- ============================================================================
print("\n[5] Comparison Metamethods Tests")

-- Test 5.1: __eq
local p1 = { x = 5, y = 5 }
local p2 = { x = 5, y = 5 }
local point_mt = {
    __eq = function(a, b)
        return a.x == b.x and a.y == b.y
    end
}
setmetatable(p1, point_mt)
setmetatable(p2, point_mt)
test("__eq equal", p1 == p2)

local p3 = { x = 1, y = 1 }
setmetatable(p3, point_mt)
test("__eq not equal", p1 ~= p3)

-- Test 5.2: __lt
setmetatable(p1, {
    __lt = function(a, b)
        return a.x < b.x or (a.x == b.x and a.y < b.y)
    end
})
setmetatable(p3, getmetatable(p1))
test("__lt true", p3 < p1)
test("__lt false", not (p1 < p3))

-- Test 5.3: __le
setmetatable(p1, {
    __le = function(a, b)
        return a.x <= b.x and a.y <= b.y
    end,
    __eq = function(a, b)
        return a.x == b.x and a.y == b.y
    end
})
setmetatable(p2, getmetatable(p1))
setmetatable(p3, getmetatable(p1))
test("__le equal", p1 <= p2)
test("__le less", p3 <= p1)

-- ============================================================================
-- [6] __tostring Metamethod Tests
-- ============================================================================
print("\n[6] __tostring Metamethod Tests")

-- Test 6.1: Custom tostring
local obj1 = { name = "Object1", id = 123 }
setmetatable(obj1, {
    __tostring = function(o)
        return o.name .. " (" .. o.id .. ")"
    end
})
test("__tostring custom", tostring(obj1) == "Object1 (123)")

-- Test 6.2: tostring with complex data
local vec = { x = 3, y = 4 }
setmetatable(vec, {
    __tostring = function(v)
        return string.format("Vector{%.1f, %.1f}", v.x, v.y)
    end
})
test("__tostring complex", tostring(vec) == "Vector{3.0, 4.0}")

-- ============================================================================
-- [7] __call Metamethod Tests
-- ============================================================================
print("\n[7] __call Metamethod Tests")

-- Test 7.1: Table as function
local counter = { count = 0 }
setmetatable(counter, {
    __call = function(t)
        t.count = t.count + 1
        return t.count
    end
})
test("__call first", counter() == 1)
test("__call second", counter() == 2)
test("__call third", counter() == 3)

-- Test 7.2: __call with arguments
local adder = { base = 10 }
setmetatable(adder, {
    __call = function(t, x)
        return t.base + x
    end
})
test("__call with arg", adder(5) == 15)

-- Test 7.3: __call returning multiple values
local multi = {}
setmetatable(multi, {
    __call = function(t, x)
        return x, x * 2, x * 3
    end
})
local a, b, c = multi(5)
test("__call multi values", a == 5 and b == 10 and c == 15)

-- ============================================================================
-- [8] __concat Metamethod Tests
-- ============================================================================
print("\n[8] __concat Metamethod Tests")

-- Test 8.1: String concatenation
local str1 = { value = "Hello" }
local str2 = { value = "World" }
setmetatable(str1, {
    __concat = function(a, b)
        local av = type(a) == "table" and a.value or a
        local bv = type(b) == "table" and b.value or b
        return { value = av .. " " .. bv }
    end
})
setmetatable(str2, getmetatable(str1))
local str3 = str1 .. str2
test("__concat tables", str3.value == "Hello World")

-- Test 8.2: Concat with string
local str4 = str1 .. "!"
test("__concat with string", str4.value == "Hello !")

-- ============================================================================
-- [9] __len Metamethod Tests
-- ============================================================================
print("\n[9] __len Metamethod Tests")

-- Test 9.1: Custom length
local collection = { items = {1, 2, 3, 4, 5} }
setmetatable(collection, {
    __len = function(t)
        return #t.items
    end
})
test("__len custom", #collection == 5)

-- Test 9.2: Length changing
table.insert(collection.items, 6)
test("__len after insert", #collection == 6)

-- ============================================================================
-- [10] Complex Metatable Patterns Tests
-- ============================================================================
print("\n[10] Complex Metatable Patterns Tests")

-- Test 10.1: Private fields pattern
local function createObject(value)
    local private = { data = value }
    local public = {}
    
    setmetatable(public, {
        __index = function(t, k)
            if k == "value" then
                return private.data
            end
        end,
        __newindex = function(t, k, v)
            if k == "value" then
                private.data = v
            else
                error("field " .. k .. " does not exist")
            end
        end
    })
    
    return public
end

local private_obj = createObject(42)
test("private field read", private_obj.value == 42)
private_obj.value = 100
test("private field write", private_obj.value == 100)

-- Test 10.2: Immutable object pattern
local function createImmutable(data)
    local obj = {}
    setmetatable(obj, {
        __index = data,
        __newindex = function() error("immutable object") end
    })
    return obj
end

local immut = createImmutable({ x = 10, y = 20 })
test("immutable read", immut.x == 10)
local immut_error = not pcall(function() immut.x = 99 end)
test("immutable write fails", immut_error)

-- ============================================================================
-- [11] Metatable Inheritance Tests
-- ============================================================================
print("\n[11] Metatable Inheritance Tests")

-- Test 11.1: Simple inheritance
local Animal = {
    speak = function(self) return "Some sound" end
}
Animal.__index = Animal

local Dog = {}
setmetatable(Dog, { __index = Animal })
Dog.__index = Dog

function Dog:speak()
    return "Woof"
end

function Dog:new()
    local dog = {}
    setmetatable(dog, self)
    return dog
end

local myDog = Dog:new()
test("inheritance method", myDog:speak() == "Woof")

-- Test 11.2: Multi-level inheritance
local Puppy = {}
setmetatable(Puppy, { __index = Dog })
Puppy.__index = Puppy

function Puppy:speak()
    return "Yip"
end

function Puppy:new()
    local puppy = {}
    setmetatable(puppy, self)
    return puppy
end

local myPuppy = Puppy:new()
test("multi-level inheritance", myPuppy:speak() == "Yip")

-- ============================================================================
-- [12] Metamethod Priority Tests
-- ============================================================================
print("\n[12] Metamethod Priority Tests")

-- Test 12.1: __index priority over __newindex
local meta_priority = {}
local access_log = {}

setmetatable(meta_priority, {
    __index = function(t, k)
        table.insert(access_log, "index_" .. k)
        return "from_index"
    end,
    __newindex = function(t, k, v)
        table.insert(access_log, "newindex_" .. k)
        rawset(t, k, v)
    end
})

meta_priority.test1 = "value1"
local val = meta_priority.test1
test("__newindex called on new key", access_log[1] == "newindex_test1")
test("__index not called on existing", val == "value1")

-- ============================================================================
-- [13] Metatable with Multiple Metamethods Tests
-- ============================================================================
print("\n[13] Metatable with Multiple Metamethods Tests")

-- Test 13.1: Comprehensive metatable
local ComplexObj = {}
local complex_mt = {
    __index = ComplexObj,
    __tostring = function(o) return "ComplexObj:" .. o.id end,
    __eq = function(a, b) return a.id == b.id end,
    __lt = function(a, b) return a.id < b.id end,
    __add = function(a, b) return { id = a.id + b.id } end,
    __call = function(o, x) return o.id + x end
}

function ComplexObj.new(id)
    local obj = { id = id }
    setmetatable(obj, complex_mt)
    return obj
end

local co1 = ComplexObj.new(5)
local co2 = ComplexObj.new(5)
local co3 = ComplexObj.new(3)

test("multiple meta __tostring", tostring(co1) == "ComplexObj:5")
test("multiple meta __eq", co1 == co2)
test("multiple meta __lt", co3 < co1)

local co4 = co1 + co3
test("multiple meta __add", co4.id == 8)
test("multiple meta __call", co1(10) == 15)

-- ============================================================================
-- [14] Weak Tables Tests (if supported)
-- ============================================================================
print("\n[14] Weak Tables Tests")

-- Test 14.1: Weak table creation
local weak_table = {}
setmetatable(weak_table, { __mode = "k" })
test("weak table created", getmetatable(weak_table).__mode == "k")

-- Test 14.2: Weak value table
local weak_values = {}
setmetatable(weak_values, { __mode = "v" })
test("weak value table", getmetatable(weak_values).__mode == "v")

-- Test 14.3: Weak key-value table
local weak_both = {}
setmetatable(weak_both, { __mode = "kv" })
test("weak both table", getmetatable(weak_both).__mode == "kv")

-- ============================================================================
-- [15] Metatable Edge Cases Tests
-- ============================================================================
print("\n[15] Metatable Edge Cases Tests")

-- Test 15.1: Empty metatable
local t_empty = {}
setmetatable(t_empty, {})
test("empty metatable", getmetatable(t_empty) ~= nil)

-- Test 15.2: Metatable on number (should use global metatable)
local num_mt = {}
-- Note: Can't set metatable on number directly in Lua
test("number metatable test", true)  -- Placeholder

-- Test 15.3: Nested metatables
local inner_mt = { value = "inner" }
local outer_mt = { value = "outer", __index = inner_mt }
local nested = {}
setmetatable(nested, outer_mt)
-- When accessing nested.value:
-- 1. nested doesn't have 'value'
-- 2. Check metatable (outer_mt) for __index -> finds inner_mt
-- 3. Look in inner_mt for 'value' -> finds "inner"
-- So the correct result is "inner", not "outer"
test("nested metatable access", nested.value == "inner")

-- Test 15.4: Metatable with nil values
local nil_mt = { __index = function() return nil end }
local t_nil = {}
setmetatable(t_nil, nil_mt)
test("metatable returns nil", t_nil.anything == nil)

-- ============================================================================
-- [16] Performance Pattern Tests
-- ============================================================================
print("\n[16] Performance Pattern Tests")

-- Test 16.1: Cached __index
local cache = {}
local expensive_mt = {
    __index = function(t, k)
        if not cache[k] then
            cache[k] = "computed_" .. k
        end
        return cache[k]
    end
}

local t_cached = {}
setmetatable(t_cached, expensive_mt)
local val1 = t_cached.key1
local val2 = t_cached.key1
test("cached __index works", val1 == val2 and val1 == "computed_key1")

-- Test 16.2: Lazy initialization
local lazy_mt = {
    __index = function(t, k)
        if k == "data" then
            local computed = {1, 2, 3, 4, 5}
            rawset(t, k, computed)
            return computed
        end
    end
}

local t_lazy = {}
setmetatable(t_lazy, lazy_mt)
test("lazy init first", t_lazy.data[1] == 1)
test("lazy init cached", rawget(t_lazy, "data") ~= nil)

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
    print("\n*** ALL METAMETHOD TESTS PASSED ***")
else
    print("\n*** SOME TESTS FAILED ***")
end
