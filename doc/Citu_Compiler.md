# Citu — Language and Compiler

**Student ID:** BSCS23029
**Repository:** `https://github.com/<username>/citu-compiler`
**Commit:** see section 5

Citu is the language from the grammar assignment. Its keywords are Urdu
words. The compiler is in `citu/` and is run with:

```
python cituc.py examples/search.citu
```

Four phases, each one writes its result into `build/`:

| Phase | File | Output file |
|---|---|---|
| 1. lexical analysis | `citu/lexer.py` | `name.tokens` |
| 2. syntax analysis | `citu/parser.py` | `name.tree` |
| 3. semantic analysis | `citu/semantic.py` | `name.symbols` |
| 4. code generation | `citu/codegen.py` | `name.tac` |

| Keyword | Meaning | Keyword | Meaning |
|---|---|---|---|
| `shuro` | `{` | `melado` | assignment |
| `khatam` | `}` | `dikhao` | print |
| `agar` | `if` | `aur` | `&&` |
| `wagarna` | `else` | `ya` | `\|\|` |
| `jabtak` | `while` | `nahi` | `!` |
| `nikal` | `break` | `=` | equality test |

Assignment is the word `melado`, so `=` is free to mean equality.
Types are `char`, `int16`, `uint16`, `int32`, `uint32`, `real` (`float` is
the same type), and one-dimensional arrays of those.

---

## 1. Example Programs

### 1.1 `examples/search.citu` — linear search

Array, `jabtak`, `agar` / `wagarna`, `nikal` to leave the loop early,
unary minus. This is the loop from the grammar assignment with data and a
result added.

```
int32 size melado 8;
int32 a[8];

a[0] melado 14;
a[1] melado 7;
a[2] melado 23;
a[3] melado 0;
a[4] melado 9;
a[5] melado 0;
a[6] melado 31;
a[7] melado 5;

int32 i melado 0;
int32 found melado -1;

jabtak ( i < size ) shuro
    agar ( a[i] = 0 ) shuro
        found melado i;
        nikal;
    khatam
    i melado i + 1;
khatam

agar ( found < 0 ) shuro
    dikhao("no zero in the array");
khatam wagarna shuro
    dikhao("first zero at index ", found);
khatam
```

Finds the first zero at index 3. 133 tokens, 4 symbols, 40 instructions.

### 1.2 `examples/primes.citu` — primes below a limit

Nested `jabtak`, `%`, `nikal` leaving only the inner loop, `aur` and
`nahi`, the unsigned types, and a block scope: `d` and `prime` are
declared inside the loop body, not at the top of the program.

```
uint16 limit melado 40;
uint16 n melado 2;
uint16 count melado 0;
uint32 total melado 0;

jabtak ( n < limit ) shuro
    uint16 d melado 2;
    int16 prime melado 1;

    jabtak ( d * d <= n ) shuro
        agar ( n % d = 0 ) shuro
            prime melado 0;
            nikal;
        khatam
        d melado d + 1;
    khatam

    agar ( prime = 1 aur nahi (n = 1) ) shuro
        dikhao(n, " is prime");
        count melado count + 1;
        total melado total + n;
    khatam

    n melado n + 1;
khatam

dikhao("primes below ", limit, " = ", count);
dikhao("their sum = ", total);
```

Finds 12 primes below 40, summing to 197. 129 tokens, 6 symbols,
59 instructions.

### 1.3 `examples/average.citu` — lowest, highest and mean

Every type, mixed arithmetic with automatic widening, real division, a
character constant, `ya`, and nested `agar` / `wagarna` used as a chain.

