INDEX , OP , ARG1 , ARG2 , RESULT
-----------------------------------
0 , alloc , int32 , 1 , x
1 , alloc , int32 , 1 , y
2 , add , x , 1 , t0
3 , copy , t0 , - , y
4 , write , "y = " , - , -
5 , write , y , - , -
6 , line , - , - , -
7 , stop , - , - , -
-----------------------------------
total instructions = 8
