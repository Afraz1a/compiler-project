import re

keywords = {
    "shuro": "SHURO", "khatam": "KHATAM",
    "agar": "AGAR", "wagarna": "WAGARNA",
    "jabtak": "JABTAK", "nikal": "NIKAL",
    "melado": "MELADO", "dikhao": "DIKHAO",
    "aur": "AUR", "ya": "YA", "nahi": "NAHI",
    "int16": "INT16", "int32": "INT32",
    "uint16": "UINT16", "uint32": "UINT32",
    "real": "REAL", "float": "FLOAT", "char": "CHAR",
}

type_tokens = ["INT16", "INT32", "UINT16", "UINT32", "REAL", "FLOAT", "CHAR"]

symbols = {
    "<=": "LE", ">=": "GE", "!=": "NE",
    "<": "LT", ">": "GT", "=": "EQ",
    "+": "PLUS", "-": "MINUS", "*": "STAR",
    "/": "SLASH", "%": "PERCENT",
    "(": "LPAREN", ")": "RPAREN",
    "[": "LBRACK", "]": "RBRACK",
    ";": "SEMI", ",": "COMMA",
}

operators = ["LE", "GE", "NE", "LT", "GT", "EQ", "PLUS", "MINUS", "STAR",
             "SLASH", "PERCENT", "AUR", "YA", "NAHI", "MELADO"]

patterns = [
    ("newline", r"\n"),
    ("space", r"[ \t\r]+"),
    ("comment", r"//[^\n]*|/\*[\s\S]*?\*/"),
    ("real", r"\d+\.\d*|\.\d+"),
    ("number", r"\d+"),
    ("character", r"'(?:\\.|[^'\\\n])'"),
    ("string", r"\"(?:\\.|[^\"\\\n])*\""),
    ("identifier", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("symbol", r"<=|>=|!=|[-+*/%<>=()\[\];,]"),
    ("unknown", r"."),
]

big = "|".join("(?P<" + name + ">" + pattern + ")" for name, pattern in patterns)


class Token:
    def __init__(self, kind, text, value, line, col):
        self.kind = kind
        self.text = text
        self.value = value
        self.line = line
        self.col = col


def category(kind):
    if kind in type_tokens:
        return "TYPE"
    if kind in keywords.values():
        return "KEYWORD"
    if kind == "IDENTIFIER":
        return "IDENTIFIER"
    if kind == "NUMBER":
        return "NUMBER"
    if kind == "REALNUM":
        return "REAL_NUMBER"
    if kind == "CHARACTER":
        return "CHARACTER"
    if kind == "STRING":
        return "STRING"
    if kind in operators:
        return "OPERATOR"
    if kind == "EOF":
        return "EOF"
    return "PUNCTUATOR"


def unescape(text):
    out = ""
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            c = text[i + 1]
            if c == "n":
                out = out + "\n"
            elif c == "t":
                out = out + "\t"
            else:
                out = out + c
            i = i + 2
        else:
            out = out + text[i]
            i = i + 1
    return out


def scan(code, errors):
    tokens = []
    line = 1
    line_start = 0

    for m in re.finditer(big, code):
        kind = m.lastgroup
        word = m.group()
        col = m.start() - line_start + 1

        if kind == "newline":
            line = line + 1
            line_start = m.end()
            continue

        if kind == "space":
            continue

        if kind == "comment":
            if "\n" in word:
                line = line + word.count("\n")
                line_start = m.start() + word.rfind("\n") + 1
            continue

        if kind == "real":
            tokens.append(Token("REALNUM", word, float(word), line, col))
        elif kind == "number":
            tokens.append(Token("NUMBER", word, int(word), line, col))
        elif kind == "character":
            body = unescape(word[1:-1])
            if len(body) != 1:
                errors.append((line, col, "lexical",
                               "bad character constant " + word))
            else:
                tokens.append(Token("CHARACTER", word, body, line, col))
        elif kind == "string":
            tokens.append(Token("STRING", word, unescape(word[1:-1]),
                                line, col))
        elif kind == "identifier":
            tokens.append(Token(keywords.get(word, "IDENTIFIER"), word, None,
                                line, col))
        elif kind == "symbol":
            tokens.append(Token(symbols[word], word, None, line, col))
        else:
            errors.append((line, col, "lexical",
                           "illegal character " + word))

    tokens.append(Token("EOF", "end of file", None, line,
                        len(code) - line_start + 1))
    return tokens


def write_tokens(tokens, path):
    out = open(path, "w")
    out.write("LINE , COL , TOKEN TYPE , LEXEME\n")
    out.write("-----------------------------------\n")
    for t in tokens:
        out.write(str(t.line) + " , " + str(t.col) + " , " +
                  category(t.kind) + " , " + t.text + "\n")
    out.write("-----------------------------------\n")
    out.write("total tokens = " + str(len(tokens)) + "\n")
    out.close()
