-- test_metatable.lua
-- Comprehensive metatable and metamethod tests for Lua 5.3

print("=== Metatable Tests ===")
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
-- 1. Basic Metatable Operations
-- ============================================================================
print("\n--- Basic Metatable Operations ---")

local t = {}
local mt = {}

test("getmetatable nil", getmetatable(t) == nil, nil, getmetatable(t))

setmetatable(t, mt)
test("setmetatable", getmetatable(t) == mt, true, getmetatable(t) == mt)

-- ============================================================================
-- 2. __index Metamethod (Table)
-- ============================================================================
print("\n--- __index (Table) ---")

local base = {x = 10, y = 20}
local derived = {}
setmetatable(derived, {__index = base})

test("__index table get x", derived.x == 10, 10, derived.x)
test("__index table get y", derived.y == 20, 20, derived.y)
test("__index table nil", derived.z == nil, nil, derived.z)

-- Override in derived
derived.x = 100
test("__index override", derived.x == 100, 100, derived.x)
test("__index base unchanged", base.x == 10, 10, base.x)

-- ============================================================================
-- 3. __index Metamethod (Function)
-- ============================================================================
print("\n--- __index (Function) ---")

local obj = {a = 1}
setmetatable(obj, {
    __index = function(t, k)
        return "key_" .. tostring(k)
    end
})

test("__index func existing", obj.a == 1, 1, obj.a)
test("__index func missing", obj.b == "key_b", "key_b", obj.b)
test("__index func missing2", obj.xyz == "key_xyz", "key_xyz", obj.xyz)

-- ============================================================================
-- 4. __newindex Metamethod (Table)
-- ============================================================================
print("\n--- __newindex (Table) ---")

local storage = {}
local proxy = {}
setmetatable(proxy, {__newindex = storage})

proxy.a = 10
proxy.b = 20
test("__newindex table a", rawget(storage, "a") == 10, 10, rawget(storage, "a"))
test("__newindex table b", rawget(storage, "b") == 20, 20, rawget(storage, "b"))
test("__newindex proxy empty", rawget(proxy, "a") == nil, nil, rawget(proxy, "a"))

-- ============================================================================
-- 5. __newindex Metamethod (Function)
-- ============================================================================
print("\n--- __newindex (Function) ---")

