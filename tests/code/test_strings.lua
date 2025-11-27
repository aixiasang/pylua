-- test_strings.lua
-- String operations tests

print("=== String Basics ===")
local s = "hello"
print(s)
print(#s)

print("=== String Concatenation ===")
print("a" .. "b")
print("hello" .. " " .. "world")
print("num: " .. 42)
print("float: " .. 3.14)

-- Multiple concat
local parts = ""
for i = 1, 5 do
    parts = parts .. tostring(i)
end
print(parts)

print("=== String Comparison ===")
print("abc" == "abc")
print("abc" ~= "def")
print("abc" < "abd")
print("abc" <= "abc")
print("xyz" > "abc")
print("xyz" >= "xyz")

-- Empty string
print("=== Empty String ===")
print(#"")
print("" == "")
print("" < "a")

print("=== Done ===")
