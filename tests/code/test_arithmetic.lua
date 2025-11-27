-- test_arithmetic.lua
-- Simple arithmetic tests - compare output between lua53 and pylua

-- Integer arithmetic
print("=== Integer Arithmetic ===")
print(1 + 2)
print(10 - 3)
print(4 * 5)
print(10 // 3)
print(10 % 3)
print(-10 // 3)
print(-10 % 3)

-- Float arithmetic
print("=== Float Arithmetic ===")
print(1.5 + 2.5)
print(5.0 - 2.0)
print(2.5 * 4.0)
print(10.0 / 4.0)
print(2.0 ^ 3.0)

-- Mixed
print("=== Mixed Arithmetic ===")
print(1 + 2.5)
print(10 / 3)

-- Comparisons
print("=== Comparisons ===")
print(1 < 2)
print(2 > 1)
print(1 == 1)
print(1 ~= 2)
print(1 <= 1)
print(2 >= 2)

-- String comparisons
print("=== String Comparisons ===")
print("abc" < "abd")
print("abc" == "abc")
print("abc" ~= "xyz")

-- Logical
print("=== Logical ===")
print(not false)
print(not true)
print(not nil)
print(true and false)
print(true or false)

-- For loops
print("=== For Loops ===")
local sum = 0
for i = 1, 5 do
    sum = sum + i
end
print(sum)

sum = 0
for i = 10, 1, -2 do
    sum = sum + i
end
print(sum)

-- String operations
print("=== Strings ===")
print("hello" .. " " .. "world")
print(#"hello")

-- Tables
print("=== Tables ===")
local t = {10, 20, 30}
print(t[1])
print(t[2])
print(t[3])
print(#t)

print("=== Done ===")
