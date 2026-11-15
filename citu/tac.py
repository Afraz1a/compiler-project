"""Citu intermediate-code generator (phase 4).

Walks the type-annotated AST and emits THREE-ADDRESS CODE as a flat list of
quadruples

        (op, arg1, arg2, result)

Each quadruple performs at most one operation on at most two operands, so
every expression tree is flattened into a sequence of simple steps joined by
compiler-generated temporaries t0, t1, ...  Control flow becomes labels and
jumps.  This is the representation an optimiser and a code generator want,
and it is what the .tac intermediate file contains.

Operands are small objects rather than plain strings so that later phases
can tell a constant from a variable from a temporary without re-parsing
text:

    Const(value, type)   a literal
    Name(name, type)     a declared variable or array
    Temp(n, type)        a compiler-generated temporary
    Label(name)          a jump target
"""

from . import ast_nodes as A
from .symtab import promote

# ----------------------------------------------------------------- opcodes --
# op         arg1        arg2       result     meaning
# ---------- ----------- ---------- ---------- -------------------------------
# alloc      type        length     name       reserve storage
# assign     src         -          dst        dst = src
# add/sub/   lhs         rhs        dst        dst = lhs <op> rhs
#  mul/div/
#  mod
# lt/le/gt/  lhs         rhs        dst        dst = lhs <rel> rhs  (0 or 1)
#  ge/eq/ne
# neg        src         -          dst        dst = -src
# not        src         -          dst        dst = logical not src
# cast       src         type       dst        dst = (type) src
# aload      array       index      dst        dst = array[index]
# astore     index       src        array      array[index] = src
# label      name        -          -          jump target
# goto       label       -          -          unconditional jump
# iffalse    cond        label      -          jump if cond is 0
# iftrue     cond        label      -          jump if cond is not 0
# print      value       -          -          write one value
# printstr   text        -          -          write a string literal
# newline    -           -          -          end the current output line
# halt       -           -          -          stop

BINOP = {"+": "add", "-": "sub", "*": "mul", "/": "div", "%": "mod",
         "<": "lt", "<=": "le", ">": "gt", ">=": "ge",
         "=": "eq", "!=": "ne"}

RELOPS = frozenset(["lt", "le", "gt", "ge", "eq", "ne"])
ARITHOPS = frozenset(["add", "sub", "mul", "div", "mod"])

SYMBOL_OF = {"add": "+", "sub": "-", "mul": "*", "div": "/", "mod": "%",
             "lt": "<", "le": "<=", "gt": ">", "ge": ">=",
             "eq": "==", "ne": "!="}


# ---------------------------------------------------------------- operands --
class Operand(object):
    __slots__ = ("ctype",)


class Const(Operand):
    __slots__ = ("value",)

    def __init__(self, value, ctype):
        self.value = value
        self.ctype = ctype

    def __str__(self):
        if self.ctype == "char":
            return repr(self.value)
        if self.ctype == "string":
            return '"%s"' % self.value.replace("\n", "\\n")
        return str(self.value)

    def __eq__(self, other):
        return (isinstance(other, Const) and other.value == self.value
                and other.ctype == self.ctype)

    def __hash__(self):
        return hash(("c", self.value, self.ctype))


class Name(Operand):
    __slots__ = ("name",)

    def __init__(self, name, ctype):
        self.name = name
        self.ctype = ctype

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Name) and other.name == self.name

    def __hash__(self):
        return hash(("n", self.name))


class Temp(Operand):
    __slots__ = ("n",)

    def __init__(self, n, ctype):
        self.n = n
        self.ctype = ctype

    def __str__(self):
        return "t%d" % self.n

    def __eq__(self, other):
        return isinstance(other, Temp) and other.n == self.n

    def __hash__(self):
        return hash(("t", self.n))


class Label(Operand):
    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name
        self.ctype = None

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Label) and other.name == self.name

    def __hash__(self):
        return hash(("L", self.name))


