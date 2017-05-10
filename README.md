# MPEDS Annotation Interface

This is the annotation interface used in creating datasets for the Machine-learning Protest Event Data System (MPEDS). While applied to the specific task of coding for protest events, this can also be used for the development of other event datasets.

The MPEDS project uses this interface to generate a training data for event data coding. As structured in this project, coders must first discern whether an article contains a protest event (the haystack task) and then highlight the text in which variables of interest are present. Although many of the variables (e.g. claims) are not explicit in the text, we must rely on the text itself to produce variables of interest. After this 'first pass' of coding, articles which are candidates for event coding are passed to a 'second pass', in which coders disentangle multiple events in a single article, categorize forms, claims, and targets into discrete categories, and ensure the coding for specific locations, dates, social movement organizations, and crowd sizes.

This system is built in Python using the [Flask](http://flask.pocoo.org/) microframework. It can source articles parsed from Lexis-Nexis (using the `split-ln.py` script), [Apache Solr](http://lucene.apache.org/solr/), or XML files formatted in [News Industry Text Format](http://www.nitf.org/), such as the [LDC's New York Times Annotated Corpus](https://catalog.ldc.upenn.edu/LDC2008T19). 

It also uses [Bootstrap](http://getbootstrap.com/) for CSS and [jQuery](https://jquery.com/) for JavaScript. It only works in Firefox (for now).

## Setup

To populate the database with example information, first run the setup script.

    python setup.py

This will add five users: an admin (admin), two first-pass coders (coder1p\_1, coder1p\_2), and two second-pass coders (coder2p\_1, coder2p\_2). They will  all have the password `default`). It will add a variable hierarchy for second-pass coding. It will also enter metadata for all the articles in the `example-articles` directory, and queue them up for the first-pass coders.

Then run the Flask test server with the following.

    python mpeds_coder.py

## Development plan

This is a product in early alpha stages. Features we hope to have working eventually:

* Template system for variables
* Ability to specify multiple article sources
* Generalizing an n-pass structure and control flow
* Ability for multiple database integration
* Cross-browser compatibility

If you're a movement or event data scholar and have a specific project for which you think this would be a good tool, shoot Alex Hanna (alex.hanna@gmail.com) a message.

## Acknowledgments

Development of this interface has been supported by a National Science Foundation Graduate Research Fellowship and National Science Foundation grant [SES-1423784](http://www.nsf.gov/awardsearch/showAward?AWD_ID=1423784). Thanks to Emanuel Ubert and Katie Fallon for working with this system since its inception, and to many undergraduate annotators who have put a lot of time working with and refining this system.
