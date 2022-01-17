##
## Generate a wide-to-long CEC table from a long-to-wide CEC table.
##

import pandas as pd
import sqlalchemy

import os
import sys
import yaml

import datetime as dt

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
non_users = ['test1', 'admin', 'tina', 'alex', 'ellen', 'ishita', 'andrea', 'karishma', 'adj1']

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

## there should not be duplicates but here we are
df_long = df_long.drop_duplicates()

## remove test users
df_long = df_long[~df_long['coder_id'].isin(non_users)]

## get disqualified events and remove
disqualified_events = df_long[df_long['variable'].isin(disqualifying_variables)].event_id.unique()
df_long = df_long[~df_long['event_id'].isin(disqualified_events)]

## move text field into value if not null
df_long['value'] = df_long.apply(lambda x: x['text'] if x['text'] is not None else x['value'], axis = 1)

## pivot, join variables with multiple values with ;
indexes = ['event_id', 'coder_id', 'article_id', 'publication', 'pub_date', 'title']
df_wide = pd.pivot_table(data = df_long,
        index = indexes, 
        columns = 'variable', 
        values  = 'value', 
        aggfunc = lambda x: ';'.join(x))

df_wide.to_csv('../exports/pivoted-events_{}.csv'.format(dt.datetime.now().strftime('%Y-%m-%d')))