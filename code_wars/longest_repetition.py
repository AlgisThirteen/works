def longest_repetition(chars):
    maxChar, maxLen = '', 0
    curChar, curLen = '', 0
    for item in chars:
        curChar = item
        for letter in chars:
            if letter == curChar:
                print('t')
                curLen =+ 1
            else:
                if curLen > maxLen:
                    maxChar, maxLen = curChar, curLen

    return maxChar, maxLen


# longest_repetition("aaaabb")         #, ('a', 4)],
# longest_repetition("bbbaaabaaaa")    #, ('a', 4)],
# longest_repetition("cbdeuuu900")     #, ('u', 3)],
print(longest_repetition("abbbbb"))         #, ('b', 5)],
#print(longest_repetition("aabb"))           #, ('a', 2)],
#print(longest_repetition("ba"))             #, ('b', 1)],
#print(longest_repetition(""))               #, ('', 0)],
