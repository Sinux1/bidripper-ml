from os import environ
import boto3
import datetime
import sys
import json
import numpy as np
from dateutil.relativedelta import relativedelta
import pandas as pd
import io

FILE_NAME_TIME_FORMAT = "%Y_%m_%d"
DATA_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TS = "Timestamp"
C4 = "c4.8xlarge"
UPLOAD_BUCKET = environ['FORECAST_BUCKET']

S3_CLI = boto3.client('s3')
EC2_CLI = boto3.client('ec2')
S3 = boto3.resource('s3')


def default_converter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

def get_First_Moment_of_Day(date):
    fm = date.replace(hour=0).replace(minute=0).replace(second=0).replace(microsecond=0)
    return fm

def get_Last_Moment_of_Day(date):
    lm = date.replace(hour=23).replace(minute=59).replace(second=59).replace(microsecond=999999)
    return lm

def load_trigger_pipeline(data_frame, key):
    # Instantiate StringIO objects to act as files
    forDf1 = io.StringIO()
    forDf2 = io.StringIO()
    buffer = io.StringIO()
    # Retrieve bucket as resource object
    Bucket = S3.Bucket(UPLOAD_BUCKET)
    # Empty data frame 
    old_df = None
    # Generate list of objects in bucket
    prefix_objs = Bucket.objects.filter(Prefix="train/")
    # There may be up to one object in prefix
    if prefix_objs:
        # Log all objects in train/ prefix
        print(f"The following objects exist in {UPLOAD_BUCKET} prior to LOAD")
        for obj in prefix_objs:
            old_key = obj.key
            # Log key
            print(f'\t{old_key}')
            # Move on if not a csv file
            if not old_key.endswith('.csv') and not old_key.endswith('.CSV'):
                continue
            else:
                print("Previous training data loading...")
                body = obj.get()['Body'].read()
                old_df = pd.read_csv(io.BytesIO(body), encoding='utf8', index_col=0)
                break
    # Delete all objects of prefix train/
    print("Deleting previous objects")
    prefix_objs.delete()
    print("Concatenating training data with recent data")
    # Add new data to old training data if it exists
    if isinstance(old_df, pd.DataFrame):
        old_df.to_csv(forDf1)
        data_frame.to_csv(forDf2)
        csv1 = forDf1.getvalue()
        csv2 = forDf2.getvalue()
        csv2 = csv2.split("\n",1)[1]
        newcsv = f'{csv1}{csv2}'
        training_df = pd.read_csv(io.StringIO(newcsv), index_col=0)
    else:
        training_df = data_frame
    training_df.to_csv(buffer)

    # Log training data
    print(f'Abbreviated training DataFrame\n{training_df}')
    
    # Write new training data to train/ prefix
    writeToBucket(buffer.getvalue(), UPLOAD_BUCKET, "train", f'{key}.csv')

    
    


def transform_write_data(raw_data, start_time, key):

    transition_raw = generateTransRaw(raw_data, start_time)
    # Log Transitional Data
    print(f'Tranformation from raw data to parsable dictionary\n{transition_raw}')

    time_series_dict = transformDataToDict(start_time, transition_raw)

    # Now time series dict is in a form to create a pandas data frame
    df = pd.DataFrame(time_series_dict)

    # Set the Timestamp column as the dataframe index
    df.set_index(TS, inplace=True)

    print(f'Abreviated Time Series DataFrame in minutes\n{df}')

    # Write dataframe to bucket as csv
    write_df_as_csv(df, "transformed/weekly/minute", f'{key}.csv')

    # Transform again but into weekly quartile values
    # Time-series timestamp, spot-price target_value, quartiles-value item_id 
    quartile_dict = transformFromMinIncrementToWeeklyQuartiles(time_series_dict)

    # Transform quartile dictionary to pandas dataframe
    df = pd.DataFrame(quartile_dict)

    # Set the Timestamp column as the dataframe index
    df.set_index(TS, inplace=True)

    print(f'Weekly quartiles DataFrame generated from Time Series in minutes\n{df}')

    # Write dataframe to bucket prefix as csv
    write_df_as_csv(df, "transformed/weekly/quartiles", f'{key}.csv')

    # Return quartile data frame
    return df

