-- Debug Dijkstra 最小化测试
print("=== Dijkstra Debug Test ===")

-- 简化的Dijkstra
local function dijkstra_simple(graph, start)
    print("\n1. Input:")
    print("  start = " .. start)
    print("  graph type = " .. type(graph))
    
    -- 初始化
    local dist = {}
    local visited = {}
    local nodes = {}
    
    print("\n2. Initialize:")
    for node in pairs(graph) do
        print("  node = " .. node)
        dist[node] = 999999
        nodes[#nodes + 1] = node
    end
    dist[start] = 0
    
    print("\n3. After init:")
    print("  dist[A] = " .. tostring(dist.A))
    print("  #nodes = " .. #nodes)
    print("  graph.A type = " .. type(graph.A))
    
    -- 第一次迭代
    print("\n4. First iteration:")
    
    -- 找最小距离节点
    local min_node = start
    local min_idx = 1
    print("  min_node = " .. min_node)
    
    -- 从nodes移除
    local temp = {}
    for i = 2, #nodes do
        temp[#temp + 1] = nodes[i]
    end
    nodes = temp
    print("  After remove, #nodes = " .. #nodes)
    
    -- 标记已访问
    visited[min_node] = true
    print("  visited[" .. min_node .. "] = true")
    
    -- 获取邻居
    print("\n5. Get neighbors:")
    print("  Before: graph.A = " .. tostring(graph.A))
    
    local neighbors = graph[min_node]
    print("  neighbors = " .. tostring(neighbors))
    print("  type(neighbors) = " .. type(neighbors))
    
    print("  After: graph.A = " .. tostring(graph.A))
    
    if type(neighbors) == "table" then
        print("\n6. Iterate neighbors:")
        for neighbor, weight in pairs(neighbors) do
            print("  neighbor = " .. neighbor .. ", weight = " .. weight)
            if not visited[neighbor] then
                local new_dist = dist[min_node] + weight
                print("    new_dist = " .. new_dist)
                if new_dist < dist[neighbor] then
                    dist[neighbor] = new_dist
                    print("    Updated dist[" .. neighbor .. "] = " .. new_dist)
                end
            end
        end
    else
        print("  ERROR: neighbors is not a table!")
    end
    
    print("\n7. Final distances:")
    for node, d in pairs(dist) do
        print("  dist[" .. node .. "] = " .. d)
    end
    
    return dist
end

-- 测试数据
local graph = {
    A = {B = 4, C = 2},
    B = {A = 4, C = 1},
    C = {A = 2, B = 1}
}

print("\nGraph before:")
for k, v in pairs(graph) do
    print("  graph[" .. k .. "] = " .. tostring(v))
end

-- 运行测试
local distances = dijkstra_simple(graph, "A")

print("\n=== Results ===")
print("Expected: A=0, B=3, C=2")
print("Actual:   A=" .. distances.A .. ", B=" .. distances.B .. ", C=" .. distances.C)

local pass = distances.A == 0 and distances.B == 3 and distances.C == 2
print(pass and "\nPASS" or "\nFAIL")
