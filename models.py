from sqlalchemy import Boolean, Column, DateTime, Integer, String, Unicode, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from flask.ext.login import UserMixin
from database import Base
import datetime as dt
import pytz
from pytz import timezone

central = timezone('US/Central')

class CodeFirstPass(Base):
    __tablename__ = 'code_first_pass'
    id         = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('article_metadata.id'), nullable = False)
    variable   = Column(String, nullable = False)
    value      = Column(String, nullable = False)
    text       = Column(Unicode)
    coder_id   = Column(Integer, ForeignKey('user.id'), nullable = False)
    timestamp  = Column(DateTime)

    def __init__(self, article_id, variable, value, coder_id, text = None):
        self.article_id = article_id
        self.variable   = variable
        self.value	    = value
        self.text       = text
        self.coder_id   = coder_id
        self.timestamp  = dt.datetime.now(tz = central).replace(tzinfo = None)

    def __repr__(self):
        return '<CodeFirstPass %r>' % (self.id)

class CodeSecondPass(Base):
    __tablename__ = 'coder_second_pass'
    id         = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('article_metadata.id'), nullable = False)
    event_id   = Column(Integer, ForeignKey('event.id'), nullable = False)
    variable   = Column(String, nullable = False)
    value      = Column(String, nullable = False)
    coder_id   = Column(Integer, ForeignKey('user.id'))
    timestamp  = Column(DateTime)

    def __init__(self, article_id, event_id, variable, value, coder_id):
        self.article_id = article_id
        self.event_id   = event_id
        self.variable   = variable
        self.value	    = value
        self.coder_id   = coder_id
        self.timestamp  = dt.datetime.now(tz = central).replace(tzinfo = None)

    def __repr__(self):
        return '<CodeSecondPass %r>' % (self.id)

class Event(Base):
    __tablename__ = 'event'
    id         = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('article_metadata.id'), nullable = False)

    def __init__(self, article_id):
        self.article_id = article_id

    seconds = relationship("CodeSecondPass", backref = backref("event", order_by = id))

    def __repr__(self):
        return '<Event %r>' % (self.id)

class ArticleQueue(Base):
    __tablename__ = 'article_queue'
    id         = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('article_metadata.id'), nullable = False)
    coder_id   = Column(Integer, ForeignKey('user.id'), nullable = False)
    coded1_dt  = Column(DateTime)
    coded2_dt  = Column(DateTime)

    UniqueConstraint('article_id', 'coder_id', name = 'unique1')

    def __init__(self, article_id, coder_id):
        self.article_id = article_id
        self.coder_id   = coder_id

    def __repr__(self):
        return '<ArticleQueue %r>' % (self.article_id)

class SecondPassQueue(Base):
    __tablename__ = 'second_pass_queue'
    id         = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('article_metadata.id'), nullable = False)
    coder_id   = Column(Integer, ForeignKey('user.id'), nullable = False)
    coded_dt   = Column(DateTime)

    UniqueConstraint('article_id', 'coder_id', name = 'unique1')

    def __init__(self, article_id, coder_id):
        self.article_id = article_id
        self.coder_id   = coder_id

    def __repr__(self):
        return '<SecondPassQueue %r>' % (self.article_id)

class ArticleMetadata(Base):
    __tablename__ = 'article_metadata'
    id        = Column(Integer, primary_key=True)
    title     = Column(String)
    db_name   = Column(String)
    db_id     = Column(String)
    filename  = Column(String, nullable = False)

    firsts  = relationship("CodeFirstPass",  backref = backref("article_metadata", order_by = id))
    seconds = relationship("CodeSecondPass", backref = backref("article_metadata", order_by = id))
    queue   = relationship("ArticleQueue",   backref = backref("article_metadata", order_by = id))

    def __init__(self, filename, db_name = None, db_id = None, title = None):
        self.filename  = filename
        self.db_name   = db_name
        self.db_id     = db_id
        self.title     = title

    def __repr__(self):
        return '<ArticleMetadata %r (%r)>' % (self.title, self.id)

## All these are manually added
class User(Base, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username  = Column(String, nullable = False)
    password  = Column(String, nullable = False)
    authlevel = Column(Integer, nullable = False)

    firsts  = relationship("CodeFirstPass",  backref = backref("user", order_by = id))
    seconds = relationship("CodeSecondPass", backref = backref("user", order_by = id))
    queue   = relationship("ArticleQueue",   backref = backref("user", order_by = id))

    def __init__(self, username, password, authlevel):
        self.username  = username
        self.password  = password
        self.authlevel = authlevel

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def __repr__(self):
        return '<Coder %r>' % (self.id)

class VarOption(Base):
    __tablename__ = 'var_option'
    id       = Column(Integer, primary_key=True)
    variable = Column(String, nullable = False)
    options   = Column(String, nullable = False)
    parent   = Column(Integer)

    def __init__(self, variable, option, parent = None):
        self.variable = variable
        self.options   = option
        self.parent   = parent

    def __repr__(self):
        return '<VarOption %r>' % (self.id)
