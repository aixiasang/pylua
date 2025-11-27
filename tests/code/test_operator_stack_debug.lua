-- 调试操作符栈

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
        print("\n处理token[" .. i .. "]: type=" .. token.type)
        
        if token.type == TokenType.NUMBER then
            print("  添加到output: " .. token.value)
            output[#output + 1] = token.value
            print("  output现在: {" .. table.concat(output, ", ") .. "}")
        elseif token.type == TokenType.PLUS or token.type == TokenType.MULT then
            print("  操作符, precedence=" .. get_precedence(token.type))
            
            -- 弹出优先级更高或相等的操作符
            while op_top > 0 and
                  get_precedence(operators[op_top].type) >= get_precedence(token.type) do
                print("  弹出操作符: " .. operators[op_top].type)
                output[#output + 1] = operators[op_top].type
                op_top = op_top - 1
            end
            
            -- 压入当前操作符
            op_top = op_top + 1
            operators[op_top] = token
            print("  压入操作符: " .. token.type)
            print("  操作符栈 (top=" .. op_top .. "):")
            for j = 1, op_top do
                print("    [" .. j .. "] = " .. operators[j].type)
            end
        end
    end
    
    print("\n弹出剩余操作符 (op_top=" .. op_top .. "):")
    while op_top > 0 do
        print("  operators[" .. op_top .. "] = " .. operators[op_top].type)
        output[#output + 1] = operators[op_top].type
        print("  添加到output: " .. operators[op_top].type)
        op_top = op_top - 1
    end
    
    return output
end

-- 测试 "3 + 5 * 2"
print("=== 测试: 3 + 5 * 2 ===")
local tokens = {
    {type = TokenType.NUMBER, value = 3},
    {type = TokenType.PLUS, value = "+"},
    {type = TokenType.NUMBER, value = 5},
    {type = TokenType.MULT, value = "*"},
    {type = TokenType.NUMBER, value = 2}
}

local postfix = infix_to_postfix(tokens)

print("\n最终结果:")
for i = 1, #postfix do
    print("  [" .. i .. "] = " .. tostring(postfix[i]))
end

print("\n验证:")
print("  期望: [1]=3, [2]=5, [3]=2, [4]=MULT, [5]=PLUS")
print("  实际: [1]=" .. tostring(postfix[1]) .. ", [2]=" .. tostring(postfix[2]) .. ", [3]=" .. tostring(postfix[3]) .. ", [4]=" .. tostring(postfix[4]) .. ", [5]=" .. tostring(postfix[5]))
