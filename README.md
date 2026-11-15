# Citu — language and compiler

**Student ID: BSCS23029** · Compiler Construction

Citu is a small imperative language whose keywords are Urdu words.
`cituc` is its compiler: a scanner, an LL(1) recursive-descent parser, a
semantic analyser with a scoped symbol table, a three-address-code
generator, a machine-independent optimiser, and an interpreter that runs
the generated code.

Written in Python 3. No third-party libraries.

## A Citu program

```citu
int32 i medalo 0;
int32 a[5];

jabtak ( i < 5 ) shuro
    agar ( i % 2 = 0 ) shuro
        a[i] medalo i * i;
    khatam wagarna shuro
        a[i] medalo -1;
    khatam
    i medalo i + 1;
khatam

dikhao("a[2] = ", a[2]);
```

| Citu | Meaning | | Citu | Meaning |
|---|---|---|---|---|
| `shuro` / `khatam` | `{` / `}` | | `medalo` | assignment |
| `agar` / `wagarna` | `if` / `else` | | `dikhao` | print |
| `jabtak` | `while` | | `aur` / `ya` / `nahi` | `&&` / `\|\|` / `!` |
| `nikal` | `break` | | `=` | equality test |

Types: `char`, `int16`, `uint16`, `int32`, `uint32`, `real`, plus 1-D arrays.

## Running it

```bash
python cituc.py examples/ex1_search.citu --run
```

```bash
python run_tests.py
```

Useful options:

```bash
python cituc.py FILE --run              # compile and execute
python cituc.py FILE --stop-after tac   # lex | parse | semantic | tac | optimize
python cituc.py FILE --no-optimize      # skip the optimiser
python cituc.py FILE -o DIR             # choose the output directory
python cituc.py --grammar-report doc/grammar_report.txt
```

## What a compile produces

Each phase writes its result into `build/`:

| File | Phase |
|---|---|
| `.tok` | token stream |
| `.pt` | concrete parse tree |
| `.ast.json` | abstract syntax tree |
| `.sym` | symbol table |
| `.tast.json` | type-annotated AST |
| `.tac` | three-address code |
| `.opt.tac` | optimised three-address code |
| `.out` | program output |
| `.diag` | errors and warnings |

## Examples

| File | Shows |
|---|---|
| `examples/ex1_search.citu` | arrays, `jabtak`, `agar`/`wagarna`, `nikal` |
| `examples/ex2_primes.citu` | nested loops, `%`, `aur`/`nahi`, block scope |
| `examples/ex3_stats.citu` | all six types, mixed arithmetic, real division |
| `examples/ex4_errors.citu` | deliberately broken — error reporting and recovery |

## Documentation

**[doc/Citu_Compiler_Documentation.md](doc/Citu_Compiler_Documentation.md)** — the
submission document: example programs, the complete grammar (lexical and
syntax rules), the compiler's data structures, and the intermediate file
formats.

**[doc/grammar_report.txt](doc/grammar_report.txt)** — generated: all 69
productions, FIRST, FOLLOW, every PREDICT set, and the LL(1) conflict check.

## Also in this repository

`lexer.py`, `sample.c`, `tokens.txt`, `extra/`, and the `LL1_` / `SLR1_`
markdown files are the earlier C lexical-analyser and parsing assignments.
They are unrelated to the Citu compiler in `citu/`.
