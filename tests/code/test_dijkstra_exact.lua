-- 完全按照test_04的Dijkstra实现
print("=== Exact Dijkstra Test ===\n")

local function dijkstra(graph, start)
    local dist = {}
    local visited = {}
    local nodes = {}
    
    -- Initialize
    print("Before init: graph.A = " .. tostring(graph.A))
    for node in pairs(graph) do
        print("  Loop: node=" .. node .. ", graph.A=" .. tostring(graph.A))
        dist[node] = 999999
        print("    After dist: graph.A=" .. tostring(graph.A))
        nodes[#nodes + 1] = node
        print("    After nodes: graph.A=" .. tostring(graph.A))
    end
    print("After init: graph.A = " .. tostring(graph.A))
    dist[start] = 0
    print("After dist[start]=0: graph.A = " .. tostring(graph.A))
    
    while #nodes > 0 do
        -- Find min distance node
        local min_node = nil
        local min_dist = 999999
        local min_idx = -1
        
        for i, node in ipairs(nodes) do
            if dist[node] < min_dist then
                min_dist = dist[node]
                min_node = node
                min_idx = i
            end
        end
        
        if min_idx == -1 then
            break
        end
        
        -- Remove min node
        local temp = {}
        for i, n in ipairs(nodes) do
            if i ~= min_idx then
                temp[#temp + 1] = n
            end
        end
        nodes = temp
        
        visited[min_node] = true
        
        -- Update neighbors
        print("Processing " .. min_node .. ": graph[min_node] = " .. tostring(graph[min_node]))
        local min_neighbors = graph[min_node]
        if min_neighbors and type(min_neighbors) == "table" then
            for neighbor, weight in pairs(min_neighbors) do
                if not visited[neighbor] then
                    local new_dist = dist[min_node] + weight
                    if new_dist < dist[neighbor] then
                        dist[neighbor] = new_dist
                    end
                end
            end
        else
            print("  ERROR: neighbors is " .. type(min_neighbors))
        end
    end
    
    return dist
end

local dijkstra_graph = {
    A = {B = 4, C = 2},
    B = {A = 4, C = 1, D = 5},
    C = {A = 2, B = 1, D = 8, E = 10},
    D = {B = 5, C = 8, E = 2},
    E = {C = 10, D = 2}
}

local distances = dijkstra(dijkstra_graph, "A")

print("\nResults:")
print("  A: " .. distances.A .. " (expected 0) " .. (distances.A == 0 and "PASS" or "FAIL"))
print("  B: " .. distances.B .. " (expected 3) " .. (distances.B == 3 and "PASS" or "FAIL"))
print("  C: " .. distances.C .. " (expected 2) " .. (distances.C == 2 and "PASS" or "FAIL"))
print("  D: " .. distances.D .. " (expected 8) " .. (distances.D == 8 and "PASS" or "FAIL"))
print("  E: " .. distances.E .. " (expected 10) " .. (distances.E == 10 and "PASS" or "FAIL"))
