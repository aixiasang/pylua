-- test_string_lib.lua
-- String library function tests

print("=== String Library Tests ===")

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
-- 1. Basic String Functions
-- ============================================================================
print("\n--- Basic String ---")

test("string.len", string.len("hello") == 5)
test("string.len empty", string.len("") == 0)
test("#string operator", #"hello" == 5)

test("string.upper", string.upper("hello") == "HELLO")
test("string.lower", string.lower("HELLO") == "hello")

test("string.reverse", string.reverse("hello") == "olleh")
test("string.reverse empty", string.reverse("") == "")

-- ============================================================================
-- 2. String Substring
-- ============================================================================
print("\n--- Substring ---")

test("string.sub basic", string.sub("hello", 2, 4) == "ell")
test("string.sub start only", string.sub("hello", 2) == "ello")
test("string.sub negative", string.sub("hello", -2) == "lo")
test("string.sub negative both", string.sub("hello", -4, -2) == "ell")

-- ============================================================================
-- 3. String Repeat
-- ============================================================================
print("\n--- Repeat ---")

test("string.rep basic", string.rep("ab", 3) == "ababab")
test("string.rep zero", string.rep("ab", 0) == "")
test("string.rep with sep", string.rep("ab", 3, "-") == "ab-ab-ab")

-- ============================================================================
-- 4. Character Conversion
-- ============================================================================
print("\n--- Character Conversion ---")

test("string.byte", string.byte("ABC") == 65)
test("string.byte index", string.byte("ABC", 2) == 66)
test("string.byte range", ({string.byte("ABC", 1, 3)})[2] == 66)

test("string.char", string.char(65) == "A")
test("string.char multi", string.char(65, 66, 67) == "ABC")

-- ============================================================================
-- 5. String Find
-- ============================================================================
print("\n--- Find ---")

local s, e = string.find("hello world", "world")
test("string.find found", s == 7 and e == 11)

s, e = string.find("hello world", "xyz")
test("string.find not found", s == nil)

s, e = string.find("hello world", "o")
test("string.find first", s == 5)

s, e = string.find("hello world", "o", 6)
test("string.find with init", s == 8)

-- Plain find (no pattern)
s, e = string.find("a.b.c", ".", 1, true)
test("string.find plain", s == 2)

-- ============================================================================
-- 6. String Match
-- ============================================================================
print("\n--- Match ---")

test("string.match literal", string.match("hello", "ell") == "ell")
test("string.match pattern", string.match("hello123", "%d+") == "123")
test("string.match capture", string.match("key=value", "(%w+)=(%w+)") == "key")

-- ============================================================================
-- 7. String Gsub
-- ============================================================================
print("\n--- Gsub ---")

local result, count = string.gsub("hello", "l", "L")
test("string.gsub basic", result == "heLLo" and count == 2)

result, count = string.gsub("hello", "l", "L", 1)
test("string.gsub limit", result == "heLlo" and count == 1)

result = string.gsub("hello world", "%w+", string.upper)
test("string.gsub function", result == "HELLO WORLD")

result = string.gsub("$x + $y", "%$(%w)", function(v) return "_" .. v end)
test("string.gsub capture func", result == "_x + _y")

-- ============================================================================
-- 8. String Format
-- ============================================================================
print("\n--- Format ---")

test("string.format %d", string.format("%d", 42) == "42")
test("string.format %s", string.format("%s", "hello") == "hello")
test("string.format %f", string.format("%.2f", 3.14159) == "3.14")
test("string.format %%", string.format("%%") == "%")
test("string.format mixed", string.format("%s = %d", "x", 10) == "x = 10")
test("string.format padding", string.format("%05d", 42) == "00042")
test("string.format hex", string.format("%x", 255) == "ff")
test("string.format HEX", string.format("%X", 255) == "FF")

-- ============================================================================
-- 9. String Gmatch
-- ============================================================================
print("\n--- Gmatch ---")

local words = {}
for word in string.gmatch("hello world lua", "%w+") do
    words[#words + 1] = word
end
test("string.gmatch count", #words == 3)
test("string.gmatch first", words[1] == "hello")
test("string.gmatch last", words[3] == "lua")

local pairs_t = {}
for k, v in string.gmatch("a=1, b=2, c=3", "(%w+)=(%d+)") do
    pairs_t[k] = tonumber(v)
end
test("string.gmatch captures", pairs_t.a == 1 and pairs_t.b == 2)

-- ============================================================================
-- 10. String Concatenation
-- ============================================================================
print("\n--- Concatenation ---")

test(".. operator", "hello" .. " " .. "world" == "hello world")
test(".. with number", "value: " .. 42 == "value: 42")

-- table.concat
local parts = {"a", "b", "c"}
test("table.concat", table.concat(parts) == "abc")
test("table.concat sep", table.concat(parts, ", ") == "a, b, c")
test("table.concat range", table.concat(parts, "-", 1, 2) == "a-b")

-- ============================================================================
-- 11. Pattern Matching Specials
-- ============================================================================
print("\n--- Pattern Classes ---")

test("pattern %a", string.match("hello123", "%a+") == "hello")
test("pattern %d", string.match("hello123", "%d+") == "123")
test("pattern %w", string.match("hello_123", "%w+") == "hello_123")
test("pattern %s", string.match("hello world", "%s") == " ")
test("pattern %p", string.match("hello!", "%p") == "!")

test("pattern [set]", string.match("hello", "[aeiou]+") == "e")
test("pattern [^set]", string.match("hello", "[^aeiou]+") == "h")

-- ============================================================================
-- 12. String Dump (if available)
-- ============================================================================
print("\n--- Dump ---")

local f = function(x) return x + 1 end
local ok, dump = pcall(string.dump, f)
if ok then
    test("string.dump type", type(dump) == "string")
    test("string.dump length", #dump > 0)
else
    print("SKIP: string.dump not available")
end

-- ============================================================================
-- 13. Edge Cases
-- ============================================================================
print("\n--- Edge Cases ---")

test("empty string len", #"" == 0)
test("empty string sub", string.sub("", 1, 1) == "")
test("empty string find", string.find("", "x") == nil)
test("empty pattern find", string.find("hello", "") == 1)

-- Unicode-like (bytes)
local utf8str = "héllo"
test("multibyte len", #utf8str >= 5)

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
