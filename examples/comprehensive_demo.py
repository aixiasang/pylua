# -*- coding: utf-8 -*-
"""
PyLua Comprehensive Demo
========================
Complete examples showing compilation, analysis, execution, and more.
"""

import sys
import io
import os
from pathlib import Path
from contextlib import redirect_stdout

sys.path.insert(0, str(Path(__file__).parent.parent))

from pylua.compile import (
    pylua_compile, disassemble, compile_source, extract_proto,
    decode_instruction, format_compiled_proto
)
from pylua.lopcodes import OpCode, luaP_opnames as opnames


# =============================================================================
# Helper Functions
# =============================================================================

def section(title: str):
    """Print section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def subsection(title: str):
    """Print subsection header"""
    print(f"\n--- {title} ---\n")


def run_lua(source: str, name: str = "=demo") -> tuple:
    """
    Execute Lua code and capture output.
    Returns (success, output, error)
    """
    try:
        from pylua.lvm import execute_lua
        
        # Capture stdout
        output = io.StringIO()
        with redirect_stdout(output):
            execute_lua(source, name)
        
        return True, output.getvalue(), None
    except Exception as e:
        import traceback
        return False, "", f"{type(e).__name__}: {e}"


# =============================================================================
# PART 1: Basic Compilation Examples
# =============================================================================

def demo_hello_world():
    """Hello World - simplest example"""
    section("1.1 Hello World")
    
    source = 'print("Hello, World!")'
    proto, err = pylua_compile(source, "hello")
    
    print(f"Source: {source}\n")
    
    if proto:
        print("Compiled bytecode:")
        print(disassemble(proto, show_constants=True))
        
        # Try to execute
        subsection("Execution attempt")
        success, output, error = run_lua(source)
        if success:
            print(f"Output: {output if output else '(no output)'}")
        else:
            print(f"Execution note: {error}")
    else:
        print(f"Compilation error: {err}")


def demo_arithmetic():
    """Arithmetic operations"""
    section("1.2 Arithmetic Operations")
    
    examples = [
        ("Addition", "return 1 + 2"),
        ("Subtraction", "return 10 - 3"),
        ("Multiplication", "return 4 * 5"),
        ("Division", "return 20 / 4"),
        ("Integer division", "return 17 // 3"),
        ("Modulo", "return 17 % 5"),
        ("Power", "return 2 ^ 10"),
        ("Complex", "return (1 + 2) * 3 - 4 / 2"),
    ]
    
    for name, source in examples:
        proto, err = pylua_compile(source, name)
        if proto:
            print(f"{name}: {source}")
            # Show just the core instructions
            for inst in proto.instructions[:3]:
                print(f"    {inst.pc:3d}  {inst.opname:<12s}  A={inst.a} B={inst.b} C={inst.c}")
            print()


def demo_variables():
    """Variable declarations and assignments"""
    section("1.3 Variables")
    
    source = """
-- Local variables
local x = 10
local y = 20
local z = x + y

-- Multiple assignment
local a, b, c = 1, 2, 3

-- Reassignment
x = x * 2

-- Return result
return z, x
"""
    proto, err = pylua_compile(source.strip(), "variables")
    
    print(f"Source:\n{source}")
    
    if proto:
        print("Bytecode:")
        print(disassemble(proto, show_constants=True, show_locals=True))


# =============================================================================
# PART 2: Control Flow
# =============================================================================

def demo_if_else():
    """If-else statements"""
    section("2.1 If-Else Statements")
    
    source = """
local x = 15

if x > 10 then
    print("x is greater than 10")
elseif x > 5 then
    print("x is greater than 5")
else
    print("x is 5 or less")
end
"""
    proto, err = pylua_compile(source.strip(), "if_else")
    
    print(f"Source:\n{source}")
    
    if proto:
        print("\nBytecode (notice JMP instructions for branching):")
        print(disassemble(proto, show_constants=True))


def demo_while_loop():
    """While loop"""
    section("2.2 While Loop")
    
    source = """
local i = 1
local sum = 0

while i <= 5 do
    sum = sum + i
    i = i + 1
end

return sum
"""
    proto, err = pylua_compile(source.strip(), "while_loop")
    
    print(f"Source:\n{source}")
    
    if proto:
        print("\nBytecode:")
        print(disassemble(proto, show_locals=True))


def demo_for_loop():
    """For loops - numeric and generic"""
    section("2.3 For Loops")
    
    subsection("Numeric for loop")
    source1 = """
local sum = 0
for i = 1, 10, 2 do  -- start, stop, step
    sum = sum + i
