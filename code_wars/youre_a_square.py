import math

def is_square(n):
    if n < 0:
        return False
    else:
        if math.sqrt(n) == int(math.sqrt(n)):
            return True
        else:
            return False

