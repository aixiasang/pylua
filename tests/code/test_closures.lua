-- test_closures.lua - Test closures and recursion

print("Test 1: Simple closure")
local function make_counter()
    local count = 0
    return function()
        count = count + 1
        return count
    end
end

local counter = make_counter()
print(counter())
print(counter())
print(counter())

print("Test 2: Second counter")
local counter2 = make_counter()
print(counter2())

print("Test 3: Recursive factorial")
local function factorial(n)
    if n <= 1 then
        return 1
    else
        return n * factorial(n - 1)
    end
end
print(factorial(1))
print(factorial(5))
print(factorial(10))

print("Test 4: Recursive fibonacci")
local function fibonacci(n)
    if n <= 2 then
        return 1
    else
        return fibonacci(n - 1) + fibonacci(n - 2)
    end
end
print(fibonacci(1))
print(fibonacci(5))
print(fibonacci(10))

print("Done!")
