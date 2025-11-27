-- ============================================================================
-- Expression Evaluator & Mini Calculator (~700 lines)
-- Tests: Tokenizer, Parser, Expression Evaluation, Variables
-- ============================================================================

print("=== Expression Evaluator Test Suite ===\n")

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

-- ============================================================================
-- 1. Tokenizer
-- ============================================================================
print("\n[1] Tokenizer")

local TokenType = {
    NUMBER = "NUMBER",
    PLUS = "PLUS",
    MINUS = "MINUS",
    MULT = "MULT",
    DIV = "DIV",
    LPAREN = "LPAREN",
    RPAREN = "RPAREN",
    IDENT = "IDENT",
    ASSIGN = "ASSIGN",
    EOF = "EOF"
}

local function tokenize(input)
    local tokens = {}
    local pos = 1
    local len = #input
    
    while pos <= len do
        local char = input:sub(pos, pos)
        
        if char == " " or char == "\t" or char == "\n" then
            pos = pos + 1
        elseif char >= "0" and char <= "9" then
            local num = ""
            while pos <= len and ((input:sub(pos, pos) >= "0" and input:sub(pos, pos) <= "9") or input:sub(pos, pos) == ".") do
                num = num .. input:sub(pos, pos)
                pos = pos + 1
            end
            tokens[#tokens + 1] = {type = TokenType.NUMBER, value = tonumber(num)}
        elseif char >= "a" and char <= "z" or char >= "A" and char <= "Z" then
            local ident = ""
            while pos <= len do
                local c = input:sub(pos, pos)
                if (c >= "a" and c <= "z") or (c >= "A" and c <= "Z") or 
                   (c >= "0" and c <= "9") or c == "_" then
                    ident = ident .. c
                    pos = pos + 1
                else
                    break
                end
            end
            tokens[#tokens + 1] = {type = TokenType.IDENT, value = ident}
        elseif char == "+" then
            tokens[#tokens + 1] = {type = TokenType.PLUS}
            pos = pos + 1
        elseif char == "-" then
            tokens[#tokens + 1] = {type = TokenType.MINUS}
            pos = pos + 1
        elseif char == "*" then
            tokens[#tokens + 1] = {type = TokenType.MULT}
            pos = pos + 1
        elseif char == "/" then
            tokens[#tokens + 1] = {type = TokenType.DIV}
            pos = pos + 1
        elseif char == "(" then
            tokens[#tokens + 1] = {type = TokenType.LPAREN}
            pos = pos + 1
        elseif char == ")" then
            tokens[#tokens + 1] = {type = TokenType.RPAREN}
            pos = pos + 1
        elseif char == "=" then
            tokens[#tokens + 1] = {type = TokenType.ASSIGN}
            pos = pos + 1
        else
            pos = pos + 1
        end
    end
    
    tokens[#tokens + 1] = {type = TokenType.EOF}
    return tokens
end

-- Test Tokenizer
local tokens = tokenize("3 + 5 * 2")
test("tokenize count", #tokens == 6)
test("tokenize first", tokens[1].type == TokenType.NUMBER and tokens[1].value == 3)
test("tokenize plus", tokens[2].type == TokenType.PLUS)
test("tokenize mult", tokens[4].type == TokenType.MULT)

-- ============================================================================
-- 2. Expression Parser & Evaluator
-- ============================================================================
print("\n[2] Expression Parser")

local Parser = {}
Parser.__index = Parser

function Parser.new(tokens)
    local self = setmetatable({}, Parser)
    self.tokens = tokens
    self.pos = 1
    self.variables = {}
    return self
end

function Parser:current()
    return self.tokens[self.pos]
end

function Parser:consume(expected_type)
    local token = self:current()
    if expected_type and token.type ~= expected_type then
        error("Expected " .. expected_type .. " but got " .. token.type)
    end
    self.pos = self.pos + 1
    return token
end

function Parser:parse_number()
    local token = self:consume(TokenType.NUMBER)
    return {type = "number", value = token.value}
end

function Parser:parse_ident()
    local token = self:consume(TokenType.IDENT)
    return {type = "ident", name = token.value}
end

function Parser:parse_factor()
    local token = self:current()
    
    if token.type == TokenType.NUMBER then
        return self:parse_number()
    elseif token.type == TokenType.IDENT then
        return self:parse_ident()
    elseif token.type == TokenType.LPAREN then
        self:consume(TokenType.LPAREN)
        local expr = self:parse_expression()
        self:consume(TokenType.RPAREN)
        return expr
    elseif token.type == TokenType.MINUS then
        self:consume(TokenType.MINUS)
        local factor = self:parse_factor()
        return {type = "unary", op = "-", operand = factor}
    end
    
    error("Unexpected token: " .. token.type)
end

function Parser:parse_term()
    local left = self:parse_factor()
    
    while self:current().type == TokenType.MULT or self:current().type == TokenType.DIV do
        local op = self:consume().type
        local right = self:parse_factor()
        left = {type = "binary", op = op, left = left, right = right}
    end
    
    return left
end

function Parser:parse_expression()
    local left = self:parse_term()
    
    while self:current().type == TokenType.PLUS or self:current().type == TokenType.MINUS do
        local op = self:consume().type
        local right = self:parse_term()
        left = {type = "binary", op = op, left = left, right = right}
    end
    
    return left
end

function Parser:parse_assignment()
    local token = self:current()
    
    if token.type == TokenType.IDENT then
        local next_token = self.tokens[self.pos + 1]
        if next_token and next_token.type == TokenType.ASSIGN then
            local name = self:consume(TokenType.IDENT).value
            self:consume(TokenType.ASSIGN)
            local expr = self:parse_expression()
            return {type = "assignment", name = name, value = expr}
        end
    end
    
    return self:parse_expression()
end

function Parser:evaluate(node)
    if node.type == "number" then
        return node.value
    elseif node.type == "ident" then
        local val = self.variables[node.name]
        if val == nil then
            error("Undefined variable: " .. node.name)
        end
        return val
    elseif node.type == "unary" then
        local operand = self:evaluate(node.operand)
        if node.op == "-" then
            return -operand
        end
    elseif node.type == "binary" then
        local left = self:evaluate(node.left)
        local right = self:evaluate(node.right)
        
        if node.op == TokenType.PLUS then
            return left + right
        elseif node.op == TokenType.MINUS then
            return left - right
        elseif node.op == TokenType.MULT then
            return left * right
        elseif node.op == TokenType.DIV then
            return left / right
        end
    elseif node.type == "assignment" then
        local value = self:evaluate(node.value)
        self.variables[node.name] = value
        return value
    end
    
    error("Unknown node type: " .. node.type)
end

function Parser:parse_and_eval()
    local ast = self:parse_assignment()
    return self:evaluate(ast)
end

-- Test Parser
local function eval_expr(expr)
    local tokens = tokenize(expr)
    local parser = Parser.new(tokens)
    return parser:parse_and_eval()
end

test("eval simple", eval_expr("2 + 3") == 5)
test("eval mult", eval_expr("2 * 3") == 6)
test("eval precedence", eval_expr("2 + 3 * 4") == 14)
test("eval paren", eval_expr("(2 + 3) * 4") == 20)
test("eval complex", eval_expr("10 + 2 * 6") == 22)
test("eval div", eval_expr("100 / 4") == 25)
test("eval minus", eval_expr("20 - 5 - 3") == 12)
test("eval unary", eval_expr("-5 + 3") == -2)

-- Test Variables
local tokens = tokenize("x = 10")
local parser = Parser.new(tokens)
local result = parser:parse_and_eval()
test("assignment", result == 10 and parser.variables.x == 10)

tokens = tokenize("x + 5")
parser.tokens = tokens
parser.pos = 1
result = parser:parse_and_eval()
test("use variable", result == 15)

-- ============================================================================
-- 3. RPN Calculator (Reverse Polish Notation)
-- ============================================================================
print("\n[3] RPN Calculator")

local function eval_rpn(tokens)
    local stack = {}
    
    for i, token in ipairs(tokens) do
        if type(token) == "number" then
            stack[#stack + 1] = token
        else
            local b = stack[#stack]
            stack[#stack] = nil
            local a = stack[#stack]
            stack[#stack] = nil
            
            if token == "+" then
                stack[#stack + 1] = a + b
            elseif token == "-" then
                stack[#stack + 1] = a - b
            elseif token == "*" then
                stack[#stack + 1] = a * b
            elseif token == "/" then
                stack[#stack + 1] = a / b
            end
        end
    end
    
    return stack[1]
end

test("rpn simple", eval_rpn({2, 3, "+"}) == 5)
test("rpn complex", eval_rpn({15, 7, 1, 1, "+", "-", "/", 3, "*"}) == 9)
test("rpn mult", eval_rpn({5, 1, 2, "+", 4, "*", "+", 3, "-"}) == 14)

-- ============================================================================
-- 4. Infix to Postfix Conversion
-- ============================================================================
print("\n[4] Infix to Postfix")

local function get_precedence(op)
    if op == TokenType.PLUS or op == TokenType.MINUS then
        return 1
    elseif op == TokenType.MULT or op == TokenType.DIV then
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
        elseif token.type == TokenType.IDENT then
            output[#output + 1] = token.value
        elseif token.type == TokenType.LPAREN then
            op_top = op_top + 1
            operators[op_top] = token
        elseif token.type == TokenType.RPAREN then
            while op_top > 0 and operators[op_top].type ~= TokenType.LPAREN do
                output[#output + 1] = operators[op_top].type
                op_top = op_top - 1
            end
            op_top = op_top - 1  -- Pop left paren
        elseif token.type == TokenType.PLUS or token.type == TokenType.MINUS or 
               token.type == TokenType.MULT or token.type == TokenType.DIV then
            while op_top > 0 and operators[op_top].type ~= TokenType.LPAREN and
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

local tokens = tokenize("3 + 5 * 2")
local postfix = infix_to_postfix(tokens)
test("postfix length", #postfix == 5)
test("postfix first", postfix[1] == 3)
test("postfix last", postfix[5] == TokenType.PLUS)

-- ============================================================================
-- 5. Function Evaluator
-- ============================================================================
print("\n[5] Function Evaluator")

local MathEval = {}
MathEval.__index = MathEval

function MathEval.new()
    local self = setmetatable({}, MathEval)
    self.functions = {
        abs = function(x) return x < 0 and -x or x end,
        max = function(a, b) return a > b and a or b end,
        min = function(a, b) return a < b and a or b end,
        pow = function(a, b) return a ^ b end,
        sqrt = function(x)
            if x < 0 then return nil end
            local guess = x / 2
            for i = 1, 10 do
                guess = (guess + x / guess) / 2
            end
            return guess
        end
    }
    return self
end

function MathEval:call(name, args)
    local func = self.functions[name]
    if not func then
        error("Unknown function: " .. name)
    end
    
    if #args == 1 then
        return func(args[1])
    elseif #args == 2 then
        return func(args[1], args[2])
    end
end

local math_eval = MathEval.new()
test("func abs", math_eval:call("abs", {-5}) == 5)
test("func max", math_eval:call("max", {10, 20}) == 20)
test("func min", math_eval:call("min", {10, 20}) == 10)
test("func pow", math_eval:call("pow", {2, 3}) == 8)

local sqrt_result = math_eval:call("sqrt", {16})
test("func sqrt", sqrt_result > 3.99 and sqrt_result < 4.01)

-- ============================================================================
-- 6. Expression Tree Visualization
-- ============================================================================
print("\n[6] Expression Tree")

local function tree_to_string(node, depth)
    depth = depth or 0
    local indent = string.rep("  ", depth)
    
    if node.type == "number" then
        return indent .. tostring(node.value)
    elseif node.type == "ident" then
        return indent .. node.name
    elseif node.type == "binary" then
        local result = indent .. node.op .. "\n"
        result = result .. tree_to_string(node.left, depth + 1) .. "\n"
        result = result .. tree_to_string(node.right, depth + 1)
        return result
    end
    
    return indent .. "?"
end

local tokens = tokenize("3 + 5 * 2")
local parser = Parser.new(tokens)
local ast = parser:parse_expression()
local tree_str = tree_to_string(ast)
test("tree not empty", #tree_str > 0)

-- ============================================================================
-- TEST SUMMARY
-- ============================================================================
print("\n" .. string.rep("=", 60))
print("TEST SUMMARY")
print(string.rep("=", 60))
print("Total tests: " .. test_count)
print("Passed: " .. pass_count)
print("Failed: " .. (test_count - pass_count))
print("Success rate: " .. string.format("%.1f%%", (pass_count / test_count) * 100))
print(string.rep("=", 60))

if pass_count == test_count then
    print("\n*** ALL EXPRESSION EVALUATOR TESTS PASSED ***")
else
    print("\n*** SOME TESTS FAILED ***")
end
