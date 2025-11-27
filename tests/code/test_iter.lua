-- test_iter.lua - Test select and iteration

print("Test select")
print(select("#", 1, 2, 3))
print(select(1, "a", "b", "c"))
print(select(2, "a", "b", "c"))

print("Done!")