```
int32 count melado 10;
int16 marks[10];

marks[0] melado 72;
marks[1] melado 48;
marks[2] melado 91;
marks[3] melado 65;
marks[4] melado 33;
marks[5] melado 88;
marks[6] melado 57;
marks[7] melado 79;
marks[8] melado 95;
marks[9] melado 61;

int16 lowest melado 32767;
int16 highest melado -32768;
int32 sum melado 0;
int32 passed melado 0;
int32 k melado 0;

jabtak ( k < count ) shuro
    agar ( marks[k] < lowest ) shuro
        lowest melado marks[k];
    khatam
    agar ( marks[k] > highest ) shuro
        highest melado marks[k];
    khatam
    sum melado sum + marks[k];
    agar ( marks[k] >= 50 ) shuro
        passed melado passed + 1;
    khatam
    k melado k + 1;
khatam

real mean melado sum * 1.0 / count;
char grade melado 'F';

agar ( mean >= 80.0 ) shuro
    grade melado 'A';
khatam wagarna shuro
    agar ( mean >= 70.0 ) shuro
        grade melado 'B';
    khatam wagarna shuro
        agar ( mean >= 60.0 ya mean >= 55.0 ) shuro
            grade melado 'C';
        khatam
    khatam
khatam

dikhao("lowest = ", lowest);
dikhao("highest = ", highest);
dikhao("sum = ", sum);
dikhao("mean = ", mean);
dikhao("passed = ", passed, " of ", count);
dikhao("grade = ", grade);
```

Lowest 33, highest 95, sum 689, mean 68.9, 8 of 10 passed, grade C.
290 tokens, 9 symbols, 101 instructions.

---

## 2. Citu Grammar

### 2.1 Lexical rules

One regular expression per category. They are joined into one master
expression of named groups and matched at the current position. Python
returns the **first alternative that matches**, so the order below is the
order in the code and it gives the longest match.

| Category | Regular expression | Note |
|---|---|---|
| newline | `\n` | counts lines, discarded |
| space | `[ \t\r]+` | discarded |
| comment | `//[^\n]*` or `/\*[\s\S]*?\*/` | lazy `*?` stops at the first `*/` |
| real | `\d+\.\d*` or `\.\d+` | before `number` |
| number | `\d+` | |
| character | `'(?:\\.\|[^'\\\n])'` | `'A'`, `'\n'` |
| string | `"(?:\\.\|[^"\\\n])*"` | |
| identifier | `[A-Za-z_][A-Za-z0-9_]*` | then looked up in the keyword table |
| symbol | `<=\|>=\|!=\|[-+*/%<>=()\[\];,]` | two-character ones first |
| unknown | `.` | illegal character, reported, scanning continues |

Why the order matters:

* comment before symbol, or `/*` is read as `/` then `*`
* real before number, or `3.14` is read as `3` `.` `14`
* character and string before identifier, so a literal is never split
* `<=` `>=` `!=` before `<` `>` `=`, or they split in two
* `unknown` last, so the scanner always moves forward at least one
  character and can never loop

Keywords get no regular expression of their own. They match the
identifier rule and are then re-classified by a dictionary lookup, so
`integer` is not read as `int` + `eger`.

| Lexeme | Token | Lexeme | Token | Lexeme | Token |
|---|---|---|---|---|---|
| `shuro` | SHURO | `melado` | MELADO | `int16` | INT16 |
| `khatam` | KHATAM | `dikhao` | DIKHAO | `int32` | INT32 |
| `agar` | AGAR | `aur` | AUR | `uint16` | UINT16 |
| `wagarna` | WAGARNA | `ya` | YA | `uint32` | UINT32 |
| `jabtak` | JABTAK | `nahi` | NAHI | `real` | REAL |
| `nikal` | NIKAL | | | `float` | FLOAT |
| | | | | `char` | CHAR |

| Lexeme | Token | Lexeme | Token | Lexeme | Token |
|---|---|---|---|---|---|
| `<=` | LE | `+` | PLUS | `(` | LPAREN |
| `>=` | GE | `-` | MINUS | `)` | RPAREN |
| `!=` | NE | `*` | STAR | `[` | LBRACK |
| `<` | LT | `/` | SLASH | `]` | RBRACK |
| `>` | GT | `%` | PERCENT | `;` | SEMI |
| `=` | EQ | | | `,` | COMMA |

The categories written into the token file are `TYPE`, `KEYWORD`,
`IDENTIFIER`, `NUMBER`, `REAL_NUMBER`, `CHARACTER`, `STRING`, `OPERATOR`,
`PUNCTUATOR`, `EOF`. With `EOF` there are 40 terminals.

### 2.2 Syntax rules

