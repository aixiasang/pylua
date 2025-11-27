-- test_coroutine_yield.lua
-- 测试协程 yield 功能

print("=== Coroutine Yield Test ===")

-- Test 1: 简单 yield
print("\n[1] Simple Yield")
local co1 = coroutine.create(function()
    print("  co1: before yield")
    coroutine.yield(1)
    print("  co1: after yield")
    return 2
end)

local ok1, v1 = coroutine.resume(co1)
print("  first resume:", ok1, v1)

local ok2, v2 = coroutine.resume(co1)
print("  second resume:", ok2, v2)

print("  status:", coroutine.status(co1))

-- Test 2: 多次 yield
print("\n[2] Multiple Yields")
local co2 = coroutine.create(function()
    for i = 1, 3 do
        coroutine.yield(i * 10)
    end
    return 100
end)

for i = 1, 4 do
    local ok, val = coroutine.resume(co2)
    print("  resume " .. i .. ":", ok, val)
end

-- Test 3: yield 带参数返回
print("\n[3] Yield with Resume Args")
local co3 = coroutine.create(function(x)
    local a = coroutine.yield(x + 1)
    local b = coroutine.yield(a + 1)
    return b + 1
end)

local ok3a, v3a = coroutine.resume(co3, 10)
print("  first:", ok3a, v3a)

local ok3b, v3b = coroutine.resume(co3, 20)
print("  second:", ok3b, v3b)

local ok3c, v3c = coroutine.resume(co3, 30)
print("  third:", ok3c, v3c)

print("\n=== Done ===")
