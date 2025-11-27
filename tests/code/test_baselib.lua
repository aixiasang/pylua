-- test_baselib.lua
-- Test basic library functions

print("=== tostring tests ===")
print(tostring(nil))
print(tostring(true))
print(tostring(false))
print(tostring(42))
print(tostring(3.14))
print(tostring("hello"))

print("=== type tests ===")
print(type(nil))
print(type(true))
print(type(42))
print(type(3.14))
print(type("hello"))
print(type({}))
print(type(print))

print("=== tonumber tests ===")
print(tonumber(42))
print(tonumber(3.14))
print(tonumber("123"))
print(tonumber("45.67"))
print(tonumber("0x1F"))

print("=== rawlen tests ===")
print(rawlen("hello"))
print(rawlen({1, 2, 3, 4, 5}))

print("=== rawequal tests ===")
print(rawequal(1, 1))
print(rawequal(1, 2))
print(rawequal("a", "a"))
print(rawequal(nil, nil))

print("=== rawget/rawset tests ===")
local t = {10, 20, 30}
print(rawget(t, 1))
print(rawget(t, 2))
rawset(t, 4, 40)
print(rawget(t, 4))

print("=== select tests ===")
print(select("#", 1, 2, 3, 4, 5))
print(select(2, "a", "b", "c"))
print(select(-1, "x", "y", "z"))

print("=== assert tests ===")
local ok = assert(true, "should pass")
print(ok)

print("=== metatable tests ===")
local mt = {}
local t2 = {}
setmetatable(t2, mt)
print(getmetatable(t2) == mt)

print("=== Done ===")
