import os
import unittest

import selenium
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait

class LoginTest(unittest.TestCase):
    opts = FirefoxOptions()
    opts.add_argument("--headless")
    driver = selenium.webdriver.Firefox(options=opts)

    def setUp(self):
        fh = open('credentials.csv', 'r')
        username, password = fh.read().split(',')
        fh.close()

        print("Navigating to homepage...")
        self.driver.get("http://cliff.ssc.wisc.edu/campus_protest_dev/")

        print("Logging in...")
        self.driver.find_element(By.NAME, 'username').send_keys(username)
        self.driver.find_element(By.NAME, 'password').send_keys(password)
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