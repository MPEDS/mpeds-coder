from database import db_session, init_db
from models import User, ArticleMetadata, CodeFirstPass, CodeSecondPass, CodeEventCreator, \
	ArticleQueue, SecondPassQueue, EventCreatorQueue, Event
from sqlalchemy import func

import csv
import random
import glob
import json

import config

def addArticlesExample(db_name = 'test'):
	""" Add articles from example directory. """

	print("Adding example articles...")
	articles = []
	for f in glob.iglob(config.DOC_ROOT + "*.txt"):
		print(f)
		filename = f.split('/')[-1]
		lines    = open(f, 'r').read().split("\n")
		title    = lines[0].replace("TITLE: ", "")

		articles.append( ArticleMetadata(filename = filename, title = title, db_name = db_name) )

	db_session.add_all(articles)
	db_session.commit()


def addArticles(filename, db_name):
	articles = []
	with open(filename) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			title = row[0]
			db_id = row[1]
			if title == 'TITLE':
				continue
			articles.append( ArticleMetadata(filename = db_id, db_id = db_id, title = title, db_name = db_name) )

	db_session.add_all(articles)
	db_session.commit()


def addUsersExample():
	""" Add some example users. """
	print("Adding example users...")

	## Add admin
	db_session.add(User(username = 'admin', password = 'default', authlevel = 3))

	## add first pass coders
	db_session.add(User(username = 'coder1p_1', password = 'default', authlevel = 1))
	db_session.add(User(username = 'coder1p_2', password = 'default', authlevel = 1))

	## second pass coders
	db_session.add(User(username = 'coder2p_1', password = 'default', authlevel = 2))
	db_session.add(User(username = 'coder2p_2', password = 'default', authlevel = 2))

	db_session.commit()


def addQueueExample():
	print("Adding example queues...")

	articles = db_session.query(ArticleMetadata).all()
	random.shuffle(articles)

	users = db_session.query(User).filter(User.authlevel == 1).all()

	aq  = []
	ecq = []
	## assign articles randomly to core team members for funsies
	for a in articles:
		for u in users:
			aq.append( ArticleQueue(article_id = a.id, coder_id = u.id) )
			ecq.append( EventCreatorQueue(article_id = a.id, coder_id = u.id) ) 

	db_session.add_all(aq)
	db_session.add_all(ecq)
	db_session.commit()


def main():
        init_db()
	#addArticles(config.DOC_ROOT + config.DOC_FILE, config.DOC_DBNAME)
        addArticles("uwire2016-18_haystack_us-canada.csv", "uwire2016-18")

if __name__ == '__main__':
	main()
