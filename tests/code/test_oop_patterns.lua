-- test_oop_patterns.lua
-- Object-Oriented Programming patterns tests

print("=== OOP Patterns Tests ===")

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
-- 1. Simple Class Pattern
-- ============================================================================
print("\n--- Simple Class ---")

local Point = {}
Point.__index = Point

function Point.new(x, y)
    local self = setmetatable({}, Point)
    self.x = x or 0
    self.y = y or 0
    return self
end

function Point:distance(other)
    local dx = self.x - other.x
    local dy = self.y - other.y
    return math.sqrt(dx * dx + dy * dy)
end

function Point:move(dx, dy)
    self.x = self.x + dx
    self.y = self.y + dy
end

local p1 = Point.new(0, 0)
local p2 = Point.new(3, 4)
test("Point creation", p1.x == 0 and p1.y == 0)
test("Point distance", p1:distance(p2) == 5)
p1:move(1, 1)
test("Point move", p1.x == 1 and p1.y == 1)

-- ============================================================================
-- 2. Inheritance Pattern
-- ============================================================================
print("\n--- Inheritance ---")

local Animal = {}
Animal.__index = Animal

function Animal.new(name)
    local self = setmetatable({}, Animal)
    self.name = name
    return self
end

function Animal:speak()
    return self.name .. " makes a sound"
end

function Animal:get_name()
    return self.name
end

-- Dog inherits from Animal
local Dog = setmetatable({}, {__index = Animal})
Dog.__index = Dog

function Dog.new(name, breed)
    local self = setmetatable(Animal.new(name), Dog)
    self.breed = breed
    return self
end

function Dog:speak()
    return self.name .. " barks!"
end

function Dog:get_breed()
    return self.breed
end

local animal = Animal.new("Generic")
local dog = Dog.new("Rex", "Shepherd")

test("Animal speak", animal:speak() == "Generic makes a sound")
test("Dog override", dog:speak() == "Rex barks!")
test("Dog inherited method", dog:get_name() == "Rex")
test("Dog own method", dog:get_breed() == "Shepherd")

-- ============================================================================
-- 3. Private Members Pattern
-- ============================================================================
print("\n--- Private Members ---")

local function make_counter(start)
    local count = start or 0  -- private
    local self = {}
    
    function self:increment()
        count = count + 1
    end
    
    function self:decrement()
        count = count - 1
    end
    
    function self:get()
        return count
    end
    
    return self
end

local counter = make_counter(10)
test("Private initial", counter:get() == 10)
counter:increment()
counter:increment()
test("Private increment", counter:get() == 12)
counter:decrement()
test("Private decrement", counter:get() == 11)

-- ============================================================================
-- 4. Mixin Pattern
-- ============================================================================
print("\n--- Mixin Pattern ---")

local function mixin(target, source)
    for k, v in pairs(source) do
        if target[k] == nil then
            target[k] = v
        end
    end
    return target
end

local Comparable = {
    __eq = function(a, b) return a:compare(b) == 0 end,
    __lt = function(a, b) return a:compare(b) < 0 end,
    __le = function(a, b) return a:compare(b) <= 0 end
}

local Number = {}
Number.__index = Number
mixin(Number, Comparable)

function Number.new(value)
    local self = setmetatable({}, Number)
    self.value = value
    return self
end

function Number:compare(other)
    if self.value < other.value then return -1
    elseif self.value > other.value then return 1
    else return 0 end
end

local n1 = Number.new(5)
local n2 = Number.new(10)
local n3 = Number.new(5)

test("Mixin eq false", n1 == n2 == false)
test("Mixin eq true", n1 == n3 == true)
test("Mixin lt", (n1 < n2) == true)
test("Mixin le", (n1 <= n3) == true)

-- ============================================================================
-- 5. Singleton Pattern
-- ============================================================================
print("\n--- Singleton Pattern ---")

local Singleton = {}
local instance = nil

function Singleton.get_instance()
    if instance == nil then
        instance = {value = 0}
        function instance:set(v) self.value = v end
        function instance:get() return self.value end
    end
    return instance
