"""Three-address-code interpreter (the Citu back end).

Executes the quadruples directly, which lets the compiler actually RUN a
Citu program and makes the generated code testable: the unoptimised and the
optimised listings must produce byte-identical output.

Storage is a flat map from name to value.  A scalar holds one value, an
array holds a Python list of `length` values.  Every store goes through
runtime.wrap(), so an int16 really does wrap at 32767.
"""

from .runtime import (DivideByZero, cast, default_value, eval_binop,
                      eval_unop, numeric, render, wrap)
from .tac import ARITHOPS, RELOPS, Const, Label, Name, Temp


class CituRuntimeError(Exception):
    def __init__(self, message, line):
        Exception.__init__(self, message)
        self.message = message
        self.line = line


class VM(object):

    MAX_STEPS = 20000000          # stops a runaway loop instead of hanging

    def __init__(self, code):
        self.code = code
        self.mem = {}             # variable name -> value or list
        self.types = {}           # variable name -> declared type
        self.lengths = {}         # variable name -> element count
        self.temps = {}           # temp number -> value
        self.labels = {}
        self.output = []
        self._line = []
        self.steps = 0
        for i, q in enumerate(code):
            if q.op == "label":
                self.labels[str(q.arg1)] = i

    # ------------------------------------------------------------ values --
    def value_of(self, operand):
        if isinstance(operand, Const):
            return operand.value
        if isinstance(operand, Temp):
            return self.temps.get(operand.n, 0)
        if isinstance(operand, Name):
            v = self.mem.get(operand.name)
            if isinstance(v, list):
                return v
            return v if v is not None else 0
        return operand

    def store(self, operand, value):
        if isinstance(operand, Temp):
            self.temps[operand.n] = value
        elif isinstance(operand, Name):
            t = self.types.get(operand.name, operand.ctype or "int32")
            self.mem[operand.name] = wrap(value, t)

    # ------------------------------------------------------------- output --
    def emit_text(self, text):
        self._line.append(text)

    def end_line(self):
        self.output.append("".join(self._line))
        self._line = []

    # --------------------------------------------------------------- run --
    def run(self):
        pc = 0
        n = len(self.code)
        while pc < n:
            self.steps += 1
            if self.steps > self.MAX_STEPS:
                raise CituRuntimeError(
                    "program exceeded %d instructions; it is probably "
                    "looping for ever" % self.MAX_STEPS, self.code[pc].line)
            q = self.code[pc]
            op = q.op

            try:
                if op == "alloc":
                    name = q.result.name
                    self.types[name] = q.arg1
                    self.lengths[name] = q.arg2
                    if q.arg2 > 1:
                        self.mem[name] = [default_value(q.arg1)] * q.arg2
                    else:
                        self.mem[name] = default_value(q.arg1)

                elif op == "assign":
                    self.store(q.result, self.value_of(q.arg1))

                elif op in ARITHOPS:
                    v = eval_binop(op, self.value_of(q.arg1),
                                   self.value_of(q.arg2), q.result.ctype)
                    self.store(q.result, v)

                elif op in RELOPS:
                    v = eval_binop(op, self.value_of(q.arg1),
                                   self.value_of(q.arg2), "int32")
                    self.store(q.result, v)

                elif op in ("neg", "not"):
                    self.store(q.result,
                               eval_unop(op, self.value_of(q.arg1),
                                         q.result.ctype))

                elif op == "cast":
                    self.store(q.result, cast(self.value_of(q.arg1), q.arg2))

                elif op == "aload":
                    arr = self.mem.get(q.arg1.name)
                    idx = int(numeric(self.value_of(q.arg2)))
                    self._bounds(q.arg1.name, arr, idx, q.line)
                    self.store(q.result, arr[idx])

                elif op == "astore":
                    name = q.result.name
                    arr = self.mem.get(name)
                    idx = int(numeric(self.value_of(q.arg1)))
                    self._bounds(name, arr, idx, q.line)
                    arr[idx] = wrap(self.value_of(q.arg2),
                                    self.types.get(name, "int32"))

                elif op == "label":
                    pass

                elif op == "goto":
                    pc = self.labels[str(q.arg1)]
                    continue

                elif op == "iffalse":
                    if not numeric(self.value_of(q.arg1)):
                        pc = self.labels[str(q.arg2)]
                        continue

                elif op == "iftrue":
                    if numeric(self.value_of(q.arg1)):
                        pc = self.labels[str(q.arg2)]
                        continue

                elif op == "print":
                    ctype = q.arg1.ctype or "int32"
                    self.emit_text(render(self.value_of(q.arg1), ctype))

                elif op == "printstr":
                    self.emit_text(str(q.arg1.value))

                elif op == "newline":
                    self.end_line()

                elif op == "halt":
                    break

                else:
                    raise CituRuntimeError("unknown opcode %r" % op, q.line)

            except DivideByZero:
                raise CituRuntimeError("division by zero", q.line)

            pc += 1

        if self._line:
            self.end_line()
        return self.output

    @staticmethod
    def _bounds(name, arr, idx, line):
        if not isinstance(arr, list):
            raise CituRuntimeError("'%s' is not an array" % name, line)
        if idx < 0 or idx >= len(arr):
            raise CituRuntimeError(
                "index %d is outside '%s', which has %d elements"
                % (idx, name, len(arr)), line)

    # ---------------------------------------------------------- reporting --
    def write_output_file(self, path, source):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# citu-program-output v1\n")
            fh.write("# source: %s\n" % source)
            fh.write("# instructions executed: %d\n" % self.steps)
            fh.write("#" + "-" * 50 + "\n")
            for line in self.output:
                fh.write(line + "\n")
        return path


def run(code):
    vm = VM(code)
    vm.run()
    return vm
