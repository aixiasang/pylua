-- ============================================================================
-- Test 11: String Library Comprehensive Tests
-- 测试字符串库的全面功能
-- ============================================================================

print("=== Test 11: String Library ===")

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
-- [1] string.sub Tests
-- ============================================================================
print("\n[1] string.sub Tests")

-- Test 1.1: Basic substring
test("sub basic", string.sub("hello", 2, 4) == "ell")
test("sub from start", string.sub("hello", 1, 3) == "hel")
test("sub to end", string.sub("hello", 3, 5) == "llo")

-- Test 1.2: Negative indices
test("sub negative start", string.sub("hello", -3, -1) == "llo")
test("sub negative end", string.sub("hello", 2, -2) == "ell")
test("sub both negative", string.sub("hello", -4, -2) == "ell")

-- Test 1.3: Default parameters
test("sub no end", string.sub("hello", 2) == "ello")
test("sub from 1", string.sub("hello", 1) == "hello")

-- Test 1.4: Edge cases
test("sub empty", string.sub("hello", 3, 2) == "")
test("sub out of range", string.sub("hello", 10, 20) == "")
test("sub single char", string.sub("hello", 3, 3) == "l")

-- ============================================================================
-- [2] string.len Tests
-- ============================================================================
print("\n[2] string.len Tests")

-- Test 2.1: Basic length
test("len basic", string.len("hello") == 5)
test("len empty", string.len("") == 0)
test("len single", string.len("a") == 1)

-- Test 2.2: Length with special characters
test("len spaces", string.len("  ") == 2)
test("len newline", string.len("a\nb") == 3)
test("len tab", string.len("a\tb") == 3)

