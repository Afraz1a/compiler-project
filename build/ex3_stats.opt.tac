# citu-tac-optimised v1
# source: examples/ex3_stats.citu
# instructions: 105   temporaries: 22   labels: 11
# fields: INDEX | OP | ARG1 | ARG2 | RESULT   ; readable form
#--------------------------------------------------------------------------------------
0000 | alloc    | int32        | 1            | count      ; alloc int32 count[1]
0001 | alloc    | int16        | 10           | marks      ; alloc int16 marks[10]
0002 | alloc    | int16        | 1            | lowest     ; alloc int16 lowest[1]
0003 | alloc    | int16        | 1            | highest    ; alloc int16 highest[1]
0004 | alloc    | int32        | 1            | sum        ; alloc int32 sum[1]
0005 | alloc    | int32        | 1            | passes     ; alloc int32 passes[1]
0006 | alloc    | int32        | 1            | k          ; alloc int32 k[1]
0007 | alloc    | real         | 1            | mean       ; alloc real mean[1]
0008 | alloc    | char         | 1            | grade      ; alloc char grade[1]
0009 | assign   | 10           | -            | count      ; count = 10
0010 | astore   | 0            | 72           | marks      ; marks[0] = 72
0011 | astore   | 1            | 48           | marks      ; marks[1] = 48
0012 | astore   | 2            | 91           | marks      ; marks[2] = 91
0013 | astore   | 3            | 65           | marks      ; marks[3] = 65
0014 | astore   | 4            | 33           | marks      ; marks[4] = 33
0015 | astore   | 5            | 88           | marks      ; marks[5] = 88
0016 | astore   | 6            | 57           | marks      ; marks[6] = 57
0017 | astore   | 7            | 79           | marks      ; marks[7] = 79
0018 | astore   | 8            | 95           | marks      ; marks[8] = 95
0019 | astore   | 9            | 61           | marks      ; marks[9] = 61
0020 | assign   | 32767        | -            | lowest     ; lowest = 32767
0021 | assign   | -32768       | -            | highest    ; highest = -32768
0022 | assign   | 0            | -            | sum        ; sum = 0
0023 | assign   | 0            | -            | passes     ; passes = 0
0024 | assign   | 0            | -            | k          ; k = 0
0025 | label    | Ltop0        | -            | -          ; Ltop0:
0026 | lt       | k            | count        | t2         ; t2 = k < count
0027 | iffalse  | t2           | Lend1        | -          ; ifFalse t2 goto Lend1
0028 | aload    | marks        | k            | t3         ; t3 = marks[k]
0029 | lt       | t3           | lowest       | t4         ; t4 = t3 < lowest
0030 | iffalse  | t4           | Lend2        | -          ; ifFalse t4 goto Lend2
0031 | aload    | marks        | k            | t5         ; t5 = marks[k]
0032 | assign   | t5           | -            | lowest     ; lowest = t5
0033 | label    | Lend2        | -            | -          ; Lend2:
0034 | aload    | marks        | k            | t6         ; t6 = marks[k]
0035 | gt       | t6           | highest      | t7         ; t7 = t6 > highest
0036 | iffalse  | t7           | Lend3        | -          ; ifFalse t7 goto Lend3
0037 | aload    | marks        | k            | t8         ; t8 = marks[k]
0038 | assign   | t8           | -            | highest    ; highest = t8
0039 | label    | Lend3        | -            | -          ; Lend3:
0040 | aload    | marks        | k            | t9         ; t9 = marks[k]
0041 | cast     | t9           | int32        | t10        ; t10 = (int32) t9
0042 | add      | sum          | t10          | t11        ; t11 = sum + t10
0043 | assign   | t11          | -            | sum        ; sum = t11
0044 | aload    | marks        | k            | t12        ; t12 = marks[k]
0045 | ge       | t12          | 50           | t13        ; t13 = t12 >= 50
0046 | iffalse  | t13          | Lend4        | -          ; ifFalse t13 goto Lend4
0047 | add      | passes       | 1            | t14        ; t14 = passes + 1
0048 | assign   | t14          | -            | passes     ; passes = t14
0049 | label    | Lend4        | -            | -          ; Lend4:
0050 | add      | k            | 1            | t15        ; t15 = k + 1
0051 | assign   | t15          | -            | k          ; k = t15
0052 | goto     | Ltop0        | -            | -          ; goto Ltop0
0053 | label    | Lend1        | -            | -          ; Lend1:
0054 | cast     | sum          | real         | t16        ; t16 = (real) sum
0055 | cast     | count        | real         | t18        ; t18 = (real) count
0056 | div      | t16          | t18          | t19        ; t19 = t16 / t18
0057 | assign   | t19          | -            | mean       ; mean = t19
0058 | printstr | "count   : " | -            | -          ; print "count   : "
0059 | print    | count        | -            | -          ; print count
0060 | newline  | -            | -            | -          ; newline
0061 | printstr | "lowest  : " | -            | -          ; print "lowest  : "
0062 | print    | lowest       | -            | -          ; print lowest
0063 | newline  | -            | -            | -          ; newline
0064 | printstr | "highest : " | -            | -          ; print "highest : "
0065 | print    | highest      | -            | -          ; print highest
0066 | newline  | -            | -            | -          ; newline
0067 | printstr | "sum     : " | -            | -          ; print "sum     : "
0068 | print    | sum          | -            | -          ; print sum
0069 | newline  | -            | -            | -          ; newline
0070 | printstr | "mean    : " | -            | -          ; print "mean    : "
0071 | print    | t19          | -            | -          ; print t19
0072 | newline  | -            | -            | -          ; newline
0073 | printstr | "passed  : " | -            | -          ; print "passed  : "
0074 | print    | passes       | -            | -          ; print passes
0075 | printstr | " of "       | -            | -          ; print " of "
0076 | print    | count        | -            | -          ; print count
0077 | newline  | -            | -            | -          ; newline
0078 | assign   | 'F'          | -            | grade      ; grade = 'F'
0079 | ge       | t19          | 80.0         | t20        ; t20 = t19 >= 80.0
0080 | iffalse  | t20          | Lelse5       | -          ; ifFalse t20 goto Lelse5
0081 | assign   | 'A'          | -            | grade      ; grade = 'A'
0082 | goto     | Lend6        | -            | -          ; goto Lend6
0083 | label    | Lelse5       | -            | -          ; Lelse5:
0084 | ge       | mean         | 70.0         | t21        ; t21 = mean >= 70.0
0085 | iffalse  | t21          | Lelse7       | -          ; ifFalse t21 goto Lelse7
0086 | assign   | 'B'          | -            | grade      ; grade = 'B'
0087 | goto     | Lend8        | -            | -          ; goto Lend8
0088 | label    | Lelse7       | -            | -          ; Lelse7:
0089 | assign   | 1            | -            | t22        ; t22 = 1
0090 | ge       | mean         | 60.0         | t23        ; t23 = mean >= 60.0
0091 | iftrue   | t23          | Lsc9         | -          ; if t23 goto Lsc9
0092 | ge       | mean         | 55.0         | t24        ; t24 = mean >= 55.0
0093 | iftrue   | t24          | Lsc9         | -          ; if t24 goto Lsc9
0094 | assign   | 0            | -            | t22        ; t22 = 0
0095 | label    | Lsc9         | -            | -          ; Lsc9:
0096 | iffalse  | t22          | Lend10       | -          ; ifFalse t22 goto Lend10
0097 | assign   | 'C'          | -            | grade      ; grade = 'C'
0098 | label    | Lend10       | -            | -          ; Lend10:
0099 | label    | Lend8        | -            | -          ; Lend8:
0100 | label    | Lend6        | -            | -          ; Lend6:
0101 | printstr | "grade   : " | -            | -          ; print "grade   : "
0102 | print    | grade        | -            | -          ; print grade
0103 | newline  | -            | -            | -          ; newline
0104 | halt     | -            | -            | -          ; halt
#--------------------------------------------------------------------------------------
# optimisation summary
#   instructions before : 108
#   instructions after  : 105
#   algebraic_simplification  : 1
#   constant_folding          : 2
#   constant_propagation      : 2
#   copy_propagation          : 3
#   dead_temporaries_removed  : 3
#   jumps_removed             : 0
#   labels_removed            : 0
#   unreachable_removed       : 0
