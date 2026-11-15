"""The formal Citu grammar, plus FIRST / FOLLOW and LL(1) table construction.

The grammar below is the single source of truth for the language syntax.  The
recursive-descent parser in parser.py implements exactly these productions,
one method per nonterminal, and this module mechanically proves the grammar
is LL(1) by building the predictive parsing table and checking that no cell
receives two productions.

Notation
    - A production is (lhs, [rhs symbols]).  An empty rhs list is epsilon.
    - Terminals are the token-type names produced by lexer.py (upper case).
    - Nonterminals are CamelCase names.
"""

EPSILON = "eps"
END = "$"

# --------------------------------------------------------------------------
# The grammar.  Numbered in this order in the documentation.
# --------------------------------------------------------------------------
PRODUCTIONS = [
    # program and statement list
    ("Program",  ["StmtList"]),
    ("StmtList", ["Stmt", "StmtList"]),
    ("StmtList", []),

    # statements
    ("Stmt", ["Decl"]),
    ("Stmt", ["Assign"]),
    ("Stmt", ["If"]),
    ("Stmt", ["While"]),
    ("Stmt", ["Break"]),
    ("Stmt", ["Print"]),

    # declarations
    ("Decl",     ["Type", "ID", "DeclTail"]),
    ("DeclTail", ["LBRACK", "INTLIT", "RBRACK", "SEMI"]),
    ("DeclTail", ["MELADO", "Expr", "SEMI"]),
    ("DeclTail", ["SEMI"]),
    ("Type", ["INT16"]),
    ("Type", ["INT32"]),
    ("Type", ["UINT16"]),
    ("Type", ["UINT32"]),
    ("Type", ["REAL"]),
    ("Type", ["FLOAT"]),
    ("Type", ["CHAR"]),

    # assignment
    ("Assign",  ["ID", "AsgTail"]),
    ("AsgTail", ["LBRACK", "Expr", "RBRACK", "MELADO", "Expr", "SEMI"]),
    ("AsgTail", ["MELADO", "Expr", "SEMI"]),

    # control flow
    ("If",       ["AGAR", "LPAREN", "Expr", "RPAREN", "Block", "ElsePart"]),
    ("ElsePart", ["WAGARNA", "Block"]),
    ("ElsePart", []),
    ("While",    ["JABTAK", "LPAREN", "Expr", "RPAREN", "Block"]),
    ("Break",    ["NIKAL", "SEMI"]),

    # output
    ("Print",   ["DIKHAO", "LPAREN", "ArgList", "RPAREN", "SEMI"]),
    ("ArgList", ["Arg", "ArgTail"]),
    ("ArgTail", ["COMMA", "Arg", "ArgTail"]),
    ("ArgTail", []),
    ("Arg",     ["STRLIT"]),
    ("Arg",     ["Expr"]),

    # blocks
    ("Block", ["SHURO", "StmtList", "KHATAM"]),

    # expressions, lowest precedence first
    ("Expr",    ["OrExpr"]),
    ("OrExpr",  ["AndExpr", "OrTail"]),
    ("OrTail",  ["YA", "AndExpr", "OrTail"]),
    ("OrTail",  []),
    ("AndExpr", ["RelExpr", "AndTail"]),
    ("AndTail", ["AUR", "RelExpr", "AndTail"]),
    ("AndTail", []),
    ("RelExpr", ["AddExpr", "RelTail"]),
    ("RelTail", ["RelOp", "AddExpr"]),
    ("RelTail", []),
    ("RelOp", ["EQ"]),
    ("RelOp", ["NE"]),
    ("RelOp", ["LT"]),
    ("RelOp", ["LE"]),
    ("RelOp", ["GT"]),
    ("RelOp", ["GE"]),
    ("AddExpr", ["MulExpr", "AddTail"]),
    ("AddTail", ["PLUS", "MulExpr", "AddTail"]),
    ("AddTail", ["MINUS", "MulExpr", "AddTail"]),
    ("AddTail", []),
    ("MulExpr", ["Unary", "MulTail"]),
    ("MulTail", ["STAR", "Unary", "MulTail"]),
    ("MulTail", ["SLASH", "Unary", "MulTail"]),
    ("MulTail", ["PERCENT", "Unary", "MulTail"]),
    ("MulTail", []),
    ("Unary",   ["MINUS", "Unary"]),
    ("Unary",   ["NAHI", "Unary"]),
    ("Unary",   ["Primary"]),
    ("Primary", ["ID", "PrimTail"]),
    ("Primary", ["INTLIT"]),
    ("Primary", ["REALLIT"]),
    ("Primary", ["CHARLIT"]),
    ("Primary", ["LPAREN", "Expr", "RPAREN"]),
    ("PrimTail", ["LBRACK", "Expr", "RBRACK"]),
    ("PrimTail", []),
]

START = "Program"

_seen = []
for _lhs, _rhs in PRODUCTIONS:
    if _lhs not in _seen:
        _seen.append(_lhs)
NONTERMINALS = tuple(_seen)

TERMINALS = tuple(
    sorted({s for _, rhs in PRODUCTIONS for s in rhs if s not in NONTERMINALS}
           | {"EOF"}))


