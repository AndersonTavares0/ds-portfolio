# 0006. A lane is a pair of states

**Status:** Accepted
**Date:** 2026-10-14

## The situation

The delivery finding started out geographic. Rio de Janeiro is late on 12.10% of
its deliveries against São Paulo's 4.49%, and the obvious next move is to find the
sellers who cause it. The obvious way to build that table is to attribute every
order to the seller on it and rank the sellers.

Two things are wrong with that. An order can carry items from more than one
seller, and those sellers can sit in different states, so "the seller on the
order" is not always a single value. More importantly, the dataset carries seller
state and customer state and nothing else: no distance, no route, no carrier, and
no warehouse. A seller-based table would have looked precise and answered a
question the data cannot support.

## The decision

Delivery lateness is measured per **lane**: a pair of `seller_state` to
`customer_state`, in `mart_late_delivery_by_lane`. An order counts in a lane only
when every item on it came from sellers in one state. 65 of the 96,476 delivered
orders span two seller states, have no single lane, and are excluded.

The model also splits elapsed time into `avg_handling_days` (purchase to carrier)
and `avg_transit_days` (carrier to customer), and carries
`late_pct_if_promise_plus3` and `late_pct_if_promise_plus7`.

## What it costs

- **65 delivered orders carry no lane at all.** They are 0.07% of the delivered
  set and they are genuinely unassignable rather than awkward, but they are gone
  from that table. No other delivery figure changes.
- **A lane is not a distance and not a road.** "São Paulo to Rio" means a seller
  in one state and a customer in the other. Everything about the actual route is
  outside the data.
- **The counterfactual columns move the record and not the parcel.** They say what
  the late rate would have been had the promise been longer, which is not the same
  claim as what the customer would have felt. Olist sets the promise, so widening
  it changes a measurement, and the promise and the actual delivery time are
  correlated by construction, so this data cannot separate them.
- **No carrier is identified**, which is the question the laned table raises and
  cannot answer.

## What it bought

The handling/transit split answered what the geographic framing could not. Handling
is between 2.75 and 3.69 days on every lane with volume, so a seller dispatches on
schedule whatever the destination, and the entire Rio gap is in transit. Paired
against the same sellers shipping to both states, 53 of 65 are worse into Rio. A
Rio seller delivering inside Rio is late 4.67% of the time, which is what a São
Paulo seller achieves inside São Paulo at 4.63%.

That moved the recommendation from "investigate Rio" to "work the São Paulo to Rio
lane": 8,129 of Rio's 12,353 deliveries cross it, it is late 14.17% of the time,
and its promise is 27.0 days against 30.3 for the farther São Paulo to Rio Grande
do Sul lane. A table of sellers would have produced a league table of names and no
lever.
