-- test_io_csv.lua
-- 文件 I/O 和 CSV 解析器测试
-- Tests file I/O operations and implements a CSV parser/writer

print("=== I/O and CSV Parser Tests ===")

local tests_passed = 0
local tests_total = 0

local function test(name, condition)
    tests_total = tests_total + 1
    if condition then
        tests_passed = tests_passed + 1
        print("  PASS: " .. name)
    else
        print("  FAIL: " .. name)
    end
end

-- ============================================================================
-- [1] io 库基本存在性测试
-- ============================================================================
print("\n[1] io Library Existence")
test("io exists", io ~= nil)
test("io is table", type(io) == "table")
test("io.open exists", io.open ~= nil)
test("io.write exists", io.write ~= nil)
test("io.read exists", io.read ~= nil)
test("io.close exists", io.close ~= nil)
test("io.lines exists", io.lines ~= nil)

-- ============================================================================
-- [2] 文件写入测试
-- ============================================================================
print("\n[2] File Write Tests")

local test_file = "test_output.txt"
local f = io.open(test_file, "w")
test("open file for write", f ~= nil)

if f then
    f:write("Hello, World!\n")
    f:write("Line 2\n")
    f:write("Line 3\n")
    f:close()
    test("write and close", true)
else
    test("write and close", false)
end

-- ============================================================================
-- [3] 文件读取测试
-- ============================================================================
print("\n[3] File Read Tests")

local f2 = io.open(test_file, "r")
test("open file for read", f2 ~= nil)

if f2 then
    local content = f2:read("*a")
    test("read all content", content ~= nil)
    test("content not empty", content and #content > 0)
    f2:close()
end

-- ============================================================================
-- [4] CSV 解析器实现
-- ============================================================================
print("\n[4] CSV Parser Implementation")

-- CSV 解析函数
local function parse_csv_line(line)
    local result = {}
    local field = ""
    local in_quotes = false
    
    for i = 1, #line do
        local c = line:sub(i, i)
        
        if c == '"' then
            in_quotes = not in_quotes
        elseif c == ',' and not in_quotes then
            table.insert(result, field)
            field = ""
        else
            field = field .. c
        end
    end
    
    -- 添加最后一个字段
    table.insert(result, field)
    
    return result
end

-- 测试 CSV 解析
local csv_line1 = "name,age,city"
local parsed1 = parse_csv_line(csv_line1)
test("parse csv header", #parsed1 == 3)
test("parse field 1", parsed1[1] == "name")
test("parse field 2", parsed1[2] == "age")
test("parse field 3", parsed1[3] == "city")

local csv_line2 = "John,25,New York"
local parsed2 = parse_csv_line(csv_line2)
test("parse csv data", #parsed2 == 3)
test("parse value 1", parsed2[1] == "John")
test("parse value 2", parsed2[2] == "25")
test("parse value 3", parsed2[3] == "New York")

-- ============================================================================
-- [5] CSV 写入器实现
-- ============================================================================
print("\n[5] CSV Writer Implementation")

-- CSV 写入函数
local function write_csv_line(fields)
    local result = ""
    for i, field in ipairs(fields) do
        -- 如果字段包含逗号或引号，需要用引号包围
        local needs_quotes = field:find(",") or field:find('"')
        if needs_quotes then
            field = '"' .. field:gsub('"', '""') .. '"'
        end
        if i > 1 then
            result = result .. ","
        end
        result = result .. field
    end
    return result
end

local csv_out1 = write_csv_line({"name", "age", "city"})
test("write csv header", csv_out1 == "name,age,city")

local csv_out2 = write_csv_line({"John", "25", "New York"})
test("write csv data", csv_out2 == "John,25,New York")

-- ============================================================================
-- [6] 完整 CSV 文件读写测试
-- ============================================================================
print("\n[6] Complete CSV File Test")

local csv_file = "test_data.csv"

-- 写入 CSV 文件
local function write_csv_file(filename, data)
    local f = io.open(filename, "w")
    if not f then return false end
    
    for _, row in ipairs(data) do
        f:write(write_csv_line(row) .. "\n")
    end
    
    f:close()
    return true
end

-- 读取 CSV 文件
local function read_csv_file(filename)
    local f = io.open(filename, "r")
    if not f then return nil end
    
    local data = {}
    for line in f:lines() do
        if #line > 0 then
            table.insert(data, parse_csv_line(line))
        end
    end
    
    f:close()
    return data
end

-- 测试数据
local test_data = {
    {"id", "name", "score"},
    {"1", "Alice", "95"},
    {"2", "Bob", "87"},
    {"3", "Charlie", "92"}
}

-- 写入
local write_ok = write_csv_file(csv_file, test_data)
test("write csv file", write_ok)

-- 读取
local read_data = read_csv_file(csv_file)
test("read csv file", read_data ~= nil)
test("correct row count", read_data and #read_data == 4)

if read_data and #read_data >= 4 then
    test("header row", read_data[1][1] == "id" and read_data[1][2] == "name")
    test("data row 1", read_data[2][1] == "1" and read_data[2][2] == "Alice")
    test("data row 2", read_data[3][2] == "Bob" and read_data[3][3] == "87")
    test("data row 3", read_data[4][2] == "Charlie")
end

-- ============================================================================
-- [7] 数据处理测试
-- ============================================================================
print("\n[7] Data Processing Tests")

-- 计算平均分
local function calculate_average(data)
    local sum = 0
    local count = 0
    for i = 2, #data do  -- 跳过表头
        local score = tonumber(data[i][3])
        if score then
            sum = sum + score
            count = count + 1
        end
    end
    return count > 0 and (sum / count) or 0
end

if read_data then
    local avg = calculate_average(read_data)
    test("calculate average", avg > 90 and avg < 95)  -- (95+87+92)/3 = 91.33
    print("  Average score: " .. string.format("%.2f", avg))
end

-- 按分数排序
local function sort_by_score(data)
    local sorted = {}
    for i = 2, #data do
        table.insert(sorted, data[i])
    end
    table.sort(sorted, function(a, b)
        return tonumber(a[3]) > tonumber(b[3])
    end)
    return sorted
end

if read_data then
    local sorted = sort_by_score(read_data)
    test("sort by score", sorted[1][2] == "Alice")  -- Alice has highest score
    test("sort order", tonumber(sorted[1][3]) >= tonumber(sorted[2][3]))
end

-- ============================================================================
-- [8] 清理测试文件
-- ============================================================================
print("\n[8] Cleanup")
os.remove(test_file)
os.remove(csv_file)
test("cleanup files", true)

-- ============================================================================
-- 测试总结
-- ============================================================================
print("\n" .. string.rep("=", 60))
print("I/O AND CSV TEST SUMMARY")
print(string.rep("=", 60))
print("Total tests: " .. tests_total)
print("Passed: " .. tests_passed)
print("Failed: " .. (tests_total - tests_passed))
print("Success rate: " .. string.format("%.1f", (tests_passed / tests_total * 100)) .. "%")
print(string.rep("=", 60))

if tests_passed == tests_total then
    print("\n*** ALL I/O AND CSV TESTS PASSED ***")
else
    print("\n*** SOME TESTS FAILED ***")
end
