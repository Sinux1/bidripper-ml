#!/usr/bin/env python3
'''
 * Author:    Samad Mazarei
 * Created:   9.17.2021
 * 
 * (c) Copyright - If you use my code please credit me.
'''
import datetime
from subprocess import Popen
from dateutil.relativedelta import relativedelta

# AWS only provides 3 months of spot price history so we go
# back 3 months and make a list of strings to pass as args to Collect.py
# including the current month
todays_date = datetime.datetime.now()
three_months_ago = todays_date - relativedelta(months=3)
months_of_interest = []

for i in range(4):
    tMonth = three_months_ago + relativedelta(months=i)
    months_of_interest.append(tMonth.strftime("%m-%Y"))

# Main will create a subprocess and call Collect.py and pass the args
def main():

    # Retrive data up to yesterday
    for month in months_of_interest:
        p = Popen(["python3", "./Collect.py", month])
        p.wait()
# Entry point for script
if __name__ == "__main__":
    main()
    