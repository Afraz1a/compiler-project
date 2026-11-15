"""Citu syntax analyser (phase 2).

A predictive recursive-descent parser.  There is exactly one method per
nonterminal of the grammar in grammar.py, and each method chooses its
production by looking at a single lookahead token -- the same decision the
LL(1) table would make.  Because the grammar is LL(1) (grammar.py proves
this mechanically) no backtracking is ever needed.

The parser produces two things at once:

  * a CONCRETE parse tree, which mirrors the grammar derivation exactly and
    is written out as the .pt intermediate file;
  * an ABSTRACT syntax tree, which drops punctuation and chain productions
    and is written out as the .ast.json intermediate file.

On a syntax error the parser reports it and recovers in panic mode: it skips
tokens until it reaches one that can begin a statement, or a `;` / `khatam`,
and then carries on, so one mistake does not hide the rest.
"""

from . import ast_nodes as A
from .errors import DiagnosticBag

# Tokens that may begin a statement -- used by panic-mode recovery.
STMT_START = frozenset([
    "INT16", "INT32", "UINT16", "UINT32", "REAL", "FLOAT", "CHAR",
    "ID", "AGAR", "JABTAK", "NIKAL", "DIKHAO",
])

TYPE_TOKENS = {
    "INT16": "int16", "INT32": "int32",
    "UINT16": "uint16", "UINT32": "uint32",
    "REAL": "real", "FLOAT": "real", "CHAR": "char",
}

REL_OPS = {"EQ": "=", "NE": "!=", "LT": "<", "LE": "<=", "GT": ">", "GE": ">="}
ADD_OPS = {"PLUS": "+", "MINUS": "-"}
MUL_OPS = {"STAR": "*", "SLASH": "/", "PERCENT": "%"}

# Readable names used in syntax error messages.
FRIENDLY = {
    "SEMI": "';'", "LPAREN": "'('", "RPAREN": "')'",
    "LBRACK": "'['", "RBRACK": "']'", "COMMA": "','",
    "SHURO": "'shuro'", "KHATAM": "'khatam'", "MELADO": "'melado'",
    "ID": "an identifier", "INTLIT": "an integer literal",
    "EOF": "end of file",
}


def friendly(tok_type):
    return FRIENDLY.get(tok_type, "'%s'" % tok_type.lower())


class ParseNode(object):
    """A node of the concrete parse tree."""

    __slots__ = ("symbol", "token", "kids", "production")

    def __init__(self, symbol, token=None, production=None):
        self.symbol = symbol          # nonterminal name, or terminal type
        self.token = token            # Token for leaves, else None
        self.kids = []
        self.production = production  # production index, for nonterminals

    def add(self, node):
        self.kids.append(node)
        return node

    @property
    def is_leaf(self):
        return self.token is not None

    def render(self, indent=0, out=None):
        if out is None:
            out = []
        pad = "|  " * indent
        if self.is_leaf:
            out.append("%s%s  \"%s\"" % (pad, self.symbol, self.token.lexeme))
        else:
            out.append("%s%s" % (pad, self.symbol))
        for k in self.kids:
            k.render(indent + 1, out)
        return out

    def count(self):
        return 1 + sum(k.count() for k in self.kids)


class _Recovered(Exception):
    """Internal: thrown after a syntax error so the caller can resynchronise."""


