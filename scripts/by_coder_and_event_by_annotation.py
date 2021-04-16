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

def catDuplicatedVariables(df, groupbylist, valcollist):
    df = (df
          .filter(groupbylist + valcollist)
          .groupby(groupbylist)
          .agg(lambda x: '|||'.join(x.fillna('').astype('unicode')))
          .reset_index()
          )
    return df

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

def query_to_pd(
        table,
        session):

    ## Get tables into data frames
    q = (
        session
        .query(table)
        .order_by('id')
        )
    out = pd.read_sql_query(
        q.statement, 
        # Old pandas fears real connections
        #q.session.connection())
        q.session.get_bind())
    return out

def pivot_annotations_wider(
        annotation_long,
        dim_cols,
        col_prefix):

    ## Concatenate duplicated variables
    catted = catDuplicatedVariables(
        df=annotation_long,
        groupbylist=dim_cols + ['variable'],
        valcollist=['value', 'text'])

    ## Reshape tables
    val = unstackWithoutMissings(
        df=catted,
        indexlist=dim_cols + ['variable'],
        valuecol='value')

    text = unstackWithoutMissings(
        df=catted,
        indexlist=dim_cols + ['variable'],
        valuecol='text')

    ## Merge article annotations and rename columns
    wide = (
        val
        .join(text, how='outer')
        .reset_index()
        .swaplevel(0, 1, axis=1)
        )
    # NB columns are multilevel
    wide.columns = [col_prefix + '_' + '_'.join(col).strip('_')
                       for col in wide.columns.values]

    ## Align join key names
    prefixless_dims = {'_'.join([col_prefix, c]):c for c in dim_cols}
    wide = (
        wide
        .rename(columns=prefixless_dims)
        )
    return wide

def merge_pivot_times(
      annotation_longs):

    ## Create dfs with max and min timestamps from all levels
    time_dfs = [df.filter(['coder_id', 'article_id', 'timestamp'])
                   for df in annotation_longs]

    times = pd.concat(time_dfs)
    times_wide = (times
                  .dropna()
                  .groupby(['coder_id', 'article_id'])
                  .agg(['min', 'max'])
                  .reset_index()
                  .swaplevel(0, 1, axis=1)
                  )
    times_wide.columns = ['article_' + '_'.join(col).strip('_')
                          for col in times_wide.columns.values]
    times_wide = (times_wide
                  .rename(columns={'article_coder_id': 'coder_id'})
                  .rename(columns={'article_article_id': 'article_id'})
                  )
    return times_wide

def genByCoderAndEventByAnnotation(
        session,
        coder_event_table,
        user_table,
        article_metadata_table,
        coder_article_table = None):

    ## Get tables into data frames
    event_long = query_to_pd(coder_event_table, session)

    u_q = (session
           .query(user_table.id.label('coder_id'), user_table.username)
           )
    user = pd.read_sql_query(u_q.statement, 
                             # Old pandas fears real connections
                             #u_q.session.connection())
                             u_q.session.get_bind())

    am_q = (session
            .query(article_metadata_table.id,
                   article_metadata_table.title,
                   article_metadata_table.db_name,
                   article_metadata_table.db_id,
                   article_metadata_table.filename,
                   article_metadata_table.pub_date,
                   article_metadata_table.publication,
                   article_metadata_table.source_description
                   )
            )
    am = pd.read_sql_query(am_q.statement, 
                           # Old pandas fears real connections
                           #am_q.session.connection())
                           am_q.session.get_bind())

    e_wide = pivot_annotations_wider(
        event_long,
        dim_cols=['coder_id', 'article_id', 'event_id'],
        col_prefix='event')

    annotation_longs = [event_long]
    annotaion_wides = [e_wide]

    if coder_article_table is not None:
        ca_long = query_to_pd(coder_article_table, session)
        ca_wide = pivot_annotations_wider(
          ca_long,
          dim_cols=['coder_id', 'article_id'],
          col_prefix='article')
        annotation_longs = annotation_longs + [ca_long]
    else:
        ca_wide = None

    times_wide = merge_pivot_times(annotation_longs)
    am = (am
          .rename(columns={'id': 'article_id'})
          )

    ## Grand Unified Merge
    if coder_article_table is None:
        all_wide = (
            e_wide
            .merge(times_wide, how='outer', on=['coder_id', 'article_id'])
            .merge(user, how='left', on=['coder_id'])
            .merge(am, how='left', on='article_id')
            )
    else:
        all_wide = (
            ca_wide
            .merge(e_wide, how='outer', on=['coder_id', 'article_id'])
            .merge(times_wide, how='outer', on=['coder_id', 'article_id'])
            .merge(user, how='left', on=['coder_id'])
            .merge(am, how='left', on='article_id')
            )

    return all_wide

export = genByCoderAndEventByAnnotation(
    session=database.db_session,
    coder_event_table=models.CodeEventCreator,
    user_table=models.User,
    article_metadata_table=models.ArticleMetadata,
    coder_article_table=None) #models.CoderArticleAnnotation)

## Create df of counts by coder and article
counts_by_coder_and_event = (
    export
    .filter(['coder_id', 'article_id', 'event_id'])
    .groupby(['coder_id', 'article_id'])
    .agg(['count'])
    .reset_index()
    )
counts_by_coder_and_event.columns = ['coder_id', 'article_id', 'events']

#print counts_by_coder_and_event

filename = ('%s/exports/%s_by_coder_and_event_by_annotation_%s.csv' 
            % (config.WD, 
               config.MYSQL_DB, 
               dt.datetime.now().strftime('%Y-%m-%d_%H%M%S')))

export.to_csv(filename, index=False, encoding='utf8')
