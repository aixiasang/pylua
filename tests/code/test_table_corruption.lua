-- 测试表是否在pairs循环中被破坏
print("=== Table Corruption Test ===\n")

local graph = {
    A = {x = 1},
    B = {y = 2},
    C = {z = 3}
}

print("Before loop:")
print("  graph.A = " .. tostring(graph.A))
print("  graph.B = " .. tostring(graph.B))
print("  graph.C = " .. tostring(graph.C))
print()

-- 创建另一个表并在循环中赋值
local dist = {}
local nodes = {}

print("During loop:")
for node in pairs(graph) do
    print("  Iteration: node = " .. tostring(node) .. ", type = " .. type(node))
    print("    Before: graph.A = " .. tostring(graph.A))
    
    dist[node] = 999999
    
    print("    After dist[node]=999999: graph.A = " .. tostring(graph.A))
    
    nodes[#nodes + 1] = node
    
    print("    After nodes append: graph.A = " .. tostring(graph.A))
    print()
end

print("After loop:")
print("  graph.A = " .. tostring(graph.A))
print("  graph.B = " .. tostring(graph.B))
print("  graph.C = " .. tostring(graph.C))
print()

print("dist table:")
for k, v in pairs(dist) do
    print("  dist[" .. tostring(k) .. "] = " .. tostring(v))
end
print()

print("nodes array:")
for i, v in ipairs(nodes) do
    print("  nodes[" .. i .. "] = " .. tostring(v))
end
