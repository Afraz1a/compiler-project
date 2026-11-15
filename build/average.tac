INDEX , OP , ARG1 , ARG2 , RESULT
-----------------------------------
0 , alloc , int32 , 1 , count
1 , alloc , int16 , 10 , marks
2 , alloc , int16 , 1 , lowest
3 , alloc , int16 , 1 , highest
4 , alloc , int32 , 1 , sum
5 , alloc , int32 , 1 , passed
6 , alloc , int32 , 1 , k
7 , alloc , real , 1 , mean
8 , alloc , char , 1 , grade
9 , copy , 10 , - , count
10 , store , 0 , 72 , marks
11 , store , 1 , 48 , marks
12 , store , 2 , 91 , marks
13 , store , 3 , 65 , marks
14 , store , 4 , 33 , marks
15 , store , 5 , 88 , marks
16 , store , 6 , 57 , marks
17 , store , 7 , 79 , marks
18 , store , 8 , 95 , marks
19 , store , 9 , 61 , marks
20 , copy , 32767 , - , lowest
21 , neg , 32768 , - , t0
22 , copy , t0 , - , highest
23 , copy , 0 , - , sum
24 , copy , 0 , - , passed
25 , copy , 0 , - , k
26 , label , L0 , - , -
27 , lt , k , count , t1
28 , iffalse , t1 , L1 , -
29 , load , marks , k , t2
30 , lt , t2 , lowest , t3
31 , iffalse , t3 , L2 , -
32 , load , marks , k , t4
33 , copy , t4 , - , lowest
34 , label , L2 , - , -
35 , load , marks , k , t5
36 , gt , t5 , highest , t6
37 , iffalse , t6 , L3 , -
38 , load , marks , k , t7
39 , copy , t7 , - , highest
40 , label , L3 , - , -
41 , load , marks , k , t8
42 , add , sum , t8 , t9
43 , copy , t9 , - , sum
44 , load , marks , k , t10
45 , ge , t10 , 50 , t11
46 , iffalse , t11 , L4 , -
47 , add , passed , 1 , t12
48 , copy , t12 , - , passed
49 , label , L4 , - , -
50 , add , k , 1 , t13
51 , copy , t13 , - , k
52 , goto , L0 , - , -
53 , label , L1 , - , -
54 , mul , sum , 1.0 , t14
55 , div , t14 , count , t15
56 , copy , t15 , - , mean
57 , copy , 'F' , - , grade
58 , ge , mean , 80.0 , t16
59 , iffalse , t16 , L5 , -
60 , copy , 'A' , - , grade
61 , goto , L6 , - , -
62 , label , L5 , - , -
63 , ge , mean , 70.0 , t17
64 , iffalse , t17 , L7 , -
65 , copy , 'B' , - , grade
66 , goto , L8 , - , -
67 , label , L7 , - , -
68 , copy , 1 , - , t18
69 , ge , mean , 60.0 , t19
70 , iftrue , t19 , L9 , -
71 , ge , mean , 55.0 , t20
72 , iftrue , t20 , L9 , -
73 , copy , 0 , - , t18
74 , label , L9 , - , -
75 , iffalse , t18 , L10 , -
76 , copy , 'C' , - , grade
77 , label , L10 , - , -
78 , label , L8 , - , -
79 , label , L6 , - , -
80 , write , "lowest = " , - , -
81 , write , lowest , - , -
82 , line , - , - , -
83 , write , "highest = " , - , -
84 , write , highest , - , -
85 , line , - , - , -
86 , write , "sum = " , - , -
87 , write , sum , - , -
88 , line , - , - , -
89 , write , "mean = " , - , -
90 , write , mean , - , -
91 , line , - , - , -
92 , write , "passed = " , - , -
93 , write , passed , - , -
94 , write , " of " , - , -
95 , write , count , - , -
96 , line , - , - , -
97 , write , "grade = " , - , -
98 , write , grade , - , -
99 , line , - , - , -
100 , stop , - , - , -
-----------------------------------
total instructions = 101
