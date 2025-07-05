# ======================================================================================================================
# Project:      BookginsImport_SQL
# Name:         main function
# Creator:      Algis S
# Purpose:      Import the bookings to the sql server
# Corrections:
#               DATE            AUTHOR          NOTE
#               2019-06-21        AS            creation

# ======================================================================================================================
# Libraries
import pyodbc
import pandas as pd
import os


connection = 'Driver={ODBC Driver 17 for SQL Server};Server=<Server>;Trusted_Connection=yes;'
reportPath = os.getcwd()
sql_import = """
                INSERT INTO database.dbo.table
                VALUES ( 
                %s
                )
            """

field_Names = [['OpportunityID', 'nvarchar'],               # 0 - nvarchar
               ['Type', 'nvarchar'],                        # 5 - nvarchar
               ['CloseDate', 'date'],                       # 7 - date/nvarchar
               ['ContractTermMonths', 'int'],               # 8 - int
               ['AmountAACV', 'float'],                     # 12 - float
               ['Comment', 'nvarchar'],                     # 14 - nvarchar
               ['Recurring', 'int']
               ]
workbookName = 'BookingsUploadTemplate.xlsx'

# this function creates a template to set the data into
def droptoExcel():
    column_names = []
    for col_name in field_Names:
        column_names.append(col_name[0])
    writer = pd.ExcelWriter(workbookName)
    fields_df = pd.DataFrame(columns=column_names)
    fields_df.to_excel(writer, 'Template', index=False)
    writer.save()
    writer.close()


def getData():
    bookings_df = pd.read_excel(workbookName, sheet_name='Template')
    load_file = []
    for index, row in bookings_df.iterrows():
        # assemble the values for import
        one_entry = ""
        for i in range(0, len(field_Names)):
            if str(row[field_Names[i][0]]) != 'nan':
                if field_Names[i][1] == 'nvarchar':
                    if i < len(field_Names) - 1:
                        one_entry = one_entry + "'" + str(row[field_Names[i][0]]) + "', "
    #                    one_entry.append(str(row[field_Names[i][0]]))
                    else:
                        one_entry = one_entry + "'" + str(row[field_Names[i][0]]) + "'"
                elif field_Names[i][1] == 'date':
                    if i < len(field_Names) - 1:
                        one_entry = one_entry + "'" + str(row[field_Names[i][0]]) + "', "
    #                    one_entry.append(str(row[field_Names[i][0]]))
                    else:
                        one_entry = one_entry + "'" + str(row[field_Names[i][0]]) + "' "
                else:
                    if i < len(field_Names) - 1:
                        one_entry = one_entry + str((row[field_Names[i][0]])) + ", "
    #                    one_entry.append(row[field_Names[i][0]])
                    else:
                        one_entry = one_entry + str((row[field_Names[i][0]]))
            else:
                if i < len(field_Names) - 1:
                    one_entry = one_entry + 'NULL, '
                else:
                    one_entry = one_entry + 'NULL'
        load_file.append(one_entry)
    return load_file


def loadData(load_file):
    db = pyodbc.connect(connection)
    sql_connection = db.cursor()
    for value in load_file:
        print(value)
        print(sql_import % value)
        sql_connection.execute(sql_import % value)
        sql_connection.commit()
    sql_connection.close()

selection = input('Select action:\n1. generate template\n2. upload template to SQL \n\nInput: ')

if int(selection) == 1:
    droptoExcel()
    print('Excel template named "' + workbookName + '" was created in ' + reportPath)
elif int(selection) == 2:
    data_to_load = getData()
    loadData(data_to_load)
    print("Data has been imported to the table in the server")
else:
    print('Input is invalid')

input('Press any key to exit')