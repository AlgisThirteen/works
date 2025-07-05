# ==================================================================================================================
# Version:      Python 3.4, Excel 2016
# Project:      API Usage Report - 3scale
# Name:         hit function
# Creator:      Algis S
# Create Date:  10/26/2018
# Purpose:      pull url lists to
# Corrections:
#               DATE            AUTHOR          CORRECTION
#               2020.01.17      AS              Updated format for the month setup
# libraries ============================================================================================================
import requests
import xmltodict
import json
import datetime
import calendar
# variable =============================================================================================================
accessToken = ''
scaleOutput = []
today = datetime.date.today()
if today.month == 1:
    startDate = datetime.datetime(today.year - 1, 12, 1).strftime('%Y-%m-%d')       # updated 2020.01.17
    endDate = datetime.datetime(today.year - 1, 12, 31).strftime('%Y-%m-%d')        # updated 2020.01.17
    yr = today.year - 1
    mth = 12
else:
## Previous month
    startDate = datetime.datetime(today.year, today.month - 1, 1).strftime('%Y-%m-%d')
    endDate = datetime.datetime(today.year, today.month - 1, calendar.mdays[today.month - 1]).strftime('%Y-%m-%d')
    yr = today.year
    mth = today.month - 1
## Current month
    # startDate = datetime.datetime(today.year, today.month, 1).strftime('%Y-%m-%d')
    # endDate = datetime.datetime(today.year, today.month, calendar.mdays[today.month - 1]).strftime('%Y-%m-%d')
    # yr = today.year
    # mth = today.month

############################
## generic path variables ##
############################
url3Scale = 'https://developer-onboard-apis-admin.3scale.net/'
token = 'access_token=' + accessToken
xmlPage = 1
per_page = 20

########################################################
## Account List                                       ##
## Customer name, Application Name and Application ID ##
## url3Scale + urlAccount + token                     ##
########################################################
urlAccount = 'admin/api/accounts.xml?'
accountPage = '&page='
perPage = '&per_page=500'

############################################################################
## Application List (all services)                                        ##
## url3Scale + urlApplication + token + accountPage + str(page) + perPage ##
############################################################################

urlApplication = 'admin/api/applications.xml?'

#####################################
## Service List                    ##
## url3Scale + urlServices + token ##
#####################################
urlServices = 'admin/api/services.xml?'

###############################################################
## variables for Metric List                                 ##
## url3Scale + urlMetric + str(service_id) + metrics + token ##
###############################################################
urlMetric = 'admin/api/services/'
metrics =  '/metrics.xml?'

###########################################################################################################
## Application Usage by Metrics input fields: application_id, MetricName                                 ##
## url3Scale + urlStats + str(application_id) + urlUsage + token + urlMetricNM + MetricName + urlSince + ##
## startDate + urlPeriod + endDate + urlGranularity                                                      ##
###########################################################################################################
urlStats = 'stats/applications/'
urlUsage = '/usage.xml?'
urlMetricNM = '&metric_name='
MetricName = 'hits'
urlSince = '&since='
urlPeriod = '&period=month&until='
urlGranularity = '&granularity=month&skip_change=true'

# functions ============================================================================================================
def outputDict(xmlPath):
    r = requests.get(url=xmlPath)
    data =str(r.text)
    dataList = xmltodict.parse(data, xml_attribs=True)
    json_data = json.dumps(dataList, indent=4)
    dataDict = json.loads(json_data)
    return dataDict

def getAccountList(url3Scale, urlAdmin, token, accountPage, xmlPage, perPage):
    getURL = url3Scale + urlAdmin + token + accountPage + str(xmlPage) + perPage
    jsonData = outputDict(getURL)
    return jsonData

# function uses data passed by getAccountList
# This data will be passed to the FactAccounts table
def aggregateAccountList(AccountData, ThreeScaleAccounts):
    for i in AccountData['accounts']['account']:
        try:
            accountSubList = []
            accountSubList.append(i['org_name'])                                # 0 companyName
            accountSubList.append(int(i['id']))                                 # 1 account_id
            accountSubList.append(i['users']['user']['email'])                  # 2 user_email
            accountSubList.append(i['monthly_billing_enabled'])                 # 3 monthly_billing
            accountSubList.append(i['monthly_charging_enabled'])                # 4 monthly_changing
            accountSubList.append(i['credit_card_stored'])                      # 5 cc_stored

            ThreeScaleAccounts.append(accountSubList)
        except Exception:
            print(str(i['org_name']) + '|' + str(i['id']) + ' - not added to the list')
    return ThreeScaleAccounts

def getApplicationList(url3Scale, urlApplication, token, accountPage, page, perPage):
    appURL = url3Scale + urlApplication + token + accountPage + str(page) + perPage
    applicationData = outputDict(appURL)
    return applicationData

# the function uses data pased from getApplicatonList
def aggregateApplicationList(ApplicationData, ThreeScaleApplications):
    for app in ApplicationData['applications']['application']:
        try:
            applicationSubList = []
            applicationSubList.append(app['id'])                                                # 0 application_id
            applicationSubList.append(app['user_account_id'])                                   # 1 account_id
            applicationSubList.append(app['service_id'])                                        # 2 service_id
            applicationSubList.append(app['name'])                                              # 3 application_name
            applicationSubList.append(app['state'])                                             # 4 status
            applicationSubList.append(app['first_daily_traffic_at'].split('T')[0]
                                      if app['first_daily_traffic_at'] is not None else
                                      app['first_daily_traffic_at'])                            # 5 Traffic on

            ThreeScaleApplications.append(applicationSubList)
        except Exception:
            print(str(app['name']) + ' was not loaded')
    return ThreeScaleApplications

