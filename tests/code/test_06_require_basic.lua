-- ============================================================================
-- Test 06: Require and Module System - Basic Tests
-- 测试require和模块系统的基础功能
-- ============================================================================

print("=== Test 06: Require and Module System - Basic ===")

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
-- [1] Package Table Tests
-- ============================================================================
print("\n[1] Package Table Tests")

-- Test 1.1: package exists
test("package exists", package ~= nil)

-- Test 1.2: package.loaded exists
test("package.loaded exists", package.loaded ~= nil)

-- Test 1.3: package.preload exists
test("package.preload exists", package.preload ~= nil)

-- Test 1.4: package.searchers exists
test("package.searchers exists", package.searchers ~= nil)

-- Test 1.5: package.path exists
test("package.path exists", package.path ~= nil)

-- Test 1.6: package.path is string
test("package.path is string", type(package.path) == "string")

-- Test 1.7: package.cpath exists
test("package.cpath exists", package.cpath ~= nil)

-- Test 1.8: package table type
test("package is table", type(package) == "table")

-- Test 1.9: package.loaded is table
test("package.loaded is table", type(package.loaded) == "table")

-- Test 1.10: package.preload is table
test("package.preload is table", type(package.preload) == "table")

-- ============================================================================
-- [2] Require Function Tests
-- ============================================================================
print("\n[2] Require Function Tests")

-- Test 2.1: require exists
test("require exists", require ~= nil)

-- Test 2.2: require is function
test("require is function", type(require) == "function")

-- Test 2.3: require can be called
local status, result = pcall(function() 
    return require
end)
test("require callable", status)

-- ============================================================================
-- [3] Package.searchers Tests
-- ============================================================================
print("\n[3] Package.searchers Tests")

-- Test 3.1: searchers is table
test("searchers is table", type(package.searchers) == "table")

-- Test 3.2: searchers[1] exists
test("searchers[1] exists", package.searchers[1] ~= nil)

-- Test 3.3: searchers[1] is function
test("searchers[1] is function", type(package.searchers[1]) == "function")

-- Test 3.4: searchers[2] exists
test("searchers[2] exists", package.searchers[2] ~= nil)

-- Test 3.5: searchers[2] is function
test("searchers[2] is function", type(package.searchers[2]) == "function")

-- Test 3.6: searchers length >= 2
local searcher_count = 0
for i = 1, 10 do
    if package.searchers[i] ~= nil then
        searcher_count = searcher_count + 1
    else
        break
    end
end
test("searchers count >= 2", searcher_count >= 2)

-- ============================================================================
-- [4] Package.loaded Cache Tests
-- ============================================================================
print("\n[4] Package.loaded Cache Tests")

-- Test 4.1: Can add to package.loaded
package.loaded.test_module_1 = { version = "1.0" }
test("can add to loaded", package.loaded.test_module_1 ~= nil)

-- Test 4.2: Can retrieve from package.loaded
test("can retrieve from loaded", package.loaded.test_module_1.version == "1.0")

-- Test 4.3: Can modify package.loaded
package.loaded.test_module_1.version = "2.0"
test("can modify loaded", package.loaded.test_module_1.version == "2.0")

-- Test 4.4: Can remove from package.loaded
package.loaded.test_module_1 = nil
test("can remove from loaded", package.loaded.test_module_1 == nil)

-- ============================================================================
-- [5] Package.preload Tests
-- ============================================================================
print("\n[5] Package.preload Tests")

-- Test 5.1: Can add to package.preload
package.preload.test_preload_1 = function()
    return { name = "preloaded" }
end
test("can add to preload", package.preload.test_preload_1 ~= nil)

-- Test 5.2: preload function is callable
test("preload function callable", type(package.preload.test_preload_1) == "function")

-- Test 5.3: Can call preload function
local preload_result = package.preload.test_preload_1()
test("can call preload", preload_result.name == "preloaded")

-- Test 5.4: Can remove from preload
package.preload.test_preload_1 = nil
test("can remove from preload", package.preload.test_preload_1 == nil)

-- ============================================================================
-- [6] Module Return Value Tests
-- ============================================================================
print("\n[6] Module Return Value Tests")

-- Test 6.1: Module returning table
package.preload.module_table = function()
    return { type = "table", value = 42 }
end
local mod_table = require("module_table")
test("module returns table", type(mod_table) == "table")
test("module table content", mod_table.value == 42)

-- Test 6.2: Module returning function
package.preload.module_func = function()
    return function(x) return x * 2 end
end
local mod_func = require("module_func")
test("module returns function", type(mod_func) == "function")
test("module function works", mod_func(5) == 10)

-- Test 6.3: Module returning number
package.preload.module_number = function()
    return 123
end
local mod_num = require("module_number")
test("module returns number", mod_num == 123)

-- Test 6.4: Module returning string
package.preload.module_string = function()
    return "hello"
end
local mod_str = require("module_string")
test("module returns string", mod_str == "hello")

-- Test 6.5: Module returning boolean
package.preload.module_bool = function()
    return true
end
local mod_bool = require("module_bool")
test("module returns boolean", mod_bool == true)

-- ============================================================================
-- [7] Module Caching Tests
-- ============================================================================
print("\n[7] Module Caching Tests")

-- Test 7.1: Module loaded once
local load_count = 0
package.preload.cache_test = function()
    load_count = load_count + 1
    return { count = load_count }
end
local first = require("cache_test")
local second = require("cache_test")
test("module loaded once", load_count == 1)
test("same module instance", first == second)
test("cached count correct", first.count == 1)

