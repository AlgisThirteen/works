def dig_pow(n, p):
    total = 0
    total = for x in str(n):
        total += int(x) ** p
        p += 1
    if total / n == int(total / n):
        return int(total / n)
    else:
        return -1



# print(dig_pow(89, 1))        #, 1)
# dig_pow(695, 2)        #, 1)
# print(dig_pow(92, 1))        #, -1)
print(dig_pow(46288, 3))     #, 51)
