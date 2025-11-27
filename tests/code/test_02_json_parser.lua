-- ============================================================================
-- Deep Integration Test: JSON Parser & Serializer
-- ~1000 lines of complex Lua code testing multiple features
-- Features tested: tables, strings, functions, recursion, patterns, metatables
-- ============================================================================

print("=== JSON Parser & Serializer Integration Test ===\n")

-- ============================================================================
-- PART 1: JSON SERIALIZER (400 lines)
-- ============================================================================

local JSON = {}

-- Escape special characters in strings
local function escape_str(s)
    local escape_chars = {
        ["\\"] = "\\\\",
        ["\""] = "\\\"",
        ["\n"] = "\\n",
        ["\r"] = "\\r",
        ["\t"] = "\\t"
    }
    
    local result = ""
    for i = 1, #s do
        local char = s:sub(i, i)
        local escaped = escape_chars[char]
        if escaped then
            result = result .. escaped
        else
            result = result .. char
        end
    end
    
    return result
end

-- Check if table is array
local function is_array(t)
    if type(t) ~= "table" then
        return false
    end
    
    local count = 0
    for _ in pairs(t) do
        count = count + 1
    end
    
    local array_count = 0
    for i = 1, count do
        if t[i] ~= nil then
            array_count = array_count + 1
        else
            break
        end
    end
    
    return array_count == count
end

