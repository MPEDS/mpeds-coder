#!/usr/bin/env python
# encoding: utf-8

## adapted from Neal Caren's split_ln
## http://nealcaren.web.unc.edu/cleaning-up-lexisnexis-files/

import os, re, sys
from datetime import datetime

def parseLexisNexis(filename, output = "."):
    text = open(filename, 'r').read()

    # Figure out what metadata is being reported
    meta_list = list(set(re.findall('\\n([A-Z][A-Z-]*?):', text))) 

    ## set permanent columns
    header    = ['INTERNAL_ID', 'PUBLICATION', 'DATE', 'TITLE', 'EDITION']
    today_str = datetime.today().strftime('%Y-%m-%d')

    ## silly hack to find the end of the documents
    ## TK: This will break on abstracts
    # text = re.sub('                Copyright .*?\\r\\n','ENDOFILE', text)

    # clean up crud at the beginning of the file
    text = text.replace('\xef\xbb\xbf\r\n','') 

    ## Split by LN header
    ## odd numbers are search_id, evens are the documents
    docs = []
    ids  = []
    for i, d in enumerate(re.split("\s+(\d+) of \d+ DOCUMENTS", text)):
        if i == 0:
            pass
        elif i % 2 == 0:
            docs.append(d)
        else:
            ids.append(d)

    # remove blank rows
    docs = [f for f in docs if len(f.split('\r\n\r\n')) > 2] 
    
    # Keep only the commonly occuring metadata
    meta_list = [m for m in meta_list if float(text.count(m)) / len(docs) > .20] 

    articles = []
    ## Begin loop over each article
    for i, f in enumerate(docs):
        # Split into lines, and clean up the hard returns at the end of each line
        lines = [row.replace('\r\n', ' ').strip() for row in f.split('\r\n\r\n') if len(row) > 0]

        ## With an abstract, this is the format:
        # Copyright 1990 The New York Times Company: Abstracts
        #                  WALL STREET JOURNAL

        ## Skip the whole article if it's an abstract
        if 'Abstracts' in lines[0]:
            continue

        ## remove copyright
        lines = [row for row in lines if not re.match("^Copyright \d+.*$", row) and 'All Rights Reserved' not in row]

        ## make metadata dict
        meta_dict  = {k : '' for k in header}

        # doc_id  = lines[0].strip().split(' ')[0]
        pub     = lines[0].strip()
        date_ed = lines[1].strip()
        title   = lines[2].strip()

        ## format date into YYYY-MM-DD
        ## NYT format: July 27 2008 Sunday                               Late Edition - Final
        ## USATODAY:   April 7, 1997, Monday, FINAL EDITION
        ## WaPo:       June 06, 1996, Thursday, Final Edition

        date_ed = date_ed.replace(',', '')
        da      = re.split('\s+', date_ed)

        date = datetime.strptime(" ".join(da[0:3]), "%B %d %Y")
        date = date.strftime("%Y-%m-%d")
        ed   = " ".join( [x.strip() for x in da[4:]] )

        ## if edition is a time or day, skip it      
        if 'GMT' in ed or 'day' in ed:
            ed = ''
        
        ## Edit the text and other information
        paragraphs = []
        for line in lines[3:]:
            ## find out if this line is part of the main text
            if len(line) > 0 and line[:2] != '  ' and line != line.upper() and len(re.findall('^[A-Z][A-Z-]*?:',line)) == 0 and title not in line:
                ## remove new lines
                line = re.sub(r'\s+', ' ', line)
                line = line.replace('","','" , "')

                ## add to paragraph array
                paragraphs.append(line)
            else:
                metacheck = re.findall('^([A-Z][A-Z-]*?):', line)
                if len(metacheck) > 0:
                    if metacheck[0] in meta_list:
                       meta_dict[metacheck[0]] = line.replace(metacheck[0] + ': ','')  

        ## put everything in the metadata dictionary
        meta_dict['PUBLICATION'] = pub
        meta_dict['DATE']        = date
        meta_dict['TITLE']       = title
        meta_dict['EDITION']     = ed

        ## since JSON won't preserve escaped newlines
        meta_dict['TEXT']        = "<br/>".join(paragraphs)
        meta_dict['INTERNAL_ID'] = "%s_%s_%s" % (pub, date, ids[i])

        articles.append(meta_dict)

    return articles

if __name == '__main__':
    ## TK: add command-line args
    parseLexisNexis()

