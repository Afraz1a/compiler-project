# citu-tac-optimised v1
# source: examples/ex0_board.citu
# instructions: 21   temporaries: 4   labels: 3
# fields: INDEX | OP | ARG1 | ARG2 | RESULT   ; readable form
#--------------------------------------------------------------------------------------
0000 | alloc    | int32        | 1            | SIZE       ; alloc int32 SIZE[1]
0001 | alloc    | int32        | 4            | a          ; alloc int32 a[4]
0002 | alloc    | int32        | 1            | i          ; alloc int32 i[1]
0003 | assign   | 4            | -            | SIZE       ; SIZE = 4
0004 | assign   | 0            | -            | i          ; i = 0
0005 | label    | Ltop0        | -            | -          ; Ltop0:
0006 | lt       | i            | SIZE         | t0         ; t0 = i < SIZE
0007 | iffalse  | t0           | Lend1        | -          ; ifFalse t0 goto Lend1
0008 | aload    | a            | i            | t1         ; t1 = a[i]
0009 | eq       | t1           | 0            | t2         ; t2 = t1 == 0
0010 | iffalse  | t2           | Lend2        | -          ; ifFalse t2 goto Lend2
0011 | goto     | Lend1        | -            | -          ; goto Lend1
0012 | label    | Lend2        | -            | -          ; Lend2:
0013 | add      | i            | 1            | t3         ; t3 = i + 1
0014 | assign   | t3           | -            | i          ; i = t3
0015 | goto     | Ltop0        | -            | -          ; goto Ltop0
0016 | label    | Lend1        | -            | -          ; Lend1:
0017 | printstr | "i = "       | -            | -          ; print "i = "
0018 | print    | i            | -            | -          ; print i
0019 | newline  | -            | -            | -          ; newline
0020 | halt     | -            | -            | -          ; halt
#--------------------------------------------------------------------------------------
# optimisation summary
#   instructions before : 21
#   instructions after  : 21
#   algebraic_simplification  : 0
#   constant_folding          : 0
#   constant_propagation      : 0
#   copy_propagation          : 0
#   dead_temporaries_removed  : 0
#   jumps_removed             : 0
#   labels_removed            : 0
#   unreachable_removed       : 0
