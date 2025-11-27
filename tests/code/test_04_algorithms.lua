-- ============================================================================
-- Advanced Algorithms Test Suite (~800 lines)
-- Tests: Sorting, Searching, Dynamic Programming, Graph Algorithms
-- ============================================================================

print("=== Advanced Algorithms Test Suite ===\n")

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
-- 1. Sorting Algorithms
-- ============================================================================
print("\n[1] Sorting Algorithms")

-- Bubble Sort
local function bubble_sort(arr)
    local n = #arr
    for i = 1, n do
        for j = 1, n - i do
            if arr[j] > arr[j + 1] then
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
            end
        end
    end
    return arr
end

-- Insertion Sort
local function insertion_sort(arr)
    for i = 2, #arr do
        local key = arr[i]
        local j = i - 1
        while j > 0 and arr[j] > key do
            arr[j + 1] = arr[j]
            j = j - 1
        end
        arr[j + 1] = key
    end
    return arr
end

-- Merge Sort
local function merge_sort(arr)
    if #arr <= 1 then
        return arr
    end
    
    local mid = #arr // 2
    local left = {}
    local right = {}
    
    for i = 1, mid do
        left[i] = arr[i]
    end
    
    for i = mid + 1, #arr do
        right[i - mid] = arr[i]
    end
    
    left = merge_sort(left)
    right = merge_sort(right)
    
    local result = {}
    local i, j = 1, 1
    
    while i <= #left and j <= #right do
        if left[i] <= right[j] then
            result[#result + 1] = left[i]
            i = i + 1
        else
            result[#result + 1] = right[j]
            j = j + 1
        end
    end
    
    while i <= #left do
        result[#result + 1] = left[i]
        i = i + 1
    end
    
    while j <= #right do
        result[#result + 1] = right[j]
        j = j + 1
    end
    
    return result
end

-- Quick Sort
local function quick_sort(arr, low, high)
    if low >= high then
        return arr
    end
    
    local pivot = arr[high]
    local i = low - 1
    
    for j = low, high - 1 do
        if arr[j] < pivot then
            i = i + 1
            arr[i], arr[j] = arr[j], arr[i]
        end
    end
    
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    local pi = i + 1
    
    quick_sort(arr, low, pi - 1)
    quick_sort(arr, pi + 1, high)
    
    return arr
end

-- Test Sorting
local test_arr = {64, 34, 25, 12, 22, 11, 90}
local sorted = bubble_sort({64, 34, 25, 12, 22, 11, 90})
test("bubble sort", sorted[1] == 11 and sorted[7] == 90)

sorted = insertion_sort({64, 34, 25, 12, 22, 11, 90})
test("insertion sort", sorted[1] == 11 and sorted[7] == 90)

sorted = merge_sort({64, 34, 25, 12, 22, 11, 90})
test("merge sort", sorted[1] == 11 and sorted[7] == 90)

local qsort_arr = {64, 34, 25, 12, 22, 11, 90}
quick_sort(qsort_arr, 1, 7)
test("quick sort", qsort_arr[1] == 11 and qsort_arr[7] == 90)

-- ============================================================================
-- 2. Binary Search
-- ============================================================================
print("\n[2] Binary Search")

local function binary_search(arr, target)
    local left, right = 1, #arr
    
    while left <= right do
        local mid = (left + right) // 2
        
        if arr[mid] == target then
            return mid
        elseif arr[mid] < target then
            left = mid + 1
        else
            right = mid - 1
        end
    end
    
    return -1
end

local sorted_arr = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19}
test("binary search found", binary_search(sorted_arr, 7) == 4)
test("binary search not found", binary_search(sorted_arr, 8) == -1)
test("binary search first", binary_search(sorted_arr, 1) == 1)
test("binary search last", binary_search(sorted_arr, 19) == 10)

-- ============================================================================
-- 3. Dynamic Programming - Fibonacci
-- ============================================================================
print("\n[3] Dynamic Programming")

-- Fibonacci with memoization
local function fib_memo(n, memo)
    memo = memo or {}
    
    if n <= 2 then
        return 1
    end
    
    if memo[n] then
        return memo[n]
    end
    
    memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
    return memo[n]
end

-- Fibonacci iterative
local function fib_iter(n)
    if n <= 2 then
        return 1
    end
    
    local a, b = 1, 1
    for i = 3, n do
        a, b = b, a + b
    end
    
    return b
end

test("fib memo 10", fib_memo(10) == 55)
test("fib memo 15", fib_memo(15) == 610)
test("fib iter 10", fib_iter(10) == 55)
test("fib iter 15", fib_iter(15) == 610)

-- ============================================================================
-- 4. Longest Common Subsequence
-- ============================================================================
print("\n[4] Longest Common Subsequence")

local function lcs(s1, s2)
    local m, n = #s1, #s2
    local dp = {}
    
    for i = 0, m do
        dp[i] = {}
        for j = 0, n do
            dp[i][j] = 0
        end
    end
    
    for i = 1, m do
        for j = 1, n do
            if s1:sub(i, i) == s2:sub(j, j) then
                dp[i][j] = dp[i-1][j-1] + 1
            else
                local val1 = dp[i-1][j]
                local val2 = dp[i][j-1]
                dp[i][j] = (val1 > val2) and val1 or val2
            end
        end
    end
    
    return dp[m][n]
end

test("lcs simple", lcs("ABCDEF", "ACDGEF") == 5)
test("lcs equal", lcs("HELLO", "HELLO") == 5)
test("lcs different", lcs("ABC", "DEF") == 0)

-- ============================================================================
-- 5. Edit Distance (Levenshtein Distance)
-- ============================================================================
print("\n[5] Edit Distance")

local function edit_distance(s1, s2)
    local m, n = #s1, #s2
    local dp = {}
    
    for i = 0, m do
        dp[i] = {}
        dp[i][0] = i
    end
    
    for j = 0, n do
        dp[0][j] = j
    end
    
    for i = 1, m do
        for j = 1, n do
            if s1:sub(i, i) == s2:sub(j, j) then
                dp[i][j] = dp[i-1][j-1]
            else
                local insert = dp[i][j-1]
                local delete = dp[i-1][j]
                local replace = dp[i-1][j-1]
                
                local min_val = insert
                if delete < min_val then min_val = delete end
                if replace < min_val then min_val = replace end
                
                dp[i][j] = 1 + min_val
            end
        end
    end
    
    return dp[m][n]
end

test("edit distance same", edit_distance("kitten", "kitten") == 0)
test("edit distance 1", edit_distance("kitten", "sitting") == 3)
test("edit distance 2", edit_distance("saturday", "sunday") == 3)

-- ============================================================================
-- 6. Knapsack Problem
-- ============================================================================
print("\n[6] Knapsack Problem")

local function knapsack(weights, values, capacity)
    local n = #weights
    local dp = {}
    
    for i = 0, n do
        dp[i] = {}
        for w = 0, capacity do
            dp[i][w] = 0
        end
    end
    
    for i = 1, n do
        for w = 0, capacity do
            if weights[i] <= w then
                local include = values[i] + dp[i-1][w - weights[i]]
                local exclude = dp[i-1][w]
                dp[i][w] = (include > exclude) and include or exclude
            else
                dp[i][w] = dp[i-1][w]
            end
        end
    end
    
    return dp[n][capacity]
end

local weights = {2, 3, 4, 5}
local values = {3, 4, 5, 6}
local capacity = 5

test("knapsack", knapsack(weights, values, capacity) == 7)

-- ============================================================================
-- 7. Graph - Dijkstra's Shortest Path
-- ============================================================================
print("\n[7] Dijkstra's Algorithm")

local function dijkstra(graph, start)
    local dist = {}
    local visited = {}
    local nodes = {}
    
    -- Initialize - workaround: store graph reference
    local g = graph
    for node in pairs(g) do
        dist[node] = 999999
        nodes[#nodes + 1] = node
    end
    dist[start] = 0
    
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
        local min_neighbors = g[min_node]
        if min_neighbors and type(min_neighbors) == "table" then
            for neighbor, weight in pairs(min_neighbors) do
                if not visited[neighbor] then
                    local new_dist = dist[min_node] + weight
                    if new_dist < dist[neighbor] then
                        dist[neighbor] = new_dist
                    end
                end
            end
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
test("dijkstra A to A", distances.A == 0)
test("dijkstra A to B", distances.B == 3)
test("dijkstra A to C", distances.C == 2)
test("dijkstra A to D", distances.D == 8)
test("dijkstra A to E", distances.E == 10)

-- ============================================================================
-- 8. Backtracking - N-Queens
-- ============================================================================
print("\n[8] N-Queens Problem")

local function is_safe(board, row, col, n)
    -- Check column
    for i = 1, row - 1 do
        if board[i] == col then
            return false
        end
    end
    
    -- Check diagonals
    for i = 1, row - 1 do
        if board[i] - i == col - row or board[i] + i == col + row then
            return false
        end
    end
    
    return true
end

local function solve_n_queens(n)
    local board = {}
    local solutions = 0
    
    local function backtrack(row)
        if row > n then
            solutions = solutions + 1
            return
        end
        
        for col = 1, n do
            if is_safe(board, row, col, n) then
                board[row] = col
                backtrack(row + 1)
                board[row] = nil
            end
        end
    end
    
    backtrack(1)
    return solutions
end

test("n-queens 4x4", solve_n_queens(4) == 2)
test("n-queens 5x5", solve_n_queens(5) == 10)
test("n-queens 6x6", solve_n_queens(6) == 4)

-- ============================================================================
-- 9. String Matching - KMP Algorithm
-- ============================================================================
print("\n[9] String Matching")

local function compute_lps(pattern)
    local m = #pattern
    local lps = {}
    lps[1] = 0
    local len = 0
    local i = 2
    
    while i <= m do
        if pattern:sub(i, i) == pattern:sub(len + 1, len + 1) then
            len = len + 1
            lps[i] = len
            i = i + 1
        else
            if len ~= 0 then
                len = lps[len]
            else
                lps[i] = 0
                i = i + 1
            end
        end
    end
    
    return lps
end

local function kmp_search(text, pattern)
    local n = #text
    local m = #pattern
    local lps = compute_lps(pattern)
    local matches = {}
    
    local i = 1
    local j = 1
    
    while i <= n do
        if pattern:sub(j, j) == text:sub(i, i) then
            i = i + 1
            j = j + 1
        end
        
        if j > m then
            matches[#matches + 1] = i - j
            j = lps[j - 1] or 0
            if j == 0 then j = 1 end
        elseif i <= n and pattern:sub(j, j) ~= text:sub(i, i) then
            if j ~= 1 then
                j = (lps[j - 1] or 0) + 1
            else
                i = i + 1
            end
        end
    end
    
    return matches
end

local matches = kmp_search("ABABDABACDABABCABAB", "ABABCABAB")
test("kmp search found", #matches > 0)

matches = kmp_search("HELLO WORLD", "WORLD")
test("kmp search single", #matches == 1)

matches = kmp_search("HELLO WORLD", "NOTFOUND")
test("kmp search not found", #matches == 0)

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
    print("\n*** ALL ALGORITHM TESTS PASSED ***")
else
    print("\n*** SOME TESTS FAILED ***")
end
