widths = {"char": 1, "int16": 2, "uint16": 2, "int32": 4, "uint32": 4,
          "real": 8}

ranks = {"char": 1, "int16": 2, "uint16": 3, "int32": 4, "uint32": 5,
         "real": 6}

limits = {"char": (-128, 127), "int16": (-32768, 32767),
          "uint16": (0, 65535), "int32": (-2147483648, 2147483647),
          "uint32": (0, 4294967295)}

numbers = ["char", "int16", "uint16", "int32", "uint32", "real"]
whole = ["char", "int16", "uint16", "int32", "uint32"]


class Symbol:
    def __init__(self, name, slot, kind, datatype, length, offset, scope,
                 line):
        self.name = name
        self.slot = slot
        self.kind = kind
        self.datatype = datatype
        self.length = length
        self.offset = offset
        self.scope = scope
        self.line = line


def common(a, b):
    if a == "number":
        return b if b != "number" else "int32"
    if b == "number":
        return a
    if a == "real" or b == "real":
        return "real"
    wider = a if ranks[a] >= ranks[b] else b
    if wider == "char":
        return "int16"
    return wider


class Checker:
    def __init__(self, errors):
        self.errors = errors
        self.scopes = [{}]
        self.table = []
        self.used = []
        self.offset = 0
        self.depth = 0

    def error(self, node, message):
        self.errors.append((node.line, 0, "semantic", message))

    def declare(self, node, name, kind, datatype, length):
        if name in self.scopes[-1]:
            self.error(node, name + " is already declared")
            return None
        slot = name
        if slot in self.used:
            slot = name + "_" + str(len(self.scopes))
        self.used.append(slot)
        symbol = Symbol(name, slot, kind, datatype, length, self.offset,
                        len(self.scopes) - 1, node.line)
        self.offset = self.offset + widths[datatype] * length
        self.scopes[-1][name] = symbol
        self.table.append(symbol)
        return symbol

    def find(self, name):
        i = len(self.scopes) - 1
        while i >= 0:
            if name in self.scopes[i]:
                return self.scopes[i][name]
            i = i - 1
        return None

    def run(self, tree):
        for item in tree.body:
            self.statement(item)

    def statement(self, node):
        if node.kind == "Declare":
            self.do_declare(node)
        elif node.kind == "Array":
            self.do_array(node)
        elif node.kind == "Set":
            self.do_set(node)
        elif node.kind == "SetItem":
            self.do_set_item(node)
        elif node.kind == "If":
            self.do_if(node)
        elif node.kind == "While":
            self.do_while(node)
        elif node.kind == "Break":
            self.do_break(node)
        elif node.kind == "Print":
            self.do_print(node)
        elif node.kind == "Block":
            self.do_block(node)

    def do_block(self, node):
        self.scopes.append({})
        for item in node.body:
            self.statement(item)
        self.scopes.pop()

    def do_declare(self, node):
        symbol = self.declare(node, node.name, "scalar", node.datatype, 1)
        node.symbol = symbol
        if node.value is not None:
            self.store(node, node.datatype, self.expression(node.value),
                       node.name)
            self.fits(node.value, node.datatype)

    def do_array(self, node):
        if node.size < 1:
            self.error(node, node.name + " must have at least one element")
        node.symbol = self.declare(node, node.name, "array", node.datatype,
                                   max(node.size, 1))

    def do_set(self, node):
        symbol = self.find(node.name)
        if symbol is None:
            self.error(node, node.name + " is not declared")
            self.expression(node.value)
            return
        if symbol.kind == "array":
            self.error(node, node.name + " is an array, use " + node.name +
                       "[index]")
        node.symbol = symbol
        self.store(node, symbol.datatype, self.expression(node.value),
                   node.name)
        self.fits(node.value, symbol.datatype)

    def do_set_item(self, node):
        symbol = self.find(node.name)
        if symbol is None:
            self.error(node, node.name + " is not declared")
            self.expression(node.index)
            self.expression(node.value)
            return
        if symbol.kind != "array":
            self.error(node, node.name + " is not an array")
        node.symbol = symbol
        self.index(node, symbol, node.index)
        self.store(node, symbol.datatype, self.expression(node.value),
                   node.name)

    def do_if(self, node):
        self.condition(node, self.expression(node.test), "agar")
        self.do_block(node.yes)
        if node.no is not None:
            self.do_block(node.no)

    def do_while(self, node):
        self.condition(node, self.expression(node.test), "jabtak")
        self.depth = self.depth + 1
        self.do_block(node.body)
        self.depth = self.depth - 1

    def do_break(self, node):
        if self.depth == 0:
            self.error(node, "nikal is only allowed inside jabtak")

    def do_print(self, node):
        for item in node.items:
            if item.kind == "Text":
                item.type = "text"
            else:
                self.expression(item)

    def condition(self, node, found, word):
        if found is not None and found != "truth":
            self.error(node, "the condition of " + word +
                       " must be a comparison")

    def store(self, node, target, found, name):
        if found is None:
            return
        if found == "truth" or found == "text":
            self.error(node, "cannot store a " + found + " value in " + name)
            return
        if found == "number":
            return
        if target == found or target == "real":
            return
        if found == "real":
            self.error(node, "cannot store a real value in " + name +
                       " of type " + target)
            return
        if widths[found] > widths[target]:
            self.error(node, "a " + found + " value does not fit in " +
                       name + " of type " + target)

    def fits(self, node, target):
        if target not in limits:
            return
        value = None
        if node.kind == "Number":
            value = node.value
        if node.kind == "Negate" and node.value.kind == "Number":
            value = -node.value.value
        if value is None:
            return
        low, high = limits[target]
        if value < low or value > high:
            self.error(node, str(value) + " does not fit in " + target)

    def index(self, node, symbol, where):
        found = self.expression(where)
        if found is None:
            return
        if found != "number" and found not in whole:
            self.error(where, "an index must be a whole number")
            return
        if where.kind == "Number" and where.value >= symbol.length:
            self.error(where, "index " + str(where.value) + " is outside " +
                       symbol.name)

    def expression(self, node):
        node.type = self.work_out(node)
        return node.type

    def work_out(self, node):
        if node.kind == "Number":
            return "number"
        if node.kind == "RealNumber":
            return "real"
        if node.kind == "Character":
            return "char"
        if node.kind == "Text":
            return "text"
        if node.kind == "Name":
            return self.read_name(node)
        if node.kind == "Item":
            return self.read_item(node)
        if node.kind == "Negate":
            return self.read_negate(node)
        if node.kind == "Not":
            return self.read_not(node)
        return self.read_binary(node)

    def read_name(self, node):
        symbol = self.find(node.name)
        if symbol is None:
            self.error(node, node.name + " is not declared")
            return None
        if symbol.kind == "array":
            self.error(node, node.name + " is an array, use " + node.name +
                       "[index]")
            return None
        node.symbol = symbol
        return symbol.datatype

    def read_item(self, node):
        symbol = self.find(node.name)
        if symbol is None:
            self.error(node, node.name + " is not declared")
            self.expression(node.index)
            return None
        if symbol.kind != "array":
            self.error(node, node.name + " is not an array")
            self.expression(node.index)
            return None
        node.symbol = symbol
        self.index(node, symbol, node.index)
        return symbol.datatype

    def read_negate(self, node):
        found = self.expression(node.value)
        if found is None:
            return None
        if found == "number":
            return "number"
        if found not in numbers:
            self.error(node, "minus needs a number")
            return None
        return "int16" if found == "char" else found

    def read_not(self, node):
        found = self.expression(node.value)
        if found is not None and found != "truth":
            self.error(node, "nahi needs a comparison")
        return "truth"

    def read_binary(self, node):
        left = self.expression(node.left)
        right = self.expression(node.right)

        if node.op == "aur" or node.op == "ya":
            if left is not None and left != "truth":
                self.error(node, node.op + " needs a comparison on the left")
            if right is not None and right != "truth":
                self.error(node, node.op + " needs a comparison on the right")
            return "truth"

        if left is None or right is None:
            return None

        if left not in numbers and left != "number":
            self.error(node, node.op + " needs numbers")
            return None
        if right not in numbers and right != "number":
            self.error(node, node.op + " needs numbers")
            return None

        if node.op in ["=", "!=", "<", "<=", ">", ">="]:
            return "truth"

        if node.op == "%":
            if (left not in whole and left != "number") or \
                    (right not in whole and right != "number"):
                self.error(node, "% needs whole numbers")
                return None

        if node.op == "/" or node.op == "%":
            if node.right.kind == "Number" and node.right.value == 0:
                self.error(node, "division by zero")

        return common(left, right)


def check(tree, errors):
    checker = Checker(errors)
    checker.run(tree)
    return checker


def write_symbols(checker, path):
    out = open(path, "w")
    out.write("NAME , KIND , TYPE , LENGTH , WIDTH , OFFSET , SCOPE , LINE\n")
    out.write("-------------------------------------------------------------\n")
    for s in checker.table:
        out.write(s.name + " , " + s.kind + " , " + s.datatype + " , " +
                  str(s.length) + " , " + str(widths[s.datatype] * s.length) +
                  " , " + str(s.offset) + " , " + str(s.scope) + " , " +
                  str(s.line) + "\n")
    out.write("-------------------------------------------------------------\n")
    out.write("total symbols = " + str(len(checker.table)) + "\n")
    out.write("total bytes = " + str(checker.offset) + "\n")
    out.close()
