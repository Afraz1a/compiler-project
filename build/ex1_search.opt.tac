# citu-tac-optimised v1
# source: examples/ex1_search.citu
# instructions: 43   temporaries: 6   labels: 5
# fields: INDEX | OP | ARG1 | ARG2 | RESULT   ; readable form
#--------------------------------------------------------------------------------------
0000 | alloc    | int32        | 1            | size       ; alloc int32 size[1]
0001 | alloc    | int32        | 8            | a          ; alloc int32 a[8]
0002 | alloc    | int32        | 1            | i          ; alloc int32 i[1]
0003 | alloc    | int32        | 1            | found      ; alloc int32 found[1]
0004 | assign   | 8            | -            | size       ; size = 8
0005 | astore   | 0            | 14           | a          ; a[0] = 14
0006 | astore   | 1            | 7            | a          ; a[1] = 7
0007 | astore   | 2            | 23           | a          ; a[2] = 23
0008 | astore   | 3            | 0            | a          ; a[3] = 0
0009 | astore   | 4            | 9            | a          ; a[4] = 9
0010 | astore   | 5            | 0            | a          ; a[5] = 0
0011 | astore   | 6            | 31           | a          ; a[6] = 31
0012 | astore   | 7            | 5            | a          ; a[7] = 5
0013 | assign   | 0            | -            | i          ; i = 0
0014 | assign   | -1           | -            | found      ; found = -1
0015 | label    | Ltop0        | -            | -          ; Ltop0:
0016 | lt       | i            | size         | t2         ; t2 = i < size
0017 | iffalse  | t2           | Lend1        | -          ; ifFalse t2 goto Lend1
0018 | aload    | a            | i            | t3         ; t3 = a[i]
0019 | eq       | t3           | 0            | t4         ; t4 = t3 == 0
0020 | iffalse  | t4           | Lend2        | -          ; ifFalse t4 goto Lend2
0021 | assign   | i            | -            | found      ; found = i
0022 | goto     | Lend1        | -            | -          ; goto Lend1
0023 | label    | Lend2        | -            | -          ; Lend2:
0024 | add      | i            | 1            | t5         ; t5 = i + 1
0025 | assign   | t5           | -            | i          ; i = t5
0026 | goto     | Ltop0        | -            | -          ; goto Ltop0
0027 | label    | Lend1        | -            | -          ; Lend1:
0028 | lt       | found        | 0            | t6         ; t6 = found < 0
0029 | iffalse  | t6           | Lelse3       | -          ; ifFalse t6 goto Lelse3
0030 | printstr | "there is no zero in the array" | -            | -          ; print "there is no zero in the array"
0031 | newline  | -            | -            | -          ; newline
0032 | goto     | Lend4        | -            | -          ; goto Lend4
0033 | label    | Lelse3       | -            | -          ; Lelse3:
0034 | printstr | "first zero is at index " | -            | -          ; print "first zero is at index "
0035 | print    | found        | -            | -          ; print found
0036 | newline  | -            | -            | -          ; newline
0037 | label    | Lend4        | -            | -          ; Lend4:
0038 | printstr | "elements inspected: " | -            | -          ; print "elements inspected: "
0039 | add      | i            | 1            | t7         ; t7 = i + 1
0040 | print    | t7           | -            | -          ; print t7
0041 | newline  | -            | -            | -          ; newline
0042 | halt     | -            | -            | -          ; halt
#--------------------------------------------------------------------------------------
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
