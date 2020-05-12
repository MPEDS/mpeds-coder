## Script to output wide-format CSV of content by coder and event by annotation
import sys
import datetime as dt

import pandas as pd
import sqlalchemy

from context import config
from context import database
from context import models


## Get tables into data frames
event_q = (database
           .db_session
           .query(models.CodeEventCreator)
           )
event_long = pd.read_sql_query(event_q.statement, 
                               # Old pandas fears real connections
                               #event_q.session.connection())
                               event_q.session.get_bind())

u_q = (database
       .db_session
       .query(models.User.id.label('coder_id'), models.User.username)
       )
user = pd.read_sql_query(u_q.statement, 
                         # Old pandas fears real connections
                         #u_q.session.connection())
                         u_q.session.get_bind())

am_q = (database
        .db_session
        .query(models.ArticleMetadata)
        )
am = pd.read_sql_query(am_q.statement, 
                       # Old pandas fears real connections
                       #am_q.session.connection())
                       am_q.session.get_bind())

ca_q = (database
        .db_session
        .query(models.CoderArticleAnnotation)
        )
ca_long = pd.read_sql_query(ca_q.statement, 
                            # Old pandas fears real connections
                            #ca_q.session.connection())
                            ca_q.session.get_bind())

## Number duplicated variables
## I can't figure out how to assign this in an ungrouped pipeline, alas
event_long['varocc'] = (event_long
                        .groupby(['coder_id', 'article_id', 
                                  'event_id', 'variable'])
                        .cumcount() + 1
                        )
ca_long['varocc'] = (ca_long
                     .groupby(['coder_id', 'article_id', 
                               'variable'])
                     .cumcount() + 1
                     )
event_long = (event_long
              .assign(varocc=lambda x: "_" + x.varocc.astype('str'))
              .assign(varocc=lambda x: x.varocc.replace("_1", ""))
              .assign(variable=lambda x: x['variable'] + x['varocc'])
              )
ca_long = (ca_long
           .assign(varocc=lambda x: "_" + x.varocc.astype('str'))
           .assign(varocc=lambda x: x.varocc.replace("_1", ""))
           .assign(variable=lambda x: x['variable'] + x['varocc'])
           )

## Reshape tables
e_val = (event_long
         .filter(['coder_id', 'article_id', 'event_id', 'variable', 'value'])
         .dropna()
         # Next block should remove both empty strings and missings
         .assign(length=lambda x: x.value.astype('str').str.len())
         .query('length > 0')
         .drop('length', axis=1)
         .set_index(['coder_id', 'article_id', 'event_id', 'variable'])
         .unstack()
         )

e_text = (event_long
          .filter(['coder_id', 'article_id', 'event_id', 'variable', 'text'])
          .dropna()
          # Next block should remove both empty strings and missings
          .assign(length=lambda x: x.text.astype('str').str.len())
          .query('length > 0')
          .drop('length', axis=1)
          .set_index(['coder_id', 'article_id', 'event_id', 'variable'])
          .unstack()
          )

ca_val = (ca_long
          .filter(['coder_id', 'article_id', 'variable', 'value'])
          .dropna()
          # Next block should remove both empty strings and missings
          .assign(length=lambda x: x.value.astype('str').str.len())
          .query('length > 0')
          .drop('length', axis=1)
          .set_index(['coder_id', 'article_id', 'variable'])
          .unstack()
          )

ca_text = (ca_long
           .filter(['coder_id', 'article_id', 'variable', 'text'])
           .dropna()
           # Next block should remove both empty strings and missings
           .assign(length=lambda x: x.text.astype('str').str.len())
           .query('length > 0')
           .drop('length', axis=1)
           .set_index(['coder_id', 'article_id', 'variable'])
           .unstack()
           )

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

## Create df of counts by coder and article
counts_by_coder_and_event = (
    e_wide
    .filter(['event_coder_id', 'event_article_id', 'event_event_id'])
    .groupby(['event_coder_id', 'event_article_id'])
    .agg(['count'])
    .reset_index()
    )
counts_by_coder_and_event.columns = ['coder_id', 'article_id', 'events']

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
            .merge(am, how='left', left_on='article_id', right_on='id')
            .drop(['id'], axis=1)
            )

## Clean up
print '***** Grand unified wide df *****'
print all_wide

filename = '%s/exports/by_coder_and_event_by_annotation_%s.csv' % (config.WD, dt.datetime.now().strftime('%Y-%m-%d_%H%M%S'))

#all_wide.to_csv(filename)
