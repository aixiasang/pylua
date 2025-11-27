# -*- coding: utf-8 -*-
"""
PyLua Usage Demo - Comprehensive Examples
==========================================
Examples showing how to use PyLua to compile, analyze, and execute Lua code.
"""

import sys
import io
from pathlib import Path
from contextlib import redirect_stdout

sys.path.insert(0, str(Path(__file__).parent.parent))

from pylua.compile import (
    pylua_compile, disassemble, compile_source, extract_proto,
    decode_instruction, format_compiled_proto
)


# =============================================================================
# Helper Functions
# =============================================================================

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
        return False, "", str(e)


def section(title: str):
    """Print section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


# =============================================================================
# Demo 1: Basic Compilation
# =============================================================================

def demo_basic_compile():
    """Basic compilation example"""
    section("Demo 1: Basic Compilation")
    
    source = """
local a = 1 + 2
local b = a * 3
print(b)
"""
    proto, err = pylua_compile(source.strip(), "demo1")
    if proto:
        print(f"Source:\n{source}")
        print("Bytecode:")
        print(disassemble(proto))
    else:
        print(f"Error: {err}")


def demo_with_constants():
    """Show constants in bytecode"""
    print("\n" + "=" * 60)
    print("Demo 2: Constants Display")
    print("=" * 60)
    
    source = 'local x = "hello" .. " world"'
    proto, err = pylua_compile(source, "demo2")
    if proto:
        print(f"Source: {source}")
        print("\nBytecode with constants:")
        print(disassemble(proto, show_constants=True))
    else:
        print(f"Error: {err}")


def demo_function():
    """Function compilation example"""
    print("\n" + "=" * 60)
    print("Demo 3: Function Compilation")
    print("=" * 60)
    
    source = """
function add(a, b)
    return a + b
end

local result = add(10, 20)
"""
    proto, err = pylua_compile(source.strip(), "demo3")
    if proto:
        print(f"Source:\n{source}")
        print("Main function bytecode:")
        print(disassemble(proto, show_locals=True))
    else:
        print(f"Error: {err}")


def demo_control_flow():
    """Control flow example"""
    print("\n" + "=" * 60)
    print("Demo 4: Control Flow")
    print("=" * 60)
    
    source = """
local x = 10
if x > 5 then
    x = x + 1
else
    x = x - 1
end
"""
    proto, err = pylua_compile(source.strip(), "demo4")
    if proto:
        print(f"Source:\n{source}")
        print("Bytecode:")
        print(disassemble(proto))
    else:
        print(f"Error: {err}")


def demo_loop():
    """Loop example"""
    print("\n" + "=" * 60)
    print("Demo 5: Loop")
    print("=" * 60)
    
    source = """
local sum = 0
for i = 1, 10 do
    sum = sum + i
end
"""
    proto, err = pylua_compile(source.strip(), "demo5")
    if proto:
        print(f"Source:\n{source}")
        print("Bytecode:")
        print(disassemble(proto, show_locals=True))
    else:
        print(f"Error: {err}")


def demo_table():
    """Table example"""
    print("\n" + "=" * 60)
    print("Demo 6: Table")
    print("=" * 60)
    
    source = """
local t = {x = 1, y = 2, "hello"}
local a = t.x
local b = t[1]
"""
    proto, err = pylua_compile(source.strip(), "demo6")
    if proto:
        print(f"Source:\n{source}")
        print("Bytecode:")
        print(disassemble(proto, show_constants=True))
    else:
        print(f"Error: {err}")


def demo_closure():
    """Closure example"""
    print("\n" + "=" * 60)
    print("Demo 7: Closure")
    print("=" * 60)
    
    source = """
local x = 10
local function inc()
    x = x + 1
    return x
end
"""
    proto, err = pylua_compile(source.strip(), "demo7")
    if proto:
        print(f"Source:\n{source}")
        print("Bytecode:")
        print(disassemble(proto, show_upvalues=True))
    else:
        print(f"Error: {err}")


def demo_raw_proto():
    """Access raw Proto object for advanced analysis"""
    print("\n" + "=" * 60)
    print("Demo 8: Raw Proto Access")
    print("=" * 60)
    
    source = "local a, b = 1, 2; return a + b"
    closure, err = compile_source(source, "demo8")
    
    if closure:
        proto = closure.p
        print(f"Source: {source}")
        print(f"\nRaw Proto info:")
        print(f"  - Number of instructions: {proto.sizecode}")
        print(f"  - Number of constants: {proto.sizek}")
        print(f"  - Number of locals: {proto.sizelocvars}")
        print(f"  - Max stack size: {proto.maxstacksize}")
        print(f"  - Is vararg: {proto.is_vararg}")
        
        # Extract as CompiledProto for analysis
        cp = extract_proto(proto)
        print(f"\nCompiledProto:")
        print(f"  - Instructions: {len(cp.instructions)}")
        print(f"  - Constants: {cp.constants}")
    else:
        print(f"Error: {err}")


if __name__ == "__main__":
    demo_basic_compile()
    demo_with_constants()
    demo_function()
    demo_control_flow()
    demo_loop()
    demo_table()
    demo_closure()
    demo_raw_proto()
    
    print("\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)
