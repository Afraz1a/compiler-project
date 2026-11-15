import os
import sys

from citu.lexer import scan, write_tokens
from citu.parser import parse, write_tree
from citu.semantic import check, write_symbols
from citu.codegen import generate, write_code

filename = "examples/search.citu"
if len(sys.argv) > 1:
    filename = sys.argv[1]

name = os.path.splitext(os.path.basename(filename))[0]
folder = "build"
if not os.path.isdir(folder):
    os.makedirs(folder)

code = open(filename).read()
errors = []

tokens = scan(code, errors)
write_tokens(tokens, folder + "/" + name + ".tokens")

tree = parse(tokens, errors)
checker = check(tree, errors)
write_tree(tree, folder + "/" + name + ".tree")
write_symbols(checker, folder + "/" + name + ".symbols")

quads = []
if not errors:
    quads = generate(tree, checker.table)
    write_code(quads, folder + "/" + name + ".tac")

print("input file :", filename)
print("tokens :", len(tokens))
print("symbols :", len(checker.table))
print("instructions :", len(quads))

if errors:
    print("errors :", len(errors))
    for line, col, phase, message in sorted(errors):
        print("  line", line, ":", phase, "error :", message)
else:
    print("errors : 0")
