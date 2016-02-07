# MPEDS Coder - An Event Coding System

This is the annotation interface used in creating datasets for the Machine-learning Protest Event Data System (MPEDS). While applied to the specific task of coding for protest events, this can also be used for the development of other event datasets.

The MPEDS project uses this interface to generate a training data for event data coding. As structured in this project, coders must first discern whether an article contains a protest event (the haystack task) and then highlight the text in which variables of interest are present. Although many of the variables (e.g. claims) are not explicit in the text, we must rely on the text itself to produce variables of interest. After this 'first pass' of coding, articles which are candidates for event coding are passed to a 'second pass', in which coders disentangle multiple events in a single article, categorize forms, claims, and targets into discrete categories, and ensure the coding for specific locations, dates, social movement organizations, and crowd sizes.