69 productions, 31 nonterminals, start symbol `program`, `λ` is the empty
string. No left recursion and no two alternatives of one nonterminal start
with the same token.

```
 1  program     → statements
 2  statements  → statement statements
 3  statements  → λ
 4  statement   → declaration
 5  statement   → assignment
 6  statement   → ifpart
 7  statement   → whilepart
 8  statement   → breakpart
 9  statement   → printpart

10  declaration → type id decltail
11  decltail    → [ num ] ;
12  decltail    → melado expression ;
13  decltail    → ;
14  type        → int16
15  type        → int32
16  type        → uint16
17  type        → uint32
18  type        → real
19  type        → float
20  type        → char

21  assignment  → id asgtail
22  asgtail     → [ expression ] melado expression ;
23  asgtail     → melado expression ;

24  ifpart      → agar ( expression ) block elsepart
25  elsepart    → wagarna block
26  elsepart    → λ
27  whilepart   → jabtak ( expression ) block
28  breakpart   → nikal ;

29  printpart   → dikhao ( arglist ) ;
30  arglist     → arg argtail
31  argtail     → , arg argtail
32  argtail     → λ
33  arg         → string
34  arg         → expression

35  block       → shuro statements khatam

36  expression  → andpart ortail
37  ortail      → ya andpart ortail
38  ortail      → λ
39  andpart     → compare andtail
40  andtail     → aur compare andtail
41  andtail     → λ
42  compare     → sum comptail
43  comptail    → relop sum
44  comptail    → λ
45  relop       → =
46  relop       → !=
47  relop       → <
48  relop       → <=
49  relop       → >
50  relop       → >=
51  sum         → term sumtail
52  sumtail     → + term sumtail
53  sumtail     → - term sumtail
54  sumtail     → λ
55  term        → unary termtail
56  termtail    → * unary termtail
57  termtail    → / unary termtail
58  termtail    → % unary termtail
59  termtail    → λ
60  unary       → - unary
61  unary       → nahi unary
62  unary       → primary
63  primary     → id primtail
64  primary     → num
65  primary     → realnum
66  primary     → charconst
67  primary     → ( expression )
68  primtail    → [ expression ]
69  primtail    → λ
```

Notes on the shape of the grammar:

* `statement` is chosen by one token: a type keyword begins a declaration,
  `id` an assignment, and `agar` `jabtak` `nikal` `dikhao` one each.
* `declaration` and `assignment` both continue with `id`, so the common
  part is **left factored** into `decltail` and `asgtail`.
* Precedence is one nonterminal per level, lowest first:
  `ya` < `aur` < relational < `+ -` < `* / %` < unary < primary.
* Each level uses the right-recursive `...tail` form so there is no left
  recursion. The parser writes each tail as a loop, which folds the
  result leftwards, so `+ - * / %` come out left-associative.
* `comptail` does not call itself, so relational operators do not chain:
  `a < b < c` is a syntax error instead of a wrong answer.
* The body of `agar` and `jabtak` is always a `block`, so there is no
  dangling-else problem: `elsepart` can only belong to the `agar` before it.
* An array size must be a `num`, so the storage is known at compile time.

### 2.3 FIRST and FOLLOW

`S` below stands for the statement starter set
`{int16 int32 uint16 uint32 real float char id agar jabtak nikal dikhao}`.

