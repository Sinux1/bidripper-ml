'''
 * Author:    Samad Mazarei
 * Created:   9.17.2021
 * 
 * (c) Copyright - If you use my code please credit me.
'''
import datetime
from dateutil.relativedelta import *
import calendar

def is_Date_After_Yesterday(date):
    """
        This function will check if the date passed in occurs after the day previous to today, returning true or false.
        If the date resolves to any date after yesterday (relative to today) it will return false.
        Any day occuring prior to today will return true.

        Parameters:
            date (datetime object) : Date to be checked against todays date 
        
        Return:
            (bool)) : True or False depending on when the date passed in occurs relative to today
    """
    today = datetime.datetime.now()
    return (date.year >= today.year) and (date.month >= today.month) and (date.day >= today.day)


def string_Year_Month_Day(date):

    readable = date.strftime('%Y_%m_%d')
    return readable

def string_Year_Month(date):
    readable = date.strftime('%Y_%m')
    return readable

def string_Month_Day_Year(date):
    """
        This function will return the month in english, day, and year of a datetime object in human readable string

        Parameters:
            date (datetime object) : Date to be converted to string 
        
        Return:
            readable (string) : String representation of date parameter in human readable form
    """
    readable = date.strftime('%b_%d_%Y')
    return readable

def get_First_Moment_of_Day(date):
    fm = date.replace(hour=0).replace(minute=0).replace(second=0).replace(microsecond=0)
    return fm

def get_Last_Moment_of_Day(date):
    lm = date.replace(hour=23).replace(minute=59).replace(second=59).replace(microsecond=999999)
    return lm

def string_Month_Year(date):
    """
        This function will return the month in english, and year of a datetime object in human readable string

        Parameters:
            date (datetime object) : Date to be converted to string 
        
        Return:
            readable (string) : String representation of date parameter in human readable form
    """
    readable = date.strftime('%b_%Y')
    return readable

def get_Number_of_Days_in_Month(date):
    """
        This function will return the number of days in the month passed in as a datetime object

        Parameters:
            date (datetime object) : Date whose month we calculate number of months from 
        
        Return:
            nOfDaysInMonth (datetime object) : Number of days in month passed in from date parameter
    """
    month = date.month
    year = date.year
    nOfDaysInMonth = calendar.monthrange(year, month)[1]
    return nOfDaysInMonth

def get_First_Moment_Of_Month(date):
    """
        This function will return the first moment of the previous month

        Parameters:
            date (datetime object) : Date to calculate first moment of month from 
        
        Return:
            date (datetime object) : First moment of the month passes in as date
    """
    date = date.replace(day=1).replace(hour=0).replace(minute=0).replace(second=0).replace(microsecond=0)
    return date


def get_Last_Moment_Of_Month(date):
    """
        This function will return the last moment of the month passed in as datetime object

        Parameters:
            date (datetime object) : Date to calculate last moment of month from 
        
        Return:
            date (datetime object) : Last moment of the month passes in as date
    """
    firstDay = date.replace(day=1).replace(hour=0).replace(minute=0).replace(second=0).replace(microsecond=0)
    firstDayNextMonth = firstDay + relativedelta(months=1)
    
    lastDayOfMonth = firstDayNextMonth - datetime.timedelta(days=1)
    return lastDayOfMonth

def first_And_Last_of_Month(month):
    """
        This function will call get_First_Moment_Of_Month() and get_Last_Moment_Of_Month(),
        to get the first and last moments of a given datetime month

        Parameters:
            date (datetime object) : Date to calculate first and last moment of month from 
        
        Return:
            first, last (datetime objects) : first represents first moment of date arg, last represents last moment of date arg
    """
    first, last = get_First_Moment_Of_Month(month), get_Last_Moment_Of_Month(month)
    return first, last
