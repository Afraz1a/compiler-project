# citu-tac v1
# source: examples/ex1_search.citu
# instructions: 45   temporaries: 8   labels: 5
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
0014 | neg      | 1            | -            | t0         ; t0 = -1
0015 | cast     | t0           | int32        | t1         ; t1 = (int32) t0
0016 | assign   | t1           | -            | found      ; found = t1
0017 | label    | Ltop0        | -            | -          ; Ltop0:
0018 | lt       | i            | size         | t2         ; t2 = i < size
0019 | iffalse  | t2           | Lend1        | -          ; ifFalse t2 goto Lend1
0020 | aload    | a            | i            | t3         ; t3 = a[i]
0021 | eq       | t3           | 0            | t4         ; t4 = t3 == 0
0022 | iffalse  | t4           | Lend2        | -          ; ifFalse t4 goto Lend2
0023 | assign   | i            | -            | found      ; found = i
0024 | goto     | Lend1        | -            | -          ; goto Lend1
0025 | label    | Lend2        | -            | -          ; Lend2:
0026 | add      | i            | 1            | t5         ; t5 = i + 1
0027 | assign   | t5           | -            | i          ; i = t5
0028 | goto     | Ltop0        | -            | -          ; goto Ltop0
0029 | label    | Lend1        | -            | -          ; Lend1:
0030 | lt       | found        | 0            | t6         ; t6 = found < 0
0031 | iffalse  | t6           | Lelse3       | -          ; ifFalse t6 goto Lelse3
0032 | printstr | "there is no zero in the array" | -            | -          ; print "there is no zero in the array"
0033 | newline  | -            | -            | -          ; newline
0034 | goto     | Lend4        | -            | -          ; goto Lend4
0035 | label    | Lelse3       | -            | -          ; Lelse3:
0036 | printstr | "first zero is at index " | -            | -          ; print "first zero is at index "
0037 | print    | found        | -            | -          ; print found
0038 | newline  | -            | -            | -          ; newline
0039 | label    | Lend4        | -            | -          ; Lend4:
0040 | printstr | "elements inspected: " | -            | -          ; print "elements inspected: "
0041 | add      | i            | 1            | t7         ; t7 = i + 1
0042 | print    | t7           | -            | -          ; print t7
0043 | newline  | -            | -            | -          ; newline
0044 | halt     | -            | -            | -          ; halt
#--------------------------------------------------------------------------------------
