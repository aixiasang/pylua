-- test_coroutine_advanced.lua
-- 高级协程测试 - 验证 yield/resume 和 wrap 功能

print("=== Advanced Coroutine Tests ===")

local passed = 0
local total = 0

local function test(name, cond)
    total = total + 1
    if cond then
        passed = passed + 1
        print("  PASS: " .. name)
    else
        print("  FAIL: " .. name)
    end
end

-- [1] 多次 yield 测试
print("\n[1] Multiple Yields")
local co1 = coroutine.create(function()
    local a = coroutine.yield(1)
    local b = coroutine.yield(a + 1)
    local c = coroutine.yield(b + 1)
    return c + 1
end)

local ok1, v1 = coroutine.resume(co1)
test("first yield", ok1 and v1 == 1)

local ok2, v2 = coroutine.resume(co1, 10)
test("second yield with arg", ok2 and v2 == 11)

local ok3, v3 = coroutine.resume(co1, 20)
test("third yield with arg", ok3 and v3 == 21)

local ok4, v4 = coroutine.resume(co1, 30)
test("final return", ok4 and v4 == 31)

test("status after return", coroutine.status(co1) == "dead")

-- [2] coroutine.wrap 测试
print("\n[2] coroutine.wrap")
local wrap_fn = coroutine.wrap(function(x)
    local y = coroutine.yield(x * 2)
    return y * 3
end)

local r1 = wrap_fn(5)
test("wrap first call", r1 == 10)

local r2 = wrap_fn(7)
test("wrap second call", r2 == 21)

-- [3] 嵌套协程测试
print("\n[3] Nested Coroutines")
local outer = coroutine.create(function()
    local inner = coroutine.create(function()
        coroutine.yield("inner")
        return "inner_done"
    end)
    
    local ok, v = coroutine.resume(inner)
    coroutine.yield("outer:" .. v)
    
    ok, v = coroutine.resume(inner)
    return "outer:" .. v
end)

local ok_o1, v_o1 = coroutine.resume(outer)
test("nested first", ok_o1 and v_o1 == "outer:inner")

local ok_o2, v_o2 = coroutine.resume(outer)
test("nested second", ok_o2 and v_o2 == "outer:inner_done")

-- [4] 协程状态转换测试
print("\n[4] Status Transitions")
local co_status = coroutine.create(function()
    coroutine.yield()
    return "done"
end)

test("initial status", coroutine.status(co_status) == "suspended")

coroutine.resume(co_status)
test("after first resume", coroutine.status(co_status) == "suspended")

coroutine.resume(co_status)
test("after final resume", coroutine.status(co_status) == "dead")

-- [5] 带错误的协程测试
print("\n[5] Error Handling")
local co_err = coroutine.create(function()
    error("test error")
end)

local ok_err, msg_err = coroutine.resume(co_err)
test("error returns false", ok_err == false)
test("error has message", msg_err ~= nil)
test("dead after error", coroutine.status(co_err) == "dead")

-- [6] isyieldable 测试
print("\n[6] isyieldable")
local in_main = coroutine.isyieldable()
test("main not yieldable", in_main == false)

local co_yield = coroutine.create(function()
    local y = coroutine.isyieldable()
    coroutine.yield(y)
end)

local ok_y, is_y = coroutine.resume(co_yield)
test("inside coroutine yieldable", ok_y and is_y == true)

-- [7] running 测试
print("\n[7] coroutine.running")
local main_co, is_main = coroutine.running()
test("main thread flag", is_main == true)

local co_run = coroutine.create(function()
    local co, is_m = coroutine.running()
    coroutine.yield(co ~= nil, is_m)
end)

local ok_r, has_co, is_m_inside = coroutine.resume(co_run)
test("inside has thread", ok_r and has_co == true)
test("inside not main", is_m_inside == false)

-- 总结
print("\n" .. string.rep("=", 50))
print("ADVANCED COROUTINE SUMMARY")
print(string.rep("=", 50))
print("Passed: " .. passed .. "/" .. total)
if passed == total then
    print("*** ALL TESTS PASSED ***")
else
    print("*** " .. (total - passed) .. " TESTS FAILED ***")
end
