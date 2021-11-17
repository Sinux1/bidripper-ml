#!/usr/bin/env python3
'''
 * Author:    Samad Mazarei
 * Created:   9.17.2021
 * 
 * (c) Copyright - If you use my code please credit me.
'''

import sys
import datetime
from dateutil.relativedelta import *
from MyImports.MyTimeFuncs import get_Number_of_Days_in_Month, is_Date_After_Yesterday, string_Month_Day_Year
from MyImports.ThreadedCollect import ClientThread
import re

# Make sure that an argujkment is correctly passed in from command line
if len(sys.argv) < 2:
    print("Not enough arguments")
    print("Command: python3 Collect.py <integer value of month>-<integer value for year>\n\tMonth range: 1-12\n\tYear Range: 2000-*")
    sys.exit("Argument not in correct format")

# Assign argument to variable
cla = sys.argv[1]

# Compile a egex that matches the form <month>-<year> with month and year as integer values
p = re.compile(r'^(0[1-9]|1[0-2])-(2[0-9]{3})$')

# Check to make sure command line arg matches the correct form
if not bool(p.match(cla)):
    print("Command: python3 Collect.py <integer value of month>-<integer value for year>\n\tMonth range: 1-12\n\tYear Range: 2000-*")
    sys.exit("Argument not in correct format")

# This returns a dateteime object representing the first day and moment of the month and year passed in as argument
month = datetime.datetime.strptime(cla, "%m-%Y")

# Check if current month, and do not collect data 
today = datetime.datetime.now()

# Pass each day of the month to a thread until the last month is passed.
numberOfDays = get_Number_of_Days_in_Month(month)

for i in range(numberOfDays):
    tData = month + datetime.timedelta(days=i)
    # Check if new date comes after yesterday (collect whole day data only)
    if is_Date_After_Yesterday(tData):
        print(f"{tData}: Cannot retrieve full day data")
        break
    # Pass date to thread
    ct = ClientThread(tData)
    # Start thread
    ct.start() 