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

## Get article IDs
am_id_df = pd.read_sql('SELECT db_id FROM article_metadata', con=mysql_engine)
am_id_df = (am_id_df
            .assign(dupe=am_id_df['db_id'].duplicated(keep='first'))
            .query('dupe == False')
            )
ids = am_id_df['db_id'].tolist()

## Query SOLR for IDs
docs = sobj.getDocumentsFromIDs(ids)
solr_df = pd.DataFrame(docs)

## Trim dataframe
etl_df = (solr_df
          .filter(['id', 'PUBLICATION', 'DOCSOURCE']))

## Test for duplicate IDs
#### Put in fake dupe to test
#etl_df.iloc[5]['id'] = etl_df.iloc[6]['id']

etl_df = (etl_df
          .assign(dupe=etl_df['id'].duplicated())
          )
if not etl_df.query('dupe == True').empty:
    sys.exit("Duplicate SOLR IDs found.  Aborting.")

## Write temporary DB table
etl_df.to_sql('temp_etl_table',
              mysql_engine,
              if_exists='replace',
              dtype={'id': sqlalchemy.types.String(255),
                     'PUBLICATION': sqlalchemy.types.String(511),
                     'DOCSOURCE': sqlalchemy.types.String(511)})

## Update canonical table with new data
updatecleaned = sqlalchemy.sql.text(
    'UPDATE article_metadata AS dest'
        ' LEFT JOIN temp_etl_table AS source'
        ' ON dest.db_id = source.id'
        ' SET dest.publication = source.PUBLICATION'
        ', dest.source_description = source.DOCSOURCE')
mysql_engine.execute(updatecleaned)

## Clean up
droptemp = sqlalchemy.sql.text('DROP TABLE temp_etl_table')
mysql_engine.execute(droptemp)

