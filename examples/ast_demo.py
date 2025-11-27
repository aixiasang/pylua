# -*- coding: utf-8 -*-
"""
PyLua AST Demo - AST Parsing and Analysis Examples

Demonstrate how to use PyLua's AST parser to analyze Lua code structure.

Based on Lua 5.3.6 official implementation.
Author: aixiasang
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pylua.last_parser import parse_lua, print_ast, ASTParser
from pylua.last import *


def section(title: str):
    """Print section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


# =============================================================================
# Demo 1: Basic AST Parsing
# =============================================================================

def demo_basic_ast():
    """Basic AST parsing example"""
    section("1. Basic AST Parsing")
    
    source = """
local x = 10
local y = 20
return x + y
"""
    print(f"Source:{source}")
    print("AST Tree:")
    print(print_ast(source.strip()))


# =============================================================================
# Demo 2: Function AST
# =============================================================================

def demo_function_ast():
    """Function definition AST"""
    section("2. Function AST")
    
    source = """
function add(a, b)
    return a + b
end

local result = add(1, 2)
"""
    print(f"Source:{source}")
    print("AST Tree:")
    print(print_ast(source.strip()))


# =============================================================================
# Demo 3: Control Flow AST
# =============================================================================

def demo_control_flow_ast():
    """Control flow AST"""
    section("3. Control Flow AST")
    
    source = """
local x = 10

if x > 5 then
    print("big")
elseif x > 0 then
    print("positive")
else
    print("other")
end
"""
    print(f"Source:{source}")
    print("AST Tree:")
    print(print_ast(source.strip()))


# =============================================================================
# Demo 4: Loop AST
# =============================================================================

def demo_loop_ast():
    """Loop AST"""
    section("4. Loop AST")
    
    source = """
-- Numeric for
for i = 1, 10, 2 do
    print(i)
end

-- While loop
local x = 0
while x < 5 do
    x = x + 1
end

-- Generic for
for k, v in pairs(t) do
    print(k, v)
end
"""
    print(f"Source:{source}")
    print("AST Tree:")
    print(print_ast(source.strip()))


# =============================================================================
# Demo 5: Table AST
# =============================================================================

def demo_table_ast():
    """Table constructor AST"""
    section("5. Table Constructor AST")
    
    source = """
local t = {
    "first",
    key = "value",
    [1 + 1] = "computed key",
    nested = {a = 1, b = 2}
}
"""
    print(f"Source:{source}")
    print("AST Tree:")
    print(print_ast(source.strip()))


# =============================================================================
# Demo 6: Expression Analysis
# =============================================================================

def demo_expression_analysis():
    """Analyze expression structure"""
    section("6. Expression Analysis")
    
    source = "1 + 2 * 3 - 4 / 2"
    
    print(f"Expression: {source}")
    print("\nAST shows operator precedence:")
    
    ast = parse_lua(f"return {source}", "expr")
    
    def show_expr(node, indent=0):
        """Recursively show expression structure"""
        prefix = "  " * indent
        if isinstance(node, BinaryExpr):
            print(f"{prefix}BinaryExpr(op={node.op.name})")
            print(f"{prefix}  left:")
            show_expr(node.left, indent + 2)
            print(f"{prefix}  right:")
            show_expr(node.right, indent + 2)
        elif isinstance(node, NumberLiteral):
            print(f"{prefix}Number({node.value})")
        elif isinstance(node, ReturnStat):
            for val in node.values:
                show_expr(val, indent)
        elif isinstance(node, Block):
            if node.return_stat:
                show_expr(node.return_stat, indent)
        elif isinstance(node, Chunk):
            show_expr(node.block, indent)
    
    show_expr(ast)


# =============================================================================
# Demo 7: Custom AST Visitor
# =============================================================================

def demo_custom_visitor():
    """Custom AST visitor example"""
    section("7. Custom AST Visitor - Find All Identifiers")
    
    source = """
local x = 10
local y = x + 20
function foo(a, b)
    return a + b + x
end
print(foo(1, 2))
"""
    
    class IdentifierFinder(ASTVisitor):
        """Find all identifiers in the AST"""
        def __init__(self):
            self.identifiers = set()
        
        def generic_visit(self, node: ASTNode):
            """Default: visit all children"""
            self.visit_children(node)
        
        def visit_Identifier(self, node: Identifier):
            self.identifiers.add(node.name)
            self.visit_children(node)
    
    print(f"Source:{source}")
    
    ast = parse_lua(source.strip(), "identifiers")
    finder = IdentifierFinder()
    ast.accept(finder)
    
    print(f"Found identifiers: {sorted(finder.identifiers)}")


