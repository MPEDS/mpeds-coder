import sys

import pandas as pd
import sqlalchemy
import sqlalchemy.orm

import solr

class Wrangler:
    def __init__(self):
        pass

    def test_db(self, con):
        user_df = pd.read_sql_table("user", con=con)
        return user_df

    def test_solr(self):
        pass
