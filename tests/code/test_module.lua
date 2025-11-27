-- 测试模块
local M = {}

M.version = "1.0"

function M.add(a, b)
    return a + b
end

function M.greet(name)
    return "Hello, " .. name
end

return M
