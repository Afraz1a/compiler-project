"""Value semantics shared by the optimiser and the interpreter.

Both the constant folder and the TAC interpreter must agree exactly on what
an operation means, otherwise optimising a program could change its output.
Putting the rules in one module guarantees they cannot drift apart.
"""

from .symtab import RANGES, TYPES


def wrap(value, ctype):
    """Store `value` into a slot of type `ctype`, as the hardware would."""
    if ctype == "intlit":
        ctype = "int32"
    if ctype == "real":
        return float(value)
    if ctype == "bool":
        return 1 if value else 0
    if ctype == "char":
        if isinstance(value, str):
            return value
        return chr(int(value) & 0xFF)
    if ctype in RANGES:
        lo, hi = RANGES[ctype]
        span = hi - lo + 1
        v = int(value)
        return (v - lo) % span + lo
    return value


def numeric(value):
    """The arithmetic value of an operand (a char counts as its code)."""
    if isinstance(value, str):
        return ord(value) if len(value) == 1 else 0
    if isinstance(value, bool):
        return int(value)
    return value


def cast(value, target):
    v = numeric(value)
    if target == "real":
        return float(v)
    if target == "char":
        return chr(int(v) & 0xFF)
    if target == "bool":
        return 1 if v else 0
    return wrap(int(v), target)


class DivideByZero(Exception):
    pass


def eval_binop(op, a, b, ctype):
    """Apply one arithmetic or relational operator."""
    x, y = numeric(a), numeric(b)

    if op in ("lt", "le", "gt", "ge", "eq", "ne"):
        return {
            "lt": x < y, "le": x <= y, "gt": x > y,
            "ge": x >= y, "eq": x == y, "ne": x != y,
        }[op] and 1 or 0

    if op in ("div", "mod") and y == 0:
        raise DivideByZero("division by zero")

    if op == "add":
        r = x + y
    elif op == "sub":
        r = x - y
    elif op == "mul":
        r = x * y
    elif op == "div":
        if ctype == "real":
            r = float(x) / float(y)
        else:
            # integer division truncates toward zero, as in C
            r = abs(x) // abs(y)
            if (x < 0) != (y < 0):
                r = -r
    elif op == "mod":
        r = abs(x) % abs(y)
        if x < 0:
            r = -r
    else:
        raise ValueError("unknown binary operator %r" % op)

    return wrap(r, ctype)


def eval_unop(op, a, ctype):
    x = numeric(a)
    if op == "neg":
        return wrap(-x, ctype)
    if op == "not":
        return 0 if x else 1
    raise ValueError("unknown unary operator %r" % op)


def default_value(ctype):
    if ctype == "real":
        return 0.0
    if ctype == "char":
        return chr(0)
    return 0


def render(value, ctype):
    """How `dikhao` prints a value."""
    if ctype == "real":
        text = "%.6g" % value
        return text
    if ctype == "char" and isinstance(value, str):
        return value
    return str(value)


def type_width(ctype):
    return TYPES[ctype]["width"]
