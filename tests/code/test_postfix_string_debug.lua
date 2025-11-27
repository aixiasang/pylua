-- 调试postfix问题 - 使用字符串TokenType

local TokenType = {
    NUMBER = "NUMBER",
    PLUS = "PLUS",
    MULT = "MULT"
}

print("TokenType定义:")
print("  PLUS = " .. tostring(TokenType.PLUS))
print("  MULT = " .. tostring(TokenType.MULT))

local function infix_to_postfix(tokens)
    local output = {}
    local operators = {}
    local op_top = 0
    
    for i, token in ipairs(tokens) do
        if token.type == TokenType.NUMBER then
            print("  处理NUMBER: " .. token.value)
            output[#output + 1] = token.value
        elseif token.type == TokenType.PLUS or token.type == TokenType.MULT then
            print("  处理操作符: " .. token.type)
            op_top = op_top + 1
            operators[op_top] = token
        end
    end
    
    print("弹出操作符:")
    while op_top > 0 do
        print("    弹出: " .. tostring(operators[op_top].type))
        output[#output + 1] = operators[op_top].type
        op_top = op_top - 1
    end
    
    return output
end

-- 模拟 "3 + 5"
local tokens = {
    {type = TokenType.NUMBER, value = 3},
    {type = TokenType.PLUS, value = "+"}
}

print("\n执行算法:")
local postfix = infix_to_postfix(tokens)

print("\nOutput postfix:")
print("  length = " .. #postfix)
for i = 1, #postfix do
    local val = postfix[i]
    print("  [" .. i .. "] = " .. tostring(val) .. " (type: " .. type(val) .. ")")
end

print("\n测试:")
print("  postfix[2] == TokenType.PLUS? " .. tostring(postfix[2] == TokenType.PLUS))
if postfix[2] ~= TokenType.PLUS then
    print("  期望: " .. tostring(TokenType.PLUS))
    print("  实际: " .. tostring(postfix[2]))
end