def transformFromMinIncrementToWeeklyQuartiles(minuteIncDict):
    # Clean up time stamp
    ts = minuteIncDict[TS][0].split(' ')[0]
    # Instantiate a dictionary to track quartiles
    quartDict = {TS : [ts]*4}
    # Instantiate a numpy array of the SpotPrice column of the minuteIncDict
    priceList = np.array(minuteIncDict['SpotPrice'])
    # Convert all strings in numpy array to float64
    conv_priceList = priceList.astype(np.float64)
    # Retrieve the first 3 quartiles and max value of the SpotPrice values of the numpy array
    q1 = np.quantile(conv_priceList, 0.25)
    q2 = np.quantile(conv_priceList, 0.5)
    q3 = np.quantile(conv_priceList, 0.75)
    max = np.max(conv_priceList)
    # Assign the quartiles and quartile IDs as lists to dictionary keys
    quartDict['SpotPrice'] = [q1, q2, q3, max]
    quartDict['q_id'] = ['q1', 'q2', 'q3', 'max']
    # Return the quartile dictionary
    return quartDict

def writeToBucket(body, bucket, prefix, key):
    # Upload object to bucket using prefix to generate key
    S3_CLI.put_object(Body=body, Bucket=bucket, Key=f'{prefix}/{key}')


def write_df_as_csv(data_frame, prefix, objKey):
    csv_buffer = io.StringIO()
    data_frame.to_csv(csv_buffer, header=False)
    body = csv_buffer.getvalue()
    writeToBucket(body, UPLOAD_BUCKET, prefix, objKey)

def transformDataToDict(starting_dt, tr_dict, instanceType=C4):
    # Initiate a dictionary to build record of instance prices
    temp_ts_dict = {TS: [], "SpotPrice": [], "InstanceType": []}
    # Some variables to use for transform
    MN = 60
    HR = 24
    DAYS = 7
    prevPrice = None

    # Iterating for every minute in a week
    for i in range(MN*HR*DAYS):
        # Incrementing datetime in every iteration
        time = (starting_dt + datetime.timedelta(minutes=i)).strftime(DATA_TIME_FORMAT)
        # Checking the tr_dict for a price change at this increment
        listedPrice = tr_dict.get(time)
        # If a price change exists, update price and previous price
        if listedPrice:
            price = listedPrice
            prevPrice = price
        # If no price change exists, use previous minutes price
        else:
            price = prevPrice
        # Quick sanity check for error
        if not price:
            print("Big Problem")
            raise NameError("No Price")
            
        # Once price is established, update time, price and instance type (id)
        temp_ts_dict[TS].append(time)
        temp_ts_dict["SpotPrice"].append(price)
        temp_ts_dict["InstanceType"].append(instanceType)
    # Return fully built record
    return temp_ts_dict

def generateTransRaw(rawData, startDate):
    # Instantiate dictionary to record price and time of price change for instance type
    tr = {}
    # Raw data is a list of json objects represting price and time of price change
    # Iterate over each element in the list, transorm the data into easily parseable tr dict
    for elm in rawData:
        # Some data may include instance types other than c4.8xlarge, if so skip it
        if elm["InstanceType"] != C4:
            continue
        # Convert time entries to strings
        reformedDT = None
        # Strip timezone data from Timestamp in raw data
        elm[TS] = elm[TS].strftime(DATA_TIME_FORMAT).split('+')[0]
        # Get the datetime of the current elm's spot price change
        elm_datetime = datetime.datetime.strptime(elm[TS], DATA_TIME_FORMAT)
        # If the spot price change is prior to start time (midnight) then update to midnight
        if elm_datetime < startDate:
            reformedDT = startDate.strftime(DATA_TIME_FORMAT)
            tr[reformedDT] = elm.get('SpotPrice')
            continue
        # For every price change that occurs mid minute, forward fill to top of next minute
        if elm_datetime.second != 0:
            upDate = elm_datetime + datetime.timedelta(minutes=1)
            upDate = upDate.replace(second=0)
            elm[TS] = upDate.strftime(DATA_TIME_FORMAT)
        # Assign the price value to the datetime string key of tr dict
        tr[elm[TS]] = elm.get('SpotPrice')
    # Return tr once raw data cleaned/converted
    return tr

