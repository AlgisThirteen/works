# def likes(names):
#     if len(names) == 0:
#         output = 'no one likes this'
#     elif len(names) == 1:
#         output = names[0] + ' likes this'
#     elif len(names) == 2:
#         output = names[0] + ' and ' + names[1] + ' like this'
#     elif len(names) == 3:
#         output = names[0] + ', ' + names[1] + ' and ' + names[2] + ' like this'
#     else:
#         output = names[0] + ', ' + names[1] + ' and ' + str(len(names) - 2) +' others like this'
#     return output

def likes(names):
    names = names
    if len(names) >= 4:
        n = 4
    else:
        n = len(names)

    mylist = {
        0: 'no one likes this',
        1: f'{names[0]} likes this',
        2: f'{names[0]} and {names[1]} likes this',
        3: f'{names[0]}, {names[1]} and {names[2]} like this',
        4: f'{names[0]}, {names[1]} and {len(names)-2} others like this',
    }    
    return mylist[n]  


#print(likes([])) # must be "no one likes this"
print(likes(["Peter"])) # must be "Peter likes this"
#print(likes(["Jacob", "Alex"])) # must be "Jacob and Alex like this"
#print(likes(["Max", "John", "Mark"])) # must be "Max, John and Mark like this"
#print(likes(["Alex", "Jacob", "Mark", "Max"])) # must be "Alex, Jacob and 2 others like this"


