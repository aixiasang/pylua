-- 测试require功能
print("=== Test Require ===")

-- 测试package是否存在
if package then
    print("PASS: package exists")
    print("package.path:", package.path)
else
    print("FAIL: package not found")
end

-- 测试require是否存在
if require then
    print("PASS: require exists")
else
    print("FAIL: require not found")
end

-- 测试package.loaded
if package and package.loaded then
    print("PASS: package.loaded exists")
else
    print("FAIL: package.loaded not found")
end

-- 测试package.searchers
if package and package.searchers then
    print("PASS: package.searchers exists")
else
    print("FAIL: package.searchers not found")
end

print("\n*** Test Complete ***")
