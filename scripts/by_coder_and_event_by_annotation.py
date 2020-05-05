import sys

import pandas as pd
import sqlalchemy

from context import config
from context import database
from context import models


## MySQL setup
mysql_engine = sqlalchemy.create_engine(
    'mysql://%s:%s@localhost/%s?unix_socket=%s&charset=%s' % 
        (config.MYSQL_USER, 
        config.MYSQL_PASS, 
        config.MYSQL_DB, 
        config.MYSQL_SOCK, 
        'utf8'), 
    convert_unicode=True)

coder_event_q = (database
				 .db_session
         .query(models.CodeEventCreator)
         )
eventdf = (pd
           .read_sql_query(coder_event_q.statement, 
                           coder_event_q.session.connection())
           )

coder_article_q = (database
                   .db_session
                   .query(models.CoderArticleAnnotation)
                   )
articledf = pd.read_sql_query(coder_article_q.statement, 
                            coder_article_q.session.connection())

e_val = (eventdf
         .filter(['coder_id', 'article_id', 'event_id', 'variable', 'value'])
         .dropna()
         .assign(length=lambda x: x.value.astype("str").str.len())
         .query('length > 0')
         .drop('length', axis=1)
         .set_index(['coder_id', 'article_id', 'event_id', 'variable'])
         .unstack()
         )

print "***** Event df *****"
print eventdf
print "***** Article df *****"
print articledf
print "***** Event value df *****"
print e_val