end
return sum
"""
    proto, err = pylua_compile(source1.strip(), "for_num")
    print(f"Source:\n{source1}")
    if proto:
        print("Bytecode (FORPREP/FORLOOP instructions):")
        print(disassemble(proto, show_locals=True))
    
    subsection("Generic for loop (ipairs style)")
    source2 = """
local t = {10, 20, 30}
local sum = 0
for i, v in ipairs(t) do
    sum = sum + v
end
return sum
"""
    proto, err = pylua_compile(source2.strip(), "for_in")
    print(f"Source:\n{source2}")
    if proto:
        print("Bytecode (TFORCALL/TFORLOOP instructions):")
        print(disassemble(proto, show_locals=True))


def demo_repeat_until():
    """Repeat-until loop"""
    section("2.4 Repeat-Until Loop")
    
    source = """
local i = 0
repeat
    i = i + 1
    print(i)
until i >= 5
"""
    proto, err = pylua_compile(source.strip(), "repeat")
    
    print(f"Source:\n{source}")
    
    if proto:
        print("\nBytecode:")
        print(disassemble(proto))


# =============================================================================
# PART 3: Functions
# =============================================================================

def demo_simple_function():
    """Simple function definition and call"""
    section("3.1 Simple Function")
    
    source = """
function greet(name)
    return "Hello, " .. name
end

local message = greet("Lua")
print(message)
"""
    proto, err = pylua_compile(source.strip(), "simple_func")
    
    print(f"Source:\n{source}")
    
    if proto:
        print("\nMain bytecode:")
        print(disassemble(proto, show_constants=True))


def demo_local_function():
    """Local function"""
    section("3.2 Local Function")
    
    source = """
local function factorial(n)
    if n <= 1 then
        return 1
    else
        return n * factorial(n - 1)
    end
end

return factorial(5)
"""
    proto, err = pylua_compile(source.strip(), "factorial")
    
    print(f"Source:\n{source}")
    
    if proto:
        print("\nBytecode with nested functions:")
        print(disassemble(proto, show_locals=True))


def demo_closure():
    """Closures and upvalues"""
    section("3.3 Closures and Upvalues")
    
    source = """
local function counter()
    local count = 0
    return function()
        count = count + 1
        return count
    end
end

local c = counter()
print(c())  -- 1
print(c())  -- 2
"""
    proto, err = pylua_compile(source.strip(), "closure")
    
    print(f"Source:\n{source}")
    
    if proto:
        print("\nBytecode (notice GETUPVAL/SETUPVAL for closure variables):")
        print(disassemble(proto, show_upvalues=True, show_locals=True))


def demo_vararg():
    """Vararg functions"""
    section("3.4 Vararg Functions (...)")
    
    source = """
function sum(...)
    local args = {...}
    local total = 0
    for i = 1, #args do
        total = total + args[i]
    end
    return total
end

return sum(1, 2, 3, 4, 5)
"""
    proto, err = pylua_compile(source.strip(), "vararg")
    
    print(f"Source:\n{source}")
    
    if proto:
        print("\nBytecode (notice VARARG instruction):")
        print(disassemble(proto, show_locals=True))


# =============================================================================
# PART 4: Tables
# =============================================================================

def demo_table_constructor():
    """Table constructors"""
    section("4.1 Table Constructors")
    
    source = """
-- Array-like table
local arr = {10, 20, 30, 40}

-- Dictionary-like table
local dict = {
    name = "Lua",
    version = 5.3,
    ["key with space"] = "value"
}

-- Mixed table
local mixed = {
    "first",
    key = "value",
    "second",
    100
}

return arr[1], dict.name
"""
    proto, err = pylua_compile(source.strip(), "table_ctor")
    
    print(f"Source:\n{source}")
    
    if proto:
        print("\nBytecode (NEWTABLE, SETTABLE, SETLIST):")
        print(disassemble(proto, show_constants=True))


def demo_table_access():
    """Table access patterns"""
    section("4.2 Table Access")
    
    source = """
local t = {x = 10, y = 20}

-- Dot notation
local a = t.x

-- Bracket notation
local b = t["y"]

-- Dynamic key
local key = "x"
local c = t[key]

-- Nested tables
local nested = {inner = {value = 42}}
local d = nested.inner.value

return a, b, c, d
"""
    proto, err = pylua_compile(source.strip(), "table_access")
    
    print(f"Source:\n{source}")
    
    if proto:
        print("\nBytecode (GETTABLE variations):")
        print(disassemble(proto, show_constants=True, show_locals=True))


# =============================================================================
# PART 5: String Operations
# =============================================================================

def demo_strings():
    """String operations"""
    section("5.1 String Operations")
    
    source = """
