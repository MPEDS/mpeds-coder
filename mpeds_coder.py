# -*- coding: utf-8 -*-
"""
    MPEDS Annotation Interface
    ~~~~~~

    Alex Hanna
    @alexhanna
    alex.hanna@gmail.com
"""

## base
import csv
import json
import math
import os
import re
import smtplib
import string
import sys
import urllib
import datetime as dt
import time
from math import ceil
from random import sample
from random import choice
import yaml

if (sys.version_info < (3, 0)):
    import urllib2
else:
    import urllib.request

## pandas
import pandas as pd
import numpy as np

## lxml, time
from lxml import etree
from pytz import timezone
import pytz

## flask
from flask import Flask, request, session, g, redirect, url_for, abort, make_response, render_template, flash, jsonify, Response, stream_with_context
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

## article assignment library
import assign_lib

## db
from sqlalchemy.exc import OperationalError
from sqlalchemy import func, desc, distinct, or_, text
from sqlalchemy.sql import select
from sqlalchemy.schema import Table
from sqlite3 import dbapi2 as sqlite3

## app-specific
from database import db_session
from models import ArticleMetadata, ArticleQueue, CodeFirstPass, CodeSecondPass, CodeEventCreator, \
    Event, EventCreatorQueue, SecondPassQueue, User

# create our application
app = Flask(__name__)
app.config.from_pyfile('config.py')

## login stuff
lm  = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

## retrieve central time
central = timezone('US/Central')

## open-ended vars
v2 = [
    ('loc',    'Location'),
    ('time',   'Timing and Duration'),
    ('size',   'Size'),
    ('orgs',   'Organizations')
]

## informational vars
v3 = [
    ('actor',  'Protest actors'),
    ('police', 'Police/protester interactions'),
    ('counter','Counter protests'),
    ('viol',   'Violence')
]

event_creator_vars = []

## if there's the yaml text selects
if os.path.isfile(app.config['WD'] + '/text-selects.yaml'):
    ecs = yaml.load(open(app.config['WD'] + '/text-selects.yaml', 'r'))
    event_creator_vars = [(x, ecs[x]) for x in sorted(ecs.keys())]
elif os.path.isfile(app.config['WD'] + '/text-selects.csv'):
    for var in open(app.config['WD'] + '/text-selects.csv', 'r').read().split('\n'):
        var = var.strip()
        if var:
            key  = '-'.join(re.split('[ /]', var.lower()))
            key += '-text'
            event_creator_vars.append( (key, var) )

## load preset variables
preset_vars = yaml.load(open(app.config['WD'] + '/presets.yaml', 'r'))
v1 = [(x, str.title(x).replace('-', ' ')) for x in sorted(preset_vars.keys())]

## multiple variable keys
multi_vars_keys = v1[:] 
multi_vars_keys.extend(event_creator_vars[:])
multi_vars_keys = [x[0] for x in multi_vars_keys]

## pass one variables
vars = v1[:]
vars.extend(v2[:])
vars.extend(v3[:])

## single value variables for first-pass coding
sv = ['comments', 'protest', 'multi', 'nous', 'ignore']

## yaml for yes/no variables
yes_no_vars = yaml.load(open(app.config['WD'] + '/yes-no.yaml', 'r'))

## mark the single-valued items
event_creator_single_value = ['article-desc', 'desc', 'start-date', 'end-date', 
    'location', 'duration', 'date-est']

event_creator_single_value.extend([[x[0] for x in v] for k, v in yes_no_vars.iteritems()])

## metadata for Solr
meta_solr = ['PUBLICATION', 'SECTION', 'BYLINE', 'DATELINE', 'DATE', 'INTERNAL_ID']

#####
##### Helper functions
#####

##### load text from Solr database
def loadSolr(solr_id):
    solr_id    = urllib.quote(solr_id)
    url        = '%s/select?q=id:"%s"&wt=json' % (app.config['SOLR_ADDR'], solr_id)
    not_found  = (0, [], [])
    no_connect = (-1, [], [])

    try:
        if (sys.version_info < (3, 0)):
            ## Python 2
            req  = urllib2.Request(url)
            res  = urllib2.urlopen(req)
        else:
            ## Python 3
            res = urllib.request.urlopen(url)
    except:
        return no_connect
    res = json.loads(res.read())
    if res['responseHeader']['status'] != 0:
        return not_found

    if len(res['response']['docs']) != 1:
        return not_found

    doc = res['response']['docs'][0]

    ## sometimes no text is available with AGW
    if 'TEXT' not in doc:
        return (-2, [], [])

    paras = doc['TEXT'].split('<br/>')
    meta  = []
    for k in meta_solr:
        if k in doc:
            if k == 'DATE':
                meta.append(doc[k][0].split('T')[0])
            else:
                meta.append(doc[k])

    if 'TITLE' in doc:
        title = doc['TITLE']
    else:
        title = paras[0]
        del paras[0]

    return title, meta, paras

## prep any article for display
def prepText(article):
    fn    = article.filename
    db_id = article.db_id

    metawords = ['DATE', 'PUBLICATION', 'LANGUAGE', 'DATELINE', 'SECTION',
    'EDITION', 'LENGTH', 'DATE', 'SEARCH_ID', 'Published', 'By', 'AP', 'UPI']

    text  = ''
    html  = ''
    title = ''
    meta  = []
    paras = []
    path  = app.config['DOC_ROOT'] + fn

    filename = str('INTERNAL_ID: %s' % fn)

    if app.config['SOLR'] == True:
        title, meta, paras = loadSolr(db_id)
        if title == 0:
            title = "Cannot find article in Solr."
        elif title == -1:
            title = "Cannot connect to Solr."
        elif title == -2:
            title = "No text. Skip article."
    elif re.match(r"^.+txt$", fn):
        i     = 0
        title = ''
        pLine = ''

        f = open(path, 'r')

        for line in f:
            line  = line.strip()
            words = line.split()

            ## remove colon from first word in the line
            if len(words) > 0:
                words[0] = words[0].replace(":", '')

            if False:
                pass
            elif line == '':
                pass
            elif i == 0:
                ## first line is title
                if words[0] == 'TITLE':
                    line = " ".join(words[1:])

                title = line
            elif pLine != '' and words[0] in metawords:
                meta.append(line)
            else:
                ## add to html
                paras.append(line)

            i += 1
            pLine = line

        ## append filename info
        meta.append(filename)
    elif re.match(r"^.+xml$", fn):
        ## this format only works for LDC XML files
        tree     = etree.parse(open(path, "r"))
        headline = tree.xpath("/nitf/body[1]/body.head/hedline/hl1")
        paras    = tree.xpath("/nitf/body/body.content/block[@class='full_text']/p")
        lead     = tree.xpath("/nitf/body/body.content/block[@class='lead_paragraph']/p")
        byline   = tree.xpath("/nitf/body/body.head/byline[@class='print_byline']")
        dateline = tree.xpath("/nitf/body/body.head/dateline")

        if len(byline):
            meta.append(byline[0].text)

        if len(dateline):
            meta.append(dateline[0].text)

        meta.append(filename)

        title = headline[0].text
        paras = [x.text for x in paras]

    ## get rid of lead if it says the same thing
    if len(paras) > 0:
        p0 = paras[0]
        p0 = p0.replace("LEAD: ", "")
        if len(paras) > 1:
            if p0 == paras[1]:
                del paras[0]

    ## remove HTML from every paragraph
    paras = [re.sub(r'<[^>]*>', '', x) for x in paras]
             
    ## paste together paragraphs, give them an ID
    all_paras = ""
    for i, text in enumerate(paras):
        all_paras += "<p id='%d'>%s</p>\n" % (i, text)
    all_paras = all_paras.strip()

    html  = "<h4>%s</h4>\n" % title
    html += "<p class='meta' id='meta'>%s</p>\n" % " | ".join(map(lambda x: "%s" % x, meta)).strip()
    html += "<div class='bodytext' id='bodytext'>\n%s\n</div>" % all_paras

    ## plain-text
    text = "\n".join(paras)

    text = text.encode("utf-8")
    html = html.encode("utf-8")

    return text, html