def is_nonterminal(sym):
    return sym in NONTERMINALS


# --------------------------------------------------------------------------
# FIRST / FOLLOW
# --------------------------------------------------------------------------
def compute_first():
    first = {nt: set() for nt in NONTERMINALS}
    for t in TERMINALS:
        first[t] = {t}

    changed = True
    while changed:
        changed = False
        for lhs, rhs in PRODUCTIONS:
            before = len(first[lhs])
            if not rhs:
                first[lhs].add(EPSILON)
            else:
                for sym in rhs:
                    first[lhs] |= (first[sym] - {EPSILON})
                    if EPSILON not in first[sym]:
                        break
                else:
                    first[lhs].add(EPSILON)
            if len(first[lhs]) != before:
                changed = True
    return first


def first_of_sequence(seq, first):
    """FIRST of a string of grammar symbols."""
    out = set()
    for sym in seq:
        out |= (first[sym] - {EPSILON})
        if EPSILON not in first[sym]:
            return out
    out.add(EPSILON)
    return out


def compute_follow(first):
    follow = {nt: set() for nt in NONTERMINALS}
    follow[START].add(END)

    changed = True
    while changed:
        changed = False
        for lhs, rhs in PRODUCTIONS:
            for i, sym in enumerate(rhs):
                if not is_nonterminal(sym):
                    continue
                before = len(follow[sym])
                rest = first_of_sequence(rhs[i + 1:], first)
                follow[sym] |= (rest - {EPSILON})
                if EPSILON in rest:
                    follow[sym] |= follow[lhs]
                if len(follow[sym]) != before:
                    changed = True
    return follow


def build_table(first=None, follow=None):
    """Return (table, conflicts).

    table[(nonterminal, terminal)] = production index
    conflicts is a list of (nonterminal, terminal, [production indices])
    """
    first = first or compute_first()
    follow = follow or compute_follow(first)

    table = {}
    collisions = {}
    for idx, (lhs, rhs) in enumerate(PRODUCTIONS):
        predict = first_of_sequence(rhs, first)
        terminals = predict - {EPSILON}
        if EPSILON in predict:
            terminals = terminals | follow[lhs]
        for t in terminals:
            key = (lhs, t)
            if key in table and table[key] != idx:
                collisions.setdefault(key, [table[key]]).append(idx)
            else:
                table.setdefault(key, idx)

    conflicts = [(lhs, t, prods) for (lhs, t), prods in collisions.items()]
    return table, conflicts


def predict_set(idx, first=None, follow=None):
    first = first or compute_first()
    follow = follow or compute_follow(first)
    lhs, rhs = PRODUCTIONS[idx]
    p = first_of_sequence(rhs, first)
    out = p - {EPSILON}
    if EPSILON in p:
        out = out | follow[lhs]
    return out


def production_str(idx):
    lhs, rhs = PRODUCTIONS[idx]
    return "%s -> %s" % (lhs, " ".join(rhs) if rhs else EPSILON)


# --------------------------------------------------------------------------
# Report (generates the grammar appendix used in the documentation)
# --------------------------------------------------------------------------
def write_report(path):
    first = compute_first()
    follow = compute_follow(first)
    table, conflicts = build_table(first, follow)

    def fmt(s):
        return " ".join(sorted(s)) if s else "(empty)"

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# citu-grammar-report v1\n\n")

        fh.write("## Terminals (%d)\n\n" % len(TERMINALS))
        fh.write(fmt(set(TERMINALS)) + "\n\n")

        fh.write("## Nonterminals (%d)\n\n" % len(NONTERMINALS))
        fh.write(" ".join(NONTERMINALS) + "\n\n")

        fh.write("## Productions (%d)\n\n" % len(PRODUCTIONS))
        for i in range(len(PRODUCTIONS)):
            fh.write("%3d.  %s\n" % (i + 1, production_str(i)))
        fh.write("\n")

        fh.write("## FIRST and FOLLOW\n\n")
        fh.write("%-10s | %-50s | %s\n" % ("NT", "FIRST", "FOLLOW"))
        fh.write("-" * 118 + "\n")
        for nt in NONTERMINALS:
            fh.write("%-10s | %-50s | %s\n"
                     % (nt, fmt(first[nt]), fmt(follow[nt])))
        fh.write("\n")

        fh.write("## PREDICT sets (one row of the LL(1) table each)\n\n")
        for i in range(len(PRODUCTIONS)):
            fh.write("%3d.  %-46s  PREDICT = { %s }\n"
                     % (i + 1, production_str(i),
                        fmt(predict_set(i, first, follow))))
        fh.write("\n")

        fh.write("## LL(1) check\n\n")
        if conflicts:
            fh.write("CONFLICTS FOUND: %d\n" % len(conflicts))
            for lhs, t, prods in conflicts:
                fh.write("  M[%s, %s] = productions %s\n"
                         % (lhs, t, ", ".join(str(p + 1) for p in prods)))
        else:
            fh.write("No cell of the parsing table received two productions.\n")
            fh.write("The grammar is LL(1).  Filled cells: %d\n" % len(table))
    return path, conflicts