local s1 = "Hello"
local s2 = 'World'
local s3 = [[
Multi-line
string
]]

-- Concatenation
local greeting = s1 .. ", " .. s2 .. "!"

-- String length
local len = #greeting

return greeting, len
"""
    proto, err = pylua_compile(source.strip(), "strings")
    
    print(f"Source:\n{source}")
    
    if proto:
        print("\nBytecode (CONCAT, LEN operations):")
        print(disassemble(proto, show_constants=True))


# =============================================================================
# PART 6: Advanced Analysis
# =============================================================================

def demo_instruction_decode():
    """Decode raw instructions"""
    section("6.1 Instruction Decoding")
    
    source = "local a = 1 + 2; return a"
    closure, err = compile_source(source, "decode")
    
    print(f"Source: {source}\n")
    
    if closure:
        proto = closure.p
        print("Raw instruction analysis:")
        print("-" * 60)
        
        for i, code in enumerate(proto.code):
            line = proto.lineinfo[i] if i < len(proto.lineinfo) else 0
            inst = decode_instruction(code, line)
            
            print(f"  [{i+1}] Raw: 0x{code:08X}")
            print(f"      Opcode: {inst.opcode} ({inst.opname})")
            print(f"      A={inst.a}, B={inst.b}, C={inst.c}, Bx={inst.bx}, sBx={inst.sbx}")
            print()


def demo_proto_structure():
    """Examine Proto structure"""
    section("6.2 Proto Structure Analysis")
    
    source = """
local function outer(x)
    local function inner(y)
        return x + y
    end
    return inner
end
return outer(10)(20)
"""
    closure, err = compile_source(source.strip(), "proto_struct")
    
    print(f"Source:\n{source}")
    
    if closure:
        def analyze_proto(proto, depth=0):
            indent = "  " * depth
            print(f"\n{indent}Proto at depth {depth}:")
            print(f"{indent}  - sizecode: {proto.sizecode}")
            print(f"{indent}  - sizek: {proto.sizek}")
            print(f"{indent}  - sizelocvars: {proto.sizelocvars}")
            print(f"{indent}  - sizeupvalues: {proto.sizeupvalues}")
            print(f"{indent}  - numparams: {proto.numparams}")
            print(f"{indent}  - is_vararg: {proto.is_vararg}")
            print(f"{indent}  - maxstacksize: {proto.maxstacksize}")
            print(f"{indent}  - nested functions: {proto.sizep}")
            
            # Recurse into nested protos
            if hasattr(proto, 'p') and proto.p:
                for i, sub in enumerate(proto.p):
                    print(f"{indent}  --- Nested function {i} ---")
                    analyze_proto(sub, depth + 1)
        
        analyze_proto(closure.p)


def demo_opcode_reference():
    """Show all Lua 5.3 opcodes"""
    section("6.3 Opcode Reference")
    
    print("Lua 5.3 VM Opcodes:")
    print("-" * 60)
    
    for i, name in enumerate(opnames):
        if name:
            print(f"  {i:2d}  {name}")
    
    print("\n(47 opcodes total)")


# =============================================================================
# PART 7: File Operations
# =============================================================================

def demo_compile_file():
    """Compile Lua from file"""
    section("7.1 Compile from File")
    
    # Create a temp Lua file
    test_file = Path(__file__).parent / "test_script.lua"
    lua_code = """
-- test_script.lua
-- A sample Lua script

local function fibonacci(n)
    if n <= 1 then
        return n
    end
    return fibonacci(n - 1) + fibonacci(n - 2)
end

-- Calculate first 10 fibonacci numbers
for i = 0, 9 do
    print("fib(" .. i .. ") = " .. fibonacci(i))
