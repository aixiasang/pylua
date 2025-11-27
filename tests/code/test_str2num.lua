-- test_str2num.lua
-- 测试字符串到数字的转换

print("=== String to Number Tests ===")

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

-- [1] 十进制整数
print("\n[1] Decimal Integers")
test("'123' + 0", "123" + 0 == 123)
test("'-456' + 0", "-456" + 0 == -456)
test("'+789' + 0", "+789" + 0 == 789)
test("'  42  ' + 0", "  42  " + 0 == 42)

-- [2] 十六进制整数
print("\n[2] Hexadecimal Integers")
test("'0xff' + 0", "0xff" + 0 == 255)
test("'0XFF' + 0", "0XFF" + 0 == 255)
test("'0x10' + 0", "0x10" + 0 == 16)
test("'-0x10' + 0", "-0x10" + 0 == -16)

-- [3] 十进制浮点数
print("\n[3] Decimal Floats")
test("'3.14' + 0", "3.14" + 0 == 3.14)
test("'-2.5' + 0", "-2.5" + 0 == -2.5)
test("'.5' + 0", ".5" + 0 == 0.5)
test("'1.' + 0", "1." + 0 == 1.0)
test("'1e10' + 0", "1e10" + 0 == 1e10)
test("'1.5e-3' + 0", "1.5e-3" + 0 == 0.0015)

-- [4] 十六进制浮点数
print("\n[4] Hexadecimal Floats")
test("'0x1p0' + 0", "0x1p0" + 0 == 1.0)
test("'0x1p4' + 0", "0x1p4" + 0 == 16.0)
test("'0x1.8p0' + 0", "0x1.8p0" + 0 == 1.5)

-- [5] tonumber 函数
print("\n[5] tonumber Function")
test("tonumber('123')", tonumber("123") == 123)
test("tonumber('0xff')", tonumber("0xff") == 255)
test("tonumber('3.14')", tonumber("3.14") == 3.14)
test("tonumber('invalid')", tonumber("invalid") == nil)
test("tonumber('')", tonumber("") == nil)

-- 总结
print("\n" .. string.rep("=", 40))
print("Passed: " .. passed .. "/" .. total)
if passed == total then
    print("*** ALL TESTS PASSED ***")
else
    print("*** " .. (total - passed) .. " TESTS FAILED ***")
end
