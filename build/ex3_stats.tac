# citu-tac v1
# source: examples/ex3_stats.citu
# instructions: 108   temporaries: 25   labels: 11
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
0021 | neg      | 32768        | -            | t0         ; t0 = -32768
0022 | cast     | t0           | int16        | t1         ; t1 = (int16) t0
0023 | assign   | t1           | -            | highest    ; highest = t1
0024 | assign   | 0            | -            | sum        ; sum = 0
0025 | assign   | 0            | -            | passes     ; passes = 0
0026 | assign   | 0            | -            | k          ; k = 0
0027 | label    | Ltop0        | -            | -          ; Ltop0:
0028 | lt       | k            | count        | t2         ; t2 = k < count
0029 | iffalse  | t2           | Lend1        | -          ; ifFalse t2 goto Lend1
0030 | aload    | marks        | k            | t3         ; t3 = marks[k]
0031 | lt       | t3           | lowest       | t4         ; t4 = t3 < lowest
0032 | iffalse  | t4           | Lend2        | -          ; ifFalse t4 goto Lend2
0033 | aload    | marks        | k            | t5         ; t5 = marks[k]
0034 | assign   | t5           | -            | lowest     ; lowest = t5
0035 | label    | Lend2        | -            | -          ; Lend2:
0036 | aload    | marks        | k            | t6         ; t6 = marks[k]
0037 | gt       | t6           | highest      | t7         ; t7 = t6 > highest
0038 | iffalse  | t7           | Lend3        | -          ; ifFalse t7 goto Lend3
0039 | aload    | marks        | k            | t8         ; t8 = marks[k]
0040 | assign   | t8           | -            | highest    ; highest = t8
0041 | label    | Lend3        | -            | -          ; Lend3:
0042 | aload    | marks        | k            | t9         ; t9 = marks[k]
0043 | cast     | t9           | int32        | t10        ; t10 = (int32) t9
0044 | add      | sum          | t10          | t11        ; t11 = sum + t10
0045 | assign   | t11          | -            | sum        ; sum = t11
0046 | aload    | marks        | k            | t12        ; t12 = marks[k]
0047 | ge       | t12          | 50           | t13        ; t13 = t12 >= 50
0048 | iffalse  | t13          | Lend4        | -          ; ifFalse t13 goto Lend4
0049 | add      | passes       | 1            | t14        ; t14 = passes + 1
0050 | assign   | t14          | -            | passes     ; passes = t14
0051 | label    | Lend4        | -            | -          ; Lend4:
0052 | add      | k            | 1            | t15        ; t15 = k + 1
0053 | assign   | t15          | -            | k          ; k = t15
0054 | goto     | Ltop0        | -            | -          ; goto Ltop0
0055 | label    | Lend1        | -            | -          ; Lend1:
0056 | cast     | sum          | real         | t16        ; t16 = (real) sum
0057 | div      | t16          | 1.0          | t17        ; t17 = t16 / 1.0
0058 | cast     | count        | real         | t18        ; t18 = (real) count
0059 | div      | t17          | t18          | t19        ; t19 = t17 / t18
0060 | assign   | t19          | -            | mean       ; mean = t19
0061 | printstr | "count   : " | -            | -          ; print "count   : "
0062 | print    | count        | -            | -          ; print count
0063 | newline  | -            | -            | -          ; newline
0064 | printstr | "lowest  : " | -            | -          ; print "lowest  : "
0065 | print    | lowest       | -            | -          ; print lowest
0066 | newline  | -            | -            | -          ; newline
0067 | printstr | "highest : " | -            | -          ; print "highest : "
0068 | print    | highest      | -            | -          ; print highest
0069 | newline  | -            | -            | -          ; newline
0070 | printstr | "sum     : " | -            | -          ; print "sum     : "
0071 | print    | sum          | -            | -          ; print sum
0072 | newline  | -            | -            | -          ; newline
0073 | printstr | "mean    : " | -            | -          ; print "mean    : "
0074 | print    | mean         | -            | -          ; print mean
0075 | newline  | -            | -            | -          ; newline
0076 | printstr | "passed  : " | -            | -          ; print "passed  : "
0077 | print    | passes       | -            | -          ; print passes
0078 | printstr | " of "       | -            | -          ; print " of "
0079 | print    | count        | -            | -          ; print count
0080 | newline  | -            | -            | -          ; newline
0081 | assign   | 'F'          | -            | grade      ; grade = 'F'
0082 | ge       | mean         | 80.0         | t20        ; t20 = mean >= 80.0
0083 | iffalse  | t20          | Lelse5       | -          ; ifFalse t20 goto Lelse5
0084 | assign   | 'A'          | -            | grade      ; grade = 'A'
0085 | goto     | Lend6        | -            | -          ; goto Lend6
0086 | label    | Lelse5       | -            | -          ; Lelse5:
0087 | ge       | mean         | 70.0         | t21        ; t21 = mean >= 70.0
0088 | iffalse  | t21          | Lelse7       | -          ; ifFalse t21 goto Lelse7
0089 | assign   | 'B'          | -            | grade      ; grade = 'B'
0090 | goto     | Lend8        | -            | -          ; goto Lend8
0091 | label    | Lelse7       | -            | -          ; Lelse7:
0092 | assign   | 1            | -            | t22        ; t22 = 1
0093 | ge       | mean         | 60.0         | t23        ; t23 = mean >= 60.0
0094 | iftrue   | t23          | Lsc9         | -          ; if t23 goto Lsc9
0095 | ge       | mean         | 55.0         | t24        ; t24 = mean >= 55.0
0096 | iftrue   | t24          | Lsc9         | -          ; if t24 goto Lsc9
0097 | assign   | 0            | -            | t22        ; t22 = 0
0098 | label    | Lsc9         | -            | -          ; Lsc9:
0099 | iffalse  | t22          | Lend10       | -          ; ifFalse t22 goto Lend10
0100 | assign   | 'C'          | -            | grade      ; grade = 'C'
0101 | label    | Lend10       | -            | -          ; Lend10:
0102 | label    | Lend8        | -            | -          ; Lend8:
0103 | label    | Lend6        | -            | -          ; Lend6:
0104 | printstr | "grade   : " | -            | -          ; print "grade   : "
0105 | print    | grade        | -            | -          ; print grade
0106 | newline  | -            | -            | -          ; newline
0107 | halt     | -            | -            | -          ; halt
#--------------------------------------------------------------------------------------
