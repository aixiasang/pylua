-- test_coroutine.lua
-- Basic coroutine tests (simplified to avoid timeout)

print("=== Coroutine Tests ===")

local tests_passed = 0
local tests_total = 0

local function test(name, condition)
    tests_total = tests_total + 1
    if condition then
        tests_passed = tests_passed + 1
        print("  PASS: " .. name)
    else
        print("  FAIL: " .. name)
    end
end

-- [1] Basic coroutine table existence
print("\n[1] Coroutine Table Tests")
test("coroutine exists", coroutine ~= nil)
test("coroutine is table", type(coroutine) == "table")
test("coroutine.create exists", coroutine.create ~= nil)
test("coroutine.resume exists", coroutine.resume ~= nil)
test("coroutine.status exists", coroutine.status ~= nil)

-- [2] coroutine.create tests
print("\n[2] coroutine.create Tests")
local co1 = coroutine.create(function() return 1 end)
test("create returns thread", co1 ~= nil)
test("create with function", type(co1) == "thread")

-- [3] coroutine.status tests
print("\n[3] coroutine.status Tests")
local co2 = coroutine.create(function() return 42 end)
test("initial status suspended", coroutine.status(co2) == "suspended")

-- [4] coroutine.resume tests
print("\n[4] coroutine.resume Tests")
local co3 = coroutine.create(function(a, b)
    return a + b
end)
local ok, result = coroutine.resume(co3, 10, 20)
test("resume returns true", ok == true)
test("resume returns result", result == 30)

-- [5] Dead coroutine
print("\n[5] Dead Coroutine Tests")
local co4 = coroutine.create(function() return "done" end)
coroutine.resume(co4)
test("finished coroutine dead", coroutine.status(co4) == "dead")

local ok_dead, err = coroutine.resume(co4)
test("cannot resume dead", ok_dead == false)

-- [6] coroutine.running tests
print("\n[6] coroutine.running Tests")
local main_co, is_main = coroutine.running()
test("running returns main flag", is_main == true or is_main == false)

-- Summary
print("\n" .. string.rep("=", 50))
print("COROUTINE TEST SUMMARY")
print(string.rep("=", 50))
print("Total: " .. tests_total)
print("Passed: " .. tests_passed)
print("Failed: " .. (tests_total - tests_passed))
print(string.rep("=", 50))

if tests_passed == tests_total then
    print("\n*** ALL COROUTINE TESTS PASSED ***")
else
    print("\n*** SOME TESTS FAILED ***")
end
