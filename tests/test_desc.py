import csv
import sys
import time
import unittest

sys.path.insert(0, '/var/www/campus_protest_dev')

from database import db_session
from models import CodeEventCreator

from sqlalchemy import desc

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
        self.driver.find_element(By.NAME, 'username').send_keys('test1')
        self.driver.find_element(By.NAME, 'password').send_keys(users['test1'])
        self.driver.find_element(By.NAME, 'login').send_keys(Keys.ENTER)

        WebDriverWait(driver = self.driver, timeout = 10).\
            until(lambda d: d.find_element_by_link_text("Home"))

    def tearDown(self):
        ## remove all test fields
        q = db_session.query(CodeEventCreator).\
            filter(CodeEventCreator.coder_id == 2)
        q.delete()
        db_session.commit()

        ## shut down firefox
        self.driver.quit()

    ## Tests
    def test_add_desc(self):
        self.driver.get("http://cliff.ssc.wisc.edu/campus_protest_dev/event_creator/319")
        WebDriverWait(driver = self.driver, timeout = 10).\
            until(lambda d: d.find_element_by_id("add-event"))

        ## Click add event 
        self.driver.find_element_by_id("add-event").click()
        WebDriverWait(driver = self.driver, timeout = 10).\
            until(lambda d: d.find_element_by_id("info_article-desc"))

        ## find text box and add
        self.driver.find_element_by_id("info_article-desc").send_keys("This is a test of adding text.")
        # time.sleep(1)

        self.driver.find_element_by_id("info_desc").send_keys("Adding text to the event description.")
        # time.sleep(1)

        ## get the fields from the database
        q = db_session.query(CodeEventCreator).\
            filter(CodeEventCreator.coder_id == 2)
        texts = [x.value for x in q]

        ## TK: This doesn't actually work yet! Not sure why.
        self.assertIn("This is a test of adding text.", texts)
        self.assertIn("Adding text to the event description.", texts)
        
if __name__ == "__main__":
    unittest.main()