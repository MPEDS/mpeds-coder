import pandas as pd
import numpy as np
import sqlalchemy

import os
import sys
import yaml

sys.path.insert(0, os.path.join(os.path.abspath('.'), 'scripts'))

from context import config

## MySQL setup
mysql_engine = sqlalchemy.create_engine(
    'mysql://%s:%s@localhost/%s?unix_socket=%s&charset=%s' % 
        (config.MYSQL_USER, 
        config.MYSQL_PASS, 
        config.MYSQL_DB, 
        config.MYSQL_SOCK, 
        'utf8mb4'), convert_unicode=True)

## get the users to skip
non_users = ['test1', 'admin', 'tina', 'alex', 'ellen', 'ishita', 'andrea', 'karishma']

## get the disqualifying information rows
disqualifying_variables = yaml.load(
            open(os.path.join(os.path.abspath('..'), 'yes-no.yaml'), 'r'), 
            Loader = yaml.BaseLoader)
disqualifying_variables = [x[0] for x in disqualifying_variables['Disqualifying information']]

query = """SELECT 
    event_id, 
    u.username coder_id, 
    variable, 
    value, 
    cec.text, 
    am.id article_id,
    am.pub_date, 
    am.publication, 
    am.title
FROM coder_event_creator cec
LEFT JOIN article_metadata am ON (cec.article_id = am.id)  
LEFT JOIN user u ON (cec.coder_id = u.id)"""

## get the query
df_long = pd.read_sql(query, con = mysql_engine)

## there should be duplicates but here we are
df_long = df_long.drop_duplicates()

## remove test users
df_long = df_long[~df_long['coder_id'].isin(non_users)]

## get disqualified events and remove
disqualified_events = df_long[df_long['variable'].isin(disqualifying_variables)].event_id.unique()
df_long = df_long[~df_long['event_id'].isin(disqualified_events)]

## move text field into value if not null
df_long['value'] = df_long.apply(lambda x: x['text'] if x['text'] is not None else x['value'], axis = 1)

## pivot
columns = ['article-desc', 'desc', 'location', 'start-date'] 
indexes = ['event_id', 'coder_id', 'article_id', 'publication', 'pub_date', 'title']
df_wide = df_long[df_long['variable'].isin(columns)].\
    pivot(index = indexes, columns = 'variable', values  = 'value')

## rename a few things to be MySQL and SQLAlchemy friendly
df_wide = df_wide.rename(columns = {'article-desc': 'article_desc', 'start-date': 'start_date'})

## reset indexes 
df_wide = df_wide.reset_index()

## replace empty values with NaN
df_wide[df_wide == ''] = np.nan

## upload to MySQL
df_wide.to_sql(name = 'event_metadata',
            con = mysql_engine,
            if_exists= 'replace',
            index = True,
            index_label = 'id',
            dtype = {
                'id': sqlalchemy.types.Integer(),
                'coder_id': sqlalchemy.types.Text(),
                'event_id': sqlalchemy.types.Integer(),
                'article_id': sqlalchemy.types.Integer(),
                'article_desc': sqlalchemy.types.UnicodeText(),
                'desc': sqlalchemy.types.UnicodeText(),
                'location': sqlalchemy.types.Text(),
                'start_date': sqlalchemy.types.Date(),
                'publication': sqlalchemy.types.Text(),
                'pub_date': sqlalchemy.types.Date(),
                'title': sqlalchemy.types.Text()
            })