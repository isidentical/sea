## SEA's Format

```py
a = random()

if a >= 5.0:
    print('a is too big')
    a = 5.0
elif a <= 2.0:
    print('a is too small')
    a *= 2

for counter in range(int(a)):
    if counter > 4:
        print('up to 4')
        break
    
    print(counter)

print('done')
```

Would normally compile to the following

<details>
  <summary>Original dis output (click to expand)</summary>

```
  1           0 LOAD_NAME                0 (random)
              2 CALL_FUNCTION            0
              4 STORE_NAME               1 (a)

  3           6 LOAD_NAME                1 (a)
              8 LOAD_CONST               0 (5.0)
             10 COMPARE_OP               5 (>=)
             12 POP_JUMP_IF_FALSE       28

  4          14 LOAD_NAME                2 (print)
             16 LOAD_CONST               1 ('a is too big')
             18 CALL_FUNCTION            1
             20 POP_TOP

  5          22 LOAD_CONST               0 (5.0)
             24 STORE_NAME               1 (a)
             26 JUMP_FORWARD            24 (to 52)

  6     >>   28 LOAD_NAME                1 (a)
             30 LOAD_CONST               2 (2.0)
             32 COMPARE_OP               1 (<=)
             34 POP_JUMP_IF_FALSE       52

  7          36 LOAD_NAME                2 (print)
             38 LOAD_CONST               3 ('a is too small')
             40 CALL_FUNCTION            1
             42 POP_TOP

  8          44 LOAD_NAME                1 (a)
             46 LOAD_CONST               4 (2)
             48 INPLACE_MULTIPLY
             50 STORE_NAME               1 (a)

 10     >>   52 LOAD_NAME                3 (range)
             54 LOAD_NAME                4 (int)
             56 LOAD_NAME                1 (a)
             58 CALL_FUNCTION            1
             60 CALL_FUNCTION            1
             62 GET_ITER
        >>   64 FOR_ITER                32 (to 98)
             66 STORE_NAME               5 (counter)

 11          68 LOAD_NAME                5 (counter)
             70 LOAD_CONST               5 (4)
             72 COMPARE_OP               4 (>)
             74 POP_JUMP_IF_FALSE       88

 12          76 LOAD_NAME                2 (print)
             78 LOAD_CONST               6 ('up to 4')
             80 CALL_FUNCTION            1
             82 POP_TOP

 13          84 POP_TOP
             86 JUMP_ABSOLUTE           98

 15     >>   88 LOAD_NAME                2 (print)
             90 LOAD_NAME                5 (counter)
             92 CALL_FUNCTION            1
             94 POP_TOP
             96 JUMP_ABSOLUTE           64

 17     >>   98 LOAD_NAME                2 (print)
            100 LOAD_CONST               7 ('done')
            102 CALL_FUNCTION            1
            104 POP_TOP
            106 LOAD_CONST               8 (None)
            108 RETURN_VALUE
```
</details>

However with basic SEA, it is getting compiled to this

<details>
  <summary>python -m sea (click to expand)</summary>
  
```
$0 = LOAD_NAME('random')
$1 = CALL_FUNCTION(0, $0)
$2 = STORE_NAME('a', $1)
$3 = LOAD_NAME('a')
$4 = LOAD_CONST(5.0)
$5 = COMPARE_OP('>=', $3, $4)
$6 = POP_JUMP_IF_FALSE(28, $5)
$7 = LOAD_NAME('print')
$8 = LOAD_CONST('a is too big')
$9 = CALL_FUNCTION(1, $7, $8)
$10 = POP_TOP($9)
$11 = LOAD_CONST(5.0)
$12 = STORE_NAME('a', $11)
$13 = JUMP_FORWARD(52)
$14 = LOAD_NAME('a')
$15 = LOAD_CONST(2.0)
$16 = COMPARE_OP('<=', $14, $15)
$17 = POP_JUMP_IF_FALSE(52, $16)
$18 = LOAD_NAME('print')
$19 = LOAD_CONST('a is too small')
$20 = CALL_FUNCTION(1, $18, $19)
$21 = POP_TOP($20)
$22 = LOAD_NAME('a')
$23 = LOAD_CONST(2)
$24 = INPLACE_MULTIPLY($22, $23)
$25 = STORE_NAME('a', $24)
$26 = LOAD_NAME('range')
$27 = LOAD_NAME('int')
$28 = LOAD_NAME('a')
$29 = CALL_FUNCTION(1, $27, $28)
$30 = CALL_FUNCTION(1, $26, $29)
$31 = GET_ITER($30)
$32 = FOR_ITER(98)
$33 = STORE_NAME('counter', $32)
$34 = LOAD_NAME('counter')
$35 = LOAD_CONST(4)
$36 = COMPARE_OP('>', $34, $35)
$37 = POP_JUMP_IF_FALSE(88, $36)
$38 = LOAD_NAME('print')
$39 = LOAD_CONST('up to 4')
$40 = CALL_FUNCTION(1, $38, $39)
$41 = POP_TOP($40)
$42 = POP_TOP($31)
$43 = JUMP_ABSOLUTE(98)
$44 = LOAD_NAME('print')
$45 = LOAD_NAME('counter')
$46 = CALL_FUNCTION(1, $44, $45)
$47 = POP_TOP($46)
$48 = JUMP_ABSOLUTE(64)
$49 = LOAD_NAME('print')
$50 = LOAD_CONST('done')
$51 = CALL_FUNCTION(1, $49, $50)
$52 = POP_TOP($51)
$53 = LOAD_CONST(None)
$54 = RETURN_VALUE($53)
```
</details>

