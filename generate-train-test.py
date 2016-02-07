from database import db_session, init_db
from models import ArticleMetadata, CodeFirstPass, CodeSecondPass
from sqlalchemy import func
from datetime import datetime
import random
import pandas as pd
import numpy as np

today_str = datetime.today().strftime('%Y-%m-%d')

## get the database of variables
df_db = pd.DataFrame([(x[1].db_id, x[0].variable, x[0].value, x[0].text) \
                for x in db_session.query(CodeFirstPass, ArticleMetadata).\
                join(ArticleMetadata).filter(~CodeFirstPass.variable.in_(['load', 'protest', 'multi', 'nous', 'ignore'])).all()],\
                columns = ['id', 'variable', 'value', 'text'])

def findVariableLocation(id, variable):
    """ Gets the first instance of variable in the article text. """
    values = df_db[(df_db.variable == variable) & (df_db.id == id)].value.values

    ## paragraph numbers are noted by pp-start-end, indexed from 0. 
    ## meta data is included and will be indexed as -1
    try:
        values = map(lambda x: -1 if 'meta' in x else int(x.split('-')[0]), values) 
    except ValueError as detail:
        print(detail)
        pass ## some weirdness happening but whatever we'll just catch

    ## TK: Make any affordances for things that just say, non-descriptly, 'protest', like in form?
    ## I think this is okay for now since it still provides information about the locus of the action.

    if len(values) < 1:
        return None

    return min(values)

# def addParagraphNums():
#     """ Take the existing files and add paragraph numbers for form, issue, location, time, and size """
#    for pub in ['NYT', 'WaPo', 'AGW-AFP']:
#         for filename in ['training', 'test']:
#             df_pub = pd.read_csv("generate-train-test/haystack-%s-mpeds-%s_2015-08-30.csv" % (filename, pub))

#             for variable in ['form', 'issue', 'loc', 'time', 'size']:
#                 print(filename, pub, variable)
#                 ## if at least one record is yes or maybe
#                 var_index = df_pub[(df_pub.percent_yes > 0) | (df_pub.percent_maybe > 0)].id
#                 df_pub[variable + '_paragraph'] = var_index.apply(findVariableLocation, args = [variable])

#             df_pub.to_csv("generate-train-test/haystack-%s-mpeds-%s_2015-08-30.csv" % (filename, pub), index = False)

# def addNumCoders(df):
#     """ Take existing files and add number of coders. """
#     df_numcoders = pd.DataFrame({'num_coders': df.num_coders, 'id' = df.index)
#     for pub in ['NYT', 'WaPo', 'AGW-AFP']:
#         for filename in ['training', 'test']:
#             df_pub = pd.read_csv("generate-train-test/haystack-%s-mpeds-%s_2015-08-30.csv" % (filename, pub))
#             df_pub = df_pub.merge(df_numcoders)
#             df_pub.to_csv("generate-train-test/haystack-%s-mpeds-%s_2015-08-30.csv" % (filename, pub), index = False)

def generateTrainTestSets():
    """ Generates training and test sets by publication from the MPEDS database. """
    cfp_dict  = {}

    for cfp, am in db_session.query(CodeFirstPass, ArticleMetadata).join(ArticleMetadata).filter(CodeFirstPass.variable == 'protest').all():
        pub = ''
        if 'AGW' in am.db_id:
            pub = "-".join(am.db_id.split("_")[0:2])
        elif 'NYT' in am.db_id:
            pub = 'NYT'
        else:
            pub = am.db_id.split("_")[0]

        if am.db_id not in cfp_dict:
        	cfp_dict[am.db_id] = {"coder_value": [], "num_coders": 0, "pub": pub, "percent_yes": 0, "percent_maybe": 0, "percent_no": 0}
        
        cfp_dict[am.db_id]["coder_value"].append( (cfp.coder_id, cfp.value) )
        cfp_dict[am.db_id]["num_coders"] += 1

    for article_id, v in cfp_dict.items():
        for coder, decision in v["coder_value"]:
            ## not sure why this would be null, but it is
            if not decision:
                continue

            ## add to percent
            cfp_dict[article_id]["percent_" + decision] += 1.

        ## divide all
        for decision in ['yes', 'no', 'maybe']:
            cfp_dict[article_id]["percent_" + decision] /= len(cfp_dict[article_id]["coder_value"])

    df = pd.DataFrame(cfp_dict).T
    del df['coder_value']

    df['id'] = df.index

    ## add in variable paragraph numbers
    for variable in ['form', 'issue', 'loc', 'time', 'size']:
        print(variable)
        ## if at least one record is yes or maybe
        var_index = df[(df.percent_yes > 0) | (df.percent_maybe > 0)].id
        df[variable + '_paragraph'] = var_index.apply(findVariableLocation, args = [variable])

    for pub in ['NYT', 'WaPo', 'AGW-AFP']:
        df_pub = df[df.pub == pub]

        ## 90/10 split
        rows = random.sample(df_pub.index, int(df_pub.index.shape[0]*0.9))
        df_pub.ix[rows].to_csv("generate-train-test/haystack-training-mpeds-%s_%s.csv" % (pub, today_str), index = False)
        df_pub.drop(rows).to_csv("generate-train-test/haystack-test-mpeds-%s_%s.csv" % (pub, today_str), index = False)

