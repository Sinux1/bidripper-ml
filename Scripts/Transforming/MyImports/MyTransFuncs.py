
'''
 * Author:    Samad Mazarei
 * Created:   10.4.2021
 * 
 * (c) Copyright - If you use my code please credit me.
'''

import sys
import os
import datetime
import json
import numpy as np
from dateutil.relativedelta import relativedelta

FILE_NAME_TIME_FORMAT = "%Y_%m_%d"
DATA_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TS = "Timestamp"
C4 = "c4.8xlarge"

def checkAndSetInFile(argList):
    '''
    Description:

    Parameters:

    Return:

    '''
    if len(argList) != 2:
        wMss = "Please pass a full input file path as parameter"
        sys.exit(wMss)
    elif not os.path.isfile(argList[1]):
        wMss = "File does not exist"
        sys.exit(wMss)
    else:
        return os.path.join(argList[1])

def transformDataToDict(starting_dt, tr_dict, instanceType=C4):
    '''
    Description:

    Parameters:

    Return:

    '''
    temp_ts_dict = {TS: [], "SpotPrice": [], "InstanceType": []}
    MN = 60
    HR = 24
    DAYS = 7
    prevPrice = None
    for i in range(MN*HR*DAYS):
        time = (starting_dt + datetime.timedelta(minutes=i)).strftime(DATA_TIME_FORMAT)
        listedPrice = tr_dict.get(time)
        if listedPrice:
            price = listedPrice
            prevPrice = price
        else:
            price = prevPrice
        if not price:
            print("Big Problem")
            sys.exit(starting_dt)
        temp_ts_dict[TS].append(time)
        temp_ts_dict["SpotPrice"].append(price)
        temp_ts_dict["InstanceType"].append(instanceType)
    return temp_ts_dict    

def getDateTimeFromInFilePath(filePath):
    '''
    Description:

    Parameters:

    Return:

    '''
    # Extract filename from path
    fileName = os.path.split(filePath)[1]
    # Remove extension from fileName
    fNameNoExt = fileName.split('.')[0]
    # Convert date into foramtted time stamp
    try:
        startDate = datetime.datetime.strptime(fNameNoExt, FILE_NAME_TIME_FORMAT)
    except Exception as e:
        wMss = "File Name Incorrect Format"
        sys.exit(wMss)
    # Return datetime object
    return startDate

def generateTransRaw(rawData, startDate):
    '''
    Description:

    Parameters:

    Return:

    '''
    tr = {}
    for elm in rawData:
        if elm["InstanceType"] != C4:
            continue
        reformedDT = None
        # Strip timezone data from Timestamp in raw data
        elm[TS] = elm[TS].split('+')[0]
        # Get the datetime of the current elm's spot price change
        elm_datetime = datetime.datetime.strptime(elm[TS], DATA_TIME_FORMAT)
        # If the spot price change is prior to start time (midnight) then update to midnight
        if elm_datetime < startDate:
            reformedDT = startDate.strftime(DATA_TIME_FORMAT)
            tr[reformedDT] = elm.get('SpotPrice')
            continue

        if elm_datetime.second != 0:
            upDate = elm_datetime + datetime.timedelta(minutes=1)
            upDate = upDate.replace(second=0)
            elm[TS] = upDate.strftime(DATA_TIME_FORMAT)

        tr[elm[TS]] = elm.get('SpotPrice')
    return tr

def generateOutFilePath(cleanDir, inPath, fileName):
    '''
    Description:

    Parameters:

    Return:

    '''
    parentDirBaseName = os.path.basename(os.path.dirname(os.path.abspath(inPath)))
    saveDirPath = os.path.join(cleanDir, parentDirBaseName)
    os.makedirs (saveDirPath, exist_ok=True)
    savePath = os.path.join(saveDirPath, fileName)
    return savePath

def transformFromMinIncrementToWeeklyQuartiles(minuteIncDict):
    ts = minuteIncDict[TS][0].split(' ')[0]
    quartDict = {TS : [ts]*4}
    priceList = np.array(minuteIncDict['SpotPrice'])
    conv_priceList = priceList.astype(np.float)
    q1 = np.quantile(conv_priceList, 0.25)
    q2 = np.quantile(conv_priceList, 0.5)
    q3 = np.quantile(conv_priceList, 0.75)
    max = np.max(conv_priceList)
    """
    Add minimum projection to quart_dict and uncomment this block
    min = np.min(conv_priceList)
    """
    quartDict['SpotPrice'] = [q1, q2, q3, max]
    quartDict['q_id'] = ['q1', 'q2', 'q3', 'max']
    
    return quartDict