And with the IR mode, it even supports basic control flow operations accross blocks;
<details>
  <summary>python -m sea --enable-ir (click to expand)</summary>
  

```
Block $B0: 
    $0 = LOAD_NAME('random')
    $1 = CALL_FUNCTION(0, $0)
    $2 = STORE_NAME('a', $1)
    $3 = LOAD_NAME('a')
    $4 = LOAD_CONST(5.0)
    $5 = COMPARE_OP('>=', $3, $4)
    $6 = POP_JUMP_IF_FALSE(28, $5)
    may jump to: $B1 (on false), $B2 (on true)
Block $B1: 
    $7 = LOAD_NAME('a')
    $8 = LOAD_CONST(2.0)
    $9 = COMPARE_OP('<=', $7, $8)
    $10 = POP_JUMP_IF_FALSE(52, $9)
    may jump to: $B3 (on false), $B4 (on true)
Block $B2: 
    $11 = LOAD_NAME('print')
    $12 = LOAD_CONST('a is too big')
    $13 = CALL_FUNCTION(1, $11, $12)
    $14 = POP_TOP($13)
    $15 = LOAD_CONST(5.0)
    $16 = STORE_NAME('a', $15)
    $17 = JUMP_FORWARD(52)
    may jump to: $B3
Block $B3: 
    $18 = LOAD_NAME('range')
    $19 = LOAD_NAME('int')
    $20 = LOAD_NAME('a')
    $21 = CALL_FUNCTION(1, $19, $20)
    $22 = CALL_FUNCTION(1, $18, $21)
    $23 = GET_ITER($22)
    $24 = FOR_ITER(98)
    may jump to: $B5 (on exhaust), $B6 (on loop)
Block $B4: 
    $25 = LOAD_NAME('print')
    $26 = LOAD_CONST('a is too small')
    $27 = CALL_FUNCTION(1, $25, $26)
    $28 = POP_TOP($27)
    $29 = LOAD_NAME('a')
    $30 = LOAD_CONST(2)
    $31 = INPLACE_MULTIPLY($29, $30)
    $32 = STORE_NAME('a', $31)
    may jump to: $B3
Block $B5: 
    $33 = LOAD_NAME('print')
    $34 = LOAD_CONST('done')
    $35 = CALL_FUNCTION(1, $33, $34)
    $36 = POP_TOP($35)
    $37 = LOAD_CONST(None)
    $38 = RETURN_VALUE($37)
Block $B6: 
    $39 = STORE_NAME('counter', $24)
    $40 = LOAD_NAME('counter')
    $41 = LOAD_CONST(4)
    $42 = COMPARE_OP('>', $40, $41)
    $43 = POP_JUMP_IF_FALSE(88, $42)
    may jump to: $B7 (on false), $B8 (on true)
Block $B7: 
    $44 = LOAD_NAME('print')
    $45 = LOAD_NAME('counter')
    $46 = CALL_FUNCTION(1, $44, $45)
    $47 = POP_TOP($46)
    $48 = JUMP_ABSOLUTE(64)
    may jump to: $B3
Block $B8: 
    $49 = LOAD_NAME('print')
    $50 = LOAD_CONST('up to 4')
    $51 = CALL_FUNCTION(1, $49, $50)
    $52 = POP_TOP($51)
    $53 = POP_TOP($23)
    $54 = JUMP_ABSOLUTE(98)
    may jump to: $B5
```
</details>

Note: for visualizing this output, you can simply pass `--show-graph` option
![graph](https://user-images.githubusercontent.com/47358913/135715738-9177779a-7b43-4249-a30a-b5c7b0ae6f22.png)
