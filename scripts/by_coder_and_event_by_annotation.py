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

query = (database
				 .db_session
         .query(models.CodeEventCreator, models.ArticleMetadata)
         .join(models.ArticleMetadata)
         )
print pd.read_sql_query(query.statement, database.db_session.connection())
