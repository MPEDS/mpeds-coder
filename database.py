from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import config

mysql_engine = create_engine('mysql://%s:%s@localhost/%s?unix_socket=%s&charset=%s' % 
    (config.MYSQL_USER, config.MYSQL_PASS, config.MYSQL_DB, config.MYSQL_SOCK, 'utf8'), 
                             convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=mysql_engine))

Base = declarative_base()

Base.query = db_session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import models
    Base.metadata.create_all(bind=mysql_engine)