# =============================================================================
# Demo 8: Statement Counter
# =============================================================================

def demo_statement_counter():
    """Count different statement types"""
    section("8. Statement Counter")
    
    source = """
local x = 1
local y = 2
x = x + 1

if x > 0 then
    print(x)
end

for i = 1, 10 do
    y = y + i
end

while y > 0 do
    y = y - 1
end

return x, y
"""
    
    class StatementCounter(ASTVisitor):
        """Count statement types"""
        def __init__(self):
            self.counts = {}
        
        def generic_visit(self, node: ASTNode):
            """Default: visit all children"""
            self.visit_children(node)
        
        def _count(self, name: str):
            self.counts[name] = self.counts.get(name, 0) + 1
        
        def visit_LocalVarStat(self, node):
            self._count("LocalVar")
            self.visit_children(node)
        
        def visit_AssignStat(self, node):
            self._count("Assignment")
            self.visit_children(node)
        
        def visit_IfStat(self, node):
            self._count("If")
            self.visit_children(node)
        
        def visit_ForNumStat(self, node):
            self._count("NumericFor")
            self.visit_children(node)
        
        def visit_WhileStat(self, node):
            self._count("While")
            self.visit_children(node)
        
        def visit_ReturnStat(self, node):
            self._count("Return")
            self.visit_children(node)
        
        def visit_CallStat(self, node):
            self._count("FunctionCall")
            self.visit_children(node)
    
    print(f"Source:{source}")
    
    ast = parse_lua(source.strip(), "counter")
    counter = StatementCounter()
    ast.accept(counter)
    
    print("Statement counts:")
    for stmt_type, count in sorted(counter.counts.items()):
        print(f"  {stmt_type}: {count}")


# =============================================================================
# Demo 9: Code Complexity
# =============================================================================

def demo_complexity():
    """Analyze code complexity"""
    section("9. Code Complexity Analysis")
    
    source = """
function factorial(n)
    if n <= 1 then
        return 1
    else
        return n * factorial(n - 1)
    end
end

function fibonacci(n)
    if n <= 0 then
        return 0
    elseif n == 1 then
        return 1
    else
        return fibonacci(n - 1) + fibonacci(n - 2)
    end
end
"""
    
    class ComplexityAnalyzer(ASTVisitor):
        """Analyze cyclomatic complexity (simplified)"""
        def __init__(self):
            self.complexity = 1  # Base complexity
            self.nesting_level = 0
            self.max_nesting = 0
        
        def generic_visit(self, node: ASTNode):
            """Default: visit all children"""
            self.visit_children(node)
        
        def visit_IfStat(self, node):
            self.complexity += 1  # Each branch adds complexity
            self.complexity += len(node.elseif_clauses)
            self._enter_block()
            self.visit_children(node)
            self._exit_block()
        
        def visit_WhileStat(self, node):
            self.complexity += 1
            self._enter_block()
            self.visit_children(node)
            self._exit_block()
        
        def visit_ForNumStat(self, node):
            self.complexity += 1
            self._enter_block()
            self.visit_children(node)
            self._exit_block()
        
        def visit_ForInStat(self, node):
            self.complexity += 1
            self._enter_block()
            self.visit_children(node)
            self._exit_block()
        
        def _enter_block(self):
            self.nesting_level += 1
            self.max_nesting = max(self.max_nesting, self.nesting_level)
        
        def _exit_block(self):
            self.nesting_level -= 1
    
    print(f"Source:{source}")
    
    ast = parse_lua(source.strip(), "complexity")
    analyzer = ComplexityAnalyzer()
    ast.accept(analyzer)
    
    print(f"Cyclomatic Complexity: {analyzer.complexity}")
    print(f"Max Nesting Level: {analyzer.max_nesting}")


# =============================================================================
# Main
# =============================================================================

def main():
    print("\n" + "=" * 70)
    print("       PyLua AST Demo")
    print("       Lua 5.3 AST Parser and Analysis")
    print("=" * 70)
    
    demo_basic_ast()
    demo_function_ast()
    demo_control_flow_ast()
    demo_loop_ast()
    demo_table_ast()
    demo_expression_analysis()
    demo_custom_visitor()
    demo_statement_counter()
    demo_complexity()
    
    print("\n" + "=" * 70)
    print("  All AST demos completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