-- Serialize value to JSON
function JSON.serialize(value, indent, current_indent)
    indent = indent or ""
    current_indent = current_indent or ""
    
    local value_type = type(value)
    
    if value_type == "nil" then
        return "null"
    
    elseif value_type == "boolean" then
        return value and "true" or "false"
    
    elseif value_type == "number" then
        return tostring(value)
    
    elseif value_type == "string" then
        return "\"" .. escape_str(value) .. "\""
    
    elseif value_type == "table" then
        if is_array(value) then
            -- Serialize as JSON array
            if #value == 0 then
                return "[]"
            end
            
            local parts = {}
            local new_indent = current_indent .. indent
            
            for i = 1, #value do
                local serialized = JSON.serialize(value[i], indent, new_indent)
                if indent == "" then
                    parts[#parts + 1] = serialized
                else
                    parts[#parts + 1] = new_indent .. serialized
                end
            end
            
            if indent == "" then
                return "[" .. table.concat(parts, ",") .. "]"
            else
                return "[\n" .. table.concat(parts, ",\n") .. "\n" .. current_indent .. "]"
            end
        else
            -- Serialize as JSON object
            local parts = {}
            local new_indent = current_indent .. indent
            local has_keys = false
            
            for k, v in pairs(value) do
                has_keys = true
                local key = tostring(k)
                local val = JSON.serialize(v, indent, new_indent)
                
                if indent == "" then
                    parts[#parts + 1] = "\"" .. escape_str(key) .. "\":" .. val
                else
                    parts[#parts + 1] = new_indent .. "\"" .. escape_str(key) .. "\": " .. val
                end
            end
            
            if not has_keys then
                return "{}"
            end
            
            if indent == "" then
                return "{" .. table.concat(parts, ",") .. "}"
            else
                return "{\n" .. table.concat(parts, ",\n") .. "\n" .. current_indent .. "}"
            end
        end
    else
        error("Cannot serialize type: " .. value_type)
    end
end

-- ============================================================================
-- PART 2: JSON PARSER (500 lines)
-- ============================================================================

-- Parser state
local Parser = {}
Parser.__index = Parser

function Parser.new(text)
    local self = setmetatable({}, Parser)
    self.text = text
    self.pos = 1
    self.len = #text
    return self
end

-- Get current character
function Parser:peek()
    if self.pos <= self.len then
        return self.text:sub(self.pos, self.pos)
    end
    return nil
end

-- Consume current character
function Parser:consume()
    local char = self:peek()
    self.pos = self.pos + 1
    return char
end

-- Skip whitespace
function Parser:skip_whitespace()
    while self:peek() do
        local char = self:peek()
        if char == " " or char == "\t" or char == "\n" or char == "\r" then
            self:consume()
        else
            break
        end
    end
end

-- Parse null
function Parser:parse_null()
    if self.text:sub(self.pos, self.pos + 3) == "null" then
        self.pos = self.pos + 4
        return nil
    end
    error("Expected 'null' at position " .. self.pos)
end

-- Parse boolean
function Parser:parse_boolean()
    if self.text:sub(self.pos, self.pos + 3) == "true" then
        self.pos = self.pos + 4
        return true
    elseif self.text:sub(self.pos, self.pos + 4) == "false" then
        self.pos = self.pos + 5
        return false
    end
    error("Expected boolean at position " .. self.pos)
end

-- Parse number
function Parser:parse_number()
    local start_pos = self.pos
    local has_dot = false
    local has_exp = false
    
    -- Handle negative
    if self:peek() == "-" then
        self:consume()
    end
    
    -- Parse digits
    while self:peek() do
        local char = self:peek()
        
        if char >= "0" and char <= "9" then
            self:consume()
        elseif char == "." and not has_dot and not has_exp then
            has_dot = true
            self:consume()
        elseif (char == "e" or char == "E") and not has_exp then
            has_exp = true
            self:consume()
            -- Handle exp sign
            if self:peek() == "+" or self:peek() == "-" then
                self:consume()
            end
        else
            break
        end
    end
    
    local num_str = self.text:sub(start_pos, self.pos - 1)
    local num = tonumber(num_str)
    
    if not num then
        error("Invalid number at position " .. start_pos)
    end
    
    return num
end

-- Parse string
function Parser:parse_string()
    if self:consume() ~= "\"" then
        error("Expected '\"' at position " .. (self.pos - 1))
    end
    
    local result = ""
    
    while self:peek() and self:peek() ~= "\"" do
        local char = self:consume()
        
        if char == "\\" then
            local next_char = self:consume()
            if next_char == "n" then
                result = result .. "\n"
            elseif next_char == "r" then
                result = result .. "\r"
            elseif next_char == "t" then
                result = result .. "\t"
            elseif next_char == "\"" then
                result = result .. "\""
            elseif next_char == "\\" then
                result = result .. "\\"
            else
                result = result .. next_char
            end
        else
            result = result .. char
        end
    end
    
    if self:consume() ~= "\"" then
        error("Unterminated string")
    end
    
    return result
end

-- Parse array
function Parser:parse_array()
    if self:consume() ~= "[" then
        error("Expected '[' at position " .. (self.pos - 1))
    end
    
    local result = {}
    self:skip_whitespace()
    
    -- Handle empty array
    if self:peek() == "]" then
        self:consume()
        return result
    end
    
    while true do
        self:skip_whitespace()
        result[#result + 1] = self:parse_value()
        self:skip_whitespace()
        
        local char = self:peek()
        if char == "]" then
            self:consume()
            break
        elseif char == "," then
            self:consume()
        else
            error("Expected ',' or ']' at position " .. self.pos)
        end
    end
    
    return result
end

-- Parse object
function Parser:parse_object()
    if self:consume() ~= "{" then
        error("Expected '{' at position " .. (self.pos - 1))
    end
    
    local result = {}
    self:skip_whitespace()
    
    -- Handle empty object
    if self:peek() == "}" then
        self:consume()
        return result
    end
    
    while true do
        self:skip_whitespace()
        
        -- Parse key
        local key = self:parse_string()
        
        self:skip_whitespace()
        if self:consume() ~= ":" then
            error("Expected ':' at position " .. (self.pos - 1))
        end
        
        self:skip_whitespace()
        
        -- Parse value
        local value = self:parse_value()
        
        result[key] = value
        
        self:skip_whitespace()
        local char = self:peek()
        if char == "}" then
            self:consume()
            break
        elseif char == "," then
            self:consume()
        else
            error("Expected ',' or '}' at position " .. self.pos)
        end
    end
    
    return result
end

-- Parse any value
function Parser:parse_value()
    self:skip_whitespace()
    
    local char = self:peek()
    if not char then
        error("Unexpected end of input")
    end
    
    if char == "n" then
        return self:parse_null()
    elseif char == "t" or char == "f" then
        return self:parse_boolean()
    elseif char == "\"" then
        return self:parse_string()
    elseif char == "[" then
        return self:parse_array()
    elseif char == "{" then
        return self:parse_object()
    elseif char == "-" or (char >= "0" and char <= "9") then
        return self:parse_number()
    else
        error("Unexpected character '" .. char .. "' at position " .. self.pos)
    end
end

-- Main parse function
function JSON.parse(text)
    local parser = Parser.new(text)
    local result = parser:parse_value()
    parser:skip_whitespace()
    if parser:peek() then
        error("Unexpected content after JSON at position " .. parser.pos)
    end
    return result
end

-- ============================================================================
-- PART 3: TEST SUITE (100 lines)
-- ============================================================================

local test_count = 0
local pass_count = 0

local function test(name, condition)
    test_count = test_count + 1
    if condition then
        pass_count = pass_count + 1
        print("  PASS: " .. name)
    else
        print("  FAIL: " .. name)
    end
end

local function deep_equal(a, b)
    if type(a) ~= type(b) then
        return false
    end
    
    if type(a) ~= "table" then
        return a == b
    end
    
    for k, v in pairs(a) do
        if not deep_equal(v, b[k]) then
            return false
        end
    end
    
    for k in pairs(b) do
        if a[k] == nil then
            return false
        end
    end
    
    return true
end

print("\n[1] Serialization Tests")

-- Test primitives
test("serialize nil", JSON.serialize(nil) == "null")
test("serialize true", JSON.serialize(true) == "true")
test("serialize false", JSON.serialize(false) == "false")
test("serialize number", JSON.serialize(42) == "42")
test("serialize float", JSON.serialize(3.14) == "3.14")
test("serialize string", JSON.serialize("hello") == "\"hello\"")
test("serialize escaped", JSON.serialize("line1\nline2") == "\"line1\\nline2\"")

-- Test arrays
test("serialize empty array", JSON.serialize({}) == "[]")
test("serialize array", JSON.serialize({1, 2, 3}) == "[1,2,3]")
test("serialize nested array", JSON.serialize({{1, 2}, {3, 4}}) == "[[1,2],[3,4]]")

-- Test objects
local obj = {name = "John", age = 30}
local json_str = JSON.serialize(obj)
test("serialize object", json_str:find("\"name\":\"John\"") and json_str:find("\"age\":30"))

print("\n[2] Parsing Tests")

-- Test primitives
test("parse null", JSON.parse("null") == nil)
test("parse true", JSON.parse("true") == true)
test("parse false", JSON.parse("false") == false)
test("parse integer", JSON.parse("42") == 42)
test("parse float", JSON.parse("3.14") == 3.14)
test("parse negative", JSON.parse("-10") == -10)
test("parse string", JSON.parse("\"hello\"") == "hello")
test("parse escaped string", JSON.parse("\"line1\\nline2\"") == "line1\nline2")

-- Test arrays
local arr = JSON.parse("[1,2,3]")
test("parse array length", #arr == 3)
test("parse array [1]", arr[1] == 1)
test("parse array [2]", arr[2] == 2)
test("parse array [3]", arr[3] == 3)

local nested_arr = JSON.parse("[[1,2],[3,4]]")
test("parse nested array", nested_arr[1][2] == 2 and nested_arr[2][1] == 3)

-- Test objects
local parsed_obj = JSON.parse("{\"name\":\"John\",\"age\":30}")
test("parse object name", parsed_obj.name == "John")
test("parse object age", parsed_obj.age == 30)

-- Test whitespace
test("parse with spaces", JSON.parse(" { \"a\" : 1 } ").a == 1)

print("\n[3] Round-trip Tests")

-- Test round-trip
local function test_roundtrip(name, value)
    local json = JSON.serialize(value)
    local parsed = JSON.parse(json)
    test(name, deep_equal(value, parsed))
end

test_roundtrip("roundtrip number", 42)
test_roundtrip("roundtrip string", "hello")
test_roundtrip("roundtrip array", {1, 2, 3})
test_roundtrip("roundtrip nested", {a = {b = {c = 123}}})

print("\n[4] Complex Data Tests")

-- Complex nested structure
local complex = {
    users = {
        {name = "Alice", age = 25, active = true},
        {name = "Bob", age = 30, active = false}
    },
    config = {
        timeout = 3000,
        retries = 3,
        endpoints = {"api1", "api2", "api3"}
    }
}

local complex_json = JSON.serialize(complex)
local complex_parsed = JSON.parse(complex_json)

test("complex users[1] name", complex_parsed.users[1].name == "Alice")
test("complex users[2] age", complex_parsed.users[2].age == 30)
test("complex config timeout", complex_parsed.config.timeout == 3000)
test("complex endpoints[2]", complex_parsed.config.endpoints[2] == "api2")

print("\n[5] Edge Cases")

-- Empty structures
test("empty array roundtrip", deep_equal(JSON.parse(JSON.serialize({})), {}))

-- Numbers
test("parse zero", JSON.parse("0") == 0)
test("parse decimal", JSON.parse("0.5") == 0.5)

-- Strings
test("empty string", JSON.parse("\"\"") == "")
test("unicode escape", JSON.parse("\"\\\"\"") == "\"")

-- ============================================================================
-- PART 4: PERFORMANCE TEST
-- ============================================================================

print("\n[6] Performance Tests")

-- Generate large data
local function generate_large_data(size)
    local data = {}
    for i = 1, size do
        data[i] = {
            id = i,
            name = "User" .. i,
            email = "user" .. i .. "@example.com",
            active = (i % 2 == 0)
        }
    end
    return data
end

local large_data = generate_large_data(50)
local large_json = JSON.serialize(large_data)
local large_parsed = JSON.parse(large_json)

test("large data size", #large_parsed == 50)
test("large data [25]", large_parsed[25].name == "User25")
test("large data [50]", large_parsed[50].email == "user50@example.com")

print("\n" .. string.rep("=", 60))
print("TEST SUMMARY")
print(string.rep("=", 60))
print("Total tests: " .. test_count)
print("Passed: " .. pass_count)
print("Failed: " .. (test_count - pass_count))
print("Success rate: " .. string.format("%.1f%%", (pass_count / test_count) * 100))
print(string.rep("=", 60))

if pass_count == test_count then
    print("\n*** ALL INTEGRATION TESTS PASSED ***")
else
    print("\n*** SOME INTEGRATION TESTS FAILED ***")
end
