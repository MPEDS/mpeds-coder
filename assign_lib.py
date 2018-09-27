from database import db_session
from models import User, ArticleMetadata, CodeFirstPass, CodeSecondPass, CodeEventCreator, ArticleQueue, SecondPassQueue, EventCreatorQueue, Event
from sqlalchemy import func, or_, distinct, desc
from datetime import datetime
from itertools import combinations
import csv, pickle, random
import pandas as pd
import numpy as np
from math import factorial

########
### USER MANAGEMENT
########

def addUser(username, password, authlevel):
    added = db_session.add(User(username = username, password = password, authlevel = authlevel))
    db_session.commit()

    return added

def addUsers(filename):
    users = []
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            users.append( User(username = row[0], password = row[1], authlevel = row[2]) )

    added = db_session.add_all(users)
    db_session.commit()

    return added

def deleteUser(username):
    user = db_session.query(User).filter(User.username == username).first()
    aqs  = db_session.query(ArticleQueue).filter(ArticleQueue.coder_id == user.id).delete()

    user_r = db_session.delete(user)
    db_session.commit()

    if user_r:
        print("User %s deleted, %d article queue items deleted." % (username, aqs) )
        return aqs

########
### Generating samples
########

def generateSample(n, db_name = None, pass_number = '1', publication = None):
    """Create a sample of articles of size N. """
    if pass_number == '1':
        if db_name == None:
            raise Exception('Need a database name for first pass coding.')
            return

        ## query existing articles and all articles in the specified database.
        existing = [x[0] for x in db_session.query(distinct(ArticleQueue.article_id)).all()]
        query    = [x.id for x in db_session.query(ArticleMetadata).filter_by(db_name = db_name).all()]
    elif pass_number == '2':
        ## query existing articles
        existing = [x[0] for x in db_session.query(distinct(SecondPassQueue.article_id)).all()]

        ## prioritize articles which have more than 1 coder
        df = pd.DataFrame(db_session.query(CodeFirstPass.article_id, CodeFirstPass.coder_id).\
            filter(CodeFirstPass.variable == 'protest', or_(CodeFirstPass.value == 'yes', CodeFirstPass.value == 'maybe')).\
            all(), columns = ['article_id', 'coder_id'])

        gr = df.groupby('article_id').agg(np.count_nonzero)
        gr.columns   = ['count']

        ## filter out singles
        gt_one = gr[gr['count'] > 1].index
        df_gt1 = df[~df['article_id'].isin(gt_one)]

        ## dump all unique articles into population
        query = df_gt1.article_id.unique()

        ## all of those which have only been coded by 1
        df_1 = df[~df['article_id'].isin(gt_one)]
        query = np.append(query, df_1.article_id.unique())
    elif pass_number == 'ec':
        ## query existing articles and all articles in the specified database.
        existing = [x[0] for x in db_session.query(distinct(EventCreatorQueue.article_id)).all()]

        ## query by publication
        ## database will be implicit        
        if publication:
            publication = "-".join(publication.split())
            query = [x.id for x in db_session.query(ArticleMetadata).filter(ArticleMetadata.db_id.like('%s%%' % publication)).all()]
        else:
            query = [x.id for x in db_session.query(ArticleMetadata).filter_by(db_name = db_name).all()]

    ## if articles aren't in existing queues, add them to the population
    population = list(set(query) - set(existing))

    ## if the size of the population is smaller than n, return the population
    if len(population) < n:
        sample = population
    else:
        sample = random.sample(population, n)
    
    return sample


def getArticlesbyID(ids):
    articles = [x.id for x in db_session.query(ArticleMetadata).filter(ArticleMetadata.id.in_(ids)).all()]
    return articles


def getUnpairedSecondPass():
    """ Gets all second pass articles which have only been coded by one coder. """
    q  = [(x.article_id, x.coder_id) for x in db_session.query(SecondPassQueue).all()]
    df = pd.DataFrame(q, columns = ['article_id', 'coder_id'])
    vc = df.article_id.value_counts()

    return list(vc[vc == 1].index)


def assignmentToBin(article_ids, coder_bins, pass_number = '1'):
    """Given a list of bins, assign one article to each coder in the bin"""
    i = 0
    print(article_ids)
    for article_id in article_ids:
        my_bin = coder_bins[i]

        for coder_id in my_bin:
            ## add to coder queue
            assignmentToCoders([article_id], [coder_id], pass_number)
        if i == len(coder_bins) - 1:
            i = 0
        else:
            i += 1

    return i


