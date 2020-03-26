import sys

import pandas as pd
import sqlalchemy
import sqlalchemy.orm

import config
import models

mysql_engine = sqlalchemy.create_engine(
    'mysql://%s:%s@localhost/%s?unix_socket=%s&charset=%s' % 
        (config.MYSQL_USER, 
        config.MYSQL_PASS, 
        config.MYSQL_DB, 
        config.MYSQL_SOCK, 
        'utf8'), 
    convert_unicode=True)
#db_session = sqlalchemy.orm.scoped_session(
#    sqlalchemy.orm.sessionmaker(
#        autocommit=False,
#        autoflush=False,
#        bind=mysql_engine))
#
#print(db_session.query(models.ArticleMetadata).filter_by(id = 10).first())
df = pd.read_sql_table("user", con=mysql_engine)
print df