def aggregateServiceList(url3Scale, urlServices, token, ThreeScaleService):
    getURL = url3Scale + urlServices + token
    ServiceData = outputDict(getURL)

    for service in ServiceData['services']['service']:
        try:
            serviceSubList = []
            serviceSubList.append(service['name'])
            serviceSubList.append(service['id'])
            ThreeScaleService.append(serviceSubList)
        except Exception:
            print(str(service['name']) + '|' + str(service['id']))
    return ThreeScaleService

def aggregateMetricList(url3Scale, urlMetric, service_id, metrics, token, ThreeScaleMetrics):
    getURL = url3Scale + urlMetric + service_id + metrics + token
    MetricData = outputDict(getURL)
    for metric in MetricData['metrics']['method']:
        ThreeScaleMetricsSub = []
        ThreeScaleMetricsSub.append(service_id)
        ThreeScaleMetricsSub.append(metric['name'])
        ThreeScaleMetrics.append(ThreeScaleMetricsSub)
    # print(MetricData)
    return ThreeScaleMetrics

# this is the final function run n the Main file
def aggregateUsage(usageURL):
    urlResults = []
    UsageData = outputDict(usageURL)
    try:
        usage = UsageData['usage']
        metricSubList = []
        metricSubList.append(usage['metric']['name'])                               # 0 metricName
        metricSubList.append(usage['period']['since'])                              # 1 periodStart
        metricSubList.append(usage['period']['until'])                              # 2 periodEnd
        metricSubList.append(usage['data']['total'])                                # 3 hits
        metricSubList.append(usage['application']['id'])                            # 4 applicationID
        metricSubList.append(usage['application']['name'])                          # 5 applicationName
        metricSubList.append(usage['application']['account']['name'])               # 6 accountName
        metricSubList.append(usage['application']['account']['id'])                 # 7 account id
# adding a new call for customer email
        urlResults.append(metricSubList)
#        print(urlResults)
    except KeyError:
        print(UsageData)
    return urlResults

# Run Time ============================================================================================================
def getList():
    # Derive the account list for merge
    AccountData = getAccountList(url3Scale, urlAccount, token, accountPage, xmlPage, perPage)

    maxPage = AccountData['accounts']['@total_pages']
    ThreeScaleAccounts = []
    # list of accounts with the email
    ThreeScaleAccounts = aggregateAccountList(AccountData, ThreeScaleAccounts)
    for page in range(2, int(maxPage) + 1):
        AccountData = getAccountList(url3Scale, urlAccount, token, accountPage, str(page), perPage)
        ThreeScaleAccounts = aggregateAccountList(AccountData, ThreeScaleAccounts)

    ## Assembling the list of Services
    ServiceURL = url3Scale + urlServices + token
    ThreeScaleServices = []
    ThreeScaleServices = aggregateServiceList(url3Scale, urlServices, token, ThreeScaleServices)

    ## Assembling the list of Metrics
    ThreeScaleMetrics = []
    for serviceID in ThreeScaleServices:
        ThreeScaleMetrics = aggregateMetricList(url3Scale, urlMetric, str(serviceID[1]), metrics, token,
                                                ThreeScaleMetrics)
#    print('Metrics' + ' ' + str(len(ThreeScaleMetrics)))

    ## Getting usage for each account, application, matric
    ApplicationData = getApplicationList(url3Scale, urlApplication, token, accountPage, xmlPage, perPage)
    appPage = ApplicationData['applications']['@total_pages']
# The first run and then it carries into a for loop
    ThreeScaleApplications = []
    ThreeScaleApplications = aggregateApplicationList(ApplicationData, ThreeScaleApplications)
    for appPage in range(2, int(appPage) + 1):
        ApplicationData = []
        ApplicationData = getApplicationList(url3Scale, urlApplication, token, accountPage, appPage, perPage)
        ThreeScaleApplications = aggregateApplicationList(ApplicationData, ThreeScaleApplications)
#    print('Application' + ' ' + str(len(ThreeScaleApplications)))

    activeApps = []
    for a in ThreeScaleApplications:
        if a[5] != None:
            dateE = datetime.datetime.strptime(a[5], "%Y-%m-%d")
            # print(str(dateE.year) + ' ' + str(dateE.month, ))
            if dateE >= datetime.datetime.strptime(startDate, "%Y-%m-%d"):
                activeApps.append(a)
## this part is no longer needed ---------------------------------------------------------------------------------------
    # for a in activeApps:
    #     print(a)

    # activeAppList = []
    # hitUsageUrlList = []
    # for appID in ThreeScaleApplications:
    #     if appID[4] != 'suspended':
    #         activeAppList.append(appID)
    #
    # ## get the
    # hitsUsage = []
    # for appID in activeAppList:
    #     for metricName in ThreeScaleMetrics:
    #         metricURL = url3Scale + urlStats + str(appID[0]) + urlUsage + token + urlMetricNM + 'hits' + \
    #                     urlSince + monthStart + urlPeriod + monthEnd + urlGranularity
    #         hitsUsage.append(metricURL)
    #         del metricURL
    #
    # return hitsUsage
# ----------------------------------------------------------------------------------------------------------------------
    usageUrlList = []
    for appID in activeApps:
        for metricName in ThreeScaleMetrics:
            metricURL = url3Scale + urlStats + str(appID[0]) + urlUsage + token + urlMetricNM + metricName[1] + \
                        urlSince + startDate + urlPeriod + endDate + urlGranularity
            usageUrlList.append(metricURL)
            del metricURL
    # for hit in usageUrlList:
    #     print(hit)
    # for a in usageUrlList:
    #     print(a)
    return usageUrlList, ThreeScaleAccounts, ThreeScaleApplications

# if __name__ == '__main__':
#     getList()