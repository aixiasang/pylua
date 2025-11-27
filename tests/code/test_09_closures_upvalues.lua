-- ============================================================================
-- Test 09: Closures and Upvalues Comprehensive Tests
-- 测试闭包和upvalue的高级特性
-- ============================================================================

print("=== Test 09: Closures and Upvalues ===")

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
-- [1] Basic Closure Tests
-- ============================================================================
print("\n[1] Basic Closure Tests")

-- Test 1.1: Simple closure capturing local variable
local function make_counter()
    local count = 0
    return function()
        count = count + 1
        return count
    end
end

local counter1 = make_counter()
test("counter first call", counter1() == 1)
test("counter second call", counter1() == 2)
test("counter third call", counter1() == 3)

-- Test 1.2: Independent closures
local counter2 = make_counter()
test("independent counter first", counter2() == 1)
test("counter1 still independent", counter1() == 4)

-- ============================================================================
-- [2] Multiple Upvalues Tests
-- ============================================================================
print("\n[2] Multiple Upvalues Tests")

-- Test 2.1: Closure with multiple upvalues
local function make_calculator(initial)
    local value = initial
    local history = {}
    
    return {
        add = function(x)
            value = value + x
            table.insert(history, "+" .. x)
            return value
        end,
        sub = function(x)
            value = value - x
            table.insert(history, "-" .. x)
            return value
        end,
        get = function()
            return value
        end,
        history_count = function()
            return #history
        end
    }
end

local calc = make_calculator(10)
test("calculator initial", calc.get() == 10)
test("calculator add", calc.add(5) == 15)
test("calculator sub", calc.sub(3) == 12)
test("calculator history", calc.history_count() == 2)

-- ============================================================================
-- [3] Nested Closures Tests
-- ============================================================================
print("\n[3] Nested Closures Tests")

-- Test 3.1: Closure returning closure
local function outer(x)
    return function(y)
        return function(z)
            return x + y + z
        end
    end
end

local f1 = outer(1)
local f2 = f1(2)
test("nested closure result", f2(3) == 6)

-- Test 3.2: Multiple levels of nesting
local function make_adder(base)
    return function(increment)
        return function(value)
            return base + increment + value
        end
    end
end

local add_from_10 = make_adder(10)
local add_from_10_plus_5 = add_from_10(5)
test("multi-level nesting", add_from_10_plus_5(3) == 18)

-- ============================================================================
-- [4] Upvalue Modification Tests
-- ============================================================================
print("\n[4] Upvalue Modification Tests")

-- Test 4.1: Multiple closures sharing upvalue
local function make_shared_counter()
    local count = 0
    
    local inc = function()
        count = count + 1
        return count
    end
    
    local dec = function()
        count = count - 1
        return count
    end
    
    local get = function()
        return count
    end
    
    return inc, dec, get
end

local inc, dec, get = make_shared_counter()
test("shared upvalue initial", get() == 0)
inc()
inc()
test("shared upvalue after inc", get() == 2)
dec()
test("shared upvalue after dec", get() == 1)

-- ============================================================================
-- [5] Upvalue in Loops Tests
-- ============================================================================
print("\n[5] Upvalue in Loops Tests")

-- Test 5.1: Closure in loop (common pitfall)
local closures = {}
for i = 1, 5 do
    local captured = i  -- Important: capture in local variable
    closures[i] = function()
        return captured
    end
end

test("loop closure 1", closures[1]() == 1)
test("loop closure 3", closures[3]() == 3)
test("loop closure 5", closures[5]() == 5)

-- Test 5.2: Closure modifying loop variable
local function make_incrementers(n)
    local funcs = {}
    for i = 1, n do
        local val = i * 10
        funcs[i] = function()
            val = val + 1
            return val
        end
    end
    return funcs
end

local incs = make_incrementers(3)
test("loop incrementer 1 first", incs[1]() == 11)
test("loop incrementer 1 second", incs[1]() == 12)
test("loop incrementer 2 first", incs[2]() == 21)

