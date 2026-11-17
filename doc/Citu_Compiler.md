# Citu Language and Compiler

Student ID: BSCS23029

Repository: https://github.com/Afraz1a/compiler-project

Citu is a small language whose keywords are Urdu words. The compiler is
written in Python and is run like this:

```
python cituc.py examples/search.citu
```

It has four parts, and each part writes one file into the build folder.

```
citu/lexer.py      lexical analysis      name.tokens
citu/parser.py     syntax analysis       name.tree
citu/semantic.py   semantic analysis     name.symbols
citu/codegen.py    code generation       name.tac
```

The keywords are:

```
shuro     {                melado    assignment
khatam    }                dikhao    print
agar      if               aur       and
wagarna   else             ya        or
jabtak    while            nahi      not
nikal     break
```

Assignment is the word `melado`, so `=` is used for the equality test.

The types are `char`, `int16`, `uint16`, `int32`, `uint32` and `real`.
`float` means the same as `real`. Arrays of one dimension are allowed.

---

## 1. Example Programs

### 1.1 search.citu

Finds the first zero in an array. Uses an array, a `jabtak` loop,
`agar` and `wagarna`, and `nikal` to leave the loop early.

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

The first zero is at index 3.

### 1.2 primes.citu

Prints the prime numbers below 40. Uses nested `jabtak` loops, the `%`
operator, `nikal` in the inner loop, `aur` and `nahi`, and the unsigned
types. `d` and `prime` are declared inside the loop body, so they belong
to that block.

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

There are 12 primes below 40 and their sum is 197.

### 1.3 average.citu

Finds the lowest, highest and mean of ten marks and gives a grade. Uses
every type, mixed arithmetic, real division, a character constant, `ya`,
and `agar` with `wagarna` used as a chain.

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

The lowest is 33, the highest is 95, the sum is 689, the mean is 68.9,
8 of 10 passed and the grade is C.

---

## 2. Citu Grammar

### 2.1 Lexical rules

There is one regular expression for each kind of token. They are joined
into one big expression and matched at the current position. Python
returns the first one that matches, so the order below is the order in
the code.

```
newline       \n
space         [ \t\r]+
comment       //[^\n]*        or   /\*[\s\S]*?\*/
real          \d+\.\d*        or   \.\d+
number        \d+
character     '(?:\\.|[^'\\\n])'
string        "(?:\\.|[^"\\\n])*"
identifier    [A-Za-z_][A-Za-z0-9_]*
symbol        <=|>=|!=|[-+*/%<>=()\[\];,]
unknown       .
```

The order matters. Comment comes before symbol, otherwise `/*` is read
as `/` and `*`. Real comes before number, otherwise `3.14` is read as
`3`, `.` and `14`. Character and string come before identifier.
`<=`, `>=` and `!=` come before `<`, `>` and `=`. The rule `unknown`
is last, so an illegal character is reported and the scanner still moves
forward.

Keywords have no rule of their own. They match the identifier rule and
are then looked up in a table, so `integer` is not read as `int` and
`eger`.

The token names are:

```
SHURO KHATAM AGAR WAGARNA JABTAK NIKAL MELADO DIKHAO AUR YA NAHI
INT16 INT32 UINT16 UINT32 REAL FLOAT CHAR
IDENTIFIER NUMBER REALNUM CHARACTER STRING
LE GE NE LT GT EQ PLUS MINUS STAR SLASH PERCENT
LPAREN RPAREN LBRACK RBRACK SEMI COMMA
EOF
```

That is 40 terminals.

### 2.2 Syntax rules

There are 69 productions and 31 nonterminals. The start symbol is
`program` and `λ` is the empty string. There is no left recursion, and
no two choices of the same nonterminal start with the same token.

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

One token is enough to choose a statement: a type keyword begins a
declaration, `id` begins an assignment, and `agar`, `jabtak`, `nikal`
and `dikhao` begin one each. A declaration and an assignment both carry
on with `id`, so the common part is left factored into `decltail` and
`asgtail`.

Precedence is one nonterminal per level, lowest first:
`ya`, then `aur`, then the relational operators, then `+ -`, then
`* / %`, then unary, then primary. Each level uses the `...tail` form so
there is no left recursion, and the parser writes each tail as a loop so
`+ - * / %` stay left-associative.

