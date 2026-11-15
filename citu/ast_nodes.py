"""Abstract syntax tree node classes for Citu.

Every node carries the source position of the construct it came from and an
empty `ctype` slot that the semantic analyser fills in.  `to_dict()` turns a
whole tree into plain Python data, which is what the .ast.json and
.tast.json intermediate files contain.
"""

ORDER = {}      # node kind -> field order used when serialising


class Node(object):
    """Base class.  Subclasses only declare `kind` and `fields`."""

    kind = "Node"
    fields = ()

    def __init__(self, line=0, col=0, **kw):
        self.line = line
        self.col = col
        self.ctype = None          # filled by the semantic analyser
        self.sym = None            # resolved Symbol, for name-bearing nodes
        for name in self.fields:
            setattr(self, name, kw.pop(name, None))
        if kw:
            raise TypeError("%s got unexpected fields %s"
                            % (self.kind, sorted(kw)))

    # -- serialisation ----------------------------------------------------
    def to_dict(self, typed=False):
        out = {"kind": self.kind, "line": self.line, "col": self.col}
        if typed and self.ctype is not None:
            out["ctype"] = self.ctype
        for name in self.fields:
            out[name] = _conv(getattr(self, name), typed)
        return out

    def children(self):
        """Direct child nodes, in source order."""
        out = []
        for name in self.fields:
            v = getattr(self, name)
            if isinstance(v, Node):
                out.append(v)
            elif isinstance(v, list):
                out.extend(x for x in v if isinstance(x, Node))
        return out

    def __repr__(self):
        bits = ", ".join("%s=%r" % (f, getattr(self, f)) for f in self.fields)
        return "%s(%s)" % (self.kind, bits)


def _conv(v, typed):
    if isinstance(v, Node):
        return v.to_dict(typed)
    if isinstance(v, list):
        return [_conv(x, typed) for x in v]
    return v


def _node(kind, *fields):
    cls = type(kind, (Node,), {"kind": kind, "fields": tuple(fields)})
    ORDER[kind] = tuple(fields)
    globals()[kind] = cls
    return cls


# ------------------------------------------------------------- statements --
Program     = _node("Program", "stmts")
VarDecl     = _node("VarDecl", "type_name", "name", "init")
ArrayDecl   = _node("ArrayDecl", "type_name", "name", "size")
Assign      = _node("Assign", "name", "value")
IndexAssign = _node("IndexAssign", "name", "index", "value")
If          = _node("If", "cond", "then_block", "else_block")
While       = _node("While", "cond", "body")
Break       = _node("Break")
Print       = _node("Print", "args")
Block       = _node("Block", "stmts")

# ------------------------------------------------------------ expressions --
Binary  = _node("Binary", "op", "left", "right")
Unary   = _node("Unary", "op", "operand")
Var     = _node("Var", "name")
Index   = _node("Index", "name", "index")
IntLit  = _node("IntLit", "value")
RealLit = _node("RealLit", "value")
CharLit = _node("CharLit", "value")
StrLit  = _node("StrLit", "value")


# --------------------------------------------------------------- printing --
def render(node, indent=0, out=None):
    """Indented text rendering of an AST, used for debugging and the docs."""
    if out is None:
        out = []
    pad = "  " * indent
    scalars = []
    for f in node.fields:
        v = getattr(node, f)
        if not isinstance(v, (Node, list)):
            if v is not None:
                scalars.append("%s=%r" % (f, v))
    tag = node.kind
    if scalars:
        tag += " [" + ", ".join(scalars) + "]"
    if node.ctype:
        tag += " : " + node.ctype
    out.append("%s%s" % (pad, tag))
    for child in node.children():
        render(child, indent + 1, out)
    return out