class Parser(object):

    def __init__(self, tokens, filename="<source>", diagnostics=None):
        self.toks = tokens
        self.i = 0
        self.filename = filename
        self.diag = diagnostics if diagnostics is not None else DiagnosticBag()
        self.root = ParseNode("<start>")
        self._stack = [self.root]

    # ---------------------------------------------------------- plumbing --
    @property
    def tok(self):
        return self.toks[self.i]

    @property
    def ttype(self):
        return self.toks[self.i].type

    def _advance(self):
        if self.ttype != "EOF":
            self.i += 1

    def _enter(self, symbol):
        node = self._stack[-1].add(ParseNode(symbol))
        self._stack.append(node)
        return node

    def _leave(self):
        self._stack.pop()

    def _leaf(self, token):
        self._stack[-1].add(ParseNode(token.type, token))

    def _match(self, ttype):
        """Consume the lookahead if it is `ttype`, else report and recover."""
        t = self.tok
        if t.type == ttype:
            self._leaf(t)
            self._advance()
            return t
        self._error("expected %s but found '%s'" % (friendly(ttype), t.lexeme))
        raise _Recovered()

    def _error(self, message):
        t = self.tok
        self.diag.error("syntax", t.line, t.col, message,
                        None if t.type == "EOF" else t.lexeme)

    def _sync(self):
        """Panic-mode recovery: skip to a plausible restart point."""
        while self.ttype not in ("EOF", "KHATAM"):
            if self.ttype == "SEMI":
                self._advance()
                return
            if self.ttype in STMT_START:
                return
            self._advance()

    # ------------------------------------------------------------- entry --
    def parse(self):
        self._enter("Program")
        stmts = self._stmt_list(stop={"EOF"})
        if self.ttype != "EOF":
            self._error("unexpected '%s' after end of program"
                        % self.tok.lexeme)
        self._leave()
        prog = A.Program(line=1, col=1, stmts=stmts)
        self.ast = prog
        return prog

    # -------------------------------------------------------- statements --
    def _stmt_list(self, stop):
        """StmtList -> Stmt StmtList | eps"""
        self._enter("StmtList")
        stmts = []
        guard = -1
        while self.ttype not in stop and self.ttype != "EOF":
            if self.i == guard:          # no progress: force one token forward
                self._advance()
                continue
            guard = self.i
            try:
                s = self._stmt()
                if s is not None:
                    stmts.append(s)
            except _Recovered:
                self._sync()
        self._leave()
        return stmts

    def _stmt(self):
        t = self.ttype
        self._enter("Stmt")
        try:
            if t in TYPE_TOKENS:
                node = self._decl()
            elif t == "ID":
                node = self._assign()
            elif t == "AGAR":
                node = self._if()
            elif t == "JABTAK":
                node = self._while()
            elif t == "NIKAL":
                node = self._break()
            elif t == "DIKHAO":
                node = self._print()
            else:
                self._error("expected a statement but found '%s'"
                            % self.tok.lexeme)
                raise _Recovered()
        finally:
            self._leave()
        return node

    def _decl(self):
        """Decl -> Type ID DeclTail"""
        start = self.tok
        self._enter("Decl")
        try:
            self._enter("Type")
            type_name = TYPE_TOKENS[self.ttype]
            self._match(self.ttype)
            self._leave()

            name_tok = self._match("ID")

            self._enter("DeclTail")
            try:
                if self.ttype == "LBRACK":
                    self._match("LBRACK")
                    size_tok = self._match("INTLIT")
                    self._match("RBRACK")
                    self._match("SEMI")
                    return A.ArrayDecl(line=start.line, col=start.col,
                                       type_name=type_name,
                                       name=name_tok.lexeme,
                                       size=size_tok.value)
                if self.ttype == "MELADO":
                    self._match("MELADO")
                    init = self._expr()
                    self._match("SEMI")
                    return A.VarDecl(line=start.line, col=start.col,
                                     type_name=type_name,
                                     name=name_tok.lexeme, init=init)
                self._match("SEMI")
                return A.VarDecl(line=start.line, col=start.col,
                                 type_name=type_name,
                                 name=name_tok.lexeme, init=None)
            finally:
                self._leave()
        finally:
            self._leave()

    def _assign(self):
        """Assign -> ID AsgTail"""
        self._enter("Assign")
        try:
            name_tok = self._match("ID")
            self._enter("AsgTail")
            try:
                if self.ttype == "LBRACK":
                    self._match("LBRACK")
                    index = self._expr()
                    self._match("RBRACK")
                    self._match("MELADO")
                    value = self._expr()
                    self._match("SEMI")
                    return A.IndexAssign(line=name_tok.line, col=name_tok.col,
                                         name=name_tok.lexeme,
                                         index=index, value=value)
                self._match("MELADO")
                value = self._expr()
                self._match("SEMI")
                return A.Assign(line=name_tok.line, col=name_tok.col,
                                name=name_tok.lexeme, value=value)
            finally:
                self._leave()
        finally:
            self._leave()

    def _if(self):
        """If -> agar ( Expr ) Block ElsePart"""
        self._enter("If")
        try:
            kw = self._match("AGAR")
            self._match("LPAREN")
            cond = self._expr()
            self._match("RPAREN")
            then_block = self._block()

            self._enter("ElsePart")
            try:
                else_block = None
                if self.ttype == "WAGARNA":
                    self._match("WAGARNA")
                    else_block = self._block()
            finally:
                self._leave()

            return A.If(line=kw.line, col=kw.col, cond=cond,
                        then_block=then_block, else_block=else_block)
        finally:
            self._leave()

    def _while(self):
        """While -> jabtak ( Expr ) Block"""
        self._enter("While")
        try:
            kw = self._match("JABTAK")
            self._match("LPAREN")
            cond = self._expr()
            self._match("RPAREN")
            body = self._block()
            return A.While(line=kw.line, col=kw.col, cond=cond, body=body)
        finally:
            self._leave()

    def _break(self):
        """Break -> nikal ;"""
        self._enter("Break")
        try:
            kw = self._match("NIKAL")
            self._match("SEMI")
            return A.Break(line=kw.line, col=kw.col)
        finally:
            self._leave()

    def _print(self):
        """Print -> dikhao ( ArgList ) ;"""
        self._enter("Print")
        try:
            kw = self._match("DIKHAO")
            self._match("LPAREN")
            args = self._arg_list()
            self._match("RPAREN")
            self._match("SEMI")
            return A.Print(line=kw.line, col=kw.col, args=args)
        finally:
            self._leave()

    def _arg_list(self):
        """ArgList -> Arg ArgTail ;  ArgTail -> , Arg ArgTail | eps"""
        self._enter("ArgList")
        try:
            args = [self._arg()]
            self._enter("ArgTail")
            try:
                while self.ttype == "COMMA":
                    self._match("COMMA")
                    args.append(self._arg())
            finally:
                self._leave()
            return args
        finally:
            self._leave()

    def _arg(self):
        self._enter("Arg")
        try:
            if self.ttype == "STRLIT":
                t = self._match("STRLIT")
                return A.StrLit(line=t.line, col=t.col, value=t.value)
            return self._expr()
        finally:
            self._leave()

    def _block(self):
        """Block -> shuro StmtList khatam"""
        self._enter("Block")
        try:
            kw = self._match("SHURO")
            stmts = self._stmt_list(stop={"KHATAM"})
            self._match("KHATAM")
            return A.Block(line=kw.line, col=kw.col, stmts=stmts)
        finally:
            self._leave()

    # ------------------------------------------------------- expressions --
    # Each level is a nonterminal of the grammar.  The *Tail productions are
    # written as loops, which is the standard way to implement the
    # right-recursive form of a left-associative operator without building a
    # right-leaning tree.
    def _expr(self):
        self._enter("Expr")
        try:
            return self._or_expr()
        finally:
            self._leave()

    def _or_expr(self):
        self._enter("OrExpr")
        try:
            node = self._and_expr()
            self._enter("OrTail")
            try:
                while self.ttype == "YA":
                    op = self._match("YA")
                    rhs = self._and_expr()
                    node = A.Binary(line=op.line, col=op.col, op="ya",
                                    left=node, right=rhs)
            finally:
                self._leave()
            return node
        finally:
            self._leave()

    def _and_expr(self):
        self._enter("AndExpr")
        try:
            node = self._rel_expr()
            self._enter("AndTail")
            try:
                while self.ttype == "AUR":
                    op = self._match("AUR")
                    rhs = self._rel_expr()
                    node = A.Binary(line=op.line, col=op.col, op="aur",
                                    left=node, right=rhs)
            finally:
                self._leave()
            return node
        finally:
            self._leave()

    def _rel_expr(self):
        """RelExpr -> AddExpr RelTail  (relational operators do not chain)"""
        self._enter("RelExpr")
        try:
            node = self._add_expr()
            self._enter("RelTail")
            try:
                if self.ttype in REL_OPS:
                    self._enter("RelOp")
                    op = self._match(self.ttype)
                    self._leave()
                    rhs = self._add_expr()
                    node = A.Binary(line=op.line, col=op.col,
                                    op=REL_OPS[op.type],
                                    left=node, right=rhs)
            finally:
                self._leave()
            return node
        finally:
            self._leave()

    def _add_expr(self):
        self._enter("AddExpr")
        try:
            node = self._mul_expr()
            self._enter("AddTail")
            try:
                while self.ttype in ADD_OPS:
                    op = self._match(self.ttype)
                    rhs = self._mul_expr()
                    node = A.Binary(line=op.line, col=op.col,
                                    op=ADD_OPS[op.type],
                                    left=node, right=rhs)
            finally:
                self._leave()
            return node
        finally:
            self._leave()

    def _mul_expr(self):
        self._enter("MulExpr")
        try:
            node = self._unary()
            self._enter("MulTail")
            try:
                while self.ttype in MUL_OPS:
                    op = self._match(self.ttype)
                    rhs = self._unary()
                    node = A.Binary(line=op.line, col=op.col,
                                    op=MUL_OPS[op.type],
                                    left=node, right=rhs)
            finally:
                self._leave()
            return node
        finally:
            self._leave()

    def _unary(self):
        self._enter("Unary")
        try:
            if self.ttype == "MINUS":
                op = self._match("MINUS")
                return A.Unary(line=op.line, col=op.col, op="-",
                               operand=self._unary())
            if self.ttype == "NAHI":
                op = self._match("NAHI")
                return A.Unary(line=op.line, col=op.col, op="nahi",
                               operand=self._unary())
            return self._primary()
        finally:
            self._leave()

    def _primary(self):
        self._enter("Primary")
        try:
            t = self.tok
            if t.type == "ID":
                self._match("ID")
                self._enter("PrimTail")
                try:
                    if self.ttype == "LBRACK":
                        self._match("LBRACK")
                        idx = self._expr()
                        self._match("RBRACK")
                        return A.Index(line=t.line, col=t.col,
                                       name=t.lexeme, index=idx)
                finally:
                    self._leave()
                return A.Var(line=t.line, col=t.col, name=t.lexeme)
            if t.type == "INTLIT":
                self._match("INTLIT")
                return A.IntLit(line=t.line, col=t.col, value=t.value)
            if t.type == "REALLIT":
                self._match("REALLIT")
                return A.RealLit(line=t.line, col=t.col, value=t.value)
            if t.type == "CHARLIT":
                self._match("CHARLIT")
                return A.CharLit(line=t.line, col=t.col, value=t.value)
            if t.type == "LPAREN":
                self._match("LPAREN")
                inner = self._expr()
                self._match("RPAREN")
                return inner
            self._error("expected an expression but found '%s'" % t.lexeme)
            raise _Recovered()
        finally:
            self._leave()

    # ------------------------------------------------ intermediate files --
    def write_parse_tree(self, path):
        """Write the .pt intermediate file (see doc section 4.2)."""
        body = []
        for kid in self.root.kids:
            kid.render(0, body)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# citu-parse-tree v1\n")
            fh.write("# source: %s\n" % self.filename)
            fh.write("# nodes: %d\n"
                     % sum(k.count() for k in self.root.kids))
            fh.write("# notation: one node per line, depth shown by '|  ';"
                     " leaves carry their lexeme\n")
            fh.write("#" + "-" * 70 + "\n")
            fh.write("\n".join(body) + "\n")
        return path


def parse(tokens, filename="<source>", diagnostics=None):
    p = Parser(tokens, filename, diagnostics)
    p.parse()
    return p