def assignDoubleCheck(coder_id1, coder_id2, n, pass_number = 1):
    """ 
        Assign n articles coded by coder_id1 to coder_id2. 
        Restricted to articles which have only been coded once, by a coder in coder_id1.
    """

    ## Get all coded articles
    if pass_number == 1:
        df = pd.DataFrame(db_session.query(ArticleQueue.article_id, ArticleQueue.coder_id).\
            filter(ArticleQueue.coded_dt != None).all(), columns = ['article_id', 'coder_id'])

        ## get those queues which do not belong to double checked coders
        existing = [x[0] for x in db_session.query(distinct(ArticleQueue.article_id)).\
            filter(~ArticleQueue.coder_id.in_(coder_id1)).all()]
    else:
        df = pd.DataFrame(db_session.query(SecondPassQueue.article_id, SecondPassQueue.coder_id).\
            filter(SecondPassQueue.coded_dt != None).all(), columns = ['article_id', 'coder_id'])

        existing = [x[0] for x in db_session.query(distinct(SecondPassQueue.article_id)).\
            filter(~SecondPassQueue.coder_id.in_(coder_id1)).all()]

    ## get all those coded by only one
    gr = df.groupby('article_id').agg(np.count_nonzero)
    gr.columns   = ['count']
    index_single = gr[gr['count'] == 1].index

    ## select singles which are in coder_id1 and not in any other queue
    df = df[df['article_id'].isin(index_single) & df['coder_id'].isin(coder_id1) & ~df['article_id'].isin(existing)]

    ## pass to assignmentToCoders
    assignmentToCoders(df.article_id[0:n].values, coder_id2, pass_number = pass_number)


def assignmentToCoders(article_ids, coder_ids, pass_number = '1'):
    """ Assigns each article to all coders in list. """
    if pass_number == '1':
        model = ArticleQueue
    elif pass_number == '2':
        model = SecondPassQueue
    elif pass_number == 'ec':
        model = EventCreatorQueue

    ## add to queues
    to_add = []
    for coder_id in coder_ids:
        for a in article_ids:
            if pass_number == '1':
                item = ArticleQueue(article_id = a, coder_id = coder_id)
            elif pass_number == '2':
                item = SecondPassQueue(article_id = a, coder_id = coder_id)
            elif pass_number == 'ec':
                item = EventCreatorQueue(article_id = a, coder_id = coder_id)

            to_add.append( item )

    db_session.add_all(to_add)
    db_session.commit()

    return len(to_add)

def transferCoderToCoder(coder1, coder2, pass_number = '1', n_to_assign = 0):
    """ Transfer articles from coder1 to coder2 """
    if type(coder1) != list and type(coder2) != list:
        print('coder1 and coder2 must be list types')
        return -1

    if pass_number == '1':
        model  = ArticleQueue 
    elif pass_number == '2':
        model  = SecondPassQueue
    elif pass_number == 'ec':
        model = EventCreatorQueue

    src_aq = db_session.query(model).filter(model.coded_dt == None, model.coder_id.in_(coder1)).all()
    dst_aq = [x.article_id for x in db_session.query(model).filter(model.coder_id.in_(coder2)).all()]

    ## shuffle so if we're transferring from many to one we don't just get one coder
    random.shuffle(src_aq)

    n_transferred = 0
    for aq in src_aq:
        if aq.article_id in dst_aq:
            ## skip if the article is in the destination queue
            ## this has the consequence that it will return to the original coder
            continue
        else:
            for c in coder2:
                if pass_number == '1':
                    new_aq = ArticleQueue( article_id = aq.article_id, coder_id = c )
                elif pass_number == '2':
                    new_aq = SecondPassQueue( article_id = aq.article_id, coder_id = c )
                elif pass_number == 'ec':
                    new_aq = EventCreatorQueue( article_id = aq.article_id, coder_id = c )

            db_session.add(new_aq)
            db_session.delete(aq)
            dst_aq.append(aq.article_id)
            n_transferred += 1

        if n_transferred >= n_to_assign:
            break

    ## TK: This query is kind of buggy for some reason.

    ## assert that dupes have not been entered
    # dupes = db_session.query(model).filter(model.coder_id.in_(coder2)).\
    #     group_by(model.article_id, model.coder_id).having(func.count(model.id) > 1).all()

    # ## rollback if this there are dupes
    # if len(dupes) != 0:
    #     db_session.rollback()
    #     print("%d duplicates have been detected. Rolling back." % len(dupes))
    #     return -1

    db_session.commit()
    return n_transferred


