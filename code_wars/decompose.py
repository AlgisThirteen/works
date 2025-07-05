def decompose(n):
    outputArray = []
    targetValue = n ** 2
    for number in range(n - 1, 0, -1):
        if targetValue - number ** 2 >= 0:
            targetValue = targetValue - number ** 2
            outputArray.append(number)
        elif targetValue < 0:
            pass
    outputArray.reverse()
    print(outputArray)
    # if targetValue > 0:
    #     return None
    # else:
    #     return outputArray
# print(decompose(5))     #, [3,4])
# print(decompose(8))     #, None)
# print(decompose(11))     #, [1, 2, 4, 10])
print(decompose(1234567))       #2, 8, 32, 1571, 1234566]
