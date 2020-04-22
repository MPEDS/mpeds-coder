import sys

import pandas as pd
import sqlalchemy
#import sqlalchemy.orm

from context import config
import solr

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

am_id_df = pd.read_sql("SELECT db_id FROM article_metadata", con=mysql_engine)
ids = am_id_df['db_id'].tolist()

docs = sobj.getDocumentsFromIDs(ids)
solr_df = pd.DataFrame(docs)

etl_df = (solr_df
          .filter(['id', 'PUBLICATION', 'DOCSOURCE'])
          )

print etl_df