end

local s1 = Singleton.get_instance()
local s2 = Singleton.get_instance()
s1:set(42)
test("Singleton same instance", s1 == s2)
test("Singleton shared state", s2:get() == 42)

-- ============================================================================
-- 6. Factory Pattern
-- ============================================================================
print("\n--- Factory Pattern ---")

local ShapeFactory = {}

function ShapeFactory.create(shape_type, ...)
    if shape_type == "circle" then
        local radius = ...
        return {type = "circle", radius = radius, area = function(self) return math.pi * self.radius ^ 2 end}
    elseif shape_type == "rectangle" then
        local w, h = ...
        return {type = "rectangle", width = w, height = h, area = function(self) return self.width * self.height end}
    else
        return nil
    end
end

local circle = ShapeFactory.create("circle", 5)
local rect = ShapeFactory.create("rectangle", 4, 6)

test("Factory circle", circle.type == "circle" and circle.radius == 5)
test("Factory rectangle", rect.type == "rectangle")
test("Factory circle area", math.abs(circle:area() - 78.539816) < 0.001)
test("Factory rect area", rect:area() == 24)

-- ============================================================================
-- 7. Observer Pattern
-- ============================================================================
print("\n--- Observer Pattern ---")

local Subject = {}
Subject.__index = Subject

function Subject.new()
    local self = setmetatable({}, Subject)
    self.observers = {}
    self.state = nil
    return self
end

function Subject:attach(observer)
    self.observers[#self.observers + 1] = observer
end

function Subject:notify()
    for _, observer in ipairs(self.observers) do
        observer:update(self.state)
    end
end

function Subject:set_state(state)
    self.state = state
    self:notify()
end

local updates = {}
local observer1 = {update = function(self, state) updates[1] = state end}
local observer2 = {update = function(self, state) updates[2] = state end}

local subject = Subject.new()
subject:attach(observer1)
subject:attach(observer2)
subject:set_state("new state")

test("Observer 1 notified", updates[1] == "new state")
test("Observer 2 notified", updates[2] == "new state")

-- ============================================================================
-- 8. Decorator Pattern
-- ============================================================================
print("\n--- Decorator Pattern ---")

local function make_coffee()
    return {cost = 2, description = "Coffee"}
end

local function with_milk(coffee)
    coffee.cost = coffee.cost + 0.5
    coffee.description = coffee.description .. " with Milk"
    return coffee
end

local function with_sugar(coffee)
    coffee.cost = coffee.cost + 0.2
    coffee.description = coffee.description .. " with Sugar"
    return coffee
end

local order = with_sugar(with_milk(make_coffee()))
test("Decorator description", order.description == "Coffee with Milk with Sugar")
test("Decorator cost", order.cost == 2.7)

-- ============================================================================
-- 9. Prototype Pattern
-- ============================================================================
print("\n--- Prototype Pattern ---")

local function clone(obj)
    local copy = {}
    for k, v in pairs(obj) do
        copy[k] = v
    end
    setmetatable(copy, getmetatable(obj))
    return copy
end

local prototype = {x = 10, y = 20}
setmetatable(prototype, {__index = {z = 30}})

local cloned = clone(prototype)
test("Clone values", cloned.x == 10 and cloned.y == 20)
test("Clone metatable", cloned.z == 30)
cloned.x = 100
test("Clone independent", prototype.x == 10 and cloned.x == 100)

-- ============================================================================
-- 10. Module Pattern
-- ============================================================================
print("\n--- Module Pattern ---")

local function create_module()
    local M = {}
    
    -- Private
    local private_data = "secret"
    local function private_func()
        return private_data
    end
    
    -- Public
    function M.get_data()
        return private_func()
    end
    
    function M.process(x)
        return x * 2
    end
    
    return M
end

local mymodule = create_module()
test("Module public method", mymodule.process(5) == 10)
test("Module private access", mymodule.get_data() == "secret")

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
