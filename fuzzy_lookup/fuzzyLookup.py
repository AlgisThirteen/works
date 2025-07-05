
from fuzzywuzzy import fuzz
from cleanco import basename

accounts_OBI = []
accounts_OBI_clean = []
accounts_ATTM = []
accounts_ATTM_clean = []
matched_Arr = []

# List to look up
obi_file = open('LookupNames.txt', 'r',  encoding='ISO-8859-1')
for file_line in obi_file:
    accounts_OBI.append(file_line.replace('\n', ''))
obi_file.close()


for coName in accounts_OBI:
    accounts_OBI_cleanSUB = []
    coName_c =basename(coName)
    accounts_OBI_cleanSUB.append(coName)
    accounts_OBI_cleanSUB.append(coName_c)  
    accounts_OBI_clean.append(accounts_OBI_cleanSUB)

# Lookup list
attm_file = open('MasterNames.txt', 'r', encoding='ISO-8859-1')
for file_line in attm_file:
    accounts_ATTM.append(file_line.replace('\n', ''))
attm_file.close()

for coName in accounts_ATTM:
    accounts_ATTM_cleanSUB = []
    coName_c = basename(coName)
    accounts_ATTM_cleanSUB.append(coName)
    accounts_ATTM_cleanSUB.append(coName_c)
    accounts_ATTM_clean.append(accounts_ATTM_cleanSUB)
globalCounter = 1
max_point = len(accounts_ATTM_clean)
for obi_value in accounts_OBI_clean:
    i = 0
    inter_Matched_Arr2 = []
    while i < max_point:
        inter_Matched_Arr = []
        ratio = 0
        ratio = fuzz.ratio(obi_value[1], accounts_ATTM_clean[i][1])
        inter_Matched_Arr.append(obi_value[0])
        inter_Matched_Arr.append(accounts_ATTM_clean[i][0])
        inter_Matched_Arr.append(ratio)
        print(str(i) + str(inter_Matched_Arr))
        inter_Matched_Arr2.append(inter_Matched_Arr)
        i += 1
    inter_Matched_Arr2.sort(reverse=True, key=lambda x: x[2])


    counter = 0
    while counter < 10:
        print(inter_Matched_Arr2[counter])
        matched_Arr.append(inter_Matched_Arr2[counter])
        counter += 1

finish_file = open('match_Output.txt', 'a', encoding='ISO-8859-1')
for line in matched_Arr:
    finish_file.write(line[0] + '|' + line[1] + '|' + str(line[2]) + '\n')

finish_file.close()
