import sys

import pandas as pd
import sqlalchemy
#import sqlalchemy.orm

from .context import config
from . import solr

## MySQL setup
mysql_engine = sqlalchemy.create_engine(
    'mysql://%s:%s@localhost/%s?unix_socket=%s&charset=%s' % 
        (config.MYSQL_USER, 
        config.MYSQL_PASS, 
        config.MYSQL_DB, 
        config.MYSQL_SOCK, 
        'utf8mb4'), 
    convert_unicode=True)

## SOLR setup
sobj = solr.Solr()
sobj.setSolrURL('%s/select' % config.SOLR_ADDR)

## Get article IDs
am_id_df = pd.read_sql('SELECT db_id FROM article_metadata', con=mysql_engine)
am_id_df = (am_id_df
            .assign(dupe=am_id_df['db_id'].duplicated())
            .query('dupe == False')
            )
ids = am_id_df['db_id'].tolist()

## Query SOLR for IDs
docs = sobj.getDocumentsFromIDs(ids)
solr_df = pd.DataFrame(docs)

## Trim and clean dataframe
etl_df = (
    solr_df
    .filter(['id', 'DATE', 'PUBLICATION', 'DOCSOURCE', 'TEXT'])
    .assign(DATE=pd.to_datetime(solr_df['DATE'].str.get(0),
                                format='%Y-%m-%dT%H:%M:%SZ'))
    )

## Test for duplicate IDs
#### Put in fake dupe to test
#etl_df.iloc[5]['id'] = etl_df.iloc[6]['id']

dupe_check_df = (etl_df
                 .assign(dupe=etl_df['id'].duplicated())
                 )
if not dupe_check_df.query('dupe == True').empty:
    sys.exit("Duplicate SOLR IDs found.  Aborting.")

## Manually create temp table with correct column specs
droptemp = sqlalchemy.sql.text('DROP TABLE IF EXISTS temp_etl_table')
mysql_engine.execute(droptemp)
createtemp = sqlalchemy.sql.text(
    'CREATE TABLE temp_etl_table ('
        'id varchar(255) DEFAULT NULL'
        ', DATE date DEFAULT NULL'
        ', PUBLICATION varchar(511) DEFAULT NULL'
        ', DOCSOURCE varchar(511) DEFAULT NULL'
        ', TEXT mediumtext CHARACTER SET utf8mb4'
        ') DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci'
        )
mysql_engine.execute(createtemp)

## Split to keep query packets small
etl_dfs = [etl_df[i:i+100] for i in range(0, len(etl_df), 100)]

for df in etl_dfs:
  ## Write temporary DB table
  df.to_sql('temp_etl_table',
            mysql_engine,
            if_exists='append',
            index=False,
            dtype={'id': sqlalchemy.types.String(255),
                   'DATE': sqlalchemy.types.Date,
                   'PUBLICATION': sqlalchemy.types.String(511),
                   'DOCSOURCE': sqlalchemy.types.String(511),
                   'TEXT': sqlalchemy.types.UnicodeText(16777200)
                   })

## Update canonical table with new data
updatecleaned = sqlalchemy.sql.text(
    'UPDATE article_metadata AS dest'
        ' LEFT JOIN temp_etl_table AS source'
        ' ON dest.db_id = source.id'
        ' SET dest.pub_date = source.DATE'
        ' WHERE dest.pub_date IS NULL'
        )
mysql_engine.execute(updatecleaned)
updatecleaned = sqlalchemy.sql.text(
    'UPDATE article_metadata AS dest'
        ' LEFT JOIN temp_etl_table AS source'
        ' ON dest.db_id = source.id'
        ' SET dest.publication = source.PUBLICATION'
        ' WHERE dest.publication IS NULL'
        )
mysql_engine.execute(updatecleaned)
updatecleaned = sqlalchemy.sql.text(
    'UPDATE article_metadata AS dest'
        ' LEFT JOIN temp_etl_table AS source'
        ' ON dest.db_id = source.id'
        ' SET dest.source_description = source.DOCSOURCE'
        ' WHERE dest.source_description IS NULL'
        )
mysql_engine.execute(updatecleaned)
updatecleaned = sqlalchemy.sql.text(
    'UPDATE article_metadata AS dest'
        ' LEFT JOIN temp_etl_table AS source'
        ' ON dest.db_id = source.id'
        ' SET dest.text = source.TEXT'
        ' WHERE dest.text IS NULL'
        )
mysql_engine.execute(updatecleaned)

## Clean up
mysql_engine.execute(droptemp)

