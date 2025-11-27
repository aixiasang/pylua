-- ============================================================================
-- Data Structures Implementation Test (~600 lines)
-- Tests: Linked List, Binary Search Tree, Stack, Queue, Graph
-- ============================================================================

print("=== Data Structures Test Suite ===\n")

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
-- 1. Linked List Implementation
-- ============================================================================
print("\n[1] Linked List")

local LinkedList = {}
LinkedList.__index = LinkedList

function LinkedList.new()
    local self = setmetatable({}, LinkedList)
    self.head = nil
    self.size = 0
    return self
end

function LinkedList:append(value)
    local node = {value = value, next = nil}
    
    if not self.head then
        self.head = node
    else
        local current = self.head
        while current.next do
            current = current.next
        end
        current.next = node
    end
    
    self.size = self.size + 1
end

function LinkedList:get(index)
    if index < 1 or index > self.size then
        return nil
    end
    
    local current = self.head
    for i = 1, index - 1 do
        current = current.next
    end
    
    return current.value
end

function LinkedList:remove(index)
    if index < 1 or index > self.size then
        return false
    end
    
    if index == 1 then
        self.head = self.head.next
    else
        local current = self.head
        for i = 1, index - 2 do
            current = current.next
        end
        current.next = current.next.next
    end
    
    self.size = self.size - 1
    return true
end

