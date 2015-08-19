# Created by Patrick Sheehan
# The following code:
	# 1. goes to fracfocus.org
	# 2. iterates through the list of states (to ensure less than 2,000 search results)
	# 3. downloads all well PDFs for each state (separate folder for each state)
	# 4. retains a count of all state and folder downloads for redundancy
	#	and to ensure that each state does indeed have less than 2,000 wells

# Import selenium bindings
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time # To have time delay capabilities
import multiprocessing as mp # To run multiple browsers
from watchdog.events import FileSystemEventHandler # To detect download
# from watchdog.observers import Observer                              # General Observer
from watchdog.observers.fsevents import FSEventsObserver as Observer   # Mac OS X


def main_process():
	# Initialize parallel processes
	pool = mp.Pool(num_processes) # Start multiple threads
	results = pool.map_async(download_pdfs_for_state,range(0,num_processes)) # run
	results.get()
	return 0

def download_pdfs_for_state(process_number):
	(driver,download_folder) = setup_driver(process_number,state_number) # Set up browser
	get_search_results_for_state(state_number,driver) # Get search results for state
	max_page = get_max_page(driver) # Find total number of result pages
	current_page = initialize_with_page(first_page,process_number,driver) # Initialize start page

	while current_page <= max_page: # Download all PDFs
		print("State: " + `state_number` + " Beginning page: " + `current_page`) 	
		PDFs = driver.find_elements_by_css_selector('input') # Get all of the possible PDF links
		for PDF in PDFs: # Find which ones are actually PDF links
			if PDF.get_attribute("src") == "http://www.fracfocusdata.org/Images/pdf-icon-48x48.png":
				while(initiate_download(PDF,download_folder) == -1):
					print("Clicking PDF again in page: " + `current_page`)
		for i in range(0,num_processes): 
			go_to_next_page(driver,current_page) # Go to next page
			current_page += 1 # Increment counter
			
	driver.close()
	return current_page

def go_to_next_page(driver,current_page):
	next_button = driver.find_elements_by_id("MainContent_GridView1_ButtonNext")
	if(len(next_button) == 0):
		return 1
	while True:
		try:
			next_button[0].click()
			WebDriverWait(driver,100).until(
				EC.text_to_be_present_in_element_value(
					(By.ID,"MainContent_GridView1_PageCurrent"),`current_page+1`
				)
			)
			break
		except:
			print("Took too long to go to the next page, going to click again")
	return 0

def get_max_page(driver):
	WebDriverWait(driver,400).until(
		EC.presence_of_element_located((By.ID,"MainContent_GridView1_TotalPageLabel"))
	)
	return int(driver.find_element_by_id("MainContent_GridView1_TotalPageLabel").text)

def get_search_results_for_state(state_number,driver):
	state = select_state(driver,state_number) # select the desired state
	state.click() # Click on the state
	search_button = driver.find_element_by_id("MainContent_btnSearch") # Find the search button
	search_button.click() # Search for all wells owned by that state
	return 0

def setup_driver(process_number,state_number):
	download_folder = base_folder
	#download_folder += `state_number` + "_" + `process_number+1`
	firefox_settings = get_firefox_settings(download_folder)
	driver = webdriver.Firefox(firefox_settings)
	driver.get("http://www.fracfocusdata.org/DisclosureSearch/StandardSearch.aspx")
	return (driver,download_folder)

def initialize_with_page(first_page,process_number,driver):
	first_page += process_number
	if(first_page > 1):
		page_input = driver.find_element_by_id("MainContent_GridView1_PageCurrent")
		page_input.clear()
		page_input.send_keys(str(first_page))
		go_button = driver.find_element_by_id("MainContent_GridView1_GoBtn")
		go_button.click()
		WebDriverWait(driver,400).until(
			EC.presence_of_element_located((By.ID,"MainContent_GridView1_ButtonPrev"))
		)
	return first_page

class MyEventHandler(FileSystemEventHandler):
	def __init__(self, observer):
		self.observer = observer
	def on_created(self, event):
		if not event.src_path.endswith(".pdf"):
			global check
			check = 1 # signal download complete

# ensure that we have actually downloaded the file
def initiate_download(PDF,download_folder):
	file_location = download_folder
	global check
	check = 0
	time_passed = 0
	observer = Observer()
	event_handler = MyEventHandler(observer)
	observer.schedule(event_handler, file_location)
	observer.start()
	PDF.click()
	while(check == 0):
		time.sleep(1) # wait for download signal
		time_passed += 1
		if(time_passed > 10):
			observer.stop()
			observer.join()
			return -1
	observer.stop()
	observer.join()
	return 0



# select_state finds the next state and returns that element
def select_state(driver,state_number):
	choose_state_button = driver.find_element_by_id("MainContent_cboStateList")
	all_states = choose_state_button.find_elements_by_tag_name("option")
	return all_states[state_number]

# establish firefox settings for easy downloads and anonymity
def get_firefox_settings(download_folder):
	# Get my browser settings
	ff_prof = webdriver.FirefoxProfile()
	# Set some privacy settings
	ff_prof.set_preference( "places.history.enabled", False )
	ff_prof.set_preference( "privacy.clearOnShutdown.offlineApps", True )
	ff_prof.set_preference( "privacy.clearOnShutdown.passwords", True )
	ff_prof.set_preference( "privacy.clearOnShutdown.siteSettings", True )
	ff_prof.set_preference( "privacy.sanitize.sanitizeOnShutdown", True )
	ff_prof.set_preference( "signon.rememberSignons", False )
	ff_prof.set_preference( "network.cookie.lifetimePolicy", 2 )
	ff_prof.set_preference( "network.dns.disablePrefetch", True )
	ff_prof.set_preference( "network.http.sendRefererHeader", 0 )
	# Set socks proxy to prevent IP blockage (requires Tor)
	ff_prof.set_preference( "network.proxy.type", 1 )
	ff_prof.set_preference( "network.proxy.socks_version", 5 )
	ff_prof.set_preference( "network.proxy.socks", '127.0.0.1' )
	ff_prof.set_preference( "network.proxy.socks_port", 9150 )
	ff_prof.set_preference( "network.proxy.socks_remote_dns", True )
	# Set automatic downloads
	ff_prof.set_preference( "pdfjs.disabled",True)
	ff_prof.set_preference( "browser.download.manager.showWhenStarting",False)
	ff_prof.set_preference( "browser.helperApps.alwaysAsk.force", False)
	ff_prof.set_preference( "browser.download.folderList",2)
	ff_prof.set_preference( "browser.helperApps.neverAsk.saveToDisk","application/pdf")
	ff_prof.set_preference( "browser.download.dir", download_folder)
	return ff_prof

if __name__ == '__main__':
	# Where is the download folder?
	base_folder = "/Users/Patrick/Desktop/"
	# How many threads?
	num_processes = 3
	# Which start page?
	first_page = 1
	# Which states do you want to download the PDFs for?
	state_list = [6,37,35,39,45,51,4,32,5,19,49,36,17,27,1,47,2,25]
	for state_number in state_list:
		main_process()
