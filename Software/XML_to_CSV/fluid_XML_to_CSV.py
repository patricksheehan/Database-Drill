#!/usr/bin/python
# Converts XML files from Frac Focus PDFs into a HF fluid CSV table
# Created by: Patrick Sheehan

import os
import csv
import glob
import logging
import re
import sys
import traceback
from lxml import etree
# from bs4 import BeautifulSoup # (not currently used)
from operator import attrgetter # for sorting the element lists

# Globals
report_identifier = 'No current report' # unique id for each report
# Column alignment values determined statistically in "lefthist.R"
TRADE_NAME_COL = [60,80]	# Trade name
SUPPLIER_COL = [180,200]	# Supplier
PURPOSE_COL = [305,325]     # Purpose
INGREDIENT_COL = [430,450]  # Ingredient
CAS_COL = [610,630]    		# CAS
ADD_CONC_COL = [775,805]    # Concentration in additive
CONC_FLUID_COL = [860,905]      # Concentration in HF fluid / Comments
COMMENTS_COL = [930,950]    	# Comments 
MAX_WIDTH = 500 # Maximum fluid info width (elements larger are annotations)

class Cell(object):
	""" Class for each cell of the original PDF report containing the xml page
		number and "top" positioning which I take to be the effective "row" of
		the data.

		Note: cells in the original PDF which span multiple lines will be
			 recoreded as multiple cells. This issue is dealt with in the 
			 function "create_table_from_columns()"
	"""
	def __init__(self, text= "", page= None, row= None, column= None):
		self.text = text
		self.page = page
		self.row = row
		self.column = column
	def __eq__(self, other):
		return self.page == other.page and self.row == other.row
	def __lt__(self, other):
		if self.page < other.page:
			return True
		else:
			return self.page == other.page and self.row < other.row
	def __le__(self, other):
		return self < other or self == other
			
def fluid_xml_to_csv(directory):
	""" High-level function to run XML to CSV conversion

	- Sets the directory where the XML files to be converted are located
	- Grabs the file path of all XML files in the XML directory
	- Sets the directory for the result CSV file
	- Establishes the headers for the CSV file
	- Calls the XML info extraction function
	- Calls the CSV write function to write the result into a CSV file

	Args: None
	Returns: None
	"""
	xml_directory = directory
	xml_files = os.path.join(xml_directory, '*.xml')
	csv_directory = '../../Data/CSV'
	headers = ['Report_Identifier', 'Trade_Name', 'Supplier', 'Purpose', 
			   'Ingredient', 'CAS_Number', 'Max_Concentration_Additive',
			   'Max_Concentration_Fluid', 'Comments']
	fluid_info = extract_fluid_info(xml_files)
	write_csv('fluid_info.csv', headers, fluid_info,csv_directory)
	return None

def extract_fluid_info(xml_files):
	""" Iterate over all XML files and call fluid info table extraction method

	- Parses each file into an XML Element Tree
	- Extracts the fluid info table from each element tree

	Args: 
			xml_files: List of names of all XML files in XML directory
	Returns:
			fluid_info: Table containing fluid info table from all XML files 
	"""
	global report_identifier # refer to global for logging purposes
	fluid_info = [] # Initialize
	for xml_filepath in glob.glob(xml_files): # For all XML files
		report_identifier = os.path.basename(xml_filepath)[:-4] # get report ID
		parser = etree.XMLParser(encoding='utf-8') # Use lxml to parse
		xml_data = etree.parse(xml_filepath,parser) # get the xml data
		assert len(parser.error_log) == 0 # expect no errors in parsing
		fluid_table = extract_fluid_table(xml_data) # parse xml
		fluid_info += fluid_table
	return fluid_info

def extract_fluid_table(xml_data):
	""" Get fluid info table for a single report
	Args:
			xml_data: iterator for the xml-converted PDF well report
	Returns:
			fluid_table: a list of rows for the fluid info CSV file containing
						the fluid info for the single well report 
	"""
	# First, skip over the well table at the top of each report
	(fluid_elements, min_top) = skip_to_fluid_elements(xml_data)
	columns = extract_columns(fluid_elements, min_top) # get the report columns
	fluid_table = create_table_from_columns(columns) # analyze columns for data
	return fluid_table

