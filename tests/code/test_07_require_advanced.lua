-- ============================================================================
-- Test 07: Require Advanced Features and Error Handling
-- 测试require的高级功能和错误处理
-- ============================================================================

print("=== Test 07: Require Advanced Features ===")

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
-- [1] Module with Upvalues Tests
-- ============================================================================
print("\n[1] Module with Upvalues Tests")

-- Test 1.1: Module capturing external variable
local external_value = "captured"
package.preload.upvalue_mod = function()
    return {
        get_external = function() return external_value end,
        local_value = "internal"
    }
end

local upval_mod = require("upvalue_mod")
test("upvalue captured", upval_mod.get_external() == "captured")
test("local value exists", upval_mod.local_value == "internal")

-- Test 1.2: Module with closure
package.preload.closure_mod = function()
    local private = 0
    return {
        inc = function() private = private + 1 end,
        dec = function() private = private - 1 end,
        get = function() return private end
    }
end

local closure = require("closure_mod")
test("closure initial", closure.get() == 0)
closure.inc()
closure.inc()
test("closure after inc", closure.get() == 2)
closure.dec()
test("closure after dec", closure.get() == 1)

-- ============================================================================
-- [2] Module with Metatable Tests
-- ============================================================================
print("\n[2] Module with Metatable Tests")

-- Test 2.1: Module as metatable
package.preload.meta_mod = function()
    local mt = {
        __index = function(t, k)
            return "default_" .. tostring(k)
        end,
        __call = function(t, x)
            return x * 2
        end
    }
    
    local mod = setmetatable({ real_value = 100 }, mt)
    return mod
end

local meta = require("meta_mod")
test("metatable real value", meta.real_value == 100)
test("metatable __index", meta.fake_key == "default_fake_key")
test("metatable __call", meta(5) == 10)

-- Test 2.2: Module with __tostring
package.preload.tostring_mod = function()
    local mt = {
        __tostring = function() return "Custom Module" end
    }
    return setmetatable({ version = "1.0" }, mt)
end

local ts_mod = require("tostring_mod")
test("custom __tostring", tostring(ts_mod) == "Custom Module")

-- ============================================================================
-- [3] Nested Table Module Tests
-- ============================================================================
print("\n[3] Nested Table Module Tests")

-- Test 3.1: Deep nested structure
package.preload.nested_mod = function()
    return {
        level1 = {
            level2 = {
                level3 = {
                    level4 = {
                        value = "deep"
                    }
                }
            },
            data = "mid"
        },
        top = "surface"
    }
end

local nested = require("nested_mod")
test("nested top level", nested.top == "surface")
test("nested mid level", nested.level1.data == "mid")
test("nested deep level", nested.level1.level2.level3.level4.value == "deep")

-- Test 3.2: Module with array
package.preload.array_mod = function()
    return {
        numbers = {1, 2, 3, 4, 5},
        strings = {"a", "b", "c"},
        mixed = {1, "two", 3, "four", 5}
    }
end

local arr_mod = require("array_mod")
test("array numbers", arr_mod.numbers[3] == 3)
test("array strings", arr_mod.strings[2] == "b")
test("array mixed", arr_mod.mixed[4] == "four")

-- ============================================================================
-- [4] Module Function Export Tests
-- ============================================================================
print("\n[4] Module Function Export Tests")

-- Test 4.1: Math utilities module
package.preload.math_utils = function()
    local M = {}
    
    function M.add(a, b)
        return a + b
    end
    
    function M.multiply(a, b)
        return a * b
    end
    
    function M.power(base, exp)
        local result = 1
        for i = 1, exp do
            result = result * base
        end
        return result
    end
    
    return M
end

local math_utils = require("math_utils")
test("math add", math_utils.add(3, 5) == 8)
test("math multiply", math_utils.multiply(4, 7) == 28)
test("math power", math_utils.power(2, 10) == 1024)

-- Test 4.2: String utilities module
package.preload.string_utils = function()
    return {
        reverse = function(s)
            local r = ""
            for i = #s, 1, -1 do
                r = r .. string.sub(s, i, i)
            end
            return r
        end,
        
        count = function(s, char)
            local c = 0
            for i = 1, #s do
                if string.sub(s, i, i) == char then
                    c = c + 1
                end
            end
            return c
        end
    }
end

local str_utils = require("string_utils")
test("string reverse", str_utils.reverse("hello") == "olleh")
test("string count", str_utils.count("hello", "l") == 2)

-- ============================================================================
-- [5] Module with Constants Tests
-- ============================================================================
print("\n[5] Module with Constants Tests")

-- Test 5.1: Config module
package.preload.config = function()
    return {
        VERSION = "1.0.0",
        MAX_SIZE = 1000,
        MIN_SIZE = 10,
        DEFAULT_NAME = "unnamed",
        PI = 3.14159,
        FLAGS = {
            DEBUG = true,
            VERBOSE = false,
            STRICT = true
        }
    }
