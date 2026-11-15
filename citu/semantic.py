"""Citu semantic analyser (phase 3).

Walks the AST produced by the parser and

  * builds the symbol table (scopes, declarations, offsets);
  * resolves every identifier to a symbol;
  * computes and checks the type of every expression, writing the result
    into each node's `ctype` slot;
  * applies the context rules that a context-free grammar cannot express:
        - a name must be declared before it is used, and only once per scope
        - an array name needs a subscript, a scalar name must not have one
        - a subscript must have an integral type and, when it is a constant,
          must be inside the declared bounds
        - the condition of `agar` / `jabtak` must be a bool-valued expression
        - `nikal` may only appear inside a `jabtak` loop
        - `%` needs integral operands; division by a literal zero is an error
        - an assignment must be type compatible, with a warning on a
          narrowing, truncating or signedness-changing conversion

The output is the same AST, now annotated with types (written out as
.tast.json), plus the symbol table (.sym).
"""

from . import ast_nodes as A
from .errors import DiagnosticBag
from .symtab import (SymbolTable, RANGES, assignable, is_integral,
                     is_numeric, promote)

ARITH_OPS = ("+", "-", "*", "/", "%")
REL_OPS = ("=", "!=", "<", "<=", ">", ">=")
LOGIC_OPS = ("aur", "ya")


