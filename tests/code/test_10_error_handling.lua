-- ============================================================================
-- Test 10: Error Handling and Protected Calls
-- 测试错误处理、pcall和xpcall
-- ============================================================================

print("=== Test 10: Error Handling ===")

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
-- [1] Basic pcall Tests
-- ============================================================================
print("\n[1] Basic pcall Tests")

-- Test 1.1: pcall with successful function
local function safe_function()
    return 42
end

local status, result = pcall(safe_function)
test("pcall success status", status == true)
test("pcall success result", result == 42)

-- Test 1.2: pcall with error
local function error_function()
    error("test error")
end

local status2, err = pcall(error_function)
test("pcall error status", status2 == false)
test("pcall error message", type(err) == "string")

-- Test 1.3: pcall with arguments
local function add(a, b)
    return a + b
end

local status3, result3 = pcall(add, 10, 20)
test("pcall with args status", status3 == true)
test("pcall with args result", result3 == 30)

-- ============================================================================
-- [2] pcall with Multiple Return Values Tests
-- ============================================================================
print("\n[2] pcall with Multiple Return Values Tests")

-- Test 2.1: Multiple returns on success
local function multi_return()
    return 1, 2, 3
end

local s, r1, r2, r3 = pcall(multi_return)
test("multi return status", s == true)
test("multi return 1", r1 == 1)
test("multi return 2", r2 == 2)
test("multi return 3", r3 == 3)

-- Test 2.2: No return values
local function no_return()
end

local s2, r = pcall(no_return)
test("no return status", s2 == true)
test("no return result", r == nil)

-- ============================================================================
-- [3] pcall Error Types Tests
-- ============================================================================
print("\n[3] pcall Error Types Tests")

-- Test 3.1: String error
local s1, e1 = pcall(function() error("string error") end)
test("string error caught", s1 == false)

-- Test 3.2: Number error
local s2, e2 = pcall(function() error(123) end)
test("number error caught", s2 == false)

-- Test 3.3: Table error
local s3, e3 = pcall(function() error({msg = "table error"}) end)
test("table error caught", s3 == false)

-- Test 3.4: Runtime error (type error)
local s4, e4 = pcall(function()
    local x = nil
    return x + 1  -- attempt to perform arithmetic on nil
end)
test("runtime error caught", s4 == false)

-- ============================================================================
-- [4] Nested pcall Tests
-- ============================================================================
print("\n[4] Nested pcall Tests")

-- Test 4.1: pcall inside pcall
local function outer_pcall()
    local inner_status, inner_result = pcall(function()
        return 100
    end)
    
    if inner_status then
        return inner_result * 2
    end
    return 0
end

local s, r = pcall(outer_pcall)
test("nested pcall status", s == true)
test("nested pcall result", r == 200)

-- Test 4.2: Error in nested pcall
local function outer_with_error()
    local inner_status, inner_err = pcall(function()
        error("inner error")
    end)
    
    if not inner_status then
        return "caught: " .. tostring(inner_err)
    end
    return "no error"
end

local s2, r2 = pcall(outer_with_error)
test("nested error caught status", s2 == true)
test("nested error caught result", type(r2) == "string")

-- ============================================================================
-- [5] pcall with Closures Tests
-- ============================================================================
print("\n[5] pcall with Closures Tests")

-- Test 5.1: pcall with closure
local function make_divider(denominator)
    return function(numerator)
        if denominator == 0 then
            error("division by zero")
        end
        return numerator / denominator
    end
end

local div_by_2 = make_divider(2)
local s1, r1 = pcall(div_by_2, 10)
test("closure pcall success", s1 == true and r1 == 5)

local div_by_0 = make_divider(0)
local s2, e2 = pcall(div_by_0, 10)
test("closure pcall error", s2 == false)

-- ============================================================================
-- [6] pcall State Preservation Tests
-- ============================================================================
print("\n[6] pcall State Preservation Tests")

-- Test 6.1: Local variables preserved after error
local counter = 0

local function increment_and_error()
    counter = counter + 1
    error("test")
end

local s1 = pcall(increment_and_error)
test("state after error 1", counter == 1)

local s2 = pcall(increment_and_error)
test("state after error 2", counter == 2)

-- ============================================================================
-- [7] pcall with Tables Tests
-- ============================================================================
print("\n[7] pcall with Tables Tests")

-- Test 7.1: Table method call in pcall
local obj = {
    value = 10,
    get = function(self) return self.value end,
    set = function(self, v) self.value = v end,
    error_method = function(self) error("method error") end
}

local s1, r1 = pcall(obj.get, obj)
test("table method pcall", s1 == true and r1 == 10)

local s2 = pcall(obj.error_method, obj)
test("table method error", s2 == false)

-- ============================================================================
-- [8] pcall with Variadic Functions Tests
-- ============================================================================
print("\n[8] pcall with Variadic Functions Tests")

-- Test 8.1: Variadic function in pcall
local function sum(...)
    local total = 0
    for i, v in ipairs({...}) do
        total = total + v
    end
    return total
end

local s, r = pcall(sum, 1, 2, 3, 4, 5)
test("variadic pcall status", s == true)
test("variadic pcall result", r == 15)

-- Test 8.2: Variadic with error
local function check_all_positive(...)
    for i, v in ipairs({...}) do
        if v < 0 then
            error("negative value")
        end
    end
    return true
end

local s1 = pcall(check_all_positive, 1, 2, 3)
test("variadic check pass", s1 == true)

