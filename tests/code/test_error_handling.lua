-- test_error_handling.lua
-- Error handling and protected calls tests

print("=== Error Handling Tests ===")

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
-- 1. pcall Basic Tests
-- ============================================================================
print("\n--- pcall Basic ---")

-- Successful call
local ok, result = pcall(function() return 42 end)
test("pcall success", ok == true and result == 42)

-- Multiple returns
local ok, a, b, c = pcall(function() return 1, 2, 3 end)
test("pcall multiple returns", ok and a == 1 and b == 2 and c == 3)

-- Error in function
local ok, err = pcall(function() error("test error") end)
test("pcall catches error", ok == false)

-- nil error
ok, err = pcall(function() error(nil) end)
test("pcall nil error", ok == false)

-- ============================================================================
-- 2. pcall with Arguments
-- ============================================================================
print("\n--- pcall with Arguments ---")

local function add(a, b) return a + b end
ok, result = pcall(add, 10, 20)
test("pcall with args", ok and result == 30)

local function greet(name) return "Hello, " .. name end
ok, result = pcall(greet, "World")
test("pcall string arg", ok and result == "Hello, World")

-- ============================================================================
-- 3. xpcall Basic Tests
-- ============================================================================
print("\n--- xpcall Basic ---")

local handler_called = false
local function error_handler(err)
    handler_called = true
    return "handled: " .. tostring(err)
end

-- Successful call
handler_called = false
ok, result = xpcall(function() return 42 end, error_handler)
test("xpcall success", ok and result == 42 and not handler_called)

-- Error with handler
handler_called = false
ok, result = xpcall(function() error("oops") end, error_handler)
test("xpcall error caught", ok == false and handler_called)

-- ============================================================================
-- 4. assert Tests
-- ============================================================================
print("\n--- assert Tests ---")

-- True assertion
result = assert(true)
test("assert true", result == true)

-- Value assertion
result = assert(42)
test("assert value", result == 42)

-- String assertion
result = assert("hello")
test("assert string", result == "hello")

-- Multiple values
local a, b = assert(1, 2)
test("assert multiple", a == 1 and b == 2)

-- False assertion (caught by pcall)
ok, err = pcall(function() assert(false, "assertion failed") end)
test("assert false", ok == false)

-- nil assertion
ok, err = pcall(function() assert(nil) end)
test("assert nil", ok == false)

-- ============================================================================
-- 5. error Function
-- ============================================================================
print("\n--- error Function ---")

-- String error
ok, err = pcall(function() error("my error") end)
test("error string", ok == false)

-- Number error
ok, err = pcall(function() error(42) end)
test("error number", ok == false)

-- Table error
local err_table = {msg = "error"}
ok, err = pcall(function() error(err_table) end)
test("error table", ok == false)

-- ============================================================================
-- 6. Nested pcall
-- ============================================================================
print("\n--- Nested pcall ---")

ok, result = pcall(function()
    local inner_ok, inner_result = pcall(function()
        return 100
    end)
    return inner_ok and inner_result
end)
test("nested pcall success", ok and result == 100)

ok, result = pcall(function()
    local inner_ok = pcall(function()
        error("inner error")
    end)
    return inner_ok
end)
test("nested pcall inner error", ok and result == false)

-- ============================================================================
-- 7. Error Propagation
-- ============================================================================
print("\n--- Error Propagation ---")

local function level3() error("deep error") end
local function level2() level3() end
local function level1() level2() end

ok, err = pcall(level1)
test("error propagates", ok == false)

-- ============================================================================
-- 8. pcall with Methods
-- ============================================================================
print("\n--- pcall with Methods ---")

local obj = {value = 10}
function obj:get() return self.value end
function obj:set(v) self.value = v end

ok, result = pcall(obj.get, obj)
test("pcall method", ok and result == 10)

ok = pcall(obj.set, obj, 20)
test("pcall method set", ok and obj.value == 20)

-- ============================================================================
-- 9. Cleanup Pattern
-- ============================================================================
print("\n--- Cleanup Pattern ---")

local cleanup_called = false
local function with_cleanup(func)
    local ok, err = pcall(func)
    cleanup_called = true
    return ok, err
end

cleanup_called = false
ok, err = with_cleanup(function() return 42 end)
test("cleanup success", ok and cleanup_called)

cleanup_called = false
ok, err = with_cleanup(function() error("fail") end)
test("cleanup on error", not ok and cleanup_called)

-- ============================================================================
-- 10. Type Errors
-- ============================================================================
print("\n--- Type Errors ---")

-- Arithmetic on nil
ok = pcall(function() return nil + 1 end)
test("nil arithmetic", ok == false)

-- Call non-function
ok = pcall(function() local t = {} return t() end)
test("call non-function", ok == false)

-- Index nil
ok = pcall(function() local x = nil return x.y end)
test("index nil", ok == false)

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