| Nonterminal | FIRST | FOLLOW |
|---|---|---|
| program | S, λ | `$` |
| statements | S, λ | `$ khatam` |
| statement | S | S, `khatam $` |
| declaration | type keywords | S, `khatam $` |
| decltail | `[ melado ;` | S, `khatam $` |
| type | the 7 type keywords | `id` |
| assignment | `id` | S, `khatam $` |
| asgtail | `[ melado` | S, `khatam $` |
| ifpart, whilepart, breakpart, printpart | `agar` / `jabtak` / `nikal` / `dikhao` | S, `khatam $` |
| elsepart | `wagarna`, λ | S, `khatam $` |
| block | `shuro` | S, `khatam wagarna $` |
| arglist | `string id num realnum charconst ( - nahi` | `)` |
| argtail | `,`, λ | `)` |
| arg | `string id num realnum charconst ( - nahi` | `) ,` |
| expression | `id num realnum charconst ( - nahi` | `) , ; ]` |
| ortail | `ya`, λ | `) , ; ]` |
| andpart | `id num realnum charconst ( - nahi` | `) , ; ] ya` |
| andtail | `aur`, λ | `) , ; ] ya` |
| compare | `id num realnum charconst ( - nahi` | `) , ; ] aur ya` |
| comptail | `= != < <= > >=`, λ | `) , ; ] aur ya` |
| relop | `= != < <= > >=` | `id num realnum charconst ( - nahi` |
| sum | `id num realnum charconst ( - nahi` | relops, `) , ; ] aur ya` |
| sumtail | `+ -`, λ | relops, `) , ; ] aur ya` |
| term | `id num realnum charconst ( - nahi` | `+ -`, relops, `) , ; ] aur ya` |
| termtail | `* / %`, λ | `+ -`, relops, `) , ; ] aur ya` |
| unary | `id num realnum charconst ( - nahi` | `* / % + -`, relops, `) , ; ] aur ya` |
| primary | `id num realnum charconst (` | `* / % + -`, relops, `) , ; ] aur ya` |
| primtail | `[`, λ | `* / % + -`, relops, `) , ; ] aur ya` |

### 2.4 The table is conflict free

For `A → α` the table is filled with `M[A,a] = A → α` for every
`a ∈ FIRST(α)`, and if `λ ∈ FIRST(α)` also for every `a ∈ FOLLOW(A)`.
Blank cell = error.

Doing this for all 69 productions fills **222 cells and no cell receives
two productions**, so the grammar is **LL(1)**. The three places where a
clash could have happened:

| Nonterminal | Why there is no clash |
|---|---|
| `decltail` | `[` vs `melado` vs `;` are three different tokens |
| `asgtail` | `[` vs `melado` |
| `elsepart` | FIRST = `{wagarna}`, FOLLOW does not contain `wagarna` |

Because no cell is doubled, the parser needs one token of lookahead and
never backtracks. It is written as recursive descent, one function per
nonterminal, which is the same decision the table would make.

### 2.5 Rules the grammar cannot express

Checked in `citu/semantic.py`:

* a name must be declared before it is used, and only once per scope
* an array name needs an index, a plain variable must not have one
* an index must be a whole number, and a constant index must be in range
* the condition of `agar` and `jabtak` must be a comparison, not a number
* `nikal` is only allowed inside `jabtak`
* `%` needs whole numbers, and division by the constant 0 is an error
* a value must fit the variable it is stored in, and a constant that is
  out of range for its type is an error

When two numbers of different type meet, the wider one wins; if either is
`real` the result is `real`; `char` widens to `int16` first.

---

## 3. Data Structures

| Structure | Where | Shape |
|---|---|---|
| keyword table | `lexer.py` | dictionary, lexeme → token name |
| token | `lexer.py` | object: kind, text, value, line, col |
| token list | `lexer.py` | list of tokens, ending with `EOF` |
| tree node | `parser.py` | object: kind, line, type, symbol, named parts |
| symbol | `semantic.py` | object: name, slot, kind, type, length, offset, scope, line |
| scope stack | `semantic.py` | list of dictionaries |
| symbol table | `semantic.py` | list of every symbol, in declaration order |
| quadruple | `codegen.py` | list of four strings: op, arg1, arg2, result |
| code | `codegen.py` | list of quadruples |
| error list | `cituc.py` | list of (line, col, phase, message) |

### 3.1 Token and token list

```
class Token:
    kind    token name, e.g. JABTAK, IDENTIFIER, NUMBER, PLUS
    text    the exact text matched
    value   the number or character behind a literal, else None
    line    line number
    col     column number
```

A flat list, not a stream, because the parser is then just an index into
it, and the whole list can be written out and read.

Line and column are carried on every token. That is the only reason the
later phases can report an error against the right line, since by then
the source text is gone.

### 3.2 Tree node

