import csv
import unittest

from selenium.webdriver import Firefox, FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait

class LoginTest(unittest.TestCase):
    opts = FirefoxOptions()
    opts.add_argument("--headless")
    driver = Firefox(options=opts)

    def setUp(self):
        users = {}
        with open('credentials.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                users[row[0]] = row[1]

        print("Navigating to homepage...")
        self.driver.get("http://cliff.ssc.wisc.edu/campus_protest_dev/adj")

        print("Logging in...")
        self.driver.find_element(By.NAME, 'username').send_keys('adj1')
        self.driver.find_element(By.NAME, 'password').send_keys(users['adj1'])
        self.driver.find_element(By.NAME, 'login').send_keys(Keys.ENTER)

    def tearDown(self):
        self.driver.quit()

    ## Tests
    def test_login(self):
        el = WebDriverWait(driver = self.driver, timeout = 10).\
            until(lambda d: d.find_element_by_link_text("Home"))
        self.assertEqual(el.text, "Home")
        
if __name__ == "__main__":
    unittest.main()