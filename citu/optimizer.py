"""Citu machine-independent optimiser (phase 5).

Rewrites the three-address code into equivalent but cheaper code.  The
passes are the classic local ones, applied repeatedly until nothing changes:

  1. constant folding          t = 3 * 4        ->  t = 12
  2. algebraic simplification  t = x + 0        ->  t = x
  3. constant propagation      x = 5; t = x + 1 ->  t = 5 + 1
  4. copy propagation          t = x; y = t     ->  y = x
  5. dead-temporary removal    a temporary that is never read is deleted
  6. unreachable-code removal  instructions after goto/halt up to the next
                               label can never run
  7. jump and label cleanup    `goto L` immediately before `L:` is dropped,
                               and labels nobody jumps to are dropped

Passes 3 and 4 are applied one BASIC BLOCK at a time.  A basic block is a
maximal run of instructions with a single entry and a single exit, so inside
one block the compiler knows the exact order of execution and the
substitutions are safe.
"""

from .runtime import DivideByZero, eval_binop, eval_unop, wrap
from .tac import ARITHOPS, RELOPS, Const, Label, Name, Quad, Temp, write_tac


# --------------------------------------------------------------------------
# Which fields of a quadruple are operands that are READ, and which single
# operand (if any) is WRITTEN.  Getting this table right is what makes the
# whole pass safe.
# --------------------------------------------------------------------------
def read_slots(q):
    """Names of the attributes of `q` that hold a value being read."""
    op = q.op
    if op == "assign":
        return ["arg1"]
    if op in ARITHOPS or op in RELOPS:
        return ["arg1", "arg2"]
    if op in ("neg", "not", "cast"):
        return ["arg1"]
    if op == "aload":
        return ["arg2"]                 # arg1 is the array itself
    if op == "astore":
        return ["arg1", "arg2"]         # index, value; result is the array
    if op in ("iffalse", "iftrue", "print"):
        return ["arg1"]
    return []


def defined(q):
    """The operand this instruction writes to, or None."""
    if q.op in ("assign", "neg", "not", "cast", "aload") \
            or q.op in ARITHOPS or q.op in RELOPS:
        return q.result
    return None


def reads(q):
    return [getattr(q, s) for s in read_slots(q)]


BLOCK_ENDERS = frozenset(["goto", "iffalse", "iftrue", "halt"])


def basic_blocks(code):
    """Split the instruction list into (start, end) half-open ranges."""
    if not code:
        return []
    leaders = {0}
    for i, q in enumerate(code):
        if q.op == "label":
            leaders.add(i)
        if q.op in BLOCK_ENDERS and i + 1 < len(code):
            leaders.add(i + 1)
    starts = sorted(leaders)
    return [(s, starts[k + 1] if k + 1 < len(starts) else len(code))
            for k, s in enumerate(starts)]


