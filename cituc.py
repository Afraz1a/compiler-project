#!/usr/bin/env python
"""cituc -- the Citu compiler driver.

Usage
    python cituc.py <file.citu> [options]

Options
    -o DIR, --outdir DIR   where to put the intermediate files (default build/)
    --run                  execute the generated code and show its output
    --no-optimize          skip the optimisation phase
    --stop-after PHASE     lex | parse | semantic | tac | optimize
    --grammar-report FILE  write the FIRST/FOLLOW/LL(1) report and exit
    --quiet                only print errors

The driver runs the phases in order and writes one intermediate file per
phase into the output directory:

    <name>.tok        token stream              (lexical analysis)
    <name>.pt         concrete parse tree       (syntax analysis)
    <name>.ast.json   abstract syntax tree      (syntax analysis)
    <name>.sym        symbol table              (semantic analysis)
    <name>.tast.json  type-annotated AST        (semantic analysis)
    <name>.tac        three-address code        (intermediate code generation)
    <name>.opt.tac    optimised three-address code (optimisation)
    <name>.diag       all diagnostics
    <name>.out        program output            (--run)
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from citu.errors import DiagnosticBag
from citu.lexer import Lexer
from citu.optimizer import Optimizer
from citu.parser import Parser
from citu.semantic import SemanticAnalyzer
from citu.tac import TACGenerator
from citu.vm import VM, CituRuntimeError

PHASES = ("lex", "parse", "semantic", "tac", "optimize")


def log(quiet, *parts):
    if not quiet:
        print(*parts)


def compile_file(path, outdir="build", optimize=True, stop_after=None,
                 run_program=False, quiet=False):
    """Run the whole pipeline.  Returns (exit_code, artifacts dict)."""
    name = os.path.splitext(os.path.basename(path))[0]
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    def out(ext):
        return os.path.join(outdir, name + ext)

    with open(path, "r", encoding="utf-8") as fh:
        source = fh.read()

    diag = DiagnosticBag()
    art = {}

    # ---------------------------------------------------- 1. lexical ----
    lx = Lexer(source, path, diag)
    lx.tokenize()
    art["tokens"] = lx.write_token_file(out(".tok"))
    log(quiet, "  lexical analysis    -> %-22s %4d tokens"
        % (os.path.basename(art["tokens"]), len(lx.tokens)))
    # Note: a lexical error does NOT stop the run.  The scanner recovers in
    # panic mode, so parsing and semantic analysis still go ahead and the
    # user sees every problem in the file at once.  Only code generation is
    # skipped when the front end found errors.
    if stop_after == "lex":
        return finish(diag, out, art, quiet)

    # ----------------------------------------------------- 2. syntax ----
    ps = Parser(lx.tokens, path, diag)
    ast = ps.parse()
    art["parse_tree"] = ps.write_parse_tree(out(".pt"))
    with open(out(".ast.json"), "w", encoding="utf-8") as fh:
        json.dump({"format": "citu-ast", "version": 1, "source": path,
                   "tree": ast.to_dict(typed=False)}, fh, indent=2)
    art["ast"] = out(".ast.json")
    log(quiet, "  syntax analysis     -> %-22s %4d parse-tree nodes"
        % (os.path.basename(art["parse_tree"]),
           sum(k.count() for k in ps.root.kids)))
    if stop_after == "parse":
        return finish(diag, out, art, quiet)

    # --------------------------------------------------- 3. semantic ----
    sa = SemanticAnalyzer(path, diag)
    sa.analyze(ast)
    art["symbols"] = sa.write_symbol_file(out(".sym"))
    with open(out(".tast.json"), "w", encoding="utf-8") as fh:
        json.dump({"format": "citu-typed-ast", "version": 1, "source": path,
                   "frame_size": sa.table.frame_size,
                   "tree": ast.to_dict(typed=True)}, fh, indent=2)
    art["typed_ast"] = out(".tast.json")
    n_syms = sum(len(s.names) for s in sa.table.all_scopes)
    log(quiet, "  semantic analysis   -> %-22s %4d symbols in %d scopes"
        % (os.path.basename(art["symbols"]), n_syms,
           len(sa.table.all_scopes)))
    if diag.has_errors() or stop_after == "semantic":
        if diag.has_errors():
            log(quiet, "  code generation     -- skipped, the front end "
                       "found %d error(s)" % len(diag.errors))
        return finish(diag, out, art, quiet)

    # ---------------------------------------- 4. intermediate code ------
    gen = TACGenerator(sa.table, path)
    code = gen.generate(ast)
    art["tac"] = gen.write_tac_file(out(".tac"))
    log(quiet, "  intermediate code   -> %-22s %4d quadruples"
        % (os.path.basename(art["tac"]), len(code)))
    if stop_after == "tac":
        return finish(diag, out, art, quiet)

    # ----------------------------------------------- 5. optimisation ----
    final_code = code
    if optimize:
        op = Optimizer(code, path)
        final_code = op.run()
        art["opt_tac"] = op.write_tac_file(out(".opt.tac"))
        saved = len(code) - len(final_code)
        log(quiet, "  optimisation        -> %-22s %4d quadruples "
            "(%d removed)"
            % (os.path.basename(art["opt_tac"]), len(final_code), saved))
    if stop_after == "optimize":
        return finish(diag, out, art, quiet)

    # ------------------------------------------------------- 6. run -----
    if run_program:
        vm = VM(final_code)
        try:
            vm.run()
        except CituRuntimeError as exc:
            diag.error("runtime", exc.line, 0, exc.message)
            art["output"] = vm.write_output_file(out(".out"), path)
            return finish(diag, out, art, quiet)
        art["output"] = vm.write_output_file(out(".out"), path)
        log(quiet, "  execution           -> %-22s %4d instructions executed"
            % (os.path.basename(art["output"]), vm.steps))
        art["stdout"] = vm.output

    return finish(diag, out, art, quiet)


def finish(diag, out, art, quiet):
    with open(out(".diag"), "w", encoding="utf-8") as fh:
        fh.write("# citu-diagnostics v1\n")
        fh.write("# errors: %d   warnings: %d\n"
                 % (len(diag.errors), len(diag.warnings)))
        fh.write("# fields: SEVERITY PHASE LINE:COL MESSAGE\n")
        fh.write("#" + "-" * 70 + "\n")
        fh.write(diag.render())
    art["diagnostics"] = out(".diag")
    return (1 if diag.has_errors() else 0), art, diag


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="cituc", description="Compiler for the Citu language")
    ap.add_argument("source", nargs="?", help="a .citu source file")
    ap.add_argument("-o", "--outdir", default="build")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--no-optimize", dest="optimize", action="store_false")
    ap.add_argument("--stop-after", choices=PHASES)
    ap.add_argument("--grammar-report", metavar="FILE")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if args.grammar_report:
        from citu.grammar import write_report
        path, conflicts = write_report(args.grammar_report)
        print("grammar report written to", path)
        print("LL(1) conflicts:", len(conflicts))
        return 1 if conflicts else 0

    if not args.source:
        ap.error("a source file is required")

    if not args.quiet:
        print("cituc: compiling %s" % args.source)

    code, art, diag = compile_file(
        args.source, args.outdir, args.optimize, args.stop_after,
        args.run, args.quiet)

    if diag.items:
        print()
        print(diag.render().rstrip())

    if not args.quiet:
        print()
        print("  %d error(s), %d warning(s)"
              % (len(diag.errors), len(diag.warnings)))

    if args.run and "stdout" in art:
        print()
        print("--- program output " + "-" * 40)
        for line in art["stdout"]:
            print(line)
        print("-" * 59)

    return code


if __name__ == "__main__":
    sys.exit(main())
