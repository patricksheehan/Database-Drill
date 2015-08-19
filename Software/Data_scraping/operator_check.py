# Created by Patrick Sheehan
# The following code:
	# 1. goes to fracfocus.org
	# 2. iterates through the list of operators (to ensure less than 2,000 search results)
	# 3. downloads all well PDFs for each operator (separate folder for each operator)
	# 4. retains a count of all operator and folder downloads for redundancy
	#	and to ensure that each operator does indeed have less than 2,000 wells

# Import selenium bindings
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main():
	# Initialize Browser Settings:
	firefox_settings = get_firefox_settings()
	# Set browser as FireFox with our settings
	driver = webdriver.Firefox(firefox_settings)
	# Open search tool on Frac Focus
	driver.get("http://www.fracfocusdata.org/DisclosureSearch/StandardSearch.aspx")
	found_2000 = False
	num_operators = 835
	for operator_number in range(7,num_operators):
		operator = select_operator(driver,operator_number)
		operator_name = operator.text
		# Click on the operator
		operator.click()
		# Find the search button
		search_button = WebDriverWait(driver,30).until(
							EC.presence_of_element_located((By.ID,"MainContent_btnSearch"))
						)
		# Search for all wells owned by that operator
		search_button.click()
		page_count = driver.find_elements_by_id("MainContent_GridView1_TotalPageLabel")
		if(len(page_count) > 0):
			print(operator_name, page_count[0].text)
			if(int(page_count[0].text) > 99):
				found_2000 = True
		back_button = driver.find_element_by_id("MainContent_btnBackToFilter")
		back_button.click()
	if(found_2000):
		print("Some operator had more than 99 pages... fuck")
		
# select_operator find the next operator and returns that element
def select_operator(driver,operator_number):
	# Find the "choose operator" button
	choose_operator_button = driver.find_element_by_id("MainContent_cboOperator")
	# Pull the list of all operators
	all_operators = choose_operator_button.find_elements_by_tag_name("option")
	# Get the desired operator
	return all_operators[operator_number]

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