-- Test 7.2: Cache cleared on nil
package.loaded.cache_test = nil
local third = require("cache_test")
test("reload after cache clear", load_count == 2)
test("new instance after clear", first ~= third)

-- ============================================================================
-- [8] Multiple Module Tests
-- ============================================================================
print("\n[8] Multiple Module Tests")

-- Test 8.1: Load multiple modules
package.preload.mod_a = function() return { name = "A" } end
package.preload.mod_b = function() return { name = "B" } end
package.preload.mod_c = function() return { name = "C" } end

local ma = require("mod_a")
local mb = require("mod_b")
local mc = require("mod_c")

test("module A loaded", ma.name == "A")
test("module B loaded", mb.name == "B")
test("module C loaded", mc.name == "C")
test("modules independent", ma ~= mb and mb ~= mc)

-- Test 8.2: Modules in package.loaded
test("mod_a in loaded", package.loaded.mod_a == ma)
test("mod_b in loaded", package.loaded.mod_b == mb)
test("mod_c in loaded", package.loaded.mod_c == mc)

-- ============================================================================
-- [9] Module Interdependency Tests
-- ============================================================================
print("\n[9] Module Interdependency Tests")

-- Test 9.1: Module requiring another module
package.preload.dep_base = function()
    return { value = 100 }
end

package.preload.dep_user = function()
    local base = require("dep_base")
    return { base_value = base.value, own_value = 200 }
end

local dep_user = require("dep_user")
test("dependent module loads base", dep_user.base_value == 100)
test("dependent module has own data", dep_user.own_value == 200)

-- Test 9.2: Both modules cached
test("base module cached", package.loaded.dep_base ~= nil)
test("user module cached", package.loaded.dep_user ~= nil)

-- ============================================================================
-- [10] Module with Local State Tests
-- ============================================================================
print("\n[10] Module with Local State Tests")

-- Test 10.1: Module with counter
package.preload.stateful = function()
    local counter = 0
    return {
        increment = function() counter = counter + 1; return counter end,
        get = function() return counter end
    }
end

local state1 = require("stateful")
test("initial state", state1.get() == 0)
test("increment works", state1.increment() == 1)
test("state persists", state1.get() == 1)

local state2 = require("stateful")
test("shared state", state2.get() == 1)
test("same module", state1 == state2)

-- ============================================================================
-- [11] Module Returning nil Tests
-- ============================================================================
print("\n[11] Module Returning nil Tests")

-- Test 11.1: Module returning nil uses true
package.preload.nil_module = function()
    return nil
end
local nil_mod = require("nil_module")
test("nil module returns true", nil_mod == true)
test("nil module cached as true", package.loaded.nil_module == true)

-- ============================================================================
-- [12] Complex Module Pattern Tests
-- ============================================================================
print("\n[12] Complex Module Pattern Tests")

-- Test 12.1: OOP module pattern
package.preload.class_module = function()
    local Class = {}
    Class.__index = Class
    
    function Class.new(value)
        local self = setmetatable({}, Class)
        self.value = value
        return self
    end
    
    function Class:get()
        return self.value
    end
    
    function Class:set(v)
        self.value = v
    end
    
    return Class
end

local ClassMod = require("class_module")
local obj1 = ClassMod.new(42)
local obj2 = ClassMod.new(99)

test("OOP module creates objects", obj1 ~= nil and obj2 ~= nil)
test("OOP object 1 value", obj1:get() == 42)
test("OOP object 2 value", obj2:get() == 99)

obj1:set(100)
test("OOP object 1 modified", obj1:get() == 100)
test("OOP object 2 unchanged", obj2:get() == 99)

-- Test 12.2: Factory module pattern
package.preload.factory = function()
    return {
        create = function(type_name, value)
            if type_name == "number" then
                return { type = "number", val = value }
            elseif type_name == "string" then
                return { type = "string", val = tostring(value) }
            else
                return { type = "unknown", val = nil }
            end
        end
    }
end

local factory = require("factory")
local num_obj = factory.create("number", 123)
local str_obj = factory.create("string", 456)

test("factory creates number", num_obj.type == "number" and num_obj.val == 123)
test("factory creates string", str_obj.type == "string" and str_obj.val == "456")

-- ============================================================================
-- [13] Package Path Manipulation Tests
-- ============================================================================
print("\n[13] Package Path Manipulation Tests")

-- Test 13.1: Can read package.path
local path = package.path
test("can read path", type(path) == "string")

-- Test 13.2: Can modify package.path
local old_path = package.path
package.path = "./custom/?.lua;" .. package.path
test("can modify path", package.path ~= old_path)

-- Test 13.3: Path contains patterns
test("path contains ?", string.find(package.path, "?", 1, true) ~= nil)

-- Restore path
package.path = old_path

-- ============================================================================
-- [14] Module Name with Special Characters Tests
-- ============================================================================
print("\n[14] Module Name Tests")

-- Test 14.1: Simple name
package.preload.simple = function() return { name = "simple" } end
local simple = require("simple")
test("simple name works", simple.name == "simple")

-- Test 14.2: Name with underscore
package.preload.my_module = function() return { name = "underscore" } end
local underscore = require("my_module")
test("underscore name works", underscore.name == "underscore")

-- Test 14.3: Name with number
package.preload.module123 = function() return { name = "number" } end
local numbered = require("module123")
test("numbered name works", numbered.name == "number")

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
    print("\n*** ALL REQUIRE TESTS PASSED ***")
else
    print("\n*** SOME TESTS FAILED ***")
end
