import sys
import datetime
import urllib.request
import urllib.parse

import pandas as pd
import sqlalchemy
import sqlalchemy.orm

from .context import config
from . import solr

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
sobj = solr.Solr()
sobj.setSolrURL('%s/select' % config.SOLR_ADDR)

## Crossover query

am_id_df = pd.read_sql("SELECT DISTINCT db_id FROM article_metadata",
                       con=mysql_engine)

## Put IDs from MySQL into a SOLR query string
ids = am_id_df['db_id'].tolist()

def testURLEncoding(id):
    data = {
        'q':     id,
        'start': 0,
        'rows':  10,
        'wt':    'json'
        }
    try:
        urllib.parse.urlencode(data)
    except UnicodeEncodeError:
        print("#### Bad encoding: %s" % id)

[testURLEncoding(id) for id in ids]

def getQueryChunk(ids):
    ids_qclause = '"' + '" OR "'.join(ids) + '"'
    ids_q = 'id: (' + ids_qclause + ')'

    print("Retrieving %d articles..." % sobj.getResultsFound(ids_q))

    import time
    t0    = time.time()
    docs  = sobj.getDocuments(ids_q)
    test_time = time.time() - t0
    print("Loading time:  %0.3fs" % test_time)
    return docs

# Chunk trick from https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
id_chunks = [ids[i:i + 1024] for i in range(0, len(ids), 1024)]

docs = list()
# NB: making copies of this list will use up memory fast!
for i in range(len(id_chunks)):
    print("### Chunk %d of %d" % (i, len(id_chunks)))
    docs.extend(getQueryChunk(id_chunks[i]))

solr_df = pd.DataFrame(docs)

print("Article count: %d" % solr_df.shape[0])


## Clean list columns

def clean_lists(listcell):
    if isinstance(listcell, list):
        listcell = '|||'.join(str(v) for v in listcell)
    return listcell

solr_df = solr_df.applymap(clean_lists)


## Reorder columns

knowngood = ['PUBLICATION', 
             'SECTION', 
             'BYLINE', 
             'DATELINE', 
             'DATE', 
             'INTERNAL_ID',
             'TITLE',
             'TEXT']
cols = ([c for c in solr_df.columns if c in knowngood]
        + [c for c in solr_df.columns if c not in knowngood])
solr_df = solr_df[cols]


## Output

wd = config.WD
filename = ('%s/exports/%s_solr_output_%s.csv' 
                % (wd, 
                   config.MYSQL_DB,
                   datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')))

solr_df.to_csv(filename, encoding = 'utf-8', index = False)


## Object count analysis

def countobj(x):
    if isinstance(x, list) or isinstance(x, dict):
        return len(x)
    else:
        return 1

maxentries = (solr_df
                .applymap(countobj)
                .apply(max)
                .to_frame('maxn')
                .query('maxn > 1')
                # sort changed to sort_values at pandas 0.17 or so
                #.sort('maxn', ascending=False)
                )
print('\n\nLargest multi-entry cell in each column:')
print(maxentries)

## Nonempty analysis

nonmissing = (solr_df
                .count()
                # sort changed to sort_values at pandas 0.17 or so
                #.sort(ascending=False)
                )
print('\n\nNonmissing entries in each column:')
print(nonmissing)