end
"""
    
    # Write file
    test_file.write_text(lua_code, encoding='utf-8')
    print(f"Created test file: {test_file}\n")
    print(f"Contents:\n{lua_code}")
    
    # Compile from file
    content = test_file.read_text(encoding='utf-8')
    proto, err = pylua_compile(content, str(test_file))
    
    if proto:
        print("\nCompiled bytecode:")
        print(disassemble(proto, show_locals=True))
    else:
        print(f"Compilation error: {err}")
    
    # Cleanup
    test_file.unlink()
    print(f"\nCleaned up test file.")


# =============================================================================
# PART 8: Print/Output Examples
# =============================================================================

def demo_print_examples():
    """Various print examples"""
    section("8.1 Print Statement Analysis")
    
    examples = [
        ('print("hello")', "Simple string"),
        ('print(1, 2, 3)', "Multiple values"),
        ('print("sum:", 1+2)', "Expression in print"),
        ('local x = 42; print("x =", x)', "Variable in print"),
        ('print(type("hello"))', "Function call in print"),
    ]
    
    for source, desc in examples:
        print(f"\n{desc}:")
        print(f"  Source: {source}")
        
        proto, err = pylua_compile(source, desc)
        if proto:
            print("  Instructions:")
            for inst in proto.instructions:
                print(f"    {inst.pc:2d}  {inst.opname:<12s}  {inst.a:3d} {inst.b:3d} {inst.c:3d}")


def demo_execution_attempt():
    """Try to execute various Lua code"""
    section("8.2 Execution Attempts")
    
    test_cases = [
        ('print("Hello from PyLua!")', "Simple print"),
        ('return 1 + 2', "Return arithmetic"),
        ('local x = 10; return x * 2', "Local variable"),
        ('print(1, 2, 3)', "Multi-value print"),
    ]
    
    for source, desc in test_cases:
        print(f"\n{desc}:")
        print(f"  Source: {source}")
        
        success, output, error = run_lua(source, desc)
        if success:
            print(f"  Status: SUCCESS")
            print(f"  Output: {output if output else '(no output captured)'}")
        else:
            print(f"  Status: Not fully supported")
            print(f"  Note: {error[:80]}..." if len(str(error)) > 80 else f"  Note: {error}")


# =============================================================================
# PART 9: Error Handling
# =============================================================================

def demo_syntax_errors():
    """Demonstrate syntax error detection"""
    section("9.1 Syntax Error Detection")
    
    bad_code = [
        ('local x =', "Missing expression"),
        ('if x then', "Missing end"),
        ('function ()', "Missing function name"),
        ('local 123 = 1', "Invalid identifier"),
        ('return return', "Double return"),
    ]
    
    for source, desc in bad_code:
        print(f"\n{desc}:")
        print(f"  Source: {source}")
        
        proto, err = pylua_compile(source, "error_test")
        if proto:
            print("  Result: Unexpectedly compiled!")
        else:
            # Truncate long error messages
            err_msg = str(err)[:100] + "..." if len(str(err)) > 100 else str(err)
            print(f"  Error: {err_msg}")


# =============================================================================
# Main
# =============================================================================

def run_all_demos():
    """Run all demonstrations"""
    print("\n" + "=" * 70)
    print("       PyLua Comprehensive Demo")
    print("       Lua 5.3 Compatible Compiler & VM in Python")
    print("=" * 70)
    
    # Part 1: Basic
    demo_hello_world()
    demo_arithmetic()
    demo_variables()
    
    # Part 2: Control Flow
    demo_if_else()
    demo_while_loop()
    demo_for_loop()
    demo_repeat_until()
    
    # Part 3: Functions
    demo_simple_function()
    demo_local_function()
    demo_closure()
    demo_vararg()
    
    # Part 4: Tables
    demo_table_constructor()
    demo_table_access()
    
    # Part 5: Strings
    demo_strings()
    
    # Part 6: Advanced Analysis
    demo_instruction_decode()
    demo_proto_structure()
    demo_opcode_reference()
    
    # Part 7: File Operations
    demo_compile_file()
    
    # Part 8: Print/Execution
    demo_print_examples()
    demo_execution_attempt()
    
    # Part 9: Error Handling
    demo_syntax_errors()
    
    print("\n" + "=" * 70)
    print("  All demos completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Run specific demo or all
    if len(sys.argv) > 1:
        demo_name = sys.argv[1]
        demos = {
            'hello': demo_hello_world,
            'arithmetic': demo_arithmetic,
            'variables': demo_variables,
            'if': demo_if_else,
            'while': demo_while_loop,
            'for': demo_for_loop,
            'repeat': demo_repeat_until,
            'function': demo_simple_function,
            'local_func': demo_local_function,
            'closure': demo_closure,
            'vararg': demo_vararg,
            'table': demo_table_constructor,
            'access': demo_table_access,
            'string': demo_strings,
            'decode': demo_instruction_decode,
            'proto': demo_proto_structure,
            'opcode': demo_opcode_reference,
            'file': demo_compile_file,
            'print': demo_print_examples,
            'exec': demo_execution_attempt,
            'error': demo_syntax_errors,
        }
        
        if demo_name in demos:
            demos[demo_name]()
        else:
            print(f"Unknown demo: {demo_name}")
            print(f"Available: {', '.join(demos.keys())}")
    else:
        run_all_demos()
