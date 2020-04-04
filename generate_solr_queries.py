import sys
import datetime

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

## Crossover query

am_id_df = pd.read_sql("SELECT db_id FROM article_metadata", con=mysql_engine)

## Put IDs from MySQL into a SOLR query string
ids = am_id_df['db_id'].tolist()
ids_qclause = '"' + '" OR "'.join(ids) + '"'
ids_q = 'id: (' + ids_qclause + ')'

output_counts = {}

output_counts['retrieved-articles'] = sobj.getResultsFound(ids_q)

print("Retrieving %d articles..." % output_counts['retrieved-articles'])

import time
t0    = time.time()
docs  = sobj.getDocuments(ids_q)
test_time = time.time() - t0
print("Loading time:  %0.3fs" % test_time)

solr_df = pd.DataFrame(docs)

output_counts['retrieved-articles-cleaned'] = solr_df.shape[0]
print("Article count: %d" % solr_df.shape[0])


## Output

wd = '/home/skalinder' #config.WD
filename = ('%s/exports/solr_output_%s.csv' 
                % (wd, 
                   datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')))

#solr_df.to_csv(filename, encoding = 'utf-8', index = False)


## Analysis

def countobj(x):
    if isinstance(x, list) or isinstance(x, dict):
        return len(x)
    else:
        return 1

maxentries = (solr_df
            .applymap(countobj)
            .apply(max)
            )

maxentries = (maxentries
                # Don't know why this doesn't work
                #.rename('cols')
                #.where(cols == 1)
                #.order()
            )

print '\n\nMaximum entries per cell in each column:'
print maxentries
