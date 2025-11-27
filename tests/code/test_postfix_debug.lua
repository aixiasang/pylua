-- 调试postfix问题

local TokenType = {
    NUMBER = 1,
    PLUS = 2,
    MULT = 3,
    LPAREN = 4,
    RPAREN = 5
}

local function get_precedence(op)
    if op == TokenType.MULT then
        return 2
    end
    return 0
end

local function infix_to_postfix(tokens)
    local output = {}
    local operators = {}
    local op_top = 0
    
    for i, token in ipairs(tokens) do
        if token.type == TokenType.NUMBER then
            output[#output + 1] = token.value
        elseif token.type == TokenType.PLUS or token.type == TokenType.MULT then
            while op_top > 0 and 
                  get_precedence(operators[op_top].type) >= get_precedence(token.type) do
                output[#output + 1] = operators[op_top].type
                op_top = op_top - 1
            end
            op_top = op_top + 1
            operators[op_top] = token
        end
    end
    
    while op_top > 0 do
        output[#output + 1] = operators[op_top].type
        op_top = op_top - 1
    end
    
    return output
end

-- 模拟 "3 + 5 * 2"
local tokens = {
    {type = TokenType.NUMBER, value = 3},
    {type = TokenType.PLUS, value = "+"},
    {type = TokenType.NUMBER, value = 5},
    {type = TokenType.MULT, value = "*"},
    {type = TokenType.NUMBER, value = 2}
}

print("Input tokens:")
for i, t in ipairs(tokens) do
    print("  " .. i .. ": type=" .. t.type .. ", value=" .. tostring(t.value))
end

local postfix = infix_to_postfix(tokens)

print("\nOutput postfix:")
print("  length = " .. #postfix)
for i = 1, #postfix do
    print("  " .. i .. ": " .. tostring(postfix[i]))
end

print("\nTests:")
print("  #postfix == 5? " .. tostring(#postfix == 5))
print("  postfix[1] == 3? " .. tostring(postfix[1] == 3))
print("  postfix[5] == TokenType.PLUS? " .. tostring(postfix[5] == TokenType.PLUS))
print("  postfix[5] value = " .. tostring(postfix[5]))
print("  TokenType.PLUS value = " .. tostring(TokenType.PLUS))
