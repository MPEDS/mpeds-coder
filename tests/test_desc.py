import csv
import sys
import time
import unittest

sys.path.insert(0, '/var/www/campus_protest_dev')

from database import db_session
from models import CodeEventCreator, Event

from sqlalchemy import desc

from selenium.webdriver import Firefox, FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait

class EventAddTest(unittest.TestCase):
    driver = None

    def setUp(self):
        print("SET-UP")
        ## spin up new firefox session
        opts = FirefoxOptions()
        opts.add_argument("--headless")
        self.driver = Firefox(options=opts)

        users = {}
        with open('credentials.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                users[row[0]] = row[1]

        ## Delete all the test entries
        q = db_session.query(CodeEventCreator).\
            filter(CodeEventCreator.coder_id == 2)
        q.delete()
        db_session.commit()

        self.driver.get("http://cliff.ssc.wisc.edu/campus_protest_dev")

        self.driver.find_element(By.NAME, 'username').send_keys('test1')
        self.driver.find_element(By.NAME, 'password').send_keys(users['test1'])
        self.driver.find_element(By.NAME, 'login').send_keys(Keys.ENTER)

        WebDriverWait(driver = self.driver, timeout = 10).\
            until(lambda d: d.find_element_by_link_text("Event Coder Interface"))

        ## Head to event page and click add-event
        self.driver.get("http://cliff.ssc.wisc.edu/campus_protest_dev/event_creator/319")
        addevent = WebDriverWait(driver = self.driver, timeout = 10).\
            until(lambda d: d.find_element_by_id("add-event"))
        addevent.click()

        ## wait until article-desc box loads
        WebDriverWait(driver = self.driver, timeout = 10).\
            until(lambda d: d.find_element_by_id("info_article-desc"))


    def tearDown(self):
        ## Logout
        print("TEAR DOWN")
        self.driver.find_element_by_link_text("Logout").click()

        ## remove all test codings
        cecs = db_session.query(CodeEventCreator).filter(CodeEventCreator.coder_id == 2)

        ## remove all the test events
        events = db_session.query(Event).filter(Event.id.in_([x.event_id for x in cecs]))

        cecs.delete()
        events.delete()

        db_session.commit()

        ## shut down firefox
        self.driver.quit()

    ###
    ## Tests
    ###
    def test_add_desc(self):        
        ## find text box and add descriptions
        self.driver.find_element_by_id("info_article-desc").send_keys("This is a test of adding text.")
        self.driver.find_element_by_id("info_desc").send_keys("Adding text to the event description.")
        self.driver.find_element_by_id("info_start-date").click()

        ## get the fields from the database
        q = db_session.query(CodeEventCreator).\
            filter(CodeEventCreator.coder_id == 2)
        texts = [x.value for x in q]

        self.assertIn("This is a test of adding text.", texts)
        self.assertIn("Adding text to the event description.", texts)


    def test_add_dates(self):
        d = {}
        self.driver.find_element_by_id("info_start-date").send_keys("2020-07-20")
        self.driver.find_element_by_id("info_end-date").send_keys("2020-07-21")
        self.driver.find_element_by_id("info_location").send_keys("Chicago, IL, USA")
        self.driver.find_element_by_id("info_start-date").click()

        for a in db_session.query(CodeEventCreator).filter(CodeEventCreator.coder_id == 2).all():
            d[a.variable] = a.value

        self.assertIn("2020-07-20", d["start-date"])
        self.assertIn("2020-07-21", d["end-date"])
        self.assertIn("Chicago, IL, USA", d["location"])


    def test_yesno(self):
        ## Test the Yes/No pane
        yesno = WebDriverWait(driver = self.driver, timeout = 10).\
            until(lambda d: d.find_element_by_id("yes-no_button"))
        yesno.click()

        ## Click "exact" in Date
        self.driver.find_element_by_id("info_date-est").click()
        q = db_session.query(CodeEventCreator).\
            filter(CodeEventCreator.coder_id == 2, CodeEventCreator.variable == "date-est").first()
        #self.assertEqual(q.value, "exact")
        
        ## Click "One" in duration
        self.driver.find_element_by_id("info_duration").click()
        q = db_session.query(CodeEventCreator).\
            filter(CodeEventCreator.coder_id == 2, CodeEventCreator.variable == "duration").first()
        self.assertEqual(q.value, "one") 

        qs = db_session.query(CodeEventCreator).filter(CodeEventCreator.coder_id == 2).all()
        print([(x.variable, x.value) for x in qs])

        ## Click "off-campus with no higher ed issue"
        self.driver.find_element_by_id("l_info_non-campus").click()
        q = db_session.query(CodeEventCreator).\
            filter(CodeEventCreator.coder_id == 2, CodeEventCreator.variable == "non-campus").first()
        self.assertEqual(q.value, "yes") 
        
        ## Click "off-campus with a higher ed issue"
        self.driver.find_element_by_id("l_info_off-campus").click()
        q = db_session.query(CodeEventCreator).\
            filter(CodeEventCreator.coder_id == 2, CodeEventCreator.variable == "off-campus").first()
        self.assertEqual(q.value, "yes") 

    # def test_text_select(self):
    #     ## TK: test text selects
    #     pass

    # def test_presets(self):
    #     ## TK: test presets
    #     pass
        
if __name__ == "__main__":
    unittest.main()