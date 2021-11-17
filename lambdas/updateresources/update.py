import re
from datetime import datetime
import io
from boto3 import client, resource
import pandas as pd
import json


S3_CLI = client('s3')
S3 = resource('s3')


def get_type_string(forecast_type):
    try:
        return 'p{:.0f}'.format(float(forecast_type) * 100)
    except ValueError:
        return forecast_type


# Move an object within the specified bucket.
def move_object(bucket, source, destination):
    S3_CLI.copy_object(
        Bucket=bucket,
        CopySource='{bucket}/{key}'.format(bucket=bucket, key=source),
        Key=destination
    )
    S3_CLI.delete_object(Bucket=bucket, Key=source)

def transform(bucket_name):
    # Transform forecast output to single, easily parseable, json file
    Bucket = S3.Bucket(bucket_name)
    prefix_df = []
    prefix_objs = Bucket.objects.filter(Prefix="tmp/")
    # Read through all csv files in tmp/ and concatenate them into a pandas df
    for obj in prefix_objs:
        key = obj.key
        # Move on if not a csv file
        if not key.endswith('.csv') and not key.endswith('.CSV'):
            continue
        body = obj.get()['Body'].read()
        temp = pd.read_csv(io.BytesIO(body), encoding='utf8')        
        prefix_df.append(temp)
    # Concatenate to new df object
    new_df = pd.concat(prefix_df)
    # Replace default index with item_id (q1, q2, q3, or max)
    new_df.set_index('item_id', inplace=True)
    # Forecast dictionary will conatain forecasted values
    forecast_dict = {"Forecast" : {}}
    # Extract Y_M_D for file name from timestamp in forecasted data
    date = f'{new_df.at["max", "date"]}'.split("T")[0]

    forecast_dict["Forecast"]["Date"] = date
    # Iterate over the df rows, defining the quartiles with their predicted values
    for item_id, row in new_df.iterrows():
        forecast_dict["Forecast"][item_id] = row['p50']
    # Dump dictionary into prettified json object and sort the keys
    json_body = json.dumps(forecast_dict, indent=4, sort_keys=True)
    # Define object key
    json_file_key = f'tmp/{date}.json'

    S3_CLI.put_object(Body=json_body, Bucket=bucket_name, Key=json_file_key)
    return json_file_key


def lambda_handler(event, context):
    outdated_objects = S3_CLI.list_objects_v2(
        Bucket=event['bucket'], Prefix='current'
    )
    new_objects = S3_CLI.list_objects_v2(Bucket=event['bucket'], Prefix='tmp/')
    if 'Contents' in outdated_objects.keys():
        for key in [obj['Key'] for obj in outdated_objects['Contents']]:
            move_object(
                bucket=event['bucket'],
                source=key,
                destination='history/clean/{}'.format(key.split('/')[1])
            )
    if 'Contents' in new_objects.keys():
        # transorm objects into json
        current_fc_key = transform(event['bucket'])
        for page, key in enumerate([obj['Key'] for obj in new_objects['Contents']]):
            if re.match('^.*\.(csv|CSV)', key):
                move_object(
                    bucket=event['bucket'],
                    source=key,
                    destination='history/raw/{}'.format(key.split('/')[1])
                )
        move_object(
            bucket=event['bucket'],
            source=current_fc_key,
            destination='current/{}'.format(current_fc_key.split('/')[1])
        )

    return event
