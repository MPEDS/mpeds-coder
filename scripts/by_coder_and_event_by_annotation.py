import sys

import pandas as pd
import sqlalchemy

from context import config
from context import database
from context import models


## Get tables into data frames
coder_event_q = (database
				 .db_session
         .query(models.CodeEventCreator)
         )
eventdf = pd.read_sql_query(coder_event_q.statement, 
                            # Old pandas fears real connections
                            #coder_event_q.session.connection())
                            coder_event_q.session.get_bind())

coder_article_q = (database
                   .db_session
                   .query(models.CoderArticleAnnotation)
                   )
articledf = pd.read_sql_query(coder_article_q.statement, 
                              # Old pandas fears real connections
                              #coder_event_q.session.connection())
                              coder_event_q.session.get_bind())

## Number duplicated variables
## I can't figure out how to assign this in an ungrouped pipeline, alas
eventdf['varocc'] = (eventdf
                     .groupby(['coder_id', 'article_id', 'event_id', 'variable'])
                     .cumcount() + 1
                     )
articledf['varocc'] = (articledf
                       .groupby(['coder_id', 'article_id', 'variable'])
                       .cumcount() + 1
                       )
eventdf = (eventdf
           .assign(varocc=lambda x: "_" + x.varocc.astype('str'))
           .assign(varocc=lambda x: x.varocc.replace("_1", ""))
           .assign(variable=lambda x: x['variable'] + x['varocc'])
           )
articledf = (articledf
             .assign(varocc=lambda x: "_" + x.varocc.astype('str'))
             .assign(varocc=lambda x: x.varocc.replace("_1", ""))
             .assign(variable=lambda x: x['variable'] + x['varocc'])
             )

## Reshape tables
e_val = (eventdf
         .filter(['coder_id', 'article_id', 'event_id', 'variable', 'value'])
         .dropna()
         # Next block should remove both empty strings and missings
         .assign(length=lambda x: x.value.astype('str').str.len())
         .query('length > 0')
         .drop('length', axis=1)
         .set_index(['coder_id', 'article_id', 'event_id', 'variable'])
         .unstack()
         )

e_text = (eventdf
          .filter(['coder_id', 'article_id', 'event_id', 'variable', 'text'])
          .dropna()
          # Next block should remove both empty strings and missings
          .assign(length=lambda x: x.text.astype('str').str.len())
          .query('length > 0')
          .drop('length', axis=1)
          .set_index(['coder_id', 'article_id', 'event_id', 'variable'])
          .unstack()
          )

e_time = (eventdf
          .filter(['coder_id', 'article_id', 'event_id', 'timestamp'])
          .dropna()
          .groupby(['coder_id', 'article_id', 'event_id'])
          .agg(['min', 'max'])
          )

a_val = (articledf
         .filter(['coder_id', 'article_id', 'variable', 'value'])
         .dropna()
         # Next block should remove both empty strings and missings
         .assign(length=lambda x: x.value.astype('str').str.len())
         .query('length > 0')
         .drop('length', axis=1)
         .set_index(['coder_id', 'article_id', 'variable'])
         .unstack()
         )

a_text = (articledf
          .filter(['coder_id', 'article_id', 'variable', 'text'])
          .dropna()
          # Next block should remove both empty strings and missings
          .assign(length=lambda x: x.text.astype('str').str.len())
          .query('length > 0')
          .drop('length', axis=1)
          .set_index(['coder_id', 'article_id', 'variable'])
          .unstack()
          )

a_time = (articledf
          .filter(['coder_id', 'article_id', 'timestamp'])
          .dropna()
          .groupby(['coder_id', 'article_id'])
          .agg(['min', 'max'])
          )

## Merge tables
event_wide = e_val.join(e_text, how='outer')
article_wide = a_val.join(a_text, how='outer')

print '***** Event df *****'
print eventdf
#print '***** Event value df *****'
#print e_val
#print '***** Event text df *****'
#print e_text
#print '***** Event time df *****'
#print e_time
print '***** Event merged wide df *****'
print event_wide
print '***** Article df *****'
print articledf
#print '***** Article value df *****'
#print a_val
#print '***** Article text df *****'
#print a_text
#print '***** Article time df *****'
#print a_time
print '***** Article merged wide df *****'
print article_wide
