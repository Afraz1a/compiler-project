"""Citu lexical analyser (phase 1).

Reads Citu source text and produces a list of Token objects plus a list of
lexical diagnostics.  The scanner is regular-expression based: one named
pattern per token category, all joined into a single master regular
expression that is matched at the current input position.  Python's
alternation returns the FIRST alternative that matches, so the categories are
listed longest / most specific first, which gives the maximal-munch rule
(`<=` is matched before `<`, a real literal before an integer, and so on).

On an illegal character the scanner records an error and advances one
character (panic-mode recovery), so a single bad character never aborts the
whole scan.
"""

import re

from .tokens import KEYWORDS, SYMBOLS, Token
from .errors import DiagnosticBag

# Symbols sorted longest-first so that '<=' wins over '<'.
_SYMBOLS_SORTED = sorted(SYMBOLS, key=lambda p: -len(p[0]))
_SYMBOL_ALT = "|".join(re.escape(s) for s, _ in _SYMBOLS_SORTED)
_SYMBOL_LOOKUP = dict(_SYMBOLS_SORTED)

# The order of this list is the order of the alternatives in the master
# regular expression, and it matters.  See doc section 2.2 for the full
# table and the justification of every ordering constraint.
_SPEC = [
    ("NEWLINE",      r"\r\n|\r|\n"),
    ("WS",           r"[ \t\f\v]+"),
    ("COMMENT_ML",   r"/\*[\s\S]*?\*/"),
    ("COMMENT_BAD",  r"/\*[\s\S]*"),
    ("COMMENT_SL",   r"//[^\r\n]*"),
    ("REALLIT",      r"(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+"),
    ("INTLIT",       r"0[xX][0-9a-fA-F]+|\d+"),
    ("CHARLIT",      r"'(?:\\[nrt0\\'\"]|[^'\\\r\n])'"),
    ("CHARLIT_BAD",  r"'(?:\\.|[^'\\\r\n])*'?"),
    ("STRLIT",       r"\"(?:\\[nrt0\\'\"]|[^\"\\\r\n])*\""),
    ("STRLIT_BAD",   r"\"(?:\\.|[^\"\\\r\n])*"),
    ("ID",           r"[A-Za-z_][A-Za-z0-9_]*"),
    ("SYM",          _SYMBOL_ALT),
    ("BAD",          r"."),
]

_MASTER = re.compile(
    "|".join("(?P<%s>%s)" % (name, pat) for name, pat in _SPEC))

_ESCAPES = {"n": "\n", "r": "\r", "t": "\t", "0": "\0",
            "\\": "\\", "'": "'", "\"": "\""}


def _unescape(body):
    """Decode the escape sequences inside a char or string literal body."""
    out = []
    i = 0
    while i < len(body):
        c = body[i]
        if c == "\\" and i + 1 < len(body):
            out.append(_ESCAPES.get(body[i + 1], body[i + 1]))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


class Lexer(object):
    """Turns Citu source text into a token list."""

    def __init__(self, text, filename="<source>", diagnostics=None):
        self.text = text
        self.filename = filename
        self.diag = diagnostics if diagnostics is not None else DiagnosticBag()
        self.tokens = []

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _pos(offset, line_start, line_no):
        return line_no, offset - line_start + 1

    def _emit(self, type_, lexeme, value, line, col):
        tok = Token(type_, lexeme, value, line, col, len(self.tokens))
        self.tokens.append(tok)
        return tok

    # -- main loop --------------------------------------------------------
    def tokenize(self):
        text = self.text
        pos = 0
        line_no = 1
        line_start = 0
        n = len(text)

        while pos < n:
            m = _MASTER.match(text, pos)
            if m is None:                 # cannot happen: BAD matches any char
                pos += 1
                continue

            kind = m.lastgroup
            lexeme = m.group()
            line, col = self._pos(pos, line_start, line_no)

            if kind == "NEWLINE":
                line_no += 1
                line_start = m.end()
                pos = m.end()
                continue

            if kind in ("WS", "COMMENT_SL"):
                pos = m.end()
                continue

            if kind == "COMMENT_ML":
                nl = lexeme.count("\n")
                if nl:
                    line_no += nl
                    line_start = pos + lexeme.rfind("\n") + 1
                pos = m.end()
                continue

            if kind == "COMMENT_BAD":
                self.diag.error("lexical", line, col,
                                "unterminated block comment", "/*")
                pos = n
                continue

            if kind == "REALLIT":
                self._emit("REALLIT", lexeme, float(lexeme), line, col)

            elif kind == "INTLIT":
                base = 16 if lexeme[:2].lower() == "0x" else 10
                self._emit("INTLIT", lexeme, int(lexeme, base), line, col)

            elif kind == "CHARLIT":
                self._emit("CHARLIT", lexeme, _unescape(lexeme[1:-1]),
                           line, col)

            elif kind == "CHARLIT_BAD":
                self.diag.error("lexical", line, col,
                                "malformed character literal", lexeme)

            elif kind == "STRLIT":
                self._emit("STRLIT", lexeme, _unescape(lexeme[1:-1]),
                           line, col)

            elif kind == "STRLIT_BAD":
                self.diag.error("lexical", line, col,
                                "unterminated string literal", lexeme)

            elif kind == "ID":
                # Keywords are matched by the identifier rule and then
                # re-classified by a table lookup.
                self._emit(KEYWORDS.get(lexeme, "ID"), lexeme, None, line, col)

            elif kind == "SYM":
                self._emit(_SYMBOL_LOOKUP[lexeme], lexeme, None, line, col)

            else:   # BAD -- panic-mode recovery, advance one character
                self.diag.error("lexical", line, col,
                                "illegal character", lexeme)

            pos = m.end()

        line, col = self._pos(pos, line_start, line_no)
        self._emit("EOF", "<eof>", None, line, col)
        return self.tokens

    # -- intermediate file -------------------------------------------------
    def write_token_file(self, path):
        """Write the .tok intermediate file (see doc section 4.1)."""
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# citu-tokens v1\n")
            fh.write("# source: %s\n" % self.filename)
            fh.write("# fields: INDEX | LINE | COL | TOKEN_TYPE | CATEGORY"
                     " | LEXEME | VALUE\n")
            fh.write("#" + "-" * 78 + "\n")
            for t in self.tokens:
                value = "-" if t.value is None else repr(t.value)
                fh.write("%-5d | %-4d | %-3d | %-10s | %-14s | %-12s | %s\n"
                         % (t.index, t.line, t.col, t.type, t.category,
                            t.lexeme, value))
            fh.write("#" + "-" * 78 + "\n")
            fh.write("# total tokens: %d (including EOF)\n" % len(self.tokens))
            fh.write("# lexical errors: %d\n" % len(self.diag.errors))
        return path


def tokenize(text, filename="<source>", diagnostics=None):
    lx = Lexer(text, filename, diagnostics)
    lx.tokenize()
    return lx
