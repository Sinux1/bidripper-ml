#!/usr/bin/env python3
'''
 * Author:    Samad Mazarei
 * Created:   9.29.2021
 * 
 * 
 * (c) Copyright - If you use my code please credit me.
'''
import json
import pandas as pd
from MyImports.MyTransFuncs import *

# Paths to root of repo and transform data directory
ROOT_OF_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLEAN_PATH_MINUTES = os.path.join(ROOT_OF_REPO, "Data", "Clean", "Minute")
CLEAN_PATH_DAILY_QUARTILES = os.path.join(ROOT_OF_REPO, "Data", "Clean", "Quartiles")
# Check for files existence, and assigne to variable
inFilePath = checkAndSetInFile(sys.argv)

# Retrieve starting datetime from in file name (begins at midnight)
starting_datetime = getDateTimeFromInFilePath(inFilePath)

# Generate save path for output file
outFileName = f'{starting_datetime.strftime(FILE_NAME_TIME_FORMAT)}.csv'
outFilePathMin = generateOutFilePath(CLEAN_PATH_MINUTES, inFilePath, outFileName)
outFilePathQuart = generateOutFilePath(CLEAN_PATH_DAILY_QUARTILES, inFilePath, outFileName)

# If file exists exit
if os.path.isfile(outFilePathMin) and os.path.isfile(outFilePathQuart):
    wMss = f'Skipping: {outFilePathMin} and {outFilePathQuart} exist'
    sys.exit(wMss)


# Read into raw from data file
with open(inFilePath, 'r') as jf:
    raw = json.load(jf)

# Transform raw data to transition_raw dictionary, clean time stamps.
transition_raw = generateTransRaw(raw, starting_datetime)

time_series_dict = transformDataToDict(starting_datetime, transition_raw)

# Now time series dict is in a form to create a pandas data frame
df = pd.DataFrame(time_series_dict)

# Set the Timestamp column as the dataframe index
df.set_index(TS, inplace=True)


# Write data frame to csv file without header
df.to_csv(outFilePathMin, header=False)

# Transform again but into daily value quartiles
quartile_dict = transformFromMinIncrementToWeeklyQuartiles(time_series_dict)

# Now daily quartiles dict is in df form for csv writing
df = pd.DataFrame(quartile_dict)

# Set the Timestamp column as the dataframe index
df.set_index(TS, inplace=True)

# Write data frame to csv file without header
df.to_csv(outFilePathQuart, header=False)
