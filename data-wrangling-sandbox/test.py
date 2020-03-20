import pandas as pd
import sqlalchemy
import sys
#from .. import config
#
#mysql_engine = sqlalchemy.create_engine('mysql://%s:%s@localhost/%s?unix_socket=%s&charset=%s' % 
#                                        (config.MYSQL_USER, 
#                                        config.MYSQL_PASS, 
#                                        config.MYSQL_DB, 
#                                        config.MYSQL_SOCK, 
#                                        'utf8'), 
#                                        convert_unicode=True)
#db_session = scoped_session(sessionmaker(autocommit=False,
#                                         autoflush=False,
#                                         bind=mysql_engine))
print(sys.path)