end

local config = require("config")
test("config VERSION", config.VERSION == "1.0.0")
test("config MAX_SIZE", config.MAX_SIZE == 1000)
test("config nested flag", config.FLAGS.DEBUG == true)
test("config PI", config.PI > 3.14 and config.PI < 3.15)

-- ============================================================================
-- [6] Module Initialization Tests
-- ============================================================================
print("\n[6] Module Initialization Tests")

-- Test 6.1: Module with initialization code
local init_log = {}
package.preload.init_mod = function()
    table.insert(init_log, "init_start")
    
    local data = {}
    for i = 1, 5 do
        data[i] = i * i
    end
    
    table.insert(init_log, "init_end")
    
    return {
        data = data,
        init_count = #init_log
    }
end

local init_mod = require("init_mod")
test("initialization ran", #init_log == 2)
test("initialization data", init_mod.data[4] == 16)
test("init count correct", init_mod.init_count == 2)

-- Test 6.2: Module not re-initialized
local before_count = #init_log
local init_mod2 = require("init_mod")
test("no re-initialization", #init_log == before_count)
test("same instance", init_mod == init_mod2)

-- ============================================================================
-- [7] Module Return Validation Tests
-- ============================================================================
print("\n[7] Module Return Validation Tests")

-- Test 7.1: Empty table module
package.preload.empty_mod = function()
    return {}
end
local empty = require("empty_mod")
test("empty module is table", type(empty) == "table")

-- Test 7.2: Module returning zero
package.preload.zero_mod = function()
    return 0
end
local zero = require("zero_mod")
test("zero module returns 0", zero == 0)

-- Test 7.3: Module returning false
package.preload.false_mod = function()
    return false
end
local false_mod = require("false_mod")
test("false module returns false", false_mod == false)

-- Test 7.4: Module returning empty string
package.preload.empty_string_mod = function()
    return ""
end
local empty_str = require("empty_string_mod")
test("empty string module", empty_str == "")

-- ============================================================================
-- [8] Circular Dependency Tests
-- ============================================================================
print("\n[8] Circular Dependency Tests")

-- Test 8.1: Simple circular dependency
package.preload.circ_a = function()
    local a = { name = "A" }
    a.get_b = function()
        local b = require("circ_b")
        return b
    end
    return a
end

package.preload.circ_b = function()
    local b = { name = "B" }
    b.get_a = function()
        local a = require("circ_a")
        return a
    end
    return b
end

local circ_a = require("circ_a")
local circ_b = require("circ_b")
test("circular A name", circ_a.name == "A")
test("circular B name", circ_b.name == "B")
test("circular A gets B", circ_a.get_b().name == "B")
test("circular B gets A", circ_b.get_a().name == "A")

-- ============================================================================
-- [9] Module with Variadic Functions Tests
-- ============================================================================
print("\n[9] Module with Variadic Functions Tests")

-- Test 9.1: Variadic function module
package.preload.variadic = function()
    return {
        sum = function(...)
            local total = 0
            for i, v in ipairs({...}) do
                total = total + v
            end
            return total
        end,
        
        concat = function(...)
            local result = ""
            for i, v in ipairs({...}) do
                result = result .. tostring(v)
            end
            return result
        end,
        
        count = function(...)
            return select("#", ...)
        end
    }
end

local variadic = require("variadic")
test("variadic sum", variadic.sum(1, 2, 3, 4, 5) == 15)
test("variadic concat", variadic.concat("a", "b", "c") == "abc")
test("variadic count", variadic.count(1, 2, 3) == 3)

-- ============================================================================
-- [10] Module with Iterators Tests
-- ============================================================================
print("\n[10] Module with Iterators Tests")

-- Test 10.1: Custom iterator module
package.preload.iterators = function()
    return {
        range = function(n)
            local i = 0
            return function()
                i = i + 1
                if i <= n then
                    return i
                end
            end
        end,
        
        reverse = function(arr)
            local i = #arr + 1
            return function()
                i = i - 1
                if i >= 1 then
                    return i, arr[i]
                end
            end
        end
    }
end

local iterators = require("iterators")

local sum = 0
for i in iterators.range(5) do
    sum = sum + i
end
test("iterator range sum", sum == 15)

local rev_arr = {10, 20, 30}
local rev_results = {}
for idx, val in iterators.reverse(rev_arr) do
    table.insert(rev_results, val)
end
test("iterator reverse", rev_results[1] == 30 and rev_results[3] == 10)

-- ============================================================================
-- [11] Module Hygiene Tests
-- ============================================================================
print("\n[11] Module Hygiene Tests")

-- Test 11.1: Module doesn't pollute globals
local before_globals = 0
for k, v in pairs(_G) do
    before_globals = before_globals + 1
end

package.preload.clean_mod = function()
    local private = "hidden"
    local function helper() return private end
    return { get = helper }
end

local clean = require("clean_mod")
test("clean module works", clean.get() == "hidden")

local after_globals = 0
for k, v in pairs(_G) do
    after_globals = after_globals + 1
end
test("no global pollution", after_globals == before_globals)

-- ============================================================================
-- [12] Multiple Module Versions Tests
-- ============================================================================
print("\n[12] Multiple Module Versions Tests")

-- Test 12.1: Version 1
package.preload.versioned_v1 = function()
    return {
        version = 1,
        greet = function(name) return "Hello, " .. name end
    }
end

-- Test 12.2: Version 2
package.preload.versioned_v2 = function()
    return {
        version = 2,
        greet = function(name) return "Hi, " .. name .. "!" end
    }
end

local v1 = require("versioned_v1")
local v2 = require("versioned_v2")

test("version 1 loaded", v1.version == 1)
test("version 2 loaded", v2.version == 2)
test("version 1 greet", v1.greet("Alice") == "Hello, Alice")
test("version 2 greet", v2.greet("Bob") == "Hi, Bob!")
test("versions independent", v1 ~= v2)

-- ============================================================================
-- [13] Module with Table Methods Tests
-- ============================================================================
print("\n[13] Module with Table Methods Tests")

-- Test 13.1: Module returning table with methods
package.preload.table_methods = function()
    return {
        data = {1, 2, 3},
        
        push = function(self, val)
            table.insert(self.data, val)
        end,
        
        pop = function(self)
            return table.remove(self.data)
        end,
        
        size = function(self)
            return #self.data
        end
    }
end

local tm = require("table_methods")
test("table methods initial size", tm:size() == 3)
tm:push(4)
tm:push(5)
test("table methods after push", tm:size() == 5)
local popped = tm:pop()
test("table methods pop value", popped == 5)
test("table methods after pop", tm:size() == 4)

-- ============================================================================
-- [14] Module with Colon Syntax Tests
-- ============================================================================
print("\n[14] Module with Colon Syntax Tests")

-- Test 14.1: Module designed for colon calls
package.preload.object_mod = function()
    local Object = {}
    Object.__index = Object
    
    function Object:new(value)
        local o = setmetatable({}, self)
        o.value = value
        return o
    end
    
    function Object:getValue()
        return self.value
    end
    
    function Object:setValue(v)
        self.value = v
    end
    
    return Object
end

local Object = require("object_mod")
local obj = Object:new(42)
test("colon syntax new", obj ~= nil)
test("colon syntax getValue", obj:getValue() == 42)
obj:setValue(100)
test("colon syntax setValue", obj:getValue() == 100)

-- ============================================================================
-- [15] Module with Complex Logic Tests
-- ============================================================================
print("\n[15] Module with Complex Logic Tests")

-- Test 15.1: State machine module
package.preload.state_machine = function()
    local state = "idle"
    local transitions = {
        idle = { start = "running" },
        running = { stop = "idle", pause = "paused" },
        paused = { resume = "running", stop = "idle" }
    }
    
    return {
        getState = function() return state end,
        
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

local sm = require("state_machine")
test("state machine initial", sm.getState() == "idle")
test("state machine start", sm.transition("start") == true)
test("state machine running", sm.getState() == "running")
test("state machine pause", sm.transition("pause") == true)
test("state machine paused", sm.getState() == "paused")
test("state machine invalid", sm.transition("invalid") == false)

-- ============================================================================
-- [16] Module Data Sharing Tests
-- ============================================================================
print("\n[16] Module Data Sharing Tests")

-- Test 16.1: Shared data module
package.preload.shared_data = function()
    local shared = { counter = 0, items = {} }
    
    return {
        increment = function()
            shared.counter = shared.counter + 1
            return shared.counter
        end,
        
        getCounter = function()
            return shared.counter
        end,
        
        addItem = function(item)
            table.insert(shared.items, item)
        end,
        
        getItems = function()
            return shared.items
        end
    }
end

local sd1 = require("shared_data")
local sd2 = require("shared_data")

test("shared data same module", sd1 == sd2)
sd1.increment()
test("shared data counter via sd1", sd1.getCounter() == 1)
test("shared data counter via sd2", sd2.getCounter() == 1)
sd2.increment()
test("shared data counter updated", sd1.getCounter() == 2)

sd1.addItem("first")
sd2.addItem("second")
local items = sd1.getItems()
test("shared items count", #items == 2)
test("shared items content", items[1] == "first" and items[2] == "second")

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
    print("\n*** ALL ADVANCED REQUIRE TESTS PASSED ***")
else
    print("\n*** SOME TESTS FAILED ***")
end