class Optimizer(object):

    def __init__(self, code, filename="<source>"):
        self.code = list(code)
        self.filename = filename
        self.stats = {
            "constant_folding": 0,
            "algebraic_simplification": 0,
            "constant_propagation": 0,
            "copy_propagation": 0,
            "dead_temporaries_removed": 0,
            "unreachable_removed": 0,
            "jumps_removed": 0,
            "labels_removed": 0,
        }
        self.original_size = len(code)

    # ---------------------------------------------------------------- run --
    def run(self, max_rounds=12):
        for _ in range(max_rounds):
            before = self._snapshot()
            self.fold_and_simplify()
            self.propagate()
            self.remove_dead_temps()
            self.remove_unreachable()
            self.clean_jumps()
            if self._snapshot() == before:
                break
        self.final_size = len(self.code)
        return self.code

    def _snapshot(self):
        return [(q.op, str(q.arg1), str(q.arg2), str(q.result))
                for q in self.code]

    # -------------------------------------------- 1 & 2: fold / simplify --
    def fold_and_simplify(self):
        for q in self.code:
            if q.op in ARITHOPS or q.op in RELOPS:
                self._fold_binary(q)
            elif q.op in ("neg", "not") and isinstance(q.arg1, Const):
                try:
                    v = eval_unop(q.op, q.arg1.value, q.result.ctype)
                except (ValueError, TypeError):
                    continue
                q.op, q.arg1, q.arg2 = "assign", Const(v, q.result.ctype), None
                self.stats["constant_folding"] += 1
            elif q.op == "cast" and isinstance(q.arg1, Const):
                from .runtime import cast as rt_cast
                q.op = "assign"
                q.arg1 = Const(rt_cast(q.arg1.value, q.arg2), q.arg2)
                q.arg2 = None
                self.stats["constant_folding"] += 1

    def _fold_binary(self, q):
        a, b = q.arg1, q.arg2
        ctype = q.result.ctype if q.result is not None else "int32"

        if isinstance(a, Const) and isinstance(b, Const):
            try:
                v = eval_binop(q.op, a.value, b.value,
                               "int32" if q.op in RELOPS else ctype)
            except (DivideByZero, ValueError, TypeError):
                return
            q.op = "assign"
            q.arg1 = Const(v, ctype)
            q.arg2 = None
            self.stats["constant_folding"] += 1
            return

        if q.op in RELOPS:
            return

        # algebraic identities
        def zero(x):
            return isinstance(x, Const) and x.ctype != "string" \
                and x.value == 0

        def one(x):
            return isinstance(x, Const) and x.ctype != "string" \
                and x.value == 1

        replacement = None
        if q.op == "add" and zero(b):
            replacement = a
        elif q.op == "add" and zero(a):
            replacement = b
        elif q.op == "sub" and zero(b):
            replacement = a
        elif q.op == "mul" and one(b):
            replacement = a
        elif q.op == "mul" and one(a):
            replacement = b
        elif q.op == "mul" and (zero(a) or zero(b)):
            replacement = Const(wrap(0, ctype), ctype)
        elif q.op == "div" and one(b):
            replacement = a

        if replacement is not None:
            q.op = "assign"
            q.arg1 = replacement
            q.arg2 = None
            self.stats["algebraic_simplification"] += 1

    # ------------------------------------------ 3 & 4: value propagation --
    def propagate(self):
        for start, end in basic_blocks(self.code):
            known = {}        # operand key -> replacement operand
            for i in range(start, end):
                q = self.code[i]

                for slot in read_slots(q):
                    operand = getattr(q, slot)
                    key = _key(operand)
                    if key is not None and key in known:
                        setattr(q, slot, known[key])
                        if isinstance(known[key], Const):
                            self.stats["constant_propagation"] += 1
                        else:
                            self.stats["copy_propagation"] += 1

                # a write invalidates what we knew about that location ...
                d = defined(q)
                if d is not None:
                    dk = _key(d)
                    known.pop(dk, None)
                    for k, v in list(known.items()):
                        if _key(v) == dk:
                            del known[k]
                    if q.op == "assign" and isinstance(q.arg1, (Const, Name,
                                                                Temp)):
                        if _key(q.arg1) != dk:
                            known[dk] = q.arg1
                # ... and an array store invalidates nothing we track,
                # because we never propagate through array elements.

    # ----------------------------------------- 5: dead temporary removal --
    def remove_dead_temps(self):
        used = set()
        for q in self.code:
            for operand in reads(q):
                if isinstance(operand, Temp):
                    used.add(operand.n)
            if q.op == "astore" and isinstance(q.result, Temp):
                used.add(q.result.n)

        kept = []
        for q in self.code:
            d = defined(q)
            # div and mod are kept even when their result is dead: they can
            # fault at run time, so deleting them would change behaviour.
            if (isinstance(d, Temp) and d.n not in used
                    and q.op not in ("div", "mod")):
                self.stats["dead_temporaries_removed"] += 1
                continue
            kept.append(q)
        self.code = kept

    # ------------------------------------------- 6: unreachable removal --
    def remove_unreachable(self):
        kept = []
        dead = False
        for q in self.code:
            if q.op == "label":
                dead = False
            if dead:
                self.stats["unreachable_removed"] += 1
                continue
            kept.append(q)
            if q.op in ("goto", "halt"):
                dead = True
        self.code = kept

    # ------------------------------------------ 7: jump / label cleanup --
    def clean_jumps(self):
        # `goto L` directly followed by `L:`
        kept = []
        i = 0
        n = len(self.code)
        while i < n:
            q = self.code[i]
            if (q.op == "goto" and i + 1 < n
                    and self.code[i + 1].op == "label"
                    and str(self.code[i + 1].arg1) == str(q.arg1)):
                self.stats["jumps_removed"] += 1
                i += 1
                continue
            kept.append(q)
            i += 1
        self.code = kept

        # labels nobody targets
        targets = set()
        for q in self.code:
            if q.op == "goto" and isinstance(q.arg1, Label):
                targets.add(str(q.arg1))
            if q.op in ("iffalse", "iftrue") and isinstance(q.arg2, Label):
                targets.add(str(q.arg2))
        kept = []
        for q in self.code:
            if q.op == "label" and str(q.arg1) not in targets:
                self.stats["labels_removed"] += 1
                continue
            kept.append(q)
        self.code = kept

    # ------------------------------------------------ intermediate file --
    def write_tac_file(self, path):
        write_tac(self.code, path, self.filename, "citu-tac-optimised")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("# optimisation summary\n")
            fh.write("#   instructions before : %d\n" % self.original_size)
            fh.write("#   instructions after  : %d\n" % len(self.code))
            for k in sorted(self.stats):
                fh.write("#   %-26s: %d\n" % (k, self.stats[k]))
        return path


def _key(operand):
    """A hashable identity for a storage location, or None for non-values."""
    if isinstance(operand, Temp):
        return ("t", operand.n)
    if isinstance(operand, Name):
        return ("n", operand.name)
    return None


def optimize(code, filename="<source>"):
    o = Optimizer(code, filename)
    o.run()
    return o
