"""Token definitions for the Citu language.

A Token is the unit the lexer produces and the parser consumes.  Every token
carries its own source position so that later phases can report errors in
terms of the original program text.
"""

# ---------------------------------------------------------------- keywords --
# Citu keywords are Urdu words.  The lexer first matches the identifier
# pattern and then looks the lexeme up in this table; if it is found the
# token is re-classified as that keyword.  This is the standard technique and
# avoids a 17-way alternation in the master regular expression.
KEYWORDS = {
    # block delimiters
    "shuro":   "SHURO",      # {   begin a block
    "khatam":  "KHATAM",     # }   end a block
    # control flow
    "agar":    "AGAR",       # if
    "wagarna": "WAGARNA",    # else
    "jabtak":  "JABTAK",     # while
    "nikal":   "NIKAL",      # break
    # statements
    "melado":  "MELADO",     # assignment operator (a melado b  ==  a = b)
    "medalo":  "MELADO",     # an accepted second spelling of 'melado'
    "dikhao":  "DIKHAO",     # print
    # word operators
    "aur":     "AUR",        # &&
    "ya":      "YA",         # ||
    "nahi":    "NAHI",       # !
    # type names
    "int16":   "INT16",
    "int32":   "INT32",
    "uint16":  "UINT16",
    "uint32":  "UINT32",
    "real":    "REAL",
    "float":   "FLOAT",     # an accepted second spelling of 'real'
    "char":    "CHAR",
}

TYPE_KEYWORDS = frozenset(
    ["INT16", "INT32", "UINT16", "UINT32", "REAL", "FLOAT", "CHAR"])

# ----------------------------------------------------------- operator sets --
# Longest first: the lexer tries these in order, which implements maximal
# munch (`<=` must be tried before `<`, `!=` before `!`).
SYMBOLS = [
    ("<=", "LE"),
    (">=", "GE"),
    ("!=", "NE"),
    ("<",  "LT"),
    (">",  "GT"),
    ("=",  "EQ"),       # '=' is the EQUALITY test in Citu, not assignment
    ("+",  "PLUS"),
    ("-",  "MINUS"),
    ("*",  "STAR"),
    ("/",  "SLASH"),
    ("%",  "PERCENT"),
    ("(",  "LPAREN"),
    (")",  "RPAREN"),
    ("[",  "LBRACK"),
    ("]",  "RBRACK"),
    (";",  "SEMI"),
    (",",  "COMMA"),
]

OPERATOR_TYPES = frozenset(
    ["LE", "GE", "NE", "LT", "GT", "EQ", "PLUS", "MINUS",
     "STAR", "SLASH", "PERCENT", "AUR", "YA", "NAHI", "MELADO"])

PUNCTUATOR_TYPES = frozenset(
    ["LPAREN", "RPAREN", "LBRACK", "RBRACK", "SEMI", "COMMA"])

LITERAL_CATEGORY = {
    "INTLIT":  "INT_LITERAL",
    "REALLIT": "REAL_LITERAL",
    "CHARLIT": "CHAR_LITERAL",
    "STRLIT":  "STRING_LITERAL",
}


def category_of(token_type):
    """Broad lexical class, used for the human-readable token listing."""
    if token_type in TYPE_KEYWORDS:
        return "TYPE_KEYWORD"
    if token_type in KEYWORDS.values():
        return "KEYWORD"
    if token_type in LITERAL_CATEGORY:
        return LITERAL_CATEGORY[token_type]
    if token_type == "ID":
        return "IDENTIFIER"
    if token_type in OPERATOR_TYPES:
        return "OPERATOR"
    if token_type in PUNCTUATOR_TYPES:
        return "PUNCTUATOR"
    if token_type == "EOF":
        return "EOF"
    return "ERROR"


class Token:
    """(type, lexeme, value, line, col) produced by the lexer.

    type   - grammar terminal name, e.g. 'JABTAK', 'ID', 'INTLIT', 'PLUS'
    lexeme - the exact source text that was matched
    value  - the decoded literal value (int / float / str), else None
    line   - 1-based line number of the first character
    col    - 1-based column number of the first character
    index  - position of the token inside the token list
    """

    __slots__ = ("type", "lexeme", "value", "line", "col", "index")

    def __init__(self, type_, lexeme, value=None, line=0, col=0, index=-1):
        self.type = type_
        self.lexeme = lexeme
        self.value = value
        self.line = line
        self.col = col
        self.index = index

    @property
    def category(self):
        return category_of(self.type)

    def __repr__(self):
        return "Token(%s, %r, line=%d, col=%d)" % (
            self.type, self.lexeme, self.line, self.col)
