-- 完整Dijkstra调试
print("=== Full Dijkstra Debug ===\n")

local function dijkstra(graph, start)
    local dist = {}
    local visited = {}
    local nodes = {}
    
    -- Initialize
    print("Before init loop: graph.A = " .. tostring(graph.A))
    for node in pairs(graph) do
        print("  In loop, node=" .. node .. ", graph.A=" .. tostring(graph.A))
        dist[node] = 999999
        print("    After dist: graph.A=" .. tostring(graph.A))
        nodes[#nodes + 1] = node
        print("    After nodes: graph.A=" .. tostring(graph.A))
    end
    print("After init loop: graph.A = " .. tostring(graph.A))
    dist[start] = 0
    print("After dist[start]=0: graph.A = " .. tostring(graph.A))
    
    print("\nAfter init:")
    print("  dist.A=" .. dist.A .. ", dist.B=" .. dist.B .. ", dist.C=" .. dist.C)
    print("  #nodes=" .. #nodes)
    print()
    
    local iteration = 0
    while #nodes > 0 do
        iteration = iteration + 1
        print("Iteration " .. iteration .. ":")
        print("  At start: graph.A = " .. tostring(graph.A))
        
        -- Find min
        local min_node = nil
        local min_dist = 999999
        local min_idx = -1
        
        print("  Before find loop: graph.A = " .. tostring(graph.A))
        for i, node in ipairs(nodes) do
            if dist[node] < min_dist then
                min_dist = dist[node]
                min_node = node
                min_idx = i
            end
        end
        print("  After find loop: graph.A = " .. tostring(graph.A))
        
        if min_idx == -1 then
            print("  No min found, break")
            break
        end
        
        print("  Processing node: " .. min_node .. ", dist=" .. min_dist)
        print("  Before remove: graph.A = " .. tostring(graph.A))
        
        -- Remove node
        local temp = {}
        for i, n in ipairs(nodes) do
            if i ~= min_idx then
                temp[#temp + 1] = n
            end
        end
        print("  After temp build: graph.A = " .. tostring(graph.A))
        nodes = temp
        print("  After nodes=temp: graph.A = " .. tostring(graph.A))
        
        print("  Before visited: graph.A = " .. tostring(graph.A))
        visited[min_node] = true
        print("  After visited: graph.A = " .. tostring(graph.A))
        
        -- Update neighbors
        print("  Getting neighbors for: " .. min_node)
        print("  graph." .. min_node .. " = " .. tostring(graph[min_node]))
        local min_neighbors = graph[min_node]
        print("  min_neighbors = " .. tostring(min_neighbors))
        print("  type(min_neighbors) = " .. type(min_neighbors))
        if min_neighbors and type(min_neighbors) == "table" then
            print("  Neighbors:")
            for neighbor, weight in pairs(min_neighbors) do
                print("    " .. neighbor .. " (weight=" .. weight .. ")")
                if not visited[neighbor] then
                    local new_dist = dist[min_node] + weight
                    if new_dist < dist[neighbor] then
                        print("      Update: " .. dist[neighbor] .. " -> " .. new_dist)
                        dist[neighbor] = new_dist
                    end
                end
            end
        end
        print()
    end
    
    return dist
end

-- 测试图
local dijkstra_graph = {
    A = {B = 4, C = 2},
    B = {A = 4, C = 1, D = 5},
    C = {A = 2, B = 1, D = 8, E = 10},
    D = {B = 5, C = 8, E = 2},
    E = {C = 10, D = 2}
}

print("Graph:")
for node, neighbors in pairs(dijkstra_graph) do
    local line = "  " .. node .. ": "
    for n, w in pairs(neighbors) do
        line = line .. n .. "=" .. w .. " "
    end
    print(line)
end
print()

local distances = dijkstra(dijkstra_graph, "A")

print("Results:")
print("  A: " .. distances.A .. " (expected 0)")
print("  B: " .. distances.B .. " (expected 3)")
print("  C: " .. distances.C .. " (expected 2)")
print("  D: " .. distances.D .. " (expected 8)")
print("  E: " .. distances.E .. " (expected 10)")

local all_pass = distances.A == 0 and 
                 distances.B == 3 and 
                 distances.C == 2 and 
                 distances.D == 8 and 
                 distances.E == 10

print(all_pass and "\nALL PASS" or "\nSOME FAIL")
