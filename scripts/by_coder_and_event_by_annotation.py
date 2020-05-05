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

## Reshape tables
e_val = (eventdf
         .filter(['coder_id', 'article_id', 'event_id', 'variable', 'value'])
         .dropna()
         # Next block should remove both empty strings and missings
         .assign(length=lambda x: x.value.astype("str").str.len())
         .query('length > 0')
         .drop('length', axis=1)
         .set_index(['coder_id', 'article_id', 'event_id', 'variable'])
         .unstack()
         )

e_text = (eventdf
          .filter(['coder_id', 'article_id', 'event_id', 'variable', 'text'])
          .dropna()
          # Next block should remove both empty strings and missings
          .assign(length=lambda x: x.text.astype("str").str.len())
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
          #.set_index(['coder_id', 'article_id', 'event_id', 'variable'])
          #.unstack()
          )

print "***** Event df *****"
print eventdf
print "***** Article df *****"
print articledf
print "***** Event value df *****"
print e_val
print "***** Event text df *****"
print e_text
print "***** Event time df *****"
print e_time