`comptail` does not call itself, so relational operators cannot chain
and `a < b < c` is a syntax error. The body of `agar` and `jabtak` is
always a `block`, so there is no dangling else problem.

### 2.3 FIRST and FOLLOW

`S` is the set of tokens that can start a statement, that is
`int16 int32 uint16 uint32 real float char id agar jabtak nikal dikhao`.

```
program       FIRST  S λ                              FOLLOW  $
statements    FIRST  S λ                              FOLLOW  $ khatam
statement     FIRST  S                                FOLLOW  S khatam $
declaration   FIRST  type keywords                    FOLLOW  S khatam $
decltail      FIRST  [ melado ;                       FOLLOW  S khatam $
type          FIRST  the 7 type keywords              FOLLOW  id
assignment    FIRST  id                               FOLLOW  S khatam $
asgtail       FIRST  [ melado                         FOLLOW  S khatam $
ifpart        FIRST  agar                             FOLLOW  S khatam $
elsepart      FIRST  wagarna λ                        FOLLOW  S khatam $
whilepart     FIRST  jabtak                           FOLLOW  S khatam $
breakpart     FIRST  nikal                            FOLLOW  S khatam $
printpart     FIRST  dikhao                           FOLLOW  S khatam $
block         FIRST  shuro                            FOLLOW  S khatam wagarna $
arglist       FIRST  string id num realnum char ( - nahi   FOLLOW  )
argtail       FIRST  , λ                              FOLLOW  )
arg           FIRST  string id num realnum char ( - nahi   FOLLOW  ) ,
expression    FIRST  id num realnum char ( - nahi     FOLLOW  ) , ; ]
ortail        FIRST  ya λ                             FOLLOW  ) , ; ]
andpart       FIRST  id num realnum char ( - nahi     FOLLOW  ) , ; ] ya
andtail       FIRST  aur λ                            FOLLOW  ) , ; ] ya
compare       FIRST  id num realnum char ( - nahi     FOLLOW  ) , ; ] aur ya
comptail      FIRST  = != < <= > >= λ                 FOLLOW  ) , ; ] aur ya
relop         FIRST  = != < <= > >=                   FOLLOW  id num realnum char ( - nahi
sum           FIRST  id num realnum char ( - nahi     FOLLOW  relops ) , ; ] aur ya
sumtail       FIRST  + - λ                            FOLLOW  relops ) , ; ] aur ya
term          FIRST  id num realnum char ( - nahi     FOLLOW  + - relops ) , ; ] aur ya
termtail      FIRST  * / % λ                          FOLLOW  + - relops ) , ; ] aur ya
unary         FIRST  id num realnum char ( - nahi     FOLLOW  * / % + - relops ) , ; ] aur ya
primary       FIRST  id num realnum char (            FOLLOW  * / % + - relops ) , ; ] aur ya
primtail      FIRST  [ λ                              FOLLOW  * / % + - relops ) , ; ] aur ya
```

### 2.4 The parsing table

For `A → α` the table gets `M[A,a] = A → α` for every `a` in FIRST(α),
and if `λ` is in FIRST(α) then also for every `a` in FOLLOW(A). A blank
cell is an error.

Doing this for all 69 productions fills 222 cells and no cell gets two
productions, so the grammar is LL(1). The parser is written as recursive
descent with one function per nonterminal, which makes the same choice
the table would make, with one token of lookahead and no backtracking.

---

## 3. Data Structures

**Token.** One object per token, holding the token name, the exact text,
the value behind a literal, and the line and column. The line and column
are the reason the later parts can still report an error on the right
line after the source text is gone.

**Token list.** A plain list of tokens ending with `EOF`. A list and not
a stream, so the parser is only an index into it.

**Keyword table.** A dictionary from the word to its token name, used to
turn an identifier into a keyword.

**Tree node.** One object per node, holding its kind, its line, its type,
the symbol it refers to, and its children under their own names such as
`test`, `yes`, `no`, `left` and `right`. There are 19 kinds: Program,
Declare, Array, Set, SetItem, If, While, Break, Print, Block, Binary,
Negate, Not, Name, Item, Number, RealNumber, Character and Text.

