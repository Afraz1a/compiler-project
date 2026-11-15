# The Citu Language and its Compiler

**Compiler Construction — Project Submission**

| | |
|---|---|
| Student ID | **BSCS23029** |
| Repository | *(see section 5)* |
| Language | **Citu** — a small imperative language with Urdu keywords |
| Compiler | `cituc`, written in Python 3 (no third-party libraries) |
| Status | 3 example programs compile, optimise and run; 26/26 self-checks pass |

This single document covers all five required items:

1. [Example Programs](#1-example-programs)
2. [Citu Language Grammar](#2-citu-language-grammar)
3. [Data Structures](#3-data-structures)
4. [Intermediate File Format](#4-intermediate-file-format)
5. [Git Repository](#5-git-repository)

---

## 0. Overview

### 0.1 Where Citu comes from

Citu is the language from the earlier grammar assignment. Its keywords are
Urdu words:

| Citu keyword | Meaning | C equivalent |
|---|---|---|
| `shuro` | start | `{` |
| `khatam` | end | `}` |
| `agar` | if | `if` |
| `wagarna` | otherwise | `else` |
| `jabtak` | as long as | `while` |
| `nikal` | get out | `break` |
| `medalo` | put into | `=` (assignment) |
| `dikhao` | show | `printf` |
| `aur` | and | `&&` |
| `ya` | or | `\|\|` |
| `nahi` | not | `!` |

The loop from the original assignment is still valid Citu today:

```citu
jabtak ( i < size ) shuro
    agar ( a[i] = 0 ) shuro nikal; khatam
    i medalo i + 1;
khatam
```

Note that `=` is the **equality test**. Assignment is the word `medalo`, so
the classic `if (x = 0)` bug cannot be written in Citu.

The language was extended beyond the original assignment sketch with
`wagarna`, `dikhao`, the word operators `aur` / `ya` / `nahi`, the full
operator set `+ - * / %` with proper precedence, and block scope. The six
declarable types (`int16`, `int32`, `uint16`, `uint32`, `real`, `char`) are
the ones listed with the original language.

### 0.2 Compiler structure

The compiler is a classic multi-pass front end plus an optimiser and an
interpreting back end. Each phase writes its result to a file, so every
stage can be inspected on its own.

```
  source.citu
       |
       v
  +---------------------+                          (citu/lexer.py)
  | 1. lexical analysis |  -------->  source.tok
  +---------------------+
       |  token list
       v
  +---------------------+                          (citu/parser.py)
  | 2. syntax analysis  |  -------->  source.pt
  +---------------------+  -------->  source.ast.json
       |  abstract syntax tree
       v
  +---------------------+                          (citu/semantic.py)
  | 3. semantic analysis|  -------->  source.sym
  +---------------------+  -------->  source.tast.json
       |  typed AST + symbol table
       v
  +---------------------+                          (citu/tac.py)
  | 4. code generation  |  -------->  source.tac
  +---------------------+
       |  three-address code
       v
  +---------------------+                          (citu/optimizer.py)
  | 5. optimisation     |  -------->  source.opt.tac
  +---------------------+
       |  optimised three-address code
       v
  +---------------------+                          (citu/vm.py)
  | 6. execution        |  -------->  source.out
  +---------------------+

  every phase also appends to                      source.diag
```

### 0.3 Files in the repository

| Path | What it is |
|---|---|
| `cituc.py` | compiler driver / command line |
| `run_tests.py` | self-check: grammar, examples, optimiser, error reporting |
| `citu/tokens.py` | token classes and the keyword table |
| `citu/lexer.py` | phase 1 — scanner |
| `citu/grammar.py` | the formal grammar + FIRST/FOLLOW + LL(1) table |
| `citu/parser.py` | phase 2 — recursive-descent parser |
| `citu/ast_nodes.py` | AST node classes |
| `citu/symtab.py` | symbol table and type system |
| `citu/semantic.py` | phase 3 — type checking and context rules |
| `citu/tac.py` | phase 4 — three-address code generation |
| `citu/optimizer.py` | phase 5 — machine-independent optimisation |
| `citu/vm.py` | phase 6 — three-address-code interpreter |
| `citu/runtime.py` | value semantics shared by optimiser and interpreter |
| `citu/errors.py` | diagnostics |
| `examples/*.citu` | the example programs |
| `doc/` | this document and the generated grammar report |
| `build/` | generated intermediate files |

### 0.4 How to run it

```bash
python cituc.py examples/ex1_search.citu --run
python cituc.py examples/ex2_primes.citu --stop-after tac
python cituc.py --grammar-report doc/grammar_report.txt
python run_tests.py
```

---

## 1. Example Programs

Three programs, in `examples/`. Each one compiles with **zero errors and
zero warnings**, and the output shown below is the real output of
`python cituc.py <file> --run`.

| Program | Tokens | Parse-tree nodes | Symbols / scopes | Quads | After optimisation |
|---|---|---|---|---|---|
| `ex1_search.citu` | 142 | 614 | 4 / 5 | 45 | 43 |
| `ex2_primes.citu` | 129 | 551 | 6 / 5 | 60 | 60 |
| `ex3_stats.citu` | 297 | 1327 | 9 / 10 | 108 | 105 |

A fourth file, `ex4_errors.citu`, is deliberately broken and is described in
section 1.4.

### 1.1 `ex1_search.citu` — linear search

Demonstrates: array declaration and element assignment, a `jabtak` loop,
`agar` / `wagarna`, `nikal` for an early exit, unary minus, `dikhao`.
This is the program from the original grammar assignment, extended so that
it declares its own data and reports the answer.

```citu
int32 size medalo 8;
int32 a[8];

a[0] medalo 14;
a[1] medalo 7;
a[2] medalo 23;
a[3] medalo 0;
a[4] medalo 9;
a[5] medalo 0;
a[6] medalo 31;
a[7] medalo 5;

int32 i medalo 0;
int32 found medalo -1;          /* -1 stands for "not found yet" */

jabtak ( i < size ) shuro
    agar ( a[i] = 0 ) shuro
        found medalo i;
        nikal;                  // stop at the FIRST zero
    khatam
    i medalo i + 1;
khatam

agar ( found < 0 ) shuro
    dikhao("there is no zero in the array");
khatam wagarna shuro
    dikhao("first zero is at index ", found);
khatam

dikhao("elements inspected: ", i + 1);
```

Output:

```
first zero is at index 3
elements inspected: 4
```

### 1.2 `ex2_primes.citu` — primes below a limit

Demonstrates: nested `jabtak` loops, `%`, `nikal` leaving only the inner
loop, the word operators `aur` and `nahi`, block scope (`d` and `prime`
belong to the loop body, not to the program), and the unsigned types.

```citu
uint16 limit medalo 40;
uint16 n medalo 2;
uint16 count medalo 0;
uint32 total medalo 0;          // sum of the primes found

jabtak ( n < limit ) shuro

    // these two belong to the loop body block, not to the program
    uint16 d medalo 2;
    int16 prime medalo 1;

    jabtak ( d * d <= n ) shuro
        agar ( n % d = 0 ) shuro
            prime medalo 0;
            nikal;              // no need to try any more divisors
        khatam
        d medalo d + 1;
    khatam

    agar ( prime = 1 aur nahi (n = 1) ) shuro
        dikhao(n, " is prime");
        count medalo count + 1;
        total medalo total + n;
    khatam

    n medalo n + 1;
khatam

dikhao("primes below ", limit, ": ", count);
dikhao("their sum: ", total);
```

Output:

```
2 is prime
3 is prime
5 is prime
7 is prime
11 is prime
13 is prime
17 is prime
19 is prime
23 is prime
29 is prime
31 is prime
37 is prime
primes below 40: 12
their sum: 197
```

### 1.3 `ex3_stats.citu` — minimum, maximum and mean

Demonstrates: every declarable type, mixed-type arithmetic with the
widening the compiler inserts automatically, real division, `ya`, a
character literal, and nested `agar` / `wagarna` used as a chain.

```citu
int32 count medalo 10;
int16 marks[10];

marks[0] medalo 72;
marks[1] medalo 48;
marks[2] medalo 91;
marks[3] medalo 65;
marks[4] medalo 33;
marks[5] medalo 88;
marks[6] medalo 57;
marks[7] medalo 79;
marks[8] medalo 95;
marks[9] medalo 61;

int16  lowest  medalo 32767;    // the largest value an int16 can hold
int16  highest medalo -32768;
int32  sum     medalo 0;
int32  passes  medalo 0;
int32  k       medalo 0;

jabtak ( k < count ) shuro
    agar ( marks[k] < lowest ) shuro
        lowest medalo marks[k];
    khatam
    agar ( marks[k] > highest ) shuro
        highest medalo marks[k];
    khatam
    sum medalo sum + marks[k];
    agar ( marks[k] >= 50 ) shuro
        passes medalo passes + 1;
    khatam
    k medalo k + 1;
khatam

// integer sum divided by an integer count, in real arithmetic:
// the compiler widens both operands to real before dividing
real mean medalo sum / 1.0 / count;

dikhao("count   : ", count);
dikhao("lowest  : ", lowest);
dikhao("highest : ", highest);
dikhao("sum     : ", sum);
dikhao("mean    : ", mean);
dikhao("passed  : ", passes, " of ", count);

// a grade for the class average
char grade medalo 'F';
agar ( mean >= 80.0 ) shuro
    grade medalo 'A';
khatam wagarna shuro
    agar ( mean >= 70.0 ) shuro
        grade medalo 'B';
    khatam wagarna shuro
        agar ( mean >= 60.0 ya mean >= 55.0 ) shuro
            grade medalo 'C';
        khatam
    khatam
khatam

dikhao("grade   : ", grade);
```

Output:

```
count   : 10
lowest  : 33
highest : 95
sum     : 689
mean    : 68.9
passed  : 8 of 10
grade   : C
```

### 1.4 `ex4_errors.citu` — error reporting

Not a working program. Every line has a deliberate mistake, and it shows
that the compiler does **not** stop at the first error: the scanner recovers
in panic mode, the parser resynchronises on statement boundaries, and
semantic analysis still runs, so one compilation reports everything.

```
$ python cituc.py examples/ex4_errors.citu

  lexical analysis    -> ex4_errors.tok           78 tokens
  syntax analysis     -> ex4_errors.pt           317 parse-tree nodes
  semantic analysis   -> ex4_errors.sym            7 symbols in 2 scopes
  code generation     -- skipped, the front end found 14 error(s)

error    semantic 13:1    'x' is already declared in this scope (first declared at line 12)
warning  semantic 15:1    'c' is assigned but its value is never read
error    semantic 15:16   literal 70000 does not fit in char (range -128..127)
warning  semantic 17:1    'arr' is assigned but its value is never read
error    semantic 18:5    index 7 is outside 'arr', which has 3 elements (0 to 2)
error    semantic 20:8    the condition of 'agar' must be a comparison, not a plain int32 value
error    semantic 21:12   'y' is not declared
error    semantic 24:1    'nikal' is only allowed inside a 'jabtak' loop
warning  semantic 26:1    'q' is assigned but its value is never read
error    semantic 26:18   division by zero
warning  semantic 27:1    'w' is assigned but its value is never read
error    semantic 27:16   'arr' is an array; it needs a subscript such as arr[0]
warning  semantic 30:1    'z' is assigned but its value is never read
error    semantic 30:18   operator '%' needs integer operands, not int32 and real
error    lexical  32:18   illegal character  (near '@')
error    syntax   32:20   expected ';' but found '4'  (near '4')
error    syntax   34:16   expected an expression but found ';'  (near ';')
error    lexical  35:8    unterminated string literal  (near '"unterminated ...')
error    syntax   36:1    expected an expression but found '<eof>'

  14 error(s), 5 warning(s)
```

---

## 2. Citu Language Grammar

The grammar lives in `citu/grammar.py` and is the single source of truth:
the parser implements exactly these productions, and the same file
mechanically builds the LL(1) table and checks it for conflicts. The full
machine-generated listing — all 69 productions, FIRST, FOLLOW, every
PREDICT set, and the conflict check — is in **`doc/grammar_report.txt`**,
regenerated with:

```bash
python cituc.py --grammar-report doc/grammar_report.txt
```

### 2.1 Lexical rules (tokens)

The scanner joins one regular expression per category into a single master
regular expression of named alternatives and matches it at the current
position. Python's alternation returns the **first alternative that
matches**, so listing the categories longest/most-specific first implements
the **maximal munch** rule.

#### Token categories

| # | Category | Regular expression | Note |
|---|---|---|---|
| 1 | `NEWLINE` | `\r\n|\r|\n` | drives the line counter, discarded |
| 2 | `WS` | `[ \t\f\v]+` | discarded |
| 3 | `COMMENT_ML` | `/\*[\s\S]*?\*/` | lazy `*?` stops at the first `*/` |
| 4 | `COMMENT_BAD` | `/\*[\s\S]*` | `/*` with no `*/` → error |
| 5 | `COMMENT_SL` | `//[^\r\n]*` | discarded |
| 6 | `REALLIT` | `(?:\d+\.\d*\|\.\d+)(?:[eE][+-]?\d+)?\|\d+[eE][+-]?\d+` | `3.14`, `.5`, `2.`, `1e10` |
| 7 | `INTLIT` | `0[xX][0-9a-fA-F]+\|\d+` | `42`, `0xFF` |
| 8 | `CHARLIT` | `'(?:\\[nrt0\\'"]\|[^'\\\r\n])'` | `'A'`, `'\n'` |
| 9 | `CHARLIT_BAD` | `'(?:\\.\|[^'\\\r\n])*'?` | malformed → error |
| 10 | `STRLIT` | `"(?:\\[nrt0\\'"]\|[^"\\\r\n])*"` | `"hello"` |
| 11 | `STRLIT_BAD` | `"(?:\\.\|[^"\\\r\n])*` | unterminated → error |
| 12 | `ID` | `[A-Za-z_][A-Za-z0-9_]*` | then looked up in the keyword table |
| 13 | `SYM` | the operators and punctuators, longest first | see below |
| 14 | `BAD` | `.` | any illegal character → error, scanning continues |

#### Why the order matters

* **Comments before operators** — otherwise `/*` scans as `/` then `*`.
* **`REALLIT` before `INTLIT`** — otherwise `3.14` scans as `3`, `.`, `14`.
* **Hexadecimal before decimal inside `INTLIT`** — otherwise `0xFF` scans as
  `0` then the identifier `xFF`.
* **Literals before `ID`** — so a character literal is never split up.
* **Longest operator first** — `<=` before `<`, `!=` before `!`. The symbol
  list is sorted by descending length in code, so this is automatic.
* **`BAD` last** — it matches any single character, which guarantees the
  scanner always advances and can never loop forever. This is the
  panic-mode recovery point.

#### Keywords

Keywords are **not** given their own regular expression. They match the
`ID` rule and are then re-classified by a table lookup, which avoids needing
a `\b` guard so that `integer` is not scanned as `int` + `eger`.

| Lexeme | Token | Lexeme | Token |
|---|---|---|---|
| `shuro` | `SHURO` | `int16` | `INT16` |
| `khatam` | `KHATAM` | `int32` | `INT32` |
| `agar` | `AGAR` | `uint16` | `UINT16` |
| `wagarna` | `WAGARNA` | `uint32` | `UINT32` |
| `jabtak` | `JABTAK` | `real` | `REAL` |
| `nikal` | `NIKAL` | `char` | `CHAR` |
| `medalo` | `MEDALO` | `aur` | `AUR` |
| `dikhao` | `DIKHAO` | `ya` | `YA` |
| | | `nahi` | `NAHI` |

#### Operators and punctuators

| Lexeme | Token | Lexeme | Token | Lexeme | Token |
|---|---|---|---|---|---|
| `<=` | `LE` | `+` | `PLUS` | `(` | `LPAREN` |
| `>=` | `GE` | `-` | `MINUS` | `)` | `RPAREN` |
| `!=` | `NE` | `*` | `STAR` | `[` | `LBRACK` |
| `<` | `LT` | `/` | `SLASH` | `]` | `RBRACK` |
| `>` | `GT` | `%` | `PERCENT` | `;` | `SEMI` |
| `=` | `EQ` (equality) | | | `,` | `COMMA` |

There are **40 terminals** in all, including `EOF`.

### 2.2 Syntax rules

69 productions over 32 nonterminals. Start symbol `Program`. `eps` is the
empty string. The grammar has **no left recursion** and **no common
prefixes**, which is what makes it LL(1).

#### Program, statements and blocks

```
 1  Program   -> StmtList
 2  StmtList  -> Stmt StmtList
 3  StmtList  -> eps

 4  Stmt      -> Decl
 5  Stmt      -> Assign
 6  Stmt      -> If
 7  Stmt      -> While
 8  Stmt      -> Break
 9  Stmt      -> Print

32  Block     -> SHURO StmtList KHATAM
```

`Stmt` is decided by one lookahead token: a type keyword starts a `Decl`,
`ID` starts an `Assign`, and `agar` / `jabtak` / `nikal` / `dikhao` each
start exactly one other kind of statement.

#### Declarations

```
10  Decl      -> Type ID DeclTail
11  DeclTail  -> LBRACK INTLIT RBRACK SEMI        -- int32 a[8];
12  DeclTail  -> MEDALO Expr SEMI                 -- int32 x medalo 5;
13  DeclTail  -> SEMI                             -- int32 x;
14  Type      -> INT16
15  Type      -> INT32
16  Type      -> UINT16
17  Type      -> UINT32
18  Type      -> REAL
19  Type      -> CHAR
```

An array size must be an integer **literal**, so storage is known at compile
time.

#### Assignment

```
20  Assign    -> ID AsgTail
21  AsgTail   -> LBRACK Expr RBRACK MEDALO Expr SEMI   -- a[i] medalo e;
22  AsgTail   -> MEDALO Expr SEMI                      -- x medalo e;
```

Factoring the common `ID` out into `Assign` and deciding on the next token
is **left factoring**; without it the two forms would share a prefix and the
grammar would not be LL(1).

#### Control flow and output

```
23  If        -> AGAR LPAREN Expr RPAREN Block ElsePart
24  ElsePart  -> WAGARNA Block
25  ElsePart  -> eps
26  While     -> JABTAK LPAREN Expr RPAREN Block
27  Break     -> NIKAL SEMI

28  Print     -> DIKHAO LPAREN ArgList RPAREN SEMI
29  ArgList   -> Arg ArgTail
30  ArgTail   -> COMMA Arg ArgTail
31  ArgTail   -> eps
32  Arg       -> STRLIT
33  Arg       -> Expr
```

Because the body of `agar` and `jabtak` is always a `Block`, Citu has **no
dangling-else problem**: the braces are compulsory, so `ElsePart` can only
attach to the `agar` it follows.

#### Expressions

Precedence is built into the grammar, one nonterminal per level, lowest
first. Each level uses the right-recursive `...Tail` form so that there is
no left recursion.

```
34  Expr      -> OrExpr
35  OrExpr    -> AndExpr OrTail
36  OrTail    -> YA AndExpr OrTail
37  OrTail    -> eps
38  AndExpr   -> RelExpr AndTail
39  AndTail   -> AUR RelExpr AndTail
40  AndTail   -> eps
41  RelExpr   -> AddExpr RelTail
42  RelTail   -> RelOp AddExpr
43  RelTail   -> eps
44-49  RelOp  -> EQ | NE | LT | LE | GT | GE
50  AddExpr   -> MulExpr AddTail
51  AddTail   -> PLUS MulExpr AddTail
52  AddTail   -> MINUS MulExpr AddTail
53  AddTail   -> eps
54  MulExpr   -> Unary MulTail
55  MulTail   -> STAR Unary MulTail
56  MulTail   -> SLASH Unary MulTail
57  MulTail   -> PERCENT Unary MulTail
58  MulTail   -> eps
59  Unary     -> MINUS Unary
60  Unary     -> NAHI Unary
61  Unary     -> Primary
62  Primary   -> ID PrimTail
63  Primary   -> INTLIT
64  Primary   -> REALLIT
65  Primary   -> CHARLIT
66  Primary   -> LPAREN Expr RPAREN
67  PrimTail  -> LBRACK Expr RBRACK
68  PrimTail  -> eps
```

Precedence, lowest to highest: `ya` < `aur` < relational < `+ -` < `* / %` <
unary `-` `nahi` < primary. `RelTail` has no recursive call, so relational
operators do **not** chain: `a < b < c` is a syntax error, not a silently
wrong comparison.

`+ - * / %` are left-associative. The `...Tail` productions are
right-recursive on paper, but the parser implements each of them as a
`while` loop that folds the result leftwards, which produces a
left-associative tree. This is the standard way to get left associativity
out of a grammar that must not be left-recursive.

### 2.3 FIRST and FOLLOW

Computed by `citu/grammar.py`. An abridged table; the complete one is in
`doc/grammar_report.txt`.

| Nonterminal | FIRST | FOLLOW |
|---|---|---|
| `Program` | type keywords, `ID`, `AGAR`, `JABTAK`, `NIKAL`, `DIKHAO`, eps | `$` |
| `StmtList` | same as `Program` | `$` `KHATAM` |
| `Decl` | `CHAR INT16 INT32 REAL UINT16 UINT32` | statement starters, `KHATAM`, `$` |
| `DeclTail` | `LBRACK MEDALO SEMI` | statement starters, `KHATAM`, `$` |
| `Assign` | `ID` | statement starters, `KHATAM`, `$` |
| `AsgTail` | `LBRACK MEDALO` | statement starters, `KHATAM`, `$` |
| `ElsePart` | `WAGARNA`, eps | statement starters, `KHATAM`, `$` |
| `Block` | `SHURO` | statement starters, `KHATAM`, `WAGARNA`, `$` |
| `Expr` | `CHARLIT ID INTLIT LPAREN MINUS NAHI REALLIT` | `COMMA RBRACK RPAREN SEMI` |
| `OrTail` | `YA`, eps | `COMMA RBRACK RPAREN SEMI` |
| `AndTail` | `AUR`, eps | `COMMA RBRACK RPAREN SEMI YA` |
| `RelTail` | `EQ GE GT LE LT NE`, eps | `AUR COMMA RBRACK RPAREN SEMI YA` |
| `AddTail` | `MINUS PLUS`, eps | relational ops, `AUR COMMA RBRACK RPAREN SEMI YA` |
| `MulTail` | `PERCENT SLASH STAR`, eps | `MINUS PLUS`, relational ops, … |
| `PrimTail` | `LBRACK`, eps | all operators, `COMMA RBRACK RPAREN SEMI` |

### 2.4 The LL(1) check

For every production `A -> alpha`, `PREDICT(A -> alpha)` is `FIRST(alpha)`,
and if `alpha` can derive eps then also `FOLLOW(A)`. The table is filled
with `M[A, t] = A -> alpha` for every `t` in the predict set.

```
## LL(1) check

No cell of the parsing table received two productions.
The grammar is LL(1).  Filled cells: 223
```

Because the table is conflict-free, the recursive-descent parser needs one
token of lookahead and never backtracks.

### 2.5 Static semantics

Rules a context-free grammar cannot express, all enforced in
`citu/semantic.py`:

* a name must be declared before use, and at most once per scope;
* an array name needs a subscript; a scalar must not have one;
* a subscript must be of integer type and, when constant, within bounds;
* the condition of `agar` / `jabtak` must be a comparison (type `bool`);
  there is no "non-zero means true" rule;
* `nikal` may only appear inside a `jabtak` loop;
* `%` needs integer operands; division by a literal zero is an error;
* an assignment must be type-compatible, with a warning on a narrowing,
  truncating or signedness-changing conversion;
* an integer literal has the adaptive type `intlit`: it takes the type of
  whatever it is combined with, so `uint16 n medalo 40;` is silent, while a
  literal that does not fit (`char c medalo 70000;`) is an error.

Usual arithmetic conversion: if either operand is `real` the result is
`real`; otherwise the wider type wins, with `char` widening to `int16`
before it takes part in arithmetic.

---

## 3. Data Structures

### 3.1 Summary

| Structure | Where | Python shape | Used by |
|---|---|---|---|
| `Token` | `citu/tokens.py` | class with `__slots__` | lexer → parser |
| Token list | `citu/lexer.py` | `list[Token]` | parser |
| Keyword table | `citu/tokens.py` | `dict[str, str]` | lexer |
| `ParseNode` | `citu/parser.py` | n-ary tree | the `.pt` file |
| `Node` (AST) | `citu/ast_nodes.py` | class hierarchy | all later phases |
| `Symbol` | `citu/symtab.py` | class with `__slots__` | semantic, codegen |
| `Scope` | `citu/symtab.py` | `dict[str, Symbol]` | semantic |
| `SymbolTable` | `citu/symtab.py` | stack of `Scope` | semantic |
| `Quad` | `citu/tac.py` | 4-field record | codegen, optimiser, VM |
| Operand classes | `citu/tac.py` | `Const`/`Name`/`Temp`/`Label` | codegen, optimiser, VM |
| Basic blocks | `citu/optimizer.py` | `list[(start, end)]` | optimiser |
| `Diagnostic` | `citu/errors.py` | class | every phase |
| VM memory | `citu/vm.py` | `dict[str, value \| list]` | interpreter |

### 3.2 Token and the token list

```python
class Token:
    __slots__ = ("type", "lexeme", "value", "line", "col", "index")
```

| Field | Meaning |
|---|---|
| `type` | grammar terminal name — `JABTAK`, `ID`, `INTLIT`, `PLUS`, … |
| `lexeme` | the exact source text matched |
| `value` | decoded literal (`int`, `float`, `str`), else `None` |
| `line`, `col` | 1-based position of the first character |
| `index` | position in the token list |

The lexer produces a **flat Python list** of these, terminated by one `EOF`
token. A list, not a stream, because the parser is then a simple index into
it, error messages can look at neighbours, and the list can be dumped to
`.tok` and inspected. `__slots__` keeps a token to a fixed small size —
`ex3_stats.citu` alone produces 297 of them.

The **keyword table** is a plain `dict` from lexeme to token type. Keywords
are recognised by matching the identifier rule and then looking the lexeme
up, which is O(1) and avoids a 17-way alternation in the master regex.

### 3.3 Parse tree (concrete syntax tree)

```python
class ParseNode:
    __slots__ = ("symbol", "token", "kids", "production")
```

An n-ary tree that mirrors the derivation exactly: one node per grammar
symbol, interior nodes for nonterminals, leaves for terminals, carrying
their `Token`. Reading the leaves left to right reproduces the source token
stream, which is the standard way to check a parse is correct.

It is big — 614 nodes for a 142-token program — because it keeps every
chain production and every piece of punctuation. That is exactly why the
compiler does not use it after phase 2; it exists to be written to `.pt` and
inspected. The AST is what the later phases walk.

### 3.4 Abstract syntax tree

```python
class Node:
    kind      # "While", "Binary", "Index", ...
    fields    # the named children of this node kind
    line, col # source position
    ctype     # type, filled in by the semantic analyser
    sym       # resolved Symbol, for nodes that name a variable
```

18 node kinds, declared by one table-driven factory so that serialisation,
child iteration and printing are written once:

| Group | Kinds |
|---|---|
| statements | `Program`, `VarDecl`, `ArrayDecl`, `Assign`, `IndexAssign`, `If`, `While`, `Break`, `Print`, `Block` |
| expressions | `Binary`, `Unary`, `Var`, `Index`, `IntLit`, `RealLit`, `CharLit`, `StrLit` |

The AST drops punctuation and chain productions. The 614-node parse tree of
`ex1_search.citu` becomes an AST small enough to read on one screen:

```
Program
  VarDecl [type_name='int32', name='size'] : int32
    IntLit [value=8] : intlit
  ArrayDecl [type_name='int32', name='a', size=8] : int32
  ...
  While
    Binary [op='<'] : bool
      Var [name='i'] : int32
      Var [name='size'] : int32
    Block
      If
        Binary [op='='] : bool
          Index [name='a'] : int32
            Var [name='i'] : int32
          IntLit [value=0] : intlit
        Block
          Assign [name='found'] : int32
            Var [name='i'] : int32
          Break
```

Two slots are filled in later rather than at parse time: `ctype` by the
semantic analyser, and `sym` by name resolution. Code generation then needs
no lookups of its own — it reads the symbol straight off the node.

### 3.5 Symbol table

A **stack of scopes**, each scope a hash table.

```python
class Symbol:
    __slots__ = ("name", "rt_name", "sym_kind", "type_name", "length",
                 "width", "offset", "scope_level", "scope_id",
                 "line", "col", "assigned", "reads", "writes")

class Scope:
    id, level, parent, tag
    names        # dict[str, Symbol]

class SymbolTable:
    all_scopes   # every scope ever created, kept for the .sym dump
    stack        # the scopes currently open
```

| Field | Why it is there |
|---|---|
| `name` | as written in the source |
| `rt_name` | unique name used in generated code (see below) |
| `sym_kind` | `scalar` or `array` |
| `type_name` | `int32`, `real`, … |
| `length` | element count — 1 for a scalar |
| `width` | bytes = element width × length |
| `offset` | byte offset inside the frame, assigned at declaration |
| `scope_level`, `scope_id` | where it was declared |
| `line`, `col` | for error messages |
| `assigned` | has it ever been written? drives the read-before-write warning |
| `reads`, `writes` | drive the unused-variable warnings |

**Operations.** `push` / `pop` on entering and leaving a `shuro … khatam`
block; `declare` inserts into the innermost scope only (so redeclaration in
the same scope is an error but shadowing an outer name is allowed);
`lookup` walks the stack innermost-first, which is what gives shadowing its
meaning.

**Why popped scopes are kept.** `all_scopes` holds every scope ever
created. A scope that has been popped is no longer visible to `lookup`, but
it is still needed to write the complete `.sym` file and to emit storage for
every variable in the program. `ex3_stats.citu` has 9 symbols spread over 10
scopes.

**Why `rt_name` exists.** Two different blocks may each declare a `d`. They
are different variables and must not share storage, but both are spelled
`d`. Each symbol therefore gets a unique run-time name: the plain name when
it is unambiguous, otherwise `name#<scope id>`. Generated code uses
`rt_name`, which keeps the common case readable and the shadowing case
correct.

### 3.6 Three-address code

```python
class Quad:
    __slots__ = ("op", "arg1", "arg2", "result", "line")
```

A **flat Python list** of quadruples. Flat, not a tree, because the
optimiser needs to scan neighbours and the interpreter needs to jump to an
index.

Operands are small typed objects, not strings, so that later phases can tell
a constant from a variable from a temporary without re-parsing text:

| Class | Holds | Printed as |
|---|---|---|
| `Const` | `value`, `ctype` | `5`, `2.5`, `'A'`, `"text"` |
| `Name` | `name`, `ctype` | `size`, `d#3` |
| `Temp` | `n`, `ctype` | `t0`, `t1` |
| `Label` | `name` | `Ltop0`, `Lend1` |

Each carries its own `ctype`, which is how the generator knows where to
insert a `cast` and how the interpreter knows how wide a store is.

The 22 opcodes:

| Group | Opcodes |
|---|---|
| storage | `alloc` |
| move | `assign`, `cast` |
| arithmetic | `add`, `sub`, `mul`, `div`, `mod`, `neg` |
| comparison | `lt`, `le`, `gt`, `ge`, `eq`, `ne` |
| logical | `not` |
| arrays | `aload`, `astore` |
| control | `label`, `goto`, `iffalse`, `iftrue` |
| output | `print`, `printstr`, `newline` |
| end | `halt` |

Counters `_temp` and `_label` hand out fresh `t0, t1, …` and `L0, L1, …`.
A stack `_break_stack` holds the exit label of each enclosing `jabtak`, so
`nikal` compiles to a `goto` to the top of that stack — which is also how
the compiler knows `nikal` outside a loop has nowhere to go.

Temporaries are **single-assignment by construction**: each one is created
by exactly one `new_temp` call and written exactly once. That is what makes
dead-temporary elimination safe without a full liveness analysis.

### 3.7 Basic blocks

For the propagation passes the instruction list is cut into **basic
blocks** — maximal runs with one entry and one exit, represented as a list
of `(start, end)` index pairs. Leaders are the first instruction, every
`label`, and every instruction after a `goto` / `iffalse` / `iftrue` /
`halt`. Inside one block the order of execution is known exactly, so
substituting a constant or a copy is safe; across a block boundary it is
not, and the optimiser resets its knowledge.

The optimiser also keeps two small lookup tables, `read_slots(q)` and
`defined(q)`, which say for each opcode which fields are read and which
single field is written. Getting these right is what makes every pass safe:
for example `astore`'s `result` is the array being **read** as a base
address, not a destination.

### 3.8 Diagnostics

```python
class Diagnostic:
    severity   # "error" | "warning"
    phase      # "lexical" | "syntax" | "semantic" | "runtime"
    line, col, message, lexeme
```

A single `DiagnosticBag` is threaded through every phase, so one
compilation reports lexical, syntax and semantic problems together, sorted
by position.

### 3.9 Interpreter memory

| Structure | Shape | Holds |
|---|---|---|
| `mem` | `dict[str, value \| list]` | variables; an array is a Python list |
| `types` | `dict[str, str]` | declared type of each variable |
| `temps` | `dict[int, value]` | temporaries |
| `labels` | `dict[str, int]` | label name → instruction index |

`labels` is built in one pass before execution, so a `goto` is a dictionary
lookup rather than a search. Every store goes through `runtime.wrap()`, so
an `int16` really does wrap at 32767.

---

## 4. Intermediate File Format

Every phase writes its result to its own file in the output directory
(`build/` by default). The formats are all **plain UTF-8 text**, so they can
be read, diffed and graded without a tool.

Shared conventions:

* a line starting with `#` is a header or a comment;
* the first line is always a format tag and version, e.g. `# citu-tokens v1`;
* data lines use `|` as the field separator;
* positions are `line:col`, both 1-based.

| Phase | File | Format | Purpose |
|---|---|---|---|
| 1. lexical | `.tok` | pipe-separated table | the token stream |
| 2. syntax | `.pt` | indented text | concrete parse tree |
| 2. syntax | `.ast.json` | JSON | abstract syntax tree |
| 3. semantic | `.sym` | sectioned table | symbol table, one section per scope |
| 3. semantic | `.tast.json` | JSON | AST annotated with types |
| 4. codegen | `.tac` | quadruple table | three-address code |
| 5. optimise | `.opt.tac` | quadruple table + summary | optimised code |
| 6. run | `.out` | plain text | program output |
| all | `.diag` | aligned text | errors and warnings |

### 4.1 `.tok` — token stream

```
# citu-tokens v1
# source: examples/ex1_search.citu
# fields: INDEX | LINE | COL | TOKEN_TYPE | CATEGORY | LEXEME | VALUE
#------------------------------------------------------------------------------
0     | 15   | 1   | INT32      | TYPE_KEYWORD   | int32        | -
1     | 15   | 7   | ID         | IDENTIFIER     | size         | -
2     | 15   | 12  | MEDALO     | KEYWORD        | medalo       | -
3     | 15   | 19  | INTLIT     | INT_LITERAL    | 8            | 8
4     | 15   | 20  | SEMI       | PUNCTUATOR     | ;            | -
#------------------------------------------------------------------------------
# total tokens: 142 (including EOF)
# lexical errors: 0
```

Seven fields. `TOKEN_TYPE` is the grammar terminal the parser consumes;
`CATEGORY` is the broad lexical class (`KEYWORD`, `TYPE_KEYWORD`,
`IDENTIFIER`, `INT_LITERAL`, `REAL_LITERAL`, `CHAR_LITERAL`,
`STRING_LITERAL`, `OPERATOR`, `PUNCTUATOR`, `EOF`). `VALUE` is the decoded
literal, or `-` when the token has none. The listing always ends with an
`EOF` token and a two-line summary.

### 4.2 `.pt` — concrete parse tree

```
# citu-parse-tree v1
# source: examples/ex1_search.citu
# nodes: 614
# notation: one node per line, depth shown by '|  '; leaves carry their lexeme
#----------------------------------------------------------------------
Program
|  StmtList
|  |  Stmt
|  |  |  Decl
|  |  |  |  Type
|  |  |  |  |  INT32  "int32"
|  |  |  |  ID  "size"
|  |  |  |  DeclTail
|  |  |  |  |  MEDALO  "medalo"
|  |  |  |  |  Expr
|  |  |  |  |  |  OrExpr
```

One node per line. Depth is three characters (`|  `) per level. A
nonterminal is just its name; a terminal is its token type followed by its
lexeme in double quotes. Reading the quoted lexemes top to bottom gives
back the source token stream.

### 4.3 `.ast.json` — abstract syntax tree

```json
{
  "format": "citu-ast",
  "version": 1,
  "source": "examples/ex1_search.citu",
  "tree": {
    "kind": "Program",
    "line": 1,
    "col": 1,
    "stmts": [
      {
        "kind": "VarDecl",
        "line": 15,
        "col": 1,
        "type_name": "int32",
        "name": "size",
        "init": { "kind": "IntLit", "line": 15, "col": 19, "value": 8 }
      },
      {
        "kind": "ArrayDecl",
        "line": 16, "col": 1,
        "type_name": "int32", "name": "a", "size": 8
      }
    ]
  }
}
```

Every node object has `kind`, `line` and `col`, then one key per field of
that node kind. Child nodes are nested objects; a list of children is a
JSON array. JSON was chosen so the tree can be re-read by another tool
without writing a parser for it.

### 4.4 `.sym` — symbol table

```
# citu-symbol-table v1
# source: examples/ex1_search.citu
# scopes: 5   symbols: 4   frame size: 44 bytes
# fields: NAME | RT_NAME | KIND | TYPE | LEN | WIDTH | OFFSET | LINE:COL | READS | WRITES

[scope 0] level=0 parent=- tag=global
----------------------------------------------------------------------------------
  size       | size         | scalar | int32  | 1   | 4     | 0      |   15:1   | 1     | 1
  a          | a            | array  | int32  | 8   | 32    | 4      |   16:1   | 1     | 8
  i          | i            | scalar | int32  | 1   | 4     | 36     |   27:1   | 5     | 2
  found      | found        | scalar | int32  | 1   | 4     | 40     |   28:1   | 2     | 2

[scope 1] level=1 parent=0 tag=block@30:21
----------------------------------------------------------------------------------
  (empty)
```

One section per scope, in creation order. The section header gives the
scope id, its nesting level, its parent's id, and a tag (`global`, or
`block@line:col`). Offsets accumulate across the whole program, so the
header's frame size is the total storage the program needs — 44 bytes here:
one `int32` (4) + an eight-element `int32` array (32) + two more `int32` (8).

### 4.5 `.tac` and `.opt.tac` — three-address code

```
# citu-tac v1
# source: examples/ex1_search.citu
# instructions: 45   temporaries: 8   labels: 5
# fields: INDEX | OP | ARG1 | ARG2 | RESULT   ; readable form
#--------------------------------------------------------------------------------------
0000 | alloc    | int32        | 1            | size       ; alloc int32 size[1]
0001 | alloc    | int32        | 8            | a          ; alloc int32 a[8]
0004 | assign   | 8            | -            | size       ; size = 8
0005 | astore   | 0            | 14           | a          ; a[0] = 14
0014 | neg      | 1            | -            | t0         ; t0 = -1
...
0020 | lt       | i            | size         | t1         ; t1 = i < size
0021 | iffalse  | t1           | Lend1        | -          ; ifFalse t1 goto Lend1
0022 | aload    | a            | i            | t2         ; t2 = a[i]
0023 | eq       | t2           | 0            | t3         ; t3 = t2 == 0
#--------------------------------------------------------------------------------------
```

Each line carries the quadruple **and** its readable rendering, after the
`;`. The quadruple is the real data — four fixed fields, which is what an
optimiser or a code generator reads — while the text after the `;` is for a
human. A missing operand is `-`.

The index in column 1 is the jump target: `goto Lend1` transfers to the
`label Lend1` instruction, and the interpreter resolves the label to its
index once before it starts.

`.opt.tac` uses exactly the same format, tagged `# citu-tac-optimised v1`,
with a summary appended:

```
# optimisation summary
#   instructions before : 45
#   instructions after  : 43
#   algebraic_simplification  : 0
#   constant_folding          : 2
#   constant_propagation      : 2
#   copy_propagation          : 0
#   dead_temporaries_removed  : 2
#   jumps_removed             : 0
#   labels_removed            : 0
#   unreachable_removed       : 0
```

Because both files are in one format, the effect of the optimiser is a
plain `diff` of the two.

### 4.6 `.out` — program output

```
# citu-program-output v1
# source: examples/ex1_search.citu
# instructions executed: 66
#--------------------------------------------------
first zero is at index 3
elements inspected: 4
```

Header lines start with `#`; everything after the rule is exactly what the
program printed. `run_tests.py` compares this against the expected output
for the unoptimised and the optimised code and requires them to be
identical.

### 4.7 `.diag` — diagnostics

```
# citu-diagnostics v1
# errors: 14   warnings: 5
# fields: SEVERITY PHASE LINE:COL MESSAGE
#----------------------------------------------------------------------
error    semantic 13:1    'x' is already declared in this scope (first declared at line 12)
error    semantic 15:16   literal 70000 does not fit in char (range -128..127)
error    lexical  32:18   illegal character  (near '@')
error    syntax   32:20   expected ';' but found '4'  (near '4')
```

Fixed-width columns, sorted by source position, naming the phase that
raised each message. Written on every run, including a successful one.

---

## 5. Git Repository

| | |
|---|---|
| **Student ID** | **BSCS23029** |
| **Repository URL** | `https://github.com/<your-username>/citu-compiler` |
| **Commit** | *(filled in after pushing — `git rev-parse HEAD`)* |

### Access for the instructor and TA

The repository must be shared with:

* `umarsuleman@gmail.com`
* `mscs24052@itu.edu.pk`

On GitHub: **Settings → Collaborators → Add people**, then add each address
and send the invitation.

### Publishing checklist

```bash
git init
git add .
git commit -m "Citu language compiler: lexer, parser, semantic analysis, TAC, optimiser"
```

```bash
git remote add origin https://github.com/<your-username>/citu-compiler.git
```

```bash
git branch -M main && git push -u origin main
```

Then report the commit hash and the URL:

```bash
git rev-parse HEAD
```

### Repository layout

```
citu-compiler/
├── cituc.py                 compiler driver
├── run_tests.py             self-check (26 checks)
├── citu/                    the compiler
│   ├── tokens.py            token classes, keyword table
│   ├── lexer.py             phase 1
│   ├── grammar.py           grammar, FIRST/FOLLOW, LL(1) table
│   ├── parser.py            phase 2
│   ├── ast_nodes.py         AST node classes
│   ├── symtab.py            symbol table and types
│   ├── semantic.py          phase 3
│   ├── tac.py               phase 4
│   ├── optimizer.py         phase 5
│   ├── vm.py                phase 6
│   ├── runtime.py           shared value semantics
│   └── errors.py            diagnostics
├── examples/
│   ├── ex1_search.citu      linear search
│   ├── ex2_primes.citu      primes below a limit
│   ├── ex3_stats.citu       min / max / mean
│   └── ex4_errors.citu      deliberately broken
├── doc/
│   ├── Citu_Compiler_Documentation.md     this document
│   └── grammar_report.txt                 generated grammar appendix
└── build/                   generated intermediate files
```

---

## Appendix — verification

```
$ python run_tests.py

1. grammar
  PASS  grammar is LL(1) (223 cells filled)

2-4. example programs
  PASS  ex1_search.citu compiles without errors
  PASS  ex1_search.citu compiles without warnings
  PASS  ex1_search.citu produces the expected output
  PASS  ex1_search.citu optimised output is identical (45 -> 43 quads)
  PASS  ex2_primes.citu compiles without errors
  PASS  ex2_primes.citu compiles without warnings
  PASS  ex2_primes.citu produces the expected output
  PASS  ex2_primes.citu optimised output is identical (60 -> 60 quads)
  PASS  ex3_stats.citu compiles without errors
  PASS  ex3_stats.citu compiles without warnings
  PASS  ex3_stats.citu produces the expected output
  PASS  ex3_stats.citu optimised output is identical (108 -> 105 quads)

5. error reporting
  PASS  ex4_errors.citu is rejected
  PASS  reports: already declared
  PASS  reports: does not fit in char
  PASS  reports: is outside 'arr'
  PASS  reports: must be a comparison
  PASS  reports: 'y' is not declared
  PASS  reports: only allowed inside a 'jabtak' loop
  PASS  reports: division by zero
  PASS  reports: needs a subscript
  PASS  reports: needs integer operands
  PASS  reports: illegal character
  PASS  reports: expected an expression
  PASS  reports: unterminated string literal

26 passed, 0 failed
```
