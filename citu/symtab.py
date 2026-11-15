"""Symbol table and type system for Citu.

The symbol table is a STACK OF SCOPES.  Each scope is a hash table mapping a
name to a Symbol.  Entering a `shuro ... khatam` block pushes a new scope;
leaving it pops the scope.  A lookup walks the stack from the innermost
scope outwards, which gives the usual shadowing rule.

Popped scopes are not thrown away: they stay in `all_scopes` so that the
whole table can be written out as the .sym intermediate file after the
semantic phase has finished.
"""

# --------------------------------------------------------------------------
# Types
# --------------------------------------------------------------------------
# Every Citu type is described by (width in bytes, kind, signed, rank).
# 'bool' and 'string' are INTERNAL types: the programmer cannot declare them,
# they only ever arise as the type of an expression.
TYPES = {
    "char":   {"width": 1, "kind": "int",    "signed": True,  "rank": 1},
    "int16":  {"width": 2, "kind": "int",    "signed": True,  "rank": 2},
    "uint16": {"width": 2, "kind": "int",    "signed": False, "rank": 3},
    "int32":  {"width": 4, "kind": "int",    "signed": True,  "rank": 4},
    "uint32": {"width": 4, "kind": "int",    "signed": False, "rank": 5},
    "real":   {"width": 8, "kind": "real",   "signed": True,  "rank": 6},
    "bool":   {"width": 1, "kind": "bool",   "signed": False, "rank": 0},
    # 'intlit' is the type of an integer literal before it is used.  It
    # adapts to whatever integer type it meets, exactly so that writing
    # `uint16 n medalo 40;` is not reported as a narrowing conversion.
    "intlit": {"width": 4, "kind": "int",    "signed": True,  "rank": 0},
    "string": {"width": 0, "kind": "string", "signed": False, "rank": 0},
}

DECLARABLE = ("char", "int16", "uint16", "int32", "uint32", "real")
NUMERIC = ("char", "int16", "uint16", "int32", "uint32", "real", "intlit")
INTEGRAL = ("char", "int16", "uint16", "int32", "uint32", "intlit")

# Inclusive value range of every integer type, used for constant checking.
RANGES = {
    "char":   (-128, 127),
    "int16":  (-32768, 32767),
    "uint16": (0, 65535),
    "int32":  (-2147483648, 2147483647),
    "uint32": (0, 4294967295),
    "intlit": (-2147483648, 2147483647),
}


def width_of(type_name):
    return TYPES[type_name]["width"]


def is_numeric(t):
    return t in NUMERIC


def is_integral(t):
    return t in INTEGRAL


def promote(a, b):
    """Usual arithmetic conversion: the common type of `a` and `b`."""
    # An integer literal takes the type of whatever it is combined with.
    if a == "intlit" and b == "intlit":
        return "int32"
    if a == "intlit":
        return "int32" if b in ("bool", None) else b
    if b == "intlit":
        return "int32" if a in ("bool", None) else a
    if a == "real" or b == "real":
        return "real"
    ra, rb = TYPES[a]["rank"], TYPES[b]["rank"]
    wider = a if ra >= rb else b
    # char only ever takes part in arithmetic after widening to int16
    if wider == "char":
        return "int16"
    return wider


def assignable(target, source):
    """Return (ok, note).  `note` is None, 'narrowing' or 'signedness'."""
    if target == source:
        return True, None
    if not (is_numeric(target) and is_numeric(source)):
        return False, None
    # a literal that fits the target is a silent conversion; whether it
    # actually fits is checked separately by fold_range_check()
    if source == "intlit":
        return True, None
    if target == "real":
        return True, None
    if source == "real":
        return True, "truncation"
    if TYPES[source]["width"] > TYPES[target]["width"]:
        return True, "narrowing"
    if TYPES[source]["signed"] != TYPES[target]["signed"]:
        return True, "signedness"
    return True, None