local s2 = pcall(check_all_positive, 1, -2, 3)
test("variadic check fail", s2 == false)

-- ============================================================================
-- [9] Error Message Handling Tests
-- ============================================================================
print("\n[9] Error Message Handling Tests")

-- Test 9.1: Custom error messages
local function validate_age(age)
    if type(age) ~= "number" then
        error("age must be a number")
    end
    if age < 0 then
        error("age cannot be negative")
    end
    if age > 150 then
        error("age too large")
    end
    return true
end

local s1, e1 = pcall(validate_age, "abc")
test("type error caught", s1 == false)

local s2, e2 = pcall(validate_age, -5)
test("negative error caught", s2 == false)

local s3, r3 = pcall(validate_age, 25)
test("valid age", s3 == true)

-- ============================================================================
-- [10] pcall with Metatables Tests
-- ============================================================================
print("\n[10] pcall with Metatables Tests")

-- Test 10.1: Metamethod errors
local t1 = {}
local t2 = {}

-- No __add metamethod
local s1 = pcall(function() return t1 + t2 end)
test("metamethod missing error", s1 == false)

-- With __add metamethod
setmetatable(t1, {
    __add = function(a, b) return {result = "added"} end
})
setmetatable(t2, getmetatable(t1))

local s2, r2 = pcall(function() return t1 + t2 end)
test("metamethod success", s2 == true)
test("metamethod result", r2.result == "added")

-- ============================================================================
-- [11] pcall with Type Errors Tests
-- ============================================================================
print("\n[11] pcall with Type Errors Tests")

-- Test 11.1: Calling non-function
local s1 = pcall(function()
    local x = 5
    x()  -- attempt to call a number
end)
test("call number error", s1 == false)

-- Test 11.2: Indexing non-table
local s2 = pcall(function()
    local x = 5
    return x.field  -- attempt to index a number
end)
test("index number error", s2 == false)

-- Test 11.3: Arithmetic on non-number
local s3 = pcall(function()
    return "abc" + 5
end)
test("arithmetic string error", s3 == false)

-- ============================================================================
-- [12] pcall Return Value Propagation Tests
-- ============================================================================
print("\n[12] pcall Return Value Propagation Tests")

-- Test 12.1: nil return
local function return_nil()
    return nil
end

local s1, r1 = pcall(return_nil)
test("nil return status", s1 == true)
test("nil return value", r1 == nil)

-- Test 12.2: false return
local function return_false()
    return false
end

local s2, r2 = pcall(return_false)
test("false return status", s2 == true)
test("false return value", r2 == false)

-- Test 12.3: zero return
local function return_zero()
    return 0
end

local s3, r3 = pcall(return_zero)
test("zero return status", s3 == true)
test("zero return value", r3 == 0)

-- ============================================================================
-- [13] Complex Error Scenarios Tests
-- ============================================================================
print("\n[13] Complex Error Scenarios Tests")

-- Test 13.1: Error in loop
local function process_array(arr)
    local results = {}
    for i, v in ipairs(arr) do
        if v < 0 then
            error("negative at index " .. i)
        end
        table.insert(results, v * 2)
    end
    return results
end

local s1, r1 = pcall(process_array, {1, 2, 3})
test("array process success", s1 == true and #r1 == 3)

local s2, e2 = pcall(process_array, {1, -2, 3})
test("array process error", s2 == false)

-- Test 13.2: Error in recursive function
local function factorial(n)
    if type(n) ~= "number" then
        error("not a number")
    end
    if n < 0 then
        error("negative factorial")
    end
    if n == 0 then return 1 end
    return n * factorial(n - 1)
end

local s3, r3 = pcall(factorial, 5)
test("factorial success", s3 == true and r3 == 120)

local s4 = pcall(factorial, -5)
test("factorial error", s4 == false)

-- ============================================================================
-- [14] pcall with assert Tests
-- ============================================================================
print("\n[14] pcall with assert Tests")

-- Test 14.1: assert in pcall
local function check_positive(x)
    assert(x > 0, "must be positive")
    return x * 2
end

local s1, r1 = pcall(check_positive, 5)
test("assert pass", s1 == true and r1 == 10)

local s2, e2 = pcall(check_positive, -5)
test("assert fail", s2 == false)

-- Test 14.2: assert with custom message
local function validate_string(s)
    assert(type(s) == "string", "expected string, got " .. type(s))
    return #s
end

local s3, r3 = pcall(validate_string, "hello")
test("assert string pass", s3 == true and r3 == 5)

local s4 = pcall(validate_string, 123)
test("assert string fail", s4 == false)

-- ============================================================================
-- [15] Edge Cases Tests
-- ============================================================================
print("\n[15] Edge Cases Tests")

-- Test 15.1: Empty function
local s1, r1 = pcall(function() end)
test("empty function", s1 == true)

-- Test 15.2: Immediate error
local s2 = pcall(function() error("immediate") end)
test("immediate error", s2 == false)

-- Test 15.3: Error with nil message
local s3 = pcall(function() error(nil) end)
test("nil error message", s3 == false)

-- Test 15.4: Very long error message
local long_msg = string.rep("x", 1000)
local s4 = pcall(function() error(long_msg) end)
test("long error message", s4 == false)

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
    print("\n*** ALL ERROR HANDLING TESTS PASSED ***")
else
    print("\n*** SOME TESTS FAILED ***")
end
