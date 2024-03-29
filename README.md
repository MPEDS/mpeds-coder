# MPEDS Annotation Interface

The MPEDS Annotation Interface helps facilitate the creation of protest event datasets. While applied to the specific task of coding for protest events, this could also plausibly be used for the development of other types of event datasets or other types of text annotations tasks. 

This system is built in Python using the [Flask](http://flask.pocoo.org/) microframework. It can source articles parsed from Lexis-Nexis (using the `split-ln.py` script), [Apache Solr](http://lucene.apache.org/solr/), or XML files formatted in [News Industry Text Format](http://www.nitf.org/), such as the [LDC's New York Times Annotated Corpus](https://catalog.ldc.upenn.edu/LDC2008T19). 

It also uses [Bootstrap](http://getbootstrap.com/) for CSS and [jQuery](https://jquery.com/) for JavaScript. It only works in Firefox (for now).

## Setup

To populate the database with example information, first run the setup script.

    python setup.py

This will add five users: an admin (admin), two first-pass coders (coder1p\_1, coder1p\_2), and two second-pass coders (coder2p\_1, coder2p\_2). They will  all have the password `default`). It will add a variable hierarchy for second-pass coding. It will also enter metadata for all the articles in the `example-articles` directory, and queue them up for the first-pass coders.

Then run the Flask test server with the following.

    python mpeds_coder.py

## Publications

1. Hanna, Alex. 2017. MPEDS: Automating the Generation of Protest Event Data. SocArXiv. DOI: [10.31235/osf.io/xuqmv](https://osf.io/preprints/socarxiv/xuqmv).
2. Oliver, Pamela, Chaeyoon Lim, Morgan Matthews and Alex Hanna. 2022. "Black Protests in the United States, 1994-2010." Sociological Science 9(May):275-312. DOI: [10.15195/v9.a12](https://sociologicalscience.com/articles-v9-12-275/).
3. Oliver, Pamela, Alex Hanna, Chaeyoon Lim. 2022. “Constructing Relational and Verifiable Protest Event Data: Four Challenges and Some Solutions” Forthcoming in Mobilization. Preprint available https://osf.io/preprints/socarxiv/d89g7/

## DOI

The DOI for this repository has been created with Zenodo.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6953975.svg)](https://doi.org/10.5281/zenodo.6953975)

You can cite this software as:

Hanna, Alex and David Skalinder. 2018. MPEDS Annotation Interface (v1.0.0). Zenodo. https://doi.org/10.5281/zenodo.6953975

## Acknowledgments

Development of this interface has been supported by a National Science Foundation Graduate Research Fellowship and National Science Foundation grants [SES-1423784](http://www.nsf.gov/awardsearch/showAward?AWD_ID=1423784) and [SES-1918342](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1918342). Thanks to Emanuel Ubert, Katie Fallon, and David Skalinder for working with this system since its inception, and to countless annotators who have put a significant time working with and refining this system.