def createBins(coders, n):
    """Create bins of users given a list and a bin size"""
    ## create bins
    bins = list(combinations(coders, n))

    ## shuffle the bins so the first few users don't get more articles
    random.shuffle(bins)

    return bins


def generateSampleNumberForBins(num_per_coder, n, k):
    """
        Generate the number of articles necessary to assign each coder * number
        of articles, given the bin size.
        Formula is: (n - 1)! / (k - 1)! (n - 1)!
    """

    a = factorial(n - 1) / ( factorial( k - 1 ) * factorial(n - k) )

    ## the number per coder doesn't divide evenly into the number of appearances
    ## subtract the remainder
    remainder = num_per_coder % a
    num_per_coder -= remainder

    ## get number of bins
    num_bins = len(list(combinations(range(0,n), k)))

    return int(num_bins * num_per_coder / a)

#####
### DUPE HANDLING
#####

def deleteDupes(coder):
    """ If a dupe was coded more than once (somehow??) 
        then remove the one that was coded second.
    """
    dupes = db_session.query(SecondPassQueue.article_id, SecondPassQueue.coder_id, func.count(SecondPassQueue.id)).\
        filter(SecondPassQueue.coder_id == coder).\
        group_by(SecondPassQueue.article_id, SecondPassQueue.coder_id).having(func.count(SecondPassQueue.id) > 1).all()

    dupes_all = db_session.query(SecondPassQueue).\
        filter(SecondPassQueue.article_id.in_([x[0] for x in dupes]), SecondPassQueue.coder_id == coder, SecondPassQueue.coded_dt != None).\
        order_by(desc(SecondPassQueue.coded_dt)).all()

    ## order by descending and delete the first item you come across
    deleted = []
    for aq in dupes_all:
        if aq.article_id not in deleted:
            deleted.append(aq.article_id)
            db_session.delete(aq)

    db_session.commit()


def distributeDupes(coder1, coder2_list):
    """ Takes dupes from coder1 and distributes them to coders 
    in the coder2_list if they do not have this article."""

    ## collect dupes in coder1 queue
    dupes = db_session.query(SecondPassQueue.article_id, SecondPassQueue.coder_id, func.count(SecondPassQueue.id)).\
        filter(SecondPassQueue.coder_id == coder1).\
        group_by(SecondPassQueue.article_id, SecondPassQueue.coder_id).having(func.count(SecondPassQueue.id) > 1).all()

    ## get list of existing articles in coder2_list queues
    ## NB: A list comprehension embedded in a dict comprehension!
    existing = {coder_id: [x[0] for x in db_session.query(distinct(SecondPassQueue.article_id)).filter(SecondPassQueue.coder_id == coder_id).all()] for coder_id in coder2_list}

    to_del = []
    to_add = {x: [] for x in existing.keys()}
    nope   = []
    for article_id, old_coder_id, _ in dupes:
        reassigned = False
        ## find the dupe to delete
        aq = db_session.query(SecondPassQueue).\
            filter(
                SecondPassQueue.article_id == article_id,
                SecondPassQueue.coder_id   == old_coder_id,
                SecondPassQueue.coded_dt   == None
            ).first()

        ## if aq is None. This shouldn't happen but it has.
        if not aq:
            continue

        ## go through a random list of the other coders.
        ## if article is not in their queue, add it.
        coders = existing.keys()
        random.shuffle(coders)

        for coder_id in coders:
            if article_id not in existing[coder_id]:
                ## create new queue item
                new_aq = SecondPassQueue(article_id = article_id, coder_id = coder_id)
                to_add[coder_id].append(new_aq)

                reassigned = True
                break

        if reassigned:
            to_del.append( aq )
        else:
            nope.append( aq )

    ## commit
    for aq in to_del:
        db_session.delete(aq)
    for k in to_add.keys():
        db_session.add_all(to_add[k])
    db_session.commit()

    return "%d reassigned, %d could not be reassigned." % (len(to_del), len(nope))


def fix_dupes():
    dupes = db_session.query(ArticleQueue.article_id, ArticleQueue.coder_id, func.count(ArticleQueue.id)).\
        group_by(ArticleQueue.article_id, ArticleQueue.coder_id).having(func.count(ArticleQueue.id) > 1).all()

    to_del = []
    for row in dupes:
        aq = db_session.query(ArticleQueue).\
            filter(
                ArticleQueue.article_id == row[0], 
                ArticleQueue.coder_id   == row[1],
                ArticleQueue.coded_dt  == None
            ).first()

        to_del.append( aq )
        db_session.delete(aq)

    db_session.commit()

    return len(to_del)

