# -*- coding: utf-8 -*-
import json
import urllib
import urllib2

""" 
Helper class for querying an Apache Solr database. 
"""

class Solr:
    def __init__(self):
        self.solr_url   = None


    def setSolrURL(self, url):
        self.solr_url = url


    def _getDocumentsFromIDChunk(self, ids):
        ids_qclause = '"' + '" OR "'.join(ids) + '"'
        ids_q = 'id: (' + ids_qclause + ')'
        
        docs  = self.getDocuments(ids_q)

        return docs


    def buildSolrQuery(self, q_dict):
        ''' Build a query for a Solr request. '''
        q = []
        for k, v in q_dict.iteritems():
            sub_q = '%s:"%s"' % (k, v)
            q.append(sub_q)

        query = ' AND '.join(q)
        return query


    def getResultsFound(self, q, fq = None):
        """ report the number of results found for any given request. """
        data = {
            'q':     q,
            'start': 0,
            'rows':  10,
            'wt':    'json'
        }

        if fq:
            data['fq'] = fq

        data = urllib.urlencode(data)
        req  = urllib2.Request(self.solr_url, data)
        res  = urllib2.urlopen(req)
        res  = json.loads(res.read())

        return res['response']['numFound']


    def getDocuments(self, q, fq = None):
        """ makes Solr requests to get article texts """

        data = {
            'q':     q,
            'start': 0,
            'rows':  10,
            'wt':    'json',
        }

        if fq:
            data['fq'] = fq

        data = urllib.urlencode(data)
        req  = urllib2.Request(self.solr_url, data)
        res  = urllib2.urlopen(req)
        res  = json.loads(res.read())

        numFound = res['response']['numFound']

        print("%d documents found." % numFound)

        interval = 100

        ## add 100 to get everything for sure
        numFound += interval

        articles = []
        for i in range(0, numFound, interval):
            data = {
                'q': q,
                'rows': interval,
                'start': i,
                'wt': 'json'
            }

            if fq:
                data['fq'] = fq

            data = urllib.urlencode(data)
            req  = urllib2.Request(self.solr_url, data)
            res  = urllib2.urlopen(req)
            res  = json.loads(res.read())

            articles.extend(res['response']['docs'])

            if i % 1000 == 0 and i > 0:
                print('%d documents collected.' % i)

        return articles

    def getDocumentsFromIDs(self, ids, maxclauses=1024):
        # Chunk trick from https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
        id_chunks = [ids[i:i + maxclauses] for i
                     in xrange(0, len(ids), maxclauses)]

        docs = list()
        # NB: making copies of this list will use up memory fast!
        for i in range(len(id_chunks)):
            print("### Chunk %d of %d" % (i + 1, len(id_chunks)))
            docs.extend(self._getDocumentsFromIDChunk(id_chunks[i]))
        
        return docs