def extract_data(startTime, stopTime):
    # The sdk call describe_spot_price_history is paginated.
    # Using the first and last moment of the interval of interest
    # to retrieve all spot price data for the interval.
    max_results=1000
    instance_types = ['c4.8xlarge']
    filters = [
                            {
                                'Name' : 'availability-zone',
                                'Values' : [
                                    'us-west-2a'
                                ]
                            },
                            {
                                'Name' : 'product-description',
                                'Values' : [
                                    'Linux/UNIX'
                                ]
                            }
                        ]
    try:
        data_out = []
        nOfCalls = 0
        response = EC2_CLI.describe_spot_price_history(
            Filters=filters, 
            DryRun=False,
            EndTime=stopTime,
            InstanceTypes=instance_types,
            MaxResults=max_results,
            StartTime=startTime
        )
        # First page of data assigned to data out
        data_out = response.get('SpotPriceHistory')
        pagination_token = response.get('NextToken')
        while(pagination_token):
            response = EC2_CLI.describe_spot_price_history(
                Filters=filters,
                DryRun=False,
                EndTime=stopTime,
                InstanceTypes=instance_types,
                MaxResults=max_results,
                StartTime=startTime,
                NextToken=pagination_token
            )
            # Subsequent pages of data assigned to temporary data
            data = response.get('SpotPriceHistory')
            # Current page of data is appended to data_out and deleted
            data_out = data_out + data
            del data
        # Return full raw data list
        return data_out 
    except Exception as e:
        # If there is any exception, print to stdout so that data is retrieved later
        # print statements log to cloudwatch logs
        print(f'EXCEPTION:{e}')
        sys.exit("RAW DATA EXTRACTION FAILED")

def extract_write_data():

    # Determining beginning/end of interval for data to extract
    current_time = datetime.datetime.now()
    print(f"Extraction Begins: {current_time.ctime()}")
    end_interval = get_Last_Moment_of_Day(current_time - datetime.timedelta(1))
    beg_interval = get_First_Moment_of_Day(current_time - datetime.timedelta(7))
    
    # Log Collection Interval
    print(f'Collection Interval: {beg_interval.strftime(DATA_TIME_FORMAT)} - {end_interval.strftime(DATA_TIME_FORMAT)}')
    
    # Retrieve raw data
    raw_data = extract_data(beg_interval, end_interval)

    # Turn raw into pretty json
    raw_pretty = json.dumps(raw_data, indent=4, default=default_converter)

    # Log Raw Data
    print(f'Raw Data:\n{raw_pretty}')

    # Use the beginning datetime (first day of interval) as object key
    obj_key = beg_interval.strftime('%Y_%m_%d')

    # Write raw data to bucket prefix
    writeToBucket(raw_pretty, UPLOAD_BUCKET, "extracted", f'{obj_key}.json')

    # Return raw data and beginning datetime for further processing
    return raw_data, beg_interval

def lambda_handler(event, context):
    # All print statements are logged by Cloudwatch
    # Log event
    if event:
        print(event)

    # Extract/retrieves raw data, writes it to "extracted/" prefix, and returns the data.
    rData, start_datetime = extract_write_data()

    # Format start_datetime for object key
    obj_key = start_datetime.strftime('%Y_%m_%d')


    # Transform data and upload to appropriate prefixes, assign weeks quartile dataframe
    quartile_df = transform_write_data(rData, start_datetime, obj_key)

    # Load data frame to train/ prefix to trigger MLOps pipeline
    load_trigger_pipeline(quartile_df, obj_key)

    return event


if __name__ == "__main__":
    lambda_handler(None, None)