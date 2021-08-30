# -*- coding: utf-8 -*-
"""Tools to generate exports"""

from __future__ import division
import datetime as dt
import math
import string

import pandas as pd
from sqlalchemy.exc import OperationalError
from sqlalchemy import func, desc, distinct, or_
from sqlalchemy.sql import select, func
from sqlalchemy.schema import Table

#from ..database import db_session
from ..models import ArticleMetadata, CodeEventCreator, User

def validate( x ):
    """ replace newlines, returns, and tabs with blank space """
    if x:
        if type(x) == unicode:
            x = string.replace(x, "\n", " ")
            x = string.replace(x, "\r", " ")
            x = string.replace(x, "\t", " ")
            return x.encode('utf-8')
        else:
            return str(x)
    else:
        return "0"

def split_solr_id(id):
    if id is None:
        pass
    elif 'AGW' in id:
        ## e.g.
        ## AGW_AFP_ENG_20040104.0056
        pieces   = id.split("_")
        pub      = "-".join(pieces[0:3])
        pub_date = pieces[3].split('.')[0]
        pub_date = dt.datetime.strptime(pub_date, '%Y%m%d').strftime('%Y-%m-%d')
    elif 'NYT' in id:
        ## e.g. 
        ## 1989/03/11/0230638.xml_LDC_NYT
        pub      = 'NYT'
        pub_date = id[0:10].replace('/', '-')
    else:
        ## e.g. 
        ## Caribbean-Today;-Miami_1996-12-31_26b696eae2887c8cf71735a33eb39771
        pieces   = id.split("_")
        pub      = pieces[0]
        pub_date = pieces[1]

        ## remove T00:00:00Z from dates
        ## e.g. 2013-03-19T00:00:00Z
        if 'T' in pub_date:
            pub_date = pub_date.split('T')[0]
    return (pub, pub_date)

def write_chunk(
        resultset,
        filename):
    df = pd.DataFrame(resultset)
    df.to_csv(filename, mode = "a", header = False, index = False)

def export_query(
        colwise_query,
        filename):
    r = colwise_query.all()
    write_chunk(r, filename)
    return filename

def build_event_annotations_query(
        db_session):
    print(event_cols)
    q = (db_session
            .query(CodeEventCreator))
    return q

def export_event_annotations(
        db_session,
        filename):
    q = build_event_annotations_query(db_session)
    export_query(q, filename)
    return filename

def gen_event_export(
        filename):
    # Doesn't seem to do anything?
    users = {u.id: u.username for u in db_session.query(User).all()}
    annotations = CodeEventCreator
    cols  = [x.name for x in annotations.__table__.columns]

    chunksize = 1000
    resultset = []

    annotations_n = db_session.query(annotations).count()
    chunks_n = int(math.ceil(annotations_n / chunksize))
    
    print("Query:")
    for i in range(0, chunks_n):
        if i % 50 == 0:
            print("  " + str(i) + "...")
        offset = i*chunksize
        q  = (db_session
                  .query(
                      annotations,
                      ArticleMetadata)
                  .join(ArticleMetadata)
                  .order_by(annotations.id)
                  .offset(offset)
                  .limit(chunksize))
        r = q.all()

        resultset.extend(r)

    print("  " + str(i) + "...DONE")
        
    ## do this in chunks to save memory

    header = cols[:]
    header.extend(['publication', 'pub_date', 'solr_id'])

    ## write headers
    df = pd.DataFrame([], columns = header)
    df.to_csv(filename, encoding = 'utf-8', index = False)
    
    i = 0
    print("Resultset:")
    for row in resultset:
        fp  = row[0]
        db_id  = row[1].db_id
        i += 1

        ## store all fields in a row in a tuple
        to_print = ()
        for c in cols:
            if c == 'coder_id':
                to_print += ( users[fp.__getattribute__(c)], )
            else:
                to_print += ( validate(fp.__getattribute__(c)), )

        ## add publication, publication date, and solr_id
        pub      = ''
        pub_date = ''
        solr_id  = db_id 
        pub_info = split_solr_id(solr_id)
        to_print += pub_info
        to_print += (solr_id,)

        df = pd.DataFrame([to_print], columns = header)
        df.to_csv(filename, mode = "a", header = False, index = False)

        if i % 50000 == 0:
            print("  " + str(i) + "...")
    print("  " + str(i) + "...DONE")
    return filename

