# -*- coding: utf-8 -*-
"""
last.py - Lua Abstract Syntax Tree
===================================

AST node definitions and AST builder.

Note: Lua 5.3's standard implementation has no AST, parser directly generates bytecode.
This is an additional AST layer implemented by PyLua for analysis and debugging.

AST Node Types (based on Lua 5.3 grammar):
- Chunk: program block
- Block: statement block
- Statement: statement
- Expression: expression
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union, Any
from enum import Enum, auto


# =============================================================================
# AST Node Base
# =============================================================================
@dataclass
class ASTNode:
    """AST node base class"""
    line: int = 0
    column: int = 0
    
    def accept(self, visitor):
        """Visitor pattern"""
        method_name = f'visit_{self.__class__.__name__}'
        visitor_method = getattr(visitor, method_name, visitor.generic_visit)
        return visitor_method(self)


# =============================================================================
# Expressions
# =============================================================================
@dataclass
class NilLiteral(ASTNode):
    """nil literal"""
    pass


@dataclass
class BoolLiteral(ASTNode):
    """Boolean literal"""
    value: bool = False


@dataclass
class NumberLiteral(ASTNode):
    """Number literal"""
    value: Union[int, float] = 0
    is_integer: bool = True


@dataclass
class StringLiteral(ASTNode):
    """String literal"""
    value: str = ""
    is_long: bool = False


@dataclass
class VarargExpr(ASTNode):
    """Vararg expression ..."""
    pass


@dataclass
class Identifier(ASTNode):
    """Identifier"""
    name: str = ""


@dataclass
class IndexExpr(ASTNode):
    """Index expression table[key]"""
    table: ASTNode = None
    key: ASTNode = None


@dataclass
class FieldExpr(ASTNode):
    """Field access expression table.field"""
    table: ASTNode = None
    field: str = ""


@dataclass
class MethodExpr(ASTNode):
    """Method access expression table:method"""
    table: ASTNode = None
    method: str = ""


class UnaryOp(Enum):
    """Unary operator"""
    MINUS = auto()  # -
    NOT = auto()    # not
    LEN = auto()    # #
    BNOT = auto()   # ~


@dataclass
class UnaryExpr(ASTNode):
    """Unary expression"""
    op: UnaryOp = None
    operand: ASTNode = None


class BinaryOp(Enum):
    """Binary operator"""
    ADD = auto()     # +
    SUB = auto()     # -
    MUL = auto()     # *
    DIV = auto()     # /
    IDIV = auto()    # //
    MOD = auto()     # %
    POW = auto()     # ^
    CONCAT = auto()  # ..
    LT = auto()      # <
    LE = auto()      # <=
    GT = auto()      # >
    GE = auto()      # >=
    EQ = auto()      # ==
    NE = auto()      # ~=
    AND = auto()     # and
    OR = auto()      # or
    BAND = auto()    # &
    BOR = auto()     # |
    BXOR = auto()    # ~
    SHL = auto()     # <<
    SHR = auto()     # >>


@dataclass
class BinaryExpr(ASTNode):
    """Binary expression"""
    op: BinaryOp = None
    left: ASTNode = None
    right: ASTNode = None


@dataclass
class TableField(ASTNode):
    """Table field"""
    key: Optional[ASTNode] = None  # None means list item
    value: ASTNode = None


@dataclass
class TableConstructor(ASTNode):
    """Table constructor {}"""
    fields: List[TableField] = field(default_factory=list)


@dataclass
class FuncCall(ASTNode):
    """Function call"""
    func: ASTNode = None
    args: List[ASTNode] = field(default_factory=list)
    is_method: bool = False


@dataclass
class FuncBody(ASTNode):
    """Function body"""
    params: List[str] = field(default_factory=list)
    is_vararg: bool = False
    body: 'Block' = None


@dataclass
class FuncExpr(ASTNode):
    """Anonymous function expression"""
    body: FuncBody = None


# =============================================================================
# Statements
# =============================================================================
@dataclass
class Block(ASTNode):
    """Statement block"""
    statements: List[ASTNode] = field(default_factory=list)
    return_stat: Optional['ReturnStat'] = None


@dataclass
class EmptyStat(ASTNode):
    """Empty statement ;"""
    pass


@dataclass
class AssignStat(ASTNode):
    """Assignment statement"""
    targets: List[ASTNode] = field(default_factory=list)
    values: List[ASTNode] = field(default_factory=list)


@dataclass
class LocalVarStat(ASTNode):
    """Local variable declaration"""
    names: List[str] = field(default_factory=list)
    values: List[ASTNode] = field(default_factory=list)


@dataclass
class LocalFuncStat(ASTNode):
    """Local function declaration"""
    name: str = ""
    body: FuncBody = None


@dataclass
class FuncStat(ASTNode):
    """Function declaration"""
    name: ASTNode = None  # can be Identifier, FieldExpr, or MethodExpr
    body: FuncBody = None


@dataclass
class CallStat(ASTNode):
    """Function call statement"""
    call: FuncCall = None


@dataclass
class DoStat(ASTNode):
    """do ... end block"""
    body: Block = None


@dataclass
class WhileStat(ASTNode):
    """while loop"""
    condition: ASTNode = None
    body: Block = None


@dataclass
class RepeatStat(ASTNode):
    """repeat ... until loop"""
    body: Block = None
    condition: ASTNode = None


@dataclass
class IfStat(ASTNode):
    """if statement"""
    condition: ASTNode = None
    then_block: Block = None
    elseif_clauses: List[tuple] = field(default_factory=list)  # [(condition, block), ...]
    else_block: Optional[Block] = None


@dataclass
class ForNumStat(ASTNode):
    """Numeric for loop"""
    var: str = ""
    start: ASTNode = None
    stop: ASTNode = None
    step: Optional[ASTNode] = None
    body: Block = None


@dataclass
class ForInStat(ASTNode):
    """Generic for loop"""
    names: List[str] = field(default_factory=list)
    exprs: List[ASTNode] = field(default_factory=list)
    body: Block = None


@dataclass
class BreakStat(ASTNode):
    """break statement"""
    pass


@dataclass
class GotoStat(ASTNode):
    """goto statement"""
    label: str = ""


@dataclass
class LabelStat(ASTNode):
    """Label ::label::"""
    name: str = ""


@dataclass
class ReturnStat(ASTNode):
    """return statement"""
    values: List[ASTNode] = field(default_factory=list)


@dataclass
class Chunk(ASTNode):
    """Program chunk (top level)"""
    block: Block = None
    source: str = ""


# =============================================================================
# AST Visitor
# =============================================================================
class ASTVisitor:
    """AST visitor base class"""
    
    def generic_visit(self, node: ASTNode):
        """Default visit method"""
        pass
    
    def visit_children(self, node: ASTNode):
        """Visit all child nodes"""
        for field_name in node.__dataclass_fields__:
            value = getattr(node, field_name)
            if isinstance(value, ASTNode):
                value.accept(self)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        item.accept(self)
                    elif isinstance(item, tuple):
                        for elem in item:
                            if isinstance(elem, ASTNode):
                                elem.accept(self)


# =============================================================================
# AST Printer
# =============================================================================
class ASTPrinter(ASTVisitor):
    """AST printer"""
    
    def __init__(self):
        self.indent = 0
        self.output = []
    
    def print(self, node: ASTNode) -> str:
        """Print AST"""
        self.indent = 0
        self.output = []
        node.accept(self)
        return '\n'.join(self.output)
    
    def _emit(self, text: str):
        """Output a line"""
        self.output.append('  ' * self.indent + text)
    
    def _visit_node(self, node: ASTNode, extra: str = ""):
        """Visit node"""
        line_info = f" (line {node.line})" if node.line else ""
        self._emit(f"{node.__class__.__name__}{extra}{line_info}")
        self.indent += 1
        self.visit_children(node)
        self.indent -= 1
    
    def visit_Chunk(self, node: Chunk):
        self._emit(f"Chunk: {node.source}")
        self.indent += 1
        if node.block:
            node.block.accept(self)
        self.indent -= 1
    
    def visit_Block(self, node: Block):
        self._emit("Block")
        self.indent += 1
        for stmt in node.statements:
            stmt.accept(self)
        if node.return_stat:
            node.return_stat.accept(self)
        self.indent -= 1
    
    def visit_NilLiteral(self, node: NilLiteral):
        self._emit("nil")
    
    def visit_BoolLiteral(self, node: BoolLiteral):
        self._emit(f"Bool: {node.value}")
    
    def visit_NumberLiteral(self, node: NumberLiteral):
        self._emit(f"Number: {node.value}")
    
    def visit_StringLiteral(self, node: StringLiteral):
        self._emit(f'String: "{node.value}"')
    
    def visit_Identifier(self, node: Identifier):
        self._emit(f"Identifier: {node.name}")
    
    def visit_VarargExpr(self, node: VarargExpr):
        self._emit("Vararg: ...")
    
    def visit_IndexExpr(self, node: IndexExpr):
        self._emit("Index")
        self.indent += 1
        self._emit("table:")
        self.indent += 1
        node.table.accept(self)
        self.indent -= 1
        self._emit("key:")
        self.indent += 1
        node.key.accept(self)
        self.indent -= 1
        self.indent -= 1
    
    def visit_FieldExpr(self, node: FieldExpr):
        self._emit(f"Field: .{node.field}")
        self.indent += 1
        node.table.accept(self)
        self.indent -= 1
    
    def visit_MethodExpr(self, node: MethodExpr):
        self._emit(f"Method: :{node.method}")
        self.indent += 1
        node.table.accept(self)
        self.indent -= 1
    
    def visit_UnaryExpr(self, node: UnaryExpr):
        op_names = {
            UnaryOp.MINUS: '-',
            UnaryOp.NOT: 'not',
            UnaryOp.LEN: '#',
            UnaryOp.BNOT: '~',
        }
        self._emit(f"Unary: {op_names.get(node.op, '?')}")
        self.indent += 1
        node.operand.accept(self)
        self.indent -= 1
    
    def visit_BinaryExpr(self, node: BinaryExpr):
        op_names = {
            BinaryOp.ADD: '+', BinaryOp.SUB: '-', BinaryOp.MUL: '*',
            BinaryOp.DIV: '/', BinaryOp.IDIV: '//', BinaryOp.MOD: '%',
            BinaryOp.POW: '^', BinaryOp.CONCAT: '..', BinaryOp.LT: '<',
            BinaryOp.LE: '<=', BinaryOp.GT: '>', BinaryOp.GE: '>=',
            BinaryOp.EQ: '==', BinaryOp.NE: '~=', BinaryOp.AND: 'and',
            BinaryOp.OR: 'or', BinaryOp.BAND: '&', BinaryOp.BOR: '|',
            BinaryOp.BXOR: '~', BinaryOp.SHL: '<<', BinaryOp.SHR: '>>',
        }
        self._emit(f"Binary: {op_names.get(node.op, '?')}")
        self.indent += 1
        self._emit("left:")
        self.indent += 1
        node.left.accept(self)
        self.indent -= 1
        self._emit("right:")
        self.indent += 1
        node.right.accept(self)
        self.indent -= 1
        self.indent -= 1
    
    def visit_TableConstructor(self, node: TableConstructor):
        self._emit(f"Table ({len(node.fields)} fields)")
        self.indent += 1
        for i, f in enumerate(node.fields):
            if f.key:
                self._emit(f"[{i}] key:")
                self.indent += 1
                f.key.accept(self)
                self.indent -= 1
            else:
                self._emit(f"[{i}] (list item)")
            self._emit("value:")
            self.indent += 1
            f.value.accept(self)
            self.indent -= 1
        self.indent -= 1
    
    def visit_FuncCall(self, node: FuncCall):
        method = " (method)" if node.is_method else ""
        self._emit(f"Call{method}")
        self.indent += 1
        self._emit("func:")
        self.indent += 1
        node.func.accept(self)
        self.indent -= 1
        if node.args:
            self._emit(f"args ({len(node.args)}):")
            self.indent += 1
            for arg in node.args:
                arg.accept(self)
            self.indent -= 1
        self.indent -= 1
    
    def visit_FuncExpr(self, node: FuncExpr):
        self._emit("FunctionExpr")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1
    
    def visit_FuncBody(self, node: FuncBody):
        vararg = ", ..." if node.is_vararg else ""
        params = ", ".join(node.params)
        self._emit(f"Params: ({params}{vararg})")
        if node.body:
            node.body.accept(self)
    
    def visit_AssignStat(self, node: AssignStat):
        self._emit(f"Assign ({len(node.targets)} = {len(node.values)})")
        self.indent += 1
        self._emit("targets:")
        self.indent += 1
        for t in node.targets:
            t.accept(self)
        self.indent -= 1
        self._emit("values:")
        self.indent += 1
        for v in node.values:
            v.accept(self)
        self.indent -= 1
        self.indent -= 1
    
    def visit_LocalVarStat(self, node: LocalVarStat):
        names = ", ".join(node.names)
        self._emit(f"LocalVar: {names}")
        if node.values:
            self.indent += 1
            self._emit("values:")
            self.indent += 1
            for v in node.values:
                v.accept(self)
            self.indent -= 1
            self.indent -= 1
    
    def visit_LocalFuncStat(self, node: LocalFuncStat):
        self._emit(f"LocalFunc: {node.name}")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1
    
    def visit_FuncStat(self, node: FuncStat):
        self._emit("Function")
        self.indent += 1
        self._emit("name:")
        self.indent += 1
        node.name.accept(self)
        self.indent -= 1
        node.body.accept(self)
        self.indent -= 1
    
    def visit_CallStat(self, node: CallStat):
        self._emit("CallStatement")
        self.indent += 1
        node.call.accept(self)
        self.indent -= 1
    
    def visit_DoStat(self, node: DoStat):
        self._emit("Do")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1
    
    def visit_WhileStat(self, node: WhileStat):
        self._emit("While")
        self.indent += 1
        self._emit("condition:")
        self.indent += 1
        node.condition.accept(self)
        self.indent -= 1
        self._emit("body:")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1
        self.indent -= 1
    
    def visit_RepeatStat(self, node: RepeatStat):
        self._emit("Repeat")
        self.indent += 1
        self._emit("body:")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1
        self._emit("until:")
        self.indent += 1
        node.condition.accept(self)
        self.indent -= 1
        self.indent -= 1
    
    def visit_IfStat(self, node: IfStat):
        self._emit("If")
        self.indent += 1
        self._emit("condition:")
        self.indent += 1
        node.condition.accept(self)
        self.indent -= 1
        self._emit("then:")
        self.indent += 1
        node.then_block.accept(self)
        self.indent -= 1
        for cond, block in node.elseif_clauses:
            self._emit("elseif:")
            self.indent += 1
            cond.accept(self)
            self.indent -= 1
            self._emit("then:")
            self.indent += 1
            block.accept(self)
            self.indent -= 1
        if node.else_block:
            self._emit("else:")
            self.indent += 1
            node.else_block.accept(self)
            self.indent -= 1
        self.indent -= 1
    
    def visit_ForNumStat(self, node: ForNumStat):
        self._emit(f"ForNum: {node.var}")
        self.indent += 1
        self._emit("start:")
        self.indent += 1
        node.start.accept(self)
        self.indent -= 1
        self._emit("stop:")
        self.indent += 1
        node.stop.accept(self)
        self.indent -= 1
        if node.step:
            self._emit("step:")
            self.indent += 1
            node.step.accept(self)
            self.indent -= 1
        self._emit("body:")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1
        self.indent -= 1
    
    def visit_ForInStat(self, node: ForInStat):
        names = ", ".join(node.names)
        self._emit(f"ForIn: {names}")
        self.indent += 1
        self._emit("exprs:")
        self.indent += 1
        for e in node.exprs:
            e.accept(self)
        self.indent -= 1
        self._emit("body:")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1
        self.indent -= 1
    
    def visit_BreakStat(self, node: BreakStat):
        self._emit("Break")
    
    def visit_GotoStat(self, node: GotoStat):
        self._emit(f"Goto: {node.label}")
    
    def visit_LabelStat(self, node: LabelStat):
        self._emit(f"Label: ::{node.name}::")
    
    def visit_ReturnStat(self, node: ReturnStat):
        self._emit(f"Return ({len(node.values)} values)")
        if node.values:
            self.indent += 1
            for v in node.values:
                v.accept(self)
            self.indent -= 1
    
    def visit_EmptyStat(self, node: EmptyStat):
        self._emit(";")