-- ============================================================================
-- [6] Closure with Table Upvalues Tests
-- ============================================================================
print("\n[6] Closure with Table Upvalues Tests")

-- Test 6.1: Closure capturing table
local function make_object(name)
    local data = {
        name = name,
        count = 0,
        items = {}
    }
    
    return {
        get_name = function() return data.name end,
        increment = function() data.count = data.count + 1 end,
        get_count = function() return data.count end,
        add_item = function(item) table.insert(data.items, item) end,
        item_count = function() return #data.items end
    }
end

local obj = make_object("test")
test("object name", obj.get_name() == "test")
obj.increment()
obj.increment()
test("object count", obj.get_count() == 2)
obj.add_item("a")
obj.add_item("b")
test("object items", obj.item_count() == 2)

-- ============================================================================
-- [7] Closure Returning Multiple Values Tests
-- ============================================================================
print("\n[7] Closure Returning Multiple Values Tests")

-- Test 7.1: Closure with multiple returns
local function make_divmod()
    local last_a, last_b = 0, 0
    
    return function(a, b)
        last_a, last_b = a, b
        return a // b, a % b
    end, function()
        return last_a, last_b
    end
end

local divmod, get_last = make_divmod()
local q, r = divmod(17, 5)
test("divmod quotient", q == 3)
test("divmod remainder", r == 2)
local la, lb = get_last()
test("divmod last_a", la == 17)
test("divmod last_b", lb == 5)

-- ============================================================================
-- [8] Closure with Variadic Functions Tests
-- ============================================================================
print("\n[8] Closure with Variadic Functions Tests")

-- Test 8.1: Closure capturing variadic arguments
local function make_logger(prefix)
    return function(...)
        local args = {...}
        local count = select("#", ...)
        return prefix .. " " .. count
    end
end

local logger = make_logger("LOG:")
test("variadic closure 1 arg", logger("a") == "LOG: 1")
test("variadic closure 3 args", logger("a", "b", "c") == "LOG: 3")

-- Test 8.2: Closure with variadic upvalue
local function make_accumulator(...)
    local values = {...}
    
    return function(...)
        for i, v in ipairs({...}) do
            table.insert(values, v)
        end
        return #values
    end
end

local acc = make_accumulator(1, 2, 3)
test("accumulator initial", acc() == 3)
test("accumulator add 2", acc(4, 5) == 5)

-- ============================================================================
-- [9] Closure with Recursive Functions Tests
-- ============================================================================
print("\n[9] Closure with Recursive Functions Tests")

-- Test 9.1: Recursive closure
local function make_factorial()
    local cache = {}
    
    local function fact(n)
        if n <= 1 then return 1 end
        if cache[n] then return cache[n] end
        
        local result = n * fact(n - 1)
        cache[n] = result
        return result
    end
    
    return fact, function() 
        local count = 0
        for _ in pairs(cache) do count = count + 1 end
        return count
    end
end

local factorial, cache_size = make_factorial()
test("factorial 5", factorial(5) == 120)
test("factorial 6", factorial(6) == 720)
test("factorial cache", cache_size() >= 2)

-- ============================================================================
-- [10] Closure State Machine Tests
-- ============================================================================
print("\n[10] Closure State Machine Tests")

-- Test 10.1: State machine using closures
local function make_state_machine()
    local state = "idle"
    local transitions = {
        idle = {start = "running", reset = "idle"},
        running = {stop = "idle", pause = "paused"},
        paused = {resume = "running", stop = "idle"}
    }
    
    return {
        get_state = function() return state end,
        transition = function(event)
            local next_state = transitions[state] and transitions[state][event]
            if next_state then
                state = next_state
                return true
            end
            return false
        end
    }
end

local sm = make_state_machine()
test("state machine initial", sm.get_state() == "idle")
sm.transition("start")
test("state machine running", sm.get_state() == "running")
sm.transition("pause")
test("state machine paused", sm.get_state() == "paused")
sm.transition("resume")
test("state machine resumed", sm.get_state() == "running")

-- ============================================================================
-- [11] Closure Memory Tests
-- ============================================================================
print("\n[11] Closure Memory Tests")

