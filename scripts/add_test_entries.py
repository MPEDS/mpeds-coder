

from context import config, database
from models import CanonicalEvent, CanonicalEventLink, CodeEventCreator, RecentEvent, RecentCanonicalEvent
import random

CODER_ID_ADJ1 = 43

def add_canonical_event():
    """ Adds a canonical event and linkages to two candidate events."""

    ## Add event
    ce = database.db_session.query(CanonicalEvent).filter(CanonicalEvent.key == 'Milo_Chicago_2016').first()

    if not ce:
        ce = CanonicalEvent(coder_id = CODER_ID_ADJ1, 
            key = 'Milo_Chicago_2016', 
            notes = 'This is the main event for the protest against Milo in Chicago in 2016. This is filler text to try to break this part of it. This is filler text to try to break this part of it. This is filler text to try to break this part of it. This is filler text to try to break this part of it.', 
            status = 'In progress')

        ## commit this first so we can get the ID
        database.db_session.add(ce)
        database.db_session.commit()

    ## get two of the candidate events and store in tables
    cand_events = {6032: {}, 21646: {}}

    for event_id in cand_events.keys():
        for record in database.db_session.query(CodeEventCreator).filter(CodeEventCreator.event_id == event_id).all():
            ## put in a list if it a single valued variable
            if record.variable not in cand_events[event_id]:
                if record.variable not in config.SINGLE_VALUE_VARS:
                    cand_events[event_id][record.variable] = []

            ## store the ID as the single variable if SV
            if record.variable in config.SINGLE_VALUE_VARS:
                cand_events[event_id][record.variable] = record.id
            else: ## else, push into the list
                cand_events[event_id][record.variable].append(record.id)

    ## new list for links
    cels = []

    ## randomly put in single-value'd elements into the canonical event
    for sv in config.SINGLE_VALUE_VARS:
        event_id = random.choice(list(cand_events.keys()))

        ## skip if not in cand_events
        if sv not in cand_events[event_id]:
            continue

        ## add the new CELink
        cels.append(CanonicalEventLink(
                coder_id     = CODER_ID_ADJ1, 
                canonical_id = ce.id,
                cec_id       = cand_events[event_id][sv]
            ))

    ## just add in the rest of the data
    for event_id in cand_events.keys():
        for variable in cand_events[event_id].keys():
            
            ## skip because we're ignoring single values
            if variable in config.SINGLE_VALUE_VARS:
                continue

            for value in cand_events[event_id][variable]:
                cels.append(CanonicalEventLink(
                    coder_id     = CODER_ID_ADJ1,
                    canonical_id = ce.id,
                    cec_id       = value
                ))

    database.db_session.add_all(cels)
    database.db_session.commit()


def add_recent_events():
    """ Add two recent candidate events. """
    database.db_session.add_all([
        RecentEvent(CODER_ID_ADJ1, 6032),
        RecentEvent(CODER_ID_ADJ1, 21646)
    ])
    database.db_session.commit()


def add_recent_canonical_events():
    """ Add example canonical event to recent canonical events. """
    ce = database.db_session.query(CanonicalEvent).filter(CanonicalEvent.key == 'Milo_Chicago_2016').first()    

    database.db_session.add(RecentCanonicalEvent(CODER_ID_ADJ1, ce.id))
    database.db_session.commit()

if __name__ == "__main__":
    #add_recent_events()
    #add_recent_canonical_events()
    pass