class Quad(object):
    """One three-address instruction."""

    __slots__ = ("op", "arg1", "arg2", "result", "line")

    def __init__(self, op, arg1=None, arg2=None, result=None, line=0):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
        self.line = line

    # -- rendering --------------------------------------------------------
    def readable(self):
        op, a, b, r = self.op, self.arg1, self.arg2, self.result
        if op == "alloc":
            return "alloc %s %s[%s]" % (a, r, b)
        if op == "assign":
            return "%s = %s" % (r, a)
        if op in ARITHOPS or op in RELOPS:
            return "%s = %s %s %s" % (r, a, SYMBOL_OF[op], b)
        if op == "neg":
            return "%s = -%s" % (r, a)
        if op == "not":
            return "%s = not %s" % (r, a)
        if op == "cast":
            return "%s = (%s) %s" % (r, b, a)
        if op == "aload":
            return "%s = %s[%s]" % (r, a, b)
        if op == "astore":
            return "%s[%s] = %s" % (r, a, b)
        if op == "label":
            return "%s:" % a
        if op == "goto":
            return "goto %s" % a
        if op == "iffalse":
            return "ifFalse %s goto %s" % (a, b)
        if op == "iftrue":
            return "if %s goto %s" % (a, b)
        if op == "print":
            return "print %s" % a
        if op == "printstr":
            return "print %s" % a
        if op == "newline":
            return "newline"
        if op == "halt":
            return "halt"
        return op

    def fields(self):
        def s(x):
            return "-" if x is None else str(x)
        return s(self.arg1), s(self.arg2), s(self.result)

    def __repr__(self):
        return "Quad(%s)" % self.readable()


# --------------------------------------------------------------- generator --
class TACGenerator(object):

    def __init__(self, symbol_table, filename="<source>"):
        self.table = symbol_table
        self.filename = filename
        self.code = []
        self._temp = 0
        self._label = 0
        self._break_stack = []
        self._types = {}            # variable name -> declared type

    # -- emission ---------------------------------------------------------
    def emit(self, op, arg1=None, arg2=None, result=None, line=0):
        q = Quad(op, arg1, arg2, result, line)
        self.code.append(q)
        return q

    def new_temp(self, ctype):
        t = Temp(self._temp, ctype)
        self._temp += 1
        return t

    def new_label(self, hint="L"):
        lb = Label("%s%d" % (hint, self._label))
        self._label += 1
        return lb

    def coerce(self, operand, target, line):
        """Insert a cast when the operand is not already of `target` type."""
        if operand is None or target is None:
            return operand
        if operand.ctype == target or target in ("bool", "string"):
            return operand
        if operand.ctype in ("bool", "string"):
            return operand
        if isinstance(operand, Const):
            if target == "real":
                return Const(float(operand.value), "real")
            if operand.ctype == "char":
                return Const(ord(operand.value), target)
            if operand.ctype == "real":
                return Const(int(operand.value), target)
            return Const(operand.value, target)
        dst = self.new_temp(target)
        self.emit("cast", operand, target, dst, line)
        return dst

    # -- entry ------------------------------------------------------------
    def generate(self, program):
        # Storage declarations first, in declaration order, so the .tac file
        # is self-contained and the interpreter needs nothing else.
        for sc in self.table.all_scopes:
            for sym in sc:
                self._types[sym.rt_name] = sym.type_name
                self.emit("alloc", sym.type_name, sym.length,
                          Name(sym.rt_name, sym.type_name), sym.line)
        for s in program.stmts:
            self.stmt(s)
        self.emit("halt")
        return self.code

    # -- statements -------------------------------------------------------
    def stmt(self, node):
        getattr(self, "st_" + node.kind)(node)

    def st_Block(self, node):
        for s in node.stmts:
            self.stmt(s)

    def st_ArrayDecl(self, node):
        pass            # storage already reserved by the alloc preamble

    def st_VarDecl(self, node):
        if node.init is None:
            return
        v = self.expr(node.init)
        v = self.coerce(v, node.type_name, node.line)
        self.emit("assign", v, None,
                  Name(_rt(node), node.type_name), node.line)

    def st_Assign(self, node):
        v = self.expr(node.value)
        rt = _rt(node)
        t = self._types.get(rt, node.ctype)
        v = self.coerce(v, t, node.line)
        self.emit("assign", v, None, Name(rt, t), node.line)

    def st_IndexAssign(self, node):
        idx = self.expr(node.index)
        v = self.expr(node.value)
        rt = _rt(node)
        t = self._types.get(rt, node.ctype)
        v = self.coerce(v, t, node.line)
        self.emit("astore", idx, v, Name(rt, t), node.line)

    def st_If(self, node):
        cond = self.expr(node.cond)
        if node.else_block is None:
            end = self.new_label("Lend")
            self.emit("iffalse", cond, end, None, node.line)
            self.st_Block(node.then_block)
            self.emit("label", end)
        else:
            els = self.new_label("Lelse")
            end = self.new_label("Lend")
            self.emit("iffalse", cond, els, None, node.line)
            self.st_Block(node.then_block)
            self.emit("goto", end)
            self.emit("label", els)
            self.st_Block(node.else_block)
            self.emit("label", end)

    def st_While(self, node):
        top = self.new_label("Ltop")
        end = self.new_label("Lend")
        self.emit("label", top)
        cond = self.expr(node.cond)
        self.emit("iffalse", cond, end, None, node.line)
        self._break_stack.append(end)
        self.st_Block(node.body)
        self._break_stack.pop()
        self.emit("goto", top)
        self.emit("label", end)

    def st_Break(self, node):
        if self._break_stack:
            self.emit("goto", self._break_stack[-1], None, None, node.line)

    def st_Print(self, node):
        for a in node.args:
            if isinstance(a, A.StrLit):
                self.emit("printstr", Const(a.value, "string"),
                          None, None, node.line)
            else:
                v = self.expr(a)
                self.emit("print", v, None, None, node.line)
        self.emit("newline", None, None, None, node.line)

    # -- expressions ------------------------------------------------------
    def expr(self, node):
        return getattr(self, "ex_" + node.kind)(node)

    def ex_IntLit(self, node):
        return Const(node.value, node.ctype or "int32")

    def ex_RealLit(self, node):
        return Const(node.value, "real")

    def ex_CharLit(self, node):
        return Const(node.value, "char")

    def ex_StrLit(self, node):
        return Const(node.value, "string")

    def ex_Var(self, node):
        return Name(_rt(node), node.ctype)

    def ex_Index(self, node):
        idx = self.expr(node.index)
        dst = self.new_temp(node.ctype)
        self.emit("aload", Name(_rt(node), node.ctype), idx, dst, node.line)
        return dst

    def ex_Unary(self, node):
        v = self.expr(node.operand)
        dst = self.new_temp(node.ctype)
        self.emit("neg" if node.op == "-" else "not", v, None, dst, node.line)
        return dst

    def ex_Binary(self, node):
        op = node.op
        if op in ("aur", "ya"):
            return self._short_circuit(node)

        lhs = self.expr(node.left)
        rhs = self.expr(node.right)
        code = BINOP[op]

        if code in RELOPS:
            common = promote(_num(lhs.ctype), _num(rhs.ctype))
            lhs = self.coerce(lhs, common, node.line)
            rhs = self.coerce(rhs, common, node.line)
            dst = self.new_temp("bool")
        else:
            lhs = self.coerce(lhs, node.ctype, node.line)
            rhs = self.coerce(rhs, node.ctype, node.line)
            dst = self.new_temp(node.ctype)

        self.emit(code, lhs, rhs, dst, node.line)
        return dst

    def _short_circuit(self, node):
        """`aur` and `ya` evaluate the right operand only when they must."""
        dst = self.new_temp("bool")
        done = self.new_label("Lsc")
        if node.op == "aur":
            self.emit("assign", Const(0, "bool"), None, dst, node.line)
            left = self.expr(node.left)
            self.emit("iffalse", left, done, None, node.line)
            right = self.expr(node.right)
            self.emit("iffalse", right, done, None, node.line)
            self.emit("assign", Const(1, "bool"), None, dst, node.line)
        else:
            self.emit("assign", Const(1, "bool"), None, dst, node.line)
            left = self.expr(node.left)
            self.emit("iftrue", left, done, None, node.line)
            right = self.expr(node.right)
            self.emit("iftrue", right, done, None, node.line)
            self.emit("assign", Const(0, "bool"), None, dst, node.line)
        self.emit("label", done)
        return dst

    # -- intermediate file -------------------------------------------------
    def write_tac_file(self, path, title="citu-tac"):
        return write_tac(self.code, path, self.filename, title)