The tree is abstract, so brackets, semicolons and the chain productions
are not in it. `i + 1` is one Binary node with two children. The whole of
search.citu is 62 nodes.

The type and the symbol start empty and are filled in by the semantic
part, so the code generator does not have to look anything up.

**Scope stack.** A list of dictionaries. Entering a `shuro ... khatam`
block pushes an empty dictionary and leaving it pops one. A lookup walks
the list from the back, so an inner declaration hides an outer one of the
same name. A declaration only looks in the last dictionary, so declaring
the same name twice in one block is an error but shadowing is allowed.

**Symbol table.** A list of every symbol that was ever declared. Popping
a scope hides it from lookup but does not remove it from this list, which
is what gets written to the symbol file and what the code generator walks
to reserve storage. Each symbol holds its name, the name used in the
generated code, whether it is a plain variable or an array, its type, its
number of elements, its byte offset, its scope and its line.

The second name is needed because two different blocks can both declare a
`d`. They are different variables and must not share storage, so the
second one is called `d_2`.

**Quadruple list.** The three address code, a flat list where each entry
is four strings: the operation, two arguments and a result. Flat and not
a tree, because the position in the list is the jump target. A missing
argument is written `-`. Temporaries are `t0`, `t1` and so on, and labels
are `L0`, `L1` and so on. The operations are:

```
alloc copy
add sub mul div mod neg
eq ne lt le gt ge
not
load store
label goto iffalse iftrue
write line
stop
```

The generator also keeps a list of the exit labels of the loops it is
inside. `jabtak` pushes its exit label before the body and pops it after,
so `nikal` is a `goto` to the last one. It is also how the compiler knows
that a `nikal` outside any loop has nowhere to jump.

**Error list.** One list of line, column, part and message, filled by all
the parts, so one run reports every problem instead of only the first.

---

## 4. Intermediate File Format

Every part writes one file into the build folder. All four are plain
text with the same shape: a heading line with the column names, a line of
dashes, the rows, another line of dashes, and a total. The fields are
separated by a space, a comma and a space.

### 4.1 name.tokens

```
LINE , COL , TOKEN TYPE , LEXEME
-----------------------------------
1 , 1 , TYPE , int32
1 , 7 , IDENTIFIER , size
1 , 12 , KEYWORD , melado
1 , 19 , NUMBER , 8
1 , 20 , PUNCTUATOR , ;
-----------------------------------
total tokens = 133
```

The token type is the category, which is one of TYPE, KEYWORD,
IDENTIFIER, NUMBER, REAL_NUMBER, CHARACTER, STRING, OPERATOR,
PUNCTUATOR and EOF. The last token is always EOF.

### 4.2 name.tree

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

One node per line with four spaces for each level. A node shows its kind,
then the plain values it carries, then a colon and its type once the
semantic part has filled it in. The indentation is the only structure:
anything printed deeper than a node is a child of it.

### 4.3 name.symbols

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

In declaration order, so the offsets go upwards down the page. The scope
is 0 for the program itself and 1, 2 and so on inside blocks. The width
is the width of one element times the length.

### 4.4 name.tac

```
INDEX , OP , ARG1 , ARG2 , RESULT
-----------------------------------
0 , alloc , int32 , 1 , size
1 , alloc , int32 , 8 , a
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

The index is the jump target, so `goto L1` goes to the line that holds
`label , L1`. The `alloc` lines come first, one for each symbol, so the
file is complete on its own.

Reading lines 16 to 21: `L0` is the top of the loop, `t1` is `i < size`,
if that is false jump out of the loop to `L1`, otherwise load `a[i]` into
`t2`, compare it with 0 into `t3`, and if that is false skip the body of
the `agar` to `L2`.

If any part reports an error, no `.tac` file is written.

---

## 5. Git Repository

Student ID: BSCS23029

Repository: https://github.com/Afraz1a/compiler-project

Shared with umarsuleman@gmail.com and mscs24052@itu.edu.pk.

```
compiler-project/
    cituc.py
    citu/lexer.py
    citu/parser.py
    citu/semantic.py
    citu/codegen.py
    examples/search.citu
    examples/primes.citu
    examples/average.citu
    doc/Citu_Compiler.md
    doc/Citu_Compiler.pdf
    build/
```