# --------------------------------------------------------------------------
# Symbols and scopes
# --------------------------------------------------------------------------
class Symbol(object):
    """One entry of the symbol table."""

    __slots__ = ("name", "rt_name", "sym_kind", "type_name", "length",
                 "width", "offset", "scope_level", "scope_id", "line", "col",
                 "assigned", "reads", "writes")

    def __init__(self, name, sym_kind, type_name, length, offset,
                 scope_level, scope_id, line, col, rt_name=None):
        self.name = name
        # Two blocks may each declare a `d`.  They are different variables,
        # so each symbol gets a unique run-time name; the plain name is kept
        # when it is unambiguous, which keeps the generated code readable.
        self.rt_name = rt_name or name
        self.sym_kind = sym_kind          # 'scalar' | 'array'
        self.type_name = type_name
        self.length = length              # element count (1 for a scalar)
        self.width = width_of(type_name) * length
        self.offset = offset              # byte offset inside the frame
        self.scope_level = scope_level
        self.scope_id = scope_id
        self.line = line
        self.col = col
        self.assigned = False             # has it ever been written to?
        self.reads = 0
        self.writes = 0

    def to_dict(self):
        return {
            "name": self.name, "rt_name": self.rt_name,
            "sym_kind": self.sym_kind,
            "type": self.type_name, "length": self.length,
            "width": self.width, "offset": self.offset,
            "scope_level": self.scope_level, "scope_id": self.scope_id,
            "line": self.line, "col": self.col,
            "reads": self.reads, "writes": self.writes,
        }


class Scope(object):
    """One hash table of the scope stack."""

    def __init__(self, scope_id, level, parent, tag):
        self.id = scope_id
        self.level = level
        self.parent = parent
        self.tag = tag                    # 'global' | 'block@line:col'
        self.names = {}                   # name -> Symbol

    def __contains__(self, name):
        return name in self.names

    def __iter__(self):
        return iter(self.names.values())


class SymbolTable(object):

    def __init__(self):
        self.all_scopes = []
        self.stack = []
        self._next_id = 0
        self._next_offset = 0
        self._rt_names = set()
        self.push("global")

    # -- scope management --------------------------------------------------
    def push(self, tag):
        parent = self.stack[-1] if self.stack else None
        sc = Scope(self._next_id, len(self.stack), parent, tag)
        self._next_id += 1
        self.all_scopes.append(sc)
        self.stack.append(sc)
        return sc

    def pop(self):
        return self.stack.pop()

    @property
    def current(self):
        return self.stack[-1]

    # -- declaration and lookup -------------------------------------------
    def declare(self, name, sym_kind, type_name, length, line, col):
        """Insert into the innermost scope.  Returns (symbol, already)."""
        sc = self.current
        if name in sc.names:
            return sc.names[name], True
        rt_name = name
        if rt_name in self._rt_names:
            rt_name = "%s#%d" % (name, sc.id)
        self._rt_names.add(rt_name)
        sym = Symbol(name, sym_kind, type_name, length, self._next_offset,
                     sc.level, sc.id, line, col, rt_name)
        self._next_offset += sym.width
        sc.names[name] = sym
        return sym, False

    def lookup(self, name):
        """Innermost-first search of the scope stack."""
        for sc in reversed(self.stack):
            if name in sc.names:
                return sc.names[name]
        return None

    @property
    def frame_size(self):
        return self._next_offset

    # -- intermediate file -------------------------------------------------
    def write_symbol_file(self, path, source):
        """Write the .sym intermediate file (see doc section 4.4)."""
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# citu-symbol-table v1\n")
            fh.write("# source: %s\n" % source)
            fh.write("# scopes: %d   symbols: %d   frame size: %d bytes\n"
                     % (len(self.all_scopes),
                        sum(len(s.names) for s in self.all_scopes),
                        self.frame_size))
            fh.write("# fields: NAME | RT_NAME | KIND | TYPE | LEN | WIDTH"
                     " | OFFSET | LINE:COL | READS | WRITES\n")
            for sc in self.all_scopes:
                parent = "-" if sc.parent is None else str(sc.parent.id)
                fh.write("\n[scope %d] level=%d parent=%s tag=%s\n"
                         % (sc.id, sc.level, parent, sc.tag))
                fh.write("-" * 100 + "\n")
                if not sc.names:
                    fh.write("  (empty)\n")
                for sym in sc.names.values():
                    fh.write("  %-10s | %-12s | %-6s | %-6s | %-3d | %-5d"
                             " | %-6d | %4d:%-3d | %-5d | %d\n"
                             % (sym.name, sym.rt_name, sym.sym_kind,
                                sym.type_name, sym.length, sym.width,
                                sym.offset, sym.line, sym.col,
                                sym.reads, sym.writes))
        return path