def create_table_from_columns(columns):
	""" Use the information and position values in columns to fill a
		csv-appropriate table which reflects the data in the original well
		report

		Note: will skip lines without a fluid concentration value
	Args:
			columns: dictionary containing lists of data for each data column
	Returns:
			fluid_table: a list of rows for the fluid info CSV file containing
						the fluid info for the single well report 
	"""
	fluid_table = [] # Initialize
	# First, sort each column by page number then by row number
	for column_name in columns: 
		columns[column_name].sort(key = attrgetter('page','row'))
	# Next, fill fluid_table in the format of the final CSV file using the 
	# information from the cells in the PDF report
	# Use the fluid concentration as a reference
	conc_ref = get_next_ref(['Fluid Concentrations'], columns)
	info_ref = get_next_ref(['Trade Names', 'Suppliers', 'Purposes'], columns)
	# While there is still concentration data
	while columns['Fluid Concentrations']:
		# get the next set of info which applies to multiple conc data points
		trade_name = pop('Trade Names', columns, info_ref, conc_ref)
		supplier = pop('Suppliers', columns, info_ref, conc_ref)
		purpose = pop('Purposes', columns, info_ref, conc_ref)
		next_info_ref = get_next_ref(['Trade Names', 'Suppliers', 'Purposes'],
									 columns)
		# While the current fluid concentration data applies to the same
		# Trade name, supplier, and purpose data
		while info_ref <= conc_ref and conc_ref < next_info_ref:
			fluid_conc = pop('Fluid Concentrations', columns, conc_ref,conc_ref)
			next_conc_ref = get_next_ref(['Fluid Concentrations'], columns)
			add_conc = pop('Additive Concentrations', columns, conc_ref, 
			               next_conc_ref)
			ingredient = pop('Ingredients', columns, conc_ref, next_conc_ref)
			cas_number = pop('CAS Numbers', columns, conc_ref, next_conc_ref)
			comment = pop('Comments', columns, conc_ref, next_conc_ref)
			fluid_table.append([report_identifier, trade_name, supplier,
								purpose, ingredient, cas_number, add_conc,
								fluid_conc, comment])
			conc_ref = next_conc_ref
		info_ref = next_info_ref
	return fluid_table

def get_next_ref(column_names, columns):
	""" Finds the next closest reference point to collect data. A reference
		point is an element in the table with the lowest location in the table
		determined by the page number and row location. This helps to ensure
		that no rows are skipped due to missing values in one column

		Args: column_names: list of names of columns to search for the next ref
			  columns: dictionary of all table columns
	    Returns:
	    	  reference: Lowest cell amongst the columns specified
	"""
	possible_references = []
	for column_name in column_names:
		if columns[column_name]:
			possible_references.append(columns[column_name][0])
	if possible_references:
		reference = min(possible_references)
	else:
		reference = Cell(text= 'Empty', page= float("inf"), row= float("inf"))
	return reference

def pop(column_name, columns, row_start, row_end):
	""" Pops off the next element of the given column, matches it with the
		position of the reference given, and matches the element text with
		the given format if a format is given

		Args: column_name: name of the column to be popped
			  columns: dictionary containing all table data
			  reference: Cell passed as a reference for the location of the row
			  data_format: regular expression to be matched to the popped text
		returns: text for the desired column element
	"""
	while columns[column_name] and columns[column_name][0] < row_start:
		skip = columns[column_name].pop(0)
		logger.critical("Missed a line: text= %s, row= %d", skip.text, skip.row)
	if columns[column_name] and columns[column_name][0] == row_start:
		item = columns[column_name].pop(0)
	else:
		item = Cell()
	while columns[column_name] and columns[column_name][0] < row_end:
		item.text += columns[column_name].pop(0).text
	return item.text.replace(",","") # return element value without ','

def extract_columns(fluid_elements, min_top):
	""" With a set of elements which we believe to be the fluid info table,
		iterate over each element, record its xml-identified positioning, and
		sort each element into its appropriate column, skipping elements which
		do not belong in any column and logging elements which do not appear to
		fit in any of the column boundaries which were determined by a histogram
		of all positioning data for all fluid tables in all XML files

	Args:
			fluid_elements: iterator for the PDF report fluid info table data
	Returns:
			columns: a dictionary of lists which contains the information for
					the data under each column in the PDF report 
	"""
	columns = { # Initialize columns as a dictionary of lists
				'Trade Names': [],
				'Suppliers': [],
				'Purposes': [],
				'Ingredients': [],
				'CAS Numbers': [],
				'Additive Concentrations': [],
				'Fluid Concentrations': [],
				'Comments': []}
	page_number = 1
	# Now, fill the columns based on the positioning of the XML elements
	for fluid_element in fluid_elements:
		if fluid_element.tag != "text":
			if fluid_element.tag == "page":
				page_number += 1 # confirmed pages are in order for all files
			continue
		top = int(fluid_element.get("top") or -1) # top position of text
		if top < min_top and page_number == 1:
			logger.warning("Might be out-of-page order: text= %s",
						   fluid_element.text)
			continue # This element is in the other table
		width = int(fluid_element.get("width") or -1) # width of field	
		if width > MAX_WIDTH:
			continue # Not fluid info element
		column_name = get_column_name(fluid_element)
		if column_name:
			current_cell = Cell(fluid_element.text, page_number,top,column_name)
			columns[column_name].append(current_cell)
	return columns

