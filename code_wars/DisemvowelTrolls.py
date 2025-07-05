def disemvowel(string):
    newString = ''
    vowels = 'aioue'
    for letter in string:
        trigger = 0
        for vowel in vowels:
            if letter.lower() == vowel:
                trigger += 1
        if trigger == 0:
            newString = newString + letter

    return newString

print(disemvowel("This website is for losers LOL!"))
