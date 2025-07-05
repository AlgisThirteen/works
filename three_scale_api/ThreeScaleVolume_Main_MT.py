# ==================================================================================================================
# Version:      Python 3.4, Excel 2016
# Project:      API Usage Report - 3scale
# Name:         main function
# Creator:      Algis S
# Create Date:  10/26/2018
# Purpose:      used to pull data back from the servers and importing all of it to an excel spreadsheet
# Corrections:
#               DATE            AUTHOR          CORRECTION
#
# libraries ============================================================================================================
import pyodbc
from ThreeScaleVolume_hits_MT import getList, aggregateUsage
import concurrent.futures
import time
# variable =============================================================================================================
sqlConnection = 'Driver={ODBC Driver 17 for SQL Server};Server=;Trusted_Connection=yes;'

sqlQuery_Usage = """
                INSERT INTO Database.dbo.ThreeScale_MonthlyUsageStaging
                    (metricName
                    ,periodStart
                    ,periodEnd
                    ,hits
                    ,applicationID
                    ,applicationName
                    ,accountName)
                VALUES
                    ('%s', '%s', '%s', %s, '%s', '%s', '%s')"""

dateFormat = '%d/%m/%Y'

sqlQuery_UpsertFact_sp = """exec database.dbo.ThreeScale_UpsertFact"""

# pull back the current list of accounts and check if
sqlQueary_getAccount = """
                    SELECT
                        AccountID
                    FROM database.dbo.ThreeScale_Accounts
                    """

# need to create the table
sqlQuery_AccountStaging = """ 
                INSERT INTO database.dbo.ThreeScale_AccountsStaging
                    (
                     CompanyName
                    ,AccountID
                    ,UserEmail
                    ,EmailDomain
                    ,MonthlyBilling
                    ,MonthlyCharge
                    ,CcStored
                    )
                VALUES
                    ('%s', '%s', '%s', '%s', '%s', '%s', '%s')
                """

sqlQuery_ApplicationStaging = """
                INSERT INTO database.dbo.ThreeScale_ApplicationsStaging
                    (
                     ApplicationID
                    ,AccountID
                    ,ServiceID
                    ,ApplicationName
                    ,ApplicationStatus
                    ,TrafficOn
                    )
                VALUES
                    ('%s', '%s', '%s', '%s', '%s', '%s')
"""

def main():

    start = time.perf_counter()
    db = pyodbc.connect(sqlConnection)
    openConnection = db.cursor()
    hits, ThreeScaleAccounts, ThreeScaleApplications = getList()

    # The script is to ingest the Account info into the staging table
    def account_Upload(account):
        print(str(account[0]) + ' --------------------------> uploaded to database.dbo.ThreeScale_AccountsStaging\n')
        openConnection.execute(sqlQuery_AccountStaging % (str(account[0]).replace("'", "`"), str(account[1]),
                                                          str(account[2]), str(account[2]).split('@')[-1],
                                                          str(account[3]), str(account[4]), str(account[5])
                                                          )
                               )
        openConnection.commit()

    # the script is to ingest Application info into the staging table
    def application_Upload(application):
        print(str(application[3]) + ' ---------------------> uploaded to database.dbo.ThreeScale_ApplicationsStaging\n')
        openConnection.execute(sqlQuery_ApplicationStaging % (str(application[0]), str(application[1]),
                                                              str(application[2]),
                                                              str(application[3]).replace("'", '`'),
                                                              str(application[4]), str(application[5])
                                                      )
                       )
        openConnection.commit()

    def hits_Uploads(hit):
        output = aggregateUsage(hit)
        if len(output) > 0 and int(output[0][3]) > 0:
            print(output[0][0] + ' ------------------------> uploaded to database.dbo.ThreeScale_MonthlyUsageStaging\n')
            openConnection.execute(sqlQuery_Usage % (str(output[0][0]), str((output[0][1])[0:10]),
                                                     str((output[0][2])[0:10]),
                                                     str(output[0][3]), str(output[0][4]),
                                                     str(output[0][5].replace("'", "`")),
                                                     str(output[0][6].replace("'", "`"))))
            openConnection.commit()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(account_Upload, ThreeScaleAccounts)
        executor.map(application_Upload, ThreeScaleApplications)
        executor.map(hits_Uploads, hits)
    executor.shutdown(wait = False)

    # Moving the data into the Fact table and truncating the Staging table
    print('Move Account Data to Fact in database')
    openConnection.execute(sqlQuery_UpsertFact_sp)
    openConnection.commit()

    finish = time.perf_counter()
    print(f'Script finished in {finish-start} seconds')

if __name__ == '__main__':
    main()
