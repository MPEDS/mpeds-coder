

from context import config, database
from models import CanonicalEvent, CanonicalEventLink, CodeEventCreator
import random

## adj1 coder ID
coder_id_adj1 = 43

## Add event
ce = database.db_session.query(CanonicalEvent).filter(CanonicalEvent.key == 'Milo_Chicago_2016').first()

if not ce:
    ce = CanonicalEvent(coder_id = coder_id_adj1, 
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
            coder_id     = coder_id_adj1, 
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
                coder_id     = coder_id_adj1,
                canonical_id = ce.id,
                cec_id       = value
            ))

database.db_session.add_all(cels)
database.db_session.commit()