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


def main():
	output_file = open('state_well_count.csv','w')
	# Initialize Browser Settings:
	firefox_settings = get_firefox_settings()
	# Set browser as FireFox with our settings
	driver = webdriver.Firefox(firefox_settings)
	# Open search tool on Frac Focus
	driver.get("http://www.fracfocusdata.org/DisclosureSearch/StandardSearch.aspx")
	num_states = 51
	for state_number in range(1,num_states + 1):
		state = select_state(driver,state_number)
		state_name = state.text
		# Click on the state
		state.click()
		# Find the search button
		search_button_sequence(driver)
		page_count = driver.find_elements_by_id("MainContent_GridView1_TotalPageLabel")
		if(len(page_count) > 0):
			output_string = `state_number` + "," + state_name + "," + page_count[0].text + "\n"
			print(output_string)
			output_file.write(output_string)
		back_button = driver.find_element_by_id("MainContent_btnBackToFilter")
		back_button.click()

def search_button_sequence(driver):
	while True:
		try:
			search_button = driver.find_element_by_id("MainContent_btnSearch")
			# Search for all wells owned by that state
			search_button.click()
			break
		except:
			print("Shit went down")
			
# select_state find the next state and returns that element
def select_state(driver,state_number):
	# Find the "choose state" button
	choose_state_button = driver.find_element_by_id("MainContent_cboStateList")
	# Pull the list of all states
	all_states = choose_state_button.find_elements_by_tag_name("option")
	# Get the desired state
	return all_states[state_number]

# establish firefox settings for easy downloads and anonymity
def get_firefox_settings():
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
	return ff_prof

# The following code allows for simultaneous operation
# of 4 firefox browsers to increase download speed
if __name__ == '__main__':
	main()

