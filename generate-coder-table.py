"""
Generates the coder table independently of the dashboard.
"""

from .database import db_session
from .models import ArticleMetadata, CodeEventCreator, User

from sqlalchemy.exc import OperationalError
from sqlalchemy import func, desc, distinct, or_
from sqlalchemy.sql import select, func
from sqlalchemy.schema import Table

import pandas as pd

import datetime as dt

def validate( x ):
    """ replace newlines, returns, and tabs with blank space """
    if x:
        if type(x) == str:
            x = x.replace("\n", " ")
            x = x.replace("\r", " ")
            x = x.replace("\t", " ")
        return x
    else:
        return "0"


def main():
    users = {u.id: u.username for u in db_session.query(User).all()}
    model = CodeEventCreator
    cols  = [x.name for x in model.__table__.columns]

    resultset = []
    filename = '/var/www/campus_protest/exports/coder-table_%s.csv' % (dt.datetime.now().strftime('%Y-%m-%d'))
    
    query = db_session.query(func.max(model.id)).first()
    
    print("Query:")
    for i in range(0, 1000):
        if i % 50 == 0:
            print(("  " + str(i) + "..."))
        offset = i*1000
        query  = db_session.query(model, ArticleMetadata).\
                 join(ArticleMetadata).order_by(model.id).offset(offset).limit(1000).all()

        if len(query) <= 0:
            print(("  " + str(i) + "...DONE"))
            break
        
        resultset.extend(query)

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
            ## HOWEVER
            ## North-Carolina-A-_-T-State-University_The-A_T-Register_2018-03-21T00:00:00Z_96c6bc5e6701f8b1ccbba7a318cc50ad
            
            pieces   = am.db_id.split("_")
            if len(pieces) > 3:
                pub = '_'.join(pieces[0:-2])
            else:
                pub = pieces[0]
            
            pub_date = pieces[-2]

            ## remove T00:00:00Z from dates
            ## e.g. 2013-03-19T00:00:00Z
            if 'T' in pub_date:
                pub_date = pub_date.split('T')[0]
            
        to_print += ( pub, pub_date, solr_id )

        df = pd.DataFrame([to_print], columns = header)
        df.to_csv(filename, mode = "a", header = False, index = False, encoding = 'utf-8')

        if i % 50000 == 0:
            print(("  " + str(i) + "..."))
    print(("  " + str(i) + "...DONE"))

if __name__ == '__main__':
    main()
