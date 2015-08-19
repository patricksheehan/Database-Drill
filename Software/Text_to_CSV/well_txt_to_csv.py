# Converts frac focus PDF reports which are already comma-separated
# into database-style csv files
#
# Created by: Patrick Sheehan

import os
import csv
import glob
import logging
import re

def well_txt_to_csv():
	# Set up the directories for the source text files and the output CSV file
	txt_directory = '../../Data/CSVs/Well_Microsoft_delimited'
	txt_files = os.path.join(txt_directory,'*.txt')
	csv_directory = '.'

	headers = [	'Report_Identifier','API_Number','Well_Name','Operator_Name',
				'Start_Date','End_Date','State','County','Longitude','Latitude',
				'Datum','Federal_Tribal_Well','True_Vertical_Depth',
				'Total_Base_Water_Volume','Total_Base_Non_Water_Volume']
	well_info = extract_well_info(txt_files)
	write_csv('well_info.csv',headers,well_info,csv_directory,append=False)
	return None

# Extract info from group of text files
def extract_well_info(txt_files):
	logger.info('extracting well info from text files')
	well_info = [] # Initialize
	for txt_filepath in glob.glob(txt_files): # For all .txt files in txt_directory
		global report_identifier
		report_identifier = os.path.basename(txt_filepath)[:-4] # key for both files
		logger.debug('extracting info from file: %s',report_identifier)
		with open(txt_filepath,'rb') as txt_file: # Open txt file
			set_row_overflow(False) # initialize
			txt_data = csv.reader(txt_file,delimiter=',') # Read as csv
			first_row = row_to_string(next_row(txt_data))
			if 'Hydraulic' not in first_row: # if no title string found
				logger.critical('No well title string found for this txt file')
				exit()
			well_line = extract_well_info_line(txt_data)
		well_info.append(well_line)
	return well_info

# Assuming the order of the data for Microsoft reported documents
# Go through the data row by row and pull values
# Ends with next line right after total non-base water volume
def extract_well_info_line(txt_data):
	logger.info('extracting well info')
	identifier = report_identifier
	start_date = get_value_for('Job Start Date:',txt_data,date_format)
	end_date = get_value_for('Job End Date:',txt_data)
	state = get_value_for('State:',txt_data)
	county = get_value_for('County:',txt_data)
	api_number = get_value_for('API Number:',txt_data,api_format)
	operator_name = get_value_for('Operator Name:',txt_data)
	well_name = get_value_for('Well Name and Number:',txt_data)
	longitude = get_value_for('Longitude:',txt_data,longitude_format)
	latitude = get_value_for('Latitude:',txt_data,latitude_format)
	datum = get_value_for('Datum:',txt_data)
	federal_or_tribal = get_value_for('Federal/Tribal Well:',txt_data)
	if federal_or_tribal == missing_data_string:
		federal_or_tribal = get_value_for('Federal Well:',txt_data)
	true_vertical_depth = get_value_for('True Vertical Depth:',txt_data,number_format)
	water_volume = get_value_for('Total Base Water Volume (gal):',txt_data,number_format)
	non_water_volume = get_value_for('Total Base Non Water Volume:',txt_data,number_format)
	return [identifier,api_number,well_name,operator_name,
			start_date,end_date,state,county,longitude,latitude,
			datum,federal_or_tribal,true_vertical_depth,water_volume,
			non_water_volume]

# Note: get_value_for assumes only 1 row overflow for now
# Also determines overflow from second element in overflow row
def get_value_for(data_name,txt_data,required_format=None):
	logger.info('Getting %s',data_name)
	data_row = next_row(txt_data) # get first data row
	data_row_string = row_to_string(data_row)
	if data_name not in data_row_string: # check for data name
		logger.warning('%s Not found',data_name)
		set_row_overflow(True) # possible overflow into different data name row
		return missing_data_string
	if required_format: # If a required format is given, search in first row for expression match
		return find_expression_in_row(data_name,required_format,data_row)
	else: # Otherwise, grab all non-title values and add them to value
		overflow_row = next_row(txt_data) # next row is possibly overflow from last row
		return find_values_in_rows(data_name,data_row_string,overflow_row)		

# Look for a regular expression in a data row
def find_expression_in_row(data_name,expression,row):
	for string in row:
		match = expression.match(string)
		if match:
			logger.debug('Found match for %s: %s',data_name,string)
			return string
	# if for-loop ends without match
	logger.warning('No match found for %s: \t Row observed: %s',data_name,row)
	return missing_data_string

# gets all strings in first row and overflow row
# if the overflow row is truly an overflow (determined by empty second element)
def find_values_in_rows(data_name,first_row,overflow_row):
	value = first_row.replace(data_name,'').lstrip() # first row of strings without data name
	if overflow_row[1]: # if not an overflow row
		set_row_overflow(True) # set overflow bit so we reuse this row
	else: # otherwise, have more value strings to add
		value += ' ' + row_to_string(overflow_row)
	if not value: # if value string is empty, we've got missing data
		logger.warning('%s value not found',data_name)
		return missing_data_string
	else:
		logger.debug('Found %s: %s',data_name,value)
		return value

# Access function to get the proper next row
# which is not necessarily the next row in the csv
# since we check for overflow in some rows
def next_row(txt_data):
	global current_row
	if row_overflow:
		set_row_overflow(False)
	else:
		current_row = txt_data.next()
	return current_row

# row_overflow is an indicator of whether or not the current row should be reused by the next
# parsing function
def set_row_overflow(value):
	global row_overflow # bool to indicate if the previous row has run into the next row
	row_overflow = value # set new value
	return None # no return value

class ContextFilter(logging.Filter):
    def filter(self, record):
        record.report_identifier = report_identifier
        return True

# Write info into csv file
def write_csv(filename,headers,info,csv_directory,append):
	csv_filepath = os.path.join(csv_directory,filename)
	if append:
		file_mode = 'a'
	else:
		file_mode = 'w'
	with open(csv_filepath, file_mode) as csv_file:
		csv_writer = csv.writer(csv_file,
									 delimiter=',',
									 quotechar='',
									 quoting=csv.QUOTE_NONE)
		csv_writer.writerow(headers)
		csv_writer.writerows(info)
	return None

# Convert row string list into a single string with
# multiple and leading white spaces removed
def row_to_string(row):
	string = ' '.join(row) # join all members of rows by spaces
	string.lstrip() # remove leading white space if there is one
	string = re.sub(r" {2,}",' ',string) # remove extra white spaces
	return string

if __name__ == '__main__':
	report_identifier = 'No report open' # initialize
	# Create logger
	format_string = ''
	format_string += '%(report_identifier)s '
	format_string += '%(levelname)s: %(message)s' 
	logging.basicConfig(filename='well_txt_to_csv.log',
						filemode='w',
						level= logging.WARNING,
						format=format_string)
	logger = logging.getLogger(__name__)
	logger.addFilter(ContextFilter())

	missing_data_string = 'Missing' # Missing data value

	# Regular expressions for data values
	api_format = re.compile(r"[0-9]{2}-[0-9]{3}-[0-9]{5}.*")
	date_format = re.compile(r"[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}")
	longitude_format = re.compile(r"-?[0-9]{1,3}\.[0-9]{8}")
	latitude_format = longitude_format
	number_format = re.compile(r"-?[0-9]+")

	well_txt_to_csv()