def validate( x ):
    """ replace newlines, returns, and tabs with blank space """
    if x:
        if type(x) == unicode:
            x = string.replace(x, "\n", " ")
            x = string.replace(x, "\r", " ")
            x = string.replace(x, "\t", " ")
            return x.encode('utf-8')
        else:
            return str(x)
    else:
        return "0"

def convertIDToPublication(db_id, db_name):
    """ Takes a Solr ID and spits out the publication"""

    if 'AGW' in db_id:
        ## AGW-XXX-ENG_YYYYMMDD.NNNN
        r = db_id.split("_")[1]
    elif 'NYT' in db_id:
        r = 'NYT'
    else:
        r = db_id.split("_")[0]

        ## replace - with space
        r = r.replace('-', ' ')

        ## add (87-95) to WaPo and USATODAY
        if 'LN' in db_name:
            r += " (87-95)"

    return r

## truncating text for summary
@app.template_filter('summarizeText')
def summarizeText(s):
    if len(s) > 15:
        n = s[0:8] + "..." + s[-5:]
        return n
    return s


@app.template_filter('datetime')
def format_datetime(value):
    if value:
        return dt.datetime.strftime(value, "%Y-%m-%d %H:%M:%S")
    return ''


@app.template_filter('nonestr')
def nonestr(s):
    if s is not None:
        return s
    return ''


