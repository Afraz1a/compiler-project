names = {"+": "add", "-": "sub", "*": "mul", "/": "div", "%": "mod",
         "=": "eq", "!=": "ne", "<": "lt", "<=": "le", ">": "gt",
         ">=": "ge"}


class Generator:
    def __init__(self, table):
        self.table = table
        self.code = []
        self.temps = 0
        self.labels = 0
        self.exits = []

    def emit(self, op, a="-", b="-", result="-"):
        self.code.append([op, str(a), str(b), str(result)])

    def temp(self):
        self.temps = self.temps + 1
        return "t" + str(self.temps - 1)

    def label(self):
        self.labels = self.labels + 1
        return "L" + str(self.labels - 1)

    def run(self, tree):
        for s in self.table:
            self.emit("alloc", s.datatype, s.length, s.slot)
        for item in tree.body:
            self.statement(item)
        self.emit("stop")
        return self.code

    def statement(self, node):
        if node.kind == "Declare":
            if node.value is not None:
                self.emit("copy", self.expression(node.value), "-",
                          node.symbol.slot)
        elif node.kind == "Set":
            self.emit("copy", self.expression(node.value), "-",
                      node.symbol.slot)
        elif node.kind == "SetItem":
            where = self.expression(node.index)
            what = self.expression(node.value)
            self.emit("store", where, what, node.symbol.slot)
        elif node.kind == "Block":
            for item in node.body:
                self.statement(item)
        elif node.kind == "If":
            self.if_code(node)
        elif node.kind == "While":
            self.while_code(node)
        elif node.kind == "Break":
            if self.exits:
                self.emit("goto", self.exits[-1])
        elif node.kind == "Print":
            self.print_code(node)

    def if_code(self, node):
        test = self.expression(node.test)
        if node.no is None:
            done = self.label()
            self.emit("iffalse", test, done)
            self.statement(node.yes)
            self.emit("label", done)
        else:
            other = self.label()
            done = self.label()
            self.emit("iffalse", test, other)
            self.statement(node.yes)
            self.emit("goto", done)
            self.emit("label", other)
            self.statement(node.no)
            self.emit("label", done)

    def while_code(self, node):
        top = self.label()
        done = self.label()
        self.emit("label", top)
        self.emit("iffalse", self.expression(node.test), done)
        self.exits.append(done)
        self.statement(node.body)
        self.exits.pop()
        self.emit("goto", top)
        self.emit("label", done)

    def print_code(self, node):
        for item in node.items:
            if item.kind == "Text":
                self.emit("write", '"' + item.value + '"')
            else:
                self.emit("write", self.expression(item))
        self.emit("line")

    def expression(self, node):
        if node.kind == "Number":
            return node.value
        if node.kind == "RealNumber":
            return node.value
        if node.kind == "Character":
            return "'" + node.value + "'"
        if node.kind == "Name":
            return node.symbol.slot
        if node.kind == "Item":
            where = self.expression(node.index)
            target = self.temp()
            self.emit("load", node.symbol.slot, where, target)
            return target
        if node.kind == "Negate":
            target = self.temp()
            self.emit("neg", self.expression(node.value), "-", target)
            return target
        if node.kind == "Not":
            target = self.temp()
            self.emit("not", self.expression(node.value), "-", target)
            return target
        if node.op == "aur" or node.op == "ya":
            return self.short_code(node)
        left = self.expression(node.left)
        right = self.expression(node.right)
        target = self.temp()
        self.emit(names[node.op], left, right, target)
        return target

    def short_code(self, node):
        target = self.temp()
        done = self.label()
        if node.op == "aur":
            self.emit("copy", 0, "-", target)
            self.emit("iffalse", self.expression(node.left), done)
            self.emit("iffalse", self.expression(node.right), done)
            self.emit("copy", 1, "-", target)
        else:
            self.emit("copy", 1, "-", target)
            self.emit("iftrue", self.expression(node.left), done)
            self.emit("iftrue", self.expression(node.right), done)
            self.emit("copy", 0, "-", target)
        self.emit("label", done)
        return target


def generate(tree, table):
    return Generator(table).run(tree)


def write_code(code, path):
    out = open(path, "w")
    out.write("INDEX , OP , ARG1 , ARG2 , RESULT\n")
    out.write("-----------------------------------\n")
    i = 0
    for q in code:
        out.write(str(i) + " , " + q[0] + " , " + q[1] + " , " + q[2] +
                  " , " + q[3] + "\n")
        i = i + 1
    out.write("-----------------------------------\n")
    out.write("total instructions = " + str(len(code)) + "\n")
    out.close()
