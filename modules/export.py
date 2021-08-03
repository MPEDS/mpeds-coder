# -*- coding: utf-8 -*-
"""Tools to generate exports"""

import datetime as dt
import string

import pandas as pd
from sqlalchemy.exc import OperationalError
from sqlalchemy import func, desc, distinct, or_
from sqlalchemy.sql import select, func
from sqlalchemy.schema import Table

from ..database import db_session
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


def gen_event_export(
    filename):
    users = {u.id: u.username for u in db_session.query(User).all()}
    annotations = CodeEventCreator
    cols  = [x.name for x in annotations.__table__.columns]

    resultset = []

    annotations_n = db_session.query(annotations).count()
    
    print("Query:")
    for i in range(0, annotations_n):
        if i % 50 == 0:
            print("  " + str(i) + "...")
        offset = i*1000
        q  = (db_session
                  .query(
                      annotations,
                      ArticleMetadata)
                  .join(ArticleMetadata)
                  .order_by(annotations.id)
                  .offset(offset)
                  .limit(1000))
        r = q.all()

        if len(r) <= 0:
            print("  " + str(i) + "...DONE")
            break
        
        resultset.extend(r)

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
        am  = row[1]
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
        solr_id  = am.db_id 
        if am.db_id is None:
            pass
        elif 'AGW' in am.db_id:
            ## e.g.
            ## AGW_AFP_ENG_20040104.0056
            pieces   = am.db_id.split("_")
            pub      = "-".join(pieces[0:3])
            pub_date = pieces[3].split('.')[0]
            pub_date = dt.datetime.strptime(pub_date, '%Y%m%d').strftime('%Y-%m-%d')
        elif 'NYT' in am.db_id:
            ## e.g. 
            ## 1989/03/11/0230638.xml_LDC_NYT
            pub      = 'NYT'
            pub_date = am.db_id[0:10].replace('/', '-')
        else:
            ## e.g. 
            ## Caribbean-Today;-Miami_1996-12-31_26b696eae2887c8cf71735a33eb39771
            pieces   = am.db_id.split("_")
            pub      = pieces[0]
            pub_date = pieces[1]

            ## remove T00:00:00Z from dates
            ## e.g. 2013-03-19T00:00:00Z
            if 'T' in pub_date:
                pub_date = pub_date.split('T')[0]
            
        to_print += ( pub, pub_date, solr_id )

        df = pd.DataFrame([to_print], columns = header)
        df.to_csv(filename, mode = "a", header = False, index = False)

        if i % 50000 == 0:
            print("  " + str(i) + "...")
    print("  " + str(i) + "...DONE")
    return filename