-- Test 2.3: # operator
test("# operator", #"hello" == 5)
test("# empty", #"" == 0)

-- ============================================================================
-- [3] string.rep Tests
-- ============================================================================
print("\n[3] string.rep Tests")

-- Test 3.1: Basic repetition
test("rep basic", string.rep("ab", 3) == "ababab")
test("rep single", string.rep("x", 5) == "xxxxx")
test("rep zero", string.rep("abc", 0) == "")

-- Test 3.2: Repetition with separator
test("rep with sep", string.rep("x", 3, ",") == "x,x,x")
test("rep with space", string.rep("a", 4, " ") == "a a a a")

-- Test 3.3: Edge cases
test("rep empty string", string.rep("", 5) == "")
test("rep one time", string.rep("hello", 1) == "hello")

-- ============================================================================
-- [4] string.upper and string.lower Tests
-- ============================================================================
print("\n[4] string.upper and string.lower Tests")

-- Test 4.1: Basic case conversion
test("upper basic", string.upper("hello") == "HELLO")
test("lower basic", string.lower("HELLO") == "hello")
test("upper mixed", string.upper("HeLLo") == "HELLO")
test("lower mixed", string.lower("HeLLo") == "hello")

-- Test 4.2: Non-alphabetic characters
test("upper numbers", string.upper("abc123") == "ABC123")
test("lower numbers", string.lower("ABC123") == "abc123")
test("upper symbols", string.upper("a!b@c#") == "A!B@C#")

-- Test 4.3: Edge cases
test("upper empty", string.upper("") == "")
test("lower empty", string.lower("") == "")

-- ============================================================================
-- [5] string.format Tests
-- ============================================================================
print("\n[5] string.format Tests")

-- Test 5.1: Integer formatting
test("format %d", string.format("%d", 42) == "42")
test("format %i", string.format("%i", -10) == "-10")
test("format %d zero", string.format("%d", 0) == "0")

-- Test 5.2: Float formatting
test("format %f", string.format("%f", 3.14) == "3.140000")
test("format %.2f", string.format("%.2f", 3.14159) == "3.14")
test("format %.0f", string.format("%.0f", 3.7) == "4")

-- Test 5.3: String formatting
test("format %s", string.format("%s", "hello") == "hello")
test("format multiple", string.format("%s %d", "count", 5) == "count 5")

-- Test 5.4: Complex formatting
test("format complex", string.format("x=%d, y=%d", 10, 20) == "x=10, y=20")
test("format mixed", string.format("%s: %.1f", "pi", 3.14159) == "pi: 3.1")

-- ============================================================================
-- [6] string.find Tests
-- ============================================================================
print("\n[6] string.find Tests")

-- Test 6.1: Basic find
local i1, j1 = string.find("hello world", "world")
test("find basic start", i1 == 7)
test("find basic end", j1 == 11)

-- Test 6.2: Find from position
local i2, j2 = string.find("hello hello", "hello", 3)
test("find from pos start", i2 == 7)
test("find from pos end", j2 == 11)

-- Test 6.3: Not found
local i3 = string.find("hello", "xyz")
test("find not found", i3 == nil)

-- Test 6.4: Find at start
local i4, j4 = string.find("hello", "hel")
test("find at start", i4 == 1 and j4 == 3)

-- Test 6.5: Find single character
local i5, j5 = string.find("hello", "l")
test("find single char", i5 == 3 and j5 == 3)

-- ============================================================================
-- [7] String Concatenation Tests
-- ============================================================================
print("\n[7] String Concatenation Tests")

-- Test 7.1: Basic concatenation
test("concat basic", "hello" .. " " .. "world" == "hello world")
test("concat empty", "hello" .. "" == "hello")
test("concat multiple", "a" .. "b" .. "c" == "abc")

-- Test 7.2: Concatenation with numbers
test("concat number", "value: " .. 42 == "value: 42")
test("concat float", "pi: " .. 3.14 == "pi: 3.14")

-- Test 7.3: Concatenation in expressions
local s = "hello"
s = s .. " world"
test("concat assignment", s == "hello world")

-- ============================================================================
-- [8] String Comparison Tests
-- ============================================================================
print("\n[8] String Comparison Tests")

-- Test 8.1: Equality
test("equal same", "hello" == "hello")
test("equal different", "hello" ~= "world")
test("equal case", "Hello" ~= "hello")

-- Test 8.2: Lexicographic comparison
test("less than", "abc" < "abd")
test("greater than", "xyz" > "abc")
test("less or equal", "abc" <= "abc")
test("greater or equal", "abc" >= "abc")

-- Test 8.3: Number string comparison
test("num string less", "1" < "2")
test("num string greater", "10" < "2")  -- lexicographic!

-- ============================================================================
-- [9] String Coercion Tests
-- ============================================================================
print("\n[9] String Coercion Tests")

-- Test 9.1: Number to string
test("tostring number", tostring(42) == "42")
test("tostring float", tostring(3.14) == "3.14")
test("tostring negative", tostring(-10) == "-10")

-- Test 9.2: Boolean to string
test("tostring true", tostring(true) == "true")
test("tostring false", tostring(false) == "false")

-- Test 9.3: Nil to string
test("tostring nil", tostring(nil) == "nil")

-- Test 9.4: String to number
test("tonumber string", tonumber("42") == 42)
test("tonumber float", tonumber("3.14") == 3.14)
test("tonumber invalid", tonumber("abc") == nil)

-- ============================================================================
-- [10] String as Array Tests
-- ============================================================================
print("\n[10] String as Array Tests")

-- Test 10.1: Iterate characters
local chars = {}
for i = 1, #"hello" do
    table.insert(chars, string.sub("hello", i, i))
end
test("iterate chars count", #chars == 5)
test("iterate first char", chars[1] == "h")
test("iterate last char", chars[5] == "o")

-- Test 10.2: Build string from characters
local s = ""
for i = 1, 5 do
    s = s .. string.sub("hello", i, i)
end
test("build from chars", s == "hello")

-- ============================================================================
-- [11] String Escape Sequences Tests
-- ============================================================================
print("\n[11] String Escape Sequences Tests")

-- Test 11.1: Basic escapes
test("escape newline", "a\nb" == "a\nb")
test("escape tab", "a\tb" == "a\tb")
test("escape quote", "a\"b" == 'a"b')

-- Test 11.2: Length with escapes
test("len with newline", #"a\nb" == 3)
test("len with tab", #"a\tb" == 3)

-- ============================================================================
-- [12] String Method Syntax Tests
-- ============================================================================
print("\n[12] String Method Syntax Tests")

-- Test 12.1: Colon syntax
test("method sub", ("hello"):sub(2, 4) == "ell")
test("method upper", ("hello"):upper() == "HELLO")
test("method len", ("hello"):len() == 5)

-- Test 12.2: Chaining
test("method chain", ("hello"):upper():sub(1, 3) == "HEL")
test("method chain lower", ("HELLO"):lower():sub(2, 4) == "ell")

-- ============================================================================
-- [13] String Buffer Tests
-- ============================================================================
print("\n[13] String Buffer Tests")

-- Test 13.1: Efficient concatenation
local parts = {}
for i = 1, 10 do
    table.insert(parts, tostring(i))
end
local result = table.concat(parts, ",")
test("buffer concat", result == "1,2,3,4,5,6,7,8,9,10")

-- Test 13.2: Concatenation without separator
local parts2 = {"a", "b", "c"}
test("buffer no sep", table.concat(parts2) == "abc")

-- ============================================================================
-- [14] String Immutability Tests
-- ============================================================================
print("\n[14] String Immutability Tests")

-- Test 14.1: Strings are immutable
local s1 = "hello"
local s2 = s1
s1 = s1 .. " world"
test("immutable original", s2 == "hello")
test("immutable new", s1 == "hello world")

-- Test 14.2: String interning
local a = "test"
local b = "test"
test("string interning", a == b)

-- ============================================================================
-- [15] Complex String Operations Tests
-- ============================================================================
print("\n[15] Complex String Operations Tests")

-- Test 15.1: Reverse string
local function reverse(s)
    local r = ""
    for i = #s, 1, -1 do
        r = r .. string.sub(s, i, i)
    end
    return r
end

test("reverse string", reverse("hello") == "olleh")
test("reverse single", reverse("a") == "a")
test("reverse empty", reverse("") == "")

-- Test 15.2: Count character occurrences
local function count_char(s, c)
    local count = 0
    for i = 1, #s do
        if string.sub(s, i, i) == c then
            count = count + 1
        end
    end
    return count
end

test("count char", count_char("hello", "l") == 2)
test("count char none", count_char("hello", "x") == 0)
test("count char all", count_char("aaa", "a") == 3)

-- Test 15.3: String trimming
local function trim(s)
    local start = 1
    while start <= #s and string.sub(s, start, start) == " " do
        start = start + 1
    end
    
    local finish = #s
    while finish >= 1 and string.sub(s, finish, finish) == " " do
        finish = finish - 1
    end
    
    if start > finish then
        return ""
    end
    return string.sub(s, start, finish)
end

test("trim both", trim("  hello  ") == "hello")
test("trim left", trim("  hello") == "hello")
test("trim right", trim("hello  ") == "hello")
test("trim none", trim("hello") == "hello")
test("trim all spaces", trim("   ") == "")

-- Test 15.4: Split string
local function split(s, sep)
    local parts = {}
    local start = 1
    
    while true do
        local pos = string.find(s, sep, start, true)
        if not pos then
            table.insert(parts, string.sub(s, start))
            break
        end
        
        table.insert(parts, string.sub(s, start, pos - 1))
        start = pos + #sep
    end
    
    return parts
end

local parts = split("a,b,c", ",")
test("split count", #parts == 3)
test("split first", parts[1] == "a")
test("split last", parts[3] == "c")

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
    print("\n*** ALL STRING LIBRARY TESTS PASSED ***")
else
    print("\n*** SOME TESTS FAILED ***")
end