```
class Node:
    kind    Program, Declare, Array, Set, SetItem, If, While, Break,
            Print, Block, Binary, Negate, Not, Name, Item, Number,
            RealNumber, Character, Text
    line    source line
    type    filled in later by the semantic phase
    symbol  filled in later, the symbol this node refers to
    parts   the names of this node's children
```

19 node kinds. Parts are stored under their own names (`test`, `yes`,
`no`, `left`, `right`, `body`), so the code reads as `node.test` rather
than `node.children[0]`.

`type` and `symbol` start empty and are filled in by phase 3. That is why
the code generator does not need to look anything up: the type and the
storage slot are already sitting on the node.

The tree is abstract, not a full parse tree: brackets, semicolons and the
chain productions (`expression → andpart → compare → sum → term → unary
→ primary`) are gone, and only the structure is left. `i + 1` becomes one
`Binary` node with two children, where a full parse tree needs about
twenty. The whole of `search.citu` is 62 nodes.

### 3.3 Scope stack and symbol table

The scope stack is a **list of dictionaries**. Entering a `shuro ...
khatam` block pushes an empty dictionary, leaving it pops. `find` walks
the list from the back, so an inner declaration hides an outer one of the
same name. `declare` only looks in the last dictionary, so declaring the
same name twice in one block is an error but shadowing is allowed.

Alongside the stack there is a plain list of every symbol ever declared.
Popping a scope removes it from view but not from this list, which is
what gets written to the symbol file and what the code generator walks to
reserve storage.

```
class Symbol:
    name     as written
    slot     the name used in the generated code
    kind     scalar or array
    datatype char, int16, uint16, int32, uint32, real
    length   number of elements, 1 for a plain variable
    offset   byte offset, handed out at declaration
    scope    which scope it belongs to
    line     where it was declared
```

`slot` exists because two different blocks may both declare a `d`. They
are two different variables and must not share storage, but both are
spelled `d`, so the second one gets the slot `d_2`.

`offset` runs on across the whole program, so the last offset plus the
last width is the total storage the program needs — 44 bytes for
`search.citu`.

### 3.4 Quadruples

Three-address code is a flat list, each entry four strings:

```
[ op , arg1 , arg2 , result ]
```

Flat and not a tree, because an index into the list is a jump target.
A missing operand is written `-`. Temporaries are `t0`, `t1`, ... and
labels are `L0`, `L1`, ...; two counters hand them out.

The 24 operations:

| Group | Operations |
|---|---|
| storage | `alloc` |
| move | `copy` |
| arithmetic | `add` `sub` `mul` `div` `mod` `neg` |
| comparison | `eq` `ne` `lt` `le` `gt` `ge` |
| logic | `not` |
| array | `load` `store` |
| jumps | `label` `goto` `iffalse` `iftrue` |
| output | `write` `line` |
| end | `stop` |

The generator also keeps a small list of loop exit labels. `jabtak`
pushes its exit label before generating the body and pops it after, so
`nikal` is a `goto` to the top of that list. It is also how the compiler
knows a `nikal` outside any loop has nowhere to jump.

`aur` and `ya` do not become single instructions. They expand into
jumps so the right operand is only evaluated when it has to be.

---

## 4. Intermediate File Format

Every phase writes one file into `build/`. All four are plain text and
follow the same shape: a header line naming the columns, a line of
dashes, the rows, another line of dashes, and a total. Fields are
separated by ` , `.

| Phase | File | Contents |
|---|---|---|
| lexical analysis | `name.tokens` | one line per token |
| syntax analysis | `name.tree` | the tree, indented |
| semantic analysis | `name.symbols` | one line per symbol |
| code generation | `name.tac` | one line per quadruple |

### 4.1 `name.tokens`

`LINE , COL , TOKEN TYPE , LEXEME`

```
LINE , COL , TOKEN TYPE , LEXEME
-----------------------------------
1 , 1 , TYPE , int32
1 , 7 , IDENTIFIER , size
1 , 12 , KEYWORD , melado
1 , 19 , NUMBER , 8
1 , 20 , PUNCTUATOR , ;
2 , 1 , TYPE , int32
-----------------------------------
total tokens = 133
```

The last token is always `EOF`. Token type is the category, not the
individual token name, so the list reads the same way as the token list
of the C scanner from the first assignment.

