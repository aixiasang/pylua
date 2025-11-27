-- test.lua - Simple test file for PyLua bytecode loader
-- Compile with: lua53 -o test.luac test.lua

print("Hello, PyLua!")

local a = 10
local b = 20
local c = a + b

print("Result:", c)

function add(x, y)
    return x + y
end

local result = add(100, 200)
print("100 + 200 =", result)