-- Test 11.1: Large number of closures
local function make_many_closures(n)
    local closures = {}
    for i = 1, n do
        local val = i
        closures[i] = function() return val * 2 end
    end
    return closures
end

local many = make_many_closures(100)
test("many closures first", many[1]() == 2)
test("many closures middle", many[50]() == 100)
test("many closures last", many[100]() == 200)

-- ============================================================================
-- [12] Closure with Metatables Tests
-- ============================================================================
print("\n[12] Closure with Metatables Tests")

-- Test 12.1: Closure creating objects with metatables
local function make_vector(x, y)
    local v = {x = x, y = y}
    
    local mt = {
        __add = function(a, b)
            return make_vector(a.x + b.x, a.y + b.y)
        end,
        __tostring = function(t)
            return "(" .. t.x .. ", " .. t.y .. ")"
        end
    }
    
    setmetatable(v, mt)
    return v
end

local v1 = make_vector(1, 2)
local v2 = make_vector(3, 4)
local v3 = v1 + v2
test("vector add x", v3.x == 4)
test("vector add y", v3.y == 6)

-- ============================================================================
-- [13] Closure Chaining Tests
-- ============================================================================
print("\n[13] Closure Chaining Tests")

-- Test 13.1: Method chaining with closures
local function make_builder()
    local data = {}
    
    local builder = {}
    
    builder.add = function(key, value)
        data[key] = value
        return builder
    end
    
    builder.remove = function(key)
        data[key] = nil
        return builder
    end
    
    builder.build = function()
        return data
    end
    
    return builder
end

local result = make_builder()
    .add("a", 1)
    .add("b", 2)
    .add("c", 3)
    .remove("b")
    .build()

test("builder has a", result.a == 1)
test("builder no b", result.b == nil)
test("builder has c", result.c == 3)

-- ============================================================================
-- [14] Closure with Coroutine-like Behavior Tests
-- ============================================================================
print("\n[14] Closure with Coroutine-like Behavior Tests")

-- Test 14.1: Generator using closure
local function make_range(from, to, step)
    local current = from - (step or 1)
    
    return function()
        current = current + (step or 1)
        if current <= to then
            return current
        end
        return nil
    end
end

local gen = make_range(1, 5)
test("generator 1", gen() == 1)
test("generator 2", gen() == 2)
test("generator 3", gen() == 3)

-- Test 14.2: Stateful iterator
local function make_fibonacci()
    local a, b = 0, 1
    
    return function()
        local result = a
        a, b = b, a + b
        return result
    end
end

local fib = make_fibonacci()
test("fibonacci 0", fib() == 0)
test("fibonacci 1", fib() == 1)
test("fibonacci 1", fib() == 1)
test("fibonacci 2", fib() == 2)
test("fibonacci 3", fib() == 3)
test("fibonacci 5", fib() == 5)

-- ============================================================================
-- [15] Complex Upvalue Scenarios Tests
-- ============================================================================
print("\n[15] Complex Upvalue Scenarios Tests")

-- Test 15.1: Closure modifying upvalue from different scopes
local function complex_closure()
    local outer = 10
    
    local function level1()
        local middle = 20
        
        local function level2()
            local inner = 30
            
            return function()
                outer = outer + 1
                middle = middle + 1
                inner = inner + 1
                return outer, middle, inner
            end
        end
        
        return level2()
    end
    
    local f = level1()
    return f, function() return outer end
end

local modify, get_outer = complex_closure()
local o1, m1, i1 = modify()
test("complex upvalue outer 1", o1 == 11)
test("complex upvalue middle 1", m1 == 21)
test("complex upvalue inner 1", i1 == 31)

local o2, m2, i2 = modify()
test("complex upvalue outer 2", o2 == 12)
test("complex upvalue middle 2", m2 == 22)
test("complex upvalue inner 2", i2 == 32)

test("complex upvalue get_outer", get_outer() == 12)

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
    print("\n*** ALL CLOSURE AND UPVALUE TESTS PASSED ***")
else
    print("\n*** SOME TESTS FAILED ***")
end
