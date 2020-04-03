import sys

import pandas as pd
import sqlalchemy
import sqlalchemy.orm

import config
import data_wrangling.solr
import models

## MySQL setup
mysql_engine = sqlalchemy.create_engine(
    'mysql://%s:%s@localhost/%s?unix_socket=%s&charset=%s' % 
        (config.MYSQL_USER, 
        config.MYSQL_PASS, 
        config.MYSQL_DB, 
        config.MYSQL_SOCK, 
        'utf8'), 
    convert_unicode=True)

## SOLR setup
sobj = data_wrangling.solr.Solr()
sobj.setSolrURL('%s/select' % config.SOLR_ADDR)

## MySQL testing
user_df = pd.read_sql_table("user", con=mysql_engine)
print user_df

## SOLR testing
#SEARCH_STR = 'boycott* "press conference" "news conference" (protest* AND NOT protestant*) strik* rally ralli* riot* sit-in occupation mobiliz* blockage demonstrat* marchi* marche*'

QUERY_STR = 'PUBLICATION:("Associated Press Worldstream, English Service" OR "New York Times Newswire Service" OR ' + \
        '"Los Angeles Times/Washington Post Newswire Service" OR "Washington Post/Bloomberg Newswire Service")'
FQ_STR = 'Wisconsin AND boycott'

output_counts = {}

output_counts['retrieved-articles'] = sobj.getResultsFound(QUERY_STR, FQ_STR)

print("Retrieving %d articles..." % output_counts['retrieved-articles'])

import time
t0    = time.time()
docs  = sobj.getDocuments(QUERY_STR, fq = FQ_STR)
test_time = time.time() - t0
print("Loading time:  %0.3fs" % test_time)

df = pd.DataFrame(docs)

#print df
#print '\n'.join([doc[u'TITLE'] for doc in docs])

output_counts['retrieved-articles-cleaned'] = df.shape[0]
print("Article count: %d" % df.shape[0])

## Crossover testing
# data = {
#     'PUBLICATION': '("Associated Press Worldstream, English Service" OR "New York Times Newswire Service" OR '+\
#      '"Los Angeles Times/Washington Post Newswire Service" OR "Washington Post/Bloomberg Newswire Service")'
# }

## this is a bit buggy. DS 2020-03-26: why?
#query = sobj.buildSolrQuery(data)

