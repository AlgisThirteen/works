import datetime

def count_days(d):
    dif = (d - datetime.datetime.today())
    # if dif < 0:
    #     return 'The day is in the past!'
    # elif dif == 0:
    #     return 'Today is the day!'
    # else:
    #     return f'{dif} days'
    return dif


d = datetime.datetime(2016, 12, 24, 18, 0)
# d = datetime.datetime(2022, 12, 24, 18, 0)
# d = datetime.datetime(2022, 12, 31, 18, 0)

# print(count_days(d))

diff = d - datetime.datetime.today()

print(d)