local log = {}
local logged = {}
setmetatable(logged, {
    __newindex = function(t, k, v)
        log[#log + 1] = k .. "=" .. tostring(v)
        rawset(t, k, v)
    end
})

logged.x = 5
logged.y = 10
test("__newindex func set x", logged.x == 5, 5, logged.x)
test("__newindex func set y", logged.y == 10, 10, logged.y)
test("__newindex func log1", log[1] == "x=5", "x=5", log[1])
test("__newindex func log2", log[2] == "y=10", "y=10", log[2])

-- ============================================================================
-- 6. __add Metamethod
-- ============================================================================
print("\n--- __add Metamethod ---")

local Vector = {}
Vector.__index = Vector

function Vector.new(x, y)
    local v = {x = x, y = y}
    setmetatable(v, Vector)
    return v
end

function Vector.__add(a, b)
    return Vector.new(a.x + b.x, a.y + b.y)
end

local v1 = Vector.new(1, 2)
local v2 = Vector.new(3, 4)
local v3 = v1 + v2

test("__add x", v3.x == 4, 4, v3.x)
test("__add y", v3.y == 6, 6, v3.y)

-- ============================================================================
-- 7. __sub Metamethod
-- ============================================================================
print("\n--- __sub Metamethod ---")

function Vector.__sub(a, b)
    return Vector.new(a.x - b.x, a.y - b.y)
end

local v4 = v2 - v1
test("__sub x", v4.x == 2, 2, v4.x)
test("__sub y", v4.y == 2, 2, v4.y)

-- ============================================================================
-- 8. __mul Metamethod
-- ============================================================================
print("\n--- __mul Metamethod ---")

function Vector.__mul(a, b)
    if type(b) == "number" then
        return Vector.new(a.x * b, a.y * b)
    else
        return Vector.new(a.x * b.x, a.y * b.y)
    end
end

local v5 = v1 * 3
test("__mul scalar x", v5.x == 3, 3, v5.x)
test("__mul scalar y", v5.y == 6, 6, v5.y)

-- ============================================================================
-- 9. __unm Metamethod
-- ============================================================================
print("\n--- __unm Metamethod ---")

function Vector.__unm(v)
    return Vector.new(-v.x, -v.y)
end

local v6 = -v1
test("__unm x", v6.x == -1, -1, v6.x)
test("__unm y", v6.y == -2, -2, v6.y)

-- ============================================================================
-- 10. __len Metamethod
-- ============================================================================
print("\n--- __len Metamethod ---")

local sized = {1, 2, 3}
setmetatable(sized, {
    __len = function(t)
        return 100
    end
})

test("__len custom", #sized == 100, 100, #sized)

-- ============================================================================
-- 11. __eq Metamethod
-- ============================================================================
print("\n--- __eq Metamethod ---")

local EqClass = {}
EqClass.__index = EqClass

function EqClass.new(val)
    local obj = {value = val}
    setmetatable(obj, EqClass)
    return obj
end

function EqClass.__eq(a, b)
    return a.value == b.value
end

local eq1 = EqClass.new(42)
local eq2 = EqClass.new(42)
local eq3 = EqClass.new(100)

test("__eq same value", eq1 == eq2, true, eq1 == eq2)
test("__eq diff value", eq1 == eq3, false, eq1 == eq3)

-- ============================================================================
-- 12. __lt and __le Metamethods
-- ============================================================================
print("\n--- __lt and __le Metamethods ---")

function EqClass.__lt(a, b)
    return a.value < b.value
end

function EqClass.__le(a, b)
    return a.value <= b.value
end

test("__lt true", eq1 < eq3, true, eq1 < eq3)
test("__lt false", eq3 < eq1, false, eq3 < eq1)
test("__le true eq", eq1 <= eq2, true, eq1 <= eq2)
test("__le true lt", eq1 <= eq3, true, eq1 <= eq3)
test("__le false", eq3 <= eq1, false, eq3 <= eq1)

-- ============================================================================
-- 13. __concat Metamethod
-- ============================================================================
print("\n--- __concat Metamethod ---")

local ConcatClass = {}
ConcatClass.__index = ConcatClass

function ConcatClass.new(s)
    local obj = {str = s}
    setmetatable(obj, ConcatClass)
    return obj
end

function ConcatClass.__concat(a, b)
    local as = type(a) == "table" and a.str or tostring(a)
    local bs = type(b) == "table" and b.str or tostring(b)
    return ConcatClass.new(as .. bs)
end

local c1 = ConcatClass.new("hello")
local c2 = ConcatClass.new(" world")
local c3 = c1 .. c2

test("__concat", c3.str == "hello world", "hello world", c3.str)

-- ============================================================================
-- 14. __call Metamethod
-- ============================================================================
print("\n--- __call Metamethod ---")

local callable = {}
setmetatable(callable, {
    __call = function(t, a, b)
        return a + b
    end
})

test("__call", callable(3, 4) == 7, 7, callable(3, 4))

-- ============================================================================
-- 15. __tostring Metamethod
-- ============================================================================
print("\n--- __tostring Metamethod ---")

local Printable = {}
Printable.__index = Printable

function Printable.new(name)
    local obj = {name = name}
    setmetatable(obj, Printable)
    return obj
end

function Printable.__tostring(obj)
    return "Printable(" .. obj.name .. ")"
end

local p1 = Printable.new("test")
test("__tostring", tostring(p1) == "Printable(test)", "Printable(test)", tostring(p1))

-- ============================================================================
-- 16. Chained __index
-- ============================================================================
print("\n--- Chained __index ---")

local level1 = {a = 1}
local level2 = {b = 2}
local level3 = {c = 3}

setmetatable(level3, {__index = level2})
setmetatable(level2, {__index = level1})

test("chain level3.c", level3.c == 3, 3, level3.c)
test("chain level3.b", level3.b == 2, 2, level3.b)
test("chain level3.a", level3.a == 1, 1, level3.a)

-- ============================================================================
-- 17. rawget and rawset bypass metamethods
-- ============================================================================
print("\n--- rawget/rawset bypass ---")

local bypassed = {}
local called = false
setmetatable(bypassed, {
    __index = function(t, k) called = true; return "mm" end,
    __newindex = function(t, k, v) called = true end
})

called = false
local val = rawget(bypassed, "x")
test("rawget no mm", called == false, false, called)
test("rawget nil", val == nil, nil, val)

called = false
rawset(bypassed, "x", 42)
test("rawset no mm", called == false, false, called)
test("rawset value", rawget(bypassed, "x") == 42, 42, rawget(bypassed, "x"))

-- ============================================================================
-- 18. Prototype pattern
-- ============================================================================
print("\n--- Prototype Pattern ---")

local Animal = {}
Animal.__index = Animal

function Animal.new(name)
    local self = setmetatable({}, Animal)
    self.name = name
    return self
end

function Animal:speak()
    return self.name .. " says hello"
end

local dog = Animal.new("Dog")
test("prototype method", dog:speak() == "Dog says hello", "Dog says hello", dog:speak())

-- ============================================================================
-- 19. Inheritance pattern
-- ============================================================================
print("\n--- Inheritance Pattern ---")

local Cat = setmetatable({}, {__index = Animal})
Cat.__index = Cat

function Cat.new(name)
    local self = setmetatable({}, Cat)
    self.name = name
    return self
end

function Cat:speak()
    return self.name .. " says meow"
end

local cat = Cat.new("Kitty")
test("inherit override", cat:speak() == "Kitty says meow", "Kitty says meow", cat:speak())

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