function LinkedList:to_array()
    local arr = {}
    local current = self.head
    while current do
        arr[#arr + 1] = current.value
        current = current.next
    end
    return arr
end

-- Test LinkedList
local list = LinkedList.new()
test("list initial size", list.size == 0)

list:append(10)
list:append(20)
list:append(30)
test("list after append", list.size == 3)
test("list get index 1", list:get(1) == 10)
test("list get index 2", list:get(2) == 20)
test("list get index 3", list:get(3) == 30)

list:remove(2)
test("list after remove", list.size == 2)
test("list get after remove", list:get(2) == 30)

local arr = list:to_array()
test("list to array", arr[1] == 10 and arr[2] == 30)

-- ============================================================================
-- 2. Stack Implementation
-- ============================================================================
print("\n[2] Stack")

local Stack = {}
Stack.__index = Stack

function Stack.new()
    local self = setmetatable({}, Stack)
    self.items = {}
    self.top = 0
    return self
end

function Stack:push(value)
    self.top = self.top + 1
    self.items[self.top] = value
end

function Stack:pop()
    if self.top == 0 then
        return nil
    end
    
    local value = self.items[self.top]
    self.items[self.top] = nil
    self.top = self.top - 1
    return value
end

function Stack:peek()
    if self.top == 0 then
        return nil
    end
    return self.items[self.top]
end

function Stack:is_empty()
    return self.top == 0
end

-- Test Stack
local stack = Stack.new()
test("stack initial empty", stack:is_empty())

stack:push(1)
stack:push(2)
stack:push(3)
test("stack peek", stack:peek() == 3)
test("stack size", stack.top == 3)

local val = stack:pop()
test("stack pop value", val == 3)
test("stack after pop", stack:peek() == 2)

-- ============================================================================
-- 3. Queue Implementation
-- ============================================================================
print("\n[3] Queue")

local Queue = {}
Queue.__index = Queue

function Queue.new()
    local self = setmetatable({}, Queue)
    self.items = {}
    self.head = 1
    self.tail = 0
    return self
end

function Queue:enqueue(value)
    self.tail = self.tail + 1
    self.items[self.tail] = value
end

function Queue:dequeue()
    if self.head > self.tail then
        return nil
    end
    
    local value = self.items[self.head]
    self.items[self.head] = nil
    self.head = self.head + 1
    return value
end

function Queue:is_empty()
    return self.head > self.tail
end

function Queue:size()
    return self.tail - self.head + 1
end

-- Test Queue
local queue = Queue.new()
test("queue initial empty", queue:is_empty())

queue:enqueue(1)
queue:enqueue(2)
queue:enqueue(3)
test("queue size", queue:size() == 3)

local v1 = queue:dequeue()
test("queue dequeue", v1 == 1)
test("queue after dequeue", queue:size() == 2)

-- ============================================================================
-- 4. Binary Search Tree
-- ============================================================================
print("\n[4] Binary Search Tree")

local BST = {}
BST.__index = BST

function BST.new()
    local self = setmetatable({}, BST)
    self.root = nil
    self.count = 0
    return self
end

function BST:insert(value)
    local function insert_node(node, value)
        if not node then
            self.count = self.count + 1
            return {value = value, left = nil, right = nil}
        end
        
        if value < node.value then
            node.left = insert_node(node.left, value)
        elseif value > node.value then
            node.right = insert_node(node.right, value)
        end
        
        return node
    end
    
    self.root = insert_node(self.root, value)
end

function BST:search(value)
    local function search_node(node, value)
        if not node then
            return false
        end
        
        if value == node.value then
            return true
        elseif value < node.value then
            return search_node(node.left, value)
        else
            return search_node(node.right, value)
        end
    end
    
    return search_node(self.root, value)
end

function BST:inorder()
    local result = {}
    
    local function traverse(node)
        if node then
            traverse(node.left)
            result[#result + 1] = node.value
            traverse(node.right)
        end
    end
    
    traverse(self.root)
    return result
end

function BST:height()
    local function calc_height(node)
        if not node then
            return 0
        end
        
        local left_h = calc_height(node.left)
        local right_h = calc_height(node.right)
        
        return 1 + (left_h > right_h and left_h or right_h)
    end
    
    return calc_height(self.root)
end

-- Test BST
local bst = BST.new()
bst:insert(50)
bst:insert(30)
bst:insert(70)
bst:insert(20)
bst:insert(40)
bst:insert(60)
bst:insert(80)

test("bst count", bst.count == 7)
test("bst search found", bst:search(40))
test("bst search not found", not bst:search(100))

local inorder = bst:inorder()
test("bst inorder", inorder[1] == 20 and inorder[4] == 50 and inorder[7] == 80)
test("bst height", bst:height() == 3)

-- ============================================================================
-- 5. Graph (Adjacency List)
-- ============================================================================
print("\n[5] Graph")

local Graph = {}
Graph.__index = Graph

function Graph.new()
    local self = setmetatable({}, Graph)
    self.adjacency = {}
    return self
end

function Graph:add_vertex(v)
    if not self.adjacency[v] then
        self.adjacency[v] = {}
    end
end

function Graph:add_edge(v1, v2)
    self:add_vertex(v1)
    self:add_vertex(v2)
    
    -- Undirected graph
    self.adjacency[v1][v2] = true
    self.adjacency[v2][v1] = true
end

function Graph:has_edge(v1, v2)
    return self.adjacency[v1] and self.adjacency[v1][v2] or false
end

function Graph:bfs(start)
    local visited = {}
    local queue = {start}
    local order = {}
    local head = 1
    local tail = 1
    
    visited[start] = true
    
    while head <= tail do
        local v = queue[head]
        head = head + 1
        order[#order + 1] = v
        
        for neighbor in pairs(self.adjacency[v] or {}) do
            if not visited[neighbor] then
                visited[neighbor] = true
                tail = tail + 1
                queue[tail] = neighbor
            end
        end
    end
    
    return order
end

function Graph:dfs(start)
    local visited = {}
    local order = {}
    
    local function dfs_visit(v)
        visited[v] = true
        order[#order + 1] = v
        
        for neighbor in pairs(self.adjacency[v] or {}) do
            if not visited[neighbor] then
                dfs_visit(neighbor)
            end
        end
    end
    
    dfs_visit(start)
    return order
end

-- Test Graph
local graph = Graph.new()
graph:add_edge(1, 2)
graph:add_edge(1, 3)
graph:add_edge(2, 4)
graph:add_edge(3, 4)
graph:add_edge(4, 5)

test("graph has edge 1-2", graph:has_edge(1, 2))
test("graph has edge 2-1", graph:has_edge(2, 1))
test("graph no edge 1-5", not graph:has_edge(1, 5))

local bfs_order = graph:bfs(1)
test("graph bfs start", bfs_order[1] == 1)
test("graph bfs length", #bfs_order == 5)

local dfs_order = graph:dfs(1)
test("graph dfs start", dfs_order[1] == 1)
test("graph dfs length", #dfs_order == 5)

-- ============================================================================
-- 6. Priority Queue (Min Heap)
-- ============================================================================
print("\n[6] Priority Queue")

local PriorityQueue = {}
PriorityQueue.__index = PriorityQueue

function PriorityQueue.new()
    local self = setmetatable({}, PriorityQueue)
    self.heap = {}
    self.size = 0
    return self
end

function PriorityQueue:parent(i)
    return i // 2
end

function PriorityQueue:left(i)
    return 2 * i
end

function PriorityQueue:right(i)
    return 2 * i + 1
end

function PriorityQueue:swap(i, j)
    self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
end

function PriorityQueue:heapify_up(i)
    while i > 1 and self.heap[self:parent(i)] > self.heap[i] do
        self:swap(i, self:parent(i))
        i = self:parent(i)
    end
end

function PriorityQueue:heapify_down(i)
    while true do
        local smallest = i
        local l = self:left(i)
        local r = self:right(i)
        
        if l <= self.size and self.heap[l] < self.heap[smallest] then
            smallest = l
        end
        
        if r <= self.size and self.heap[r] < self.heap[smallest] then
            smallest = r
        end
        
        if smallest == i then
            break
        end
        
        self:swap(i, smallest)
        i = smallest
    end
end

function PriorityQueue:insert(value)
    self.size = self.size + 1
    self.heap[self.size] = value
    self:heapify_up(self.size)
end

function PriorityQueue:extract_min()
    if self.size == 0 then
        return nil
    end
    
    local min = self.heap[1]
    self.heap[1] = self.heap[self.size]
    self.heap[self.size] = nil
    self.size = self.size - 1
    
    if self.size > 0 then
        self:heapify_down(1)
    end
    
    return min
end

-- Test Priority Queue
local pq = PriorityQueue.new()
pq:insert(5)
pq:insert(3)
pq:insert(7)
pq:insert(1)
pq:insert(9)

test("pq size", pq.size == 5)

local min1 = pq:extract_min()
test("pq extract min 1", min1 == 1)

local min2 = pq:extract_min()
test("pq extract min 2", min2 == 3)

local min3 = pq:extract_min()
test("pq extract min 3", min3 == 5)

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
    print("\n*** ALL DATA STRUCTURE TESTS PASSED ***")
else
    print("\n*** SOME TESTS FAILED ***")
end
