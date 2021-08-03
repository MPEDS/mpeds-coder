# -*- coding: utf-8 -*-
import csv
import random
import sys
import time
import unittest
import yaml

sys.path.insert(0, '/var/www/campus_protest_dev')

from database import db_session
from models import CodeEventCreator, Event

from sqlalchemy import desc

from selenium import webdriver
from selenium.webdriver import Firefox, FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support import expected_conditions as EC
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

        ## remove all test codings
        cecs = db_session.query(CodeEventCreator).filter(CodeEventCreator.coder_id == 2)

        ## remove all the test events
        events = db_session.query(Event).filter(Event.id.in_([x.event_id for x in cecs]))

        cecs.delete()
        events.delete()
        db_session.commit()

        ## close the session
        db_session.close()

        ## shut down firefox
        self.driver.quit()

    ###
    ## Tests
    ###

    ## Test adding descriptions
    def test_add_desc(self):        
        ## find text box and add descriptions
        self.driver.find_element_by_id("info_article-desc").send_keys("This is a test of adding text.")
        self.driver.find_element_by_id("info_desc").send_keys("Adding text to the event description.")

        ## change focus to save
        self.driver.find_element_by_id("info_start-date").click()

        ## get the fields from the database
        q = db_session.query(CodeEventCreator).\
            filter(CodeEventCreator.coder_id == 2)
        texts = [x.value for x in q]

        self.assertIn("This is a test of adding text.", texts)
        self.assertIn("Adding text to the event description.", texts)


    ## test adding of dates and location
    def test_add_dates(self):
        d = {}
        self.driver.find_element_by_id("info_start-date").send_keys("2020-07-20")
        self.driver.find_element_by_id("info_end-date").send_keys("2020-07-21")
        self.driver.find_element_by_id("info_location").send_keys("Chicago, IL, USA")
        
        ## changes focus to start-date
        self.driver.find_element_by_id("info_start-date").click()

        for a in db_session.query(CodeEventCreator).filter(CodeEventCreator.coder_id == 2).all():
            d[a.variable] = a.value

        self.assertIn("2020-07-20", d["start-date"])
        self.assertIn("2020-07-21", d["end-date"])
        self.assertIn("Chicago, IL, USA", d["location"])


    ## Test the Yes/No pane
    def test_yesno(self):
        yesno = WebDriverWait(driver = self.driver, timeout = 10).\
            until(lambda d: d.find_element_by_id("yes-no_button"))
        yesno.click()

        test_dict = {
            'date-est': 'exact', 
            'duration': 'one',
            'non-campus': 'yes',
            'off-campus': 'yes'
        }

        for variable in test_dict.keys():
            el = self.driver.find_element_by_id('info_{}'.format(variable))
            el.click()

        qs = db_session.query(CodeEventCreator).filter(CodeEventCreator.coder_id == 2).all()

        for q in qs:
            self.assertEqual(test_dict[q.variable], q.value)

    ## TK: This is not quite working yet.
    @unittest.skip("Skipping text selects for now.")
    def test_text_select(self):
        textselect = WebDriverWait(driver = self.driver, timeout = 10).\
            until(lambda d: d.find_element_by_id("textselect_button"))
        textselect.click()

        ## Load from YAML
        fh = open('../text-selects.yaml', 'r')
        test_fields = [x for x in yaml.load(fh, Loader = yaml.BaseLoader).keys()]
        fh.close()

        ## get the grafs
        grafs = self.driver.find_element_by_id("bodytext").find_elements(By.TAG_NAME, "p")

        ## set the average length of text fields
        avg_length = 50

        for variable in test_fields:
            ## Select some random body text by picking a random graf 
            ## and getting some random text
            graf = random.choice(grafs)
            graf.click()

            graf_len = len(graf.text)
            offset = random.choice(range(avg_length)) if graf_len > avg_length else graf_len

            print(variable, offset)

            ## move over to the n-th character
            # for _ in range(start):
            #     webdriver.ActionChains(self.driver).send_keys(Keys.ARROW_RIGHT).perform()

            ## press left shift
            webdriver.ActionChains(self.driver).key_up(Keys.LEFT_SHIFT).perform()

            ## move to n+kth character
            for _ in range(offset):
                webdriver.ActionChains(self.driver).send_keys(Keys.ARROW_RIGHT).perform()

            ## lift up left shift
            webdriver.ActionChains(self.driver).key_up(Keys.LEFT_SHIFT).perform()

            ## click an add button
            self.driver.find_element_by_id("add_{}".format(variable)).click()

            ## get the selected text but wait until it loads
            ## TK: this is timing out?? need to find out why this is happening
            selected_text = WebDriverWait(driver = self.driver, timeout = 10).\
                until(lambda d: d.find_element_by_id("list_{}".format(variable)).\
                    find_element_by_tag_name("p"))

            ## clear selected text by clicking on the graf
            graf.click()

            ## Assert that the addition has ended up in the list
            self.assertIsNot(selected_text, "")

        vals = {}
        qs = db_session.query(CodeEventCreator).filter(CodeEventCreator.coder_id == 2).all()

        ## ensure that the number of fields stored is equal
        self.assertEqual(len(qs), len(test_fields))

        for q in qs:
            vals[q.variable] = q.text

            print(q.variable, q.value, q.text)
            self.assertIsNot(q.text, None)


    ## test presets
    def test_presets(self):
        presets = WebDriverWait(driver = self.driver, timeout = 10).\
            until(lambda d: d.find_element_by_id("preset_button"))
        presets.click()

        ## Load from YAML
        fh = open('../presets.yaml', 'r')
        preset_fields = yaml.load(fh, Loader = yaml.BaseLoader)
        fh.close()

        ## stored values to check
        d = {}

        ## select form, issue, racial issue, and target
        for variable in (['form', 'issue', 'racial-issue', 'target']):
            self.driver.find_element_by_id("l_varevent_{}".format(variable)).click()
            d[variable] = []

            ## select three random items
            for value in random.sample(preset_fields[variable], 3):
                ## wait until we can click
                ## from https://stackoverflow.com/questions/56085152/selenium-python-error-element-could-not-be-scrolled-into-view
                element = WebDriverWait(self.driver, 10).until(\
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[value='{}']".format(value))))
                element.location_once_scrolled_into_view
                element.click()

                ## append to stored value dict
                d[variable].append(value)

        qs = db_session.query(CodeEventCreator).filter(CodeEventCreator.coder_id == 2).all()

        ## ensure that the number of fields stored 
        ## is equal to number of fields * number selected (4 * 3 = 12)
        self.assertEqual(len(qs), 12)

        ## check if the value was selected
        for q in qs:
            self.assertIn(q.value, d[q.variable])


if __name__ == "__main__":
    unittest.main()