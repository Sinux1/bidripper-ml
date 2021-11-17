'''
 * Author:    Samad Mazarei
 * Created:   9.17.2021
 * 
 * 
 * (c) Copyright - If you use my code please credit me.
'''
from datetime import datetime
import threading
import boto3
from MyImports.MyTimeFuncs import get_First_Moment_of_Day, get_Last_Moment_of_Day, string_Year_Month, string_Year_Month_Day
import os
import json
import sys

# Path to directory for raw data

ROOT_OF_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RAW_PATH = os.path.join(ROOT_OF_REPO, "Data", "Raw", "Daily")

class ClientThread(threading.Thread):
	def __init__(self, date):
		'''
            Constructor
        '''
		threading.Thread.__init__(self)
		
		self.client = boto3.client('s3')
		self.start_time = get_First_Moment_of_Day(date)
		self.stop_time = get_Last_Moment_of_Day(date)
		self.out_file_parent_dir = os.path.join(RAW_PATH, string_Year_Month(date))
		self.out_file_name = f'{string_Year_Month_Day(date)}.json'
		self.out_file_path = os.path.join(self.out_file_parent_dir, self.out_file_name)
		self.client = boto3.client('ec2')
		self.instance_types = ['c4.8xlarge']
		self.max_results=1000
		self.filters = [
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

		os.makedirs (self.out_file_parent_dir, exist_ok=True)


    # This is the entry point for the thread. At this point in the code
    # the constructor has executed
	def run(self):
		# If the out put file already exists RETURN - DO NOT MNOVE FORWARD
		if os.path.exists(self.out_file_path):
			print(f'{self.out_file_path} exists, terminating thread')
			sys.exit("Data already exists")
		data_out = self.retrieve_data(self.start_time, self.stop_time)
		if data_out:	
			self.write_to_file(data_out)
		else:
			print(f'Outside 90 day window, no history for {self.start_time:%D}')
	def retrieve_data(self, startTime, stopTime):
		try:
			data_out = []
			nOfCalls = 0
			response = self.client.describe_spot_price_history(
				Filters=self.filters, 
				DryRun=False,
				EndTime=stopTime,
				InstanceTypes=self.instance_types,
				MaxResults=self.max_results,
				StartTime=startTime
			)
			nOfCalls+=1
			data = response.get('SpotPriceHistory')
			data_out = data
			del data
			pagination_token = response.get('NextToken')
			while(pagination_token):
				response = self.client.describe_spot_price_history(
					Filters=self.filters,
					DryRun=False,
					EndTime=stopTime,
					InstanceTypes=self.instance_types,
					MaxResults=self.max_results,
					StartTime=startTime,
					NextToken=pagination_token
				)
				nOfCalls += 1
				data = response.get('SpotPriceHistory')
				data_out = data_out + data
				del data

			return data_out 
		except Exception as e:
			# If there is any exception, print to stdout so that data is retrieved later
			print(f'EXCEPTION:{e}:{self.start_time:%D}')		

	def defaultconverter(self, o):
		if isinstance(o, datetime):
			return o.__str__()

	def write_to_file(self, data_out):
		with open(self.out_file_path, 'w') as jf:
			json.dump(data_out, jf, indent=4, sort_keys=True, default=self.defaultconverter)
