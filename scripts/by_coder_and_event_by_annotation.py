import sys
import datetime as dt

import pandas as pd
import sqlalchemy

from context import config
from context import database
from context import models


## Get tables into data frames
event_q = (database
           .db_session
           .query(models.CodeEventCreator)
           )
event_long = pd.read_sql_query(event_q.statement, 
                               # Old pandas fears real connections
                               #event_q.session.connection())
                               event_q.session.get_bind())

u_q = (database
       .db_session
       .query(models.User)
       )
user = pd.read_sql_query(u_q.statement, 
                         # Old pandas fears real connections
                         #u_q.session.connection())
                         u_q.session.get_bind())

am_q = (database
        .db_session
        .query(models.ArticleMetadata)
        )
am = pd.read_sql_query(am_q.statement, 
                       # Old pandas fears real connections
                       #am_q.session.connection())
                       am_q.session.get_bind())

ca_q = (database
        .db_session
        .query(models.CoderArticleAnnotation)
        )
ca_long = pd.read_sql_query(ca_q.statement, 
                            # Old pandas fears real connections
                            #ca_q.session.connection())
                            ca_q.session.get_bind())

## Number duplicated variables
## I can't figure out how to assign this in an ungrouped pipeline, alas
event_long['varocc'] = (event_long
                        .groupby(['coder_id', 'article_id', 
                                  'event_id', 'variable'])
                        .cumcount() + 1
                        )
ca_long['varocc'] = (ca_long
                     .groupby(['coder_id', 'article_id', 
                               'variable'])
                     .cumcount() + 1
                     )
event_long = (event_long
              .assign(varocc=lambda x: "_" + x.varocc.astype('str'))
              .assign(varocc=lambda x: x.varocc.replace("_1", ""))
              .assign(variable=lambda x: x['variable'] + x['varocc'])
              )
ca_long = (ca_long
           .assign(varocc=lambda x: "_" + x.varocc.astype('str'))
           .assign(varocc=lambda x: x.varocc.replace("_1", ""))
           .assign(variable=lambda x: x['variable'] + x['varocc'])
           )

## Reshape tables
e_val = (event_long
         .filter(['coder_id', 'article_id', 'event_id', 'variable', 'value'])
         .dropna()
         # Next block should remove both empty strings and missings
         .assign(length=lambda x: x.value.astype('str').str.len())
         .query('length > 0')
         .drop('length', axis=1)
         .set_index(['coder_id', 'article_id', 'event_id', 'variable'])
         .unstack()
         )

e_text = (event_long
          .filter(['coder_id', 'article_id', 'event_id', 'variable', 'text'])
          .dropna()
          # Next block should remove both empty strings and missings
          .assign(length=lambda x: x.text.astype('str').str.len())
          .query('length > 0')
          .drop('length', axis=1)
          .set_index(['coder_id', 'article_id', 'event_id', 'variable'])
          .unstack()
          )

e_time = (event_long
          .filter(['coder_id', 'article_id', 'event_id', 'timestamp'])
          .dropna()
          .groupby(['coder_id', 'article_id', 'event_id'])
          .agg(['min', 'max'])
          )

ca_val = (ca_long
          .filter(['coder_id', 'article_id', 'variable', 'value'])
          .dropna()
          # Next block should remove both empty strings and missings
          .assign(length=lambda x: x.value.astype('str').str.len())
          .query('length > 0')
          .drop('length', axis=1)
          .set_index(['coder_id', 'article_id', 'variable'])
          .unstack()
          )

ca_text = (ca_long
           .filter(['coder_id', 'article_id', 'variable', 'text'])
           .dropna()
           # Next block should remove both empty strings and missings
           .assign(length=lambda x: x.text.astype('str').str.len())
           .query('length > 0')
           .drop('length', axis=1)
           .set_index(['coder_id', 'article_id', 'variable'])
           .unstack()
           )

ca_time = (ca_long
           .filter(['coder_id', 'article_id', 'timestamp'])
           .dropna()
           .groupby(['coder_id', 'article_id'])
           .agg(['min', 'max'])
           )

## Merge tables
e_wide = e_val.join(e_text, how='outer').reset_index('event_id')
ca_wide = ca_val.join(ca_text, how='outer')
all_wide = ca_wide.join(e_wide, how='outer')

## Clean up
print '***** Event df *****'
print event_long
#print '***** Event value df *****'
#print e_val
#print '***** Event text df *****'
#print e_text
#print '***** Event time df *****'
#print e_time
print '***** Event merged wide df *****'
print e_wide
print '***** Article df *****'
print ca_long
#print '***** Article value df *****'
#print ca_val
#print '***** Article text df *****'
#print ca_text
#print '***** Article time df *****'
#print ca_time
print '***** Article merged wide df *****'
print ca_wide
print '***** Grand unified wide df *****'
print all_wide

filename = '%s/exports/by_coder_and_event_by_annotation_%s.csv' % (config.WD, dt.datetime.now().strftime('%Y-%m-%d_%H%M%S'))

#all_wide.to_csv(filename)
