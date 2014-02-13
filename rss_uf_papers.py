#!/user/bin/env/python
"""
    rss-uf-papers.py -- Generate an RSS feed for recently published UF papers.

    Papers are selected based on harvest date and date of publication.

    Version 1.0 MC 2012-09-03
    --  first version.  Run from command line or IDE.  Result is a single file
        named by the global variable OUTPUT_FILE_NAME (see below).  The
        resulting file should be put in the appropriate file folder of a web
        server to be accessible by news reader software

    Version 1.1 MC 2014-02-13
    --  Formatting improvements
"""

__author__ = "Michael Conlon"
__copyright__ = "Copyright 2013, University of Florida"
__license__ = "BSD 3-Clause license"
__version__ = "1.1"

import datetime
import PyRSS2Gen
import tempita
import vivotools

#  Global variables define the feed and its contents

OUTPUT_FILE_NAME = "rss_uf_papers.xml"
TODAY = datetime.date.today()
DAYS_SINCE_HARVEST = 21     # Added to VIVO in the last 14 days
DAYS_SINCE_PUBLICATION = 90 # Published in the last 90 days
FEED_TITLE = "Recent Publications by UF Authors"
FEED_DESCRIPTION = """
The latest publications by UF authors.  Publications listed here are indexed
by Thomson Reuters in Web of Knowledge (tm) or hand-entered, and represented
in VIVO. Papers published in the last 90 days and added to VIVO in the last
14 days are listed here.
"""


def make_date_expression():
    """
    Generate the regular expression needed to restrict papers based on dated
    harvested
    """
    exp = "^"+datetime.date.isoformat(TODAY)
    for i in range(1, DAYS_SINCE_HARVEST):
        exp = exp + "|^" + datetime.date.isoformat(\
            TODAY-datetime.timedelta(days=i))
    return exp

def make_items(debug=False):
    """
    Extract all the papers for the feed and organize them as feed items
    in a list
    """
    query = tempita.Template("""SELECT DISTINCT ?x ?dt ?label WHERE {
      ?x rdf:type bibo:Document .
      ?x core:dateTimeValue ?dtv .
      ?x rdfs:label ?label . 
      ?x ufVivo:dateHarvested ?dh .
      ?dtv core:dateTime ?dt .
      FILTER regex(?dh,"{{expression}}")
      }
      ORDER BY DESC(?dt)""")
    query = query.substitute(expression=make_date_expression())
    #print query
    result = vivotools.vivo_sparql_query(query)
    #print result
    try:
        count = len(result["results"]["bindings"])
    except:
        count = 0
    if debug:
        print query, count, result["results"]["bindings"][0],\
            result["results"]["bindings"][1]
    i = 0
    date_cutoff = TODAY - datetime.timedelta(days=DAYS_SINCE_PUBLICATION)
    if debug:
        print "Cutoff date for publications is ", date_cutoff
    items = []
    while i < count:
        b = result["results"]["bindings"][i]
        title = b['label']['value']
        uri = b['x']['value']
        dt = b['dt']['value']
        date_published = datetime.date(int(dt[0:4]), int(dt[5:7]),
                                       int(dt[8:10]))
        if date_published >= date_cutoff:
            items.append(PyRSS2Gen.RSSItem(title=title,
                                           link=uri,
                                           pubDate=datetime.datetime.now()))
        i = i + 1
    return items

#  Main Starts here

print "Cutoff date for harvests is ", \
    TODAY - datetime.timedelta(days=DAYS_SINCE_HARVEST)
print "Cutoff date for publications is ", \
    TODAY - datetime.timedelta(days=DAYS_SINCE_PUBLICATION)
items = make_items()
print len(items), " papers in the feed"
rss = PyRSS2Gen.RSS2(title=FEED_TITLE, link = "http://vivo.ufl.edu/rdf",
                     description=FEED_DESCRIPTION,
                     lastBuildDate=datetime.datetime.now(),
                     items=items)
rss.write_xml(open(OUTPUT_FILE_NAME, "w"))