def get_column_name(fluid_element):
	""" Returns the name of the column which corresponds to the position
		of the given xml element. If the position of the element (determined by
		"lefthist.R") is outside of all column boundaries, an error is logged
		and None is returned

	Args:
			fluid_element: xml element 
	Returns:
			string of column name corresponding to xml element
	"""
	left = int(fluid_element.get("left") or -1) # left position of text
	if TRADE_NAME_COL[0] < left and left < TRADE_NAME_COL[1]:
		return 'Trade Names'
	elif SUPPLIER_COL[0] < left and left < SUPPLIER_COL[1]:
		return 'Suppliers'
	elif PURPOSE_COL[0] < left and left < PURPOSE_COL[1]:
		return 'Purposes'
	elif INGREDIENT_COL[0] < left and left < INGREDIENT_COL[1]:
		return 'Ingredients'
	elif CAS_COL[0] < left and left < CAS_COL[1]:
		return 'CAS Numbers'
	elif ADD_CONC_COL[0] < left and left < ADD_CONC_COL[1]:
		return 'Additive Concentrations'
	elif CONC_FLUID_COL[0] < left and left < CONC_FLUID_COL[1]:
		return 'Fluid Concentrations'
	elif COMMENTS_COL[0] < left and left < COMMENTS_COL[1]:
		return 'Comments'
	else:
		logger.critical("Element out of bounds: text= %s left= %d",
					   fluid_element.text, left)
	return None

def skip_to_fluid_elements(xml_data):
	""" Skip over well info table in PDF

	Args:
			xml_data: iterator for the PDF report XML data 
	Returns:
			fluid_elements: iterator at position of start of fluid info table 
			min_top: Minimum top alignment value to check that elements in xml
					document are in top-to-bottom order
	"""
	# First, establish where the two tables in the PDF document are separate
	# in the XML document
	trade_name_element = xml_data.xpath('.//text[text()="Trade Name"]')
	min_top = int(trade_name_element[0].get("top") or -1)
	xml_data_elements = xml_data.iter()
	for element in xml_data_elements:
		if element.text == 'Trade Name': # past the well info table
			break
		# check that no fluid information is being passed over
		try:
			assert  int(element.get("top") or -1) <= min_top
		except:
			# On all microsoft xml documents confirmed that no actual info is
			# passed over, only note text
			logger.warning("Possible fluid info being passed over: text= %s",
							 element.text)
	# Test for consistent column ordering
	skip_column_names(xml_data_elements)
	fluid_elements = xml_data_elements
	return (fluid_elements, min_top) 

def skip_column_names(xml_data):
	""" Both skips and checks column names for consistency

	Args:
			xml_data: iterator for the PDF report XML data 
	Returns:
			None
	"""
	try:
		assert xml_data.next().text == 'Supplier'
		assert xml_data.next().text == 'Purpose'
		assert xml_data.next().text == 'Ingredients'
		assert xml_data.next().text == 'Chemical'
		assert 'Abstract' in xml_data.next().text
		partial_column = xml_data.next().text
		if partial_column == 'Service':
			assert xml_data.next().text == 'Number'
		else:
			assert partial_column == 'Number'
		assert xml_data.next().text == '(CAS #)'
		assert xml_data.next().text == 'Maximum '
		assert xml_data.next().text == 'Ingredient '
		assert 'Concentration' in xml_data.next().text
		assert 'Additive' in xml_data.next().text
		assert xml_data.next().text == r'(% by mass)**'
		assert xml_data.next().text == 'Maximum '
		assert xml_data.next().text == 'Ingredient '
		assert 'Concentration' in xml_data.next().text
		assert 'HF Fluid' in xml_data.next().text
		assert xml_data.next().text == r'(% by mass)**'
		assert xml_data.next().text == 'Comments'
	except:
		logger.critical("Column parsing failed")
		_, _, tb = sys.exc_info()
		traceback.print_tb(tb) # Fixed format
		tb_info = traceback.extract_tb(tb)
		filename, line, func, text = tb_info[-1]
		print('An error occurred on line {} in statement {}'.format(line, text))
	return None

def write_csv(filename,headers,info,csv_directory):
	csv_filepath = os.path.join(csv_directory,filename)
	with open(csv_filepath, 'w') as csv_file:
		csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
		csv_writer.writerow(headers)
		for row in info:
			csv_writer.writerow([data.encode('utf-8') for data in row])
	return None

class ContextFilter(logging.Filter): 
	""" Allows logger access to the report_identifier for logging purposes
	"""
	def filter(self, record):
		record.report_identifier = report_identifier
		return True

def initialize_logger(lvl):
	""" Initializes logger at the given logging level
	"""
	report_identifier = 'No report open' # initialize
	format_string = ''
	format_string += '%(report_identifier)s '
	format_string += '%(levelname)s: %(message)s' 
	logging.basicConfig(filename='fluid_XML_to_CSV.log',
						filemode='w',
						level=lvl,
						format=format_string)
	logger = logging.getLogger(__name__)
	logger.addFilter(ContextFilter())
	return logger

def main():
	fluid_xml_to_csv('../../Data/XML/Microsoft/Sample')

if __name__ == '__main__':
	logger = initialize_logger(logging.CRITICAL)
	main()