## java string hashcode
## copy-pasta from http://garage.pimentech.net/libcommonPython_src_python_libcommon_javastringhashcode/
## make it a Jinja2 filter for template ease
@app.template_filter('hashcode')
def hashcode(s):
    h = 0
    for c in s:
        h = (31 * h + ord(c)) & 0xFFFFFFFF
    a = ((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000

    return int(math.fabs(a))

#####
##### App setup
#####

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

### auth stuff
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")

    username = request.form['username']
    password = request.form['password']
    reg_user = User.query.filter_by(username=username, password=password).first()
    if reg_user is None:
        flash("Username or password is invalid. Please try again.", "error")
        return redirect(url_for('login'))

    login_user(reg_user)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

## views
@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template("index.html")

#####
##### Coding pages
#####

@app.route('/code1')
@login_required
def code1Next():
    now     = dt.datetime.now(tz = central).replace(tzinfo = None)
    article = None

    while article == None:
        ## get next article in this user's queue
        next    = db_session.query(ArticleQueue).filter_by(coder_id = current_user.id, coded_dt = None).first()

        ## out of articles, return null page
        if next is None:
            return render_template("null.html")

        article = db_session.query(ArticleMetadata).filter_by(id = next.article_id).first()

        ## this is a weird error and shouldn't happen but here we are.
        if article is None:
            next.coded_dt = now
            db_session.add(next)
            db_session.commit()

    return redirect(url_for('code1', aid = next.article_id))


@app.route('/code1/<aid>')
@login_required
def code1(aid):
    article    = db_session.query(ArticleMetadata).filter_by(id = aid).first()
    text, html = prepText(article)

    aq = db_session.query(ArticleQueue).filter_by(coder_id = current_user.id, article_id = aid).first()

    return render_template("code1.html", vars = vars, aid = aid, text = html.decode('utf-8'))


@app.route('/code2')
@login_required
def code2Next():
    if current_user.authlevel < 2:
        return redirect(url_for('index'))

    nextArticle = db_session.query(SecondPassQueue).filter_by(coder_id = current_user.id, coded_dt = None).first()

    if nextArticle:
        return redirect(url_for('code2', aid = nextArticle.article_id))
    else:
        return render_template("null.html")


@app.route('/code2/<aid>')
@login_required
def code2(aid):
    if current_user.authlevel < 2:
        return redirect(url_for('index'))

    aid       = int(aid)
    cfp_order = ['protest', 'multi', 'nous']
    cfp_dict  = {cfp_name: {} for cfp_name in cfp_order}
    cfp_ex    = ['load', 'ignore']
    sv_order  = ['yes', 'no', 'maybe', 'ignore']
    comments  = []
    opts      = {}
    curr      = {}

    ## initialize the dictionary
    for v in vars:
        cfp_dict[v[0]] = 0

    ## gather coders which have coded this article
    ## and get single-valued items
    cfps           = db_session.query(CodeFirstPass).filter(CodeFirstPass.article_id == aid).all()
    coders_protest = [(x[1].username, x[0].value) for x in db_session.query(CodeFirstPass, User).join(User).\
        filter(CodeFirstPass.article_id == aid, CodeFirstPass.variable == 'protest').all()]
    yes_coders     = db_session.query(CodeFirstPass).\
        filter(CodeFirstPass.article_id == aid, CodeFirstPass.variable == 'protest', CodeFirstPass.value.in_(['yes', 'maybe'])).count()

    ## load the single-value variables
    for cfp in cfps:
        if cfp.variable in cfp_ex:
            continue
        elif cfp.variable == 'comments':
            comments.append(cfp.value)
        elif cfp.variable == 'ignore':
            ## assign ignore to protest
            if 'ignore' not in cfp_dict['protest']:
                cfp_dict['protest']['ignore'] = 0

            cfp_dict['protest']['ignore'] += 1
        elif cfp.variable in cfp_order:
            ## if in the dichotomous variables, sum values
            if cfp.value not in cfp_dict[cfp.variable]:
                cfp_dict[cfp.variable][cfp.value] = 0

            cfp_dict[cfp.variable][cfp.value] += 1
        else:
            ## else, just mark existence
            cfp_dict[cfp.variable] += 1

    article    = db_session.query(ArticleMetadata).filter_by(id = aid).first()
    text, html = prepText(article)

    return render_template(
        "code2.html",
        vars       = vars,
        aid        = aid,
        cfp_dict   = cfp_dict,
        cfp_order  = cfp_order,
        sv_order   = sv_order,
        comments   = comments,
        opts       = opts,
        curr       = curr,
        coders_p   = coders_protest,
        num_coders = len(coders_protest),
        yes_coders = float(yes_coders),
        text       = html.decode('utf-8'))


@app.route('/event_creator')
@login_required
def ecNext():
    nextArticle = db_session.query(EventCreatorQueue).filter_by(coder_id = current_user.id, coded_dt = None).first()

    if nextArticle:
        return redirect(url_for('eventCreator', aid = nextArticle.article_id))
    else:
        return render_template("null.html")


@app.route('/event_creator/<aid>')
@login_required
def eventCreator(aid):
    aid        = int(aid)
    article    = db_session.query(ArticleMetadata).filter_by(id = aid).first()
    text, html = prepText(article)

    return render_template("event-creator.html", aid = aid, text = html.decode('utf-8'))


class Pagination(object):
    """
    Extracted from flask-sqlalchemy
    Internal helper class returned by :meth:`BaseQuery.paginate`.  You
    can also construct it from any other SQLAlchemy query object if you are
    working with other libraries.  Additionally it is possible to pass `None`
    as query object in which case the :meth:`prev` and :meth:`next` will
    no longer work.
    """

    def __init__(self, query, page, per_page, total, items):
        #: the unlimited query object that was used to create this
        #: pagination object.
        self.query = query
        #: the current page number (1 indexed)
        self.page = page
        #: the number of items to be displayed on a page.
        self.per_page = per_page
        #: the total number of items matching the query
        self.total = total
        #: the items for the current page
        self.items = items

    @property
    def pages(self):
        """The total number of pages"""
        if self.per_page == 0:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page."""
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return paginate(self.query, self.page - 1, self.per_page, error_out)

    @property
    def prev_num(self):
        """Number of the previous page."""
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self, error_out=False):
        """Returns a :class:`Pagination` object for the next page."""
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return paginate(self.query, self.page + 1, self.per_page, error_out)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        """Iterates over the page numbers in the pagination.  The four
        parameters control the thresholds how many numbers should be produced
        from the sides.  Skipped page numbers are represented as `None`.
        This is how you could render such a pagination in the templates:
        .. sourcecode:: html+jinja
            {% macro render_pagination(pagination, endpoint) %}
              <div class=pagination>
              {%- for page in pagination.iter_pages() %}
                {% if page %}
                  {% if page != pagination.page %}
                    <a href="{{ url_for(endpoint, page=page) }}">{{ page }}</a>
                  {% else %}
                    <strong>{{ page }}</strong>
                  {% endif %}
                {% else %}
                  <span class=ellipsis>…</span>
                {% endif %}
              {%- endfor %}
              </div>
            {% endmacro %}
        """
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

def paginate(query, page, per_page=20, error_out=True):
    """
    Modified from the flask-sqlalchemy to support paging for
    the original version of the sqlalchemy that not use BaseQuery.
    """
    if page < 1 and error_out:
        abort(404)

    items = query.limit(per_page).offset((page - 1) * per_page).all()
    if not items and page != 1 and error_out:
        abort(404)

    # No need to count if we're on the first page and there are fewer
    # items than we expected.
    if page == 1 and len(items) < per_page:
        total = len(items)
    else:
        total = query.order_by(None).count()

    return Pagination(query, page, per_page, total, items)

def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)

app.jinja_env.globals['url_for_other_page'] = url_for_other_page

@app.route('/code2queue/<sort>/<sort_dir>')
@app.route('/code2queue/<sort>/<sort_dir>/<int:page>')
@login_required
def code2queue(sort, sort_dir, page = 1):
    if current_user.authlevel < 2:
        return redirect(url_for('index'))

    ## get existing queue items to note which ones are coded
    spqs = {spq.article_id: 1 for spq in db_session.query(SecondPassQueue).filter(SecondPassQueue.coded_dt != None).all()}

    ## get coding info
    cfp_dict  = {}
    cfp_order = []

    pagination = paginate(db_session.query(CodeFirstPass, ArticleMetadata)
                            .join(ArticleMetadata)
                            .filter(CodeFirstPass.variable == 'protest'),
                            page, 10000, True)
    for cfp, am in pagination.items:
        pub = ''
        if 'AGW' in am.db_id:
            pub = "-".join(am.db_id.split("_")[0:2])
        elif 'NYT' in am.db_id:
            pub = 'NYT'
        else:
            pub = am.db_id.split("_")[0]

        if cfp.article_id not in cfp_dict:
            cfp_dict[cfp.article_id] = {"coder_value": [], "pub": pub, "percent_yes": 0, "percent_maybe": 0, "percent_no": 0}

        ## set css class
        cfp_dict[cfp.article_id]["coder_value"].append( (cfp.coder_id, cfp.value) )
        cfp_order.append(cfp.article_id)

    ## add metadata and delete all nos
    for article_id, v in cfp_dict.items():
        to_del = True
        for coder, decision in v["coder_value"]:
            ## not sure why this would be null, but it is
            if not decision:
                continue

            ## filter out articles in which all users said no
            if decision == "yes" or decision == "maybe":
                to_del = False

            ## add to percent
            cfp_dict[article_id]["percent_" + decision] += 1.

        ## divide all
        for decision in ['yes', 'no', 'maybe']:
            cfp_dict[article_id]["percent_" + decision] /= len(cfp_dict[article_id]["coder_value"])

        ## inefficient way to do listwise delete but ¯\_(ツ)_/¯
        if to_del:
            del cfp_dict[article_id]
            cfp_order.remove(article_id)

    ## sort by different variables
    if sort == 'coder_value':
        cfp_order = [x[0] for x in sorted(cfp_dict.items(), key = lambda x: len(x[1][sort]), reverse = True if sort_dir == 'desc' else False)]
    else:
        cfp_order = [x[0] for x in sorted(cfp_dict.items(), key = lambda x: x[1][sort], reverse = True if sort_dir == 'desc' else False)]

    return render_template(
        "code2queue.html",
        cfp_dict  = cfp_dict,
        cfp_order = cfp_order,
        spqs = spqs,
        pagination = pagination)

#####
##### Coder stats
#####

@login_required
def _pubCount():
    """
        Determine yes/maybe, total coded, in for each publication

        I hate everything and am just going to do this in pandas
        get all the articles in the database.
        TK: One day, convert this to a pure sqlalchemy solution.
    """

    df_am = pd.DataFrame([(x.id, x.db_name, x.db_id)  for x in db_session.query(ArticleMetadata).all()],\
        columns = ['article_id', 'db_name', 'db_id'])
    df_am = df_am.set_index('article_id')

    ## get all the articles in the queue
    df_aq = pd.DataFrame([(x.article_id, x.coded_dt) for x in db_session.query(ArticleQueue).all()],\
        columns = ['article_id', 'coded_dt'])

    ## note that they're in the queue
    df_aq['in_queue'] = 1
    df_aq = df_aq.set_index('article_id')

    ## note all of those which have protest values
    df_cfp = pd.DataFrame([(x.article_id, x.value) for x in db_session.query(CodeFirstPass).filter(CodeFirstPass.variable == 'protest').all()],\
        columns = ['article_id', 'protest_value'])
    df_cfp = df_cfp.set_index('article_id')

    ## do an outer join of all of the tables
    df_all = df_am.join(df_aq).join(df_cfp)

    ## fill NA with 0 for convenience
    df_all = df_all.fillna(0)

    ## Retrieve publication name
    df_all['publication'] = df_all.apply(lambda x: convertIDToPublication(x['db_id'], x['db_name']), axis = 1)

    ## calculate various counts per publication
    ## 1. Number of unique articles which have been labeled yes/maybe
    ## 2. Total number of articles coded
    ## 3. Articles remaining in user queues
    ## 4. Remaining number of articles which are in the database but aren't in a queue/haven't been coded
    gr        = df_all.groupby(['publication'])
    total     = {'yes_maybe': 0, 'coded': 0, 'in_queue': 0, 'in_db': 0}
    pub_total = []
    for publication, group in gr:

        ## weird bug here
        if publication == 'id':
            continue

        ## skip DoCA
        if publication == 'NYT':
            group = group[(group.db_name != 'DoCA') & (group.db_name != 'LDC')]

        yes_maybe = group[(group.protest_value == 'yes') | (group.protest_value == 'maybe')].db_id.nunique()
        coded     = group[group.coded_dt == group.coded_dt].db_id.nunique()
        in_queue  = group[(group.in_queue == 1) & (group.coded_dt != group.coded_dt)].db_id.nunique()
        in_db     = group[group.in_queue != 1].db_id.nunique()

        pub_total.append( (publication, yes_maybe, coded, in_queue, in_db ) )

        total['yes_maybe'] += yes_maybe
        total['coded']     += coded
        total['in_queue']  += in_queue
        total['in_db']     += in_db

    ## Generate total
    pub_total.append( ('Total', total['yes_maybe'], total['coded'], total['in_queue'], total['in_db']) )
    return pub_total


@login_required
def _codedOnce():
    """ Count all articles which have only been coded once, by coder. """

    ## get all coded articles
    df_cq = pd.DataFrame([(x[0].article_id, x[1].username) \
        for x in db_session.query(ArticleQueue, User).join(User).filter(ArticleQueue.coded_dt != None).all()],\
        columns = ['article_id', 'coder_id'])

    ## count number of times article has been coded
    gr = df_cq.groupby('article_id').agg(np.count_nonzero)
    gr.columns = ['count']

    ## get all those articles only coded once
    df_us = df_cq[df_cq.article_id.isin(gr[gr['count'] == 1].index)].copy()
    gr    = df_us.groupby('coder_id').agg(np.count_nonzero).reset_index()

    ## make tuple of counts, add total
    coded_once = [tuple(x) for x in gr.values]
    coded_once.append( ('total', np.sum(gr['article_id'])) )

    return coded_once


@app.route('/admin')
@login_required
def admin():
    if current_user.authlevel < 3:
        return redirect(url_for('index'))

    ura   = {u.id: u.username for u in db_session.query(User).filter(User.authlevel == 1).all()}
    coded = {user: {} for user in ura.keys()}
    dbs   = [x[0] for x in db_session.query(ArticleMetadata.db_name).distinct()]
    pubs  = []

    ## get the available publications
    if app.config['SOLR']:
        url = '{}/select?q=Database:"University%20Wire"&rows=0&wt=json'.format(app.config['SOLR_ADDR'])
        fparams = 'facet=true&facet.field=PUBLICATION&facet.limit=1000'

        if (sys.version_info < (3, 0)):
            ## Python 2
            import urllib2
            req  = urllib2.Request(url + '&' + fparams)
            res  = urllib2.urlopen(req)
        else:
            ## Python 3
            res = urllib.request.urlopen(url + '&' + fparams)

        jobj = json.loads(res.read())

        ## get every other entry in this list
        pubs = sorted(jobj['facet_counts']['facet_fields']['PUBLICATION'][0::2])

    ## get user stats for EC
    for count, user in db_session.query(func.count(EventCreatorQueue.id), User.id).\
        join(User).group_by(User.id).filter(EventCreatorQueue.coded_dt == None, User.id.in_(ura.keys())).all():
        coded[user]['remaining'] = count

    for count, user in db_session.query(func.count(EventCreatorQueue.id), User.id).\
        join(User).group_by(User.id).filter(EventCreatorQueue.coded_dt != None, User.id.in_(ura.keys())).all():
        coded[user]['completed'] = count

    ## get number of unassigned articles
    ## TK: Eventually generate this count for publications
    unassigned = []
    #all_metadata = db_session.query(ArticleMetadata).all()
    #assigned_metadata = db_session.query(EventCreatorQueue).all()

    for db in dbs:
        unassigned.append( (db, len( set([x.id for x in db_session.query(ArticleMetadata).filter_by(db_name = db).all()]) - \
        set([x[0] for x in db_session.query(distinct(EventCreatorQueue.article_id)).all()]))) )

    return render_template(
        "admin.html",
        coded      = coded,
        ura        = ura,
        dbs        = dbs,
        unassigned = unassigned,
        pubs       = pubs
    )


@app.route('/coderstats')
@login_required
def coderStats():
    ## get last week datetime
    last_week  = dt.datetime.now(tz = central) - dt.timedelta(weeks=1)
    pub_total  = []
    coded_once = None
    pub_total  = None
    passes     = ['1', '2', 'ec']
    stats      = ['completed', 'lw', 'remaining', 'dt']
    models     = [ArticleQueue, SecondPassQueue, EventCreatorQueue]
    if current_user.authlevel < 3:
        ## show own stats if not an admin
        ura = [current_user.username]
        gra = [current_user.username]

        last_cfp = None
        last_csp = None
        last_cec = None
    else:
        ## first pass coders
        ura = [u.username for u in db_session.query(User).filter(User.authlevel == 1).all()]

        ## Add stats for second pass coders
        gra = [u.username for u in db_session.query(User).filter(User.authlevel > 1).all()]

        ## get most recent DB updates
        last_cfp = db_session.query(CodeFirstPass, User).join(User).order_by(desc(CodeFirstPass.timestamp)).first()
        last_csp = db_session.query(CodeSecondPass, User).join(User).order_by(desc(CodeSecondPass.timestamp)).first()
        last_cec = db_session.query(CodeEventCreator, User).join(User).order_by(desc(CodeEventCreator.timestamp)).first()

    ## initialize user list
    coded = {user: {s: {p: None for p in passes} for s in stats} for user in ura[:] + gra[:]}

    ## get total articles coded
    for i in range(len(passes)):
        pn = passes[i]
        for count, user in db_session.query(func.count(models[i].id), User.username).\
            join(User).group_by(User.username).filter(models[i].coded_dt != None, User.username.in_(ura)).all():
            coded[user]['completed'][pn] = count

        for count, user in db_session.query(func.count(models[i].id), User.username).\
            join(User).group_by(User.username).filter(models[i].coded_dt > last_week, User.username.in_(ura)).all():
            coded[user]['lw'][pn] = count

        ## remaining articles in queue
        for count, user in db_session.query(func.count(models[i].id), User.username).\
            join(User).group_by(User.username).filter(models[i].coded_dt == None, User.username.in_(ura)).all():
            coded[user]['remaining'][pn] = count

        ## get the last time coded
        for timestamp, user in db_session.query(func.max(models[i].coded_dt), User.username).\
            join(User).group_by(models[i].coder_id).filter(models[i].coded_dt != None, User.username.in_(ura)).all():
            coded[user]['dt'][pn] = timestamp

    ## comment this out to save on a lot of load time for this page.
    if current_user.authlevel > 2:
        ## generate the publication statistics
        #pub_total = _pubCount()

        ## get the coded once counts
        #coded_once = _codedOnce()
        pass

    return render_template(
        "coder_stats.html",
        coded      = coded,
        pub_total  = pub_total,
        last_cfp   = last_cfp,
        last_csp   = last_csp,
        last_cec   = last_cec,
        pn         = 'ec',
        pass_title = 'Event Creator Status',
        ura        = ura,
        gra        = gra,
        coded_once = coded_once
    )

@app.route('/publications')
@app.route('/publications/<sort>')
@login_required
def publications(sort = 'tbc'):
    """
      Geenerate list of all publications and all articles remaining. 
    """
    if current_user.authlevel < 3:
        return redirect(url_for('index'))

    ## TK: Write code to sort by selected attribute
    
    query = """
    SELECT REPLACE(REPLACE(dem.publication, '-', ' '), '   ', ' - ') as publication, 
    COALESCE(num.in_queue,0) as in_queue, 
    dem.total as total,
    IF(in_queue IS NULL OR in_queue = 0, total, total - in_queue) AS to_be_coded 
    FROM
    (
    SELECT SUBSTRING_INDEX(am.db_id, '_', 1) as publication, COUNT(*) AS in_queue
    FROM article_metadata am
    WHERE am.db_name = 'uwire' AND am.id IN (SELECT article_id FROM event_creator_queue)
    GROUP BY 1
) num RIGHT JOIN
(
    SELECT SUBSTRING_INDEX(am.db_id, '_', 1) as publication, COUNT(*) AS total
    FROM article_metadata am
    WHERE db_name = 'uwire'
    GROUP BY 1
) dem ON num.publication = dem.publication
ORDER BY to_be_coded DESC, total DESC
    """
    
    result = db_session.execute(query)
    rows = [(row[0], row[1], row[2], row[3]) for row in result]

    return render_template("publications.html", pub_list = rows)

    
@app.route('/userarticlelist/<pn>')
@app.route('/userarticlelist/<pn>/<int:page>')
@login_required
def userArticleList(pn, page = 1):
    """ View for coders to see their past articles. """
    model = None
    if pn == '1':
        model = ArticleQueue
    elif pn == '2':
        model = SecondPassQueue
    elif pn =='ec':
        model = EventCreatorQueue
    else:
        return make_response("Invalid page.", 404)

    pagination = paginate(db_session.query(model, ArticleMetadata).\
            filter(model.coder_id == current_user.id, model.coded_dt != None).\
            join(ArticleMetadata).\
            order_by(desc(model.coded_dt)), page, 10000, True)

    return render_template("list.html", 
                           pn  = pn,
                           aqs = pagination.items,
                           pagination = pagination)


@app.route('/userarticlelist/admin/<is_coded>/<coder_id>/<pn>')
@app.route('/userarticlelist/admin/<is_coded>/<coder_id>/<pn>/<int:page>')
@login_required
def userArticleListAdmin(coder_id, is_coded, pn, page = 1):
    """ View for admins to manually inspect specific coder queues. """
    if current_user.authlevel < 3:
        return redirect(url_for('index'))

    model = None
    if pn == '1':
        model = ArticleQueue
    elif pn == '2':
        model = SecondPassQueue
    elif pn =='ec':
        model = EventCreatorQueue
    else:
        return make_response("Invalid page.", 404)

    is_coded_condition = None
    if is_coded == '0':
        is_coded_condition = model.coded_dt == None
    else:
        is_coded_condition = model.coded_dt != None

    ## show articles in the order they entered the user's queue
    pagination = paginate(db_session.query(model, ArticleMetadata).\
                     filter(model.coder_id == coder_id, is_coded_condition).\
                     join(ArticleMetadata).\
                     order_by(model.id), page, 10000, True)
    username = db_session.query(User).filter(User.id == int(coder_id)).first().username

    return render_template("list.html", 
        pn  = pn,
        aqs = pagination.items,
        is_coded = is_coded,
        username = username,
        pagination = pagination)


## generate report CSV file and store locally/download
@app.route('/_generate_coder_stats')
@login_required
def generateCoderAudit():
    if current_user.authlevel < 3:
        return redirect(url_for('index'))

    pn = request.args.get('pn')
    action = request.args.get('action')

    # last_month = dt.datetime.now(tz = central) - dt.timedelta(weeks=4)
    users = {u.id: u.username for u in db_session.query(User).all()}

    if pn == '1':
        model = CodeFirstPass
    elif pn == 'ec':
        model = CodeEventCreator
    else:
        return make_response('Invalid pass number.', 500)

    to_df = []
    cols  = [x.name for x in model.__table__.columns]
    query = db_session.query(model, ArticleMetadata).join(ArticleMetadata).all()

    if len(query) <= 0:
        return

    for row in query:
        fp  = row[0]
        am  = row[1]

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
            pub_date   = pieces[3].split('.')[0]
            pub_date = dt.datetime.strptime(pub_date, '%Y%m%d').strftime('%Y-%m-%d')
        elif 'NYT' in am.db_id:
            ## e.g. 
            ## 1989/03/11/0230638.xml_LDC_NYT
            pub      = 'NYT'
            pub_date = am.db_id[0:10].replace('/', '-')
        else:
            ## e.g. 
            ## Caribbean-Today;-Miami_1996-12-31_26b696eae2887c8cf71735a33eb39771
            pieces   = am.db_id.split("_")
            pub      = pieces[0]
            pub_date = pieces[1]
        to_print += ( pub, pub_date, solr_id )
        to_df.append(to_print)

    cols.extend(['publication', 'pub_date', 'solr_id'])

    ## let the dataframe do all the heavy lifting for CSV formatting
    df = pd.DataFrame(to_df, columns = cols)

    if action == 'download':
        file_str = df.to_csv(None, encoding = 'utf-8', index = False)
        response = make_response(file_str)
        response.headers["Content-Disposition"] = "attachment; filename=coder-table.tsv"
        response.headers["mime-type"] = "text/csv"
        return response
    elif action == 'save':
        filename = '%s/coder-table_%s.csv' % (app.config['WD'], dt.datetime.now().strftime('%Y-%m-%d'))
        df.to_csv(filename, encoding = 'utf-8', index = False)
        return jsonify(result={"status": 200, "filename": filename})
    else:
        return make_response("Illegal action.", 500)

#####
##### Internal calls
#####

@app.route('/_add_code/<pn>', methods=['POST'])
@login_required
def addCode(pn):
    aid  = int(request.form['article'])
    var  = request.form['variable']
    val  = request.form['value']
    ev   = request.form['event']
    text = request.form['text']
    aqs  = []
    now  = dt.datetime.now(tz = central).replace(tzinfo = None)

    if pn == '1':
        model = CodeFirstPass

        ## store highlighted text on first pass
        if text:
            p = CodeFirstPass(aid, var, val, current_user.id, text)
        else:
            p = CodeFirstPass(aid, var, val, current_user.id)

        ## update datetime on every edit
        aq = db_session.query(ArticleQueue).filter_by(article_id = aid, coder_id = current_user.id).first()
        aq.coded_dt = now
        aqs.append(aq)
    elif pn == '2':
        model = CodeSecondPass
        p     = CodeSecondPass(aid, ev, var, val, current_user.id)

        for aq in db_session.query(SecondPassQueue).filter_by(article_id = aid, coder_id = current_user.id).all():
            aq.coded_dt = now
            aqs.append(aq)
    elif pn == 'ec':
        model = CodeEventCreator
        p     = CodeEventCreator(aid, ev, var, val, current_user.id, text)

        for aq in db_session.query(EventCreatorQueue).filter_by(article_id = aid, coder_id = current_user.id).all():
            aq.coded_dt = now
            aqs.append(aq)
    else:
        return make_response("Invalid model", 404)

    ## variables which only have one value per article
    if var in sv:
        if pn == '1':
            a = db_session.query(model).filter_by(
                article_id = aid,
                variable   = var,
                coder_id   = current_user.id
            ).all()
        else:
            ## for second pass and event coder, filter for distinct event
            a = db_session.query(model).filter_by(
                article_id = aid,
                variable   = var,
                event_id   = ev,
                coder_id   = current_user.id
            ).all()

        ## if there's more then one, delete them
        if len(a) > 0:
            for o in a:
                db_session.delete(o);

            db_session.commit()

    ## if this is a 2nd comment pass comment and it is null, skip it
    if var == 'comments' and pn == '2' and val == '':
        return jsonify(result={"status": 200})

    # try:
    db_session.add(p)
    db_session.add_all(aqs)
    db_session.commit()
    return make_response("", 200)


@app.route('/_del_event', methods=['POST'])
@login_required
def delEvent():
    """ Delete an event. """
    # if current_user.authlevel < 2:
    #     return redirect(url_for('index'))

    eid = int(request.form['event'])
    pn  = request.form['pn'];

    model = None
    if pn == '2':
        model = CodeSecondPass
    elif pn == 'ec':
        model = CodeEventCreator
    else:
        return make_response("Invalid model.", 404)

    db_session.query(model).filter_by(event_id = eid).delete()
    db_session.query(Event).filter_by(id = eid).delete()

    db_session.commit()

    return make_response("Delete succeeded.", 200)


@app.route('/_del_code/<pn>', methods=['POST'])
@login_required
def delCode(pn):
    """ Deletes a record from coding tables. """
    article  = request.form['article']
    variable = request.form['variable']
    value    = request.form['value']
    event    = request.form['event']

    if False:
        pass
    elif pn == '1':
        a = db_session.query(CodeFirstPass).filter_by(
            article_id = article,
            variable   = variable,
            value      = value,
            coder_id   = current_user.id
        ).all()
    elif pn == '2':
        a = db_session.query(CodeSecondPass).filter_by(
            article_id = article,
            variable   = variable,
            value      = value,
            event_id   = event,
            coder_id   = current_user.id
        ).all()
    elif pn == 'ec':
        a = db_session.query(CodeEventCreator).filter_by(
            article_id = article,
            variable   = variable,
            value      = value,
            event_id   = event,
            coder_id   = current_user.id
        ).all()
    else:
        return make_response("Invalid model", 404)

    if len(a) == 1:
        for o in a:
            db_session.delete(o)

        db_session.commit()

        return jsonify(result={"status": 200})
    elif len(a) > 1:
        return make_response(" Leave duplicates in so we can collect data on this bug.", 500)
    else:
        return make_response("", 404)


@app.route('/_change_code/<pn>', methods=['POST'])
@login_required
def changeCode(pn):
    """ 
        Changes a radio button by removing all prior values, adds one new one. 
        Only implemented for event creator right now.
    """
    article  = request.form['article']
    variable = request.form['variable']
    value    = request.form['value']
    event    = request.form['event']

    ## delete all prior values
    a = db_session.query(CodeEventCreator).filter_by(
        article_id = article,
        variable   = variable,
        event_id   = event,
        coder_id   = current_user.id
    ).all()

    for o in a:
        db_session.delete(o)
    db_session.commit()

    ## add new value
    ec = CodeEventCreator(article, event, variable, value, current_user.id) 

    db_session.add(ec)
    db_session.commit()

    return jsonify(result={"status": 200})


@app.route('/_mark_ec_done', methods=['POST'])
@login_required
def markECDone():
    article_id = request.form['article_id']
    coder_id   = current_user.id
    now        = dt.datetime.now(tz = central).replace(tzinfo = None)

    ## update time, commit
    ecq = db_session.query(EventCreatorQueue).filter_by(article_id = article_id, coder_id = coder_id).first()
    ecq.coded_dt = now

    db_session.add(ecq)
    db_session.commit()

    return jsonify(result={"status": 200})


@app.route('/_mark_sp_done')
@login_required
def markSPDone():
    if current_user.authlevel < 2:
        return redirect(url_for('index'))

    article_id = request.args.get('article_id')
    coder_id   = current_user.id
    now        = dt.datetime.now(tz = central).replace(tzinfo = None)

    ## update time, commit
    spq = db_session.query(SecondPassQueue).filter_by(article_id = article_id, coder_id = coder_id).first()
    spq.coded_dt = now

    db_session.add(spq)
    db_session.commit()

    return make_response("", 200)


@app.route('/_add_queue/<pn>')
@login_required
def addQueue(pn):
    if current_user.authlevel < 2:
        return redirect(url_for('index'))

    article_id = request.args.get('article_id')
    coder_id   = request.args.get('coder_id')

    ## if this doesn't exist, add it
    if not db_session.query(SecondPassQueue).filter_by(article_id = article_id, coder_id = coder_id).count():
        spq = SecondPassQueue(article_id = article_id, coder_id = coder_id)

        db_session.add(spq)
        db_session.commit()

    return jsonify(result={"status": 200})


@app.route('/_get_events')
@login_required
def getEvents():
    aid  = int(request.args.get('article_id'))
    pn   = request.args.get('pn')
    evs  = []

    model = None
    if pn == '2':
        model = CodeSecondPass
    elif pn == 'ec':
        model = CodeEventCreator
    else:
        return make_response("Not a valid model.", 404)

    ## get a summary of the existing events for this article
    for event in db_session.query(Event).filter(Event.article_id == aid).all():

        if pn == '2':
            rvar = {'loc': [], 'form': []}
        elif pn == 'ec':
            rvar = {'desc': [], 'article-desc': []}

        yes_nos = []
        ev = {}
        ev['id'] = event.id

        codes = db_session.query(model).\
            filter_by(event_id = event.id, coder_id = current_user.id).\
            order_by(model.variable).all()

        if len(codes) == 0:
            continue

        ## get the fields in rvar
        for code in codes:
            if code.variable in rvar.keys():
                ## otherwise, just use the value
                rvar[code.variable].append(code.value)
        
        if pn == '2':
            ev['repr'] = ", ".join(rvar['loc']) + '-' + ', '.join(rvar['form'])
        elif pn =='ec':
            if len(rvar['desc']) > 0 and len(rvar['desc'][0]) > 0:
                ev['repr'] = ", ".join(rvar['desc'])
            elif len(rvar['article-desc']) > 0 and len(rvar['article-desc'][0]) > 0:
                ev['repr'] = "(no event description): " + ", ".join(rvar['article-desc'])
            else:
                ev['repr'] = "(no article description)"

        evs.append(ev)

    return jsonify({'events': evs})


@app.route('/_get_codes')
@login_required
def getCodes():
    aid   = int(request.args.get('article'))
    pn    = request.args.get('pn')
    ev    = request.args.get('event')
    l_i   = 0

    model = None
    if pn == '1':
        model = CodeFirstPass
    elif pn == '2':
        model = CodeSecondPass
    elif pn == 'ec':
        model = CodeEventCreator

    ## load current values
    curr = db_session.query(model).\
           filter_by(coder_id = current_user.id, event_id = ev, article_id = aid).all()
    cd   = {}

    for c in curr:
        ## these will occur only once
        if c.variable in sv:
            cd[c.variable] = c.value
        else:
            ## if they've seen this article before, note which pass it is
            if c.variable == 'load':
                l_i = int(c.value) + 1

            if c.variable in multi_vars_keys:
                ## stash in array
                if c.variable not in cd:
                    cd[c.variable] = []

                cd[c.variable].append( (c.value, c.text) )

    ## insert row for every time they load the article
    ## to measure how much time it takes to read the article
    if pn == '1':
        load = CodeFirstPass(aid, "load", l_i, current_user.id)
        db_session.add(load)
        db_session.commit() 

    return jsonify(cd)


@app.route('/_load_event_block')
@login_required
def modifyEvents():
    # if current_user.authlevel < 2:
    #     return redirect(url_for('index'))

    eid  = request.args.get('event_id')
    aid  = int(request.args.get('article_id'))
    pn   = request.args.get('pn')
    opts = {}
    curr = {}

    model = None
    if pn == '2':
        model = CodeSecondPass
        template = 'event-block.html'
    elif pn == 'ec':
        model = CodeEventCreator
        template = 'event-creator-block.html'
    else:
        return make_response("Not a valid model.", 404)

    ## initialize drop-down options
    opts = {v[0]: [] for v in vars}

    if eid:
        eid = int(eid)
        ## get the current values
        for code in db_session.query(model).filter_by(event_id = eid, coder_id = current_user.id).all():
            if code.variable in sv or code.variable in event_creator_single_value:
                curr[code.variable] = code.value
            else:
                ## stash in array
                if code.variable not in curr:
                    curr[code.variable] = []

                ## loads the items which do not have text, which means
                ## everything but text selects
                if code.text is None:
                    curr[code.variable].append(code.value)

    else:
        ## add a new event
        ev  = Event(aid)
        db_session.add(ev)
        db_session.commit()

        eid = ev.id

    ## built-in dropdown options
    for preset_key in sorted(preset_vars.keys()):
        for preset_value in preset_vars[preset_key]:
            opts[ preset_key ].append(preset_value)

    ## None of the above for v1 variables
    if pn in ['1', '2']:
        for k,v in v2:
            ## coder 1-generated dropdown options
            for o in db_session.query(CodeFirstPass).filter_by(variable = k, article_id = aid).all():
                opts[ o.variable ].append(o.text)

            ## coder 2-generated dropdown options
            for o in db_session.query(CodeSecondPass).filter_by(variable = k, article_id = aid, coder_id = current_user.id).all():
                opts[ o.variable ].append(o.value)

    ## filter out repeated items and sort
    for k,v in opts.items():
        opts[k] = list( set( map(lambda x: x.strip(" .,"), opts[k]) ) )
        opts[k].sort()

    return render_template(template, 
            v1 = v1, 
            v2 = v2,
            vars = event_creator_vars,
            yes_no_vars = yes_no_vars,
            opts = opts, 
            curr = curr, 
            event_id = eid)


@app.route('/dynamic_form')
@login_required
def dynamic_form():
    aid = 23317
    article = db_session.query(ArticleMetadata).filter_by(id=aid).first()
    text, html = prepText(article)

    aq = db_session.query(ArticleQueue).filter_by(coder_id=current_user.id, article_id=aid).first()

    return render_template("dynamic_form.html", vars=vars, aid=aid, text=html.decode('utf-8'))


@app.route('/form_template_management')
@login_required
def form_template_management():
    return render_template("form_template_manager.html")


@app.route('/_highlight_var')
@login_required
def highlightVar():
    """
    Highlights first-pass coding. 
    Adds intensity for text selected multiple times.

    Algorithm:
    For each first-pass entry
        Store every boundary (both start and end) in a hashtable with a list.
    For each paragraph:
        state <- 0
        Sort boundaries
        For each boundary:
            For each item in the boundary list:
                if item == start
                    state <- state + 1
                else item == end
                    state <- state - 1

            if this is the last boundary
                use closing span
            if this boundary has a start and isn't the first item, or has an end
                use closing span
            else
                use opening span

            add the tag to the existing text

    add edited paragraph to paragraph list

    """
    if current_user.authlevel < 2:
        return redirect(url_for('index'))

    aid       = int(request.args.get('article'))
    var       = request.args.get('variable')
    body,html = prepText(db_session.query(ArticleMetadata).filter_by(id = aid).first())
    text_para = body.strip().split("\n")
    paras     = {}
    bounds    = {}
    r_paras   = {}
    r_meta    = {}
    meta      = html.strip().split("\n")[1]\
        .replace("<p class='meta' id='meta'>", "")\
        .replace("</p>", "")

    ## initialize
    for p_key in range(0, len(text_para)):
        p_str = str(p_key)
        bounds[p_str] = {}
        paras[p_str]  = text_para[p_key]

    paras['meta']  = meta
    bounds['meta'] = {}

    ## collect all the start and ends
    cfps = db_session.query(CodeFirstPass).filter_by(article_id = aid, variable = var).order_by('value').all()
    for cfp in cfps:
        ## trash the existing numbers, use find
        p    = cfp.value.split("-")[0]
        text = cfp.text

        ## find the first instance of the text
        ## mark as the start
        start = paras[p].find(text.encode('utf-8'))

        ## um this should happen but okay
        if start == -1:
            continue

        ## mark the end as the start plus the offset
        end   = start + len(text)

        ## add a list to the index
        ## and the type of bound it is
        if start not in bounds[p]:
            bounds[p][start] = []
        bounds[p][start].append('start')

        ## and vice versa with the end
        if end not in bounds[p]:
            bounds[p][end] = []
        bounds[p][end].append('end')

    ## based on the depth of highlighting, mark with the correct class
    for p_key, para in paras.items():
        state  = 0
        last_i = 0
        r_para = ""

        keys = bounds[p_key].keys()
        if len(keys) > 0:
            ## sort so we can go in order
            keys = sorted(keys)
        else:
            ## no highlights
            r_para = para

        for bound_index in keys:
            st_tag = ""
            en_tag = ""

            ## treat this like a state machine: if we are entering a highlight, increment the class
            ## if we are exiting a highlight, decrement it
            (has_start, has_end) = (False, False)
            for type_bound in bounds[p_key][bound_index]:
                if type_bound == 'start':
                    state += 1
                    has_start = True
                elif type_bound == 'end':
                    state -= 1
                    has_end = True

            tag = ""
            if bound_index == keys[-1]:
                en_tag = "</span>"
            else:
                if has_end:
                    en_tag = "</span>"
                if has_start:
                    if last_i != 0:
                        en_tag = "</span>"
                st_tag = "<span class='hl-%d'>" % state

            tag = en_tag + st_tag

            ## add the tag to the existing text
            r_para += para[last_i:bound_index] + tag

            ## if this is the last key, add the rest of the paragraph
            if bound_index == keys[-1]:
                r_para += para[bound_index:]

            last_i = bound_index

        ## add to the return array
        r_paras[p_key] = r_para

    r_body = ""
    for p_key in range(0, len(text_para)):
        p_key = str(p_key)
        r_body += "<p id='%s'>%s</p>\n" % (p_key, r_paras[p_key])

    return jsonify(result={"status": 200, "meta": r_paras['meta'], "body": r_body})


#####
##### ADMIN TOOLS
#####

@app.route('/_add_user', methods=['POST'])
@login_required
def addUser():
    if current_user.authlevel < 3:
        return redirect(url_for('index'))

    username = request.form['username']

    ## validate
    if not re.match(r'[A-Za-z0-9_]+', username):
        return make_response('Invalid username. Use only letters, numbers, and underscores.', 500)

    exists = db_session.query(User).filter_by(username = username).first()
    if exists:
        return make_response('Username exists. Choose another.', 500)

    ## generate password
    chars    = string.ascii_letters + string.digits
    length   = 8
    password = ''.join([choice(chars) for i in range(length)])

    db_session.add(User(username = username, password = password, authlevel = 1))
    db_session.commit()

    ## TK: Send email to admin to have notice of new account

    return jsonify(result={"status": 200, "password": password})


@app.route('/_assign_articles')
@login_required
def assignArticles():
    if current_user.authlevel < 3:
        return redirect(url_for('index'))

    num     = request.args.get('num')
    db_name = request.args.get('db')
    pub     = request.args.get('pub')
    ids     = request.args.get('ids')
    users   = request.args.get('users')
    same    = request.args.get('same')
    group_size = request.args.get('group_size')
    
    ## input validations
    if num == '' and ids == '':
        return make_response('Please enter a valid number of articles or a list of IDs.', 500)
    if num != '' and ids != '':
        return make_response('You can either enter a number of articles or a list of IDs, but not both.', 500)
    if db_name == '' and pub == '' and ids == '':
        return make_response('Please select a valid database or publication, or enter a list of IDs.', 500)
    if db_name != '' and pub != '':
        return make_response('You can only choose a database or publication, but not both.', 500)
    if same is None and group_size == '':
        return make_response('Please select a "same" or "different" option, or enter a group size number.', 500)
    if same is not None and group_size != '':
        return make_response('You can only choose same/different or a group size. Force reload the page to reset same/different.', 500)
    if num != '':
        try:
            num = int(num)
        except:
            return make_response('Please enter a valid number of articles.', 500)

        ## get number of unassigned articles
        if pub:
            pub = "-".join(pub.split())
            full_set = set([x.id for x in db_session.query(ArticleMetadata).\
                            filter(ArticleMetadata.db_id.like('%s%%' % pub)).all()])
        else:
            full_set = set([x.id for x in db_session.query(ArticleMetadata).\
                            filter_by(db_name = db_name).all()])

        assigned   = set([x[0] for x in db_session.query(distinct(EventCreatorQueue.article_id)).all()])
        unassigned = len( full_set - assigned )

        if num > unassigned:
            return make_response('Select a number less than or equal to number of unassigned articles.', 500)

    if users == '':
        return make_response('Please select some users.', 500)

    user_ids = map(lambda x: int(x), users.split(','))

    if group_size != '':
        try:
            group_size = int(group_size)
        except:
            return make_response('Please enter a valid group size.', 500)

        if len(user_ids) <= group_size:
            return make_response('Number of users must be greater than k.', 500)

    n_added = 0
    ## assign a number of articles
    if ids == '':
        ## assign by individual
        if group_size == '':
            if same == 'same':
                ## assign by database
                if db_name:
                    articles = assign_lib.generateSample(num, db_name, 'ec')
                else:
                    ## assign by publication
                    articles = assign_lib.generateSample(num, None, 'ec', pub)

                n_added = assign_lib.assignmentToCoders(articles, user_ids, 'ec')
            elif same == 'different':
                for u in user_ids:
                    if db_name:
                        articles = assign_lib.generateSample(num, db_name, 'ec')
                    else:
                        articles = assign_lib.generateSample(num, None, 'ec', pub)
                    n_added  += assign_lib.assignmentToCoders(articles, [u], 'ec')
        else:
            ## assignment by bin
            bins       = assign_lib.createBins(user_ids, group_size)
            num_sample = assign_lib.generateSampleNumberForBins(num, len(user_ids), group_size)
            if db_name:
                articles = assign_lib.generateSample(num_sample, db_name, pass_number = 'ec')
            else: 
                articles = assign_lib.generateSample(num, None, 'ec', pub)
            assign_lib.assignmentToBin(articles, bins, pass_number = 'ec')
            n_added = len(articles)
    else: 
        ## assignment by ID
        if group_size:
            ## can't assign by ID because of the factorial math
            return make_response('Cannot assign articles by ID with bins.', 500)

        ids = map(lambda x: int(x), ids.strip().split('\n'))
        if same == 'same':
            n_added = assign_lib.assignmentToCoders(ids, user_ids, 'ec')
        elif same == 'different':
            return make_response('Can only assign the same articles by ID.', 500)

    return make_response('%d articles assigned successfully.' % n_added, 200)


@app.route('/_transfer_articles')
@login_required
def transferArticles():
    if current_user.authlevel < 3:
        return redirect(url_for('index'))

    num        = request.args.get('num')
    from_users = request.args.get('from_users')
    to_users   = request.args.get('to_users')

    try:
        num = int(num)
    except:
        return make_response('Please enter a valid number.', 500)
   
    from_users = map(lambda x: int(x), from_users.split(','))
    to_users = map(lambda x: int(x), to_users.split(','))

    n = assign_lib.transferCoderToCoder(from_users, to_users, 'ec', num)

    return make_response('%d articles transferred successfully.' % n, 200)


@app.route('/_search_solr')
@login_required
def searchSolr():
    if current_user.authlevel < 3:
        return redirect(url_for('index'))

    database    = request.args.get('database')
    publication = request.args.get('publication')
    start_date  = request.args.get('start-date')
    end_date    = request.args.get('end-date')
    search_str  = request.args.get('search-string')
    solr_ids    = request.args.get('solr-ids')

    if (database == '---' and publication != '') or (database != '' and publication == '---'):
        return make_response('Choose either a database or publication.', 500)

    ## build query
    query = []

    ## choose correct database field
    if database:
        if database in ['Annotated Gigaword v5', 'LDC']:
            query.append('DOCSOURCE:"%s"' % database)
        elif database == 'Ethnic NewsWatch':
            query.append('Database:"%s"' % database)
        else:
            return make_response('Invalid database.', 500)

    if start_date == '' and end_date != '':
        return make_response('End date needs a matching start date.', 500)

    if publication:
        query.append('PUBLICATION:"%s"' % publication)

    if start_date:
        ## set end date to now
        if not end_date:
            end_date = dt.datetime.now().strftime('%Y-%m-%d')

        query.append('DATE:[%sT00:00:00.000Z TO %sT00:00:00.000Z]' % (start_date, end_date))

    if search_str:
        query.append('(%s)' % search_str)

    if solr_ids:
        query.append('id:(%s)' % " ".join(solr_ids.split('\n')))

    qstr = ' AND '.join(query)

    return make_response(qstr, 200)

if __name__ == '__main__':
    app.run()
