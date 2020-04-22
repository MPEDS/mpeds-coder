import sys

import pandas as pd
import sqlalchemy
import sqlalchemy.orm

import solr

class Wrangler:
    def __init__(self):
        self.solr = None

    def set_solr(self, url):
        self.solr = solr.Solr()
        self.solr.setSolrURL(url)

    def get_db_test(self, con):
        user_df = pd.read_sql_table("user", con=con)
        return user_df

    def run_solr_test(self, query_str, fq_str = None):
        retrieved_articles = self.solr.getResultsFound(query_str, fq_str)
        print("Retrieving %d articles..." % retrieved_articles)

        docs  = self.solr.getDocuments(query_str, fq = fq_str)

        solr_df = pd.DataFrame(docs)

        return "Article count: %d" % solr_df.shape[0]

