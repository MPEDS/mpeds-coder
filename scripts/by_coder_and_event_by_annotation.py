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
eventdf = pd.read_sql_query(coder_event_q.statement, 
                            coder_event_q.session.connection())
print eventdf

coder_article_q = (database
                   .db_session
                   .query(models.ArticleMetadata)
                   )
