INDEX , OP , ARG1 , ARG2 , RESULT
-----------------------------------
0 , alloc , uint16 , 1 , limit
1 , alloc , uint16 , 1 , n
2 , alloc , uint16 , 1 , count
3 , alloc , uint32 , 1 , total
4 , alloc , uint16 , 1 , d
5 , alloc , int16 , 1 , prime
6 , copy , 40 , - , limit
7 , copy , 2 , - , n
8 , copy , 0 , - , count
9 , copy , 0 , - , total
10 , label , L0 , - , -
11 , lt , n , limit , t0
12 , iffalse , t0 , L1 , -
13 , copy , 2 , - , d
14 , copy , 1 , - , prime
15 , label , L2 , - , -
16 , mul , d , d , t1
17 , le , t1 , n , t2
18 , iffalse , t2 , L3 , -
19 , mod , n , d , t3
20 , eq , t3 , 0 , t4
21 , iffalse , t4 , L4 , -
22 , copy , 0 , - , prime
23 , goto , L3 , - , -
24 , label , L4 , - , -
25 , add , d , 1 , t5
26 , copy , t5 , - , d
27 , goto , L2 , - , -
28 , label , L3 , - , -
29 , copy , 0 , - , t6
30 , eq , prime , 1 , t7
31 , iffalse , t7 , L5 , -
32 , eq , n , 1 , t9
33 , not , t9 , - , t8
34 , iffalse , t8 , L5 , -
35 , copy , 1 , - , t6
36 , label , L5 , - , -
37 , iffalse , t6 , L6 , -
38 , write , n , - , -
39 , write , " is prime" , - , -
40 , line , - , - , -
41 , add , count , 1 , t10
42 , copy , t10 , - , count
43 , add , total , n , t11
44 , copy , t11 , - , total
45 , label , L6 , - , -
46 , add , n , 1 , t12
47 , copy , t12 , - , n
48 , goto , L0 , - , -
49 , label , L1 , - , -
50 , write , "primes below " , - , -
51 , write , limit , - , -
52 , write , " = " , - , -
53 , write , count , - , -
54 , line , - , - , -
55 , write , "their sum = " , - , -
56 , write , total , - , -
57 , line , - , - , -
58 , stop , - , - , -
-----------------------------------
total instructions = 59
