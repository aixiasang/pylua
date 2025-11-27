-- 完整的postfix算法调试

local TokenType = {
    NUMBER = "NUMBER",
    PLUS = "PLUS",
    MULT = "MULT"
}

local function get_precedence(op)
    if op == TokenType.MULT then
        return 2
    elseif op == TokenType.PLUS then
        return 1
    end
    return 0
end

local function infix_to_postfix(tokens)
    local output = {}
    local operators = {}
    local op_top = 0
    
    print("开始转换:")
    for i, token in ipairs(tokens) do
        print("  处理token[" .. i .. "]: type=" .. token.type)
        
        if token.type == TokenType.NUMBER then
            print("    -> 添加到output: " .. token.value)
            output[#output + 1] = token.value
        elseif token.type == TokenType.PLUS or token.type == TokenType.MULT then
            print("    -> 操作符, precedence=" .. get_precedence(token.type))
            
            while op_top > 0 and
                  get_precedence(operators[op_top].type) >= get_precedence(token.type) do
                print("    -> 弹出操作符: " .. operators[op_top].type)
                output[#output + 1] = operators[op_top].type
                op_top = op_top - 1
            end
            
            op_top = op_top + 1
            operators[op_top] = token
            print("    -> 压入操作符栈, op_top=" .. op_top)
        end
    end
    
    print("弹出剩余操作符:")
    while op_top > 0 do
        print("  弹出: " .. operators[op_top].type)
        output[#output + 1] = operators[op_top].type
        op_top = op_top - 1
    end
    
    return output
end

-- 测试 "3 + 5 * 2"
print("=== 测试: 3 + 5 * 2 ===\n")
local tokens = {
    {type = TokenType.NUMBER, value = 3},
    {type = TokenType.PLUS, value = "+"},
    {type = TokenType.NUMBER, value = 5},
    {type = TokenType.MULT, value = "*"},
    {type = TokenType.NUMBER, value = 2}
}

local postfix = infix_to_postfix(tokens)

print("\n结果:")
print("  length = " .. #postfix)
for i = 1, #postfix do
    print("  [" .. i .. "] = " .. tostring(postfix[i]))
end

print("\n验证:")
print("  期望: 3, 5, 2, *, +")
print("  实际: " .. tostring(postfix[1]) .. ", " .. tostring(postfix[2]) .. ", " .. 
      tostring(postfix[3]) .. ", " .. tostring(postfix[4]) .. ", " .. tostring(postfix[5]))

print("\n测试结果:")
print("  postfix[1] == 3? " .. tostring(postfix[1] == 3))
print("  postfix[5] == 'PLUS'? " .. tostring(postfix[5] == TokenType.PLUS))
print("  postfix[5] == " .. tostring(postfix[5]))
print("  TokenType.PLUS == " .. tostring(TokenType.PLUS))
