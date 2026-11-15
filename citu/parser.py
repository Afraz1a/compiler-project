from citu.lexer import type_tokens

type_names = {
    "INT16": "int16", "INT32": "int32",
    "UINT16": "uint16", "UINT32": "uint32",
    "REAL": "real", "FLOAT": "real", "CHAR": "char",
}

relops = {"EQ": "=", "NE": "!=", "LT": "<", "LE": "<=", "GT": ">", "GE": ">="}
addops = {"PLUS": "+", "MINUS": "-"}
mulops = {"STAR": "*", "SLASH": "/", "PERCENT": "%"}

starters = type_tokens + ["IDENTIFIER", "AGAR", "JABTAK", "NIKAL", "DIKHAO"]


class Node:
    def __init__(self, kind, line, **parts):
        self.kind = kind
        self.line = line
        self.type = None
        self.symbol = None
        self.parts = list(parts.keys())
        for name in parts:
            setattr(self, name, parts[name])


class Bad(Exception):
    pass


class Parser:
    def __init__(self, tokens, errors):
        self.tokens = tokens
        self.errors = errors
        self.pos = 0

    def look(self):
        return self.tokens[self.pos]

    def kind(self):
        return self.tokens[self.pos].kind

    def step(self):
        if self.kind() != "EOF":
            self.pos = self.pos + 1

    def take(self, kind):
        t = self.look()
        if t.kind != kind:
            self.fail("expected " + kind + " but found " + t.text)
        self.step()
        return t

    def fail(self, message):
        t = self.look()
        self.errors.append((t.line, t.col, "syntax", message))
        raise Bad()

    def recover(self):
        while self.kind() != "EOF" and self.kind() != "KHATAM":
            if self.kind() == "SEMI":
                self.step()
                return
            if self.kind() in starters:
                return
            self.step()

    def program(self):
        return Node("Program", 1, body=self.statements(["EOF"]))

    def statements(self, stop):
        body = []
        while self.kind() not in stop and self.kind() != "EOF":
            here = self.pos
            try:
                body.append(self.statement())
            except Bad:
                self.recover()
            if self.pos == here:
                self.step()
        return body

    def statement(self):
        k = self.kind()
        if k in type_tokens:
            return self.declaration()
        if k == "IDENTIFIER":
            return self.assignment()
        if k == "AGAR":
            return self.if_statement()
        if k == "JABTAK":
            return self.while_statement()
        if k == "NIKAL":
            return self.break_statement()
        if k == "DIKHAO":
            return self.print_statement()
        self.fail("expected a statement but found " + self.look().text)

    def declaration(self):
        t = self.look()
        kind = type_names[t.kind]
        self.step()
        name = self.take("IDENTIFIER")
        if self.kind() == "LBRACK":
            self.step()
            size = self.take("NUMBER")
            self.take("RBRACK")
            self.take("SEMI")
            return Node("Array", t.line, datatype=kind, name=name.text,
                        size=size.value)
        if self.kind() == "MELADO":
            self.step()
            value = self.expression()
            self.take("SEMI")
            return Node("Declare", t.line, datatype=kind, name=name.text,
                        value=value)
        self.take("SEMI")
        return Node("Declare", t.line, datatype=kind, name=name.text,
                    value=None)

    def assignment(self):
        name = self.take("IDENTIFIER")
        if self.kind() == "LBRACK":
            self.step()
            index = self.expression()
            self.take("RBRACK")
            self.take("MELADO")
            value = self.expression()
            self.take("SEMI")
            return Node("SetItem", name.line, name=name.text, index=index,
                        value=value)
        self.take("MELADO")
        value = self.expression()
        self.take("SEMI")
        return Node("Set", name.line, name=name.text, value=value)

    def if_statement(self):
        t = self.take("AGAR")
        self.take("LPAREN")
        test = self.expression()
        self.take("RPAREN")
        yes = self.block()
        no = None
        if self.kind() == "WAGARNA":
            self.step()
            no = self.block()
        return Node("If", t.line, test=test, yes=yes, no=no)

    def while_statement(self):
        t = self.take("JABTAK")
        self.take("LPAREN")
        test = self.expression()
        self.take("RPAREN")
        return Node("While", t.line, test=test, body=self.block())

    def break_statement(self):
        t = self.take("NIKAL")
        self.take("SEMI")
        return Node("Break", t.line)

    def print_statement(self):
        t = self.take("DIKHAO")
        self.take("LPAREN")
        items = [self.argument()]
        while self.kind() == "COMMA":
            self.step()
            items.append(self.argument())
        self.take("RPAREN")
        self.take("SEMI")
        return Node("Print", t.line, items=items)

    def argument(self):
        if self.kind() == "STRING":
            t = self.take("STRING")
            return Node("Text", t.line, value=t.value)
        return self.expression()

    def block(self):
        t = self.take("SHURO")
        body = self.statements(["KHATAM"])
        self.take("KHATAM")
        return Node("Block", t.line, body=body)

    def expression(self):
        left = self.and_part()
        while self.kind() == "YA":
            t = self.look()
            self.step()
            left = Node("Binary", t.line, op="ya", left=left,
                        right=self.and_part())
        return left

    def and_part(self):
        left = self.compare()
        while self.kind() == "AUR":
            t = self.look()
            self.step()
            left = Node("Binary", t.line, op="aur", left=left,
                        right=self.compare())
        return left

    def compare(self):
        left = self.sum_part()
        if self.kind() in relops:
            t = self.look()
            op = relops[t.kind]
            self.step()
            return Node("Binary", t.line, op=op, left=left,
                        right=self.sum_part())
        return left

    def sum_part(self):
        left = self.term()
        while self.kind() in addops:
            t = self.look()
            op = addops[t.kind]
            self.step()
            left = Node("Binary", t.line, op=op, left=left, right=self.term())
        return left

    def term(self):
        left = self.unary()
        while self.kind() in mulops:
            t = self.look()
            op = mulops[t.kind]
            self.step()
            left = Node("Binary", t.line, op=op, left=left, right=self.unary())
        return left

    def unary(self):
        t = self.look()
        if t.kind == "MINUS":
            self.step()
            return Node("Negate", t.line, value=self.unary())
        if t.kind == "NAHI":
            self.step()
            return Node("Not", t.line, value=self.unary())
        return self.primary()

    def primary(self):
        t = self.look()
        if t.kind == "IDENTIFIER":
            self.step()
            if self.kind() == "LBRACK":
                self.step()
                index = self.expression()
                self.take("RBRACK")
                return Node("Item", t.line, name=t.text, index=index)
            return Node("Name", t.line, name=t.text)
        if t.kind == "NUMBER":
            self.step()
            return Node("Number", t.line, value=t.value)
        if t.kind == "REALNUM":
            self.step()
            return Node("RealNumber", t.line, value=t.value)
        if t.kind == "CHARACTER":
            self.step()
            return Node("Character", t.line, value=t.value)
        if t.kind == "LPAREN":
            self.step()
            inside = self.expression()
            self.take("RPAREN")
            return inside
        self.fail("expected an expression but found " + t.text)


def parse(tokens, errors):
    return Parser(tokens, errors).program()


def show(node, depth, lines):
    label = node.kind
    for name in node.parts:
        value = getattr(node, name)
        if not isinstance(value, Node) and not isinstance(value, list):
            if value is not None:
                label = label + " " + str(value)
    if node.type is not None:
        label = label + " : " + node.type
    lines.append("    " * depth + label)
    for name in node.parts:
        value = getattr(node, name)
        if isinstance(value, Node):
            show(value, depth + 1, lines)
        elif isinstance(value, list):
            for item in value:
                show(item, depth + 1, lines)
    return lines


def write_tree(tree, path):
    lines = show(tree, 0, [])
    out = open(path, "w")
    out.write("PARSE TREE\n")
    out.write("-----------------------------------\n")
    for line in lines:
        out.write(line + "\n")
    out.write("-----------------------------------\n")
    out.write("total nodes = " + str(len(lines)) + "\n")
    out.close()