def _rt(node):
    """The unique run-time name of the variable a node refers to."""
    return node.sym.rt_name if node.sym is not None else node.name


def _num(t):
    """Treat bool as a small integer when a common type is needed."""
    return "int16" if t in (None, "bool") else t


def _settled(t):
    """The concrete type an operand ends up with."""
    return "int32" if t in (None, "intlit", "bool") else t


def write_tac(code, path, source, title="citu-tac"):
    """Write a quadruple listing -- the .tac / .opt.tac format (doc 4.5)."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# %s v1\n" % title)
        fh.write("# source: %s\n" % source)
        fh.write("# instructions: %d   temporaries: %d   labels: %d\n"
                 % (len(code),
                    len({str(q.result) for q in code
                         if isinstance(q.result, Temp)}),
                    sum(1 for q in code if q.op == "label")))
        fh.write("# fields: INDEX | OP | ARG1 | ARG2 | RESULT"
                 "   ; readable form\n")
        fh.write("#" + "-" * 86 + "\n")
        for i, q in enumerate(code):
            a1, a2, r = q.fields()
            fh.write("%04d | %-8s | %-12s | %-12s | %-10s ; %s\n"
                     % (i, q.op, a1, a2, r, q.readable()))
        fh.write("#" + "-" * 86 + "\n")
    return path


def generate(program, symbol_table, filename="<source>"):
    g = TACGenerator(symbol_table, filename)
    g.generate(program)
    return g
