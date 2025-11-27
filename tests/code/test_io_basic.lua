-- test_io_basic.lua
-- Basic I/O tests

print("=== Basic I/O Tests ===")

-- [1] io table exists
print("\n[1] io Library")
print("io exists:", io ~= nil)
print("io.open exists:", io.open ~= nil)

-- [2] Write test
print("\n[2] Write Test")
local f = io.open("test_basic.txt", "w")
print("open for write:", f ~= nil)

if f then
    f:write("Line 1\n")
    f:write("Line 2\n")
    f:close()
    print("write ok")
end

-- [3] Read test
print("\n[3] Read Test")
local f2 = io.open("test_basic.txt", "r")
print("open for read:", f2 ~= nil)

if f2 then
    local content = f2:read("*a")
    print("content length:", #content)
    f2:close()
    print("read ok")
end

-- [4] Cleanup
os.remove("test_basic.txt")
print("\n=== Done ===")