class SemanticAnalyzer(object):

    def __init__(self, filename="<source>", diagnostics=None):
        self.filename = filename
        self.diag = diagnostics if diagnostics is not None else DiagnosticBag()
        self.table = SymbolTable()
        self.loop_depth = 0

    # ------------------------------------------------------------ helpers --
    def err(self, node, msg):
        self.diag.error("semantic", node.line, node.col, msg)

    def warn(self, node, msg):
        self.diag.warning("semantic", node.line, node.col, msg)

    # -------------------------------------------------------------- entry --
    def analyze(self, program):
        for s in program.stmts:
            self.stmt(s)
        self.check_unused()
        program.ctype = "void"
        return program

    def check_unused(self):
        for sc in self.table.all_scopes:
            for sym in sc:
                if sym.reads == 0 and sym.writes == 0:
                    self.diag.warning(
                        "semantic", sym.line, sym.col,
                        "'%s' is declared but never used" % sym.name)
                elif sym.reads == 0:
                    self.diag.warning(
                        "semantic", sym.line, sym.col,
                        "'%s' is assigned but its value is never read"
                        % sym.name)

    # --------------------------------------------------------- statements --
    def stmt(self, node):
        getattr(self, "st_" + node.kind)(node)

    def st_Block(self, node):
        self.table.push("block@%d:%d" % (node.line, node.col))
        for s in node.stmts:
            self.stmt(s)
        self.table.pop()
        node.ctype = "void"

    def st_VarDecl(self, node):
        sym, already = self.table.declare(
            node.name, "scalar", node.type_name, 1, node.line, node.col)
        if already:
            self.err(node, "'%s' is already declared in this scope "
                           "(first declared at line %d)"
                     % (node.name, sym.line))
            return
        node.sym = sym
        if node.init is not None:
            vt = self.expr(node.init)
            self.check_assign(node, node.type_name, vt, node.name)
            sym.assigned = True
            sym.writes += 1
            self.fold_range_check(node.init, node.type_name)
        node.ctype = node.type_name

    def st_ArrayDecl(self, node):
        if node.size is None or node.size <= 0:
            self.err(node, "array '%s' must have a size greater than 0"
                     % node.name)
            size = 1
        else:
            size = node.size
        sym, already = self.table.declare(
            node.name, "array", node.type_name, size, node.line, node.col)
        if already:
            self.err(node, "'%s' is already declared in this scope "
                           "(first declared at line %d)"
                     % (node.name, sym.line))
        node.sym = sym
        node.ctype = node.type_name

    def st_Assign(self, node):
        sym = self.table.lookup(node.name)
        if sym is None:
            self.err(node, "'%s' is not declared" % node.name)
            self.expr(node.value)
            return
        if sym.sym_kind == "array":
            self.err(node, "'%s' is an array; assign to an element such as "
                           "%s[0]" % (node.name, node.name))
            self.expr(node.value)
            return
        node.sym = sym
        vt = self.expr(node.value)
        self.check_assign(node, sym.type_name, vt, node.name)
        self.fold_range_check(node.value, sym.type_name)
        sym.assigned = True
        sym.writes += 1
        node.ctype = sym.type_name

    def st_IndexAssign(self, node):
        sym = self.table.lookup(node.name)
        if sym is None:
            self.err(node, "'%s' is not declared" % node.name)
            self.expr(node.index)
            self.expr(node.value)
            return
        if sym.sym_kind != "array":
            self.err(node, "'%s' is not an array, so it cannot be subscripted"
                     % node.name)
        node.sym = sym
        self.check_index(node, sym, node.index)
        vt = self.expr(node.value)
        self.check_assign(node, sym.type_name, vt, "%s[]" % node.name)
        sym.assigned = True
        sym.writes += 1
        node.ctype = sym.type_name

    def st_If(self, node):
        ct = self.expr(node.cond)
        self.check_condition(node.cond, ct, "agar")
        self.st_Block(node.then_block)
        if node.else_block is not None:
            self.st_Block(node.else_block)
        node.ctype = "void"

    def st_While(self, node):
        ct = self.expr(node.cond)
        self.check_condition(node.cond, ct, "jabtak")
        self.loop_depth += 1
        self.st_Block(node.body)
        self.loop_depth -= 1
        node.ctype = "void"

    def st_Break(self, node):
        if self.loop_depth == 0:
            self.err(node, "'nikal' is only allowed inside a 'jabtak' loop")
        node.ctype = "void"

    def st_Print(self, node):
        for a in node.args:
            t = self.expr(a)
            if t is None:
                continue          # the operand already reported an error
            if t not in ("string", "bool") and not is_numeric(t):
                self.err(a, "'dikhao' cannot print a value of type %s" % t)
        node.ctype = "void"

    # ---------------------------------------------------------- the rules --
    def check_condition(self, node, t, keyword):
        if t != "bool":
            self.err(node,
                     "the condition of '%s' must be a comparison, not a "
                     "plain %s value" % (keyword, t))

    def check_assign(self, node, target, source, what):
        if source is None:
            return
        ok, note = assignable(target, source)
        if not ok:
            self.err(node, "cannot assign a %s value to '%s' of type %s"
                     % (source, what, target))
            return
        if note == "narrowing":
            self.warn(node, "narrowing conversion: %s value stored into "
                            "'%s' of type %s" % (source, what, target))
        elif note == "truncation":
            self.warn(node, "real value stored into '%s' of type %s loses "
                            "its fractional part" % (what, target))
        elif note == "signedness":
            self.warn(node, "signed/unsigned mismatch storing a %s value "
                            "into '%s' of type %s" % (source, what, target))

    def check_index(self, node, sym, index_node):
        it = self.expr(index_node)
        if it is None:
            return
        if not is_integral(it):
            self.err(index_node,
                     "array subscript must have an integer type, not %s" % it)
            return
        if isinstance(index_node, A.IntLit) and sym.sym_kind == "array":
            if index_node.value >= sym.length:
                self.err(index_node,
                         "index %d is outside '%s', which has %d elements "
                         "(0 to %d)" % (index_node.value, sym.name,
                                        sym.length, sym.length - 1))

    def fold_range_check(self, node, target):
        """If the initialiser is a literal, check it fits the target type."""
        if target not in RANGES:
            return
        value = None
        if isinstance(node, A.IntLit):
            value = node.value
        elif (isinstance(node, A.Unary) and node.op == "-"
                and isinstance(node.operand, A.IntLit)):
            value = -node.operand.value
        if value is None:
            return
        lo, hi = RANGES[target]
        if not (lo <= value <= hi):
            self.err(node, "literal %d does not fit in %s (range %d..%d)"
                     % (value, target, lo, hi))

    # -------------------------------------------------------- expressions --
    def expr(self, node):
        t = getattr(self, "ex_" + node.kind)(node)
        node.ctype = t
        return t

    def ex_IntLit(self, node):
        return "intlit"

    def ex_RealLit(self, node):
        return "real"

    def ex_CharLit(self, node):
        return "char"

    def ex_StrLit(self, node):
        return "string"

    def ex_Var(self, node):
        sym = self.table.lookup(node.name)
        if sym is None:
            self.err(node, "'%s' is not declared" % node.name)
            return None
        if sym.sym_kind == "array":
            self.err(node, "'%s' is an array; it needs a subscript such as "
                           "%s[0]" % (node.name, node.name))
            return None
        if not sym.assigned:
            self.warn(node, "'%s' may be read before it is given a value"
                      % node.name)
        sym.reads += 1
        node.sym = sym
        return sym.type_name

    def ex_Index(self, node):
        sym = self.table.lookup(node.name)
        if sym is None:
            self.err(node, "'%s' is not declared" % node.name)
            self.expr(node.index)
            return None
        if sym.sym_kind != "array":
            self.err(node, "'%s' is not an array, so it cannot be subscripted"
                     % node.name)
            self.expr(node.index)
            return None
        self.check_index(node, sym, node.index)
        sym.reads += 1
        node.sym = sym
        return sym.type_name

    def ex_Unary(self, node):
        t = self.expr(node.operand)
        if t is None:
            return None
        if node.op == "-":
            if not is_numeric(t):
                self.err(node, "unary '-' needs a number, not %s" % t)
                return None
            return "int16" if t == "char" else t
        # nahi
        if t != "bool":
            self.err(node, "'nahi' needs a comparison, not a %s value" % t)
            return None
        return "bool"

    def ex_Binary(self, node):
        lt = self.expr(node.left)
        rt = self.expr(node.right)
        op = node.op

        if op in LOGIC_OPS:
            if lt is not None and lt != "bool":
                self.err(node.left,
                         "left operand of '%s' must be a comparison, not %s"
                         % (op, lt))
            if rt is not None and rt != "bool":
                self.err(node.right,
                         "right operand of '%s' must be a comparison, not %s"
                         % (op, rt))
            return "bool"

        if lt is None or rt is None:
            return None

        if op in REL_OPS:
            if not (is_numeric(lt) and is_numeric(rt)):
                self.err(node, "cannot compare %s with %s" % (lt, rt))
                return None
            return "bool"

        # arithmetic
        if not (is_numeric(lt) and is_numeric(rt)):
            self.err(node, "operator '%s' needs numbers, not %s and %s"
                     % (op, lt, rt))
            return None
        if op == "%":
            if not (is_integral(lt) and is_integral(rt)):
                self.err(node, "operator '%%' needs integer operands, "
                               "not %s and %s" % (lt, rt))
                return None
        if op in ("/", "%"):
            r = node.right
            if isinstance(r, A.IntLit) and r.value == 0:
                self.err(node, "division by zero")
            elif isinstance(r, A.RealLit) and r.value == 0.0:
                self.err(node, "division by zero")
        return promote(lt, rt)

    # ------------------------------------------------ intermediate files --
    def write_symbol_file(self, path):
        return self.table.write_symbol_file(path, self.filename)


def analyze(program, filename="<source>", diagnostics=None):
    sa = SemanticAnalyzer(filename, diagnostics)
    sa.analyze(program)
    return sa