### 4.2 `name.tree`

One node per line, four spaces per level. A node shows its kind, then
any plain values it carries, then `:` and its type once the semantic
phase has filled it in.

```
PARSE TREE
-----------------------------------
Program
    Declare int32 size
        Number 8 : number
    Array int32 a 8
    SetItem a
        Number 0 : number
        Number 14 : number
-----------------------------------
total nodes = 62
```

Indentation is the only structure: everything printed deeper than a node
is a child of it.

### 4.3 `name.symbols`

`NAME , KIND , TYPE , LENGTH , WIDTH , OFFSET , SCOPE , LINE`

```
NAME , KIND , TYPE , LENGTH , WIDTH , OFFSET , SCOPE , LINE
-------------------------------------------------------------
size , scalar , int32 , 1 , 4 , 0 , 0 , 1
a , array , int32 , 8 , 32 , 4 , 0 , 2
i , scalar , int32 , 1 , 4 , 36 , 0 , 13
found , scalar , int32 , 1 , 4 , 40 , 0 , 14
-------------------------------------------------------------
total symbols = 4
total bytes = 44
```

In declaration order, not scope order, so the offsets run upwards down
the page. `SCOPE` is 0 for the program itself and 1, 2, ... inside
blocks. `WIDTH` is the width of one element times the length.

### 4.4 `name.tac`

`INDEX , OP , ARG1 , ARG2 , RESULT`

```
INDEX , OP , ARG1 , ARG2 , RESULT
-----------------------------------
0 , alloc , int32 , 1 , size
1 , alloc , int32 , 8 , a
2 , alloc , int32 , 1 , i
3 , alloc , int32 , 1 , found
4 , copy , 8 , - , size
5 , store , 0 , 14 , a
13 , copy , 0 , - , i
14 , neg , 1 , - , t0
15 , copy , t0 , - , found
16 , label , L0 , - , -
17 , lt , i , size , t1
18 , iffalse , t1 , L1 , -
19 , load , a , i , t2
20 , eq , t2 , 0 , t3
21 , iffalse , t3 , L2 , -
-----------------------------------
total instructions = 40
```

`INDEX` is the jump target: `goto L1` goes to the line that holds
`label , L1`. The `alloc` instructions come first, one per symbol, so the
file is complete on its own and nothing else has to be read to know how
much storage the program needs.

Reading rows 16 to 21 back: `L0` is the top of the loop, `t1` is
`i < size`, if it is false jump past the loop to `L1`, otherwise load
`a[i]` into `t2`, compare it with 0 into `t3`, and if that is false skip
the body of the `agar` to `L2`.

If any phase reports an error, no `.tac` file is written.

### 4.5 Errors

Errors are collected from all phases and printed together, sorted by
line, so one run shows every problem rather than only the first:

```
errors : 9
  line 2 : semantic error : x is already declared
  line 3 : semantic error : 70000 does not fit in char
  line 5 : semantic error : index 7 is outside arr
  line 6 : semantic error : the condition of agar must be a comparison
  line 6 : semantic error : y is not declared
  line 7 : semantic error : nikal is only allowed inside jabtak
  line 8 : semantic error : division by zero
  line 9 : lexical error : illegal character @
  line 9 : syntax error : expected SEMI but found 4
```

The scanner reports an illegal character and moves on one character, and
the parser skips to the next `;` or statement keyword, so one mistake
does not hide the rest of the file.

---

## 5. Git Repository

| | |
|---|---|
| Student ID | BSCS23029 |
| Repository | `https://github.com/<username>/citu-compiler` |
| Commit | `git rev-parse HEAD` after pushing |

Shared with `umarsuleman@gmail.com` and `mscs24052@itu.edu.pk` through
Settings → Collaborators.

```
citu-compiler/
    cituc.py              driver
    citu/lexer.py         phase 1
    citu/parser.py        phase 2
    citu/semantic.py      phase 3
    citu/codegen.py       phase 4
    examples/search.citu
    examples/primes.citu
    examples/average.citu
    doc/Citu_Compiler.md  this document
    build/                the generated files
```
