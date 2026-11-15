#!/usr/bin/env python
"""Self-check for the Citu compiler.

Checks, in order:

  1. the grammar is LL(1)            -- no cell of the table gets two rules
  2. each example compiles cleanly   -- no errors and no warnings
  3. each example produces the expected output
  4. optimising does not change behaviour
         the unoptimised and the optimised code must print the same thing
  5. the error example really is rejected, with every expected diagnostic

Run with:   python run_tests.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from citu.errors import DiagnosticBag
from citu.grammar import build_table
from citu.lexer import Lexer
from citu.optimizer import Optimizer
from citu.parser import Parser
from citu.semantic import SemanticAnalyzer
from citu.tac import TACGenerator
from citu.vm import VM

EXPECTED = {
    # the program from the original Citu grammar assignment, verbatim
    "ex0_board.citu": [
        "i = 0",
    ],
    "ex1_search.citu": [
        "first zero is at index 3",
        "elements inspected: 4",
    ],
    "ex2_primes.citu": [
        "2 is prime", "3 is prime", "5 is prime", "7 is prime",
        "11 is prime", "13 is prime", "17 is prime", "19 is prime",
        "23 is prime", "29 is prime", "31 is prime", "37 is prime",
        "primes below 40: 12",
        "their sum: 197",
    ],
    "ex3_stats.citu": [
        "count   : 10",
        "lowest  : 33",
        "highest : 95",
        "sum     : 689",
        "mean    : 68.9",
        "passed  : 8 of 10",
        "grade   : C",
    ],
}

# Each entry is a substring that must appear somewhere in the diagnostics
# produced for ex4_errors.citu.
EXPECTED_ERRORS = [
    "already declared",
    "does not fit in char",
    "is outside 'arr'",
    "must be a comparison",
    "'y' is not declared",
    "only allowed inside a 'jabtak' loop",
    "division by zero",
    "needs a subscript",
    "needs integer operands",
    "illegal character",
    "expected an expression",
    "unterminated string literal",
]

passed = 0
failed = 0


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print("  PASS  %s" % name)
    else:
        failed += 1
        print("  FAIL  %s   %s" % (name, detail))


def front_end(path):
    """Run every phase up to code generation.  Returns (code, diag)."""
    with open(path, "r", encoding="utf-8") as fh:
        source = fh.read()
    diag = DiagnosticBag()
    lx = Lexer(source, path, diag)
    lx.tokenize()
    if diag.has_errors():
        return None, diag
    ps = Parser(lx.tokens, path, diag)
    ast = ps.parse()
    if diag.has_errors():
        return None, diag
    sa = SemanticAnalyzer(path, diag)
    sa.analyze(ast)
    if diag.has_errors():
        return None, diag
    gen = TACGenerator(sa.table, path)
    return gen.generate(ast), diag


def main():
    print("Citu compiler self-check")
    print()

    print("1. grammar")
    table, conflicts = build_table()
    check("grammar is LL(1) (%d cells filled)" % len(table),
          not conflicts, str(conflicts))
    print()

    ex_dir = os.path.join(HERE, "examples")

    print("2-4. example programs")
    for fname in sorted(EXPECTED):
        path = os.path.join(ex_dir, fname)
        code, diag = front_end(path)

        check("%s compiles without errors" % fname,
              code is not None and not diag.has_errors(),
              diag.render().strip())
        if code is None:
            continue
        check("%s compiles without warnings" % fname,
              not diag.warnings,
              "; ".join(d.message for d in diag.warnings))

        plain = VM(code)
        plain.run()
        check("%s produces the expected output" % fname,
              plain.output == EXPECTED[fname],
              "got %r" % (plain.output,))

        opt = Optimizer(code, path)
        opt_code = opt.run()
        tuned = VM(opt_code)
        tuned.run()
        check("%s optimised output is identical (%d -> %d quads)"
              % (fname, len(code), len(opt_code)),
              tuned.output == plain.output,
              "plain %r vs optimised %r" % (plain.output, tuned.output))
    print()

    print("5. error reporting")
    path = os.path.join(ex_dir, "ex4_errors.citu")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            source = fh.read()
        diag = DiagnosticBag()
        lx = Lexer(source, path, diag)
        lx.tokenize()
        ps = Parser(lx.tokens, path, diag)
        ast = ps.parse()
        sa = SemanticAnalyzer(path, diag)
        sa.analyze(ast)
        text = diag.render()
        check("ex4_errors.citu is rejected", diag.has_errors())
        for needle in EXPECTED_ERRORS:
            check("reports: %s" % needle, needle in text)
    print()

    print("%d passed, %d failed" % (passed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
