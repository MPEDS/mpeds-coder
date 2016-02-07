from database import db_session, init_db
from models import User, ArticleMetadata, CodeFirstPass, CodeSecondPass, ArticleQueue, VarOption, Event
from sqlalchemy import func
import csv, random
from lxml import etree

init_db()

## code to print header name + select * from table
# query = db_session.query(CodeFirstPass).all()
# cols = [x.name for x in CodeFirstPass.__table__.columns]
# print ','.join(cols)
# for a in q:
# 	print(','.join( map(lambda x: str(a.__getattribute__(x)), cols) ))

## get config
jsonConfig = json.load( open("config.json", "r") )

## load dropdowns
def resetVariableOptions():	
	db_session.query(VarOption).delete()

	dds = []
	with open("dropdowns.csv") as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			dds.append( VarOption(variable = row[0], option = row[1]) )

	db_session.add_all(dds)
	db_session.commit()

## load articles
def addArticles(filename, db_name):
	filename = 'article_manipulation/agw-apw-1996-2007.csv'
	db_name  = 'AGW-APW-1996-2007'

	articles = []
	with open(filename) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			title = row[0]
			db_id = row[1]
			if title == 'TITLE':
				continue
			articles.append( ArticleMetadata(filename = db_id, db_id = db_id, title = unicode(title, "utf-8", errors = "ignore"), db_name = db_name) )

	db_session.add_all(articles)
	db_session.commit()

with open('doca-list-filtered.csv') as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		tree     = etree.parse(open(jsonConfig['LDC_ROOT'] + row[0], "r"))
		headline = tree.xpath("/nitf/body[1]/body.head/hedline/hl1")
		headline = headline[0].text

		articles.append( ArticleMetadata(filename = row[0], db_id = row[0], title = headline, db_name = "DoCA") )

## load users
## authlevels: 3 - admin, 2 - core team, 1 - undergrad coder, 0 - testcoder
users = []
with open("users5.csv") as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		users.append( User(username = row[0], password = row[1], authlevel = row[2]) )

db_session.add_all(users)
db_session.add_all(articles)

## query some stuff
# [(x.coder_id, x.variable, x.value) for x in db_session.query(CodeFirstPass).all()]
# [(x.variable, x.value) for x in db_session.query(CodeSecondPass).all()]

### assign current queue randomly
aq = []

articles = db_session.query(ArticleMetadata).all()
random.shuffle(articles)

## all core team members
users = db_session.query(User).filter(User.authlevel > 1).all()

## assign articles randomly to core team members for funsies
for a in articles:
	for u in users:
		aq.append( ArticleQueue(article_id = a.id, coder_id = u.id) )

db_session.add_all(aq)
db_session.commit()
