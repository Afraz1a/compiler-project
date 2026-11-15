# citu-tac-optimised v1
# source: examples/ex2_primes.citu
# instructions: 60   temporaries: 14   labels: 7
# fields: INDEX | OP | ARG1 | ARG2 | RESULT   ; readable form
#--------------------------------------------------------------------------------------
0000 | alloc    | uint16       | 1            | limit      ; alloc uint16 limit[1]
0001 | alloc    | uint16       | 1            | n          ; alloc uint16 n[1]
0002 | alloc    | uint16       | 1            | count      ; alloc uint16 count[1]
0003 | alloc    | uint32       | 1            | total      ; alloc uint32 total[1]
0004 | alloc    | uint16       | 1            | d          ; alloc uint16 d[1]
0005 | alloc    | int16        | 1            | prime      ; alloc int16 prime[1]
0006 | assign   | 40           | -            | limit      ; limit = 40
0007 | assign   | 2            | -            | n          ; n = 2
0008 | assign   | 0            | -            | count      ; count = 0
0009 | assign   | 0            | -            | total      ; total = 0
0010 | label    | Ltop0        | -            | -          ; Ltop0:
0011 | lt       | n            | limit        | t0         ; t0 = n < limit
0012 | iffalse  | t0           | Lend1        | -          ; ifFalse t0 goto Lend1
0013 | assign   | 2            | -            | d          ; d = 2
0014 | assign   | 1            | -            | prime      ; prime = 1
0015 | label    | Ltop2        | -            | -          ; Ltop2:
0016 | mul      | d            | d            | t1         ; t1 = d * d
0017 | le       | t1           | n            | t2         ; t2 = t1 <= n
0018 | iffalse  | t2           | Lend3        | -          ; ifFalse t2 goto Lend3
0019 | mod      | n            | d            | t3         ; t3 = n % d
0020 | eq       | t3           | 0            | t4         ; t4 = t3 == 0
0021 | iffalse  | t4           | Lend4        | -          ; ifFalse t4 goto Lend4
0022 | assign   | 0            | -            | prime      ; prime = 0
0023 | goto     | Lend3        | -            | -          ; goto Lend3
0024 | label    | Lend4        | -            | -          ; Lend4:
0025 | add      | d            | 1            | t5         ; t5 = d + 1
0026 | assign   | t5           | -            | d          ; d = t5
0027 | goto     | Ltop2        | -            | -          ; goto Ltop2
0028 | label    | Lend3        | -            | -          ; Lend3:
0029 | assign   | 0            | -            | t6         ; t6 = 0
0030 | eq       | prime        | 1            | t7         ; t7 = prime == 1
0031 | iffalse  | t7           | Lsc5         | -          ; ifFalse t7 goto Lsc5
0032 | eq       | n            | 1            | t8         ; t8 = n == 1
0033 | not      | t8           | -            | t9         ; t9 = not t8
0034 | iffalse  | t9           | Lsc5         | -          ; ifFalse t9 goto Lsc5
0035 | assign   | 1            | -            | t6         ; t6 = 1
0036 | label    | Lsc5         | -            | -          ; Lsc5:
0037 | iffalse  | t6           | Lend6        | -          ; ifFalse t6 goto Lend6
0038 | print    | n            | -            | -          ; print n
0039 | printstr | " is prime"  | -            | -          ; print " is prime"
0040 | newline  | -            | -            | -          ; newline
0041 | add      | count        | 1            | t10        ; t10 = count + 1
0042 | assign   | t10          | -            | count      ; count = t10
0043 | cast     | n            | uint32       | t11        ; t11 = (uint32) n
0044 | add      | total        | t11          | t12        ; t12 = total + t11
0045 | assign   | t12          | -            | total      ; total = t12
0046 | label    | Lend6        | -            | -          ; Lend6:
0047 | add      | n            | 1            | t13        ; t13 = n + 1
0048 | assign   | t13          | -            | n          ; n = t13
0049 | goto     | Ltop0        | -            | -          ; goto Ltop0
0050 | label    | Lend1        | -            | -          ; Lend1:
0051 | printstr | "primes below " | -            | -          ; print "primes below "
0052 | print    | limit        | -            | -          ; print limit
0053 | printstr | ": "         | -            | -          ; print ": "
0054 | print    | count        | -            | -          ; print count
0055 | newline  | -            | -            | -          ; newline
0056 | printstr | "their sum: " | -            | -          ; print "their sum: "
0057 | print    | total        | -            | -          ; print total
0058 | newline  | -            | -            | -          ; newline
0059 | halt     | -            | -            | -          ; halt
#--------------------------------------------------------------------------------------
# optimisation summary
#   instructions before : 60
#   instructions after  : 60
#   algebraic_simplification  : 0
#   constant_folding          : 0
#   constant_propagation      : 0
#   copy_propagation          : 0
#   dead_temporaries_removed  : 0
#   jumps_removed             : 0
#   labels_removed            : 0
#   unreachable_removed       : 0
