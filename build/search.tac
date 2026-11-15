INDEX , OP , ARG1 , ARG2 , RESULT
-----------------------------------
0 , alloc , int32 , 1 , size
1 , alloc , int32 , 8 , a
2 , alloc , int32 , 1 , i
3 , alloc , int32 , 1 , found
4 , copy , 8 , - , size
5 , store , 0 , 14 , a
6 , store , 1 , 7 , a
7 , store , 2 , 23 , a
8 , store , 3 , 0 , a
9 , store , 4 , 9 , a
10 , store , 5 , 0 , a
11 , store , 6 , 31 , a
12 , store , 7 , 5 , a
13 , copy , 0 , - , i
14 , neg , 1 , - , t0
15 , copy , t0 , - , found
16 , label , L0 , - , -
17 , lt , i , size , t1
18 , iffalse , t1 , L1 , -
19 , load , a , i , t2
20 , eq , t2 , 0 , t3
21 , iffalse , t3 , L2 , -
22 , copy , i , - , found
23 , goto , L1 , - , -
24 , label , L2 , - , -
25 , add , i , 1 , t4
26 , copy , t4 , - , i
27 , goto , L0 , - , -
28 , label , L1 , - , -
29 , lt , found , 0 , t5
30 , iffalse , t5 , L3 , -
31 , write , "no zero in the array" , - , -
32 , line , - , - , -
33 , goto , L4 , - , -
34 , label , L3 , - , -
35 , write , "first zero at index " , - , -
36 , write , found , - , -
37 , line , - , - , -
38 , label , L4 , - , -
39 , stop , - , - , -
-----------------------------------
total instructions = 40
