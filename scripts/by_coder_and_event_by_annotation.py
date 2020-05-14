## Script to output wide-format CSV of content by coder and event by annotation
import sys
import datetime as dt

import pandas as pd
import sqlalchemy

from context import config
from context import database
from context import models

def unstackWithoutMissings(df, indexlist, valuecol):
    keepers = indexlist + [valuecol]
    widedf = (df
             .filter(keepers)
             .dropna()
             # Next block should remove both empty strings and missings
             .assign(length=lambda x: x[valuecol].astype('unicode').str.len())
             .query('length > 0')
             .drop('length', axis=1)
             .set_index(indexlist)
             .unstack()
             )
    return widedf

def numberDuplicatedVariables(df, groupbylist, varcol):
    ## I can't figure out how to assign this in an ungrouped pipeline, alas
    df['varocc'] = (df
                    .groupby(groupbylist)
                    .cumcount() + 1
                    )
    df = (df
          .assign(varocc=lambda x: "_" + x.varocc.astype('str'))
          .assign(varocc=lambda x: x.varocc.replace("_1", ""))
          .assign(variable=lambda x: x['variable'] + x['varocc'])
          )
    return df

def genByCoderAndEventByAnnotation(
        session,
        coder_event_table,
        coder_article_table,
        user_table,
        article_metadata_table):

    ## Get tables into data frames
    event_q = (session
               .query(coder_event_table)
               )
    event_long = pd.read_sql_query(event_q.statement, 
                                   # Old pandas fears real connections
                                   #event_q.session.connection())
                                   event_q.session.get_bind())

    ca_q = (session
            .query(coder_article_table)
            )
    ca_long = pd.read_sql_query(ca_q.statement, 
                                # Old pandas fears real connections
                                #ca_q.session.connection())
                                ca_q.session.get_bind())

    u_q = (session
           .query(user_table.id.label('coder_id'), user_table.username)
           )
    user = pd.read_sql_query(u_q.statement, 
                             # Old pandas fears real connections
                             #u_q.session.connection())
                             u_q.session.get_bind())

    am_q = (session
            .query(article_metadata_table)
            )
    am = pd.read_sql_query(am_q.statement, 
                           # Old pandas fears real connections
                           #am_q.session.connection())
                           am_q.session.get_bind())

    ## Number duplicated variables
    event_long = numberDuplicatedVariables(
                     df=event_long,
                     groupbylist=['coder_id', 'article_id', 
                                 'event_id', 'variable'],
                     varcol='variable')

    ca_long = numberDuplicatedVariables(
                     df=ca_long,
                     groupbylist=['coder_id', 'article_id', 
                                 'variable'],
                     varcol='variable')

    ## Reshape tables
    e_val = unstackWithoutMissings(
        df=event_long,
        indexlist=['coder_id', 'article_id', 'event_id', 'variable'],
        valuecol='value')

    e_text = unstackWithoutMissings(
         df=event_long,
         indexlist=['coder_id', 'article_id', 'event_id', 'variable'],
         valuecol='text')

    ca_val = unstackWithoutMissings(
         df=ca_long,
         indexlist=['coder_id', 'article_id', 'variable'],
         valuecol='value')

    ca_text = unstackWithoutMissings(
          df=ca_long,
          indexlist=['coder_id', 'article_id', 'variable'],
          valuecol='text')

    ## Merge events and rename columns
    e_wide = (e_val
              .join(e_text, how='outer')
              .reset_index()
              .swaplevel(0, 1, axis=1)
              )
    e_wide.columns = ['event_' + '_'.join(col).strip('_') 
                      for col in e_wide.columns.values]

    ## Merge article annotations and rename columns
    ca_wide = (ca_val
               .join(ca_text, how='outer')
               .reset_index()
               .swaplevel(0, 1, axis=1)
               )
    ca_wide.columns = ['article_' + '_'.join(col).strip('_') 
                      for col in ca_wide.columns.values]

    ## Create df with max and min timestamps from both levels
    ea_times = (event_long
                .filter(['coder_id', 'article_id', 'timestamp'])
                )

    ca_times = (ca_long
                .filter(['coder_id', 'article_id', 'timestamp'])
                )

    times = pd.concat([ea_times, ca_times])
    times_wide = (times
                  .dropna()
                  .groupby(['coder_id', 'article_id'])
                  .agg(['min', 'max'])
                  .swaplevel(0, 1, axis=1)
                  )
    times_wide.columns = ['article_' + '_'.join(col).strip('_') 
                          for col in times_wide.columns.values]

    ## Grand Unified Merge
    all_wide = (user
                .merge(ca_wide, how='outer', 
                       left_on=['coder_id'],
                       right_on=['article_coder_id'])
                .drop(['article_coder_id'], axis=1)
                .rename(columns={'article_article_id': 'article_id'})
                .merge(e_wide, how='outer', 
                       left_on=['coder_id', 'article_id'],
                       right_on=['event_coder_id', 'event_article_id'])
                .drop(['event_coder_id', 'event_article_id'], axis=1)
                .rename(columns={'event_event_id': 'event_id'})
                .merge(am, how='left', left_on='article_id', right_on='id')
                .drop(['id'], axis=1)
                )

    return all_wide

export = genByCoderAndEventByAnnotation(
    session=database.db_session,
    coder_event_table=models.CodeEventCreator,
    coder_article_table=models.CoderArticleAnnotation,
    user_table=models.User,
    article_metadata_table=models.ArticleMetadata)

## Create df of counts by coder and article
counts_by_coder_and_event = (
    export
    .filter(['coder_id', 'article_id', 'event_id'])
    .groupby(['coder_id', 'article_id'])
    .agg(['count'])
    .reset_index()
    )
counts_by_coder_and_event.columns = ['coder_id', 'article_id', 'events']

print counts_by_coder_and_event

filename = '%s/exports/by_coder_and_event_by_annotation_%s.csv' % (config.WD, dt.datetime.now().strftime('%Y-%m-%d_%H%M%S'))

export.to_csv(filename)
