-- test_vararg.lua - Vararg test

print("Test 1: Vararg to table")
local function test1(...)
    local args = {...}
    print(#args)
end
test1(1, 2, 3)

print("Done!")
